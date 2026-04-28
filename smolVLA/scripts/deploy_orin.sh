#!/bin/bash
# devPC → Orin 배포 스크립트
# 실행 위치: devPC (어디서든)
# 사용:    bash smolVLA/scripts/deploy_orin.sh
#
# orin/ 디렉토리가 curated lerobot 포함 전체 배포 패키지이므로 orin/ 하나만 동기화.
# Orin 측 배포 경로: /home/laba/smolvla/orin/ (dgx 와 형제 구조 유지)
# venv 는 /home/laba/smolvla/orin/.hylion_arm (orin 디렉터리 안쪽, dgx/.arm_finetune 과 격리)

ORIN_HOST="orin"
ORIN_DEST="/home/laba/smolvla/orin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SMOLVLA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC="${SMOLVLA_ROOT}/orin/"

echo "[deploy] ${SRC} → ${ORIN_HOST}:${ORIN_DEST}/"

rsync -avz --delete \
    --exclude '.hylion_arm' \
    --exclude 'calibration' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    --exclude '.git' \
    "$SRC" "${ORIN_HOST}:${ORIN_DEST}/"

echo "[deploy] 완료. Orin에서 초기 설치가 필요하면:"
echo "  ssh orin"
echo "  bash ~/smolvla/orin/scripts/setup_env.sh"
echo "  source ~/smolvla/orin/.hylion_arm/bin/activate"
echo ""
echo "[deploy] ⚠ 배포 경로 변경 알림 (2026-04-28):"
echo "         이전 배포는 ~/smolvla/ 에 직접 풀어졌으나, 현재는 ~/smolvla/orin/ 으로 변경됨."
echo "         Orin 에 옛 경로 잔존 여부 확인 후 정리 필요:"
echo ""
echo "  ssh orin"
echo "  ls ~/smolvla/                                  # lerobot/ scripts/ 등 옛 파일이 있으면 정리 대상"
echo "  deactivate 2>/dev/null || true                 # 옛 venv 활성화 상태 해제"
echo "  rm -rf ~/smolvla/.venv ~/smolvla/lerobot       # 옛 venv·lerobot (이전 컨벤션)"
echo "  rm -rf ~/smolvla/scripts ~/smolvla/calibration ~/smolvla/examples"
echo "  rm -f ~/smolvla/pyproject.toml ~/smolvla/README.md"
echo "  bash ~/smolvla/orin/scripts/setup_env.sh       # 새 venv 생성"