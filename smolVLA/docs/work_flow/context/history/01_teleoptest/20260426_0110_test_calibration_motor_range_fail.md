# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-26 00:51 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03

## 테스트 목표

SO-ARM calibration 파일 생성 — follower·leader 각각 calibration 절차를 실행하여 파일이 지정 경로에 저장되는지 확인

## DOD (완료 조건)

- follower calibration 파일 생성: `~/.cache/huggingface/lerobot/calibration/robots/` 하위에 파일 존재
- leader calibration 파일 생성: `~/.cache/huggingface/lerobot/calibration/teleoperators/` 하위에 파일 존재

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC → `ssh orin` → Orin (`laba@ubuntu`) — **대화형 세션 필요** (calibration은 input() 호출)
- Orin 스크립트 경로: `~/smolvla/scripts/run_teleoperate.sh`
- 하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) — Orin USB 연결 및 전원 공급 필요

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin` + `source ~/smolvla/.venv/bin/activate` | `(.venv)` 활성화 | PASS | Orin SSH 접속 및 `(.venv)` 프롬프트 확인 |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` 실행 후 calibration 절차 진행 | 프롬프트 안내에 따라 follower calibration 완료 | FAIL | `/dev/ttyACM0` 연결 후 range 기록 단계에서 모든 관절 min/max가 2047로 동일하여 `ValueError: Some motors have the same min and max values` 발생 |
| 3 | `ls ~/.cache/huggingface/lerobot/calibration/robots/` | follower calibration 파일 존재 | FAIL | `robots/so_follower/` 디렉터리는 있으나 `find ... -type f` 결과 파일 없음 |
| 4 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` 실행 후 calibration 절차 진행 | 프롬프트 안내에 따라 leader calibration 완료 | NOT RUN | follower calibration 실패 및 물리 range 조작 확인 필요로 중단 |
| 5 | `ls ~/.cache/huggingface/lerobot/calibration/teleoperators/` | leader calibration 파일 존재 | FAIL | `teleoperators/so_leader/` 디렉터리는 있으나 `find ... -type f` 결과 파일 없음 |
