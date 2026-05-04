#!/usr/bin/env bash
# =============================================================================
# check_hardware.sh — DGX 수집 환경 하드웨어 점검 스크립트
#
# 원본: orin/tests/check_hardware.sh (04 G1 산출물) 패턴 미러
# 이식·신규: 06_dgx_absorbs_datacollector TODO-X3 (2026-05-02)
#
# 책임 분담 결정:
#   - preflight_check.sh  = 학습 환경 (venv·RAM·GPU·Ollama·디스크) — 그대로 유지
#   - check_hardware.sh   = 수집 환경 (USB·dialout·v4l2·SO-ARM 포트·카메라) — 본 파일
#
# 이유: preflight_check.sh 는 학습 시나리오(smoke/s1/s3/lora) 별 메모리 임계치
#       논리를 담고 있어 수집 환경 체크를 혼합하면 단일 책임 원칙 위반.
#       env_check.py 의 mode 파라미터 (collect / train) 와도 정합됨.
#
# 용도: DGX 에서 SO-ARM·카메라 직결 후 수집 가능 여부를 빠르게 점검
#   Step 1: venv 활성화
#   Step 2: dialout 그룹 멤버십 (SO-ARM 포트 접근 권한)
#   Step 3: SO-ARM 포트 발견 (/dev/ttyACM*, /dev/ttyUSB*)
#   Step 4: v4l2 장치 발견 (/dev/video*)
#   Step 5: 카메라 인덱스 발견 (lerobot OpenCVCamera.find_cameras)
#
# 사용법:
#   bash check_hardware.sh
#   bash check_hardware.sh --quiet
#   bash check_hardware.sh --output-json /tmp/dgx_hw.json
#
# 인자:
#   --quiet        비대화형: 사용자 입력 프롬프트 건너뜀 (prod-test-runner 호출용)
#   --output-json FILE  결과를 JSON 파일로 저장 (env_check.py 파싱용)
#
# 전제 조건:
#   - dgx venv: ~/smolvla/dgx/.arm_finetune
#   - lerobot [hardware,feetech] extra 설치 (dgx/scripts/setup_train_env.sh §3-c 완료 후)
#   - USB: SO-ARM 2대 (follower + leader) 직결
#   - USB: 카메라 2대 (top + wrist) 직결
#
# 종료 코드:
#   0 — 모든 점검 PASS
#   1 — 하나 이상 FAIL (상세는 --output-json 또는 stdout)
#   2 — 사용법 오류
#
# 참조:
#   orin/tests/check_hardware.sh (04 G1) — JSON 결과 관리·record_step 패턴 미러
#   dgx/scripts/preflight_check.sh — 학습 환경 체크 (본 파일 분리 근거)
# =============================================================================

set -uo pipefail
# 주의: set -e 를 사용하지 않음. 개별 step 실패가 전체 중단을 유발하지 않도록
# 각 step 함수는 return 1 로 실패를 알리고 메인에서 || overall_exit=1 로 수집

# ---------------------------------------------------------------------------
# 0. 경로 상수
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DGX_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_ACTIVATE="${HOME}/smolvla/dgx/.arm_finetune/bin/activate"

# JSON 결과 임시 파일 (특수문자 안전 처리)
TMP_RESULT_JSON="$(mktemp /tmp/dgx_check_hardware_XXXXXX.json)"
trap 'rm -f "${TMP_RESULT_JSON}"' EXIT

# ---------------------------------------------------------------------------
# 1. 인자 파싱
# ---------------------------------------------------------------------------
QUIET=false
OUTPUT_JSON=""

usage() {
    echo "사용법: bash check_hardware.sh [--quiet] [--output-json FILE]"
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quiet)
            QUIET=true; shift ;;
        --output-json)
            OUTPUT_JSON="$2"; shift 2 ;;
        -h|--help)
            usage ;;
        *)
            echo "[ERROR] 알 수 없는 인자: $1"; usage ;;
    esac
done

# ---------------------------------------------------------------------------
# 2. 결과 관리 (JSON 임시 파일 방식 — orin/tests/check_hardware.sh 패턴 미러)
# ---------------------------------------------------------------------------
PASS_COUNT=0
FAIL_COUNT=0

# 초기 JSON 구조 기록
python3 -c "
import json
data = {'node': 'dgx', 'purpose': 'data_collection', 'steps': {}}
with open('${TMP_RESULT_JSON}', 'w') as f:
    json.dump(data, f, indent=2)
"

record_step() {
    local step_name="$1"
    local status="$2"   # PASS | FAIL | WARN
    local detail="$3"

    if [[ "$status" == "PASS" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        [[ "$QUIET" == "false" ]] && echo "[PASS] ${step_name}: ${detail}"
    elif [[ "$status" == "WARN" ]]; then
        [[ "$QUIET" == "false" ]] && echo "[WARN] ${step_name}: ${detail}"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        [[ "$QUIET" == "false" ]] && echo "[FAIL] ${step_name}: ${detail}"
    fi

    # 임시 파일에 step 결과 누적 (환경변수 경유 — bash 특수문자 안전)
    STEP_NAME="$step_name" STEP_STATUS="$status" STEP_DETAIL="$detail" \
    python3 -c "
import json, os
step_name = os.environ['STEP_NAME']
status = os.environ['STEP_STATUS']
detail = os.environ['STEP_DETAIL']
tmp_path = '${TMP_RESULT_JSON}'
try:
    with open(tmp_path, 'r') as f:
        data = json.load(f)
    data['steps'][step_name] = {'status': status, 'detail': detail}
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=2)
except Exception:
    pass  # JSON 기록 실패해도 스크립트 계속 진행
"
}

# ---------------------------------------------------------------------------
# 3. Step 1: venv 활성화
# ---------------------------------------------------------------------------
step_venv() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 1/5] venv 활성화 ==="

    if [[ ! -f "$VENV_ACTIVATE" ]]; then
        record_step "venv" "FAIL" "activate 스크립트 미존재: ${VENV_ACTIVATE}"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV_ACTIVATE"

    local python_bin
    python_bin="$(which python3)"
    record_step "venv" "PASS" "python: ${python_bin}"
}

# ---------------------------------------------------------------------------
# 4. Step 2: dialout 그룹 멤버십 (SO-ARM 포트 접근 권한)
# ---------------------------------------------------------------------------
step_dialout() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 2/5] dialout 그룹 멤버십 ==="

    local current_user
    current_user="$(id -un)"
    local groups_out
    groups_out="$(id -Gn)"

    if echo "${groups_out}" | grep -qw "dialout"; then
        record_step "dialout" "PASS" "사용자 ${current_user} 는 dialout 그룹 멤버"
    else
        record_step "dialout" "FAIL" "사용자 ${current_user} 가 dialout 그룹 미포함. 해결: sudo usermod -aG dialout ${current_user} (재로그인 필요)"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# 5. Step 3: SO-ARM 포트 발견 (/dev/ttyACM*, /dev/ttyUSB*)
#    orin/tests/check_hardware.sh step_soarm_port 패턴 미러 (비대화형 단순화)
# ---------------------------------------------------------------------------
step_soarm_port() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 3/5] SO-ARM 포트 발견 ==="

    local port_out
    local port_exit=0
    port_out=$(python3 - 2>&1 <<'PYEOF'
import json, sys
from pathlib import Path

# lerobot_find_port.py find_available_ports() 의 Linux 분기 기반:
# ttyACM* = Feetech STS/SCS 서보 (SO-ARM 사용), ttyUSB* = 일반 USB-Serial
tty_paths = sorted(Path("/dev").glob("ttyACM*")) + sorted(Path("/dev").glob("ttyUSB*"))
ports = [str(p) for p in tty_paths if p.exists()]

if not ports:
    sys.exit(2)

print(json.dumps(ports))
PYEOF
) || port_exit=$?

    if [[ $port_exit -eq 2 ]]; then
        record_step "soarm_port" "FAIL" "포트 미발견 — SO-ARM USB 연결 확인 필요 (/dev/ttyACM* or /dev/ttyUSB*)"
        return 1
    elif [[ $port_exit -ne 0 ]]; then
        record_step "soarm_port" "FAIL" "포트 스캔 오류: ${port_out}"
        return 1
    fi

    local found_count
    found_count=$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])))" "${port_out}" 2>/dev/null || echo "0")
    [[ "$QUIET" == "false" ]] && echo "발견된 포트: ${port_out}"

    if [[ "$found_count" -lt 2 ]]; then
        record_step "soarm_port" "WARN" "포트 ${found_count}개 발견 (SO-ARM 2대 연결 시 2개 이상 기대): ${port_out}"
    else
        record_step "soarm_port" "PASS" "${found_count}개 발견: ${port_out}"
    fi
}

# ---------------------------------------------------------------------------
# 6. Step 4: v4l2 장치 발견 (/dev/video*)
# ---------------------------------------------------------------------------
step_v4l2() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 4/5] v4l2 장치 발견 ==="

    local video_devices
    video_devices=$(find /dev -name "video*" -type c 2>/dev/null | sort || true)

    if [[ -z "$video_devices" ]]; then
        record_step "v4l2" "FAIL" "v4l2 장치 미발견 — 카메라 USB 연결 확인 필요 (/dev/video*)"
        return 1
    fi

    local dev_count
    dev_count=$(echo "$video_devices" | wc -l)
    [[ "$QUIET" == "false" ]] && echo "발견된 v4l2 장치: ${video_devices}"

    if [[ "$dev_count" -lt 2 ]]; then
        record_step "v4l2" "WARN" "${dev_count}개 발견 (카메라 2대 시 2개 이상 기대)"
    else
        record_step "v4l2" "PASS" "${dev_count}개 발견"
    fi
}

# ---------------------------------------------------------------------------
# 7. Step 5: 카메라 인덱스 발견 (lerobot OpenCVCamera.find_cameras)
#    orin/tests/check_hardware.sh step_cameras 패턴 미러 (비대화형 단순화)
#    NOTE: lerobot [hardware] extra 설치 필요 (setup_train_env.sh §3-c 완료 후 동작)
# ---------------------------------------------------------------------------
step_cameras() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 5/5] 카메라 인덱스 발견 (lerobot OpenCVCamera) ==="

    local cam_out
    local cam_exit=0
    cam_out=$(python3 - 2>&1 <<'PYEOF'
import json, sys
try:
    from lerobot.cameras.opencv import OpenCVCamera
    cameras = OpenCVCamera.find_cameras()
    result = []
    for c in cameras:
        result.append({
            "id": c["id"],
            "name": c.get("name", ""),
            "width": c.get("default_stream_profile", {}).get("width"),
            "height": c.get("default_stream_profile", {}).get("height"),
            "fps": c.get("default_stream_profile", {}).get("fps"),
        })
    print(json.dumps(result))
except ImportError as e:
    print(f"IMPORT_ERROR: {e}", file=sys.stderr)
    sys.exit(3)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
) || cam_exit=$?

    if [[ $cam_exit -eq 3 ]]; then
        # lerobot [hardware] extra 미설치 시 — setup_train_env.sh §3-c 실행 전 단계에서 발생 가능
        record_step "cameras" "FAIL" "lerobot import 실패 (hardware extra 미설치 가능성): ${cam_out}"
        return 1
    elif [[ $cam_exit -ne 0 ]]; then
        record_step "cameras" "FAIL" "카메라 스캔 오류: ${cam_out}"
        return 1
    fi

    local found_count
    found_count=$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])))" "${cam_out}" 2>/dev/null || echo "0")
    [[ "$QUIET" == "false" ]] && echo "발견된 카메라 ${found_count}개"

    if [[ "$found_count" -eq 0 ]]; then
        record_step "cameras" "FAIL" "카메라 미발견 — USB 카메라 연결 확인 필요"
        return 1
    elif [[ "$found_count" -lt 2 ]]; then
        record_step "cameras" "WARN" "${found_count}개 발견 (top + wrist 2대 기대): ${cam_out}"
    else
        record_step "cameras" "PASS" "${found_count}개 발견: ${cam_out}"
    fi
}

# ---------------------------------------------------------------------------
# 8. JSON 출력 마무리
# ---------------------------------------------------------------------------
finalize_output() {
    local total_exit=0
    [[ $FAIL_COUNT -gt 0 ]] && total_exit=1

    # summary 추가
    python3 -c "
import json, sys
total_exit = int(sys.argv[1])
pass_count = int(sys.argv[2])
fail_count = int(sys.argv[3])
tmp_path = sys.argv[4]
try:
    with open(tmp_path, 'r') as f:
        data = json.load(f)
    data['summary'] = {'pass': pass_count, 'fail': fail_count, 'exit_code': total_exit}
    with open(tmp_path, 'w') as f:
        json.dump(data, f, indent=2)
except Exception:
    pass
" "${total_exit}" "${PASS_COUNT}" "${FAIL_COUNT}" "${TMP_RESULT_JSON}"

    # --output-json 지정 시 복사
    if [[ -n "$OUTPUT_JSON" ]]; then
        cp "${TMP_RESULT_JSON}" "${OUTPUT_JSON}"
        [[ "$QUIET" == "false" ]] && echo ""
        [[ "$QUIET" == "false" ]] && echo "JSON 결과 저장: ${OUTPUT_JSON}"
    fi

    [[ "$QUIET" == "false" ]] && echo ""
    if [[ $FAIL_COUNT -eq 0 ]]; then
        echo "[DONE] 모든 점검 PASS (${PASS_COUNT}단계)"
    else
        echo "[DONE] ${FAIL_COUNT}개 FAIL / ${PASS_COUNT}개 PASS"
        echo ""
        echo " 해결 힌트:"
        echo "   dialout FAIL → sudo usermod -aG dialout \$(id -un)  (재로그인 필요)"
        echo "   soarm_port FAIL → SO-ARM USB 케이블 연결 확인"
        echo "   v4l2 FAIL → 카메라 USB 케이블 연결 확인"
        echo "   cameras FAIL (import) → setup_train_env.sh §3-c 실행 후 재시도 (lerobot hardware extra 필요)"
    fi

    return $total_exit
}

# ---------------------------------------------------------------------------
# 9. 메인 실행
# ---------------------------------------------------------------------------
main() {
    if [[ "$QUIET" == "false" ]]; then
        echo ""
        echo "=============================================="
        echo " check_hardware.sh (DGX 수집 환경)"
        echo " 책임: USB·dialout·v4l2·SO-ARM·카메라"
        echo " 학습 환경 점검: preflight_check.sh 사용"
        echo "=============================================="
    fi

    local overall_exit=0

    # set -e 로 인한 중단 방지: || true 로 개별 실패를 overall_exit 에 기록
    step_venv       || overall_exit=1
    step_dialout    || overall_exit=1
    step_soarm_port || overall_exit=1
    step_v4l2       || overall_exit=1
    step_cameras    || overall_exit=1

    finalize_output || overall_exit=1
    return $overall_exit
}

main
