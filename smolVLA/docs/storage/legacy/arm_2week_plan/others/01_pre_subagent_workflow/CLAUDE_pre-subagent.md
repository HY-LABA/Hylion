# CLAUDE.md
<!-- For Claude Code only. Copilot: see .github/copilot-instructions.md. Codex: see AGENTS.md. -->

## Project Snapshot

- Project: smolVLA for Physical AI robotics workflow
- Platform: Orin-centered execution and validation workflow
- Main development layer: `smolVLA/orin/`
- Core objective: implement and stabilize custom behavior without touching upstream submodule code

## Architecture At A Glance

- `smolVLA/docs/reference/` — 외부 참조 전체 **read-only** (수정 금지)
  - `lerobot/`: HuggingFace lerobot upstream submodule
  - `reComputer-Jetson-for-Beginners/`: Seeed Jetson beginner reference submodule
  - `seeed-lerobot/`: Seeed lerobot fork submodule
  - `nvidia_official/`: NVIDIA PyTorch on Jetson 공식 문서
  - `seeedwiki/`: Seeed SO-101 위키
- `smolVLA/orin/`: custom runtime, wrappers, and extensions
- `smolVLA/docs/`: project docs and operational knowledge
- `smolVLA/scripts/`: deployment and utility scripts

## 작업 흐름

- 스펙·컨텍스트 관리: `docs/work_flow/` — `/handoff-task`, `/handoff-test`, `/complete-task`, `/complete-test` 커맨드로 운영
- 에이전트 계획 전체: `agent_plan.md` 참조

## 핸드오프 프롬프트 출력 규칙

`/handoff-task` 또는 `/handoff-test` 실행이 완료되면, 반드시 아래 해당 프롬프트를 개발자에게 출력한다. 개발자가 Codex·Copilot에 직접 붙여넣을 수 있도록 코드 블록으로 제공한다.

### `/handoff-task` 완료 시 — 구현 작업 (레퍼런스 참조 필요)

#### Codex용 프롬프트 (VS Code Codex Chat)

```
#file:docs/work_flow/context/current_task.md 의 TODO를 구현하세요.

구현 시작 전 반드시 아래 두 레퍼런스에서 관련 코드·API를 확인하세요:
#file:docs/reference/lerobot/          (HuggingFace lerobot upstream)
#file:docs/reference/seeed-lerobot/    (Seeed lerobot fork)
```

#### Copilot용 프롬프트 (VS Code Copilot Chat)

```
#file:docs/work_flow/context/current_task.md 의 TODO를 구현합니다.

구현 시작 전 반드시 아래 두 레퍼런스에서 관련 코드·API를 확인하세요:
#file:docs/reference/lerobot/          (HuggingFace lerobot upstream)
#file:docs/reference/seeed-lerobot/    (Seeed lerobot fork)

레퍼런스 활용 규칙:
- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성합니다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행합니다.

구현 완료 후 반드시 current_task.md 의 `## 업데이트` 섹션을 채웁니다:
- `### 변경한 내용` — 변경한 파일과 내용 요약
- `### 검증 방법 및 결과` — 실행한 검증 명령과 결과
- `### 실 실행 검증 필요 여부` — prod 환경 추가 검증이 필요하면 명시
```

### `/handoff-test` 완료 시 — 테스트 실행 (레퍼런스 참조 불필요)

#### Codex용 프롬프트 (VS Code Codex Chat)

```
#file:docs/work_flow/context/current_test.md 의 테스트 단계를 실행하고 결과 컬럼을 채우세요.
스펙 파일은 직접 수정하지 않습니다.
```

#### Copilot용 프롬프트 (VS Code Copilot Chat)

```
#file:docs/work_flow/context/current_test.md 의 테스트 단계를 실행하고 결과 컬럼을 채웁니다.
스펙 파일은 직접 수정하지 않습니다.
```

## current_task.md 작성 규칙

`/handoff-task` 실행 시 `current_task.md` 를 작성할 때, `## 참고 레퍼런스` 섹션 아래에 반드시 아래 레퍼런스 활용 규칙을 포함한다:

```
## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.
```

## Backlog 기록 규칙

Backlog는 **스펙 파일에 두지 않는다**. 모든 Backlog는 `docs/work_flow/specs/BACKLOG.md` 에 스펙별 섹션으로 중앙 관리한다.

`/complete-test` 또는 `/complete-task` 실행 중 아래 항목이 발견되면 `BACKLOG.md` 의 해당 스펙 섹션에 추가한다:

- 현재 워크플로우를 블로킹하지 않지만 나중에 문제가 될 수 있는 잔여 리스크
- 테스트 중 발견된 설계 개선 필요 사항
- 당장 처리하지 않고 미루기로 결정한 기술 부채

Backlog 테이블 형식 (상태 컬럼 포함):

```markdown
| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | [항목 설명] | [TODO 번호] | 높음/중간/낮음 | 미완/완료 |
```

## 스펙 문서 생성 시 필수 참조

`docs/work_flow/specs/*.md` 스펙 파일을 새로 작성하기 전에 반드시 아래 파일들을 읽고 환경 맥락을 확인한다. 이 파일들을 읽지 않으면 실행 주체(devPC vs Orin), 접근 방법(SSH), 코드 경로, 하드웨어 구성 등 핵심 전제가 누락된다.

- `docs/storage/01_smolvla_arm_env_requirements.md` — 요구사항 개요 및 문서 네비게이션
- `docs/storage/02_hardware.md` — 컴퓨팅 장치 및 SO-ARM 하드웨어 현황
- `docs/storage/03_software.md` — Orin / devPC / DGX 소프트웨어 실측값
- `docs/storage/04_devnetwork.md` — devPC ↔ Orin SSH 연결 구조 및 네트워크 설정
- `docs/storage/05_orin_venv_setting.md` — Orin venv 구성 방식 및 PyTorch 설치 현황

**핵심 맥락 (반드시 인지):**
- 실행/검증은 항상 **Orin** (`laba@ubuntu`) 에서 수행. devPC는 코드 정리/문서화/배포 관리 전용.
- devPC → Orin 접근: `ssh orin` (IP 기반, `~/.ssh/config` 등록)
- Orin 코드 경로: `/home/laba/smolvla/orin/` (rsync 배포 기준 — dgx 와 형제 구조)
- Orin venv: `/home/laba/smolvla/orin/.hylion_arm` (`~/smolvla/orin/.hylion_arm`) — DGX venv `~/smolvla/dgx/.arm_finetune` 과 격리

## Current Working Agreements

- Keep changes small and verifiable to reduce integration risk.
- For non-trivial updates, include a short reason (`why`) in commit or doc context.
- If assumptions are needed, state them clearly before implementation.

## Current Focus (Keep Updated)

- Active sprint goals:
	- Finalize arm-related workflow milestones from `smolVLA/arm_2week_plan.md`
	- Improve reliability of Orin-side integration paths
	- Keep documentation aligned with the current deployment flow
- Near-term blockers:
	- Hardware/runtime mismatch risk between environments
	- Drift between docs and executable scripts

## Hard Constraints

- `smolVLA/docs/reference/` 하위 전체는 수정 금지 (외부 참조 및 upstream submodule).
- Any lerobot behavior change must be done by wrapping/extending in `smolVLA/orin/`.
- Under `docs/storage/`, do not include bash command examples unless explicitly requested.

## Coupled File Rules

`orin/pyproject.toml`을 수정할 때 반드시 아래 두 파일도 함께 확인하고 업데이트한다.

1. **`orin/scripts/setup_env.sh`**
   - pyproject.toml의 의존성 변경이 Orin 설치 스크립트에도 반영되어야 한다.
   - 특히 torch/torchvision/numpy는 pyproject.toml이 아닌 setup_env.sh에서 직접 관리하므로, 버전 결정이 바뀌면 스크립트 URL·버전도 수정한다.

2. **`docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`**
   - pyproject.toml 변경 이력을 날짜·이유·before/after 형식으로 누적 기록한다.
   - upstream(`lerobot/pyproject.toml`) 대비 차이도 유지 업데이트한다.

`orin/lerobot/` 하위 코드를 수정할 때 반드시 아래 파일도 함께 업데이트한다.

3. **`docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`**
   - upstream(`lerobot/src/lerobot/`) 대비 `orin/lerobot/` 코드 변경 이력을 날짜·파일·이유·영향 범위 형식으로 누적 기록한다.
   - `orin/lerobot/`은 추론 전용 레이어이므로, 학습/HIL/시뮬레이션 전용 코드 제거 시 반드시 이유와 영향 범위를 명시한다.

## Working Style

- Prefer minimal, incremental edits with quick validation.
- Do not use destructive operations unless explicitly requested.
- When requirements are ambiguous, clarify assumptions before large changes.
- Inspect nearby README/docs in the target directory before editing code.

## Definition Of Done

- Code changes include at least one practical verification step.
- Documentation changes include intent, impact, and next action when relevant.
- Report remaining risks explicitly when full validation is not possible.
- Always report: what changed, why it changed, how it was validated, remaining risks.
