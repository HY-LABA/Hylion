#!/bin/bash
set -e
# devPC → DataCollector 배포 스크립트
# 실행 위치: devPC (어디서든)
# 사용:    bash smolVLA/scripts/deploy_datacollector.sh [--dry-run]
#
# DataCollector 데이터 수집 환경에 필요한 것:
#   - datacollector/                        (데이터 수집 스크립트·환경)
#   - docs/reference/lerobot/              (editable 설치 대상 submodule)
#   - docs/storage/09_datacollector_setup.md  (셋업 참고용)
#
# orin 과 달리 DataCollector 는 lerobot 코드를 직접 수정하지 않으므로
# docs/reference/lerobot/ submodule 자체를 그대로 사용합니다.
# 수집된 data/ 는 동기화 제외 (데이터 전송은 TODO-T1 스크립트 책임).
#
# SSH alias 'datacollector' 는 ~/.ssh/config 에 등록 필요.
# 참조: docs/storage/09_datacollector_setup.md §5 SSH 설정

DATACOLLECTOR_HOST="datacollector"
DATACOLLECTOR_DEST="/home/laba/smolvla"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SMOLVLA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DRY_RUN=false
RSYNC_DRY_RUN_FLAG=""

# --dry-run 플래그 처리
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    RSYNC_DRY_RUN_FLAG="-n"
    echo "[deploy-datacollector] --dry-run 모드: 실제 전송 없이 동작 확인만 수행합니다."
    echo ""
fi

# ──────────────────────────────────────────────
# pre-check 1: SSH alias 존재 확인
# ──────────────────────────────────────────────
if ! grep -q "^Host datacollector" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[deploy-datacollector] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다."
    echo "  docs/storage/09_datacollector_setup.md §5-1 을 참조하여 SSH alias 를 먼저 등록하세요."
    exit 1
fi

# ──────────────────────────────────────────────
# pre-check 2: 대상 디렉터리 사전 생성
# (BACKLOG 02 #9 버그1 — 대상 디렉터리 미생성 → rsync 실패 패턴 답습 X)
# ──────────────────────────────────────────────
if [[ "${DRY_RUN}" == false ]]; then
    echo "[deploy-datacollector] 원격 디렉터리 사전 생성 중..."
    ssh "${DATACOLLECTOR_HOST}" "mkdir -p \
        ${DATACOLLECTOR_DEST}/datacollector \
        ${DATACOLLECTOR_DEST}/docs/reference/lerobot \
        ${DATACOLLECTOR_DEST}/docs/storage"
fi

# ──────────────────────────────────────────────
# 동기화 1: datacollector/ → DataCollector
# ──────────────────────────────────────────────
echo "[deploy-datacollector] datacollector/ → ${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/datacollector/"
rsync -avz ${RSYNC_DRY_RUN_FLAG} --delete \
    --exclude '.hylion_collector' \
    --exclude 'data/' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    --exclude '.git' \
    --exclude '.gitignore' \
    "${SMOLVLA_ROOT}/datacollector/" \
    "${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/datacollector/" \
    || { echo "[deploy-datacollector] ERROR: datacollector/ rsync 실패"; exit 1; }

# ──────────────────────────────────────────────
# 동기화 2: docs/reference/lerobot/ → DataCollector
# (editable 설치 대상 — datacollector/ 의 pyproject.toml 이 lerobot 을 -e 로 설치)
# ──────────────────────────────────────────────
echo ""
echo "[deploy-datacollector] docs/reference/lerobot/ → ${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/docs/reference/lerobot/"
echo "[deploy-datacollector]   (editable 설치 대상 — 약 수백 MB, 최초 1회는 시간이 걸립니다)"
rsync -avz ${RSYNC_DRY_RUN_FLAG} --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.egg-info' \
    --exclude 'tests/outputs' \
    "${SMOLVLA_ROOT}/docs/reference/lerobot/" \
    "${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/docs/reference/lerobot/" \
    || { echo "[deploy-datacollector] ERROR: docs/reference/lerobot/ rsync 실패"; exit 1; }

# ──────────────────────────────────────────────
# 동기화 3: docs/storage/09_datacollector_setup.md → DataCollector (참고용)
# ──────────────────────────────────────────────
echo ""
echo "[deploy-datacollector] docs/storage/09_datacollector_setup.md → ${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/docs/storage/"
rsync -avz ${RSYNC_DRY_RUN_FLAG} \
    "${SMOLVLA_ROOT}/docs/storage/09_datacollector_setup.md" \
    "${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/docs/storage/" \
    || { echo "[deploy-datacollector] ERROR: 09_datacollector_setup.md rsync 실패"; exit 1; }

# ──────────────────────────────────────────────
# post-check: rsync 모두 성공 (set -e + || exit 1 로 이미 보장)
# (BACKLOG 02 #9 버그2 — rsync 실패 후 exit 0 덮어씀 패턴 답습 X)
# ──────────────────────────────────────────────
echo ""
if [[ "${DRY_RUN}" == true ]]; then
    echo "[deploy-datacollector] --dry-run 완료. 실제 배포는 --dry-run 플래그 없이 재실행하세요."
else
    echo "[deploy-datacollector] 완료. DataCollector 에서 초기 설치가 필요하면:"
    echo "  ssh datacollector"
    echo "  bash ~/smolvla/datacollector/scripts/setup_env.sh"
    echo "  source ~/smolvla/datacollector/.hylion_collector/bin/activate"
    echo ""
    echo "[deploy-datacollector] 환경 검증:"
    echo "  ssh datacollector 'source ~/smolvla/datacollector/.hylion_collector/bin/activate && lerobot-find-port'"
    echo "  ssh datacollector 'source ~/smolvla/datacollector/.hylion_collector/bin/activate && lerobot-find-cameras opencv'"
    echo ""
    echo "[deploy-datacollector] 수집된 dataset 전송은 TODO-T1 스크립트 (sync_dataset_collector_to_dgx.sh) 책임."
    echo "  data/ 는 본 스크립트에서 의도적으로 제외됩니다."
fi
