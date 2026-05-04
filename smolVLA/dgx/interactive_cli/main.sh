#!/usr/bin/env bash
# =============================================================================
# main.sh — interactive_cli 진입점 (dgx 노드)
#
# 사용법:
#   bash dgx/interactive_cli/main.sh
#
# 동작:
#   1. venv activate (dgx: ~/smolvla/dgx/.arm_finetune)
#   2. flows/entry.py 호출 (node.yaml 경로 전달)
#
# 노드별 차이 (orin 대비):
#   - VENV_ACTIVATE: dgx 전용 경로
#   - cusparseLt 블록 없음 (dgx 불필요)
#
# 레퍼런스: check_hardware.sh step_venv() line 152~173
#   - venv source 패턴 (line 156~162)
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# 0. 경로 상수
#    check_hardware.sh line 41~49 패턴 (SCRIPT_DIR + VENV_ACTIVATE)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_CONFIG="${SCRIPT_DIR}/configs/node.yaml"

# ★ dgx 전용 venv 경로
VENV_ACTIVATE="${HOME}/smolvla/dgx/.arm_finetune/bin/activate"

# ---------------------------------------------------------------------------
# 1. venv 활성화
#    check_hardware.sh step_venv() line 156~162 패턴 그대로
# ---------------------------------------------------------------------------
if [[ ! -f "${VENV_ACTIVATE}" ]]; then
    echo "[ERROR] venv not found: ${VENV_ACTIVATE}"
    echo "        dgx venv 설정을 먼저 완료하세요."
    exit 1
fi

# shellcheck source=/dev/null
source "${VENV_ACTIVATE}"

# ---------------------------------------------------------------------------
# 1.5 프로젝트 루트 .env 자동 source (있을 때만)
#    HF_TOKEN 등 비밀 환경변수를 매번 수동 export 안 해도 되게 자동화.
#    .env 는 .gitignore 처리되며 권한 600 권장.
# ---------------------------------------------------------------------------
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
if [[ -f "${ENV_FILE}" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${ENV_FILE}"
    set +a
fi

# ---------------------------------------------------------------------------
# 2. node.yaml 존재 확인
# ---------------------------------------------------------------------------
if [[ ! -f "${NODE_CONFIG}" ]]; then
    echo "[ERROR] configs/node.yaml 미존재: ${NODE_CONFIG}"
    echo "        F2 task 가 configs/node.yaml 을 생성했는지 확인하세요."
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. flows/entry.py 호출
# ---------------------------------------------------------------------------
cd "${SCRIPT_DIR}" && exec python3 -m flows.entry --node-config "${NODE_CONFIG}"
