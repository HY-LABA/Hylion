#!/usr/bin/env python3
"""mock_coordinator.py - bridge.py 의 TCP/NDJSON 입력을 시뮬레이션 + DONE 회신 수신.

사용:
    python mock_coordinator.py walk           # walk_forward 2초 (keepalive 10Hz) 후 자동 DONE 확인
    python mock_coordinator.py turn           # turn_left 2초
    python mock_coordinator.py emergency      # EMERGENCY 송신
    python mock_coordinator.py safety_off     # safety_allowed=false
    python mock_coordinator.py bad_json       # 깨진 JSON (브리지 죽지 않는지 검증)
    python mock_coordinator.py watchdog       # 1건 보내고 침묵 (200ms 후 STOP 되는지)
    python mock_coordinator.py loop           # walk_forward 10Hz 무한 송신 (Ctrl+C 로 종료 → 끊김 검증)
    python mock_coordinator.py stop_mid       # walk 2초 keepalive 중 1초 시점에 stop 송신

대상 bridge 주소는 기본 127.0.0.1:9000. NUC 로 쏠 때는 두 번째 인자 또는 env 로:
    python mock_coordinator.py walk 10.42.0.221
    BRIDGE_HOST=10.42.0.221 python mock_coordinator.py walk
"""

import json
import os
import socket
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

# env(BRIDGE_HOST/BRIDGE_PORT) 또는 두 번째 CLI 인자로 override 가능.
HOST = os.environ.get("BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("BRIDGE_PORT", "9000"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_cmd(**overrides) -> dict:
    base = {
        "action_id": str(uuid.uuid4())[:8],
        "timestamp": now_iso(),
        "session_id": "mock",
        "schema_version": "1.0",
        "source": "terminal",
        "network_online": True,
        "intent": "move",
        "target_object": "",
        "reply_text": "",
        "requires_smolvla": False,
        "requires_bhl": True,
        "gait_cmd": "none",
        "duration_sec": 0.0,
        "state_current": "WALKING",
        "safety_allowed": True,
        "fallback_policy": "",
    }
    base.update(overrides)
    return base


def send_one(sock: socket.socket, msg: dict) -> None:
    line = (json.dumps(msg) + "\n").encode("utf-8")
    sock.sendall(line)
    print(f"TX {msg.get('action_id')} gait={msg.get('gait_cmd')} intent={msg.get('intent')} "
          f"state={msg.get('state_current')} safe={msg.get('safety_allowed')} dur={msg.get('duration_sec')}")


def connect() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print(f"connected to bridge {HOST}:{PORT}")
    return s


# =============================================================================
# DONE 수신 스레드 (백그라운드)
# =============================================================================
class DoneReader:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.thread = threading.Thread(target=self._run, name="done_reader", daemon=True)
        self.running = True

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.running = False

    def _run(self) -> None:
        self.sock.settimeout(0.5)
        buf = b""
        while self.running:
            try:
                data = self.sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            if not data:
                return
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode("utf-8"))
                except Exception:
                    print(f"RX (parse fail): {line[:80]!r}")
                    continue
                print(f"RX EVENT {msg.get('event')} action_id={msg.get('action_id')} reason={msg.get('reason')}")


# =============================================================================
# 시나리오
# =============================================================================
def scenario_walk(sock: socket.socket) -> None:
    """duration_sec=2.0 로 한 번 보내고 keepalive 10Hz 로 반복. bridge 가 2초 후 DONE 회신."""
    action_id = str(uuid.uuid4())[:8]
    # cold_start 1.5s + duration 2.0s + DONE 여유 1.5s = 5초
    end = time.time() + 5.0
    while time.time() < end:
        send_one(sock, make_cmd(
            action_id=action_id,
            gait_cmd="walk_forward",
            intent="move",
            duration_sec=2.0,
        ))
        time.sleep(0.1)


def scenario_turn(sock: socket.socket) -> None:
    action_id = str(uuid.uuid4())[:8]
    end = time.time() + 5.0
    while time.time() < end:
        send_one(sock, make_cmd(
            action_id=action_id,
            gait_cmd="turn_left",
            intent="move",
            duration_sec=2.0,
        ))
        time.sleep(0.1)


def scenario_emergency(sock: socket.socket) -> None:
    action_id = str(uuid.uuid4())[:8]
    send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", duration_sec=5.0))
    time.sleep(0.5)
    send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", state_current="EMERGENCY", duration_sec=5.0))
    time.sleep(1.5)


def scenario_safety_off(sock: socket.socket) -> None:
    action_id = str(uuid.uuid4())[:8]
    send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", duration_sec=5.0))
    time.sleep(0.5)
    send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", safety_allowed=False, duration_sec=5.0))
    time.sleep(1.5)


def scenario_bad_json(sock: socket.socket) -> None:
    sock.sendall(b"this is not json\n")
    time.sleep(0.5)
    action_id = str(uuid.uuid4())[:8]
    send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", duration_sec=1.0))
    time.sleep(2.0)


def scenario_watchdog(sock: socket.socket) -> None:
    send_one(sock, make_cmd(gait_cmd="walk_forward", duration_sec=5.0))
    print("now silent for 2s — bridge must drop to STOP after watchdog timeout")
    time.sleep(2.0)


def scenario_loop(sock: socket.socket) -> None:
    print("looping walk_forward @ 10Hz with same action_id. Ctrl+C to disconnect.")
    action_id = str(uuid.uuid4())[:8]
    try:
        while True:
            send_one(sock, make_cmd(action_id=action_id, gait_cmd="walk_forward", duration_sec=30.0))
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\ndisconnecting (bridge should STOP)")


def scenario_stop_mid(sock: socket.socket) -> None:
    """walk 시작 → 1초 뒤 stop intent 보내서 즉시 종료 + DONE 확인.

    cold_start 1.5s 가 있으므로 walk keepalive 를 2.5s 보낸 뒤 stop 송신.
    """
    walk_id = str(uuid.uuid4())[:8]
    deadline = time.time() + 2.5
    while time.time() < deadline:
        send_one(sock, make_cmd(action_id=walk_id, gait_cmd="walk_forward", duration_sec=10.0))
        time.sleep(0.1)
    stop_id = str(uuid.uuid4())[:8]
    send_one(sock, make_cmd(action_id=stop_id, intent="stop", gait_cmd="stop", state_current="IDLE"))
    time.sleep(1.5)


SCENARIOS = {
    "walk": scenario_walk,
    "turn": scenario_turn,
    "emergency": scenario_emergency,
    "safety_off": scenario_safety_off,
    "bad_json": scenario_bad_json,
    "watchdog": scenario_watchdog,
    "loop": scenario_loop,
    "stop_mid": scenario_stop_mid,
}


def main() -> None:
    global HOST
    if len(sys.argv) < 2 or sys.argv[1] not in SCENARIOS:
        print(__doc__)
        print("scenarios:", ", ".join(SCENARIOS.keys()))
        sys.exit(1)

    # 두 번째 인자가 있으면 대상 host override (env 보다 우선).
    if len(sys.argv) >= 3:
        HOST = sys.argv[2]

    sock = connect()
    reader = DoneReader(sock)
    reader.start()
    try:
        SCENARIOS[sys.argv[1]](sock)
    finally:
        reader.stop()
        sock.close()
        print("closed")


if __name__ == "__main__":
    main()
