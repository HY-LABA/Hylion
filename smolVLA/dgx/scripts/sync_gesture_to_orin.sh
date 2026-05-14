#!/usr/bin/env bash
set -euo pipefail

# DGX → Jetson(Orin) gesture trajectory + follower 캘리브레이션 동기화
# 자매: record_gesture.sh
# 가이드: dgx/docs/gestures.md §6
#
# 용도: DGX 에서 녹화한 gesture trajectory + 해당 캘리브레이션 JSON 을
#       Jetson 의 동일 경로 구조로 rsync. Jetson 측은 동기화 후 곧바로
#       lerobot-replay 사용 가능.
#
# 중요: Jetson 측 환경 (사용자 / venv / HF_HOME 경로) 은 사전에 한 번 확인하여
#       ORIN_HF_HOME / ORIN_GESTURES_ROOT 를 export. 기본 placeholder 검증으로
#       미설정 시 명시적 에러.

# ── DGX 측 경로 ─────────────────────────────────────────────────────────────
GESTURES_ROOT="${HOME}/smolvla/dgx/gestures"
HF_HOME_DEFAULT="${HF_HOME:-${HOME}/smolvla/.hf_cache}"

# ── Jetson 측 경로 (env override 필수) ───────────────────────────────────────
# ORIN_HOST : ssh alias (~/.ssh/config 에 'Host orin' 정의 권장)
# ORIN_HF_HOME : Jetson 의 HF_HOME (Jetson agent 측 setup 결과)
# ORIN_GESTURES_ROOT : Jetson 의 gesture 데이터 저장 루트
ORIN_HOST="${ORIN_HOST:-orin}"
ORIN_HF_HOME="${ORIN_HF_HOME:-PLEASE_SET_ORIN_HF_HOME}"
ORIN_GESTURES_ROOT="${ORIN_GESTURES_ROOT:-PLEASE_SET_ORIN_GESTURES_ROOT}"

FOLLOWER_ID="${FOLLOWER_ID:-rightarm_test_follower}"

usage() {
  cat <<EOF
Usage: sync_gesture_to_orin.sh <gesture_name>

DGX 에 녹화된 gesture trajectory + follower 캘리브레이션 파일을 Jetson 에 rsync.

Args:
  gesture_name   필수. ${GESTURES_ROOT}/<gesture_name>/ 존재 가정.

환경변수 (Jetson 환경 확인 후 사전 export 필수):
  ORIN_HOST              SSH alias 또는 'user@host' (기본: orin)
  ORIN_HF_HOME           Jetson 의 HF_HOME 경로 (예: /home/laba/smolvla/.hf_cache)
  ORIN_GESTURES_ROOT     Jetson 의 gesture 데이터 루트 (예: /home/laba/smolvla/orin/gestures)
  FOLLOWER_ID            캘리브레이션 파일 이름 (기본: rightarm_test_follower — gesture 우측 팔 전담)

전송 항목:
  1) ${GESTURES_ROOT}/<name>/
     → \${ORIN_HOST}:\${ORIN_GESTURES_ROOT}/<name>/
  2) \${HF_HOME}/lerobot/calibration/robots/so_follower/\${FOLLOWER_ID}.json
     → \${ORIN_HOST}:\${ORIN_HF_HOME}/lerobot/calibration/robots/so_follower/

예시 (Jetson 측 사용자가 laba, 동일 디렉토리 컨벤션 사용):
  export ORIN_HOST=orin
  export ORIN_HF_HOME=/home/laba/smolvla/.hf_cache
  export ORIN_GESTURES_ROOT=/home/laba/smolvla/orin/gestures
  bash $(basename "$0") wave_hello
EOF
}

# ── 인자 파싱 ────────────────────────────────────────────────────────────────
if [ "$#" -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

GESTURE_NAME="$1"
GESTURE_DIR="${GESTURES_ROOT}/${GESTURE_NAME}"
CALIB_FOLLOWER="${HF_HOME_DEFAULT}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json"

# ── pre-check ───────────────────────────────────────────────────────────────
if [ ! -d "${GESTURE_DIR}" ]; then
  echo "[sync] ERROR: ${GESTURE_DIR} 디렉터리 없음 — 녹화 먼저 수행하세요." >&2
  echo "  bash scripts/record_gesture.sh ${GESTURE_NAME}" >&2
  exit 2
fi

if [ ! -f "${CALIB_FOLLOWER}" ]; then
  echo "[sync] ERROR: follower 캘리브레이션 ${CALIB_FOLLOWER} 없음." >&2
  echo "  bash scripts/run_teleoperate.sh calibrate-follower" >&2
  exit 3
fi

if [ "${ORIN_HF_HOME}" = "PLEASE_SET_ORIN_HF_HOME" ] || [ "${ORIN_GESTURES_ROOT}" = "PLEASE_SET_ORIN_GESTURES_ROOT" ]; then
  echo "[sync] ERROR: ORIN_HF_HOME / ORIN_GESTURES_ROOT 미설정." >&2
  echo "  Jetson 환경 확인 후:" >&2
  echo "    export ORIN_HOST=orin" >&2
  echo "    export ORIN_HF_HOME=/home/<user>/smolvla/.hf_cache" >&2
  echo "    export ORIN_GESTURES_ROOT=/home/<user>/smolvla/orin/gestures" >&2
  exit 4
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "[sync] ERROR: rsync 명령 없음. sudo apt install rsync" >&2
  exit 5
fi

# ── 안내 ─────────────────────────────────────────────────────────────────────
cat <<EOF
==========================================================
 sync_gesture_to_orin
==========================================================
  gesture        : ${GESTURE_NAME}
  source dir     : ${GESTURE_DIR}/
  target dir     : ${ORIN_HOST}:${ORIN_GESTURES_ROOT}/${GESTURE_NAME}/
  calib source   : ${CALIB_FOLLOWER}
  calib target   : ${ORIN_HOST}:${ORIN_HF_HOME}/lerobot/calibration/robots/so_follower/
==========================================================

EOF

# ── SSH 도달성 확인 ──────────────────────────────────────────────────────────
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${ORIN_HOST}" true 2>/dev/null; then
  echo "[sync] ERROR: ${ORIN_HOST} 에 SSH 접근 실패." >&2
  echo "  ~/.ssh/config 또는 ssh-copy-id 로 사전 설정 필요." >&2
  exit 6
fi

# ── 1) gesture dataset rsync ────────────────────────────────────────────────
echo "[sync] (1/2) gesture dataset rsync ..."
ssh "${ORIN_HOST}" "mkdir -p '${ORIN_GESTURES_ROOT}'"
rsync -av --delete \
  "${GESTURE_DIR}/" \
  "${ORIN_HOST}:${ORIN_GESTURES_ROOT}/${GESTURE_NAME}/"

# ── 2) calibration JSON rsync ───────────────────────────────────────────────
echo ""
echo "[sync] (2/2) follower calibration rsync ..."
ssh "${ORIN_HOST}" "mkdir -p '${ORIN_HF_HOME}/lerobot/calibration/robots/so_follower'"
rsync -av \
  "${CALIB_FOLLOWER}" \
  "${ORIN_HOST}:${ORIN_HF_HOME}/lerobot/calibration/robots/so_follower/"

echo ""
echo "[sync] 완료. Jetson 측 다음 단계:"
echo "  ssh ${ORIN_HOST}"
echo "  source <jetson_venv>/bin/activate"
echo "  lerobot-replay \\"
echo "    --robot.type=so101_follower \\"
echo "    --robot.port=\${FOLLOWER_PORT} \\"
echo "    --robot.id=${FOLLOWER_ID} \\"
echo "    --dataset.repo_id=local/${GESTURE_NAME} \\"
echo "    --dataset.root=${ORIN_GESTURES_ROOT}/${GESTURE_NAME} \\"
echo "    --dataset.episode=0"
echo ""
echo "Jetson 측 wrapper / trigger 통합은 dgx/docs/gestures_jetson_setup_prompt.md 참조."
