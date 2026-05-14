# TODO-N1 — Code Test

> 작성: 2026-05-04 14:30 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 0건, Recommended 3건.

---

## 단위 테스트 결과

```
python3 -m py_compile — 14개 파일 전체

dgx/interactive_cli/flows/_back.py        OK
orin/interactive_cli/flows/_back.py       OK
dgx/interactive_cli/flows/entry.py        OK
dgx/interactive_cli/flows/env_check.py   OK
dgx/interactive_cli/flows/mode.py         OK
dgx/interactive_cli/flows/precheck.py     OK
dgx/interactive_cli/flows/data_kind.py   OK
dgx/interactive_cli/flows/record.py       OK
dgx/interactive_cli/flows/teleop.py       OK
dgx/interactive_cli/flows/training.py     OK
dgx/interactive_cli/flows/transfer.py     OK
orin/interactive_cli/flows/entry.py       OK
orin/interactive_cli/flows/env_check.py  OK
orin/interactive_cli/flows/inference.py  OK

전체 14개 구문 오류 없음.
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/
  All checks passed!

ruff check orin/interactive_cli/flows/
  E402 Module level import not at top of file
  --> orin/interactive_cli/flows/entry.py:38:1
  |  from flows._back import is_back

  Found 1 error.
```

**분석**: E402 는 orin/entry.py 기존 패턴에서 비롯됨.
- entry.py 는 main.sh 에서 직접 경로로 호출되므로 `sys.path.insert(0, str(_CLI_DIR))` 가 34~36 번째 줄에 먼저 필요함.
- 해당 패턴은 TODO-N1 이전부터 존재했으며 (git diff 확인 — `from flows._back import is_back` 만 신규 추가), E402 는 pre-existing 아키텍처 제약으로 인한 비-Critical lint 경고임.
- `# noqa: E402` 주석으로 억제 가능 (Recommended 개선 사항 #1).

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 모든 prompt 분기점에 b/back 처리 (dgx 9 + orin 3 flows) | ✅ | is_back() 호출 확인: entry.py(3), mode.py(2), precheck.py(2), data_kind.py(2), record.py(5), teleop.py(3), training.py(7), transfer.py(2), orin/entry.py(2), orin/inference.py(5). env_check.py 2개는 input() prompt 없는 subprocess 래퍼 → 해당 없음. |
| 2. helper 위치 — flows/_back.py (Category C 회피) | ✅ | dgx/interactive_cli/flows/_back.py, orin/interactive_cli/flows/_back.py 신규 생성. common/ 디렉터리 없음 확인 (ls 검증). |
| 3. entry (0 단계) b/back 시 종료 또는 메뉴 재표시 | ✅ | dgx/entry.py flow1_select_node: `return None` (종료). detect_display_mode 최상위: 자동 검출값으로 진행 (종료 아닌 계속 — 상위 없으므로 합리적). orin/entry.py flow1_select_node: `return None` (종료). |
| 4. README 두 개 갱신 (UX 섹션) | ✅ | dgx/interactive_cli/README.md § UX — 뒤로가기(b/back) 신규 섹션 확인. orin/interactive_cli/README.md 동일 확인. |
| 5. subprocess 진행 중 단계 안내 (Ctrl+C 권고) | ✅ | teleop.py L113, training.py L682, record.py L614, orin/inference.py L271·L274 — "뒤로가기 불가 — Ctrl+C 로만 종료 가능" 안내 확인. |

---

## Critical 이슈

없음.

---

## 잔여 리스크 A 분석 — teleop.py `return 2` sentinel

**결론: 동작상 안전. 의미론적 개선 Recommended.**

**실제 returncode=2 충돌 가능성 검토**:
- `_run_teleop_script()` 는 `subprocess.run(["bash", str(teleop_script), "all"], check=False).returncode` 를 반환.
- `run_teleoperate.sh` 는 lerobot-teleoperate subprocess — Ctrl+C 표준 종료 시 returncode=0 반환 (KeyboardInterrupt catch → return 0 L85). 비정상 종료 시 1 또는 쉘 종료 코드.
- lerobot upstream (`lerobot_teleoperate.py`) 이 returncode=2 를 명시적으로 반환하는 경로 없음 (except KeyboardInterrupt: pass → 0 으로 마무리되거나 비0 으로 쉘에 의해 처리됨).
- `run_teleoperate.sh` 가 내부에서 `exit 2` 를 직접 반환하는지는 스크립트 미존재 환경이라 정적 확인 불가 (SKILL_GAP 해당).

**flow4_confirm_teleop 처리**:
- L147: `if prev_returncode == 2:` → b/back 취소로 명확히 처리 (`return False`).
- L196: 재시도(r) 후 `flow3_teleoperate` 재호출 시에도 returncode==2 처리 있음.
- `prev_returncode != 0` 분기에서 `prev_returncode == 2` 가 먼저 필터링되므로, 2가 "에러" 메시지로 오분류되지 않음.

**단, 모호성**: `run_teleoperate.sh` 가 내부 오류로 `exit 2` 를 반환하는 경우, flow4 에서 b/back 취소와 동일하게 처리됨 — 사용자 관점에서 "오류인데 취소됐다고 안내" 가 될 수 있음.

## 잔여 리스크 B 분석 — `_run_real_training` ckpt_case == "back" → (False, None)

**결론: 동작상 안전. 의미론적 개선 Recommended.**

**흐름 추적**:
1. `_select_start_ckpt()` 에서 b/back → `return "back", None, None`.
2. `_run_real_training()` L583: `if ckpt_case == "back": return False, None`.
3. `flow5_train_and_manage_ckpt()` L828: `success, output_dir = _run_real_training(...)`.
4. L833: `if not success:` → "[flow 5] 학습이 오류 또는 중단으로 종료되었습니다." 출력.
5. L841: `_show_ckpt_management(output_dir=None)` 호출 — ckpt 전송 안내 UI 표시.
6. L842: `return False`.

**문제**: back 취소 시에도 `_show_ckpt_management()` 가 호출되어 "ckpt 전송 안내" UI가 표시됨 (output_dir=None 이므로 "출력 디렉터리 정보 없음" 메시지 포함). 학습이 실행되지 않았는데 ckpt 전송 안내를 보여주는 것은 혼란.

**동작 안전성**: `output_dir=None` 이므로 실제 ckpt 경로 참조 없음 → 런타임 오류 없음. 사용자가 ckpt 전송 메뉴를 보게 되지만 b/back으로 건너뛸 수 있음.

**의미론적 문제**: `success=False` 반환이 "취소"와 "학습 실패"를 구분하지 못함. `run_training_flow()` 에서 `return 1` 로 전파됨.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/interactive_cli/flows/entry.py:38` | `from flows._back import is_back  # noqa: E402` 추가 — ruff E402 억제. pre-existing 아키텍처 제약이지만 lint clean 상태 유지 권장. |
| 2 | `dgx/interactive_cli/flows/teleop.py:127` | returncode=2 sentinel 주석 강화 또는 `run_teleoperate.sh` 에서 exit 2 가 사용되지 않는다는 검증 주석 추가. 또는 sentinel 을 -1 로 변경 (bash returncode 범위 0~255 이므로 -1 은 Python 측 sentinel 로만 사용 가능). SKILL_GAP: `run_teleoperate.sh` 내용 미검증. |
| 3 | `dgx/interactive_cli/flows/training.py:583` | `ckpt_case == "back"` 분기 직후 `return False, None` 전에 `_show_ckpt_management` 건너뜀 처리 추가 — early return 으로 분리하거나, `flow5_train_and_manage_ckpt` 에서 `(False, None)` 수신 시 ckpt 관리 UI skip. 현재는 back 취소 후 불필요한 ckpt 전송 안내 표시됨. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/ 미변경. |
| B (자동 재시도 X) | ✅ | orin/lerobot/, dgx/lerobot/ 미변경. pyproject.toml 미변경. setup_env.sh 미변경. |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경 → 03_orin_lerobot_diff.md 갱신 불필요. pyproject.toml 미변경 → 02_orin_pyproject_diff.md 갱신 불필요. |
| Category C 회피 | ✅ | 신규 디렉터리 없음. common/ 디렉터리 생성 X. flows/ 기존 디렉터리 내 _back.py 배치. |
| 옛 룰 | ✅ | docs/storage/ 하위 bash 명령 예시 추가 없음. |

---

## ANOMALIES

| TYPE | 내용 |
|---|---|
| `SKILL_GAP` | `run_teleoperate.sh` 파일 미존재 환경이라 정적 분석 불가 — returncode=2 를 명시적으로 반환하는지 검증 못함. 잔여 리스크 A 의 sentinel 충돌 가능성 완전 배제 불가. |

---

## 배포 권장

MINOR_REVISIONS — task-executor 1회 추가 수정 권장 후 prod-test 진입.

수정 우선순위:
1. Recommended #3 (training.py back 취소 시 ckpt 관리 UI skip) — UX 혼란 방지 실용적 개선.
2. Recommended #1 (entry.py noqa 주석) — lint clean.
3. Recommended #2 (teleop returncode sentinel 주석 강화) — 선택적.
