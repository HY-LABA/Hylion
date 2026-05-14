#!/usr/bin/env bash
# =============================================================================
# main.sh — interactive_cli 진입점 (orin 노드)
#
# 사용법:
#   bash orin/interactive_cli/main.sh
#
# 동작:
#   1. venv activate (orin: ~/smolvla/orin/.hylion_arm)
#   2. orin 전용 cusparseLt LD_LIBRARY_PATH 패치
#   3. flows/entry.py 호출 (node.yaml 경로 전달)
#
# 노드별 차이:
#   orin:          VENV_ACTIVATE, cusparseLt 블록 유지
#   dgx:           VENV_ACTIVATE 만 변경, cusparseLt 블록 없음
#   (datacollector 노드는 06_dgx_absorbs_datacollector 결정으로 운영 종료)
#
# 레퍼런스: check_hardware.sh step_venv() line 152~173
#   - venv source 패턴 (line 156~162)
#   - cusparseLt LD_LIBRARY_PATH 패치 패턴 (line 164~168)
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# 0. 경로 상수
#    check_hardware.sh line 41~49 패턴 (SCRIPT_DIR + VENV_ACTIVATE)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_CONFIG="${SCRIPT_DIR}/configs/node.yaml"

# ★ orin 전용 venv 경로
VENV_ACTIVATE="${HOME}/smolvla/orin/.hylion_arm/bin/activate"

# ★ orin 전용 cusparseLt LD_LIBRARY_PATH 패치
#    check_hardware.sh line 49 패턴 (CUSPARSELT_PATH 상수 정의)
CUSPARSELT_PATH="${HOME}/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib"

# ---------------------------------------------------------------------------
# 1. venv 활성화
#    check_hardware.sh step_venv() line 156~162 패턴 그대로
# ---------------------------------------------------------------------------
if [[ ! -f "${VENV_ACTIVATE}" ]]; then
    echo "[ERROR] venv not found: ${VENV_ACTIVATE}"
    echo "        orin/scripts/setup_env.sh 를 먼저 실행하세요."
    exit 1
fi

# shellcheck source=/dev/null
source "${VENV_ACTIVATE}"

# orin 전용: cusparseLt fallback
#   check_hardware.sh step_venv() line 164~168 패턴
#   (SSH 비대화형 환경에서 libcusparseLt ImportError 해소)
if [[ -d "${CUSPARSELT_PATH}" ]]; then
    export LD_LIBRARY_PATH="${CUSPARSELT_PATH}:${LD_LIBRARY_PATH:-}"
fi

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
