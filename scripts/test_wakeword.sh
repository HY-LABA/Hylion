#!/usr/bin/env bash
# Standalone wake-word 테스터 런처. run_coordinator.sh 와 동일하게 venv +
# LD_LIBRARY_PATH + P5HD 마이크 설정을 잡아주고, scripts/test_wakeword.py 를
# 실행한다.
#
# 사용법:
#   bash scripts/test_wakeword.sh checkpoints/wakeword/hailion_stop.tflite
#   bash scripts/test_wakeword.sh checkpoints/wakeword/hailion_stop.onnx 20 0.005
#       # args: <model_path> [duration_sec=30] [print_floor=0.001]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/jetson/expression/.venv"
VENV_PY="$VENV/bin/python"

if [ ! -x "$VENV_PY" ]; then
    echo "[test_wakeword] venv python not found: $VENV_PY" >&2
    exit 1
fi

CUSPARSELT_LIB="$VENV/lib/python3.10/site-packages/nvidia/cusparselt/lib"
if [ -e "$CUSPARSELT_LIB/libcusparseLt.so.0" ]; then
    export LD_LIBRARY_PATH="$CUSPARSELT_LIB:${LD_LIBRARY_PATH:-}"
fi

export HYLION_WAKEWORD_DEVICE_KEYWORD="${HYLION_WAKEWORD_DEVICE_KEYWORD:-P5HD}"
export HYLION_WAKEWORD_SAMPLE_RATE="${HYLION_WAKEWORD_SAMPLE_RATE:-44100}"

cd "$PROJECT_ROOT"
exec "$VENV_PY" scripts/test_wakeword.py "$@"
