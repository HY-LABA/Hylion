# Reflection — 06_dgx_absorbs_datacollector (2026-05-03)

> reflection 에이전트 자동 생성. 사용자 승인 후 메인이 갱신 적용.
> 직전 보고서: `docs/storage/workflow_reflections/2026-05-02_05_interactive_cli.md`

---

## §1 사이클 요약

| 항목 | 내용 |
|---|---|
| 활성 spec | `06_dgx_absorbs_datacollector` |
| 사이클 기간 | 2026-05-02 19:00 ~ 2026-05-03 10:30 (약 15h 30m) |
| 총 todo | 13 (L1·L2 / M1·M2·M3 / X1·X2·X3·X4·X5 / V1·V2·V3) |
| 자동 종결 (task·study, 10건) | 10/10 PASS (X4 skip 포함) |
| Phase 3 prod 검증 (3건) | V1·V2·V3 전부 NEEDS_USER_VERIFICATION → 사용자 무시 결정 (B-3), BACKLOG 이관 |
| code-tester 1차 verdict 분포 | READY_TO_SHIP 9 / MINOR_REVISIONS 1 (X5) |
| code-tester 2-cycle 발생율 | 1/10 = 10% (04 45%, 05 38% 대비 대폭 개선) |
| prod-test verdict 분포 | NEEDS_USER_VERIFICATION 3 / AUTOMATED_PASS 0 / FAIL 0 |
| ANOMALY 누적 (본 사이클) | USER_OVERRIDE 1건 (V1·V2·V3 BACKLOG 이관) |
| awaits_user 발동 | G·H (X1 후 일괄 발송) / I (X4 조사 후 발송) — 3건 모두 정상 해소 |
| 사용자 개입 (USER_INPUT) | 3회 (G·H 일괄 1회, I 1회, wrap 결정 1회) |
| USER_OVERRIDE | 1회 (V1·V2·V3 BACKLOG 이관 결정) |
| ORCHESTRATOR_GAP | 0건 (04·05 갱신 효과 지속) |
| 사이클 시간·토큰 | log.md 기록 기준 약 15.5h. 토큰 미집계 (log.md 에 토큰 정보 없음) |

### 04·05 reflection 기준치 대비 지표 변화

| 지표 | 04 | 05 | 06 | 비고 |
|---|---|---|---|---|
| 2-cycle 발생율 | 45% | 38% | 10% | 대폭 개선 — X5 MINOR 1건만 발생 |
| AUTOMATED_PASS 비율 | 0% | 0% | 0% | 변동 없음 — test 타입은 물리 환경 의존 고착 |
| NEEDS_USER_VERIFICATION 비율 | 55% | 27% | 23% (3/13) | 소폭 개선 |
| ORCHESTRATOR_GAP | 2건 | 0건 | 0건 | 04 갱신 효과 지속 |
| USER_OVERRIDE | 0건 | 1건 | 1건 | 환경 의존 fallback 패턴 반복 |
| awaits_user 효율 | — | 3건·분리 발송 | G·H 일괄 + I 별도 = 2회로 처리 | 적정 분할 |

---

## §2 발견 패턴

### 패턴 1 — 환경 의존 fallback 패턴의 3 회 누적 확립

**발생**: USER_OVERRIDE 1건 (ANOMALIES 06 #1) — 04 BACKLOG #7, 05 ANOMALIES #4 와 동일 신호

**구체 상황**:
- 04 BACKLOG #7: Phase 3 사용자 검증 대기 7건 (시간·환경 의존) → BACKLOG 이관 (1회째)
- 05 ANOMALIES #4: 사용자 옵션 A (끝까지 검증) → 옵션 B (wrap) fallback — 학교 WiFi 차단 트리거 (2회째)
- 06 ANOMALIES #1: V1·V2·V3 모두 NEEDS_USER_VERIFICATION + DGX·Orin 시연장 환경 떨어짐 → 사용자 무시 결정 B-3 으로 BACKLOG 이관 (3회째)

**패턴 분석**:
본 프로젝트에서 "코드·문서 변경 = 자동화 100% 완결, Phase 3 실물 검증 = 물리 환경 의존으로 BACKLOG 이관" 흐름이 구조적 패턴으로 확립됐다. 06 사이클의 경우 코드·문서 10/10 완전 자동화 종결이었음에도 prod 검증 3건이 환경 이유로 무시됐다.

**핵심 문제**:
1. `/wrap-spec` 이 "미처리 verification_queue 항목이 있어도 사용자가 무시 결정 내리면 통과" 구조 — 현재 명시적 prompt 없이 사용자 자연어 판단에 전적 의존
2. spec 작성 시 V 그룹 (Phase 3 실물 검증) todo 가 "환경 의존" 임을 명시적으로 분류하는 메타데이터 없음 — planner 가 V 그룹을 plan 에 포함할 때 환경 전제 조건을 `awaits_user` 분류 대신 단순 의존 조건으로만 명시

**현재 룰 검토**:
- CLAUDE.md Phase 3 절은 "사용자 /verify-result → 통과 분기 + 실패 분기" 만 명시. "미처리 항목의 명시적 처리 결정" 강제 없음
- plan.md §6 검증 대기 큐 후보는 상세하게 기술되지만 "환경 전제 조건이 미충족 시 어떻게 처리" 에 대한 플로우 없음
- verification_queue.md 형식에 "환경 전제 조건" 필드 없음

**04 reflection 비교**: 04 패턴 없음. 05 갱신 제안에서 USER_OVERRIDE fallback 패턴 정책화를 "META #9 와 함께 차기 사이클 정식 검토" 로 보류함 → 06 에서 동일 패턴 3회째 재발.

**harness 원칙 매핑**: 원칙 10 (사람 입력의 방향성) — 사람의 "무시 결정" 이 반복 발생한다면 자동화가 그 결정을 미리 수행하거나 최소한 구조화된 선택지를 제공해야 함. 원칙 3 (에이전트 가독성) — "환경 의존 verification 항목은 자동화 시 BACKLOG 이관 후보" 라는 지식이 어디에도 명문화되지 않음.

**제안 위치**: 갱신 제안 #1, #4

---

### 패턴 2 — legacy 이관 + grep 인계 워크플로우의 효율성

**발생**: L2 (grep 다수 발견·인계) + X2 (7라인 sync_ckpt 참조 정정) + M3 (11파일 잔재 정리) — 3 todo 연쇄

**구체 상황**:
L2 task-executor 가 datacollector 자산 통째 이관 후 `grep` 으로 경로 하드코딩 잔재를 발견하여 X2·M3 에 인계 명세를 작성했다. code-tester L2 verdict 시 Recommended 2번으로 "인계 라인 번호 보강" 을 요청했다. M3 에서 11파일 정리를 완료했고, X2 에서 `training.py` 7라인 `sync_ckpt_dgx_to_datacollector.sh` 참조를 정정했다.

이 "grep 결과를 후속 todo 에 구조적으로 인계" 하는 패턴은 본 사이클에서 처음으로 명시적으로 동작했고, plan.md 의 R4 위험 신호 ("datacollector 경로 하드코딩 잔재") 에 대한 정확한 선제 대응이었다.

단, BACKLOG 06 #6 에는 M3 code-tester 가 발견한 `lerobot-reference-usage/SKILL.md:111` 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 경로 오기재가 Category A 영역이라 워커가 수정하지 못하고 인계된 상태다. 이 패턴 — "Category A 파일 내 경로 참조 오기재를 grep 으로 발견했으나 워커가 수정 불가 → reflection 인계" — 은 현재 시스템에서 처리 흐름이 명확하지 않다.

**현재 룰 검토**:
- "대규모 파일 이동 후 grep 로 잔재 탐색 → 후속 todo 에 인계" 패턴이 skill·agent 정의에 명시된 표준 절차 없음
- Category A 파일 내 경로 참조 오기재 발견 시 처리 흐름 불명 (현재: BACKLOG #6 에서 "reflection 시점 처리" 로 미루어짐)
- lerobot-reference-usage SKILL.md 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 참조는 실제로 `legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 로 갱신 필요 (Category A 영역이므로 반드시 메인 수동 적용)

**harness 원칙 매핑**: 원칙 3 (에이전트 가독성) — "이동 후 잔재 grep 결과를 후속 todo 에 인계하는 표준 형식" 이 문서화되면 향후 대규모 이관 시 재현 가능. 원칙 4 (황금 원칙 + 가비지 컬렉션) — Category A 파일 내 경로 오기재는 "기술 부채의 특수 사례" 로, reflection 이후에도 처리 흐름이 명확하지 않으면 누적될 수 있음.

**제안 위치**: 갱신 제안 #5 (lerobot-reference-usage SKILL.md 경로 갱신 — Category A, 즉시 수동 적용)

---

### 패턴 3 — spec 본문 가정과 실제 파일 구조의 충돌 (setup_env.sh 오기재)

**발생**: 1건 (X5 task-executor 발견 — BACKLOG 06 #8 등록)

**구체 상황**:
spec 본문 및 plan.md 에서 `dgx/scripts/setup_env.sh` 로 표기됐으나, 실제 DGX 파일은 `dgx/scripts/setup_train_env.sh` 였다. X5 task-executor 가 작업 시작 후 발견했고, 보고서 §5 잔여 리스크 표에 "spec 표기 오류" 로 명시 후 `setup_train_env.sh` 에 정확히 작업했다. code-tester X5 보고서도 DOD 충족 체크 시 "실제 파일명 setup_train_env.sh — spec 오기재" 를 명시했다.

**영향**:
파일명 오기재가 실제 작업에 악영향을 주진 않았지만 (task-executor 가 직접 확인), "spec Phase 1 작성 시 실제 파일 이름·경로를 직접 확인하지 않고 기억·추측으로 작성한 것" 이 root cause 다. 동일 패턴이 반복되면 spec Phase 1 자체의 신뢰도가 떨어진다.

**현재 룰 검토**:
- CLAUDE.md Phase 1 절에 "todo 에 언급된 파일·경로는 실존 확인 의무" 없음
- planner.md 에도 "spec 본문의 파일명 정합성 검증" 절 없음
- spec 작성 가이드라인이 사용자 + 메인 Claude 의 "대화형 합의" 에 의존하므로, 특정 파일 이름이 틀렸더라도 자동 검증 없음

**04·05 reflection 비교**: 04 패턴 3 "레퍼런스 추측 작성" 과 동류 — Phase 1 에서 가정을 사실 확인 없이 명시하는 패턴. 05 에서 lerobot-reference-usage 강화로 code 단위 추측 작성은 감소했지만, spec 메타 레벨 (파일명·경로 표기) 의 검증 의무는 여전히 없음.

**harness 원칙 매핑**: 원칙 6 (YOLO-style 금지 — 추측한 모양 위에 빌드 X) — spec 에 언급된 파일 경로를 "추측으로 작성" 하는 것은 YOLO 의 특수 사례. 이 경우 code 수준이 아닌 spec 메타 수준에서 발생했다는 점이 다르다. 원칙 3 (에이전트 가독성) — planner 가 spec 본문을 입력 자료로 받지만 파일명 정합성을 별도 검증하지 않음.

**제안 위치**: 갱신 제안 #2

---

### 패턴 4 — spec 가정 조사 후 반증 (Option A vs B 제시 + 사용자 권고 채택)

**발생**: 1건 (X4 task-executor — awaits_user I 조사 결과에서 DGX pyproject.toml 미존재 발견)

**구체 상황**:
plan.md 와 spec 본문에 "TODO-X4: dgx/pyproject.toml extras 추가" 로 명시됐으나, task-executor 가 조사 단계에서 `dgx/pyproject.toml` 이 **애초에 존재하지 않음** 을 발견했다. DGX 는 lerobot upstream submodule 을 `setup_train_env.sh` 에서 직접 editable 설치하는 구조였다 (pyproject.toml 없이도 9 entrypoint 이미 등록됨). task-executor 가 이 사실을 발견하고 Option A (pyproject.toml 신규 생성) vs Option B (setup_env.sh 만 수정) 를 사용자에게 제시했고, 사용자는 Option B (권고 채택) 를 선택했다. 결과적으로 X4 는 변경 0건 (조사 보고서만 보존), X5 가 단독으로 extras 설치 책임을 흡수했다.

**패턴 분석**:
spec Phase 1 시점에 "DGX 에 pyproject.toml 이 있을 것" 이라는 가정이 암묵적으로 내포됐다. task-executor 가 Category B awaits_user 절차를 통해 조사 먼저 수행 → 가정 반증 발견 → 사용자 제시 → 올바른 결정을 이끌어낸 워크플로우는 잘 동작했다. 그러나 이 패턴이 "어떤 경우에 조사 선행 + 가정 반증 가능성 감지가 필요한가" 를 명시하는 가이드 없이 암묵적으로 동작했다.

**현재 룰 검토**:
- task-executor.md / planner.md 에 "spec 본문의 암묵적 가정 (파일 존재 여부·현재 구조) 을 실제 코드베이스에서 사전 확인" 의무 없음
- lerobot-reference-usage 는 "레퍼런스에서 존재 확인 후 작성" 을 다루지만, "현재 코드베이스의 실제 구조 (파일 존재 여부·설치 방식) 확인" 은 별도로 언급 없음
- Category B awaits_user 절차가 조사 단계를 자연스럽게 포함한 것은 긍정적 — 단 이 패턴이 "Category B 에만" 적용되는지 vs "일반 task 에도" 적용해야 하는지 불명확

**05 reflection 비교**: 05 패턴 2 (Python 3.12 가정 오류) 와 동류 — "spec Phase 1 에 명시된 가정이 실제 환경 조사 후 반증될 수 있음". 05 에서는 setup_env.sh 수정 후 반증 발견 (비용 발생), 06 에서는 조사 먼저 (Category B awaits_user) 후 반증 발견 (비용 최소) — 06 의 흐름이 더 적절했음.

**harness 원칙 매핑**: 원칙 3 (에이전트 가독성) — "spec Phase 1 가정이 실제 코드베이스 구조와 어긋날 수 있음" 이라는 지식 명시 필요. 원칙 10 (사람 입력의 방향성) — Option A vs B 제시가 "사용자의 조직 메모리 (DGX 구조 의도) 에 의존하는 판단" 이었으므로 사람 개입이 정당했음. 단 "조사 후 가정 반증 발견 → 사용자 제시" 패턴을 표준화하면 매번 암묵적 판단에 의존하지 않아도 됨.

**제안 위치**: 갱신 제안 #3

---

### 패턴 5 — AUTOMATED_PASS 0% 고착: 물리 환경 의존 verification 구조

**발생**: 사이클 4·5·6 연속 AUTOMATED_PASS 0% — test 타입 todo 전건이 NEEDS_USER_VERIFICATION

**구체 상황**:
04 사이클: test 6건 모두 NEEDS_USER_VERIFICATION (Bash 도구 차단 + 실물 의존)
05 사이클: test 3건 모두 NEEDS_USER_VERIFICATION (실물 의존)
06 사이클: test 3건 모두 NEEDS_USER_VERIFICATION (DGX 실물 SSH 불가 + 시연장 환경 떨어짐)

현재 prod-test-runner 는 DGX SSH read-only 검증을 자율 수행할 수 있으나 (CLAUDE.md prod-test-runner 자율성 표), 06 에서는 DGX SSH 자체가 불가능했기 때문에 devPC 정적 검증만 수행했다. 정적 검증 (py_compile·ruff·bash -n) 은 모두 통과했으나 실물 6·12·10항목은 모두 사용자 위임.

**패턴 분석**:
이 구조는 본 프로젝트의 물리 환경 특성 (Orin·DGX·시연장 = 물리적으로 분리된 노드) 에서 필연적이다. "코드 정확성 자동 검증" vs "하드웨어 동작 실물 검증" 의 경계가 명확하고, 후자는 자동화 불가다. 단 AUTOMATED_PASS 0% 가 "자동화 한계" 인지 vs "개선 가능한 구조" 인지를 점검할 시점이다.

개선 가능한 영역: prod-test-runner 가 DGX SSH 가능 상태일 때 자율 smoke test (ssh dgx `python3 -c "import lerobot"` 등) 를 먼저 수행하고 AUTOMATED_PASS 를 일부 획득할 수 있는 구조가 있지만, 현재 verification_queue 에는 "DGX SSH 가능 전제 test 항목" vs "시연장 물리 전제 test 항목" 이 구분 없이 혼재.

**현재 룰 검토**:
- CLAUDE.md prod-test-runner 자율성 표에 "ssh orin/dgx read-only 검증 = 자율" 명시 있음 — 단 "SSH 불가 시 devPC 정적 fallback" 흐름은 암묵적 동작이며 명시 없음
- verification_queue.md 형식에 "SSH 자율 검증 가능 항목" vs "시연장 물리 필수 항목" 구분 필드 없음

**harness 원칙 매핑**: 원칙 9 (최소 차단 병합 게이트) — AUTOMATED_PASS 가능한 항목을 자동으로 처리하고 실물 필수 항목만 사용자 위임하면 사람 부담 감소. 원칙 2 (Progressive Disclosure) — verification_queue 에 검증 항목의 "전제 조건 레벨" 을 분류하면 자동화 처리 범위가 명확해짐.

**제안 위치**: 갱신 제안 #4 (패턴 1 과 연계)

---

## §3 하네스 원칙 평가

### 10 원칙 매핑 (10점 척도)

| 원칙 | 06 점수 | 05 점수 | 변화 | 본 사이클 근거 |
|---|---|---|---|---|
| 1. CLAUDE.md = 목차 | 7/10 | 7/10 | 동일 | 분량 적절 유지. 단 wrap-spec 절차 명시 추가 여지 있음 |
| 2. Progressive Disclosure | 8/10 | 8/10 | 동일 | G·H·I awaits_user 분할 발송 적절. verification_queue 항목 분류 미흡 |
| 3. 에이전트 가독성 | 6/10 | 5/10 | +1 | spec 파일명 오기재 발견·인계 (X5 §5), Category A 경로 오기재 인계 (BACKLOG #6). 보이지 않는 지식이 여전히 일부 존재 |
| 4. 황금 원칙 + 가비지 컬렉션 | 7/10 | 6/10 | +1 | 2-cycle 발생율 10% 로 대폭 개선. grep 인계 패턴이 잔재 청소 역할 수행 |
| 5. 맞춤형 린터 | 6/10 | 5/10 | +1 | py_compile·ruff·bash -n 이 모든 코드 todo 에서 실행됨 (05 화이트리스트 16건 효과). shellcheck 미설치는 잔여 |
| 6. YOLO-style 금지 | 7/10 | 6/10 | +1 | X4 조사 선행 패턴 (가정 반증 발견). spec 파일명 오기재는 여전히 YOLO 잔재 |
| 7. Architecture Fitness | 6/10 | 6/10 | 동일 | DGX lerobot editable 설치 구조 발견 (X4) 으로 아키텍처 이해 증가. invariant 자동 검증 없음 |
| 8. 자체 구현 선호 | 7/10 | 7/10 | 동일 | Option B (setup_env.sh 단독) 채택 = 단순성 우선 양호 |
| 9. 최소 차단 병합 게이트 | 7/10 | 6/10 | +1 | 2-cycle 1건만, AUTOMATED_PASS 0% 고착은 구조적 한계 |
| 10. 사람 입력의 방향성 | 7/10 | 7/10 | 동일 | G·H·I 모두 "조직 메모리·아키텍처 결정" 수준 판단. V1·V2·V3 BACKLOG 이관도 사용자만 판단 가능한 환경 결정 |

**평균**: 6.8/10 (05: 6.3/10, 04: 5.9/10 — 사이클별 개선 추세 확인)

---

## §4 갱신 제안 (사용자 승인 필요)

| # | 대상 파일 | 변경 내용 요약 | 위험도 | 우선순위 |
|---|---|---|---|---|
| 1 | `CLAUDE.md` Phase 3 절 | `/wrap-spec` 시 미처리 verification_queue 항목 → 명시적 처리 prompt 강제 절차 추가 | 낮음 | 적용 |
| 2 | `.claude/agents/planner.md` | spec 작성 시 언급된 파일·경로 실존 확인 권고 절 추가 | 낮음 | 적용 |
| 3 | `.claude/agents/task-executor.md` (또는 lerobot-reference-usage) | "Category B awaits_user 조사 단계에서 spec 가정이 실제 코드베이스와 충돌 시 사용자 제시" 패턴 명문화 | 낮음 | 차기 검토 |
| 4 | `CLAUDE.md` Phase 3 절 / verification_queue 형식 | verification_queue 항목에 "환경 전제 조건 레벨 (SSH 자율 가능 / 시연장 물리 필수)" 분류 필드 추가 | 낮음 | 적용 |
| 5 | `.claude/skills/lerobot-reference-usage/SKILL.md` (Category A — 즉시 수동 적용) | line 111 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 경로를 `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 로 정정 | 낮음 | 즉시 적용 (Category A 영역 — 메인 수동) |

### 상세 변경 명세

---

#### 제안 #1 — CLAUDE.md Phase 3 절: 미처리 verification_queue 항목 처리 강제

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/CLAUDE.md`

**도입 사유**: 04 BACKLOG #7 + 05 ANOMALIES #4 + 06 ANOMALIES #1 로 3 회 연속 "환경 의존 test 항목 BACKLOG 이관" 패턴이 고착. 현재 `/wrap-spec` 흐름에서 이 처리가 사용자의 자연어 판단에 전적 의존하며, 명시적 처리 결정이 강제되지 않음.

**변경 내용**:

`## 워크플로우 — 3 Phase 모델` 의 `### Phase 3 — Verification (사용자)` 절 하단 `**분기**:` 에 다음 항목 추가:

```markdown
  - 미처리 항목 (환경 의존 등으로 검증 불가) → `/wrap-spec` 전 명시적 처리 결정 필요:
    - 무시 결정 (B-3): 항목별 이유·전제 조건 명시 후 BACKLOG 이관 → `/wrap-spec` 진행
    - 연기 결정: 같은 spec 내 조건 충족 시까지 대기
    - Phase 3 실패 분기 진입
```

---

#### 제안 #2 — planner.md: spec 작성 시 파일·경로 실존 확인 권고

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/planner.md` (Category A — 메인 수동 적용)

**도입 사유**: X5 에서 spec 본문 `setup_env.sh` ↔ 실제 `setup_train_env.sh` 파일명 오기재 발견. spec Phase 1 에 명시된 파일·경로가 실제 코드베이스와 다를 경우 task-executor 가 작업 시작 후 발견하게 됨 — 늦은 오류 감지.

**변경 내용**:

`### 2. todo 추출 + 분석` 절의 각 todo 분석 항목에 추가:

```markdown
- 파일·경로 정합 확인: spec 본문에 명시된 파일명·경로가 실제 코드베이스에 존재하는지 Glob/Read 로 사전 확인. 오기재 발견 시 §6 가정 절에 "spec 본문 X 는 실제 Y 임" 명시.
```

`## 확신 가정 (병렬 진행 OK)` 형식 예시에 추가:

```markdown
## 확신 가정 (병렬 진행 OK)
- ...
- 파일명 정합: spec 본문 `setup_env.sh` → 실제 파일 `setup_train_env.sh` (사전 확인 완료)
```

---

#### 제안 #3 — task-executor.md: 조사 후 가정 반증 발견 시 사용자 제시 패턴 명문화

**대상**: `.claude/agents/task-executor.md` (Category A — 메인 수동 적용)

**도입 사유**: X4 에서 task-executor 가 조사 단계에서 `dgx/pyproject.toml` 미존재를 발견하고 Option A vs B 를 사용자에게 제시한 것은 좋은 패턴이었으나, 현재 agent 정의에 이 패턴이 명시되지 않아 암묵적 동작에 의존.

**변경 내용**:

task-executor.md (실제 파일 내용 확인 후 적절한 위치에) 다음 절 추가:

```markdown
## spec 가정 반증 발견 시 처리

작업 시작 전 또는 조사 단계에서 spec·plan.md 의 암묵적 가정이 실제 코드베이스와 충돌할 경우:

1. 작업 보류 (기존 파일 수정 X)
2. 발견 내용 정리:
   - "spec 가정: <A>. 실제 코드베이스: <B>."
   - 가능한 선택지 (Option A / Option B) + 각 장단점 + 권고
3. orchestrator 에게 보고 → orchestrator 가 사용자에게 awaits_user 발송
4. 사용자 결정 수신 후 작업 재개

**위반 패턴**:
- spec 에 "X 파일 갱신" 이라고 명시됐는데 X 가 존재하지 않음 → 파일 신규 생성 전 확인 필수
- spec 가정과 실제 구조가 다를 때 임의로 한 옵션 선택 후 진행 X
```

**위험도 낮음 — 단 task-executor.md 가 Category A 영역이므로 메인 수동 적용 필요. 본 사이클에서 X4 가 정확히 이 패턴을 따랐으므로 문서화만 남음.**

---

#### 제안 #4 — CLAUDE.md + verification_queue 형식: 환경 레벨 분류 필드

**대상**: `CLAUDE.md` (planner §6 검증 큐 운영 원칙 또는 Phase 3 절)

**도입 사유**: 04·05·06 세 사이클 연속으로 AUTOMATED_PASS 0% — test 타입 todo 전부 NEEDS_USER_VERIFICATION 이었다. 이 중 "DGX SSH 자율 검증 가능 항목" 과 "시연장 물리 필수 항목" 이 verification_queue 에 혼재하여 prod-test-runner 가 상황에 따라 다른 처리를 해야 함. 구분 명시 시 prod-test-runner 가 SSH 가능 상태일 때 자율 처리 가능 항목을 먼저 처리 → AUTOMATED_PASS 일부 획득 가능.

**변경 내용**:

`CLAUDE.md § 워크플로우 Phase 2` 의 prod-test-runner 관련 부분 또는 Phase 3 절에 다음 분류 명시:

```markdown
#### verification_queue 항목 환경 레벨 분류

| 레벨 | 의미 | prod-test-runner 처리 |
|---|---|---|
| SSH_AUTO | DGX/Orin SSH 자율 검증 가능 | 자율 AUTOMATED_PASS 목표 |
| PHYS_REQUIRED | 시연장 물리 환경 필수 | NEEDS_USER_VERIFICATION 즉시 발급 |

plan.md §6 검증 대기 큐 후보 작성 시 레벨 명시 권고.
```

---

#### 제안 #5 — lerobot-reference-usage SKILL.md: 경로 오기재 즉시 정정 (Category A)

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/skills/lerobot-reference-usage/SKILL.md` (Category A — 메인 수동 즉시 적용)

**도입 사유**: L1 task-executor 가 발견 → M3 code-tester 가 Rec 으로 인계 → BACKLOG 06 #6 에 "reflection 시점 처리 후보" 로 등록됨. 현재 SKILL.md line 111 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 는 L1 git mv 이후 실제로는 `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 에 있다.

**변경 내용**:

SKILL.md line 111 단독 수정:

```
변경 전: `docs/storage/legacy/CLAUDE_pre-subagent.md`
변경 후: `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md`
```

**위험도 낮음 (단순 경로 정정). Category A 영역이므로 메인 Claude 가 사용자 승인 후 직접 수정.**

---

## §5 사용자 승인 결과

사용자 답 (2026-05-03): "모두 적용". 메인 Claude 가 hook 임시 비활성화 (사용자 협조) 후 5 갱신 모두 직접 적용.

| # | 결정 | 적용 시점 | 비고 |
|---|---|---|---|
| 1 | ✅ 적용 | 2026-05-03 wrap | CLAUDE.md Phase 3 절: `/wrap-spec` 미처리 verification_queue 처리 정책 신규 절 (무시/연기/실패 prompt 강제). wrap-spec.md 사전 조건도 동시 보강 |
| 2 | ✅ 적용 | 2026-05-03 wrap | planner.md §2 spec 본문 언급 파일·경로 실존 확인 절 신규 추가 (이후 §3~§7 번호 시프트). 06 의 setup_env.sh 오기재 패턴 차단 |
| 3 | ✅ 적용 | 2026-05-03 wrap | task-executor.md §2-c spec 가정 반증 검증 절 신규 (Option A/B 사용자 제시 패턴 명문화). 06 X4 패턴 미러 |
| 4 | ✅ 적용 | 2026-05-03 wrap | CLAUDE.md Phase 3 절: verification_queue 환경 레벨 분류 (`AUTO_LOCAL`/`SSH_AUTO`/`PHYS_REQUIRED`) + planner.md §6 동시 적용. AUTOMATED_PASS 0% 고착 해소 첫 단계 |
| 5 | ✅ 적용 | 2026-05-03 wrap | `lerobot-reference-usage/SKILL.md` line 111 경로 정정 (`legacy/CLAUDE_pre-subagent.md` → `legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md`). BACKLOG 06 #6 자연 처리 |

**갱신 적용 시 hook 차단**: 04 ANOMALIES #4 + 05 ANOMALIES #1 의 META #9 (메인 세션 우회 조건 미해결) 가 본 사이클에서도 재발. 사용자가 hook matcher (`Write|Edit` → `NEVER_MATCH`) 임시 비활성화 → 메인 5 Edit 적용 → 사용자 복원 흐름. **META #9 차기 사이클 정식 갱신 후보** — 본 사이클에서 적용된 5 갱신은 모두 hook 메커니즘 자체와 무관 (Phase 3 정책·planner·task-executor·skill 경로·환경 레벨 분류).

---

## §6 관련 ANOMALIES.md 처리

본 보고서로 분석된 anomaly 항목들:

| ANOMALIES 항목 | 관련 제안 | 현재 처리 상태 |
|---|---|---|
| 06 #1 USER_OVERRIDE (V1·V2·V3 BACKLOG 이관) | 제안 #1, #4 | 미처리 → reflection 분석됨 |

BACKLOG 06 #6 (lerobot-reference-usage SKILL.md 경로 오기재) → 제안 #5 로 즉시 처리 후보 도출.

---

## §7 05 reflection 제안 재발 여부 확인

| 05 제안 | 적용 여부 | 06 재발 |
|---|---|---|
| #1 settings.json 16건 추가 | 적용 (부분) | 06 사이클 추가 auto_grants 0건 — 완전 효과 확인 |
| #2 hook 메인 세션 우회 (META #9) | 보류 | 06 사이클 Category A 영역 wrap-spec 수정 없음 — 미발동 (잠재 미해결) |
| #3 lerobot-upstream-check Python 버전 grep | 적용 | 06 사이클 Python 버전 이슈 없음 — 효과 확인 |
| #4 04_devnetwork.md 학교 WiFi 차단 | 적용 | 06 플래너가 V2 에서 "학교 WiFi HF Hub push 권고" 명시 (plan.md §6) — 효과 확인 |
| #5 02_hardware.md USB 토폴로지 | 적용 | 06 사이클 USB 이슈 없음 |
| #6 Category B + datacollector/lerobot/ 추가 | 적용 | datacollector 노드 legacy 이관 완료 — 관련 없어짐. 단 옵션 B 영역 정의 자체는 유지 |

---

## §8 다음 사이클 진입 권고

### BACKLOG 처리 우선순위

| BACKLOG | 내용 | 추천 처리 |
|---|---|---|
| 06 #1·#2·#3 (V1·V2·V3) | DGX 시연장 이동 후 실물 검증 | 07_leftarmVLA 진입 전 처리 필수 (데이터 수집 기반) |
| 06 #4 (sync_ckpt_dgx_to_orin.sh) | DGX → Orin ckpt 전송 스크립트 | 07_leftarmVLA 학습 후 배포 시 필요 |
| 06 #6 (SKILL.md 경로) | Category A 수정 — 즉시 처리 가능 | 본 reflection 승인 후 제안 #5 즉시 적용 |
| 06 #8 (spec 파일명 오기재) | 메타 학습 신호 — 차기 spec Phase 1 시 정확한 파일명 사용 | 제안 #2 (planner.md) 적용 후 구조 개선 |

### 차기 spec 권고

07_leftarmVLA 진입 전 조건:
1. 06 V1·V2·V3 실물 검증 (DGX 시연장 이동 가능 시)
2. 카메라 키 매핑 결정 (BACKLOG 03 #1 — smolvla_base camera1/2/3 vs top/wrist)
3. sync_ckpt_dgx_to_orin.sh 신규 작성 (06 BACKLOG #4)

### 하네스 차기 개선 권고

- `docs/QUALITY_SCORE.md` 신설 검토 (harness-engineering-principles §보강 후보 #2) — 사이클별 2-cycle 발생율 추세 그래프 (04: 45% → 05: 38% → 06: 10%) 를 시각화하면 개선 효과 확인 + 목표 설정 가능
- verification_queue 환경 레벨 분류 (제안 #4) 는 AUTOMATED_PASS 0% 고착 해소의 첫 단계 — 구조 변경 비용 낮음, 효과 높음 (우선 적용 권장)
- META #9 (hook 메인 세션 우회) 는 차기 사이클에서도 Category A 영역 wrap-spec 수정이 필요한 상황이 발생하면 재발할 잠재적 문제 — 07 사이클에서 reflection 갱신 제안이 Category A 영역을 포함할 경우 hook 임시 비활성화 흐름 재발 예상
