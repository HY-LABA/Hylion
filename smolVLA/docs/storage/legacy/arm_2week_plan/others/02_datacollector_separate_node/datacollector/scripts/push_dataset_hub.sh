#!/bin/bash
# DataCollector 수집 dataset → HuggingFace Hub push
#
# 실행 위치: DataCollector 머신 (직접 실행) 또는 devPC 에서 ssh 경유
#
# 사용:
#   bash datacollector/scripts/push_dataset_hub.sh \
#       --dataset ~/smolvla/datacollector/data/<name> \
#       --repo-id <HF_USER>/<REPO_NAME>
#   bash datacollector/scripts/push_dataset_hub.sh \
#       --dataset ~/smolvla/datacollector/data/<name> \
#       --repo-id <HF_USER>/<REPO_NAME> \
#       --private \
#       --dry-run
#
# 동작:
#   1. pre-check: HF_TOKEN 환경변수 또는 huggingface-cli 로그인 확인
#   2. pre-check: dataset 경로 존재 확인
#   3. lerobot LeRobotDataset.push_to_hub() 패턴 활용
#      (docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py:501)
#   4. --dry-run 시 실제 push 없이 환경·경로 확인만
#
# HF Hub 인증:
#   옵션 A (권장): HF_TOKEN 환경변수 설정
#     export HF_TOKEN=hf_xxxxxxxxxx
#     bash push_dataset_hub.sh ...
#   옵션 B: huggingface-cli login 으로 사전 로그인
#     huggingface-cli login
#     bash push_dataset_hub.sh ...
#
# 레퍼런스:
#   lerobot upstream LeRobotDataset.push_to_hub():
#     hub_api.create_repo(repo_id, private=private, repo_type="dataset", exist_ok=True)
#     hub_api.upload_folder(repo_id, folder_path=root, repo_type="dataset")
#     card.push_to_hub(repo_id, repo_type="dataset")
#
# 결정 근거: 04_infra_setup spec TODO-T1 / docs/storage/09_datacollector_setup.md §5-3

set -e

DATASET_PATH=""
REPO_ID=""
PRIVATE_FLAG=""
DRY_RUN=""
BRANCH=""

# ── 인자 파싱 ──────────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --dataset)  DATASET_PATH="$2"; shift 2 ;;
        --repo-id)  REPO_ID="$2"; shift 2 ;;
        --private)  PRIVATE_FLAG="--private"; shift ;;
        --branch)   BRANCH="$2"; shift 2 ;;
        --dry-run)  DRY_RUN="true"; shift ;;
        -h|--help)
            echo "사용: bash $0 --dataset <local_path> --repo-id <hf_user/repo_name> [옵션]"
            echo ""
            echo "필수 인자:"
            echo "  --dataset <path>     로컬 dataset 경로 (예: ~/smolvla/datacollector/data/my_dataset)"
            echo "  --repo-id <id>       HF Hub repo ID (예: myuser/my_robot_dataset)"
            echo ""
            echo "선택 인자:"
            echo "  --private            private repo 로 생성 (기본: public)"
            echo "  --branch <name>      push 대상 branch (기본: main)"
            echo "  --dry-run            실제 push 없이 환경·경로 확인만"
            echo ""
            echo "인증 방법:"
            echo "  export HF_TOKEN=hf_xxxxxxxxxx  # 환경변수 (권장)"
            echo "  huggingface-cli login           # 사전 로그인 (대안)"
            exit 0
            ;;
        *) echo "[push-hub] 알 수 없는 옵션: $1 (--help 참조)"; exit 1 ;;
    esac
done

# ── 필수 인자 확인 ─────────────────────────────────────────────────────────────
if [ -z "${DATASET_PATH}" ]; then
    echo "[push-hub] ERROR: --dataset <local_path> 필수 인자 없음."
    echo "  사용 예: bash $0 --dataset ~/smolvla/datacollector/data/my_dataset --repo-id myuser/my_dataset"
    exit 1
fi

if [ -z "${REPO_ID}" ]; then
    echo "[push-hub] ERROR: --repo-id <hf_user/repo_name> 필수 인자 없음."
    echo "  사용 예: bash $0 --dataset ~/smolvla/datacollector/data/my_dataset --repo-id myuser/my_dataset"
    exit 1
fi

# repo-id 형식 검증 (user/repo 형태)
if ! echo "${REPO_ID}" | grep -qE "^[^/]+/[^/]+$"; then
    echo "[push-hub] ERROR: --repo-id 형식 오류. '<hf_user>/<repo_name>' 형태여야 합니다."
    echo "  예: myuser/my_robot_dataset"
    exit 1
fi

# ── pre-check: dataset 경로 존재 확인 ─────────────────────────────────────────
DATASET_PATH_EXPANDED="${DATASET_PATH/#\~/$HOME}"
if [ ! -d "${DATASET_PATH_EXPANDED}" ]; then
    echo "[push-hub] ERROR: dataset 경로가 존재하지 않습니다: ${DATASET_PATH_EXPANDED}"
    echo "  lerobot-record 로 먼저 dataset 수집 후 재실행하세요."
    exit 1
fi

# ── pre-check: HF 인증 확인 ───────────────────────────────────────────────────
HF_AUTH_OK="false"
if [ -n "${HF_TOKEN}" ]; then
    HF_AUTH_OK="token"
elif python3 -c "from huggingface_hub import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)" 2>/dev/null; then
    HF_AUTH_OK="cached"
fi

if [ "${HF_AUTH_OK}" = "false" ]; then
    echo "[push-hub] ERROR: HuggingFace 인증 정보 없음."
    echo "  옵션 A (권장): export HF_TOKEN=hf_xxxxxxxxxx"
    echo "  옵션 B: huggingface-cli login"
    exit 1
fi

echo ""
echo "=========================================================="
echo " push_dataset_hub"
echo "=========================================================="
echo "  dataset 경로:  ${DATASET_PATH_EXPANDED}"
echo "  HF repo-id:    ${REPO_ID}"
echo "  private:       ${PRIVATE_FLAG:-(public)}"
echo "  branch:        ${BRANCH:-(default/main)}"
echo "  HF 인증:       ${HF_AUTH_OK}"
echo "  dry-run:       ${DRY_RUN:-(off)}"
echo "=========================================================="
echo ""

# ── dry-run 모드: 실제 push 없이 확인만 ───────────────────────────────────────
if [ -n "${DRY_RUN}" ]; then
    echo "[push-hub] dry-run 모드 — 실제 HF Hub push 없이 확인만 수행"
    echo ""
    echo "[push-hub] dataset 파일 목록:"
    find "${DATASET_PATH_EXPANDED}" -type f | head -20 | sed 's/^/    /'
    FILE_COUNT=$(find "${DATASET_PATH_EXPANDED}" -type f | wc -l)
    echo "    ... (총 ${FILE_COUNT} 파일)"
    echo ""
    echo "[push-hub] dry-run 완료. 실제 push 시 --dry-run 플래그 제거 후 재실행."
    exit 0
fi

# ── Python: lerobot LeRobotDataset.push_to_hub() 패턴 활용 ────────────────────
# lerobot upstream 의 push_to_hub 구현체 (lerobot_dataset.py:501) 를 직접 호출:
#   hub_api.create_repo(repo_id, private, repo_type="dataset", exist_ok=True)
#   hub_api.upload_folder(repo_id, folder_path=root, ...)
#   card.push_to_hub(repo_id, repo_type="dataset")
#
# 단, LeRobotDataset(root=) 생성자는 메타데이터(meta.json 등) 가 있는 정규 dataset 을
# 기대한다. 본 스크립트는 정규 LeRobotDataset 포맷 (lerobot-record 가 생성한) 을 가정.

PRIVATE_PYTHON="False"
if [ -n "${PRIVATE_FLAG}" ]; then
    PRIVATE_PYTHON="True"
fi

BRANCH_PYTHON="None"
if [ -n "${BRANCH}" ]; then
    BRANCH_PYTHON="\"${BRANCH}\""
fi

echo "[push-hub] HF Hub push 시작 (repo: ${REPO_ID}) ..."

# 환경변수로 Python 에 전달 — bash 변수 직접 삽입 시 공백·특수문자가 Python syntax error 를 유발하므로
# heredoc 인자를 single-quote ('PYEOF') 로 닫아 변수 확장을 차단하고 os.environ 으로 수신.
DATASET_PATH="${DATASET_PATH_EXPANDED}" \
REPO_ID="${REPO_ID}" \
PRIVATE="${PRIVATE_PYTHON}" \
BRANCH="${BRANCH_PYTHON}" \
python3 - <<'PYEOF'
import os
import sys

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
except ImportError:
    print("[push-hub] ERROR: lerobot 패키지를 찾을 수 없습니다.")
    print("  venv 가 활성화되어 있는지 확인하세요:")
    print("    source ~/smolvla/datacollector/.hylion_collector/bin/activate")
    sys.exit(1)

dataset_path = os.environ["DATASET_PATH"]
repo_id      = os.environ["REPO_ID"]
private      = os.environ["PRIVATE"] == "True"
branch_raw   = os.environ["BRANCH"]
branch       = None if branch_raw == "None" else branch_raw

print(f"[push-hub] LeRobotDataset 로드 중: {dataset_path}")
try:
    # repo_id 는 HF Hub push 대상 ID.
    # 로컬 dataset 내부 메타의 repo_id 와 달라도 push_to_hub() 는 이 값(self.repo_id)을 사용.
    dataset = LeRobotDataset(repo_id=repo_id, root=dataset_path)
except Exception as e:
    print(f"[push-hub] ERROR: dataset 로드 실패: {e}")
    print("  lerobot-record 로 수집된 정규 LeRobotDataset 포맷인지 확인하세요.")
    sys.exit(1)

print(f"[push-hub] dataset 로드 완료: {len(dataset)} 프레임")
print(f"[push-hub] HF Hub push 중 (private={private}, branch={branch}) ...")

try:
    dataset.push_to_hub(private=private, branch=branch)
    print(f"[push-hub] push 완료: https://huggingface.co/datasets/{repo_id}")
except Exception as e:
    print(f"[push-hub] ERROR: push 실패: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "=========================================================="
echo " 완료."
echo "  HF Hub: https://huggingface.co/datasets/${REPO_ID}"
echo ""
echo " DGX 에서 dataset 다운로드:"
echo "  ssh dgx"
echo "  source ~/smolvla/dgx/.arm_finetune/bin/activate"
echo "  python -c 'from lerobot.datasets.lerobot_dataset import LeRobotDataset; \\"
echo "    ds = LeRobotDataset(\"${REPO_ID}\"); print(ds)'"
echo "=========================================================="
