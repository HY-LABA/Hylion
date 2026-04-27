#!/usr/bin/env python3
"""Diagnostic utility to verify SO-ARM motor encoder responses.

This script prints:
1) /dev/serial/by-id mapping to /dev/ttyACM*
2) raw Present_Position values for motor IDs 1-6 at 1Hz
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

# Make `orin/lerobot` importable when the script is executed from source.
SCRIPT_DIR = Path(__file__).resolve().parent
ORIN_ROOT = SCRIPT_DIR.parent
if str(ORIN_ROOT) not in sys.path:
    sys.path.insert(0, str(ORIN_ROOT))

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

JOINTS = [
    ("shoulder_pan", 1),
    ("shoulder_lift", 2),
    ("elbow_flex", 3),
    ("wrist_flex", 4),
    ("wrist_roll", 5),
    ("gripper", 6),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SO-ARM encoder diagnostic tool")
    parser.add_argument(
        "--port",
        default="/dev/ttyACM0",
        help="Serial port to diagnose (default: /dev/ttyACM0, follower expected)",
    )
    parser.add_argument(
        "--hz",
        type=float,
        default=1.0,
        help="Sampling frequency in Hz (default: 1.0)",
    )
    return parser.parse_args()


def extract_serial_from_by_id(name: str) -> str:
    match = re.search(r"_([^_]+)-if\d+-port\d+$", name)
    return match.group(1) if match else "unknown"


def guess_role(link_name: str, tty_path: str) -> str:
    lowered = link_name.lower()
    if "follower" in lowered:
        return "follower"
    if "leader" in lowered:
        return "leader"
    if tty_path.endswith("ttyACM0"):
        return "follower?"
    if tty_path.endswith("ttyACM1"):
        return "leader?"
    return "unknown"


def print_serial_mapping() -> None:
    by_id_dir = Path("/dev/serial/by-id")
    print("=" * 96)
    print("[Serial Mapping] /dev/serial/by-id -> /dev/ttyACM*")
    print("=" * 96)

    if not by_id_dir.exists():
        print(f"Directory not found: {by_id_dir}")
        return

    links = sorted(by_id_dir.iterdir())
    if not links:
        print("No entries found under /dev/serial/by-id")
        return

    print(f"{'Role':<10} {'Serial':<16} {'TTY':<14} {'by-id entry'}")
    print("-" * 96)

    for link in links:
        if not link.is_symlink():
            continue
        resolved = link.resolve(strict=False)
        tty_path = str(resolved)
        role = guess_role(link.name, tty_path)
        serial = extract_serial_from_by_id(link.name)
        print(f"{role:<10} {serial:<16} {tty_path:<14} {link.name}")

    print("-" * 96)


def make_bus(port: str) -> FeetechMotorsBus:
    motors = {
        "shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
        "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
        "elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
        "wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
        "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
        "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
    }
    return FeetechMotorsBus(port=port, motors=motors)


def print_positions_table(positions: dict[str, int], previous: dict[str, int] | None) -> None:
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Present_Position raw")
    print(f"{'Joint':<15} {'ID':<4} {'Raw':<8} {'Delta':<8}")
    print("-" * 40)
    for joint_name, motor_id in JOINTS:
        raw = positions[joint_name]
        if previous is None:
            delta = "-"
        else:
            delta = f"{raw - previous[joint_name]:+d}"
        print(f"{joint_name:<15} {motor_id:<4} {raw:<8} {delta:<8}")


def run(port: str, hz: float) -> int:
    if hz <= 0:
        print("Error: --hz must be > 0", file=sys.stderr)
        return 2

    print_serial_mapping()
    print(f"\n[Encoder Diagnostic] Connecting to {port}")
    print("Press Ctrl+C to stop. Move each joint by hand and watch Raw/Delta change.")

    bus = make_bus(port)
    interval = 1.0 / hz
    previous: dict[str, int] | None = None

    try:
        bus.connect()
        while True:
            positions = bus.sync_read("Present_Position", normalize=False)
            print_positions_table(positions, previous)
            previous = positions
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")
        return 0
    except Exception as exc:
        print(f"\nDiagnostic failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


def main() -> int:
    args = parse_args()
    return run(port=args.port, hz=args.hz)


if __name__ == "__main__":
    raise SystemExit(main())
