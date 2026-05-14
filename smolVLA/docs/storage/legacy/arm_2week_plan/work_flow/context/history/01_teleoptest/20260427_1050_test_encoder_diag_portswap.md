# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 10:39 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03a

## 테스트 목표

motor encoder 진단 스크립트 prod 검증.
먼저 `lerobot-find-port` 레퍼런스 절차처럼 leader/follower MotorsBus 포트를 각각 식별한 뒤,
`orin/calibration/diagnose_motor_encoder.py` 를 각 포트에서 실행하여 두 팔 모두 관절을 손으로 움직일 때 `Present_Position` Raw/Delta 값이 실시간으로 변하는지 확인한다.

## 확인된 문제

- 2026-04-27 개발자 직접 확인: 기존 테스트에서 leader arm 포트를 follower arm 포트로 오인했다.
- `/dev/ttyACM0`, `/dev/ttyACM1` 번호만으로 leader/follower를 추정하지 않는다.
- 각 암의 USB를 직접 뽑는 방식으로 포트를 식별한 뒤, 식별된 포트 기준으로 진단을 진행한다.

## DOD (완료 조건)

1. leader/follower 각각의 MotorsBus 포트가 물리 분리 방식으로 식별됨
2. `/dev/serial/by-id/` 기준 포트 매핑이 출력됨
3. leader/follower 각각에서 motor id 1~6 `Present_Position` 값이 1Hz 주기로 테이블 출력됨
4. leader/follower 각각에서 각 관절을 손으로 움직일 때 해당 motor id의 `Raw` / `Delta` 값이 변함
5. Ctrl+C 로 정상 종료됨

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower + leader 연결 필요

## 포트 식별 기록

| Arm | 식별 절차 | 확인된 포트 | 결과 | 비고 |
|---|---|---|---|---|
| follower | `lerobot-find-port` 실행 -> follower USB 분리 -> Enter -> 포트 기록 -> 재연결 | | 미실행 | `/dev/ttyACM*` 번호 추정 금지 |
| leader | `lerobot-find-port` 실행 -> leader USB 분리 -> Enter -> 포트 기록 -> 재연결 | | 미실행 | `/dev/ttyACM*` 번호 추정 금지 |

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS (`ok`) | SSH 접속 확인 |
| 2 | `ssh orin "source ~/smolvla/.venv/bin/activate && python -c 'import sys; print(sys.prefix)'"` | `/home/laba/smolvla/.venv` 포함 경로 출력 | PASS (`/home/laba/smolvla/.venv`) | venv 활성화 확인 |
| 3 | `ssh orin "ls /dev/ttyACM0"` | `/dev/ttyACM0` 출력 (에러 없음) | PASS (`/dev/ttyACM0`) | 장치 연결 확인. follower 여부는 직접 포트 식별 전까지 미확정 |
| 4 | `ssh orin "ls ~/smolvla/calibration/diagnose_motor_encoder.py"` | 파일 경로 출력 (에러 없음) | PASS (`/home/laba/smolvla/calibration/diagnose_motor_encoder.py`) | 배포 파일 존재 확인 |
| 5 | `ssh orin "source ~/smolvla/.venv/bin/activate && python -m py_compile ~/smolvla/calibration/diagnose_motor_encoder.py && echo ok"` | `ok` 출력 (문법 에러 없음) | PASS (`ok`) | Orin에서 문법 검증 |
| 6 | `ssh orin "ls -la /dev/serial/by-id/ 2>/dev/null \|\| echo 'no serial/by-id entries'"` | serial/by-id symlink 목록 출력 | PASS (`ttyACM0`, `ttyACM1` symlink 확인) | `ttyACM0`: `5B42138566`, `ttyACM1`: `5B42138563`; arm 역할은 직접 포트 식별 필요 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- VS Code Remote SSH 또는 Orin 직접 접속 터미널 사용. 물리 조작 필요. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin Remote SSH 터미널에서 `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | 미실행 | 개발자 직접 터미널 확인 필요 |
| 2 | `lerobot-find-port` 실행 -> follower USB 분리 -> Enter -> 출력된 포트 기록 -> follower USB 재연결 | follower MotorsBus 포트가 1개만 감지됨 | 미실행 | 예: `The port of this MotorsBus is '/dev/ttyACM?'` |
| 3 | `lerobot-find-port` 실행 -> leader USB 분리 -> Enter -> 출력된 포트 기록 -> leader USB 재연결 | leader MotorsBus 포트가 1개만 감지됨 | 미실행 | follower와 leader 포트가 서로 다르게 기록되어야 함 |
| 4 | `python ~/smolvla/calibration/diagnose_motor_encoder.py --port <FOLLOWER_PORT>` 실행 | `/dev/serial/by-id/` 매핑 출력 후 follower Joint/ID/Raw/Delta 테이블 루프 시작 | 미실행 | `<FOLLOWER_PORT>`는 2번에서 식별한 포트 |
| 5 | **[물리/follower]** follower 6개 관절(`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`)을 순서대로 천천히 움직임 | 각 motor id 1~6의 `Raw` / `Delta` 값이 변함 | 미실행 | 값이 고정이면 motor id·관절명·증상 기록 |
| 6 | Ctrl+C 입력 | 에러 없이 정상 종료 (disconnect 메시지 또는 프롬프트 복귀) | 미실행 | follower 진단 종료 |
| 7 | `python ~/smolvla/calibration/diagnose_motor_encoder.py --port <LEADER_PORT>` 실행 | `/dev/serial/by-id/` 매핑 출력 후 leader Joint/ID/Raw/Delta 테이블 루프 시작 | 미실행 | `<LEADER_PORT>`는 3번에서 식별한 포트 |
| 8 | **[물리/leader]** leader 6개 관절(`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`)을 순서대로 천천히 움직임 | 각 motor id 1~6의 `Raw` / `Delta` 값이 변함 | 미실행 | 값이 고정이면 motor id·관절명·증상 기록 |
| 9 | Ctrl+C 입력 | 에러 없이 정상 종료 (disconnect 메시지 또는 프롬프트 복귀) | 미실행 | leader 진단 종료 |
| 10 | 포트 오인 또는 관절 중 값이 변하지 않은 항목이 있으면 motor id·관절명·증상을 여기에 기록 | — | 미해당 | FAIL 시 TODO-03a 재진단 필요 |
