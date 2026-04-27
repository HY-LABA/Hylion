#!/usr/bin/env bash
# Hylion/BG smolVLA -> LABA5_Bootcamp/main 단방향 백업 스크립트 (Linux/macOS)
#
# 사용법 (Hylion 루트에서):
#   bash smolVLA/scripts/sync_to_laba5.sh
#   bash smolVLA/scripts/sync_to_laba5.sh --dry-run
#   bash smolVLA/scripts/sync_to_laba5.sh --no-push
#   bash smolVLA/scripts/sync_to_laba5.sh --laba5 /custom/path/LABA5_Bootcamp
#
# 동작:
#   1. Hylion/smolVLA/  ->  LABA5_Bootcamp/smolVLA/  로 rsync mirror (--delete)
#   2. submodule 폴더는 제외 (lerobot, seeed-lerobot, reComputer-Jetson-for-Beginners)
#   3. .git, .venv, __pycache__ 등 위생 폴더 제외
#   4. LABA5_Bootcamp 에서 git add . && git commit && git push
#
# 전제:
#   - LABA5_Bootcamp 가 ~/LABA5_Bootcamp 또는 --laba5 로 지정한 경로에 위치
#   - LABA5_Bootcamp 의 main 브랜치에서 작업 중일 것
#   - LABA5_Bootcamp 에 푸시 권한이 있을 것

set -euo pipefail

# --- arg parsing ---
DRY_RUN=0
NO_PUSH=0
LABA5_PATH="${HOME}/LABA5_Bootcamp"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  DRY_RUN=1; shift ;;
        --no-push)  NO_PUSH=1; shift ;;
        --laba5)    LABA5_PATH="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            echo "unknown arg: $1" >&2
            exit 2
            ;;
    esac
done

# --- paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HYLION_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SRC_SMOLVLA="${HYLION_ROOT}/smolVLA"
DST_SMOLVLA="${LABA5_PATH}/smolVLA"

echo "=== Hylion -> LABA5 smolVLA sync ==="
echo "Source : ${SRC_SMOLVLA}"
echo "Target : ${DST_SMOLVLA}"
echo

# --- preflight ---
[[ -d "${SRC_SMOLVLA}" ]] || { echo "Source not found: ${SRC_SMOLVLA}" >&2; exit 1; }
[[ -d "${LABA5_PATH}" ]]  || { echo "LABA5 path not found: ${LABA5_PATH}" >&2; exit 1; }

LABA5_BRANCH="$(git -C "${LABA5_PATH}" branch --show-current)"
if [[ "${LABA5_BRANCH}" != "main" ]]; then
    echo "LABA5 is on '${LABA5_BRANCH}', expected 'main'." >&2
    echo "Switch first: git -C ${LABA5_PATH} checkout main" >&2
    exit 1
fi

# 대상 부모 디렉토리 보장
mkdir -p "${DST_SMOLVLA}"

# --- rsync ---
RSYNC_OPTS=(
    -a                    # archive (perms, times, recursive)
    --delete              # mirror (소스에 없는 파일은 대상에서도 삭제)
    --exclude='/docs/reference/lerobot/'
    --exclude='/docs/reference/seeed-lerobot/'
    --exclude='/docs/reference/reComputer-Jetson-for-Beginners/'
    --exclude='.git/'
    --exclude='.venv/'
    --exclude='venv/'
    --exclude='__pycache__/'
    --exclude='.pytest_cache/'
    --exclude='.mypy_cache/'
    --exclude='.ruff_cache/'
    --exclude='node_modules/'
    --exclude='.DS_Store'
    --exclude='Thumbs.db'
    --exclude='desktop.ini'
    --exclude='*.pyc'
    --exclude='*.pyo'
)

if [[ "${DRY_RUN}" -eq 1 ]]; then
    RSYNC_OPTS+=(--dry-run --itemize-changes)
    echo "[dry-run] rsync preview:"
fi

# trailing slash 매우 중요: SRC/  -> DST/  (내용물 미러)
rsync "${RSYNC_OPTS[@]}" "${SRC_SMOLVLA}/" "${DST_SMOLVLA}/"
echo "rsync ok"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] stopping before git operations."
    exit 0
fi

# --- git ---
if [[ -z "$(git -C "${LABA5_PATH}" status --porcelain)" ]]; then
    echo "No changes in LABA5. Already in sync."
    exit 0
fi

echo
echo "=== LABA5 git status ==="
git -C "${LABA5_PATH}" status --short
echo

STAMP="$(date '+%Y-%m-%d %H:%M')"
HYLION_SHA="$(git -C "${HYLION_ROOT}" rev-parse --short HEAD)"
MSG="sync: smolVLA from Hylion/BG @ ${HYLION_SHA} (${STAMP})"

git -C "${LABA5_PATH}" add smolVLA/
git -C "${LABA5_PATH}" commit -m "${MSG}"
echo "committed: ${MSG}"

if [[ "${NO_PUSH}" -eq 1 ]]; then
    echo "[--no-push] skipping push."
    exit 0
fi

git -C "${LABA5_PATH}" push origin main
echo "pushed to LABA5/main"
