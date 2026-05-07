# docs/storage/ — Navigator

실측 기록, 환경 설정 이력, upstream 추적 문서를 보관하는 디렉토리.

---

## 문서 목록 (활성)

> 2026-05-07 활성 문서 01-10 으로 순차 재번호. legacy 이관 항목은 하단 별도 섹션 참조.

| 번호 | 파일 | 내용 |
|---|---|---|
| 01 | [01_smolvla_arm_env_requirements.md](01_smolvla_arm_env_requirements.md) | 요구사항 — 환경 구성에 필요한 것 (What is required) |
| 02 | [02_hardware.md](02_hardware.md) | 하드웨어 실측/보유 현황 |
| 03 | [03_software.md](03_software.md) | 소프트웨어 실측/설정 현황 |
| 04 | [04_devnetwork.md](04_devnetwork.md) | 개발 네트워크 설정 |
| 05 | [05_orin_venv_setting.md](05_orin_venv_setting.md) | Orin 환경 세팅 기록 (venv `~/smolvla/orin/.hylion_arm`, PyTorch JP 6.0 wheel, torchvision 등) |
| 06 | [06_dgx_venv_setting.md](06_dgx_venv_setting.md) | DGX Spark 학습·배포 환경 세팅 기록 (venv `~/smolvla/dgx/.arm_finetune`, PyTorch 2.10.0+cu130, lerobot editable, TODO-09b smoke 실측치, §9 DGX→Orin 체크포인트 sync 절차 — TODO-10b 완료 시 실측치 누적) |
| 07 | [07_orin_structure.md](07_orin_structure.md) | orin/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획 (04 사이클 기준 — 추론 전용 책임 명확화) — 구 08 |
| 08 | [08_dgx_structure.md](08_dgx_structure.md) | dgx/ 디렉터리 구조·기능 책임 매트릭스 (04 사이클 기준; 06 결정으로 학습 + 데이터 수집 두 책임 흡수 반영은 X2 todo 에서 처리) — 구 09 |
| 09 | [09_demo_site_mirroring.md](09_demo_site_mirroring.md) | 시연장 환경 미러링 가이드 (04 기준; 06 결정으로 DataCollector → DGX 역할 전환 — 본 문서의 "DataCollector 인근" 표현은 역사적 결정 보존, 실제 운영은 DGX 직접 이동으로 대체) — 구 11 |
| 10 | [10_orin_config_policy.md](10_orin_config_policy.md) | `orin/config/ports.json`·`cameras.json` 의 git 추적 정책 명문화 (07_e2e_pilot_and_cleanup TODO-W4, 04 BACKLOG #3 흡수) — 구 15 |

---

## Legacy 이관 항목

활성 영역에서 분리된 자산. 이관 사유·이관 위치는 각 legacy 디렉터리의 README 참조.

| 원 번호 | 원 파일 | 이관일 | 이관 위치 |
|---|---|---|---|
| 07 | 07_datacollector_venv_setting.md | 2026-05-02 | [legacy/02_datacollector_separate_node/](legacy/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md) |
| 10 | 10_datacollector_structure.md | 2026-05-02 | [legacy/02_datacollector_separate_node/](legacy/02_datacollector_separate_node/docs_storage_10_datacollector_structure.md) |
| 12 | 12_interactive_cli_framework.md | 2026-05-07 | [legacy/03_interactive_cli/](legacy/03_interactive_cli/docs_storage_12_interactive_cli_framework.md) |
| 13 | 13_orin_cli_flow.md | 2026-05-07 | [legacy/03_interactive_cli/](legacy/03_interactive_cli/docs_storage_13_orin_cli_flow.md) |
| 14 | 14_dgx_cli_flow.md | 2026-05-07 | [legacy/03_interactive_cli/](legacy/03_interactive_cli/docs_storage_14_dgx_cli_flow.md) |
| 15 (구) | 15_datacollector_cli_flow.md | 2026-05-02 | [legacy/02_datacollector_separate_node/](legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md) |

> 번호 매핑 변경 이력 (2026-05-07): 활성 문서 재번호로 구 `08_orin_structure` → 07, 구 `09_dgx_structure` → 08, 구 `11_demo_site_mirroring` → 09, 구 `15_orin_config_policy` → 10. 위 legacy 표의 "원 번호" 는 이관 당시 번호 (재번호 이전 기준).

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
