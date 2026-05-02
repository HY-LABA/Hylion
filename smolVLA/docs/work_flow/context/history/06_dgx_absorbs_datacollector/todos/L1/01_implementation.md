# TODO-L1 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

기존 `docs/storage/legacy/` 직하 8 파일을 `docs/storage/legacy/01_pre_subagent_workflow/` 하위로 `git mv` 이동 + `legacy/README.md` 신규 작성.

---

## §1 변경 파일

| 경로 (이전) | 경로 (이후) | 변경 종류 | 한 줄 요약 |
|---|---|---|---|
| `docs/storage/legacy/agent_plan_pre-subagent.md` | `docs/storage/legacy/01_pre_subagent_workflow/agent_plan_pre-subagent.md` | git mv (R) | 3-AI 역할 분담 정책 파일 이동 |
| `docs/storage/legacy/AGENTS_codex-guide.md` | `docs/storage/legacy/01_pre_subagent_workflow/AGENTS_codex-guide.md` | git mv (R) | Codex 전용 가이드 이동 |
| `docs/storage/legacy/CLAUDE_pre-subagent.md` | `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` | git mv (R) | 옛 CLAUDE.md 스냅샷 이동 |
| `docs/storage/legacy/copilot-instructions_pre-subagent.md` | `docs/storage/legacy/01_pre_subagent_workflow/copilot-instructions_pre-subagent.md` | git mv (R) | Copilot 가이드 이동 |
| `docs/storage/legacy/current_task_pre-subagent.md` | `docs/storage/legacy/01_pre_subagent_workflow/current_task_pre-subagent.md` | git mv (R) | 옛 단일 task 슬롯 이동 |
| `docs/storage/legacy/current_test_pre-subagent.md` | `docs/storage/legacy/01_pre_subagent_workflow/current_test_pre-subagent.md` | git mv (R) | 옛 단일 test 슬롯 이동 |
| `docs/storage/legacy/HANDOFF_2026-04-30.md` | `docs/storage/legacy/01_pre_subagent_workflow/HANDOFF_2026-04-30.md` | git mv (R) | 2026-04-30 세션 핸드오프 이동 |
| `docs/storage/legacy/README.md` | `docs/storage/legacy/01_pre_subagent_workflow/README.md` | git mv (R) | 기존 legacy README (단일 폴더 색인) 이동 |
| `docs/storage/legacy/README.md` | (신규) | A (신규) | 두 하위 폴더 (`01_pre_subagent_workflow/`, `02_datacollector_separate_node/`) 색인 |

합계: git mv 8건 + 신규 1건 = 총 9개 파일 작업.

---

## §2 grep 검증 결과

이동된 8개 파일의 **이전 경로 (`docs/storage/legacy/<파일명>`) 를 프로젝트 전체에서 grep** 한 결과:

### 발견된 참조 (1건)

| 파일 | 라인 | 내용 |
|---|---|---|
| `.claude/skills/lerobot-reference-usage/SKILL.md` | L111 | `` `docs/storage/legacy/CLAUDE_pre-subagent.md` 의 "## 핸드오프 프롬프트 출력 규칙" `` |

### 비발견 경로

나머지 7개 파일 (`agent_plan_pre-subagent.md`, `AGENTS_codex-guide.md`, `copilot-instructions_pre-subagent.md`, `current_task_pre-subagent.md`, `current_test_pre-subagent.md`, `HANDOFF_2026-04-30.md`, `README.md`) 의 이전 경로는 다른 파일에서 참조되지 않음.

### 판단

`.claude/skills/lerobot-reference-usage/SKILL.md:111` 의 참조는 **Category A 영역** (`.claude/skills/`) 이므로 task-executor 가 직접 수정 불가. M1 또는 M3 처리 시 함께 갱신하거나 reflection 시점에 orchestrator 가 사용자 승인 후 수정.

---

## §3 잔여 리스크

| 리스크 | 영향도 | 처리 방안 |
|---|---|---|
| `.claude/skills/lerobot-reference-usage/SKILL.md` L111 의 `CLAUDE_pre-subagent.md` 경로가 이전 위치 참조 | 낮음 (read-only 참조라 런타임 영향 없음) | orchestrator 가 사용자 승인 후 `.claude/skills/` 경로 갱신 (reflection 시점 또는 M3) |
| L2 와 동시 진행 시 `legacy/` 디렉터리 충돌 | 없음 | L1 은 `01_pre_subagent_workflow/` 내부만, L2 는 `02_datacollector_separate_node/` 내부만 처리 — 디렉터리 분리됨 |
| 기존 `01_pre_subagent_workflow/README.md` (이동된 파일) 와 신규 `legacy/README.md` 의 색인 중복 우려 | 없음 | 기존 파일은 단일 폴더 내부 설명, 신규는 두 폴더 상위 색인 — 역할 분리 명확 |

---

## §4 lerobot upstream 영향

본 TODO 는 `docs/storage/legacy/` 문서 파일 이동만 수행. `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh` 등 lerobot 영향 영역 변경 없음.

- Coupled File Rule 비해당
- Category B 영역 미변경

---

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 ✓
- CLAUDE.md Hard Constraints Category A: `.claude/agents/`, `.claude/skills/` 미변경 ✓
- Category C 비해당: `docs/storage/legacy/` 는 `docs/` 내부라 새 디렉터리 신설 자유 ✓
- git mv 사용: git 이 모두 `R` (rename) 으로 인식 ✓ (history 보존)
- lerobot-reference-usage SKILL: L 그룹은 lerobot 코드 구현 아님 → 레퍼런스 검색 불요 ✓
- lerobot-upstream-check SKILL: Coupled File Rule 비해당 ✓

---

## 변경 내용 요약

`docs/storage/legacy/` 직하에 혼재되어 있던 8개 파일을 `01_pre_subagent_workflow/` 하위 디렉터리로 git mv 이동하여 보관 단위를 명확히 구분했다. 기존 `README.md` 도 함께 이동시켜 하위 폴더 자체 설명으로 역할을 유지한다.

`legacy/README.md` 는 두 하위 폴더 (`01_pre_subagent_workflow/` + `02_datacollector_separate_node/`) 를 색인하는 상위 목차로 신규 작성했다. `02_` 폴더는 L2 가 별도 처리하므로 placeholder + L2 README 참조 안내만 포함했다.

---

## code-tester 입장에서 검증 권장 사항

- git status 확인: `git status --short docs/storage/legacy/` → 8건 모두 `R` 표시, `README.md` 는 `??` (untracked) 또는 `A` (신규)
- 파일 실존 확인: `ls docs/storage/legacy/01_pre_subagent_workflow/` → 8개 파일 존재
- 신규 README 실존: `cat docs/storage/legacy/README.md` → 두 폴더 색인 내용
- DOD 항목 1: `01_pre_subagent_workflow/` 디렉터리 + 8 파일 이동 ✓
- DOD 항목 2: `legacy/README.md` 신규 (두 하위 폴더 색인) ✓
- DOD 항목 3 (테스트): `git status` rename 인식 ✓
