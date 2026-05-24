#!/usr/bin/env bash
# =============================================================================
# check_hardware.sh — Orin 하드웨어 점검 게이트 스크립트
#
# 용도: first-time (발견 + cache 갱신) / resume (cache 기반 검증) 두 모드
# 해소 대상:
#   BACKLOG 03 #14 — SSH 비대화형 libcusparseLt ImportError
#   BACKLOG 03 #15 — 카메라 인덱스 사전 발견 단계 필요
#   BACKLOG 03 #16 — wrist 카메라 flip 확인 단계 필요
#   BACKLOG 01 #1  — SO-ARM USB 포트 번호 변동
#
# 사용법:
#   bash check_hardware.sh --mode first-time
#   bash check_hardware.sh --mode resume
#   bash check_hardware.sh --mode resume --quiet --output-json /tmp/hw.json
#
# 인자:
#   --mode       {first-time|resume}  (필수)
#   --config     YAML 파일 경로 (기본: 스크립트 위치 기준 configs/<mode>.yaml)
#   --quiet      비대화형: 사용자 입력 프롬프트 건너뜀
#   --output-json FILE  결과를 JSON 파일로 저장 (prod-test-runner 파싱용)
#
# 전제 조건:
#   - orin venv: ~/smolvla/orin/.hylion_arm
#   - lerobot [hardware,feetech] extra 설치 (SO-ARM 포트·카메라 발견)
#   - orin/config/ports.json, cameras.json (placeholder 또는 실 cache)
#
# 종료 코드:
#   0 — 모든 점검 PASS
#   1 — 하나 이상 FAIL (상세는 --output-json 또는 stdout)
#   2 — 사용법 오류
# =============================================================================

set -uo pipefail
# 주의: set -e 를 사용하지 않음. 개별 step 실패가 전체 중단을 유발하지 않도록
# 각 step 함수는 return 1 로 실패를 알리고 메인에서 || overall_exit=1 로 수집

# ---------------------------------------------------------------------------
# 0. 경로 상수
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_ACTIVATE="${HOME}/smolvla/orin/.hylion_arm/bin/activate"
CONFIG_DIR="${ORIN_DIR}/config"
PORTS_JSON="${CONFIG_DIR}/ports.json"
CAMERAS_JSON="${CONFIG_DIR}/cameras.json"

# cusparseLt LD_LIBRARY_PATH fallback (05_orin_venv_setting.md §3·§4 패턴)
CUSPARSELT_PATH="${HOME}/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib"

# JSON 결과 임시 파일 (특수문자 안전 처리)
TMP_RESULT_JSON="$(mktemp /tmp/check_hardware_XXXXXX.json)"
trap 'rm -f "${TMP_RESULT_JSON}"' EXIT

# ---------------------------------------------------------------------------
# 1. 인자 파싱
# ---------------------------------------------------------------------------
MODE=""
CONFIG_FILE=""
QUIET=false
OUTPUT_JSON=""

usage() {
    echo "사용법: bash check_hardware.sh --mode {first-time|resume} [--config YAML] [--quiet] [--output-json FILE]"
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"; shift 2 ;;
        --config)
            CONFIG_FILE="$2"; shift 2 ;;
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

if [[ -z "$MODE" ]]; then
    echo "[ERROR] --mode 필수 인자 누락"; usage
fi
if [[ "$MODE" != "first-time" && "$MODE" != "resume" ]]; then
    echo "[ERROR] --mode 는 first-time 또는 resume 이어야 합니다 (입력: '${MODE}')"; usage
fi

# config 파일 기본값
if [[ -z "$CONFIG_FILE" ]]; then
    if [[ "$MODE" == "first-time" ]]; then
        CONFIG_FILE="${SCRIPT_DIR}/configs/first_time.yaml"
    else
        CONFIG_FILE="${SCRIPT_DIR}/configs/resume.yaml"
    fi
fi

# ---------------------------------------------------------------------------
# 2. 결과 관리 (JSON 임시 파일 방식 — 특수문자 안전)
# ---------------------------------------------------------------------------
PASS_COUNT=0
FAIL_COUNT=0

# 초기 JSON 구조 기록
python3 -c "
import json
data = {'mode': '${MODE}', 'steps': {}}
with open('${TMP_RESULT_JSON}', 'w') as f:
    json.dump(data, f, indent=2)
"

record_step() {
    local step_name="$1"
    local status="$2"   # PASS | FAIL
    local detail="$3"

    if [[ "$status" == "PASS" ]]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        [[ "$QUIET" == "false" ]] && echo "[PASS] ${step_name}: ${detail}"
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
except Exception as e:
    pass  # JSON 기록 실패해도 스크립트 계속 진행
"
}

# ---------------------------------------------------------------------------
# 3. venv 활성화 (BACKLOG 03 #14 해소 핵심)
#    SSH 비대화형 환경에서도 이 스크립트가 직접 source 수행 →
#    호출자가 venv 를 미리 활성화할 필요 없음
# ---------------------------------------------------------------------------
step_venv() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 1/4] venv 활성화 ==="

    if [[ ! -f "$VENV_ACTIVATE" ]]; then
        record_step "venv" "FAIL" "activate 스크립트 미존재: ${VENV_ACTIVATE}"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV_ACTIVATE"

    # cusparseLt fallback (05_orin_venv_setting.md §3 패턴)
    # 시스템 설치 없을 경우 pip 번들 경로를 LD_LIBRARY_PATH 에 추가
    if [[ -d "$CUSPARSELT_PATH" ]]; then
        export LD_LIBRARY_PATH="${CUSPARSELT_PATH}:${LD_LIBRARY_PATH:-}"
    fi

    local python_bin
    python_bin="$(which python3)"
    record_step "venv" "PASS" "python: ${python_bin}"
}

# ---------------------------------------------------------------------------
# 4. CUDA 라이브러리 점검 (BACKLOG 03 #14)
#    setup_env.sh §6 검증 패턴과 동일 — libcusparseLt lazy load 트리거 포함
# ---------------------------------------------------------------------------
step_cuda() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 2/4] CUDA 라이브러리 점검 ==="

    local cuda_out
    local cuda_exit=0
    cuda_out=$(python3 - 2>&1 <<'PYEOF'
import sys
try:
    import torch
    assert torch.cuda.is_available(), "torch.cuda.is_available() == False"
    # libcusparseLt lazy load 트리거 (setup_env.sh §6 패턴)
    a = torch.cuda.FloatTensor(2).zero_()
    b = torch.randn(2).cuda()
    _ = a + b
    torch.backends.cudnn.version()
    print(f"OK torch={torch.__version__} cuda={torch.version.cuda}")
except AssertionError as e:
    print(f"FAIL {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"FAIL {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
) || cuda_exit=$?

    if [[ $cuda_exit -eq 0 ]]; then
        record_step "cuda" "PASS" "${cuda_out}"
    else
        record_step "cuda" "FAIL" "${cuda_out}"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# 5. SO-ARM 포트 발견
#    lerobot_find_port.py 의 find_port() 는 stdin 대화형 (input() 호출) →
#    비대화형 가능한 find_available_ports() 의 Linux 부분만 wrapping:
#      /dev/ttyACM* (Feetech 서보 USB) + /dev/ttyUSB* 스캔
#    BACKLOG 01 #1 해소: 동적 발견 + cache 저장 → udev rule 의존 제거
# ---------------------------------------------------------------------------
step_soarm_port() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 3/4] SO-ARM 포트 발견 ==="

    local port_out
    local port_exit=0
    port_out=$(python3 - 2>&1 <<'PYEOF'
import json, sys, platform
from pathlib import Path

if platform.system() != "Linux":
    print("SKIP non-Linux", file=sys.stderr)
    sys.exit(0)

# lerobot_find_port.py find_available_ports() 의 Linux 분기 기반:
# ttyACM* = Feetech STS/SCS 서보 (SO-ARM 사용), ttyUSB* = 일반 USB-Serial
tty_paths = sorted(Path("/dev").glob("ttyACM*")) + sorted(Path("/dev").glob("ttyUSB*"))
ports = [str(p) for p in tty_paths if p.exists()]

if not ports:
    # exit 2: 포트 없음 (오류 아님)
    sys.exit(2)

print(json.dumps(ports))
PYEOF
) || port_exit=$?

    if [[ $port_exit -eq 2 ]]; then
        # 포트 없음: first-time 은 경고(PASS), resume 은 FAIL
        if [[ "$MODE" == "first-time" ]]; then
            [[ "$QUIET" == "false" ]] && echo "[WARN] SO-ARM 포트 미발견 (연결 전이면 정상)"
            record_step "soarm_port" "PASS" "포트 미발견 (first-time: 연결 전 허용)"
            # ports.json 미갱신 (null 유지)
        else
            record_step "soarm_port" "FAIL" "포트 미발견 — SO-ARM 연결 확인 필요"
            return 1
        fi
        return 0
    elif [[ $port_exit -ne 0 ]]; then
        record_step "soarm_port" "FAIL" "포트 스캔 오류: ${port_out}"
        return 1
    fi

    # 발견된 포트 목록 (JSON 배열 문자열)
    local found_ports_json="$port_out"
    [[ "$QUIET" == "false" ]] && echo "발견된 포트: ${found_ports_json}"

    if [[ "$MODE" == "first-time" ]]; then
        local follower_input=""
        local leader_input=""

        if [[ "$QUIET" == "false" ]]; then
            echo ""
            echo "SO-ARM follower 포트를 입력하세요 (예: /dev/ttyACM0, 없으면 Enter):"
            read -r follower_input
            echo "SO-ARM leader 포트를 입력하세요 (없으면 Enter):"
            read -r leader_input
        else
            # --quiet: 첫 번째 포트를 follower 자동 할당
            follower_input=$(python3 -c "import json,sys; ports=json.loads(sys.argv[1]); print(ports[0] if ports else '')" "${found_ports_json}")
            leader_input=""
        fi

        # ports.json 갱신 (환경변수 경유)
        FOLLOWER_PORT="$follower_input" LEADER_PORT="$leader_input" PORTS_JSON_PATH="$PORTS_JSON" \
        python3 -c "
import json, os
follower = os.environ.get('FOLLOWER_PORT') or None
leader = os.environ.get('LEADER_PORT') or None
path = os.environ['PORTS_JSON_PATH']
with open(path, 'w') as f:
    json.dump({'follower_port': follower, 'leader_port': leader}, f, indent=2)
print('ports.json 갱신 완료')
"
        record_step "soarm_port" "PASS" "발견: ${found_ports_json} follower=${follower_input:-null}"

    else
        # resume: cache 와 현재 포트 비교
        if [[ ! -f "$PORTS_JSON" ]]; then
            record_step "soarm_port" "FAIL" "ports.json 미존재 (first-time 먼저 실행 필요)"
            return 1
        fi

        local cached_follower
        cached_follower=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(d.get('follower_port') or '')
" "${PORTS_JSON}")

        if [[ -z "$cached_follower" ]]; then
            # cache follower_port = null → 비교 건너뜀
            record_step "soarm_port" "PASS" "cache follower_port=null (발견된 포트: ${found_ports_json})"
        else
            if echo "${found_ports_json}" | python3 -c "
import json, sys
ports = json.load(sys.stdin)
cached = sys.argv[1]
sys.exit(0 if cached in ports else 1)
" "${cached_follower}" 2>/dev/null; then
                record_step "soarm_port" "PASS" "cache 일치: ${cached_follower}"
            else
                record_step "soarm_port" "FAIL" "cache(${cached_follower}) 가 현재 포트 목록에 없음: ${found_ports_json}"
                return 1
            fi
        fi
    fi
}

# ---------------------------------------------------------------------------
# 6. 카메라 인덱스·flip 발견
#    lerobot_find_cameras.py 의 OpenCVCamera.find_cameras() 비대화형 호출
#    (lerobot 레퍼런스: camera_opencv.py OpenCVCamera.find_cameras() 정적 메서드)
#    BACKLOG 03 #15 (인덱스 발견) + BACKLOG 03 #16 (wrist flip 확인) 해소
# ---------------------------------------------------------------------------
step_cameras() {
    [[ "$QUIET" == "false" ]] && echo ""
    [[ "$QUIET" == "false" ]] && echo "=== [Step 4/4] 카메라 인덱스·flip 발견 ==="

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
        record_step "cameras" "FAIL" "lerobot import 실패: ${cam_out}"
        return 1
    elif [[ $cam_exit -ne 0 ]]; then
        record_step "cameras" "FAIL" "카메라 스캔 오류: ${cam_out}"
        return 1
    fi

    local found_count
    found_count=$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])))" "${cam_out}" 2>/dev/null || echo "0")
    [[ "$QUIET" == "false" ]] && echo "발견된 카메라 ${found_count}개"

    if [[ "$MODE" == "first-time" ]]; then
        if [[ "$found_count" -eq 0 ]]; then
            [[ "$QUIET" == "false" ]] && echo "[WARN] 카메라 미발견 (연결 전이면 정상)"
            record_step "cameras" "PASS" "카메라 미발견 (first-time: 연결 전 허용)"
            return 0
        fi

        [[ "$QUIET" == "false" ]] && echo "카메라 목록: ${cam_out}"

        local top_index=""
        local top_flip="false"
        local wrist_index=""
        local wrist_flip="false"

        if [[ "$QUIET" == "false" ]]; then
            echo ""
            echo "top 카메라 인덱스를 입력하세요 (예: /dev/video0, 없으면 Enter):"
            read -r top_index
            echo "top 카메라 상하반전 여부 (y/n, 기본 n):"
            read -r top_flip_input
            [[ "${top_flip_input:-n}" == "y" ]] && top_flip="true" || top_flip="false"

            echo ""
            echo "wrist 카메라 인덱스를 입력하세요 (없으면 Enter):"
            read -r wrist_index
            echo "wrist 카메라 상하반전 여부 (y/n, BACKLOG 03 #16 — 기본 n):"
            read -r wrist_flip_input
            [[ "${wrist_flip_input:-n}" == "y" ]] && wrist_flip="true" || wrist_flip="false"
        else
            # --quiet: 발견 순서대로 top(첫 번째), wrist(두 번째) 자동 할당
            top_index=$(python3 -c "import json,sys; cams=json.loads(sys.argv[1]); print(str(cams[0]['id']) if cams else '')" "${cam_out}")
            wrist_index=$(python3 -c "import json,sys; cams=json.loads(sys.argv[1]); print(str(cams[1]['id']) if len(cams)>1 else '')" "${cam_out}")
        fi

        # cameras.json 갱신 (환경변수 경유)
        TOP_INDEX="$top_index" TOP_FLIP="$top_flip" \
        WRIST_INDEX="$wrist_index" WRIST_FLIP="$wrist_flip" \
        CAMERAS_JSON_PATH="$CAMERAS_JSON" \
        python3 -c "
import json, os
top_idx = os.environ.get('TOP_INDEX') or None
wrist_idx = os.environ.get('WRIST_INDEX') or None
top_flip = os.environ.get('TOP_FLIP', 'false') == 'true'
wrist_flip = os.environ.get('WRIST_FLIP', 'false') == 'true'
path = os.environ['CAMERAS_JSON_PATH']
data = {
    'top': {'index': top_idx, 'flip': top_flip},
    'wrist': {'index': wrist_idx, 'flip': wrist_flip}
}
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
print('cameras.json 갱신 완료')
"
        record_step "cameras" "PASS" "발견 ${found_count}개 / top=${top_index:-null} flip=${top_flip} / wrist=${wrist_index:-null} flip=${wrist_flip}"

    else
        # resume: cache 와 현재 발견 비교
        if [[ ! -f "$CAMERAS_JSON" ]]; then
            record_step "cameras" "FAIL" "cameras.json 미존재 (first-time 먼저 실행 필요)"
            return 1
        fi

        local cached_top_idx cached_wrist_idx
        cached_top_idx=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(str(d.get('top', {}).get('index') or ''))
" "${CAMERAS_JSON}")
        cached_wrist_idx=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(str(d.get('wrist', {}).get('index') or ''))
" "${CAMERAS_JSON}")

        # 현재 발견된 카메라 ID 목록
        local current_ids_json
        current_ids_json=$(python3 -c "import json,sys; cams=json.loads(sys.argv[1]); print(json.dumps([str(c['id']) for c in cams]))" "${cam_out}")

        # top 비교 (cache null 이면 건너뜀)
        if [[ -n "$cached_top_idx" ]]; then
            if ! python3 -c "
import json, sys
ids = json.loads(sys.argv[1])
cached = sys.argv[2]
sys.exit(0 if cached in ids else 1)
" "${current_ids_json}" "${cached_top_idx}" 2>/dev/null; then
                record_step "cameras" "FAIL" "top cache(${cached_top_idx}) 미발견 — 현재: ${current_ids_json}"
                return 1
            fi
        fi

        # wrist 비교 (cache null 이면 건너뜀)
        if [[ -n "$cached_wrist_idx" ]]; then
            if ! python3 -c "
import json, sys
ids = json.loads(sys.argv[1])
cached = sys.argv[2]
sys.exit(0 if cached in ids else 1)
" "${current_ids_json}" "${cached_wrist_idx}" 2>/dev/null; then
                record_step "cameras" "FAIL" "wrist cache(${cached_wrist_idx}) 미발견 — 현재: ${current_ids_json}"
                return 1
            fi
        fi

        record_step "cameras" "PASS" "cache 일치 / top=${cached_top_idx:-null} wrist=${cached_wrist_idx:-null} / 현재: ${current_ids_json}"
    fi
}

# ---------------------------------------------------------------------------
# 7. JSON 출력 마무리
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
    fi

    return $total_exit
}

# ---------------------------------------------------------------------------
# 8. 메인 실행
# ---------------------------------------------------------------------------
main() {
    if [[ "$QUIET" == "false" ]]; then
        echo ""
        echo "=============================="
        echo " check_hardware.sh (mode: ${MODE})"
        echo " config: ${CONFIG_FILE}"
        echo "=============================="
    fi

    local overall_exit=0

    # set -e 로 인한 중단 방지: || true 로 개별 실패를 overall_exit 에 기록
    step_venv     || overall_exit=1
    step_cuda     || overall_exit=1
    step_soarm_port || overall_exit=1
    step_cameras  || overall_exit=1

    finalize_output || overall_exit=1
    return $overall_exit
}

main
