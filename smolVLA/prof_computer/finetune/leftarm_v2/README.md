# prof_computer / leftarm_v2 — 학습 entry (DGX 학습 잠정 중단 후 단독 책임 노드)

> **역할**: leftarm_v2 fine-tune 학습 *전담*. DGX 는 데이터 수집 전용 ([dgx/legacy/train_trial_2026-05-17/README.md](../../../dgx/legacy/train_trial_2026-05-17/README.md) — 학습 중단 사유 참조).
> **학습 방법 결정 근거**: [model_config.md](../../docs/model_config.md). 본 노드 학습 기록: [learning_log.md](../../docs/leftarm_v2/learning_log.md).

---

## 1) 노드 구성

| 항목 | 값 |
|---|---|
| 호스트 | `DESKTOP-G8LO9C5` (Windows 10 + WSL2 Ubuntu 22.04) |
| GPU | RTX 3090 24GB (분리 VRAM) |
| Python | 3.12 (`.venv_arm_finetune`) |
| 데이터셋 | HF Hub `BaboGaeguri/leftarm_v2` (DGX 가 수집·push, prof_computer 가 read-only 학습) |

## 2) 분기 entry 구조 — *분기별 단일 변수 비교* 컨벤션

학습 분기마다 *wrapper + config* 1쌍씩 분리. 분기 정의·결정 근거는 [model_config.md](../../docs/model_config.md) §2 매트릭스.

| 분기 | wrapper | config (본 학습) | config (smoke) | run name prefix |
|---|---|---|---|---|
| **M1.5 baseline** (A2: LoRA r=16 all-linear) | `run_train.py` | `config/train_config.yaml` | `config/train_config_smoke.yaml` | `leftarm_v2_2a_pc_<ts>` |
| **camera_empty** (M1.5 + `empty_cameras: 1`) | `run_train_camera_empty.py` | `config/train_config_camera_empty.yaml` | `config/train_config_camera_empty_smoke.yaml` | `leftarm_v2_camera_empty_2a_pc_<ts>` |
| (향후 신규 분기) | `run_train_<branch>.py` | `config/train_config_<branch>.yaml` | `config/train_config_<branch>_smoke.yaml` | `leftarm_v2_<branch>_2a_pc_<ts>` |

**컨벤션 원칙**:
- 분기 = *단일 변수* 변경 (비교 깔끔)
- 분기 entry 신설 시 *원본 파일 *수정 금지*** — 별도 파일 신설로 회귀 위험 0
- 본 README 표에 분기 추가 + 결정 근거는 model_config.md §2 매트릭스 행 추가

## 3) 학습 실행 절차

```bash
# 1. venv 활성화 (HF_HOME / PYTORCH_CUDA_ALLOC_CONF / CUDA_VISIBLE_DEVICES 자동 export)
source /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/.venv_arm_finetune/bin/activate

# 2. HF / wandb 로그인 확인 (최초 1회)
hf auth whoami
cat ~/.netrc | grep -A2 wandb

# 3. 작업 디렉터리 이동
cd /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/finetune/leftarm_v2

# 4. 분기 선택 (예: M1.5 baseline)
#    dry-run 으로 명령 점검
python run_train.py train --pass 2a --dry-run

# 5. smoke (100 step, ~1분)
python run_train.py train --pass smoke

# 6. smoke 통과 시 본 학습 (75000 step, ~7-8시간)
python run_train.py train --pass 2a
```

분기별 실행: 같은 패턴, wrapper 파일명만 변경.
- camera_empty 분기: `python run_train_camera_empty.py train --pass smoke|2a`

## 4) 학습 산출물 경로

| 산출 | 경로 |
|---|---|
| ckpt + 학습 로그 | `~/prof_computer_runs/<run_name>/` (WSL2 home — Windows 측 mount 아님) |
| wandb 동기화 | `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/<id>` |
| metrics CSV (학습 후 자동) | `~/prof_computer_runs/<run_name>/metrics.{scalar,system}.csv` |

## 5) DGX 와의 분담 (2026-05-18 분리 후)

| 책임 | DGX | prof_computer |
|---|---|---|
| 데이터 수집 (record/teleop) | ✅ 전담 | ❌ |
| 학습 (train) | ❌ 잠정 중단 (legacy) | ✅ 전담 |
| 추론 (Orin 배포·평가) | ❌ | (Orin 노드 별도 — prof_computer 가 ckpt push) |
| dataset Hub | DGX 가 push | prof_computer 가 read |

→ DGX 학습 재진입 조건은 [`dgx/legacy/train_trial_2026-05-17/README.md`](../../../dgx/legacy/train_trial_2026-05-17/README.md) §5 참조.
