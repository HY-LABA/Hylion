# leftarm_v2 — 모델 구성 카탈로그

> **역할**: SmolVLA fine-tune 의 *학습 방식·hyperparameter 선택지* 정적 카탈로그. "어떤 인자로 학습하는가" + "어떤 옵션이 추가 고려 가치 있는가" 의 참조본.
> **본 파일이 *담지 않는* 것**: 특정 분기 학습의 결과·시도 이력·시점별 의사결정 흐름. → [leftarm_v2/learning_log1.md](leftarm_v2/learning_log1.md) (001~003 아카이브) · [leftarm_v2/learning_log2.md](leftarm_v2/learning_log2.md) (현행).
> **자매 문서**: [collection_log.md](../../dgx/docs/finetune/leftarm_v2/collection_log.md) (수집 차수 — DGX 책임). 학습 설정 정본: [`prof_computer/finetune/leftarm_v2/branches/<분기>/train_config.yaml`](../finetune/leftarm_v2/).
> **편집 정책**: 본 파일은 *카탈로그* — 특정 학습의 결과나 시점별 결정 흐름은 *learning_log* 측에 기록하고, 본 파일에는 그 결과로 *추출된 추상 옵션·trade-off* 만 반영. 시점 표기·"YYYY-MM-DD 갱신" 식 누적 이력 박지 말 것.
> **명명 컨벤션**: 분기명·계층 구조·시간 라벨 룰은 [prof_computer/README.md §7 명명 3-계층 + 시간 라벨](../README.md) 참조 — 본 파일은 *카탈로그 내용* 만 다룸.

---

## 1) SmolVLA 구조 (fine-tune 관점)

`lerobot/smolvla_base` 는 두 part 로 구성:

- **VLM (vision-language model)** — 사전학습된 SmolLM + vision encoder. image 와 instruction 을 받아 representation 생성. ~450M params 추정.
- **Action expert** — VLM representation 을 받아 action chunk 를 예측. transformer 기반. ~150M params 추정.

fine-tune 시 어느 part 를 *얼마나* 학습시킬지가 핵심 결정 차원.

---

## 2) 학습 방법 매트릭스 (2×3 = 6 옵션)

[VLM frozen / LoRA / Full FT] × [expert LoRA / Full FT] = 6 옵션. *VLA 의미 보존 여부* 와 *lerobot 표준 entry 사용 가능 여부* 가 핵심 분류 축.

| 옵션 | VLM | expert | trainable (대략) | 메모리/시간 | VLA 의미 보존 | lerobot 표준 entry | 비고 |
|---|---|---|---|---|---|---|---|
| A1 | frozen | LoRA | ~3M | 가장 작음 | ❌ (ACT 화) | ✅ | VLM 미적응 — 환경 적응 능력은 base VLM 의 0-shot 인식에 의존. base 가 우리 환경 인식 못 하면 expert 단독 매핑만 학습 → instruction-conditioned ACT 와 동치. *VLA 가치 폐기*. |
| **A2** | LoRA | LoRA | ~6–12M | 작음 | ✅ 부분 (LoRA r=16) | ✅ | VLM + expert 둘 다 LoRA adapter. *PEFT 표준 경로*. r=16/all-linear 가 v1 검증값. |
| B1 | frozen | Full FT | ~150M | 중간 | ❌ (ACT 화) | ❌ | A1 의 expert 확장판. PEFT wrap 이 base 전체 frozen + adapter 만 trainable 강제 ([pretrained.py:303](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L303)) → expert base weight 도 frozen 됨. expert 만 별도 unfreeze 하려면 코드 우회 필요. |
| B2 | Full FT | Full FT | ~600M | 큼 | ✅ 최대 | ✅ | 전체 Full FT. RTX 3090 24GB 단일 GPU 에서는 OOM 영역. DGX 또는 multi-GPU 환경 필요. |
| **C1** | LoRA | Full FT | ~156M | 큼 (24GB 경계) | ⚠️ VLM 측 LoRA 만 살아 *부분 약화* | ❌ | "VLM 적응 유지 + expert capacity ↑" — A2 의 LoRA r=16 표현력 한계 돌파. lerobot 표준 entry 불가 (B1 과 동일 이유) — 신규 학습 entry + lerobot 코드 우회 필요. |
| C2 | Full FT | LoRA | ~456M | 큼 (24GB 경계) | ✅ VLM 최대 + expert 약 | ❌ | VLM 600M Full FT 는 데이터 양 요구량이 크고 (VLA 분야 1000ep+ 표준), 본 프로젝트 데이터 양 (현 310ep 영역) 에서는 시간 비용 대비 가치 낮음. |

> **VLA 의미 보존 축**: VLM frozen 분기 (A1/B1) 는 *smolVLA 라는 VLA framework 의 가치 (사전학습 multimodal representation + action 의 통합 학습)* 가 사라지고 사실상 *vision-conditioned action policy = ACT 류* 가 됨. smolVLA 를 base 로 선택한 이유 자체와 배치되는 분기.

> **LoRA 의 의미**: base weight 는 frozen, 각 linear layer 에 low-rank adapter (`A·B` matrix, rank=16) 만 trainable. `target_modules: all-linear` = 모델 내 *모든* linear layer 에 adapter 부착 (VLM linear + expert linear 둘 다). 따라서 **A2 는 expert 도 LoRA** (Full FT 가 아님).

### Trade-off 분석

- **VLM frozen vs trainable**: SmolVLA paper 표준 권장은 frozen — *일반화 능력 보존* 의도. 단 base VLM 의 우리 환경 0-shot 인식 능력이 약하면 frozen 의 가치 (사전학습 representation 활용) 가 작아짐 — *환경 적응 신호를 살리는 게 우선* → LoRA 또는 Full FT.
- **LoRA vs Full FT**: Full FT 600M (B2) 는 안정 학습에 큰 데이터 양 (VLA 분야 1000ep+ 표준) 과 충분한 VRAM 필요. LoRA 는 trainable params 1–2% 수준이라 작은 데이터에도 안전.
- **데이터 양 영역과 옵션 적합도**: 100ep 시점에서 안전했던 옵션이 300ep 영역에서도 동일하지 않을 수 있음 — 일부 옵션 (특히 B1·C1) 은 데이터 양에 따라 *과적합 위험 영역* 이 변동. 자세한 시점별 적합도 변화는 [learning_log1.md §이관 2 / 이관 3](leftarm_v2/learning_log1.md) 참조.
- **C1/C2 의 lerobot 표준 entry 불가 이유**: [pretrained.py:303](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L303) 의 `wrap_with_peft()` 가 `for p in self.parameters(): p.requires_grad_(False)` 로 *모든* base param 강제 frozen → LoRA adapter 만 trainable. expert base weight 도 같이 frozen 됨. expert 만 별도 unfreeze 하려면 *lerobot upstream 코드 우회 (Category A read-only)* 또는 신규 학습 entry 필요.

---

## 3) 현 권장 분기 — A2 (LoRA all-linear)

### 권장 이유

1. **PEFT 표준 경로** — `--peft.*` 인자만으로 활성화. lerobot 코드 우회 없음.
2. **VLM + expert 양쪽 부분 적응** — `all-linear` 로 두 part 모두 LoRA adapter. *VLA 의미 보존* 부분 충족.
3. **trainable params 작음** — RTX 3090 24GB 단일 GPU 에서 batch 4~6 안전 영역.
4. **데이터 양 100~400ep 영역에서 안정** — 과적합 위험 낮음 ([best_practice §4-4](leftarm_v2/lerobot_smolvla_training_best_practice.md): VLA 고성능 300-1200ep, multi-task 100ep/task 권장 — 본 데이터 양 영역 권장 범위 안).

### 권장 hyperparameter 묶음

| 항목 | 값 | 근거 |
|---|---|---|
| `policy_path` | `lerobot/smolvla_base` | SmolVLA fine-tune 표준 base. |
| `method` | `lora` | A2 채택. |
| `lora.target_modules` | `all-linear` | VLM + expert 둘 다 LoRA adapter. |
| `lora.r` | `16` | rank. r=32 시도 가치는 *capacity ↑ 단일 변수* 영역. |
| `batch_size` | RTX 3090 단일 GPU: bf16 시 `6`, fp32 시 `4` | VRAM 24GB 제약 — smoke 측정 기반 결정 영역. |
| `num_workers` | `4` (prof_computer) | system RAM·VRAM 분리 환경. UMA 노드 (DGX) 는 더 보수적. |
| `prefetch_factor` | `2` | dataloader bottleneck 회피 + RAM 압박 균형. |
| `dataset_return_uint8` | `true` | float32 → uint8, IPC 1/4. GPU 변환 — 정확도 영향 0. |
| `persistent_workers` | `false` | epoch 사이 워커 재시작, memory leak 위험 회피. |
| `video_backend` | `torchcodec` | x86_64 + cu128 환경에서 pyav buffer leak 회피. aarch64 환경에서는 ABI 깨짐 — 별도 검토. |
| `mixed_precision` | bf16 (`accelerate launch --mixed_precision=bf16`) | `lerobot-train` 직접 호출 + `--policy.use_amp=true` 만으로는 효과 없음 확인 — accelerate launcher 가 진짜 트리거. |
| `scheduler_decay_steps` | `= steps` (동기화) | cosine decay 가 전 구간 작동. 미동기화 시 후반 lr ≈ 0 영역 학습 정체. |
| `wandb_enable` | `true` | 실측 메트릭 추출 표준. |
| `device` | `cuda` | 명시. auto-select 의존 회피. |
| `push_to_hub` | `false` | 학습 측 자동 push 차단 — 검증 후 수동 push. |

> **rename_map 자동 생성**: smolvla 가 `observation.images.cameraN` 키를 기대 — `base_config.cameras` 키 순서로 `{top:camera1, wrist:camera2}` 매핑 자동 생성. 누락 시 `Key not found` 에러.

> **`use_policy_training_preset=true`** (default): smolvla 의 preset optimizer/scheduler 자동 사용. lerobot 표준 경로.

> **PEFT 활성화 시 smolvla 자동 동작**: `--peft.*` 인자가 주어지면 smolvla policy 의 `tune_llm` / `tune_visual` / `tune_projector` / `tune_diffusion_model` 인자는 *무시되고* base model 전체가 자동 frozen + `target_modules` 에만 LoRA adapter 부착. `--peft.target_modules=all-linear` 가 A2 의도와 정확히 일치. smolvla 자체 인자 `--policy.lora_*` 는 별도 경로 — *A2 분기는 `--peft.*` 경로 사용*.

### 다음 시도 후보 영역 (capacity / 학습 효율 차원)

본 카탈로그가 *추가 고려해볼 옵션* 으로 안내하는 영역:

| 후보 | 변경 | 기대 효과 | 위험 |
|---|---|---|---|
| LoRA r ↑ (16→32) | `lora.r=32` | adapter capacity ↑ | trainable params 2배 — 작은 데이터에서 과적합 위험 약간 ↑ |
| batch_size ↑ | RTX 3090 한계 b6 (bf16) — 다른 노드면 16/32 | gradient noise ↓, 학습 안정 | VRAM 한계 + memory peak transient |
| steps ↑ (epoch ↑) | dataset 크기 × 5~10 epoch | 더 깊은 수렴 | overtrain 위험 (단 LoRA 는 비교적 안전) |
| `scheduler_decay_steps` < steps (의도적 early decay) | 후반 plateau | 후반 학습 정체 + 수렴 안정 | 후반 학습 거의 정지 — 보통 비추 |
| `bf16` (accelerate launch) | mixed precision | VRAM ↓ + 속도 ↑ | 정확도 영향 검증 필요 (보통 VLA 영역에서 무해) |
| `empty_cameras=1` | base 의 3 cam 입력 형식과 우리 2 cam dataset 의 mismatch 해소 (3번째 카메라 zero-pad) | base 사전학습 분포 정합 | 학습 시간 ~24% ↑ (입력 차원 ↑). 단독 변경의 root-cause 효과는 약함 ([learning_log1.md §002 분기](leftarm_v2/learning_log1.md) 참조). |

### 다음 분기 후보 영역 (학습 방법 차원)

| 후보 | 코드 우회 | 데이터 양 영역 | 비고 |
|---|---|---|---|
| A2 + r=32 | ❌ (단순 config) | 모든 영역 | capacity ↑ 단일 변수 시도 |
| C1 (LoRA VLM + Full FT expert) | ✅ 필요 (PEFT manual wrap + expert unfreeze + lr group 분리) | 300ep+ 영역에서 시도 가치 ↑ | A2 의 LoRA r=16 한계 돌파. expert Full FT 의 과적합 위험은 데이터 양에 따라 변동. |
| B2 (전체 Full FT) | ❌ | 1000ep+ 영역 권장 | RTX 3090 24GB 에선 OOM, DGX/multi-GPU 영역 |

---

## 4) 데이터 subset 정책

### 균형 subset 의 의미

multi-task fine-tune 에서 task 간 sample 수 균형은 *task 간 비교 가능성* 의 전제. 한쪽 task 가 압도적으로 많으면 정책이 *그쪽으로 bias* 됨.

| subset 형식 | 정의 | 사용 시점 |
|---|---|---|
| **balanced subset (P)** | task 별 동일 ep 수 + 동일 front/back 비율 | 사이클 검증 + 조기 평가 |
| **전체 dataset** | 수집된 모든 ep | M2 최종 학습 |

### lerobot CLI 전달

`docs/reference/lerobot/src/lerobot/configs/default.py:33` 의 `episodes: list[int] | None` 사용. `run_train.py` 가 yaml 의 `episode_ranges_inclusive` 를 expand → `--dataset.episodes='[0,1,2,...,N]'` 로 전달. 별도 subset dataset 생성 X (원 HF Hub repo 그대로 사용).

### 균형 가능성과 수집 진행도

진짜 균형 (예: task1·task2 각각 front 25 / back 25) 은 수집된 차수 분포가 받쳐줘야 가능. 수집이 진행 중인 시점에는 *균형 ≈ subset* 으로 진행 → 수집 완성 후 *진짜 균형* 으로 재학습. 현 시점 차수 분포는 [collection_log.md](../../dgx/docs/finetune/leftarm_v2/collection_log.md) 참조.

---

## 5) wandb 관찰 핵심 메트릭

학습 중 wandb dashboard 에서 *조정 신호* 로 봐야 할 메트릭:

| 메트릭 | 해석 | 조치 후보 |
|---|---|---|
| `train/loss` 추이 | 수렴 패턴 (강하/평탄/발산) | 평탄 → lr/scheduler 검토. 발산 → batch / lr 축소. |
| `train/grad_norm` | gradient clip (10) 도달 여부 | 빈번한 clip → lr 축소 또는 batch ↑ |
| `train/dataloading_s` vs `train/update_s` | dataloader bottleneck 여부 | data > update 의 1/2 → `num_workers` ↑ 또는 `prefetch_factor` ↑ |
| `system/gpu.0.memoryAllocated` peak | VRAM peak (RTX 3090 24GB 대비) | < 70% → batch ↑ 여지. > 90% → transient OOM 위험 |
| `system/gpu.0.gpu` (util) | GPU 활용도 | 낮으면 dataloader bottleneck 또는 batch 너무 작음 |
| `system/gpu.0.temp` | thermal throttle (RTX 3090 ~85°C 경계) | 지속 83°C+ → cooling 확인 |
| `system/proc.memory.rssMB` 추세 | RAM 누수 (lerobot pyav buffer leak 등) | 시간 비례 단조 증가 → backend (pyav→torchcodec) 검토 |
| `system/disk./.usageGB` 추세 | ckpt 누적 디스크 사용 | save_freq 조정 또는 prune 필요 |

---

## 6) 관련 자료

- 학습 설정 정본: [`prof_computer/finetune/leftarm_v2/branches/<분기명>/train_config.yaml`](../finetune/leftarm_v2/)
- 실행 wrapper: [`prof_computer/finetune/leftarm_v2/branches/<분기명>/run_train.py`](../finetune/leftarm_v2/)
- 실행 기록: [learning_log1.md](leftarm_v2/learning_log1.md) (M1.5~003 아카이브) · [learning_log2.md](leftarm_v2/learning_log2.md) (현행)
- 카메라 카탈로그 정합 보고서: [research_empty_cameras_2026-05-18.md](leftarm_v2/research_empty_cameras_2026-05-18.md)
- SmolVLA 학습 best practice 보고서: [lerobot_smolvla_training_best_practice.md](leftarm_v2/lerobot_smolvla_training_best_practice.md)
- 사전학습 카메라 분포 보고서: [research_smolvla_pretrain_cameras_2026-05-19.md](leftarm_v2/research_smolvla_pretrain_cameras_2026-05-19.md)
- 수집 차수: [collection_log.md](../../dgx/docs/finetune/leftarm_v2/collection_log.md)
