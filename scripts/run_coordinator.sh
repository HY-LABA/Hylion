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

# NUC bridge 주소: Jetson↔NUC 유선 직결(NetworkManager 공유망 10.42.0.0/24).
# bhl_client.py 의 기본값은 127.0.0.1 이므로 NUC 의 실제 IP 를 명시해야
# coordinator 가 NUC bridge(:9000)로 TCP/NDJSON 을 보낼 수 있다.
# NUC IP 가 바뀌면 셸에서 export HYLION_BHL_HOST=... 로 override.
export HYLION_BHL_HOST="${HYLION_BHL_HOST:-10.42.0.221}"
export HYLION_BHL_PORT="${HYLION_BHL_PORT:-9000}"

# 마이크 선택: P5HD USB (1ch mono, 44.1kHz/48kHz 둘 다 지원). YJX-C5 는 stereo
# headset 류라 wake-word 용 적합하지 않고, mono 44.1kHz 거부함. P5HD 가 4월
# 검증 때 쓰던 메인 마이크와 같은 스펙. wake-word + 녹음 + e-stop listener
# 모두 P5HD 44.1kHz 로 통일. 다른 마이크 쓰려면 셸에서 export 로 override.
export HYLION_WAKEWORD_DEVICE_KEYWORD="${HYLION_WAKEWORD_DEVICE_KEYWORD:-P5HD}"
export HYLION_WAKEWORD_SAMPLE_RATE="${HYLION_WAKEWORD_SAMPLE_RATE:-44100}"
export HYLION_MIC_SAMPLE_RATE="${HYLION_MIC_SAMPLE_RATE:-44100}"

# --preferred-keyword 도 P5HD 로 (record_to_wav 의 device picker 가 같은 마이크
# 잡도록). 사용자가 명시적으로 인자를 넘기면 그쪽이 우선됨.
if [[ "$*" != *"--preferred-keyword"* ]]; then
    set -- --preferred-keyword P5HD "$@"
fi

cd "$PROJECT_ROOT"
exec "$VENV_PY" -m jetson.core.coordinator "$@"
