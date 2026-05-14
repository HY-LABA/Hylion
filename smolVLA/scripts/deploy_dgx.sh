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
    --exclude 'gestures/*/' \
    --exclude 'finetune/*/config/base_config.yaml' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    "${SMOLVLA_ROOT}/dgx/" "${DGX_HOST}:${DGX_DEST}/dgx/"
# 참고: 'gestures/*/' — gesture 데이터셋(parquet)은 DGX local-only 자산. repo 는 gestures/README.md
#       (구조) 만 추적하므로, --delete 가 DGX 의 wave_hello* 데이터셋을 삭제하지 않도록 보호.
#       .gitignore 의 'dgx/gestures/*/' 패턴과 일치.
# 참고: 'finetune/*/config/base_config.yaml' — base_config 의 hardware 섹션(포트·카메라
#       인덱스)은 DGX 세션마다 직접 갱신하는 로컬 값. --delete rsync 가 repo 의 null
#       템플릿으로 덮어쓰지 않도록 제외. 안정값 필드(robot/teleop/cameras/calibration/
#       paths/accounts) 변경 시엔 해당 파일만 수동 rsync 필요. (사용자 결정 2026-05-14)

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
echo "  bash ~/smolvla/dgx/scripts/setup_finetune_env.sh"
echo "  source ~/smolvla/dgx/.arm_finetune/bin/activate"
echo "  bash ~/smolvla/dgx/scripts/smoke_test.sh"
