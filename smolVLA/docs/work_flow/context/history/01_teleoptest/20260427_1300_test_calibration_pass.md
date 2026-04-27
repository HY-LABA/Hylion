# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 12:51 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03

## 테스트 목표

SO-ARM follower + leader calibration 파일 생성.  
이전 FAIL 원인(`run_teleoperate.sh` 포트 역전) 수정 완료 후 재실행.  
확정 포트: **follower=`/dev/ttyACM1`**, **leader=`/dev/ttyACM0`**

## DOD (완료 조건)

follower + leader calibration 파일이 각각 생성되어 지정 경로에 저장됨.

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower (`/dev/ttyACM1`) + SO-101 leader (`/dev/ttyACM0`) 연결 필요

## 사전 확인 (포트 수정 내역)

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| `FOLLOWER_PORT` | `/dev/ttyACM0` | `/dev/ttyACM1` |
| `LEADER_PORT` | `/dev/ttyACM1` | `/dev/ttyACM0` |

배포 완료: 2026-04-27 12:51

## ⚠️ Codex 주의사항

- `lerobot-calibrate`는 `input()` 호출 대화형 스크립트 → **비대화형 SSH 실행 금지**
- 물리 조작(관절 전체 범위 구동) 필수 → 개발자 직접 수행
- **Codex 역할**: 사전 환경·포트 수정 확인(#1-6) + 개발자 완료 후 파일 생성 확인(#7-8)
- **#7-8은 개발자 직접 검증 완료 후에만 실행할 것**

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

### 사전 환경 확인 (개발자 직접 검증 전 실행)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS: `ok` 출력 | SSH 접속 확인 |
| 2 | `ssh orin "source ~/smolvla/.venv/bin/activate && python -c 'import sys; print(sys.prefix)'"` | `/home/laba/smolvla/.venv` 포함 경로 | PASS: `/home/laba/smolvla/.venv` 출력 | venv 활성화 확인 |
| 3 | `ssh orin "ls /dev/ttyACM0 /dev/ttyACM1"` | 두 장치 모두 존재 | PASS: `/dev/ttyACM0`, `/dev/ttyACM1` 존재 | follower·leader 연결 확인 |
| 4 | `ssh orin "ls ~/smolvla/scripts/run_teleoperate.sh"` | 파일 경로 출력 | PASS: `/home/laba/smolvla/scripts/run_teleoperate.sh` 출력 | 스크립트 배포 확인 |
| 5 | `ssh orin "bash -n ~/smolvla/scripts/run_teleoperate.sh && echo ok"` | `ok` 출력 | PASS: `ok` 출력 | 문법 검증 |
| 6 | `ssh orin "grep FOLLOWER_PORT ~/smolvla/scripts/run_teleoperate.sh"` | `FOLLOWER_PORT="/dev/ttyACM1"` | PASS: `FOLLOWER_PORT="/dev/ttyACM1"` 확인 | 포트 수정 배포 반영 확인 |

### calibration 파일 생성 확인 (개발자 직접 검증 완료 후 실행)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 7 | `ssh orin "find ~/.cache/huggingface/lerobot/calibration -name '*.json' 2>/dev/null || find ~/smolvla -name '*.json' -path '*/calibration/*' 2>/dev/null"` | follower·leader JSON 파일 2개 이상 출력 | PASS: leader/follower JSON 2개 출력 | 생성 경로 확인 |
| 8 | `ssh orin "cat \$(find ~/.cache/huggingface/lerobot/calibration -name '*follower*.json' 2>/dev/null | head -1)"` | JSON 내용 출력, min ≠ max | PASS: follower JSON 출력, 주요 관절 `range_min` ≠ `range_max` 확인 | 관절 범위 정상 기록 여부 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- ⚠️ VS Code Remote SSH 또는 Orin 직접 접속 터미널 사용. 물리 조작 필요. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | PASS: `(.venv)` 프롬프트 확인 | |
| 2 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-follower` 실행 | calibration 절차 시작, 프롬프트 표시 | PASS: follower calibration 시작 확인 | follower 포트: `/dev/ttyACM1` |
| 3 | **[물리]** 프롬프트에 따라 follower 팔 각 관절을 **min→max→min 전체 범위**로 천천히 구동 | 관절당 min·max 값이 다르게 기록됨 | PASS: shoulder_pan/lift, elbow_flex, wrist_flex, gripper min·max 기록 확인 | encoder 정상 확인됨(TODO-03a) — 충분히 움직일 것 |
| 4 | Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | PASS: `/home/laba/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json` 저장 확인 | 에러 없이 종료 |
| 5 | `bash ~/smolvla/scripts/run_teleoperate.sh calibrate-leader` 실행 | calibration 절차 시작, 프롬프트 표시 | PASS: leader calibration 시작 확인 | leader 포트: `/dev/ttyACM0` |
| 6 | **[물리]** leader 팔 각 관절을 **min→max→min 전체 범위**로 천천히 구동 | 관절당 min·max 값이 다르게 기록됨 | PASS: shoulder_pan/lift, elbow_flex, wrist_flex, gripper min·max 기록 확인 | |
| 7 | Enter 입력하여 다음 단계 진행, 최종 완료 확인 | `calibration saved` 또는 동등한 완료 메시지 | PASS: `/home/laba/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_awesome_leader_arm.json` 저장 확인 | 에러 없이 종료 |
| 8 | Codex 검증 #7 실행 (생성 파일 목록 확인) | follower·leader JSON 파일 각 1개 이상 존재 | PASS: follower·leader JSON 각 1개 존재 | Codex에 위임 가능 |
