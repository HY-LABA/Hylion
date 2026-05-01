# docs/storage/legacy/ — 이전 워크플로우 자산 보관소

본 디렉터리는 **2026-05-01 워크플로우 재구성 이전** 의 자산을 보존한다. 활성 영역에서 제거하되 맥락은 잃지 않도록 하기 위함.

## 보관 배경

2026-05-01, 본 프로젝트는 다음 워크플로우 전환을 시작:

| 이전 (~2026-04-30) | 이후 (2026-05-01~) |
|---|---|
| 3-AI 분업 (Claude / Copilot / Codex) | Claude 단일 + 서브에이전트 팀 |
| 슬래시 커맨드 → 외부 AI 프롬프트 출력 | 슬래시 커맨드 → 서브에이전트 호출 |
| `agent_plan.md` 의 3-AI 정책 | `.claude/agents/`·`.claude/skills/` 기반 |

본 폴더의 파일들은 **옛 정책의 정의·맥락을 기록**한다. 참조용이며 활성 워크플로우엔 영향 없음.

## 보관 파일

| 파일 | 원래 위치 | 정체 |
|---|---|---|
| `HANDOFF_2026-04-30.md` | `/HANDOFF.md` | 2026-04-30 세션 핸드오프 — 4-노드 아키텍처 도입, 04 마일스톤 진입 컨텍스트 |
| `agent_plan_pre-subagent.md` | `/agent_plan.md` | 3-AI 역할 분담 정책 (Claude 기획·Copilot 코딩·Codex 테스트) |
| `AGENTS_codex-guide.md` | `/AGENTS.md` | Codex 전용 프로젝트 가이드 |
| `copilot-instructions_pre-subagent.md` | `/.github/copilot-instructions.md` | GitHub Copilot 전용 가이드 |
| `CLAUDE_pre-subagent.md` | `/CLAUDE.md` (복사본 — 원본 그대로 유지) | Phase 2 에서 대대적 재작성 예정. 옛 버전 스냅샷 |

## 새 워크플로우 자산 위치

활성 워크플로우 정의는 다음 위치 참조:

- `CLAUDE.md` (루트) — 프로젝트 운영 룰
- `.claude/agents/` — 서브에이전트 정의 (Phase 3 에서 추가)
- `.claude/skills/` — 도메인 지식 모듈 (Phase 3 에서 추가)
- `.claude/commands/` — 슬래시 커맨드 (Phase 2 에서 갱신)
- `docs/work_flow/specs/` — 작업 스펙
- `docs/work_flow/context/` — 진행 상태

## 복구 정책

이 파일들은 **읽기 전용 참조**. 다시 활성 영역으로 끌어올 일이 있으면, **새로운 이름으로 활성 위치에 복사**하고 본 폴더는 그대로 둘 것 (이력 보존).

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초기 보관 — 4개 파일 archive (워크플로우 재구성 직전 시점) |
| 2026-05-01 | `CLAUDE.md` 스냅샷 추가 (`CLAUDE_pre-subagent.md`) — Phase 2 재작성 직전 옛 버전 보존 |
