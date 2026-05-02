# AGENTS.md — smolVLA
<!-- For OpenAI Codex only. Claude: see CLAUDE.md. Copilot: see .github/copilot-instructions.md. -->

## Project

smolVLA: Physical AI robotics workflow on Orin (NVIDIA Jetson AGX). Custom layer lives in `orin/`. Upstream lerobot is a read-only submodule.

## Directory Map

| Path | Purpose | Editable |
|---|---|---|
| `orin/` | Custom runtime, wrappers, extensions | Yes |
| `docs/reference/lerobot/` | HuggingFace lerobot upstream submodule | **No** |
| `docs/reference/reComputer-Jetson-for-Beginners/` | Seeed Jetson reference submodule | **No** |
| `docs/` | Project docs and operational knowledge | Yes |
| `scripts/` | Deployment and utility scripts | Yes |

## Current Sprint

- Finalize arm workflow milestones: see `arm_2week_plan.md`
- Improve Orin-side integration reliability
- Keep docs aligned with deployment scripts

## Hard Rules

1. Never edit anything under `docs/reference/lerobot/`.
2. To change lerobot behavior: add wrappers or extensions under `orin/` only.
3. Never add bash command examples in `docs/storage/` unless explicitly requested.

## Coupled File Rules

**When editing `orin/pyproject.toml`**, also edit:

- `orin/scripts/setup_env.sh` — torch/torchvision/numpy versions are pinned here, not in pyproject.toml; update URLs/versions if they change.
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` — append: date, reason, before/after diff.

**When editing any file under `orin/lerobot/`**, also edit:

- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — append: date, file path, what changed, why, impact scope. `orin/lerobot/` is inference-only; if removing training/HIL/sim code, state why and confirm inference path is unaffected.

## Working Style

- Small, incremental changes. Validate before moving on.
- State assumptions explicitly before implementing.
- Do not use destructive operations unless instructed.

## Done Criteria

Each task must report:
- What changed
- Why it changed
- How it was validated (or why validation was not possible)
- Remaining risks

## Workflow

### Implementation tasks (`current_task.md`)

1. Read `#file:docs/work_flow/context/current_task.md` at the start of every implementation session (VS Code IDE environment — use `#file:` to attach).
2. **Before writing any code, attach and check the following references for relevant APIs and patterns:**
   - `#file:docs/reference/lerobot/` — HuggingFace lerobot upstream (canonical interface definitions)
   - `#file:docs/reference/seeed-lerobot/` — Seeed lerobot fork (SO-ARM-specific implementations)
3. Determine implementation scope from `## DOD` and `## 구현 대상`. Do not touch files listed under `## 건드리지 말 것`.
4. After implementation, record changes in the `## 업데이트` section of `current_task.md`.
5. Do **not** modify spec files directly — request updates via `current_task.md`.

### Test tasks (`current_test.md`)

1. Read `docs/work_flow/context/current_test.md` at the start of every test session.
2. Run test code validation and prod validation as specified in the test target.
3. Record results in the tables (`test 코드 검증` / `prod 코드 검증`).
4. If a test fails or reveals a code issue, add a note in `current_test.md` requesting a spec update.
5. Do **not** modify spec files directly — flag issues in `current_test.md`.

## Current Test Target

→ Read `docs/work_flow/context/current_test.md` before starting any test task.
