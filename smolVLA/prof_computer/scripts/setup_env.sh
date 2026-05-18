#!/bin/bash
# prof_computer (WSL2 Ubuntu 22.04 + RTX 3090) SmolVLA 학습 환경 구성 스크립트
# 실행 위치: WSL Ubuntu 안에서 — bash ~/smolVLA/prof_computer/scripts/setup_env.sh
#           (또는 /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/scripts/setup_env.sh)
#
# 결정 근거 (lerobot 공식 installation.mdx / smolvla.mdx / requirements-ubuntu.txt 기반):
#   - Python: 3.12.x (lerobot 0.5.2 `requires-python = ">=3.12"`)
#             → Ubuntu 22.04 system default 3.10 으로 부족 → deadsnakes PPA 경유
#             → 시스템 3.10 은 유지, 3.12 병존 — `python3.12 -m venv` 로 격리
#   - PyTorch: **2.10.0+cu128** (lerobot 공식 lock `requirements-ubuntu.txt` 의 `torch==2.10.0`
#              + nvidia-cublas-cu12 12.8.4.1 / cuda-bindings 12.9.4 영역 매칭 → cu128 wheel).
#              RTX 3090 Ampere sm_86 = cu128 공식 지원 범위.
#              DGX 는 cu130 wheel (GB10 Blackwell + Walking RL 검증) — prof_computer 와 wheel 메이저는 다름.
#   - video_backend: torchcodec (lerobot default — installation.mdx §70 "LeRobot uses TorchCodec for video decoding by default").
#              torch>=2.10 이면 torchcodec 0.10.x 가 system-wide ffmpeg dynamic linking 지원.
#   - lerobot: editable submodule 설치 (DGX 와 동일 — Option B 일관). extras `[smolvla,training]`.
#   - HF_HOME: WSL 로컬 (~/.cache/huggingface) — /mnt/c 통한 Windows mount 는 IO 성능 저하
#
# 환경 매니저 venv 사용 — lerobot 공식 1순위는 conda 지만 프로젝트 정책 (`03_software.md §6`: 시스템 Python + venv)
# 과 DGX 정합성 위해 venv 유지. installation.mdx §3 "If you prefer another environment manager (e.g. uv, venv),
# ensure you have Python >=3.12 and support PyTorch >= 2.10" — 충족.
#
# DGX setup_finetune_env.sh 와의 차이:
#   - PyTorch wheel: cu128 (vs DGX cu130) — RTX 3090 / GB10 칩 차이 반영. 메이저 버전 (2.10.0) 동일
#   - Python 3.12: deadsnakes (vs DGX 시스템 default — Ubuntu 24.04)
#   - extras: hardware/feetech 제외 (prof_computer 는 학습 전용 — SO-ARM 미연결)

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PROF_DIR="${SMOLVLA_DIR}/prof_computer"
VENV_DIR="${PROF_DIR}/.venv_arm_finetune"
HF_CACHE_DIR="${HOME}/.cache/huggingface"
LEROBOT_SRC="${SMOLVLA_DIR}/docs/reference/lerobot"

echo "[setup] smolVLA 경로:  ${SMOLVLA_DIR}"
echo "[setup] prof 경로:     ${PROF_DIR}"
echo "[setup] venv 경로:     ${VENV_DIR}  (학습 전용, 격리)"
echo "[setup] HF_HOME:       ${HF_CACHE_DIR}  (WSL 로컬 — /mnt/c 회피)"
echo "[setup] lerobot 소스:  ${LEROBOT_SRC}"

# ── 0. 사전 점검 ──────────────────────────────────────────────────────────────
if [ ! -d "${LEROBOT_SRC}" ] || [ -z "$(ls -A "${LEROBOT_SRC}" 2>/dev/null)" ]; then
    echo "[setup] ERROR: lerobot submodule 비어 있음 — 다음 실행 후 재시도:"
    echo "   git -C ${SMOLVLA_DIR}/.. submodule update --init --recursive"
    exit 1
fi

# lerobot 0.5.2 requires-python ">=3.12" — python3.12 필수 (시스템 3.10 으로 부족)
if ! command -v python3.12 &>/dev/null; then
    echo "[setup] ERROR: python3.12 미설치. deadsnakes PPA 로 먼저 설치:"
    echo "   sudo add-apt-repository -y ppa:deadsnakes/ppa"
    echo "   sudo apt update"
    echo "   sudo apt install -y python3.12 python3.12-venv python3.12-dev"
    echo "   (그리고 build-essential ffmpeg v4l-utils 등 기본 패키지도)"
    exit 1
fi
PYTHON=python3.12
echo "[setup] Python:        $(${PYTHON} --version)"

# python3.12-venv 설치 확인 (deadsnakes 의 python3.12 만 깔고 -venv 빼먹는 케이스 차단)
if ! ${PYTHON} -c "import venv" &>/dev/null; then
    echo "[setup] ERROR: python3.12-venv 미설치. 먼저 실행:"
    echo "   sudo apt install -y python3.12-venv python3.12-dev"
    exit 1
fi

# GPU 가용성 사전 확인
if ! command -v nvidia-smi &>/dev/null; then
    echo "[setup] ERROR: nvidia-smi 없음 — WSL2 GPU passthrough 확인 필요 (Windows NVIDIA 드라이버)"
    exit 1
fi
echo "[setup] GPU:           $(nvidia-smi --query-gpu=name --format=csv,noheader)"

# ── 1. venv 생성 ───────────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "[setup] 기존 venv 발견 - 재사용. 새로 만들려면 .venv_arm_finetune 삭제 후 재실행."
else
    "$PYTHON" -m venv "$VENV_DIR"
    echo "[setup] venv 생성 완료"
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet

# ── 2. PyTorch 2.10.0+cu128 설치 (lerobot 공식 lock 일치) ─────────────────────
# lerobot upstream `requirements-ubuntu.txt` 의 `torch==2.10.0` + `nvidia-cublas-cu12==12.8.4.1`
# / `cuda-bindings==12.9.4` 영역 매칭 → cu128 wheel. RTX 3090 Ampere sm_86 공식 지원.
# Python 3.12 + linux x86_64 cp312 wheel 존재 확인 (torch-2.10.0+cu128-cp312-cp312-manylinux_2_28_x86_64.whl).
# DGX 는 cu130 wheel — 두 노드 wheel 메이저 다르지만 torch 2.10.0 동일 → 학습 결과 동등성 유지.
echo "[setup] PyTorch 2.10.0+cu128 설치 중 (lerobot 공식 lock 일치)..."
pip install \
    'torch==2.10.0' \
    --index-url https://download.pytorch.org/whl/cu128 \
    --quiet

# ── 3. lerobot editable 설치 ───────────────────────────────────────────────────
# DGX 와 동일 source (docs/reference/lerobot/) — Option B.
# extras 차이: prof_computer 는 학습 전용 → hardware/feetech 제외 (DataCollector 책임 없음).
# [peft] 필수 — LoRA fine-tune (model_config.md §3 A2 채택) 시 lerobot 이 peft 패키지 import.
#               lerobot peft_training.mdx §7 권장. 초기 누락 시 PEFT wrapping 단계에서 ModuleNotFoundError.
echo "[setup] lerobot[smolvla,training,peft] editable 설치 중..."
pip install -e "${LEROBOT_SRC}[smolvla,training,peft]" --quiet

# ── 3-c. torchcodec — lerobot 공식 default video backend ──────────────────────
# lerobot installation.mdx §70: "LeRobot uses TorchCodec for video decoding by default".
# torch 2.10 + torchcodec 0.10 = system-wide ffmpeg dynamic linking 지원 (installation.mdx §100).
# lerobot[training]→[dataset] extras 가 이미 torchcodec PyPI wheel 을 넣으므로 별도 install 불요.
# 단 cu128 wheel 매칭 강제를 위해 명시적 재설치 — pip 가 호환 wheel 자동 선택.
echo "[setup] torchcodec (cu128 wheel, lerobot default backend) 설치 중..."
pip install \
    'torchcodec>=0.3.0,<0.11.0' \
    --index-url https://download.pytorch.org/whl/cu128 \
    --quiet

# ── 4. 환경변수 자동 적용 (.venv/bin/activate 끝에 export 추가) ─────────────────
ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
ENV_MARKER="# === smolVLA prof_computer env vars ==="

if ! grep -q "${ENV_MARKER}" "${ACTIVATE_SCRIPT}"; then
    cat >> "${ACTIVATE_SCRIPT}" <<EOF

${ENV_MARKER}
export HF_HOME="${HF_CACHE_DIR}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128"
export CUDA_VISIBLE_DEVICES="0"
# Hub 캐시는 HF_HOME 하위 자동 생성 (huggingface_hub default)

# .env (HF_TOKEN, WANDB_API_KEY 등 비밀값) 자동 로드 — venv 디렉터리 내 .env 만 source.
# .gitignore 의 .env 패턴 (smolVLA/.gitignore:31) 이 트래킹 차단 — push 사고 방지.
if [ -f "\${VIRTUAL_ENV}/.env" ]; then
    set -a
    source "\${VIRTUAL_ENV}/.env"
    set +a
fi
EOF
    echo "[setup] 환경변수 export 를 ${ACTIVATE_SCRIPT} 에 추가"
else
    echo "[setup] 환경변수 export 이미 등록됨 — 스킵"
fi

# 활성화 갱신
source "${VENV_DIR}/bin/activate"
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
print(f"  VRAM total:     {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB" if torch.cuda.is_available() else "")
print(f"  HF_HOME:        {os.environ.get('HF_HOME', '(unset)')}")
print(f"  ALLOC_CONF:     {os.environ.get('PYTORCH_CUDA_ALLOC_CONF', '(unset)')}")

if torch.cuda.is_available():
    a = torch.cuda.FloatTensor(2).zero_()
    b = torch.randn(2).cuda()
    c = a + b
    print(f"  CUDA tensor op: {c.tolist()} OK")
else:
    print("[ERROR] CUDA unavailable", file=sys.stderr)
    sys.exit(1)

try:
    import lerobot
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    print(f"  lerobot import: OK ({lerobot.__file__})")
except Exception as e:
    print(f"[ERROR] lerobot import 실패: {e}", file=sys.stderr)
    sys.exit(1)

try:
    import torchcodec
    print(f"  torchcodec:     OK ({torchcodec.__version__ if hasattr(torchcodec, '__version__') else 'imported'})")
except Exception as e:
    print(f"[WARN] torchcodec import 실패: {e}", file=sys.stderr)
PYEOF

echo ""
echo "=========================================================="
echo " prof_computer 학습 환경 설치 완료"
echo ""
echo " venv 활성화 (다음부터 학습할 때마다):"
echo "   source ${VENV_DIR}/bin/activate"
echo ""
echo " 다음 단계:"
echo "   1. HF 로그인:    hf auth login    (또는 huggingface-cli login)"
echo "   2. wandb 로그인: wandb login"
echo "   3. dry-run:      cd ${SMOLVLA_DIR}/prof_computer/finetune/leftarm_v2 && python run_train.py train --pass 2a --dry-run"
echo "   4. smoke test:   python run_train.py train --pass smoke  (train_config_smoke.yaml 사용 — VRAM peak / 누수 측정)"
echo "=========================================================="
