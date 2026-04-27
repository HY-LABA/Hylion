#!/bin/bash
# 로컬에서 Orin / DGX Spark 스냅샷을 한 번에 수집하는 스크립트
# 사용법: bash ~/ros2_ws/src/LABA5_Bootcamp/smolVLA/docs/storage/run_snapshots.sh
# 출력: ./devices_snapshot/{orin,dgx_spark}_env_snapshot_YYYY-MM-DD_HHMM.txt
# 전제: ~/.ssh/config 에 Host alias 'orin', 'dgx' 가 설정돼 있어야 합니다.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="$SCRIPT_DIR/collect_snapshot.sh"
SAVE_DIR="$SCRIPT_DIR/devices_snapshot"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)

mkdir -p "$SAVE_DIR"

collect() {
  local label="$1"
  local alias="$2"
  local outfile="$SAVE_DIR/${label}_env_snapshot_${TIMESTAMP}.txt"

  echo "[${label}] 수집 시작 → ${alias}"
  ssh -o ConnectTimeout=10 -o BatchMode=yes "${alias}" 'bash -s' < "$PAYLOAD" > "$outfile" 2>&1
  local status=$?

  if [ $status -eq 0 ]; then
    echo "[${label}] 완료: $outfile"
  else
    echo "[${label}] 실패 (exit $status) — SSH 접속 또는 스크립트 오류 확인"
    rm -f "$outfile"
  fi
}

# 병렬 수집 (~/.ssh/config alias 사용)
collect "orin"      "orin" &
collect "dgx_spark" "dgx"  &

wait
echo ""
echo "전체 완료. 저장 위치: $SAVE_DIR"
