# TODO-D11 — Prod Test

> 작성: 2026-05-03 17:00 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

## 배포 대상

- DGX

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일: `interactive_cli/flows/teleop.py` 1파일 (2,709 bytes)
- docs/reference/lerobot/ delta: 26,840 bytes (speedup 440.60 — 변경 없음 수준)
- DGX 파일 확인: `/home/laba/smolvla/dgx/interactive_cli/flows/teleop.py` 2026-05-04 16:25 (7966 bytes)

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| A-1. devPC py_compile | `python3 -m py_compile dgx/interactive_cli/flows/teleop.py` | PASS |
| A-2. devPC ruff | `ruff check dgx/interactive_cli/flows/teleop.py` | All checks passed! |
| A-3. devPC bash -n | `bash -n dgx/interactive_cli/main.sh` | PASS |
| A-4. devPC import smoke | `sys.path.insert(0, 'dgx/interactive_cli'); import flows.teleop` | PASS |
| B-1. DGX 배포 | `bash scripts/deploy_dgx.sh` | 성공 (teleop.py 1파일 전송) |
| B-2. DGX sync 확인 | `ssh dgx "ls -la .../teleop.py"` | 존재 확인 (7966 bytes) |
| B-3. DGX py_compile | `ssh dgx "python3 -m py_compile .../teleop.py"` | PASS |
| B-4. DGX import smoke | `ssh dgx "python3 -c 'import flows.teleop'"` | DGX import smoke PASS |
| C-1. KeyboardInterrupt 시뮬 | subprocess.run + SIGINT → except KeyboardInterrupt → return 0 | PASS (return 0 확인) |
| D-1. UI 안내 grep (흐름:) | `grep -A 3 "흐름:" teleop.py` | "Ctrl+C 한 번 누르면 *정상 종료*" 존재 |
| D-2. ※ 안내 grep | `grep "teleop 도중에는"` | L109 "Teleop loop time: ..." 주석 존재 |
| D-3. DGX 측 grep | `ssh dgx "grep -A 3 '흐름:' ...teleop.py"` | 동일 확인 |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. `_run_teleop_script` try/except KeyboardInterrupt → return 0 + 사용자 안내 | yes (grep + 시뮬) | ✅ |
| 2. `flow3_teleoperate` 안내 강화 — Ctrl+C 강조 + lerobot 도중 안내 X 사실 명시 | yes (grep) | ✅ |
| 3. py_compile + ruff PASS | yes (devPC + DGX 양측) | ✅ |
| 4. 사용자 walkthrough 재시도 시 Ctrl+C 후 flow4 prompt 정상 진입 | no (PHYS_REQUIRED — 실물 검증 필요) | → verification_queue |

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D11-E1] teleop walkthrough 재시도 — Ctrl+C 종료 후 flow4 정상 진입 확인 (PHYS_REQUIRED)**
   - 시연장 SO-ARM + 카메라 DGX USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
   - 흐름: flow1 DGX 선택 → flow2 env_check → flow3 mode (1) 수집 → precheck → flow3 텔레오퍼레이션 진입
   - 확인 항목:
     a. teleop 시작 시 "흐름: 1. Enter ... / 2. Ctrl+C 한 번 누르면 *정상 종료* / 3. ..." 안내 출력 확인
     b. "※ teleop 도중에는 'Teleop loop time: ...' 출력만 보이고 종료 안내 X" 주석 출력 확인
     c. run_teleoperate.sh 실행 중 Ctrl+C → "[teleop] Ctrl+C 감지 — teleop 정상 종료 처리." 출력 확인
     d. entry.py 프로세스가 죽지 않고 → flow4_confirm_teleop prompt "입력 ['r'=teleop 재시도 / Enter=다음 단계 (record + 학습) / Ctrl+C=완전 종료]:" 정상 출력 확인
     e. Enter 선택 → flow5 data_kind → flow6 record (G2 single_task UI) → 정상 진행 확인

## CLAUDE.md 준수

- Category B 영역 변경 없음: `dgx/lerobot/`·`pyproject.toml`·`deploy_*.sh` 미변경 ✓
- 변경 파일 (`dgx/interactive_cli/flows/teleop.py`) — Category B 외 영역 → deploy 자율 실행 ✓
- docs/reference/lerobot/ rsync — 실제 전송량 26,840 bytes (>100MB 아님) → 자율 판단 유지 ✓
- Coupled File Rule: teleop.py 는 pyproject.toml·orin/lerobot/ 미포함 → coupled file 갱신 불요 ✓
- Category A·D 위반 없음 ✓
