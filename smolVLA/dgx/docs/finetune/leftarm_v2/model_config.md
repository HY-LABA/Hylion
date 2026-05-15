# leftarm_v2 — 모델 구성 결정 (M2)

> **목적**: leftarm_v2 fine-tune 의 학습 방법·hyperparameter 결정·근거를 한 곳에 정리. `config/train_config.yaml` 의 값이 *왜* 그 값인지의 정본.
> **자매 문서**: [collection_log.md](collection_log.md) (수집 차수 기록), [../camera_and_codec.md](../camera_and_codec.md) (코덱·해상도). 설정 파일: [`dgx/finetune/leftarm_v2/config/train_config.yaml`](../../../finetune/leftarm_v2/config/train_config.yaml).
> **작성**: 2026-05-15

---

## 0) 개요 — 2 패스

`realplaying.md` M2 / spec `02_leftarm_v2_finetune.md` 의 2 패스 구조:

| 패스 | dataset | hyperparameter 정책 | 목적 |
|---|---|---|---|
| **2A** | 100 ep balanced (subset P — task 1 [0..49] + task 2 [50..99]) | v1 검증값 그대로 + step 만 충분히 (사이클 검증에 충분한 수렴) | 사이클 검증 + 조기 성능 평가 |
| **2B** | 200 ep 전체 (M1 완성 후) | 2A 관찰 결과 + 200ep 데이터 반영해 정밀 튜닝 (사용자 주도) | M2 최종 산출 |

---

## 1) SmolVLA 구조 (fine-tune 관점 짧게)

`lerobot/smolvla_base` 는 두 큰 part 로 구성:

- **VLM (vision-language model)** — 사전학습된 SmolLM + vision encoder. image 와 instruction 을 받아 representation 생성. ~450M params 추정.
- **Action expert** — VLM representation 을 받아 action chunk 를 예측. transformer 기반. ~150M params 추정.

fine-tune 시 어느 part 를 *얼마나* 학습시킬지가 핵심 결정.

---

## 2) 학습 방법 4축 매트릭스

[LoRA vs Full FT] × [VLM frozen vs trainable] = 4 옵션.

| 옵션 | VLM | expert | trainable params (대략) | 메모리/시간 | dataset 적응 | 100ep 적합 |
|---|---|---|---|---|---|---|
| A1 | frozen | LoRA (adapter only) | ~3M | 가장 작음 | expert 만 (color·환경 미적응) | ✅ paper 권장 |
| **A2** | LoRA (adapter only) | LoRA (adapter only) | ~6–12M | 작음 | 부분 (LoRA 로 약간) | ✅ **v1 검증, 채택** |
| B1 | frozen | full FT (base weight) | ~150M | 중간 | expert 만 | ⚠️ 가능하나 무거움 |
| B2 | full FT | full FT | ~600M | 큼 | 전체 | ❌ 100ep 과적합 위험 |

> **LoRA 의 의미**: base weight 는 frozen, 각 linear layer 에 low-rank adapter (`A·B` matrix, rank=16) 만 trainable. `target_modules: all-linear` = 모델 내 *모든* linear layer 에 adapter 부착 (VLM linear + expert linear 둘 다). 따라서 **A2 는 expert 도 LoRA** (Full FT 가 아님).

### trade-off 분석

- **VLM frozen vs trainable**: SmolVLA paper 표준 권장은 frozen (사전학습 VLM 의 일반화 능력 보존). 그러나 **우리 task 는 단일 환경(시연장) 에서 잘 동작이 목적**이라 일반화 중요도 ↓ — VLM 이 우리 데이터(파랑+노랑 인형 · 노란 캔 · 특정 사람) 에 적응하는 게 task 성능에 유리. 단 100ep 으론 VLM 전체 adapt 가 noise 학습 갈 위험 → **LoRA 로 부분 adapt 가 균형**.
- **LoRA vs Full FT**: 100ep / 60k frames 는 Full FT 의 600M parameter 를 안정적으로 학습시키기엔 부족 (과적합 위험). LoRA 는 trainable params 가 1–2% 수준이라 100ep 도 안전.

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

[`config/train_config.yaml`](../../../finetune/leftarm_v2/config/train_config.yaml) 의 각 값과 근거:

| 항목 | 값 | 근거 |
|---|---|---|
| `policy_path` | `lerobot/smolvla_base` | v1 동일. SmolVLA fine-tune 표준 base. |
| `method` | `lora` | A2 채택 (위 §3). |
| `lora.target_modules` | `all-linear` | VLM + expert 둘 다 LoRA adapter. v1 동일. |
| `lora.r` | `16` | v1 검증값. 2B 에서 r=32 시도 가치. |
| `batch_size` | `16` | v1 동일. 변수 최소화. DGX 메모리 여유는 있으나 2A 는 v1 대비 변수 1개 조정 원칙. |
| `steps` | `20,000` | **2A 의 핵심 변수**. 100ep × 600 frames ≈ 60k frames, batch 16 → 1 epoch ≈ 3,750 step → 5.3 epoch. v1 의 0.13 epoch (500 step) 의 미수렴을 명확히 회피. vision policy fine-tune 일반 적정 (3–10 epoch). |
| `num_workers` | `8` | Walking RL 미가동 가정. 가동 시 `4` 로 낮춤 (lerobot dataloader 가 CPU·USB 점유). |
| `save_freq` | `1000` | step 20,000 / save 1000 = 20 체크포인트. 디스크 부담·분해능 균형. v1 의 `250` 보다 sparse — 100ep 학습은 v1 보다 길어서. |
| `log_freq` | `50` | wandb·console 로그 step 주기. v1 동일. default 200 보다 ↑ 분해능. |
| `wandb_enable` | `true` | v1 동일. entity·project 는 `base_config.accounts` (BaboGaeguri / leftarm_v2). |
| `device` | `cuda` | DGX GB10 명시. auto-select 의존 회피 (v1 동일). |
| `push_to_hub` | `false` | 체크포인트 자동 Hub push 차단 — DGX→Orin 수동 전송 흐름 (v1 동일). |
| `rename_map` | 자동 생성 | `base_config.cameras` 키 순서로 `{top:camera1, wrist:camera2}` 매핑. smolvla 가 `observation.images.cameraN` 키를 기대 — 누락 시 `Key not found` 에러 (v1 의 [`../leftarm_v1/training.md`](../leftarm_v1/training.md) §7 트러블슈팅 확인). |
| `optimizer` / `lr` | lerobot smolvla 기본 | `use_policy_training_preset=true` (default) — smolvla 의 preset optimizer/scheduler 자동 사용. 2A 변수 최소화. 2B 에서 필요 시 조정. |

> ⚠️ **2A 에서 변경한 것**: v1 대비 `steps` 만 (5000 → 20,000) + dataset (40ep 단일 task → 100ep 멀티태스크 balanced subset). 다른 모든 hyperparameter 는 v1 그대로 — 결과 해석을 깔끔하게 한다.

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

2A 추론 (spec 02 TODO-03) 결과 보고 결정. 현재 시점 candidate:

- A2 그대로 + r=32 (LoRA 표현력 ↑)
- A2 그대로 + steps 40,000 (더 긴 학습)
- B1 시도 (Full FT on expert, VLM frozen) — A2 와 비교
- B2 시도 (전체 Full FT) — 200ep 라 가능 영역
- batch 32 (DGX 메모리 활용)

→ 2A 결과 entry (§7) 채워진 후 갱신.

---

## 7) 학습 실행 기록

> 차수별로 누적. 2A·2B 각각 run 마다 entry.

### 2A — 미실행 (대기)

- run name: `leftarm_v2_2a_<timestamp>` (예정)
- 명령: `python run_train.py train --pass 2a` 또는 동등 (run_train.py 작성 시 확정 — spec 02 TODO-01)
- 산출물 경로: `~/smolvla/dgx/outputs/leftarm_v2_2a_<timestamp>/`
- 결과 (학습 완료 후 기입): steps · 최종 loss · wandb run URL · ckpt size · throughput · 이슈
- Orin smoke 추론 결과 (spec 02 TODO-03 후 기입): task 1·2 각각 정성 메모

### 2B — 미실행 (M1 완성 후 진입)
