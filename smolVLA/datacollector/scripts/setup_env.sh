#!/bin/bash
# DataCollector (x86_64 Ubuntu 22.04 LTS) 독립 Python 환경 구성 스크립트
# 실행 위치: DataCollector (~/smolvla/datacollector/scripts/setup_env.sh)
#
# 환경 기준:
#   OS: Ubuntu 22.04 LTS, x86_64
#   Python: 3.12 (Ubuntu 22.04 기본 제공 또는 deadsnakes PPA)
#   PyTorch: 표준 PyPI wheel (pip install torch torchvision)
#     — Jetson 제약 없음. NVIDIA JP 6.0 redist URL 불필요.
#   venv: .hylion_collector (orin/.hylion_arm, dgx/.arm_finetune 와 명명 패턴 통일)
#
# Orin setup_env.sh 와의 핵심 차이:
#   - cusparseLt 처리 불필요 (Jetson 한정 패키지)
#   - LD_LIBRARY_PATH 패치 불필요
#   - torch/torchvision: 표준 PyPI wheel (pip install torch torchvision)
#   - extras: record + hardware + feetech (smolvla 제외)
#   - Python: 3.12 (Jetson 3.10 제약 없음)
#   - lerobot/: upstream src 에 대한 symlink 자동 생성 (옵션 B — 파일 변경 X)

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${SMOLVLA_DIR}/.hylion_collector"  # datacollector/.hylion_collector

# Python 3.12 우선. Ubuntu 22.04 에서는 python3.12 가 설치되어 있거나
# deadsnakes PPA (`sudo add-apt-repository ppa:deadsnakes/ppa`) 로 설치 가능.
if command -v python3.12 &>/dev/null; then
    PYTHON=python3.12
elif command -v python3 &>/dev/null; then
    PYTHON=python3
    echo "[setup] 경고: python3.12 미발견 — python3 로 폴백 (버전: $($PYTHON --version))"
    echo "[setup]   권장: sudo apt-get install python3.12 python3.12-venv"
else
    echo "[setup] 오류: Python 3 이 설치되지 않았습니다." >&2
    exit 1
fi

echo "[setup] smolVLA 경로: ${SMOLVLA_DIR}"
echo "[setup] venv 경로:    ${VENV_DIR}"
echo "[setup] Python:       $($PYTHON --version)"

# ── 0. 시스템 의존 패키지 ──────────────────────────────────────────────────────────
# x86_64 Ubuntu 22.04 에서 권장되는 빌드 의존성
# libopenblas-dev: numpy/scipy 최적화 BLAS 백엔드
# libusb-1.0-0-dev: USB 장치 SDK 빌드 시 필요
# python3.12-venv: venv 생성에 필요
echo "[setup] 시스템 의존 패키지 설치 중..."
sudo apt-get install -y \
    libopenblas-dev \
    libusb-1.0-0-dev \
    python3.12-venv \
    --quiet

# ── 0-b. lerobot/ upstream symlink 설정 (옵션 B 원칙) ─────────────────────────
# datacollector/lerobot/ 은 upstream src/lerobot/ 의 symlink.
# 파일을 직접 변경하지 않고 entrypoint 등록만으로 비활성화 (pyproject.toml 담당).
# 배포 후 lerobot/ 심볼릭링크가 없을 경우 rsync 가 실제 디렉터리를 동기화하므로
# 이 단계는 devPC 에서 rsync 배포 후에도 자동 해소됨.
LEROBOT_DIR="${SMOLVLA_DIR}/lerobot"
UPSTREAM_LEROBOT=""

# rsync 배포 기준: datacollector/lerobot/ 은 실제 디렉터리로 존재해야 함.
# devPC → DataCollector rsync 시 datacollector/lerobot/ 이 전송됨.
# 단, devPC 에서 직접 실행 시 (개발 환경) upstream src 경로 자동 탐색.
if [ ! -d "${LEROBOT_DIR}" ]; then
    # devPC 개발 환경 탐색 순서:
    # 1. smolVLA/docs/reference/lerobot/src/lerobot (프로젝트 레퍼런스)
    # 2. orin/lerobot (형제 디렉터리 패턴)
    CANDIDATE1="$(cd "${SMOLVLA_DIR}/.." 2>/dev/null && pwd)/docs/reference/lerobot/src/lerobot"
    CANDIDATE2="$(cd "${SMOLVLA_DIR}/.." 2>/dev/null && pwd)/orin/lerobot"

    if [ -d "${CANDIDATE1}" ]; then
        UPSTREAM_LEROBOT="${CANDIDATE1}"
    elif [ -d "${CANDIDATE2}" ]; then
        UPSTREAM_LEROBOT="${CANDIDATE2}"
    fi

    if [ -n "${UPSTREAM_LEROBOT}" ]; then
        ln -s "${UPSTREAM_LEROBOT}" "${LEROBOT_DIR}"
        echo "[setup] lerobot/ symlink 생성: ${UPSTREAM_LEROBOT} → ${LEROBOT_DIR}"
    else
        echo "[setup] 경고: datacollector/lerobot/ 디렉터리 없음."
        echo "[setup]   devPC 에서 rsync 배포 후 재실행하거나"
        echo "[setup]   수동으로 upstream lerobot src 를 복사하세요:"
        echo "[setup]     cp -r <smolVLA>/docs/reference/lerobot/src/lerobot ${SMOLVLA_DIR}/lerobot"
        echo "[setup]   pip install -e . 는 lerobot/ 없이 실패합니다."
    fi
else
    echo "[setup] lerobot/ 디렉터리 확인 완료"
fi

# ── 1. venv 생성 ───────────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[setup] 기존 venv 발견 — 재사용합니다."
    echo "[setup]   완전히 새로 만들려면: rm -rf ${VENV_DIR} && bash scripts/setup_env.sh"
else
    if "$PYTHON" -m venv "$VENV_DIR"; then
        echo "[setup] venv 생성 완료 (.hylion_collector)"
    else
        echo "[setup] python -m venv 실패. virtualenv fallback 시도 중..."
        "$PYTHON" -m pip install --user --quiet virtualenv
        "$PYTHON" -m virtualenv "$VENV_DIR"
        echo "[setup] virtualenv 생성 완료"
    fi
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet

# ── 2. lerobot[record,hardware,feetech] editable install ──────────────────────
# torch/torchvision 을 먼저 설치하면 lerobot 설치 시 pip 가 버전 불일치 wheel 을
# 선택할 수 있으므로, lerobot 을 먼저 설치한 뒤 torch 를 별도 설치한다.
echo "[setup] lerobot 설치 중 (${SMOLVLA_DIR})..."
pip install -e "${SMOLVLA_DIR}[record,hardware,feetech]" --quiet

# ── 3. PyTorch (표준 PyPI wheel — x86_64 Ubuntu 22.04) ────────────────────────
# Orin 과 달리 NVIDIA JP 6.0 redist URL 불필요.
# DataCollector 는 x86_64 이므로 표준 PyPI wheel 사용 가능.
# CUDA 설치 환경 → CUDA wheel 자동 선택.
# CPU-only 환경 → CPU wheel 선택.
echo "[setup] PyTorch 설치 중 (표준 PyPI wheel)..."
pip install \
    "torch>=2.0.0" \
    "torchvision" \
    --quiet

# ── 4. 환경 변수 설정 (venv activate) ─────────────────────────────────────────
ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"

if ! grep -q "HF_HOME" "$ACTIVATE_SCRIPT" 2>/dev/null; then
    cat >> "$ACTIVATE_SCRIPT" <<'ENVEOF'

# smolVLA DataCollector 환경변수 (setup_env.sh 추가)
export HF_HOME="${HOME}/.cache/huggingface"
ENVEOF
    echo "[setup] HF_HOME 환경변수 venv activate 에 추가 완료"
else
    echo "[setup] HF_HOME 이미 설정됨 — 스킵"
fi

# ── 5. 설치 검증 ─────────────────────────────────────────────────────────────
echo "[setup] 설치 검증 중..."
source "${VENV_DIR}/bin/activate"

python - <<'PYEOF'
import sys

# lerobot import 검증
try:
    import lerobot
    print(f"  lerobot:        {lerobot.__version__}")
except ImportError as e:
    print(f"[ERROR] lerobot import 실패: {e}", file=sys.stderr)
    sys.exit(1)

# torch import 검증
try:
    import torch
    cuda_info = f"CUDA {torch.version.cuda}" if torch.cuda.is_available() else "CPU-only"
    print(f"  torch:          {torch.__version__} ({cuda_info})")
except ImportError as e:
    print(f"[ERROR] torch import 실패: {e}", file=sys.stderr)
    sys.exit(1)

# record extras 핵심 패키지 검증
try:
    import datasets
    print(f"  datasets:       {datasets.__version__}")
except ImportError as e:
    print(f"[WARN] datasets import 실패 (record extras 확인): {e}", file=sys.stderr)

# feetech SDK 검증
try:
    import feetech_servo_sdk
    print(f"  feetech-sdk:    OK")
except ImportError:
    try:
        import scservo_sdk
        print(f"  scservo-sdk:    OK (feetech alias)")
    except ImportError as e:
        print(f"[WARN] feetech-servo-sdk import 실패: {e}", file=sys.stderr)

# entrypoint 확인
print("")
print("  lerobot entrypoints 확인:")
import shutil
entrypoints = [
    "lerobot-record", "lerobot-teleoperate", "lerobot-calibrate",
    "lerobot-find-cameras", "lerobot-find-port", "lerobot-info",
    "lerobot-setup-motors", "lerobot-replay", "lerobot-find-joint-limits",
]
for ep in entrypoints:
    found = "OK" if shutil.which(ep) else "NOT FOUND"
    print(f"    {ep}: {found}")
PYEOF

echo ""
echo "══════════════════════════════════════════════════════"
echo " DataCollector 환경 설치 완료!"
echo ""
echo " 활성화 방법:"
echo "   source ${VENV_DIR}/bin/activate"
echo ""
echo " 사용 예시:"
echo "   lerobot-find-port"
echo "   lerobot-find-cameras opencv"
echo "   lerobot-record --robot.type=so101_follower ..."
echo "   lerobot-teleoperate --robot.type=so101_follower ..."
echo ""
echo " 참고:"
echo "   SO-ARM 포트 발견: lerobot-find-port"
echo "   포트 설정 저장:   datacollector/config/ports.json"
echo "   카메라 설정:      lerobot-find-cameras opencv"
echo "══════════════════════════════════════════════════════"
