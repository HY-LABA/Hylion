# smolVLA 환경 요구사항 (arm_2week_plan 기준)

> 기준 문서: `smolVLA/arm_2week_plan.md`  
> 작성일: 2026-04-21  
> 목적: smolVLA 작업을 위한 요구사항 정의 문서
- 개발 환경에 대한 요구사항을 간단히 정리
- storage 하위 폴더와 파일들의 네비게이션 역할을 하는 파일

## 1) 문서 역할

- 이 문서 (`01`): 요구사항 (What is required)
- 하드웨어 실측/보유 현황 (`02`): `smolVLA/docs/storage/02_hardware.md`
- 소프트웨어 실측/설정 현황 (`03`): `smolVLA/docs/storage/03_software.md`
- 개발 네트워크 설정 (`04`): `smolVLA/docs/storage/04_devnetwork.md`
- Orin 환경 세팅 기록 (`05`): `smolVLA/docs/storage/05_orin_venv_setting.md`
- 장치 스냅샷 점검: `smolVLA/docs/storage/devices_snapshot/` — `run_snapshots.sh`, `collect_snapshot.sh`
- lerobot upstream 추적: `smolVLA/docs/storage/lerobot_upstream_check/`
  - `99_lerobot_upstream_Tracking.md` — 동기화 이력
  - `01_compatibility_check.md` — 의존성 충돌 점검 기록 (Python 버전, 신규 문법)
  - `02_orin_pyproject_diff.md` — upstream vs orin/pyproject.toml 변경 이력
  - `03_orin_lerobot_diff.md` — upstream vs orin/lerobot/ 코드 변경 이력
  - `check_update_diff.sh` — 점검 스크립트

## 2) 기본 요구사항

- 개발 OS는 Ubuntu 네이티브를 사용한다.
- 로봇 문맥은 SO-ARM(SO-100/SO-101)을 기준으로 한다.
- 2주차 목표는 Orin에서 SO-ARM + smolVLA 추론 동작 확인이다.

## 3) 하드웨어 요구사항

### A. 로봇/입출력

- SO-ARM follower, leader 구성 가능해야 한다.
- 모터는 Feetech STS3215 계열(BOM 기어비 포함) 사용을 기본으로 한다.
- ST/SC 시리얼 버스 서보 드라이버 보드(팔 1대당 1개)가 필요하다.
- 카메라 1대 이상을 연결 가능해야 한다.

### B. 컴퓨팅

- 개발용 Ubuntu PC 1대 이상이 필요하다.
- 배포/실행용 Jetson Orin 계열 장치 1대가 필요하다.
- 루트/데이터 저장을 위한 SSD 기반 스토리지가 필요하다.

## 4) 소프트웨어 요구사항

- Python: Orin 실행 환경 `3.10` / upstream lerobot 기준 `>=3.12` (버전 불일치 존재)
- 의존성 그룹: Orin 실행 — `smolvla`, `feetech` / 학습/개발 PC — `smolvla`, `training`, `feetech`
- SSH 원격 접속(Orin)이 가능해야 한다.

> Python 버전 불일치로 인한 구체적인 위험 분석 및 점검 이력:
> `docs/storage/lerobot_upstream_check/01_compatibility_check.md`

## 5) 근거 문서

- `docs/source/so101.mdx:20`
- `docs/source/so101.mdx:33`
