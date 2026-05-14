# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 13:02 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 04

## 테스트 목표

SO-ARM teleoperation 동작 검증.  
leader 팔을 움직일 때 follower 팔이 실시간으로 추종하는지 육안으로 확인한다.

## DOD (완료 조건)

leader 움직임에 follower가 실시간으로 추종함을 육안 확인.

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower (`/dev/ttyACM1`) + SO-101 leader (`/dev/ttyACM0`) 모두 연결 필요

## 사전 조건 (TODO-03 완료)

| 항목 | 경로 |
|---|---|
| follower calibration | `/home/laba/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json` |
| leader calibration | `/home/laba/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_awesome_leader_arm.json` |

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS: `ok` | SSH 접속 확인 |
| 2 | `ssh orin "source ~/smolvla/.venv/bin/activate && python -c 'import sys; print(sys.prefix)'"` | `/home/laba/smolvla/.venv` 포함 경로 | PASS: `/home/laba/smolvla/.venv` | venv 활성화 확인 |
| 3 | `ssh orin "ls /dev/ttyACM0 /dev/ttyACM1"` | 두 장치 모두 존재 | PASS: `/dev/ttyACM0`, `/dev/ttyACM1` | follower·leader 연결 확인 |
| 4 | `ssh orin "ls ~/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json"` | 파일 경로 출력 | PASS: `/home/laba/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json` | follower calibration 파일 확인 |
| 5 | `ssh orin "ls ~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_awesome_leader_arm.json"` | 파일 경로 출력 | PASS: `/home/laba/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_awesome_leader_arm.json` | leader calibration 파일 확인 |
| 6 | `ssh orin "bash -n ~/smolvla/scripts/run_teleoperate.sh && echo ok"` | `ok` 출력 | PASS: `ok` | 스크립트 문법 확인 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- ⚠️ VS Code Remote SSH 또는 Orin 직접 접속 터미널 사용. 육안 확인 필요. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | PASS: 프롬프트에 `(.venv)` 표시됨 | |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh teleoperate` 실행 | teleoperation 루프 시작, 에러 없이 동작 | PASS: 재실행 후 leader/follower 연결 및 `Teleop loop time: 16.75ms (60 Hz)` 출력 | follower=`/dev/ttyACM1`, leader=`/dev/ttyACM0`; 최초 시도에서는 follower `id_=3` `Torque_Enable` write 실패 |
| 3 | **[육안]** leader 팔의 각 관절을 천천히 움직임 | follower 팔이 실시간으로 동일하게 추종함 | PASS: 개발자 육안 확인 완료 | 응답 지연·토크 부족·미추종 관절 있으면 기록 |
| 4 | 추종 정상 확인 후 Ctrl+C 입력 | 에러 없이 정상 종료 | PASS: 개발자 확인 완료 | |
| 5 | 미추종 또는 이상 동작 관절이 있으면 관절명·증상을 여기에 기록 | — | NOTE: 지속적으로 follower `id_=3` 연결 오류가 관찰됨 | FAIL 시 calibration 재확인 또는 토크 설정 검토 |

## 테스트 메모

- 2026-04-27 13:05 KST: 개발자 직접 검증 중 `bash ~/smolvla/scripts/run_teleoperate.sh teleoperate` 단계에서 실패. leader는 연결되었으나 follower configure 중 `id_=3` 모터의 `Torque_Enable` write 응답이 없어 teleoperation 루프가 시작되지 않음.
- 2026-04-27 13:09 KST: 재실행 후 follower/leader 기존 calibration 파일 적용, teleoperation 루프가 60 Hz로 시작되었고 개발자 육안 추종 확인 완료. 단, follower `id_=3`에서 연결 오류가 지속적으로 존재한다고 메모함.
- 스펙 업데이트 요청: follower `id_=3` 모터 통신 진단 절차 또는 토크 활성화 실패 시 복구 절차를 TODO-04 검증 절차에 추가 필요.
