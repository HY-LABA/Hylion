#!/usr/bin/env bash
# Hylion coordinator 를 systemd user 서비스로 설치/제거한다.
#
# 설치:
#   bash scripts/install-coordinator-service.sh
#     - scripts/systemd/hylion-coordinator.service.in 를 PROJECT_ROOT 치환해
#       ~/.config/systemd/user/hylion-coordinator.service 로 복사
#     - sudo loginctl enable-linger $USER  (로그인 없이 부팅 시 자동 실행)
#     - systemctl --user enable --now
#
# 제거:
#   bash scripts/install-coordinator-service.sh --uninstall
#     - 서비스 stop/disable 후 unit 파일 삭제
#     - linger 는 건드리지 않음 (다른 user service 가 의존할 수 있어서).
#       완전히 끄려면 수동:  sudo loginctl disable-linger $USER
#
# 로그/조작 (설치 후):
#   journalctl --user -u hylion-coordinator -f      # 실시간 로그
#   systemctl --user status hylion-coordinator      # 상태
#   systemctl --user restart hylion-coordinator     # 재시작
#   systemctl --user stop hylion-coordinator        # 정지 (다음 부팅 때 다시 뜸)
set -euo pipefail

UNIT_NAME="hylion-coordinator.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$PROJECT_ROOT/scripts/systemd/${UNIT_NAME}.in"
USER_UNIT_DIR="$HOME/.config/systemd/user"
DST_UNIT="$USER_UNIT_DIR/$UNIT_NAME"

if [ "${1:-}" = "--uninstall" ]; then
    echo "[uninstall] stopping & disabling $UNIT_NAME"
    systemctl --user disable --now "$UNIT_NAME" 2>/dev/null || true
    rm -f "$DST_UNIT"
    systemctl --user daemon-reload
    echo "[uninstall] 완료. unit 파일 제거됨: $DST_UNIT"
    echo "[uninstall] linger 는 그대로 둠. 완전히 끄려면: sudo loginctl disable-linger $USER"
    exit 0
fi

if [ ! -f "$TEMPLATE" ]; then
    echo "[install] 템플릿이 없음: $TEMPLATE" >&2
    exit 1
fi

if [ ! -x "$PROJECT_ROOT/scripts/run_coordinator.sh" ]; then
    echo "[install] run_coordinator.sh 가 실행 권한이 없음. chmod +x 부여" >&2
    chmod +x "$PROJECT_ROOT/scripts/run_coordinator.sh"
fi

mkdir -p "$USER_UNIT_DIR"
# 템플릿 치환해서 설치 (심볼릭 링크 대신 복사 — 경로가 박혀나가야 systemd 가
# 다른 머신에서도 명확)
sed "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" "$TEMPLATE" > "$DST_UNIT"
echo "[install] unit 파일 설치: $DST_UNIT"

# linger 확인. 켜져 있지 않으면 켠다 (sudo 필요, 비번 프롬프트 뜰 수 있음).
if loginctl show-user "$USER" 2>/dev/null | grep -q "Linger=yes"; then
    echo "[install] linger 이미 활성: $USER"
else
    echo "[install] enabling linger for $USER  (sudo 필요)"
    sudo loginctl enable-linger "$USER"
fi

systemctl --user daemon-reload
systemctl --user enable "$UNIT_NAME"
systemctl --user restart "$UNIT_NAME"

echo
echo "[install] 설치 완료. 현재 상태:"
systemctl --user --no-pager status "$UNIT_NAME" || true

cat <<EOF

──────────────────────────────────────────────────────────────
조작 명령:
  실시간 로그:   journalctl --user -u $UNIT_NAME -f
  상태 확인:     systemctl --user status $UNIT_NAME
  재시작:        systemctl --user restart $UNIT_NAME
  정지:          systemctl --user stop $UNIT_NAME
  완전 제거:     bash scripts/install-coordinator-service.sh --uninstall
──────────────────────────────────────────────────────────────
EOF
