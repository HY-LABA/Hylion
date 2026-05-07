#!/bin/bash
set -e
# devPC → DGX Spark 배포 스크립트
# 실행 위치: devPC (어디서든)
# 사용:    bash smolVLA/scripts/deploy_dgx.sh
#
# DGX 학습 환경에 필요한 것:
#   - dgx/                                   (학습 스크립트)
#   - docs/reference/lerobot/                (editable 설치 대상 submodule)
#
# orin/ 과 달리 DGX 는 lerobot 코드를 직접 수정하지 않으므로 docs/reference/lerobot/ submodule
# 자체를 그대로 사용합니다. SmolVLA 분석 시점의 SHA 와 학습 환경 SHA 가 자동 일치.

DGX_HOST="dgx"
DGX_DEST="/home/laba/smolvla"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SMOLVLA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[deploy-dgx] dgx/ → ${DGX_HOST}:${DGX_DEST}/dgx/"
ssh "${DGX_HOST}" "mkdir -p ${DGX_DEST}/dgx ${DGX_DEST}/docs/reference/lerobot"
rsync -avz --delete \
    --exclude '.arm_finetune' \
    --exclude 'outputs' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    "${SMOLVLA_ROOT}/dgx/" "${DGX_HOST}:${DGX_DEST}/dgx/"

echo "[deploy-dgx] docs/reference/lerobot/ → ${DGX_HOST}:${DGX_DEST}/docs/reference/lerobot/"
echo "[deploy-dgx]   (editable 설치 대상 — 약 수백 MB, 최초 1회는 시간이 걸립니다)"
rsync -avz --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    --exclude 'tests/outputs' \
    "${SMOLVLA_ROOT}/docs/reference/lerobot/" "${DGX_HOST}:${DGX_DEST}/docs/reference/lerobot/"

echo ""
echo "[deploy-dgx] 완료. DGX 에서 초기 설치/검증이 필요하면:"
echo "  ssh dgx"
echo "  bash ~/smolvla/dgx/scripts/setup_train_env.sh"
echo "  source ~/smolvla/dgx/.arm_finetune/bin/activate"
echo "  bash ~/smolvla/dgx/scripts/smoke_test.sh"
