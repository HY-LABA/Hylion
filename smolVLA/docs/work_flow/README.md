# docs/work_flow/ — 자동화 워크플로우 본부

본 디렉터리는 **milestone → spec → todo** 계층의 자동화 워크플로우 자산을 보관한다. 사용자는 spec 작성·실물 검증·spec 마무리만 직접 관여, 그 외 모든 단계는 에이전트 팀이 자동 처리.

> 본 워크플로우의 정책 정의: `/CLAUDE.md` (헌법). 본 README 는 디렉터리 책임·관계 안내.

---

## 구조

```
work_flow/
├── README.md                     # 본 문서
├── specs/                        # spec·잔여 자료 (사이클 간 누적)
│   ├── README.md
│   ├── 00_template.md
│   ├── NN_<name>.md              # 활성 spec
│   ├── BACKLOG.md                # 구현 차원 잔여 (코드·spec·테스트)
│   ├── ANOMALIES.md              # 시스템 차원 잔여 (하네스 발전 단서)
│   └── history/                  # 완료된 spec
└── context/                      # 활성 사이클의 자동화 실행 상태
    ├── README.md
    ├── plan.md                   # planner 산출물
    ├── log.md                    # orchestrator timeline
    ├── verification_queue.md     # Phase 3 검증 큐
    ├── todos/<XX>/               # todo별 작업 흔적
    └── history/<spec명>/         # 완료된 spec 의 context/ 자료
```

## 디렉터리 역할

| 디렉터리 | 역할 |
|---|---|
| `specs/` | spec 파일 + 잔여 자료. **사이클 간 누적**. BACKLOG (구현 잔여) + ANOMALIES (시스템 잔여) 가 sibling |
| `context/` | **활성 사이클의 일시 상태**. 사이클 종료 시 history/ 로 이동, 다음 spec 위해 비워짐 |

## 3 Phase 워크플로우

```
══════ Phase 1 — Discovery (사용자 + 메인 Claude) ══════
[milestone 결정 또는 직전 /wrap-spec 직후]
       │
       │ 대화 — 큰 그림 합의 → todo 분해 → DOD 작성
       ▼
[specs/NN_<name>.md 완성]
       │
       │ 사용자: /start-spec
       ▼

══════ Phase 2 — Automation (orchestrator + 워커들) ══════
[메인 Claude = orchestrator]
       │
       ├─ planner → context/plan.md (DAG·병렬 그룹·가정·검증 큐)
       │
       ├─ dispatch loop (병렬 가능 todo 동시 실행):
       │     ├─ task-executor → context/todos/<XX>/01_implementation.md
       │     ├─ code-tester → 02_code-test.md (verdict)
       │     └─ prod-test-runner → 03_prod-test.md (verdict)
       │
       ├─ 매 이벤트 → context/log.md
       ├─ prod-test 결과 → context/verification_queue.md
       └─ 하네스 이상 신호 → specs/ANOMALIES.md
       │
       │ End-A 성공: 모든 todo {AUTOMATED_PASS, NEEDS_USER_VERIFICATION}
       │   → 메인이 사용자에게 "/verify-result 실행해" 안내
       │ End-B 실패: 일부 todo MAJOR 2 cycle 또는 prod-test FAIL
       │   → 메인이 "수정 필요" 보고, 자연어 대화로 다음 단계
       ▼

══════ Phase 3 — Verification (사용자) ══════
[사용자가 Orin·SO-ARM 에서 실물 검증]
       │
       │ 사용자: /verify-result <자연어 결과>
       ▼
[orchestrator 결과 분석]
       │
       ├─ 통과 → 사용자: /wrap-spec
       │   ├─ context/* → context/history/<spec명>/
       │   ├─ specs/<spec명>.md → specs/history/<spec명>.md
       │   ├─ reflection 에이전트 호출 → workflow_reflections/<날짜>_<spec명>.md
       │   ├─ 사용자 항목별 승인 → 메인이 skill·hook·CLAUDE.md 직접 수정
       │   └─ 다음 spec Phase 1 진입
       │
       └─ 실패 → orchestrator 가 todo 추가 (1a, 1b…) → planner 재호출 → Phase 2 재진입
```

## 사용자가 관여하는 시점

| 시점 | 사용자 행동 |
|---|---|
| Phase 1 | 메인 Claude 와 대화로 spec 작성 |
| Phase 2 도중 | (선택) 별도 세션에서 `/observe` — read-only 학습 |
| Phase 2 → 3 | 메인 신호 받고 실물 환경 준비 |
| Phase 3 | Orin·SO-ARM 에서 직접 검증 → `/verify-result` 입력 |
| Phase 3 종료 | `/wrap-spec` 호출 + reflection 갱신 항목별 승인 |

## 가시화 — 진행 상황 어디서 보나

- `context/plan.md` — 현재 실행 계획
- `context/log.md` — 이벤트 timeline
- `context/todos/<XX>/` — 각 todo 진행 상태
- `context/verification_queue.md` — Phase 3 검증 대기
- `specs/ANOMALIES.md` 활성 spec 섹션 — 하네스 이상 신호
- 자세한 안내: `context/README.md`

별도 세션에서 `/observe` 호출 시 OBSERVER 모드로 전환되어 위 자료를 자동 파악 후 사용자와 대화.

## 자세한 정보

- **워크플로우 정책**: `/CLAUDE.md`
- **에이전트 정의**: `.claude/agents/*.md`
- **스킬 정의**: `.claude/skills/**/SKILL.md`
- **슬래시 커맨드**: `.claude/commands/*.md`
- **권한·훅**: `.claude/settings.json`
- **이전 워크플로우 자산** (참조용): `docs/storage/legacy/`
- **사이클별 reflection 보고서**: `docs/storage/workflow_reflections/`
