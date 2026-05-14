# TODO-W5 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 0건. Recommended 3건.

---

## 단위 테스트 결과

본 TODO 는 코드 구현이 아닌 문서 마킹 작업 (BACKLOG.md + spec 본문 체크박스). 실행 가능 코드 변경 없음 → pytest 해당 없음.

```
해당 없음 — 변경 파일: docs/work_flow/specs/BACKLOG.md, docs/work_flow/specs/07_e2e_pilot_and_cleanup.md
코드 파일 0건 변경.
```

## Lint/Type 결과

```
해당 없음 — .py 파일 변경 없음.
markdown 구조 검증: 표 정렬, 헤더, HTML 주석 이상 없음. 상세는 DOD 정합성 참조.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. BACKLOG.md — 누락 완료 마킹 4건 추가 (02#5, 05#2, 05#3, 06#6) | ✅ | 4건 모두 확인. "완료 (07 XX, 2026-05-0X)" 패턴 일관 |
| 2. BACKLOG.md — 기존 마킹 항목 보존 (02#7·#8, 03#14·#15·#16, 04#1·#3, 06#4·#7) | ✅ | 9건 모두 보존. 중복 추가 없음 |
| 3. BACKLOG.md — 신규 3건 추가 (07#7 run_python.sh -u, 07#8 deploy_orin --delete, 07#9 PHYS 통합) | ✅ | 07 섹션 #7~#9 확인. 번호 연속성 (#6 이후 연속 — 06#8 다음 07#1~#9). 내용·우선순위·발견 출처 정합 |
| 4. spec 본문 — 원본 21 todo (P1~P5, D1~D3, T1~T3, O1~O5, W1~W5) 전수 [x] | ✅ | 21건 모두 [x] 확인 |
| 5. spec 본문 — 신규 todo 섹션 "## 사이클 중 추가된 todo" 신설 + D1a·D4~D8 6건 명시 | ✅ | 섹션 존재 확인 (L397). D1a·D4·D5·D6·D7·D8 모두 [x] 마킹 + 상태 메모 포함 |
| 6. 신규 todo 모두 [x] + 자동화 완료 메모 형식 | ✅ | 6건 모두 [x] + "자동화 완료 ..." 메모 포함 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `07_e2e_pilot_and_cleanup.md` L241 — TODO-T3 상태 메모 | T3 prod-test verdict 가 `AUTOMATED_PASS` 임에도 메모가 "자동화 완료, **Phase 3 대기** (2026-05-04)" 로 기재됨. CLAUDE.md 정책상 AUTOMATED_PASS 는 "**자동화 완료 (YYYY-MM-DD)**" 형식 (Phase 3 대기 없음). 표현 불일치. 내용 자체는 올바름 (PASS 확인 기재됨). |
| R2 | `07_e2e_pilot_and_cleanup.md` L397~L428 — 신규 todo 섹션 개별 항목의 ANOMALIES/trigger 링크 미명시 | "## 사이클 중 추가된 todo" 섹션의 D1a·D4~D8 각 항목이 간략 상태 메모만 포함. 발견 ANOMALIES 번호 (예: 07-#2 SMOKE_TEST_GAP, walkthrough Ctrl+C, D7 cycle 3) 또는 trigger 명시가 없어 사후 추적성 저하. 단 spec 명세 외 추가 todo 라 형식 요구사항이 불명확한 측면 있음. |
| R3 | `07_e2e_pilot_and_cleanup.md` L219 — TODO-T2 메모 — "완주 확인" vs 실제 verification_queue 상태 | verification_queue 의 T2 상태는 "NEEDS_USER_VERIFICATION (학습 시작 PASS, 완주 polling 대기)" 인데 spec 메모가 "checkpoints/{001000,002000,last}/ 완주 확인" 으로 기재됨. prod-test 결과 요약에서 완주 확인 근거 (step 132 진행 중 + tqdm 잔여 20분 시점의 산출물 확인) 가 polling 이후 확인분과 혼재 가능. 내용상 완주가 확인되었다면 문제 없으나, verification_queue 와 spec 메모의 상태 표현이 미세하게 다름. |

---

## 평가 세부 내용

### 검증 항목 1 — BACKLOG 마킹 정합

**02 #5 (Ollama 서비스)**: BACKLOG.md L42 에 "완료 (07 T2 + D2, preflight_check.sh §4 Ollama GPU 점유 체크 + training.py preflight 5단계 흡수, 2026-05-04)" 마킹. verification_queue T2 에 "Ollama GPU 점유 없음 확인" 기록. 정합.

**05 #2 (orin/interactive_cli/ flow 0~5)**: BACKLOG.md L112 에 "완료 (07 O1, orin/interactive_cli/ flow 0~5 SSH_AUTO PASS + hil_inference PHYS_REQUIRED BACKLOG, 2026-05-04)" 마킹. verification_queue O1 에 SSH_AUTO PASS + PHYS_REQUIRED 3건 기록. 정합.

**05 #3 (dgx/interactive_cli/ 학습 mode 회귀)**: BACKLOG.md L113 에 "완료 (07 D2, dgx/interactive_cli/ 학습 mode 회귀 검증 PASS ...)" 마킹. verification_queue D2 에 py_compile·assertion·ckpt 분기 PASS 기록. 정합.

**06 #6 (SKILL.md L111 경로)**: BACKLOG.md L130 에 "완료 (07 W1 Read 확인, 이미 올바른 경로 ... 반영 확인 — 변경 불요, 2026-05-03)" 마킹. verification_queue W1 에 동일 확인 기록. 정합.

**신규 07 #7~#9**: L149~L151. #7 번호 = BACKLOG 07 섹션 7번째 항목으로 연속. #8·#9 동일. 내용이 01_implementation.md Step 2 설명 및 verification_queue 기록과 일치.

### 검증 항목 2 — spec 체크박스 전수

총 27 `[x]` 확인 (grep 결과 27건, `#### [x]` 패턴):
- P1~P5: 5건
- D1~D3: 3건
- T1~T3: 3건
- O1~O5: 5건
- W1~W5: 5건
- 신규 D1a, D4~D8: 6건
합계 = 27건. `#### [ ]` 패턴 0건.

### 검증 항목 3 — 신규 todo 섹션 정합

"## 사이클 중 추가된 todo" 섹션 (L397) 존재. D1a·D4·D5·D6·D7·D8 6건 모두 포함. 각 항목에 결과 메모 포함. 단 ANOMALIES 번호 또는 구체 trigger 링크 미명시 (Recommended R2).

### 검증 항목 4 — NEEDS_USER_VERIFICATION 항목의 [x] 마킹 정책 평가

CLAUDE.md Phase 2 정책: "prod-test NEEDS_USER_VERIFICATION (test/both) → [ ] 유지 + 자동화 완료, Phase 3 대기 메모".

현황 분석:

| todo | prod-test verdict | 게이트 통과 여부 | [x] 적정성 |
|---|---|---|---|
| D1 | NEEDS_USER_VERIFICATION | gate 1 사용자 통과 결정 (log PHASE3_GATE1_DONE) | ✅ [x] 합리 — Phase 3 통과 처리됨 |
| D2 | NEEDS_USER_VERIFICATION | gate 1 사용자 통과 결정 | ✅ [x] 합리 |
| D3 | NEEDS_USER_VERIFICATION | gate 1 사용자 통과 결정 | ✅ [x] 합리 |
| T1 | AUTOMATED_PASS | 해당 없음 | ✅ [x] 합리 |
| T2 | NEEDS_USER_VERIFICATION | gate 2 미진행 (log 에 PHASE3_GATE2_DONE 없음) | ⚠️ 정책상 [ ] — 그러나 W5 DOD 가 "전수 마킹" 요구, Phase 3 대기 메모 포함됨. 사이클 종료 시점 정리 작업으로 수용 가능 |
| T3 | AUTOMATED_PASS | 해당 없음 | ✅ [x] 합리 — 단 메모에 "Phase 3 대기" 표현이 불필요하게 포함됨 (R1) |
| O1 | NEEDS_USER_VERIFICATION | gate 3 미진행 | ⚠️ 정책상 [ ] — 단 Phase 3 대기 메모 포함. 동일 이유로 수용 |
| O4 | NEEDS_USER_VERIFICATION | gate 3 미진행 | 동일 |
| D4, D5, D6, D7, D8 | NEEDS_USER_VERIFICATION | gate 4 (비정규 게이트, BACKLOG 이관) | 동일 |

판단 근거: W5 DOD 자체가 "spec 본문 todo 체크박스 전수 마킹"을 요구하며, 사이클 완료 후 wrap-spec 진입 직전 정리 작업으로 dispatch됨. log L151 의 "W5 task-executor: ... spec 본문 27 todo [x]" 가 orchestrator 지시에 따른 수행임을 확인. gate 2·3·4 미진행 항목도 "Phase 3 대기" 메모와 함께 [x] 처리한 것은 CLAUDE.md 정책과 미세하게 다르나, W5 todo 자체의 DOD 를 충족하고 있으며 "자동화 완료, Phase 3 대기" 메모로 실제 상태가 명확히 표현됨. 이는 Critical 이 아닌 정책 적용 경계 사례 (CONSTRAINT_AMBIGUITY 후보)로 판단.

Critical 분류 기준 미충족 이유: DOD 명백한 미충족 없음, 수치·논리 모순 없음, CLAUDE.md Hard Constraints (Category A/B) 위반 없음.

### 검증 항목 5 — CLAUDE.md Hard Constraints

| Category | 상태 | 메모 |
|---|---|---|
| A (docs/reference/, .claude/agents/, .claude/skills/, settings.json) | ✅ | 변경 파일 없음. BACKLOG.md·spec 본문만 수정 |
| B (orin/lerobot/, dgx/lerobot/, pyproject.toml, setup_env.sh, deploy_*.sh, .gitignore) | ✅ | 해당 없음 |
| Coupled File Rules | ✅ | pyproject.toml·orin/lerobot/ 미변경 — 해당 없음 |
| 옛 룰 (docs/storage/ bash 예시 추가 X) | ✅ | docs/storage/ 미변경 |

### 검증 항목 6 — markdown syntax

- 표 정렬: BACKLOG.md 신규 행들이 기존 표 구조 (| # | 항목 | 발견 출처 | 우선순위 | 상태 |) 유지 확인.
- spec 헤더: "#### [x] TODO-XX" 패턴 일관.
- HTML 주석: 기존 구조 유지.
- 섹션 분리자 `---`: 위치 정합.
- 이상 없음.

---

## ANOMALIES

```
CONSTRAINT_AMBIGUITY: gate 2·3·4 미통과 NEEDS_USER_VERIFICATION 항목을 W5 (end-of-cycle 정리 todo) 에서 [x] + Phase 3 대기 메모로 처리한 것이 CLAUDE.md Phase 2 "[ ] 유지" 정책과 미세하게 다름. W5 DOD 자체가 "전수 마킹"을 요구하는 상황에서의 정책 경계 케이스. Critical 아님 — orchestrator 가 판단 결정하면 됨.
```

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/·.claude/ 미변경 |
| B (자동 재시도 X) | ✅ | 해당 영역 미변경 |
| Coupled File Rules | ✅ | 해당 없음 |
| 옛 룰 | ✅ | docs/storage/ bash 예시 추가 없음 |

---

## 배포 권장

MINOR_REVISIONS — prod-test-runner 진입 권장 (문서 마킹 작업이므로 prod-test 는 정적 확인 수준).

Recommended 3건은 모두 메모 표현·추적성 개선 사항으로 기능·정합성에 영향 없음. task-executor 1회 추가 수정 후 prod-test 진입 (재검증 X).
