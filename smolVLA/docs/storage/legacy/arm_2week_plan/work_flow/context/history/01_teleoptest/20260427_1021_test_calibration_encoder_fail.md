# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 10:07 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03

## 테스트 목표

SO-ARM follower + leader calibration 파일 생성.  
이전 FAIL 원인(관절 전체 범위 미구동 → min=max=2047)을 해소하고 calibration 재실행.

## DOD (완료 조건)

follower + leader calibration 파일이 각각 생성되어 지정 경로에 저장됨.

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) 연결 필요

## ⚠️ Codex 주의사항

- `lerobot-calibrate`는 `input()` 호출 대화형 스크립트 → **비대화형 SSH에서 실행 금지** (EOFError 발생)
- 팔 관절 물리 조작이 필수이므로 개발자 직접 검증 전까지 calibration 명령 실행 불가
- **Codex 역할**: 사전 환경 확인(#1-5) + 개발자 완료 후 파일 생성 확인(#6-7)
- **#6-7은 개발자 직접 검증 완료 후에만 실행할 것**

## 발견 이슈 / 스펙 업데이트 요청

- 2026-04-27: `calibrate-follower`가 motor bus 연결 후 calibration 기록 단계까지 진입했으나, 팔을 직접 움직였음에도 일부 관절의 `Present_Position`이 2047 근처에서 변하지 않아 `min=max`로 실패함.
- 단순히 calibration 절차를 재시도하기 전에, **포트와 모터 encoder 값이 실제 하드웨어 움직임을 읽고 있는지 확인하는 진단 코드가 필요함**.
- 요청 진단 범위:
  - `/dev/serial/by-id/` 기준 follower/leader serial → `/dev/ttyACM*` 매핑 확인
  - follower 포트에서 motor id 1~6 각각의 `Present_Position` raw 값을 주기적으로 출력
  - 사용자가 각 관절을 하나씩 움직일 때 해당 motor id의 값이 실시간으로 변하는지 확인
  - 관절명(`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`)과 motor id(1~6) 매핑이 실제 조립/응답과 일치하는지 확인
- 이 진단이 PASS된 뒤 calibration을 다시 수행해야 함. 진단이 FAIL이면 포트 고정값(`/dev/ttyACM0`, `/dev/ttyACM1`), 케이블/전원, 모터 ID/조립 매핑을 먼저 수정해야 함.

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

### 사전 환경 확인 (개발자 직접 검증 전 실행)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS: `ok` | SSH 접속 확인 |
| 2 | `ssh orin "source ~/smolvla/.venv/bin/activate && python -c 'import sys; print(sys.prefix)'"` | `/home/laba/smolvla/.venv` 포함 경로 출력 | PASS: `/home/laba/smolvla/.venv` | venv 활성화 확인 |
| 3 | `ssh orin "ls /dev/ttyACM*"` | `/dev/ttyACM0`, `/dev/ttyACM1` 모두 존재 | PASS: `/dev/ttyACM0`, `/dev/ttyACM1` | follower·leader 장치 연결 확인 |
| 4 | `ssh orin "ls ~/smolvla/scripts/run_teleoperate.sh"` | 파일 경로 출력 (에러 없음) | PASS: `/home/laba/smolvla/scripts/run_teleoperate.sh` | 스크립트 배포 확인 |
| 5 | `ssh orin "bash -n ~/smolvla/scripts/run_teleoperate.sh"` | 출력 없음 (문법 에러 없음) | PASS: 출력 없음 | 스크립트 문법 검증 |

### calibration 파일 생성 결과 확인 (개발자 직접 검증 완료 후 실행)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 6 | `ssh orin "find ~/.cache/huggingface/lerobot/calibration -name '*.json' 2>/dev/null || find ~/smolvla -name '*.json' -path '*/calibration/*' 2>/dev/null"` | follower·leader calibration JSON 파일 2개 이상 출력 | NOT RUN: 개발자 직접 검증 완료 전 단계라 실행 보류 | 생성 경로는 lerobot 기본값 또는 스크립트 지정 경로 |
| 7 | `ssh orin "cat \$(find ~/.cache/huggingface/lerobot/calibration -name '*follower*.json' 2>/dev/null | head -1)"` | JSON 내용 출력, min ≠ max (각 관절 범위 존재) | NOT RUN: 개발자 직접 검증 완료 전 단계라 실행 보류 | 관절 범위 정상 기록 여부 확인 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- ⚠️ VS Code Remote SSH 또는 Orin 직접 접속 터미널 사용. 일반 SSH 명령행 불가. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin Remote SSH 터미널에서 `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | | |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` 실행 | calibration 절차 시작, 프롬프트 표시 | | |
| 3 | **[물리]** 프롬프트에 따라 follower 팔 각 관절을 **전체 가동 범위**로 천천히 구동 (min→max→min) | 관절당 min·max 값이 다르게 기록됨 | | 이전 FAIL 원인 해소 핵심 단계 |
| 4 | 각 관절 구동 후 Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | | 에러 없이 종료 |
| 5 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` 실행 | calibration 절차 시작, 프롬프트 표시 | | |
| 6 | **[물리]** leader 팔 각 관절을 **전체 가동 범위**로 천천히 구동 (min→max→min) | 관절당 min·max 값이 다르게 기록됨 | | |
| 7 | 각 관절 구동 후 Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | | 에러 없이 종료 |
| 8 | Codex 검증 #6 실행 (생성 파일 목록 확인) | follower·leader JSON 파일 각 1개 이상 존재 | | Codex에 위임 가능 |
