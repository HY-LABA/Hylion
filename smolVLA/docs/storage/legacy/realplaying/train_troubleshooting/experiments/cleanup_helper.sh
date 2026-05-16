#!/usr/bin/env bash
# cleanup_helper.sh — DGX 학습 전 환경 정리 헬퍼
# 사용 전 실행 권한 부여: chmod +x experiments/cleanup_helper.sh
# 사용: bash experiments/cleanup_helper.sh [--dry-run]
#
# ⚠️ pkill 패턴 주의:
#   - `pkill -9 -f code` 는 명령줄에 "code" 가 포함된 모든 프로세스 catch
#     (예: VSCode server, code-server, vscode-tunnel 등은 의도된 대상,
#      단 사용자가 "code" 가 포함된 다른 도구를 실행 중이면 함께 종료될 수 있음).
#     실행 전 `pgrep -af code` 로 어떤 프로세스가 잡힐지 한 번 확인 권장.
#   - `pkill -9 -f claude` 도 동일 — Claude Code 외 "claude" 포함 프로세스 catch 가능.
#   - dry-run (`--dry-run`) 으로 먼저 명령만 출력해 확인 가능.
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

log() { echo "[cleanup_helper] $*"; }
warn() { echo "[cleanup_helper] WARNING: $*" >&2; }

# ── dry-run 래퍼 ──────────────────────────────────────────────
run_cmd() {
    if $DRY_RUN; then
        echo "[DRY-RUN] $*"
    else
        eval "$*"
    fi
}

log "===== DGX 학습 전 환경 cleanup 시작 ====="
if $DRY_RUN; then
    log "(--dry-run 모드 — 실제 kill 없음)"
fi
echo

# ── (a) VSCode server 종료 ────────────────────────────────────
log "(a) VSCode server (code) 종료..."
run_cmd "pkill -9 -f code 2>/dev/null || true"

# ── (b) Claude Code CLI 종료 ─────────────────────────────────
log "(b) Claude Code CLI (claude) 종료..."
run_cmd "pkill -9 -f 'claude' 2>/dev/null || true"

# ── (c) Firefox 종료 ─────────────────────────────────────────
log "(c) Firefox 종료..."
run_cmd "pkill -9 -f firefox 2>/dev/null || true"

# ── (d) 3초 대기 후 잔존 프로세스 확인 ─────────────────────────
if ! $DRY_RUN; then
    log "(d) 3초 대기 후 잔존 프로세스 확인..."
    sleep 3

    RESIDUAL=()
    if pgrep -f 'code' > /dev/null 2>&1; then
        RESIDUAL+=("VSCode(code)")
    fi
    if pgrep -f 'claude' > /dev/null 2>&1; then
        RESIDUAL+=("Claude(claude)")
    fi
    if pgrep -f 'firefox' > /dev/null 2>&1; then
        RESIDUAL+=("Firefox(firefox)")
    fi

    if [[ ${#RESIDUAL[@]} -gt 0 ]]; then
        warn "다음 프로세스가 아직 잔존합니다: ${RESIDUAL[*]}"
        warn "수동으로 확인하세요: ps aux | grep -E 'code|claude|firefox'"
    else
        log "(d) 잔존 프로세스 없음 — 정상 종료 확인."
    fi
else
    echo "[DRY-RUN] sleep 3"
    echo "[DRY-RUN] pgrep -f 'code|claude|firefox' (잔존 확인)"
fi
echo

# ── (e) sync ─────────────────────────────────────────────────
log "(e) sync 호출 (버퍼 플러시)..."
run_cmd "sync"
echo

# ── (f) 메모리 현황 출력 ──────────────────────────────────────
log "(f) 현재 메모리 현황 (free -h):"
if ! $DRY_RUN; then
    free -h
else
    echo "[DRY-RUN] free -h"
fi
echo

# ── (g) MemAvailable 100GB 이상 검증 ─────────────────────────
if ! $DRY_RUN; then
    log "(g) MemAvailable >= 100 GB 검증..."
    MEM_AVAIL_KB=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    MEM_AVAIL_GB=$(echo "scale=1; $MEM_AVAIL_KB / 1048576" | bc)
    log "    MemAvailable = ${MEM_AVAIL_GB} GB (${MEM_AVAIL_KB} kB)"

    # 100GB = 100 * 1048576 = 104857600 kB
    if [[ "$MEM_AVAIL_KB" -lt 104857600 ]]; then
        warn "MemAvailable ${MEM_AVAIL_GB} GB < 100 GB — 학습 전 메모리 부족 위험."
        warn "추가 프로세스를 종료하거나 page cache drop 을 수행하세요."
        echo
        echo "  sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'"
        echo "  (sudo 가능 시 위 명령으로 page cache 를 비운 후 재시도)"
        exit 1
    else
        log "    OK — MemAvailable ${MEM_AVAIL_GB} GB >= 100 GB."
    fi
else
    echo "[DRY-RUN] awk '/MemAvailable/ {print \$2}' /proc/meminfo  (100GB+ 검증)"
fi
echo

# ── (h) page cache drop 안내 (sudo 필요라 직접 실행 X) ────────
log "(h) page cache drop 안내:"
echo "    sudo 가 가능하면 다음 명령으로 page cache 도 비워주세요:"
echo "      sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'"
echo "    그 후 'free -h' 로 MemAvailable 재확인."
echo

log "===== cleanup 완료. 학습을 시작해도 됩니다. ====="
