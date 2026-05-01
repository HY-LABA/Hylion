# Anomalies — 하네스 발전 단서

> 하네스 차단·이상 패턴 누적. spec 별 섹션. 사이클 종료 시 reflection 에이전트가 본 파일을 분석하여 skill·hook·CLAUDE.md 갱신 제안 도출.
>
> **`BACKLOG.md` 와의 차이**: BACKLOG = 구현 차원 잔여. ANOMALIES = 시스템(하네스) 차원 잔여.
>
> 자세한 정책은 `/CLAUDE.md` § Hard Constraints / 가시화 레이어 참조.

## TYPE 정의

| TYPE | 의미 |
|---|---|
| `HOOK_BLOCK` | PreToolUse hook 이 워커 도구 호출 차단 (Category A 영역 수정 시도) |
| `MAJOR_RETRY` | code-tester 가 같은 todo 에 MAJOR_REVISIONS 반복 발급 |
| `AWAITS_USER_DELAY` | awaits_user 항목이 N 분 이상 정지 |
| `PROD_TEST_FAIL` | prod-test-runner FAIL verdict 발급 |
| `USER_OVERRIDE` | 사용자가 자연어로 자동화 흐름 수정 (planner·orchestrator 결정 무효화) |
| `SKILL_GAP` | code-tester / planner 가 "관련 skill 없음, 추측 진행" 판단 |
| `CONSTRAINT_AMBIGUITY` | Hard Constraints 가 모호하여 워커가 판단 보류 |
| `DEPLOY_ROLLBACK` | prod-test 후 사용자 검증에서 롤백 결정 |
| `ORCHESTRATOR_GAP` | orchestrator 가 plan 의 dispatch 또는 후처리 (spec 본문 갱신·verdict 추적) 를 누락 |

## 처리 상태 정의

- `미처리` — 사이클 진행 중
- `reflection 분석됨` — 사이클 종료 후 reflector 가 봤음
- `갱신 적용` — 사용자 승인하여 skill/hook/CLAUDE.md 갱신됨
- `무시됨` — 사용자가 처리 안 하기로 결정

## 형식

각 spec 섹션:

```
| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
```

- `시각`: `YYYY-MM-DD HH:MM`
- `source`: 신호 발생 주체 (예: `task-executor:O3`, `hook:PreToolUse`)
- `details`: 한 줄 요약 (구체 파일·verdict 등)

## 누적 정책

| 누가 | 언제 |
|---|---|
| PreToolUse hook | Category A 차단 시 즉시 |
| orchestrator | MAJOR_RETRY, AWAITS_USER_DELAY, USER_OVERRIDE, DEPLOY_ROLLBACK, ORCHESTRATOR_GAP 발생 시 (자기 발견 또는 사용자 지적) |
| prod-test-runner | PROD_TEST_FAIL verdict 발급 시 |
| code-tester / planner | SKILL_GAP, CONSTRAINT_AMBIGUITY 판단 시 |

---

## 04_infra_setup (후반 사이클)

| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
| 1 | 2026-05-01 14:30 | SKILL_GAP | code-tester:G1 + 후속 다수 | bash -n / shellcheck / Bash 도구 전반이 sandbox 차단됨 → 수동 Read 직독으로 대체. **재현된 워커**: code-tester G1·X2·T2·T3·D2·T1·X3·M2·D3, prod-test-runner T2·T3·G2·D3 (Bash 도구 전체 차단 — 더 광범위, 14건 이상 누적). 결과적으로 정적 분석은 가능 (Read), 동적 실행 검증은 사용자 verification_queue 위임. **하네스 정책 검토 후보**: code-tester / prod-test-runner 의 bash 권한 확장 또는 hook 패턴 조정. reflection 분석 핵심 대상 — 본 사이클의 가장 큰 제약이자 학습 신호. | 갱신 적용 (2026-05-01 wrap: settings.json permissions.allow 에 `Bash(bash -n *:*)` + `Bash(shellcheck:*)` 추가. 사용자가 hook matcher 임시 비활성화 → 메인 적용 → 복원 흐름으로 처리) |
| 2 | 2026-05-01 15:24 | CONSTRAINT_AMBIGUITY | code-tester:D2 | `smolVLA/.gitignore` 신규 파일이 root `Hylion/.gitignore` 와 별도 위치에 생성됨. CLAUDE.md Category B 정의는 ".gitignore 패턴 추가/변경" 인데 **신규 .gitignore 파일 자체** 가 Category B 인지 모호. code-tester 가 보수적 진행 (패턴 합리성 확인 후 PASS), 단 정의 명확화 필요 — reflection 시 CLAUDE.md Hard Constraints Category B 정의 보강 후보. | 갱신 적용 (2026-05-01 wrap: CLAUDE.md Category B 의 `.gitignore` 행을 "패턴 추가·변경 vs 신규 생성" 으로 분리) |
| 3 | 2026-05-01 16:30 | ORCHESTRATOR_GAP | orchestrator (사용자 지적) | 본 사이클에서 (a) spec 본문 todo 체크박스·완료 메모 갱신 누락 (모든 11 dispatch 완료 후 사용자 직접 발견), (b) plan §3 Wave 4 의 G3·G4 dispatch 자체 누락 — 두 건의 orchestrator gap 발생. 본 TYPE 정의도 본 사이클 wrap 시점에 신규 추가 (소급 등록). | 갱신 적용 (2026-05-01 wrap: CLAUDE.md Phase 2 절 + start-spec.md TaskCreate/PHASE2_DONE 게이트로 차단 메커니즘 도입) |
| 4 | 2026-05-01 16:50 | HOOK_BLOCK | PreToolUse hook (메타) | wrap 시점 reflection 갱신 제안 #4·#5·#6 (`.claude/skills/lerobot-reference-usage/SKILL.md`, `.claude/skills/orin-deploy-procedure/SKILL.md`, `.claude/settings.json`) 적용 시도 시 PreToolUse hook 이 모두 차단. CLAUDE.md 명시 의도는 "메인 Claude 가 사용자 승인 후 직접 수정 가능" 이지만, settings.json 의 hook command (`if echo "$FILE" \| grep -qE '/\\.claude/skills/\|/\\.claude/settings\\.json$'`) 가 메인/워커 구분 없이 차단. → 메타 레벨 결함. hook 보강 (메인 세션 우회 조건) 또는 사용자 직접 수정 필요. | 부분 처리 (2026-05-01 wrap: 사용자가 hook matcher `Write\|Edit` → `NEVER_MATCH` 임시 변경 → 메인이 #4·#5·#6 모두 적용 → 사용자 복원 예정. 단 hook 정의의 메타 결함 자체는 미해결 — 차기 사이클 META 제안 #8 으로 hook 에 메인 우회 조건 (예: 환경 변수·세션 식별자) 추가 권고) |
