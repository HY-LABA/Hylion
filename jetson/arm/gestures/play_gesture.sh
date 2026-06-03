#!/usr/bin/env bash
set -uo pipefail

# Jetson(Orin) gesture replay wrapper — trigger 시스템의 진입점
# 자매: check_gesture_ready.sh
# 가이드: dgx/docs/gestures.md, dgx/docs/gestures_jetson_setup_prompt.md §5
#
# 용도: DGX 에서 녹화·sync 된 gesture trajectory 를 lerobot-replay 로 재생.
#       coordinator.py 등 트리거 시스템이 `play_gesture.sh <name>` 한 줄로 호출.
#       VLA/ACT 추론 없음 — LeRobotDataset 의 action 컬럼을 fps 맞춰 send_action.
#       우측 follower 전담 (좌측 SmolVLA inference 와 USB 포트 분리, mutex 무관).
#
# Exit code (gestures_jetson_setup_prompt.md §5-1):
#   0  재생 성공 (disconnect overload 'cosmetic' 케이스 포함 — 아래 참조)
#   2  인자 / 형식 오류
#   3  venv / lerobot 환경 문제
#   4  gesture 데이터 / 캘리브레이션 미존재
#   5  하드웨어 (포트 / 권한) 문제
#   1  기타 (lerobot-replay 내부 실패 — 실제 재생 실패)
#
# Stdout: 한 줄 요약 (gesture, frames, elapsed, rc)
# Stderr: 에러 / 경고
#
# ── disconnect overload 'cosmetic' 처리 (본 프로젝트 특이사항) ────────────────
# SO-ARM Feetech 모터는 동작 정상 완료 후 robot.disconnect() → disable_torque
# 단계에서 모터의 overload error register 가 set 돼 있으면 lerobot 이 이를
# write 실패로 해석해 non-zero exit. 하지만 trajectory 재생 자체는 이미 완료됨.
# → 출력에 "Replaying episode" + "Overload error" + "in disconnect" 가 함께
#   보이면 cosmetic 으로 분류해 exit 0 (경고만). 그 외 non-zero 는 실패(exit 1).
#   coordinator 가 매 gesture 를 실패로 오인하지 않도록 하기 위함.
#
# env override (hardcoded 는 기본값):
#   FOLLOWER_PORT        우측 follower 시리얼 by-id 경로
#   FOLLOWER_ID          캘리브 파일 이름 = robot.id
#   ORIN_GESTURES_ROOT   sync 받은 gesture 데이터 루트
#   JETSON_VENV          추론 venv

FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00}"
FOLLOWER_ID="${FOLLOWER_ID:-rightarm_test_follower}"
# gesture 데이터는 Hylion 레포 안으로 복사됨 (smolvla/orin/gestures 원본 유지).
ORIN_GESTURES_ROOT="${ORIN_GESTURES_ROOT:-${HOME}/Hylion/jetson/arm/data}"
# lerobot 0.5.2 venv 는 5.3GB — 복제하지 않고 기존 것을 그대로 재사용한다.
JETSON_VENV="${JETSON_VENV:-${HOME}/smolvla/orin/.hylion_arm}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<EOF
Usage: play_gesture.sh <gesture_name>

DGX 에서 녹화·sync 된 gesture trajectory 를 우측 follower 로 재생.

Args:
  gesture_name   필수. snake_case (^[a-z][a-z0-9_]*\$).
                 ${ORIN_GESTURES_ROOT}/<gesture_name>/ 존재 필요.

Exit: 0=성공, 2=인자오류, 3=환경, 4=데이터/캘리브, 5=포트, 1=재생실패

env override: FOLLOWER_PORT, FOLLOWER_ID, ORIN_GESTURES_ROOT, JETSON_VENV

예시:
  bash play_gesture.sh wave_hello
EOF
}

# ── 인자 검증 ────────────────────────────────────────────────────────────────
if [ "$#" -lt 1 ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 2
fi
GESTURE_NAME="$1"

# ── venv activate (pre-check 전에 활성화 — check 와 replay 둘 다 venv 필요) ──
if [ -z "${VIRTUAL_ENV:-}" ]; then
  if [ ! -f "${JETSON_VENV}/bin/activate" ]; then
    echo "[play_gesture] ERROR: venv 없음: ${JETSON_VENV}/bin/activate" >&2
    exit 3
  fi
  set +u
  # shellcheck source=/dev/null
  source "${JETSON_VENV}/bin/activate"
  set -u
fi

# ── pre-check (check_gesture_ready.sh 재사용) ────────────────────────────────
if [ ! -f "${SCRIPT_DIR}/../utils/check_gesture_ready.sh" ]; then
  echo "[play_gesture] ERROR: check_gesture_ready.sh 없음: ${SCRIPT_DIR}" >&2
  exit 3
fi
set +e
bash "${SCRIPT_DIR}/../utils/check_gesture_ready.sh" "${GESTURE_NAME}"
PRECHECK_RC=$?
set -e
if [ "${PRECHECK_RC}" -ne 0 ]; then
  echo "[play_gesture] pre-check 실패 (rc=${PRECHECK_RC}) — 재생 중단" >&2
  exit "${PRECHECK_RC}"
fi

# ── replay_gesture.py 호출 ───────────────────────────────────────────────────
# lerobot-replay CLI 는 lerobot.datasets 를 import 하는데, Jetson 의 lerobot
# 0.5.2 curated subset 에는 그 모듈이 없다 (smolVLA inference 전용). 그래서
# parquet 을 직접 읽어 재생하는 자체 스크립트 replay_gesture.py 를 호출한다.
# torch(→cusparseLt) import 를 위해 venv 의 cusparselt lib 를 LD_LIBRARY_PATH 에
# 얹는다 (run_coordinator.sh 와 동일 패턴).
GESTURE_DIR="${ORIN_GESTURES_ROOT}/${GESTURE_NAME}"
echo "[play_gesture] 재생 시작: ${GESTURE_NAME}"
START_TS=$(date +%s)

CUSPARSELT_LIB="${JETSON_VENV}/lib/python3.10/site-packages/nvidia/cusparselt/lib"
if [ -e "${CUSPARSELT_LIB}/libcusparseLt.so.0" ]; then
  export LD_LIBRARY_PATH="${CUSPARSELT_LIB}:${LD_LIBRARY_PATH:-}"
fi

REPLAY_SCRIPT="${SCRIPT_DIR}/replay_gesture.py"
if [ ! -f "${REPLAY_SCRIPT}" ]; then
  echo "[play_gesture] ERROR: replay_gesture.py 없음: ${REPLAY_SCRIPT}" >&2
  exit 3
fi

set +e
REPLAY_OUT=$(python "${REPLAY_SCRIPT}" \
  --gesture "${GESTURE_NAME}" \
  --root "${ORIN_GESTURES_ROOT}" \
  --port "${FOLLOWER_PORT}" \
  --id "${FOLLOWER_ID}" 2>&1)
REPLAY_RC=$?
set -e

ELAPSED=$(( $(date +%s) - START_TS ))
# replay_gesture.py 출력 그대로 표시 (디버깅용)
echo "${REPLAY_OUT}"

# ── 성공 판정 ────────────────────────────────────────────────────────────────
# replay_gesture.py 가 cosmetic disconnect overload 를 자체적으로 rc=0 처리한다
# (재생 루프 실패만 rc=1). 그래도 안전망으로 출력 패턴 매칭을 남겨둔다.
FINAL_RC=0
if [ "${REPLAY_RC}" -eq 0 ]; then
  : # 성공 (cosmetic disconnect overload 포함)
elif echo "${REPLAY_OUT}" | grep -q "Replaying episode" \
  && echo "${REPLAY_OUT}" | grep -qE "Overload error|disconnect overload" \
  && echo "${REPLAY_OUT}" | grep -qE "in disconnect|disconnect overload"; then
  echo "[play_gesture] WARN: disconnect overload (cosmetic) — 재생은 정상 완료" >&2
  FINAL_RC=0
else
  echo "[play_gesture] ERROR: replay_gesture.py 실패 (rc=${REPLAY_RC})" >&2
  FINAL_RC=1
fi

# ── 한 줄 요약 ───────────────────────────────────────────────────────────────
FRAMES=$(python3 -c "import json; print(json.load(open('${GESTURE_DIR}/meta/info.json'))['total_frames'])" 2>/dev/null || echo "?")
echo "[play_gesture] ${GESTURE_NAME}: frames=${FRAMES}, elapsed=${ELAPSED}s, rc=${FINAL_RC}"
exit "${FINAL_RC}"
