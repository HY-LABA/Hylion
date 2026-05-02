# TODO-L1 — Code Test

> 작성: 2026-05-02 17:35 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 1건.

---

## 단위 테스트 결과

```
해당 없음 — 본 TODO 는 git mv (파일 이동) + 문서 신규 작성 only.
코드 변경 없음. pytest 실행 대상 없음.
```

파일 실존 확인 (직접 ls):

```
docs/storage/legacy/01_pre_subagent_workflow/
  agent_plan_pre-subagent.md       (R — git rename 인식)
  AGENTS_codex-guide.md            (R)
  CLAUDE_pre-subagent.md           (R)
  copilot-instructions_pre-subagent.md (R)
  current_task_pre-subagent.md     (R)
  current_test_pre-subagent.md     (R)
  HANDOFF_2026-04-30.md            (R)
  README.md                        (R)

docs/storage/legacy/README.md      (?? — unstaged, 파일 실존)
```

8개 파일 모두 `01_pre_subagent_workflow/` 하위 확인.

---

## Lint·Type 결과

```
해당 없음 — .md 파일 이동 및 신규 작성. Python 소스 변경 없음.
ruff / mypy 실행 대상 없음.
```

---

## DOD 정합성

spec `06_dgx_absorbs_datacollector.md` § TODO-L1 DOD:

> `docs/storage/legacy/01_pre_subagent_workflow/` 신규 디렉터리 생성 + 기존 8 파일 git mv 이동. `legacy/README.md` 신규 작성 (두 하위 폴더 색인).

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `01_pre_subagent_workflow/` 신규 디렉터리 생성 | ✅ | ls 확인 |
| 2. 8 파일 git mv 이동 | ✅ | git status `R` 8건 확인. `AGENTS_codex-guide.md`, `CLAUDE_pre-subagent.md`, `HANDOFF_2026-04-30.md`, `README.md`, `agent_plan_pre-subagent.md`, `copilot-instructions_pre-subagent.md`, `current_task_pre-subagent.md`, `current_test_pre-subagent.md` |
| 3. `legacy/README.md` 신규 작성 | ✅ | 파일 실존 (1998 bytes). 두 하위 폴더 (`01_pre_subagent_workflow/`, `02_datacollector_separate_node/`) 색인 포함. `02_` 는 L2 참조 안내 포함 |
| 4. git rename 인식 (`R`) | ✅ | git status `--porcelain` 8건 모두 `R` prefix 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/legacy/README.md` (git 상태) | 현재 `??` (untracked) 상태. git add 로 staging 하면 커밋에 포함됨. 파일 자체는 실존하고 내용도 정합하나, commit 전 `git add docs/storage/legacy/README.md` 가 필요함. 비-Critical (파일 내용·DOD 충족 문제 없음. 커밋 시점 문제) |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/`, `.claude/skills/`, `.claude/settings.json` 미변경 확인 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 변경 없음 — Coupled File Rule 비해당 |
| Category C | ✅ | `docs/storage/legacy/` 하위 신규 디렉터리 = `docs/` 내부 → Category C 비해당 (CLAUDE.md "orin·dgx·docs 외" 만 해당) |
| 옛 룰 | ✅ | `docs/storage/` 하위 신규 작성은 bash 명령 예시 없음 |

### `.claude/skills/lerobot-reference-usage/SKILL.md` L111 참조 처리

task-executor 가 발견한 하드코딩 경로 (`docs/storage/legacy/CLAUDE_pre-subagent.md` → 이동 후 `01_pre_subagent_workflow/CLAUDE_pre-subagent.md`) 를 `.claude/skills/lerobot-reference-usage/SKILL.md:111` 이 구 경로로 참조.

- 영향: 런타임 영향 없음 (read-only 참조)
- 처리: task-executor 보고서 §2·§3 에 Category A 사유로 직접 수정 불가 + M3 또는 reflection 시점 orchestrator 가 사용자 승인 후 갱신 명시 — 후속 처리 인계 적절히 기재됨
- verdict 영향: Recommended 아님 (이미 보고서에서 인계 명시. 추가 조치 불요)

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

git mv 8건 R 인식 확인, 신규 README 내용 정합 (두 폴더 색인·사유·일자·복구 정책 포함), Category A/B 미침범, DOD 4항 전부 충족.

Recommended 1건: `legacy/README.md` untracked 상태 — prod-test-runner 또는 커밋 직전 `git add` 필요. 내용·DOD 는 이미 충족.
