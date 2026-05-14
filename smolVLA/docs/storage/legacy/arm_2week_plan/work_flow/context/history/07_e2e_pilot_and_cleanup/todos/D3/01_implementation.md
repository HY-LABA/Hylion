# TODO-D3 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`dgx/scripts/check_hardware.sh` 5-step 도구 정합 정적 검증 + 사용성 개선 (07 사이클 맥락 메시지 갱신) + PHYS_REQUIRED 마킹.

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/scripts/check_hardware.sh` | M | X4·X5 참조 메시지 → setup_train_env.sh §3-c 참조로 갱신 (4곳) |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (Category A 준수)
- Coupled File Rule: `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 미변경 — Coupled File Rule 비해당
- Category B: `dgx/scripts/check_hardware.sh` 는 deploy_*.sh 패턴 아님, setup_env.sh 도 아님 → Category B 비해당 (신규 스크립트 영역)
- 레퍼런스 직접 Read:
  - `docs/work_flow/context/history/06_dgx_absorbs_datacollector/todos/X3/01_implementation.md` — 06 X3 이식 결과 (check_hardware.sh 신규 작성 근거·패턴)
  - `docs/work_flow/context/history/06_dgx_absorbs_datacollector/todos/V1/03_prod-test.md` — 06 V1 정적 검증 결과 (devPC bash -n PASS + 5-step 정합 검증 기준)
  - `dgx/scripts/check_hardware.sh` — 실제 파일 전체 Read

---

## Step 1 — check_hardware.sh 정합 정적 검증

### bash -n 검증

```
bash -n dgx/scripts/check_hardware.sh → exit 0 (PASS)
```

06 X3 code-test 단계 및 06 V1 prod-test 에서 이미 확인된 PASS 를 07 사이클 시점 재확인.

### shellcheck

shellcheck 바이너리 미설치 (06 X3 와 동일 환경). 06 X3 수동 점검 결과 그대로 유효:
- `set -uo pipefail` (set -e 미사용 — 개별 step 실패 수집 의도)
- 모든 변수 쌍따옴표 처리
- `trap + mktemp` 임시 파일 정리
- `record_step()` 환경변수 경유 Python json.dump — 특수문자 안전

### 5-step 구성 vs spec DOD 매핑

spec D3 의 "5-step 도구 매핑" 과 실제 스크립트 함수 매핑:

| spec 정의 | spec 예시 명령 | 스크립트 구현 | 정합 |
|---|---|---|---|
| Step 1: USB 장치 검출 | `lsusb` 또는 SO-ARM 패턴 | `step_soarm_port()` — `Path("/dev").glob("ttyACM*")` + `glob("ttyUSB*")` | ✅ (패턴 일치) |
| Step 2: dialout 그룹 확인 | `groups \| grep dialout` | `step_dialout()` — `id -Gn \| grep -qw "dialout"` | ✅ |
| Step 3: v4l2 확인 | `v4l2-ctl --list-devices` | `step_v4l2()` — `find /dev -name "video*" -type c` | ✅ (동등) |
| Step 4: lerobot-find-port | SO-ARM 포트 식별 | `step_soarm_port()` Python glob — lerobot_find_port.py 와 동일 로직 | ✅ |
| Step 5: lerobot-find-cameras | 카메라 인덱스 식별 | `step_cameras()` — `OpenCVCamera.find_cameras()` | ✅ |
| Step 6: wrapper | `check_hardware.sh` | `main()` — step_venv + step_dialout + step_soarm_port + step_v4l2 + step_cameras | ✅ |

주: 스크립트 내부 step 번호는 Step1=venv(추가됨), Step2=dialout, Step3=soarm_port(USB+find-port 통합), Step4=v4l2, Step5=cameras 로 구성. spec 의 6항목 (1 USB 검출 + 2 dialout + 3 v4l2 + 4 find-port + 5 find-cameras + 6 wrapper) 을 스크립트가 5개 함수로 통합 구현 — 정합 이상 없음.

### 06 V1 정합 재확인 (7항목)

06 V1 prod-test 에서 확인된 orin 패턴 미러 7항목이 현재 파일에도 유효:

| 패턴 항목 | 검증 결과 |
|---|---|
| `set -uo pipefail` (set -e 미사용) | ✅ L48 |
| `record_step()` — 환경변수 경유 Python json.dump | ✅ L101~L133 |
| `TMP_RESULT_JSON mktemp + trap EXIT` | ✅ L60~L61 |
| `OpenCVCamera.find_cameras()` 호출 경로 | ✅ L260~L261 |
| `finalize_output()` JSON summary 패턴 | ✅ L307~L348 |
| `--quiet` + `--output-json` 인자 | ✅ L29~L30, L74~L83 |
| 종료 코드 규약 (0=PASS, 1=FAIL, 2=usage) | ✅ L37~L41 |

---

## Step 2 — 시연장 이동 시 사용성 검토

### 안내·에러 메시지 명확성

각 FAIL/WARN 상황에서 사용자 행동을 안내하는 메시지 존재 확인:

| 상황 | 메시지 | 명확성 |
|---|---|---|
| venv 미존재 | "activate 스크립트 미존재: {경로}" | ✅ |
| dialout 그룹 미포함 | "해결: `sudo usermod -aG dialout {user}` (재로그인 필요)" | ✅ |
| soarm_port 미발견 | "SO-ARM USB 연결 확인 필요 (/dev/ttyACM* or /dev/ttyUSB*)" | ✅ |
| v4l2 미발견 | "카메라 USB 연결 확인 필요 (/dev/video*)" | ✅ |
| cameras import 실패 | "setup_train_env.sh §3-c 실행 후 재시도 (lerobot hardware extra 필요)" | ✅ (07 갱신) |
| cameras 미발견 | "USB 카메라 연결 확인 필요" | ✅ |
| 종합 FAIL 시 | `[DONE] {N}개 FAIL / {M}개 PASS` + 해결 힌트 블록 | ✅ |

### 07 사이클 갱신 내용 (사용성 개선)

06 사이클 X4·X5 todo 번호 참조 → 07 사이클 현재 맥락으로 갱신 (4곳):

| 위치 | 이전 | 이후 |
|---|---|---|
| L34 (주석) | `lerobot [hardware,feetech] extra 설치 (X4·X5 완료 후 — V1 검증 대상)` | `lerobot [hardware,feetech] extra 설치 (dgx/scripts/setup_train_env.sh §3-c 완료 후)` |
| L249 (주석) | `NOTE: lerobot [hardware] extra 설치 필요 (X4·X5 완료 후 동작)` | `NOTE: lerobot [hardware] extra 설치 필요 (setup_train_env.sh §3-c 완료 후 동작)` |
| L282 (주석) | `lerobot [hardware] extra 미설치 시 — X4·X5 완료 전 단계에서 발생 가능` | `lerobot [hardware] extra 미설치 시 — setup_train_env.sh §3-c 실행 전 단계에서 발생 가능` |
| L345 (출력) | `cameras FAIL (import) → X4·X5 완료 후 재실행 (lerobot hardware extra 필요)` | `cameras FAIL (import) → setup_train_env.sh §3-c 실행 후 재시도 (lerobot hardware extra 필요)` |

### 5-step 중 PHYS 필수 부분 vs 자동 fallback

| Step | PHYS 필수 여부 | 자동 실행 가능 여부 |
|---|---|---|
| Step 1 (venv) | PHYS 불필요 | DGX SSH 자율 (venv 존재 여부만 확인) |
| Step 2 (dialout) | PHYS 불필요 | DGX SSH 자율 (`id -Gn` 명령) |
| Step 3 (soarm_port) | PHYS 필수 (SO-ARM 물리 연결) | USB 미연결 시 FAIL + 안내 메시지 출력 후 계속 진행 |
| Step 4 (v4l2) | PHYS 필수 (카메라 물리 연결) | USB 미연결 시 FAIL + 안내 메시지 출력 후 계속 진행 |
| Step 5 (cameras) | PHYS 필수 (카메라 물리 연결 + lerobot 설치) | 설치 미완 시 import 에러 → 안내 후 계속 진행 |

`set -e` 미사용으로 step 별 FAIL 이 전체 중단 없이 누적 → `finalize_output()` 에서 종합. 시연장에서 한 줄 실행 (`bash dgx/scripts/check_hardware.sh`) 시 5 step 결과 일괄 출력 + FAIL 항목별 해결 힌트 제공.

---

## Step 3 — 실 SO-ARM 검증 BACKLOG 마킹

### 기존 BACKLOG 현황

`docs/work_flow/specs/BACKLOG.md` L125 에 이미 06 V1 항목이 등록됨:
> "TODO-V1 — DGX 시연장 이동 후 SO-ARM·카메라 직결 하드웨어 검증 (USB·dialout·v4l2·find-port·find-cameras·check_hardware.sh 5-step, 총 6 항목)" — 미완, 중간 우선순위

07 D3 에서 신규 중복 등록 불필요. prod-test-runner 가 `verification_queue.md` D 그룹에 D3 항목 추가 시 06 V1 BACKLOG 와 통합 (이중 등록 X) 을 명시할 것.

### prod-test-runner 인계 사항 (verification_queue D 그룹)

prod-test-runner 가 verification_queue D 그룹에 추가할 항목:

```
### [TODO-D3] DGX 5-step 하드웨어 검증 도구 정비

- **상태**: NEEDS_USER_VERIFICATION (PHYS_REQUIRED — 시연장 이동 시)
- **사용자 검증 필요 사항**:
  1. DGX 시연장 이동 + SO-ARM 2대(follower + leader) + 카메라 2대 USB 직결
  2. `cd ~/smolvla && bash dgx/scripts/check_hardware.sh` 실행
  3. 기대: `[DONE] 모든 점검 PASS (5단계)` + FAIL 0건
  4. FAIL 발생 시 해결 힌트 블록 지시에 따라 처리
- **06 V1 BACKLOG 와 통합**: BACKLOG.md L125 의 06 V1 항목과 동일 범위
  → 이중 등록 X. 시연장 이동 시 D3 verification 으로 06 V1 BACKLOG 처리 완료 가능
- **환경 레벨**: PHYS_REQUIRED
```

---

## 변경 내용 요약

`dgx/scripts/check_hardware.sh` 는 06 X3 (2026-05-02) 에 신규 작성된 파일로, 본 TODO-D3 에서는 정합 정적 검증 + 사용성 소폭 개선을 수행했다.

정합 검증 결과: bash -n exit 0, 5-step 구성 (soarm_port·dialout·v4l2·cameras + venv 선행) spec 매핑 완전 정합, orin 04 G1 패턴 미러 7항목 전부 유효, 에러 메시지 명확성 양호.

사용성 개선: 06 spec 특정 todo 번호 (X4·X5) 를 참조하던 주석·출력 메시지 4곳을 운영 실무자가 이해할 수 있는 `setup_train_env.sh §3-c` 참조로 갱신. 실물 SO-ARM·카메라 직결 검증은 PHYS_REQUIRED 로 BACKLOG 유지 (06 V1 항목과 통합).

---

## code-tester 인계 사항

| 검증 항목 | 명령 | 기대 결과 |
|---|---|---|
| bash -n | `bash -n dgx/scripts/check_hardware.sh` | exit 0 |
| shellcheck (가용 시) | `shellcheck dgx/scripts/check_hardware.sh` | warnings 0 또는 style 경고만 |
| X4·X5 참조 잔재 | `grep -n "X4\|X5" dgx/scripts/check_hardware.sh` | 0건 |
| setup_train_env.sh 갱신 메시지 | `grep -n "setup_train_env.sh" dgx/scripts/check_hardware.sh` | 4건 (L34, L249, L282, L345 인근) |
| 5-step 함수 목록 | `grep "^step_.*() {" dgx/scripts/check_hardware.sh` | 5건 (step_venv·step_dialout·step_soarm_port·step_v4l2·step_cameras) |
| DOD 1: bash -n PASS | (위 bash -n) | exit 0 |
| DOD 2: 시연장 사용 가능성 (에러 메시지 명확) | grep 안내 메시지 + 해결 힌트 | 존재 확인 |
| DOD 3: PHYS_REQUIRED 마킹 | implementation.md Step 3 + prod-test-runner 인계 사항 | 명시 확인 |

### 추가 확인 권장

- `dgx/scripts/preflight_check.sh` 미접촉 확인: `git diff dgx/scripts/preflight_check.sh` → 변경 없음
- 기타 `dgx/scripts/` 파일 미접촉 확인: smoke_test.sh · save_dummy_checkpoint.sh · setup_train_env.sh · run_teleoperate.sh · push_dataset_hub.sh 변경 없음

### PHYS_REQUIRED 처리

- verification_queue.md D 그룹에 D3 항목 추가 (prod-test-runner 책임)
- 06 V1 BACKLOG (BACKLOG.md L125) 와 통합 — D3 verification 통과 시 06 V1 BACKLOG 완료 처리 가능
- 실 SO-ARM 검증은 DGX 시연장 이동 시 (08_leftarmVLA 또는 별도 PHYS 검증 사이클)
