# 20260501_1500 — TODO-X2: dgx/ 마이그레이션 실행

> task-executor | cycle: 1 | 2026-05-01 15:00

## 요약

04_infra_setup TODO-X1 §5 마이그레이션 계획 5개 카테고리에 따라 dgx/ 구조 변경 실행.
신규 2건 (tests/, config/) + README.md 갱신 + coupled file (04_dgx_lerobot_diff.md) 갱신.
dgx/scripts/ 미변경 — 02 산출물 (setup_train_env / preflight / smoke / save_dummy_checkpoint) 회귀 없음.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/tests/README.md` | 신규 | DGX 환경 점검 + 회귀 검증 디렉터리 신설 |
| `dgx/config/README.md` | 신규 | DataCollector ↔ DGX 데이터셋 설정 캐시 디렉터리 신설 |
| `dgx/config/dataset_repos.json` | 신규 | HF Hub + rsync 두 방식 모두 지원 placeholder |
| `dgx/README.md` | 갱신 | pyproject.toml 미존재 주의사항 + DataCollector 인터페이스 + 새 디렉터리 안내 추가 |
| `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | 갱신 | TODO-X2 변경 이력 항목 추가 (coupled file 규칙) |

## 마이그레이션 계획 5개 카테고리 처리 결과

| 카테고리 | 항목 | 처리 |
|---|---|---|
| 유지 (7건) | scripts/ 4개 + runs/README.md + README.md + .arm_finetune/ | README.md 는 갱신만. 나머지 변경 없음 |
| 이관 out (1건) | run_teleoperate.sh | D2 위임. `docs/storage/others/run_teleoperate.sh.archive` 임시 보관 유지 |
| 신규 in (3건) | dgx/tests/ + dgx/config/ + dataset_repos.json | 모두 신규 생성 완료 |
| 삭제 (0건) | 없음 | 해당 없음 |
| entrypoint 정리 | dgx/pyproject.toml 미존재 | README.md 주의사항 추가로 처리 |

## 핵심 결정

- `dataset_repos.json` 스키마: HF Hub `repo_id` (`{hf_username}/{dataset_name}` — lerobot upstream DatasetRecordConfig.repo_id 표준) + rsync `source/dest` + `active_method` 필드. 두 방식 모두 지원.
- lerobot 레퍼런스 패턴 확인: `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` DatasetRecordConfig.repo_id 포맷 준수.
- orin/tests/README.md + orin/config/README.md 패턴 미러: 책임·자산 표·외부 의존성·참고 섹션 구조 동일하게 작성.

## 검증 결과 (devPC 로컬)

- dgx/tests/README.md, dgx/config/README.md, dgx/config/dataset_repos.json 신규 존재 확인 (Write 도구 성공)
- dgx/README.md 주의사항 섹션 추가 확인 (Edit 도구 성공)
- dataset_repos.json: valid JSON 구조 (Write 도구 직접 작성)
- dgx/scripts/ 내 4개 파일 미변경 — TODO-X3 에서 smoke test 재실행으로 회귀 없음 확인 예정

## 잔여 리스크

- `dgx/outputs/` gitignore 패턴 존재 여부: Hylion 루트 .gitignore 에서 미확인 (Category B 영역이라 직접 수정 보류). TODO-X3 시점에 확인 필요.
- dataset_repos.json 실 값: TODO-T1 결정 (HF Hub + rsync 둘 다) 후 05_leftarmVLA 진입 시 채움.
- run_teleoperate.sh 최종 이관: TODO-D2 시점 (datacollector/ 디렉터리 신규).
