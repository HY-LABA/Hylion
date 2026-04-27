# SmolVLA 파인튜닝 가능성 — DGX Spark 자원 기반 추정

> 기준: `docs/reference/lerobot/` (v0.5.1-52-g05a52238) `src/lerobot/scripts/lerobot_train.py`, `src/lerobot/configs/train.py`, `docs/source/smolvla.mdx`, `docs/source/peft_training.mdx`
> DGX 실측 기준일: 2026-04-27 (`docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt`)
> 작성일: 2026-04-28
> 목적: 본 프로젝트(SO-ARM 양팔 + 카메라 3대) SmolVLA 파인튜닝의 실행 가능성을 DGX Spark 실측 자원 기반으로 추정. `lerobot-train` CLI 동작·하이퍼파라미터·체크포인트·환경관리 결정사항 정리.
> 선행 읽기: `03_smolvla_architecture.md` §A (학습 시나리오 S1~S4), `03b_smolvla_milestone_config_guide.md` §2 (마일스톤별 분기), `05_hf_model_selection.md` (모델 변종 결정)

---

## 1) DGX Spark 실측 자원 요약 (2026-04-27)

| 항목 | 값 | 학습 영향 |
|---|---|---|
| GPU | NVIDIA GB10 (UMA) | VRAM 별도 표기 X — CPU/GPU 가 RAM 121 GiB 공유 |
| RAM (UMA) | 121 GiB (90 GiB 가용) | 학습 시 모델·옵티마이저·activation·dataloader 모두 같은 pool 사용 |
| 드라이버 / CUDA | 580.142 / 13.0 | **PyTorch 호환성 핵심 변수** (CUDA 13 공식 wheel 검증 필요) |
| Python | 3.12.3 (시스템) | lerobot `>=3.10` 호환 |
| pip | 24.0 | 동작 |
| 격리 도구 | venv 가용, conda 없음 | venv 권장 (단일 환경, Orin 일관성) |
| Docker | 29.1.3 + NVIDIA Container Toolkit 1.19.0 | TODO-07 Walking RL 격리 시 컨테이너 옵션 가용 |
| 디스크 | 3.3 TB 가용 | 체크포인트·HF 캐시·데이터셋 충분 |
| Ollama | 실행 중 | 학습 전 stop 권장 (UMA RAM 공유) |
| cuDNN / TensorRT | 미설치 | 학습엔 cuDNN 필요할 수 있음 — TODO-08 결정 |

**핵심 시사점**:
- **UMA 메모리 121 GiB pool** — DGX Spark 의 가장 큰 특징. 일반 dGPU 의 VRAM 제약을 벗어나 큰 batch size / 풀 파인튜닝 모두 여유 있을 가능성 높음
- **CUDA 13.0** — PyTorch 공식 안정 빌드는 보통 CUDA 12.x 지원 한계. CUDA 13 호환 wheel 확인이 TODO-08 의 첫 단계

## 2) 환경관리 / 버전 호환성 결정 (TODO-08 사전 정리)

본 절은 02_dgx_setting TODO-08 의 결정 항목 5가지를 본 시점 정보로 사전 정리. 정식 결정은 TODO-08 진입 시 본 절을 출발점으로.

### 2.1 Python 버전: 시스템 3.12.3 그대로 사용

- 근거: lerobot `pyproject.toml` 요구사항 `python>=3.10` 충족. DGX 시스템 Python = 3.12.3.
- 추가 설치 불필요 → 디스크/시간 절약, 업데이트 추적 단순.

### 2.2 패키지 매니저: venv 권장

| 항목 | venv | conda |
|---|---|---|
| Python 버전 관리 | 시스템 Python 만 | 여러 버전 가능 |
| 비-Python 의존성 | 시스템에 의존 | 환경별 격리 (CUDA 등) |
| 디스크 사용 | 작음 | 큼 |
| 설치 속도 | 빠름 | 느림 |
| 표준성 | Python 표준 | 외부 도구 |
| Orin 일관성 | ✅ Orin 도 venv | ❌ |

**결론: venv 사용**. 본 프로젝트는 단일 환경, 시스템 Python 호환, CUDA 시스템 단 고정 → conda 의 장점이 활성화되지 않음. Orin 측 `~/smolvla/.venv` 와 운영 일관성도 유지.

> **검토 시나리오**: TODO-07 결과 Walking RL 과 SmolVLA 가 다른 PyTorch/CUDA 버전을 요구하면 conda 또는 컨테이너 필요. 그 경우 **Docker (이미 설치됨) + NVIDIA Container Toolkit** 으로 격리하는 것이 conda 보다 깔끔.

### 2.3 PyTorch 버전: CUDA 13 호환 wheel 확인 필요 (TODO-08 첫 검증)

- DGX 의 CUDA SDK 13.0 / 드라이버 580.142 → 권장 PyTorch wheel 미확정
- 후보:
  - PyTorch 공식 안정 (`pip install torch`) — 최신은 CUDA 12.8 까지 지원, CUDA 13 미지원 가능성
  - PyTorch nightly — `pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu130` 형태로 시도
  - 드라이버 580 은 **CUDA 12.x runtime 도 backward compatible** — 시스템 SDK 가 13.0 이라도 PyTorch wheel 은 cu128 사용 가능할 가능성 높음
- TODO-08 진입 시 검증 절차:
  1. `pip install torch` 후 `torch.cuda.is_available()`, `torch.version.cuda` 확인
  2. 실패 시 nightly cu130 시도
  3. 그래도 실패 시 cu128 stable 로 fallback (드라이버 backward compat)

### 2.4 cuDNN / TensorRT 설치 여부

- **cuDNN**: 학습 시 PyTorch 가 내부적으로 사용 (`torch.backends.cudnn.benchmark` 등). PyTorch wheel 이 cuDNN 을 번들로 포함하므로 **별도 시스템 설치 불필요** 가능성 높음. 미동작 시 system cuDNN 설치 (PyTorch 와 동일 CUDA 버전).
- **TensorRT**: 학습엔 불필요. 배포(07_biarm_deploy) 시 Orin 에서 검토.

### 2.5 lerobot 설치 방식: pip install (editable 아님)

- DGX 는 학습 전용 → orin/ 같은 코드 수정 안 함. PyPI 또는 GitHub release 에서 stable 설치.
- 명령: `pip install 'lerobot[smolvla,training]'` — `[smolvla]` extra (transformers + peft) + `[training]` extra (accelerate + wandb).

### 2.6 종합 — TODO-08 권장 결정

| 항목 | 권장값 |
|---|---|
| Python | 시스템 3.12.3 |
| 패키지 매니저 | venv |
| venv 경로 | `/home/laba/smolvla/.venv` (Orin 과 동일 컨벤션) |
| PyTorch | TODO-08 검증 후 결정 (cu128 stable 또는 cu130 nightly) |
| cuDNN | PyTorch wheel 번들 사용 우선, 실패 시 시스템 설치 |
| TensorRT | 학습 단계에서는 미설치 |
| lerobot | `pip install 'lerobot[smolvla,training]'` |

## 3) `lerobot-train` CLI 동작

### 3.1 엔트리포인트

`docs/reference/lerobot/src/lerobot/scripts/lerobot_train.py` (CLI: `lerobot-train`)

**최소 명령 (smolvla.mdx 공식 예시)**:
```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/<dataset_name> \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/<run_name> \
  --job_name=<run_name> \
  --policy.device=cuda \
  --wandb.enable=true
```

### 3.2 주요 인자 (TrainPipelineConfig, `configs/train.py`)

| 인자 | 디폴트 | 의미 |
|---|---|---|
| `--policy.path` | (필수) | 사전학습 모델 경로/repo_id (`lerobot/smolvla_base` 권장, B1 시나리오) |
| `--dataset.repo_id` | (필수) | HF Hub 데이터셋 또는 로컬 경로 |
| `--batch_size` | **8** | 학습 batch. UMA 121 GiB 환경에선 64+ 권장 (smolvla.mdx 권장 64) |
| `--steps` | **100_000** | 총 학습 step. smolvla.mdx 공식 예시 20k, 본 문서 §5.2 권장값 참조 |
| `--num_workers` | **4** | DataLoader worker. CPU 20 코어 환경 → 8~16 권장 |
| `--prefetch_factor` | **4** | DataLoader prefetch |
| `--persistent_workers` | True | 워커 유지 |
| `--output_dir` | `outputs/train/<date>/<time>_<job>` | 자동 생성. 명시 권장 (재개 시 필요) |
| `--job_name` | `<policy.type>` | 디폴트 `smolvla` |
| `--seed` | 1000 | 재현성 |
| `--cudnn_deterministic` | False | True 시 재현성 ↑, 속도 10~20% ↓ |
| `--save_freq` | **20_000** | 체크포인트 저장 주기 (step) |
| `--eval_freq` | 20_000 | 평가 주기 (env 없으면 무시) |
| `--log_freq` | 200 | 로그 출력 주기 |
| `--resume` | False | 기존 run 재개 (output_dir 같아야 함) |
| `--use_policy_training_preset` | True | True 시 policy config 의 optimizer/scheduler preset 사용 (권장) |
| `--wandb.enable` | False | WandB 로깅 |

### 3.3 SmolVLA policy 인자 (configuration_smolvla.py)

`--policy.path=lerobot/smolvla_base` 사용 시 정책 config 가 자동 로드. 추가 override 가능:

| 인자 | 디폴트 | 의미 |
|---|---|---|
| `--policy.optimizer_lr` | 1e-4 | AdamW LR |
| `--policy.scheduler_decay_lr` | 2.5e-6 | Cosine decay 종료 LR |
| `--policy.scheduler_warmup_steps` | 1_000 | warmup |
| `--policy.scheduler_decay_steps` | 30_000 | decay 구간 |
| `--policy.train_expert_only` | True | S1: VLM 동결, expert 만 학습 (S3 전환 시 False) |
| `--policy.freeze_vision_encoder` | True | vision_model 동결 |
| `--policy.train_state_proj` | True | state_proj 학습 |
| `--policy.device` | None | "cuda" 명시 권장 |

분기 시나리오는 [03_smolvla_architecture.md §A](03_smolvla_architecture.md), 마일스톤별 권장값은 [03b_smolvla_milestone_config_guide.md §2](03b_smolvla_milestone_config_guide.md) 참조.

### 3.4 PEFT (LoRA) 인자 (`peft_training.mdx`)

VRAM 부족 또는 빠른 실험용. `pip install 'lerobot[peft]'` 추가 필요.

| 인자 | 디폴트 | 의미 |
|---|---|---|
| `--peft.method_type` | None | `LORA` 지정 시 활성화 |
| `--peft.r` | 16 | LoRA rank. 64 사용 예시 (peft_training.mdx) |
| `--peft.target_modules` | None (자동) | 자동 디폴트는 `lm_expert.q/v_proj` + projection layer (`modeling_smolvla.py:495-504`) |
| `--peft.full_training_modules` | None | 일부 layer 만 풀 학습 (예: `state_proj`) |

LoRA 사용 시 LR 권장 10× 증가: `--policy.optimizer_lr=1e-3`, `--policy.scheduler_decay_lr=1e-4`.

## 4) 체크포인트 저장 형식

`save_checkpoint()` (`src/lerobot/common/train_utils.py:69`) 의 디렉터리 구조:

```
<output_dir>/
└── checkpoints/
    ├── last/                    # 심볼릭 링크 → 가장 최근 step
    └── <step_id>/               # 예: 020000/
        ├── pretrained_model/
        │   ├── config.json
        │   ├── model.safetensors             # 정책 가중치
        │   ├── train_config.json
        │   └── step_*.safetensors            # processor state
        └── training_state/
            ├── optimizer_state.safetensors
            ├── optimizer_param_groups.json
            ├── scheduler_state.json
            ├── rng_state.safetensors
            └── training_step.json
```

**시사점**:
- **체크포인트당 디스크 크기**: SmolVLA 450M (bfloat16, 2 byte/param) → 약 900 MB 가중치 + optimizer state 약 1.8 GB (AdamW 는 가중치 2배) → **체크포인트당 약 2.7 GB**
- 200k step 학습, save_freq=20k → 10 체크포인트 → **약 27 GB** (DGX 3.3 TB 충분)
- **재개**: `--resume=true --config_path=<output_dir>/checkpoints/last/pretrained_model/train_config.json`
- **Orin 반입**: `pretrained_model/` 디렉터리만 복사하면 추론 가능 (training_state/ 는 학습 재개용이라 배포 불필요)

## 5) DGX 자원 기반 학습 비용 추정

### 5.1 비교 기준점 (smolvla.mdx)

> "Training the model for 20k steps will roughly take ~4 hrs on a single A100 GPU."

- 기준: A100 80GB, 20k step, batch_size=64 (smolvla.mdx 예시)
- 1 step ≈ 0.72 초 (A100 기준)

### 5.2 DGX Spark (GB10) 추정

GB10 의 정확한 학습 throughput 데이터는 미확보 (NVIDIA 공식 SmolVLA 벤치마크 없음). 보수적 추정:

| 시나리오 | 1 step 추정 | 20k step 추정 시간 | 200k step 추정 시간 |
|---|---|---|---|
| GB10 ≈ A100 동급 (낙관) | 0.7~1.0 초 | 4~6 시간 | 40~55 시간 |
| GB10 ≈ A100 70% (보수) | 1.0~1.5 초 | 6~8 시간 | 55~80 시간 |
| GB10 ≈ A100 50% (비관) | 1.5~2.0 초 | 8~12 시간 | 80~110 시간 |

**TODO-09 (학습 환경 세팅) 1 step smoke test 후 정확한 throughput 측정 필요**. 그 결과로 본 표 갱신.

### 5.3 메모리 추정 (UMA 121 GiB pool)

`03_smolvla_architecture.md §A` 의 시나리오별 추정 (일반 dGPU 기준 VRAM):

| 시나리오 | 학습 파라미터 | 메모리 (batch=64, bf16) | UMA pool 점유 |
|---|---|---|---|
| **S1 (권장)** | ~50M | ~12 GB | 모델·grad·optimizer + activation + dataloader 합쳐 약 25~35 GB |
| S1 + LoRA r=64 | ~10M | ~8 GB | 약 20~28 GB |
| **S3 (VLM 까지 풀)** | ~400M | ~30 GB | 약 50~65 GB |
| S4 (vision 까지) | ~600M | ~45 GB | 약 70~85 GB |

UMA 121 GiB → **S1 / S3 모두 여유. S4 도 batch_size 조정 시 가능**. dGPU 환경의 일반적인 OOM 위험은 낮음.

다만:
- **Ollama 가 RAM 일부 점유** 중 (TODO-02 실측). 학습 전 stop 권장.
- **OS / 시스템 프로세스** 가 추가 5~10 GB 소비
- **dataloader prefetch** (num_workers=4, prefetch_factor=4) 도 RAM 점유

→ **batch_size 64 → 128 단계적 증가** 검토 가능 (UMA 충분 시 throughput ↑).

### 5.4 디스크 추정

| 항목 | 크기 |
|---|---|
| smolvla_base 사전학습 가중치 (HF 캐시) | ~1.0 GB |
| SmolVLM2 백본 가중치 (HF 캐시) | ~1.0 GB |
| 체크포인트 (10 개, save_freq=20k, steps=200k) | ~27 GB |
| 본 프로젝트 데이터셋 (50 에피소드 × 카메라 3대 추정) | ~5~20 GB (mp4 인코딩) |
| WandB 로컬 캐시 | ~1 GB |
| **합계** | **~35~50 GB** |

DGX 디스크 3.3 TB → **충분**. HF 캐시 위치는 `HF_HOME` 환경변수로 분리 가능 (다중 사용자 시).

## 6) 본 프로젝트 학습 권장값

### 6.1 04_leftarmVLA (단일팔, 카메라 2대, 6 DOF)

```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/leftarm_so_arm_humanoid_v1 \
  --batch_size=64 \
  --steps=20000 \
  --num_workers=8 \
  --output_dir=outputs/train/leftarm_v1 \
  --job_name=leftarm_v1 \
  --policy.device=cuda \
  --wandb.enable=true
```

근거:
- batch_size=64: smolvla.mdx 공식 예시
- steps=20000: smolvla.mdx 공식 예시 (4시간 / A100 기준). 데이터 부족 시 50k 까지 확대
- num_workers=8: CPU 20 코어 → 절반 활용 (남은 코어는 dataloader 외 OS / 학습 메인 스레드)

예상 소요: **6~12 시간** (5.2 추정 표).

### 6.2 06_biarm_VLA (양팔, 카메라 3대, 12 DOF)

**1차 시도** (S1, 기본):
```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/biarm_so_arm_humanoid_v1 \
  --batch_size=64 \
  --steps=50000 \
  --num_workers=8 \
  --output_dir=outputs/train/biarm_s1_v1 \
  --job_name=biarm_s1_v1 \
  --policy.device=cuda \
  --wandb.enable=true
```

근거:
- steps=50000: 도메인 시프트(양팔 + 카메라 3대 + 토르소) 가 04 보다 큼 → 더 긴 학습. 50k step 후 정성 평가 → 부족하면 100k 확장
- 1차 실패 시 fallback 트리거: [03b §2 06](03b_smolvla_milestone_config_guide.md) 참조

**2차 시도** (S3, VLM 까지):
```bash
# 위 명령에 추가
  --policy.train_expert_only=false \
  --policy.optimizer_lr=5e-5 \
  --policy.scheduler_decay_lr=1e-6
```

LR 절반 (catastrophic forgetting 회피).

**VRAM 부족 fallback** (UMA 충분하지만 만일 실패 시):
```bash
# LoRA 적용
  --peft.method_type=LORA \
  --peft.r=64 \
  --policy.optimizer_lr=1e-3 \
  --policy.scheduler_decay_lr=1e-4
```

### 6.3 학습 중 모니터링 항목

| 항목 | 도구 | 주기 |
|---|---|---|
| loss (`losses_after_forward`, `losses_after_in_ep_bound`, `loss`) | WandB | 매 step |
| gradient norm | WandB | 매 step |
| learning rate | WandB | 매 step |
| GPU/CPU 사용률 | `nvidia-smi`, `htop` | 5분 간격 |
| RAM 점유 (UMA) | `free -h` | 5분 간격 |
| 디스크 (체크포인트) | `df -h /home/laba` | 체크포인트 저장 후 |
| WandB sample rollout (가능 시) | env 평가 — DGX 환경 없음, 04/06 의 정성 평가는 Orin 에서 |

## 7) 잔여 리스크 / 후속 검증

- **GB10 throughput 미확정** — TODO-09 1 step smoke test 후 §5.2 표 갱신 필요
- **CUDA 13 PyTorch 호환** — TODO-08 첫 검증 항목. nightly 또는 cu128 fallback 필요할 수 있음
- **UMA 메모리 점유 분포** — 일반 dGPU 의 VRAM 추정과 다름. nvidia-smi 가 의미 있는 값 안 줄 수 있어 `free -h` + Python 프로세스 RSS 모니터링 병행
- **Ollama 자원 경합** — 학습 시작 전 `systemctl stop ollama` 또는 모델 unload (TODO-09 환경 세팅 시 확인)
- **Orin 반입 호환성** — DGX 학습 PyTorch 버전과 Orin 추론 PyTorch 버전 차이가 safetensors 로드에 영향 있을 가능성 (보통 호환되지만 마이너 버전 차이 검증 필요, TODO-10 배포 환경 세팅 시)

## 8) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-28 | 초안 작성. DGX 실측(2026-04-27) + lerobot-train CLI/체크포인트 형식/PEFT 정리. TODO-08 환경관리 결정 사전 정리 (venv 사용 결론). 04/06 학습 권장 명령 작성. |
