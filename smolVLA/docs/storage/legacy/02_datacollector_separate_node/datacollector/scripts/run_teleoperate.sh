#!/usr/bin/env bash
set -euo pipefail

# DataCollector SO-ARM 텔레오퍼레이션 스크립트
# 출처: docs/storage/others/run_teleoperate.sh.archive (TODO-D2 최종 이관)
#
# 용도: DataCollector 노드에서 SO-ARM 리더·팔로워 캘리브레이션 + 텔레오퍼레이션 실행
# 실행 전제: .hylion_collector venv 활성화 상태
#   source ~/smolvla/datacollector/.hylion_collector/bin/activate
#
# 포트 확인: lerobot-find-port 로 실제 포트 확인 후 아래 변수 갱신
# 캐시 저장: 시연장 배치 후 datacollector/config/ports.json 에 저장 권장
#
# 이관 이력: docs/storage/others/run_teleoperate.sh.archive → 본 위치 (2026-05-01, TODO-D2)
# 원본 기록: 20260427 lerobot-find-port 확인 (follower=serial 5B42138563, leader=serial 5B42138566)

# Confirmed by lerobot-find-port (20260427): follower=serial 5B42138563, leader=serial 5B42138566
# 시연장 이동 시 lerobot-find-port 로 재확인 필요 (USB 순서 변동 가능)
FOLLOWER_PORT="/dev/ttyACM1"
LEADER_PORT="/dev/ttyACM0"
FOLLOWER_ID="my_awesome_follower_arm"
LEADER_ID="my_awesome_leader_arm"

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
  source ~/smolvla/datacollector/.hylion_collector/bin/activate
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
