#!/usr/bin/env bash
set -euo pipefail

# DGX SO-ARM gesture trajectory 녹화 (lerobot-record wrapper)
# 자매: run_teleoperate.sh, push_dataset_hub.sh
# 가이드: dgx/docs/gestures.md
#
# 용도: SmolVLA / ACT 학습 데이터와 별개로 짧은 단일 episode trajectory 녹화 →
#       Jetson 에서 lerobot-replay 로 재생 (트리거 기반 고정 동작).
#
# 핵심 결정:
#   - 카메라 / 비디오 완전 제외 (motors only) — 학습 dataset 과의 차이
#   - push_to_hub=false (로컬 전용)
#   - 1 episode / short duration (기본 5s)
#   - 별도 root 디렉토리 (gestures/ — leftarm_v1 와 격리)
#
# 의존: source ~/smolvla/dgx/.arm_finetune/bin/activate
# 캘리브레이션: lerobot-record 가 ${FOLLOWER_ID} / ${LEADER_ID} 로 자동 로드.
#               미존재 시 lerobot-calibrate 선행 (run_teleoperate.sh 참조)

# ── 기본값 (env override 가능) ────────────────────────────────────────────────
# 본 시스템은 ⓞ우측 팔 전담 (좌측은 SmolVLA / leftarm_v1 전담 — gestures.md §0-1).
# 4 devices 환경 (좌·우 follower + 좌·우 leader) 이라 USB enumeration 변동 가능.
# 첫 사용 / 시연장 이동 / 리부팅 시 lerobot-find-port 로 우측 팔 포트 재확인 후 export 필수.
#
# 2026-05-11 확인 (좌측 팔만 연결된 시점, 우측 미배치):
#   left follower=ACM0 (serial 5B42138563), left leader=ACM1 (serial 5B42138566)
# 우측 팔 추가 후 포트는 아직 미확인 — lerobot-find-port 필요.
FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM2}"
LEADER_PORT="${LEADER_PORT:-/dev/ttyACM3}"
FOLLOWER_ID="${FOLLOWER_ID:-rightarm_test_follower}"
LEADER_ID="${LEADER_ID:-rightarm_test_leader}"

GESTURES_ROOT="${HOME}/smolvla/dgx/gestures"

usage() {
  cat <<EOF
Usage: record_gesture.sh <gesture_name> [duration_s]

단일 episode teleoperation trajectory 녹화 (lerobot-replay 용).

Args:
  gesture_name   필수. snake_case (wave_hello, bow_short, ...).
                 repo_id = local/<gesture_name>
                 저장 = ${GESTURES_ROOT}/<gesture_name>/
  duration_s     선택, 기본 5. episode 최대 길이 (초). →키로 조기 종료 가능.

키 조작 (lerobot-record 표준):
  →   현재 episode 종료 후 저장
  ←   현재 episode 폐기 → 재시도
  Esc 전체 안전 종료

전제:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  (USB 변동 시) lerobot-find-port

환경변수 override:
  FOLLOWER_PORT, LEADER_PORT, FOLLOWER_ID, LEADER_ID

예시:
  bash $(basename "$0") wave_hello
  bash $(basename "$0") bow_short 3
  FOLLOWER_PORT=/dev/ttyACM2 bash $(basename "$0") wave_hello
EOF
}

# ── 인자 파싱 ─────────────────────────────────────────────────────────────────
if [ "$#" -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

GESTURE_NAME="$1"
DURATION_S="${2:-5}"

# gesture name 형식 검증 (snake_case, no slash, no spaces)
if ! echo "${GESTURE_NAME}" | grep -qE '^[a-z][a-z0-9_]*$'; then
  echo "[gesture] ERROR: gesture_name '${GESTURE_NAME}' 형식 오류." >&2
  echo "  요구: 소문자 / 숫자 / 언더스코어, 첫 글자 소문자 (예: wave_hello)" >&2
  exit 2
fi

# duration 정수 검증 (1~60)
if ! echo "${DURATION_S}" | grep -qE '^[0-9]+$' || [ "${DURATION_S}" -lt 1 ] || [ "${DURATION_S}" -gt 60 ]; then
  echo "[gesture] ERROR: duration_s '${DURATION_S}' — 1~60 정수만 허용" >&2
  exit 2
fi

GESTURE_DIR="${GESTURES_ROOT}/${GESTURE_NAME}"

# ── pre-check: lerobot-record 존재 ───────────────────────────────────────────
if ! command -v lerobot-record >/dev/null 2>&1; then
  echo "[gesture] ERROR: lerobot-record 명령 없음." >&2
  echo "  venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate" >&2
  exit 3
fi

# ── pre-check: 출력 디렉토리 중복 ─────────────────────────────────────────────
if [ -d "${GESTURE_DIR}" ]; then
  echo "[gesture] ERROR: ${GESTURE_DIR} 이미 존재." >&2
  echo "  - 덮어쓰기 원하면: rm -rf '${GESTURE_DIR}' 후 재실행" >&2
  echo "  - 다른 이름 사용: bash $0 <other_name>" >&2
  exit 4
fi

# ── pre-check: 캘리브레이션 파일 존재 ─────────────────────────────────────────
HF_HOME_DEFAULT="${HF_HOME:-${HOME}/smolvla/.hf_cache}"
CALIB_FOLLOWER="${HF_HOME_DEFAULT}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json"
CALIB_LEADER="${HF_HOME_DEFAULT}/lerobot/calibration/teleoperators/so_leader/${LEADER_ID}.json"

if [ ! -f "${CALIB_FOLLOWER}" ]; then
  echo "[gesture] WARN: follower 캘리브레이션 미존재:" >&2
  echo "  ${CALIB_FOLLOWER}" >&2
  echo "  → 사전 캘리브: bash scripts/run_teleoperate.sh calibrate-follower" >&2
fi
if [ ! -f "${CALIB_LEADER}" ]; then
  echo "[gesture] WARN: leader 캘리브레이션 미존재:" >&2
  echo "  ${CALIB_LEADER}" >&2
  echo "  → 사전 캘리브: bash scripts/run_teleoperate.sh calibrate-leader" >&2
fi

# ── pre-check: 시리얼 포트 존재 ──────────────────────────────────────────────
if [ ! -e "${FOLLOWER_PORT}" ]; then
  echo "[gesture] ERROR: follower port ${FOLLOWER_PORT} 없음. lerobot-find-port 로 재확인 후 FOLLOWER_PORT export" >&2
  exit 5
fi
if [ ! -e "${LEADER_PORT}" ]; then
  echo "[gesture] ERROR: leader port ${LEADER_PORT} 없음. lerobot-find-port 로 재확인 후 LEADER_PORT export" >&2
  exit 5
fi

# ── 안내 ─────────────────────────────────────────────────────────────────────
cat <<EOF
==========================================================
 record_gesture
==========================================================
  gesture name : ${GESTURE_NAME}
  duration max : ${DURATION_S}s (→키로 조기 종료 가능)
  output       : ${GESTURE_DIR}/
  follower     : ${FOLLOWER_PORT}  (id: ${FOLLOWER_ID})
  leader       : ${LEADER_PORT}    (id: ${LEADER_ID})
  HF_HOME      : ${HF_HOME_DEFAULT}
==========================================================

권장 절차:
  1. follower 를 자연스러운 'home pose' 로 두기
     (replay 시점도 같은 자세 시작 — 첫 프레임 점프 방지)
  2. 비프 / "Recording" 안내 들리면 leader 로 동작 시연
  3. 동작 끝나면 → 키 (오른쪽 화살표) 로 episode 종료
  4. 만족스러우면 그대로 종료. 재시도는 ← 키 또는 Esc 후 본 스크립트 재실행
     (단, 재실행 전 ${GESTURE_DIR} 삭제 필요)

== 시작 ==

EOF

# ── lerobot-record 실행 ──────────────────────────────────────────────────────
# - 카메라 인자 없음 → motor only dataset
# - dataset.video=false → 비디오 디렉토리 생성 X
# - dataset.push_to_hub=false → 로컬 전용
# - num_episodes=1, reset_time_s=0 → 단일 episode, reset 단계 스킵
lerobot-record \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}" \
  --dataset.repo_id="local/${GESTURE_NAME}" \
  --dataset.root="${GESTURE_DIR}" \
  --dataset.single_task="Gesture: ${GESTURE_NAME}" \
  --dataset.num_episodes=1 \
  --dataset.fps=30 \
  --dataset.episode_time_s="${DURATION_S}" \
  --dataset.reset_time_s=0 \
  --dataset.video=false \
  --dataset.push_to_hub=false \
  --display_data=false \
  --play_sounds=true

# ── 사후 확인 ────────────────────────────────────────────────────────────────
echo ""
if [ -f "${GESTURE_DIR}/meta/info.json" ]; then
  echo "[gesture] 녹화 완료:"
  if command -v jq >/dev/null 2>&1; then
    jq '{total_episodes, total_frames, fps}' "${GESTURE_DIR}/meta/info.json"
  fi
  echo ""
  echo "다음 단계:"
  echo "  1. (선택) DGX 에서 trajectory 검증 — 사람·물체 없는 빈 공간에서:"
  echo "     lerobot-replay \\"
  echo "       --robot.type=so101_follower \\"
  echo "       --robot.port=${FOLLOWER_PORT} \\"
  echo "       --robot.id=${FOLLOWER_ID} \\"
  echo "       --dataset.repo_id=local/${GESTURE_NAME} \\"
  echo "       --dataset.root=${GESTURE_DIR} \\"
  echo "       --dataset.episode=0"
  echo ""
  echo "  2. Jetson 동기화 (gestures.md §6 참조):"
  echo "     bash scripts/sync_gesture_to_orin.sh ${GESTURE_NAME}"
else
  echo "[gesture] WARN: ${GESTURE_DIR}/meta/info.json 없음 — 녹화 미완 또는 실패."
fi
