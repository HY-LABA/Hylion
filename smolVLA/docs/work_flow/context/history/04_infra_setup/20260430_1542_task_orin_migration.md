# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-30 15:36 | 스펙: `docs/work_flow/specs/04_infra_setup.md` | TODO: O2

## 작업 목표

orin/ 마이그레이션 실행.

TODO-O1 의 산출물 (`docs/storage/07_orin_structure.md` §5 마이그레이션 계획) 을 그대로 실행. 03 산출물 5개 (`smoke_test.py`, `inference_baseline.py`, `measure_latency.py`, `load_checkpoint_test.py`, `hil_inference.py`) 의 동작 회귀 없이 새 구조 (`tests/`, `config/`, `checkpoints/` 신규 + `calibration/` 제거 + entrypoint 2개 제거 + run_teleoperate.sh 임시 보관) 로 변경.

**트리밍 원칙 — 옵션 B (논리적 비활성화)**: upstream 구조 보존이 사용자 원칙. `orin/lerobot/` 의 파일·디렉터리는 그대로 유지하고, **`orin/pyproject.toml` 의 `[project.scripts]` entrypoint 등록만 inference + record 책임에 맞게 정리**.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

다음 6개 카테고리 모두 처리:

### 1. 이관 (out)
- `orin/calibration/diagnose_motor_encoder.py` → `orin/tests/diagnose_motor_encoder.py` (직접, 하위 디렉터리 X)
- `orin/scripts/run_teleoperate.sh` → 임시 보관 위치 (DataCollector 디렉터리 미존재). 권장 위치: `docs/storage/others/run_teleoperate.sh.archive` (BACKLOG 04 #2 가 임시 위치 컨벤션 결정 후행 작업)

### 2. 삭제 (rm)
- `orin/calibration/` 디렉터리 (diagnose_motor_encoder.py 이관 후 비게 됨)

### 3. entrypoint 정리 (orin/pyproject.toml `[project.scripts]`)
- `lerobot-eval` 제거 (Orin 평가 안 함)
- `lerobot-train` 제거 (Orin 학습 안 함)
- 9개 유지: lerobot-calibrate / lerobot-find-cameras / lerobot-find-port / lerobot-find-joint-limits / lerobot-record / lerobot-replay / lerobot-setup-motors / lerobot-teleoperate / lerobot-info

### 4. 신규 디렉터리 + README.md
- `orin/tests/README.md` — tests/ 의 책임 + first-time / resume 모드 가이드. 실 스크립트는 TODO-G1 이 채움
- `orin/config/README.md` + `orin/config/ports.json` + `orin/config/cameras.json` placeholder — config/ 책임 + 스키마 + 재생성 방법
- `orin/checkpoints/README.md` — 학습 ckpt 보관 정책 + 디렉터리 구조 (`<run_name>/<step>/pretrained_model/`) + sync_ckpt_dgx_to_orin.sh 사용법

### 5. .gitignore 갱신
- `orin/checkpoints/<run_name>/` 패턴 추가 (단 README.md 는 추적)

### 6. coupled file 갱신 (CLAUDE.md 규칙)
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` — entrypoint 2개 제거 이력 추가
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — 04 진입 시점의 옵션 B 트리밍 원칙 + entrypoint 정리 이력 추가

### 7. 회귀 검증 항목 (TODO-O3 prod 검증의 입력)
본 TODO 는 작성·이동만. 다음 항목들은 TODO-O3 에서 검증:
- `python -m py_compile` 03 산출물 5개 모두 PASS
- `from lerobot.policies.smolvla import ...` import 회귀 없음
- 신규 디렉터리 3개 git 추적 (tests/README.md, config/README.md + json 2개, checkpoints/README.md)

## 구현 대상

### 신규 파일
- `orin/tests/README.md`
- `orin/config/README.md`
- `orin/config/ports.json` (placeholder)
- `orin/config/cameras.json` (placeholder)
- `orin/checkpoints/README.md`

### 이동
- `orin/calibration/diagnose_motor_encoder.py` → `orin/tests/diagnose_motor_encoder.py`
- `orin/scripts/run_teleoperate.sh` → `docs/storage/others/run_teleoperate.sh.archive`

### 수정
- `orin/pyproject.toml` — `[project.scripts]` 섹션에서 lerobot-eval / lerobot-train 2줄 제거
- `.gitignore` (Hylion 레포 루트) — `orin/checkpoints/<run_name>/` 패턴 추가
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` — 변경 이력 추가
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — 변경 이력 추가

### 삭제
- `orin/calibration/` 디렉터리 (rm — diagnose_motor_encoder.py 이관 후)

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- **`orin/lerobot/` 하위 파일·디렉터리 — 변경 금지** (옵션 B 원칙. import 차단·entrypoint 정리만으로 비활성화)
- `orin/scripts/setup_env.sh` (Jetson PyTorch 설치 패턴 그대로 유지)
- `orin/examples/tutorial/smolvla/` 6개 .py (03 산출물 그대로)
- `orin/.hylion_arm/` venv (gitignore 대상 — 본 TODO 는 만들지 않음)
- `orin/README.md` 본문 — 새 디렉터리 안내 추가는 옵션 (간단히 추가하면 좋으나, 본 TODO 에서는 생략 가능. 04 종료 시점에 TODO-T3 와 함께 일괄 갱신 검토)

## 작업 시작 전 확인

1. `docs/storage/07_orin_structure.md` §5 마이그레이션 계획 — 본 TODO 의 입력 사양
2. `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 의 기존 변경 이력 형식 (날짜·변경 내용·이유·영향 범위)
3. `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 의 기존 변경 이력 형식 (동일)
4. 기존 `docs/storage/06_dgx_venv_setting.md` 같은 신규 README 작성 패턴 참고

## 신규 README 콘텐츠 가이드

### `orin/tests/README.md`
- tests/ 의 책임 (시나리오 점검 + 환경 게이트, 04 TODO-G1 의 위치)
- 두 모드 (first-time / resume) 의 의미 — TODO-O1 §2 의 컴포넌트 책임 인용
- 현재 자산 (diagnose_motor_encoder.py — 01 산출물 이관) 안내
- 향후 자산 (check_hardware.sh, configs/) 은 TODO-G1 에서 채움

### `orin/config/README.md`
- config/ 의 책임 (본 프로젝트 cached config — ports.json, cameras.json)
- ports.json 스키마 (예: `{"follower_port": "/dev/ttyACM1", "leader_port": null}` — null 은 미설정)
- cameras.json 스키마 (예: `{"top": {"index": 2, "flip": false}, "wrist": {"index": 0, "flip": true}}`)
- 재생성 방법: `tests/check_hardware.sh --mode first-time` 으로 cache 갱신 (TODO-G1 에서 구현)
- lerobot 캘리브레이션은 본 디렉터리 X — `~/.cache/huggingface/lerobot/calibration/` 표준 위치 그대로 사용

### `orin/config/ports.json` + `cameras.json` (placeholder)
- 빈 JSON `{}` 또는 null 값 placeholder (예: `{"follower_port": null, "leader_port": null}`)
- TODO-G1 의 first-time 모드가 갱신

### `orin/checkpoints/README.md`
- checkpoints/ 의 책임 (학습된 정책 ckpt 보관)
- 디렉터리 구조: `<run_name>/<step>/pretrained_model/{config.json, model.safetensors, train_config.json}`
- 첫 ckpt 는 05_leftarmVLA TODO-13 시점에 도착
- 전송 도구: `scripts/sync_ckpt_dgx_to_orin.sh` (devPC 경유 2-hop, 02 TODO-10b 검증)
- gitignore 정책: `<run_name>/` 하위는 추적 X, README.md 만 추적

## 참고 레퍼런스

- `docs/storage/07_orin_structure.md` — TODO-O1 산출물 (특히 §5 마이그레이션 계획)
- `docs/work_flow/specs/04_infra_setup.md` TODO-O2 본문 — 본 작업 사양
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` — 기존 pyproject 변경 이력 형식
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — 기존 orin/lerobot/ 변경 이력 형식
- `docs/storage/06_dgx_venv_setting.md` — DGX 측 README 작성 패턴 참고
- memory `project_run_teleoperate_relocation.md` — run_teleoperate.sh 위치 결정 (후보 a 채택, 임시 보관 시나리오)
- BACKLOG 04 #2 — 임시 보관 위치·확장자 컨벤션 (본 TODO 가 첫 사례)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 업데이트

*작업 완료 후 아래 항목을 채운다.*

### 변경한 내용

TODO-O1 의 §5 마이그레이션 계획 (5개 카테고리) 그대로 실행. 옵션 B (논리적 비활성화) 원칙 준수 — `orin/lerobot/` 파일·디렉터리는 변경 안 함.

**1. 이관 (out)**:
- `orin/calibration/diagnose_motor_encoder.py` → `orin/tests/diagnose_motor_encoder.py`
- `orin/scripts/run_teleoperate.sh` → `docs/storage/others/run_teleoperate.sh.archive` (DataCollector 디렉터리 미존재 시점이라 임시 보관 — TODO-D2 시점에 최종 이동)

**2. 삭제 (rm)**:
- `orin/calibration/` 디렉터리 (rmdir 후 비게 됨 확인)

**3. entrypoint 정리** (`orin/pyproject.toml [project.scripts]`):
- `lerobot-eval` 등록 해제
- `lerobot-train` 등록 해제
- 9개 entrypoint 유지 (calibrate / find-cameras / find-port / find-joint-limits / record / replay / setup-motors / teleoperate / info)
- 변경 이유 주석 추가

**4. 신규 디렉터리 + README/JSON** (5개 파일):
- `orin/tests/README.md` — tests/ 책임 + first-time/resume 모드 가이드 + 자산 표 (현재: diagnose_motor_encoder.py / 예정: check_hardware.sh + configs/)
- `orin/config/README.md` — config/ 책임 + ports.json/cameras.json 스키마 + 재생성 방법 + lerobot 표준 캘리브레이션 위치 (`~/.cache/huggingface/lerobot/calibration/`) 분리 명시
- `orin/config/ports.json` — placeholder `{"follower_port": null, "leader_port": null}`
- `orin/config/cameras.json` — placeholder `{"top": {"index": null, "flip": false}, "wrist": {"index": null, "flip": false}}`
- `orin/checkpoints/README.md` — 학습 ckpt 보관 정책 + 디렉터리 구조 + sync_ckpt_dgx_to_orin.sh 사용법 + git 정책

**5. .gitignore 갱신** (Hylion 레포 루트):
- `smolVLA/orin/checkpoints/*/` 패턴 추가 (README.md 는 추적, `<run_name>/` 하위는 추적 X)

**6. coupled file 갱신**:
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`: §5 표의 lerobot-eval/lerobot-train ✅ → ❌ 갱신 + 변경 이력 항목 추가 (2026-04-30, 변경 이유 / 영향 범위 / 잔여 리스크 BACKLOG 04 #1 명시)
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`: 옵션 B (논리적 비활성화) 원칙 명문화 변경 이력 추가

### 검증 방법 및 결과

| # | 검증 항목 | 결과 |
|---|---|---|
| 1 | `orin/` 새 구조 확인 — 8개 항목 (README, checkpoints, config, examples, lerobot, pyproject.toml, scripts, tests) | PASS — calibration/ 제거 확인 |
| 2 | `orin/tests/` 자산 — README.md + diagnose_motor_encoder.py | PASS |
| 3 | `orin/config/` 자산 — README.md + ports.json + cameras.json | PASS |
| 4 | `orin/checkpoints/` 자산 — README.md only | PASS |
| 5 | `orin/scripts/` 자산 — setup_env.sh only (run_teleoperate.sh 이관됨) | PASS |
| 6 | `docs/storage/others/run_teleoperate.sh.archive` 임시 보관 위치 존재 | PASS |
| 7 | `orin/pyproject.toml` 의 lerobot-eval / lerobot-train entrypoint 등록 해제 | PASS — grep `^lerobot-(eval\|train)` 결과 0건 |
| 8 | `.gitignore` 에 `smolVLA/orin/checkpoints/*/` 패턴 추가 | PASS — line 232 확인 |
| 9 | `02_orin_pyproject_diff.md` 변경 이력 추가 | PASS — 2026-04-30 항목 추가 + §5 표 갱신 |
| 10 | `03_orin_lerobot_diff.md` 변경 이력 추가 | PASS — 옵션 B 원칙 명문화 항목 추가 |

devPC 측 `python -m py_compile` 검증은 본 TODO 가 코드 수정 없는 디렉터리 정리 + 문서 작성이라 불필요. 03 산출물 5개 (smoke_test.py / inference_baseline.py / measure_latency.py / load_checkpoint_test.py / hil_inference.py) 의 import 회귀 검증은 TODO-O3 의 책임.

### 실 실행 검증 필요 여부

**필요.** TODO-O3 (test) 가 본 작업의 prod 검증을 담당. Orin 에서:

1. **배포 후 venv 갱신** — `pip install -e ~/smolvla/orin/[smolvla,hardware,feetech]` 재실행 (entrypoint 2개 제거 반영)
2. **import 회귀 검증** — `from lerobot.policies.smolvla import SmolVLAPolicy, ...` PASS
3. **03 산출물 5개 동작 확인** — 적어도 smoke_test.py + load_checkpoint_test.py + hil_inference.py --help 는 통과해야 함
4. **신규 디렉터리 추적 확인** — git status 로 tests/, config/, checkpoints/ 의 README + JSON 모두 추적, `<run_name>/` 하위는 ignore
5. **lerobot-eval / lerobot-train CLI 호출 시 command not found** — 등록 해제 반영 확인

특히 점검할 잔여 리스크:
- `pip install -e .` 재실행 시 entrypoint 2개가 venv 의 bin/ 에서 제거되는지 (이전 등록은 venv 측에 cache 됐을 수 있음)
- BACKLOG 04 #1 — upstream 동기화 시 본 entrypoint 정리 덮어씌움 위험. 다음 동기화 절차에 본 항목 명시 필요

## 후속 작업 식별 (사용자 인사이트)

본 TODO-O2 완료 직후 사용자가 `orin/examples/` 디렉터리 구조에 대한 위화감을 제기 — `using_smolvla_example.py` (upstream 미러) 와 본 프로젝트 5개 신규 파일 (smoke_test, inference_baseline, measure_latency, load_checkpoint_test, hil_inference) 이 한 디렉터리에 섞여 책임 분류 모호.

분석 결과:
- `using_smolvla_example.py` 는 upstream `examples/tutorial/smolvla/` 에서 그대로 가져온 튜토리얼
- 본 프로젝트 5개 중 `hil_inference.py` 만 upstream `using_smolvla_example.py` 와 80% 가까운 책임 (SmolVLA + joints + send_action 루프), 단 안전장치·dry-run·flip·empty_cameras 추가됨
- `examples/so100_to_so100_EE/evaluate.py` 는 ACT + EE 키네매틱스 + 데이터셋 push 까지 하는 다른 워크플로우라 본 프로젝트와 매핑 어색

사용자 결정: **옵션 B'' + hil_inference 별도** — 4개 검증 스크립트는 `orin/tests/` 로, hil_inference 는 `orin/inference/` 신설 디렉터리로. 향후 마일스톤별 추론 정책 아카이빙 디렉터리 역할 의도.

후속 작업은 **TODO-O2b 로 신설** 하여 명시적 추적. TODO-O2 자체는 본 시점에 완료 처리 유지.

## 배포

- 일시: 2026-04-30 15:42
- 결과: 미실행 (현재 작업 컴퓨터가 devPC 와 다른 환경 — 사용자가 추후 일괄 배포). TODO-O2 의 변경은 Orin 측 코드 (orin/pyproject.toml entrypoint + 디렉터리 구조) 에 영향. TODO-O3 (회귀 검증) 진입 시점에는 반드시 배포 선행 필요.
