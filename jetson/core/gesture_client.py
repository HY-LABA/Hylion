"""Gesture 데몬 클라이언트 — coordinator 측.

coordinator 는 jetson/expression/.venv 에서 돌고 lerobot 이 없다. gesture 재생은
.hylion_arm venv(lerobot + torch) 가 필요하다. 매 gesture 마다 subprocess 로
lerobot+torch import(~4s) + 팔 connect(~4s) 를 새로 하면 그 cold-start 가 그대로
지연이 되므로, coordinator 는 시작 시 gesture_daemon.py 를 .hylion_arm venv 의
자식 프로세스로 한 번 띄우고 Unix 소켓으로 명령만 보낸다.

`play()` 는 비블로킹이다 — 데몬이 즉시 ACK 하고 재생은 데몬의 워커 스레드가
수행하므로, 팔 동작이 coordinator 의 TTS 재생·입 서보와 동시에 진행된다.

env override:
  JETSON_VENV            lerobot venv (기본 ~/smolvla/orin/.hylion_arm)
  HYLION_GESTURE_SOCK    소켓 경로 (기본 /tmp/hylion_gesture.sock)
  HYLION_GESTURE_DAEMON  '0' 이면 데몬 비활성화 (gesture 전부 no-op)
  ORIN_GESTURES_ROOT     gesture 데이터 루트 (데몬에 전달)
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DAEMON_SCRIPT = _PROJECT_ROOT / "smolVLA" / "scripts" / "gesture_daemon.py"
_DEFAULT_VENV = Path.home() / "smolvla" / "orin" / ".hylion_arm"
_DEFAULT_SOCK = "/tmp/hylion_gesture.sock"


def _venv_python() -> Path:
    return Path(os.getenv("JETSON_VENV", str(_DEFAULT_VENV))).expanduser() / "bin" / "python"


def _sock_path() -> str:
    return os.getenv("HYLION_GESTURE_SOCK", _DEFAULT_SOCK)


def _send(sock_path: str, command: str, timeout: float = 5.0) -> str | None:
    """소켓에 한 줄 명령 → 한 줄 응답. 연결 실패 시 None."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(sock_path)
            sock.sendall((command.strip() + "\n").encode("utf-8"))
            chunks: list[bytes] = []
            while b"\n" not in b"".join(chunks):
                data = sock.recv(1024)
                if not data:
                    break
                chunks.append(data)
            return b"".join(chunks).decode("utf-8", errors="replace").strip()
    except (OSError, socket.timeout):
        return None


class GestureDaemonHandle:
    """gesture_daemon.py 자식 프로세스 + 소켓 통신 래퍼.

    `play()` 가 데몬 미가동/미준비여도 절대 예외를 올리지 않는다 — gesture 실패가
    대화 루프를 깨면 안 되므로 (False, 사유) 를 돌려줄 뿐이다.
    """

    def __init__(self, proc: subprocess.Popen | None, sock_path: str, *, disabled: bool = False):
        self._proc = proc
        self._sock_path = sock_path
        self._disabled = disabled
        self._ready = False

    # ── readiness ────────────────────────────────────────────────────────────
    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def wait_ready(self, timeout: float = 15.0) -> bool:
        """데몬이 ping 에 응답할 때까지 대기 (startup 에서 1회 호출용, 비치명적).

        torch import + 팔 connect 로 데몬 기동에 ~8-10s 걸린다. 성공하면 이후
        play() 는 곧바로 명령을 보낸다.
        """
        if self._disabled or self._proc is None:
            return False
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.is_alive():
                return False
            if _send(self._sock_path, "ping", timeout=2.0) == "pong":
                self._ready = True
                return True
            time.sleep(0.5)
        return False

    # ── commands ─────────────────────────────────────────────────────────────
    def play(self, gesture_name: str) -> tuple[bool, str]:
        """gesture 재생을 데몬에 요청. 비블로킹 — 즉시 ACK 만 받고 리턴.

        Returns (ok, message). ok=True 는 '데몬이 재생 큐에 받아들임' 을 의미하지
        재생 완료가 아니다 (재생은 데몬 워커 스레드가 비동기 수행).
        """
        if self._disabled:
            return False, "gesture 데몬 비활성화 (HYLION_GESTURE_DAEMON=0)"
        if not self.is_alive():
            return False, "gesture 데몬 미가동"
        if not self._ready:
            # 아직 준비 확인 전 — 짧게 한 번 ping (startup 직후 첫 gesture 대비).
            if _send(self._sock_path, "ping", timeout=2.0) == "pong":
                self._ready = True
            else:
                return False, "gesture 데몬 준비 안 됨"

        response = _send(self._sock_path, f"play {gesture_name}")
        if response is None:
            return False, "gesture 데몬 응답 없음"
        if response.startswith("accepted"):
            return True, response
        return False, response  # error / busy

    def stop(self) -> None:
        """데몬에 shutdown 요청 후 프로세스 정리. 멱등."""
        if self._proc is None:
            return
        if self.is_alive():
            _send(self._sock_path, "shutdown", timeout=3.0)
            try:
                self._proc.wait(timeout=15.0)
            except subprocess.TimeoutExpired:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
        self._proc = None


def start_gesture_daemon() -> GestureDaemonHandle:
    """gesture_daemon.py 를 .hylion_arm venv 의 자식 프로세스로 기동.

    실패(venv 없음, 스크립트 없음, spawn 실패)해도 예외를 올리지 않고 disabled
    핸들을 돌려준다 — gesture 는 부가 기능이라 coordinator 기동을 막으면 안 된다.
    readiness 는 호출자가 wait_ready() 로 따로 확인 (비치명적).
    """
    sock_path = _sock_path()

    if os.getenv("HYLION_GESTURE_DAEMON", "1") == "0":
        print("[Gesture] HYLION_GESTURE_DAEMON=0 — 데몬 비활성화")
        return GestureDaemonHandle(None, sock_path, disabled=True)

    venv_python = _venv_python()
    if not venv_python.is_file():
        print(f"[Gesture] venv python 없음: {venv_python} — gesture 비활성화")
        return GestureDaemonHandle(None, sock_path, disabled=True)
    if not _DAEMON_SCRIPT.is_file():
        print(f"[Gesture] daemon 스크립트 없음: {_DAEMON_SCRIPT} — gesture 비활성화")
        return GestureDaemonHandle(None, sock_path, disabled=True)

    # 데몬 자식 환경:
    #  - VIRTUAL_ENV 제거: 물려받은 stale/foreign 값이 venv 판별을 망친다.
    #  - LD_LIBRARY_PATH 에 cusparselt 추가: torch import 전 필요 (데몬도 자체
    #    re-exec 가드가 있지만, 미리 넣어주면 re-exec 한 번을 아낀다).
    #  - 소켓/데이터 경로를 명시적으로 전달해 coordinator 와 일치 보장.
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    venv_root = venv_python.parent.parent
    cusparselt = venv_root / "lib" / "python3.10" / "site-packages" / "nvidia" / "cusparselt" / "lib"
    if (cusparselt / "libcusparseLt.so.0").is_file():
        prev = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{cusparselt}:{prev}" if prev else str(cusparselt)
    env["HYLION_GESTURE_SOCK"] = sock_path
    env.setdefault("ORIN_GESTURES_ROOT", str(_PROJECT_ROOT / "smolVLA" / "gestures"))

    try:
        # stdout/stderr 는 coordinator 콘솔로 상속 — 데몬 로그가 그대로 보인다.
        proc = subprocess.Popen([str(venv_python), str(_DAEMON_SCRIPT)], env=env)
    except Exception as exc:  # noqa: BLE001
        print(f"[Gesture] 데몬 spawn 실패: {exc!r} — gesture 비활성화")
        return GestureDaemonHandle(None, sock_path, disabled=True)

    print(f"[Gesture] 데몬 기동 (pid={proc.pid}, sock={sock_path})")
    return GestureDaemonHandle(proc, sock_path)
