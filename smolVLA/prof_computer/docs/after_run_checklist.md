# 학습 종료 후 점검 명령 (after-run checklist)

> 학습 (`python run_train.py train --pass smoke|2a|2b`) 끝난 직후 사용. 결과 텍스트를 메인 Claude 에 전달해서 다음 사이클 결정에 활용.
>
> 사용 절차:
> 1. 학습 종료 확인 (`Training: 100%` 또는 `End of training`)
> 2. 본 파일의 §1·§2·§3 블록을 차례로 복사·실행
> 3. 각 블록의 출력 그대로 채팅에 붙여넣기

---

## 0) 사전 — venv 활성화 확인

```bash
# 이미 활성화 상태면 skip. 프롬프트 앞에 (.venv_arm_finetune) 있는지 확인
deactivate 2>/dev/null
source /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/.venv_arm_finetune/bin/activate
```

---

## 1) 최근 run 식별 + 산출물 목록

```bash
# 가장 최근 run 디렉터리 추적
LATEST=$(ls -td ~/prof_computer_runs/*/ | head -1)
echo "Latest run: $LATEST"
echo
echo "=== run 디렉터리 내용 ==="
ls -la "$LATEST"
echo
echo "=== checkpoint 디렉터리 ==="
ls -la "$LATEST/checkpoints/" 2>/dev/null || echo "(checkpoints/ 없음)"
echo
echo "=== metrics CSV (run_train.py 자동 export) ==="
ls -la "$LATEST"/metrics.*.csv 2>/dev/null || echo "(metrics.*.csv 없음 — export 실패 가능성)"
```

**기대 결과**:
- `LATEST` 가 가장 최근 timestamp 의 run
- `checkpoints/step_50/`, `step_100/` (smoke 의 경우) 또는 `step_1000/`, `step_2000/`, ... (본 학습)
- `metrics.scalar.csv`, `metrics.system.csv` 두 파일

---

## 2) 학습 메트릭 핵심 요약 (loss / step time)

```bash
LATEST=$(ls -td ~/prof_computer_runs/*/ | head -1)
SCALAR="$LATEST/metrics.scalar.csv"

if [ ! -f "$SCALAR" ]; then
    echo "ERROR: $SCALAR 없음"
else
    echo "=== scalar.csv columns ==="
    head -1 "$SCALAR" | tr ',' '\n' | nl
    echo
    echo "=== 처음 3 행 ==="
    head -4 "$SCALAR" | column -t -s,
    echo
    echo "=== 마지막 3 행 ==="
    tail -3 "$SCALAR" | column -t -s,
    echo
    echo "=== 총 row 수 ==="
    wc -l "$SCALAR"
fi
```

→ loss / grad_norm / step_time / lr 추이 확인. log_freq 마다 한 row.

---

## 3) GPU/system 메트릭 핵심 요약 (VRAM peak / 누수 추세)

```bash
LATEST=$(ls -td ~/prof_computer_runs/*/ | head -1)
SYSCSV="$LATEST/metrics.system.csv"

if [ ! -f "$SYSCSV" ]; then
    echo "ERROR: $SYSCSV 없음"
else
    echo "=== system.csv columns ==="
    head -1 "$SYSCSV" | tr ',' '\n' | nl
    echo
    echo "=== shape ==="
    wc -l "$SYSCSV"
    echo
    echo "=== VRAM peak (memoryAllocated %) — 큰 값 top 5 ==="
    # column 위치는 환경마다 다를 수 있어 awk 로 헤더 매칭
    awk -F',' '
    NR==1 {
        for (i=1; i<=NF; i++) if ($i ~ /memoryAllocated$/) col=i;
        if (!col) { print "  (memoryAllocated column 없음 — system.csv columns 표 직접 확인)"; exit }
        print "  (column #" col ")";
        next
    }
    $col != "" { print $col }
    ' "$SYSCSV" | sort -nr | head -5
    echo
    echo "=== System RAM available — 시간순 (누수 추세 확인) ==="
    # 시작 / 25% / 50% / 75% / 끝 — 단조 감소면 누수 의심
    awk -F',' '
    NR==1 {
        for (i=1; i<=NF; i++) if ($i ~ /availableMB/) col=i;
        if (!col) { print "  (availableMB column 없음)"; exit }
        print "  (column #" col ")";
        next
    }
    $col != "" { print NR-1, $col }
    ' "$SYSCSV" | awk 'BEGIN{n=0} {a[n++]=$2} END{
        if (n>0) {
            print "  row    1: " a[0];
            print "  row " int(n/4) ": " a[int(n/4)];
            print "  row " int(n/2) ": " a[int(n/2)];
            print "  row " int(3*n/4) ": " a[int(3*n/4)];
            print "  row " n ": " a[n-1];
            print "  delta (start - end): " a[0] - a[n-1] " MB"
        }
    }'
fi
```

→ VRAM peak 가 80% 이하면 안전 / 90% 이상이면 위험.
→ system RAM available 가 시간에 따라 *감소* 면 누수 의심. *수평선* 이면 안전.

---

## 4) (선택) wandb run URL 추적

```bash
LATEST=$(ls -td ~/prof_computer_runs/*/ | head -1)
RUN_NAME=$(basename "$LATEST")
echo "Local run name: $RUN_NAME"
echo "wandb URL: https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs"
echo "(위 페이지에서 $RUN_NAME 검색)"
```

브라우저로 차트 직접 보고 싶을 때만.

---

## 5) 학습 실패 시 — traceback 확보

학습 중 SIGKILL / CUDA OOM / 다른 에러가 나면 venv 의 tee 로그가 남아있어야 함:

```bash
# tee 명령으로 저장된 로그
ls -lat /tmp/smoke*.log /tmp/train*.log 2>/dev/null | head -5
echo
# 가장 최근 로그의 끝 100 줄
LATEST_LOG=$(ls -t /tmp/smoke*.log /tmp/train*.log 2>/dev/null | head -1)
echo "=== Last log: $LATEST_LOG ==="
tail -100 "$LATEST_LOG"
```

이 출력 그대로 채팅 전달 → 원인 분석 가능.

---

## 6) 메모 — 채팅에 붙일 때

§1, §2, §3 의 출력을 차례로 한 묶음으로 붙여주세요. §4·§5 는 필요 시만.

특히 §3 의 VRAM peak 와 RAM available delta 가 가장 중요한 신호:

- **smoke 시도 3 (bf16) 진단 기준**
  - VRAM peak < 75% → bf16 효과 확정. 본 학습 안전 진입 가능
  - VRAM peak 75–90% → 동작은 하나 본 학습 (4시간) 동안 spike 위험
  - VRAM peak > 90% → bf16 효과 약함 또는 의도대로 안 켜짐 (확인 필요)

- **본 학습 (20K~37500 step) 진단 기준**
  - 시간 진행에 따라 VRAM 단조 증가 → CUDA allocator fragmentation
  - System RAM available 단조 감소 (분당 100MB 이상) → DGX 시도 1·2 의 누수 패턴 재현
  - loss curve 가 발산 / NaN → bf16 수치 불안정 의심
