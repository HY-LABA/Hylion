# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-25 23:27 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 테스트 목표

`orin/scripts/run_teleoperate.sh` prod 검증 — 실장비 연결 상태에서 calibrate·teleoperate 서브커맨드가 정상 동작하는지 확인

## DOD (완료 조건)

- `run_teleoperate.sh calibrate-follower` 실행 시 follower arm calibration 절차 진입
- `run_teleoperate.sh calibrate-leader` 실행 시 leader arm calibration 절차 진입
- `run_teleoperate.sh teleoperate` 실행 시 leader 움직임에 follower가 반응

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/`
- 하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) — Orin USB 연결 필요

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin` 접속 후 `source ~/smolvla/.venv/bin/activate` | `(.venv)` 활성화 | PASS | Orin 접속 성공. `VIRTUAL_ENV=/home/laba/smolvla/.venv`, Python 3.10.12 확인 |
| 2 | `sudo chmod 666 /dev/ttyACM*` | 권한 부여 오류 없음 | FAIL | `sudo: a password is required`. 현재 `/dev/ttyACM0`, `/dev/ttyACM1`는 `root:dialout`, `crw-rw----` |
| 3 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh --help` | 서브커맨드 목록 출력 | FAIL | `/home/laba/smolvla/orin/scripts/run_teleoperate.sh: No such file or directory` |
| 4 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh calibrate-follower` | follower calibration 절차 시작 (프롬프트 또는 안내 출력) | FAIL | 스크립트 미존재로 실행 불가 |
| 5 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh calibrate-leader` | leader calibration 절차 시작 | FAIL | 스크립트 미존재로 실행 불가 |
| 6 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh teleoperate` | teleoperate 루프 시작, leader 조작 시 follower 반응 | FAIL | 스크립트 미존재 및 calibration 미완료로 실행 불가 |
