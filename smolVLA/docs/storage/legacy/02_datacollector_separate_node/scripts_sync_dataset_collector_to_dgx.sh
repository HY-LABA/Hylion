#!/bin/bash
# DataCollector 수집 dataset → DGX 학습 환경 전송 (devPC 경유 2-hop)
#
# 실행 위치: devPC (어디서든)
#
# 사용:
#   bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <name>          # 특정 dataset
#   bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset all             # 전체 dataset
#   bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <name> --dry-run
#
# 동작:
#   1. pre-check: SSH alias 존재 확인 (datacollector, dgx)
#   2. DataCollector → devPC 임시 디렉터리 rsync
#   3. devPC → DGX rsync
#   4. devPC 임시 정리 + DGX 측 파일 수 검증
#
# 네트워크 경로:
#   DataCollector (시연장) → devPC (2-hop hub) → DGX (연구실)
#   DataCollector ↔ DGX 가 다른 서브넷에 있으므로 devPC 경유 (sync_ckpt_dgx_to_orin.sh 패턴 동일).
#   동일 서브넷이면 직접 rsync 도 가능 (본 스크립트는 2-hop 가정).
#
# exclude 패턴:
#   __pycache__/, *.pyc, .git/ — 캐시·git 메타 제외
#   .hylion_collector/ — venv 제외
#
# 결정 근거: 04_infra_setup spec TODO-T1 / docs/storage/09_datacollector_setup.md §5-3

set -e

DATACOLLECTOR_HOST="datacollector"
DGX_HOST="dgx"
DATACOLLECTOR_DATA="/home/laba/smolvla/datacollector/data"
DGX_DATA_BASE="/home/laba/smolvla/dgx/data"

DATASET=""
DRY_RUN=""

# ── 인자 파싱 ──────────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --dataset)  DATASET="$2"; shift 2 ;;
        --dry-run)  DRY_RUN="--dry-run"; shift ;;
        -h|--help)
            echo "사용: bash $0 --dataset <name|all> [--dry-run]"
            echo ""
            echo "  --dataset <name>  특정 dataset 이름 (datacollector:~/smolvla/datacollector/data/<name>/)"
            echo "  --dataset all     data/ 전체 동기화"
            echo "  --dry-run         rsync dry-run 모드 (실제 전송 없이 목록만 확인)"
            echo ""
            echo "필요 조건:"
            echo "  ~/.ssh/config 에 'Host datacollector', 'Host dgx' alias 등록"
            echo "  docs/storage/09_datacollector_setup.md §5-1 참조"
            exit 0
            ;;
        *) echo "[sync-dataset] 알 수 없는 옵션: $1 (--help 참조)"; exit 1 ;;
    esac
done

# ── 필수 인자 확인 ─────────────────────────────────────────────────────────────
if [ -z "${DATASET}" ]; then
    echo "[sync-dataset] ERROR: --dataset <name|all> 필수 인자 없음."
    echo "  사용 예: bash $0 --dataset my_dataset --dry-run"
    exit 1
fi

# ── pre-check: SSH alias 존재 확인 ────────────────────────────────────────────
if ! grep -q "^Host datacollector" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-dataset] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다."
    echo "  docs/storage/09_datacollector_setup.md §5-1 을 참조하여 SSH alias 를 먼저 등록하세요."
    exit 1
fi

if ! grep -q "^Host dgx" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-dataset] ERROR: ~/.ssh/config 에 'Host dgx' alias 가 없습니다."
    echo "  docs/storage/04_devnetwork.md §5 를 참조하여 SSH alias 를 먼저 등록하세요."
    exit 1
fi

# ── 소스·목적 경로 결정 ────────────────────────────────────────────────────────
if [ "${DATASET}" = "all" ]; then
    DC_SRC="${DATACOLLECTOR_DATA}/"
    DGX_DEST="${DGX_DATA_BASE}/"
    DATASET_LABEL="(all)"
else
    DC_SRC="${DATACOLLECTOR_DATA}/${DATASET}/"
    DGX_DEST="${DGX_DATA_BASE}/${DATASET}/"
    DATASET_LABEL="${DATASET}"
fi

# ── DataCollector 측 경로 존재 확인 (dry-run 이 아닌 경우만) ──────────────────
if [ -z "${DRY_RUN}" ]; then
    if ! ssh "${DATACOLLECTOR_HOST}" "test -d ${DC_SRC%/}" 2>/dev/null; then
        echo "[sync-dataset] ERROR: DataCollector 측 경로 없음: ${DC_SRC%/}"
        echo "  lerobot-record 로 먼저 dataset 수집 후 재실행하세요."
        exit 1
    fi
fi

# ── devPC 임시 디렉터리 ────────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d -t smolvla_dataset_XXXXXX)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo ""
echo "=========================================================="
echo " sync_dataset_collector_to_dgx"
echo "=========================================================="
echo "  DataCollector SRC: ${DATACOLLECTOR_HOST}:${DC_SRC}"
echo "  devPC TMP:         ${TMP_DIR}/"
echo "  DGX DEST:          ${DGX_HOST}:${DGX_DEST}"
echo "  dataset:           ${DATASET_LABEL}"
echo "  dry-run:           ${DRY_RUN:-(off)}"
echo "=========================================================="
echo ""

# ── 1. DataCollector → devPC ──────────────────────────────────────────────────
# set -e 가 rsync non-zero 반환 시 즉시 abort 보장 (BACKLOG 02 #9 버그 2 대응).
echo "[sync-dataset] (1/2) DataCollector → devPC ..."
rsync -avz ${DRY_RUN} \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.hylion_collector/' \
    "${DATACOLLECTOR_HOST}:${DC_SRC}" "${TMP_DIR}/"

# ── 2. devPC → DGX ────────────────────────────────────────────────────────────
# set -e 가 rsync non-zero 반환 시 즉시 abort 보장 (BACKLOG 02 #9 버그 2 대응).
echo ""
echo "[sync-dataset] (2/2) devPC → DGX ..."
if [ -z "${DRY_RUN}" ]; then
    ssh "${DGX_HOST}" "mkdir -p ${DGX_DEST}"
fi
rsync -avz ${DRY_RUN} --delete \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    "${TMP_DIR}/" "${DGX_HOST}:${DGX_DEST}"

# ── 3. DGX 측 검증 ─────────────────────────────────────────────────────────────
if [ -z "${DRY_RUN}" ]; then
    echo ""
    echo "[sync-dataset] DGX 측 파일 검증..."
    FILE_COUNT=$(ssh "${DGX_HOST}" "find ${DGX_DEST} -type f 2>/dev/null | wc -l")
    echo "[sync-dataset] DGX 전송 파일 수: ${FILE_COUNT}"
    if [ "${FILE_COUNT}" -eq 0 ]; then
        echo "[sync-dataset] WARN: DGX 에 파일이 없습니다. DataCollector 소스 확인 필요."
    fi
    ssh "${DGX_HOST}" "ls -la ${DGX_DEST}" | sed 's/^/    /'
fi

echo ""
echo "=========================================================="
echo " 완료. DGX 에서 dataset 로드 검증:"
echo ""
echo "  ssh ${DGX_HOST}"
echo "  source ~/smolvla/dgx/.arm_finetune/bin/activate"
echo "  python -c \\"
echo "    'from lerobot.datasets.lerobot_dataset import LeRobotDataset; \\"
echo "     ds = LeRobotDataset(\"${DATASET_LABEL}\", root=\"${DGX_DEST}\"); print(ds)'"
echo ""
echo " HF Hub 방식 사용 시:"
echo "  datacollector/scripts/push_dataset_hub.sh --dataset ${DC_SRC%/} --repo-id <HF_USER>/<REPO>"
echo "=========================================================="
