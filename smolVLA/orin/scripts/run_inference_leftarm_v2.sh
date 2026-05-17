#!/usr/bin/env bash
# run_inference_leftarm_v2.sh
#
# Thin shell wrapper for leftarm_v2_A2_pc_2026-05-17 checkpoint inference on Orin.
# Wraps: orin/inference/leftarm_v2_inference.py (LoRA adapter + rename_map 추론)
#
# USER_OVERRIDE 2026-05-18 옵션 W: lerobot-record 폐기 → leftarm_v2_inference.py 직접 호출.
# - lerobot-record 는 orin/lerobot/ trim 과 양립 불가 (F1·F4·F5·F6 연쇄 import 실패).
# - hil_inference.py 는 사전학습 ckpt 책임 보존 (갱신 X).
# - F1 패치 (lerobot_record.py try/except) 는 trim 환경 정합으로 그대로 유지.
#
# Reference: orin/inference/leftarm_v2_inference.py
#   - task1: "Pick up the blue and yellow doll and place it on the left side of the table"
#   - task2: "Hand the yellow can to the person"
#   - rename_map: top->camera1, wrist->camera2 (학습 분포 정합)
#   - LoRA adapter: PeftConfig + PeftModel (peft>=0.10.0 필요)
#
# Usage:
#   ./run_inference_leftarm_v2.sh <subcommand> [args]
#   Subcommands: download | check | dry-run | live <task1|task2> | help
#
# Environment override (export before calling):
#   CKPT_REPO_ID, CKPT_LOCAL_DIR, VENV_PATH, CONFIG_DIR, INFERENCE_SCRIPT

set -euo pipefail
# F2 fix: LD_LIBRARY_PATH 가 Orin 시스템에 미설정이면 빈 문자열로 초기화.
# venv activate (line ~133) 내 `export LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 가
# nounset(-u) 모드에서 unbound variable 에러를 내지 않도록 사전 보호.
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"

# ── Defaults (override via env) ──────────────────────────────────────────────
CKPT_REPO_ID="${CKPT_REPO_ID:-BaboGaeguri/leftarm_v2_A2_pc_2026-05-17}"
CKPT_LOCAL_DIR="${CKPT_LOCAL_DIR:-${HOME}/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17}"
VENV_PATH="${VENV_PATH:-${HOME}/smolvla/orin/.hylion_arm/bin/activate}"
CONFIG_DIR="${CONFIG_DIR:-${HOME}/smolvla/orin/config}"
INFERENCE_SCRIPT="${INFERENCE_SCRIPT:-${HOME}/smolvla/orin/inference/leftarm_v2_inference.py}"
# zero-shot subcommand 전용 — base smolvla_base 만 로딩하는 별도 entry
# 가설 분리 검증 (learning_log §M1.5 추론 후 가설 분리 검증 사이클, 2026-05-18)
BASE_INFERENCE_SCRIPT="${BASE_INFERENCE_SCRIPT:-${HOME}/smolvla/orin/inference/leftarm_base_inference.py}"

# Task instructions (from collection_log.md)
TASK1_INSTRUCTION="Pick up the blue and yellow doll and place it on the left side of the table"
TASK2_INSTRUCTION="Hand the yellow can to the person"

CONFIG_PATH="${CKPT_LOCAL_DIR}/config.json"

# ── Helper: check and auto-fix n_action_steps ────────────────────────────────
check_n_action_steps() {
    if [[ ! -f "${CONFIG_PATH}" ]]; then
        echo "ERROR: config.json not found at ${CONFIG_PATH}"
        echo "       Run './run_inference_leftarm_v2.sh download' first."
        exit 1
    fi

    VAL=$(python3 -c "import json; print(json.load(open('${CONFIG_PATH}'))['n_action_steps'])" 2>/dev/null || echo "MISSING")

    if [[ "${VAL}" == "MISSING" ]]; then
        echo "ERROR: Could not read n_action_steps from ${CONFIG_PATH}"
        echo "       Check that the file is valid JSON and contains 'n_action_steps'."
        exit 1
    fi

    if [[ "${VAL}" == "1" ]]; then
        echo "WARNING: n_action_steps=1 detected — auto-fixing to 50 (prof_train_setting §7-5 trap)"
        python3 -c "
import json, pathlib
p = pathlib.Path('${CONFIG_PATH}')
d = json.loads(p.read_text())
d['n_action_steps'] = 50
p.write_text(json.dumps(d, indent=2))
"
        echo "OK: n_action_steps 1 -> 50 written to ${CONFIG_PATH}"
    elif [[ "${VAL}" == "50" ]]; then
        echo "OK: n_action_steps=50 (correct)"
    else
        echo "INFO: n_action_steps=${VAL} — manual check recommended"
    fi
}

# ── Helper: read robot config from JSON ──────────────────────────────────────
read_robot_config() {
    FOLLOWER_PORT=$(python3 -c "
import json
d = json.load(open('${CONFIG_DIR}/ports.json'))
v = d.get('follower_port')
print(v if v is not None else 'None')
" 2>/dev/null || echo "None")

    TOP_IDX=$(python3 -c "
import json
d = json.load(open('${CONFIG_DIR}/cameras.json'))
v = d.get('top', {}).get('index')
print(v if v is not None else 'None')
" 2>/dev/null || echo "None")

    WRIST_IDX=$(python3 -c "
import json
d = json.load(open('${CONFIG_DIR}/cameras.json'))
v = d.get('wrist', {}).get('index')
print(v if v is not None else 'None')
" 2>/dev/null || echo "None")
}

# ── Helper: validate robot config (all non-None) ──────────────────────────────
validate_robot_config() {
    local missing=0
    if [[ "${FOLLOWER_PORT}" == "None" ]]; then
        echo "ERROR: follower_port is null in ${CONFIG_DIR}/ports.json"
        missing=1
    fi
    if [[ "${TOP_IDX}" == "None" ]]; then
        echo "ERROR: cameras.top.index is null in ${CONFIG_DIR}/cameras.json"
        missing=1
    fi
    if [[ "${WRIST_IDX}" == "None" ]]; then
        echo "ERROR: cameras.wrist.index is null in ${CONFIG_DIR}/cameras.json"
        missing=1
    fi
    if [[ "${missing}" == "1" ]]; then
        echo ""
        echo "Fill in the null values in orin/config/{ports,cameras}.json before running live inference."
        echo "Example override (without editing JSON):"
        echo "  FOLLOWER_PORT=/dev/ttyUSB0 TOP_IDX=0 WRIST_IDX=2 ./run_inference_leftarm_v2.sh live task1"
        exit 1
    fi
}

# ── Subcommand: download ──────────────────────────────────────────────────────
cmd_download() {
    echo "=== download: ${CKPT_REPO_ID} -> ${CKPT_LOCAL_DIR} ==="
    # shellcheck source=/dev/null
    source "${VENV_PATH}"
    # F3 fix: huggingface-cli deprecated (huggingface_hub >=1.12). 'hf' 우선 사용.
    # 구형 환경 호환을 위해 hf 미존재 시 huggingface-cli 로 fallback.
    if command -v hf >/dev/null 2>&1; then
        hf download "${CKPT_REPO_ID}" --local-dir "${CKPT_LOCAL_DIR}"
    else
        huggingface-cli download "${CKPT_REPO_ID}" --local-dir "${CKPT_LOCAL_DIR}"
    fi
    check_n_action_steps
    echo "OK download complete: ${CKPT_LOCAL_DIR}"
}

# ── Subcommand: check ─────────────────────────────────────────────────────────
cmd_check() {
    echo "=== check: ${CONFIG_PATH} ==="
    check_n_action_steps

    echo ""
    echo "--- input_features keys (image feature names) ---"
    python3 -c "
import json
d = json.load(open('${CONFIG_PATH}'))
features = d.get('input_features', {})
print('input_features keys:', list(features.keys()))
image_keys = [k for k in features if 'images' in k]
print('image keys:', image_keys)
"

    echo ""
    echo "--- rename_map reminder ---"
    echo "  Training rename_map: top -> camera1, wrist -> camera2"
    echo "  => checkpoint expects: observation.images.camera1, observation.images.camera2"
    echo "  => Pass at inference: --dataset.rename_map='{\"observation.images.top\":\"observation.images.camera1\",\"observation.images.wrist\":\"observation.images.camera2\"}'"
}

# ── Subcommand: dry-run ───────────────────────────────────────────────────────
cmd_dry_run() {
    local task_key="${1:-task1}"
    echo "=== dry-run: leftarm_v2_inference.py --mode dry-run --task ${task_key} ==="
    # shellcheck source=/dev/null
    source "${VENV_PATH}"

    # config 상태 확인 (robot 연결 불필요)
    read_robot_config

    # dry-run 실행 (--follower-port 가 None 이면 에러 출력되지만 코드 경로 검증 가능)
    # Orin 에 robot 미연결 가능성 — 에러 출력 후 계속 진행 (|| true)
    OUTPUT_JSON="/tmp/leftarm_v2_dryrun_${task_key}_$(date +%Y%m%d_%H%M%S).json"
    echo "--- output-json: ${OUTPUT_JSON} ---"
    echo ""

    python "${INFERENCE_SCRIPT}" \
        --task "${task_key}" \
        --mode dry-run \
        --ckpt-dir "${CKPT_LOCAL_DIR}" \
        --gate-json "${CONFIG_DIR}" \
        --n-action-steps 50 \
        --max-steps 1 \
        --output-json "${OUTPUT_JSON}" \
        2>&1 || true

    echo ""
    echo "NOTE: dry-run 은 robot 연결 없이도 LoRA 로드 + 코드 경로를 검증합니다."
    echo "      robot 미연결 시 connect() 에서 에러 발생 (정상 — 코드 경로 검증 완료)."
    echo "      live 실행: ./run_inference_leftarm_v2.sh live task1"
    echo "      현재 config 값:"
    echo "        follower_port = ${FOLLOWER_PORT}"
    echo "        top.index     = ${TOP_IDX}"
    echo "        wrist.index   = ${WRIST_IDX}"
}

# ── Subcommand: live ──────────────────────────────────────────────────────────
cmd_live() {
    local task_key="${1:-}"
    if [[ -z "${task_key}" ]]; then
        echo "ERROR: task argument required for 'live' subcommand."
        cmd_help
        exit 1
    fi

    case "${task_key}" in
        task1|task2)
            ;;
        *)
            echo "ERROR: Unknown task '${task_key}'. Use 'task1' or 'task2'."
            exit 1
            ;;
    esac

    echo "=== live: ${task_key} ==="
    echo "    inference script: ${INFERENCE_SCRIPT}"

    # Validate checkpoint
    check_n_action_steps

    # Read and validate robot config
    read_robot_config
    validate_robot_config

    # shellcheck source=/dev/null
    source "${VENV_PATH}"

    echo ""
    echo "--- Running leftarm_v2_inference.py (LoRA adapter, live mode) ---"
    echo "    follower_port:  ${FOLLOWER_PORT}"
    echo "    top.index:      ${TOP_IDX}"
    echo "    wrist.index:    ${WRIST_IDX}"
    echo "    ckpt:           ${CKPT_LOCAL_DIR}"
    echo "    task:           ${task_key}"
    echo "    rename_map:     top->camera1, wrist->camera2 (내부 자동 적용)"
    echo ""

    # leftarm_v2_inference.py 직접 호출
    # Ref: orin/inference/leftarm_v2_inference.py
    # - LoRA adapter: PeftConfig + PeftModel (peft>=0.10.0 필요)
    # - rename_map: 내부 apply_rename_map() 자동 적용
    # - gate-json: ports.json + cameras.json 자동 로드
    python "${INFERENCE_SCRIPT}" \
        --task "${task_key}" \
        --mode live \
        --ckpt-dir "${CKPT_LOCAL_DIR}" \
        --follower-port "${FOLLOWER_PORT}" \
        --cameras "top:${TOP_IDX},wrist:${WRIST_IDX}" \
        --gate-json "${CONFIG_DIR}" \
        --n-action-steps 50 \
        --max-steps 50
}

# ── Subcommand: zero-shot ─────────────────────────────────────────────────────
# 가설 분리 검증용 — base smolvla_base 만 로딩 (LoRA adapter skip).
# learning_log.md §M1.5 추론 후 가설 분리 검증 사이클 작업 1 (사용자 담당).
cmd_zero_shot() {
    local task_key="${1:-}"
    if [[ -z "${task_key}" ]]; then
        echo "ERROR: task argument required for 'zero-shot' subcommand."
        cmd_help
        exit 1
    fi

    case "${task_key}" in
        task1|task2)
            ;;
        *)
            echo "ERROR: Unknown task '${task_key}'. Use 'task1' or 'task2'."
            exit 1
            ;;
    esac

    echo "=== zero-shot: ${task_key} (base smolvla_base only, LoRA 없음) ==="
    echo "    inference script: ${BASE_INFERENCE_SCRIPT}"

    # Read and validate robot config (cameras + ports)
    # ckpt 점검은 불요 — zero-shot 은 HF Hub base 직접 사용 (로컬 ckpt 없음)
    read_robot_config
    validate_robot_config

    # shellcheck source=/dev/null
    source "${VENV_PATH}"

    echo ""
    echo "--- Running leftarm_base_inference.py (zero-shot, base 사전학습만) ---"
    echo "    follower_port:  ${FOLLOWER_PORT}"
    echo "    top.index:      ${TOP_IDX}"
    echo "    wrist.index:    ${WRIST_IDX}"
    echo "    base ckpt:      lerobot/smolvla_base (HF Hub)"
    echo "    task:           ${task_key}"
    echo "    rename_map:     top->camera1, wrist->camera2 (내부 자동 적용)"
    echo "    가설 검증:       learning_log §M1.5 추론 후 가설 분리 검증 사이클 작업 1"
    echo ""

    # leftarm_base_inference.py 직접 호출 (별도 entry, LoRA 영역 없음)
    # - SmolVLAPolicy.from_pretrained("lerobot/smolvla_base") 직접 로딩
    # - peft 의존성 X (load_base_policy 헬퍼)
    # - 가설 검증: base VLM 의 우리 환경 task1·task2 instruction 응답성 정성 측정
    # - 책임 분리 (사용자 결정 2026-05-18): leftarm_v2_inference.py 변경 X
    python "${BASE_INFERENCE_SCRIPT}" \
        --task "${task_key}" \
        --mode live \
        --follower-port "${FOLLOWER_PORT}" \
        --cameras "top:${TOP_IDX},wrist:${WRIST_IDX}" \
        --gate-json "${CONFIG_DIR}" \
        --n-action-steps 50 \
        --max-steps 1000
}

# ── Subcommand: help ──────────────────────────────────────────────────────────
cmd_help() {
    cat <<'EOF'
run_inference_leftarm_v2.sh — leftarm_v2_A2_pc_2026-05-17 LoRA adapter 추론 wrapper

USER_OVERRIDE 2026-05-18 옵션 W: lerobot-record 폐기 → leftarm_v2_inference.py 직접 호출.

USAGE:
    ./run_inference_leftarm_v2.sh <subcommand> [args]

SUBCOMMANDS:
    download        Download checkpoint from HF Hub + auto-fix n_action_steps
    check           Inspect config.json (n_action_steps + image feature keys)
    dry-run [task]  LoRA 로드 + 코드 경로 검증 (robot 미연결 가능) [default task: task1]
    live task1      Run live inference (task1: doll pick-and-place, LoRA ckpt)
    live task2      Run live inference (task2: can handover, LoRA ckpt)
    zero-shot task1 Run zero-shot inference (base smolvla_base only — 가설 분리 검증)
    zero-shot task2 Run zero-shot inference (base smolvla_base only — 가설 분리 검증)
    help            Show this help

ENVIRONMENT OVERRIDES (export before calling):
    CKPT_REPO_ID        HF repo id  (default: BaboGaeguri/leftarm_v2_A2_pc_2026-05-17)
    CKPT_LOCAL_DIR      Local ckpt dir (default: ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17)
    VENV_PATH           venv activate path (default: ~/smolvla/orin/.hylion_arm/bin/activate)
    CONFIG_DIR          orin config dir (default: ~/smolvla/orin/config)
    INFERENCE_SCRIPT    leftarm_v2_inference.py 경로 (default: ~/smolvla/orin/inference/leftarm_v2_inference.py)

EXAMPLES:
    # 1. Download checkpoint
    ./run_inference_leftarm_v2.sh download

    # 2. Inspect config
    ./run_inference_leftarm_v2.sh check

    # 3. LoRA 로드 + dry-run (robot 미연결 시 connect 에러, 코드 경로 검증)
    ./run_inference_leftarm_v2.sh dry-run task1

    # 4. Live inference — task1
    ./run_inference_leftarm_v2.sh live task1

    # 5. Live inference — task2
    ./run_inference_leftarm_v2.sh live task2

    # 6. Override robot port without editing JSON
    FOLLOWER_PORT=/dev/ttyUSB0 TOP_IDX=0 WRIST_IDX=2 \
        ./run_inference_leftarm_v2.sh live task1

NOTES:
    - orin/config/ports.json (follower_port) and orin/config/cameras.json (top.index, wrist.index)
      must be filled in before running 'live'. Use env overrides if not.
    - rename_map (top->camera1, wrist->camera2) 은 leftarm_v2_inference.py 내부에서 자동 적용.
      (학습: prof_train_setting.md §3 --rename_map 동일)
    - n_action_steps=50 이 default (config.json 이미 수정됨).
    - LoRA 로드를 위해 peft>=0.10.0 필요:
        pip install peft>=0.10.0
      (orin/pyproject.toml 에 미등록 — Category B+C 사용자 동의 후 추가 예정)
EOF
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
SUBCMD="${1:-help}"
shift || true

case "${SUBCMD}" in
    download)
        cmd_download
        ;;
    check)
        cmd_check
        ;;
    dry-run|dryrun)
        cmd_dry_run "${1:-task1}"
        ;;
    live)
        cmd_live "${1:-}"
        ;;
    zero-shot|zeroshot)
        cmd_zero_shot "${1:-}"
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        echo "ERROR: Unknown subcommand '${SUBCMD}'"
        cmd_help
        exit 1
        ;;
esac
