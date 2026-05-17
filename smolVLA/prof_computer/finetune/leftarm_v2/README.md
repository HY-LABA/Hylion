# prof_computer / leftarm_v2 — DGX config 공유 + PC 전용 차이 기록

> DGX 의 [`dgx/finetune/leftarm_v2/`](../../../dgx/finetune/leftarm_v2/) config·래퍼를 그대로 사용. PC 전용 차이만 본 폴더에 기록.
> 학습 방법론 결정 근거: [model_config.md](../../../dgx/docs/finetune/leftarm_v2/model_config.md). DGX 학습 기록: [training_log.md](../../../dgx/docs/finetune/leftarm_v2/training_log.md). 본 노드 학습 기록: [../../docs/learning_log.md](../../docs/learning_log.md).

## 1) 공유하는 것 (DGX 와 동일)

| 항목 | 위치 |
|---|---|
| config (`train_config.yaml`, `base_config.yaml`) | `smolVLA/dgx/finetune/leftarm_v2/config/` |
| 실행 래퍼 (`run_train.py`) | `smolVLA/dgx/finetune/leftarm_v2/run_train.py` |
| 데이터셋 | HF Hub `BaboGaeguri/leftarm_v2` |
| 학습 방법 (LoRA r=16 / all-linear / batch 16 / steps 20000) | [model_config.md](../../../dgx/docs/finetune/leftarm_v2/model_config.md) |
| wandb (project `leftarm_v2`, entity `babogaeguri-hanyang-university`) | `base_config.yaml` |

## 2) PC 전용 차이 (필요 시만 override)

DGX config 의 값들이 **UMA 128GB 전제** 라 prof_computer (24GB VRAM 분리) 에서는 일부 조정이 필요할 수 있음. **smoke test 결과를 보고 결정**.

| 항목 | DGX 값 | PC 후보 (smoke 후 확정) | 결정 근거 |
|---|---|---|---|
| `batch_size` | 16 | 16 (1차) → VRAM 22GB 초과 시 8 | RTX 3090 24GB VRAM 제약 |
| `num_workers` | 2 (시도 2 OOM 후 축소) | 4~8 시도 가능 | system RAM 과 VRAM 분리 → workers 늘려도 GPU 영향 X |
| `prefetch_factor` | 1 | 2 시도 가능 | 동상 |
| `video_backend` | (CLI 미지정 → pyav default) | **torchcodec** | training_log.md §시도2 "시도 3 후보" 직접 적용 |
| `output_dir` | `~/smolvla/dgx/outputs/<run>/` | `~/prof_computer_runs/<run>/` | 산출물 분리 |
| `wandb run name` | `leftarm_v2_2a_<ts>` | `leftarm_v2_2a_pc_<ts>` | PC/DGX 구분 식별 |

## 3) PC 학습 실행 절차

```bash
# 1. venv 활성화 (HF_HOME / PYTORCH_CUDA_ALLOC_CONF 자동 export)
source ~/smolVLA/prof_computer/.venv_arm_finetune/bin/activate
# 또는 (Windows 경로 통한 호출 시)
source /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/.venv_arm_finetune/bin/activate

# 2. HF / wandb 로그인 확인 (최초 1회)
hf auth whoami
cat ~/.netrc | grep -A2 wandb

# 3. dry-run 으로 명령 점검
cd /mnt/c/Users/admin/Desktop/Hylion/smolVLA/dgx/finetune/leftarm_v2
python run_train.py train --pass 2a --dry-run

# 4. smoke test (steps=100, save_freq=50 임시 변경 후) — 또는 별도 PC override config 사용
#    목표: VRAM peak, system RAM 누수율, step time 측정
#    통과 기준: 100 step 정상 완주 + VRAM < 22GB + 누수율 < 500MB/min

# 5. 본 학습 (smoke 통과 후)
python run_train.py train --pass 2a
```

## 4) PC 학습 시 추가 인자 (CLI override)

`run_train.py` 는 yaml 만 읽고 추가 CLI 를 받지 않음 → **smoke test 시 임시 변경**은 두 가지 방법:

**방법 A — 임시 yaml 직접 수정** (간단):
```bash
# steps 만 100 으로
sed -i.bak 's/^steps: 20000/steps: 100/' \
    /mnt/c/Users/admin/Desktop/Hylion/smolVLA/dgx/finetune/leftarm_v2/config/train_config.yaml
# smoke 후 .bak 로 복원: mv config/train_config.yaml.bak config/train_config.yaml
```

**방법 B — output_dir / wandb run name override 용 PC 전용 래퍼** (선택, 작성 후 추가):
- `prof_computer/scripts/run_train_pc.sh` — `dgx/.../run_train.py` 를 호출 + output_dir·run_name 에 `_pc_` 접두 강제 + video_backend=torchcodec 인자 추가

## 5) torchcodec backend 인자 전달

lerobot-train 의 video backend 는 `--dataset.video_backend=torchcodec` 으로 CLI 지정 (lerobot upstream 의 dataset config 에 해당 필드 있는지 확인 필요 — smoke test 1차 실행 시 검증).

→ 검증 결과를 [../../docs/learning_log.md](../../docs/learning_log.md) "시도 1 (PC)" 에 기록.
