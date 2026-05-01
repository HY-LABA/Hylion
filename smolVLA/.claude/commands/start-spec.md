# /start-spec

활성 spec 의 자동화를 시작한다. orchestrator(메인 Claude) 가 planner 호출, dispatch loop 진입.

## 실행 순서

### 1. 활성 spec 자동 탐지

- `docs/work_flow/specs/` 에서 `NN_*.md` 중 **가장 높은 번호** 파일 선택 (`history/` 와 `00_template.md`, `BACKLOG.md`, `ANOMALIES.md`, `README.md` 제외)
- 없으면 사용자에게 "활성 spec 없음 — Phase 1 부터 진행 필요" 안내 후 종료

### 2. 사전 조건 검증

- `docs/work_flow/context/plan.md` 가 placeholder 상태인지 (활성 사이클 잔재 없어야 함)
- 활성 잔재 있으면 "/wrap-spec 먼저 호출 필요" 안내 후 종료
- `context/log.md`, `context/verification_queue.md` 도 동일 검증
- `context/todos/` 에 README 외 파일·디렉터리 있으면 잔재로 간주

### 3. planner 에이전트 호출

- 입력 자료:
  - 활성 spec 파일
  - `docs/work_flow/specs/BACKLOG.md` (구현 차원 잔여)
  - `docs/work_flow/specs/ANOMALIES.md` 직전 spec 섹션 (시스템 차원 잔여, 참고)
  - 직전 spec 의 `context/history/<spec명>/` (영향 가능성)
- 산출: `context/plan.md`
  - DAG (의존 관계)
  - 병렬 그룹 (동시 실행 가능 todo 묶음)
  - 확신 가정 vs 확인 필요 가정
  - `awaits_user` 항목 (사용자 결정 필요 todo)
  - 검증 대기 큐 후보 (Phase 3 사용자 검증 대상)

### 4. awaits_user 항목 일괄 질문

- planner 가 `awaits_user` 분류한 항목들을 **사용자에게 우선 일괄 질문**
- 답 받으면 plan 갱신 (해당 항목 dispatch 가능 상태로 전환)
- 답 없는 항목은 대기 — **의존 없는 다른 todo 부터 dispatch 진행** (병렬화 핵심)

### 5. dispatch loop 시작 (Phase 2 진입)

- `context/log.md` 첫 줄 추가:
  ```
  YYYY-MM-DD HH:MM:SS | START | spec=<NN_xxx>, todos=N, parallel_groups=M
  ```
- plan 따라 워커 호출:
  - 같은 그룹 내 todo 들은 **병렬** (단일 메시지에서 여러 Agent 도구)
  - 그룹 간은 **직렬** (의존 관계 따라)
- 각 todo 진행 흐름:
  1. task-executor → `context/todos/<XX>/01_implementation.md` 작성
  2. code-tester → `02_code-test.md` 작성 (verdict 발급)
  3. verdict 분기:
     - `READY_TO_SHIP` → prod-test-runner 진입
     - `MINOR_REVISIONS` → task-executor 1회 수정 (재검증 X) → prod-test-runner
     - `MAJOR_REVISIONS` → task-executor 재호출 (max 2 cycle)
       - 2 cycle 후에도 MAJOR 면 todo 실패 마킹, 다른 todo 계속
  4. prod-test-runner → `03_prod-test.md` 작성
     - `AUTOMATED_PASS` / `NEEDS_USER_VERIFICATION` → verification_queue 갱신
     - `FAIL` → ANOMALIES 에 `PROD_TEST_FAIL` 추가, 자동 재시도 (max 2 cycle)

### 6. 사용자 안내

- "Phase 2 시작됨. 진행 상황 보려면 별도 터미널·VSC 익스텐션에서 `claude` 띄우고 `/observe` 호출"
- dispatch loop 가 도는 동안 메인은 워커 호출·감시·로그 갱신에 집중

## 종료 신호 (Phase 2 → Phase 3)

- **End-A 성공**: 모든 todo verdict ∈ {AUTOMATED_PASS, NEEDS_USER_VERIFICATION}
  → 메인이 사용자에게 "spec 자동화 완료. /verify-result 실행해" 안내
- **End-B 실패**: 일부 todo 가 code-tester 2 cycle MAJOR 또는 prod-test FAIL
  → 메인이 사용자에게 "TODO-X, Y 자동 해결 실패 — 수정 필요" 보고, 자연어 대화로 다음 단계 결정
