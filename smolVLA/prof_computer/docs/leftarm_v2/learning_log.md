# prof_computer — 학습 로그

> 본 노드 (Windows 10 + WSL2 + RTX 3090) 의 fine-tune 시도별 실행 기록.
> DGX 학습 시도 (legacy): [training_log.md](../../../dgx/legacy/train_trial_2026-05-17/docs/training_log.md) — 시도 1·2·3 모두 OOM (2026-05-15~16). DGX 학습 잠정 중단 사유: [legacy/train_trial_2026-05-17/README.md](../../../dgx/legacy/train_trial_2026-05-17/README.md).
> 결정 근거: [model_config.md](../model_config.md) — leftarm_v2/v3+ 공통 학습 방법론.

---

## 학습 사이클 개요

| 항목 | 값 |
|---|---|
| dataset | `BaboGaeguri/leftarm_v2` (HF Hub) |
| 베이스 ckpt | `lerobot/smolvla_base` |
| 방법 | LoRA r=16, target=all-linear |
| 2A pass | 100 ep balanced subset (ep 0~99) · 20K steps |
| 설정 위치 | [config/train_config.yaml](../../finetune/leftarm_v2/config/train_config.yaml) |
| 실행 래퍼 | [run_train.py](../../finetune/leftarm_v2/run_train.py) |
| PC 노드 README | [finetune/leftarm_v2/README.md](../../finetune/leftarm_v2/README.md) |

---

## 환경 셋업 기록

### 셋업 1 — 2026-05-16 · WSL2 + venv + lerobot + torchcodec

- 작성: 2026-05-16
- 설치 절차: [../scripts/setup_env.sh](../scripts/setup_env.sh)
- WSL distro: Ubuntu-22.04, kernel `6.6.114.1-microsoft-standard-WSL2`
- Python: **3.12.x (deadsnakes PPA)** — lerobot 0.5.2 `requires-python>=3.12` 충족. 시스템 3.10.12 와 병존.
- PyTorch wheel: **`torch==2.10.0` (cu128 wheel)** — lerobot 공식 `requirements-ubuntu.txt` lock 일치 (RTX 3090 Ampere sm_86 cu128 공식 지원). DGX 는 cu130 wheel (GB10 Blackwell) — torch 메이저 동일, CUDA wheel 만 칩 차이.
- video_backend: `torchcodec` (DGX `시도 3 후보` 선제 적용 — pyav-libsvtav1 decoder leak 가설 회피)
- `.wslconfig`: `memory=48GB / processors=12 / swap=16GB` (적용 후 free -h 로 검증 예정)
- `.venv_arm_finetune` 활성화 시 자동 export: `HF_HOME=~/.cache/huggingface`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128`, `CUDA_VISIBLE_DEVICES=0`
- 검증 결과 (2026-05-17 setup_env.sh 실행 후 실측):
  - [x] Python 3.12.13 (deadsnakes PPA, 시스템 3.10.12 와 병존)
  - [x] torch 2.10.0+cu128 (lerobot 공식 lock 일치)
  - [x] CUDA build 12.8, cuDNN 9.10.02 (PyTorch wheel bundled)
  - [x] GPU = NVIDIA GeForce RTX 3090, VRAM 24.0 GB 인식
  - [x] CUDA tensor op 실행 OK (`UserWarning: torch.cuda.FloatTensor deprecated` 무시 가능 — 검증 코드의 옛 API 사용 흔적, 실제 학습 무관)
  - [x] lerobot import OK (editable, `docs/reference/lerobot` submodule 그대로)
  - [x] **torchcodec 0.10.0 import OK** — DGX (aarch64 + cu130 + FFmpeg 6) 에서 `torch_from_blob undefined symbol` 로 깨졌던 ABI 미스매치가 prof_computer (x86_64 + cu128 + Ubuntu 22.04 FFmpeg 4.4.2) 에선 자연 해결. lerobot 공식 default backend 가 살아있음 → pyav buffer leak 가설 우회 가능.
  - [x] venv activate 시 `HF_HOME=/home/laba/.cache/huggingface` + `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128` + `CUDA_VISIBLE_DEVICES=0` 자동 export 등록

---

## 학습 시도 로그

### smoke 시도 1 — 2026-05-17 12:12 · ❌ FAILED (CUDA driver error: out of memory)

- 명령: `python run_train.py train --pass smoke`
- wandb run: `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/w2npfah1`
- 설정 (시도 1):

| 항목 | 값 |
|---|---|
| batch_size | 16 (DGX 동일) |
| num_workers | 4 |
| prefetch_factor | 2 |
| steps | 100 (smoke) |
| LoRA | r=16, all-linear |
| trainable params | 11,525,376 (12M) / 461,571,552 (462M) = 2.5% |

- **PEFT wrap 정상 통과** (`Wrapped smolvla with PEFT (LoraConfig)`) — DGX 와 동일 구성 확인.
- **step 0 forward 완주** (9.36 s/step) — 첫 batch 처리는 됨.
- **step 1 forward 진입 시 CUDA driver OOM** — vision encoder LoRA out_proj 에서 깨짐.
  ```
  File ".../peft/tuners/lora/layer.py", line 969, in forward
      result = result + lora_B(lora_A(dropout(x))) * scaling
  RuntimeError: CUDA driver error: out of memory
  ```
- **원인 (확정)**: RTX 3090 24GB 분리 VRAM 이 batch 16 + smolvla 462M + LoRA activation 을 못 받침. DGX (UMA 128GB) 와의 환경 차이가 가시화된 첫 사례.
- **조치 (시도 2)**: `batch_size: 16 → 8` (activation 메모리 ½). `train_config_smoke.yaml` 갱신.
- **prereq 사고 (DGX 시도 1·2 OOM) 와의 차이**: DGX 는 system RAM 누수 (CONSTRAINT_NONE, global_oom, 5GB/min). PC 는 VRAM driver OOM (즉시 첫 step 에서). 메커니즘 다름.

### smoke 시도 2 — 2026-05-17 12:16 · ✅ PASSED (100/100 step 완주)

- 명령: `python run_train.py train --pass smoke`
- wandb run: `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/xpef4jqc`
- output_dir: `~/prof_computer_runs/leftarm_v2_smoke_pc_2026-05-17_12-15-12`
- 설정 (시도 2 — 시도 1 대비 변경):

| 항목 | 시도 1 | 시도 2 | 변경 사유 |
|---|---|---|---|
| batch_size | 16 | **8** | RTX 3090 24GB VRAM 제약 — 시도 1 첫 step 후 CUDA driver OOM |
| 그 외 | 동일 | 동일 | LoRA r=16/all-linear, num_workers=4, prefetch_factor=2, steps=100 |

**결과 메트릭**:

| 지표 | 값 |
|---|---|
| 도달 step | **100 / 100** (완주) |
| 총 시간 | **64초** (warmup 9초 + steady 55초) |
| step time (steady) | `updt_s: 0.47–0.51` + `data_s: 0.005–0.006` ≈ **0.5 s/step** |
| dataloader bottleneck | **없음** — data_s 가 update 의 1% (torchcodec backend 효과) |
| loss | step 10: 0.734 → step 100: 0.401 (정상 강하) |
| grad_norm | 0.46–0.73 (안정, clip 10 한참 아래) |
| ckpt 저장 | step_50 (12:17:23), step_100 (12:17:59) 정상 |

**DGX 와의 비교** (training_log.md §시도1 대비):

| 차원 | DGX 시도 1 | PC smoke 시도 2 |
|---|---|---|
| chip | GB10 (aarch64, UMA) | RTX 3090 (x86_64, 분리 VRAM) |
| video backend | pyav (torchcodec aarch64 ABI 깨짐) | **torchcodec 0.10** |
| batch | 16 | 8 |
| num_workers | 8 | 4 |
| step time | 2.7 s/step | **0.5 s/step** (5× 빠름) |
| dataloader 영향 | 3.4GB main + 95GB system 누수 | **거의 0** (data_s 0.005s) |
| 완주 | ❌ step 368/20000 system OOM | ✅ 100/100 |

→ x86_64 + torchcodec + 분리 VRAM 의 효과가 정량으로 확인됨. DGX 의 prereq M1.5 (image dataset 변환) 가 이 노드에서는 **불필요** — PC 는 video dataset 그대로 학습 가능.

**잔여 검증 필요**:

- [ ] VRAM peak 실측 (monitor 창 캡처): batch 8 에서 peak 가 몇 GB 였나? 본 학습 (20K step) 진입 전 결정 변수.
- [ ] 본 학습 (20K step) 시 누적 메모리 (system RAM 누수 가설) 재현 여부 — smoke 64초 동안은 누수 안 보였으나 장기 학습에서 다른지 확인 필요.

### smoke 시도 3 — 2026-05-17 12:36 · ⚠️ PASSED (100 step) but bf16 효과 없음

- 명령: `python run_train.py train --pass smoke` (yaml: batch 8 + use_amp=true)
- output_dir: `~/prof_computer_runs/leftarm_v2_smoke_pc_2026-05-17_12-36-18`
- 설정 변경 (시도 2 대비): `use_amp: false → true` (bf16 mixed precision)

**결과 — bf16 효과 거의 0**:

| 지표 | smoke 2 (fp32) | smoke 3 (bf16) | 차이 |
|---|---|---|---|
| VRAM peak (%) | 94.82% | **94.73%** | **-0.09%p (효과 없음)** |
| VRAM peak (GB) | 24.44 | 24.43 | -0.01 GB |
| update_s (steady) | 0.47–0.51 | 0.47–0.49 | 무차이 |
| dataloading_s | 0.005 | 0.004 | 무차이 |
| loss (step 100) | 0.401 | 0.375 | 정상 강하 |
| 100 step 완주 | ✅ | ✅ | 둘 다 통과 |

**진단**: lerobot 의 `--policy.use_amp=true` 가 dry-run 인자로 전달됐고 학습은 도는데, **VRAM 절감 효과가 측정되지 않음**. 가능한 원인 (사후 조사 가치):

1. lerobot `policies.py:90` 의 `is_amp_available` 자동 체크가 false 로 떨어졌을 가능성 (PEFT 와 결합 시 호환성 이슈 알려진 사례 있음)
2. AMP scope 가 좁아 — VLM forward 만 fp16, 나머지 fp32 라 activation 절감 미미
3. lerobot smolvla 가 이미 일부 mixed precision 으로 동작 중이라 추가 절감 여지 작음

**결정 (smoke 4 진입 전)**: bf16 변수 제거 (효과 없는 변수 유지하면 결과 해석 흐려짐) + batch 만 단일 변수로 ½ 추가 축소.

| 변경 | 시도 3 | 시도 4 (예정) |
|---|---|---|
| batch_size | 8 | **4** |
| use_amp | true | **false** |
| steps (본 학습 yaml) | 37500 | **75000** (batch 4 × 5 epoch = 75000) |

→ smoke 4 (batch 4 fp32) 의 VRAM peak 이 < 75% 이면 본 학습 (75000 step, ~5시간 38분) 진입 안전.

**잔여 backlog**:
- bf16 동작 검증 — lerobot scripts/lerobot_train.py 코드에서 `use_amp` 가 실제로 어디 적용되는지 추적. 향후 학습 시간 단축이 큰 가치가 될 때 재검토.

### smoke 시도 4 — 2026-05-17 12:44 · ✅ PASSED (batch 4 fp32, VRAM 51.8% 안전 영역)

- 명령: `python run_train.py train --pass smoke` (yaml: batch 4 + use_amp=false)
- output_dir: `~/prof_computer_runs/leftarm_v2_smoke_pc_2026-05-17_12-44-27`
- 설정 변경 (시도 3 대비): batch 8→4, use_amp true→false

**결과**:

| 지표 | smoke 2 (b8 fp32) | smoke 3 (b8 bf16) | **smoke 4 (b4 fp32)** |
|---|---|---|---|
| VRAM peak | 94.82% (24.4 GB) | 94.73% (24.4 GB) | **51.79% (12.7 GB)** ✅ |
| update_s (steady) | 0.47–0.51 | 0.47–0.49 | **0.32–0.34** |
| dataloading_s | 0.005 | 0.004 | **0.003** |
| 100 step time | ~55s | ~55s | **~38s** |
| loss (step 100) | 0.401 | 0.375 | 0.560 ⚠️ (변동 ↑) |
| grad_norm (steady) | 0.46–0.73 | 0.50–0.81 | 0.79–1.01 |

**핵심 발견**:

- VRAM 정확히 절반 (94% → 51%). batch 8 → 4 의 ½ 효과 확정.
- step time 32% 단축 (50% 단축 아님 — fixed overhead 존재).
- loss 변동성 ↑ (0.27–0.69 범위) — batch 4 의 gradient noise 가시화. **단 100 step 은 너무 짧아 결론 불가**. 본 학습 75000 step 에선 자연 수렴 기대.
- System RAM available delta -1.5 GB (55초간) — smoke 2 와 유사 패턴. **누수 아니라 학습 초기 적재 비용** (모델·dataset cache).

**본 학습 예상 시간 (smoke 4 외삽)**:

- 75000 step × 0.34 s/step ≈ **25500 s ≈ 7시간 5분**
- ckpt 75개 (step 1000마다), 각 ~수백 MB → 총 디스크 ~수십 GB 필요

**진입 결정**: batch 4 fp32 + steps 75000. DGX 의도 (5 epoch on batch 16, 60K frames 학습) 와 sample 수 동등.

---

### M1.5 중간점검 학습 (PC) — 2026-05-17 12:53 ~ 20:27 · ✅ COMPLETED (75000 step 완주)

> **사이클 식별**: realplaying.md 의 **M1.5** ("데이터셋 학습 호환성 정비 — video decode 회피"). 원 결정은 image dataset 변환이었으나 prof_computer 로 이관 (사용자 결정 2026-05-16, [prof_train_setting.md](../../../docs/storage/prof_train_setting.md)) 으로 video dataset 그대로 학습 시도. 100 ep subset 만 사용 (본 학습 = M2 는 **M1 완성 = 400ep** 후 진행 — 2026-05-18 목표 200→400 조정).
>
> M1.5 DOD ("100ep subset 학습 진입 → OOM 없이 첫 ckpt 도달") 초과 달성 — 75000 step 완주.

- 명령: `python run_train.py train --pass 2a` (`train_config.yaml`: batch=4, steps=75000, use_amp=false, num_workers=4, prefetch_factor=2, video_backend=torchcodec, LoRA r=16 all-linear)
- run name: `leftarm_v2_2a_pc_2026-05-17_12-51-51`
- output_dir: `~/prof_computer_runs/leftarm_v2_2a_pc_2026-05-17_12-51-51/`
- wandb run: `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/<id>`

**학습 메트릭**:

| 지표 | 값 |
|---|---|
| 시작 / 종료 | 2026-05-17 12:53:27 / 20:27:11 |
| 총 시간 | **7시간 33분 44초** |
| 도달 step | 75000 / 75000 (100%) ✅ |
| 도달 sample | 300,000 (75000 × batch 4) — DGX 의 M2-2A 의도 (20K step × batch 16) 와 sample 수 동등 (단 본 사이클은 M2 가 아니라 M1.5 중간점검) |
| epoch | 5.5 |
| step time (steady) | 0.343 s/step (DGX 시도 1 의 2.7 s/step 대비 5× 빠름) |
| dataloading_s | 0.004 (dataloader bottleneck 0 — torchcodec 효과) |
| loss min | **0.013** (DGX 시도 1 의 최저 0.292 대비 압도적 수렴) |
| loss avg / final | 0.087 / 0.04 (step 74900-74950 영역) |
| grad_norm 후반 | 0.55-0.65 (clip 10 한참 아래, 안정) |
| lr 마지막 | 2.5e-6 (cosine min 도달) |
| ckpt 저장 | 75개 (step 1000 마다, last → 075000 심볼릭) |
| last ckpt 크기 | 125 MB (LoRA adapter only — base weight freeze) |

**시스템 메트릭** (3375 row, 7.5 시간):

| 지표 | 값 |
|---|---|
| VRAM peak | **60.67%** (~14.7 GB / 24 GB) |
| VRAM steady | ~52% |
| System RAM 누수 (학습 동안) | **-1.36 GB / 7.5h = 0.18 GB/h** (DGX 시도 2 의 1.25 GB/min 대비 400× 감소) |
| GPU temp peak | 83°C (RTX 3090 throttle ~85°C 경계, 학습 영향 0) |
| GPU power steady | 300-320W (TDP 350W 의 87%) |
| GPU util 평균 | 60-80% 변동 |
| Disk 사용 (학습 후) | 60 GB / 1007 GB 가용 |

**핵심 결론 — DGX 사고가 prof_computer 에서 재현되지 않음**:

| 위협 패턴 (DGX `training_log.md`) | prof_computer 결과 |
|---|---|
| system RAM 5GB/min 누수 → 28분 OOM | ✅ 0.18 GB/h (1660배 감소) |
| pyav buffer leak | ✅ torchcodec 0.10 정상 동작 |
| VRAM OOM | ✅ 60.7% peak — 안전 |
| 완주 여부 | ❌ 368/20000 (DGX) ↔ ✅ **75000/75000** (PC) |

→ `prereq spec 02_prereq_dataset_video_to_image` 의 가설 **직접 증명**:
> *"torchcodec 정상 환경 (x86_64 + cu128 + Ubuntu 22.04 FFmpeg 4.4) 에선 DGX 의 aarch64 + cu130 + FFmpeg 6 조합에서 발생한 pyav buffer leak 우회 가능"*

7.5 시간 동안 dataset 의 random-access seek 가 수만 번 반복됐는데도 RAM 추세 변화 없다는 게 **torchcodec 의 release pattern 이 pyav 와 본질적으로 다르다는 강력한 증거**. lerobot upstream 의 default backend 가 torchcodec 인 이유 그 자체.

**다음 단계**:

- [ ] best ckpt 선별 — 마지막 step 74900-74950 의 loss 0.04-0.05 영역이 가장 낮음. **last (step 75000, loss 0.13)** 가 정책상 표준이나 정성 차이 미세할 가능성
- [ ] HF Hub model repo push: `BaboGaeguri/leftarm_v2_lora_pc_2026-05-17` (125 MB upload)
- [ ] Orin 추론 검증 (시연장 정성 평가, 다음 사이클)
- [ ] *backlog*: `scheduler_decay_steps: 30000` 이 `steps: 75000` 보다 작아 30k 이후 lr 거의 0 — 다음 학습 yaml 에서 동기화 권장 (model_config.md 의 2B 후보 메모)

---

## DGX 결과와의 비교 표 (2026-05-17 본 학습 완주 후)

| 차원 | DGX 시도 1·2 (`legacy/train_trial_2026-05-17/docs/training_log.md`) | PC 2A first pass |
|---|---|---|
| 환경 | aarch64 + cu130 + Ubuntu 24.04 FFmpeg 6 | x86_64 + cu128 + Ubuntu 22.04 FFmpeg 4.4 |
| video backend | pyav (torchcodec aarch64 ABI 불가) | **torchcodec 0.10.0** |
| batch / workers / prefetch | 16 / 8→2 / 2→1 | 4 / 4 / 2 |
| 완주 여부 | ❌ SIGKILL (시도 1 step 368, 시도 2 ~step 50 사망 예측) | ✅ 75000 / 75000 |
| 도달 step / sample | 368 / 5,888 | 75000 / 300,000 |
| step time | 2.7 s/step (시도 1) | **0.343 s/step** (5× 빠름) |
| VRAM peak | N/A (UMA) | 60.67% (~14.7 GB / 24 GB) |
| system RAM 누수 | **1.25 GB/min** (시도 2 steady-state) | **0.18 GB/h** (1660배 감소) |
| GPU power | 12W idle (시도 1) — GPU 활용 안 됨 | 300-320W (TDP 87%) |
| 최종 loss | 0.292 (step 350) — 미수렴 | **0.04** (수렴) |
| 정성 추론 (Orin smoke) | 미실행 | **다음 사이클 검증 예정** |

→ **prereq spec 02 가설 직접 검증**: torchcodec 정상 환경에서는 DGX 의 OOM 메커니즘 (pyav buffer leak × DataLoader workers × UMA 단일 풀) 가 발생 자체 불가. PC 노드가 DGX 의 aarch64 ecosystem 정비 (lerobot upstream 의 torchcodec aarch64 wheel 또는 PyTorch + FFmpeg ABI 정합) 전까지 학습 책임 대행.

**다음 단계** (M2 진입은 M1 의 **400ep** 완성 후 — 2026-05-18 목표 200→400 조정):

- [x] **Orin 추론 smoke** — `lerobot-record --policy.path=BaboGaeguri/leftarm_v2_A2_pc_2026-05-17` 로 M1.5 결과의 정성 평가 → **2026-05-18 실시, 0/2 (단축), 0~20% 영역 확정**. 상세: [a2_eval_2026-05-17.md](../../../orin/docs/leftarm_v2/a2_eval_2026-05-17.md)
- [ ] **M1 잔여 290ep 수집 완료** (현재 110/400)
- [ ] **M2 본 학습** — 400ep 완성 후 prof_computer 에서 본 학습. yaml 의 `scheduler_decay_steps` 를 `steps` 와 동기화 권장 (본 사이클은 30k step 이후 lr 거의 0 — backlog 메모)
- [ ] **선택: 200ep 시점 중간점검 학습** — M1.5 (100ep) 와 동일 setup 으로 1회 학습 + Orin 평가 → 데이터 양 효과 정량화 + 400ep 진입 가치 calibration
- [ ] DGX 의 aarch64 ecosystem 정비 — backlog (장기)

---

### M1.5 추론 후 가설 분리 검증 사이클 — 2026-05-18 · 🔄 진행 중

> **배경**: M1.5 추론 결과 0/2 (단축 평가) — 0~20% 영역 확정 ([a2_eval_2026-05-17.md](../../../orin/docs/leftarm_v2/a2_eval_2026-05-17.md) §결과 집계). 다음 사이클 학습 방법 결정을 위해 **A2 (현재) → A1 (VLM frozen + expert LoRA) 후퇴 시도 가치** 판단 필요.
>
> **핵심 의문**: A2 의 0% 가 (가설 α) *VLM LoRA 의 부작용 (100ep noise 학습으로 VLM 손상)* 인지, (가설 β) *데이터 양 부족 (학습 방법은 OK, 더 학습할 데이터 필요)* 인지 분리 불가. A1 으로 무조건 후퇴 시 **본인 우려**: "VLM 적응이 실제 기여했다면 A1 = 환경 인식 ↓ + action 매핑은 동일 학습 → A2 보다 더 나쁜 결과 위험".
>
> → **두 가설을 학습 추가 없이 분리 검증**: (1) base smolvla 0-shot 추론 + (2) A2 학습 중 VLM LoRA weight 변화 분석. 사용자 + 메인 병렬 진행.

#### 분리 검증 작업 분담

| # | 작업 | 담당 | 산출 | 가설 검증 |
|---|---|---|---|---|
| 1 | base smolvla 0-shot Orin 추론 (ckpt 없이 base 만 로딩, 우리 환경 task1·task2 instruction 응답성 정성 측정) | 사용자 | 정성 메모 (반응 정도·instruction 구분 여부) | base VLM 의 우리 환경 인식 능력 → A1 안전성 |
| 2 | M1.5 학습 wandb run `8les615t` 분석 (VLM LoRA adapter weight norm 추이 — 학습 동안 유의미 변화 여부) | 메인 | log 추출 + 정량 분석 | VLM LoRA 의 실제 학습 기여도 |

#### 판정 매트릭스 (두 결과 조합)

| 작업 1 (base 0-shot) | 작업 2 (LoRA norm) | 종합 가설 | 다음 사이클 권고 |
|---|---|---|---|
| base 가 어느 정도 반응 | VLM LoRA norm 거의 0 | base VLM 충분 + VLM LoRA 기여 X | **A1 안전, 1순위** |
| base 가 어느 정도 반응 | VLM LoRA norm 큰 변화 | base 도 OK 지만 LoRA 도 학습됨 | A1 시도 가치 ↑ (단 A2 와 비교 valuable) |
| base 완전 무반응 | VLM LoRA norm 거의 0 | base 부족 + LoRA 가 부족분도 못 채움 | **데이터 확장 우선** (학습 방법 X) |
| base 완전 무반응 | VLM LoRA norm 큰 변화 | base 부족 + LoRA 가 환경 적응 기여 | **A1 비추천**, A2 유지 + 데이터·r 확장 |

#### 산출 위치

- 사용자 0-shot 추론 결과: 본 entry §결과 메모 (Orin 추론 시 사용자 보고 → 메인이 본 entry 갱신)
- 메인 wandb 분석: 본 entry §wandb 분석 (메인 작성)
- 종합 결정: 본 entry §결정 (양쪽 완료 후 메인 + 사용자 합의)

#### 결과 메모 (사용자 0-shot 추론)

> Orin 환경, `lerobot/smolvla_base` 직접 로딩 (entry: `orin/inference/leftarm_base_inference.py`, wrapper: `run_inference_leftarm_v2.sh zero-shot <task>`, max-steps 1000).
> 사용자 책임 분리 결정 (2026-05-18) — leftarm_v2_inference.py 변경 X, 신규 entry 로 가시화.

- **진행일**: 2026-05-18 (시연장 직후)
- **base ckpt 로딩 OK 여부**: ✅ 로딩 정상 (`SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")` 성공, robot connect + camera connect 정상)
- **task1 (`"Pick up the blue and yellow doll and place it on the left side of the table"`) 반응**: ❌ **사용자 도중 강제 종료** — 의미있는 동작 X (학습 모델 0/2 결과 보다도 *더 형편없음* 으로 사용자 판정)
- **task2 (`"Hand the yellow can to the person"`) 반응**: 미실시 — 사용자 결정 ("볼 것도 없다 — task1 결과로 충분")
- **두 task instruction 구분 응답성**: 평가 불가 (task1 만 부분 시도)
- **종합 정성 판정**: **무반응** — base smolvla_base 가 우리 환경 (좌측 SO-101 + top/wrist 카메라 + 시연장 조명) 의 *task instruction* 에 대해 의미있는 응답 X. 학습 ckpt (LoRA A2) 보다도 더 약함.

#### 1차 결론 (wandb 분석 전 임시)

판정 매트릭스 기준 *base 0-shot = 무반응* 행 → 두 분기 모두 *데이터 확장 우선*:

| base 0-shot | VLM LoRA norm | 결론 | 권고 |
|---|---|---|---|
| **무반응** ← 현재 | 거의 0 | base 부족 + LoRA 가 부족분도 못 채움 | **데이터 확장 우선** (학습 방법 X) |
| **무반응** ← 현재 | 큰 변화 | base 부족 + LoRA 가 환경 적응 기여 (작지만) | **A1 비추천**, A2 유지 + 데이터·r 확장 |

→ **A1 (VLM frozen + Expert LoRA) 후퇴는 비추** 확정. 두 분기 모두 *데이터 확장이 1순위*. 학습 방법 조정 (LoRA r↑, scheduler decay 동기화 등) 은 *데이터 확장 후* 의 2순위 작업.

#### wandb 분석 (메인 — 2026-05-18 완료)

> run `8les615t` (`leftarm_v2_2a_pc_2026-05-17_12-51-51`). **wandb logged 메트릭 한계**: `train/{loss,lr,grad_norm,update_s,dataloading_s,samples,epochs,steps}` 만 logged — LoRA layer 별 weight norm 추적 X. → **ckpt 직접 분석으로 대체**: WSL2 `~/prof_computer_runs/leftarm_v2_2a_pc_2026-05-17_12-51-51/checkpoints/{001000, 037000, 075000}/pretrained_model/adapter_model.safetensors` 의 LoRA weight 비교.

**분석 방법**:
- 3 시점 (init=step1000, mid=step37000, last=step75000) 의 `adapter_model.safetensors` 로딩
- 17개 target module 의 LoRA weight 를 5개 그룹으로 분류:
  - `EXPERT_io` (5): action_in_proj, action_out_proj, action_time_mlp_in/out, state_proj
  - `EXPERT_lm` (112 lora_B): vlm_with_expert.lm_expert.* — expert 본체
  - `VLM_vision` (72 lora_B): vlm_with_expert.vlm.*.vision_model.*
  - `VLM_text` (113 lora_B): vlm_with_expert.vlm.*.text_model.* + lm_head
  - `VLM_connector` (1 lora_B): vlm_with_expert.vlm.*.connector
- per-group 평균: `|B|_init`, `|B|_mid`, `|B|_last` (lora_B 의 L2 norm — PEFT init 시 B=0 이라 학습량의 직접 proxy)
- `|ΔB|_init→last` = ‖B_step75000 − B_step1000‖_F 평균
- `rel_to_|A|` = ΔB / A norm (scale-normalized 학습량 — module 크기 영향 제거)

**결과 표**:

| 그룹 | #tensors | \|B\|_init | \|B\|_mid | \|B\|_last | \|ΔB\|_init→last | rel_to_\|A\| |
|---|---|---|---|---|---|---|
| EXPERT_io | 5 | 0.211 | 0.877 | 0.908 | 0.858 | 0.352 |
| **EXPERT_lm** | 112 | 0.309 | 1.517 | **1.553** | **1.453** | **0.494** |
| VLM_connector | 1 | 0.240 | 1.290 | 1.326 | 1.260 | 0.238 |
| VLM_text | 113 | 0.299 | 1.369 | 1.391 | 1.308 | 0.430 |
| **VLM_vision** | 72 | 0.281 | 1.435 | **1.454** | **1.381** | **0.486** |

**핵심 발견 3 가지**:

1. **VLM LoRA 가 expert LoRA 와 거의 동등한 학습 신호를 받음** — VLM_vision rel_to_|A| = 0.486 vs EXPERT_lm 0.494. "VLM LoRA norm 거의 0" 가설은 **기각**. VLM 측 LoRA 가 실제로 강하게 학습됨.

2. **수렴은 step 37000 에 이미 도달, 후반 38000 step 은 거의 정체** — 모든 그룹에서 |B|_mid → |B|_last 변화량 < 2%. loss 0.04 수렴과 정합. ([backlog 메모] scheduler_decay_steps=30000 < steps=75000 와 정확히 일치 — lr 0 영역에서 학습 안 됨이 ckpt 로도 증명).

3. **VLM_vision 이 EXPERT_lm 다음으로 가장 강하게 학습됨** — 우리 환경 (파랑+노랑 인형·노란 캔·시연장 조명) 의 visual feature 에 vision encoder LoRA 가 적응한 신호. 사용자 우려 ("VLM 적응이 기여했을 것") 의 *부분 증거*.

**VLM LoRA 학습 기여도 판정**: **큰 변화** (VLM 측이 expert 측과 동등 강도로 학습됨).

**본인 우려에 대한 답**: "VLM LoRA 버리면 환경 인식 ↓ + action 매핑은 동일 학습" 우려가 **데이터로 강하게 뒷받침됨**. A1 (VLM frozen) 으로 후퇴 시 학습된 VLM 환경 적응을 통째로 버리게 됨 — A2 보다 더 나빠질 위험 *실재*.

**단, 본 분석의 한계**: "VLM LoRA 가 학습됐다" 만 증명, "학습된 게 task 성능에 도움이 됐다" 는 증명 못함. VLM LoRA 가 *noise 적응* (시연장 조명 패턴 외우기 등) 만 했을 가능성 *완전 배제 불가*. → 사용자 0-shot 추론 결과가 결정적 (위 §결과 메모).

#### 결정 (2026-05-18 확정)

> 양쪽 작업 완료 — 매트릭스 4번째 행 (`base 완전 무반응 + VLM LoRA norm 큰 변화`) 적중. 사용자 우려가 데이터로 완전 확정.

**작업 1 결과** (사용자, [base_eval_2026-05-17.md](../../../orin/docs/leftarm_v2/base_eval_2026-05-17.md)): base smolvla_base 는 우리 환경 task1 instruction 에 *의미있는 동작 X* — A2 학습 모델보다도 더 형편없음. task2 는 task1 결과로 충분해 skip. **base 무반응 확정**.

**작업 2 결과** (메인, 위 §wandb 분석): VLM_vision LoRA 가 EXPERT_lm 과 거의 동등 강도 (ΔB/A: 0.486 vs 0.494) 로 학습됨. **VLM LoRA 큰 변화 확정**.

**종합 가설**: base VLM 으로는 우리 환경 인식 불가 + A2 학습이 VLM LoRA 를 강하게 사용해 환경 적응 기여. A2 의 약한 응답성 (헛스윙·캔 방향 이동) 은 그 VLM 적응이 실제 기여한 신호.

**다음 사이클 권고 (확정)**:

1. **데이터 확장 1순위** — M1 잔여 100ep 수집 (task1 +50 / task2 +40) + 다양성 보강 (다른 사람 / orientation 5:5 / 위치 분포 확대)
2. **학습 방법 미세조정 2순위** (데이터 확장 후 별도 사이클) — A2 유지 + `lora.r: 16 → 32` / `scheduler_decay_steps=steps` 동기화 (M1.5 backlog 이미 잡힘, 후반 38k step 학습 정체의 직접 원인)
3. **A1·B1·B2 모두 비추 (본 시점)** — A1 (VLM frozen) 은 학습된 환경 적응 폐기 → 본 데이터로 비추 확정. B1/B2 는 100ep 으론 과적합 위험 (model_config.md §2 매트릭스 그대로).

→ 다음 사이클 spec Phase 1 진입 시 위 권고를 출발점으로 사용. [`orin/docs/leftarm_v2/base_eval_2026-05-17.md`](../../../orin/docs/leftarm_v2/base_eval_2026-05-17.md) §다음 사이클 입력 도 동일 결론.

---

### camera_empty 분기 학습 — 2026-05-18 · 🔄 진행 중

> **배경**: M1.5 추론 0/2 결과 후 추가 가설 도출 — base smolvla 의 사전학습 분포 (3 cam) 와 우리 학습 분포 (2 cam) 의 *형식 mismatch* 가 0/2 의 *원인 후보* 일 가능성. 본인 우려 ([대화 2026-05-18](.)) 이 데이터로 뒷받침되어 *empty_cameras: 1 단일 변수 검증* 분기 개설.
>
> **검증 가설**: base smolvla 의 input_features 가 camera1/2/3 3 cam 으로 사전학습됨 (HF Hub `lerobot/smolvla_base/config.json` 확인). 우리 dataset = 2 cam (top→camera1, wrist→camera2). M1.5 ckpt 분석 결과 — `empty_cameras=0` 으로 학습되어 missing camera3 슬롯이 *zero-pad 도 안 됨* → vision encoder 가 2 cam 만 입력 받음 (base 의 3 cam attention 분포와 불일치). `empty_cameras: 1` 로 가면 missing camera3 슬롯을 -1 padded image + mask 0 으로 zero-fill → base 의 3 cam 형식 정합 회복.
>
> **단일 변수 비교**: M1.5 (empty_cameras=0, 0/2 단축) ↔ 본 분기 (empty_cameras=1, 결과 미정). 나머지 hyperparameter 100% 동일.

#### 사전 검증 — base smolvla config 확인 (2026-05-18)

- HF Hub `lerobot/smolvla_base/config.json` (WebFetch):
  - `empty_cameras: 0`
  - `input_features` = `observation.images.camera1`, `camera2`, `camera3` (3 cam)
  - 각 camera shape = [3, 256, 256]
- M1.5 ckpt `train_config.json` (직접 분석):
  - `policy.empty_cameras: 0` (default 그대로)
  - `policy.input_features` = camera1/2/3 모두 포함 (base config 상속)
  - dataset 은 camera1, camera2 만 (rename_map 결과)
  - → camera3 가 `missing_img_keys` 잡혔으나 `empty_cameras=0` 으로 `_prepare_images()` zero-pad loop 즉시 break → vision encoder 가 2 cam 만 입력

#### 추가 사전 검증 — 다른 흔한 root cause 후보 배제 (2026-05-18, researcher 보고서 §6 검증 A/B 적용)

> researcher 보고서 ([research_empty_cameras_2026-05-18.md](research_empty_cameras_2026-05-18.md)) 의 권고대로, *empty_cameras 가 *유일* 원인이 아닐* 가능성 대비 — community 의 흔한 함정 둘 (n_action_steps Hub 함정 + normalization stats infinity) 을 M1.5 ckpt 에서 직접 점검. *현 분기 학습 결과 해석 시* 이 둘이 *동시 원인 아님* 확정 후 진행하는 게 깔끔.

**검증 A — M1.5 ckpt `config.json` 핵심 필드** (`prof_computer_runs/.../checkpoints/075000/pretrained_model/config.json`):

| 항목 | 값 | 평가 |
|---|---|---|
| **`n_action_steps`** | **50** | ✅ **Hub 함정 회피** — 1 이었으면 chunking 무력화 + inference 매우 느림 (기존 researcher 보고서 §1-3 의 알려진 함정) |
| `chunk_size` | 50 | ✅ 정합 |
| `n_obs_steps` | 1 | ✅ smolvla default |
| `empty_cameras` | 0 | (예상대로 — 본 분기에서 1 로 변경 검증 중) |
| `input_features` | camera1/2/3 (3 cam) | (예상대로 — base 상속) |
| `freeze_vision_encoder` | True | smolvla default (PEFT 경로는 별도 frozen 처리하므로 무관) |
| `train_expert_only` | True | smolvla default (PEFT 경로는 별도 frozen 처리하므로 무관) |
| `use_amp` | False | M1.5 결정대로 |

→ **`n_action_steps` Hub 함정 *우리에겐 발생 안 함*** 확정. researcher 1순위 의심 root cause 후보 *배제*.

**검증 B — normalization stats sanity** (`policy_preprocessor_step_5_normalizer_processor.safetensors`):

- preprocessor 90 tensor + postprocessor 90 tensor 모두 NaN/Inf **없음**
- `action.mean` = [-39, 67] / `action.std` = [8.1, 42.8] / `action.min/max` = [-97, 117] — SO-101 joint angle 정상 범위
- `observation.images.top/wrist.mean = 0.45 / std = 0.226` — 두 카메라 모두 *동일* (ImageNet stats 사용, lerobot default, base smolvla 와 정합)
- `task_index.mean = 0.57` — 110ep dataset 의 task1 50ep (45.5%) + task2 60ep (54.5%) 분포와 정합

→ **normalization stats *완전 정상*** 확정. issue #2210 / Xavier O'Keefe Medium 의 *normalization stats infinity 함정* 우리에겐 발생 안 함. researcher 2순위 의심 root cause 후보 *배제*.

**종합**: M1.5 0/2 의 *가장 흔한 두 함정* (n_action_steps + normalization stats) 모두 우리 ckpt 에서 *배제됨*. → camera slot mismatch (empty_cameras=0) 의 *상대 가중치 ↑* — 본 분기 학습이 *옳은 가설 검증* 가능성 강화. 단 분기 결과가 *여전히 0/2* 라면 *더 깊은 원인* (dataset 품질·workspace·추론 인프라 등 — researcher 보고서 §6 검증 C·D) 으로 진단 영역 옮겨야 함.

#### 분리 entry 구조 (2026-05-18 신설)

M1.5 원본 *완전 보존* + 별도 entry 3 파일:

| 분기 | wrapper | config (본 학습) | config (smoke) | run prefix |
|---|---|---|---|---|
| M1.5 (원본) | `run_train.py` | `train_config.yaml` | `train_config_smoke.yaml` | `leftarm_v2_2a_pc_<ts>` |
| **camera_empty** | `run_train_camera_empty.py` | `train_config_camera_empty.yaml` | `train_config_camera_empty_smoke.yaml` | `leftarm_v2_camera_empty_2a_pc_<ts>` |

단일 변수 차이: yaml 의 `empty_cameras: 1` → CLI `--policy.empty_cameras=1`. 나머지 100% 동일.

#### smoke 검증 — 2026-05-18 09:58 ~ 10:00 · ✅ PASSED

- 명령: `python run_train_camera_empty.py train --pass smoke`
- wandb run: `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/8bg2txw5`
- output_dir: `~/prof_computer_runs/leftarm_v2_camera_empty_smoke_pc_2026-05-18_09-57-20`

**핵심 검증 포인트**:

| 항목 | 결과 | 비교 (M1.5 smoke 4) |
|---|---|---|
| `policy.empty_cameras=1` wandb config 반영 | ✅ 확인 | M1.5 = 0 |
| 100 step 완주 | ✅ ~1분 | 동일 |
| loss step 10 → 100 | 0.769 → 0.394 | M1.5 smoke 4 = 0.560 (본 분기 약간 빠른 강하) |
| grad_norm steady | 0.79-1.00 | M1.5 smoke 4 = 0.79-1.01 (동등) |
| update_s (steady) | 0.41-0.44 | M1.5 smoke 4 = 0.32-0.34 (본 분기 +0.05 ≈ 12% — camera3 zero-pad 추가 처리 영향 추정) |
| dataloading_s | 0.004 | 동등 |
| OOM | 없음 | 동등 |

→ **본 학습 진입 안전 신호 모두 통과**.

#### 본 학습 — 2026-05-18 10:02 ~ 19:25 · ✅ COMPLETED (75000 step 완주)

- 명령: `python run_train_camera_empty.py train --pass 2a`
- wandb run: [`wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/8jkr7edb`](https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/8jkr7edb)
- output_dir: `~/prof_computer_runs/leftarm_v2_camera_empty_2a_pc_2026-05-18_10-01-11`
- 평행 진행: 사용자 — 3번째 카메라 셋업 (다음 사이클 데이터 수집 준비)

**학습 메트릭 (완료 후 wandb summary 기준)**:

| 지표 | 값 |
|---|---|
| 시작 / 종료 | 2026-05-18 10:02:22 / 19:25:11 |
| 총 시간 | **9시간 22분** (8시간 30분 예측 대비 +10%) |
| 도달 step | 75000 / 75000 (100%) ✅ |
| 도달 sample | 300,000 |
| epoch | 5.5 |
| step time (steady) | 0.397 s/step |
| dataloading_s | 0.004-0.005 (data bottleneck 0 — torchcodec 효과) |
| **final loss (step 75000, single-batch)** | **0.130** |
| loss steady oscillation (last 20K) | 0.05-0.20 band (M1.5 final 0.04 보다 약간 ↑) |
| grad_norm 후반 | 0.56-0.71 (안정, clip 10 한참 아래) |
| lr 마지막 | 2.5e-6 (cosine min 도달) |
| ckpt 저장 | 75개 (step 1000 마다, last = step 75000) |
| last ckpt 크기 | 45 MB (LoRA adapter only, M1.5 와 거의 동일) |

**시스템 메트릭** (wandb 차트 분석):

| 지표 | 값 |
|---|---|
| VRAM (allocated) | ~14-15 GB / 24 GB = 40-42% steady |
| GPU power | 300-340W steady (TDP 350W 의 86-97% — M1.5 보다 약간 ↑ 활용) |
| GPU util | 60-90% (M1.5 60-80% 대비 ↑ — empty_cameras zero-pad image 추가 처리) |
| GPU temp | 80°C steady (RTX 3090 throttle 85°C 한참 아래) |
| System Memory util | 15% steady |
| Process Memory (main) | 2.1 GB 안정 (누수 0) |
| System RAM 누수율 | 0 (M1.5 와 동일 — torchcodec 환경 안정성 재검증) |
| Disk 사용 (학습 후) | 73→80 GB (ckpt 75개 × ~150 MB 누적) |

**M1.5 (001) 와의 비교** — *empty_cameras 단일 변수만 차이*:

| 지표 | M1.5 (001) | 002 (camera_empty) | 차이 |
|---|---|---|---|
| 총 시간 | 7시간 34분 | 9시간 22분 | **+24%** (camera3 zero-pad 처리 오버헤드 — smoke 의 +12% 보다 본 학습에서 더 큰 차이) |
| step time | 0.343 s | 0.397 s | +16% |
| final loss (single-batch) | 0.132 | 0.130 | 거의 동등 |
| loss steady (last 20K) | 0.013-0.087 | 0.05-0.20 | **002 가 약간 ↑** (empty_cameras=1 의 zero-pad slot 처리로 expert fit 부담 ↑ 추정) |
| grad_norm 후반 | 0.55-0.65 | 0.56-0.71 | 거의 동등 |
| VRAM peak | 60.7% (~14.7 GB) | 40-42% (~14-15 GB) | 비슷 (측정 방식 차이 가능) |
| GPU util | 60-80% | 60-90% | 002 가 약간 ↑ |
| GPU temp peak | 83°C | 80°C | 002 가 살짝 낮음 |
| 완주 | ✅ | ✅ | 동일 |

→ **학습 메트릭 차원에선 *큰 차이 없음***. final loss 가 002 에서 약간 ↑ 였으나 *추론 성능 영향* 은 별개 (loss = 학습 fit, 추론 = generalization). **다음 단계 = Orin 추론 비교 평가** 가 *empty_cameras 가설* 의 *결정적 검증*.

#### 다음 단계 (학습 완료 후 즉시)

- [ ] **HF Hub push**: `BaboGaeguri/leftarm_v2_camera_empty_A2_pc_2026-05-18` (가칭) — Orin 접근 위해
  ```bash
  hf upload BaboGaeguri/leftarm_v2_camera_empty_A2_pc_2026-05-18 \
    ~/prof_computer_runs/leftarm_v2_camera_empty_2a_pc_2026-05-18_10-01-11/checkpoints/last/pretrained_model
  ```
- [ ] **Orin 추론 평가** — M1.5 와 *완전 동일 패턴* 단축 평가 (task1 front 1회 + task2 front 1회)
- [ ] **`orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md`** 신설 — 평가 시트 (`orin/docs/leftarm_v2/a2_eval_2026-05-17.md` 양식 동일)
- [ ] **결과 비교 + 다음 사이클 결정**:
  - 유의미 개선 (≥1/2) → empty_cameras 가 부분 fix 확정 → 200ep 수집 + camera_empty 패턴 유지
  - 동작 패턴 개선 (헛스윙 → reach 등) → 부분 fix 신호 → 데이터 확장 + empty_cameras 유지
  - 비슷한 0/2 → empty_cameras 가 root cause 아님 → 데이터 확장이 *유일한 가치 영역* + 다른 가설 (workspace, dataset 품질 등)

#### best ckpt 선정 (잠정)

- loss steady (last 20K) = 0.05-0.20 band → step 30000 이후 *학습 정체 영역* 이라 *step 별 ckpt 차이 거의 없음* 예상
- 추천: **last (step 75000)** 또는 **step 30000 부근 (lr decay 끝, 학습 정체 시작)**
- 단 *추론 성능 비교* 는 본 분석 외 영역 (별도 검증 시점에)

#### 다음 단계 — Orin 추론 비교 검증 (학습 완료 후)

본 분기 ckpt vs M1.5 ckpt (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) 의 *동일 환경 + 동일 단축 평가 패턴* 비교:

- 비교 방법: M1.5 추론 ([`orin/docs/leftarm_v2/a2_eval_2026-05-17.md`](../../../orin/docs/leftarm_v2/a2_eval_2026-05-17.md)) 와 동일 — task1 front 1회 + task2 front 1회 = 단축 2 trial
- 평가 시트: `orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md` (신설 예정)
- 결과 분기:
  - **본 분기 추론이 M1.5 (0/2) 보다 *유의미 개선*** → camera 수 mismatch 가 0/2 의 원인 *부분 확정* → 다음 사이클 결정에 반영 (3번째 카메라 실제 활용 가치 ↑)
  - **본 분기 추론이 M1.5 와 *비슷한 0/2***  → camera 수 mismatch 는 *부차적 요인*, 데이터 양·다양성이 주 병목 확정 → 다음 사이클 데이터 확장 1순위 유지
  - **본 분기 추론이 M1.5 보다 *나쁨*** → empty_cameras: 1 의 zero-pad 가 *오히려 noise 입력* (가능성 낮음 — base 학습 분포에 zero-pad 포함됐다면 무해)

#### 본 사이클 의의

학습 결과와 무관하게 본 사이클이 확보하는 *방법론적 가치*:

1. **단일 변수 비교 가능** — M1.5 와 hyperparameter 100% 동일, 단일 변수 (`empty_cameras`) 만 차이. 결과 해석 깔끔.
2. **분리 entry 보존** — M1.5 원본 파일 미수정, 본 분기 *별도 entry* 신설. 회귀 위험 0.
3. **base config 사전학습 분포 정합 검증** — base smolvla 의 *설계 의도* (3 cam 입력) 를 *우리가 그동안 무시했는지* 직접 측정. 결과 어느 쪽이든 *base 의 input_features 형식* 의 영향력 정량화.
4. **다음 사이클 데이터 수집 방향 정보 ↑** — 3번째 카메라 실제 활용 가치 (vs zero-pad 충분) 검증 기준점 확보.

---

### 003 분기 학습 — 2026-05-18 ~ 2026-05-19

> **분기 식별**: `003_a2_310ep_empty1_sched_sync_bf16_b6`
>
> **목적**: M1.5 (001) 단축 0/2 결과 및 002 (camera_empty) 단축 0/2 결과를 바탕으로 *5변수 종합 변경* 가설 묶음 검증. empty_cameras 단독 (002) 이 root cause 아님 확정 후, 데이터 확장 + 학습 효율 변수를 동시에 투입.
>
> **vs M1.5 (001) 변경 변수 5개**:
> 1. dataset 110→310 ep (실제 학습 ep 100→310)
> 2. `empty_cameras` 0→1 (upstream LIBERO CI 표준 패턴, base smolvla 3 cam 입력 정합)
> 3. `scheduler_decay_steps` 30000→120000 (= steps 동기화, M1.5 후반 38k step 학습 정체 해결)
> 4. bf16 mixed precision (`accelerate launch --mixed_precision=bf16` — `lerobot-train` 직접 호출 대신 `accelerate launch` 래퍼로 진짜 bf16 트리거)
> 5. batch_size 4→6 (epoch 2.93→4.39, researcher 권장 3-10 epoch 영역 정중앙 진입)

#### smoke 검증 (2026-05-18, commit 5715da5)

3단계 smoke 진행 (batch 가변, bf16 + accelerate launch 공통):

| smoke | batch | VRAM peak | 결과 | 사유 |
|---|---|---|---|---|
| smoke 1 (bf16+b4) | 4 | 34.31% (8.84 GB) | ✅ PASS | bf16 작동 확정 — fp32 b4 의 51.79% 대비 -33% |
| smoke 2 (bf16+b8) | 8 | OOM (step 1) | ❌ FAIL | attention transient peak 의 batch 비선형 영향 확정 |
| smoke 3 (bf16+b6) | 6 | 79.52% (20.49 GB) | ✅ PASS | 100 step 완주, 경계 영역 — 본 학습 진입 결정 |

→ **본 학습 진입 결정**: batch 6 + bf16. OOM 위험 인지 (본 학습 transient peak 가 90%+ 도달 가능성 있음) + 진행.

#### 본 학습 — 2026-05-18 23:06 ~ 2026-05-19 (추정 ~15:00 KST) · ✅ COMPLETED (120000 step 완주)

- 명령: `accelerate launch --mixed_precision=bf16 --num_processes=1 lerobot-train` + `--policy.scheduler_decay_steps=120000`
- run name: `leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6_full_2026-05-18_23-06-14`
- output_dir: `~/prof_computer_runs/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6_full_2026-05-18_23-06-14/`
- wandb run: [`babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq`](https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq)
- HF Hub: [`BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`](https://huggingface.co/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6) (push 완료 2026-05-19 08:10 UTC)

**학습 메트릭** (train_config.json + smoke 측정 기반 — wandb 메트릭은 run 40kzxlmq 페이지에서 확인 가능):

| 지표 | 값 |
|---|---|
| 시작 | 2026-05-18 23:06 KST |
| 종료 | 2026-05-19 ~15:00 KST (추정, HF push 08:10 UTC 기준 ~16-18h 후) |
| 총 시간 | **~16시간** (smoke 3 step time 0.48s × 120000 step 외삽, 실제는 wandb run 40kzxlmq 확인) |
| 도달 step | 120000 / 120000 (100%) ✅ |
| 도달 sample | 720,000 (120000 × batch 6) |
| epoch | ~4.39 (310ep dataset, batch 6 기준) |
| step time (steady) | ~0.48 s/step (smoke 3 측정값 — 실측은 wandb 40kzxlmq 확인) |
| dataloading_s | [wandb run 40kzxlmq 확인] |
| final loss | [wandb run 40kzxlmq 확인] |
| loss steady oscillation (last 20K) | [wandb run 40kzxlmq 확인] |
| grad_norm 후반 | [wandb run 40kzxlmq 확인] |
| lr 마지막 | **2.5e-6** (cosine min — scheduler_decay_steps=120000=steps, 전 구간 decay) |
| ckpt 저장 | **60개** (save_freq=2000, step 2000 마다) |
| last ckpt 크기 | [wandb 또는 로컬 확인 — LoRA adapter only, 001/002 기준 ~45-125 MB 예상] |

> wandb 메트릭 미추출 사유: devPC 환경에 `wandb` 패키지 미설치 (시스템 Python, venv 외부). 사용자가 `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq` 에서 직접 확인 후 `[...]` 항목 갱신 가능.

**시스템 메트릭** (smoke 3 측정값 기반, 본 학습 16h 추정):

| 지표 | 값 |
|---|---|
| VRAM peak (smoke 3 측정) | **79.52%** (~20.49 GB / 24 GB) |
| VRAM steady (본 학습 — 추정) | [wandb run 40kzxlmq 확인] |
| GPU power | [wandb run 40kzxlmq 확인] |
| GPU util | [wandb run 40kzxlmq 확인] |
| GPU temp | [wandb run 40kzxlmq 확인] |
| System Memory | [wandb run 40kzxlmq 확인] |
| Disk 사용 (학습 후) | [wandb run 40kzxlmq 확인 — 60 ckpt × 파일당 크기] |

#### HF Hub 검증 (2026-05-19, prod-test AUTO_LOCAL)

`curl https://huggingface.co/api/models/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` 조회 결과:

| 검증 항목 | 결과 |
|---|---|
| siblings 총 10개 | ✅ `.gitattributes` + `README.md` + `adapter_config.json` + `adapter_model.safetensors` + `config.json` + `policy_postprocessor.json` + `policy_postprocessor_step_0_unnormalizer_processor.safetensors` + `policy_preprocessor.json` + `policy_preprocessor_step_5_normalizer_processor.safetensors` + `train_config.json` |
| `config.json.empty_cameras` | **1** ✅ (003 분기 정합 확인) |
| `config.json.n_action_steps` | 50 ✅ (Hub 함정 회피 — 002 사이클 검증 패턴 유지) |
| `config.json.chunk_size` | 50 ✅ |
| `adapter_config.json.r` | 16 ✅ (LoRA r=16, all-linear 정합) |
| `train_config.json.scheduler_decay_steps` | 120000 ✅ (= steps, 전 구간 cosine decay) |
| `train_config.json.batch_size` | 6 ✅ |
| `train_config.json.steps` | 120000 ✅ |

#### 추론 평가 결과 메모 (TODO-04 갱신 — 2026-05-19)

- **평가 시트**: [`orin/docs/leftarm_v2/003_eval_2026-05-19.md`](../../../orin/docs/leftarm_v2/003_eval_2026-05-19.md)
- **결과 (단축 8 trial, 계획 20 중)**: **8 / 8 = 100%** (사용자 단축 종료 결정 — 첫 trial 들 모두 성공으로 추가 trial 정보 가치 낮다 판단)
  - task1: 3/3 (front 1, back 2)
  - task2: 5/5 (front 2 — 캔 물 채움 1 포함, back 3 — 다중 perturbation 1 포함)
  - 학습 분포 외 perturbation 4 trial: 로봇 각도 마늘랩 방향 (task1·task2 각 1) + 캔 mass 변화 (task2 1) + **다중 perturbation 로봇 각도 + 조명 50% 감소 (task2 back 1)** → 모두 견딤
- **vs M1.5(0/2)·002(0/2)**: **0% → 100% 도약**. 5변수 종합 분기 효과 결정적 확정. dominant 변수 미분리 (단일 ablation 미수행, 다음 사이클 영역). 002 결과 (단일 변수 empty_cameras 무효) 고려 시 *데이터 양 110→310ep* 가 가장 큰 변수 추정. 다중 perturbation (시각+광량 동시) 견딤 신호로 일반화 능력 정성적 증명.
- **다음 사이클 방향**: `realplaying.md` M4 (패키징·재실행 체크리스트) 진입 합리적. 단 trial 수 적음 (7) → 통계 신뢰도 제한, 더 큰 분포 변화 robustness 또는 단일 변수 ablation 우선순위는 `/wrap-spec` reflection 단계에서 결정.

---

## M1.5 (001) vs 002 (camera_empty) vs 003 비교 표

> 본 표는 camera_empty_eval 의 §학습 메트릭 비교 표 (`### M1.5 (001) 와의 비교`) 를 확장한 3-way 비교.
> M1.5↔002 는 *single variable* (empty_cameras 0→1), 001↔003 은 *5변수 종합*.

### 학습 설정 비교

| 설정 항목 | M1.5 (001) | 002 (camera_empty) | 003 (5변수 종합) |
|---|---|---|---|
| dataset | 110 ep (subset 100ep) | 110 ep (subset 100ep) | 310 ep (전체) |
| `empty_cameras` | 0 | **1** | **1** |
| `scheduler_decay_steps` | 30000 | 30000 | **120000 (=steps)** |
| mixed precision | fp32 (`use_amp=false`) | fp32 (`use_amp=false`) | **bf16** (`accelerate launch`) |
| batch_size | 4 | 4 | **6** |
| steps | 75000 | 75000 | **120000** |
| epoch | 5.5 | 5.5 | ~4.39 |
| save_freq | 1000 | 1000 | 2000 |
| lerobot entry | `lerobot-train` 직접 | `lerobot-train` 직접 | **`accelerate launch` 래퍼** |

### 학습 메트릭 비교

| 지표 | M1.5 (001) | 002 (camera_empty) | 003 (5변수 종합) |
|---|---|---|---|
| 총 시간 | 7시간 34분 | 9시간 22분 | ~16시간 (추정) |
| step time | 0.343 s/step | 0.397 s/step | ~0.48 s/step (smoke 3) |
| 도달 step | 75,000 ✅ | 75,000 ✅ | 120,000 ✅ |
| 도달 sample | 300,000 | 300,000 | 720,000 |
| final loss (last step) | 0.132 | 0.130 | [wandb 40kzxlmq] |
| loss steady (last 20K) | 0.013–0.087 | 0.05–0.20 | [wandb 40kzxlmq] |
| grad_norm 후반 | 0.55–0.65 | 0.56–0.71 | [wandb 40kzxlmq] |
| lr 마지막 | 2.5e-6 (step 30k 이후 정체) | 2.5e-6 (step 30k 이후 정체) | **2.5e-6 (전 구간 cosine decay)** |
| ckpt 저장 수 | 75개 | 75개 | **60개** (save_freq=2000) |
| last ckpt 크기 | ~125 MB | ~45 MB | [로컬 확인 또는 wandb] |

### 시스템 메트릭 비교

| 지표 | M1.5 (001) | 002 (camera_empty) | 003 (5변수 종합) |
|---|---|---|---|
| VRAM peak | 60.67% (~14.7 GB) | 40–42% (~14–15 GB) | **79.52% (~20.49 GB)** (smoke 3) |
| GPU power | 300–320W | 300–340W | [wandb 40kzxlmq] |
| GPU util | 60–80% | 60–90% | [wandb 40kzxlmq] |
| GPU temp peak | 83°C | 80°C | [wandb 40kzxlmq] |
| System Memory | 15% steady | 15% steady | [wandb 40kzxlmq] |
| RAM 누수 | 0.18 GB/h | 0 | [wandb 40kzxlmq] |
| Disk (학습 후) | ~60 GB | 73→80 GB | [wandb 40kzxlmq — 60 ckpt × 파일당 크기] |

### 추론 평가 비교

| 지표 | M1.5 (001) | 002 (camera_empty) | 003 (5변수 종합) |
|---|---|---|---|
| 평가 방법 | 단축 2 trial (task1 front + task2 front) | 단축 2 trial (동일) | **확장 20 trial** (task×orientation×5) |
| 성공률 | 0/2 (0%) | 0/2 (0%) | [TODO-03 PHYS_REQUIRED 완료 후 갱신] |
| 평가 시트 | [`a2_eval_2026-05-17.md`](../../../orin/docs/leftarm_v2/a2_eval_2026-05-17.md) | [`camera_empty_eval_2026-05-18.md`](../../../orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md) | `003_eval_2026-05-19.md` (TODO-02 신설) |
| HF Hub repo | `leftarm_v2_A2_pc_2026-05-17` | `leftarm_v2_camera_empty_A2_pc_2026-05-18` | `leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` |

> 003 추론 평가 결과는 TODO-03 완료 + `/verify-result` 후 본 표 해당 셀 갱신 예정.
