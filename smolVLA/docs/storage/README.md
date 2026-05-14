# docs/storage/ — Navigator

실측 기록, 환경 설정 이력, upstream 추적 문서를 보관하는 디렉토리.

---

## 문서 목록 (활성)

> 2026-05-07 활성 문서 01-10 으로 순차 재번호. 2026-05-12 11 추가 (`lerobot_study` → 이관). 2026-05-14 구 01 삭제 (02·03·본 README 와 중복) + 09·10·11 삭제 (새 계획 수립 위한 fresh start — 옛 결정·실측 자산 정리). 2026-05-14 새 01 작성 (`01_collection_scenario.md` — leftarm 수집 시나리오, realplaying.md M1). 번호 재정렬은 안 함 (02·07·08 유지). legacy 이관 항목은 하단 별도 섹션 참조.

| 번호 | 파일 | 내용 |
|---|---|---|
| 01 | [01_collection_scenario.md](01_collection_scenario.md) | leftarm 데이터 수집 시나리오 — v1→v2 task 설계·수집 전략(차수 번갈기 + 캔 배치 변형)·환경 파라미터 |
| 02 | [02_hardware.md](02_hardware.md) | 하드웨어 실측/보유 현황 |
| 03 | [03_software.md](03_software.md) | 소프트웨어 실측/설정 현황 |
| 04 | [04_devnetwork.md](04_devnetwork.md) | 개발 네트워크 설정 |
| 05 | [05_orin_venv_setting.md](05_orin_venv_setting.md) | Orin 환경 세팅 기록 (venv `~/smolvla/orin/.hylion_arm`, PyTorch JP 6.0 wheel, torchvision 등) |
| 06 | [06_dgx_venv_setting.md](06_dgx_venv_setting.md) | DGX Spark 학습·배포 환경 세팅 기록 (venv `~/smolvla/dgx/.arm_finetune`, PyTorch 2.10.0+cu130, lerobot editable, TODO-09b smoke 실측치, §9 DGX→Orin 체크포인트 sync 절차 — TODO-10b 완료 시 실측치 누적) |
| 07 | [07_orin_structure.md](07_orin_structure.md) | orin/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획 (04 사이클 기준 — 추론 전용 책임 명확화) — 구 08 |
| 08 | [08_dgx_structure.md](08_dgx_structure.md) | dgx/ 디렉터리 구조·기능 책임 매트릭스 (04 사이클 기준; 06 결정으로 학습 + 데이터 수집 두 책임 흡수 반영은 X2 todo 에서 처리) — 구 09 |

> 2026-05-14 삭제: `09_demo_site_mirroring.md` (시연장 미러링 가이드 + §7 실측), `10_orin_config_policy.md` (orin/config git 추적 정책), `11_smolvla_model_decision.md` (SmolVLA 모델 선정 근거). 새 계획 수립 시 관련 내용 재검토 예정. git 히스토리에서 복구 가능.

---

## Legacy 이관 항목

활성 영역에서 분리된 자산. 이관 사유·이관 위치는 각 legacy 디렉터리의 README 참조.

| 원 번호 | 원 파일 | 이관일 | 이관 위치 |
|---|---|---|---|
| 07 | 07_datacollector_venv_setting.md | 2026-05-02 | [legacy/arm_2week_plan/others/02_datacollector_separate_node/](legacy/arm_2week_plan/others/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md) |
| 10 | 10_datacollector_structure.md | 2026-05-02 | [legacy/arm_2week_plan/others/02_datacollector_separate_node/](legacy/arm_2week_plan/others/02_datacollector_separate_node/docs_storage_10_datacollector_structure.md) |
| 12 | 12_interactive_cli_framework.md | 2026-05-07 | [legacy/arm_2week_plan/others/03_interactive_cli/](legacy/arm_2week_plan/others/03_interactive_cli/docs_storage_12_interactive_cli_framework.md) |
| 13 | 13_orin_cli_flow.md | 2026-05-07 | [legacy/arm_2week_plan/others/03_interactive_cli/](legacy/arm_2week_plan/others/03_interactive_cli/docs_storage_13_orin_cli_flow.md) |
| 14 | 14_dgx_cli_flow.md | 2026-05-07 | [legacy/arm_2week_plan/others/03_interactive_cli/](legacy/arm_2week_plan/others/03_interactive_cli/docs_storage_14_dgx_cli_flow.md) |
| 15 (구) | 15_datacollector_cli_flow.md | 2026-05-02 | [legacy/arm_2week_plan/others/02_datacollector_separate_node/](legacy/arm_2week_plan/others/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md) |

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
| [04_dgx_lerobot_diff.md](lerobot_upstream_check/04_dgx_lerobot_diff.md) | DGX 측 wrapper 스크립트 (`dgx/scripts/*.sh`) 변경 이력 — DGX 는 `docs/reference/lerobot/` editable install 이라 lerobot 코드 diff 0 (파일명 주의: 문서 상단 경고 참조) |
| [05_so100_vs_so101.md](lerobot_upstream_check/05_so100_vs_so101.md) | SO-100 vs SO-101 upstream study — `SOFollower`/`SOLeader` 클래스 구조 및 SO-101 정합 클래스 결정 (2026-05-12 `lerobot_study/06` → 이관) |
| [check_update_diff.sh](lerobot_upstream_check/check_update_diff.sh) | 점검 스크립트 |

### workflow_reflections/

reflection 에이전트가 spec 사이클 종료 (`/wrap-spec`) 시 작성하는 회고 보고서 보관. 파일명 규칙 `<YYYY-MM-DD>_<spec명>.md`. 상세는 [workflow_reflections/README.md](workflow_reflections/README.md).

### legacy/

활성 워크플로우에서 분리된 자산 보관 (위 "Legacy 이관 항목" 표 참조). 시대(era) 단위로 묶음 — 현재 `arm_2week_plan/` (구 로드맵·BACKLOG·ANOMALIES·`work_flow/` 사이클 흔적·`others/{01_pre_subagent_workflow, 02_datacollector_separate_node, 03_interactive_cli}`). 상세는 [legacy/README.md](legacy/README.md).

### others/

번호 체계·서브디렉터리 어디에도 속하지 않는 잡다 자산.

| 파일 | 내용 |
|---|---|
| `torchvision-*.whl` | Jetson aarch64용 torchvision 수동 설치 wheel (PyPI 미제공 — `setup_env.sh` fallback) |
| [ckpt_transfer_scenarios.md](others/ckpt_transfer_scenarios.md) | DGX 체크포인트 → 시연장 Orin 전송 경로 4 케이스 분류 (04_infra_setup TODO-T2) |
| [walking_rl_check.md](others/walking_rl_check.md) | Walking RL 트랙과 DGX Spark 공유 점검 요청서 (2026-04-28) |
| [walking_rl_smolvla_check_2026-04-28.md](others/walking_rl_smolvla_check_2026-04-28.md) | 위 점검 요청의 결과 기록 |
| `run_teleoperate.sh.archive` | 이관 완료 표식 파일 (DataCollector 로 최종 이관, 본 위치 미사용) |
| `다리id다운/` | Berkeley Humanoid Lite 모터 컨트롤러 펌웨어 플래싱 작업 자산 (작업 로그·StepByStep 가이드·STM32CubeIDE PDF·CAN ID 매핑표) — smolVLA 와 별개 트랙 |
