#!/usr/bin/env python
"""상주 gesture 재생 데몬 — Hylion.

coordinator 는 jetson/expression/.venv 에서 돌고 lerobot 이 없다. gesture 재생은
.hylion_arm venv(lerobot + torch) 가 필요한데, 매 gesture 마다 subprocess 로
lerobot+torch 를 새로 import(~4s) + 팔 connect(~4s) 하면 그 cold-start 가 그대로
지연이 된다. 이 데몬이 .hylion_arm venv 에서 상주하며 lerobot import 와 팔 연결을
warm 하게 유지한다.

coordinator(gesture_client.py) 는 Unix 소켓으로 `play <gesture>` 한 줄만 던지고
즉시 리턴 — 재생은 데몬의 워커 스레드가 비동기로 수행하므로 TTS 음성·입 서보와
동시에 팔이 움직인다.

메모리: 모델을 안 올리고 GPU 도 안 건드려서 RSS ~350MB (순수 torch import 비용).

idle 시 토크 OFF(팔 limp — 모터 발열/overload 회피), 재생 직전에만 토크 ON.

프로토콜 (Unix socket, newline 종료 텍스트, 연결당 1명령):
  play <gesture_name>   재생 큐에 넣고 즉시 'accepted <name>' (비블로킹). 이름
                        형식/데이터 오류 'error <reason>'. 큐 가득 'busy'.
  ping                  'pong'
  status                'ok connected=<bool> busy=<bool> queue=<n>'
  shutdown              'bye' 후 데몬 종료 (팔 disconnect)

env override:
  HYLION_GESTURE_SOCK   소켓 경로 (기본 /tmp/hylion_gesture.sock)
  ORIN_GESTURES_ROOT    gesture 데이터 루트 (기본 ~/Hylion/jetson/arm/data)
  FOLLOWER_PORT         follower 시리얼 by-id 경로
  FOLLOWER_ID           robot.id = 캘리브 파일명
"""

from __future__ import annotations

import os
import queue
import re
import signal
import socket
import sys
import threading
from pathlib import Path

# torch import 전에 LD_LIBRARY_PATH 보장 (필요 시 self re-exec).
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from gesture_replay_core import (  # noqa: E402
    DEFAULT_ID,
    DEFAULT_PORT,
    connect_arm,
    ensure_ld_library_path,
    load_episode,
    replay_episode,
)

ensure_ld_library_path()

_GESTURE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_QUEUE_MAXSIZE = 8


def _log(msg: str) -> None:
    # 데몬 stdout 은 coordinator 콘솔로 상속됨 — 즉시 보이도록 flush.
    print(f"[gesture_daemon] {msg}", flush=True)


def _sock_path() -> str:
    return os.getenv("HYLION_GESTURE_SOCK", "/tmp/hylion_gesture.sock")


def _gestures_root() -> Path:
    env = os.getenv("ORIN_GESTURES_ROOT")
    if env:
        return Path(env).expanduser()
    return Path.home() / "Hylion" / "jetson" / "arm" / "data"


class GestureDaemon:
    """팔 연결을 warm 하게 들고, 소켓 명령을 워커 스레드 큐로 흘려보낸다."""

    def __init__(self, port: str, robot_id: str, gestures_root: Path):
        self._port = port
        self._robot_id = robot_id
        self._root = gestures_root
        self._robot = None
        self._jobs: queue.Queue = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        self._busy = threading.Event()
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        """팔 connect → idle 토크 OFF → 워커 스레드 기동."""
        _log(f"연결 시도: port={self._port} id={self._robot_id}")
        self._robot = connect_arm(self._port, self._robot_id)
        # connect() 직후엔 토크 ON — idle 동안엔 OFF 로 둬서 모터 발열을 피한다.
        self._set_torque(False, context="startup idle")
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        _log("팔 연결 완료, 워커 스레드 기동 — READY")

    def shutdown(self) -> None:
        """워커 정지 → 팔 disconnect. 멱등."""
        if self._stop.is_set():
            return
        self._stop.set()
        self._jobs.put(None)  # 워커 깨우는 sentinel
        if self._worker is not None:
            self._worker.join(timeout=15.0)
        if self._robot is not None:
            try:
                self._robot.disconnect()
                _log("팔 disconnect 완료")
            except Exception as exc:  # noqa: BLE001
                # disconnect 의 disable_torque 단계 overload 는 cosmetic.
                _log(f"disconnect 중 예외 (cosmetic 가능): {exc!r}")
            self._robot = None

    # ── torque helper ────────────────────────────────────────────────────────
    def _set_torque(self, on: bool, context: str) -> None:
        """idle=OFF / 재생=ON. 재생 직후 OFF 단계의 overload 는 cosmetic 처리."""
        try:
            if on:
                self._robot.bus.enable_torque()
            else:
                self._robot.bus.disable_torque()
        except Exception as exc:  # noqa: BLE001
            _log(f"토크 {'ON' if on else 'OFF'} 실패 ({context}, cosmetic 가능): {exc!r}")

    # ── worker ───────────────────────────────────────────────────────────────
    def _worker_loop(self) -> None:
        while True:
            gesture_name = self._jobs.get()
            if gesture_name is None or self._stop.is_set():
                self._jobs.task_done()
                break
            self._busy.set()
            try:
                self._replay_one(gesture_name)
            except Exception as exc:  # noqa: BLE001
                # 재생 실패는 로그만 — 데몬은 절대 안 죽는다.
                _log(f"{gesture_name}: 재생 실패 {exc!r}")
            finally:
                self._set_torque(False, context=f"after {gesture_name}")
                self._busy.clear()
                self._jobs.task_done()

    def _replay_one(self, gesture_name: str) -> None:
        gesture_dir = self._root / gesture_name
        action_names, fps, actions = load_episode(gesture_dir)
        self._set_torque(True, context=f"before {gesture_name}")
        _log(f"{gesture_name}: 재생 시작 (frames={len(actions)}, fps={fps})")
        elapsed = replay_episode(self._robot, action_names, fps, actions)
        _log(f"{gesture_name}: 재생 완료 (frames={len(actions)}, elapsed={elapsed:.1f}s)")

    # ── command dispatch ─────────────────────────────────────────────────────
    def handle_command(self, line: str) -> str:
        """소켓 한 줄 → 한 줄 응답. play 는 큐에 넣고 즉시 ACK (비블로킹)."""
        parts = line.strip().split()
        if not parts:
            return "error empty command"
        cmd = parts[0]

        if cmd == "ping":
            return "pong"

        if cmd == "status":
            return (
                f"ok connected={self._robot is not None and self._robot.is_connected} "
                f"busy={self._busy.is_set()} queue={self._jobs.qsize()}"
            )

        if cmd == "shutdown":
            # 응답을 보낸 뒤 main 루프가 정리하도록 stop 만 세팅.
            self._stop.set()
            return "bye"

        if cmd == "play":
            if len(parts) < 2:
                return "error play: gesture_name 누락"
            gesture_name = parts[1]
            if not _GESTURE_NAME_RE.match(gesture_name):
                return f"error play: 이름 형식 오류 '{gesture_name}'"
            if not (self._root / gesture_name / "meta" / "info.json").is_file():
                return f"error play: gesture 데이터 없음 '{gesture_name}'"
            try:
                self._jobs.put_nowait(gesture_name)
            except queue.Full:
                return "busy"
            return f"accepted {gesture_name}"

        return f"error 알 수 없는 명령 '{cmd}'"

    @property
    def stopping(self) -> bool:
        return self._stop.is_set()


def _serve(daemon: GestureDaemon, sock_path: str) -> None:
    """소켓 accept 루프 — main 스레드. 연결당 1명령 처리."""
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    srv.listen(8)
    srv.settimeout(1.0)  # stop 플래그를 주기적으로 확인
    _log(f"소켓 listen: {sock_path}")

    try:
        while not daemon.stopping:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                conn.settimeout(5.0)
                try:
                    chunks = []
                    while b"\n" not in b"".join(chunks):
                        data = conn.recv(1024)
                        if not data:
                            break
                        chunks.append(data)
                    line = b"".join(chunks).decode("utf-8", errors="replace")
                    if not line:
                        continue
                    response = daemon.handle_command(line)
                    conn.sendall((response + "\n").encode("utf-8"))
                except socket.timeout:
                    _log("클라이언트 응답 타임아웃 — 연결 종료")
                except Exception as exc:  # noqa: BLE001
                    _log(f"명령 처리 중 예외: {exc!r}")
    finally:
        srv.close()
        if os.path.exists(sock_path):
            os.unlink(sock_path)


def main() -> int:
    port = os.getenv("FOLLOWER_PORT", DEFAULT_PORT)
    robot_id = os.getenv("FOLLOWER_ID", DEFAULT_ID)
    gestures_root = _gestures_root()
    sock_path = _sock_path()

    if not gestures_root.is_dir():
        _log(f"ERROR: gesture 루트 없음: {gestures_root}")
        return 4

    daemon = GestureDaemon(port=port, robot_id=robot_id, gestures_root=gestures_root)

    # SIGTERM/SIGINT → 정상 종료 (coordinator 가 종료 시 보냄).
    def _on_signal(signum, _frame):
        _log(f"시그널 {signum} 수신 — 종료 절차 시작")
        daemon._stop.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    try:
        daemon.start()
    except Exception as exc:  # noqa: BLE001
        _log(f"ERROR: 팔 연결 실패 — 데몬 기동 중단: {exc!r}")
        return 5

    try:
        _serve(daemon, sock_path)
    finally:
        daemon.shutdown()
    _log("종료 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
