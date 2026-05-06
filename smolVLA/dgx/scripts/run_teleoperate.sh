#!/usr/bin/env bash
set -euo pipefail

# DGX SO-ARM 텔레오퍼레이션 스크립트
# 원본: docs/storage/legacy/02_datacollector_separate_node/datacollector/scripts/run_teleoperate.sh
# 이식: 06_dgx_absorbs_datacollector TODO-X3 (2026-05-02)
#
# 변경 항목:
#   - venv 경로: ~/smolvla/datacollector/.hylion_collector → ~/smolvla/dgx/.arm_finetune
#   - 실행 전제 주석 및 usage 경로 갱신
#   - lerobot-calibrate / lerobot-teleoperate CLI 인자: 원본 그대로 (SO-ARM 구성 동일)
#
# 용도: DGX 노드에서 SO-ARM 리더·팔로워 캘리브레이션 + 텔레오퍼레이션 실행
# 실행 전제: .arm_finetune venv 활성화 상태
#   source ~/smolvla/dgx/.arm_finetune/bin/activate
#
# 포트 확인: lerobot-find-port 로 실제 포트 확인 후 아래 변수 갱신
# 캐시 저장: 시연장 배치 후 dgx/config/ports.json 에 저장 권장
#
# 이관 이력:
#   datacollector/scripts/run_teleoperate.sh → 본 위치 (2026-05-02, TODO-X3)
# 원본 기록:
#   20260427 lerobot-find-port 확인 (follower=serial 5B42138563, leader=serial 5B42138566)

# Confirmed by lerobot-find-port (20260427): follower=serial 5B42138563, leader=serial 5B42138566
# 시연장 이동 시 lerobot-find-port 로 재확인 필요 (USB 순서 변동 가능)
FOLLOWER_PORT="/dev/ttyACM1"
LEADER_PORT="/dev/ttyACM0"
# C0d: 환경변수 우선, hardcoded fallback (calibration.json 미존재 시)
# teleop.py flow3_teleoperate 가 calibration.json 로드 후 FOLLOWER_ID / LEADER_ID 주입.
# lerobot calibration 파일명 = robot.id → ID 정합이 calibration 정합.
FOLLOWER_ID="${FOLLOWER_ID:-my_awesome_follower_arm}"
LEADER_ID="${LEADER_ID:-my_awesome_leader_arm}"

calibrate_follower() {
  echo "[1/3] Calibrating follower on ${FOLLOWER_PORT}"
  lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id="${FOLLOWER_ID}"
}

calibrate_leader() {
  echo "[2/3] Calibrating leader on ${LEADER_PORT}"
  lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port="${LEADER_PORT}" \
    --teleop.id="${LEADER_ID}"
}

teleoperate() {
  echo "[3/3] Starting teleoperation"
  lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.id="${FOLLOWER_ID}" \
    --teleop.type=so101_leader \
    --teleop.port="${LEADER_PORT}" \
    --teleop.id="${LEADER_ID}"
}

usage() {
  cat <<'EOF'
Usage: run_teleoperate.sh [all|calibrate-follower|calibrate-leader|teleoperate]

Commands:
  all                 Run both calibrations + teleoperate
  calibrate-follower  Run follower calibration
  calibrate-leader    Run leader calibration
  teleoperate         Run teleoperate only

Prerequisites:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  lerobot-find-port  (시연장 이동 시 포트 재확인)
EOF
}

main() {
  local cmd="${1:-all}"

  case "${cmd}" in
    all)
      calibrate_follower
      calibrate_leader
      teleoperate
      ;;
    calibrate-follower)
      calibrate_follower
      ;;
    calibrate-leader)
      calibrate_leader
      ;;
    teleoperate)
      teleoperate
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "Unknown command: ${cmd}" >&2
      usage
      exit 2
      ;;
  esac
}

main "$@"
