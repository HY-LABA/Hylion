# TODO-G1 — orin/tests/check_hardware.sh

> 작성: 2026-05-01 | task-executor | cycle: 1

## 목표

Orin 에서 카메라 인덱스·flip / SO-ARM 포트 / venv 활성화 / CUDA 라이브러리를 자동 점검하는 게이트 스크립트. first-time (발견 + cache 갱신) + resume (cache 기반 검증) 두 모드. BACKLOG 03 #14·#15·#16 + 01 #1 해소.

## 사전 점검 결과

### 레퍼런스 비대화형 분리 가능성 분석

- **lerobot_find_port.py**:
  - `find_port()` — `input()` stdin 대화형 포함. 비대화형 wrapping 불가.
  - `find_available_ports()` — pyserial 목록 조회만, Linux 에서 `/dev/tty*` glob. 완전 비대화형.
  - 채택 전략: `find_available_ports()` 의 Linux 분기 (`/dev/ttyACM*` + `/dev/ttyUSB*` 스캔) 를 Python3 인라인으로 직접 구현. lerobot CLI 호출 없음. (SO-ARM 은 ttyACM* = Feetech USB-Serial)
  
- **lerobot_find_cameras.py / camera_opencv.py**:
  - `OpenCVCamera.find_cameras()` 정적 메서드 — `/dev/video*` glob + cv2.VideoCapture 시도. 완전 비대화형.
  - 채택 전략: venv 활성화 후 `from lerobot.cameras.opencv import OpenCVCamera; OpenCVCamera.find_cameras()` Python3 인라인 호출.

### BACKLOG 해소 매핑

| BACKLOG | 해소 방법 |
|---|---|
| 03 #14 SSH 비대화형 cusparseLt | step_venv 에서 스크립트 자체가 `source activate` 수행 → SSH 비대화형 호출 시에도 venv+LD_LIBRARY_PATH 패치 적용 |
| 03 #15 카메라 인덱스 사전 발견 | step_cameras 에서 `OpenCVCamera.find_cameras()` 비대화형 호출 + cameras.json cache |
| 03 #16 wrist flip 확인 | step_cameras first-time 모드에서 사용자에게 wrist flip 확인 프롬프트. cache 에 `"wrist": {"flip": true/false}` 저장 |
| 01 #1 SO-ARM 포트 변동 | step_soarm_port 에서 ttyACM*/ttyUSB* 동적 스캔 + ports.json cache. udev rule 의존 없음 |

### orin/tests/configs/ 신규 디렉터리

- `orin/tests/configs/` 는 TODO-O2 에서 구조로 정의됐으나 실 파일 미생성 상태. 본 TODO 에서 신규 생성 (placeholder yaml 2개).

### config/ports.json·cameras.json git 추적 정책 결정 (BACKLOG 04 #3)

**결정:**
- `orin/config/ports.json`, `orin/config/cameras.json` placeholder (null 값) — **git 추적 유지** (TODO-O2 산출물 그대로)
- first-time 모드가 실 환경값으로 갱신한 이후의 변경분 — **사용자가 직접 판단** (`git status` 로 확인 후 commit/checkout)
- gitignore 에 실 cache 파일을 자동 제외하는 패턴 추가 대신, `.gitignore` 에 의도와 판단 기준 코멘트 추가

**근거:**
- placeholder null 값을 git 추적해야 `orin/config/README.md` 와 함께 레포 구조로 전달 가능
- 실 cache 는 노드(시연장 Orin)에 따라 달라짐 → commit 하면 다른 노드 혼동 유발
- `ports.json` / `cameras.json` 을 직접 gitignore 에 넣으면 placeholder 도 추적 불가 → 현재 구조 파괴
- DataCollector 이식 (TODO-G3) 시 노드별 cache 분기 방안 재논의 예정

**`.gitignore` 변경:** 코멘트 블록만 추가 (실 패턴 추가 없음). Category B 최소 변경 원칙.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/tests/check_hardware.sh` | A (신규) | 4단계 점검 게이트 스크립트 (venv/cuda/port/camera) |
| `orin/tests/configs/first_time.yaml` | A (신규) | first-time 모드 설정 placeholder |
| `orin/tests/configs/resume.yaml` | A (신규) | resume 모드 설정 placeholder |
| `/home/babogaeguri/Desktop/Hylion/.gitignore` | M | orin/config/ cache 파일 추적 정책 코멘트 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `orin/lerobot/` 미변경 (lerobot CLI 호출만, 수정 없음).
- Coupled File Rule: `orin/lerobot/` 미변경이므로 `03_orin_lerobot_diff.md` 갱신 불필요. `orin/pyproject.toml` 미변경이므로 `02_orin_pyproject_diff.md` 갱신 불필요.
- Category B `.gitignore` 변경: 최소 변경 (코멘트 블록만). 실 패턴 추가 없음 → code-tester MAJOR 시 자동 재시도 X 게이트 적용 범위 최소화.
- 레퍼런스 활용:
  - `lerobot_find_port.py` 의 `find_available_ports()` Linux 분기 패턴 기반 → ttyACM*/ttyUSB* 스캔
  - `camera_opencv.py` 의 `OpenCVCamera.find_cameras()` 정적 메서드 직접 호출
  - `05_orin_venv_setting.md §3·§4` 의 cusparseLt LD_LIBRARY_PATH 패턴 재현

## 변경 내용 요약

`orin/tests/check_hardware.sh` 는 단일 진입점으로 `--mode {first-time,resume}` 인자를 받는다. 스크립트 내부에서 `source ~/smolvla/orin/.hylion_arm/bin/activate` 를 직접 실행하므로 SSH 비대화형 환경 (BACKLOG 03 #14) 에서도 venv 와 LD_LIBRARY_PATH 가 올바르게 설정된다. 4단계 점검 (venv → CUDA → SO-ARM 포트 → 카메라) 을 순서대로 수행하며 각 단계의 결과를 JSON 임시 파일로 누적한다. `--output-json` 플래그로 prod-test-runner 가 비대화형으로 파싱 가능한 결과 JSON 을 저장한다.

SO-ARM 포트 발견 (step 3) 은 lerobot_find_port.py 의 대화형 `find_port()` 를 우회하고, 비대화형인 `find_available_ports()` 의 Linux 분기 (`/dev/ttyACM*` + `/dev/ttyUSB*` glob) 만 인라인 Python3 으로 재현한다. 카메라 발견 (step 4) 은 `OpenCVCamera.find_cameras()` 정적 메서드를 직접 호출해 완전 비대화형으로 동작한다. first-time 모드에서는 발견 결과를 사용자에게 확인하거나 (`--quiet` 없을 때) 자동 할당 (`--quiet` 시) 후 `orin/config/ports.json`·`cameras.json` 에 저장한다. resume 모드에서는 cache 와 현재 발견을 비교하여 불일치 시 FAIL 을 반환한다.

## 본 사이클 자연 해소 BACKLOG

| BACKLOG 항목 | 해소 여부 | 비고 |
|---|---|---|
| 04 #3 ports/cameras git 정책 | 해소 (결정) | placeholder 추적 / 실 cache 사용자 판단. `.gitignore` 코멘트 추가 |
| 01 #1 SO-ARM 포트 변동 | 해소 (설계) | 동적 발견 + cache 패턴으로 udev 의존 없이 처리. prod 검증은 TODO-G2 |
| 01 #2 lerobot-find-port 비대화형 | 해소 (우회) | find_available_ports() Linux 분기만 재현. stdin 대화형 find_port() 호출 없음 |
| 03 #14 SSH 비대화형 cusparseLt | 해소 (설계) | step_venv 에서 스크립트 자체가 source + LD_LIBRARY_PATH 적용. prod 검증은 TODO-G2 |
| 03 #15 카메라 인덱스 발견 | 해소 (설계) | step_cameras 에서 OpenCVCamera.find_cameras() 비대화형 호출 |
| 03 #16 wrist flip | 해소 (설계) | first-time 모드 사용자 확인 프롬프트 + cameras.json wrist.flip 저장 |

## 잔여 리스크 / SKILL_GAP

- **SKILL_GAP 없음**: lerobot 레퍼런스 (`find_available_ports()` Linux 분기, `OpenCVCamera.find_cameras()`) 에 대응 구현이 존재하고 그것을 기반으로 작성.
- **X11 없는 카메라 미리보기**: first-time 모드에서 카메라 영상 확인 (flip 방향 육안 확인) 은 Orin 콘솔 직접 또는 X11 forwarding 필요. 본 스크립트는 인덱스·flip 값만 기록하며 영상 미리보기는 제공하지 않음. (spec 의 "Orin 콘솔 직접 사용 가정" 과 일치)
- **ttyACM0 외 포트**: Orin 에 Feetech 서보 2개 (follower + leader) 연결 시 ttyACM0/ttyACM1 이 각각 할당될 수 있음. 현재 스크립트는 follower 만 cache 에 저장하는 설계 — leader 추가 지원은 추후 요구사항에 따라 확장.
- **cam_out 에 특수문자**: OpenCVCamera.find_cameras() 결과 중 `name` 필드에 따옴표·슬래시가 포함될 수 있음. 환경변수 경유 방식으로 처리하여 bash 파싱 오류 방지.

## 검증 필요 (다음 단계)

- **task-executor 자체 문법 검증**: `bash -n orin/tests/check_hardware.sh` — 아래 참조
- **code-tester 검증**:
  - `bash -n orin/tests/check_hardware.sh` 문법 오류 없음
  - `--mode first-time --help` exit code 2 확인
  - `--mode invalid` exit code 2 확인
  - JSON schema 일관성: `summary.pass + summary.fail == steps 수`
  - `--output-json` 파일 생성 확인
- **prod-test-runner (TODO-G2)**:
  - Orin + 카메라 2대 + SO-ARM follower 연결 상태에서 `--mode first-time` PASS
  - cache 저장 후 `--mode resume` PASS
  - `--mode resume --quiet --output-json /tmp/hw.json` 비대화형 PASS + JSON 파싱 가능 확인
  - BACKLOG 03 #14: SSH 비대화형 (`ssh orin "bash ~/smolvla/orin/tests/check_hardware.sh --mode resume --quiet"`) PASS
