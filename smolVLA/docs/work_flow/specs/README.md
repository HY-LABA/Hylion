# docs/work_flow/specs/ — spec 정의 + 잔여 자료

본 디렉터리는 spec 파일과 사이클 간 누적되는 잔여 자료 (BACKLOG, ANOMALIES) 를 보관한다.

> 본 워크플로우 정책: `/CLAUDE.md`. 디렉터리 큰 그림: `../README.md`.

---

## 구조

```
specs/
├── README.md                # 본 문서
├── 00_template.md           # spec 작성 템플릿 (실제 spec 아님)
├── NN_<name>.md             # 활성 spec (사이클 한 번에 하나)
├── BACKLOG.md               # 구현 차원 잔여 자료
├── ANOMALIES.md             # 시스템 차원 잔여 자료
└── history/                 # 완료된 spec 보관
    └── NN_<name>.md
```

## 파일별 역할

| 파일 | 역할 | 작성자·갱신자 |
|---|---|---|
| `NN_<name>.md` | 활성 spec — todo + DOD | Phase 1 에서 사용자 + 메인 Claude |
| `BACKLOG.md` | **구현 차원 잔여** — 코드·spec·테스트 미해결 항목 | orchestrator·prod-test-runner (자동 누적) |
| `ANOMALIES.md` | **시스템 차원 잔여** — 하네스 차단·이상 패턴 | hook + 워커 + orchestrator (자동 누적) → reflection 분석 |
| `history/<name>.md` | 완료된 spec | `/wrap-spec` 시 자동 이동 |

## 두 백로그의 차이

| | `BACKLOG.md` | `ANOMALIES.md` |
|---|---|---|
| 차원 | 구현 (spec·todo·테스트) | 시스템 (하네스·워크플로우) |
| 누가 누적 | orchestrator·prod-test-runner | hook + 워커 + orchestrator |
| 누가 분석 | 다음 spec 작성 시 사용자 + 메인 (Phase 1) | reflection 에이전트 (사이클 종료 시 자동) |
| 갱신 효과 | 다음 spec 의 todo·우선순위 결정 | skill·hook·CLAUDE.md 갱신 제안 |

## spec 파일 명명 규칙

```
NN_<짧은_설명>.md        (NN = 순번, 예: 01, 02, 03)
```

- **순번이 높을수록 최신**
- `/start-spec` 이 specs/ 루트에서 가장 높은 NN 파일을 자동 선택 (`history/`·`00_template`·`BACKLOG`·`ANOMALIES`·`README` 제외)
- 한 spec 파일 = 한 사이클 (Phase 1 → 2 → 3)
- 종료 시 `history/` 로 이동

## 활성 spec 흐름

```
[Phase 1] 작성 (사용자 + 메인 Claude)
       ↓
specs/NN_<name>.md 완성
       ↓
[사용자: /start-spec — Phase 2 진입]
       ↓
planner → context/plan.md
       ↓
orchestrator dispatch loop
   ├ task-executor   → context/todos/<XX>/01_implementation.md
   ├ code-tester     → 02_code-test.md (verdict)
   └ prod-test-runner → 03_prod-test.md (verdict)
       ↓
[Phase 2 종료 — End-A 성공 또는 End-B 실패]
       ↓
[Phase 3 — 사용자 실물 검증]
       ↓
[/verify-result → 통과 시 /wrap-spec]
       ↓
specs/<NN_name>.md → specs/history/<NN_name>.md 이동
       ↓
context/* → context/history/<NN_name>/ 이동
       ↓
reflection → workflow_reflections/<날짜>_<NN_name>.md
       ↓
[사용자 항목별 승인 → 메인이 skill·hook·CLAUDE.md 갱신]
       ↓
다음 spec Phase 1 진입
```

## spec 파일 구조 (00_template.md 기반)

| 요소 | 설명 |
|---|---|
| `### [ ] TODO-XX` | 미완료 todo. planner 가 DAG 분석 시 추출 |
| `### [x] TODO-XX` | 완료된 todo. orchestrator 가 자동 마킹 (모든 워커 verdict 통과 시) |
| `DOD:` | 완료 조건. code-tester (단위 검증) + prod-test-runner (prod 검증) verdict 의 기준 |

> 옛 워크플로우의 `타입: task/test/both` 구분은 새 워크플로우에서 불필요 — orchestrator 가 자동 통합 처리 (구현 → 코드 테스트 → prod 테스트).

## BACKLOG·ANOMALIES 관리 정책

본 두 파일은 **사이클 간 누적**:

- spec 사이클 종료 시에도 `history/` 로 이동 X
- 각 spec 마다 별도 섹션 추가
- BACKLOG 항목은 다음 spec 작성 시 우선순위 검토 대상
- ANOMALIES 항목은 reflection 에이전트가 사이클 종료 시 자동 분석

자세한 정책: `BACKLOG.md` 본문, `ANOMALIES.md` 본문, `/CLAUDE.md` § 가시화 레이어.

> **2026-05-14 fresh start**: 구 `arm_2week_plan` era 의 BACKLOG·ANOMALIES 누적 기록은 → [`docs/storage/legacy/arm_2week_plan/`](../../storage/legacy/arm_2week_plan/) (`BACKLOG.md`·`ANOMALIES.md`) 로 이관. 현재 `specs/BACKLOG.md`·`ANOMALIES.md` 는 `realplaying.md` 로드맵 기준 새 누적본. **워커가 풀리지 않는 문제·하네스 이상을 만났을 때, 옛 era 에 유사 사례가 있는지 위 legacy 경로를 참조할 수 있다.**

---

## 활성 spec 번호 현황 (2026-05-14 fresh start 기준)

> 구 `arm_2week_plan` era 의 완료 spec (01_teleoptest ~ 08_final_e2e) 는 `docs/storage/legacy/arm_2week_plan/work_flow/specs/history/` 로 이관. 새 numbering 은 `realplaying.md` 로드맵 마일스톤 기준 01 부터 다시 시작.

| 번호 | realplaying.md 마일스톤 | 상태 |
|---|---|---|
| 01 | M1 — Task 정의 + 데이터 수집 | Phase 1 작성 예정 |
| 02 | M2 — 학습 (DGX) | 대기 |
| 03 | M3 — 배포 + 추론 (Orin) | 대기 |
| 04 | M4 — E2E 검증 + 사이클 패키징 | 대기 |

> 마일스톤 → spec 매핑: `realplaying.md` 의 M1~M4 가 각각 spec `01`~`04` 로 분해된다. spec 파일명의 `<name>` 부분은 각 Phase 1 작성 시 확정.

## Reference

- spec 작성 템플릿: [00_template.md](00_template.md)
- 워크플로우 정책: `/CLAUDE.md`
- 디렉터리 큰 그림: [`../README.md`](../README.md)
- 활성 spec 진행 상태: [`../context/`](../context/)
