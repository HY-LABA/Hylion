# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-26 00:15 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 테스트 목표

`orin/scripts/run_teleoperate.sh` prod 검증 (재테스트) — dialout 그룹 설정 및 배포 완료 후 실장비 연결 상태에서 서브커맨드 정상 동작 확인

## DOD (완료 조건)

- `run_teleoperate.sh --help` 정상 출력
- `run_teleoperate.sh calibrate-follower` 실행 시 follower arm calibration 절차 진입
- `run_teleoperate.sh calibrate-leader` 실행 시 leader arm calibration 절차 진입
- `run_teleoperate.sh teleoperate` 실행 시 leader 움직임에 follower가 반응

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/`
- 하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) — Orin USB 연결 필요
- 사전 조건: `laba` 사용자 `dialout` 그룹 추가 완료, `run_teleoperate.sh` 배포 완료

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin` 접속 후 `source ~/smolvla/.venv/bin/activate` | `(.venv)` 활성화 | PASS | 2026-04-26: `VIRTUAL_ENV=/home/laba/smolvla/.venv`, Python 3.10.12 확인 |
| 2 | `ls /dev/ttyACM*` 확인 | `/dev/ttyACM0`, `/dev/ttyACM1` 존재 | PASS | 2026-04-26: `/dev/ttyACM0`, `/dev/ttyACM1` 존재, owner `root:dialout`, mode `crw-rw----` |
| 3 | `bash ~/smolvla/scripts/run_teleoperate.sh --help` | 서브커맨드 목록 출력 | PASS | 2026-04-26: `all`, `calibrate-follower`, `calibrate-leader`, `teleoperate` 출력 |
| 4 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` | follower calibration 절차 시작 | FAIL | 2026-04-26: `[1/4] Granting serial device permissions` 이후 `sudo chmod 666 /dev/ttyACM*`가 비대화형 SSH에서 sudo 비밀번호를 요구해 종료(code 1). follower calibration 진입 전 중단 |
| 5 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` | leader calibration 절차 시작 | FAIL | 2026-04-26: 동일하게 serial permission 단계의 sudo 비밀번호 요구로 종료(code 1). leader calibration 진입 전 중단 |
| 6 | `bash ~/smolvla/scripts/run_teleoperate.sh teleoperate` | teleoperate 루프 시작, leader 조작 시 follower 반응 | FAIL | 2026-04-26: 동일하게 serial permission 단계의 sudo 비밀번호 요구로 종료(code 1). teleoperate 루프 진입 전 중단. calibration 완료 후 동작은 미검증 |

## 테스트 메모

- 2026-04-26: `laba` 사용자는 `dialout` 그룹에 포함되어 있고 `/dev/ttyACM0`, `/dev/ttyACM1`도 `root:dialout` `crw-rw----` 상태라 일반 사용자 접근 조건은 충족된 것으로 보임.
- 2026-04-26: prod 스크립트가 매 서브커맨드 시작 시 `sudo chmod 666 /dev/ttyACM*`를 실행하므로 비대화형 SSH 테스트에서 calibration/teleoperate 진입 전에 차단됨.
- 스펙 업데이트 요청: dialout 그룹 기반 운용을 전제로 한다면 `run_teleoperate.sh`의 permission 단계가 sudo 비밀번호 없이 통과하도록 변경하거나, 이미 접근 가능한 포트에서는 chmod를 건너뛰는 요구사항을 스펙에 반영 필요.
