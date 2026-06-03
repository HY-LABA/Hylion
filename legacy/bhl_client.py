"""bhl_client.py - Jetson coordinator 측의 NUC bridge 연결 클라이언트.

역할:
  - 단일 TCP 연결 위에 양방향 NDJSON
  - 송신: coordinator 가 결정한 action_json 을 keepalive 주기로 반복 송신
  - 수신: bridge 가 보낸 {"event":"done", ...} 를 받아 coordinator 에 통지
  - 끊김 시 재연결, 모든 오류 격리 (coordinator main flow 를 절대 안 죽임)

자세한 사양: nuc/bhl/Jetson_NUC_연결_가이드.md §5
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
from typing import Optional

log = logging.getLogger("bhl_client")


DEFAULT_HOST = os.environ.get("HYLION_BHL_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("HYLION_BHL_PORT", "9000"))
DEFAULT_KEEPALIVE_HZ = float(os.environ.get("HYLION_BHL_KEEPALIVE_HZ", "10"))


class BhlClient:
    """NUC bridge 와의 TCP/NDJSON 양방향 연결.

    사용:
        client = BhlClient(host, port)
        client.start()
        ...
        client.set_command(action_json)            # 송신 워커가 keepalive 시작
        done = client.wait_for_done(action_id, timeout=action.duration_sec + 2.0)
        client.clear()                              # keepalive 중단
        ...
        client.stop()
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        keepalive_hz: float = DEFAULT_KEEPALIVE_HZ,
        reconnect_backoff_s: float = 1.0,
    ) -> None:
        self.host = host
        self.port = port
        self.period = 1.0 / keepalive_hz
        self.reconnect_backoff_s = reconnect_backoff_s

        self._lock = threading.Lock()
        self._sock: Optional[socket.socket] = None
        self._current: Optional[dict] = None  # 송신 워커가 반복 보낼 명령

        # action_id -> threading.Event (done 수신 시 set)
        self._done_events: dict[str, threading.Event] = {}
        self._done_reasons: dict[str, str] = {}

        self._running = False
        self._sender_thread: Optional[threading.Thread] = None
        self._receiver_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # 라이프사이클
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._sender_thread = threading.Thread(target=self._sender_loop, name="bhl_sender", daemon=True)
        self._receiver_thread = threading.Thread(target=self._receiver_loop, name="bhl_receiver", daemon=True)
        self._sender_thread.start()
        self._receiver_thread.start()
        log.info("BhlClient started: target=%s:%d keepalive=%.1fHz", self.host, self.port, 1.0 / self.period)

    def stop(self) -> None:
        self._running = False
        with self._lock:
            sock = self._sock
            self._sock = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
        log.info("BhlClient stopped")

    # ------------------------------------------------------------------
    # coordinator 가 호출하는 API
    # ------------------------------------------------------------------
    def set_command(self, action_json: dict) -> None:
        """현재 보관 중인 명령을 갱신. 송신 워커가 다음 사이클부터 이걸 송신.

        같은 action_id 의 명령을 여러 번 set 해도 안전 (keepalive 효과).
        새 action_id 면 그 명령부터 송신.
        """
        action_id = action_json.get("action_id")
        with self._lock:
            self._current = action_json
            # done 이벤트 미리 등록 (해당 action_id 에 wait_for_done 가능)
            if action_id and action_id not in self._done_events:
                self._done_events[action_id] = threading.Event()

    def clear(self) -> None:
        """송신 워커를 idle 상태로. 다음 keepalive 사이클부터 송신 안 함."""
        with self._lock:
            self._current = None

    def wait_for_done(self, action_id: str, timeout: float) -> tuple[bool, Optional[str]]:
        """bridge 로부터 해당 action_id 의 done 이벤트 수신을 timeout 까지 대기.

        반환: (성공 여부, reason 문자열)
            (True, "duration_elapsed" | "stop_command" | "safety_or_emergency") 정상 수신
            (False, None) timeout
        """
        with self._lock:
            ev = self._done_events.get(action_id)
            if ev is None:
                ev = threading.Event()
                self._done_events[action_id] = ev

        got = ev.wait(timeout=timeout)
        if not got:
            return False, None

        with self._lock:
            reason = self._done_reasons.pop(action_id, None)
            # 일회용 event 정리
            self._done_events.pop(action_id, None)
        return True, reason

    # ------------------------------------------------------------------
    # 내부 — 연결 관리
    # ------------------------------------------------------------------
    def _ensure_connected(self) -> Optional[socket.socket]:
        """소켓 없으면 새로 연결. 실패하면 None 반환 (다음 사이클 재시도)."""
        with self._lock:
            sock = self._sock
        if sock is not None:
            return sock

        try:
            new_sock = socket.create_connection((self.host, self.port), timeout=2.0)
            new_sock.settimeout(None)  # 송수신은 비-블로킹/timeout 별도 적용
            with self._lock:
                self._sock = new_sock
            log.info("connected to bridge %s:%d", self.host, self.port)
            return new_sock
        except OSError as e:
            log.debug("connect to %s:%d failed: %s", self.host, self.port, e)
            time.sleep(self.reconnect_backoff_s)
            return None

    def _drop_connection(self, why: str) -> None:
        with self._lock:
            sock = self._sock
            self._sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
            log.warning("connection dropped: %s", why)

    # ------------------------------------------------------------------
    # 내부 — 송신 워커
    # ------------------------------------------------------------------
    def _sender_loop(self) -> None:
        while self._running:
            t0 = time.monotonic()

            with self._lock:
                cmd = self._current
                sock = self._sock

            if cmd is not None:
                if sock is None:
                    sock = self._ensure_connected()
                if sock is not None:
                    try:
                        line = (json.dumps(cmd) + "\n").encode("utf-8")
                        sock.sendall(line)
                    except OSError as e:
                        self._drop_connection(f"send failed: {e}")
            else:
                # 보관 명령 없음 — 연결은 유지하되 송신만 skip.
                # 연결 자체도 유지 안 해도 됨. 다만 wait_for_done 중인 동작이 있을 수
                # 있으므로 receiver 가 살아있게 끊지는 않음.
                pass

            elapsed = time.monotonic() - t0
            sleep_for = self.period - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    # ------------------------------------------------------------------
    # 내부 — 수신 워커 (DONE 이벤트)
    # ------------------------------------------------------------------
    def _receiver_loop(self) -> None:
        buf = b""
        while self._running:
            with self._lock:
                sock = self._sock
            if sock is None:
                # 송신 워커가 연결 만들기 전엔 수신할 게 없음
                time.sleep(self.reconnect_backoff_s)
                continue

            try:
                sock.settimeout(0.5)
                data = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError as e:
                self._drop_connection(f"recv failed: {e}")
                buf = b""
                continue

            if not data:
                self._drop_connection("peer closed")
                buf = b""
                continue

            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    log.warning("RX parse error: %s (line=%r)", e, line[:120])
                    continue
                self._handle_event(msg)

    def _handle_event(self, msg: dict) -> None:
        event = msg.get("event")
        if event != "done":
            log.debug("RX unknown event: %s", msg)
            return

        action_id = msg.get("action_id")
        reason = msg.get("reason", "unknown")
        if not action_id:
            log.warning("RX done without action_id: %s", msg)
            return

        log.info("RX DONE action_id=%s reason=%s", action_id, reason)
        with self._lock:
            ev = self._done_events.get(action_id)
            if ev is None:
                ev = threading.Event()
                self._done_events[action_id] = ev
            self._done_reasons[action_id] = reason
        ev.set()
