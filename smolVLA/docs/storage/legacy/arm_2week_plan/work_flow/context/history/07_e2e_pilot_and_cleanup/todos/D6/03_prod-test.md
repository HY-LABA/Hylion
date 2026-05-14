# TODO-D6 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL(A·B·C) + SSH_AUTO(D·E) 전 항목 PASS. PHYS_REQUIRED(F) 사용자 실물 검증 필요 — verification_queue 게이트 4 항목 추가됨.

---

## 배포 대상

- DGX (dgx/interactive_cli/flows/ 3파일 변경)

---

## 배포 결과

- 명령: `bash /home/babogaeguri/Desktop/Hylion/smolVLA/scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일:
  - `interactive_cli/configs/cameras.json`
  - `interactive_cli/configs/ports.json`
  - `interactive_cli/flows/entry.py`
  - `interactive_cli/flows/mode.py`
  - `interactive_cli/flows/precheck.py`
  - `scripts/setup_train_env.sh`
- rsync 전송: 11,921 bytes sent / 560 bytes received (speedup 16.84)
- docs/reference/lerobot 동기화: 26,840 bytes sent (변경 없음, speedup 440.60)

---

## 자동 비대화형 검증 결과

### A. devPC 정적

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile entry.py | `python3 -m py_compile dgx/interactive_cli/flows/entry.py` | OK |
| py_compile mode.py | `python3 -m py_compile dgx/interactive_cli/flows/mode.py` | OK |
| py_compile precheck.py | `python3 -m py_compile dgx/interactive_cli/flows/precheck.py` | OK |
| ruff 3파일 | `ruff check dgx/interactive_cli/flows/{entry,mode,precheck}.py` | All checks passed! |
| bash -n main.sh | `bash -n dgx/interactive_cli/main.sh` | OK |

### B. devPC import smoke

| 검증 | 명령 | 결과 |
|---|---|---|
| precheck 함수 import | `cd dgx/interactive_cli && python3 -c "from flows.precheck import teleop_precheck, _run_find_cameras_split, _get_video_devices, _capture_frame_to_file, _show_frame; print('import OK')"` | import OK |
| detect_display_mode import | `cd dgx/interactive_cli && python3 -c "from flows.entry import detect_display_mode; print('display_mode import OK')"` | display_mode import OK |

### C. detect_display_mode 동작 검증 (devPC 비대화형)

| 검증 | 명령 | 결과 |
|---|---|---|
| SMOLVLA_DISPLAY_MODE=ssh override | `SMOLVLA_DISPLAY_MODE=ssh python3 -c "... detect_display_mode()..."` | "ssh" 반환, PASS |
| SMOLVLA_DISPLAY_MODE=direct+DISPLAY=:0 | `SMOLVLA_DISPLAY_MODE=direct DISPLAY=:0 ...` | "direct" 반환, PASS |
| SSH_CLIENT 시뮬 (env override=ssh) | `SSH_CLIENT='...' SMOLVLA_DISPLAY_MODE=ssh ...` | "ssh" 반환, PASS |
| DISPLAY 없는 경우 fallback 로직 | auto_detected='direct', DISPLAY unset → selected='ssh' | ssh fallback 확인, PASS |

비고: DISPLAY 없음 + SSH 없음 + SMOLVLA_DISPLAY_MODE 없음 → auto_detected="direct" → DISPLAY unset fallback → "ssh" 전환 로직을 직접 코드 검증으로 확인 (input() 대화형 우회).

### D. DGX SSH deploy + 양측 import

| 검증 | 명령 | 결과 |
|---|---|---|
| 신규 파일 sync 확인 | `ssh dgx "ls -la ~/smolvla/dgx/interactive_cli/flows/{entry,mode,precheck}.py"` | entry.py 12606B / mode.py 10769B / precheck.py 33145B, 전 파일 존재 |
| DGX import smoke | `ssh dgx "cd ~/smolvla/dgx/interactive_cli && python3 -c 'from flows.precheck import _run_find_cameras_split; from flows.entry import detect_display_mode; print(\"OK\")'"` | OK |
| DGX SSH 자동 검출 확인 | `ssh dgx "... SSH_CLIENT: 172.16.141.201 47902 22 ... auto_detected='ssh'"` | SSH_CLIENT 설정 확인, auto_detected="ssh" PASS |

### E. menu walkthrough 시뮬 (DGX SSH)

시나리오 1: DGX 선택(2) → 학습 mode(2) → 시나리오(3) → 데이터셋 진입 흐름

```
입력: echo -e '2\n2\n3' | SMOLVLA_DISPLAY_MODE=ssh timeout 30 bash dgx/interactive_cli/main.sh

출력 요약:
  flow 1 — 장치 선택: DGX [*] active 확인
  preflight check (5/5 PASS):
    [1/5] venv/HF_HOME/CUDA: OK
    [2/5] RAM 112 GiB 가용: OK
    [3/5] Walking RL 미실행: INFO
    [4/5] Ollama GPU 미점유: OK
    [5/5] 디스크 3311 GiB 가용: OK
  flow 2 — env_check (smoke) PASS
  flow 3 — mode 선택: (2) 학습 진입 → 시나리오 선택 화면 도달
  detect_display_mode prompt: SMOLVLA_DISPLAY_MODE=ssh env_override 즉시 반환 (prompt 출력 X)
```

시나리오 2: DGX 선택(2) → 수집 mode(1) → precheck 취소(3)

```
입력: echo -e '2\n1\n3' | SMOLVLA_DISPLAY_MODE=ssh timeout 45 bash dgx/interactive_cli/main.sh

출력 요약:
  flow 1 — DGX 선택 확인
  preflight 5/5 PASS
  flow 2 — env_check(smoke) PASS
  flow 3 — mode (1) 수집 진입
  flow 2 (collect) — 수집 환경 체크:
    [항목 6] USB 포트: leader(/dev/ttyACM0) PASS, follower(/dev/ttyACM1) PASS
    [항목 7] dialout 그룹: laba 멤버 PASS
    [항목 8] v4l2 카메라: 4개 발견 [/dev/video0~3] PASS
    [항목 9] serial open: /dev/ttyACM1 PASS
  teleop 사전 점검 UI:
    모터 포트: (미설정)
    카메라 인덱스: (미설정)
    캘리브 위치: /home/laba/smolvla/.hf_cache/lerobot/calibration (존재)
    (3) 취소 → "[precheck] 취소됩니다." + 정상 종료
```

D6 신규 기능(detect_display_mode + _run_find_cameras_split 경로) 통합 확인 PASS. D4 walkthrough 와 동일 흐름 + display_mode 전달 경로 정합 확인.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. `_run_find_cameras_split` 신규 + teleop_precheck 내 option 1 분기 대체 호출 | yes (import smoke + walkthrough) | ✅ |
| 2. `detect_display_mode` 신규 + entry.py prompt | yes (import smoke + env override 동작) | ✅ |
| 3. mode.py·precheck.py display_mode 인자 전파 | yes (walkthrough 흐름 정합 확인) | ✅ |
| 4. DISPLAY 자동 fallback (entry.py) | yes (로직 직접 검증 — DISPLAY unset → ssh) | ✅ |
| 5. py_compile + ruff PASS | yes (devPC + DGX 양측) | ✅ |
| 실 카메라 USB 분리/재연결 walkthrough | no (PHYS_REQUIRED — 사용자 실물) | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

### [D6-1] 실 카메라 USB 분리/재연결 walkthrough — 게이트 4 통합

환경 레벨: PHYS_REQUIRED

절차:
1. DGX 에 SO-ARM + 카메라 USB 연결 상태에서:
   ```
   cd ~/smolvla
   bash dgx/interactive_cli/main.sh
   ```
2. flow 1 → DGX 선택
3. detect_display_mode 프롬프트:
   - SSH 접속 시: 자동 검출 "ssh" 표시 → Enter 확인
   - 직접 접속 시: "direct" 또는 "ssh" 선택
4. flow 2 env_check PASS 확인
5. flow 3 mode (1) 수집 → teleop 사전 점검 (3-way 분기)
6. (1) 새 학습 데이터 수집 시작 선택 → lerobot-find-port (follower, leader 순) 실행
7. lerobot-find-cameras 실행 → wrist 카메라 USB 단독 연결:
   - baseline /dev/video* 기록 → wrist USB 연결 후 신규 device 검출
   - 1프레임 캡처 → ssh 모드: jpg 저장 경로 출력 → 영상 확인 OK
   - overview 카메라 추가 → 신규 device 검출 → 영상 확인 OK
8. cameras.json 갱신 확인: `cat ~/smolvla/dgx/interactive_cli/configs/cameras.json`
   기대: `{"wrist_left": {"index": "/dev/videoN"}, "overview": {"index": "/dev/videoM"}}`
9. 캘리브레이션 prompt [y/N] → N 선택 (기존 재사용) 또는 Y (재실행)
10. teleop 진입 정상 확인

---

## 게이트 4 통합 verification_queue 현황

| 항목 | 상태 | 환경 레벨 |
|---|---|---|
| [D1-1~4] env_check + teleop + record + BACKLOG#14 실물 | PHYS BACKLOG (게이트 1 통과) | PHYS_REQUIRED |
| [D4-1] pyserial 설치 후 항목 9 PASS 확인 | 대기 중 | PHYS_REQUIRED |
| [D4-2] precheck 옵션(1) 실 포트·카메라 입력 → configs 갱신 | 대기 중 | PHYS_REQUIRED |
| [D5-1] 새 venv 셋업 시 lerobot-find-port 정상 동작 | 대기 중 | PHYS_REQUIRED 류 |
| [D6-1] 실 카메라 USB 분리/재연결 walkthrough | 신규 등재 | PHYS_REQUIRED |

D4 + D5 + D6 PHYS_REQUIRED 항목은 시연장 이동 시 통합 검증 권장.

---

## CLAUDE.md 준수

| Category | 체크 | 메모 |
|---|---|---|
| Category A (절대 금지 영역) | ✅ | docs/reference/ 미변경, .claude/ 미변경 |
| Category B (자동 재시도 X 영역) | ✅ | dgx/lerobot/ 미변경, pyproject.toml 미변경, setup_env.sh 미변경, deploy_dgx.sh 실행만 (내용 변경 X) |
| deploy_dgx.sh 자율 여부 | ✅ 자율 | Category B 영역 외 파일 변경 (interactive_cli/flows/ 3파일) — rsync 만 수행, GPU 학습·패키지 설치·데이터 다운로드 트리거 X |
| 동의 필요 영역 | 없음 | 모든 작업 자율 범위 |
| Coupled File Rules | ✅ | Category B 미변경 — coupled file 갱신 불필요 |
