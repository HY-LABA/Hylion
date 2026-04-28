#!/bin/bash
# Jetson Orin (L4T R36.x / JetPack 6.2.2) 독립 Python 환경 구성 스크립트
# 실행 위치: Orin (~/smolvla/scripts/setup_env.sh)
#
# JetPack 6.2.2 (R36.5.0) 기준:
#   CUDA 12.6, Python 3.10 (cp310)
#   PyTorch: NVIDIA JP 6.0 공식 wheel (nv24.08, cu12.6 forward-compatible)
#   - JP 6.2 공식 배포는 컨테이너 전용 (wheel 없음). 네이티브 venv + SO-ARM UART hotplug +
#     lerobot editable dev 조합과 맞지 않아 JP 6.0 wheel(nv24.08)을 의도적으로 선택.
#     (2026-03부터 NVIDIA도 iGPU standalone 컨테이너 생산 중단)
#   - jp6/cu126 Jetson AI Lab 인덱스 wheel은 libcudss/libcusparseLt 미설치로 동작 불가
#   - JP 6.0 wheel (2.5.0a0+872d972e41.nv24.08) 동작 확인

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${SMOLVLA_DIR}/.hylion_arm"  # orin/.hylion_arm (hidden, orin 디렉터리 안). dgx/.arm_finetune 과 격리

# Python 3.10 우선 (jp6/cu126 wheel이 cp310만 제공)
if command -v python3.10 &>/dev/null; then
    PYTHON=python3.10
else
    PYTHON=python3
fi

echo "[setup] smolVLA 경로: ${SMOLVLA_DIR}"
echo "[setup] venv 경로:    ${VENV_DIR}"
echo "[setup] Python:       $($PYTHON --version)"

# ── 0. 시스템 의존 패키지 ──────────────────────────────────────────────────────────
# NVIDIA 공식 요건 (Install-PyTorch-Jetson-Platform.md §2)
echo "[setup] 시스템 의존 패키지 설치 중 (libopenblas-dev, libopenmpi-dev, libomp-dev)..."
sudo apt-get install -y libopenblas-dev libopenmpi-dev libomp-dev --quiet

# cusparselt 시스템 설치: 24.06 이상 wheel 사용 시 필요.
# 권장: NVIDIA cuSPARSELt 0.8.1 deb(aarch64-jetson, Ubuntu 22.04)를 먼저 수동 설치.
#   https://developer.nvidia.com/cusparselt-downloads
#   sudo dpkg -i libcusparselt*.deb && sudo ldconfig
# 미설치 시 아래 Option A 폴백 자동 실행.
if ! ldconfig -p 2>/dev/null | grep -q "libcusparseLt"; then
    # Option B (권장 — Orin 단일 장비): 사전에 NVIDIA deb 수동 설치 시 이 블록 스킵됨
    #   https://developer.nvidia.com/cusparselt-downloads
    #   → Linux / aarch64-jetson / Native / Ubuntu / 22.04 / deb (local) 선택 후 설치
    #   sudo dpkg -i libcusparselt*.deb && sudo ldconfig
    #
    # Option A (자동 폴백): install_cusparselt.sh 는 CUDA 12.1–12.4만 지원
    #   CUDA 12.6 에서는 스크립트 내 버전 분기가 없어 실패함 → 현재는 스킵
    echo "[setup] libcusparseLt 시스템 미설치 — Option A 스킵 (CUDA 12.6 미지원)"
    echo "[setup]   권장: NVIDIA cuSPARSELt 0.8.1 deb(aarch64-jetson) 수동 설치"
    echo "[setup]   https://developer.nvidia.com/cusparselt-downloads"
    echo "[setup]   → LD_LIBRARY_PATH 패치(§4)로 임시 대체"
else
    echo "[setup] libcusparseLt 시스템 설치 확인 — 스킵"
fi

# ── 1. venv 생성 ───────────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[setup] 기존 venv 발견 — 재사용합니다. 완전히 새로 만들려면 .venv 디렉토리를 삭제 후 재실행하세요."
else
    if "$PYTHON" -m venv "$VENV_DIR"; then
        echo "[setup] venv 생성 완료"
    else
        echo "[setup] python -m venv 실패. python3-venv 미설치 환경으로 판단되어 virtualenv fallback을 시도합니다."
        "$PYTHON" -m pip install --user --quiet virtualenv
        "$PYTHON" -m virtualenv "$VENV_DIR"
        echo "[setup] virtualenv 생성 완료"
    fi
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet

# ── 2. lerobot[smolvla,hardware,feetech] 설치 ─────────────────────────────────
# torch/torchvision 을 먼저 설치하면 lerobot 설치 시 pip 가 PyPI CPU-only wheel 로
# 덮어쓰므로, lerobot 을 먼저 설치한 뒤 torch 를 force-reinstall 한다.
echo "[setup] lerobot 설치 중 (${SMOLVLA_DIR})..."
pip install -e "${SMOLVLA_DIR}[smolvla,hardware,feetech]" --quiet

# ── 3. PyTorch (NVIDIA JP 6.0 공식 redist wheel, CUDA 12.6 forward-compatible) ─
# JP 6.2 공식 배포는 컨테이너 전용. lerobot editable + SO-ARM 환경에 맞지 않아 JP 6.0
# wheel(nv24.08)을 의도적으로 선택. lerobot 이후 설치해야 PyPI CPU-only wheel 덮어쓰기 방지.
echo "[setup] PyTorch 설치 중 (NVIDIA JP 6.0 wheel — CUDA 12.6 forward-compatible)..."
pip install \
    "https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl" \
    --force-reinstall --no-deps \
    --quiet

# numpy: torch 2.5.0a0 는 NumPy 1.x 로 컴파일됨 — 2.x 설치 시 ABI 불일치 경고 발생
echo "[setup] NumPy 1.x 고정 중..."
pip install "numpy>=1.24.0,<2" --force-reinstall --quiet

# ── 3-b. torchvision (Jetson aarch64 + CUDA 12.6 + PyTorch 2.5 대응 wheel) ───
# PyPI torchvision wheel은 Jetson CUDA 빌드가 아니어서 ABI 불일치 가능성이 있다.
# 따라서 Orin에서는 사전빌드 wheel을 수동 1회 설치하는 방식을 사용한다.
if ! python -c "import torchvision" >/dev/null 2>&1; then
    echo "[setup] torchvision 미설치 — 수동 1회 설치 필요"
    echo "[setup]   devPC: scp smolVLA/docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl orin:~/"
    echo "[setup]   Orin:  pip install ~/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl --no-deps --force-reinstall"
else
    echo "[setup] torchvision 설치 확인: $(python -c 'import torchvision; print(torchvision.__version__)')"
fi

# ── 4. LD_LIBRARY_PATH 패치 (cusparselt 시스템 미설치 시 임시 우회) ──────────────
# §0에서 시스템 설치 성공 시 불필요. 실패 시에만 pip 번들 경로를 activate에 추가.
ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
if ! ldconfig -p 2>/dev/null | grep -q "libcusparseLt"; then
    CUSPARSELT_LIB="${VENV_DIR}/lib/python3.10/site-packages/nvidia/cusparselt/lib"
    # NOTE: 본 경로는 venv 디렉터리 이름(.hylion_arm) 변경 시 함께 갱신 필요
    if [ -d "$CUSPARSELT_LIB" ] && ! grep -q "cusparselt" "$ACTIVATE_SCRIPT"; then
        echo "export LD_LIBRARY_PATH=${CUSPARSELT_LIB}:\$LD_LIBRARY_PATH" >> "$ACTIVATE_SCRIPT"
        echo "[setup] 경고: cusparselt 시스템 미설치. LD_LIBRARY_PATH 임시 패치 적용."
        echo "[setup]       해결: NVIDIA cuSPARSELt 0.8.1 deb(aarch64-jetson) 설치 권장."
    fi
else
    echo "[setup] cusparselt 시스템 설치 확인 — LD_LIBRARY_PATH 패치 불필요"
fi

# ── 5. nvcc PATH 등록 (~/.bashrc) ─────────────────────────────────────────────
if [ -d "/usr/local/cuda/bin" ] && ! grep -q "cuda/bin" ~/.bashrc 2>/dev/null; then
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
    echo "[setup] nvcc PATH ~/.bashrc 등록 완료 (source ~/.bashrc 또는 재로그인 필요)"
else
    echo "[setup] nvcc PATH 이미 등록됨 또는 /usr/local/cuda/bin 없음 — 스킵"
fi

source "${VENV_DIR}/bin/activate"

# ── 6. 설치 검증 (실제 CUDA 텐서 연산 — cusparselt lazy load 포함) ─────────────
echo "[setup] CUDA 연산 검증 중..."
python - <<'PYEOF'
import torch, sys
print(f"  torch:          {torch.__version__}")
print(f"  CUDA available: {torch.cuda.is_available()}")
print(f"  cuDNN version:  {torch.backends.cudnn.version()}")
try:
    a = torch.cuda.FloatTensor(2).zero_()
    b = torch.randn(2).cuda()
    c = a + b
    print(f"  CUDA 텐서 연산: {c.tolist()} ✓")
except Exception as e:
    print(f"[ERROR] CUDA 연산 실패: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

echo ""
echo "══════════════════════════════════════════════════════"
echo " 환경 설치 완료!"
echo ""
echo " 활성화 방법:"
echo "   source ${VENV_DIR}/bin/activate"
echo ""
echo " 실행 예시:"
echo "   python ${SMOLVLA_DIR}/examples/tutorial/smolvla/using_smolvla_example.py"
echo "══════════════════════════════════════════════════════"