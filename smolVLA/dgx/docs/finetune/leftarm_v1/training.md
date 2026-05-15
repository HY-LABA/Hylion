# SmolVLA 학습 가이드 (DGX, leftarm_v1)

> **대상 데이터셋**: `${HF_USER}/leftarm_v1` (40 episodes, "Pick up the doll and reach forward")
> **베이스 모델**: `lerobot/smolvla_base` (450M params)
> **노드**: DGX Spark (단일 노드, 데이터 수집 + 학습)
> **작성**: 2026-05-11
> **자매 문서**: [data_collection.md](data_collection.md) — 데이터 수집 단계
> **참조**: [smolvla.mdx](../../docs/reference/lerobot/docs/source/smolvla.mdx) (공식 학습 가이드), `~/smolvla/dgx/scripts/smoke_test.sh`, `~/smolvla/dgx/scripts/preflight_check.sh`

---

## ⚠ Walking RL 트랙 보호 — 가동 여부에 따라 자원 정책 분기

같은 DGX 에서 Walking RL 학습이 가동 중인지 여부로 자원 정책이 달라집니다.

| Walking RL 상태 | SmolVLA 학습 자원 정책 |
|---|---|
| **가동 중** | 잔여 자원만 사용 — batch ↓, num_workers ↓, S1 모드 (action expert 만) 권장. preflight `s1` 통과 필수 |
| **미가동** | **DGX 전체 자원 풀 사용 가능** — batch ↑, num_workers ↑, S2 / S3 (vision encoder / VLM) 모드까지 고려 가능 |

매 학습 시작 전 [preflight_check.sh](../scripts/preflight_check.sh) 통과 필수 — Walking RL 가동 시 절대 우회 X.

**Walking RL 가동 여부 확인**:

```bash
# Walking RL 프로세스 검색 (env_isaaclab venv 사용)
ps aux | grep -iE "env_isaaclab|walking_rl|isaaclab" | grep -v grep | head -5
# → 결과 있음: 가동 중 → 보수적 자원 정책
# → 결과 없음: 미가동 → 풀 사용 가능

# GPU 점유 확인 (보조 검증)
nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv
# → env_isaaclab/python 프로세스 보이면 가동 중
```

---

## 0) 전제 조건

### 0-1. 환경 요건

- DGX Spark, venv `~/smolvla/dgx/.arm_finetune` 활성화
- `HF_HOME=/home/laba/smolvla/.hf_cache` ([setup_finetune_env.sh](../scripts/setup_finetune_env.sh) 가 적용)
- 데이터 수집 완료 ([data_collection.md](data_collection.md) §5 까지) — `${HF_USER}/leftarm_v1` 가 로컬 캐시 + HF Hub 양쪽에 존재
- HuggingFace 로그인 (`hf auth whoami`)
- Walking RL 동시 가동 가능 (다만 GPU 메모리 / RAM 점유 상황 확인 필요)

### 0-2. venv 활성화 + HF_USER

```bash
source ~/smolvla/dgx/.arm_finetune/bin/activate
export HF_USER=BaboGaeguri

# 데이터셋이 로컬에 있나 확인 (없으면 자동 다운로드되지만 시간 절약 위해 미리 확인)
jq '{total_episodes, total_frames}' \
  /home/laba/smolvla/.hf_cache/lerobot/${HF_USER}/leftarm_v1/meta/info.json
# → {"total_episodes": 40, "total_frames": 21352}
```

### 0-3. (선택) wandb 설정

학습 메트릭 시각화 원하면:

```bash
pip install wandb     # 이미 설치돼 있을 가능성 ↑
wandb login           # API 키 입력 (https://wandb.ai/authorize)
```

미사용 시 `--wandb.enable=false` 로 비활성화.

### 0-4. preflight 점검 + 학습 stage 매핑

preflight 시나리오는 §2-4 의 학습 stage (S1/S2/S3) 와 매칭됩니다:

| 시나리오 | 필요 RAM | Stage 매핑 | 용도 |
|---|---|---|---|
| `smoke` | 20 GB | — | 1 step 검증 (§1) |
| `s1` | 35 GB | **Stage 1** (action expert 만) | 본 가이드 exploratory 표준 — 데이터 적을 때 |
| `s3` | 65 GB | **Stage 3** (VLM 풀 학습) | Walking RL 미가동 + 200+ episodes 시 |
| `lora` | 28 GB | LoRA fallback | 메모리 부족 시 (S1 도 안 들어갈 때) |

> S2 (vision encoder 학습) 는 별도 시나리오가 없으나 메모리 추정 ~50 GB. `s1` 통과한 시스템이면 대부분 OK, 마진 확인 후 진행.

```bash
# 사용자 권장 (현재 케이스 LoRA all-linear) — s1 (~35GB) 통과면 충분
bash ~/smolvla/dgx/scripts/preflight_check.sh s1

# S3 full FT 비교 학습 시 → s3 (~65GB)
# bash ~/smolvla/dgx/scripts/preflight_check.sh s3
```

> LoRA all-linear 의 실제 메모리는 `lora` 시나리오 (28GB) 보다 약간 큼 (~35-40GB) — vision encoder + VLM 의 frozen forward 가 메모리 차지하기 때문. `s1` (35GB + 10GB margin = 45GB 통과 요구) 이 안전.

→ HF_HOME 격리 / venv 활성화 / 가용 RAM / Walking RL 보호 정책 / Ollama 등 점검. **FAIL 떨어지면 학습 시작 X** — 메시지 따라 조치 후 재실행.

### 0-5. (Walking RL 미가동 시) 자원 풀 사용 가이드

`ps aux | grep -i env_isaaclab` 가 비어있고 `nvidia-smi` 에 다른 사용자 프로세스 없는 상태라면 DGX 자원을 풀로 쓸 수 있습니다. 권장 인자 (현재 사용자 케이스 — Walking RL 미가동):

| 인자 | Walking RL 가동 시 (보수) | **Walking RL 미가동 시 (풀 사용, 권장)** |
|---|---|---|
| `--batch_size` | `8` | **`32`** (또는 GPU 메모리 마진 보면서 64까지) |
| `--num_workers` | `4` | **`8`** (CPU 코어 20개 활용) |
| `--policy.compile_model` | `false` (기본) | **`true`** 시도 가능 (torch.compile, 초기 컴파일 ~수분 후 step time 단축) |
| preflight 시나리오 | `s1` | `s1` ~ `s3` 자유 선택 (학습 stage 에 따라) |
| 학습 stage (§2-4) | S1 | S1 / S2 / S3 자유 선택 (데이터 분량 기준) |

⚠️ Walking RL 트랙이 **언제든 학습 재개될 수 있으므로**, 학습 진행 중 주기적으로 (10~15분마다) `ps aux | grep env_isaaclab` 체크. 새 Walking RL 프로세스 발견 시 즉시 본 학습 종료 + batch 축소 후 재시작.

---

## 1) Smoke test — lerobot-train CLI 검증 (최초 1회)

설치 / GPU / 데이터셋 로딩 검증용. **1 step** 만 돌립니다. 기존 [smoke_test.sh](../scripts/smoke_test.sh) 는 lerobot 의 `svla_so100_pickplace` 공식 데이터셋을 쓰지만, 본 가이드에선 우리 데이터셋으로 변형해서 빠르게 한 번 통과시킵니다.

```bash
RUN_ID="smoke_$(date +%Y-%m-%d_%H-%M-%S)"
OUTPUT_DIR="${HOME}/smolvla/dgx/outputs/${RUN_ID}"

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id="${HF_USER}/leftarm_v1" \
  --batch_size=8 \
  --steps=1 \
  --log_freq=1 \
  --num_workers=4 \
  --save_checkpoint=false \
  --output_dir="${OUTPUT_DIR}" \
  --job_name="${RUN_ID}" \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --rename_map='{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
  --wandb.enable=false
```

> **`rename_map` 의 의미**: 우리 데이터셋은 `observation.images.top` / `observation.images.wrist` 키를 쓰지만, `smolvla_base` 는 학습 시 `camera1` / `camera2` 라는 일반화된 카메라 키를 가정합니다. 이 매핑이 없으면 학습 시작 시 key mismatch 에러 발생.

성공 시:
- `loss: ...` 한 줄 출력
- `${OUTPUT_DIR}/` 에 1 step 학습 로그 (checkpoint 미저장)
- 종료 코드 0

실패 시 — §7 트러블슈팅 참조.

---

## 2) Exploratory 학습 — 40 episodes 로 빠르게 검증 (권장 첫 시도)

본격적 20000 steps 학습 전에, **5000 steps** 로 짧게 돌려서 ① policy 가 task 핵심 동작을 학습하는지 ② vision encoder 적응이 안정적으로 진행되는지 빠르게 검증합니다. 학습 시간 약 1시간 예상 (DGX Spark GB10, batch=16, **LoRA all-linear**).

> **현재 사용자 케이스 권장 조합** (Walking RL 미가동 + single deployment 환경 + 카메라 시점 / 인형 외관 특화 적응 필요 + 오버피팅 허용 + 40 episodes 소량):
> - **LoRA all-linear (r=16)** — vision encoder + VLM + expert 모든 linear 에 LoRA. S3 full FT 의 효율적 버전
> - `batch_size=16` (LoRA base 가 frozen 이라 optimizer state ↓, 메모리 여유. 첫 100 step 후 24~32 시도 가능)
> - `num_workers=8` (Walking RL 미가동이라 풀 사용)
> - `save_freq=250` (LoRA 라도 학습 안정성 확인 위해 자주)
> - **wandb 활성화** — 실시간 loss / grad_norm 추이 모니터 필수

### LoRA 를 선택한 이유

| 옵션 | trainable params | 메모리 | 학습 시간 | 위험 | 우리 케이스 적합성 |
|---|---|---|---|---|---|
| S1 (full FT) | ~50M (expert만) | ~35GB | ~1h | 환경 적응 X | ❌ vision encoder 적응 안 됨 |
| S3 (full FT) | ~500M (전체) | ~65GB | ~2h | catastrophic forgetting ↑↑ | ⚠️ 효과 대비 비용 ↑ |
| **LoRA all-linear (r=16)** ⭐ | **~10-20M (adapter)** | **~35-40GB** | **~1h** | **forgetting 위험 ↓↓** | ✅ vision 적응 + 효율 |
| LoRA default (action expert만) | ~수M | ~28GB | ~1h | 환경 적응 X | ❌ default 가 expert 만 (커스텀 필요) |

[pretrained.py:302-304](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L302-L304) 의 동작:
- PEFT 활성화 시 base model 전체 자동 frozen
- `target_modules=all-linear` → 모든 `nn.Linear` 에 LoRA adapter (A=r×in, B=out×r)
- 학습되는 건 LoRA adapter 만 → forgetting 위험 ↓, 메모리 ↓, but vision / text / action 표현은 모두 우리 데이터로 조정 가능

### 2-1. 학습 명령 (foreground, DGX 직접 실행 기준)

```bash
RUN_ID="leftarm_v1_explore_$(date +%Y-%m-%d_%H-%M-%S)"
OUTPUT_DIR="${HOME}/smolvla/dgx/outputs/${RUN_ID}"
# lerobot-train 이 OUTPUT_DIR 을 자동 생성. 사전 mkdir 하면 FileExistsError

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id="${HF_USER}/leftarm_v1" \
  --batch_size=16 \
  --steps=5000 \
  --log_freq=50 \
  --save_freq=250 \
  --num_workers=8 \
  --output_dir="${OUTPUT_DIR}" \
  --job_name="${RUN_ID}" \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --rename_map='{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
  --wandb.enable=true \
  --wandb.project=leftarm_v1 \
  --wandb.entity="${HF_USER}" \
  --peft.method_type=LORA \
  --peft.target_modules=all-linear \
  --peft.r=16
```

> **PEFT 활성화 시 자동 동작**: `freeze_vision_encoder` / `train_expert_only` 인자는 무시되고 base model 전체가 자동 frozen. 따라서 stage 인자 제거 (§2-4 LoRA 절 참조).

> **batch_size=16 인 이유**: LoRA 라 메모리 여유 있지만 안전 마진. 첫 100 step 의 GPU 메모리 보고 여유 있으면 24~32 로 증가 가능. nvidia-smi 로 모니터.

### 2-2. (선택) tmux 세션으로 detach — 자리 비울 때만

`Ctrl+C` 누를 일이 생기거나 (실수 / 정전 / 잠금화면) 터미널 닫고 싶을 때 보호 장치. SSH 가 아니어도 tmux 는 가치 있습니다 (사용자가 잠시 자리 비우는 동안에도 학습 보존).

```bash
# 1. tmux 세션 시작 (이름: train)
tmux new -s train

# 2. tmux 안에서 §2-1 명령 실행

# 3. detach: Ctrl+B, D (학습은 계속됨)

# 4. 나중에 다시 보기:
tmux attach -t train

# 5. tmux 안에서 종료:
exit
# 또는 attach 후 학습 종료(Ctrl+C) → 세션 종료(Ctrl+D)
```

대안 — 그냥 백그라운드 + 로그 파일 (tmux 익숙하지 않을 때):

```bash
# 로그는 OUTPUT_DIR 의 형제 위치에 (lerobot 이 OUTPUT_DIR 자동 생성하므로 그 안에는 못 씀)
LOG_FILE="${HOME}/smolvla/dgx/outputs/${RUN_ID}_train.log"

# §2-1 명령 끝에 아래 redirect 추가
... (§2-1 명령) ... > "${LOG_FILE}" 2>&1 &
echo "Training PID: $!"
echo "Log: ${LOG_FILE}"
# 진행 확인:
tail -f "${LOG_FILE}"
```

> ⚠️ **`mkdir -p "${OUTPUT_DIR}"` 하지 말 것** — lerobot-train 은 output_dir 이 이미 존재하면 `FileExistsError` (resume=False 모드에서 덮어쓰기 방지). 로그 파일도 OUTPUT_DIR **외부** 에 둬야 합니다.

### 2-3. wandb — 학습 진행 시각화 (권장 표준)

`wandb.enable=true` 가 §2-1 명령에 기본 포함. 첫 실행 시 wandb 로그인 필요:

```bash
# (0-3 단계에서 안 했다면 지금)
wandb login    # API 키 입력
```

학습 시작 시 콘솔에 표시되는 URL 따라 접속:
```
wandb: 🚀 View run at https://wandb.ai/${HF_USER}/leftarm_v1/runs/<run_id>
```

거기서 실시간 확인 가능:
- **train/loss**: step 별 loss 곡선 (smooth)
- **train/grad_norm**: 학습 안정성
- **train/lr**: cosine decay 스케줄
- **train/step_s**: 학습 속도 (DGX 자원 변동 모니터)
- **system metrics**: GPU util, memory 자동 수집

> wandb 미사용 시: `--wandb.enable=false` 로 바꾸고, 터미널 출력 또는 `tail -f train.log` 로 확인. wandb 의 시각화 / 비교 기능을 잃지만 학습 자체에는 영향 없음. **DGX 인터넷 차단 환경이라면 wandb 미사용 필수**.

### 2-4. 학습 깊이 선택 — Stage 1 / 2 / 3 (코드 기반 정확한 정의)

SmolVLA 의 **두 플래그**가 어떻게 동작하는지 [smolvlm_with_expert.py:150-180](../../docs/reference/lerobot/src/lerobot/policies/smolvla/smolvlm_with_expert.py#L150-L180) 의 `set_requires_grad()` 를 보면:

```python
if self.freeze_vision_encoder:
    # vision_model 의 requires_grad = False
if self.train_expert_only:
    # ★ VLM 전체 (vision encoder + text decoder) 의 requires_grad = False
    # → freeze_vision_encoder 설정이 무시됨
```

**핵심**: `train_expert_only=True` 면 VLM 전체가 frozen 되어 `freeze_vision_encoder` 설정이 무시됩니다. Vision encoder 를 학습시키려면 반드시 `train_expert_only=False` 필요.

| Stage | `freeze_vision_encoder` | `train_expert_only` | **실제 학습 대상** | 메모리 | preflight |
|---|---|---|---|---|---|
| **S1 (기본)** | (무시됨) | `true` | Action expert + state_proj | ~35 GB | `s1` |
| **S2** | `true` | **`false`** | + VLM **text decoder 대부분** (vision encoder 는 frozen 유지) | ~50 GB | `s1` ~ `s3` |
| **S3 (풀)** | **`false`** | **`false`** | + VLM 전체 (vision encoder 포함) | ~65 GB | `s3` |

> S1 은 `freeze_vision_encoder=true/false` 둘 다 동일 결과. `train_expert_only=true` 가 우선 적용되어 vision encoder 도 frozen 됩니다.

### 단계별 학습 대상 (직관적 비유)

| Stage | 무엇이 추가 학습되나 | 직관적 비유 |
|---|---|---|
| **S1** | Action expert + state proj | "이미지·텍스트 이해는 사전학습 그대로, **행동 출력만** 우리 task 에 fit" |
| **S2** | + VLM text decoder (대부분 layers) | + "**명령어 임베딩** 과 action expert 사이의 cross-attention 가중치 fine-tune" |
| **S3** | + Vision encoder (SigLIP) | + "내 **카메라가 보는 화면** 의 시각 표현도 우리 환경에 맞게 재학습" |

### 사용자 케이스 (single instruction) 별 stage 의미

| 학습 목표 | 필요한 stage | 우리 케이스에서 효과 |
|---|---|---|
| Task 의 action mapping fit | S1 | ✅ 가장 기본. 빠름, 안전, 환경 적응 X |
| Instruction 의미 fine-tune | S2 | ⚠️ Single instruction 이라 학습 시그널 거의 없음. 효과 의문 |
| **카메라 시점 / 조명 / 물체 외관 적응 (vision encoder)** | **S3 만 가능** | ✅ Single deployment 환경에서 가장 의미 있는 학습 효과 |

→ "환경 적응" 목적이면 **S3 만이 진짜 vision encoder 를 학습**시킵니다. S2 는 사용자 케이스에서 효과가 적어 잘 안 씀.

### 권장 (현재 사용자 케이스: 40 episodes + single deployment 환경 적응 목표)

§2-1 명령은 **S3** 인자로 설정 (`freeze_vision_encoder=false`, `train_expert_only=false`). 다른 stage 로 변경 시:

**S1 (가장 보수적, baseline 용):**
```bash
  --policy.train_expert_only=true
  # freeze_vision_encoder 줄은 제거 가능 (무시됨)
```

**S2 (VLM text decoder 만, 일반적으로 잘 안 씀):**
```bash
  --policy.freeze_vision_encoder=true \
  --policy.train_expert_only=false
```

**S3 (현재 §2-1, 권장):**
```bash
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false
```

### 2-4-1. LoRA — 효율적 fine-tuning (현재 권장)

[pretrained.py:270-317](../../docs/reference/lerobot/src/lerobot/policies/pretrained.py#L270-L317) 의 `wrap_with_peft()`. 동작 방식:

1. `--peft.method_type=LORA` 지정 시 lerobot 가 PEFT (HuggingFace 라이브러리) 적용
2. **모든 base model parameters 자동 frozen** (위의 stage 플래그 무시)
3. `target_modules` 에 해당하는 layers 에 LoRA adapter (rank r 의 A, B 행렬) 추가
4. 학습되는 건 LoRA adapter 만 → trainable params 가 base 의 ~1~5%

### LoRA target_modules 옵션

| 값 | 적용 범위 | trainable params | 우리 케이스 적합성 |
|---|---|---|---|
| (lerobot default for SmolVLA) | Action expert 의 `q/v_proj` + state/action projections | ~수M | ❌ vision encoder 적응 X — S1 의 LoRA 버전일 뿐 |
| `all-linear` ⭐ | 모든 `nn.Linear` (vision + VLM + expert) | ~10-20M | ✅ vision encoder 까지 LoRA — 우리 목적 |
| 커스텀 regex | 사용자 지정 | 가변 | 정밀 제어 원할 때 |

### LoRA rank (`--peft.r`) 선택

| r | trainable params 비율 | 효과 |
|---|---|---|
| `4` | 가장 가벼움 (~1% base) | 표현 여력 제한적, underfitting 가능 |
| `8` | 가벼움 | 일반적인 LoRA 첫 시도 |
| **`16` (default, 권장)** | 균형 | **충분한 표현 여력 + 여전히 가벼움 — 우리 케이스 sweet spot** |
| `32` | 두꺼움 | 추가 표현 여력, 메모리 약간 ↑ |
| `64+` | 매우 두꺼움 | full FT 에 근접 → LoRA 의 의미 ↓ |

### S1 / S2 / S3 (full FT) — baseline 비교용

§2-1 명령은 LoRA all-linear. full FT 와 비교하려면 PEFT 인자 제거 + stage 플래그 적용:

**S1 (action expert 만 full FT — baseline):**
```bash
# §2-1 명령에서 --peft.* 세 줄 제거 + 아래 추가
  --policy.train_expert_only=true
```

**S3 (전체 full FT — 메모리·시간 워스트):**
```bash
# §2-1 명령에서 --peft.* 세 줄 제거 + 아래 추가
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false
```

### 권장 진행 순서

```
LoRA all-linear r=16 (5000 steps, 40 ep, batch=16) → wandb 로 loss / grad_norm 안정성 모니터
  │
  ├── 안정적 수렴 → §5-2 inference 검증
  │    ├── 성공률 ≥ 60% → 더 많은 데이터 (60~100 ep) → 동일 설정 재학습
  │    └── 성공률 < 60% → 데이터 / instruction 재검토. r=32 로 표현 여력 ↑ 시도
  │
  └── 불안정 (loss NaN, grad_norm 폭주) → r=8 로 축소 또는 lr ↓ (`optimizer.lr=5e-5`)
```

### ⚠️ LoRA 의 위험과 mitigation

| 위험 | 증상 | mitigation |
|---|---|---|
| 표현 여력 부족 (underfitting) | loss 가 일정 수준에서 안 떨어짐 (plateau) | `--peft.r=32` 로 rank ↑ 또는 full FT (S3) 로 전환 |
| 메모리 OOM (드물지만) | `CUDA out of memory` | batch_size ↓ (16→8). LoRA 라 base 가 frozen 이라 OOM 흔치 않음 |
| 학습 발산 (NaN) | Loss = NaN | `optimizer.lr=5e-5` (절반) |
| Catastrophic forgetting | (LoRA 라 위험 ↓↓ — base 가 frozen 이라 사전학습 표현 보존됨) | LoRA 의 본질적 이점 |

---

## 3) 학습 모니터링

### 3-1. 학습 로그 확인

```bash
tail -f ${OUTPUT_DIR}/train.log
```

기대 출력 패턴 (`log_freq=50` 기준):

```
INFO step=50/5000 ... loss=2.345 ... grad_norm=0.78 ... lr=1e-4
INFO step=100/5000 ... loss=1.892 ... grad_norm=0.62 ... lr=1e-4
...
```

핵심 관찰 포인트:
- **loss 감소 추세**: 100 step 후 초기값의 60~80% 까지 떨어지면 정상. flat 하면 데이터 / 모델 미스매치 의심
- **grad_norm**: 1.0 미만 안정적. 폭주 (10+) 시 학습 발산 위험
- **step/s**: DGX Spark 에서 약 1~2 step/s 예상 (batch=8, 두 카메라). 0.1 step/s 이하면 data loading 병목

### 3-2. GPU / 메모리 모니터링 (별도 터미널)

```bash
# 1초 간격 GPU / 메모리 확인
watch -n 1 'nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader; echo; free -h | grep -E "Mem|Swap"'
```

기대값:
- GPU util: 70~95% (학습 활성 시)
- GPU/UMA 메모리: 약 30~40 GB (smolvla_base + batch=8)
- 시스템 RAM: smoke test 결과 + α (Walking RL 사용량 포함)

⚠️ **메모리 90% 초과 시 즉시 중단** — Walking RL OOM 위험. `Ctrl+C` 또는 `kill ${PID}` 로 학습 종료 후 batch_size 축소.

### 3-3. Walking RL 상태 확인

```bash
# Walking RL 프로세스 (참고: 절대 kill X)
ps aux | grep -i "env_isaaclab\|walking_rl" | grep -v grep | head -5
```

Walking RL 학습이 우리 학습 때문에 느려지는 징후 (예: training step time 이 평소 대비 2배 이상) 있으면 우리 batch_size 를 줄여서 양보.

---

## 4) 결과 위치

```
${OUTPUT_DIR}/
├── train.log                          # nohup 사용 시
├── checkpoints/
│   ├── 000500/                        # save_freq=500 마다 한 번씩 (5000/500 = 10개)
│   │   ├── pretrained_model/
│   │   ├── training_state/
│   │   └── ...
│   ├── 001000/
│   ├── ...
│   └── last/                          # 마지막 step 의 symlink
└── (wandb on 시 wandb/)
```

| 위치 | 내용 |
|---|---|
| `checkpoints/<step>/pretrained_model/` | inference 에 사용 가능한 모델 weights |
| `checkpoints/last/` | 학습 종료 시점의 latest checkpoint 로의 symlink |
| `checkpoints/<step>/training_state/` | optimizer state, RNG, step counter (resume 용) |

---

## 5) 결과 해석 / 추가 데이터 수집 결정

5000 steps 학습 종료 후 다음을 판단:

### 5-1. Loss 추세

| loss 패턴 | 해석 | 다음 행동 |
|---|---|---|
| 초기값 → 30% 수준으로 수렴, 마지막 500 step 동안 plateau | 데이터로 학습 가능한 만큼 학습. 정상 | inference 검증 (§5-2) |
| 초기값 → 50% 정도, 여전히 감소 중 | 학습 부족. 더 돌릴 가치 ↑ | 같은 명령에 `--resume=true` 추가하고 `--steps=10000` 으로 연장 |
| loss 가 떨어지지 않음 / NaN | 데이터 / 모델 미스매치, 학습률 / 배치 문제 | §7 트러블슈팅 |

### 5-2. (선택) 실기 inference 로 검증

[smolvla.mdx](../../docs/reference/lerobot/docs/source/smolvla.mdx) 의 평가 패턴 따라, follower + 두 카메라 연결 상태에서:

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --robot.cameras="{
    top: {type: opencv, index_or_path: ${CAMERA_TOP_INDEX}, width: 480, height: 640, fps: 30, color_mode: rgb, fourcc: MJPG, rotation: -90},
    wrist: {type: opencv, index_or_path: ${CAMERA_WRIST_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG}
  }" \
  --dataset.repo_id="${HF_USER}/leftarm_v1_eval_$(date +%Y%m%d)" \
  --dataset.single_task="Pick up the doll and reach forward" \
  --dataset.num_episodes=5 \
  --dataset.fps=30 \
  --dataset.episode_time_s=30 \
  --dataset.push_to_hub=false \
  --policy.path="${OUTPUT_DIR}/checkpoints/last/pretrained_model" \
  --display_data=true \
  --play_sounds=true
```

→ doll 을 시작 위치에 놓고 policy 가 추론한 action 으로 follower 가 동작. **policy 가 doll 을 잡고 앞으로 뻗는 동작을 일관되게 수행하면 성공**. 5 episodes 중 3개 이상 성공이면 데이터 / 학습 모두 합리적.

⚠️ inference 시점에도 모터 overload 위험 — episode 시작 전 follower 자세 자연스럽게 풀어두고, 그리퍼 휴식 충분히 후 시작.

### 5-3. 다음 데이터 수집 차수 결정

| inference 결과 | 권장 다음 단계 |
|---|---|
| 5/5 성공 (완벽) | 데이터 충분 가능성 ↑. 추가 수집 보류, 학습 steps 만 증가 (10000~20000) 후 재평가 |
| 3-4/5 성공 (일관성 부족) | **추가 데이터 수집 권장**. 60 / 80 / 100 까지 가면서 다양성 확보. [data_collection.md §5-2](data_collection.md#5-2-2n-차--resume-누적-episodes-증가) 참조 |
| 0-2/5 성공 (학습 부족 또는 데이터 문제) | 우선 영상 검토 (시연 일관성 / instruction 적합성). 데이터 패턴 자체에 문제 있으면 dataset 재시작. instruction 의미 명확하지 않으면 wording 조정 |
| policy 가 무작위 / 안전하지 않은 동작 | **즉시 중단**. 학습 / 데이터 둘 다 재검토. inference 시 follower 동작 범위 사전 제한 검토 |

---

## 6) 인자 결정 근거 (DGX Spark + 40 episodes exploratory + LoRA all-linear + Walking RL 미가동)

§2-1 명령 기준. Full FT (S1 / S3) 와 비교 컬럼 별도.

| 인자 | 값 (현재 권장 LoRA) | S1 full FT | S3 full FT | 근거 |
|---|---|---|---|---|
| `policy.path=lerobot/smolvla_base` | 450M 사전학습 모델 | (동일) | (동일) | smolvla.mdx 표준. SO-100/101 데이터로 학습된 base 가 가장 빠른 수렴 |
| `batch_size` | **`16`** | `32` | `16` | LoRA 라 메모리 여유 있으나 안전 마진. 첫 100 step 모니터 후 ↑ 가능 |
| `steps=5000` | exploratory | (동일) | (동일) | 공식 20000 의 1/4. 40 episodes 면 sample efficiency 한계 |
| `log_freq=50` | 50 step 로그 | (동일) | (동일) | 50 step 마다 wandb / 콘솔에 메트릭 |
| `save_freq` | **`250`** | `500` | `250` | 학습 안정성 확인 위해 자주. 발산 시 가까운 체크포인트로 복귀 가능 |
| `num_workers` | **`8`** | `8` | `8` | DGX Grace 20-core. Walking RL 미가동이라 풀 사용. 가동 시는 4로 |
| `save_checkpoint=false` (smoke 만) | 1 step 검증 시 디스크 낭비 X | (동일) | (동일) | 본 학습 (§2) 에선 기본값 (`true`) 사용 |
| `policy.device=cuda` | DGX GB10 | (동일) | (동일) | UMA 메모리 구조 — GPU 메모리는 시스템 RAM 공유 |
| `policy.push_to_hub=false` | exploratory 단계 | (동일) | (동일) | base 모델 + 우리 데이터로 fine-tune 한 모델을 Hub 에 매번 푸시할 필요 X |
| **`peft.method_type=LORA`** | ★ LoRA 활성화 | (제거) | (제거) | PEFT 적용 — base 자동 frozen, adapter 만 학습 |
| **`peft.target_modules=all-linear`** | ★ 모든 linear | (제거) | (제거) | vision + VLM + expert 모두 LoRA. 우리 케이스 핵심 |
| **`peft.r=16`** | ★ rank 16 | (제거) | (제거) | 표현 여력 + 효율 균형. underfitting 시 32 시도 |
| `policy.freeze_vision_encoder` | (제거 — LoRA 가 우선) | (무시됨) | `false` | LoRA 사용 시 PEFT 가 base 전체 frozen 자동 처리 |
| `policy.train_expert_only` | (제거 — LoRA 가 우선) | `true` | `false` | (동일) |
| `rename_map=...` | top→camera1, wrist→camera2 | (동일) | (동일) | smolvla_base 의 expected key 와 매핑. **꼭 필요** |
| `wandb.enable=true` | 표준 권장 | (동일) | (동일) | DGX 직접 실행이라도 실시간 곡선 / 비교. 미사용 시 false 가능 |
| `wandb.project=leftarm_v1` | dataset 이름과 동일 | (동일) | (동일) | run 들을 dataset 기준으로 그룹핑 (LoRA vs S1 baseline 비교 시) |
| `policy.compile_model` | `false` (기본) | (동일) | (동일) | torch.compile. exploratory 에서는 디버깅성 우선이라 false |
| (선택) `optimizer.lr=5e-5` | 발산 시만 | — | — | 기본 lr=1e-4 가 발산 위험 시. NaN / 폭주 조짐 시 절반으로 |

---

## 7) 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `lerobot-train: command not found` | venv 미활성 → `source ~/smolvla/dgx/.arm_finetune/bin/activate` |
| `Key 'observation.images.camera1' not found` | `rename_map` 누락. §2-1 명령의 `--rename_map=...` 한 줄 추가 필수 |
| `CUDA out of memory` | `batch_size` 축소 (8→4→2). 그래도 부족하면 LoRA fallback 검토 (`policy.lora.enable=true`, 본 가이드 범위 외) |
| `RAM available < required` | Walking RL 외에 무거운 프로세스 (Jupyter, Ollama, 다른 학습) kill / 종료. 본인 프로세스만 정리 — 타인 프로세스 절대 X |
| `dataset features mismatch` | `rename_map` 의 키가 데이터셋의 실제 키와 일치 안 함. `jq '.features | keys' ~/.../leftarm_v1/meta/info.json` 으로 확인 |
| 학습 중 OOM | preflight 통과해도 학습 진행 중 메모리 누수 가능. `--num_workers=2` 로 줄이거나 batch 축소 |
| Loss = NaN | 학습률 너무 높거나 데이터 이상치. `--optimizer.lr=5e-5` 로 절반 시도. 또는 데이터셋 stats.json 확인 |
| step/s 가 0.5 미만 | data loading 병목. `num_workers` 증가 시도 (단 Walking RL 양보 고려 후) |
| 학습이 중간에 종료 (SIGKILL) | OOM killer 발동 가능 (`dmesg | grep -i kill` 로 확인). 즉시 메모리 사용량 점검 후 batch 축소 |
| `RuntimeError: ... shape mismatch` | 데이터셋의 카메라 해상도가 학습 중 변경됐을 가능성 (multi-resolution data). info.json 의 features 확인 |

### Walking RL 보호 우선 — 한 번 더 강조

본 학습 중 Walking RL 학습 step time 이 평소보다 **2배 이상 느려지면** 양보 의무 발생:
1. 즉시 본 학습 종료 (`Ctrl+C` 또는 `kill ${PID}`)
2. `nvidia-smi` / `free -h` 로 자원 점유 재확인
3. `batch_size` / `num_workers` 축소 후 재시도

---

## 8) 참조

- [data_collection.md](data_collection.md) — 데이터 수집 단계 (선행)
- [smolvla.mdx](../../docs/reference/lerobot/docs/source/smolvla.mdx) — SmolVLA 공식 학습 / 평가 가이드
- [smoke_test.sh](../scripts/smoke_test.sh) — 1 step 검증 (참고용 스크립트)
- [preflight_check.sh](../scripts/preflight_check.sh) — 학습 전 게이트
- [setup_finetune_env.sh](../scripts/setup_finetune_env.sh) — venv / HF_HOME 격리 설정
- [configuration_smolvla.py](../../docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py) — SmolVLAConfig 정의 (chunk_size=50, num_steps=10 등 기본값)
- [configuration_smolvla.py:68-71](../../docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py#L68-L71) — `freeze_vision_encoder` / `train_expert_only` / `train_state_proj` — §2-4 Stage 선택의 근거 플래그
- `~/smolvla/dgx/runs/05_leftarm/` — 마일스톤 진입 시 `train.sh` 셸 스크립트화 (현재는 본 문서의 명령을 직접 사용)
- 본 repo CLAUDE.md — Walking RL 보호 원칙
