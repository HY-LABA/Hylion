# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 09:57 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03

## 테스트 목표

SO-ARM follower + leader calibration 파일 생성.  
이전 FAIL 원인(관절 전체 범위 미구동 → min=max=2047)을 해소하고 calibration 재실행.

## DOD (완료 조건)

follower + leader calibration 파일이 각각 생성되어 지정 경로에 저장됨.

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower (`/dev/ttyACM0`) + SO-101 leader (`/dev/ttyACM1`) 연결 필요

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->
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
| 6 | `ssh orin "find ~/.cache/huggingface/lerobot/calibration -name '*.json' 2>/dev/null || find ~/smolvla -name '*.json' -path '*/calibration/*' 2>/dev/null"` | follower·leader calibration JSON 파일 2개 이상 출력 | FAIL: 출력 없음 | 생성 경로는 lerobot 기본값 또는 스크립트 지정 경로 |
| 7 | `ssh orin "cat \$(find ~/.cache/huggingface/lerobot/calibration -name '*follower*.json' 2>/dev/null | head -1)"` | JSON 내용 출력, min ≠ max (각 관절 범위 존재) | FAIL: follower calibration JSON 경로 없음, 출력 없음 | 관절 범위 정상 기록 여부 확인 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin Remote SSH 터미널에서 `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | 미실행: 개발자 Remote SSH 터미널 직접 검증 필요 | |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` 실행 | calibration 절차 시작, 프롬프트 표시 | 미실행: 대화형 calibration 필요 | |
| 3 | **[물리]** 프롬프트에 따라 follower 팔 각 관절을 **전체 가동 범위**로 천천히 구동 (min→max→min) | 관절당 min·max 값이 다르게 기록됨 | 미실행: 물리 조작 필요 | 이전 FAIL 원인 해소 핵심 단계 |
| 4 | 각 관절 구동 후 Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | 미실행: follower calibration 미수행 | 에러 없이 종료 |
| 5 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` 실행 | calibration 절차 시작, 프롬프트 표시 | 미실행: 대화형 calibration 필요 | |
| 6 | **[물리]** leader 팔 각 관절을 **전체 가동 범위**로 천천히 구동 | 관절당 min·max 값이 다르게 기록됨 | 미실행: 물리 조작 필요 | |
| 7 | 각 관절 구동 후 Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | 미실행: leader calibration 미수행 | 에러 없이 종료 |
| 8 | Codex 검증 #6 실행 (생성 파일 목록 확인) | follower·leader JSON 파일 각 1개 이상 존재 | FAIL: Codex 검증 #6 출력 없음 | Codex에 위임 가능 |
