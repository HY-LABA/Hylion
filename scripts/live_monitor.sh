#!/usr/bin/env bash
# 라이브 모니터: Hylion 풀 가동 중 RAM/GPU/프로세스 상태를 1초마다 갱신.
#
# 사용법:  bash scripts/live_monitor.sh
# 종료:    Ctrl+C

set +e
trap 'echo; echo "[모니터 종료]"; exit 0' INT TERM

# 색깔 코드 (terminal이 지원하면)
if [ -t 1 ]; then
    BOLD=$'\e[1m'; CYAN=$'\e[36m'; YEL=$'\e[33m'; GRN=$'\e[32m'; RED=$'\e[31m'; RST=$'\e[0m'
else
    BOLD=""; CYAN=""; YEL=""; GRN=""; RED=""; RST=""
fi

# tegrastats를 백그라운드로 한 번만 띄우고 마지막 줄 캐시
TEG_PIPE=/tmp/hylion_tegrastats.pipe
[ -p "$TEG_PIPE" ] || mkfifo "$TEG_PIPE" 2>/dev/null
tegrastats --interval 1000 > /tmp/hylion_tegrastats.log 2>&1 &
TEG_PID=$!
trap "kill $TEG_PID 2>/dev/null; rm -f $TEG_PIPE; exit 0" INT TERM

while true; do
    clear
    echo "${BOLD}${CYAN}═══ Hylion 라이브 모니터  ($(date +%H:%M:%S)) ═══${RST}"
    echo

    # ── RAM/SWAP ─────────────────────────────────────────────
    echo "${BOLD}메모리:${RST}"
    free -h | awk 'NR==1{print "         " $0}
                   NR==2{printf "  RAM    %s\n", $0}
                   NR==3{printf "  SWAP   %s\n", $0}'
    echo

    # ── 우리 핵심 프로세스 ───────────────────────────────────
    echo "${BOLD}프로세스:${RST}"
    printf "  %-6s %10s %s\n" "PID" "RSS(MB)" "CMD"
    ps -eo pid,rss,cmd --no-headers 2>/dev/null \
      | awk 'BEGIN{FS=" +"}
             /coordinator|tts_server|ollama|whisper/ && !/awk/ && !/grep/ {
                 cmd=$3; for (i=4;i<=NF && i<=12;i++) cmd=cmd" "$i;
                 printf "  %-6d %10.1f %s\n", $1, $2/1024, cmd
             }' \
      | sort -k2 -nr | head -10

    echo

    # ── tegrastats 마지막 라인 (CPU%, RAM, GPU%) ───────────────
    echo "${BOLD}Tegra (CPU/RAM/GPU):${RST}"
    LAST=$(tail -n 1 /tmp/hylion_tegrastats.log 2>/dev/null)
    if [ -n "$LAST" ]; then
        # tegrastats 형식: "RAM 5042/7620MB ... CPU [25%@1500,...] ... GR3D_FREQ 10%@600 ..."
        echo "$LAST" \
          | grep -oE "RAM [0-9]+/[0-9]+MB|CPU \[[^]]+\]|GR3D_FREQ [^ ]+|gpu@[0-9]+C|cpu@[0-9]+C" \
          | head -5 | sed 's/^/  /'
    else
        echo "  (tegrastats 로딩 중...)"
    fi
    echo

    # ── 데몬 health ──────────────────────────────────────────
    echo "${BOLD}데몬 상태:${RST}"
    OLL=$(curl -sS --max-time 1 http://127.0.0.1:11434/api/tags 2>/dev/null | head -c 50)
    if [ -n "$OLL" ]; then
        echo "  ${GRN}● ollama${RST}    127.0.0.1:11434 alive"
    else
        echo "  ${RED}○ ollama${RST}    down"
    fi
    TTS=$(curl -sS --max-time 1 http://127.0.0.1:8001/health 2>/dev/null)
    if [ -n "$TTS" ]; then
        if echo "$TTS" | grep -q '"loaded":true'; then
            echo "  ${GRN}● tts${RST}       127.0.0.1:8001 ${YEL}loaded${RST}"
        else
            echo "  ${GRN}● tts${RST}       127.0.0.1:8001 ${CYAN}lazy (모델 미적재)${RST}"
        fi
    else
        echo "  ${RED}○ tts${RST}       down"
    fi
    echo
    echo "(Ctrl+C 종료)"

    sleep 1
done
