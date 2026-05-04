# TODO-T2 — Prod Test

> 작성: 2026-05-04 09:44 | prod-test-runner | cycle: 2 (cycle 1 FileExistsError → 빈 디렉터리 제거 후 재시작)

## Verdict

**`NEEDS_USER_VERIFICATION`**

학습 명령 백그라운드 시작 PASS (PID 462216). 60초 후 로그 정상 — cfg dump + step 50·100 loss 출력 확인. step 132 진행 중 (tqdm 예상 잔여 ~20분). 완주 (step 2000 + ckpt 2회 저장) 는 메인이 polling 후 최종 PASS 결정.

---

## 배포 대상

- dgx (코드 변경 없음 — 학습 명령 실행만. deploy 불요)

## 배포 결과

- 배포 불필요 (T2 는 학습 명령 실행 전용 todo — 코드 변경 없음)
- T1 산출물 (캐시 449MB, HF_HOME=~/smolvla/.hf_cache) 활용

---

## 자동 비대화형 검증 결과

### Cycle 1 — 실패 (FileExistsError, mkdir로 생성된 빈 디렉터리 충돌)

| 검증 | 결과 |
|---|---|
| nohup lerobot-train 실행 | PID 461031 반환 |
| 60초 후 PID 생존 확인 | 미존재 (즉시 종료) |
| 로그 확인 | FileExistsError: Output directory dgx/outputs/train/07_pilot_2k already exists and resume is False |
| 조치 | `rmdir ~/smolvla/dgx/outputs/train/07_pilot_2k` (빈 디렉터리 제거) |

- 원인: 학습 명령 전 `mkdir -p dgx/outputs/train/07_pilot_2k` 실행으로 빈 디렉터리 생성됨 → lerobot-train 이 기존 output_dir 존재 시 FileExistsError (--resume=false 기본값). 빈 디렉터리이므로 rmdir 으로 안전 제거.

### Cycle 2 — 정상 시작

| 검증 | 명령 | 결과 |
|---|---|---|
| nohup 백그라운드 실행 | `nohup lerobot-train ... > .../07_pilot_2k.log 2>&1 &` | PID 462216 반환 |
| PID 생존 (60초 후) | `pgrep -f 'lerobot-train.*07_pilot_2k'` | 462215/462216/462398/462399/462400 살아있음 |
| 로그 — cfg dump | `tail -30 .../07_pilot_2k.log` | INFO ot_train.py:207 cfg dump 정상 출력 |
| 로그 — 학습 설정 | output_dir·job_name·steps=2000·log_freq=50·save_freq=1000 | 전 항목 일치 |
| 로그 — Creating policy | Loading HuggingFaceTB/SmolVLM2-500M-Video-Instruct weights 489/489 | PASS |
| 로그 — Creating optimizer | INFO ot_train.py:316 Creating optimizer and scheduler | PASS |
| 로그 — LR auto-scale | warmup 1000→66, decay 30000→2000 (scale 0.067) | 정상 (steps=2000 < decay 30000) |
| 로그 — step 50 | loss:0.325 grdn:6.122 lr:4.0e-05 updt_s:0.592 data_s:0.033 | PASS |
| 로그 — step 100 | loss:0.313 grdn:6.003 lr:9.6e-05 updt_s:0.599 data_s:0.008 | PASS |
| 학습 진행 (step 132 확인) | tqdm 예상 잔여 ~20분 | 진행 중 |

### 학습 환경 preflight (사전 확인)

| 항목 | 결과 |
|---|---|
| RAM (가용) | 112 GiB 가용 (총 121 GiB) |
| 디스크 | 3.3 TB 가용 |
| ollama GPU 점유 | GPU Processes 에 ollama 없음 (45MiB nautilus만) |
| Walking RL | 미실행 확인 |
| HF 캐시 | T1 완료 — 449MB (`~/smolvla/.hf_cache/hub/datasets--lerobot--svla_so100_pickplace/`) |
| CUDA | GB10 cuda 12.1 (PyTorch 지원 범위 12.0 초과 UserWarning 있으나 학습 진행에 지장 없음 확인) |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 학습 명령 SSH 백그라운드 시작 PASS | SSH nohup 실행 + PID 생존 확인 | ✅ |
| 2. 60초 후 log 첫 출력 정상 (dataset/model 로딩 또는 첫 step 진입) | cfg dump + step 50·100 log 확인 | ✅ |
| 3. PID + log 파일 경로 보고 | PID 462216, log `/home/laba/smolvla/dgx/outputs/train/07_pilot_2k.log` | ✅ |
| 4. 메인이 polling 가능한 명령 안내 | 아래 polling 명령 시퀀스 참조 | ✅ |
| 5. step 2000 완주 + checkpoints/{001000,002000,last}/ 존재 | → 사용자 polling 후 확인 필요 | → verification_queue |

---

## 핵심 수치

- **PID**: 462216 (lerobot-train 메인 프로세스)
- **log 파일**: `/home/laba/smolvla/dgx/outputs/train/07_pilot_2k.log`
- **output_dir**: `/home/laba/smolvla/dgx/outputs/train/07_pilot_2k`
- **step 50 log**: loss=0.325, grdn=6.122, lr=4.0e-05
- **step 100 log**: loss=0.313, grdn=6.003, lr=9.6e-05
- **tqdm 예상 완주 시간**: step 132 기준 잔여 ~20분 (약 09:43 시작 → ~10:03 완주 예상)
- **실제 throughput**: ~1.5~2.0 step/s (초기 워밍업 후 안정)
- **예상 총 소요**: 약 18~22분 (D 분기 1-step 5.86s 기반 3.3시간 추정과 다름 — 1-step 은 워밍업 포함이어서 실 throughput 보다 훨씬 느림)

---

## Polling 명령 시퀀스 (메인이 완주 확인용)

```bash
# 1. 학습 진행 상태 확인 (tqdm 진행률 + 최신 loss)
ssh dgx "tail -5 /home/laba/smolvla/dgx/outputs/train/07_pilot_2k.log"

# 2. PID 생존 확인
ssh dgx "pgrep -f 'lerobot-train.*07_pilot_2k' && echo 'ALIVE' || echo 'DONE or FAIL'"

# 3. 완주 후 체크포인트 존재 확인
ssh dgx "ls /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/ 2>/dev/null || echo '체크포인트 미존재 (학습 중 또는 실패)'"

# 4. 체크포인트 상세 (완주 후)
ssh dgx "ls -lh /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/001000/pretrained_model/ 2>/dev/null"
ssh dgx "ls -lh /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/002000/pretrained_model/ 2>/dev/null"

# 5. 완주 확인 (last 심볼릭 링크)
ssh dgx "ls -la /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/last 2>/dev/null"
```

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

### 1. 학습 완주 + 체크포인트 2회 저장 확인 (SSH_AUTO)

- 환경 레벨: SSH_AUTO
- 조건: 학습 완주 후 (약 ~10:03 예상, tqdm 기준)
- 검증 명령:
  ```bash
  ssh dgx "ls /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/"
  # 기대: 001000  002000  last (3개 항목)
  ssh dgx "ls /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/002000/pretrained_model/"
  # 기대: model.safetensors (865MB 내외) 포함 7개 파일
  ```
- 기대 결과: `checkpoints/{001000,002000,last}/` 모두 존재 + log 마지막 줄 step:2000 loss 출력
- T3 의존: 체크포인트 확인 후 T3 (sync_ckpt_dgx_to_orin.sh) dispatch 가능

---

## CLAUDE.md 준수

- Category B 영역 (dgx/lerobot/) 변경: 없음 (학습 명령 실행만)
- Category D 명령 시도: 없음 (rmdir 은 허용 명령 — Category D 는 rm -rf 만 해당)
- 긴 실행 (>5분) 동의: Phase 1 결정 J 위임 (prod-test-runner 백그라운드 실행 OK, nohup + log) — 동의 완료
- 자율성 정책: SSH_AUTO (read-only 검증 + 학습 시작) — 사용자 위임 동의로 긴 실행 포함 허용
- Cycle 2 재시도 사유: FileExistsError (빈 디렉터리 충돌) — 학습 코드 문제 아님. 안전 조치 (rmdir) 후 정상 시작 확인.
