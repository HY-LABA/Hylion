#!/usr/bin/env bash
# A 켜기: 다음 부팅부터 GUI/로그인 화면을 띄우지 않고 텍스트 콘솔로 부팅한다.
# coordinator (B 서비스) 는 linger 덕분에 그대로 자동 실행됨.
#
# 사용:
#   bash scripts/headless-on.sh
#
# 되돌리려면 (GUI 다시 켜기):
#   bash scripts/headless-off.sh
#
# 재부팅 없이 즉시 GUI 끄고 싶으면:
#   sudo systemctl isolate multi-user.target
#   (이러면 현재 X 세션이 죽음. SSH 로 들어와 있는 게 아니면 위험)
set -euo pipefail

current="$(systemctl get-default)"
if [ "$current" = "multi-user.target" ]; then
    echo "[headless-on] 이미 multi-user.target. 변경 없음."
    exit 0
fi

echo "[headless-on] 현재 default-target: $current"
echo "[headless-on] -> multi-user.target 로 변경  (sudo 필요)"
sudo systemctl set-default multi-user.target

cat <<EOF

[headless-on] 완료. 다음 부팅부터 GUI 안 뜸.
  - 되돌리기:           bash scripts/headless-off.sh
  - 지금 즉시 GUI 끄기:  sudo systemctl isolate multi-user.target   (X 세션 끊김 주의)
  - 재부팅:              sudo reboot
EOF
