# TODO-D6 — Code Test

> 작성: 2026-05-03 17:00 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 이슈 0건. Recommended 개선 사항 3건.

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/precheck.py  → OK
python3 -m py_compile dgx/interactive_cli/flows/entry.py     → OK
python3 -m py_compile dgx/interactive_cli/flows/mode.py      → OK
bash -n dgx/interactive_cli/main.sh                          → PASS
import smoke (precheck + entry functions)                    → OK
SMOLVLA_DISPLAY_MODE=ssh override                            → OK (returned "ssh")
SMOLVLA_DISPLAY_MODE=direct override                        → OK (returned "direct")
SSH_CLIENT 환경변수 → auto_detected="ssh"                    → OK
Enter 입력 → auto_detected 기본값 사용                        → OK
_get_video_devices() → ['/dev/video0', '/dev/video1']        → OK (lerobot upstream 동일 결과)
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/precheck.py entry.py mode.py
→ All checks passed!
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `_run_find_cameras_split` 신규 + teleop_precheck 내 option 1 분기에서 대체 호출 | ✅ | precheck.py L466 신규, teleop_precheck L806 `_run_find_cameras_split(configs_dir, display_mode)` 호출 |
| 2. `detect_display_mode` 신규 + entry.py prompt | ✅ | entry.py L119 신규, dgx 분기 L321 호출 |
| 3. mode.py·precheck.py `display_mode` 인자 전파 | ✅ | `flow3_mode_entry(display_mode="ssh")` + `teleop_precheck(display_mode="ssh")` 기본값 설정 |
| 4. DISPLAY 자동 fallback (entry.py) | ✅ | L171 `selected == "direct" and not os.environ.get("DISPLAY")` → `"ssh"` 전환 + 안내 |
| 5. py_compile + ruff PASS | ✅ | 모두 통과 (위 결과 참조) |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `precheck.py` 모듈 docstring L18 | `{"wrist_left": {"index": <int\|null>}}` 로 기재되어 있으나, `_run_find_cameras_split` 은 실제로 `str path` (예: `/dev/video2`) 또는 `None` 을 저장. docstring 을 `<str path\|null>` 로 수정 권장 |
| R2 | `cameras.json` → `record.py` 연결 단절 | `_run_find_cameras_split` 이 cameras.json 에 `str path` 를 저장하지만, `_run_collect_flow` 는 cameras.json 을 읽지 않고 `cam_wrist_left_index=0, cam_overview_index=1` 하드코딩 전달. 현재 실제 회귀 없음 (분리됨). 단, 향후 cameras.json 읽어 전달하는 코드 추가 시 `_validate_camera_indices(str, str)` 에서 `< 0` 비교 → `TypeError` 발생 위험. 차후 연결 시 `_validate_camera_indices` 를 `int \| str` 수용으로 수정하거나, cameras.json 저장 포맷을 통일해야 함. 본 todo 의 DOD 에는 연결이 명시되지 않아 MAJOR 해당 X, BACKLOG 항목으로 등재 권장 |
| R3 | `_run_find_cameras_split` 복수 device 감지 시 첫 번째 선택 코멘트 | L537 "짝수 인덱스가 영상 device 인 경우가 많으나" 설명 있으나, 실제로 첫 번째(sorted 최솟값)를 사용 — v4l2 metadata device(홀수 인덱스)가 아닌 짝수가 영상이라는 보장이 sorted 에서는 다소 약함. 현재 사용자 OK prompt 로 수동 확인 가능하여 Critical X. 향후 짝수 우선 필터(`[x for x in new_wrist if int(x[-1]) % 2 == 0]`) 방식 검토 권장 |

---

## 세부 검증 결과

### 1. detect_display_mode 정합

- `SSH_CLIENT`/`SSH_TTY` 환경변수 자동 검출: `is_ssh = bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))` — 표준 SSH 환경변수 정확히 사용 (OK)
- Enter 입력 시 default: `raw == ""` → `selected = auto_detected` — 정확히 동작 (OK)
- `SMOLVLA_DISPLAY_MODE` env override (비대화형 우선): `env_override in ("direct", "ssh")` 시 즉시 반환 — 기대대로 동작 (OK)
- DISPLAY 미설정 + direct 선택 시 SSH fallback: `selected == "direct" and not os.environ.get("DISPLAY")` → `"ssh"` + 안내 출력 (OK)
- KeyboardInterrupt 보호: `_prompt_entry` 래퍼에서 `EOFError·KeyboardInterrupt` 처리 (OK)

### 2. _run_find_cameras_split 정합

- USB 분리/재연결 패턴 (1차 wrist, 2차 overview): `baseline → after_wrist` 차집합, `baseline_after_wrist → after_overview` 차집합 — 두 단계 분리 정확히 구현 (OK)
- `_get_video_devices()` 검증:
  - 구현: `sorted(glob.glob("/dev/video*"))` — 현재 환경에서 lerobot upstream `sorted(Path("/dev").glob("video*"), key=lambda p: p.name)` 과 동일 결과 실증 (OK)
  - 단, `key=lambda p: p.name` vs 전체 경로 문자열 정렬: `/dev/video0`, `/dev/video10`, `/dev/video9` 순서에서 차이 가능. 현실적으로 10개 이상 `/dev/video*` 없으므로 실용 문제 X
- `_capture_frame_to_file`: 3-retry + 5-frame warm-up 적절. 각 시도 후 `cap.release()` 호출로 자원 해제 (OK)
- `_show_frame` 분기: direct → `cv2.imshow` + `waitKey(2000)` + `destroyAllWindows()`, ssh → `_capture_frame_to_file` + `xdg-open` subprocess (OK)
- 신규 device 없을 시 사용자 수동 입력 fallback 구현 (OK)

### 3. cameras.json 타입 호환성

현재 코드에서 실제 회귀 없음:
- `_run_find_cameras_split` 이 cameras.json 에 `str path` 저장
- `_run_collect_flow` (mode.py L108-109) 는 cameras.json 을 읽지 않고 `0, 1` 하드코딩 전달
- 따라서 cameras.json 의 str path 가 `_validate_camera_indices` 나 `build_record_args` 에 도달하지 않음
- lerobot upstream `index_or_path: int | Path` 필드로 str path 도 파싱 가능 (draccus 경유 시)
- **현재 단계 회귀 없음 — Recommended R2 로 분류**

### 4. mode.py 전파 정합

- `flow3_mode_entry(script_dir, display_mode="ssh")` 기본값 `"ssh"` — 안전한 fallback (OK)
- `teleop_precheck(script_dir, display_mode=display_mode)` 인자 전달 정합 (OK)
- D1 패치 (`flow2_env_check` 호출) + D4 패치 (`teleop_precheck` 호출) 모두 D6 후에도 보존 (OK)

### 5. entry.py main() 분기 정합

- `detect_display_mode()` 는 dgx 분기 L321 에서 호출 — flow1 (장치 선택) 후, flow2 (env_check) 전
  - 순서: flow0 → flow1 → `detect_display_mode` → `flow2_env_check` → `flow3_mode_entry`
  - 타이밍 적절: flow 초반 결정, env_check 전 (OK)
- orin 분기 (`else:` 블록): `detect_display_mode` 호출 없음 → orin 은 영향 없음 (OK)

### 6. circular dependency

- entry.py: `flows.precheck` 미import (지연 import 사용하지 않음 — 직접 import 없음)
- precheck.py: `flows.entry` 미import
- mode.py: `flows.precheck` 를 함수 내부에서 `from flows.precheck import teleop_precheck as _teleop_precheck` 지연 import — D4 패턴 유지 (OK)
- `_prompt_entry` 를 entry.py 내부에 추가한 이유: entry 모듈에서 input() 보호 래퍼 필요 + precheck import 없이 독립적 구현 (OK)

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/` 미변경 |
| B (자동 재시도 X 영역) | ✅ | `dgx/lerobot/` 미변경, `pyproject.toml` 미변경, `setup_env.sh` 미변경, `deploy_*.sh` 미변경, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 미변경이므로 해당 coupled file 갱신 불필요 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `docs/storage/` 하위 변경 없음 |
| lerobot-reference-usage | ✅ | `_get_video_devices`: lerobot `camera_opencv.py` L301-303 정확 인용; `_capture_frame_to_file`: `_read_from_hardware` L343-348 패턴 인용; `_run_find_cameras_split`: `lerobot_find_cameras.py` L130-151 save_image 패턴 인용. 모두 직접 Read 후 인용 (추측 아님) |

---

## 배포 권장

MINOR_REVISIONS — task-executor 1회 추가 수정 후 prod-test 진입 권장.

수정 권장 사항:
- R1: `precheck.py` 모듈 docstring L18 카메라 형식 설명을 `<str path|null>` 로 수정
- R2: cameras.json → record.py 연결 단절을 BACKLOG 에 명시적 등재 (코드 수정 아니라 문서 메모)
- R3: R3는 선택적 (현재 사용자 OK prompt 로 커버됨) — 수정 불요 판단 시 무시 가능

R1·R2 만 처리해도 READY_TO_SHIP 조건 (Recommended 2건 이하) 충족.
