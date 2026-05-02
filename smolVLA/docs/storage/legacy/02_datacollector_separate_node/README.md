# 02_datacollector_separate_node — Legacy 이관 기록

> 이관 일자: 2026-05-02
> 이관 사유: 06_dgx_absorbs_datacollector 결정 — DGX 가 데이터 수집 책임 흡수
> DataCollector 머신 (smallgaint, Ubuntu 22.04) 운영 종료

---

## 이관 배경

본 디렉터리는 04_infra_setup 사이클에서 구축된 **DataCollector 별도 노드** 자산을 보관한다.

### 결정 동력

**동력 1 — BACKLOG #11 차단 (Python 3.12)**

DataCollector (smallgaint, Ubuntu 22.04, Python 3.10) 가 lerobot upstream import 실패.
lerobot 5+ 파일이 PEP 695 generic syntax 사용 → Python 3.12+ 강제.
학교 WiFi 가 launchpad.net (deadsnakes PPA endpoint) timeout 으로 차단 — 우회 불가능
(05_interactive_cli ANOMALIES #2·#3).

→ DGX (이미 Python 3.12.3 + `.arm_finetune` venv 운영 중) 가 데이터 수집 책임을 흡수하면
BACKLOG #11 자연 우회.

**동력 2 — 시연장 미러링 원칙의 단순화**

04 가 DataCollector 별도 노드를 둔 이유: *시연장 인근 데이터 수집*.
06 결정으로 DGX 자체가 시연장 직접 이동 → 미러링 원칙 유지.
데이터 수집 → 학습 → 시연장 추론 흐름이 DGX 한 곳에서 처음 두 단계 통합 + Orin 시연장 추론
한 단계로 단순화.

---

## DataCollector 머신 운영 종료

- 머신: smallgaint (Ubuntu 22.04, Python 3.10, CPU-only)
- 상태: 본 사이클 (06_dgx_absorbs_datacollector) 종료 이후 **운영 종료**
- 후속: 머신 회수 또는 다른 용도 재활용 — 사용자 결정 사항 (본 spec 범위 외)

---

## 이관 자산 목록

### 디렉터리 1건

| 원래 위치 | 이관 후 위치 |
|---|---|
| `smolVLA/datacollector/` | `docs/storage/legacy/02_datacollector_separate_node/datacollector/` |

`datacollector/` 내부 구조:
- `config/` — SO-ARM 캘리브레이션·설정 파일
- `data/` — 로컬 데이터셋 (git 추적 외)
- `interactive_cli/` — flow 0~7 (entry·env_check·teleop·data_kind·record·transfer)
- `pyproject.toml` — 의존성 (record·hardware·feetech extras + lerobot editable)
- `README.md` — DataCollector 노드 설명
- `scripts/` — run_teleoperate.sh·push_dataset_hub.sh·check_hardware.sh
- `tests/` — 단위 테스트

### docs/storage 파일 3건 (prefix 변경 이관)

| 원래 위치 | 이관 후 위치 |
|---|---|
| `docs/storage/07_datacollector_venv_setting.md` | `docs_storage_07_datacollector_venv_setting.md` |
| `docs/storage/10_datacollector_structure.md` | `docs_storage_10_datacollector_structure.md` |
| `docs/storage/15_datacollector_cli_flow.md` | `docs_storage_15_datacollector_cli_flow.md` |

### smolVLA/scripts 파일 3건 (prefix 변경 이관)

| 원래 위치 | 이관 후 위치 |
|---|---|
| `scripts/sync_dataset_collector_to_dgx.sh` | `scripts_sync_dataset_collector_to_dgx.sh` |
| `scripts/sync_ckpt_dgx_to_datacollector.sh` | `scripts_sync_ckpt_dgx_to_datacollector.sh` |
| `scripts/deploy_datacollector.sh` | `scripts_deploy_datacollector.sh` |

이관 이유 (scripts 3건):
- `sync_dataset_collector_to_dgx.sh` — DGX 가 자기 자신에게 sync 무의미
- `sync_ckpt_dgx_to_datacollector.sh` — DGX → DataCollector 케이스 무효 (머신 회수)
- `deploy_datacollector.sh` — DataCollector 머신 회수로 불요

---

## 후속 — DGX 흡수 (06_dgx_absorbs_datacollector X 그룹)

DataCollector 책임은 DGX 가 흡수:

- `dgx/interactive_cli/flows/mode.py` — NEW: "수집 / 학습 / 종료" mode 분기 질문 (TODO-X2)
- `dgx/interactive_cli/flows/{teleop,data_kind,record,transfer}.py` — datacollector/flows/ 이식 (TODO-X2)
- `dgx/scripts/{run_teleoperate,push_dataset_hub,check_hardware}.sh` — datacollector/scripts/ 이식 (TODO-X3)
- `dgx/pyproject.toml` — record·hardware·feetech extras 추가 (TODO-X4, Category B 사용자 동의)
- `dgx/scripts/setup_env.sh` — extras 설치 추가 (TODO-X5, Coupled File Rule 1)

DGX → Orin ckpt sync 스크립트 (구 sync_ckpt_dgx_to_datacollector.sh 의 후속) 는
차기 사이클 (07_leftarmVLA) 진입 시 필요 시 신규 작성.

---

## 참조

- 이관 결정 원본: `docs/work_flow/specs/06_dgx_absorbs_datacollector.md` §사용자 결정 사항 A
- 04 BACKLOG #11·#12·#13 처리: `docs/work_flow/specs/BACKLOG.md` 참조 (TODO-M2 에서 "완료(불요)" 마킹)
- DGX 학습 환경: `docs/storage/06_dgx_venv_setting.md`
