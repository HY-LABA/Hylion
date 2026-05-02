#!/bin/bash
# DGX 학습 체크포인트 → DataCollector 전송 (케이스 3 우회 경로)
#
# 실행 위치: devPC (어디서든)
#
# 사용:
#   bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh                                # 가장 최근 run 의 last 체크포인트
#   bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --run leftarm_v1               # 특정 run, last 체크포인트
#   bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --run leftarm_v1 --step 020000 # 특정 run + step
#   bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run                      # rsync dry-run
#
# 목적 (케이스 3 우회 경로):
#   시연장 Orin 이 인터넷 격리 또는 devPC·DGX 와 다른 서브넷 → 직접 전송 불가.
#   DataCollector 는 시연장 WiFi 에 위치하여 Orin 과 동일 서브넷 접근 가능.
#   본 스크립트는 DGX → DataCollector 까지 전송하고,
#   DataCollector → Orin 전송은 사용자 직접 또는 deploy_orin.sh/수동 rsync 로 수행.
#
# 케이스 분류 (docs/storage/others/ckpt_transfer_scenarios.md 참조):
#   케이스 1: 시연장 Orin 과 devPC·DGX 동일 광역 네트워크 → sync_ckpt_dgx_to_orin.sh 직접 사용
#   케이스 2: Orin 인터넷 가능, 다른 서브넷 → sync_ckpt_dgx_to_orin.sh devPC 2-hop 그대로 사용
#   케이스 3: Orin 인터넷 격리 → 본 스크립트 (DGX → DataCollector) + 수동 DataCollector → Orin
#   케이스 4: Orin USB 드라이브만 가능 → USB 절차 (docs/storage/others/ckpt_transfer_scenarios.md §4)
#
# 전제 조건:
#   - ~/.ssh/config 에 dgx, datacollector SSH alias 모두 등록
#   - DataCollector 에서 Orin 의 SSH alias 또는 IP 확인 필요 (DataCollector → Orin 2단계 시)
#   - devPC 가 DGX 와 DataCollector 양쪽 SSH 접근 가능
#
# 동작:
#   1. SSH 로 DGX 의 체크포인트 경로 식별
#   2. DGX → devPC 임시 디렉터리 (/tmp/smolvla_ckpt_<ts>/) rsync
#   3. devPC → DataCollector (~/smolvla/ckpt_transfer/<run>/<step>/) rsync
#   4. devPC 임시 정리 + DataCollector 측 파일 크기 검증
#   5. 다음 단계 안내 (DataCollector → Orin 수동 전송)
#
# 결정 근거: 04_infra_setup spec TODO-T2 / docs/storage/others/ckpt_transfer_scenarios.md

set -e

DGX_HOST="dgx"
DATACOLLECTOR_HOST="datacollector"
DGX_OUTPUTS="/home/laba/smolvla/dgx/outputs/train"
DATACOLLECTOR_CKPT_BASE="/home/laba/smolvla/ckpt_transfer"

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
            echo "  --dry-run rsync dry-run 모드 (실제 전송 없이 확인만)"
            echo ""
            echo "케이스 분류:"
            echo "  본 스크립트는 케이스 3 (시연장 Orin 인터넷 격리) 전용."
            echo "  케이스 1·2 는 sync_ckpt_dgx_to_orin.sh 직접 사용."
            echo "  전체 케이스 설명: docs/storage/others/ckpt_transfer_scenarios.md"
            exit 0
            ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
done

# ── pre-check: SSH alias 확인 ──────────────────────────────────────────────────
if ! grep -q "^Host dgx" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-ckpt-dc] ERROR: ~/.ssh/config 에 'Host dgx' alias 가 없습니다."
    echo "  docs/storage/04_devnetwork.md §5 를 참조하여 SSH alias 를 먼저 등록하세요."
    exit 1
fi

if ! grep -q "^Host datacollector" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-ckpt-dc] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다."
    echo "  docs/storage/09_datacollector_setup.md §5-1 을 참조하여 SSH alias 를 먼저 등록하세요."
    exit 1
fi

# ── 1. DGX 의 체크포인트 경로 식별 ─────────────────────────────────────────────
if [ -z "${RUN}" ]; then
    echo "[sync-ckpt-dc] --run 미지정 — DGX 의 가장 최근 run 자동 선택"
    RUN=$(ssh "${DGX_HOST}" "ls -1t ${DGX_OUTPUTS} 2>/dev/null | head -1")
    if [ -z "${RUN}" ]; then
        echo "[sync-ckpt-dc] ERROR: DGX 에 학습 산출물 없음 (${DGX_OUTPUTS})"
        exit 1
    fi
    echo "[sync-ckpt-dc] 자동 선택: run=${RUN}"
fi

if [ -z "${STEP}" ]; then
    # checkpoints/last 심볼릭 링크가 가리키는 step 추출
    STEP=$(ssh "${DGX_HOST}" "readlink ${DGX_OUTPUTS}/${RUN}/checkpoints/last 2>/dev/null | xargs -r basename")
    if [ -z "${STEP}" ]; then
        # last 없으면 가장 큰 step 번호
        STEP=$(ssh "${DGX_HOST}" "ls -1 ${DGX_OUTPUTS}/${RUN}/checkpoints 2>/dev/null | grep -E '^[0-9]+$' | sort -n | tail -1")
    fi
    if [ -z "${STEP}" ]; then
        echo "[sync-ckpt-dc] ERROR: ${DGX_OUTPUTS}/${RUN}/checkpoints 에 step 디렉터리 없음"
        exit 1
    fi
    echo "[sync-ckpt-dc] 자동 선택: step=${STEP}"
fi

DGX_SRC="${DGX_OUTPUTS}/${RUN}/checkpoints/${STEP}/pretrained_model"
DATACOLLECTOR_DEST="${DATACOLLECTOR_CKPT_BASE}/${RUN}/${STEP}"

# DGX 측 존재 확인
if ! ssh "${DGX_HOST}" "test -d ${DGX_SRC}"; then
    echo "[sync-ckpt-dc] ERROR: DGX 측 경로 없음: ${DGX_SRC}"
    exit 1
fi

# ── 2. devPC 임시 디렉터리 ─────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d -t smolvla_ckpt_XXXXXX)"
trap "rm -rf ${TMP_DIR}" EXIT

echo ""
echo "=========================================================="
echo " sync_ckpt_dgx_to_datacollector (케이스 3 우회 경로)"
echo "=========================================================="
echo "  DGX SRC:            ${DGX_HOST}:${DGX_SRC}"
echo "  devPC TMP:          ${TMP_DIR}"
echo "  DataCollector DEST: ${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}"
echo "  dry-run:            ${DRY_RUN:-(off)}"
echo ""
echo "  [다음 단계] DataCollector → Orin 전송은 수동 수행 필요"
echo "  (케이스 3: 시연장 Orin 인터넷 격리로 직접 전송 불가)"
echo "=========================================================="
echo ""

# ── 3. DGX → devPC ────────────────────────────────────────────────────────────
echo "[sync-ckpt-dc] (1/2) DGX → devPC ..."
rsync -avz ${DRY_RUN} \
    "${DGX_HOST}:${DGX_SRC}/" "${TMP_DIR}/"

# ── 4. devPC → DataCollector ──────────────────────────────────────────────────
echo ""
echo "[sync-ckpt-dc] (2/2) devPC → DataCollector ..."
if [ -z "${DRY_RUN}" ]; then
    ssh "${DATACOLLECTOR_HOST}" "mkdir -p ${DATACOLLECTOR_DEST}"
fi
rsync -avz ${DRY_RUN} --delete \
    "${TMP_DIR}/" "${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/"

# ── 5. DataCollector 측 검증 ───────────────────────────────────────────────────
if [ -z "${DRY_RUN}" ]; then
    echo ""
    echo "[sync-ckpt-dc] DataCollector 측 파일 검증..."
    ssh "${DATACOLLECTOR_HOST}" "ls -la ${DATACOLLECTOR_DEST}/" | sed 's/^/    /'

    # safetensors 헤더 8 byte 읽기 (헤더 무결성 minimal 검증)
    SAFETENSORS_OK=$(ssh "${DATACOLLECTOR_HOST}" \
        "test -f ${DATACOLLECTOR_DEST}/model.safetensors && head -c 8 ${DATACOLLECTOR_DEST}/model.safetensors | wc -c")
    if [ "${SAFETENSORS_OK}" = "8" ]; then
        echo "[sync-ckpt-dc] model.safetensors 헤더 읽기 OK"
    else
        echo "[sync-ckpt-dc] WARN: model.safetensors 헤더 검증 실패 (파일 없거나 손상 가능성)"
    fi
fi

# ── 6. DataCollector → Orin 다음 단계 안내 ─────────────────────────────────────
echo ""
echo "=========================================================="
echo " 완료. DataCollector 에 ckpt 도착:"
echo ""
echo "  DataCollector: ${DATACOLLECTOR_DEST}"
echo ""
echo " [다음 단계 A] DataCollector → Orin rsync (DataCollector 가 Orin 에 SSH 접근 가능한 경우)"
echo ""
echo "  ssh ${DATACOLLECTOR_HOST}"
echo "  ORIN_IP=<시연장 Orin IP>"
echo "  rsync -avz --delete \\"
echo "    ${DATACOLLECTOR_DEST}/ \\"
echo "    laba@\${ORIN_IP}:/home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}/"
echo ""
echo " [다음 단계 B] DataCollector → Orin USB 드라이브 (네트워크 완전 격리 시)"
echo "  docs/storage/others/ckpt_transfer_scenarios.md §케이스 4 참조"
echo ""
echo " [Orin 에서 로드 검증]"
echo "  ssh orin"
echo "  source ~/smolvla/orin/.hylion_arm/bin/activate"
echo "  python ~/smolvla/orin/tests/load_checkpoint_test.py \\"
echo "    --ckpt-path /home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}"
echo "=========================================================="
