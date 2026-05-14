#!/usr/bin/env bash
set -uo pipefail

# Jetson(Orin) gesture replay 사전 점검 (dry-run)
# 자매: play_gesture.sh
# 가이드: dgx/docs/gestures.md, dgx/docs/gestures_jetson_setup_prompt.md §5-4
#
# 용도: play_gesture.sh 가 lerobot-replay 호출 전 수행하는 pre-check 5단계를
#       독립 실행 가능하게 분리. play_gesture.sh 가 내부에서 그대로 호출.
#       실제 모터 구동 X — 환경 / 데이터 / 캘리브 / 포트 존재만 확인.
#
# Exit code (gestures_jetson_setup_prompt.md §5-1 매핑):
#   0  모든 점검 통과
#   2  인자 / gesture_name 형식 오류
#   3  venv / lerobot 환경 문제
#   4  gesture 데이터 / 캘리브레이션 미존재
#   5  하드웨어 (포트) 문제
#
# env override (hardcoded 는 기본값):
#   FOLLOWER_PORT        우측 follower 시리얼 by-id 경로 (재부팅에도 안정)
#   FOLLOWER_ID          캘리브 파일 이름 = robot.id
#   ORIN_GESTURES_ROOT   sync 받은 gesture 데이터 루트
#   JETSON_VENV          추론 venv (lerobot-replay 제공)
#   HF_HOME              미설정 시 ~/.cache/huggingface (Jetson 기본 — 캘리브 경로 root)

FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00}"
FOLLOWER_ID="${FOLLOWER_ID:-rightarm_test_follower}"
# gesture 데이터는 Hylion 레포 안으로 복사됨 (smolvla/orin/gestures 원본 유지).
ORIN_GESTURES_ROOT="${ORIN_GESTURES_ROOT:-${HOME}/Hylion/smolVLA/gestures}"
# lerobot 0.5.2 venv 는 5.3GB — 복제하지 않고 기존 것을 그대로 재사용한다.
JETSON_VENV="${JETSON_VENV:-${HOME}/smolvla/orin/.hylion_arm}"

usage() {
  cat <<EOF
Usage: check_gesture_ready.sh <gesture_name>

Jetson gesture replay 사전 점검 (모터 구동 X).

Args:
  gesture_name   필수. snake_case (^[a-z][a-z0-9_]*\$).

Exit: 0=OK, 2=인자오류, 3=환경, 4=데이터/캘리브, 5=포트

env override: FOLLOWER_PORT, FOLLOWER_ID, ORIN_GESTURES_ROOT, JETSON_VENV, HF_HOME
EOF
}

# ── 1. 인자 검증 ─────────────────────────────────────────────────────────────
if [ "$#" -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 2
fi

GESTURE_NAME="$1"
if ! echo "${GESTURE_NAME}" | grep -qE '^[a-z][a-z0-9_]*$'; then
  echo "[check] ERROR: gesture_name '${GESTURE_NAME}' 형식 오류 (^[a-z][a-z0-9_]*\$)" >&2
  exit 2
fi

# ── 2. venv activate (이미 활성이면 skip) ────────────────────────────────────
if [ -z "${VIRTUAL_ENV:-}" ]; then
  if [ ! -f "${JETSON_VENV}/bin/activate" ]; then
    echo "[check] ERROR: venv 없음: ${JETSON_VENV}/bin/activate" >&2
    echo "  orin/scripts/setup_env.sh 선행 필요" >&2
    exit 3
  fi
  set +u
  # shellcheck source=/dev/null
  source "${JETSON_VENV}/bin/activate"
  set -u
fi

# ── 3. replay_gesture.py + pyarrow 존재 ──────────────────────────────────────
# lerobot-replay CLI 는 lerobot.datasets(curated subset 에 없음) 의존이라 쓰지
# 않는다. 대신 자체 스크립트 replay_gesture.py + parquet 리더(pyarrow) 를 점검.
CHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "${CHECK_DIR}/replay_gesture.py" ]; then
  echo "[check] ERROR: replay_gesture.py 없음: ${CHECK_DIR}/replay_gesture.py" >&2
  exit 3
fi
if ! python -c "import pyarrow" >/dev/null 2>&1; then
  echo "[check] ERROR: pyarrow import 실패 (venv 활성 / 'pip install pyarrow' 확인)" >&2
  exit 3
fi

# ── 4. gesture 데이터 존재 ───────────────────────────────────────────────────
INFO_JSON="${ORIN_GESTURES_ROOT}/${GESTURE_NAME}/meta/info.json"
if [ ! -f "${INFO_JSON}" ]; then
  echo "[check] ERROR: gesture 데이터 없음: ${INFO_JSON}" >&2
  echo "  DGX 에서 sync 선행: bash dgx/scripts/sync_gesture_to_orin.sh ${GESTURE_NAME}" >&2
  exit 4
fi

# ── 5. follower 캘리브레이션 존재 ────────────────────────────────────────────
# Jetson 은 HF_HOME 미설정 → lerobot 이 ~/.cache/huggingface 사용 (검증 완료 2026-05-14)
HF_BASE="${HF_HOME:-${HOME}/.cache/huggingface}"
CALIB_FOLLOWER="${HF_BASE}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json"
if [ ! -f "${CALIB_FOLLOWER}" ]; then
  echo "[check] ERROR: follower 캘리브레이션 없음: ${CALIB_FOLLOWER}" >&2
  echo "  DGX 에서 sync 선행: bash dgx/scripts/sync_gesture_to_orin.sh ${GESTURE_NAME}" >&2
  exit 4
fi

# ── 6. follower 시리얼 포트 존재 ─────────────────────────────────────────────
if [ ! -e "${FOLLOWER_PORT}" ]; then
  echo "[check] ERROR: follower 포트 없음: ${FOLLOWER_PORT}" >&2
  echo "  우측 follower USB 가 Jetson 에 연결됐는지 확인 (lerobot-find-port)" >&2
  exit 5
fi

echo "[check] OK  gesture=${GESTURE_NAME}  port=${FOLLOWER_PORT}  id=${FOLLOWER_ID}"
exit 0
