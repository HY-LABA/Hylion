#!/usr/bin/env python3
# DGX SO-ARM wrist_roll 실제 mech 범위 캘리브 → 캘리브 JSON 패치
# 자매: run_teleoperate.sh, record_gesture.sh
# 가이드: dgx/docs/gestures.md
#
# 용도:
#   lerobot 의 lerobot-calibrate 는 wrist_roll 을 full-turn 관절로 하드코딩
#   (so_follower.py / so_leader.py: range_min=0, range_max=4095 고정).
#   하지만 본 SO-ARM 의 wrist_roll 은 전선 때문에 ~350° 에서 막히는 실제 한계가 있음.
#   range 를 0-4095 로 두면 teleop/replay 시 leader↔follower 의 homing_offset 차이로
#   follower wrist_roll 이 물리 한계 너머로 명령받아 mech stop 에 밀림 → overload error.
#
#   본 스크립트는 wrist_roll 만 골라 record_ranges_of_motion 으로 실제 한계를 기록한 뒤,
#   기존 캘리브 JSON 의 wrist_roll.range_min / range_max 두 값만 패치한다.
#   (lerobot upstream 무수정 원칙 — JSON 은 우리 산출물이라 수정 OK)
#
# 의존: source ~/smolvla/dgx/.arm_finetune/bin/activate
# 전제: 대상 팔 lerobot-calibrate 선행 (JSON 이 이미 존재해야 함)
#       wrist_roll 모터가 overload state 가 아니어야 함 (필요시 follower 보드 power cycle)
#
# 사용:
#   FOLLOWER_PORT=/dev/serial/by-id/...5AE6082773-if00 \
#     python dgx/scripts/calibrate_wrist_roll.py follower
#   LEADER_PORT=/dev/serial/by-id/...5AE6056701-if00 \
#     python dgx/scripts/calibrate_wrist_roll.py leader
#
# env override:
#   FOLLOWER_PORT / LEADER_PORT  (필수)
#   FOLLOWER_ID  (기본: rightarm_test_follower)
#   LEADER_ID    (기본: rightarm_test_leader)

import json
import os
import sys

ARM = sys.argv[1] if len(sys.argv) > 1 else None
if ARM not in ("follower", "leader"):
    print("Usage: calibrate_wrist_roll.py [follower|leader]", file=sys.stderr)
    sys.exit(2)

if ARM == "follower":
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    port = os.environ.get("FOLLOWER_PORT")
    dev_id = os.environ.get("FOLLOWER_ID", "rightarm_test_follower")
    if not port:
        print("[wrist_roll] ERROR: FOLLOWER_PORT env 미설정", file=sys.stderr)
        sys.exit(2)
    device = SO101Follower(SO101FollowerConfig(port=port, id=dev_id, use_degrees=True))
else:
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

    port = os.environ.get("LEADER_PORT")
    dev_id = os.environ.get("LEADER_ID", "rightarm_test_leader")
    if not port:
        print("[wrist_roll] ERROR: LEADER_PORT env 미설정", file=sys.stderr)
        sys.exit(2)
    device = SO101Leader(SO101LeaderConfig(port=port, id=dev_id, use_degrees=True))

fpath = device.calibration_fpath
if not fpath.is_file():
    print(f"[wrist_roll] ERROR: 캘리브 파일 없음: {fpath}", file=sys.stderr)
    print("  먼저 lerobot-calibrate 수행 (run_teleoperate.sh calibrate-*)", file=sys.stderr)
    sys.exit(4)

print(f"[wrist_roll] {ARM}  id={dev_id}")
print(f"[wrist_roll] port={port}")
print(f"[wrist_roll] 캘리브 파일: {fpath}")

device.bus.connect()
try:
    # wrist_roll 만 torque off → 손으로 회전 가능. 나머지 관절은 torque 유지 (팔 안정).
    device.bus.disable_torque("wrist_roll")
    print()
    print("=" * 58)
    print(" wrist_roll 을 한쪽 mech 한계 → 반대쪽 한계까지 천천히 회전")
    print(" (전선 때문에 더 안 돌아가는 그 지점까지). 양끝 다 찍은 후 ENTER")
    print("=" * 58)
    print()
    mins, maxes = device.bus.record_ranges_of_motion(["wrist_roll"])
finally:
    try:
        device.bus.disconnect()
    except Exception as e:
        print(f"[wrist_roll] disconnect 경고 (무시 가능): {e}", file=sys.stderr)

rmin = int(mins["wrist_roll"])
rmax = int(maxes["wrist_roll"])
width = rmax - rmin
print(f"\n[wrist_roll] 기록된 범위: range_min={rmin}, range_max={rmax} (폭 {width})")

# 너무 좁으면 (양끝까지 안 움직였을 가능성) 패치 거부
if width < 100:
    print("[wrist_roll] ERROR: 범위가 너무 좁음 — 양쪽 한계까지 회전 안 됐을 수 있음.", file=sys.stderr)
    print("  JSON 패치 안 함. 재시도 권장.", file=sys.stderr)
    sys.exit(1)

with open(fpath) as f:
    calib = json.load(f)

if "wrist_roll" not in calib:
    print(f"[wrist_roll] ERROR: JSON 에 wrist_roll 항목 없음: {fpath}", file=sys.stderr)
    sys.exit(4)

old_min = calib["wrist_roll"]["range_min"]
old_max = calib["wrist_roll"]["range_max"]
calib["wrist_roll"]["range_min"] = rmin
calib["wrist_roll"]["range_max"] = rmax

with open(fpath, "w") as f:
    json.dump(calib, f, indent=4)

print(f"[wrist_roll] 패치 완료: {old_min}-{old_max} → {rmin}-{rmax}")
print(f"[wrist_roll] 저장: {fpath}")
