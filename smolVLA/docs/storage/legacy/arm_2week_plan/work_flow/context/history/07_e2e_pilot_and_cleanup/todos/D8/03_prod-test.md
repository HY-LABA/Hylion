# TODO-D8 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 전 항목 PASS. PHYS_REQUIRED 1건 시연장 대기.

---

## 배포 대상

DGX

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일: `interactive_cli/flows/precheck.py` + `interactive_cli/configs/cameras.json` + `interactive_cli/configs/ports.json` + `interactive_cli/flows/` (디렉터리)
- 전송량: sent 6,406 bytes / speedup=33.25
- DGX 타임스탬프: 2026-05-04 14:05
- `docs/reference/lerobot/` rsync: sent 26,840 bytes / speedup=440.60 (변경분 없음 — 기존 동일)
- Category B 영역 변경 여부: 없음 (`dgx/lerobot/` 미변경, `setup_train_env.sh` 미변경) — 자율 배포 정책 적용

---

## 자동 비대화형 검증 결과

### A. devPC 정적 검증

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile | `python3 -m py_compile dgx/interactive_cli/flows/precheck.py` | PASS (exit 0) |
| ruff lint | `ruff check dgx/interactive_cli/flows/precheck.py` | All checks passed! |
| bash -n main.sh | `bash -n dgx/interactive_cli/main.sh` | PASS (exit 0) |

### B. devPC import smoke

| 검증 | 명령 | 결과 |
|---|---|---|
| import 6 함수 | `from flows.precheck import _get_streamable_video_devices, _run_find_cameras_split, _get_video_devices, _show_frame, _run_find_port_self, teleop_precheck` | PASS |
| `_get_streamable_video_devices()` 호출 | devPC 직접 실행 | `['/dev/video0', '/dev/video1']` — 2개 반환 (devPC 내장 카메라) |

### C. DGX 배포 + 정적 검증

| 검증 | 명령 | 결과 |
|---|---|---|
| DGX py_compile | `ssh dgx "python3 -m py_compile .../precheck.py"` | PASS |
| DGX 파일 타임스탬프 | `ssh dgx "ls -la .../precheck.py"` | 2026-05-04 14:05 (49740 bytes) |
| DGX import smoke | `ssh dgx python3 -c "from flows.precheck import _get_streamable_video_devices, _run_find_cameras_split, _get_video_devices, _show_frame"` | PASS — 4 함수 |

### D. DGX `_get_streamable_video_devices()` 실 실행

| 검증 | 결과 |
|---|---|
| DGX 실 실행 결과 | `['/dev/video0', '/dev/video2']` — 2개 반환 |
| 메타 device 필터링 | video1·video3 필터링 성공 (streamable 아님) |
| 기대 동작 정합 | main stream device 만 반환 — PASS |

### E. deepdiff 9.0.0 호환성 spot-check

| 검증 | 명령 | 결과 |
|---|---|---|
| deepdiff 버전 확인 | `python3 -c "import deepdiff; print(deepdiff.__version__)"` | 9.0.0 |
| 기본 API | `DeepDiff({"a":1}, {"a":2})` | `{'values_changed': {"root['a']": {'new_value': 2, 'old_value': 1}}}` — PASS |
| exclude_regex_paths 패턴 | `DeepDiff(..., exclude_regex_paths=[r".*\['info'\]$"])` | info 키 제외 + a 키 변경 감지 정상 — PASS |
| lerobot motors_bus.py 패턴 grep | `grep -n "DeepDiff" .../motors_bus.py` | L394: `DeepDiff(dict1, dict2)` — 기본 생성자 |
| lerobot control_utils.py 패턴 grep | `grep -n "DeepDiff" .../control_utils.py` | L238: `DeepDiff(..., exclude_regex_paths=[...])` — 9.x 안정 API |
| 종합 호환성 판정 | — | PASS — 기능 파손 위험 없음 |

### F. menu walkthrough 부분 시뮬

| 검증 | 결과 |
|---|---|
| flow1 → detect_display_mode (ssh-file 자동) | PASS |
| flow2 preflight 5/5 PASS | PASS (RAM 111GB·디스크 3311GB·Walking RL 미실행·Ollama 미점유) |
| flow3 mode 선택 화면 진입 | PASS |
| flow4 데이터셋 선택 화면 진입 | PASS |
| flow3 종료(5) → `[mode] 종료합니다.` | PASS |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| (II) lerobot pyproject.toml extras 직접 확인 + deepdiff transitive 포함 | yes (정적 Read + 코드 검사) | ✅ 충족 (D8 04_dgx_lerobot_diff.md 항목 기록) |
| (II) setup_train_env.sh 변경 불필요 사유 명시 | yes (정적) | ✅ 충족 (01_implementation.md + 04_dgx_lerobot_diff.md 기록) |
| (III) `_get_streamable_video_devices` 신규 구현 | yes (py_compile + DGX 실 실행) | ✅ 충족 (video0·video2 반환, video1·video3 필터링 확인) |
| (III) `_run_find_cameras_split` baseline·baseline_restored `_get_streamable_video_devices()` 사용 | yes (정적 grep) | ✅ 충족 (L762·L861 확인) |
| (III) after_disconnect `_get_video_devices()` 유지 | yes (정적 grep) | ✅ 충족 (L794·L882 확인) |
| (III) `_get_video_devices()` backward-compat 보존 | yes (정적) | ✅ 충족 (L450-466 변경 없음) |
| (IV) `_show_frame` ssh-file VSCode remote-ssh 안내 + code -r 명시 | yes (정적) | ✅ 충족 (L679-681 확인) |
| (IV) xdg-open poll() 결과 명시 보고 | yes (정적) | ✅ 충족 (L696-706 rc=None/0/기타 분기) |
| (IV) X11 fallback libgtk2 원인 후보 추가 | yes (정적) | ✅ 충족 (L665-667 확인) |
| deepdiff 9.0.0 lerobot 호환성 확인 | yes (DGX 실 실행 + 정적 grep) | ✅ PASS (기본 생성자·exclude_regex_paths 안정 API) |
| py_compile PASS | yes | ✅ PASS |
| ruff PASS | yes | ✅ PASS |
| `04_dgx_lerobot_diff.md` D8 항목 추가 | yes (정적) | ✅ 충족 ([2026-05-04] 항목) |
| BACKLOG #5·#6 신규 추가 | yes (code-tester 확인 완료) | ✅ 충족 |
| 실 카메라 분리 시 단일 device 검출 (메타 필터링 정합) | no — 사용자 실물 필요 | → verification_queue |
| ssh-file 모드 영상 미리보기 안내 육안 확인 | no — 사용자 실물 필요 | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D8-1] 실 카메라 분리 시 메타 device 필터링 + 단일 device 검출 확인** (PHYS_REQUIRED — 시연장 이동 시):
   - DGX + SO-ARM + 카메라 USB 직결 환경에서 `bash dgx/interactive_cli/main.sh`
   - `[사전 스캔] 영상 스트림 가능 device 확인 중...` 출력 후 baseline (streamable device 만) 표시
   - wrist USB 분리 후 Enter — `[검출] wrist device: /dev/videoN` (단일 device, 메타 제외) 확인
   - `cat cameras.json` → wrist·overview 각각 단일 device 경로 갱신 확인

2. **[D8-2] ssh-file 모드 영상 확인 방법 안내 출력 확인** (PHYS_REQUIRED — 시연장 이동 시):
   - 영상 capture 후 VSCode remote-ssh 안내 메시지 출력 확인
   - `code -r /path/to/...jpg` 명령 표시 확인
   - xdg-open 결과 보고 (`(xdg-open 실행됨 — VSCode remote 미리보기 창 확인)` 또는 rc 명시) 확인
   - VSCode remote-ssh Explorer 에서 jpg 파일 클릭 → 미리보기 가능 여부 육안 확인

(D4·D6·D7 PHYS_REQUIRED walkthrough 와 통합 검증 권장)

---

## CLAUDE.md 준수

| 체크 | 결과 |
|---|---|
| Category A 미변경 (`docs/reference/`, `.claude/`) | yes — 정적 확인 |
| Category B 미변경 (`dgx/lerobot/`, `setup_train_env.sh`, `deploy_*.sh` 내용 변경 없음) | yes |
| Coupled File Rules (04_dgx_lerobot_diff.md D8 항목 추가) | yes (task-executor 산출물 확인) |
| prod-test-runner 자율성 정책 — Category B 외 배포 자율 실행 | yes |
| deploy_dgx.sh 내용 변경 없음 (rsync 실행만) | yes |
| docs/reference/lerobot/ rsync 14MB < 100MB 임계값 | yes — 자율 실행 적용 |
