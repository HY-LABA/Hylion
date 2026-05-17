# prof_computer — DGX 보조 학습 노드 (WSL2 + RTX 3090)

> [prof_train_setting.md](../docs/storage/prof_train_setting.md) §1 옵션 #1 "로컬 GPU PC" 의 구체 구현체.
> 시연장 외 (개발실·실험) 학습 수행. DGX 의 aarch64 한계 (torchcodec 부재 → pyav fallback leak) 우회를 위한 일반 x86 학습 노드.
> 등록: 2026-05-16 · **M1.5 중간점검 학습 완주: 2026-05-17** (leftarm_v2 100ep subset, 75000 step)
> 실측 사양: [02_hardware.md §6](../docs/storage/02_hardware.md) · 소프트웨어: [03_software.md §7](../docs/storage/03_software.md)
>
> **위치**: M1 (200ep 수집 중, 100ep 도달) → **M1.5 (현재 사이클, prof_computer 로 이관 — image 변환 폐기, video dataset 그대로 학습 성공)** → M2 (200ep 완성 후 본 학습, 미시작) → M3 (Orin 추론).

## 1) 노드 정체성

| 항목 | 값 |
|---|---|
| 호스트 | `DESKTOP-G8LO9C5` (Windows 10 + WSL2 Ubuntu 22.04) |
| GPU | RTX 3090 **24GB VRAM** (분리 — DGX UMA 와 다름) |
| 학습 distro | `Ubuntu-22.04` (WSL2), 사용자 `laba` |
| Python | **`3.12.x` (deadsnakes PPA)** + venv (`.venv_arm_finetune`) — lerobot 0.5.2 `requires-python>=3.12` 충족용. 시스템 3.10.12 와 병존. |
| 데이터 | HF Hub (`BaboGaeguri/leftarm_v2` 등) — DGX 와 공유 |
| 작업 영역 | `smolVLA/prof_computer/` (본 폴더) |

## 2) DGX 와의 분담

- **공유**: 데이터셋 (HF Hub) + lerobot upstream (`docs/reference/lerobot/`) + finetune config (`dgx/finetune/leftarm_v2/`)
- **분리**: venv 위치, 학습 산출물 (`~/prof_computer_runs/` vs DGX `~/smolvla/dgx/outputs/`), wandb run name (`_pc_` 접두로 구분)

## 3) DGX vs prof_computer — 메모리 모델 차이 (운영 핵심)

| 차원 | DGX (UMA 128GB) | prof_computer (분리) |
|---|---|---|
| GPU 메모리 | UMA 공유 (VRAM 별도 없음) | **24GB VRAM (분리)** |
| system RAM | UMA 공유 | 64GB (WSL 48GB 할당) |
| swap | 0 | 16GB (`.wslconfig`) |
| OOM 위협 1순위 | system 전체 OOM (`CONSTRAINT_NONE`) | **VRAM OOM** |
| OOM 위협 2순위 | UMA 헤드룸 부족 | system RAM 누수 (시도 2 가설 잔존) |

→ DGX 의 시도 1·2 OOM (`training_log.md`) 은 UMA 특수 사정. prof_computer 에서는 **VRAM 24GB 가 새 제약** + system RAM 누수 가설 그대로.

## 4) 채택한 사전 조치 (training_log §시도2 "시도 3 후보" 선제 반영)

| 조치 | 근거 |
|---|---|
| `video_backend=torchcodec` | 시도 2 의 시간 비례 누수 = pyav-libsvtav1 decoder leak 가설 → backend 교체로 회피 |
| `.wslconfig memory=48GB` + swap 16GB | 누수 발생 시 시간 벌이 |
| smoke test 우선 (steps=100) | 본 학습 20K step 전에 VRAM peak + 누수율 실측 |

## 5) 폴더 구조 (planned)

```
prof_computer/
├── README.md                       # 본 파일
├── scripts/
│   ├── setup_env.sh                # WSL apt + venv + lerobot/torchcodec 설치
│   ├── env_check.sh                # 학습 전 환경 검증
│   └── run_train.sh                # dgx/finetune/leftarm_v2/run_train.py 호출 래퍼
├── finetune/
│   └── leftarm_v2/
│       └── README.md               # DGX config 공유 + PC 전용 차이만 기록
└── docs/
    └── learning_log.md             # PC 학습 시도 기록 (DGX training_log 와 별도)
```

> ⚠️ **upstream 옵션 B 일관**: prof_computer 도 `docs/reference/lerobot/` editable install 을 그대로 사용 — DGX 와 같은 정책. lerobot 코드 분기 없음.

## 6) 사용 시점 트리거

- DGX 가동·이동 불가
- 새 hyperparameter 후보를 DGX 본 학습 전에 빠르게 실험
- 동일 dataset 으로 DGX 와 결과 비교

## 7) 진행 상황 (2026-05-17 첫 사이클 완주)

### 셋업 + 검증 (2026-05-16)

- [x] `.wslconfig` 작성 (`C:\Users\admin\.wslconfig` — memory=48GB)
- [x] 02_hardware / 03_software 에 prof_computer 등록
- [x] `scripts/setup_env.sh` 작성 + 실행 — apt + Python 3.12 (deadsnakes) + lerobot[smolvla,training,peft] + torchcodec 0.10
- [x] HF + wandb 로그인 (`.env` 자동 source)
- [x] dry-run + smoke test (4회):
  - smoke 1 (batch 16 fp32) → ❌ CUDA OOM
  - smoke 2 (batch 8 fp32) → ✅ 통과, VRAM 94.82%
  - smoke 3 (batch 8 bf16) → ⚠️ bf16 효과 없음 확인
  - smoke 4 (batch 4 fp32) → ✅ VRAM 51.79%, 본 학습 진입 결정

### M1.5 중간점검 학습 (2026-05-17, leftarm_v2 100ep subset)

> **M1.5 의 원 결정** ([realplaying.md M1.5](../realplaying.md)) 은 "image dataset 변환" 이었으나, **본 사이클에서 변경** — image 변환 폐기 + prof_computer (일반 x86 환경) 로 video dataset 그대로 학습.
> DOD ("100ep subset 학습 진입 → OOM 없이 첫 ckpt 도달") 초과 달성: 75000 step 완주 + 5.5 epoch + loss 0.04 수렴.

- [x] 본 사이클 학습 (batch 4 fp32, steps 75000, DGX 의도 5 epoch on batch 16 과 sample 수 동등)
  - 학습 시간 7시간 34분, step time 0.343 s/step
  - VRAM peak 60.67%, GPU temp peak 83°C
  - System RAM 누수 0.18 GB/h (DGX 시도 2 의 1.25 GB/min 대비 400× 감소)
  - loss min 0.013, final 0.04
  - 75개 ckpt 저장, last ckpt 폴더 125 MB (LoRA adapter 46MB + meta)
  - 상세: [docs/learning_log.md](docs/learning_log.md)
- [x] HF Hub model repo push 완료: [`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`](https://huggingface.co/BaboGaeguri/leftarm_v2_A2_pc_2026-05-17) (46 MB, public)

### 다음 사이클

- [ ] **Orin 추론 검증** — `lerobot-record --policy.path=BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 ...` 으로 시연장 정성 평가 (M3 영역 일부 선검증)
- [ ] **M1 완성** — 잔여 100ep 수집 (현재 100/200 ep)
- [ ] **M2 본 학습** — 200ep 완성 후 prof_computer 또는 (가능 시) DGX 에서 본 학습
- [ ] DGX 의 aarch64 ecosystem 정비 (torchcodec wheel 또는 FFmpeg 7) — backlog (장기)
