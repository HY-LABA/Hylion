# TODO-V1 — Prod Test

> 작성: 2026-05-02 17:00 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

---

## 배포 대상

- DGX (SSH 불가 — devPC 정적 검증 + Phase 3 사용자 실물 검증 위임)

## 배포 결과

- 명령: N/A (DGX 물리적으로 분리된 상태 — SSH 접근 불가)
- 결과: 배포 실행 불가 (환경 제약)
- 조치: 사용자 실물 환경 검증 (Phase 3) 으로 100% 위임

---

## 자동 비대화형 검증 결과

### devPC 정적 검증 (가능한 부분)

| 검증 | 명령 | 결과 |
|---|---|---|
| bash -n 문법 검증 | `bash -n dgx/scripts/check_hardware.sh` | exit 0 (PASS) |

**주의**: bash -n 은 X3 code-test 단계에서도 이미 통과 확인 (X3 `02_code-test.md` §단위 테스트 결과). 본 단계 재실행으로 재확인.

### check_hardware.sh 5-step 구성 정합 검증

spec 호출 요구 사항 (`TODO-V1 작업 범위 §1`): 5-step 구성 + orin `check_hardware.sh` 04 G1 패턴 미러 확인.

| 항목 | 검증 방법 | 결과 |
|---|---|---|
| Step 1: venv 활성화 | 코드 직접 Read | `step_venv()` — `VENV_ACTIVATE="${HOME}/smolvla/dgx/.arm_finetune/bin/activate"` 정합 |
| Step 2: dialout 그룹 멤버십 | 코드 직접 Read | `step_dialout()` — `id -Gn` + `grep -qw "dialout"` 패턴 |
| Step 3: SO-ARM 포트 발견 | 코드 직접 Read | `step_soarm_port()` — `/dev/ttyACM*` + `/dev/ttyUSB*` glob (orin 원본 동일 패턴) |
| Step 4: v4l2 장치 발견 | 코드 직접 Read | `step_v4l2()` — `find /dev -name "video*" -type c` |
| Step 5: lerobot OpenCVCamera | 코드 직접 Read | `step_cameras()` — `from lerobot.cameras.opencv import OpenCVCamera` (orin 원본 동일 패턴) |

### orin 04 G1 패턴 미러 비교

| 패턴 항목 | orin (참조) | dgx (검증 대상) | 정합 |
|---|---|---|---|
| `set -uo pipefail` (set -e 미사용) | ✅ | ✅ | 정합 |
| `record_step()` — 환경변수 경유 Python json.dump | ✅ | ✅ | 정합 |
| `TMP_RESULT_JSON mktemp + trap EXIT` | ✅ | ✅ | 정합 |
| `OpenCVCamera.find_cameras()` 호출 경로 | `from lerobot.cameras.opencv import OpenCVCamera` | `from lerobot.cameras.opencv import OpenCVCamera` | 정합 |
| `finalize_output()` JSON summary 패턴 | `{'pass': ..., 'fail': ..., 'exit_code': ...}` | `{'pass': ..., 'fail': ..., 'exit_code': ...}` | 정합 |
| `--quiet` + `--output-json` 인자 | ✅ | ✅ | 정합 |
| 종료 코드 규약 (0=PASS, 1=FAIL, 2=usage) | ✅ | ✅ | 정합 |

**orin 대비 dgx 차이점** (의도적, 정합):

- orin Step 2: CUDA 라이브러리 점검 → dgx 제외 (수집 환경 CUDA 불필요)
- dgx Step 2: dialout 그룹 멤버십 추가 (Ubuntu 22.04 USB 권한 — orin 에서는 JetPack venv 활성화 시 처리됨)
- dgx Step 4: v4l2 장치 발견 추가 (카메라 USB 인식 확인 단계 — orin 에서는 cameras.json cache 방식으로 대체)
- orin: first-time / resume 2 모드 분기 → dgx: 단순 1-pass (시연장 이동 후 매번 fresh 연결 가정 — 적절)

**판정**: 5-step 구성 + orin 패턴 미러 정합 확인. bash -n exit 0.

### X4 산출물 (torchcodec 호환) 실 가용성 명세 상태

X4 `01_implementation.md` 조사 결과 요약 (devPC 정적 확인):
- torchcodec `>=0.3.0,<0.11.0` + cu130 인덱스 URL 지정 — X4 조사 시 PyPI 가용성 확인 완료
- DGX 실물 설치 (setup_train_env.sh §3-c 실행) 결과는 V1 prod 검증 시 사용자 확인 항목

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. SO-ARM follower + leader USB 직결 | no (사용자 물리 연결) | → verification_queue |
| 2. 카메라 2대 USB 직결 + v4l2-ctl 인식 | no (사용자 물리 연결 + DGX 명령) | → verification_queue |
| 3. DGX 사용자 dialout 그룹 권한 확인 | no (DGX SSH 불가) | → verification_queue |
| 4. lerobot-find-port 비대화형 SO-ARM 포트 인식 | no (DGX SSH 불가, 하드웨어 필요) | → verification_queue |
| 5. lerobot-find-cameras opencv 카메라 인덱스 발견 | no (DGX SSH 불가, 하드웨어 필요) | → verification_queue |
| 6. check_hardware.sh 5-step 모두 PASS | no (DGX SSH 불가) | → verification_queue |
| check_hardware.sh bash -n 통과 | yes (devPC 정적) | ✅ |
| check_hardware.sh 5-step 구성 정합 | yes (코드 Read + orin 비교) | ✅ |
| check_hardware.sh orin 패턴 미러 | yes (코드 Read + 비교) | ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

모든 검증이 DGX 시연장 이동 + 하드웨어 직결 후 사용자 직접 실행 필요.

1. **DGX 시연장 이동 + USB 직결**
   - SO-ARM follower (12V 전원, Feetech STS/SCS 서보) USB 케이블 DGX 직결
   - SO-ARM leader (7.4V 전원) USB 케이블 DGX 직결
   - 카메라 top + wrist USB 직결
   - DGX Spark USB 포트 부족 시 USB hub 경유 (사용자 별도 준비)

2. **dialout 그룹 권한 확인**
   - DGX 에서: `groups` 또는 `id -Gn` — `dialout` 포함 여부 확인
   - 미포함 시: `sudo usermod -aG dialout $USER` 실행 후 재로그인
   - 재로그인 후 `id -Gn` 으로 dialout 재확인

3. **v4l2 인식 확인**
   - `ls /dev/video*` 또는 `v4l2-ctl --list-devices` 카메라 2대 인식 확인
   - v4l-utils 미설치 시: `sudo apt install v4l-utils`
   - 기대: `/dev/video0`, `/dev/video2` (또는 짝수 인덱스 2개 이상)

4. **lerobot-find-port 비대화형 SO-ARM 포트 식별**
   - venv 활성화: `source ~/smolvla/dgx/.arm_finetune/bin/activate`
   - `python3 -c "from pathlib import Path; print(sorted(Path('/dev').glob('ttyACM*'))[:2])"`
   - 기대: `/dev/ttyACM0`, `/dev/ttyACM1` (follower + leader 각 1개)
   - 미발견 시: USB 케이블 재연결 + `dmesg | tail -20` 에러 확인
   - 참조: 04 BACKLOG #2 (대화형 lerobot-find-port → 비대화형 변환) 패턴

5. **lerobot-find-cameras opencv 카메라 인덱스 발견**
   - venv 활성화 후: `python3 -c "from lerobot.cameras.opencv import OpenCVCamera; print(OpenCVCamera.find_cameras())"`
   - 기대: 카메라 2개 (top + wrist) 인덱스 목록
   - ImportError 발생 시: X5 `setup_train_env.sh §3-c` 실행 여부 확인 (lerobot [hardware] extra 필요)

6. **dgx/scripts/check_hardware.sh 실행 — 5-step 모두 PASS**
   - DGX 에서:
     ```bash
     cd ~/smolvla && bash dgx/scripts/check_hardware.sh
     ```
   - 또는 JSON 결과 저장:
     ```bash
     bash dgx/scripts/check_hardware.sh --output-json /tmp/dgx_hw.json
     cat /tmp/dgx_hw.json
     ```
   - 기대: `[DONE] 모든 점검 PASS (5단계)` + JSON `summary.fail == 0`
   - JSON 이 `env_check.py` 파싱 가능 형식 (`node: dgx`, `purpose: data_collection`, `steps: {...}`) 확인

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| DGX SSH read-only 검증 (자율) | 미실행 — DGX 물리 분리 (환경 제약, 사용자 명시) |
| devPC 정적 검증 | bash -n + 코드 Read — 자율 영역, 실행 |
| Category B 영역 변경 배포 | 해당 없음 — V1 은 검증 todo (구현 없음) |
| 동의 필요 영역 | 없음 |
| prod-test-runner 자율성 정책 준수 | ✅ — devPC 정적 검증만 실행, DGX 접근 시도 없음 |
