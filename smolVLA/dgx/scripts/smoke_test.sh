#!/bin/bash
# DGX Spark SmolVLA 1 step 학습 smoke test
# 실행 위치: DGX (~/smolvla/dgx/scripts/smoke_test.sh)
#
# 검증 목표:
#   - lerobot-train CLI 동작
#   - smolvla_base 가중치 다운로드 + 로드
#   - lerobot/svla_so100_pickplace 데이터셋 다운로드 + 로드
#   - 1 step forward / backward / optimizer step 통과
#   - GPU 점유 / 메모리 점유 실측 (06_smolvla_finetune_feasibility.md §5 갱신용)
#
# 결정 근거: docs/lerobot_study/06_smolvla_finetune_feasibility.md §6.1
#   smolvla.mdx 공식 학습 명령 + steps=1 만 변경 (개발 검증 목적)

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DGX_DIR="${SMOLVLA_DIR}/dgx"
VENV_DIR="${DGX_DIR}/.arm_finetune"
RUN_ID="$(date +%Y-%m-%d_%H-%M-%S)"
OUTPUT_DIR="${DGX_DIR}/outputs/smoke_test/${RUN_ID}"

# ── 1. venv 활성화 보장 ────────────────────────────────────────────────────────
if [ -z "${VIRTUAL_ENV:-}" ] || [ "${VIRTUAL_ENV}" != "${VENV_DIR}" ]; then
    source "${VENV_DIR}/bin/activate"
fi

# ── 2. preflight (smoke 시나리오) ──────────────────────────────────────────────
echo "[smoke] preflight check 실행..."
bash "${DGX_DIR}/scripts/preflight_check.sh" smoke || {
    echo "[smoke] preflight FAIL — smoke test 중단"
    exit 1
}

# ── 3. 1 step 학습 실행 ────────────────────────────────────────────────────────
echo ""
echo "=========================================================="
echo " smoke test — lerobot-train --steps=1"
echo "=========================================================="
echo "  policy: lerobot/smolvla_base"
echo "  dataset: lerobot/svla_so100_pickplace"
echo "  output:  ${OUTPUT_DIR}"
echo ""
echo "  최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."
echo "=========================================================="
echo ""

# 백그라운드에서 1초 간격으로 nvidia-smi / free -m 샘플링
SAMPLE_DIR="${DGX_DIR}/outputs/resource_samples"
SAMPLE_LOG="${SAMPLE_DIR}/smoke_test_${RUN_ID}.log"
mkdir -p "${SAMPLE_DIR}"

(
    while true; do
        echo "=== $(date +%H:%M:%S) ===" >> "${SAMPLE_LOG}"
        nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv,noheader >> "${SAMPLE_LOG}" 2>&1
        free -m | awk '/^Mem:/ {print "MemMiB used=" $3 ", available=" $7}' >> "${SAMPLE_LOG}"
        free -m | awk '/^Swap:/ {print "SwapMiB used=" $3 ", free=" $4}' >> "${SAMPLE_LOG}"
        echo "" >> "${SAMPLE_LOG}"
        sleep 1
    done
) &
SAMPLER_PID=$!
trap "kill ${SAMPLER_PID} 2>/dev/null || true" EXIT

# 학습 실행
START_TS=$(date +%s)
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=lerobot/svla_so100_pickplace \
    --batch_size=8 \
    --steps=1 \
    --log_freq=1 \
    --num_workers=4 \
    --save_checkpoint=false \
    --output_dir="${OUTPUT_DIR}" \
    --job_name=smoke_test \
    --policy.device=cuda \
    --policy.push_to_hub=false \
    --rename_map='{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
    --wandb.enable=false
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

kill ${SAMPLER_PID} 2>/dev/null || true

echo ""
echo "=========================================================="
echo " smoke test 결과"
echo "=========================================================="
echo "  소요 시간:        ${ELAPSED} 초"
echo "  output_dir:       ${OUTPUT_DIR}"
echo "  resource samples: ${SAMPLE_LOG}"
echo ""
echo "  자원 점유 피크 (nvidia-smi 샘플링 결과):"
if [ -f "${SAMPLE_LOG}" ]; then
    PEAK_GPU=$(awk -F',' '/%/ {gsub(" %",""); if($1>max)max=$1} END {print max}' "${SAMPLE_LOG}")
    PEAK_MEM=$(awk -F',' '/%/ && /MiB/ {gsub(" MiB","",$2); if($2>max)max=$2} END {if(max=="") print "N/A"; else print max}' "${SAMPLE_LOG}")
    PEAK_SYS_MEM=$(awk -F'[=,]' '/MemMiB/ {gsub(" ","",$2); if($2>max)max=$2} END {if(max!="") print max}' "${SAMPLE_LOG}")
    echo "    GPU util peak:    ${PEAK_GPU} %"
    if [ "${PEAK_MEM}" = "N/A" ]; then
        echo "    GPU mem used:     N/A (GB10 UMA)"
    else
        echo "    GPU mem used:     ${PEAK_MEM} MiB"
    fi
    echo "    System RAM used:  ${PEAK_SYS_MEM} MiB"
fi
echo ""
echo "  → 본 결과를 docs/lerobot_study/06_smolvla_finetune_feasibility.md §5 표에 갱신하세요."
echo "=========================================================="
