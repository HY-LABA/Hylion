#!/usr/bin/env python3
# DGX SO-ARM wrist_roll raw 위치 실시간 표시 (read-only)
# 자매: calibrate_wrist_roll.py, run_teleoperate.sh
# 가이드: dgx/docs/gestures.md
#
# 용도:
#   wrist_roll 은 인코더 wraparound (2400→4095→0→1800) 가 있고 그 사이 (1800,2400)
#   이 dead zone (mech stop). gesture 녹화 시 wrist_roll 을 dead zone 밖 안전 위치
#   (예: raw 1800) 에 고정해야 overload 안 남.
#   본 스크립트는 wrist_roll 의 raw 인코더 값을 실시간 출력해, 손으로 follower 의
#   wrist_roll 을 안전 위치에 맞춰놓고 물리적 방향을 확인하는 용도.
#
#   read-only: torque 끄고 위치만 읽음. 모터 구동 X.
#
# 의존: source ~/smolvla/dgx/.arm_finetune/bin/activate
#
# 사용:
#   FOLLOWER_PORT=/dev/serial/by-id/...5AE6082773-if00 \
#     python dgx/scripts/read_wrist_roll.py follower
#   LEADER_PORT=/dev/serial/by-id/...5AE6056701-if00 \
#     python dgx/scripts/read_wrist_roll.py leader
#
# env override:
#   FOLLOWER_PORT / LEADER_PORT  (필수)
#   FOLLOWER_ID  (기본: rightarm_test_follower)
#   LEADER_ID    (기본: rightarm_test_leader)
#
# Ctrl+C 로 종료.

import os
import sys
import time

ARM = sys.argv[1] if len(sys.argv) > 1 else None
if ARM not in ("follower", "leader"):
    print("Usage: read_wrist_roll.py [follower|leader]", file=sys.stderr)
    sys.exit(2)

if ARM == "follower":
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    port = os.environ.get("FOLLOWER_PORT")
    dev_id = os.environ.get("FOLLOWER_ID", "rightarm_test_follower")
    if not port:
        print("[read] ERROR: FOLLOWER_PORT env 미설정", file=sys.stderr)
        sys.exit(2)
    device = SO101Follower(SO101FollowerConfig(port=port, id=dev_id, use_degrees=True))
else:
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

    port = os.environ.get("LEADER_PORT")
    dev_id = os.environ.get("LEADER_ID", "rightarm_test_leader")
    if not port:
        print("[read] ERROR: LEADER_PORT env 미설정", file=sys.stderr)
        sys.exit(2)
    device = SO101Leader(SO101LeaderConfig(port=port, id=dev_id, use_degrees=True))

print(f"[read] {ARM}  id={dev_id}  port={port}")
device.bus.connect()
try:
    device.bus.disable_torque("wrist_roll")
    print("[read] wrist_roll torque OFF — 손으로 돌려보세요. Ctrl+C 로 종료.")
    print("[read] dead zone (1800,2400) 회피. 안전 위치 목표: raw 1800 근처")
    print()
    while True:
        raw = device.bus.read("Present_Position", "wrist_roll", normalize=False)
        in_dead = 1800 < raw < 2400
        flag = "  <-- DEAD ZONE!" if in_dead else ""
        print(f"\r  wrist_roll raw = {raw:>5}{flag}        ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[read] 종료")
finally:
    try:
        device.bus.disconnect()
    except Exception as e:
        print(f"[read] disconnect 경고 (무시 가능): {e}", file=sys.stderr)
