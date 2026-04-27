# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-25 23:20 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 작업 목표

SO-ARM 실행 편의 스크립트 작성 — 확인된 포트 정보를 기반으로 calibrate·teleoperate 커맨드를 포함한 셸 스크립트를 `orin/scripts/` 에 작성한다.

## DOD (완료 조건)

- `orin/scripts/run_teleoperate.sh` (또는 동등한 위치) 작성 완료
- 스크립트 내에 아래 커맨드가 포트 포함 형태로 기록됨:
  - `lerobot-calibrate` (follower / leader 각각)
  - `lerobot-teleoperate` (follower + leader 동시)
- 실행 전 `sudo chmod 666 /dev/ttyACM*` 포함

## 확인된 포트 정보

- follower: `/dev/ttyACM0` (serial `5B42138563`, by-id `usb-1a86_USB_Single_Serial_5B42138563-if00`)
- leader: `/dev/ttyACM1` (serial `5B42138566`, by-id `usb-1a86_USB_Single_Serial_5B42138566-if00`)

## 구현 대상

- `orin/scripts/run_teleoperate.sh` — 신규 작성

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- `orin/lerobot/robots/so_follower/config_so_follower.py` — port 필드는 수정 불필요 (CLI arg 설계)
- `orin/lerobot/teleoperators/so_leader/config_so_leader.py` — 동일

## 참고

seeedwiki 기준 커맨드 형식 (`docs/reference/seeedwiki/seeedwiki_so101.md` 참조):

```bash
# 포트 권한 부여
sudo chmod 666 /dev/ttyACM*

# follower calibration
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm

# leader calibration
lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm

# teleoperate
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm
```

## 업데이트
- 변경한 내용
    - `orin/scripts/run_teleoperate.sh` 신규 작성
    - 확인된 포트(`follower=/dev/ttyACM0`, `leader=/dev/ttyACM1`)와 ID를 변수로 고정하고, 아래 실행 경로를 제공
        - `sudo chmod 666 /dev/ttyACM*`
        - `lerobot-calibrate` (follower)
        - `lerobot-calibrate` (leader)
        - `lerobot-teleoperate` (follower + leader)
    - `all|calibrate-follower|calibrate-leader|teleoperate` 서브커맨드 및 `--help` 사용법 출력 추가

- 검증 방법 및 결과
    - `bash -n orin/scripts/run_teleoperate.sh` 실행: 문법 오류 없음
    - `orin/scripts/run_teleoperate.sh --help` 실행: 사용법/서브커맨드 정상 출력 확인

- test/prod 검증이 필요한 경우
    - 실장비 연결 상태에서 아래 실제 실행 검증 필요
        - `orin/scripts/run_teleoperate.sh calibrate-follower`
        - `orin/scripts/run_teleoperate.sh calibrate-leader`
        - `orin/scripts/run_teleoperate.sh teleoperate`
