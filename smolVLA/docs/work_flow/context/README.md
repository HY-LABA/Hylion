# docs/work_flow/context/ — 자동화 실행 상태 가시화

활성 spec 의 자동화가 진행되는 동안, 각 에이전트의 작업 흔적이 본 디렉터리에 누적된다. spec 사이클 종료 시 (`/wrap-spec`) 전체 내용이 `history/<spec명>/` 으로 이동.

## 구조

```
context/
├── README.md                       # 본 문서
├── plan.md                         # planner 산출물 — DAG·병렬 그룹·가정·검증 큐
├── log.md                          # 오케스트레이터 timeline 로그
├── verification_queue.md           # Phase 3 사용자 검증 대기 항목 누적
├── todos/                          # todo 별 작업 흔적
│   └── <TODO-XX>/                  # 예: O3, O4, X1
│       ├── 01_implementation.md    # task-executor 산출
│       ├── 02_code-test.md         # code-tester 산출 (verdict 포함)
│       └── 03_prod-test.md         # prod-test-runner 산출 (해당 시)
└── history/                        # 완료된 spec 의 context/ 보관
    └── NN_<spec명>/
```

## 파일별 역할

| 파일 | 작성자 | 시점 |
|---|---|---|
| `plan.md` | planner | spec 시작 직후 1회. todo 추가 (예: O4a, O4b) 시 갱신 |
| `log.md` | 오케스트레이터 | 매 dispatch·완료·분기 이벤트마다 한 줄 추가 |
| `verification_queue.md` | 오케스트레이터 | prod-test-runner 결과 모이는 대로 누적 |
| `todos/<XX>/01_implementation.md` | task-executor | 자기 todo 시작·완료 시 |
| `todos/<XX>/02_code-test.md` | code-tester | implementation 완료 후 |
| `todos/<XX>/03_prod-test.md` | prod-test-runner | 배포·비대화형 검증 후 |

## 작업 흐름과의 매핑

```
[Phase 1] spec 작성 (사용자 + 메인)
       ↓
사용자: /start-spec
       ↓
[Phase 2] 자동화 시작
       │
       ├─ planner → context/plan.md
       │
       ├─ 오케스트레이터 dispatch loop
       │     ├─ task-executor → context/todos/<XX>/01_implementation.md
       │     ├─ code-tester → context/todos/<XX>/02_code-test.md
       │     └─ prod-test-runner → context/todos/<XX>/03_prod-test.md
       │
       ├─ 매 이벤트 → context/log.md 한 줄 추가
       │
       ├─ prod-test 완료 → context/verification_queue.md 항목 누적
       │
       └─ 하네스 이상 신호 → docs/work_flow/specs/ANOMALIES.md 활성 섹션 누적
       ↓
[Phase 2 종료 신호 — End-A 성공 또는 End-B 실패]
메인 → 사용자: "spec X 자동화 완료. /verify-result 실행해" (End-A)
   또는: "TODO-X, Y 자동 해결 실패 — 수정 필요" (End-B)
       ↓
[Phase 3] 사용자 실물 검증
       ↓
사용자: /verify-result <결과>
       ↓
└─ 통과: 사용자: /wrap-spec
        → context/* 전체를 history/NN_<spec명>/ 로 이동
        → context/ 비워짐 (다음 spec 준비)
└─ 실패: 오케스트레이터가 todo1a, todo1b 추가 → planner 재호출 → Phase 2 재진입
```

## 작업 종료 시 (`/wrap-spec`) 처리

1. `context/{plan.md, log.md, verification_queue.md}` + `context/todos/` 디렉터리 → `context/history/NN_<spec명>/` 로 이동
2. `context/` 의 placeholder README 와 빈 plan/log/queue 파일이 다음 spec 준비 상태로 재초기화
3. `docs/work_flow/specs/ANOMALIES.md` 의 활성 spec 섹션은 reflection 분석 후 "처리됨" 마킹 (파일 이동 X — 사이클 간 누적 자료라 specs/ 위치 유지)
4. reflection 보고서 → `docs/storage/workflow_reflections/<날짜>_<spec명>.md` 작성

## 가시화 — 사용자가 어디서 보나

자동화 진행 중에 사용자가 별도 터미널·VSC 익스텐션에서 본 디렉터리의 파일을 직접 열어 보거나, `/observe` 슬래시 커맨드로 새 Claude 세션 띄워서 대화로 공부 가능.

> ⚠️ 사용자가 본 디렉터리의 파일을 직접 수정하면 자동화 흐름과 충돌할 수 있음. **읽기 전용** 으로 사용 권장.
