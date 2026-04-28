#!/bin/bash
# DGX 학습 체크포인트 → Orin 추론 환경 전송 (devPC 경유 2-hop)
# 실행 위치: devPC (어디서든)
# 사용:
#   bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh                                # 가장 최근 run 의 last 체크포인트
#   bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1               # 특정 run, last 체크포인트
#   bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1 --step 020000 # 특정 run + step
#   bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh --dry-run                      # rsync dry-run
#
# 동작:
#   1. SSH 로 DGX 의 체크포인트 경로 식별
#   2. DGX → devPC 임시 디렉터리 (/tmp/smolvla_ckpt_<ts>/) rsync
#   3. devPC → Orin (~/smolvla/orin/checkpoints/<run>/<step>/) rsync
#   4. devPC 임시 정리 + Orin 측 파일 크기 검증
#
# 결정 근거: 02_dgx_setting TODO-10 / repo_management.md (devPC 가 sync hub)

set -e

DGX_HOST="dgx"
ORIN_HOST="orin"
DGX_OUTPUTS="/home/laba/smolvla/dgx/outputs/train"
ORIN_CKPT_BASE="/home/laba/smolvla/orin/checkpoints"

RUN=""
STEP=""
DRY_RUN=""

# ── 인자 파싱 ──────────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --run)      RUN="$2"; shift 2 ;;
        --step)     STEP="$2"; shift 2 ;;
        --dry-run)  DRY_RUN="--dry-run"; shift ;;
        -h|--help)
            echo "사용: bash $0 [--run <name>] [--step <id>] [--dry-run]"
            echo "  --run    체크포인트 run 이름 (생략 시 가장 최근 변경된 run)"
            echo "  --step   체크포인트 step ID (예: 020000, 생략 시 last)"
            echo "  --dry-run rsync dry-run 모드"
            exit 0
            ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

# ── 1. DGX 의 체크포인트 경로 식별 ─────────────────────────────────────────────
if [ -z "${RUN}" ]; then
    echo "[sync-ckpt] --run 미지정 — DGX 의 가장 최근 run 자동 선택"
    RUN=$(ssh "${DGX_HOST}" "ls -1t ${DGX_OUTPUTS} 2>/dev/null | head -1")
    if [ -z "${RUN}" ]; then
        echo "[sync-ckpt] ERROR: DGX 에 학습 산출물 없음 (${DGX_OUTPUTS})"
        exit 1
    fi
    echo "[sync-ckpt] 자동 선택: run=${RUN}"
fi

if [ -z "${STEP}" ]; then
    # checkpoints/last 심볼릭 링크가 가리키는 step 추출
    STEP=$(ssh "${DGX_HOST}" "readlink ${DGX_OUTPUTS}/${RUN}/checkpoints/last 2>/dev/null | xargs -r basename")
    if [ -z "${STEP}" ]; then
        # last 없으면 가장 큰 step 번호
        STEP=$(ssh "${DGX_HOST}" "ls -1 ${DGX_OUTPUTS}/${RUN}/checkpoints 2>/dev/null | grep -E '^[0-9]+$' | sort -n | tail -1")
    fi
    if [ -z "${STEP}" ]; then
        echo "[sync-ckpt] ERROR: ${DGX_OUTPUTS}/${RUN}/checkpoints 에 step 디렉터리 없음"
        exit 1
    fi
    echo "[sync-ckpt] 자동 선택: step=${STEP}"
fi

DGX_SRC="${DGX_OUTPUTS}/${RUN}/checkpoints/${STEP}/pretrained_model"
ORIN_DEST="${ORIN_CKPT_BASE}/${RUN}/${STEP}"

# DGX 측 존재 확인
if ! ssh "${DGX_HOST}" "test -d ${DGX_SRC}"; then
    echo "[sync-ckpt] ERROR: DGX 측 경로 없음: ${DGX_SRC}"
    exit 1
fi

# ── 2. devPC 임시 디렉터리 ─────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d -t smolvla_ckpt_XXXXXX)"
trap "rm -rf ${TMP_DIR}" EXIT

echo ""
echo "=========================================================="
echo " sync_ckpt_dgx_to_orin"
echo "=========================================================="
echo "  DGX SRC:     ${DGX_HOST}:${DGX_SRC}"
echo "  devPC TMP:   ${TMP_DIR}"
echo "  Orin DEST:   ${ORIN_HOST}:${ORIN_DEST}"
echo "  dry-run:     ${DRY_RUN:-(off)}"
echo "=========================================================="
echo ""

# ── 3. DGX → devPC ────────────────────────────────────────────────────────────
echo "[sync-ckpt] (1/2) DGX → devPC ..."
rsync -avz ${DRY_RUN} \
    "${DGX_HOST}:${DGX_SRC}/" "${TMP_DIR}/"

# ── 4. devPC → Orin ───────────────────────────────────────────────────────────
echo ""
echo "[sync-ckpt] (2/2) devPC → Orin ..."
ssh "${ORIN_HOST}" "mkdir -p ${ORIN_DEST}"
rsync -avz ${DRY_RUN} --delete \
    "${TMP_DIR}/" "${ORIN_HOST}:${ORIN_DEST}/"

# ── 5. Orin 측 검증 ────────────────────────────────────────────────────────────
if [ -z "${DRY_RUN}" ]; then
    echo ""
    echo "[sync-ckpt] Orin 측 파일 검증..."
    ssh "${ORIN_HOST}" "ls -la ${ORIN_DEST}/" | sed 's/^/    /'

    # safetensors 헤더 8 byte 읽기 시도 (헤더 무결성 minimal 검증)
    SAFETENSORS_OK=$(ssh "${ORIN_HOST}" "test -f ${ORIN_DEST}/model.safetensors && head -c 8 ${ORIN_DEST}/model.safetensors | wc -c")
    if [ "${SAFETENSORS_OK}" = "8" ]; then
        echo "[sync-ckpt] model.safetensors 헤더 읽기 OK"
    else
        echo "[sync-ckpt] WARN: model.safetensors 헤더 검증 실패"
    fi
fi

echo ""
echo "=========================================================="
echo " 완료. Orin 에서 로드 검증:"
echo ""
echo "  ssh ${ORIN_HOST}"
echo "  source ~/smolvla/orin/.hylion_arm/bin/activate"
echo "  python ~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py \\"
echo "    --ckpt-path ${ORIN_DEST}"
echo "=========================================================="
