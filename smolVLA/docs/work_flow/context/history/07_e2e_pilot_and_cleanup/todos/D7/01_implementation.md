# TODO-D7 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

precheck.py + entry.py 3 문제 통합 패치: (a) 카메라 방향 반전 + (b) find-port 자체 로직 + (c) SSH X11 forwarding 지원

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/precheck.py` | M | (a) `_run_find_cameras_split` 방향 반전 + (b) `_run_find_port_self` 신규 + (d) `_show_frame` ssh-x11 분기 추가 |
| `dgx/interactive_cli/flows/entry.py` | M | (c) `detect_display_mode` 3종 확장 (direct/ssh-x11/ssh-file) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓ (lerobot-find-port Read 후 미러 구현)
- Coupled File Rule: `orin/lerobot/` 미변경 → 03_orin_lerobot_diff.md 갱신 불필요 ✓
- 레퍼런스 직접 Read: `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py`
  - 인용: `find_port()` L47 `ports_before = find_available_ports()`, L51 `input()`, L53 `time.sleep(0.5)`, L54-55 `ports_after + ports_diff = list(set(ports_before) - set(ports_after))`, L57-64 len() 분기 (1=검출 / 0=OSError / >1=OSError)
  - 적용: `_run_find_port_self()` 가 동일 패턴을 subprocess 없이 직접 glob 로 구현. OSError 대신 수동 입력 fallback으로 사용자 UX 보호.
  - 변경 이유: lerobot-find-port subprocess 는 내부 `input()` 타이밍이 외부 안내와 분리되어 OSError 빈발 → 자체 구현으로 사용자 흐름 일관화.
- 레퍼런스 직접 Read: `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py`
  - 인용: `find_cameras()` line 301-303 `possible_paths = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)`
  - 적용: `_get_video_devices()` (D6 기존 유지), `_run_find_cameras_split()` 방향 반전에서 동일 패턴 사용.

## 가정 반증 검증 결과

| 가정 | 실제 코드 상태 | 처리 |
|---|---|---|
| (a) `_run_find_cameras_split` 방향이 잘못됨 | D6 구현 = "wrist 연결 → 신규 검출" 방향. spec = "모두 연결 → 분리해서 사라진 것" 방향. **반증 확인** | 함수 전체 재작성 |
| (b) `_run_find_port` 가 subprocess 사용 | 실제 subprocess + 사용자 수동 입력 방식 확인. **반증 확인** | `_run_find_port_self` 신규 추가 + `teleop_precheck` 에서 교체 |
| (c) `detect_display_mode` 가 2종 반환 | 실제 "direct" \| "ssh" 2종. **반증 확인** | 3종 확장 (direct/ssh-x11/ssh-file) + 구형 "ssh" compat |

## 변경 내용 요약

### Part A — `_run_find_cameras_split` 방향 반전 (precheck.py)

기존 D6 구현은 "wrist 만 연결 → baseline → overview 추가" 방향이었으나, spec 및 사용자 walkthrough 분석에 따라 **lerobot-find-port 패턴과 동일하게** "모두 연결 상태에서 하나씩 분리해서 사라진 것 검출" 방향으로 전체 재작성.

새 흐름: (1) wrist + overview 모두 연결 상태에서 baseline 취득 → (2) wrist 분리 후 Enter → `baseline - after = wrist device` → (3) wrist 재연결 후 영상 확인 → (4) overview 동일 패턴. 분리 후 `time.sleep(0.5)` 는 lerobot_find_port.py L53 직접 미러.

baseline 없는 경우 (카메라 미연결) 에는 수동 입력 fallback 제공. 복수 device 사라진 경우 목록 제시 + 선택 UI.

### Part B — `_run_find_port_self` 신규 (precheck.py)

`_run_find_port_self()` 신규 함수 추가 (기존 `_run_find_port` 보존). `teleop_precheck()` 에서 `_run_find_port()` → `_run_find_port_self()` 로 교체.

lerobot_find_port.py `find_port()` L47-L64 패턴을 glob 직접 구현으로 미러:
- `glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')` 로 baseline 취득
- follower / leader 순서로 분리 → `baseline - after` → 포트 결정
- 분리 → `time.sleep(0.5)` → 재연결 → baseline 갱신 → 다음 arm

OSError 발생 대신 수동 입력 fallback (0개=직접 입력, >1개=목록 선택) 으로 UX 보호.

### Part C — `detect_display_mode` 3종 확장 (entry.py)

기존 2종 ("direct" | "ssh") → 3종 ("direct" | "ssh-x11" | "ssh-file") 확장.

검출 로직:
- `SSH_CLIENT` 또는 `SSH_TTY` 미설정 → "direct"
- SSH + `DISPLAY=localhost:N` → "ssh-x11" (X11 forwarding 활성)
- SSH + 그 외 → "ssh-file"

구형 `SMOLVLA_DISPLAY_MODE=ssh` 는 "ssh-file" 로 compat 처리.
사용자 안내에 `ssh -Y dgx` / `ssh -X dgx` 접속 방법 추가.

### Part D — `_show_frame` ssh-x11 분기 + fallback (precheck.py)

`display_mode == "ssh-x11"` 분기 추가: `cv2.imshow` 시도 → `cv2.error` 발생 시 `ssh-file` 로 자동 fallback + 안내 출력. 재귀 호출 패턴 (`_show_frame(..., "ssh-file", ...)`) 으로 구현.

`display_mode in ("direct", "ssh-x11")` 공통 처리 후 fallback 분기.

## code-tester 검증 권장 사항

- 정적: `py_compile` PASS + `ruff check` PASS (모두 완료)
- import smoke: `detect_display_mode` SMOLVLA_DISPLAY_MODE 4종 override 테스트 PASS
- 자동 검출 로직 단위 검증:
  - `SSH_CLIENT` + `DISPLAY=localhost:10.0` → `ssh-x11` PASS
  - `SSH_TTY` + no DISPLAY → `ssh-file` PASS
  - 로컬 + `DISPLAY=:0` → `direct` PASS
- DOD 충족 확인:
  - (a) `_run_find_cameras_split` 함수 본문에 "분리해서 검출" 흐름 (`baseline - after_disconnect`) 확인
  - (b) `_run_find_port_self` 존재 + `teleop_precheck` 에서 호출 확인
  - (c) `detect_display_mode` 3종 반환 + ssh-x11 분기 확인
  - D6 변경 보존: `_get_video_devices`, `_capture_frame_to_file`, `display_mode` 인자 경로 유지 확인
- DGX deploy + import smoke (prod-test-runner 위임)
- 실 카메라 검증: PHYS_REQUIRED — 사용자 walkthrough 재시도 시 게이트 4 검증

## 직전 피드백 반영

해당 없음 (cycle 1).
