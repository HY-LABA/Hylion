# TODO-D10 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

사이클 흐름 분기점 강화 — G1 (teleop 종료 안내) + G2 (single_task 커스텀 입력) + G3 (precheck 옵션 2 안내) + G4 (BACKLOG #10~#14 추가)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/teleop.py` | M | G1-a: flow3 3단계 흐름 안내 추가 / G1-b: flow4 prompt 문구 정상/비정상 분기 |
| `dgx/interactive_cli/flows/record.py` | M | G2-a: flow6_record 에 single_task 확인/커스텀 UI 추가 / G2-b: build_record_args single_task 파라미터 추가 |
| `dgx/interactive_cli/flows/precheck.py` | M | G3-a: 옵션 2 + 옵션 1 완료 시 4단계 흐름 안내 추가 |
| `docs/work_flow/specs/BACKLOG.md` | M | 07 섹션 #10~#14 신규 5건 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경
- Coupled File Rule: `orin/lerobot/` 미변경 — 03_orin_lerobot_diff.md 갱신 불요
- Coupled File Rule: `orin/pyproject.toml` 미변경 — 02_orin_pyproject_diff.md·setup_env.sh 갱신 불요
- 레퍼런스 활용:
  - `docs/reference/lerobot/` 의 `lerobot_record.py` `DatasetRecordConfig.single_task` (line 161~) 직접 인용 — "모든 frame 에 붙는 자연어 task 설명, VLA instruction" 설명 문구로 활용
  - 기존 `precheck.py` 의 `_prompt` 함수 (L102) 재사용 대신 `flow6_record` 에서는 표준 `input()` 직접 사용 (flow6_record 는 precheck 와 다른 모듈 — import 없이 동일 패턴 적용)

## 변경 내용 요약

### G1 — teleop.py

`flow3_teleoperate` 의 출력에 3단계 흐름 안내 ("1. Enter → run_teleoperate.sh / 2. Ctrl+C 정상 종료 / 3. 종료 후 다음 단계") 를 추가했다. `flow4_confirm_teleop` 의 `input()` prompt 를 정상 종료(returncode==0) 와 비정상 종료 두 케이스로 분리하여 각각 "다음 단계 (record + 학습)" 와 "강제 진행 (비권장)" 문구로 명시했다.

### G2 — record.py

`flow6_record` 시작 부분에 `single_task` 확인/커스텀 입력 UI 를 추가했다. 사용자가 (1) 기본값 또는 Enter → 기본값 적용, (2) 커스텀 task 입력 → 커스텀 적용, 빈 입력 → 기본값 fallback 흐름이다. `build_record_args` 에 `single_task: str | None = None` 파라미터를 추가하여 None 이 아닌 경우 해당 값을 우선 사용하고 None 이면 `SINGLE_TASK_MAP[data_kind_choice]` 기본값을 사용하도록 했다. `flow6_record` 가 결정된 `single_task` 를 `build_record_args(single_task=single_task)` 로 전달한다.

### G3 — precheck.py

`teleop_precheck` 의 옵션 2 (`elif raw == "2"`) 에 4단계 흐름 안내를 추가했다. 옵션 1 (find-port + find-cameras + calibrate 완료) 의 성공 경로 반환 직전에도 동일 흐름 안내를 추가했다.

### G4 — BACKLOG.md

07 섹션에 #10 (transfer 후 학습 진입 prompt UX), #11 (학습 mode 로컬/HF Hub 분기), #12 (Orin hil_inference 진입 안내), #13 (각 flow 목적 설명), #14 (Ctrl+C cleanup 안내) 5건을 추가했다.

## 구조적 판단 사항

### G2 — 호출 체인 분석

spec 에서는 `build_record_args` 내부 L208 의 `single_task = SINGLE_TASK_MAP[data_kind_choice]` 직후에 prompt 를 추가하도록 명시했으나, 실제 코드 구조를 확인한 결과:

- `data_kind.py` 의 `flow5_select_data_kind()` 가 `DataKindResult` (single_task 포함) 반환
- `mode.py` 가 이를 `flow6_record(single_task=...)` 에 전달
- `flow6_record` 가 `build_record_args` 에 최종 인자 전달

따라서 사용자 prompt 를 `build_record_args` (순수 인자 생성 함수) 에 넣는 것은 SRP 위반이다. `flow6_record` 의 초기에 단계로 처리하고, 결정된 `single_task` 를 `build_record_args` 에 파라미터로 전달하는 방식을 선택했다. 이 방식이 spec 의 목표 (커스텀 task 입력 가능, 기존 동작 유지) 를 동일하게 달성하면서 아키텍처를 보존한다.

## code-tester 입장에서 검증 권장 사항

- **정적 검증**: `python3 -m py_compile` 3개 파일 모두 PASS 확인 완료
- **lint**: `ruff check` 3개 파일 모두 PASS 확인 완료
- **unit/smoke**: 변경 파일에 대한 직접 unit test 없음 — import smoke 필요
  ```bash
  python3 -c "from dgx.interactive_cli.flows.teleop import flow3_teleoperate, flow4_confirm_teleop; print('teleop OK')"
  python3 -c "from dgx.interactive_cli.flows.record import build_record_args, flow6_record; print('record OK')"
  python3 -c "from dgx.interactive_cli.flows.precheck import teleop_precheck; print('precheck OK')"
  ```
  (DGX SSH 에서: sys.path 에 dgx/interactive_cli/ 추가 필요 또는 entry.py 진입점 사용)
- **build_record_args 파라미터 회귀 확인**: `single_task=None` 기본값 → 기존 동작 동일 여부
  ```python
  from dgx.interactive_cli.flows.record import build_record_args
  args = build_record_args(1, "user/ds", 10)
  assert any("Pick up the object" in a for a in args), "single_task 기본값 누락"
  args2 = build_record_args(1, "user/ds", 10, single_task="custom task")
  assert any("custom task" in a for a in args2), "커스텀 single_task 미반영"
  ```
- **DGX deploy**: `scripts/deploy_dgx.sh` 로 배포 후 import smoke PASS 확인
- **DOD 항목 확인**:
  - G1: teleop.py 출력에 3단계 흐름 포함 여부 grep
  - G2: flow6_record 실행 시 "번호 선택 [1~2]" prompt 출력 여부
  - G3: precheck.py 옵션 2 선택 시 4단계 흐름 출력 여부
  - G4: BACKLOG.md 07 섹션에 #10~#14 항목 존재 여부
