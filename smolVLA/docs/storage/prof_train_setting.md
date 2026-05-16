# SmolVLA 학습 환경 — *일반 GPU 환경* 셋업 가이드

> 작성일: 2026-05-16
> 목적: DGX Spark 의 aarch64 환경 한계 (torchcodec 부재 → pyav fallback → leak → OOM) 우회를 위해, **일반 GPU 환경** (x86 + torchcodec 정상 동작) 에서 SmolVLA 학습을 진행하기 위한 표준 셋업 가이드.
> 배경: `docs/storage/legacy/realplaying/train_troubleshooting/` 의 M1.5 우회로 시도들 (image 변환, cleanup 강화, GOP 재인코딩 등) 모두 폐기 — DGX 자체 학습 보류 결정 (2026-05-16, 사용자 결정).
> 관련: `realplaying.md` (다음 M2 spec 재작성 시 본 문서를 baseline 으로 활용).

---

## 0) 왜 일반 환경인가 — 한 줄 요약

DGX Spark 는 *aarch64 + PyTorch 2.10 + FFmpeg 6* 의 신규 hardware 조합으로, **lerobot 의 권장 video backend (torchcodec) 가 호환 wheel 부재**. fallback (pyav) 는 *알려진 leak* (PyAV Issue #1117 + lerobot 의 불완전한 close 패턴) 발생 → 학습 OOM. 일반 x86 환경에선 torchcodec 정상 동작 → 학습 가능.

상세 진단: `docs/storage/legacy/realplaying/train_troubleshooting/` (특히 `m1.5_video_decode_oom.md` 와 `lerobot_smolvla_training_best_practice.md`).

---

## 1) GPU 자원 옵션 — 가성비 순

| # | 자원 | 비용 | 학습 시간 (SmolVLA LoRA, 20K step) | 안정성 | 우리 케이스 적합 |
|---|---|---|---|---|---|
| 1 | **로컬 GPU PC** (학원/연구실/개인) | $0 | 4-8h (RTX 3090 기준) | 안정 | ✅ **최우선** (있으면) |
| 2 | **Colab Pro** | $10/월 | A100 4-6h | 24h 세션 보장 | ✅ 단순·안정 |
| 3 | **Lambda / RunPod / Vast.ai 클라우드** (RTX 3090) | ~$0.30-0.50/h × 4-6h ≈ $2-3 | 4-6h | 끊김 X | ✅ 저렴·안정 |
| 4 | **Lambda / RunPod (A100)** | ~$1-2/h × 3-4h ≈ $5-8 | 3-4h | 끊김 X | ✅ 빠름·안정 |
| 5 | Colab Free | $0 | T4 8-12h | 12h 세션·disconnect 위험 | ⚠️ 위험 |
| 6 | Kaggle Notebook | $0 (주 30h 한도) | T4 8-12h | 9h 세션 | ⚠️ |
| 7 | Orin (사용자 기보유) | $0 | 수십 시간 (작은 GPU) | 안정 | △ 학습엔 비추 (추론 전용 권장) |

**선택 가이드**:
- 이미 접근 가능한 *로컬 PC* 있으면 → #1 (비용·속도·안정 모두 최선)
- 없고 *결제 OK* → #2 (Colab Pro, 단순) 또는 #3/#4 (클라우드, 가성비)
- *무료 만* → #5/#6 (단 시간 부담 + disconnect 대비)

---

## 2) 환경 셋업 — 어디서든 동일 (3 단계)

### 2-1. Python venv + lerobot 설치

```bash
# Python 3.10+ 권장
python -m venv .venv && source .venv/bin/activate

# lerobot + smolvla extras
pip install --upgrade pip
pip install 'lerobot[smolvla]'
# 또는 source install (최신):
# pip install git+https://github.com/huggingface/lerobot.git
```

### 2-2. 인증

```bash
# HuggingFace (dataset 다운로드 + 체크포인트 push 위해)
huggingface-cli login
# (write 권한 토큰 필요 — 체크포인트 push 하려면)

# wandb (학습 모니터링)
wandb login
```

### 2-3. dataset 준비 — *이미 완료, 추가 작업 0*

`BaboGaeguri/leftarm_v2` (110 episodes, h264_nvenc) 가 HF Hub 에 push 돼있음. 학습 시 `lerobot-train --dataset.repo_id=BaboGaeguri/leftarm_v2` 로 *자동 다운로드*.

→ devPC ↔ 학습 환경 데이터 전송 불필요. dataset 은 HF Hub 가 single source.

---

## 3) 학습 명령 — 일반 환경 표준

```bash
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --policy.device=cuda \
    --policy.dtype=bfloat16 \
    --policy.push_to_hub=true \
    --policy.repo_id=BaboGaeguri/smolvla_leftarm_v2 \
    \
    --dataset.repo_id=BaboGaeguri/leftarm_v2 \
    --dataset.episodes='[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99]' \
    \
    --batch_size=64 \
    --steps=20000 \
    --num_workers=8 \
    --save_freq=1000 \
    --log_freq=50 \
    \
    --peft.method_type=LORA \
    --peft.target_modules=all-linear \
    --peft.r=16 \
    \
    --wandb.enable=true \
    --wandb.project=leftarm_v2 \
    --wandb.entity=babogaeguri-hanyang-university \
    \
    --output_dir=outputs/leftarm_v2_2a \
    --job_name=leftarm_v2_2a \
    \
    --rename_map='{"observation.images.top":"observation.images.camera1", "observation.images.wrist":"observation.images.camera2"}'
```

### 3-1. 명령 인자 *의미*

| 인자 | 값 | 이유 |
|---|---|---|
| `policy.path` | `lerobot/smolvla_base` | 사전학습 체크포인트 |
| `policy.dtype` | `bfloat16` | best practice 권장 — 메모리 절반, 정확도 영향 0 |
| `policy.push_to_hub` | `true` | 학습 완료 시 체크포인트 자동 HF Hub push (회수 단순) |
| `policy.repo_id` | `BaboGaeguri/smolvla_leftarm_v2` | push 대상 repo (없으면 자동 생성) |
| `dataset.episodes` | `[0..99]` | 2A subset (task1: 50ep, task2: 50ep, 양 task front:back = 30:20) |
| `batch_size` | `64` | A100 / RTX 3090 일반값 (공식 권장). 메모리 부족 시 32 또는 16 으로 ↓ |
| `steps` | `20000` | best practice 표준 (~5 epoch) |
| `num_workers` | `8` | 분리 메모리 환경 default (DGX UMA 와 달리 안전) |
| `save_freq` | `1000` | 20 ckpt 생성 (디스크·분해능 균형) |
| `peft.*` | LoRA r=16 all-linear | v1 검증 + best practice |
| `rename_map` | top→camera1, wrist→camera2 | smolvla 가 `observation.images.camera{N}` 키 기대 (필수) |

### 3-2. DGX 와 다른 *핵심 차이*

| 항목 | DGX (legacy) | 일반 환경 (본 가이드) |
|---|---|---|
| `dataset.video_backend` | `pyav` 강제 | **자동 (torchcodec)** — 명시 X |
| `num_workers` | `2` (UMA 보수) | **`8`** (분리 메모리 default) |
| `prefetch_factor` | `1` | **default `4`** (명시 안 함) |
| `persistent_workers` | `false` | **default `true`** |
| `batch_size` | `16` | **`64`** (GPU 메모리 충분) |
| `policy.dtype` | 미명시 | **`bfloat16`** 명시 |
| `push_to_hub` | `false` (수동) | **`true`** (자동) |

→ 7 항목 차이. *DGX 의 모든 우회로* 가 *일반 환경에선 무의미* — 표준 lerobot 명령으로 충분.

---

## 4) 환경별 구체 셋업

### 4-1. Colab Pro

```python
# Colab 노트북 셀
!pip install 'lerobot[smolvla]' wandb -q

from google.colab import userdata
import os
os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')
os.environ['WANDB_API_KEY'] = userdata.get('WANDB_API_KEY')

!huggingface-cli login --token $HF_TOKEN --add-to-git-credential
!wandb login $WANDB_API_KEY

!lerobot-train --policy.path=lerobot/smolvla_base ...  # 위 §3 명령 그대로
```

**팁**:
- Colab Pro: A100 배정 받으려면 *high RAM* 옵션. 못 받으면 V100 (16GB) 도 가능 (batch 32 로 ↓).
- 세션 유지: `!nohup ... &` 백그라운드 가능. 또는 *Colab Pro+* (24h 백그라운드).
- 체크포인트 push 활성화로 ckpt 자동 회수.

### 4-2. Lambda / RunPod 클라우드

```bash
# 인스턴스 SSH 접속 후
sudo apt update && sudo apt install -y git ffmpeg
git clone https://github.com/<your-fork-or-clone-repo>  # 또는 dataset 만 다운로드라 git 불요

python -m venv .venv && source .venv/bin/activate
pip install 'lerobot[smolvla]'
huggingface-cli login  # 토큰 입력
wandb login            # API key 입력

lerobot-train ... # 위 §3 명령
```

**팁**:
- 인스턴스 종료 시 데이터 사라짐 — `--policy.push_to_hub=true` 필수 (ckpt 회수 보장)
- 시간 절약: ckpt 충분히 받으면 인스턴스 종료 (요금 절약)
- spot instance 가능한 곳 (Vast.ai 등) 은 더 저렴 but 끊김 위험

### 4-3. 로컬 PC (학원·연구실 GPU)

```bash
# 일반 Linux/Mac/WSL
python -m venv .venv && source .venv/bin/activate
pip install 'lerobot[smolvla]'
huggingface-cli login
wandb login

lerobot-train ... # 위 §3
```

**팁**:
- 다른 사용자와 GPU 공유라면 `nvidia-smi` 로 점유 확인
- 야간/주말 학습 권장 (다른 사용자 영향 X)
- `tmux` 또는 `screen` 으로 백그라운드 (SSH 끊겨도 학습 계속)

---

## 5) 체크포인트 회수 → Orin 배포

### 5-1. 학습 완료 후 자동 HF Hub push

`--policy.push_to_hub=true` 활성 시 학습 완료 시점에 ckpt 가 `BaboGaeguri/smolvla_leftarm_v2` 에 자동 push.

또는 학습 중간 ckpt (save_freq=1000) 도 wandb artifact 에 자동 업로드 (`--wandb.disable_artifact=false`, default).

### 5-2. Orin 에서 ckpt 다운로드

```bash
# Orin SSH 접속
ssh orin

# venv 활성화 (orin 의 lerobot 환경)
source ~/smolvla/orin/.hylion_arm/bin/activate

# HF Hub 에서 ckpt 다운로드 (한 번)
huggingface-cli download BaboGaeguri/smolvla_leftarm_v2 \
    --local-dir ~/smolvla/orin/checkpoints/smolvla_leftarm_v2

# config.json 의 n_action_steps 확인·수정 (best practice 보고서 §1-3 경고)
grep "n_action_steps" ~/smolvla/orin/checkpoints/smolvla_leftarm_v2/config.json
# 1 이면 50 으로 수동 변경:
# (jq 또는 vim 으로 "n_action_steps": 1 → "n_action_steps": 50)
```

### 5-3. Orin 추론

```bash
# lerobot eval 모드 또는 inference 스크립트
# (orin/ 의 기존 추론 파이프라인 활용)
```

---

## 6) 학습 모니터링 체크리스트

학습 시작 후 wandb 에서 관찰 (`https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/<run_id>`):

| 메트릭 | 기대값 | 이상 신호 |
|---|---|---|
| `loss` | 0.5 이하로 하강 | plateau 0.5+ → LR 또는 데이터 점검 |
| `grad_norm` | 0.1-10 | 급등 (>100) → LR 너무 높음, NaN 전조 |
| `data_load_time` | < `step_time` | data > step → workers 부족 (단 일반 환경에선 드뭄) |
| `system/memory.percent` | 안정 (90% 미만) | 시간 비례 증가 → leak 신호 (DGX 패턴 X 일반 환경에선 거의 X) |
| `system/gpu.utilization` | > 70% | < 50% → dataloader bottleneck |
| `step_time` variance | 낮음 | 큰 변동 → I/O 문제 |

**정상 동작 기대치** (RTX 3090 / A100 + torchcodec):
- `step_time`: 0.5-1.5s
- `data_load_time`: < 0.5s
- `gpu.utilization`: 80%+
- 20K step → 3-6h

---

## 7) 트러블슈팅

### 7-1. 학습 시작 안 됨 — `Key 'observation.images.camera1' not found`

→ `--rename_map` 누락. 위 §3 명령의 rename_map 인자 반드시 포함.

### 7-2. CUDA OOM (batch 64 에서)

→ batch 32 또는 16 으로 ↓:
```bash
--batch_size=32
```

### 7-3. wandb 권한 오류

→ entity 가 다른 경우. `wandb.entity` 인자 확인 (개인이면 자기 username, team 이면 team name).

### 7-4. HF Hub push 실패 — `403 Forbidden`

→ `huggingface-cli login` 시 *write* 권한 토큰 필요. `https://huggingface.co/settings/tokens` 에서 write 토큰 생성.

### 7-5. n_action_steps 함정 (Orin 추론 시)

→ Hub 의 `smolvla_base` 의 `config.json` 에 `n_action_steps=1` 박혀있음 (커뮤니티 알려진 함정). 학습 후 push 된 ckpt 의 config.json 도 동일할 수 있음. Orin 추론 전 50 으로 수동 변경:
```bash
# config.json 의 "n_action_steps": 1 → 50
```

---

## 8) 우리 leftarm_v2 사이클에의 적용 — *다음 spec (M2) 의 baseline*

본 가이드는 *다음 M2 spec 재작성* 의 입력 자료. spec 의 구조:

```
M2 — 학습 (일반 환경)
├── TODO-1: GPU 환경 결정 (사용자) → 본 가이드 §1 의 옵션 중 선택
├── TODO-2: 환경 셋업 (본 가이드 §2)
├── TODO-3: 학습 실행 (본 가이드 §3, dry-run 후 본 학습)
├── TODO-4: 체크포인트 회수 → Orin 배포 (본 가이드 §5)
└── TODO-5: Orin smoke 추론 (사이클 검증)
```

각 TODO 의 *구체적 명령·검증 절차* 는 본 가이드 §2-§7 참조.

---

## 9) DGX 의 *나중* 정착 (Backlog)

본 가이드는 *일반 환경 표준*. DGX Spark 의 우회로 정착은 별도 *장기 backlog*:

- lerobot v0.6 release (torchcodec 완전 마이그레이션) → DGX 의 torchcodec wheel 호환되면 본 가이드 그대로 DGX 에서 사용 가능
- 또는 PyTorch / FFmpeg / torchcodec 의 aarch64 + GB10 (sm_121) 정식 지원 — 외부 조건 의존
- 그 때까지 학습 = 본 가이드 (일반 환경), DGX = 수집 + 시연장 운영 전용

---

## Sources

본 가이드는 다음 자료의 종합:
- `docs/storage/legacy/realplaying/train_troubleshooting/` — M1.5 우회로 시도 history
- `docs/work_flow/context/history/02_prereq_dataset_video_to_image/research/lerobot_smolvla_training_best_practice.md` — 공식 + 커뮤니티 best practice
- `docs/work_flow/context/history/02_prereq_dataset_video_to_image/research/m1.5_video_decode_oom.md` — DGX OOM 진단
- 외부:
  - [SmolVLA 공식 docs](https://huggingface.co/docs/lerobot/en/smolvla)
  - [lerobot PEFT docs](https://huggingface.co/docs/lerobot/en/peft_training)
  - [SmolVLA paper (arxiv 2506.01844)](https://arxiv.org/abs/2506.01844)
