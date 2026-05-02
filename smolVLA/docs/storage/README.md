# docs/storage/ — Navigator

실측 기록, 환경 설정 이력, upstream 추적 문서를 보관하는 디렉토리.

---

## 문서 목록

| 번호 | 파일 | 내용 |
|---|---|---|
| 01 | [01_smolvla_arm_env_requirements.md](01_smolvla_arm_env_requirements.md) | 요구사항 — 환경 구성에 필요한 것 (What is required) |
| 02 | [02_hardware.md](02_hardware.md) | 하드웨어 실측/보유 현황 |
| 03 | [03_software.md](03_software.md) | 소프트웨어 실측/설정 현황 |
| 04 | [04_devnetwork.md](04_devnetwork.md) | 개발 네트워크 설정 |
| 05 | [05_orin_venv_setting.md](05_orin_venv_setting.md) | Orin 환경 세팅 기록 (venv `~/smolvla/orin/.hylion_arm`, PyTorch JP 6.0 wheel, torchvision 등) |
| 06 | [06_dgx_venv_setting.md](06_dgx_venv_setting.md) | DGX Spark 학습·배포 환경 세팅 기록 (venv `~/smolvla/dgx/.arm_finetune`, PyTorch 2.10.0+cu130, lerobot editable, TODO-09b smoke 실측치, §9 DGX→Orin 체크포인트 sync 절차 — TODO-10b 완료 시 실측치 누적) |
| 07 | ~~07_datacollector_venv_setting.md~~ | **legacy 이관 (2026-05-02)**: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md`. DataCollector 노드 운영 종료 — DGX 가 데이터 수집 책임 흡수 (06_dgx_absorbs_datacollector). |
| 08 | [08_orin_structure.md](08_orin_structure.md) | orin/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획 (04 사이클 기준 — 추론 전용 책임 명확화) |
| 09 | [09_dgx_structure.md](09_dgx_structure.md) | dgx/ 디렉터리 구조·기능 책임 매트릭스 (04 사이클 기준; 06 결정으로 학습 + 데이터 수집 두 책임 흡수 반영은 X2 todo 에서 처리) |
| 10 | ~~10_datacollector_structure.md~~ | **legacy 이관 (2026-05-02)**: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_10_datacollector_structure.md`. DataCollector 노드 운영 종료 — DGX 흡수 결정 (06_dgx_absorbs_datacollector). |
| 11 | [11_demo_site_mirroring.md](11_demo_site_mirroring.md) | 시연장 환경 미러링 가이드 (04 기준; 06 결정으로 DataCollector → DGX 역할 전환 — 본 문서의 "DataCollector 인근" 표현은 역사적 결정 보존, 실제 운영은 DGX 직접 이동으로 대체) |
| 12 | [12_interactive_cli_framework.md](12_interactive_cli_framework.md) | interactive_cli 3 노드 공통 boilerplate (05 기준 — flow 0·1 패턴; 06 결정으로 datacollector 노드 제거, 본 문서의 datacollector 언급은 역사적 결정 보존) |
| 13 | [13_orin_cli_flow.md](13_orin_cli_flow.md) | orin flow 3+ (추론 mode) 설계 — O1 study 산출물 |
| 14 | [14_dgx_cli_flow.md](14_dgx_cli_flow.md) | dgx 통합 flow 설계 — 학습 + 수집 mode (06 X1 study 산출물) |
| 15 | ~~15_datacollector_cli_flow.md~~ | **legacy 이관 (2026-05-02)**: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md`. DataCollector 노드 운영 종료 (06_dgx_absorbs_datacollector). |

---

## 서브디렉토리

### devices_snapshot/

장치 환경 스냅샷 수집 스크립트 및 결과 보관.

| 파일 | 내용 |
|---|---|
| [run_snapshots.sh](devices_snapshot/run_snapshots.sh) | 전체 스냅샷 실행 진입점 |
| [collect_snapshot.sh](devices_snapshot/collect_snapshot.sh) | 개별 장치 스냅샷 수집 스크립트 |
| `*_env_snapshot_*.txt` | 장치별 환경 스냅샷 (날짜 포함) |

### lerobot_upstream_check/

upstream lerobot 대비 orin/ 커스텀 레이어 변경 이력 추적.

| 파일 | 내용 |
|---|---|
| [99_lerobot_upstream_Tracking.md](lerobot_upstream_check/99_lerobot_upstream_Tracking.md) | upstream 동기화 이력 |
| [01_compatibility_check.md](lerobot_upstream_check/01_compatibility_check.md) | 의존성 충돌 점검 기록 (Python 버전, 신규 문법 등) |
| [02_orin_pyproject_diff.md](lerobot_upstream_check/02_orin_pyproject_diff.md) | upstream vs orin/pyproject.toml 변경 이력 |
| [03_orin_lerobot_diff.md](lerobot_upstream_check/03_orin_lerobot_diff.md) | upstream vs orin/lerobot/ 코드 변경 이력 |
| [check_update_diff.sh](lerobot_upstream_check/check_update_diff.sh) | 점검 스크립트 |

### others/

| 파일 | 내용 |
|---|---|
| `torchvision-*.whl` | Jetson aarch64용 torchvision 수동 설치 wheel |
