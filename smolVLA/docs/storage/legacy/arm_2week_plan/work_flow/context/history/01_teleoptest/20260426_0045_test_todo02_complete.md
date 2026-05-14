# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-26 00:40 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 테스트 목표

`run_teleoperate.sh` prod 최종 검증 — ImportError 수정(bi_openarm_follower 등 제거) 및 배포 완료 후 calibrate·teleoperate 서브커맨드 정상 동작 확인

## DOD (완료 조건)

- `run_teleoperate.sh calibrate-follower` 실행 시 follower arm calibration 절차 진입
- `run_teleoperate.sh calibrate-leader` 실행 시 leader arm calibration 절차 진입
- `run_teleoperate.sh teleoperate` 실행 시 leader 움직임에 follower가 반응

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC → `ssh orin` → Orin (`laba@ubuntu`)
- **Orin 실제 경로**: `~/smolvla/scripts/run_teleoperate.sh` (배포 구조: `orin/` → `~/smolvla/`)
- 하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) — Orin USB 연결 필요
- 사전 조건: `laba` dialout 그룹 완료, sudo chmod 제거 완료, bi_openarm_follower ImportError 수정 완료

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin` + `source ~/smolvla/.venv/bin/activate` | `(.venv)` 활성화 | PASS | `USER=laba HOST=ubuntu`, `VIRTUAL_ENV=/home/laba/smolvla/.venv`, Python 3.10.12 확인 |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh --help` | 서브커맨드 목록 출력 | PASS | `all`, `calibrate-follower`, `calibrate-leader`, `teleoperate` 출력 확인 |
| 3 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` | sudo 요구 없이 calibration 절차 진입 | PASS | ImportError 없이 `/dev/ttyACM0` follower 연결 후 calibration 프롬프트 진입. 비대화형 SSH라 `input()`에서 `EOFError`로 종료 |
| 4 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` | sudo 요구 없이 calibration 절차 진입 | PASS | ImportError 없이 `/dev/ttyACM1` leader 연결 후 calibration 프롬프트 진입. 비대화형 SSH라 `input()`에서 `EOFError`로 종료 |
| 5 | `bash ~/smolvla/scripts/run_teleoperate.sh teleoperate` | teleoperate 루프 시작, leader 조작 시 follower 반응 | BLOCKED | teleoperate 시작 후 leader calibration 파일 불일치/부재로 자동 calibration 프롬프트 진입. 비대화형 SSH라 `EOFError` 종료; 실제 follower 반응은 calibration 완료 후 대화형 세션에서 재검증 필요 |
