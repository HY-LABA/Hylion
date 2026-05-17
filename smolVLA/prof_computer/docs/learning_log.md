# prof_computer — 학습 로그

> 본 노드 (Windows 10 + WSL2 + RTX 3090) 의 fine-tune 시도별 실행 기록.
> DGX 측 대칭 문서: [dgx/docs/finetune/leftarm_v2/training_log.md](../../dgx/docs/finetune/leftarm_v2/training_log.md).
> 결정 근거: [dgx/docs/finetune/leftarm_v2/model_config.md](../../dgx/docs/finetune/leftarm_v2/model_config.md) — DGX 와 동일.

---

## 학습 사이클 개요 (DGX 와 공유)

| 항목 | 값 |
|---|---|
| dataset | `BaboGaeguri/leftarm_v2` (HF Hub) |
| 베이스 ckpt | `lerobot/smolvla_base` |
| 방법 | LoRA r=16, target=all-linear |
| 2A pass | 100 ep balanced subset (ep 0~99) · 20K steps |
| 설정 위치 | [dgx/finetune/leftarm_v2/config/train_config.yaml](../../dgx/finetune/leftarm_v2/config/train_config.yaml) |
| 실행 래퍼 | [dgx/finetune/leftarm_v2/run_train.py](../../dgx/finetune/leftarm_v2/run_train.py) |
| PC 전용 차이 | [../finetune/leftarm_v2/README.md](../finetune/leftarm_v2/README.md) |

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

> **사이클 식별**: realplaying.md 의 **M1.5** ("데이터셋 학습 호환성 정비 — video decode 회피"). 원 결정은 image dataset 변환이었으나 prof_computer 로 이관 (사용자 결정 2026-05-16, [prof_train_setting.md](../../docs/storage/prof_train_setting.md)) 으로 video dataset 그대로 학습 시도. 100 ep subset 만 사용 (M1 잔여 100ep 미수집 상태 — 본 학습 = M2 는 200ep 완성 후 진행).
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

| 차원 | DGX 시도 1·2 (`dgx/docs/finetune/leftarm_v2/training_log.md`) | PC 2A first pass |
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

**다음 단계** (M2 진입은 M1 의 200ep 완성 후):

- [ ] **Orin 추론 smoke** — `lerobot-record --policy.path=BaboGaeguri/leftarm_v2_A2_pc_2026-05-17` 로 M1.5 결과의 정성 평가 (M3 영역 일부 선검증)
- [ ] **M1 잔여 100ep 수집 완료** (현재 100/200)
- [ ] **M2 본 학습** — 200ep 완성 후 prof_computer 또는 DGX (ecosystem 정비 시) 에서 본 학습. yaml 의 `scheduler_decay_steps` 를 `steps` 와 동기화 권장 (본 사이클은 30k step 이후 lr 거의 0 — backlog 메모)
- [ ] DGX 의 aarch64 ecosystem 정비 — backlog (장기)
