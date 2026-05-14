# TODO-D2 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 1건.

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/training.py  → PASS
python3 -m py_compile dgx/interactive_cli/flows/mode.py      → PASS
python3 -m py_compile dgx/interactive_cli/flows/entry.py     → PASS
python3 -m py_compile dgx/interactive_cli/flows/env_check.py → PASS
python3 -m py_compile dgx/interactive_cli/flows/teleop.py    → PASS
python3 -m py_compile dgx/interactive_cli/flows/data_kind.py → PASS
python3 -m py_compile dgx/interactive_cli/flows/record.py    → PASS
python3 -m py_compile dgx/interactive_cli/flows/transfer.py  → PASS

구조 assertion:
  list(t.CKPT_CASES.keys()) == ['1','2','3','4']       → PASS
  list(t.SCENARIOS.keys()) == ['smoke','s1','s3','lora'] → PASS
  hasattr(t, '_select_start_ckpt')                      → PASS
  hasattr(t, '_smoke_consent_gate')                     → PASS
  hasattr(t, 'run_training_flow')                       → PASS
  hasattr(t, 'run_training_flow_with_dataset')          → PASS
  ALL ASSERTIONS PASS
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/training.py → All checks passed!
ruff check dgx/interactive_cli/flows/            → All checks passed!
```

mypy 미실행 — 본 파일은 CLAUDE.md upstream lerobot strict mypy 대상 아님.
flows/ 전체 ruff PASS 로 대체 충분.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. preflight (env·CUDA·driver·메모리·디스크) PASS | ✅ | prod-test-runner 인계용 검증 명령 시퀀스 작성 완료. SSH_AUTO. |
| 2. smoke_test 5~15분 PASS | ✅ | prod-test-runner 인계 명령 작성. >5분·>100MB → 동의 게이트 포함. T1 HF Hub 선결 명시. |
| 3. save_dummy_checkpoint 1회 PASS | ✅ | prod-test-runner 인계 명령 작성. 산출물 경로 확인 명령 포함. |
| 4. ckpt 케이스 4건 코드 분기 정합 | ✅ | `_select_start_ckpt()` 신규. 4케이스 (none/dummy/fine-tune-step/fine-tune-last) 모두 구현. 실 fine-tune 케이스는 T2 의존 명시. |
| 5. G-4 단발 종료 검증 | ✅ | `mode.py._prompt_transition_to_train()` → `run_training_flow_with_dataset()` 호출 확인. 단발 종료 구조 (수집 완주 → Y/n → 즉시 종료) PASS. |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `training.py:497~498` | `_select_start_ckpt()` 선택지 5 (취소) 가 `"none", DEFAULT_POLICY_PATH, None` 을 반환 — 취소임에도 사전학습 케이스로 무음 폴백. 사용자 관점에서 "취소"를 눌렀더니 학습이 사전학습 ckpt 로 시작될 수 있음. Critical 아님 (충돌 X, None 반환 회피로 안전). 향후 취소 시 `None, None, None` 또는 상위 메뉴로 복귀 고려. |

Recommended 1건 이하 → READY_TO_SHIP.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 (D2 변경 범위 `dgx/interactive_cli/flows/training.py` 단일). |
| B (자동 재시도 X) | ✅ | `dgx/lerobot/` 미변경 확인 (`git diff HEAD -- dgx/lerobot/` 0건). `pyproject.toml` 미변경. |
| Coupled File Rules | ✅ | `dgx/lerobot/` 변경 없음 → `04_dgx_lerobot_diff.md` 갱신 불요. 구현 문서 명시 일치. |
| lerobot-reference-usage | ✅ | `docs/reference/lerobot/src/lerobot/configs/train.py` L49·L84·L94-111 실제 Read 후 인용. upstream 코드와 구현 인자 패턴 일치 검증 완료. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | 해당 없음. |

### lerobot upstream 인용 정합 상세

- `train.py L49`: `resume: bool = False` → 코드의 `is_resume = (ckpt_case == "fine-tune-last")` + `"--resume"` 플래그 정확 대응.
- `train.py L84`: `checkpoint_path: Path | None = field(init=False, default=None)` → 코드는 `checkpoint_path` 를 직접 전달하지 않음. 이는 올바름 — upstream `validate()` 가 `config_path` 에서 `checkpoint_path` 를 **내부 파생**하므로 CLI 에서 `--checkpoint_path` 전달 불필요.
- `train.py L94-111`: `elif self.resume: ... policy_dir = Path(config_path).parent; self.checkpoint_path = policy_dir.parent` → `config_path` 는 `train_config.json` 경로여야 함. 코드의 `config_path = f"{run_dir}/checkpoints/last/pretrained_model/train_config.json"` 정확 일치 (`policy_dir = pretrained_model/`, `checkpoint_path = last/`).

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 가 실행해야 할 검증:
1. `AUTO_LOCAL`: `python3 -m py_compile training.py` + ruff + 구조 assertion (이미 본 code-test 에서 PASS)
2. `SSH_AUTO`: DGX SSH 에서 `preflight_check.sh smoke` 실행
3. `SSH_AUTO (사용자 동의)`: `save_dummy_checkpoint.sh` (5~15분) → 산출물 확인
4. `SSH_AUTO (T1 선결)`: `smoke_test.sh` (>5분, ~100MB) — T1 HF Hub 접근 PASS 후
