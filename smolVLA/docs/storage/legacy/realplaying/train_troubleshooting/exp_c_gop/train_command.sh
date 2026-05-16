#!/usr/bin/env bash
# train_command.sh — 실험 C 학습 명령 (시도 3 의 변형, 변수=dataset 만)
#
# 사전:
#   - leftarm_v2_gopcheck dataset 사본 + file-000.mp4 (top+wrist) GOP=2 재인코딩 완료
#   - 다른 AI 의 학습이 종료된 상태 (ps -ef | grep lerobot-train 빈 결과)
#   - cleanup 강화 (실험 A 와 동일 baseline — 변수 분리)
#
# 5분 후 자동 종료 (timeout 300). wandb 의 system/memory 와 step time 으로 누수율 측정.

set -euo pipefail

DATASET="${1:-${HOME}/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_gopcheck}"

if [[ ! -d "$DATASET" ]]; then
    echo "ERROR: dataset 없음: $DATASET" >&2
    echo "  먼저 reencode_file_000.sh 실행" >&2
    exit 1
fi

# 다른 학습 진행 중 확인
if pgrep -f lerobot-train > /dev/null; then
    echo "⚠️ lerobot-train 프로세스가 실행 중입니다. 종료 후 재시도." >&2
    pgrep -af lerobot-train
    exit 1
fi

source "${HOME}/smolvla/dgx/.arm_finetune/bin/activate"

TS=$(date +%Y-%m-%d_%H-%M-%S)
RUN="leftarm_v2_exp_c_gop_${TS}"
OUT="${HOME}/smolvla/dgx/outputs/${RUN}"

echo "[exp_c] run name : $RUN"
echo "[exp_c] dataset  : $DATASET"
echo "[exp_c] output   : $OUT"
echo "[exp_c] episodes : [0..9] (file-000.mp4 만 — GOP=2 재인코딩됨)"
echo "[exp_c] 5분 후 자동 종료 (timeout 300)"
echo

# 메모리 모니터링 백그라운드 시작 (5초 간격, 5분간 60 sample)
MONITOR_LOG="/tmp/exp_c_memory.log"
echo "[exp_c] memory monitor → $MONITOR_LOG"
(
    for i in $(seq 1 60); do
        TS_NOW=$(date +%H:%M:%S)
        MEM=$(free -h | awk '/^메모리:|^Mem:/ {print $7}')
        echo "[$TS_NOW] MemAvailable=$MEM (step ~$((i*5))s)" >> "$MONITOR_LOG"
        sleep 5
    done
) &
MON_PID=$!

trap "kill $MON_PID 2>/dev/null || true" EXIT

# 학습 실행 (5분 timeout, OOM 또는 step 완주 X)
timeout 300 lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --policy.device=cuda \
    --policy.push_to_hub=false \
    --dataset.repo_id=BaboGaeguri/leftarm_v2 \
    --dataset.root="$DATASET" \
    "--dataset.episodes=[0,1,2,3,4,5,6,7,8,9]" \
    --dataset.video_backend=pyav \
    --dataset.return_uint8=true \
    --batch_size=16 --steps=20000 \
    --num_workers=2 --prefetch_factor=1 --persistent_workers=false \
    --save_freq=1000 --log_freq=50 \
    --output_dir="$OUT" --job_name="$RUN" \
    "--rename_map={\"observation.images.top\":\"observation.images.camera1\", \"observation.images.wrist\":\"observation.images.camera2\"}" \
    --wandb.enable=true \
    --wandb.project=leftarm_v2 \
    --wandb.entity=babogaeguri-hanyang-university \
    --peft.method_type=LORA \
    --peft.target_modules=all-linear \
    --peft.r=16 \
    || echo "[exp_c] 학습 종료 (timeout 또는 OOM)"

echo
echo "===== 결과 ====="
echo "[exp_c] 메모리 모니터 로그:"
cat "$MONITOR_LOG"
echo
echo "[exp_c] free -h 최종:"
free -h | head -3
echo
echo "[exp_c] wandb run 확인:"
ls -lat "$OUT/wandb/" 2>/dev/null | head -3
