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

### logs/

| 파일 | 내용 |
|---|---|
| [todo.md](logs/todo.md) | Orin 환경 개선 TODO 및 결정 이력 |

### others/

| 파일 | 내용 |
|---|---|
| `torchvision-*.whl` | Jetson aarch64용 torchvision 수동 설치 wheel |
