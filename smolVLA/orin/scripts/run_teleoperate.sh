#!/usr/bin/env bash
set -euo pipefail

# Confirmed by lerobot-find-port (20260427): follower=serial 5B42138563, leader=serial 5B42138566
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
  all                 Run permission + both calibrations + teleoperate
  calibrate-follower  Run permission + follower calibration
  calibrate-leader    Run permission + leader calibration
  teleoperate         Run permission + teleoperate only
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
