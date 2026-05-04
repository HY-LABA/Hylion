# TODO-D7 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건 / Recommended 이슈: 2건

---

## 단위 테스트 결과

```
py_compile precheck.py  → exit 0 (PASS)
py_compile entry.py     → exit 0 (PASS)

import smoke:
  from flows import precheck     → PASS
  from flows.entry import detect_display_mode → PASS

함수 존재 확인:
  _run_find_cameras_split       PASS
  _run_find_port_self           PASS
  _run_find_port (구 함수 보존)  PASS
  _get_video_devices (D6)       PASS
  _capture_frame_to_file (D6)   PASS
  _show_frame                   PASS
  teleop_precheck               PASS

detect_display_mode 환경변수 override 4종:
  SMOLVLA_DISPLAY_MODE=ssh     → ssh-file  PASS (구형 compat)
  SMOLVLA_DISPLAY_MODE=direct  → direct    PASS
  SMOLVLA_DISPLAY_MODE=ssh-x11 → ssh-x11  PASS
  SMOLVLA_DISPLAY_MODE=ssh-file → ssh-file PASS

detect_display_mode 자동 검출 3종 (로직 단위):
  SSH_CLIENT + DISPLAY=localhost:10.0 → ssh-x11  PASS
  SSH_TTY + no DISPLAY               → ssh-file  PASS
  no SSH + DISPLAY=:0                → direct    PASS

teleop_precheck 호출 체인 확인:
  _run_find_port_self 호출        PASS (구 _run_find_port 교체됨)
  구 _run_find_port 직접 호출 없음 PASS
  _run_find_cameras_split 호출    PASS

_run_find_cameras_split 패턴 검증:
  time.sleep(0.5) — lerobot L53 미러        PASS
  baseline - after_wrist_disconnect 차집합   PASS
  baseline_restored 갱신 후 overview 분리    PASS
  len(wrist_removed) 1/0/>1 분기            PASS
  _show_frame + [Y/n] 사용자 확인 UI        PASS

_run_find_port_self 패턴 검증:
  glob.glob /dev/ttyACM* + /dev/ttyUSB*    PASS
  follower → leader 순서                    PASS
  time.sleep(0.5) — lerobot L53 미러        PASS
  baseline - after_disconnect 차집합         PASS
  raise OSError 없음 (docstring 언급만)      PASS
  baseline 재연결 후 갱신                    PASS
  len(removed) 1/0/>1 분기                  PASS

_show_frame 검증:
  3종 display_mode 처리 (direct/ssh-x11/ssh-file) PASS
  cv2.imshow 사용                                  PASS
  cv2.error → ssh-file fallback 재귀               PASS
  ssh-x11 실패 시 ssh -Y 재접속 안내              PASS
  ssh-file → _capture_frame_to_file + xdg-open    PASS

D6 회귀 확인:
  _get_video_devices /dev/video* glob              PASS
  _capture_frame_to_file 서명 보존                 PASS
  _show_frame display_mode 인자 보존               PASS
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/precheck.py dgx/interactive_cli/flows/entry.py
→ All checks passed!  exit 0
```

mypy: 대상 파일이 strict mypy 범위 외 (lerobot CLAUDE.md §Notes — dgx/interactive_cli/ 미포함). 미실행.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) `_run_find_cameras_split` 방향 반전 — 모두 연결 → 분리해서 검출 | ✅ | baseline - after_wrist_disconnect 패턴, time.sleep(0.5) L53 미러, baseline_restored 재취득 후 overview 분리 |
| (a) 복수 device removed 시 선택 UI | ✅ | wrist_removed / overview_removed 복수 분기, 번호 선택 UI 구현 |
| (b) `_run_find_port_self` 신규 — subprocess 회피 glob 직접 | ✅ | glob.glob /dev/ttyACM* + /dev/ttyUSB*, find_port() L47-L64 패턴 미러 |
| (b) follower → leader 순서 + 분리/재연결 사이클 | ✅ | for arm_label in ("follower", "leader") |
| (b) OSError 대신 수동 입력 fallback | ✅ | raise OSError 없음, 0개/복수 모두 직접 입력 또는 목록 선택 |
| (b) `teleop_precheck()` 에서 `_run_find_port_self` 호출 교체 | ✅ | 구 `_run_find_port` 미호출, `_run_find_port_self` 호출 확인 |
| (b) 구 `_run_find_port` 보존 여부 | ✅ | 함수 보존 (제거 X) |
| (c) `detect_display_mode` 3종 반환 — direct/ssh-x11/ssh-file | ✅ | 3종 반환 구현 |
| (c) SSH_CLIENT/SSH_TTY + DISPLAY=localhost:N → ssh-x11 자동 검출 | ✅ | is_ssh + display.startswith("localhost:") 패턴 |
| (c) 구형 SMOLVLA_DISPLAY_MODE=ssh compat → ssh-file | ✅ | env_override == "ssh" → return "ssh-file" |
| (c) ssh -Y 사용법 안내 출력 | ✅ | is_ssh + auto_detected == "ssh-file" 시 ssh -Y dgx 안내 |
| (d) `_show_frame` ssh-x11 분기 + cv2.error → ssh-file fallback | ✅ | except cv2.error → _show_frame(..., "ssh-file", ...) 재귀 |
| D6 _get_video_devices 보존 | ✅ | /dev/video* glob 패턴 유지 |
| D6 _capture_frame_to_file 보존 | ✅ | 서명 미변경 |
| 정적 검증 PASS | ✅ | py_compile + ruff 모두 exit 0 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `precheck.py:281-285` — `_get_serial_ports()` 내부 함수 | lerobot `find_available_ports()` 는 Linux 에서 `/dev/tty*` 전체를 스캔하나 자체 구현은 `/dev/ttyACM*` + `/dev/ttyUSB*` 만 스캔. SO-ARM USB serial 환경에서 실용적으로 동등하나 `/dev/tty*` 제외 이유(의도적 단순화: 하드웨어 UART ttyS* 불필요)를 docstring에 한 줄 추가 권장. |
| 2 | `precheck.py:955` — `teleop_precheck` 함수 서명 `display_mode: str = "ssh"` | D7 이후 유효값이 3종(direct/ssh-x11/ssh-file)이 되었으나 기본값은 여전히 `"ssh"` (구형). 기능적 문제는 없음(else 분기에서 ssh-file로 처리). 기본값을 `"ssh-file"` 로 변경하면 서명과 실제 동작이 일치. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md` 미변경 |
| B (자동 재시도 X) | ✅ | `dgx/lerobot/` 미변경, `orin/lerobot/` 미변경, `pyproject.toml` 미변경, `setup_env.sh` 미변경, `deploy_*.sh` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 미변경 → 03_orin_lerobot_diff.md 등 갱신 불필요 |
| lerobot-reference-usage | ✅ | `lerobot_find_port.py` L47-L64 직접 Read 후 인용. 인용 라인 번호 실제 파일과 일치. `find_available_ports()` Linux 구현(`/dev/tty*`)도 확인 완료 |
| 옛 룰 (docs/storage/ bash 예시 X) | ✅ | `docs/storage/` 하위 미변경 |

---

## lerobot 인용 정합 검증 결과

`docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` 실제 파일 Read 후 비교:

| 인용 | 실제 라인 | 내용 | 정합 |
|---|---|---|---|
| L47 `ports_before = find_available_ports()` | 47 | `ports_before = find_available_ports()` | ✅ |
| L51 `input()` | 51 | `input()  # Wait for user to disconnect the device` | ✅ |
| L53 `time.sleep(0.5)` | 53 | `time.sleep(0.5)  # Allow some time for port to be released` | ✅ |
| L54-55 `ports_after + ports_diff = set(before) - set(after)` | 54-55 | `ports_after = find_available_ports()` + `ports_diff = list(set(ports_before) - set(ports_after))` | ✅ |
| L57-64 len() 분기 | 57-64 | `len == 1` → port / `== 0` → OSError / else → OSError | ✅ |

비고: `find_available_ports()` Linux 구현은 `Path("/dev").glob("tty*")` (`/dev/tty*` 전체). 자체 구현 `/dev/ttyACM*` + `/dev/ttyUSB*` 는 좁은 하위집합이나 SO-ARM USB serial 환경에서 동등 — Recommended #1 참조.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

검증 필요 항목 (PHYS_REQUIRED):
- 실 카메라 연결 상태에서 `_run_find_cameras_split` 방향 반전 동작 확인 (walkthrough 재시도)
- 실 SO-ARM 연결 상태에서 `_run_find_port_self` 포트 검출 확인
- SSH X11 forwarding (`ssh -Y dgx`) 환경에서 `ssh-x11` 모드 cv2.imshow 동작 확인
