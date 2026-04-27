# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-25 23:00 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 테스트 목표

SO-ARM 포트 탐지 및 config 수정 — follower/leader 각각의 `/dev/ttyACM*` 포트를 Orin에서 식별하고, config 파일에 반영됨을 확인

## DOD (완료 조건)

- follower·leader `/dev/ttyACM*` 포트가 각각 식별됨
- `orin/lerobot/robots/so_follower/config_so_follower.py` — port 필드가 실제 포트로 반영됨
- `orin/lerobot/teleoperators/so_leader/config_so_leader.py` — port 필드가 실제 포트로 반영됨

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/`
- 하드웨어: SO-101 follower (12V) + SO-101 leader (7.4V) — Orin USB 연결 필요

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC에서 `ssh orin` 접속 | 프롬프트 `laba@ubuntu` 표시 | PASS | 2026-04-25 23:05 KST 확인. `ssh orin 'hostname; whoami; pwd'` 결과: host `ubuntu`, user `laba`, cwd `/home/laba`. |
| 2 | `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | PASS | `VIRTUAL_ENV=/home/laba/smolvla/.venv` 확인. `lerobot-find-port` 실행 파일은 `/home/laba/smolvla/.venv/bin/lerobot-find-port`. |
| 3 | follower 보드만 USB 연결 후 `lerobot_find_port` 실행 | `/dev/ttyACM*` 포트 1개 출력 | PARTIAL | follower만 연결된 상태에서 `/dev/ttyACM0` 1개 확인됨. 이후 양쪽 연결 상태에서 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42138563-if00 -> ../../ttyACM0` 확인. `lerobot-find-port`는 대화형 unplug/Enter 방식이라 비대화형 SSH에서 `EOFError` 발생. |
| 4 | leader 보드만 USB 연결 후 `lerobot_find_port` 실행 | `/dev/ttyACM*` 포트 1개 출력 | PARTIAL | leader 추가 연결 후 `/dev/ttyACM1` 확인됨. `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42138566-if00 -> ../../ttyACM1` 확인. leader만 단독 연결한 `lerobot-find-port` 실행은 미수행. |
| 5 | `config_so_follower.py` port 필드 확인 | 3단계에서 확인한 포트와 일치 | FAIL | Orin `/home/laba/smolvla/lerobot/robots/so_follower/config_so_follower.py`의 `SOFollowerConfig.port`는 `port: str` 타입 선언만 있고 실제 `/dev/ttyACM0` 기본값/반영값 없음. |
| 6 | `config_so_leader.py` port 필드 확인 | 4단계에서 확인한 포트와 일치 | FAIL | Orin `/home/laba/smolvla/lerobot/teleoperators/so_leader/config_so_leader.py`의 `SOLeaderConfig.port`는 `port: str` 타입 선언만 있고 실제 `/dev/ttyACM1` 기본값/반영값 없음. |

## 업데이트

- 2026-04-25 23:05 KST — prod 검증 실행. SSH 접속과 venv 활성화는 PASS.
- Orin에서 `/dev/ttyACM0`, `/dev/ttyACM1` 두 장치 확인.
  - `/dev/ttyACM0`: `ID_SERIAL_SHORT=5B42138563`, by-id `usb-1a86_USB_Single_Serial_5B42138563-if00`
  - `/dev/ttyACM1`: `ID_SERIAL_SHORT=5B42138566`, by-id `usb-1a86_USB_Single_Serial_5B42138566-if00`
- follower만 먼저 연결되어 있던 시점에 `/dev/ttyACM0`만 존재했고, leader 추가 연결 후 `/dev/ttyACM1`이 추가됨. 따라서 이번 세션 기준 follower=`/dev/ttyACM0`, leader=`/dev/ttyACM1`로 추정.
- `lerobot_find_port` 명령명은 현재 Orin venv에서 존재하지 않고, 실제 엔트리포인트는 `lerobot-find-port`.
- `lerobot-find-port`는 unplug 후 Enter를 요구하는 대화형 스크립트라 비대화형 SSH 실행에서 `EOFError: EOF when reading a line`로 종료됨.
- 스펙 업데이트 요청: 테스트 단계의 명령명을 `lerobot_find_port`에서 `lerobot-find-port`로 정정하거나 alias 제공 여부를 명확히 해야 함.
- 스펙 업데이트 요청: `config_so_follower.py`/`config_so_leader.py`는 현재 dataclass 타입 선언만 포함하고 실제 포트 기본값을 저장하지 않음. 포트를 어느 설정 파일/CLI 인자로 반영해야 하는지 명확화 필요.
