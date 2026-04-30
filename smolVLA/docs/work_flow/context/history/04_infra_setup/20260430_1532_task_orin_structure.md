# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-30 15:23 | 스펙: `docs/work_flow/specs/04_infra_setup.md` | TODO: O1

## 작업 목표

orin/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획.

현재 orin/ 의 디렉터리·스크립트·모듈을 마일스톤별 책임 관점에서 정리하고, 합의된 새 구조 (스펙 §"합의된 새 orin/ 구조") 기준으로 마이그레이션 계획 (제거 / 이관 / 신규 / 유지) 명시. 본 작업의 산출물 문서가 후속 TODO-O2 (마이그레이션 실행) 의 입력이 된다.

핵심 결정 사항 — 본 study 진행 중 사용자와 함께 확정:
1. `orin/lerobot/scripts/` 트리밍 대상 8개의 4-노드 분리 후 관점에서 재확정 (record 가 DataCollector 로 가는 경우 `lerobot_record.py` 도 제거 후보)
2. `orin/calibration/diagnose_motor_encoder.py` 의 새 위치 (`orin/tests/` 직접 vs `tests/scenarios/` 같은 하위)
3. `orin/scripts/run_teleoperate.sh` 의 최종 위치 (memory `project_run_teleoperate_relocation.md` 의 (a)/(b)/(c) 후보 중)

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

`docs/storage/07_orin_structure.md` 신규 작성 완료, 다음 5개 절 모두 채워짐:

1. **§1 디렉터리 트리** — 현재 orin/ 트리 (depth 3) + 합의된 새 orin/ 트리 비교
2. **§2 핵심 컴포넌트 책임 표** — `orin/lerobot/`, `orin/scripts/`, `orin/examples/`, `orin/.hylion_arm/`, `orin/tests/` (신규), `orin/config/` (신규), `orin/checkpoints/` (신규) 각각의 역할
3. **§3 마일스톤별 책임 매트릭스** — 마일스톤(00·01·02·03·04·05·06·07·08) × 컴포넌트의 사용/수정 시점
4. **§4 외부 의존성** — devPC sync hub (`scripts/deploy_orin.sh`, `scripts/sync_ckpt_dgx_to_orin.sh`), HuggingFace Hub, DataCollector·DGX 와의 인터페이스
5. **§5 마이그레이션 계획** — TODO-O2 의 입력. 5개 변경 카테고리 (제거 / 이관 / 신규 / 유지 / 트리밍) 별 표

## 구현 대상

- `docs/storage/07_orin_structure.md` — 신규 작성

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- `orin/` 하위 코드·스크립트 — 본 TODO 는 study (문서 작성) 만. 실제 마이그레이션은 TODO-O2 의 책임
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — TODO-O2 시점에 트리밍 이력 추가 (CLAUDE.md 의 coupled file 규칙). 본 TODO 에서는 참조만

## 작업 시작 전 확인

1. **현재 orin/ 트리 dump** — `ls -R orin/` (depth 3 권장) 또는 Glob 으로 확인
2. **`orin/lerobot/scripts/` 의 18개 파일** — 직전 분석에서 8개 제거 후보 / 10개 유지 분류했는데, **4-노드 분리 후 관점에서 record 도 DataCollector 로 가는 경우** 변경 사항 있는지 재확인
3. **memory `project_run_teleoperate_relocation.md` 읽기** — `run_teleoperate.sh` 최종 위치 결정의 후보 (a)/(b)/(c) 검토
4. **03 마일스톤 산출물 확인** — `orin/examples/tutorial/smolvla/` 의 6개 .py 가 04 이후 어느 책임을 갖는지

## 사용자 결정이 필요한 항목 (본 TODO 진행 중)

| 결정 | 후보 |
|---|---|
| `orin/lerobot/scripts/` 트리밍 대상 | 8개 제거 후보 + record 추가 후보 (DataCollector 로 가는 경우 9개) |
| `run_teleoperate.sh` 위치 | DataCollector(권장) / DGX / Orin 유지 |
| `diagnose_motor_encoder.py` 위치 | `orin/tests/` 직접 vs `orin/tests/scenarios/` |
| `orin/config/` 의 lerobot 캘리브레이션 | `~/.cache/huggingface/lerobot/calibration/` 표준 그대로 사용 (확정됨) |

## 참고 레퍼런스

### 04 스펙 (작성 중)

- `docs/work_flow/specs/04_infra_setup.md` — 본 스펙. 특히 §"합의된 새 orin/ 구조" 의 디렉터리 트리 (§5 마이그레이션 계획의 기준)

### 03 마일스톤 산출물

- `docs/work_flow/specs/history/03_smolvla_test_on_orin.md` — 03 사이클 전체. orin/examples/tutorial/smolvla/ 의 6개 .py 가 어떤 책임을 가졌는지 확인
- `orin/examples/tutorial/smolvla/{smoke_test, inference_baseline, measure_latency, load_checkpoint_test, hil_inference, using_smolvla_example}.py`

### 환경·인프라

- `orin/pyproject.toml` — 의존성 정의 (PyTorch 제외)
- `orin/scripts/setup_env.sh` — Jetson PyTorch wheel 설치 패턴 (PyTorch 가 setup_env.sh 에 머무르는 이유 4가지 코드 주석 참조)
- `orin/README.md` — 현재 orin/ 운영 가이드
- `docs/storage/05_orin_venv_setting.md` — Orin venv 구성
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — orin/lerobot/ 트리밍 이력 (TODO-O2 갱신 의무, 본 TODO 는 참조만)

### lerobot upstream 비교 (트리밍 결정 근거)

- `docs/reference/lerobot/src/lerobot/scripts/` — upstream 18 개 entry point 와 `orin/lerobot/scripts/` 비교
- `docs/reference/lerobot/CLAUDE.md` — upstream 운영 원칙 (현재 "AGENTS.md" 한 줄)

### 메모리

- `project_run_teleoperate_relocation.md` — `run_teleoperate.sh` 위치 결정 후보 정리

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 업데이트

*작업 완료 후 아래 항목을 채운다.*

### 변경한 내용

작업 시작 전 사전 점검 결과 — 중요한 사실 발견:

**현재 orin/lerobot/ 의 실태**:
- `orin/lerobot/scripts/` 18 개 파일 = upstream 18 개 그대로 복사된 상태 — 한 번도 트리밍 안 됨
- `policies/__init__.py`, `processor/__init__.py`, `configs/__init__.py` 등에서 **import 만 차단** 한 상태 (03_orin_lerobot_diff.md 에 기록된 기존 패치)
- 즉 orin/lerobot/ 은 **물리적으로는 upstream 보존, 논리적으로만 비활성화** 된 상태였음

이 발견은 사용자가 직전 대화에서 강조하신 "upstream 의 구조와 내용 최대한 변형 안 함" 원칙과 정확히 부합. 따라서 04 의 TODO-O2 트리밍 방향을 **옵션 B (논리적 비활성화)** 로 확정 (사용자 합의).

**사용자 결정 합의 내역 (본 study 진행 중)**:
1. 트리밍 방식 — **옵션 B 채택** (orin/lerobot/ 파일 제거 X, pyproject.toml entrypoint 만 정리)
2. TODO-O2 본문 갱신 — `lerobot-eval`, `lerobot-train` 2개 entrypoint 제거 + 9개 유지
3. §5 마이그레이션 5개 카테고리 (유지 / 이관 / 신규 / 삭제 / entrypoint 정리) — 합의

**산출물**: `docs/storage/07_orin_structure.md` 신규 작성, 5개 절 + §0 (본 문서 위치) + §6 (활용 포인트) 모두 채움:
- §1 디렉터리 트리 (현재 vs 새 구조 비교, 03 산출물·런타임 자산 모두 명시)
- §2 핵심 컴포넌트 책임 표 (8개 컴포넌트, 04 이후 변경 명시)
- §3 마일스톤별 책임 매트릭스 (00~08 마일스톤 × 20+ 컴포넌트, 사용/수정/무관 표기)
- §4 외부 의존성 (devPC sync hub, HF Hub, DataCollector·DGX 인터페이스, 시스템 의존성, 캘리브레이션 표준 위치)
- §5 마이그레이션 계획 — TODO-O2 의 입력 사양:
  - 5-1 유지: 6개 항목 (orin/lerobot/ 전체 보존, setup_env.sh, examples/, 9개 entrypoint, README, venv)
  - 5-2 이관: 2개 항목 (diagnose_motor_encoder.py → tests/, run_teleoperate.sh → DataCollector)
  - 5-3 신규: 3개 디렉터리 (tests/, config/, checkpoints/) + 각 README
  - 5-4 삭제: orin/calibration/ 디렉터리 (비게 됨)
  - 5-5 entrypoint 정리: lerobot-eval / lerobot-train 제거, 9개 유지
  - 부수 작업: .gitignore 갱신, 02_orin_pyproject_diff.md 갱신, 03_orin_lerobot_diff.md 갱신 (CLAUDE.md coupled file 규칙)

**04 스펙 갱신** — `docs/work_flow/specs/04_infra_setup.md` TODO-O2 본문을 옵션 B 기반으로 재작성:
- "8개 파일 제거" → "entrypoint 2개 제거 + 9개 유지"
- run_teleoperate.sh 의 임시 보관 시나리오 명시 (DataCollector 디렉터리 미존재 시점 대응)
- "orin/lerobot/ 하위 파일·디렉터리는 변경 금지" 제약 명시

### 검증 방법 및 결과

| # | 검증 항목 | 결과 |
|---|---|---|
| 1 | `docs/storage/07_orin_structure.md` 신규 작성 | PASS — 6 절 + 변경 이력 모두 채움 |
| 2 | DOD §1~§5 모두 채워짐 | PASS — 추가로 §0 (본 문서 위치) + §6 (04 활용 포인트) + 변경 이력 |
| 3 | TODO-O2 의 입력 사양으로 §5 마이그레이션 계획 작성 | PASS — 5개 카테고리별 표로 명세 |
| 4 | 04 스펙의 TODO-O2 본문 옵션 B 갱신 | PASS — `docs/work_flow/specs/04_infra_setup.md` line 160-185 갱신 |
| 5 | 사용자 결정 사항 (트리밍 방식, run_teleoperate 위치, diagnose 위치) 모두 본 문서에 명문화 | PASS |

### 실 실행 검증 필요 여부

**불필요** (study TODO). 본 산출물은 문서이며, 실 마이그레이션은 TODO-O2 (task) 가 책임. TODO-O2 의 prod 검증은 TODO-O3 가 책임.

다만 후속 TODO 가 본 §5 의 정확성에 의존하므로, TODO-O2 진행 시 §5 의 5개 카테고리를 그대로 실행하면 됨. 의문 발생 시 본 문서 §5 가 진실의 출처.

## 배포

- 일시: 2026-04-30 15:32
- 결과: 미실행 (현재 작업 컴퓨터가 devPC 와 다른 환경 — 사용자가 추후 일괄 배포). 본 TODO 산출물은 docs/ 하위라 Orin 측 즉시 반영 불필요. TODO-O2 (코드 마이그레이션) 진행 시점에 일괄 배포 예정.
