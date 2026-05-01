# TODO-X2 — dgx/ 마이그레이션 실행

> 작성: 2026-05-01 15:00 | task-executor | cycle: 1

## 목표

TODO-X1 §5 마이그레이션 계획대로 dgx/ 디렉터리 구조 변경 실행. 02 산출물 (setup_train_env.sh, preflight_check.sh, smoke_test.sh, save_dummy_checkpoint.sh) 동작 회귀 없음.

## 사전 점검 결과

- X1 §5 마이그레이션 계획 5 카테고리 그대로 따름
- dgx/pyproject.toml 미존재 확인 — Category B 변경 대상 없음. README.md 주의사항만 작성
- dgx/lerobot/ 미존재 확인 — upstream 무수정 원칙 자연 충족
- run_teleoperate.sh 이관은 D2 위임 (현재 `docs/storage/others/run_teleoperate.sh.archive` 임시 보관 유지)
- dataset_repos.json schema 결정: HF Hub repo_id (`{hf_username}/{dataset_name}`) + rsync source/dest + active_method 양쪽 필드. lerobot upstream DatasetRecordConfig.repo_id 표준 준수

## 산출물 표

| 작업 | 카테고리 | 위치 |
|---|---|---|
| dgx/tests/ + README.md | 신규 | `dgx/tests/README.md` |
| dgx/config/ + README.md + dataset_repos.json | 신규 | `dgx/config/README.md`, `dgx/config/dataset_repos.json` |
| dgx/README.md 주의사항 + DataCollector 인터페이스 + 새 디렉터리 안내 | 갱신 | `dgx/README.md` |
| 04_dgx_lerobot_diff.md 변경 이력 항목 추가 | coupled file | `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` |

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/tests/README.md` | 신규 | DGX 환경 점검 디렉터리 신설, preflight_check.sh 와 역할 분리 명시 |
| `dgx/config/README.md` | 신규 | DataCollector ↔ DGX 데이터셋 설정 캐시, dataset_repos.json 스키마 상세 |
| `dgx/config/dataset_repos.json` | 신규 | HF Hub + rsync placeholder (~20줄) |
| `dgx/README.md` | M | ⚠ 주의사항 섹션 (pyproject.toml 미존재 + lerobot 설치 방법) + DataCollector 인터페이스 섹션 추가 |
| `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | M | 2026-05-01 TODO-X2 변경 이력 항목 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints:
  - Category A: `docs/reference/` 미변경 ✓
  - Category B: dgx/lerobot/ 미존재로 자연 충족. dgx/pyproject.toml 미변경 ✓
  - Category C: dgx/ 하위 신규 디렉터리 (orin/ 형제 구조, 이미 합의된 구조) — Category C 해당 없음 ✓
- Coupled File Rule: `04_dgx_lerobot_diff.md` 동시 갱신 ✓
- 레퍼런스 활용:
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` DatasetRecordConfig.repo_id 포맷 차용 → `dataset_repos.json` 의 `hf_hub.repo_id` 필드 설계
  - `orin/tests/README.md` + `orin/config/README.md` 패턴 미러 → dgx/ 형제 README 작성

## 핵심 결정

- `dataset_repos.json` schema: lerobot upstream 의 `DatasetRecordConfig.repo_id` (`{hf_username}/{dataset_name}`) 포맷을 `hf_hub.repo_id` 필드에 그대로 채택. rsync 방식은 `source` (DataCollector 측) / `dest` (DGX 측, HF_HOME 기준 표준 위치) 로 구성. `active_method` 로 현재 사용 방식 전환 가능.
- `dgx/pyproject.toml` 미존재 처리: README.md 에 명시적 주의사항 섹션 추가. `lerobot-train` entrypoint 는 `docs/reference/lerobot/` editable install 에서 제공되며 별도 pyproject 불필요함을 명문화.
- run_teleoperate.sh: X2 에서 dgx/ 측 처리 없음. `docs/storage/others/run_teleoperate.sh.archive` 임시 보관 그대로. TODO-D2 시점에 `datacollector/scripts/run_teleoperate.sh` 로 최종 이동.

## 변경 내용 요약

TODO-X1 §5 마이그레이션 계획의 "신규 3건 (in)" 을 실행했다. `dgx/tests/` 와 `dgx/config/` 디렉터리를 신설하고, DataCollector → DGX 데이터 전송 설정을 위한 `dataset_repos.json` placeholder 를 작성했다. JSON 스키마는 lerobot upstream `DatasetRecordConfig.repo_id` 표준 포맷을 따르며, HF Hub 와 rsync 두 전송 방식을 모두 지원하는 구조로 설계했다.

`dgx/README.md` 는 `pyproject.toml 미존재` 주의사항과 `DataCollector ↔ DGX 인터페이스` 섹션을 추가하여 04 이후 아키텍처 변경을 반영했다. `dgx/scripts/` 4개 파일은 미변경으로 02 산출물 동작 회귀가 없다.

## code-tester 입장에서 검증 권장 사항

- JSON 유효성: `python -m json.tool dgx/config/dataset_repos.json` — valid JSON 확인
- 신규 디렉터리 존재: `ls dgx/tests/README.md dgx/config/README.md dgx/config/dataset_repos.json` — 3개 존재
- dgx/scripts/ 미변경: `git diff dgx/scripts/` — 변경 없음 확인
- README 패턴 일관성: `dgx/tests/README.md` 와 `orin/tests/README.md` 구조 비교 (책임·자산표·외부의존성·참고 섹션)
- coupled file 갱신: `04_dgx_lerobot_diff.md` 에 2026-05-01 항목 존재 확인
- Category B 미변경: dgx/pyproject.toml 미존재 + dgx/lerobot/ 미존재 유지 확인

## 잔여 리스크 / SKILL_GAP

- `dgx/outputs/` gitignore 패턴 존재 여부: Hylion 루트 `.gitignore` 에서 확인 보류 (bash grep 권한 없음). TODO-X3 시점 사용자 확인 권장.
- `dataset_repos.json` 실 값: TODO-T1 결정 (HF Hub + rsync 둘 다 확정) 후 05_leftarmVLA 진입 시 사용자가 채움.
- run_teleoperate.sh 최종 이관: TODO-D2 시점 (`datacollector/` 신규 후) 처리.

## 검증 필요 (다음 단계)

- **code-tester**: 신규 디렉터리 3개 + JSON valid + README 패턴 미러 + coupled file 갱신 누락 확인 + dgx/scripts/ 미변경 확인
- **prod-test-runner (TODO-X3)**: DGX 환경에서 02 산출물 (setup_train_env.sh / preflight_check.sh / smoke_test.sh / save_dummy_checkpoint.sh) 회귀 없음 확인. `dgx/outputs/` gitignore 패턴 확인.

---

## cycle 2 수정 (2026-05-01)

### Recommended #1 해소 — .gitignore smolVLA/dgx/outputs/ 패턴

- 추가 위치: `smolVLA/orin/checkpoints/*/` 패턴 직후 (235행)
- 추가 내용: 주석 1행 + 패턴 1행
- Category B 변경 (`.gitignore`) — 1행 추가만, MAJOR 시 게이트 발동 가능 영역이지만 본 cycle 은 MINOR 1회 수정
- 검증: `.gitignore` Read 235행 `smolVLA/dgx/outputs/` 패턴 존재 확인 — PASS

### #2·#3 무시 사유

- #2: DGX 맥락 적합 변형 — code-tester 판단 합리적, 무시
- #3: placeholder 실 사용 전 자명, 실용 오동작 없음 — 무시

### 다음 단계

- 본 cycle 2 종료 → X2 todo 완료 마킹 → X3 prod-test-runner 책임
- X3: DGX SSH 1 step smoke test 회귀 X 검증 + `dgx/outputs/` gitignore 패턴 확인
