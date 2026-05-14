# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-26 00:29 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 테스트 목표

SO-ARM 포트 탐지 및 런커맨드 문서화 — `sudo chmod` 제거 후 `run_teleoperate.sh` prod 재검증

`orin/scripts/run_teleoperate.sh`의 `calibrate-follower`, `calibrate-leader`, `teleoperate` 서브커맨드가 sudo 없이 정상 동작하는지 Orin에서 확인한다.

## DOD (완료 조건)

follower/leader 포트가 확인되고, calibrate·teleoperate 실행에 필요한 포트 포함 커맨드가 `orin/scripts/` 에 기록됨.  
`sudo chmod` 없이 `laba` 계정에서 ttyACM 포트 접근 및 스크립트 서브커맨드 실행 성공.

## 환경

Orin JetPack 6.2.2, venv `~/smolvla/.venv`  
follower: `/dev/ttyACM0` (serial `5B42138563`), leader: `/dev/ttyACM1` (serial `5B42138566`)  
접근: devPC → `ssh orin`

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC에서 `ssh orin` 접속 | 프롬프트 `laba@ubuntu` 표시 | PASS | 2026-04-26: `ssh orin` 접속 성공, `whoami=laba`, `hostname=ubuntu` 확인 |
| 2 | `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | PASS | 2026-04-26: `VIRTUAL_ENV=/home/laba/smolvla/.venv`, Python 3.10.12 확인 |
| 3 | `ls /dev/ttyACM*` | `/dev/ttyACM0`, `/dev/ttyACM1` 두 장치 확인 | PASS | 2026-04-26: `/dev/ttyACM0`, `/dev/ttyACM1` 존재, owner `root:dialout`, mode `crw-rw----`. follower/leader 연결 상태 확인 |
| 4 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh --help` | 서브커맨드 목록 출력 | FAIL | 2026-04-26: 원격 Orin에 `/home/laba/smolvla/orin/scripts/run_teleoperate.sh` 경로가 없어 `No such file or directory`. 실제 배포 경로 `/home/laba/smolvla/scripts/run_teleoperate.sh --help`는 `all`, `calibrate-follower`, `calibrate-leader`, `teleoperate` 출력 |
| 5 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh calibrate-follower` | sudo 요구 없이 calibration 시작 | FAIL | 2026-04-26: 표기 경로는 #4와 동일하게 미존재. 실제 배포 경로 `~/smolvla/scripts/run_teleoperate.sh calibrate-follower`는 sudo 프롬프트 없이 `[1/3] Calibrating follower on /dev/ttyACM0` 출력 후 `ImportError: cannot import name 'bi_openarm_follower' from 'lerobot.robots'`로 중단 |
| 6 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh calibrate-leader` | sudo 요구 없이 calibration 시작 | FAIL | 2026-04-26: 표기 경로는 #4와 동일하게 미존재. 실제 배포 경로 `~/smolvla/scripts/run_teleoperate.sh calibrate-leader`는 sudo 프롬프트 없이 `[2/3] Calibrating leader on /dev/ttyACM1` 출력 후 동일한 `bi_openarm_follower` ImportError로 중단 |
| 7 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh teleoperate` | sudo 요구 없이 teleoperate 시작, leader 추종 확인 | FAIL | 2026-04-26: 표기 경로는 #4와 동일하게 미존재. 실제 배포 경로 `~/smolvla/scripts/run_teleoperate.sh teleoperate`는 sudo 프롬프트 없이 `[3/3] Starting teleoperation` 출력 후 동일한 `bi_openarm_follower` ImportError로 중단. calibration 미완료 및 leader 추종 미검증 |

## 테스트 메모

- 2026-04-26: Orin의 실제 배포 스크립트는 `/home/laba/smolvla/scripts/run_teleoperate.sh`에 있으며, 로컬 repo의 `orin/scripts/run_teleoperate.sh`와 동일하게 `sudo chmod` 단계는 제거된 상태로 확인됨.
- 2026-04-26: 포트 권한 조건은 충족된 것으로 보임. `/dev/ttyACM0`, `/dev/ttyACM1` 모두 `root:dialout` `crw-rw----`이며 `laba` venv에서 스크립트가 sudo 비밀번호 프롬프트 없이 lerobot entrypoint까지 진입함.
- 2026-04-26: 현재 차단 원인은 serial permission이 아니라 Orin 런타임의 `lerobot.robots` import 불일치임. `lerobot-calibrate`와 `lerobot-teleoperate`가 `bi_openarm_follower` import에서 중단되어 실제 calibration/teleoperation 동작은 검증하지 못함.
- 스펙 업데이트 요청: 테스트 커맨드의 원격 경로를 실제 배포 경로(`~/smolvla/scripts/run_teleoperate.sh`) 또는 배포 구조에 맞게 정정 필요. 또한 Orin 런타임에서 `lerobot.robots.bi_openarm_follower` import 기대와 현재 inference-only 패키징 범위가 맞는지 확인 필요.

## 사후 조치 (2026-04-26)

**원인 분석:** `orin/lerobot/scripts/` 4개 파일(calibrate, teleoperate, record, replay)이 upstream에서 복사되어 `bi_openarm_follower`, `bi_so_follower`, `hope_jr`, `koch_follower`, `omx_follower`, `openarm_follower`, `bi_openarm_leader` 등 `orin/lerobot/`에 존재하지 않는 robot/teleoperator 모듈을 `# noqa: F401` 사이드이펙트 임포트로 불러오는 구조. `orin/lerobot/robots/`에는 `so_follower`만, `orin/lerobot/teleoperators/`에는 `so_leader`만 존재.

**수정 내용:** 4개 스크립트의 robot/teleoperator import 블록을 `so_follower`·`so_leader` 만 남기고 나머지 제거. `python -m py_compile` 문법 검증 4개 모두 통과.
