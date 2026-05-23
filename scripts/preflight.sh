#!/usr/bin/env bash
# Hylion preflight — 시연 전 "환경 설정 확인" 단계 전용 점검 스크립트.
#
#   목적: 코디네이터를 실제로 띄우기 전에, 노트북에서 SSH 로 Jetson 에 들어와
#         하드웨어 / venv / 모델 / 네트워크 / NUC 연결이 모두 정상인지 한 번에
#         확인한다. 이 스크립트는 코디네이터(메인 루프)를 절대 띄우지 않는다 —
#         오직 점검만. "환경 설정"(확인) 과 "작동 시작"(run_coordinator.sh) 을
#         명확히 분리하기 위한 것.
#
#   사용법:
#     bash scripts/preflight.sh
#
#   결과 표기:
#     [ OK ]  정상
#     [WARN]  그 기능만 제한됨 — 작동 자체는 가능 (예: 오프라인 경로만 막힘)
#     [FAIL]  작동 불가 — 고치기 전에는 run_coordinator.sh 띄우지 말 것
#
#   종료코드: FAIL 이 하나라도 있으면 1, 아니면 0.
#
#   통과 후 다음 단계 (자세한 절차는 README "시연 절차" 참고):
#     bash scripts/test_wakeword.sh checkpoints/wakeword/Hey_Hyleon.tflite   # 간단 기능 테스트
#     bash scripts/run_coordinator.sh                                       # 작동 시작
#
# 주의: set -e 를 쓰지 않는다 — 한 항목이 실패해도 나머지 점검을 끝까지 돌려야 함.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── 색상 (tty 일 때만) ───────────────────────────────────────────────────────
if [ -t 1 ]; then
    C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_FAIL=$'\033[31m'
    C_DIM=$'\033[2m'; C_BOLD=$'\033[1m'; C_RST=$'\033[0m'
else
    C_OK=; C_WARN=; C_FAIL=; C_DIM=; C_BOLD=; C_RST=
fi

n_ok=0; n_warn=0; n_fail=0
ok()   { printf '  %s[ OK ]%s %s\n' "$C_OK"   "$C_RST" "$1"; n_ok=$((n_ok+1)); }
warn() { printf '  %s[WARN]%s %s\n' "$C_WARN" "$C_RST" "$1"; n_warn=$((n_warn+1));
         [ -n "${2:-}" ] && printf '         %s↳ %s%s\n' "$C_DIM" "$2" "$C_RST"; return 0; }
fail() { printf '  %s[FAIL]%s %s\n' "$C_FAIL" "$C_RST" "$1"; n_fail=$((n_fail+1));
         [ -n "${2:-}" ] && printf '         %s↳ %s%s\n' "$C_DIM" "$2" "$C_RST"; return 0; }
info() { printf '  %s[INFO]%s %s\n' "$C_DIM"  "$C_RST" "$1"; }
section() { printf '\n%s── %s%s\n' "$C_BOLD" "$1" "$C_RST"; }

# host port — TCP 연결 가능하면 0
tcp_ok() { timeout 3 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null; }

# ── 점검 대상 설정 (run_coordinator.sh 와 동일한 기본값) ─────────────────────
BHL_HOST="${HYLION_BHL_HOST:-10.42.0.221}"
BHL_PORT="${HYLION_BHL_PORT:-9000}"
MIC_KEYWORD="${HYLION_WAKEWORD_DEVICE_KEYWORD:-P5HD}"
TTS_HOST="127.0.0.1"; TTS_PORT="8001"
OLLAMA_HOST="127.0.0.1"; OLLAMA_PORT="11434"
WAKEWORD_MODEL="${HYLION_WAKEWORD_MODEL:-$PROJECT_ROOT/checkpoints/wakeword/Hey_Hyleon.tflite}"
ESTOP_MODEL="${HYLION_ESTOP_MODEL:-$PROJECT_ROOT/checkpoints/wakeword/hyleon_stop.tflite}"
VENV="$PROJECT_ROOT/jetson/expression/.venv"
VENV_PY="$VENV/bin/python"
GESTURE_VENV="$(eval echo "${JETSON_VENV:-~/smolvla/orin/.hylion_arm}")"

printf '%s╔══════════════════════════════════════════════════════════╗%s\n' "$C_BOLD" "$C_RST"
printf '%s║  Hylion preflight — 시연 전 환경 점검 (코디네이터 안 띄움) ║%s\n' "$C_BOLD" "$C_RST"
printf '%s╚══════════════════════════════════════════════════════════╝%s\n' "$C_BOLD" "$C_RST"
printf '  %sPROJECT_ROOT%s  %s\n'  "$C_DIM" "$C_RST" "$PROJECT_ROOT"
printf '  %sNUC bridge%s    %s:%s\n' "$C_DIM" "$C_RST" "$BHL_HOST" "$BHL_PORT"
printf '  %s마이크 키워드%s  %s\n'  "$C_DIM" "$C_RST" "$MIC_KEYWORD"

# 종합 판정용 상태 플래그
NET_ONLINE=false; OLLAMA_UP=false; MELO_UP=false; GROQ_KEY=false; CLOVA_KEY=false

# ── 1. Python venv & CUDA 라이브러리 ────────────────────────────────────────
section "1. Python venv & 라이브러리"
if [ -x "$VENV_PY" ]; then
    ok "coordinator venv: $VENV_PY"
else
    fail "coordinator venv python 없음: $VENV_PY" \
         "WORKLOG 2026-05-04 항목대로 jetson/expression/.venv 를 먼저 구축할 것."
fi

CUSPARSELT="$VENV/lib/python3.10/site-packages/nvidia/cusparselt/lib/libcusparseLt.so.0"
if [ -e "$CUSPARSELT" ]; then
    ok "libcusparseLt.so.0 (PyTorch/Whisper 의존)"
else
    fail "libcusparseLt.so.0 없음" "venv 안 nvidia wheel 누락 — Whisper 가 import 시 죽음."
fi

if [ -x "$VENV_PY" ]; then
    if "$VENV_PY" -c "import Jetson.GPIO" 2>/dev/null; then
        ok "Jetson.GPIO import (입 서보 lipsync)"
    else
        warn "Jetson.GPIO import 실패" "입 서보 lipsync 만 비활성 — 음성/동작은 정상."
    fi
fi

# ── 2. 모델 파일 ────────────────────────────────────────────────────────────
section "2. wake-word 모델 파일"
if [ -f "$WAKEWORD_MODEL" ]; then
    ok "메인 wake-word 모델: $(basename "$WAKEWORD_MODEL")"
else
    fail "메인 wake-word 모델 없음: $WAKEWORD_MODEL" "이게 없으면 'Hey Hyleon' 자체가 안 됨."
fi
if [ -f "$ESTOP_MODEL" ]; then
    ok "e-stop 모델: $(basename "$ESTOP_MODEL")"
else
    warn "e-stop 모델 없음: $ESTOP_MODEL" "음성 비상정지만 비활성 — 동작 자체는 가능."
fi

# ── 3. 오디오 하드웨어 ──────────────────────────────────────────────────────
section "3. 오디오 하드웨어 (마이크 / 스피커)"
if command -v arecord >/dev/null 2>&1; then
    if arecord -l 2>/dev/null | grep -qi "$MIC_KEYWORD"; then
        ok "마이크 '$MIC_KEYWORD' 인식됨"
    else
        fail "마이크 '$MIC_KEYWORD' 가 arecord -l 에 없음" \
             "USB 마이크 재연결 후 'arecord -l' 로 확인. 다른 마이크면 HYLION_WAKEWORD_DEVICE_KEYWORD export."
    fi
else
    warn "arecord 미설치 — 마이크 자동 점검 불가" "수동 확인 필요."
fi
if command -v aplay >/dev/null 2>&1; then
    if LC_ALL=C aplay -l 2>/dev/null | grep -q '^card'; then
        ok "재생 장치(스피커) 인식됨"
    else
        warn "재생 장치가 aplay -l 에 없음" "USB 스피커 연결 확인 — 없으면 TTS 가 안 들림."
    fi
else
    warn "aplay 미설치 — 스피커 자동 점검 불가" "수동 확인 필요."
fi

# ── 4. NUC BHL bridge 연결 ──────────────────────────────────────────────────
section "4. NUC BHL bridge 연결 ($BHL_HOST:$BHL_PORT)"
if tcp_ok "$BHL_HOST" "$BHL_PORT"; then
    ok "NUC bridge TCP 도달 가능"
else
    warn "NUC bridge ($BHL_HOST:$BHL_PORT) 에 연결 안 됨" \
         "다리 동작(move/stop) 불가 — 대화/팔 동작은 가능. NUC 의 hylion-bridge.service 와 유선 직결 확인."
fi

# ── 5. 로컬 데몬 (오프라인 경로용) ──────────────────────────────────────────
section "5. 로컬 데몬 (오프라인 경로용)"
if tcp_ok "$OLLAMA_HOST" "$OLLAMA_PORT"; then
    ok "Ollama 데몬 응답 ($OLLAMA_HOST:$OLLAMA_PORT)"; OLLAMA_UP=true
else
    warn "Ollama 데몬 안 뜸" "오프라인 LLM 불가. 켜기: sudo systemctl start ollama"
fi
if tcp_ok "$TTS_HOST" "$TTS_PORT"; then
    ok "MeloTTS 서버 응답 ($TTS_HOST:$TTS_PORT)"; MELO_UP=true
else
    warn "MeloTTS 서버 안 뜸" "오프라인 TTS 불가. 켜기: systemctl --user start hylion-tts (또는 services/tts_server 참고)"
fi

# ── 6. gesture (우측 SO-ARM) ────────────────────────────────────────────────
section "6. gesture (우측 SO-ARM)"
if [ -x "$GESTURE_VENV/bin/python" ]; then
    ok "gesture venv: $GESTURE_VENV"
else
    warn "gesture venv 없음: $GESTURE_VENV" "팔 동작만 비활성 — 대화/다리 동작은 정상."
fi
if ls /dev/ttyUSB* /dev/ttyACM* >/dev/null 2>&1; then
    ok "시리얼 장치 감지: $(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | tr '\n' ' ')"
else
    warn "시리얼 장치(/dev/ttyUSB*, /dev/ttyACM*) 없음" "SO-ARM USB(CH340) 연결 확인 — 팔 동작용."
fi

# ── 7. 네트워크 & API 키 ────────────────────────────────────────────────────
# 키 점검은 "실제 코드가 어디서 읽는지" 에 맞춤:
#   GROQ_API_KEY  — groq_llm/groq_whisper 가 os.getenv 만 봄 (.env 자동 로드 X)
#                   → 셸 환경변수로 export 돼 있어야 함.
#   Clova 키      — speaker.py 가 .env 파일을 직접 파싱 (Naver_Clova_Speech_*).
section "7. 네트워크 & API 키"
if tcp_ok api.groq.com 443; then
    ok "인터넷 연결 — online 경로(Groq/Clova) 사용 가능"; NET_ONLINE=true
else
    info "인터넷 연결 안 됨 — offline 경로(Ollama/MeloTTS)로 동작"
fi

# .env 파일에서 key 값이 비어있지 않은지 (값은 노출 안 함)
envfile_has() { awk -F= -v k="$1" '$1==k && length($2)>0 {f=1} END{exit !f}' "$2" 2>/dev/null; }

if [ -n "${GROQ_API_KEY:-}" ]; then
    GROQ_KEY=true; ok "GROQ_API_KEY 환경변수 설정됨 (online LLM/STT)"
else
    warn "GROQ_API_KEY 환경변수 없음" \
         "online LLM/STT 불가 — 쓰려면 run 전에 'export GROQ_API_KEY=...' (offline Ollama 는 영향 없음)."
fi

ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    if envfile_has Naver_Clova_Speech_Client_ID "$ENV_FILE" \
       && envfile_has Naver_Clova_Speech_Client_Secret "$ENV_FILE"; then
        CLOVA_KEY=true; ok "Clova 키(.env Naver_Clova_Speech_Client_*) 설정됨"
    else
        warn ".env 의 Clova 키(Naver_Clova_Speech_Client_ID/Secret) 비어있음" \
             "online TTS(Clova) 불가 — gTTS/MeloTTS 로 fallback."
    fi
else
    warn ".env 파일 없음: $ENV_FILE" "Clova online TTS 불가."
fi

# ── 8. LLM / TTS 가용 경로 종합 판정 ────────────────────────────────────────
section "8. LLM / TTS 가용 경로 종합"
if   $NET_ONLINE && $GROQ_KEY; then ok "LLM: online(Groq) 경로 가능"
elif $OLLAMA_UP;               then ok "LLM: offline(Ollama) 경로 가능"
else fail "LLM 경로 없음" "online(Groq)·offline(Ollama) 둘 다 불가 — 대화가 동작하지 않음."
fi
if   $NET_ONLINE && $CLOVA_KEY; then ok "TTS: online(Clova) 경로 가능"
elif $MELO_UP;                  then ok "TTS: offline(MeloTTS) 경로 가능"
else warn "TTS 경로 불확실" "Clova·MeloTTS 둘 다 불가 — 음성 출력이 안 될 수 있음."
fi

# ── 9. 코디네이터 서비스 충돌 점검 ──────────────────────────────────────────
section "9. 코디네이터 자동 실행 서비스"
if systemctl --user is-active --quiet hylion-coordinator.service 2>/dev/null; then
    warn "hylion-coordinator.service 가 이미 실행 중" \
         "수동 실행 시 마이크/포트 충돌. 먼저: systemctl --user stop hylion-coordinator"
else
    ok "자동 실행 서비스 미동작 — 수동 실행 가능 (정상)"
fi

# ── 요약 ────────────────────────────────────────────────────────────────────
printf '\n%s──────────────────────────────────────────────────────────%s\n' "$C_BOLD" "$C_RST"
printf '  결과:  %s%d OK%s   %s%d WARN%s   %s%d FAIL%s\n' \
    "$C_OK" "$n_ok" "$C_RST" "$C_WARN" "$n_warn" "$C_RST" "$C_FAIL" "$n_fail" "$C_RST"
if [ "$n_fail" -gt 0 ]; then
    printf '  %s판정: FAIL — 위 [FAIL] 항목을 고치기 전에는 작동 시작 보류.%s\n' "$C_FAIL" "$C_RST"
    printf '%s──────────────────────────────────────────────────────────%s\n' "$C_BOLD" "$C_RST"
    exit 1
fi
if [ "$n_warn" -gt 0 ]; then
    printf '  %s판정: PASS (경고 있음) — [WARN] 항목이 시연 범위에 필요한지 확인 후 진행.%s\n' "$C_WARN" "$C_RST"
else
    printf '  %s판정: PASS — 모든 항목 정상.%s\n' "$C_OK" "$C_RST"
fi
cat <<EOF
${C_BOLD}──────────────────────────────────────────────────────────${C_RST}
  다음 단계:
    1) 간단 기능 테스트:
         bash scripts/test_wakeword.sh checkpoints/wakeword/Hey_Hyleon.tflite
    2) 이상 없으면 작동 시작:
         bash scripts/run_coordinator.sh
EOF
exit 0
