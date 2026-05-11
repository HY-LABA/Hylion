#!/usr/bin/env python3
"""mock_coordinator.py - bridge.py 의 TCP/NDJSON 입력을 시뮬레이션.

사용:
    python mock_coordinator.py walk           # walk_forward 2초 후 stop
    python mock_coordinator.py turn           # turn_left 2초 후 stop
    python mock_coordinator.py emergency      # EMERGENCY 송신
    python mock_coordinator.py safety_off     # safety_allowed=false
    python mock_coordinator.py bad_json       # 깨진 JSON (브리지 죽지 않는지 검증)
    python mock_coordinator.py watchdog       # 1건 보내고 침묵 (200ms 후 STOP 되는지)
    python mock_coordinator.py loop           # walk_forward 10Hz 무한 송신 (Ctrl+C 로 종료 → 끊김 검증)
"""

import json
import socket
import sys
import time
import uuid
from datetime import datetime, timezone

HOST = "127.0.0.1"
PORT = 9000


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
          f"state={msg.get('state_current')} safe={msg.get('safety_allowed')}")


def connect() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print(f"connected to bridge {HOST}:{PORT}")
    return s


def scenario_walk(sock: socket.socket) -> None:
    for _ in range(20):  # 2s @ 10Hz
        send_one(sock, make_cmd(gait_cmd="walk_forward", intent="move"))
        time.sleep(0.1)
    send_one(sock, make_cmd(gait_cmd="stop", intent="stop", state_current="IDLE"))


def scenario_turn(sock: socket.socket) -> None:
    for _ in range(20):
        send_one(sock, make_cmd(gait_cmd="turn_left", intent="move"))
        time.sleep(0.1)
    send_one(sock, make_cmd(gait_cmd="stop", intent="stop", state_current="IDLE"))


def scenario_emergency(sock: socket.socket) -> None:
    send_one(sock, make_cmd(gait_cmd="walk_forward"))
    time.sleep(0.5)
    send_one(sock, make_cmd(gait_cmd="walk_forward", state_current="EMERGENCY"))
    time.sleep(1.0)


def scenario_safety_off(sock: socket.socket) -> None:
    send_one(sock, make_cmd(gait_cmd="walk_forward"))
    time.sleep(0.5)
    send_one(sock, make_cmd(gait_cmd="walk_forward", safety_allowed=False))
    time.sleep(1.0)


def scenario_bad_json(sock: socket.socket) -> None:
    sock.sendall(b"this is not json\n")
    time.sleep(0.5)
    send_one(sock, make_cmd(gait_cmd="walk_forward"))
    time.sleep(0.5)
    send_one(sock, make_cmd(gait_cmd="stop", intent="stop"))


def scenario_watchdog(sock: socket.socket) -> None:
    send_one(sock, make_cmd(gait_cmd="walk_forward"))
    print("now silent for 2s — bridge must drop to STOP after watchdog timeout")
    time.sleep(2.0)


def scenario_loop(sock: socket.socket) -> None:
    print("looping walk_forward @ 10Hz. Ctrl+C to disconnect.")
    try:
        while True:
            send_one(sock, make_cmd(gait_cmd="walk_forward"))
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\ndisconnecting (bridge should STOP)")


SCENARIOS = {
    "walk": scenario_walk,
    "turn": scenario_turn,
    "emergency": scenario_emergency,
    "safety_off": scenario_safety_off,
    "bad_json": scenario_bad_json,
    "watchdog": scenario_watchdog,
    "loop": scenario_loop,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in SCENARIOS:
        print(__doc__)
        print("scenarios:", ", ".join(SCENARIOS.keys()))
        sys.exit(1)

    sock = connect()
    try:
        SCENARIOS[sys.argv[1]](sock)
    finally:
        sock.close()
        print("closed")


if __name__ == "__main__":
    main()
