# smolVLA DGX 환경 세팅 기록

> 작성일: 2026-04-28 (TODO-09b prod 검증 완료 직후)
> 목적: SmolVLA를 DGX Spark에서 학습하기 위한 환경 구성 과정과 현재 상태를 기록
> Orin 추론 환경 세팅은 별도 문서 `05_orin_venv_setting.md` 참조 (형제 구조)

## 1) 개요

- 실행 대상: DGX Spark (`spark-8434`, NVIDIA GB10 UMA, CUDA 13.0, Ubuntu 24.04.4 LTS)
- 환경 관리 방식: venv (`~/smolvla/dgx/.arm_finetune`, hidden) — Orin venv `~/smolvla/orin/.hylion_arm` 와 형제 구조로 격리
- 소프트웨어 실측 현황 근거: `docs/storage/03_software.md` §5
- 동시 점유 트랙: Walking RL (`/home/laba/env_isaaclab/`, uv 생성 venv) — 같은 DGX 머신, 본 SmolVLA venv 와 환경변수·디렉터리 모두 격리됨

### 디렉터리 형제 구조 (2026-04-28 변경 반영)

```
/home/laba/smolvla/
├── orin/                       # 추론 (05_orin_venv_setting.md)
│   ├── .hylion_arm/            # ← venv (hidden, Python 3.10, JP 6.0 wheel)
│   ├── lerobot/
│   ├── scripts/
│   └── ...
└── dgx/                        # 학습 (본 문서)
    ├── .arm_finetune/          # ← venv (hidden, Python 3.12, torch 2.10.0+cu130)
    ├── scripts/
    │   ├── setup_train_env.sh
    │   ├── preflight_check.sh
    │   ├── smoke_test.sh
    │   └── save_dummy_checkpoint.sh
    ├── runs/                   # 마일스톤별 학습 자료 (04 진입 시 채움)
    └── outputs/                # 학습 출력 (배포 제외, hidden 아님)
```

DGX 는 lerobot 코드를 직접 수정하지 않으므로 `dgx/lerobot/` curated 디렉터리는 두지 않는다. 대신 `docs/reference/lerobot/` submodule 을 그대로 editable 설치한다 (분석 SHA 와 학습 환경 SHA 자동 일치).

## 2) venv 환경 구성 (2026-04-28 확정)

### venv 선택 근거 (Walking RL 환경 정합 + Orin 일관성)

DGX 시스템 Python 이 lerobot 호환 (`>=3.10`) 이고 conda 가 미설치이며, Walking RL 트랙도 같은 머신에서 venv (uv 생성) 사용 중. 격리 요건은 **디렉터리 분리** 만으로 충족됨:

- DGX 시스템 Python 3.12.3 = lerobot `pyproject.toml` 요구사항 충족 → 추가 Python 설치 불필요
- conda 는 시스템 미설치, 본 프로젝트 단일 환경에서는 venv 의 디스크/속도 이점이 우세
- Walking RL `/home/laba/env_isaaclab/` 와 SmolVLA `/home/laba/smolvla/dgx/.arm_finetune` 는 절대 경로 분리로 충돌 없음
- Orin 측 `~/smolvla/orin/.hylion_arm` 와 형제 구조 → 운영 일관성 (활성화 명령 패턴 동일, hidden 컨벤션 동일)
- Docker 컨테이너 격리는 불필요 — 두 트랙이 다른 PyTorch 버전을 요구할 때만 의미 있음. 현재 Walking RL `torch 2.10.0+cu130` 와 본 프로젝트가 동일 wheel 사용

자세한 venv vs conda vs uv 비교 및 결정 근거: `docs/lerobot_study/06_smolvla_finetune_feasibility.md §2`

- venv 경로: `~/smolvla/dgx/.arm_finetune`
- Python 버전: `3.12.3` (DGX 시스템 Python)
- 설치 스크립트: `~/smolvla/dgx/scripts/setup_train_env.sh`

### 실측 설치 패키지 (2026-04-28 기준)

TODO-09b prod 검증 완료 시점:

| 패키지 | 버전 | 비고 |
|---|---|---|
| lerobot | editable | `~/smolvla/docs/reference/lerobot/` (`v0.5.1-52-g05a52238`) — `[smolvla,training]` extras |
| torch | `2.10.0+cu130` | nvidia 공식 wheel (`https://download.pytorch.org/whl/cu130`), Walking RL 검증 완료 |
| nvidia-cudnn-cu13 | `9.15.1.9` | PyTorch wheel 의존성으로 자동 설치 (시스템 별도 설치 X) |
| nvidia-nccl-cu13 | `2.28.9` | 동일 |
| transformers | lerobot deps 포함 | `[smolvla]` extra |
| accelerate | lerobot deps 포함 | `[training]` extra |
| wandb | lerobot deps 포함 | `[training]` extra (smoke test 에선 `--wandb.enable=false`) |
| safetensors | lerobot deps 포함 | 체크포인트 표준 포맷 |

### 환경변수 자동 적용

`setup_train_env.sh` 가 venv 의 `bin/activate` 끝에 자동 export 추가:

| 변수 | 값 | 의미 |
|---|---|---|
| `HF_HOME` | `~/smolvla/.hf_cache` | Walking RL 및 시스템 디폴트 HF 캐시와 격리 |
| `PYTORCH_CUDA_ALLOC_CONF` | `expandable_segments:True,max_split_size_mb:128` | UMA 환경 메모리 단편화 방지, OOM 마진 확보 |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 0 명시 사용 |

활성화: `source ~/smolvla/dgx/.arm_finetune/bin/activate` → prompt `(.arm_finetune)` 표시 + 위 변수 자동 적용.

## 3) PyTorch 설치 방식

### `torch==2.10.0+cu130` 의도적 선택 근거 (2026-04-28 확정)

**Walking RL 트랙 호환 우선** + **CUDA 13 호환 wheel 검증된 유일 옵션**:

1. **Walking RL 검증 완료 (2026-04-28 회신)**: 같은 DGX 머신에서 동일 wheel 동작 검증됨 (`docs/storage/others/walking_rl_smolvla_check_2026-04-28.md`). 두 트랙이 동일 wheel 사용 → wheel 충돌 가능성 0
2. **DGX 시스템 CUDA 13.0** (드라이버 580.142): PyTorch 공식 안정 빌드 중 cu130 wheel 만 호환 검증됨
3. **lerobot 호환**: lerobot `pyproject.toml` 의 `torch>=2.4` 요구사항 충족
4. **Orin 호환성 (체크포인트 안전성)**: PyTorch 의 safetensors 포맷은 버전 독립적이라 Orin 측 `torch 2.5.0a0+nv24.08` 와 호환. 실측 검증은 TODO-10b 에서 진행

### GB10 CUDA capability 12.1 UserWarning

PyTorch 공식 지원 범위 (compute capability 8.0~12.0) 밖이라 `UserWarning` 출력되나 **기능 정상**:

```
UserWarning: NVIDIA GB10 with CUDA capability sm_121 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_80 ... sm_120.
```

→ TODO-09b 검증에서 동작 확인. 무시 가능.

### 설치 순서 (`setup_train_env.sh` 기준)

1. DGX 시스템 Python 3.12 식별 (`python3.12` 우선, 미탐지 시 `python3` fallback)
2. venv 생성: `python -m venv ~/smolvla/dgx/.arm_finetune`
3. `pip install --upgrade pip`
4. **PyTorch 설치**: `pip install torch==2.10.0+cu130 --index-url https://download.pytorch.org/whl/cu130`
   - cuDNN, NCCL, cuSPARSELt, nvSHMEM 의존성 자동 설치
5. **lerobot editable 설치**: `pip install -e ~/smolvla/docs/reference/lerobot[smolvla,training]`
6. venv `bin/activate` 끝에 환경변수 export 추가
7. 검증: `torch.cuda.is_available()`, `lerobot import`, CUDA 텐서 연산

### Orin (JP 6.0 wheel) 과의 차이

| 항목 | DGX | Orin |
|---|---|---|
| Python | 3.12.3 (시스템) | 3.10 (JetPack 6.2.2 시스템) |
| torch | `2.10.0+cu130` (nvidia 공식 wheel) | `2.5.0a0+872d972e41` (NVIDIA JP 6.0 nv24.08 wheel) |
| CUDA | 13.0 (시스템 SDK) | 12.6 (JetPack) |
| cuDNN | wheel 번들 (`nvidia-cudnn-cu13==9.15.1.9`) | torch wheel 내장 (별도 추적 X) |
| lerobot | editable submodule (학습 전용, 코드 수정 X) | curated `orin/lerobot/` (추론 전용, 트리밍 적용) |
| Python 버전 차이의 영향 | safetensors 직렬화는 Python 마이너 버전 독립적 — 호환 가능 (TODO-10b 검증 예정) |

## 4) `setup_train_env.sh` 구성 세팅

### 시스템 의존 패키지

별도 시스템 패키지 설치 불필요 — DGX Spark 의 기본 Ubuntu 24.04 환경이 모두 충족. PyTorch wheel 이 cuDNN/NCCL/cuSPARSELt 등을 의존성으로 자동 설치하므로 Orin 의 cusparselt LD_LIBRARY_PATH 패치 같은 우회 작업은 불필요.

### lerobot editable 설치 사유

DGX 는 학습 전용이라 lerobot 코드 수정은 안 한다는 원칙이지만 **editable** 설치를 채택한 이유:

1. **분석 SHA = 학습 환경 SHA 일치**: 본 프로젝트가 분석한 `docs/lerobot_study/03_smolvla_architecture.md` / `04_lerobot_dataset_structure.md` 의 코드 동작이 학습에 그대로 적용됨. PyPI stable wheel 은 SHA 가 다를 수 있음
2. **디버깅 시 일관성**: 학습 중 발생하는 동작이 분석 문서와 일치 → 디버깅 시간 단축
3. **submodule SHA 고정**: `git submodule update --remote --merge` 로 의도적으로 갱신할 때만 변경 — 갑작스런 PyPI 업데이트로 인한 호환성 문제 없음

### 환경변수 자동 적용 (venv activate 시)

`setup_train_env.sh` 의 §4 가 venv `bin/activate` 끝에 export 추가:

```bash
# === smolVLA dgx env vars ===
export HF_HOME="/home/laba/smolvla/.hf_cache"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128"
export CUDA_VISIBLE_DEVICES="0"
```

마커 `# === smolVLA dgx env vars ===` 로 멱등성 보장 — 재실행 시 중복 추가 방지.

### 설치 검증 (`setup_train_env.sh §5`)

```python
import os, sys, torch
# 1. PyTorch / CUDA / cuDNN / GPU 정보
# 2. 환경변수 (HF_HOME / ALLOC_CONF / CUDA_VISIBLE) 적용 확인
# 3. CUDA 텐서 연산 (a + b on GPU)
# 4. lerobot import + SmolVLAPolicy import
```

검증 실패 시 `sys.exit(1)` + `set -e` 로 스크립트 전체 중단.

## 5) `preflight_check.sh` 동작 (Walking RL 보호 게이트)

학습 시작 전 매번 실행 강제. 시나리오별 메모리 임계치 검증 + Walking RL 프로세스 관찰 (절대 kill X):

| 시나리오 | 필요 메모리 (RAM, UMA pool) | 안전 마진 | 용도 |
|---|---|---|---|
| `smoke` | 20 GiB | +10 GiB | 1 step 검증 |
| `s1` | 35 GiB | +10 GiB | 05_leftarmVLA / 07_biarm 1차 |
| `s3` | 65 GiB | +10 GiB | 07_biarm 2차 (VLM 풀 학습) |
| `lora` | 28 GiB | +10 GiB | LoRA fallback |

검증 항목 5개:
1. venv 활성 + 환경변수 (HF_HOME, CUDA_VISIBLE_DEVICES)
2. 메모리 가용성 (`MemAvailable`) ≥ 필요 + 안전 마진
3. Walking RL 프로세스 식별 (관찰만, kill 금지)
4. Ollama gemma3 GPU 점유 여부
5. 디스크 가용량 (`/home/laba`)

## 6) TODO-09b prod 검증 결과 (2026-04-28)

### smoke test 1 step 실측

조건: `batch_size=8`, `steps=1`, Walking RL 동시 실행 중

| 측정 항목 | 값 |
|---|---|
| lerobot train step | **5.97 초/step** |
| 전체 smoke 소요 | **48 초** (preflight + dataset/model load + 1 step) |
| 최종 loss | `0.545` |
| GPU util peak | **90%** (1초 샘플링) |
| GPU mem peak | N/A — GB10 UMA 구조로 `nvidia-smi memory.used/free` 가 `[N/A]` 출력 |
| System RAM used peak | **48226 MiB** (`free -m` 1초 샘플링) |

**해석**:
- 1-step smoke 값은 모델/데이터셋 로드 + 워밍업 영향이 커서 장시간 학습 throughput 을 그대로 대표하지 않음
- 단순 환산 시 20k step 약 33시간 / 200k step 약 332시간 — 실제 학습 계획에는 batch size 증가, 캐시 워밍업 후 평균 step time, Walking RL 점유 변동 반영해 재측정 필요
- batch=8 인데 RAM 48 GiB 점유 → batch=64 로 늘리면 추가 점유 가능성. preflight 의 `s1` 임계치 (35 GiB) 재검토 필요
- 자세한 throughput 분석: `docs/lerobot_study/06_smolvla_finetune_feasibility.md §5.2`

### Walking RL 동시 점유 환경

검증 시점 자원 분배 관찰 (대략):

| 트랙 | RAM 점유 | GPU util |
|---|---|---|
| Walking RL 학습 | ~7 GiB | 변동 |
| SmolVLA smoke (peak) | ~48 GiB | 90% |
| OS / 시스템 | ~5 GiB | - |
| **합계** | ~60 GiB | - |
| **가용** | ~76 GiB (preflight 시점) | - |

OOM 없이 동시 진행 가능 확인. 단, **batch=64 + S3 학습 시** 본 SmolVLA 단독으로 50~65 GiB 예상 (`§5.3`) → Walking RL 동시 점유 시 OOM 위험 증가. 04/06 본 학습 시점에 재측정 권장.

### 검증 중 발견된 이슈와 보정 (모두 dgx wrapper 레벨에서 해결, upstream 수정 X)

`docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 참조. `smoke_test.sh` 4건 보정:

| 보정 항목 | 사유 |
|---|---|
| venv 활성화 → preflight 순서 | preflight 가 venv 환경변수 (HF_HOME 등) 검증을 포함하므로 venv 활성 후 실행 |
| output dir 선생성 X | lerobot-train 의 `resume=false` 검증이 빈 output dir 도 거부 → resource sample 은 별도 디렉터리로 분리 |
| `--policy.push_to_hub=false` | SmolVLA policy 의 `push_to_hub` 기본값이 True 라 `--policy.repo_id` 요구 → smoke test 에서는 비활성화 |
| `--rename_map` 추가 | dataset `lerobot/svla_so100_pickplace` 의 카메라 키 (`top`/`wrist`) 와 policy `lerobot/smolvla_base` 의 키 (`camera1`/`camera2`/`camera3`) 불일치 → smoke test 용 매핑 |
| `--log_freq=1` | 1-step smoke 에서 기본 log 주기 (200) 때문에 loss 출력 안 됨 → 매 step 로그 |
| 자원 샘플링 1초 + GB10 UMA N/A 처리 | 5초 → 1초로 정밀화, `nvidia-smi memory.used` 가 `[N/A]` 출력될 때 system RAM 만 추적 |

## 7) 디스크 사용 추정

| 항목 | 크기 |
|---|---|
| smolvla_base 사전학습 가중치 (`HF_HOME=~/smolvla/.hf_cache`) | ~1.0 GB |
| SmolVLM2 백본 가중치 (HF 캐시) | ~1.0 GB |
| `lerobot/svla_so100_pickplace` 데이터셋 (smoke test 용) | ~5 GB |
| 체크포인트 (10 개, save_freq=20k, steps=200k) | ~27 GB |
| 학습 데이터셋 (04/06 실 학습용) | ~5~20 GB (mp4 인코딩, 50 에피소드 추정) |
| WandB 로컬 캐시 | ~1 GB |
| **합계 (예상)** | **~40~55 GB** |

DGX 디스크 가용 3.3 TB 대비 충분. 다만 Walking RL 트랙도 같은 머신을 사용하므로 정기적 정리 권장.

## 8) 잔여 리스크 / 후속 검증

- **GB10 capability 12.1 UserWarning** — TODO-09b 에서 동작 확인. 장기 학습 시 PyTorch upgrade (cu130 더 높은 버전) 가 capability 추가 지원 시 사라질 가능성
- **batch_size 증가 시 메모리 재측정** — 04/06 본 학습 시 batch=8 → 64 단계적 증가 + nvidia-smi 모니터링
- **Walking RL 동시 학습 시 OOM 마진** — preflight 의 임계치는 일반적인 경우 기준. 두 트랙 동시 진행 시 안전 마진 +10 GiB 가 충분한지 실측 필요
- **DGX↔Orin 체크포인트 호환성** — TODO-10b 에서 dummy 체크포인트로 검증 예정 (safetensors 직렬화 + bf16 호환). 결과는 §10 에 누적 기록.

## 9) 배포 환경 (DGX→Orin 체크포인트 전송)

> 본 절은 TODO-10b prod 검증 완료 시 채워진다. 현재 placeholder.

### 9.1 체크포인트 디렉터리 구조 (실측 예정)

`lerobot-train` 표준 구조 (TODO-10b 검증 시 실 파일 크기 확인 후 갱신):

```
~/smolvla/dgx/outputs/train/<run_name>/
└── checkpoints/
    ├── last/                                # 심볼릭 링크 → 가장 최근 step
    └── <step>/                              # 예: 000001 (smoke), 020000 (실 학습)
        ├── pretrained_model/                # ← Orin 반입 대상
        │   ├── config.json                  # ~10 KB
        │   ├── train_config.json            # ~5 KB
        │   └── model.safetensors            # ≈ 900 MB (bf16)
        └── training_state/                  # ← Orin 반입 X (학습 재개용)
            ├── optimizer_state.safetensors
            └── ...
```

### 9.2 전송 경로: devPC 경유 2-hop

`scripts/sync_ckpt_dgx_to_orin.sh` 동작:

```
DGX (~/smolvla/dgx/outputs/train/<run>/checkpoints/<step>/pretrained_model/)
   ↓ rsync (1-hop)
devPC (/tmp/smolvla_ckpt_<ts>/)
   ↓ rsync (2-hop)
Orin (~/smolvla/orin/checkpoints/<run>/<step>/)
```

직접 SSH 미사용 — `~/.ssh/config` 추가 설정 불필요, IP 변동 대응 한 곳만 (devPC), repo_management 의 sync hub 패턴과 일관성.

**기본 사용**:
```bash
# devPC 에서
bash scripts/sync_ckpt_dgx_to_orin.sh                          # 가장 최근 run + last step
bash scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1         # 특정 run, last step
bash scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1 --step 020000
bash scripts/sync_ckpt_dgx_to_orin.sh --dry-run                # 검증용
```

### 9.3 DGX bf16 → Orin bf16 호환성 (실측 예정)

| 검증 항목 | 결과 |
|---|---|
| DGX 학습 PyTorch | `2.10.0+cu130` |
| Orin 추론 PyTorch | `2.5.0a0+872d972e41` (JP 6.0 nv24.08) |
| safetensors 로드 | (TODO-10b 측정) |
| action shape | (TODO-10b 측정 — 예상 `(1, 50, 6)` 또는 `(1, 50, 32)` padding) |
| action dtype | (TODO-10b 측정 — 예상 bf16 또는 float32) |
| action 출력 range | (TODO-10b 측정) |
| numerical drift | (TODO-10b 정성 평가) |

### 9.4 lerobot SHA 호환성 (실측 예정)

DGX editable submodule SHA 와 Orin curated `orin/lerobot/` SHA 가 매칭되어야 모델 클래스 호환:

| 측면 | 위치 | SHA 또는 버전 |
|---|---|---|
| DGX | `~/smolvla/docs/reference/lerobot/` editable | `v0.5.1-52-g05a52238` |
| Orin | `~/smolvla/orin/lerobot/` curated | (TODO-10b 검증 — `git log` 또는 `__version__` 확인) |
| 일치 여부 | (TODO-10b) |

mismatch 시 발생할 에러 (참고): `ImportError`, `KeyError` (state_dict 키 불일치). 발생 시 `orin/lerobot/` 트리밍 재검토 + `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 갱신.

### 9.5 첫 1회 실측치 (실측 예정)

| 측정 항목 | 값 |
|---|---|
| dummy 체크포인트 생성 시간 (DGX) | (TODO-10b) |
| 체크포인트 크기 (`pretrained_model/`) | (TODO-10b) |
| DGX → devPC rsync 시간 | (TODO-10b) |
| devPC → Orin rsync 시간 | (TODO-10b) |
| 전체 sync 소요 | (TODO-10b) |
| Orin `load_checkpoint_test.py` 실행 시간 (model load + forward) | (TODO-10b) |

### 9.6 05_leftarmVLA 실 학습 진입 시 운영 절차 (예정)

TODO-10b PASS 후 실 학습 체크포인트 반입 권장 절차 (4단계):

1. **DGX 본 학습 진행** — `lerobot-train --policy.path=lerobot/smolvla_base --output_dir=~/smolvla/dgx/outputs/train/leftarm_v1 ...`
2. **사전 dry-run** — `bash scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1 --dry-run` 으로 전송 대상 확인
3. **본 sync** — `bash scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1` (필요 시 `--step` 명시)
4. **사후 검증 (Orin)** — `python ~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py --ckpt-path ~/smolvla/orin/checkpoints/leftarm_v1/<step>/`

03_smolvla_test_on_orin 마일스톤에서 latency 측정 + RTC 활성화 검토 (08_biarm_deploy 단계).

## 10) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-28 | 초안 작성. TODO-09b prod 검증 완료 (loss 0.545, 5.97 초/step, RAM peak 48 GiB) 결과 반영. Orin venv (`05_orin_venv_setting.md`) 와 형제 구조 명시. Walking RL 동시 점유 환경 관찰 결과 포함. §9 배포 환경 placeholder 추가 (TODO-10b 완료 시 채움). |
