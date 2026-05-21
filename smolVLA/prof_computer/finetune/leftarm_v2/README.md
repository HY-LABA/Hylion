# prof_computer / leftarm_v2 — 학습 entry (DGX 학습 잠정 중단 후 단독 책임 노드)

> **역할**: leftarm_v2 fine-tune 학습 *전담*. DGX 는 데이터 수집 전용 ([dgx/legacy/train_trial_2026-05-17/README.md](../../../dgx/legacy/train_trial_2026-05-17/README.md) — 학습 중단 사유 참조).
> **학습 방법 결정 근거**: [model_config.md](../../docs/model_config.md). 본 노드 학습 기록: [learning_log1.md](../../docs/leftarm_v2/learning_log1.md) (M1.5~003 아카이브) · [learning_log2.md](../../docs/leftarm_v2/learning_log2.md) (현행).

---

## 1) 노드 구성

| 항목 | 값 |
|---|---|
| 호스트 | `DESKTOP-G8LO9C5` (Windows 10 + WSL2 Ubuntu 22.04) |
| GPU | RTX 3090 24GB (분리 VRAM) |
| Python | 3.12 (`.venv_arm_finetune`) |
| 데이터셋 | HF Hub `BaboGaeguri/leftarm_v2` (DGX 가 수집·push, prof_computer 가 read-only 학습) |

## 2) 분기 entry 구조 + 명명 컨벤션

### 명명 컨벤션 (4-계층 + 분기 토큰 룰)

분기명·run prefix·HF repo 명의 *3-계층 명명 구조* + *시간 라벨* + *토큰 룰* 정본: [prof_computer/README.md §7 명명 3-계층 + 시간 라벨](../../README.md). **신규 합류자는 본 § 진입 전 반드시 prof_computer/README §7 먼저 1회독**.

분기 디렉토리는 `branches/<NNN>_<방법>_<핵심 인자들>/` 형식. 새 분기 추가 시 본 README 표에 행 추가 + 분기별 *실행 기록·결정 흐름* 은 [learning_log2.md](../../docs/leftarm_v2/learning_log2.md) (현행) 에 entry 작성.

### 분기 표

| 분기 디렉토리 | 학습 방법 | 핵심 인자 (vs 기본값) | run name prefix | 상태 |
|---|---|---|---|---|
| `branches/001_a2_100ep/` | A2 | dataset 100ep subset (baseline) | `leftarm_v2_2a_pc_<ts>` *(legacy)* | ✅ 완료 (2026-05-17) — Orin 0/2 단축. *시기 맥락: M1.5 마일스톤* |
| `branches/002_a2_100ep_empty1/` | A2 | dataset 100ep + `empty_cameras=1` | `leftarm_v2_camera_empty_<pass>_pc_<ts>` *(legacy 별명 명명)* | ✅ 완료 (2026-05-18) — Orin 0/2 단축 (empty 단독 효과 0 확정). *별명: "camera_empty"* |
| `branches/003_a2_310ep_empty1_sched_sync_bf16_b6/` | A2 | dataset 310ep + `empty_cameras=1` + `scheduler_decay_steps=120000` (= steps 동기화) + bf16 mixed precision + `batch_size=6` | `leftarm_v2_003_<pass>_<ts>` *(현행 권장 — 분기 인덱스 직접 사용)* | ✅ 완료 (2026-05-19) — Orin 8/8 단축 = **100%** (5변수 종합 효과 확정) |
| (향후 신규 분기) | (A2 또는 다른 매트릭스 cell) | (변경된 인자 토큰) | `leftarm_v2_<NNN>_<pass>_<ts>` *(권장)* | (예정 — learning_log2.md 에 entry) |

### 운영 원칙

- **분기 = 학습 방법 + 인자 묶음** (계층 1 + 계층 2 — [prof_computer/README §7](../../README.md) 참조). *단일 변수 분기 / 묶음 분기 모두 허용*. 003 사이클에서 5변수 묶음 시도 후 *원칙적으로 묶음도 허용* 으로 정정.
- **분기 entry 신설 시 *원본 파일 수정 금지*** — 별도 디렉토리 + wrapper + config 1쌍 신설로 회귀 위험 0.
- **새 분기 추가 시**:
  1. `branches/<NNN>_<방법>_<인자 토큰>/` 디렉토리 신설
  2. 본 README 표에 행 추가
  3. [learning_log2.md](../../docs/leftarm_v2/learning_log2.md) 에 분기 entry 작성
  4. *별명 사용 지양* — 분기 인덱스 (NNN) + 인자 토큰으로 일관 (검색·grep 용이성 위해)
- **wandb run name·HF Hub repo 명** 도 *분기 인덱스 직접 사용 권장* (별명 안 섞기). 003 분기 = `leftarm_v2_003_<...>_<ts>` / HF repo = `BaboGaeguri/leftarm_v2_003_<인자 토큰>` 형식.

## 3) 학습 실행 절차

```bash
# 1. venv 활성화 (HF_HOME / PYTORCH_CUDA_ALLOC_CONF / CUDA_VISIBLE_DEVICES 자동 export)
source /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/.venv_arm_finetune/bin/activate

# 2. HF / wandb 로그인 확인 (최초 1회)
hf auth whoami
cat ~/.netrc | grep -A2 wandb

# 3. 분기 선택 — 해당 분기 디렉터리로 이동
cd /mnt/c/Users/admin/Desktop/Hylion/smolVLA/prof_computer/finetune/leftarm_v2/branches/003_a2_310ep_empty1_sched_sync_bf16_b6
# 또는: cd .../branches/001_a2_100ep / .../branches/002_a2_100ep_empty1

# 4. dry-run 점검
python run_train.py train --pass full --dry-run

# 5. smoke (100 step, ~1-2분)
python run_train.py train --pass smoke

# 6. smoke 통과 시 본 학습 (분기에 따라 7-17시간)
python run_train.py train --pass full
```

→ 모든 분기 *같은 명령 패턴* (`python run_train.py train --pass <smoke|full>`). 분기 차이 = *어느 디렉터리에서 실행* 인지뿐. 분기 디렉터리 안의 wrapper 가 *공용 _lib.py + base_config.yaml* 을 자동 import.

> **pass 명 legacy 주의**: 001 분기는 *legacy pass 명* (`--pass 2a`) 도 받음 (초기 시점 명명 잔존). 002+ 분기는 `--pass full` 로 통일됨.

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
