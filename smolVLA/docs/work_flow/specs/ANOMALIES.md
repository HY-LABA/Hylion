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
| orchestrator | MAJOR_RETRY, AWAITS_USER_DELAY, USER_OVERRIDE, DEPLOY_ROLLBACK 발생 시 |
| prod-test-runner | PROD_TEST_FAIL verdict 발급 시 |
| code-tester / planner | SKILL_GAP, CONSTRAINT_AMBIGUITY 판단 시 |

---

(아직 활성 spec 없음 — 첫 사이클부터 누적 시작)
