#!/bin/bash
# DGX Spark SmolVLA 학습 사전 점검 스크립트 (OOM 방어 + Walking RL 보호)
# 실행 위치: DGX (~/smolvla/dgx/scripts/preflight_check.sh)
#
# 사용:
#   bash preflight_check.sh smoke   # 1 step 검증용 (필요 메모리 20 GB)
#   bash preflight_check.sh s1      # 04 / 06 1차 학습 (35 GB)
#   bash preflight_check.sh s3      # 06 2차 학습 — VLM 까지 풀 학습 (65 GB)
#   bash preflight_check.sh lora    # LoRA fallback (28 GB)
#
# 통과 조건 (모두 만족해야 exit 0):
#   1. HF_HOME 격리 경로로 설정됨
#   2. venv 가 활성화돼 있고 SmolVLA venv 임
#   3. 가용 메모리(가용 RAM = MemAvailable) >= 필요 메모리 + 안전 마진(10 GB)
#   4. Walking RL 프로세스가 보호 정책 준수 (정보 출력만, 절대 kill X)
#   5. Ollama gemma3 미로드 (또는 사용자 명시 동의)
#
# 본 스크립트는 자원 관찰만 합니다. 다른 사용자 프로세스를 절대 건드리지 않습니다.

set -e

# ── 시나리오별 메모리 임계치 (GiB) ────────────────────────────────────────────
case "${1:-}" in
    smoke)  REQUIRED_GB=20  ; SCENARIO="Smoke test (1 step)" ;;
    s1)     REQUIRED_GB=35  ; SCENARIO="S1 / 04 leftarmVLA / 06 biarm 1차" ;;
    s3)     REQUIRED_GB=65  ; SCENARIO="S3 / 06 biarm 2차 (VLM 까지 풀 학습)" ;;
    lora)   REQUIRED_GB=28  ; SCENARIO="LoRA fallback" ;;
    *)
        echo "사용: bash $0 {smoke|s1|s3|lora}"
        echo "  smoke : Smoke test (1 step)         — 필요 20 GB"
        echo "  s1    : S1 / 04 / 06 1차            — 필요 35 GB"
        echo "  s3    : S3 / 06 2차 (VLM 풀 학습)   — 필요 65 GB"
        echo "  lora  : LoRA fallback               — 필요 28 GB"
        exit 1
        ;;
esac

SAFETY_MARGIN_GB=10
TOTAL_REQUIRED_GB=$((REQUIRED_GB + SAFETY_MARGIN_GB))
SMOLVLA_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DGX_DIR="${SMOLVLA_DIR}/dgx"
VENV_DIR="${DGX_DIR}/.arm_finetune"
HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"

PASS=true
fail() { echo "  [FAIL] $1"; PASS=false; }
ok()   { echo "  [OK]   $1"; }
info() { echo "  [INFO] $1"; }

echo "=========================================================="
echo " preflight check — ${SCENARIO}"
echo "=========================================================="
echo ""

# ── 1. venv / 환경변수 격리 검증 ───────────────────────────────────────────────
echo "[1/5] venv / 환경변수 격리"
if [ -z "${VIRTUAL_ENV:-}" ]; then
    fail "venv 비활성. 다음 실행 후 재시도:  source ${VENV_DIR}/bin/activate"
elif [ "${VIRTUAL_ENV}" != "${VENV_DIR}" ]; then
    fail "다른 venv 활성됨 (${VIRTUAL_ENV}). SmolVLA venv 활성 필요: source ${VENV_DIR}/bin/activate"
else
    ok "venv 활성: ${VIRTUAL_ENV}"
fi

if [ "${HF_HOME:-}" != "${HF_CACHE_DIR}" ]; then
    fail "HF_HOME 격리 경로 미설정 (현재: ${HF_HOME:-unset}). 기대: ${HF_CACHE_DIR}"
else
    ok "HF_HOME: ${HF_HOME}"
fi

if [ "${CUDA_VISIBLE_DEVICES:-}" != "0" ]; then
    fail "CUDA_VISIBLE_DEVICES 미설정 (현재: ${CUDA_VISIBLE_DEVICES:-unset})"
else
    ok "CUDA_VISIBLE_DEVICES: 0"
fi
echo ""

# ── 2. 메모리 가용성 ───────────────────────────────────────────────────────────
echo "[2/5] 메모리 가용성 (UMA pool)"
MEM_AVAIL_KB=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
MEM_AVAIL_GB=$((MEM_AVAIL_KB / 1024 / 1024))
MEM_TOTAL_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
MEM_TOTAL_GB=$((MEM_TOTAL_KB / 1024 / 1024))

info "전체 RAM:     ${MEM_TOTAL_GB} GiB"
info "가용 RAM:     ${MEM_AVAIL_GB} GiB"
info "필요 메모리:  ${REQUIRED_GB} GiB + 안전 마진 ${SAFETY_MARGIN_GB} GiB = ${TOTAL_REQUIRED_GB} GiB"

if [ "${MEM_AVAIL_GB}" -lt "${TOTAL_REQUIRED_GB}" ]; then
    fail "가용 메모리 부족 (${MEM_AVAIL_GB} < ${TOTAL_REQUIRED_GB} GiB)"
    echo "         → 학습 불가. Jupyter 커널 / Ollama / 본인 다른 프로세스 정리 후 재시도."
    echo "         → Walking RL 프로세스(env_isaaclab) 는 절대 종료하지 마세요."
else
    ok "가용 메모리 충분"
fi
echo ""

# ── 3. Walking RL 프로세스 보호 (관찰만) ───────────────────────────────────────
echo "[3/5] Walking RL 프로세스 (정보만, 종료 금지)"
WALKING_RL_PIDS=$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>/dev/null | grep -i "env_isaaclab" || true)
if [ -n "${WALKING_RL_PIDS}" ]; then
    info "Walking RL 학습 진행 중 — 절대 kill 금지"
    echo "${WALKING_RL_PIDS}" | sed 's/^/         /'
    info "본 학습은 Walking RL 의 잔여 자원만 사용합니다."
else
    info "Walking RL 미실행"
fi
echo ""

# ── 4. Ollama gemma3 점검 ──────────────────────────────────────────────────────
echo "[4/5] Ollama gemma3 (로드 시 17 GB 점유 위험)"
OLLAMA_GPU=$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>/dev/null | grep -i "ollama" || true)
if [ -n "${OLLAMA_GPU}" ]; then
    fail "Ollama 가 GPU 점유 중"
    echo "${OLLAMA_GPU}" | sed 's/^/         /'
    echo "         → 학습 시작 전 모델 unload 권장: curl http://localhost:11434/api/generate -d '{\"model\":\"\",\"keep_alive\":0}'"
    echo "         → 또는 ollama 본인 사용 시: ollama stop <model_name>"
else
    ok "Ollama GPU 미점유 (대기 상태)"
fi
echo ""

# ── 5. 디스크 가용량 ───────────────────────────────────────────────────────────
echo "[5/5] 디스크 가용량 (/home/laba)"
DISK_AVAIL_KB=$(df -P /home/laba | awk 'NR==2 {print $4}')
DISK_AVAIL_GB=$((DISK_AVAIL_KB / 1024 / 1024))
DISK_REQUIRED_GB=50  # 체크포인트 + HF 캐시 + WandB 캐시 합계 보수적 추정

info "가용 디스크: ${DISK_AVAIL_GB} GiB"
info "필요 추정:   ${DISK_REQUIRED_GB} GiB"

if [ "${DISK_AVAIL_GB}" -lt "${DISK_REQUIRED_GB}" ]; then
    fail "디스크 부족 (${DISK_AVAIL_GB} < ${DISK_REQUIRED_GB} GiB)"
else
    ok "디스크 충분"
fi
echo ""

# ── 결과 ───────────────────────────────────────────────────────────────────────
echo "=========================================================="
if $PASS; then
    echo " preflight PASS — 학습 진행 가능"
    echo "=========================================================="
    exit 0
else
    echo " preflight FAIL — 위 [FAIL] 항목 해결 후 재시도"
    echo "=========================================================="
    echo ""
    echo " ⚠ Walking RL / 다른 사용자 프로세스는 절대 건드리지 마세요."
    echo "   본인 프로세스(Jupyter 커널, 본인 Ollama, 본인 다른 학습) 만 정리하세요."
    exit 1
fi
