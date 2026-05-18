#!/usr/bin/env bash
# A 끄기: 다음 부팅부터 GUI/로그인 화면을 다시 띄운다 (graphical.target).
# coordinator (B 서비스) 는 영향 없음 — GUI 위에서도 그대로 백그라운드 실행됨.
#
# 사용:
#   bash scripts/headless-off.sh
#
# 재부팅 없이 즉시 GUI 켜고 싶으면:
#   sudo systemctl isolate graphical.target
set -euo pipefail

current="$(systemctl get-default)"
if [ "$current" = "graphical.target" ]; then
    echo "[headless-off] 이미 graphical.target. 변경 없음."
    exit 0
fi

echo "[headless-off] 현재 default-target: $current"
echo "[headless-off] -> graphical.target 로 변경  (sudo 필요)"
sudo systemctl set-default graphical.target

cat <<EOF

[headless-off] 완료. 다음 부팅부터 GUI 다시 뜸.
  - 다시 끄기:           bash scripts/headless-on.sh
  - 지금 즉시 GUI 켜기:  sudo systemctl isolate graphical.target
  - 재부팅:              sudo reboot
EOF
