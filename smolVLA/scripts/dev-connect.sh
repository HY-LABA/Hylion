#!/bin/bash
set -euo pipefail

ORIN_IP_HY=172.16.134.117
ORIN_IP_EDU=172.16.134.117
DGX_IP_HY=172.16.142.85
DGX_IP_EDU=172.16.142.85

# ─────────────────────────────────────
# Step 1) WiFi 네트워크 선택
# ─────────────────────────────────────
echo "================================"
echo "  Step 1: WiFi 네트워크 선택"
echo "================================"
PS3=$'\n선택 (번호): '
select _choice in "hy   (HY-WiFi)" "edu  (eduroam)"; do
    case "$REPLY" in
        1) NETWORK=hy;  break ;;
        2) NETWORK=edu; break ;;
        *) echo "1 또는 2 를 입력하세요. (입력값: $REPLY)" ;;
    esac
done

case "$NETWORK" in
    hy)  ORIN_IP="$ORIN_IP_HY"; DGX_IP="$DGX_IP_HY"  ;;
    edu) ORIN_IP="$ORIN_IP_EDU"; DGX_IP="$DGX_IP_EDU" ;;
esac

# ─────────────────────────────────────
# Step 2) 장치 선택
# ─────────────────────────────────────
echo
echo "================================"
echo "  Step 2: 장치 선택"
echo "================================"

PS3=$'\n선택 (번호): '
select _choice in "orin" "dgx" "both"; do
    case "$REPLY" in
        1) TARGET=orin; break ;;
        2) TARGET=dgx;  break ;;
        3) TARGET=both; break ;;
        *) echo "1, 2, 3 중 하나를 입력하세요. (입력값: $REPLY)" ;;
    esac
done

# ─────────────────────────────────────
# Step 3) 연결
# ─────────────────────────────────────
echo
if [[ "$TARGET" == "orin" || "$TARGET" == "both" ]]; then
    echo "→ Orin (${ORIN_IP}) 연결"
    code --remote "ssh-remote+laba@${ORIN_IP}" /home/laba
fi

if [[ "$TARGET" == "dgx" || "$TARGET" == "both" ]]; then
    echo "→ DGX (${DGX_IP}) 연결"
    code --remote "ssh-remote+laba@${DGX_IP}" /home/laba
fi
