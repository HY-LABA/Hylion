---
name: claude-md-constraints
description: CLAUDE.md Hard Constraints 4 카테고리 체크리스트 + Critical 분류 가이드. planner·code-tester 가 룰 위반 검출 시 활용. TRIGGER when 워커가 변경 영역의 룰 적용을 검토할 때, 또는 verdict 발급 시 Critical 분류가 필요할 때.
---

# CLAUDE.md Hard Constraints 체크리스트

본 스킬은 `/CLAUDE.md` § Hard Constraints 의 4 카테고리를 운영 체크리스트로 정리. planner 가 awaits_user 분류 시, code-tester 가 verdict 결정 시 활용.

## Category A — 절대 금지 영역 (PreToolUse hook 차단)

자동화 중 어떤 워커도 수정 X. 시도하면 hook 이 exit 2 로 차단 + ANOMALIES `HOOK_BLOCK` 누적.

체크리스트:
- [ ] 변경 파일이 `docs/reference/` 하위인가?
- [ ] `.claude/agents/*.md`, `.claude/skills/**/*.md` 인가?
- [ ] `.claude/settings.json` 인가?
- [ ] `~/.claude/.credentials.json` 인가?

## Category B — 자동 재시도 X 영역

본 영역 변경된 todo 가 code-tester `MAJOR_REVISIONS` 받으면 자동 재시도 X (사용자 보고 게이트).

체크리스트:
- [ ] `orin/lerobot/`, `dgx/lerobot/` (옵션 B 원칙)
- [ ] `orin/pyproject.toml`, `dgx/pyproject.toml` (의존성)
- [ ] `orin/scripts/setup_env.sh` (Jetson PyTorch 직접 설치)
- [ ] `scripts/deploy_*.sh`
- [ ] `.gitignore`, `.git/info/exclude`

→ planner 가 본 영역 변경 todo 를 plan 에 포함 시 일반 dispatch (자율 1 cycle), code-tester 가 MAJOR 발급 시 orchestrator 에 보고 → 사용자 결정.

## Category C — 사용자 동의 필수 작업 (planner awaits_user 분류)

다음 작업이 plan 에 포함되면 planner 는 `awaits_user` 분류 + dispatch 전 사용자 답 받기.

체크리스트:
- [ ] 새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외)
- [ ] 외부 의존성 추가 (`pyproject.toml` 의존성 추가)
- [ ] 시스템 환경 변경 (가상환경 재생성·업그레이드)
- [ ] 외부 시스템 호출 (Category B 영역 변경된 deploy 등)
- [ ] 새 git 브랜치·태그·remote
- [ ] BACKLOG.md "높음" 우선순위 항목 자동 처리

## Category D — 절대 금지 명령 (settings.json deny)

다음 명령은 시스템 deny 로 차단:

- `Bash(rm -rf:*)`
- `Bash(sudo:*)`
- `Bash(git push --force:*)`, `Bash(git push -f:*)`
- `Bash(git reset --hard:*)`
- `Bash(chmod 777:*)`
- `Bash(curl -fsSL :* | bash)`

## 옛 룰 (유지)

- `docs/storage/` 하위에는 사용자 명시 요청 없으면 bash 명령 예시 추가 X

## Critical 분류 가이드 (code-tester 용)

**Critical** (`MAJOR_REVISIONS`):
- Category A 영역 수정 시도 (hook 이 막아도 시도 자체가 문제)
- Category B 영역 변경 시 Coupled File Rules 미준수 (`lerobot-upstream-check` 스킬 참조)
- TODO/DOD 명백한 미충족
- 단위 테스트 실패
- 수치·논리 모순
- 보안 결함
- 레퍼런스 없이 추측 작성 (`lerobot-reference-usage` 위반)

**Recommended** (`MINOR_REVISIONS` 또는 `READY_TO_SHIP`):
- 코드 스타일 미세 개선
- 문서 표현 다듬기
- 비-Critical lint 경고

→ Recommended 3건 이상이면 MINOR, 2건 이하면 READY.

## ANOMALY 누적 가이드

| 상황 | TYPE |
|---|---|
| Category A 영역 수정 시도 → hook 차단 | `HOOK_BLOCK` |
| 같은 todo 가 MAJOR 반복 | `MAJOR_RETRY` |
| 룰 모호하여 워커가 판단 보류 | `CONSTRAINT_AMBIGUITY` |
| 룰에 매핑되지 않는 새 카테고리 발견 | `SKILL_GAP` |

## Reference

- `/CLAUDE.md` § Hard Constraints (정책 정의)
- `/CLAUDE.md` § prod-test-runner 자율성 (deploy 시점 적용)
