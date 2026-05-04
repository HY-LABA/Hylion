# TODO-D2 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`dgx/interactive_cli/flows/training.py` 학습 mode 회귀 검증 — ckpt 케이스 4건 분기 코드 추가 + prod-test-runner 인계 검증 명령 시퀀스 작성.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/training.py` | M | `_select_start_ckpt()` 신규 + `_run_real_training()` ckpt 4건 분기 통합 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (Category A 준수)
- Coupled File Rule: `dgx/lerobot/` 미변경 → 04_dgx_lerobot_diff.md 갱신 불요
- Category B 비해당: `dgx/interactive_cli/flows/` 는 lerobot upstream 아님
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/configs/train.py`
    - `resume: bool = False` (L49)
    - `checkpoint_path: Path | None = field(init=False, default=None)` (L84)
    - `elif self.resume: self.checkpoint_path = policy_dir.parent` (L94~111)
    - → resume 시 `--resume --config_path=<last>/pretrained_model/train_config.json` 패턴
  - `dgx/scripts/smoke_test.sh` — preflight, save_checkpoint=false, steps=1 인용
  - `dgx/scripts/save_dummy_checkpoint.sh` — OUTPUT_DIR 경로, save_checkpoint=true 인용
  - `dgx/scripts/preflight_check.sh` — 5단계 (env·CUDA·Walking RL·Ollama·디스크) 구조 확인
  - `dgx/interactive_cli/flows/mode.py` — G-4 단발 종료 분기 확인

## Step 1 — 학습 mode 코드 분기 정합 결과

### py_compile 검증

```
python3 -m py_compile dgx/interactive_cli/flows/training.py  → PASS
python3 -m py_compile dgx/interactive_cli/flows/mode.py      → PASS
python3 -m py_compile dgx/interactive_cli/flows/entry.py     → PASS
python3 -m py_compile dgx/interactive_cli/flows/env_check.py → PASS
python3 -m py_compile dgx/interactive_cli/flows/teleop.py    → PASS
python3 -m py_compile dgx/interactive_cli/flows/data_kind.py → PASS
python3 -m py_compile dgx/interactive_cli/flows/record.py    → PASS
python3 -m py_compile dgx/interactive_cli/flows/transfer.py  → PASS
```

### ckpt 케이스 4건 분기 — 신규 추가 (`_select_start_ckpt()`)

spec DOD 의 "ckpt 케이스 4건 (none / dummy / 실 fine-tune step / fine-tune last)" 분기는 기존 코드에 없었음 (기존 코드는 항상 `--policy.path=lerobot/smolvla_base` 고정). 분기 UI를 신규 추가하고 `_run_real_training()` 에 통합.

| 케이스 | lerobot-train 인자 | T2 의존 여부 |
|---|---|---|
| none | `--policy.path=lerobot/smolvla_base` | 없음 (사전학습 시작) |
| dummy | `--policy.path=<dgx_dir>/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model` | 없음 (save_dummy_checkpoint.sh 산출물) |
| fine-tune-step | `--policy.path=<step>/pretrained_model` (사용자 경로 입력) | T2 의존 (D2 시점엔 분기만 검증) |
| fine-tune-last | `--resume --config_path=<last>/pretrained_model/train_config.json` | T2 의존 (D2 시점엔 분기만 검증) |

레퍼런스 근거:
- `--resume` 플래그: `train.py L49 resume: bool = False`
- `config_path` 해석: `train.py L94-111` — `elif self.resume: self.checkpoint_path = policy_dir.parent`

### G-4 prompt 분기 정합

`mode.py` 의 G-4 단발 종료 케이스:
- `flow3_mode_entry()` → 수집 완주 → `_prompt_transition_to_train()` → Y 선택 → `run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)` 호출
- 단발 종료 구조: `return _prompt_transition_to_train(...)` — 루프 없음 (mode 완료 후 즉시 종료)
- `run_training_flow_with_dataset` 내 `_select_start_ckpt()` 호출 경로 포함 (s1/s3/lora 시나리오 선택 → ckpt 분기 → 실 학습)

### SCENARIOS memory_gb vs preflight_check.sh 정합

```
smoke: 20 GB == preflight_check.sh L24 REQUIRED_GB=20  ✓
s1:    35 GB == preflight_check.sh L25 REQUIRED_GB=35  ✓
s3:    65 GB == preflight_check.sh L26 REQUIRED_GB=65  ✓
lora:  28 GB == preflight_check.sh L27 REQUIRED_GB=28  ✓
```

## Step 2 — prod-test-runner 인계 검증 명령 시퀀스

### preflight 검증 (SSH_AUTO)

```bash
# DGX SSH 에서 비대화형 실행
ssh dgx "cd ~/smolvla && source dgx/.arm_finetune/bin/activate && \
    HF_HOME=~/smolvla/.hf_cache CUDA_VISIBLE_DEVICES=0 \
    bash dgx/scripts/preflight_check.sh smoke"
# 기대: preflight PASS — 학습 진행 가능 (exit 0)
# 항목: [1/5] venv, [2/5] 메모리(>30GB), [3/5] Walking RL, [4/5] Ollama, [5/5] 디스크
```

### save_dummy_checkpoint 검증 (SSH_AUTO)

```bash
# DGX SSH 에서 실행 (5~15분 소요 — >5분 → 사용자 동의 필요)
ssh dgx "cd ~/smolvla && source dgx/.arm_finetune/bin/activate && \
    HF_HOME=~/smolvla/.hf_cache CUDA_VISIBLE_DEVICES=0 \
    bash dgx/scripts/save_dummy_checkpoint.sh"
# 기대: exit 0 + 체크포인트 생성
# 산출물 확인:
ssh dgx "ls ~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/"
# 기대: config.json, train_config.json, model.safetensors (≈900MB) 3개 파일
```

### smoke_test 검증 (SSH_AUTO — >5분, >100MB 다운로드)

```bash
# 주의: 5~15분 소요 + svla_so100_pickplace ~100MB 다운로드 → 사용자 동의 필요
# (CLAUDE.md §prod-test-runner 자율성: 큰 다운로드·긴 실행 → 사용자 동의)
ssh dgx "cd ~/smolvla && source dgx/.arm_finetune/bin/activate && \
    HF_HOME=~/smolvla/.hf_cache CUDA_VISIBLE_DEVICES=0 \
    bash dgx/scripts/smoke_test.sh"
# 기대: exit 0 + "smoke test 결과" 출력 (소요 시간·GPU util·메모리 출력)
# 주의: HF Hub 접근 필요 — 학교 WiFi 차단 시 T1 fallback 결정 적용
```

### training.py 정적 검증 (SSH_AUTO 또는 devPC)

```bash
# devPC 에서 정적 검증
python3 -m py_compile dgx/interactive_cli/flows/training.py
python3 -c "
import sys; sys.path.insert(0, 'dgx/interactive_cli')
import flows.training as t
assert list(t.CKPT_CASES.keys()) == ['1','2','3','4']
assert list(t.SCENARIOS.keys()) == ['smoke','s1','s3','lora']
assert hasattr(t, '_select_start_ckpt')
assert hasattr(t, '_smoke_consent_gate')
assert hasattr(t, 'run_training_flow')
assert hasattr(t, 'run_training_flow_with_dataset')
print('ALL ASSERTIONS PASS')
"
```

## Step 3 — HF Hub 의존 분리 명시

| 항목 | 본 D2 범위 | 의존 todo |
|---|---|---|
| lerobot/svla_so100_pickplace 다운로드 | 제외 (HF Hub 접근 필요) | T1 |
| svla_so100_pickplace 기반 2,000 step fine-tune | 제외 | T2 |
| ckpt fine-tune-step / fine-tune-last 실 실행 검증 | 제외 (T2 산출물 의존) | T2 완료 후 |
| save_dummy_checkpoint (1 step, ckpt O) | 포함 (SSH_AUTO) | 없음 |
| smoke_test (1 step, ckpt X) | 포함 (SSH_AUTO — >5분 동의 필요) | T1 (HF Hub 접근) |

## Step 4 — 05 X3 통합 분 처리

spec 의 "05 X3 smoke_test·save_dummy·ckpt 케이스 검증 통합" 은 다음과 같이 처리됨:
- smoke_test: Step 2 의 smoke_test 검증 명령 시퀀스에 통합 (SSH_AUTO)
- save_dummy: Step 2 의 save_dummy_checkpoint 검증에 통합 (SSH_AUTO)
- ckpt 케이스: Step 1 의 training.py `_select_start_ckpt()` 4건 분기 코드로 통합
  - 05 X3 NEEDS_USER_VERIFICATION 항목: 코드 분기는 완료, 실 실행은 T2 의존

## 변경 내용 요약

기존 training.py 의 `_run_real_training()` 은 항상 `--policy.path=lerobot/smolvla_base` 를 고정 사용했다. spec D2 DOD 요구 — "ckpt 케이스 4건 (none/dummy/실 fine-tune step/fine-tune last) 분기 코드 정합" — 을 충족하기 위해 `_select_start_ckpt()` 함수를 신규 추가하고 `_run_real_training()` 에 통합했다.

lerobot upstream `train.py` 레퍼런스 기반으로 `--resume + --config_path` (fine-tune-last) 와 `--policy.path` (none/dummy/step) 두 경로를 정확하게 구현했다. 실 fine-tune 케이스(step·last)는 T2 산출물 의존이므로 D2 시점에서는 코드 분기 정합만 검증하며, 실 실행은 T2 완료 후 진행한다.

## verification_queue D 그룹 마킹 사항

| 항목 | 환경 레벨 | 의존 |
|---|---|---|
| training.py py_compile PASS | AUTO_LOCAL | 없음 — 완료 |
| ckpt 케이스 4건 분기 코드 정합 | AUTO_LOCAL | 없음 — 완료 |
| G-4 prompt 분기 정합 | AUTO_LOCAL | 없음 — 완료 |
| preflight 5단계 PASS | SSH_AUTO | DGX SSH 접근 |
| save_dummy_checkpoint 실행 + 산출물 존재 | SSH_AUTO | DGX SSH + HF Hub (최초 실행 시) |
| smoke_test 1 step PASS | SSH_AUTO | DGX SSH + HF Hub (~100MB, 5~15분) — T1 HF Hub 접근 선결 |
| ckpt none 케이스 실 실행 (사전학습 시작) | SSH_AUTO | save_dummy 후 |
| ckpt dummy 케이스 실 실행 | SSH_AUTO | save_dummy 산출물 |
| ckpt fine-tune-step 케이스 실 실행 | SSH_AUTO | T2 산출물 의존 |
| ckpt fine-tune-last 케이스 실 실행 | SSH_AUTO | T2 산출물 의존 |

## code-tester 입장에서 검증 권장 사항

- py_compile: `python3 -m py_compile dgx/interactive_cli/flows/training.py` → PASS
- ruff lint: `python3 -m ruff check dgx/interactive_cli/flows/training.py`
- 구조 검증:
  ```python
  import sys; sys.path.insert(0, 'dgx/interactive_cli')
  import flows.training as t
  assert hasattr(t, '_select_start_ckpt')
  assert list(t.CKPT_CASES.keys()) == ['1','2','3','4']
  assert list(t.SCENARIOS.keys()) == ['smoke','s1','s3','lora']
  ```
- DOD 항목 체크리스트:
  1. `_select_start_ckpt()` 반환 타입: `tuple[str, str | None, str | None]` (ckpt_case, policy_path, config_path)
  2. fine-tune-last 분기: `is_resume=True` → `--resume --config_path=...` cmd 생성 확인
  3. G-4 분기: `mode.py._prompt_transition_to_train()` → `run_training_flow_with_dataset()` 호출 확인
  4. HF Hub 의존 분리: smoke_test 경로에 `_smoke_consent_gate()` 동의 게이트 존재 확인
  5. lerobot 레퍼런스 인용 정합: `--resume` 플래그 `train.py L49`, `config_path` 패턴 `train.py L94-111`
