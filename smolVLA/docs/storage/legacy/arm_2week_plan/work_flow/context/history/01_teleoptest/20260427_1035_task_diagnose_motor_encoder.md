# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 10:24 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03a

## 작업 목표

motor encoder 진단 스크립트 구현.  
SO-ARM follower calibration이 2회 연속 실패(`min=max=2047`)한 원인을 규명하기 위해, 관절을 손으로 움직일 때 `Present_Position` 값이 실제로 변하는지 확인하는 진단 스크립트를 작성한다.

## DOD (완료 조건)

`orin/calibration/diagnose_motor_encoder.py` 가 아래 기능을 갖춰 작성됨:
1. `/dev/serial/by-id/` 기준 follower/leader serial → `/dev/ttyACM*` 매핑 출력
2. 지정 포트에서 motor id 1~6 `Present_Position` raw 값을 1Hz 주기로 출력
3. 각 관절 수동 구동 시 해당 motor id 값이 변하는지 터미널에서 육안 확인 가능
4. `bash -n` 또는 `python -m py_compile` 검증 통과

## 구현 대상

- `orin/calibration/diagnose_motor_encoder.py` (신규)
  - CLI 인자: `--port /dev/ttyACM0` (follower 기본값)
  - motor id 1~6 루프 → `Present_Position` 읽기 → 테이블 형식 출력 (관절명 포함)
  - 관절명↔motor id 매핑: `shoulder_pan=1, shoulder_lift=2, elbow_flex=3, wrist_flex=4, wrist_roll=5, gripper=6`
  - Ctrl+C 로 정상 종료

## 참고 레퍼런스

구현 전 반드시 아래에서 모터 read API 패턴을 확인할 것:
- `docs/reference/lerobot/` — HuggingFace lerobot upstream (특히 `lerobot/robots/`, `lerobot/motors/` 하위)
- `docs/reference/seeed-lerobot/` — Seeed lerobot fork

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only, upstream submodule)
- `orin/lerobot/` 기존 파일 — 수정이 필요하면 반드시 사유 명시 후 확인
- `orin/scripts/run_teleoperate.sh` — 이 작업과 무관

## 업데이트
<!-- Copilot이 작업 완료 후 여기에 기록:
- 변경한 내용
- 검증 방법 및 결과 (python -m py_compile, 실행 출력 샘플 등)
- Orin 배포 및 prod 검증 필요 여부 -->

- 변경한 내용
  - `orin/calibration/diagnose_motor_encoder.py` 신규 작성.
  - `/dev/serial/by-id/`의 symlink를 순회해 serial/by-id entry -> 실제 `/dev/ttyACM*` 해석 결과를 테이블로 출력하도록 구현.
  - CLI 인자 `--port`(기본 `/dev/ttyACM0`) 지원.
  - SO-ARM 관절명↔ID 매핑(1~6) 고정 후 `FeetechMotorsBus` 연결, `sync_read("Present_Position", normalize=False)`로 raw 값을 1Hz(기본) 루프 출력.
  - 출력 테이블에 `Joint`, `ID`, `Raw`, `Delta`를 포함해 관절 수동 구동 시 값 변화 여부를 즉시 육안 확인 가능하게 구성.
  - `Ctrl+C` 종료 처리 및 disconnect 정리 로직 추가.

- 검증 방법 및 결과
  - 정적 검증: `python -m py_compile orin/calibration/diagnose_motor_encoder.py` PASS
  - 실행 검증: 하드웨어 연결이 필요한 항목으로, Orin에서 follower 포트 연결 상태에서 실기 확인 필요.

- Orin 배포 및 prod 검증 필요 여부
  - 필요. Orin에서 `--port /dev/ttyACM0`로 실행 후 관절별 `Raw` 값 변화 확인 필요.

## 배포
- 일시: 2026-04-27 10:35
- 결과: 완료 (`orin/calibration/diagnose_motor_encoder.py` → `orin:/home/laba/smolvla/calibration/`)
