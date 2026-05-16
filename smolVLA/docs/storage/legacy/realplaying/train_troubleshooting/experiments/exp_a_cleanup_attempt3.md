# 실험 A — 환경 cleanup 강화 + 시도 3

> 목적: cleanup 강화 단일 변수로 OOM 해소 가능 여부 검증. researcher 보고서 §5 1단계.

---

## 배경

시도 1 (2026-05-15 16:55) 과 시도 2 (2026-05-15 18:13) 에서 두 번 연속 system OOM (global_oom, CONSTRAINT_NONE) 이 발생했다.

dmesg 에서 VSCode server (`task=code`) 가 OOM-killer 에 의해 2회 연속 kill 된 것이 직접 증거로 확인됐다. researcher 보고서 §1 의 분석에 따르면 VSCode server + Claude Code agent + Firefox 가 합산 30~60 GB 를 점유할 수 있으며, 이것이 학습 프로세스의 가용 메모리를 잠식해 OOM zone 도달 시간을 단축하는 가속 요인이라는 가설이 성립한다.

시도 2 에서 `num_workers` 8 → 2, `prefetch_factor` 2 → 1 로 DataLoader 풋프린트를 1/8 로 줄였음에도 steady-state 누수율이 30% 밖에 감소하지 않아 (1,805 → 1,254 MB/min), 시간 비례 누수 메커니즘의 주범이 worker 수 자체보다 다른 요인 (pyav 자체 leak 또는 동시 점유) 임이 시사된다.

본 실험은 **cleanup 강화 외 다른 변수를 무변경**으로 유지해 동시 점유가 OOM 의 결정타인지 단일 변수로 검증한다. v1 (40ep) 이 동일 workers 셋업에서 완주한 반면 v2 가 OOM 난 차이를 cleanup 상태로 설명할 수 있는지 확인하는 것이 핵심이다.

---

## 변수 분리

| 변수 | 시도 2 | 시도 3 (본 실험) | 변경 이유 |
|---|---|---|---|
| `num_workers` | 2 | **2 (동일)** | 변경 없음 |
| `prefetch_factor` | 1 | **1 (동일)** | 변경 없음 |
| `batch_size` | 16 | **16 (동일)** | 변경 없음 |
| `train_config.yaml` | 그대로 | **무변경** | 단일 변수 분리 필수 |
| 학습 명령 | `python run_train.py train --pass 2a` | **동일** | 변경 없음 |
| **cleanup 강화** | 미확인 (기록 부재) | **VSCode+Claude+Firefox 완전 종료 + MemAvailable 100 GB+ 확인** | 단일 실험 변수 |

**본 실험의 유일한 변수**: cleanup 강화 (동시 점유 프로세스 완전 종료 + 메모리 여유 확인).

---

## 사전 조건 체크리스트

학습 시작 전 아래 항목을 순서대로 확인:

- [ ] DGX 에 접속되어 있음 (SSH 또는 직접 콘솔)
- [ ] 현재 실행 중인 학습 프로세스 없음 확인:
  ```
  ps aux | grep -E 'lerobot|run_train' | grep -v grep
  ```
- [ ] 디스크 여유 충분 확인 (출력 저장):
  ```
  df -h ~/smolvla
  ```
- [ ] venv 활성화 확인:
  ```
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  which lerobot-train   # 경로 출력되면 OK
  ```

---

## 실행 순서

### 1단계 — 작업 디렉터리 이동

```bash
cd ~/smolvla/dgx/finetune/leftarm_v2/
```

### 2단계 — 실행 권한 부여 (최초 1회)

```bash
chmod +x experiments/cleanup_helper.sh
```

### 3단계 — cleanup_helper.sh 실행

```bash
bash experiments/cleanup_helper.sh
```

예상 출력:
```
[cleanup_helper] ===== DGX 학습 전 환경 cleanup 시작 =====
[cleanup_helper] (a) VSCode server (code) 종료...
[cleanup_helper] (b) Claude Code CLI (claude) 종료...
[cleanup_helper] (c) Firefox 종료...
[cleanup_helper] (d) 3초 대기 후 잔존 프로세스 확인...
[cleanup_helper] (d) 잔존 프로세스 없음 — 정상 종료 확인.
[cleanup_helper] (e) sync 호출 (버퍼 플러시)...
[cleanup_helper] (f) 현재 메모리 현황 (free -h):
              total        used        free      shared  buff/cache   available
Mem:          125Gi        xxGi        xxGi       ...        xxGi       1xxGi   ← 100 GB+ 확인
[cleanup_helper] (g) MemAvailable >= 100 GB 검증...
[cleanup_helper]     MemAvailable = 1xx.x GB (...  kB)
[cleanup_helper]     OK — MemAvailable 1xx.x GB >= 100 GB.
[cleanup_helper] (h) page cache drop 안내:
    sudo 가 가능하면 다음 명령으로 page cache 도 비워주세요:
      sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    ...
[cleanup_helper] ===== cleanup 완료. 학습을 시작해도 됩니다. =====
```

MemAvailable 이 100 GB 미만이면 스크립트가 종료 코드 1 로 실패하며 경고를 출력한다. 이 경우 4단계(선택)를 먼저 수행한다.

### 4단계 — (선택) sudo 가능 시 page cache drop

```bash
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
free -h   # MemAvailable 재확인
```

page cache drop 후 MemAvailable 이 100 GB 이상인지 다시 확인한다.

### 5단계 — 메모리 모니터링 터미널 (새 터미널에서)

새 터미널을 열어 메모리를 30초 간격으로 기록:

```bash
watch -n 30 'free -h | grep -E "Mem|Swap" | tee -a /tmp/exp_a_mem.log'
```

학습 종료 또는 30분 경과 시까지 이 터미널을 유지한다. `/tmp/exp_a_mem.log` 에 시계열 기록이 쌓인다.

### 6단계 — 학습 실행 (시도 2 와 완전 동일 명령)

```bash
python run_train.py train --pass 2a
```

출력 예:
```
[run_train] pass     : 2a
[run_train] dataset  : BaboGaeguri/leftarm_v2
[run_train] subset   : 100 ep (index 0~99)
[run_train] base ckpt: lerobot/smolvla_base
[run_train] method   : lora (r=16, all-linear)
[run_train] steps    : 20000 / batch 16 / save_freq 1000
[run_train] workers  : 2
...
[run_train] lerobot-train 실행...
```

실행 직후 wandb run URL 을 기록해둔다 (결과 기록 양식의 "wandb run URL" 항목).

### 7단계 — 30분 관찰 (또는 step 500 도달 시까지)

- 모니터링 터미널의 MemAvailable 변화를 주시한다.
- 30분 시점에 성공 판정 기준을 확인한다.
- 시도 1·2 는 약 20분 내에 MemAvailable 이 급락했으므로 30분 생존이 의미 있는 기준이다.

---

## 성공 판정 기준

30분 시점에 다음을 모두 충족하면 성공:

- [ ] MemAvailable > 70 GB (시도 1·2 는 30분 내 OOM zone 진입 — 70 GB 이상이면 누수율이 현저히 개선된 것). 90 GB+ 면 cleanup 이 누수 자체를 거의 멈춘 강한 신호 (researcher §5 기준).
- [ ] step 500 이상 도달
- [ ] dmesg 에 OOM 메시지 없음:
  ```bash
  dmesg | tail -50 | grep -i oom
  ```

---

## 실패 판정

다음 중 하나라도 해당하면 실패:

- OOM SIGKILL 발생 (학습 프로세스 강제 종료)
- 30분 시점 MemAvailable < 30 GB
- dmesg 에 `oom-kill` 또는 `Out of memory` 메시지 확인

---

## 결과 기록

학습 종료 (또는 30분 관찰 후) 아래 문서에 결과를 기입:

```
dgx/docs/finetune/leftarm_v2/training_log.md
```

"시도 3 (실험 A — cleanup 강화, 2026-05-15)" 섹션의 각 항목에 실측값을 기입한다.

| 기록 항목 | 확인 명령 |
|---|---|
| MemAvailable peak/min | `/tmp/exp_a_mem.log` 또는 `free -h` 출력 |
| 도달 step | wandb 또는 콘솔 출력 |
| step_time 평균 | wandb `train/update_s` |
| dmesg OOM 메시지 | `dmesg | tail -50 | grep -i oom` |

---

## 다음 단계

### 성공한 경우

cleanup 강화가 OOM 의 결정타임이 확인됐다. `pyav` 누수는 여전히 존재하나 동시 점유 제거로 가용 메모리가 충분히 확보됨. 이 경우:

- 실험 종료. TODO-1b (실험 B) 폐기.
- spec 사실상 완료 상태 → 메인에게 `/verify-result` 입력 (학습 계속 진행 여부는 사용자 판단).

### 실패한 경우

cleanup 이 OOM 의 결정타가 아님. pyav 자체 누수 또는 다른 메커니즘이 주범임을 시사. 이 경우:

- TODO-1b 진입 (실험 B — `num_workers=0` 단일 프로세스 가설 확정 실험).
- researcher 보고서 §5 2단계로 진행.
