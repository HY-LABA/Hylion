# 14_dgx_cli_flow.md

> 작성: 2026-05-01 | task-executor | TODO-X1 study cycle 1
> 목적: dgx/interactive_cli/flows/training.py 의 설계 입력.
>       X2 task 는 본 문서의 §3~§6 결정(사용자 합의 후)대로 구현한다.

---

## §1 flow 2 (환경 체크 — preflight_check.sh 활용) 동작

### 1-1) 위치

F1 boilerplate (entry.py flow 0·1) 이후 `env_check.py` 가 담당.
dgx 의 `env_check.py` 는 `preflight_check.sh` 를 subprocess 로 호출하는 래퍼.

### 1-2) preflight_check.sh 직접 Read 결과 (인용)

`dgx/scripts/preflight_check.sh` line 1~36 인용:

```bash
# 사용:
#   bash preflight_check.sh smoke   # 1 step 검증용 (필요 메모리 20 GB)
#   bash preflight_check.sh s1      # 04 / 06 1차 학습 (35 GB)
#   bash preflight_check.sh s3      # 06 2차 학습 — VLM 까지 풀 학습 (65 GB)
#   bash preflight_check.sh lora    # LoRA fallback (28 GB)
#
# 통과 조건 (모두 만족해야 exit 0):
#   1. HF_HOME 격리 경로로 설정됨
#   2. venv 가 활성화돼 있고 SmolVLA venv 임
#   3. 가용 메모리(가용 RAM = MemAvailable) >= 필요 메모리 + 안전 마진(10 GB)
#   4. Walking RL 프로세스가 보호 정책 준수 (정보 출력만, 절대 kill X)
#   5. Ollama gemma3 미로드 (또는 사용자 명시 동의)
```

5가지 체크 항목:
| # | 체크 | FAIL 조건 |
|---|---|---|
| 1 | venv / 환경변수 격리 | VIRTUAL_ENV 미일치 또는 HF_HOME 미설정 또는 CUDA_VISIBLE_DEVICES != "0" |
| 2 | 메모리 가용성 | MemAvailable < REQUIRED_GB + 10 GiB 안전 마진 |
| 3 | Walking RL 프로세스 | 관찰만, kill 절대 금지 (FAIL 아님 — INFO 출력) |
| 4 | Ollama GPU 점유 | nvidia-smi 에 ollama 프로세스 있으면 FAIL |
| 5 | 디스크 가용량 | /home/laba 가용 < 50 GiB |

### 1-3) env_check.py 구현 패턴 (X2 입력)

F1 §5 (`docs/storage/12_interactive_cli_framework.md`) 의 orin env_check.py 패턴을 dgx 에 맞게 변형:

```python
# dgx/interactive_cli/flows/env_check.py — X2 구현 시 참고
import subprocess, sys
from pathlib import Path

def run_env_check(script_dir: Path, scenario: str = "smoke") -> bool:
    """preflight_check.sh 를 subprocess 로 호출.

    Args:
        script_dir: interactive_cli/ 디렉터리 경로
        scenario:   "smoke"|"s1"|"s3"|"lora" (사용자가 선택하거나 기본값 smoke)

    Returns:
        True: preflight PASS / False: FAIL
    """
    preflight = script_dir.parent / "scripts" / "preflight_check.sh"
    result = subprocess.run(
        ["bash", str(preflight), scenario],
        check=False
    )
    return result.returncode == 0
```

비고: `setup_train_env.sh` (line 51: `source "${VENV_DIR}/bin/activate"`) 는 flow 2 이전에 main.sh 에서 이미 호출됨. env_check 에서 재호출 불필요.

---

## §2 flow 3~ 후보 옵션 정리

### 2-1) 분석 기반

직접 Read 한 스크립트:
- `dgx/scripts/preflight_check.sh` — 5체크 게이트
- `dgx/scripts/smoke_test.sh` — lerobot-train --steps=1 (5~15분, 다운로드 포함)
- `dgx/scripts/save_dummy_checkpoint.sh` — --save_checkpoint=true steps=1
- `scripts/sync_ckpt_dgx_to_datacollector.sh` — 케이스 3 우회 전송
- `docs/storage/09_dgx_structure.md` — dgx/ 책임 매트릭스

### 2-2) 후보 A — 4단계 순차

```
flow 3: preflight 재확인 (시나리오 선택 포함)
flow 4: 데이터셋 선택 (HF Hub repo_id / 로컬 rsync 결과 중 선택)
flow 5: 학습 trigger (smoke → 실 학습 분기, 사용자 동의 게이트 포함)
flow 6: 체크포인트 관리 (저장 경로 확인 + sync_ckpt 호출 분기)
```

특징:
- 각 단계가 명확히 분리 → 단계별 재실행·스킵 쉬움
- 사용자가 flow 5 직전에 명시적 동의 → smoke_test 5~15분 + 다운로드 제어 가능
- flow 6 에서 sync_ckpt_dgx_to_datacollector 호출 여부를 사용자가 결정

### 2-3) 후보 B — 2단계 통합

```
flow 3: preflight + 학습 trigger 통합
         (preflight 통과 즉시 smoke 또는 실 학습 시작 — 사용자 동의 1회)
flow 4: ckpt 관리 (로컬 확인 + 전송 분기)
```

특징:
- 단계 수 감소 → UX 단순
- 데이터셋 선택·ckpt 전송은 CLI 외부 (인자로 직접 지정) → 숙련 사용자에 적합
- smoke_test 5~15분 실행이 통합 게이트에 숨겨짐 → 첫 사용자에게 불명확

### 2-4) 후보 C — 3단계 (환경 + 데이터셋 + 학습·ckpt 통합)

```
flow 3: preflight 재확인 + 시나리오 선택 (smoke/s1/s3/lora)
flow 4: 데이터셋 선택 (HF Hub repo_id / 로컬)
flow 5: 학습 + ckpt 관리 통합
         smoke 선택 시 → smoke_test.sh 호출 (동의 게이트 포함)
         실 학습 선택 시 → lerobot-train 직접 호출 + --save_checkpoint=true + ckpt 전송 분기
```

특징:
- 데이터셋 선택을 명시적으로 분리 (HF Hub / 로컬 datacollector/ rsync 결과)
- 학습·ckpt 관리를 flow 5 한 단계에서 처리 → 흐름이 자연스러움
- smoke test 사용자 동의 게이트를 flow 5 시작 시 노출

### 2-5) 옵션 비교 표

| 항목 | 후보 A (4단계) | 후보 B (2단계) | 후보 C (3단계) |
|---|---|---|---|
| 단계 수 | 4 | 2 | 3 |
| 데이터셋 선택 UI | flow 4 포함 | CLI 외부 (인자 지정) | flow 4 포함 |
| smoke 동의 게이트 위치 | flow 5 진입 전 | flow 3 통합 (숨겨짐) | flow 5 진입 전 |
| ckpt 관리 | flow 6 분리 | flow 4 통합 | flow 5 통합 |
| 숙련도 요구 | 낮음 (안내 충분) | 높음 (인자 직접 지정) | 중간 |
| X2 구현 복잡도 | 높음 | 낮음 | 중간 |

---

## §3 데이터셋 선택 메커니즘 (§4 학습 trigger 전 입력)

### 3-1) 후보 소스

| 소스 | 형식 | 레퍼런스 |
|---|---|---|
| HF Hub repo_id | `lerobot/svla_so100_pickplace` 형식 | smoke_test.sh line 68: `--dataset.repo_id=lerobot/svla_so100_pickplace` |
| 로컬 rsync 결과 | `~/smolvla/dgx/datasets/<name>` | 09_dgx_structure.md §4-3 (HF Hub vs rsync 직접 — T1 미결) |
| 04 T1 dummy push 결과 | `<HF_USER>/dummy_so100_...` | T1 DataCollector push_dataset_hub.sh — HF Hub 경로 |

### 3-2) smoke_test.sh 의 하드코드 데이터셋

`smoke_test.sh` line 68~69 인용:
```bash
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=lerobot/svla_so100_pickplace \
```

smoke test 는 고정 데이터셋 (`lerobot/svla_so100_pickplace`) 사용. 최초 실행 시 100MB 이상 다운로드 가능 — CLAUDE.md §prod-test-runner 자율성 "큰 다운로드 (>100MB) 는 사용자 동의 필요" 해당.

### 3-3) 실 학습 데이터셋 선택 UI 후보

후보 A (대화형 입력):
```
어떤 데이터셋으로 학습하겠습니까?
1. HF Hub repo_id 직접 입력
2. 로컬 ~/smolvla/dgx/datasets/ 에서 선택
3. 기본 smoke test 데이터셋 사용 (lerobot/svla_so100_pickplace)
```

후보 B (인자 직접 지정):
```bash
bash dgx/interactive_cli/main.sh --dataset lerobot/svla_so100_pickplace
```

후보 A 가 interactive_cli 취지에 맞음 (단계별 안내). 후보 B 는 숙련 사용자용 단축 경로로 병행 제공 가능.

### 3-4) config/dataset_repos.json 연동

`dgx/config/dataset_repos.json` (04 X2 신규 — placeholder):
- DataCollector 에서 수신하는 HF 데이터셋 repo_id 목록
- interactive_cli flow 4 에서 이 파일을 읽어 선택지로 제공 가능
- 현재 T1 미결 (HF Hub vs rsync) — 스키마 확정 후 X2 구현

---

## §4 학습 trigger (smoke_test 사용자 동의 게이트 위치 / 실 학습 호출)

### 4-1) smoke_test.sh 직접 Read 결과

`dgx/scripts/smoke_test.sh` 핵심 구조 인용:

```bash
# line 24~32: preflight → 1-step 학습
bash "${DGX_DIR}/scripts/preflight_check.sh" smoke || exit 1

# line 44~45: 소요 시간 경고
echo "  최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."

# line 68~81: lerobot-train --steps=1 --save_checkpoint=false
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=lerobot/svla_so100_pickplace \
    --steps=1 \
    --save_checkpoint=false \
    ...
```

`save_dummy_checkpoint.sh` 의 차이점 (line 63: `--save_checkpoint=true`, line 62: `--save_freq=1`):
- smoke_test → 검증 전용 (저장 X)
- save_dummy_checkpoint → ckpt 생성 목적 (저장 O)

### 4-2) 사용자 동의 게이트 위치 결정 (X1 핵심)

smoke_test.sh 호출 전 interactive_cli 내부에서 동의 게이트 포함 여부:

**포함 (권고)**: interactive_cli 가 "smoke test 는 5~15분 소요 + 최초 실행 시 svla_so100_pickplace 다운로드가 발생합니다. 계속하겠습니까? [Y/n]" prompt 제공.
- CLAUDE.md 자율성 정책 ("큰 다운로드 >100MB 사용자 동의 필요") 충족
- 사용자가 실수로 학습 trigger 방지

**미포함**: smoke_test.sh 자체 경고 메시지 (line 44~45) 에 의존.
- interactive_cli 를 통하지 않는 직접 호출과 동일한 경험

**결정 필요**: 사용자 합의 후 X2 구현에서 결정.

### 4-3) 학습 단계 분기 구조 (후보)

```
flow 5 진입 시:
  1. "smoke test 로 검증 먼저 하겠습니까, 실 학습으로 바로 진행하겠습니까?"
     → (a) smoke test: 동의 게이트 → smoke_test.sh 호출 → 결과 출력
     → (b) 실 학습:    시나리오 선택 (s1/s3/lora) → preflight (해당 메모리 기준) → lerobot-train 호출

  2. 실 학습 옵션 파라미터:
     --policy.path     (기본: lerobot/smolvla_base)
     --dataset.repo_id (§3 선택 결과)
     --steps           (사용자 입력 또는 기본값)
     --save_checkpoint (항상 true — ckpt 관리 flow 6 에서 사용)
     --output_dir      (기본: dgx/outputs/train/<run_name>)
     --wandb.enable    (사용자 선택)
```

---

## §5 체크포인트 관리 (저장·전송 — sync_ckpt_dgx_to_datacollector 호출 분기)

### 5-1) 저장 경로 구조

`save_dummy_checkpoint.sh` line 25 인용:
```bash
OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"
# 체크포인트: ${OUTPUT_DIR}/checkpoints/000001/pretrained_model/
#   - config.json
#   - train_config.json
#   - model.safetensors  (약 900 MB)
```

학습 완료 후 `dgx/outputs/train/<run_name>/checkpoints/<step>/pretrained_model/` 에 저장.

### 5-2) sync_ckpt_dgx_to_datacollector.sh 직접 Read 결과

`scripts/sync_ckpt_dgx_to_datacollector.sh` 인용:

```bash
# line 6~24: 케이스 분류
#   케이스 1: Orin 과 devPC·DGX 동일 광역 네트워크 → sync_ckpt_dgx_to_orin.sh 직접
#   케이스 2: Orin 인터넷 가능, 다른 서브넷 → sync_ckpt_dgx_to_orin.sh devPC 2-hop
#   케이스 3: Orin 인터넷 격리 → 본 스크립트 (DGX → DataCollector) + 수동 DataCollector → Orin
#   케이스 4: USB 드라이브만 가능

# 사용 (line 7~9):
#   bash sync_ckpt_dgx_to_datacollector.sh                   # 가장 최근 run last 체크포인트
#   bash sync_ckpt_dgx_to_datacollector.sh --run leftarm_v1  # 특정 run
#   bash sync_ckpt_dgx_to_datacollector.sh --dry-run         # dry-run

# 동작 (line 28~36):
#   1. SSH 로 DGX 의 체크포인트 경로 식별
#   2. DGX → devPC 임시 디렉터리 rsync
#   3. devPC → DataCollector rsync
#   4. devPC 임시 정리 + DataCollector 측 파일 크기 검증
#   5. 다음 단계 안내 (DataCollector → Orin 수동)
```

비고: `sync_ckpt_dgx_to_datacollector.sh` 는 **devPC 에서 실행** 하는 스크립트 (DGX 에서 실행 X). interactive_cli 가 DGX 에서 동작하므로, flow 6 에서 "devPC 에서 다음 스크립트를 실행하세요" 안내 출력 후 종료하는 패턴이 적합.

### 5-3) ckpt 전송 분기 UI 후보

```
학습 완료. 체크포인트가 저장되었습니다:
  경로: ~/smolvla/dgx/outputs/train/<run_name>/checkpoints/<step>/pretrained_model/

체크포인트를 Orin 에 전송하겠습니까?
1. 케이스 1·2 (Orin 과 동일 네트워크) — devPC 에서 sync_ckpt_dgx_to_orin.sh 실행
2. 케이스 3 (시연장 Orin 격리) — devPC 에서 sync_ckpt_dgx_to_datacollector.sh 실행
3. 나중에 직접 전송 (안내만)

→ 선택 결과에 따라 해당 명령 출력 + 클립보드 복사 가능 안내
```

interactive_cli (DGX 프로세스) 가 실제 rsync 를 실행하지는 않음 — devPC 에서 실행할 명령 안내만.

### 5-4) 04 T2 verification_queue 연결

04 T2 verification_queue "시연장 네트워크 케이스 분류" 는 X3 prod 에서:
- 시연장 네트워크 환경 확인 → 케이스 3 이면 `sync_ckpt_dgx_to_datacollector.sh` 실행 검증
- interactive_cli 의 flow 6 안내 메시지가 T2 검증의 사용자 절차 가이드 역할

---

## §6 awaits_user-C 발송 내용

dgx interactive_cli 의 flow 3~ 단계 구체 책임을 선택해주세요.

`dgx/scripts/{setup_train_env, preflight_check, smoke_test, save_dummy_checkpoint}.sh` 직접 Read + `docs/storage/09_dgx_structure.md` 분석 결과 다음 후보를 도출했습니다:

**(A) 4단계 순차** — preflight 재확인 (시나리오 선택) → 데이터셋 선택 (HF/로컬) → 학습 trigger (smoke·실 학습 분기, 동의 게이트 포함) → 체크포인트 관리 (저장 확인·전송 안내)

**(B) 2단계 통합** — preflight + 학습 trigger 통합 (smoke 또는 실 학습), 데이터셋·ckpt 관리는 CLI 외부 (사용자가 인자 직접 지정)

**(C) 3단계 (권고)** — preflight 재확인 + 시나리오 선택 → 데이터셋 선택 (HF Hub / 로컬) → 학습 + ckpt 관리 통합 (smoke 동의 게이트 포함)

**추가 결정 사항**:

- smoke_test 5~15분 + svla_so100_pickplace 다운로드 (>100MB 가능) 에 대한 interactive_cli 내부 동의 게이트 포함 여부
  - 포함 권고 (CLAUDE.md 자율성 정책 충족)
- 데이터셋 선택 UI 포함 여부 (후보 A·C 포함 / 후보 B 미포함)
- ckpt 전송 안내 방식 (케이스 안내 출력만 vs 케이스 자동 감지)

**영향**: X2 의 `dgx/interactive_cli/flows/training.py` 구조 결정:
- 옵션 A·C 채택 시: 데이터셋 선택 UI + smoke 동의 게이트 + ckpt 전송 안내 포함
- 옵션 B 채택 시: 최소 구조 (preflight 연동 + 결과 출력만)

---

## §7 설계 결정 요약 (사용자 합의 전 현재 상태)

| 항목 | 현재 상태 | 결정 필요 여부 |
|---|---|---|
| preflight_check.sh 호출 방식 | subprocess env_check.py 래퍼 (F1 §5 패턴) | X — 확정 |
| flow 3~ 단계 구조 | A(4단계)/B(2단계)/C(3단계) 후보 | **Y — awaits_user** |
| 데이터셋 선택 UI | 후보 A·C 포함 / 후보 B 미포함 | Y — awaits_user |
| smoke_test 동의 게이트 | 포함 권고 (CLAUDE.md §prod-test-runner) | Y — awaits_user |
| ckpt 전송 | devPC 에서 실행할 명령 안내 (CLI X) | X — 구조 확정 |
| sync_ckpt_dgx_to_datacollector | 케이스 3 전용, devPC 실행 스크립트 | X — 확정 |
| training.py 위치 | `dgx/interactive_cli/flows/training.py` | X — spec 확정 |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 05 TODO-X1 study 산출물. preflight·smoke_test·save_dummy_checkpoint·sync_ckpt_dgx_to_datacollector 직접 Read + 인용. 3 후보 (A·B·C) 도출. §6 awaits_user-C 발송 명세 포함. |
