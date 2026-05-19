# leftarm_v2 — 모델 구성 결정 (M2)

> **목적**: leftarm_v2 fine-tune 의 학습 방법·hyperparameter 결정·근거를 한 곳에 정리. `config/train_config.yaml` 의 값이 *왜* 그 값인지의 정본.
> **자매 문서**: [collection_log.md](../../dgx/docs/finetune/leftarm_v2/collection_log.md) (수집 차수 기록 — DGX 책임). 코덱 관련: [camera_and_codec.md](../../docs/storage/legacy/realplaying/train_troubleshooting/camera_and_codec.md) (legacy). 학습 설정: [`prof_computer/finetune/leftarm_v2/config/train_config.yaml`](../finetune/leftarm_v2/config/train_config.yaml).
> **작성**: 2026-05-15 (원본: `dgx/docs/finetune/leftarm_v2/model_config.md`). 이관: 2026-05-18 (DGX 학습 잠정 중단 → prof_computer 가 학습 책임. [legacy/train_trial_2026-05-17/README.md](../../dgx/legacy/train_trial_2026-05-17/README.md) 참조).

---

## 0) 개요 — 2 패스 (*2026-05-18 2B 목표 200→400ep 갱신*)

`realplaying.md` M2 / spec `02_leftarm_v2_finetune.md` 의 2 패스 구조:

| 패스 | dataset | hyperparameter 정책 | 목적 |
|---|---|---|---|
| **2A** | 100 ep balanced (subset P — task 1 [0..49] + task 2 [50..99]) | v1 검증값 그대로 + step 만 충분히 (사이클 검증에 충분한 수렴) | 사이클 검증 + 조기 성능 평가 |
| **2B** | **400 ep 전체 (M1 완성 후 — 2026-05-18 200→400 갱신)** | 2A 관찰 결과 + 400ep 데이터 반영해 정밀 튜닝 (사용자 주도) | M2 최종 산출 |

> **2B 목표 200→400ep 조정 사유 (2026-05-18)**: M1.5 추론 0/2 + researcher 보고서 ([leftarm_v2/research_empty_cameras_2026-05-18.md](leftarm_v2/research_empty_cameras_2026-05-18.md)) 의 데이터 양 추정 (300~500ep) 영역 진입 + camera mismatch 확신 영역 도달. 자세한 근거 [realplaying.md M1 변경 이력](../../realplaying.md).

---

## 1) SmolVLA 구조 (fine-tune 관점 짧게)

`lerobot/smolvla_base` 는 두 큰 part 로 구성:

- **VLM (vision-language model)** — 사전학습된 SmolLM + vision encoder. image 와 instruction 을 받아 representation 생성. ~450M params 추정.
- **Action expert** — VLM representation 을 받아 action chunk 를 예측. transformer 기반. ~150M params 추정.

fine-tune 시 어느 part 를 *얼마나* 학습시킬지가 핵심 결정.

---

## 2) 학습 방법 매트릭스 (2×3 = 6 옵션)

[VLM frozen / LoRA / Full FT] × [expert LoRA / Full FT] = 6 옵션. *2026-05-18 확장* — 원 4 옵션 (A1/A2/B1/B2) 의 대각 외 오프-대각 옵션 (C1/C2) 추가, *VLA 의미 보존 여부* 축 도입.

| 옵션 | VLM | expert | trainable (대략) | 메모리/시간 | VLA 의미 보존 | 100ep 적합 | **300ep 적합** | 비고 |
|---|---|---|---|---|---|---|---|---|
| A1 | frozen | LoRA | ~3M | 가장 작음 | ❌ (ACT 화) | ⚠️ paper 권장이나 본 환경 비추 | ⚠️ 본질 동일 — 데이터 ↑ 효과는 expert 단독 학습 안정성 ↑ 이나 *VLA 의미 폐기* 그대로 | base 0-shot 우리 환경 무반응 ([learning_log.md §M1.5 추론 후 가설 분리 검증](leftarm_v2/learning_log.md)) — frozen 시 환경 적응 0, expert 가 base VLM representation 위에 매핑만 학습 → 사실상 instruction-conditioned ACT. *2026-05-18 비추 확정* |
| **A2** | LoRA | LoRA | ~6–12M | 작음 | ✅ 부분 (LoRA r=16) | ✅ **v1 검증, 채택** | ✅ **권장 영역 안** ([best_practice §4-4](leftarm_v2/lerobot_smolvla_training_best_practice.md): VLA 고성능 300-1200ep, multi-task 100ep/task 권장 — 300ep = task 당 150ep 균형 가정 시 안정 영역) — **003 분기 채택** | M1.5 실측: VLM_vision LoRA 학습량 = EXPERT_lm 과 동등 (ΔB/A 0.486 vs 0.494) — VLM 적응 *실제 작동*. 100ep 결과 0% (단축) — *데이터 양 병목 가설*. 300ep 으로 데이터 확장 검증 진입 (003) |
| B1 | frozen | Full FT | ~150M | 중간 | ❌ (ACT 화) | ⚠️ 가능하나 무거움 | ⚠️ 과적합 위험 ↓ (300ep / 150M trainable 비율 개선) — 단 *VLA 의미 폐기* 본질 동일 + 여전히 lerobot 코드 우회 필요 | A1 의 expert 확장판. VLA 의미 폐기 + 100ep 과적합 위험. lerobot 표준 entry 로 *config 만으로는 불가* — PEFT wrap 이 base 전체 frozen + adapter 만 trainable 강제 ([pretrained.py:303](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L303)) |
| B2 | Full FT | Full FT | ~600M | 큼 | ✅ 최대 | ❌ 100ep 과적합 위험 + RTX 3090 24GB OOM | ⚠️ 과적합 위험 ↓ (300ep 영역 진입) — 단 RTX 3090 24GB OOM 그대로 (메모리는 step 단위). DGX 학습 재가능 시점만 의미 | 200ep + DGX 환경 후 영역 |
| **C1** | LoRA | Full FT | ~156M | 큼 (24GB 경계) | ⚠️ VLM 측 LoRA 만 살아 *부분 약화* | ⚠️ 코드 수정 필요 | ✅ **300ep 에서 시도 가치 ↑** — expert Full FT 의 과적합 위험 ↓ 영역 진입 + LoRA r=16 표현력 한계 돌파 가능. *코드 수정 + Phase 1 spec 영역 그대로* | "VLM 적응 유지 + expert capacity ↑". 본 시점 가장 가치 ↑ 후보였으나 lerobot 표준 entry 로 *config 만 불가* (B1 과 동일 이유) — 신규 학습 entry + lerobot 코드 우회 필요. *Phase 1 spec 영역* |
| C2 | Full FT | LoRA | ~456M | 큼 (24GB 경계) | ✅ VLM 최대 + expert 약 | ⚠️ 코드 수정 + VLM Full FT 100ep 과적합 위험 | ❌ 300ep 도 VLM 600M Full FT 엔 부족 (paper SO100 250ep × multitask 권장과 비교 — VLA 분야 600M Full FT 표준 데이터 양 1000ep+) | wandb 결과 (VLM_text rel_to_\|A\|=0.430 이미 충분 학습) 로 *추가 가치 의문*. 시간 비용 ↑. 본 시점 비추 |

> **VLA 의미 보존 축의 의미**: VLM frozen 분기 (A1/B1) 는 *smolVLA 라는 VLA framework 의 가치 (사전학습 multimodal representation + action 의 통합 학습)* 가 사라지고 사실상 *vision-conditioned action policy = ACT 류* 가 됨. 본 프로젝트가 smolVLA 를 base 로 선택한 이유 자체와 배치되는 분기.

> **LoRA 의 의미**: base weight 는 frozen, 각 linear layer 에 low-rank adapter (`A·B` matrix, rank=16) 만 trainable. `target_modules: all-linear` = 모델 내 *모든* linear layer 에 adapter 부착 (VLM linear + expert linear 둘 다). 따라서 **A2 는 expert 도 LoRA** (Full FT 가 아님).

### trade-off 분석

- **VLM frozen vs trainable** (*2026-05-18 갱신*): SmolVLA paper 표준 권장은 frozen — *일반화 능력 보존*. 그러나 본 환경에서:
  - base 0-shot 추론 무반응 (사용자 검증, [base_eval_2026-05-17.md](../../orin/docs/leftarm_v2/base_eval_2026-05-17.md)) → base VLM 만으로 우리 환경 인식 X
  - A2 학습 후 ckpt 분석 → VLM LoRA 가 실제 학습됨 (위 표 비고)
  - VLM frozen 분기는 *환경 적응 능력 0 + VLA 의미 폐기* → 본 환경 비추
  - → **VLM 측 학습 신호는 살리는 게 필수** (LoRA 또는 Full FT)
- **LoRA vs Full FT**: 100ep / 60k frames 는 Full FT 600M (B2) 을 안정 학습시키기엔 부족 (과적합) + RTX 3090 24GB OOM. LoRA 는 trainable params 1–2% 수준이라 100ep 도 안전. *중간 옵션 C1 (expert 만 Full FT)* 은 가치 ↑ 후보지만 lerobot 코드 우회 필요 — 별도 spec 영역.
- **300ep 영역 변화** (*2026-05-18 데이터 확장 결정 반영*): 데이터가 100ep → 310ep 으로 ~3배 확장되며 일부 옵션의 *과적합 위험* 영역이 변경. 근거: [best_practice §4-4](leftarm_v2/lerobot_smolvla_training_best_practice.md) — multi-task 권장 100ep/task (= 200ep) 초과 + VLA 일반 고성능 300-1200ep 영역 *진입점*. 영역 변화:
  - A2 (LoRA r=16) — 권장 영역 안 (003 채택)
  - B1 (expert Full FT) — 100ep 과적합 영역 → 300ep *완화 영역 진입*. 단 lerobot 코드 우회 + VLA 의미 폐기 본질 동일
  - C1 (LoRA VLM + expert Full FT) — *가장 큰 변화* — 100ep 에선 expert 150M 과적합 위험 영역이었으나 300ep 에선 *시도 가치 영역 진입*. 코드 우회 + Phase 1 spec 영역
  - B2 / C2 — 600M / 450M Full FT 영역은 *VLA 분야 표준 데이터 양 (1000ep+)* 기준 300ep 도 *여전히 부족* — 본 시점 비추
- **C1/C2 의 lerobot 표준 entry 불가 이유**: [pretrained.py:303](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L303) 의 `wrap_with_peft()` 가 `for p in self.parameters(): p.requires_grad_(False)` 로 *모든* base param 강제 frozen → LoRA adapter 만 trainable. expert base weight 도 같이 frozen 됨. expert 만 별도 unfreeze 하려면 *lerobot upstream 코드 우회 (Category A read-only)* 또는 신규 학습 entry 필요.

### 다음 사이클 결정 (2026-05-18 — 데이터 확장 진행 중 반영)

**100ep 시점 결정** (M1.5 사후):
- 현 100ep 그대로 의미 있는 자율 학습 분기 = A2 + r=32 (capacity ↑ 단일 변수). 큰 도약 어려움 — 근본 병목은 데이터 양.
- C1 진입은 별도 spec 필요 — 신규 학습 entry 작성 + PEFT manual wrap + expert param unfreeze + lr group 분리.
- 데이터 확장 (M1 잔여 100ep + 다양성) 이 1순위 — 학습 방법 조정은 그 다음.

**310ep 시점 결정** (2026-05-18 DGX 추가 수집 push 완료, 003 분기 진입):
- **A2 유지 + 310ep + empty=1 + scheduler 동기화 = 003 분기 채택** — 데이터 확장 효과 + upstream 정합 + 학습 효율 backlog 해결 *3 영역 동시 변경*. 003 결과 보고 다음 단계 결정.
- **C1 진입 시점 *재고*** — 300ep 영역에서 expert Full FT 의 과적합 위험 영역 완화. 003 결과가 *유의미 개선* 이면 C1 우선순위 ↑ (별도 spec 으로 진행). *비슷한 0/2* 면 C1 코드 우회 비용 대비 기대 효과 ↓ — 데이터 추가 (400ep) 또는 다른 hypothesis 우선.
- **데이터 추가 수집 (310→400ep)** 계속 진행 가치 — M1 목표 도달 + 권장 영역 깊이 진입.

---

## 3) 2A 결정 — A2 (LoRA all-linear)

### 결정 근거

1. **v1 검증 base** — leftarm_v1 가 A2 (`method: lora`, `target_modules: all-linear`, `r=16`) 로 학습 사이클을 돌렸음. step 부족 (500/5000) 이라 성능은 미검증이나 *학습 구조 자체는 검증됨*.
2. **변수 1개 조정** — 2A 는 v1 대비 **step 수만** 늘려 (500 → 20,000) 변수 1개 변경. 결과 해석이 깔끔 (v1 의 미수렴 = step 부족이었나 vs 구조 문제인가 분리 가능).
3. **VLM 부분 적응** — `all-linear` 로 VLM linear layer 에도 LoRA adapter → 우리 데이터에 약간 적응 (color grounding 강화 기대).
4. **메모리·시간 적당** — DGX 메모리 헤드룸 충분, 2A 학습이 시간 폭증하지 않아 2B 진행 시간 확보.

### 2B 진입 시 재검토 (현재 미확정)

- A2 의 결과가 약하면 → B1 (Full FT on expert, VLM frozen) 으로 expert 표현력 ↑ 시도 가치
- A2 의 결과가 강하면 → LoRA r 만 32 로 늘리거나 step 만 ↑ (구조 그대로)
- 200ep 데이터로 B2 (전체 full FT) 도 가능 영역 — 단 시간·메모리 큼

→ 2A 추론 결과 (`spec 02` TODO-03) 보고 결정. 본 문서 §7 (실행 기록) 누적 후 2B §갱신.

---

## 4) 2A hyperparameter 상세

[`config/train_config.yaml`](../finetune/leftarm_v2/config/train_config.yaml) 의 각 값과 근거:

| 항목 | 값 | 근거 |
|---|---|---|
| `policy_path` | `lerobot/smolvla_base` | v1 동일. SmolVLA fine-tune 표준 base. |
| `method` | `lora` | A2 채택 (위 §3). |
| `lora.target_modules` | `all-linear` | VLM + expert 둘 다 LoRA adapter. v1 동일. |
| `lora.r` | `16` | v1 검증값. 2B 에서 r=32 시도 가치. |
| `batch_size` | `16` | v1 동일. 변수 최소화. DGX 메모리 여유는 있으나 2A 는 v1 대비 변수 1개 조정 원칙. |
| `steps` | `20,000` | **2A 의 핵심 변수**. 100ep × 600 frames ≈ 60k frames, batch 16 → 1 epoch ≈ 3,750 step → 5.3 epoch. v1 의 0.13 epoch (500 step) 의 미수렴을 명확히 회피. vision policy fine-tune 일반 적정 (3–10 epoch). |
| `num_workers` | `2` (시도 1: 8) | **시도 1 OOM 후 8→2 축소** (training_log.md §시도1). wandb 증거상 GPU 12W idle → 보존할 활용도 없음. workers 가 메모리 누수 주범. Walking RL 가동 시 더 낮춤. |
| `save_freq` | `1000` | step 20,000 / save 1000 = 20 체크포인트. 디스크 부담·분해능 균형. v1 의 `250` 보다 sparse — 100ep 학습은 v1 보다 길어서. |
| `log_freq` | `50` | wandb·console 로그 step 주기. v1 동일. default 200 보다 ↑ 분해능. |
| `wandb_enable` | `true` | v1 동일. entity·project 는 `base_config.accounts` (BaboGaeguri / leftarm_v2). |
| `device` | `cuda` | DGX GB10 명시. auto-select 의존 회피 (v1 동일). |
| `push_to_hub` | `false` | 체크포인트 자동 Hub push 차단 — DGX→Orin 수동 전송 흐름 (v1 동일). |
| `rename_map` | 자동 생성 | `base_config.cameras` 키 순서로 `{top:camera1, wrist:camera2}` 매핑. smolvla 가 `observation.images.cameraN` 키를 기대 — 누락 시 `Key not found` 에러 (v1 의 [`leftarm_v1/training.md`](../../dgx/docs/finetune/leftarm_v1/training.md) §7 트러블슈팅 확인). |
| `optimizer` / `lr` | lerobot smolvla 기본 | `use_policy_training_preset=true` (default) — smolvla 의 preset optimizer/scheduler 자동 사용. 2A 변수 최소화. 2B 에서 필요 시 조정. |
| `dataset_return_uint8` | `true` | **DGX UMA 메모리 안정**. float32 → uint8 (IPC·prefetch buffer 메모리 1/4). lerobot 이 GPU 에서 float 변환 → 정확도 영향 0. v1 default (false) 에서 변경. |
| `prefetch_factor` | `1` (시도 1: 2) | 시도 1 OOM 후 추가 축소. `num_workers × prefetch = 2 × 1 = 2 batch` buffer (X' 의 1/8). |
| `persistent_workers` | `false` | default true → false. epoch 사이 워커 재시작. **시도 1 단일 epoch 내 OOM 이라 효과 없었음** — 무해 유지. |

> ⚠️ **2A 에서 변경한 것**: v1 대비 `steps` (5000→20,000) + dataset (40ep 단일 task → 100ep 멀티태스크 balanced subset) + **메모리 안정 4 인자** (return_uint8 / prefetch_factor / persistent_workers / num_workers). 메모리 옵션은 정확도 영향 0 이라 변수 통제와 충돌하지 않음 — *결과 해석*은 여전히 steps + dataset 차원으로 깔끔.

> 💾 **DGX UMA 메모리 전략 — 시도 2 패키지 (시도 1 OOM 후 갱신)**: DGX 는 UMA 128GB (CPU/GPU/X server 공유) + swap 0 구조라 dataloader 인코딩 메모리가 GUI 까지 압박 — v1 GUI 멈춤 사고의 핵심 원인. **시도 1 (X', workers=8 / prefetch=2)** 가 step 368 에서 system OOM (5GB/min 누수, [`training_log.md §시도1`](training_log.md)). wandb 증거상 main process 3.4GB 안정 / system 95GB 증발 / GPU 12W idle → DataLoader workers 가 주범, GPU 활용도 보존 명분 사라짐. **시도 2** 는 buffer = `2 workers × 1 prefetch = 2 batch` (X' 의 1/8, v1 default 의 1/16). 학습 중 wandb 의 `data_load_time` / `system/memory` peak 관측 후 다음 run 에서 조정.

> 📌 **PEFT 활성화 시 smolvla 자동 동작 (lerobot v1 검증 확인)**: `--peft.*` 인자가 주어지면 smolvla policy 의 `tune_llm` / `tune_visual` / `tune_projector` / `tune_diffusion_model` 인자는 *무시되고* base model 전체가 자동 frozen + `target_modules` 에만 LoRA adapter 부착. 즉 `--peft.target_modules=all-linear` 가 우리 A2 의도 (VLM+expert 둘 다 LoRA, base 다 frozen) 와 정확히 일치. smolvla 자체 인자 `--policy.lora_*` 는 별도 경로 — 본 v2 는 v1 검증된 `--peft.*` 경로 사용.

---

## 5) 2A dataset subset (P 방식)

[collection_log.md](collection_log.md) 의 현재 차수 분포 기반.

| task | 현재 누적 | 2A subset | front/back |
|---|---|---|---|
| task 1 (doll) | 50 (front 30 / back 20) | **전체 50 ep — `episodes [0..49]`** | 30 / 20 |
| task 2 (can) | 60 (front 40 / back 20) | **앞 50 ep — `episodes [50..99]`** | 30 / 20 |

→ task 2 의 90~99 (7차 back 의 앞 10ep) 만 포함, 100~109 는 제외. 결과 **양 task 모두 front:back = 30:20 (6:4 동일 편향)** — task 간 비교 깔끔.

### lerobot CLI 전달

`docs/reference/lerobot/src/lerobot/configs/default.py:33` 의 `episodes: list[int] | None` 사용. `run_train.py` 가 `train_config.yaml` 의 `episode_ranges_inclusive: [[0, 99]]` 를 `list(range(0, 100))` 으로 expand → `--dataset.episodes='[0,1,2,...,99]'` 로 전달. 별도 subset dataset 생성 X (원 `BaboGaeguri/leftarm_v2` repo 그대로 사용).

### 진짜 균형 (25:25) 안 한 이유

task 2 back 이 현재 20ep 뿐이라 진짜 50:50 (25:25) 을 만들려면 추가 수집 필요. 2A 의 목적이 "조기 평가 → 200ep 추가 수집 가치 판단" 이므로 **수집 지연 없이 P 로 진행**. 2B 에서는 200ep 완성으로 자연히 균형.

---

## 6) 2B 시점 튜닝 계획 (미확정)

2A 추론 (spec 02 TODO-03) 결과 + **2A 학습 wandb 관찰값** 보고 결정.

### wandb 에서 관찰할 핵심 메트릭 (2A 학습 중)

| 메트릭 | 해석 | 조치 후보 |
|---|---|---|
| `data_load_time` vs `step_time` | data > step 이면 CPU dataloader bottleneck → GPU idle | `num_workers` ↑ (8→16) 또는 `prefetch_factor` ↑ (2→4) |
| `system/memory` peak | UMA 헤드룸 (총 121GB 중) | peak < 80% → batch ↑ (16→32) 또는 prefetch ↑ 여지 |
| `system/gpu.process.memory` | Blackwell 메모리 점유 | bf16 활용 여지 판단 |
| `system/gpu.utilization` | Blackwell 활용도 | 낮으면 dataloader bottleneck 또는 batch 너무 작음 |
| `step_time` variance | 디코딩·USB I/O 변동 신호 | 큰 변동 → `Corrupt JPEG` 류 입력단 점검 |

### 2B candidate 조정 옵션

- A2 그대로 + `r=32` (LoRA 표현력 ↑)
- A2 그대로 + `steps 40,000` (더 긴 학습, 200ep × ~600 frames ≈ 120k frames → 1 epoch ≈ 7,500 step → 5.3 epoch)
- **B1 시도** (Full FT on expert, VLM frozen) — A2 와 표현력 비교
- B2 시도 (전체 Full FT) — 200ep 라 가능 영역, system memory headroom 보고
- **batch 32 / 64** (DGX UMA 헤드룸 활용) — 2A wandb memory peak 보고 결정
- **num_workers 16** (20 코어 CPU 활용) — `data_load_time` 이 bottleneck 일 때만
- **bf16** (`policy.use_bf16=true`) — 학습 메모리 ↓ + 속도 ↑ (정확도 영향 검증 필요)

→ 2A 결과 entry (§7) 채워진 후 갱신.

---

## 7) 학습 실행 기록

> 차수별로 누적. 2A·2B 각각 run 마다 entry.

### 2A — 미실행 (대기)

> ⚠️ **본 entry 는 2026-05-15 DGX 학습 계획 시점 작성**. 실제 진행 사실:
> - DGX 시도 1·2·3 (2026-05-15~16): 모두 OOM 사망 — [legacy/train_trial_2026-05-17/docs/training_log.md](../../dgx/legacy/train_trial_2026-05-17/docs/training_log.md)
> - prof_computer M1.5 학습 (2026-05-17): 100ep × 75000 step 완주, loss 0.04 — [leftarm_v2/learning_log.md §M1.5](leftarm_v2/learning_log.md)
> - 본 §7 entry 의 *상세 결과 갱신* 은 다음 사이클에서 정리 (현 시점 outdated).

- run name: `leftarm_v2_2a_<timestamp>` (예정 → prof_computer 가 `leftarm_v2_2a_pc_<ts>` 로 실제 실행)
- 명령: `python run_train.py train --pass 2a` (prof_computer/finetune/leftarm_v2/)
- 산출물 경로: `~/prof_computer_runs/leftarm_v2_2a_pc_<timestamp>/` (prof_computer M1.5 실측 경로)
- 결과 (학습 완료 후 기입): steps · 최종 loss · wandb run URL · ckpt size · throughput · **VRAM peak (RTX 3090 24GB 대비)** · **data_load_time vs step_time 비율** · **GPU utilization** · 이슈
- Orin smoke 추론 결과 (spec 02 TODO-03 후 기입): task 1·2 각각 정성 메모

### 2B — 미실행 (M1 완성 후 진입)
