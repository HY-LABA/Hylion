#!/usr/bin/env bash
# Hylion coordinator 런처:
#   jetson/expression/.venv 의 PyTorch + openai-whisper 가 nvidia wheel 안에
#   번들된 libcusparseLt.so.0 을 찾도록 LD_LIBRARY_PATH 를 보강하고, venv 의
#   python 으로 코디네이터 모듈을 실행한다.
#
# 사용법:
#   bash scripts/run_coordinator.sh
#   bash scripts/run_coordinator.sh --whisper-model-size base
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/jetson/expression/.venv"
VENV_PY="$VENV/bin/python"

if [ ! -x "$VENV_PY" ]; then
    echo "[run_coordinator] venv python not found: $VENV_PY" >&2
    echo "[run_coordinator] WORKLOG 2026-05-04 항목 참고하여 venv 를 먼저 구축하세요." >&2
    exit 1
fi

CUSPARSELT_LIB="$VENV/lib/python3.10/site-packages/nvidia/cusparselt/lib"
if [ ! -e "$CUSPARSELT_LIB/libcusparseLt.so.0" ]; then
    echo "[run_coordinator] libcusparseLt.so.0 을 venv 안에서 찾지 못함: $CUSPARSELT_LIB" >&2
    exit 1
fi
export LD_LIBRARY_PATH="$CUSPARSELT_LIB:${LD_LIBRARY_PATH:-}"

cd "$PROJECT_ROOT"
exec "$VENV_PY" -m jetson.core.coordinator "$@"
