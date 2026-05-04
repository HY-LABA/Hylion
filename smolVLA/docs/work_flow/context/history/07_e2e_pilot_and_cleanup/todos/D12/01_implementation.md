# TODO-D12 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

record.py 가 cameras.json + ports.json 로드 (D9 패턴 record 에 확장) — OpenCVCamera 차단 방지

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/record.py` | M | `_load_configs_for_record` 신설 + `flow6_record` configs_dir 인자 추가 + `build_record_args` follower/leader port 주입 + `_validate_camera_indices` int\|str 확장 |
| `dgx/interactive_cli/flows/mode.py` | M | `_run_collect_flow` 에서 configs_dir 계산 후 `flow6_record` 에 전달 |
| `docs/work_flow/specs/BACKLOG.md` | M | 07 #4 완료 마킹 + 07 #15 신규 (deploy_dgx.sh 덮어쓰기 문제) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경, `orin/lerobot/` 미변경 (본 변경은 `dgx/interactive_cli/` 영역)
- Coupled File Rule: `orin/lerobot/` 미변경으로 `03_orin_lerobot_diff.md` 갱신 불요. `dgx/lerobot/` 미변경.
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/configuration_opencv.py` L61: `index_or_path: int | Path` — int 와 str/Path 경로 둘 다 지원 확인
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py` L158: `cv2.VideoCapture(self.index_or_path, self.backend)` — VideoCapture 가 str 경로도 수용함 확인
  - D9 패턴: `dgx/interactive_cli/flows/precheck.py` L979~1001 `_run_calibrate()` ports.json 로드 패턴 직접 인용

## 변경 내용 요약

### Part A — _load_configs_for_record helper 신설 (record.py)

`precheck.py:_run_calibrate()` 의 D9 패턴 (L979~1001) 을 record 에 동일하게 적용. `cameras.json` (형식: `{"wrist_left": {"index": "/dev/video0"}, "overview": {"index": "/dev/video2"}}`) 과 `ports.json` (형식: `{"follower_port": "/dev/ttyACM1", "leader_port": "/dev/ttyACM0"}`) 을 로드. 파일 미존재 또는 `JSONDecodeError` / `OSError` 시 빈 dict 반환 + 경고 출력 (fallback).

### Part B — flow6_record + build_record_args 확장

`flow6_record` 에 `configs_dir: Path | None = None` 인자 추가. None 이면 기존 hardcoded 동작과 완전 동일. 전달 시 `_load_configs_for_record()` 로 cameras_data / ports_data 로드 후:
- `wrist_left.index` / `overview.index` → `cam_wrist_left_index` / `cam_overview_index` 갱신
- `follower_port` / `leader_port` → `build_record_args()` 에 주입

`build_record_args()` 에 `follower_port` / `leader_port` 기본값 인자 추가 (기본값은 기존 하드코딩 상수 — 기존 호출 호환 유지).

`_validate_camera_indices()` 를 `int | str` 수용으로 확장: int 는 `>= 0`, str 은 `/dev/` 로 시작해야 유효. 기존 `< 0` 비교가 str 에 적용 시 `TypeError` 발생하는 문제 해소 (07 BACKLOG #4 발견).

### Part C — config 출처 안내 출력

`flow6_record` 실행 직전에 cameras/ports 의 출처 (검출 결과 vs hardcoded fallback) 를 명시 출력. 미설정 항목이 있으면 v4l2 메타 device 차단 가능 경고 + precheck 옵션 1 권장 안내.

### Part D — mode.py 연결

`_run_collect_flow(script_dir)` 에서 `configs_dir = script_dir / "configs"` 계산 후 `flow6_record(configs_dir=configs_dir)` 에 전달. `precheck.py:_get_configs_dir(script_dir)` 와 동일한 경로 계산 패턴.

### Part E — BACKLOG 07 #4 완료 + #15 신규

07 BACKLOG #4 (cameras.json 데이터 연결 미완) 완료 마킹.
07 BACKLOG #15 신규: deploy_dgx.sh 가 `dgx/interactive_cli/configs/` 를 rsync --delete 로 덮어쓰는 문제 — precheck 옵션 1 재실행으로 우회 가능하나 영구 fix 위해 rsync exclude 패턴 추가 권장.

## code-tester 입장에서 검증 권장 사항

- 정적: `python3 -m py_compile dgx/interactive_cli/flows/record.py` PASS
- lint: `ruff check dgx/interactive_cli/flows/record.py dgx/interactive_cli/flows/mode.py` PASS
- import smoke:
  ```
  python3 -c "import sys; sys.path.insert(0,'dgx/interactive_cli'); import flows.record as r; print(r._load_configs_for_record, r.flow6_record)"
  python3 -c "import sys; sys.path.insert(0,'dgx/interactive_cli'); import flows.mode as m; print(m._run_collect_flow)"
  ```
- 단위 검증 후보:
  - `_validate_camera_indices(0, 1)` → True
  - `_validate_camera_indices("/dev/video0", "/dev/video2")` → True
  - `_validate_camera_indices("video0", "/dev/video2")` → False (str 경로 /dev/ 미시작)
  - `_validate_camera_indices(-1, 0)` → False (int 음수)
  - `_load_configs_for_record(Path("/nonexistent"))` → ({}, {}) (빈 dict, 예외 없음)
- DOD 항목 충족 확인:
  1. record.py 가 cameras.json + ports.json 로드 + hardcoded fallback — configs_dir=None 시 기존 동작 동일 확인
  2. 사용자 안내 출력 (config source 명시) — flow6_record 헤더 직후 출력 확인
  3. BACKLOG 07 #15 추가 — BACKLOG.md 확인
  4. py_compile + ruff PASS — 위 명령 실행
  5. 사용자 walkthrough 재시도 시 cameras.json 검출 결과 사용 (PHYS_REQUIRED — 사용자 검증)
