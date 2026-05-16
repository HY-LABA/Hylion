# SmolVLA + lerobot Training Best Practice — Community Survey

> 작성: 2026-05-16 | researcher agent
> 호출자: orchestrator — 사용자 학습 OOM 대기 + image dataset 변환 (1-3h) 유휴 시간 활용
> 관련 spec: `02_prereq_dataset_video_to_image.md`, `02_leftarm_v2_finetune.md`
> 관련 보고서: `m1.5_video_decode_oom.md` (선행 OOM 진단)

---

## §1 SmolVLA 모델 권장 학습 셋업

### 1-1. 공식 권장 (HuggingFace 공식 blog + model card + docs)

SmolVLA 는 450M 파라미터 VLA 로, 두 파트로 구성:
- **VLM backbone**: SmolVLM2-500M-Video-Instruct (SigLIP vision encoder + SmolLM2-1.7B-Instruct language decoder)
- **Action expert**: ~100M params, Flow Matching Transformer. VLM 의 중간 레이어 feature 로 conditioning.

**공식 fine-tune 커맨드 (huggingface.co/docs/lerobot/en/smolvla)**:
```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/mydataset \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/my_smolvla \
  --policy.device=cuda \
  --wandb.enable=true
```

**공식 권장 핵심**:
- 20k steps → A100 단일 GPU 기준 약 4시간. steps 는 use-case 에 맞게 조정.
- `batch_size=64` 시작, GPU 허용 시 증가 — 단 loading time 이 짧게 유지되는 조건 하.
- `policy.dtype=bfloat16` — 메모리 효율 (model card 기준)
- `policy.gradient_checkpointing=true` — 메모리 제약 시 권장 (단, v0.6.0 이전 SmolVLA 는 Pi0 전용이었음 → v0.6.0 에서 전 policy 확장 예정)

### 1-2. SmolVLA 논문 (arxiv 2506.01844) — 학습 hyperparameter

| 항목 | 사전학습 값 | fine-tune 값 (시뮬레이션) | 비고 |
|------|------------|--------------------------|------|
| Steps | 200,000 | 100,000 | 실물 fine-tune: 200,000 |
| Global batch size | 256 | 64 | — |
| LR (peak) | 1e-4 | 1e-4 (기본값) | — |
| LR (min) | 2.5e-6 | 2.5e-6 | CosineDecay |
| Warmup | 100 steps | 1,000 steps (config default) | — |
| Optimizer | AdamW | AdamW | β₁=0.9, β₂=0.95 |
| Precision | bfloat16 | bfloat16 | torch.compile() 포함 |
| GPU | 4× GPU | 1× A100 가능 | — |
| Frozen | VLM frozen, expert only | 동일 (train_expert_only=True) | — |

**주의**: 논문 benchmark 에서 달성한 성능(예: libero_object 96%)을 재현 시도한 커뮤니티 사례가 0% 달성도 보고 → training recipe 의 세부(정확한 LR, commit hash, GPU 수) 가 논문에 충분히 공개되지 않은 상태 (GitHub issue #3287).

### 1-3. configuration_smolvla.py 에서 확인한 default 값 (우리 참조 레퍼런스)

`docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py`:
- `n_obs_steps: 1`, `chunk_size: 50`, `n_action_steps: 50`
- `freeze_vision_encoder: True`, `train_expert_only: True`, `train_state_proj: True`
- `optimizer_lr: 1e-4`, `optimizer_betas: (0.9, 0.95)`, `optimizer_grad_clip_norm: 10.0`
- `scheduler_warmup_steps: 1_000`, `scheduler_decay_steps: 30_000`, `scheduler_decay_lr: 2.5e-6`
- `num_vlm_layers: 16` (전체 레이어의 절반 사용 → compute 50% 절감)
- `expert_width_multiplier: 0.75` (VLM dimension 의 75% — 경량화)
- `compile_model: False` (torch.compile 기본 off)

**중요 inference 주의**: `n_action_steps` 기본값은 config 에서 50 이지만, 모델 card 및 커뮤니티 다수 보고에 따르면 **Hub 에 올라간 smolvla_base 의 `config.json` 내 `n_action_steps=1`** 로 설정돼 있어 inference 시 매우 느려짐. fine-tune 후 Hub push 전 `config.json` 에서 `n_action_steps: 50` 으로 수동 변경 필요.

### 1-4. 커뮤니티 사례

| 사례 | 환경 | 결과 | 핵심 발견 |
|------|------|------|----------|
| SO-101 pick-place (ggando.com) | RTX 3090, batch=64, 20k steps, 75ep | 100% success (5/5) | 데이터 정합성 (camera순서, 빠른 teleoperation 전략) + workspace 협소화 |
| Xavier O'Keefe (Medium) | L4 22GB, batch=64, 12k steps, 125ep | ~40% success | LIBERO statistics 오사용이 가장 큰 실수 |
| LearnOpenCV | RTX 3080Ti (12GB), batch=44 | ~11.5GB VRAM 사용 | batch 44 에서 12GB 근접 |
| SmolVLA paper (official) | SO100, 50ep 5 positions | 78.3% (pretrain) → further +multitask | 25ep 는 부족 (bad performance), 50ep per variation 필요 |

---

## §2 lerobot 학습 entry 표준 패턴

### 2-1. 표준 lerobot-train CLI

```bash
# 최소 예시
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=NAMESPACE/DATASET \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/run_name \
  --job_name=run_name \
  --policy.device=cuda \
  --wandb.enable=true
```

**episode subset 지정** (`docs/reference/lerobot/src/lerobot/configs/default.py:33`):
```bash
--dataset.episodes='[0,1,2,...,99]'  # list[int] | None
```

**video backend 명시** (DGX 환경 필수):
```bash
--dataset.video_backend=pyav  # torchcodec ABI 문제 환경에서 필수
```

**PEFT LoRA 추가**:
```bash
--peft.method_type=LORA \
--peft.r=64 \
--peft.target_modules='...'  # 생략 시 기본: q_proj, v_proj + state/action proj
```

**multi-GPU** (`accelerate launch`):
```bash
accelerate launch --multi_gpu --num_processes=N $(which lerobot-train) \
  --batch_size=8 --steps=50000 ...
# 효과적 batch = batch_size × N GPU
# LR·steps 는 자동 조정 X — 수동 스케일 필요 (lr × N, steps / N)
```

### 2-2. 표준 config 항목 (SmolVLA preset 포함)

lerobot 은 SmolVLA 에 대해 `use_policy_training_preset=True` (default) 시 아래를 자동 적용:
- Optimizer: AdamW (lr=1e-4, betas=(0.9,0.95), weight_decay=1e-10, grad_clip=10)
- Scheduler: CosineDecayWithWarmup (peak=1e-4, decay=2.5e-6, warmup=1000steps, decay=30000steps)
- 이 preset 을 override 하려면 `--policy.optimizer_lr`, `--policy.scheduler_decay_lr` 등 명시.

### 2-3. Monitoring

- **wandb** 권장 지표: `loss`, `grad_norm`, `data_load_time`, `step_time`, `system/memory`, `system/gpu.process.memory`, `system/gpu.utilization`
- `data_load_time > step_time` → DataLoader bottleneck (num_workers / prefetch 조정)
- `grad_norm` 급등 → LR 너무 높거나 NaN 전조
- loss 0.5 이하 수렴 → 일반적으로 정상 범위 (실제 사례: 0.162→0.005 @ 20k steps)

---

## §3 PEFT/LoRA 권장 사항

### 3-1. lerobot 공식 PEFT 문서 (huggingface.co/docs/lerobot/en/peft_training)

**기본 동작 (target_modules 미지정 시)**:
> "By default, PEFT will target the `q_proj` and `v_proj` layers of the LM expert in SmolVLA. It will also target the state and action projection matrices as they are most likely task-dependent."

즉 기본 target: `q_proj`, `v_proj` (VLM attention) + `state_proj`, `action_in_proj`, `action_out_proj`, `action_time_mlp_in`, `action_time_mlp_out`

**MLP 도 포함하려면**:
```bash
--peft.target_modules='(model\.vlm_with_expert\.lm_expert\..*\.(down|gate|up)_proj|.*\.(state_proj|action_in_proj|action_out_proj|action_time_mlp_in|action_time_mlp_out))'
```

**전체 linear (all-linear)**:
- `--peft.target_modules=all-linear` — VLM + expert 전 linear. 우리 현 설정.

### 3-2. Rank 권장

| Rank | 특징 | 추천 상황 |
|------|------|----------|
| r=8 | 가장 경량 (파라미터 ↓) | 데이터 소량(< 50ep), 속도 우선 |
| r=16 | 균형 (우리 현재) | 일반 fine-tune 출발점 |
| r=32 | 표현력 ↑, 5% 이내 full FT 근접 | 더 많은 데이터, domain shift 큰 경우 |
| r=64 | 공식 PEFT doc 예시값 | 더 복잡한 task, 많은 데이터 |

공식 PEFT doc 예시 (`--peft.r=64`) 와 논문 사례 (r=8, α=16) 모두 task 에 따라 다름. 2025 LoRA 가이드 라인: "r=16 은 reliable starting point, domain shift 크면 r=32 or 64".

**우리 r=16 평가**: 100ep 데이터 + domain-specific (단일 시연장) 에서 적절. 2B 에서 r=32 시도 근거 있음.

### 3-3. Learning Rate (LoRA vs Full FT)

공식 lerobot PEFT docs:
> "The learning rate and the scheduled target learning rate can usually be scaled by a factor of 10 compared to the learning rate used for full fine-tuning (e.g., 1e-4 normal, so 1e-3 using LoRA)."

즉 Full FT LR = 1e-4 → LoRA LR = 1e-3 권장.

**우리 현재 상태**: `use_policy_training_preset=True` → SmolVLA default lr=1e-4 사용 중. LoRA 적용임에도 full FT 기준 LR 사용 중 → **lr=1e-3 로 올리는 것이 공식 권장**.

단 커뮤니티 사례 (Xavier O'Keefe, ggando.com): 1e-4 사용 + 20k steps 에서 성공 사례 있음. "1e-5 같은 낮은 LR 은 LoRA fine-tune 에 좋지 않다" (SmolVLA inference correction 논문 코멘트). → **1e-4 는 보수적이지만 작동, 1e-3 는 공식 권장이나 주의 필요**.

### 3-4. adapter merge / inference

lerobot 은 현재 LoRA adapter 를 별도 merge 없이 checkpoint 저장 + 로드. inference 시 PEFT adapter 자동 적용. Orin 으로 체크포인트 전송 시 adapter weight 포함된 전체 checkpoint 전송 필요. Hub push 시 `config.json` 내 `n_action_steps=1` → `50` 수동 변경 필수.

---

## §4 Dataset 전략

### 4-1. image vs video dataset

| 항목 | video dataset (mp4) | image dataset (png/parquet) |
|------|--------------------|-----------------------------|
| 디스크 사용 | 적음 | 많음 (3-5×) |
| DataLoader 속도 | codec 의존 (H.264: 16-37ms/frame, AV1: 210-238ms/frame) | 빠름 (disk sequential read) |
| 메모리 누수 | pyav: leak 가능 (우리 확인). AV1 5× 느림 | 없음 (PNG decode 단순) |
| 학습 throughput | data_load_time > step_time 빈발 (issue #1488) | data_load_time << step_time 기대 |
| 우리 상황 | pyav 1.07GB/min leak, torchcodec ABI 실패 | **변환 중 (현재 진행)** |

**결론**: image dataset 이 우리 DGX 환경 (PyTorch 2.10 + GB10 + FFmpeg 6) 에서 유일한 안정 경로. 커뮤니티도 AV1 비디오 → 이미지 전환이 5× 속도 개선 보고.

### 4-2. frame 품질 (PNG vs JPG)

- lerobot 은 image dataset 에서 PNG 저장 (우리 convert_to_image.py 도 PNG)
- PNG: lossless, 디코딩 빠름, 메모리 사용 많음
- 커뮤니티 표준: `resize_with_pad to 512×512` (SmolVLA 입력 크기) 로 저장

### 4-3. Data Augmentation

lerobot 의 `image_transforms` 설정 (학습 시 on-the-fly):
```yaml
image_transforms:
  enable: true
  transforms:
    - type: ColorJitter
      brightness: [0.8, 1.2]
      contrast: [0.8, 1.2]
      hue: [-0.05, 0.05]
      saturation: [0.5, 1.5]
```
`lerobot-imgtransform-viz` 커맨드로 augmentation 효과 미리 확인 가능.

SmolVLA 사용자 사례 (ggando.com): 조명 변화 + 배경 변화에 취약 → color jitter augmentation 권장. 단 **smolvla 가 이미지를 512×512 padding-resize 후 64 visual token 으로 압축** — 너무 강한 crop 은 효과 제한.

### 4-4. Episode 수 권장

| 상황 | 최소 | 권장 | 비고 |
|------|------|------|------|
| 단순 pick-place, 단일 위치 | 25ep | 50ep | 25ep 는 "bad performance" (공식 doc) |
| pick-place, 위치 변형 있음 | 50ep | 50ep per position (5 pos × 10) | 공식 SVLA SO100 논문 데이터 |
| multi-task (2 task) | 50ep/task | 100ep/task | VLA 는 일반적으로 300-1200ep 권장 (고성능 목표 시) |
| 전체 full FT | 200+ | - | 100ep Full FT 는 과적합 위험 |

우리 100ep (2A subset) 는 LoRA fine-tune 기준 적절한 출발점. 200ep (2B) 는 추가 개선 기대.

### 4-5. DataLoader 권장 (num_workers / prefetch_factor)

| 설정 | 특징 | 권장 상황 |
|------|------|----------|
| num_workers=0 | 안전, 느림 | 메모리 불안정 시 진단용 |
| num_workers=2 | 우리 현재, 보수적 | image dataset + UMA 환경 |
| num_workers=8+ | 빠름 | 충분한 메모리 + data_load_time 병목 시 |
| prefetch_factor=1 | 우리 현재 | 메모리 보수적 |
| prefetch_factor=2 | default | 일반 상황 |
| persistent_workers=True | epoch 간 재시작 X | 일반 권장 (lerobot default True) |

**중요**: `std::bad_alloc` 에러 발생 시 `num_workers=0` + `prefetch_factor` 제거가 유일한 안정 경로였던 사례 보고 (issue #2209). `persistent_workers=False` 는 무해하나 효과도 제한.

image dataset 전환 후 우리 환경에서 `num_workers` 를 점진적으로 올려 `data_load_time` vs `step_time` 균형 찾기 권장 (wandb 관찰).

---

## §5 하드웨어별 권장

### 5-1. 단일 GPU (24-48GB, 예: A100, RTX 3090)

| GPU | VRAM | 권장 batch_size | LoRA r | 비고 |
|-----|------|----------------|--------|------|
| RTX 3080Ti (12GB) | 12GB | 44 (한계), 16 (안전) | 16 | 11.5GB 사용 (learnopencv) |
| L4 (22GB) | 22GB | 64 | 32 | Xavier O'Keefe |
| RTX 3090 (24GB) | 24GB | 64 | 32-64 | issue #1234 (freeze 보고) |
| A100 (80GB) | 80GB | 64+ | 64 | 공식 baseline |

### 5-2. multi-GPU (DDP, accelerate)

```bash
accelerate launch --multi_gpu --num_processes=4 \
  --mixed_precision=bf16 \
  $(which lerobot-train) \
  --batch_size=8 \  # effective: 32
  --steps=50000 \
  --optimizer.lr=4e-4 \  # LR × N_GPU (수동 스케일)
  ...
```
- LR / steps 자동 스케일 X → 수동 조정 필요
- Checkpoint, wandb 는 main process 만 처리 (자동)
- `use_amp` flag 는 accelerate 모드에서 무시됨 (accelerate 의 `mixed_precision` 이 제어)

### 5-3. DGX Spark (UMA 128GB) 특수 환경 — 직접 증거

**DGX Spark 의 핵심 특수성** (natolambert/dgx-spark-setup, Sggin1/DGX-SPARK):
- **UMA 128GB**: GPU/CPU DRAM 동일 풀. GPU OOM = system OOM → 머신 zombie 가능
- **GB10 (sm_121)**: CUDA 13.0 필요. PyTorch 2.9+ cu130 휠 필수
- **aarch64**: 일반 x86 ML 패키지 불호환 (torchcodec aarch64 wheel 미공개)
- **swap 비활성화 권장**: `sudo swapoff -a` — swap 활성화 시 OOM → swap death spiral → 머신 freeze

**권장 메모리 방어 전략** (dgx-spark-setup 가이드에서):
1. swap 비활성화
2. `systemd-run --scope -p MemoryMax=100G` 로 학습 실행 (OS ~20GB 확보)
3. SSH OOM score 보호: `/etc/systemd/system/ssh.service.d/oom.conf`
4. 학습 전 `free -h` 로 >80GB free 확인
5. 캐시 클리어: `sync; echo 3 > /proc/sys/vm/drop_caches`

**DGX Spark 메모리 특성** (SFT 기준 실측):
- batch 8 → ~47GB 사용 (권장)
- batch 16 → ~81GB 사용 (한계)
- 메모리 super-linear 증가: batch 2× → memory 1.7× 이상

**attention 주의**: flash-attn 설치 X. SDPA 사용 (`attn_implementation="sdpa"`) 이 Blackwell 에서 더 빠름.

**우리 환경 특이사항** (spec + training_log 에서 확인):
- torch 2.10.0+cu130 (cu130 wheel) → sm_121 실질 동작
- torchcodec 0.11.1: aarch64 ABI 미스매치로 사용 불가 (`torch_dtype_float4_e2m1fn_x2` undefined symbol)
- FFmpeg 6.1.1: torchvision video_reader 와 ABI 충돌 (FFmpeg <4.3 필요)
- pyav 15.1.0: video decode 중 OS-level buffer leak (process RSS 외부 누수)
- **결론**: video dataset 학습 불가 → image dataset 변환이 유일한 경로

---

## §6 메모리 관리 / OOM 회피

### 6-1. Gradient Checkpointing

```bash
--policy.gradient_checkpointing=true
```
- 활성화 전 평균 메모리 → 약 30-50% 절감 (activation 재계산)
- SmolVLA: v0.6.0 에서 전 policy 로 확장 예정 (현재 Pi0, XVLA 만 지원)
- 우리 lerobot 0.5.2 기준 smolvla 에서 지원 여부 → `configuration_smolvla.py` 에 `compile_model` 만 있음, `gradient_checkpointing` 파라미터는 확인 안됨
- 대신 `--policy.dtype=bfloat16` 이 메모리 절감 직접 효과

### 6-2. Mixed Precision (BF16 vs FP16)

| 항목 | BF16 | FP16 |
|------|------|------|
| Dynamic range | FP32 동일 (넓음) | 좁음 (overflow 위험) |
| Precision | 낮음 | 높음 |
| 권장 | pretrain / finetune 표준 | RL 등 precision 민감 |
| SmolVLA 공식 | **bfloat16** (논문·모델카드) | — |
| DGX Spark (Blackwell) | BF16 natively 지원 | — |

**우리 적용**: `--policy.dtype=bfloat16` 추가 권장. 현재 `dtype` 미명시 → FP32 가능성. BF16 명시 시 메모리 절반 + 속도 향상 기대.

### 6-3. Batch Size + Gradient Accumulation

Gradient Accumulation 으로 작은 batch 유지하면서 effective batch 확보:
```bash
# batch_size=8 + grad_accum=8 → effective 64
--batch_size=8 --training.grad_accum_steps=8  # lerobot CLI 확인 필요
```
현재 우리 batch=16 은 image dataset 전환 후 안전 범위. UMA 메모리 여유 (128GB) 감안하면 전환 성공 후 32-64 까지 올릴 여지.

### 6-4. DataLoader 메모리 누수 회피 패턴

| 패턴 | 효과 | 적용 |
|------|------|------|
| `return_uint8=true` | IPC buffer 1/4 (float32 → uint8) | 우리 현재 적용 |
| `num_workers=2` | buffer 총량 ↓ | 우리 현재 적용 |
| `prefetch_factor=1` | 사전 적재 배치 ↓ | 우리 현재 적용 |
| `persistent_workers=False` | 단일 epoch 내 OOM 회피 효과 없음 | 우리 현재 적용 (무해) |
| image dataset | video decode 자체 제거 → leak 원인 소멸 | **진행 중 (가장 강력)** |

### 6-5. video backend 선택 (우리 환경 결론)

| backend | 우리 DGX 상태 | 메모리 영향 |
|---------|--------------|-----------|
| `pyav` (15.1.0) | ⚠️ 동작하나 OS-level leak (1.07GB/min) | 치명적 누수 |
| `torchcodec` (0.11.1) | ❌ ABI crash (첫 배치에서 RuntimeError) | 사용 불가 |
| `video_reader` (torchvision) | ❌ FFmpeg 6 호환 불가 | 사용 불가 |
| **image dataset** | ✅ video decode 없음 | **누수 없음** |

lerobot 공식 v0.6.0 로드맵: "torchcodec 전체 마이그레이션 탐색 중 (PyAV 교체) — video decoding 이 RAM spike 의심 원인으로 지목" → 우리 문제가 upstream 도 인식.

---

## §7 우리 환경 적용 권장 (leftarm_v2 + DGX Spark + LoRA)

### 7-1. 현재 셋업 vs 커뮤니티 권장 비교

| 항목 | 우리 현재 (2A) | 커뮤니티 권장 | 평가 | 우선도 |
|------|--------------|--------------|------|--------|
| base model | `lerobot/smolvla_base` | 동일 | ✅ 정합 | — |
| PEFT method | LoRA | LoRA (권장) | ✅ 정합 | — |
| target_modules | `all-linear` | default: q,v + proj / 확장: all-linear | ✅ 더 광범위, acceptable | — |
| LoRA rank | r=16 | r=16 (starting point) / r=32-64 (공식 예시, domain shift) | ✅ 출발점으로 적절, 2B 에서 r=32 시도 권장 | 중간 |
| LR | 1e-4 (preset) | LoRA 권장: 1e-3 / 실용 사례: 1e-4 | ⚠️ 공식 LoRA 권장보다 낮음, 실용 사례는 1e-4 성공 있음 | 중간 |
| batch_size | 16 | 64 (공식) / 44 (RTX3080Ti 한계) | ⚠️ UMA 여유 있어 전환 성공 후 증가 권장 (32-64) | 높음 |
| steps | 20,000 | 20,000 (finetune 기준) / 100,000 (sim benchmark) | ✅ 정합 (2A) — 2B 에서 40,000 고려 | — |
| precision | 미명시 (FP32 추정) | BF16 권장 (논문·모델카드) | ❌ BF16 명시 추가 권장 | 높음 |
| scheduler | cosine_decay_with_warmup (preset) | 동일 | ✅ 정합 | — |
| dataset | image (변환 중) | image 또는 video (H.264 권장) | ✅ image 전환이 우리 환경에서 최적 | — |
| dataset 크기 | 100ep (2A) | 50ep 최소 / 50ep per variation 권장 | ✅ 적절 (2 task × 50ep) | — |
| n_action_steps | inference 시 config.json 확인 필요 | 50 (필수 수동 변경) | ⚠️ Hub push 전 반드시 확인 | 높음 |
| gradient_checkpointing | 미적용 | 메모리 제약 시 권장 | 중립 (128GB UMA → 덜 긴급) | 낮음 |
| wandb monitoring | true | 권장 | ✅ 정합 | — |

### 7-2. 즉시 적용 권장 사항 (image dataset 전환 성공 후)

**[권장 1] BF16 명시 (높음, 즉시)**

`train_config.yaml` 또는 `run_train.py` 에 추가:
```bash
--policy.dtype=bfloat16
```
- 근거: SmolVLA 논문 + 모델카드 + 공식 docs 모두 bfloat16 명시. DGX Spark Blackwell BF16 native 지원.
- 효과: 메모리 ~절반, 속도 향상. 100ep LoRA fine-tune 에서 정확도 영향 없음.

**[권장 2] batch_size 증가 탐색 (높음, image dataset 성공 후)**

현재 batch=16. UMA 128GB 여유 + image dataset (메모리 안정) 전제:
- 목표: batch=32 또는 64 (공식 권장)
- 절차: image dataset 학습 첫 100 step → wandb `system/memory` peak 확인 → 여유 20GB+ 이면 batch ↑
- 효과: GPU 활용도 ↑, 수렴 안정성 ↑, step 당 처리 데이터 ↑

**[권장 3] num_workers 최적화 (중간, batch 안정 후)**

image dataset 전환 후 video decode 오버헤드 없으므로:
- `data_load_time` vs `step_time` wandb 관찰
- `data_load_time > 0.5 × step_time` → num_workers 4-8 로 증가 시도
- workers 증가 시 `prefetch_factor=2` 복원 가능 여부 테스트

**[권장 4] LoRA LR 탐색 (중간, 2B 에서)**

2A 결과 관찰 후:
- 2A 수렴 느림 (loss plateau) → lr=5e-4 또는 1e-3 시도 (공식 LoRA 권장 상한)
- 2A 수렴 정상 → 현 1e-4 유지 + rank 조정 (r=32)

**[권장 5] n_action_steps 확인 (높음, 체크포인트 배포 전)**

Orin smoke 추론 전 checkpoint 의 `config.json` 확인:
```bash
grep "n_action_steps" outputs/<run>/config.json
# 1이면 → 50으로 수동 변경 필수
```
- 근거: smolvla_base Hub model 의 config.json 는 n_action_steps=1 (커뮤니티 다수 함정)

**[권장 6] 2A wandb 학습 중 모니터링 체크리스트**

| 메트릭 | 기대값 | 이상 신호 |
|--------|--------|----------|
| `loss` | 0.5 이하로 하강 | 0.5 이상 plateau → LR / 데이터 점검 |
| `grad_norm` | 0.1-10 범위 | 급등 (>100) → LR 너무 높음 |
| `data_load_time` | < `step_time` | data >> step → workers 증가 |
| `system/memory` peak | < 100GB | > 110GB → batch ↓ 또는 workers ↓ |
| `system/gpu.utilization` | > 70% | < 50% → dataloader bottleneck |
| `step_time` variance | 낮음 | 큰 변동 → I/O 문제 또는 image decode 오류 |

### 7-3. 2B 시 권장 hyperparameter 범위

| 항목 | 2B 탐색 범위 | 판단 기준 |
|------|-------------|----------|
| LoRA rank | r=16 (유지) or r=32 | 2A loss curve 포화 → r=32 |
| LR | 1e-4 (유지) or 5e-4 | 2A 수렴 느리면 ↑ |
| batch_size | 32 or 64 | UMA headroom (2A wandb) |
| steps | 40,000 (200ep × ~600fr ÷ batch → ~5 epoch) | 2A 수렴 확인 후 |
| expert mode | LoRA (유지) or Full FT (B1) | 2A 성능 약하면 B1 시도 |
| precision | BF16 | 즉시 적용 |

### 7-4. 우리 현 셋업 강점 / 약점 요약

**강점**:
- lerobot 0.5.2 + smolvla 공식 경로 (PEFT 통합) 사용 → 호환성 보장
- LoRA A2 (VLM + expert 양쪽) → 단일 시연장 환경 적응에 적합
- dataset_return_uint8 + 낮은 workers/prefetch → 메모리 보수적 (image dataset 에서도 유효)
- rename_map (top→camera1, wrist→camera2) → smolvla 카메라 키 정합 처리
- image dataset 변환 (convert_to_image.py ffmpeg subprocess) → video decode leak 원인 소멸
- wandb + save_freq=1000 → 학습 진행 추적 + 중간 ckpt 확보

**약점**:
- BF16 미명시 → FP32 가능성 (메모리/속도 미최적화)
- batch=16 → 공식 권장(64) 대비 낮음 (GPU 활용도 낮을 수 있음)
- LR=1e-4 → LoRA 기준 공식 권장(1e-3) 보다 낮음
- n_action_steps 배포 전 확인 프로세스 미정의
- 100ep 멀티태스크 → VLA 기준 소량 (고성능 목표 시 200ep 필요, 2B 에서 해소)

---

## §8 출처 (Sources)

1. [SmolVLA Official Documentation - HuggingFace](https://huggingface.co/docs/lerobot/en/smolvla)
2. [SmolVLA Blog Post - HuggingFace](https://huggingface.co/blog/smolvla)
3. [lerobot/smolvla_base Model Card](https://huggingface.co/lerobot/smolvla_base)
4. [Parameter Efficient Fine-Tuning (PEFT) - lerobot docs](https://huggingface.co/docs/lerobot/en/peft_training)
5. [Multi-GPU Training - lerobot docs](https://huggingface.co/docs/lerobot/en/multi_gpu_training)
6. [SmolVLA Paper: arxiv 2506.01844](https://arxiv.org/html/2506.01844v1)
7. [Fine-Tuning SmolVLA for New Environments - Xavier O'Keefe (Medium)](https://medium.com/correll-lab/fine-tuning-smolvla-for-new-environments-code-included-af266c56d632)
8. [Fine-tuning SmolVLA for Cube Pick-and-Place on SO-101 - ggando.com](https://ggando.com/blog/smolvla-so101/)
9. [SmolVLA: Efficient Vision Language Action Model - LearnOpenCV](https://learnopencv.com/smolvla-lerobot-vision-language-action-model/)
10. [Train SmolVLA - phospho.ai](https://docs.phospho.ai/learn/train-smolvla)
11. [SmolVLA fine-tuning - EmbodiFlow](https://io-ai.tech/platform/en/guides/Pipeline/LeRobot/SmolVLA/)
12. [GitHub: std::bad_alloc DataLoader issue #2209](https://github.com/huggingface/lerobot/issues/2209)
13. [GitHub: Dataloader slow for SmolVLA issue #1488](https://github.com/huggingface/lerobot/issues/1488)
14. [GitHub: Slow video decoding issue #1623](https://github.com/huggingface/lerobot/issues/1623)
15. [GitHub: Release 0.6.0 roadmap issue #3134](https://github.com/huggingface/lerobot/issues/3134)
16. [GitHub: LIBERO benchmark training configs issue #3287](https://github.com/huggingface/lerobot/issues/3287)
17. [GitHub: camera setup for SO101 issue #1763](https://github.com/huggingface/lerobot/issues/1763)
18. [GitHub: smolvla training bugs on 3090 issue #1234](https://github.com/huggingface/lerobot/issues/1234)
19. [DGX Spark Setup Guide - natolambert](https://github.com/natolambert/dgx-spark-setup)
20. [LoRA Fine-Tuning of VLA for Robot Control - arxiv 2512.11921](https://arxiv.org/html/2512.11921v1)
21. [PyAV Memory Leak Issue #1117](https://github.com/PyAV-Org/PyAV/issues/1117)
22. [LeRobotDataset v3.0 documentation](https://huggingface.co/docs/lerobot/lerobot-dataset-v3)
23. [Clarifications on fine-tuning - GitHub issue #2259](https://github.com/huggingface/lerobot/issues/2259)
