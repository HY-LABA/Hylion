# CLAUDE.md

## Project Snapshot

- Project: smolVLA for Physical AI robotics workflow
- Platform: Orin (NVIDIA Jetson AGX) 중심 실행·검증 + DGX (학습 + 데이터 수집, 시연장 이동 운영)
- Main development layer: `smolVLA/orin/`
- Core objective: implement and stabilize custom behavior without touching upstream submodule code
- 자동화 정책: spec 작성 → 모든 todo 자동 처리 → 사용자 실물 검증으로 사이클 마무리

## Architecture At A Glance

- `smolVLA/docs/reference/` — 외부 참조 전체 **read-only** (수정 금지)
  - `lerobot/`: HuggingFace lerobot upstream submodule
  - `reComputer-Jetson-for-Beginners/`: Seeed Jetson beginner reference submodule
  - `seeed-lerobot/`: Seeed lerobot fork submodule
  - `nvidia_official/`: NVIDIA PyTorch on Jetson 공식 문서
  - `seeedwiki/`: Seeed SO-101 위키
- `smolVLA/orin/`: custom runtime, wrappers, and extensions (Orin)
- `smolVLA/dgx/`: 학습 + 데이터 수집 (DGX, 시연장 직접 이동 운영)
- `smolVLA/docs/`: project docs and operational knowledge
- `smolVLA/docs/storage/legacy/`: 이전 워크플로우 자산 보관 (참조용)
- `smolVLA/docs/storage/workflow_reflections/`: spec 사이클별 reflection 보고서
- `smolVLA/scripts/`: deployment and utility scripts

## 워크플로우 — 3 Phase 모델

본 프로젝트는 **milestone → spec → todo** 계층으로 작업을 구조화하며, 한 spec 의 라이프사이클은 3 Phase 로 진행된다.

### Phase 1 — Discovery (사용자 + 메인 Claude)

사용자와 메인 Claude 가 **대화형**으로 spec 을 작성.

- **시작**: 새 milestone 결정 후, 또는 이전 spec 의 `/wrap-spec` 직후
- **활동**: 큰 그림 합의 → todo 분해 → DOD 작성
- **산출물**: `docs/work_flow/specs/NN_<name>.md`
- **종료**: 사용자 `/start-spec` 호출
- **금지**: 자동화 워커 호출, 가설적 구현·테스트

### Phase 2 — Automation (오케스트레이터 + 워커)

spec 의 모든 todo 를 **자율 처리**. 사용자는 `/observe` 로 read-only 관찰만.

- **시작**: 사용자 `/start-spec` 호출
- **흐름**:
  1. planner 가 spec 분석 → DAG·병렬 그룹·가정·검증 큐 → `context/plan.md`
  2. orchestrator 가 plan 따라 dispatch loop:
     - task-executor → `context/todos/<XX>/01_implementation.md`
     - code-tester → `context/todos/<XX>/02_code-test.md`
     - prod-test-runner → `context/todos/<XX>/03_prod-test.md`
  3. 매 이벤트 → `context/log.md` 한 줄
  4. prod-test 결과 → `context/verification_queue.md` 누적
  5. 하네스 이상 신호 → `docs/work_flow/specs/ANOMALIES.md` 누적
  6. **todo 완료 직후 → spec 본문 즉시 갱신** (orchestrator 책임):
     - code-tester READY/MINOR 통과 (study/task) → `[ ]` → `[x]` + "**자동화 완료 (YYYY-MM-DD)**: 핵심 산출물 요약" 메모
     - prod-test NEEDS_USER_VERIFICATION (test/both) → `[ ]` 유지 + "**자동화 완료, Phase 3 대기 (YYYY-MM-DD)**" 메모
     - Phase 3 사용자 검증 통과 후 → `[x]` 최종 전환 + "**최종 완료 (YYYY-MM-DD): 검증 결과 요약**" 메모
- **종료 조건**:
  - **End-A 성공**: 모든 todo verdict ∈ {AUTOMATED_PASS, NEEDS_USER_VERIFICATION} → 메인이 사용자에게 `/verify-result` 추천
  - **End-B 실패**: 일부 todo 가 code-tester 2 cycle 안에 MAJOR 해결 X 또는 prod-test FAIL → "수정 필요" 사용자 보고 (자연어 대화로 다음 단계 결정)

#### code-tester 사이클 정책

- max 2 cycle. 그래도 MAJOR 면 todo 실패 마킹 (다른 todo 는 계속 진행, BACKLOG 추가 X).

#### awaits_user 항목

- planner 가 "사용자 결정 필요" 분류한 todo 는 답 받기 전까지 dispatch X.
- 의존 없는 다른 todo 는 계속 진행 (병렬화 핵심).

### Phase 3 — Verification (사용자)

메인 Claude 의 "검증 가나?" 신호 후 사용자가 **실물 환경 검증**.

- **시작**: 메인 신호 + 사용자 OK
- **활동**: `verification_queue.md` 항목별 사용자가 Orin·SO-ARM 에 배포·실행·관찰
- **결과**: 사용자 `/verify-result <자연어 결과>`
- **분기**:
  - 통과 → `/wrap-spec` → spec history 보관 + reflection + 다음 spec Phase 1
  - 실패 → orchestrator 가 todo 추가 (1a, 1b…) → planner 재호출 → Phase 2 재진입

#### verification_queue 환경 레벨 분류 (06 reflection 도출)

각 항목에 환경 레벨 명시 — planner 가 Phase 3 검증 큐 후보 식별 시 적용:

| 환경 레벨 | 의미 | prod-test-runner 자율 | Phase 3 검증 |
|---|---|---|---|
| `AUTO_LOCAL` | devPC 로컬 자동 (pytest·ruff·bash -n) | ✅ 자율 — 즉시 verdict | 사용자 검증 불요 |
| `SSH_AUTO` | SSH 자율 (orin·dgx read-only) | ✅ 자율 — verdict 후 사용자 통과 확인 | SSH 가용 시 자율 |
| `PHYS_REQUIRED` | 사용자 실물 환경 필수 (시연장·하드웨어) | ⚠️ 정적만 + 사용자 위임 | 시연장 환경 의존 |

`PHYS_REQUIRED` 항목이 환경 차단으로 미검증 시 `/wrap-spec` 진입 시 BACKLOG 이관 (아래 정책 참조).

#### /wrap-spec 미처리 verification_queue 처리 정책 (06 reflection 도출)

`/wrap-spec` 호출 시 verification_queue 에 *미처리* (NEEDS_USER_VERIFICATION 상태로 사용자 결정 미입력) 항목이 있으면, 메인이 **항목별 명시적 처리 결정 prompt** 제시:

| 결정 | 처리 |
|---|---|
| **무시 (BACKLOG 이관)** | verification_queue 마킹 + BACKLOG.md 활성 spec 섹션 항목 추가 + ANOMALIES `USER_OVERRIDE` 누적 |
| **연기 (다음 사이클 재시도)** | 무시와 동일하나 BACKLOG 우선순위 "중간" + 트리거 명시 (예: "DGX 시연장 이동 시") |
| **실패 처리 (자동 재시도)** | `/verify-result <항목> 실패` 입력으로 분기 — todo 추가 + planner 재호출 |

→ 메인이 prompt 후 사용자 답 받기 전 `/wrap-spec` 진행 X. 04 BACKLOG #7 + 05 ANOMALIES #4 + 06 USER_OVERRIDE 패턴의 *명시적 정책화*.

### Phase 간 책임 매트릭스

| 단계 | 책임자 | 주요 산출물 |
|---|---|---|
| Phase 1 | 사용자 + 메인 | `specs/NN_<name>.md` |
| Phase 2 | planner + 워커들 (메인 dispatch) | `context/{plan, log, verification_queue}.md`, `context/todos/<XX>/*.md`, `specs/ANOMALIES.md` |
| Phase 3 | 사용자 + 메인 (피드백 분석) | 실물 검증 결과 |

## 에이전트 팀

| # | 에이전트 | 정의 위치 | 핵심 역할 |
|---|---|---|---|
| 1 | **orchestrator** | 메인 Claude (별도 .md 없음) | 사용자 대화·dispatch·종료 판단 |
| 2 | **planner** | `.claude/agents/planner.md` | spec → DAG·병렬 그룹·가정·검증 큐 (전권) |
| 3 | **task-executor** | `.claude/agents/task-executor.md` | 코드 구현 |
| 4 | **code-tester** | `.claude/agents/code-tester.md` | 단위 검증 + verdict (READY/MINOR/MAJOR) |
| 5 | **prod-test-runner** | `.claude/agents/prod-test-runner.md` | 배포·비대화형 검증 (verdict: AUTOMATED_PASS/NEEDS_USER_VERIFICATION/FAIL) |
| 6 | **reflection** | `.claude/agents/reflection.md` | 사이클 회고·갱신 제안 (`/wrap-spec` 시 호출) |

### 스킬 (`.claude/skills/`)

- `claude-md-constraints` — 본 문서의 Hard Constraints 체크리스트 (planner·code-tester 활용)
- `lerobot-upstream-check` — 옵션 B 원칙·coupled file 규칙 (task-executor·code-tester·prod-test-runner)
- `lerobot-reference-usage` — 레퍼런스 활용 규칙 (task-executor)
- `orin-deploy-procedure` — rsync·deploy 절차·검증 명령 시퀀스 (prod-test-runner)
- `harness-engineering-principles` — OpenAI harness engineering 평가 프레임워크 (reflection 활용, 사이클 분석 시 10 원칙 매핑)

## 슬래시 커맨드

| 커맨드 | 단계 | 역할 |
|---|---|---|
| `/start-spec` | Phase 1 → 2 | orchestrator 자동화 시작 (활성 spec 자동 탐지, planner 호출) |
| `/observe` | Phase 2 도중 | 별도 세션 read-only 관찰 모드 진입 (자기를 오케스트레이터 아님으로 인식) |
| `/verify-result <결과>` | Phase 3 | 실물 검증 결과 자연어 입력 → 통과/추가 todo 분기 |
| `/wrap-spec` | Phase 3 종료 | spec history 보관 + reflection + 다음 spec Phase 1 진입 |
| `/update-docs` | 보조 | navigator 문서 자동 업데이트 (옛 그대로) |

## 가시화 레이어

자동화 진행 중 모든 상태가 `docs/work_flow/context/` 에 누적. 사용자는 `/observe` 로 별도 세션에서 read-only 학습 가능. 상세는 `docs/work_flow/context/README.md`.

사이클 간 누적 자료 (sibling 관계, `docs/work_flow/specs/`):

- `BACKLOG.md` — **구현 차원** 잔여 (코드·spec·테스트 — 다음 spec 작성 시 메인이 참조)
- `ANOMALIES.md` — **시스템 차원** 잔여 (하네스 차단·이상 패턴 — reflection 이 사이클 종료 시 분석)

## Hard Constraints

자동화 안전망. 4 카테고리.

### Category A — 절대 금지 영역 (PreToolUse hook 차단)

자동화 중 어떤 워커도 수정 X.

- `docs/reference/` 하위 전체 (외부 upstream 보존)
- `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json`
- `~/.claude/.credentials.json`

→ reflection 갱신 시에도 워커 X. **메인 Claude (오케스트레이터) 가 사용자 승인 후 직접 수정**.

### Category B — 자동 재시도 X 영역

code-tester `MAJOR_REVISIONS` 시 일반적으론 task-executor 재호출. 단 다음 영역 변경에 대해서는 **자동 재시도 X, 사용자 보고 게이트**.

- `orin/lerobot/`, `dgx/lerobot/` (upstream 옵션 B)
- `pyproject.toml` 류 (의존성)
- `orin/scripts/setup_env.sh` (Jetson PyTorch 직접 설치)
- `scripts/deploy_*.sh`
- `.gitignore` **패턴 추가·변경** (기존 파일 수정) — 해당. 신규 `.gitignore` 파일 **신규 생성** 은 Category C (새 디렉터리 동의) 와 함께 처리되며, 기존 디렉터리에 신규 추가 시 Category B 에 준함.
- `.git/info/exclude` (패턴 변경) — 해당

### Category C — 사용자 동의 필수 작업

orchestrator·planner 가 다음을 plan 에 넣으려면 **사용자 답 받기** (`awaits_user` 분류).

- 새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외)
- 외부 의존성 추가 (`pyproject.toml` 의존성 추가)
- 시스템 환경 변경 (가상환경 재생성·업그레이드)
- 외부 시스템 호출 (Category B 영역 변경된 deploy 등)
- 새 git 브랜치·태그·remote
- BACKLOG.md "높음" 우선순위 항목 자동 처리

### Category D — 절대 금지 명령 (`settings.json` deny)

- `Bash(rm -rf:*)`, `Bash(sudo:*)`
- `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`
- `Bash(chmod 777:*)`
- `Bash(curl -fsSL :* | bash)`

### prod-test-runner 자율성

| 작업 | 자율 / 동의 |
|---|---|
| ssh orin/dgx read-only 검증 (cat·ls·df·ps·nvidia-smi) | ✅ 자율 |
| ssh 로 pytest·ruff·mypy | ✅ 자율 |
| `deploy_*.sh` (변경 파일이 Category B 외) | ✅ 자율 |
| Category B 영역 변경된 deploy | ⚠️ 사용자 동의 |
| 가상환경 재생성·패키지 업그레이드 | ⚠️ 사용자 동의 |
| 큰 다운로드 (>100MB)·긴 실행 (>5분) | ⚠️ 사용자 동의 |

### Reflection 갱신 정책

- **모두 사용자 승인 필요**: skill·hook·CLAUDE.md·에이전트 정의 변경
- **자동 누적**: 메모리·BACKLOG·ANOMALIES (워커 또는 hook 가 직접)

### 옛 룰 유지

- `docs/storage/` 하위에는 사용자 명시 요청 없으면 bash 명령 예시 추가 X

## Coupled File Rules

`orin/pyproject.toml` 수정 시 함께 갱신:

1. **`orin/scripts/setup_env.sh`** — 의존성 변경이 Orin 설치 스크립트에도 반영. torch/torchvision/numpy 는 `pyproject.toml` 이 아닌 `setup_env.sh` 에서 직접 관리.
2. **`docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`** — pyproject.toml 변경 이력 (날짜·이유·before/after).

`orin/lerobot/` 하위 코드 수정 시 함께 갱신:

3. **`docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`** — upstream 대비 `orin/lerobot/` 코드 변경 이력. inference-only 트리밍 시 이유·영향 범위 명시.

skill·hook·CLAUDE.md 갱신 시 (reflection 결과):

4. 해당 reflection 보고서 (`docs/storage/workflow_reflections/<날짜>_<spec명>.md`) 의 **사용자 승인 결과** 섹션 채움.
5. git commit message 에 변경 이유 명시.

## Current Working Agreements

- Keep changes small and verifiable to reduce integration risk.
- For non-trivial updates, include a short reason (`why`) in commit or doc context.
- If assumptions are needed, state them clearly before implementation.
- Inspect nearby README/docs in the target directory before editing code.

## Definition Of Done

- **코드 변경**: spec 의 DOD 충족 + code-tester verdict ∈ {READY_TO_SHIP, MINOR_REVISIONS}.
- **검증**: prod-test-runner verdict ∈ {AUTOMATED_PASS, NEEDS_USER_VERIFICATION}.
- **spec 종료**: Phase 3 사용자 검증 통과 + reflection 갱신 제안 처리 + `/wrap-spec` 완료.
- **항상 보고**: 무엇이 변했는지·왜 변했는지·어떻게 검증했는지·잔여 리스크.
