# TODO-D1 — Code Test

> 작성: 2026-05-03 14:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 1건.

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/mode.py         → OK
python3 -m py_compile dgx/interactive_cli/flows/entry.py        → OK
python3 -m py_compile dgx/interactive_cli/flows/env_check.py    → OK
python3 -m py_compile dgx/interactive_cli/flows/teleop.py       → OK
python3 -m py_compile dgx/interactive_cli/flows/data_kind.py    → OK
python3 -m py_compile dgx/interactive_cli/flows/record.py       → OK
python3 -m py_compile dgx/interactive_cli/flows/transfer.py     → OK
python3 -m py_compile dgx/interactive_cli/flows/training.py     → OK
bash -n dgx/interactive_cli/main.sh                             → OK

결과: 8/8 py_compile PASS, main.sh bash -n PASS
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/mode.py dgx/interactive_cli/flows/entry.py \
           dgx/interactive_cli/flows/env_check.py dgx/interactive_cli/flows/teleop.py \
           dgx/interactive_cli/flows/data_kind.py dgx/interactive_cli/flows/record.py \
           dgx/interactive_cli/flows/transfer.py dgx/interactive_cli/flows/training.py

결과: All checks passed!
```

mypy: 비실행 (dgx venv 로컬 부재). py_compile + ruff PASS 로 정적 검증 완료.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. SSH_AUTO PASS: flow 0 (entry), flow 1 (장치 선택), flow 2 (env_check 7단계 fallback) | ✅ | entry.py·env_check.py 정적 검증 완료. fallback(_check_hardware_collect) = False 반환 + 크래시 X 코드 확인. |
| 2. flow 3~7 py_compile·ruff·bash -n PASS | ✅ | 8파일 전체 PASS |
| 3. PHYS_REQUIRED 부분 verification_queue D 그룹 마킹 명시 | ✅ | impl.md 에 D-1~D-4 항목 명시 (PHYS_REQUIRED, 시연장 이동 시) |
| 4. 04 BACKLOG #14 진단·수정 (DGX env_check.py NoneType) | ✅ | dgx/interactive_cli/flows/env_check.py 에 port_handler 패턴 0건 확인. 항목 9 = `with serial.Serial(follower_port, timeout=0.5)` context manager → None-safe 원천 차단. 패치 불필요 결론 정당. |
| 5. prod-test-runner 인계 검증 명령 시퀀스 작성 (SSH 자율) | ✅ | impl.md Step 2 에 flow 0~2 SSH 자율 명령 상세 기술. 환경 레벨 명시. |
| 6. PHYS_REQUIRED 마킹 항목 적정성 | ✅ | SO-ARM·카메라 직결 필수 항목 D-1~D-4 적절히 분리. SSH_AUTO 가능 항목 (flow 5, flow 7(1)(2), G-4) 별도 분류 정합. |
| 7. mode.py 패치 적정성 (env_check 호출 누락 버그 수정) | ✅ | 아래 "패치 검증" 섹션 참조 |

### mode.py 패치 검증 상세

git diff 확인 결과: `flow3_mode_entry()` raw == "1" 분기 내 `_run_collect_flow()` 호출 직전에 아래 블록 삽입.

- **삽입 위치**: line 211~220 (while True 루프 내부, raw == "1" 분기)
- **import**: `from flows.env_check import flow2_env_check as _flow2_env_check_collect` (지연 import — 불필요한 순환 import 방지)
- **호출 인자**: `flow2_env_check(script_dir, scenario="smoke", mode="collect")` — env_check.py 시그니처 `(script_dir, scenario="smoke", mode="train")` 와 정합
- **return 값 처리**: `if not ...: return 1` — False 시 함수 전체 종료 (while loop 탈출 포함). 올바름.
- **FAIL 메시지**: `"[mode] 수집 환경 체크 FAIL — SO-ARM·카메라 연결 후 재시작하세요."` — 사용자 안내 적절

entry.py 체인 확인: entry.py는 `flow2_env_check(script_dir, scenario="smoke")` (mode 인자 생략 → 기본값 "train") 호출 후 `flow3_mode_entry()` 진입. 수집 모드의 추가 env_check (mode="collect")는 mode.py 에서 처리 — 이중 호출 설계이나 명세(entry.py 주석 L236-238) 및 env_check.py docstring 과 일치. 논리적 문제 없음.

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `dgx/interactive_cli/flows/mode.py` line 211 | 지연 import (`from flows.env_check import ...`)가 while True 루프 내부에 위치. 루프 반복 시마다 import가 재실행되나, Python import 캐시(sys.modules)로 실 overhead 는 없음. 명확성을 위해 함수 상단으로 이동하는 것이 관례적. 기능 오류 X. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경. |
| B (자동 재시도 X 영역) | ✅ | `dgx/lerobot/` 미변경 (git diff 확인 — 출력 없음). `dgx/pyproject.toml` 미변경. `setup_env.sh` 미변경. `.gitignore` 미변경 (P2 별도 todo). |
| Coupled File Rules | ✅ | `dgx/interactive_cli/` 변경 → `dgx/lerobot/` 영역 아님. Coupled File Rule 해당 없음. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `docs/storage/` 하위 변경 없음. |
| 옵션 B 원칙 | ✅ | lerobot-upstream-check skill 적용 — upstream 디렉터리 보존 확인. |

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

Critical 0건, Recommended 1건 (스타일 권고, 기능 오류 X). `READY_TO_SHIP`.

prod-test-runner 인계 시 impl.md Step 2 SSH 자율 검증 명령 시퀀스 실행 권장:
- py_compile 8파일 SSH (ssh dgx)
- flow 0~2 정적 검증 (VALID_NODES, env_check 시그니처, fallback 동작)
- PHYS_REQUIRED 항목 (D-1~D-4) → verification_queue D 그룹 마킹
