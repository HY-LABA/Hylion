# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 10:53 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 03a

## 테스트 목표

motor encoder 진단 스크립트 prod 검증 (포트 재식별 포함).  
이전 테스트에서 포트 역전 발견(`/dev/ttyACM0`=leader serial, `/dev/ttyACM1`=follower serial).  
`lerobot-find-port`로 follower/leader 포트를 물리 분리 방식으로 재확정한 뒤,  
`diagnose_motor_encoder.py`로 각 팔 encoder 응답 여부를 진단한다.

## DOD (완료 조건)

1. `lerobot-find-port`로 follower/leader 포트가 각각 확정됨
2. follower 포트에서 motor id 1~6 Raw/Delta 값이 관절 수동 구동 시 변함
3. leader 포트에서 motor id 1~6 Raw/Delta 값이 관절 수동 구동 시 변함
4. 두 팔 모두 Ctrl+C 정상 종료됨

## 환경

Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
하드웨어: SO-101 follower + leader 모두 연결 필요

## 사전 정보 (이전 Codex 확인)

| Serial ID | 현재 ttyACM 번호 | TODO-02 기록 역할 | 비고 |
|---|---|---|---|
| `5B42138563` | `/dev/ttyACM1` | follower | USB 연결 순서 변경으로 번호 역전됨 |
| `5B42138566` | `/dev/ttyACM0` | leader | USB 연결 순서 변경으로 번호 역전됨 |

→ `lerobot-find-port`로 재확인 후 결과를 아래 포트 식별 기록에 채운다.

## ⚠️ Codex 주의사항

- `lerobot-find-port`는 `input()` 호출 대화형 스크립트 → **비대화형 SSH 실행 금지**
- `diagnose_motor_encoder.py`는 하드웨어 연결 + 물리 조작 필요 → 개발자 직접 수행
- **Codex 역할**: 사전 환경 확인(#1-5)만 실행. 포트 식별·encoder 진단은 개발자 완료 후 결과 기록 확인

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS: `ok` | SSH 접속 확인 |
| 2 | `ssh orin "source ~/smolvla/.venv/bin/activate && which lerobot-find-port"` | `/home/laba/smolvla/.venv/bin/lerobot-find-port` 출력 | PASS: `/home/laba/smolvla/.venv/bin/lerobot-find-port` | lerobot-find-port 설치 확인 |
| 3 | `ssh orin "ls /dev/ttyACM0 /dev/ttyACM1"` | 두 장치 모두 존재 | PASS: `/dev/ttyACM0`, `/dev/ttyACM1` 존재 | follower·leader 연결 확인 |
| 4 | `ssh orin "ls ~/smolvla/calibration/diagnose_motor_encoder.py"` | 파일 경로 출력 | PASS: `/home/laba/smolvla/calibration/diagnose_motor_encoder.py` | 진단 스크립트 배포 확인 |
| 5 | `ssh orin "ls -la /dev/serial/by-id/"` | serial/by-id symlink 목록 출력 (5B42138563, 5B42138566 포함) | PASS: `5B42138563 -> ../../ttyACM1`, `5B42138566 -> ../../ttyACM0` | 포트 매핑 사전 확인 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- ⚠️ VS Code Remote SSH 또는 Orin 직접 접속 터미널 사용 -->

### 포트 식별 기록
<!-- 아래 표를 채운 뒤 진단 단계로 진행 -->

| Arm | 확인된 포트 | Serial ID |
|---|---|---|
| follower | `/dev/ttyACM1` | `5B42138563` |
| leader | `/dev/ttyACM0` | `5B42138566` |

### 검증 단계

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | PASS: 프롬프트에 `(.venv)` 표시됨 | |
| 2 | `lerobot-find-port` 실행 → follower USB 분리 → Enter → 포트 기록 → 재연결 | follower 포트 1개 출력 (예: `/dev/ttyACM?`) | PASS: `/dev/ttyACM1` 출력 | 포트 식별 기록 follower 행 반영 |
| 3 | `lerobot-find-port` 실행 → leader USB 분리 → Enter → 포트 기록 | leader 포트 1개 출력 | PASS: `/dev/ttyACM0` 출력 | 포트 식별 기록 leader 행 반영 |
| 4 | `python ~/smolvla/calibration/diagnose_motor_encoder.py --port <FOLLOWER_PORT>` 실행 | serial/by-id 매핑 출력 후 Joint/ID/Raw/Delta 테이블 루프 시작 | PASS: `/dev/ttyACM1` 연결, serial/by-id 매핑 및 Raw/Delta 테이블 출력 시작 | `<FOLLOWER_PORT>`는 `/dev/ttyACM1` |
| 5 | **[물리/follower]** 관절 6개(`shoulder_pan`→`shoulder_lift`→`elbow_flex`→`wrist_flex`→`wrist_roll`→`gripper`)를 순서대로 천천히 움직임 | 각 motor id Raw/Delta 값이 변함 | PASS: id 1~6 모두 Raw/Delta 변화 확인 | 예: id1 `2037→2041`, id2 `883→1467`, id3 `3038→2169`, id4 `2897→1693/2990`, id5 `2156→2159`, id6 `2011→2412/1965` |
| 6 | Ctrl+C 입력 | 에러 없이 정상 종료 | PASS: `Stopped by user (Ctrl+C).` 출력 후 정상 종료 | follower 진단 완료 |
| 7 | `python ~/smolvla/calibration/diagnose_motor_encoder.py --port <LEADER_PORT>` 실행 | serial/by-id 매핑 출력 후 Joint/ID/Raw/Delta 테이블 루프 시작 | PASS: `/dev/ttyACM0` 연결, serial/by-id 매핑 및 Raw/Delta 테이블 출력 시작 | `<LEADER_PORT>`는 `/dev/ttyACM0` |
| 8 | **[물리/leader]** 관절 6개를 순서대로 천천히 움직임 | 각 motor id Raw/Delta 값이 변함 | PASS: id 1~6 모두 Raw/Delta 변화 확인 | 예: id1 `1988→1883`, id2 `2047→3085`, id3 `2046→1241`, id4 `2029→1227/2027`, id5 `1863→1864`, id6 `2047→3015/2184` |
| 9 | Ctrl+C 입력 | 에러 없이 정상 종료 | PASS: `Stopped by user (Ctrl+C).` 출력 후 정상 종료 | leader 진단 완료 |

## 테스트 피드백 / 스펙 업데이트 요청

- 현재 흐름은 `lerobot-find-port`로 포트를 식별한 뒤 사용자가 포트값을 직접 기록하고, 다시 `diagnose_motor_encoder.py --port <PORT>`에 수동 입력해야 한다.
- 다음 개선에서는 `포트 식별 → 포트값 저장 → 해당 포트로 encoder 진단 실행`이 한 명령어에서 이어지도록 통합하는 것이 좋다.
- 기대 효과: `/dev/ttyACM*` 번호 역전·재연결 상황에서 수동 복사/입력 실수를 줄이고, follower/leader 진단 절차를 더 안정적으로 반복할 수 있다.
