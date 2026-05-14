# TODO-D6 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1 → 2 (MINOR R1+R2 처리, 2026-05-03)

## 목표

precheck.py 카메라 식별 강화 (USB 분리/재연결 패턴 + 영상 확인) + entry.py SSH/직접 실행 분기 prompt 신규.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/entry.py` | M | `detect_display_mode()` 신규 + dgx 분기에서 `display_mode` 전달 |
| `dgx/interactive_cli/flows/mode.py` | M | `flow3_mode_entry(display_mode)` 인자 추가 + `teleop_precheck` 호출에 전달 |
| `dgx/interactive_cli/flows/precheck.py` | M | `_run_find_cameras_split()` 신규 + `teleop_precheck(display_mode)` 인자 추가 + 보조 함수 3종 신규 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `orin/lerobot/`, `dgx/lerobot/` 미변경 (Category B 건드리지 않음).
- Coupled File Rule: `orin/lerobot/` 미변경이므로 `03_orin_lerobot_diff.md` 갱신 불필요.
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py`
    인용: `find_cameras()` line 301-303 — Linux `/dev/video*` glob 패턴:
    ```python
    possible_paths = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)
    targets_to_scan = [str(p) for p in possible_paths]
    ```
    → `_get_video_devices()` 에서 `glob.glob("/dev/video*") + sorted()` 로 동일 구현.
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py`
    인용: `_read_from_hardware()` line 343-348 — `ret, frame = self.videocapture.read()`:
    ```python
    ret, frame = self.videocapture.read()
    if not ret:
        raise RuntimeError(f"{self} read failed (status={ret}).")
    ```
    → `_capture_frame_to_file()` 에서 `cap.read()` + ret 체크 패턴으로 적용.
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_cameras.py`
    인용: `save_image()` line 130-151 — `path.parent.mkdir(parents=True, exist_ok=True)` + 파일 저장:
    → ssh 모드 저장 패턴으로 적용 (`cv2.imencode(".jpg")` + `open().write()`).

## 변경 내용 요약

### Part A — `_run_find_cameras_split()` (precheck.py)

기존 `_run_find_cameras()` 가 `lerobot-find-cameras opencv` subprocess 를 실행하고 사용자에게 *출력만 보고 인덱스 입력* 하도록 했다. D4 walkthrough 에서 어느 카메라가 wrist/overview 인지 구분 어렵고 실 영상 미확인 문제가 발생했다.

신규 `_run_find_cameras_split()` 은 lerobot-find-port 의 USB 분리/재연결 패턴을 카메라에 적용: (1) baseline `/dev/video*` 목록 기록, (2) wrist 카메라 연결 → glob 비교로 신규 device 검출, (3) 1프레임 capture 후 display_mode 에 따라 OpenCV imshow 또는 jpg 파일 저장, (4) 사용자 OK 확인, (5) overview 반복. D4 walkthrough 에서 발견된 `video read failed` 패턴 대응으로 3회 retry + warm-up 5프레임 버리기 적용.

### Part B — `detect_display_mode()` (entry.py)

flow 초반에 SSH/직접 실행 분기를 결정. `SSH_CLIENT` / `SSH_TTY` 환경변수로 자동 검출 후 사용자 확인 prompt. `SMOLVLA_DISPLAY_MODE` 환경변수로 비대화형 override 가능 (CI/스크립트용). `DISPLAY` 미설정 시 직접 모드 → SSH 모드 자동 fallback. 결정된 `display_mode` 를 `flow3_mode_entry()` → `teleop_precheck()` 로 전파.

### Part C·D — 통합 + DISPLAY 처리

mode.py `flow3_mode_entry(display_mode="ssh")` 인자 추가 + precheck.py `teleop_precheck(display_mode="ssh")` 인자 추가. 두 함수 모두 기본값 `"ssh"` 로 설정해 직접 호출 시 안전한 fallback. DISPLAY 환경변수 미설정 시 entry.py `detect_display_mode()` 단계에서 이미 `"ssh"` 로 전환되므로 precheck.py 에서는 별도 DISPLAY 재검사 불필요.

## code-tester 입장에서 검증 권장 사항

- `py_compile`: `python3 -m py_compile dgx/interactive_cli/flows/{precheck,entry,mode}.py` — 3파일 모두 PASS 확인.
- `ruff`: `ruff check dgx/interactive_cli/flows/precheck.py dgx/interactive_cli/flows/entry.py dgx/interactive_cli/flows/mode.py` — All checks passed 확인.
- `bash -n`: `bash -n dgx/interactive_cli/main.sh` (변경 없음이지만 회귀 확인).
- import smoke: `python3 -c "from flows.precheck import _run_find_cameras_split, teleop_precheck; from flows.entry import detect_display_mode; print('OK')"` (dgx/interactive_cli/ 에서 실행).
- SSH 모드 자동 검출: `SSH_CLIENT=test python3 -c "from flows.entry import detect_display_mode; import os; os.environ.pop('SMOLVLA_DISPLAY_MODE', None); ..."` — 비대화형 확인은 `SMOLVLA_DISPLAY_MODE=ssh` 사용.
- DISPLAY fallback: `DISPLAY` 미설정 + `SMOLVLA_DISPLAY_MODE` 미설정 + `input()` mock → `"ssh"` 반환 확인.
- `_get_video_devices()`: `/dev/video*` glob 정상 동작 (현 devPC 에서도 동작).
- DOD 항목 1·2·3·4·5 충족 확인:
  1. `_run_find_cameras_split` 신규 + 기존 `_run_find_cameras` 대체 호출 (호출 위치: `teleop_precheck` 내 option 1 분기) ✓
  2. `detect_display_mode` 신규 + entry.py prompt ✓
  3. mode.py·precheck.py display_mode 인자 전파 ✓
  4. DISPLAY 자동 fallback (entry.py) ✓
  5. py_compile + ruff PASS ✓

## 실제 검증 결과 (task-executor 실행)

```
python3 -m py_compile dgx/interactive_cli/flows/precheck.py  → OK
python3 -m py_compile dgx/interactive_cli/flows/entry.py     → OK
python3 -m py_compile dgx/interactive_cli/flows/mode.py      → OK
ruff check (3파일)                                            → All checks passed!
bash -n dgx/interactive_cli/main.sh                          → OK
detect_display_mode(SSH env) → "ssh"                         → OK
DISPLAY fallback (no DISPLAY, auto_detected=direct) → "ssh"  → OK
_get_video_devices() → ['/dev/video0', '/dev/video1']        → OK
import smoke (precheck + entry)                              → OK
```

## Cycle 2 (MINOR R1+R2 처리)

> 작성: 2026-05-03 | task-executor | cycle: 2

### R1 처리 — precheck.py 모듈 docstring L17-18 수정

**위치**: `dgx/interactive_cli/flows/precheck.py` L17-22 (구 L17-19)

**Before**:
```
  - 카메라 인덱스: dgx/interactive_cli/configs/cameras.json
    형식: {"wrist_left": {"index": <int|null>}, "overview": {"index": <int|null>}}
    dgx 카메라 명칭: record.py flow6_record() 의 cam_wrist_left_index / cam_overview_index 기반.
```

**After**:
```
  - 카메라 인덱스: dgx/interactive_cli/configs/cameras.json
    형식: {"wrist_left": {"index": <str path|null>}, "overview": {"index": <str path|null>}}
    예시: {"wrist_left": {"index": "/dev/video2"}, "overview": {"index": "/dev/video4"}}
    _run_find_cameras_split() 이 str path (Linux /dev/video* 경로) 또는 None 을 저장.
    (참고: record.py 는 현재 cameras.json 을 읽지 않고 하드코딩 int 인덱스 사용 — BACKLOG 07-#4)
    dgx 카메라 명칭: record.py flow6_record() 의 cam_wrist_left_index / cam_overview_index 기반.
```

근거: `_run_find_cameras_split` 은 `str path` (`/dev/videoN`) 또는 `None` 을 저장. 기존 `<int|null>` 표기는 구 `_run_find_cameras()` 기준이었으며 D6 신규 함수 이후 부정확.

### R2 처리 — BACKLOG.md 07 섹션 #4 항목 추가

**위치**: `/home/babogaeguri/Desktop/Hylion/smolVLA/docs/work_flow/specs/BACKLOG.md` — `[07_e2e_pilot_and_cleanup]` 섹션

**추가 항목**:
```
| 4 | cameras.json 데이터 연결 — `_run_find_cameras_split` 이 저장한 str path (/dev/videoN) 를
    record.py 또는 다른 사용처가 실제로 읽도록 통합. 현재 mode.py 는 cameras.json 을 읽지 않고
    cam_wrist_left_index=0, cam_overview_index=1 하드코딩 int 전달. 통합 시
    _validate_camera_indices(str, str) 의 < 0 비교에서 TypeError 위험.
    현재 실 회귀 없음 (분리됨). | D6 code-tester R2 (2026-05-03) | 중간 (08_leftarmVLA 트리거) | 미완 |
```

### R3 처리 안 함 사유

code-tester 가 "선택사항" 분류. 현재 사용자 OK prompt 로 복수 device 감지 시 수동 확인 가능하므로 실 회귀 없음. 향후 v4l2 metadata device (홀수 인덱스) 가 문제 될 경우 짝수 우선 필터 도입 검토. 본 cycle 은 처리 X.

### 검증 결과 (cycle 2)

```
python3 -m py_compile dgx/interactive_cli/flows/precheck.py  → OK
ruff check dgx/interactive_cli/flows/precheck.py             → All checks passed!
```

### prod-test-runner 인계 사항

- DGX SSH deploy: `scripts/deploy_dgx.sh` 실행 후 DGX 에 `dgx/interactive_cli/flows/precheck.py` 동기화 확인
- import smoke: `cd ~/smolvla/dgx/interactive_cli && python3 -c "from flows.precheck import teleop_precheck, _run_find_cameras_split; print('OK')"`
- (가능 시) 사용자 walkthrough 재시도: DGX 시연장 이동 후 main.sh 실행, flow 1 → detect_display_mode → flow 3 → precheck option 1 → USB 분리/재연결 → 카메라 영상 확인
- 환경 레벨: `SSH_AUTO` (import smoke) + `PHYS_REQUIRED` (walkthrough)
- BACKLOG 07-#4 cameras.json 연결은 08_leftarmVLA 진입 시 트리거

---

## 주의 사항 + 잔여 리스크

- `_run_find_cameras()` 함수는 삭제하지 않고 유지함. `teleop_precheck()` 내 option 1 분기의 호출만 `_run_find_cameras_split()` 으로 변경. 이전 함수는 향후 deprecation 예정이나 현재 다른 참조 없음.
- cameras.json 의 `index` 필드에 int 대신 str (device path) 가 저장됨 (`/dev/video2` 형식). `record.py` 의 `cam_wrist_left_index` / `cam_overview_index` 가 int 를 기대하는 경우 별도 파싱 필요. record.py 에서 OpenCV `VideoCapture(str_path)` 는 Linux 에서 지원되나 확인 필요.
- `_show_frame()` 의 direct 모드 (`cv2.imshow`) 는 DGX 에 실제 GUI 환경 필요. DGX headless 환경에서는 DISPLAY 미설정으로 이미 ssh 모드로 fallback됨.
- PHYS_REQUIRED: 실 카메라 USB 분리/재연결 검증 + 영상 확인은 사용자 walkthrough 재시도 시.
