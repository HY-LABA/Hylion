#!/bin/bash
# DGX Spark (GB10, UMA, CUDA 13.0) SmolVLA 학습 환경 구성 스크립트
# 실행 위치: DGX (~/smolvla/dgx/scripts/setup_train_env.sh)
#
# 결정 근거: docs/work_flow/specs/02_dgx_setting.md TODO-08 / docs/lerobot_study/06_smolvla_finetune_feasibility.md §2
#   - Python: 시스템 3.12.3 (Walking RL 동일)
#   - PyTorch: 2.10.0+cu130 (Walking RL 검증 완료)
#   - cuDNN/NCCL: PyTorch wheel 번들 (시스템 별도 설치 X)
#   - lerobot: editable submodule 설치 (../docs/reference/lerobot)
#   - 환경변수: HF_HOME / PYTORCH_CUDA_ALLOC_CONF / CUDA_VISIBLE_DEVICES 자동 적용
#
# Walking RL 트랙(/home/laba/env_isaaclab/) 과 venv 경로·환경변수 모두 격리됨.

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DGX_DIR="${SMOLVLA_DIR}/dgx"
VENV_DIR="${DGX_DIR}/.arm_finetune"
HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"
LEROBOT_SRC="${SMOLVLA_DIR}/docs/reference/lerobot"

echo "[setup] smolVLA 경로:  ${SMOLVLA_DIR}"
echo "[setup] dgx 경로:      ${DGX_DIR}"
echo "[setup] venv 경로:     ${VENV_DIR}  (dgx 학습 전용, orin/.hylion_arm 과 격리)"
echo "[setup] HF_HOME:       ${HF_CACHE_DIR}"
echo "[setup] lerobot 소스:  ${LEROBOT_SRC}"

# ── 0. 사전 점검 ──────────────────────────────────────────────────────────────
if [ ! -d "${LEROBOT_SRC}" ] || [ -z "$(ls -A "${LEROBOT_SRC}" 2>/dev/null)" ]; then
    echo "[setup] ERROR: lerobot submodule 비어 있음 - devPC 에서 다음 실행 후 재배포 필요:"
    echo "   git submodule update --init --recursive"
    exit 1
fi

if ! command -v python3.12 &>/dev/null; then
    echo "[setup] WARN: python3.12 미탐지 — python3 사용"
    PYTHON=python3
else
    PYTHON=python3.12
fi
echo "[setup] Python:        $(${PYTHON} --version)"

# ── 1. venv 생성 ───────────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[setup] 기존 venv 발견 - 재사용. 새로 만들려면 .arm_finetune 삭제 후 재실행."
else
    "$PYTHON" -m venv "$VENV_DIR"
    echo "[setup] venv 생성 완료"
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet

# ── 2. PyTorch 2.10.0+cu130 설치 (Walking RL 검증 wheel) ─────────────────────
# Walking RL 트랙 환경(2026-04-28 회신)과 동일 wheel 사용.
# GB10 CUDA capability 12.1 UserWarning 출력되나 기능 정상 — 무시 가능.
echo "[setup] PyTorch 2.10.0+cu130 설치 중..."
pip install \
    "torch==2.10.0+cu130" \
    --index-url https://download.pytorch.org/whl/cu130 \
    --quiet

# ── 3. lerobot editable 설치 (submodule SHA 기준) ─────────────────────────────
# docs/reference/lerobot/ 의 fixed SHA 를 그대로 사용 → 본 프로젝트가 분석한 코드와 학습 환경 일치.
echo "[setup] lerobot[smolvla,training] editable 설치 중..."
pip install -e "${LEROBOT_SRC}[smolvla,training]" --quiet

# ── 4. 환경변수 자동 적용 (.venv/bin/activate 끝에 export 추가) ─────────────────
# - HF_HOME: Walking RL / 시스템 디폴트 캐시와 격리
# - PYTORCH_CUDA_ALLOC_CONF: 메모리 단편화 방지 (UMA 환경에서 OOM 마진 확보)
# - CUDA_VISIBLE_DEVICES: 명시적으로 GPU 0 만 사용
ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
ENV_MARKER="# === smolVLA dgx env vars ==="

if ! grep -q "${ENV_MARKER}" "${ACTIVATE_SCRIPT}"; then
    cat >> "${ACTIVATE_SCRIPT}" <<EOF

${ENV_MARKER}
export HF_HOME="${HF_CACHE_DIR}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128"
export CUDA_VISIBLE_DEVICES="0"
EOF
    echo "[setup] 환경변수 export 를 ${ACTIVATE_SCRIPT} 에 추가"
else
    echo "[setup] 환경변수 export 이미 등록됨 — 스킵"
fi

# 활성화 갱신
source "${VENV_DIR}/bin/activate"

# HF 캐시 디렉터리 생성
mkdir -p "${HF_CACHE_DIR}"

# ── 5. 설치 검증 ──────────────────────────────────────────────────────────────
echo "[setup] 설치 검증 중..."
python - <<'PYEOF'
import os, sys, torch
print(f"  Python:         {sys.version.split()[0]}")
print(f"  torch:          {torch.__version__}")
print(f"  CUDA available: {torch.cuda.is_available()}")
print(f"  CUDA build:     {torch.version.cuda}")
print(f"  cuDNN version:  {torch.backends.cudnn.version()}")
print(f"  GPU name:       {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
print(f"  HF_HOME:        {os.environ.get('HF_HOME', '(unset)')}")
print(f"  ALLOC_CONF:     {os.environ.get('PYTORCH_CUDA_ALLOC_CONF', '(unset)')}")
print(f"  CUDA_VISIBLE:   {os.environ.get('CUDA_VISIBLE_DEVICES', '(unset)')}")

if torch.cuda.is_available():
    a = torch.cuda.FloatTensor(2).zero_()
    b = torch.randn(2).cuda()
    c = a + b
    print(f"  CUDA tensor op: {c.tolist()} OK")
else:
    print("[ERROR] CUDA unavailable", file=sys.stderr)
    sys.exit(1)

# lerobot import
try:
    import lerobot
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    print(f"  lerobot import: OK ({lerobot.__file__})")
except Exception as e:
    print(f"[ERROR] lerobot import 실패: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

echo ""
echo "=========================================================="
echo " DGX 학습 환경 설치 완료"
echo ""
echo " venv 활성화 (다음부터 학습할 때마다):"
echo "   source ${VENV_DIR}/bin/activate"
echo ""
echo " 다음 단계:"
echo "   1. preflight check  : bash ${DGX_DIR}/scripts/preflight_check.sh smoke"
echo "   2. smoke test       : bash ${DGX_DIR}/scripts/smoke_test.sh"
echo "=========================================================="
