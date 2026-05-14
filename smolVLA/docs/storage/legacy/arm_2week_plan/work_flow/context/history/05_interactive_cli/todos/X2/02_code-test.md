# TODO-X2 — Code Test

> 작성: 2026-05-01 17:30 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 이슈 0건. Recommended 이슈 4건 (threshold 3건 초과).

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/env_check.py   -> OK
python3 -m py_compile dgx/interactive_cli/flows/training.py    -> OK
python3 -m py_compile dgx/interactive_cli/flows/entry.py       -> OK
```

구문 오류 없음. 3개 파일 모두 통과.

---

## Lint·Type 결과

```
python3 -m ruff check dgx/interactive_cli/flows/env_check.py
  -> All checks passed!

python3 -m ruff check dgx/interactive_cli/flows/entry.py
  -> All checks passed!

python3 -m ruff check dgx/interactive_cli/flows/training.py
  -> 6 errors (모두 [*] auto-fixable):

  F541 training.py:213  f-string without placeholders  (print(f"  smoke test 는 고정 데이터셋을 사용합니다:"))
  F541 training.py:227  f-string without placeholders  (print(f"     예: lerobot/svla_so100_pickplace"))
  F541 training.py:235  f-string without placeholders  (print(f"  4. 종료"))
  F401 training.py:435  `os` imported but unused       (import os — 지역 import, os. 미사용)
  F541 training.py:503  f-string without placeholders  (print(f"  학습 출력 디렉터리:"))
  F541 training.py:518  f-string without placeholders  (print(f"  4. 종료 (전송 안 함)"))
```

F541 5건: `f` prefix 불필요한 문자열 리터럴 (placeholder 없음). Auto-fixable.
F401 1건: `import os` 지역 import 후 `os.` 미사용 — `dgx_dir = str(script_dir.parent)` 로 os 없이 처리됨. Auto-fixable.

mypy: 로컬 환경 미설치로 스킵. 구문 및 타입 힌트 수동 검토 완료 (하단 Logic 검증 참조).

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. X1 정의대로 dgx flow 구현 (env_check + training + entry 갱신) | ✅ | 3파일 모두 작성/갱신 |
| 2. 옵션 C 3단계 구조 (flow3 시나리오 선택 / flow4 데이터셋 / flow5 학습+ckpt) | ✅ | flow3_select_scenario / flow4_select_dataset / flow5_train_and_manage_ckpt 구현 |
| 3. smoke 동의 게이트 (_smoke_consent_gate 함수 + 5~15분 경고) | ✅ | training.py:317~338 구현, smoke_test.sh line 44~45 인용 |
| 4. ckpt 케이스 목록 출력 + 사용자 선택 (자동 감지 X) | ✅ | CKPT_CASES 딕셔너리 + _show_ckpt_management 구현. sync_ckpt_dgx_to_datacollector.sh line 19~22 인용 |
| 5. preflight_check.sh 경로 계산 정확 | ✅ | script_dir.parent/"scripts"/"preflight_check.sh" → dgx/scripts/preflight_check.sh 확인 |
| 6. smoke_test.sh 경로 계산 정확 | ✅ | script_dir.parent/"scripts"/"smoke_test.sh" → dgx/scripts/smoke_test.sh 확인 |
| 7. entry.py dgx 분기 추가 후 회귀 없음 | ✅ | flow0, flow1 호출 유지. orin/datacollector 분기 보존 확인 |
| 8. CLAUDE.md 준수 (Category A·B·D 비해당) | ✅ | dgx/interactive_cli/ 신규 파일만. pyproject.toml·dgx/lerobot/ 미변경 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `training.py:435` (F401) | `import os` 지역 import 제거. `dgx_dir = str(script_dir.parent)` 는 `os` 없이 동작. `--fix` 로 auto-fix 가능 |
| 2 | `training.py:213,227,235,503,518` (F541 5건) | 불필요한 `f` prefix 제거. auto-fixable. 기능 영향 없음 |
| 3 | `training.py:55~86` CKPT_CASES | sync_ckpt_dgx_to_datacollector.sh 케이스 4 (USB 드라이브) 가 CKPT_CASES 에 없음. 현재 케이스 "3. 나중에 직접 전송" 의 guide 가 ckpt_transfer_scenarios.md 를 참조하도록 되어 있어 기능 손실은 없으나, 케이스 4 항목을 명시적으로 추가하면 14_dgx_cli_flow.md §5-2 케이스 분류(1~4)와 완전 정합됨 |
| 4 | `training.py:580~604` flow5 smoke 분기 | smoke 분기 성공 후 `_show_ckpt_management` 미호출이 설계 의도(smoke는 --save_checkpoint=false)와 일치하나, 실패 시 (returncode != 0) False 반환 전 안내 메시지가 없음. 실패 경로에도 최소 안내 추가 고려 (현재 "smoke test 실패. smoke_test.sh 출력을 확인하세요." 는 있음 — 문제 없음, trivial) |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/ 미변경 |
| B (자동 재시도 X) | ✅ | orin/lerobot/, dgx/lerobot/, pyproject.toml, setup_env.sh, deploy_*.sh 미변경 |
| Coupled File Rules | ✅ | dgx/lerobot/ 미변경 → 04_dgx_lerobot_diff.md 갱신 불필요. pyproject.toml 미변경 → 02_orin_pyproject_diff.md 갱신 불필요 |
| C (사용자 동의 필수) | ✅ | dgx/interactive_cli/ 는 spec 합의 영역. 신규 외부 의존성 없음 |
| D (절대 금지 명령) | ✅ | rm -rf / sudo / git push --force 등 미사용 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | docs/storage/ 미변경 |

---

## 경로·로직 검증 상세

### script_dir 경로 계산

`entry.py:253`: `script_dir = Path(args.node_config).parent.parent`

- node_config 예시: `dgx/interactive_cli/configs/node.yaml`
- `.parent` → `dgx/interactive_cli/configs/`
- `.parent.parent` → `dgx/interactive_cli/` (script_dir)

하위 경로 파생:
- `script_dir.parent / "scripts" / "preflight_check.sh"` → `dgx/scripts/preflight_check.sh` ✅
- `script_dir.parent / "scripts" / "smoke_test.sh"` → `dgx/scripts/smoke_test.sh` ✅
- `script_dir.parent / "datasets"` → `dgx/datasets/` ✅
- `str(script_dir.parent)` + `/outputs/train/` → `dgx/outputs/train/` ✅

### SCENARIOS 메모리 임계치 (preflight_check.sh line 23~35 정합)

| 키 | training.py | preflight_check.sh | 일치 |
|---|---|---|---|
| smoke | 20 GB | REQUIRED_GB=20 | ✅ |
| s1 | 35 GB | REQUIRED_GB=35 | ✅ |
| s3 | 65 GB | REQUIRED_GB=65 | ✅ |
| lora | 28 GB | REQUIRED_GB=28 | ✅ |

### _yn_prompt 로직 검증

- `default_yes=True` + 빈 입력 → `True` ✅
- `default_yes=False` + 빈 입력 → `False` ✅
- `n` 입력 → `False` ✅ (smoke consent gate N 응답 시 중단 정상)

### smoke 분기 — ckpt 관리 미호출 설계 의도

`smoke_test.sh:75`: `--save_checkpoint=false` → 체크포인트 없음. `flow5_train_and_manage_ckpt` 의 smoke 분기에서 `_show_ckpt_management` 미호출은 의도적 설계. 코드 내 주석(`line 582`)으로 명시 ✅.

### devPC 전용 스크립트 안내

`CKPT_CASES` 의 모든 항목이 "devPC 에서 실행" 명령 안내만 출력. DGX 에서 직접 rsync 미호출. `14_dgx_cli_flow.md §5-2 비고` 준수 ✅.

---

## 잔여 리스크 (task-executor 보고 인계)

- **lerobot-train draccus 인자 정확성**: `_run_real_training` cmd 목록은 `save_dummy_checkpoint.sh` line 56~70 기반. X3 prod 에서 실제 `lerobot-train --help` 출력과 비교 필요.
- **로컬 데이터셋 경로 처리**: `~/smolvla/dgx/datasets/<name>` 를 `--dataset.repo_id` 에 전달하는 방식이 lerobot 버전에 따라 다를 수 있음.

---

## 배포 권장

MINOR_REVISIONS — task-executor 1회 추가 수정 후 prod-test-runner 진입 권장.

수정 목표: `training.py` ruff F401·F541 6건 auto-fix (`ruff check --fix dgx/interactive_cli/flows/training.py`). 코드 동작 변경 없음. 수정 후 재검증 불필요 (MINOR_REVISIONS 정책).
