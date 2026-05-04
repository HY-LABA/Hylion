#!/usr/bin/env bash
# run_python.sh — Orin venv activate + python 실행 wrapper
# 03 BACKLOG #14 해결: SSH 비대화형에서 cuSPARSELt LD_LIBRARY_PATH 누락 차단
#
# 사용:
#   ssh orin "~/smolvla/orin/scripts/run_python.sh script.py args..."
#   ssh orin "~/smolvla/orin/scripts/run_python.sh -c 'import torch; print(torch.cuda.is_available())'"
#   ssh orin "~/smolvla/orin/scripts/run_python.sh -m mod.path"
#
# 배경:
#   Orin SSH 비대화형 세션은 ~/.bashrc 를 읽지 않아 venv activate 가 누락됨.
#   activate 없이 venv python 직접 실행 시 LD_LIBRARY_PATH 미설정 →
#   libcusparseLt.so.0 ImportError 발생 (03 BACKLOG #14).
#   본 wrapper 가 activate 를 선행하여 cuSPARSELt 경로를 올바르게 적용한다.
#
# 참고:
#   VENV_PATH 는 setup_env.sh 의 VENV_DIR 과 동일한 경로 규칙 (orin/.hylion_arm).
#   setup_env.sh: SMOLVLA_DIR = ~/smolvla/orin → VENV_DIR = ~/smolvla/orin/.hylion_arm

set -euo pipefail

VENV_PATH="${HOME}/smolvla/orin/.hylion_arm"

if [[ ! -f "${VENV_PATH}/bin/activate" ]]; then
    echo "[run_python] ERROR: venv 미존재: ${VENV_PATH}" >&2
    echo "[run_python]   setup_env.sh 를 먼저 실행하여 venv 를 생성하세요." >&2
    exit 1
fi

# shellcheck disable=SC1091
source "${VENV_PATH}/bin/activate"

# activate 가 LD_LIBRARY_PATH 를 포함한 환경변수를 설정한다.
# 추가 보강이 필요한 경우 아래 주석 해제 (현재는 activate 로 충분):
# export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/usr/local/cuda/lib64"

exec python3 "$@"
