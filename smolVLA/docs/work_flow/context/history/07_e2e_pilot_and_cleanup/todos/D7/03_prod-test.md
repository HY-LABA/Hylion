# TODO-D7 — Prod Test

> 작성: 2026-05-04 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

---

## 배포 대상

- DGX (변경 파일: `dgx/interactive_cli/flows/precheck.py`, `dgx/interactive_cli/flows/entry.py`)
- Category B 영역 미변경 — 자율 배포 가능 (deploy_dgx.sh 실행)

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송: `interactive_cli/flows/entry.py` (15K), `interactive_cli/flows/precheck.py` (44K), `configs/cameras.json`, `configs/ports.json`
- `docs/reference/lerobot/` rsync: incremental diff only (26,840 bytes sent / 11.9MB total speedup 440x — 실질 전송 미미)
- DGX 파일 타임스탬프: 2026-05-04 13:19

---

## 자동 비대화형 검증 결과

| 항목 | 환경 | 명령 | 결과 |
|---|---|---|---|
| A-1: py_compile precheck.py | AUTO_LOCAL | `python -m py_compile dgx/interactive_cli/flows/precheck.py` | PASS (exit 0) |
| A-2: py_compile entry.py | AUTO_LOCAL | `python -m py_compile dgx/interactive_cli/flows/entry.py` | PASS (exit 0) |
| A-3: ruff 2파일 | AUTO_LOCAL | `ruff check precheck.py entry.py` | `All checks passed!` |
| A-4: bash -n deploy_dgx.sh | AUTO_LOCAL | `bash -n scripts/deploy_dgx.sh` | PASS (exit 0) |
| B-2: SMOLVLA_DISPLAY_MODE=direct | AUTO_LOCAL | 로직 단위 | `direct` PASS |
| B-3: SMOLVLA_DISPLAY_MODE=ssh-x11 | AUTO_LOCAL | 로직 단위 | `ssh-x11` PASS |
| B-4: SMOLVLA_DISPLAY_MODE=ssh-file | AUTO_LOCAL | 로직 단위 | `ssh-file` PASS |
| B-5: SMOLVLA_DISPLAY_MODE=ssh (구형) | AUTO_LOCAL | 로직 단위 | `ssh-file` (compat) PASS |
| B-6: SSH_CLIENT + DISPLAY=localhost:10.0 | AUTO_LOCAL | 로직 단위 | `ssh-x11` PASS |
| B-7: SSH_CLIENT + DISPLAY='' | AUTO_LOCAL | 로직 단위 | `ssh-file` PASS |
| B-8: no SSH + DISPLAY=:0 | AUTO_LOCAL | 로직 단위 | `direct` PASS |
| C-1: DGX 배포 sync 확인 | SSH_AUTO | `ssh dgx ls -lh entry.py precheck.py` | 15K + 44K 존재 확인 |
| C-2: DGX py_compile | SSH_AUTO | `ssh dgx python -m py_compile ...` | PASS |
| C-3: DGX 함수 존재 7종 | SSH_AUTO | import smoke | 전 항목 PASS |
| C-4: DGX detect_display_mode override 3종 | SSH_AUTO | import smoke | ssh-x11/ssh-file/ssh→ssh-file PASS |
| D-1: DGX menu walkthrough (flow1→display_mode→env_check→flow3 종료) | SSH_AUTO | `printf '2\n\n3\n' \| timeout 30 bash main.sh` | detect_display_mode SSH=True DISPLAY='' → ssh-file 자동 검출 + flow2 env_check 5/5 PASS + flow3 종료 정상 PASS |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| (a) `_run_find_cameras_split` 방향 반전 — baseline→분리→검출 패턴 | 함수 존재 + code-tester 소스 검증 | ✅ |
| (a) 복수 device removed 시 선택 UI | code-tester 소스 검증 | ✅ |
| (b) `_run_find_port_self` 신규 — glob 직접 | 함수 존재 SSH_AUTO 확인 | ✅ |
| (b) follower → leader 순서 + 분리/재연결 사이클 | code-tester 소스 검증 | ✅ |
| (b) `teleop_precheck()` 에서 `_run_find_port_self` 호출 교체 | code-tester 소스 검증 | ✅ |
| (b) 구 `_run_find_port` 보존 | SSH_AUTO 함수 존재 확인 | ✅ |
| (c) `detect_display_mode` 3종 반환 | AUTO_LOCAL 로직 단위 + SSH_AUTO override | ✅ |
| (c) SSH_CLIENT + DISPLAY=localhost:N → ssh-x11 | AUTO_LOCAL 로직 단위 | ✅ |
| (c) 구형 ssh compat → ssh-file | AUTO_LOCAL 로직 단위 + SSH_AUTO | ✅ |
| (c) ssh -Y 안내 출력 | code-tester 소스 검증 | ✅ |
| (d) `_show_frame` ssh-x11 분기 + cv2.error → ssh-file fallback | code-tester 소스 검증 | ✅ |
| D6 _get_video_devices 보존 | SSH_AUTO 함수 존재 확인 | ✅ |
| D6 _capture_frame_to_file 보존 | SSH_AUTO 함수 존재 확인 | ✅ |
| 정적 검증 PASS | AUTO_LOCAL py_compile + ruff | ✅ |
| 실 카메라 분리/재연결 walkthrough | PHYS_REQUIRED | → verification_queue |
| SSH X11 forwarding cv2.imshow 동작 | PHYS_REQUIRED | → verification_queue |
| 실 SO-ARM 포트 검출 (_run_find_port_self) | PHYS_REQUIRED | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

D4 게이트 4 통합 항목 — D6 PHYS_REQUIRED 대체 + D7 방향 반전 추가 반영:

1. **[D7-1] 실 카메라 분리/재연결 walkthrough (D4 게이트 4)** — DGX + 카메라 직결 환경에서:
   ```bash
   cd ~/smolvla && bash dgx/interactive_cli/main.sh
   ```
   흐름: flow1 DGX 선택 → detect_display_mode (SSH=True → ssh-file 또는 ssh-x11 선택) → flow2 env_check PASS → flow3 mode (1) 수집 → precheck (1) 새 수집 시작 → `_run_find_port_self` (follower/leader USB 분리/재연결 포트 검출) → `_run_find_cameras_split` 실행:
   - **D7 핵심**: wrist + overview 모두 연결 상태에서 wrist 분리 → 사라진 device 검출 → 재연결 → 영상 확인 (ssh-file: jpg 경로 출력)
   - overview 분리 → 사라진 device 검출 → 재연결 → 영상 확인
   - `cat ~/smolvla/dgx/interactive_cli/configs/cameras.json` 갱신 확인
   - calibrate [y/N] → N → teleop 진입 정상 확인 (feetech 설치 효과로 ImportError X)

2. **[D7-2] SSH X11 forwarding 모드 검증** (옵션, ssh -Y dgx 접속 환경에서):
   ```bash
   ssh -Y dgx "cd ~/smolvla && bash dgx/interactive_cli/main.sh"
   ```
   기대: detect_display_mode → DISPLAY=localhost:N 자동 검출 → `ssh-x11` → cv2.imshow 시도. X11 실패 시 ssh-file fallback 안내 출력.

---

## CLAUDE.md 준수

| 항목 | 체크 |
|---|---|
| Category B 영역 변경된 deploy | dgx/interactive_cli/ 만 변경 — Category B 외. 자율 배포 실행 |
| Category D 명령 (rm -rf 등) 사용 X | 사용 안 함 |
| Category A 영역 수정 X | docs/reference/ 미변경. .claude/ 미변경 |
| deploy_dgx.sh 내 `docs/reference/lerobot/` rsync | incremental diff only (신규 파일 없음, 실질 전송 26KB). 수백 MB 대용량 다운로드 아님 — 자율 판단 |
| 자율 영역만 사용 | SSH read-only + pytest·import smoke + deploy (Category B 외) 전부 자율 범위 |
