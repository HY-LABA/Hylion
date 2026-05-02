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

---

## 활성 spec 번호 현황 (2026-05-02 기준)

<!-- 06_dgx_absorbs_datacollector 삽입으로 기존 06~09 → 07~10 시프트 (M1 갱신) -->

| 번호 | spec 명 | 상태 |
|---|---|---|
| 01 | orin_setting | history |
| 02 | dgx_setting | history |
| 03 | smolvla_test_on_orin | history |
| 04 | infra_setup | history |
| 05 | interactive_cli | history |
| **06** | **dgx_absorbs_datacollector** | **활성 (현 사이클)** |
| 07 | leftarmVLA | 대기 (구 06) |
| 08 | biarm_teleop_on_dgx | 대기 (구 07) |
| 09 | biarm_VLA | 대기 (구 08) |
| 10 | biarm_deploy | 대기 (구 09) |

> 번호 시프트 배경: 06_dgx_absorbs_datacollector 삽입으로 기존 `06_leftarmVLA` → `07_leftarmVLA`, `07~09` → `08~10`. 상세: `06_dgx_absorbs_datacollector.md` §본 마일스톤의 위치.

## Reference

- spec 작성 템플릿: [00_template.md](00_template.md)
- 워크플로우 정책: `/CLAUDE.md`
- 디렉터리 큰 그림: [`../README.md`](../README.md)
- 활성 spec 진행 상태: [`../context/`](../context/)
