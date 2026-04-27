# Copilot Instructions For smolVLA
<!-- For GitHub Copilot only. Claude: see CLAUDE.md. Codex: see AGENTS.md. -->

## Mission

Deliver safe, practical changes for smolVLA with focus on the Orin customization layer.

## Project Context

- Platform: Orin-centered execution and validation workflow
- Main development layer: `smolVLA/orin/`
- `smolVLA/docs/reference/` — 하위 전체 **read-only** (lerobot, reComputer-Jetson-for-Beginners, seeed-lerobot, nvidia_official, seeedwiki)
- `smolVLA/orin/`: custom runtime, wrappers, and extensions (edit here)
- `smolVLA/docs/`: project docs and operational knowledge
- `smolVLA/scripts/`: deployment and utility scripts

## Current Focus

- Active sprint: arm workflow milestones (`smolVLA/arm_2week_plan.md`), Orin integration reliability, doc alignment
- Blockers: hardware/runtime mismatch risk, drift between docs and scripts

## Hard Rules

- Never edit files under `smolVLA/docs/reference/lerobot/`.
- If lerobot behavior must change, implement wrappers/extensions under `smolVLA/orin/`.
- In `smolVLA/docs/storage/`, do not include bash command examples unless explicitly requested.

## Coupled File Rules

When editing `orin/pyproject.toml`, always update in the same change:

1. **`orin/scripts/setup_env.sh`** — reflect dependency changes; torch/torchvision/numpy are managed here, not in pyproject.toml; update URLs/versions if they change.
2. **`docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`** — append dated entry (before/after + reason).

When editing any file under `orin/lerobot/`, also update:

3. **`docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`** — append dated entry (file path, what changed, why, impact scope). The `orin/lerobot/` layer is inference-only; document why training/HIL/simulation code was removed and confirm inference path is unaffected.

## Working Style

- Prefer minimal, incremental edits with quick validation.
- Do not use destructive operations unless explicitly requested.
- When requirements are ambiguous, clarify assumptions before large changes.
- Inspect nearby README/docs in the target directory before editing code.

## Response Format

Always report:
- What changed
- Why it changed
- How it was validated
- Remaining risks or next steps

## Workflow

1. 매 작업 세션 시작 시 `../docs/work_flow/context/current_task.md` 를 읽는다.
2. **구현 시작 전 반드시 아래 두 레퍼런스에서 관련 코드·API를 확인한다:**
   - `docs/reference/lerobot/` — HuggingFace lerobot upstream (구현 패턴·인터페이스 기준)
   - `docs/reference/seeed-lerobot/` — Seeed lerobot fork (SO-ARM 특화 구현 참조)
3. `## DOD (완료 조건)` 을 기준으로 구현 범위를 결정한다.
4. `## 구현 대상` 에 명시된 파일만 수정한다. `## 건드리지 말 것` 항목은 절대 수정하지 않는다.
5. 구현 완료 후 `current_task.md` 의 `## 업데이트` 섹션에 기록한다:
   - 변경한 내용
   - 검증 방법 및 결과
   - test/prod 검증이 추가로 필요한 경우 명시
6. spec 파일(`docs/work_flow/specs/`)은 직접 수정하지 않는다 — `current_task.md` 에 반영 요청을 남긴다.

## Current Task

→ ../docs/work_flow/context/current_task.md 를 참조하세요.
  VSCode에서 해당 파일을 탭으로 열거나 Copilot Chat에서 #file 변수로 첨부하세요.
