#!/bin/bash
# DGX Spark 측 dummy 체크포인트 생성 (TODO-10 검증 용도)
# 실행 위치: DGX (~/smolvla/dgx/scripts/save_dummy_checkpoint.sh)
#
# 목적:
#   sync_ckpt_dgx_to_orin.sh 와 load_checkpoint_test.py 검증을 위한
#   "DGX 학습 산출물" 형태의 체크포인트 1개 생성.
#   smoke_test.sh 와 달리 --save_checkpoint=true 로 디스크에 체크포인트 저장.
#
# 산출 경로:
#   ~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/
#       config.json
#       train_config.json
#       model.safetensors          (≈ 900 MB)
#
# 소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)
# 디스크: 약 4~8 GB (HF 캐시 + 체크포인트)

set -e

SMOLVLA_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DGX_DIR="${SMOLVLA_DIR}/dgx"
VENV_DIR="${DGX_DIR}/.arm_finetune"
RUN_NAME="dummy_ckpt"
OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"

# ── 1. preflight ──────────────────────────────────────────────────────────────
echo "[dummy-ckpt] preflight check 실행..."
bash "${DGX_DIR}/scripts/preflight_check.sh" smoke || {
    echo "[dummy-ckpt] preflight FAIL — 중단"
    exit 1
}

# ── 2. venv 활성화 보장 ────────────────────────────────────────────────────────
if [ -z "${VIRTUAL_ENV:-}" ] || [ "${VIRTUAL_ENV}" != "${VENV_DIR}" ]; then
    source "${VENV_DIR}/bin/activate"
fi

# ── 3. 기존 dummy_ckpt 정리 (재실행 가능하게) ──────────────────────────────────
if [ -d "${OUTPUT_DIR}" ]; then
    echo "[dummy-ckpt] 기존 ${OUTPUT_DIR} 발견 — 제거 후 재생성"
    rm -rf "${OUTPUT_DIR}"
fi

# ── 4. 1 step 학습 + 체크포인트 저장 ──────────────────────────────────────────
echo ""
echo "=========================================================="
echo " save_dummy_checkpoint — lerobot-train --steps=1 --save_checkpoint=true"
echo "=========================================================="
echo "  output_dir: ${OUTPUT_DIR}"
echo "  최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."
echo "=========================================================="
echo ""

START_TS=$(date +%s)
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=lerobot/svla_so100_pickplace \
    --batch_size=8 \
    --steps=1 \
    --log_freq=1 \
    --save_freq=1 \
    --save_checkpoint=true \
    --num_workers=4 \
    --output_dir="${OUTPUT_DIR}" \
    --job_name=${RUN_NAME} \
    --policy.device=cuda \
    --policy.push_to_hub=false \
    --rename_map='{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
    --wandb.enable=false
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

# ── 5. 산출물 검증 ────────────────────────────────────────────────────────────
CKPT_DIR="${OUTPUT_DIR}/checkpoints/000001/pretrained_model"
if [ ! -d "${CKPT_DIR}" ]; then
    echo "[dummy-ckpt] ERROR: 체크포인트 디렉터리 미생성: ${CKPT_DIR}"
    exit 1
fi

echo ""
echo "=========================================================="
echo " dummy 체크포인트 생성 완료"
echo "=========================================================="
echo "  소요 시간:        ${ELAPSED} 초"
echo "  체크포인트 경로:  ${CKPT_DIR}"
echo ""
echo "  내용:"
ls -la "${CKPT_DIR}" | sed 's/^/    /'
echo ""
echo "  → 다음: devPC 에서 sync_ckpt_dgx_to_orin.sh 실행"
echo "          bash scripts/sync_ckpt_dgx_to_orin.sh --run ${RUN_NAME}"
echo "=========================================================="
