#!/usr/bin/env bash
set -uo pipefail

# 양팔 동시 wave 재생
#   오른팔: wave_hello          (기본 FOLLOWER_PORT/ID)
#   왼팔:  wave_hello_2         (FOLLOWER_PORT=/dev/so_arm_left, ID=leftarm_test_follower)
#
# 사용:
#   bash ~/Hylion/jetson/arm/gestures/play_both_wave.sh
#
# Exit code:
#   0  양팔 모두 성공
#   1  한 쪽 이상 실패 (각 팔 rc 출력 참조)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAY="${SCRIPT_DIR}/play_gesture.sh"

RIGHT_GESTURE="wave_hello_2"
LEFT_GESTURE="wave_hello_2"

RIGHT_PORT="${RIGHT_FOLLOWER_PORT:-/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00}"
RIGHT_ID="${RIGHT_FOLLOWER_ID:-rightarm_test_follower}"
LEFT_PORT="${LEFT_FOLLOWER_PORT:-/dev/so_arm_left}"
LEFT_ID="${LEFT_FOLLOWER_ID:-leftarm_test_follower}"

echo "[both_wave] 오른팔(${RIGHT_GESTURE}) + 왼팔(${LEFT_GESTURE}) 동시 재생"

# 두 프로세스 병렬 실행
FOLLOWER_PORT="${RIGHT_PORT}" FOLLOWER_ID="${RIGHT_ID}" bash "${PLAY}" "${RIGHT_GESTURE}" &
PID_RIGHT=$!

FOLLOWER_PORT="${LEFT_PORT}"  FOLLOWER_ID="${LEFT_ID}"  bash "${PLAY}" "${LEFT_GESTURE}" &
PID_LEFT=$!

# 둘 다 완료 대기
wait "${PID_RIGHT}"; RC_RIGHT=$?
wait "${PID_LEFT}";  RC_LEFT=$?

echo "[both_wave] 오른팔 rc=${RC_RIGHT}  왼팔 rc=${RC_LEFT}"

if [ "${RC_RIGHT}" -eq 0 ] && [ "${RC_LEFT}" -eq 0 ]; then
    exit 0
else
    exit 1
fi
