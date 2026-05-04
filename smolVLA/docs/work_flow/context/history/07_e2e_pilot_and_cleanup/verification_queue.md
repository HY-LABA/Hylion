# Phase 3 검증 대기 큐

> Phase 2 진행 중 prod-test-runner 가 완료한 항목 + 사용자 실물 검증이 필요한 항목을 누적. 모든 todo 자동화 종료 시 메인이 본 큐를 사용자에게 일괄 제시.

## 형식

각 항목:

```markdown
### [TODO-XX] (제목)

- **상태**: 자동 검증 통과 / 실패 / N.A.
- **사용자 검증 필요 사항**:
  1. (구체 절차)
  2. ...
- **prod-test-runner 결과 요약**: ...
- **참고 파일**: `context/todos/XX/03_prod-test.md`
```

---

## 07_e2e_pilot_and_cleanup

### [그룹 P — AUTOMATED_PASS (사용자 검증 불요)]

#### TODO-P2: .gitignore datacollector 패턴 제거

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: grep 잔재 0건 확인. git diff 5줄 제거 (L6·L10 + orphan comment block) 정합. 파일 24줄, 섹션 구조 정상. datacollector 디렉터리 미존재 — git status 신규 노출 없음.
- **참고 파일**: `context/todos/P2/03_prod-test.md`

#### TODO-P3: arm_2week_plan.md 07 시프트 + 신규 항목

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: 마일스톤 번호 unique (06~11 각 1회), 번호 연속성 (00~11), 신규 07 항목 7건 등장, 시프트 주석 누적 (07→08 + 06 이력 병렬), 06 결정 이력 14건 보존, 내부 cross-ref 4건 갱신, 구버전 잔재 0건, 헤더 구조 정상, HTML 주석 쌍 일치 (9/9), README.md 정합 — 전 항목 PASS.
- **참고 파일**: `context/todos/P3/03_prod-test.md`

#### TODO-P4: 활성 spec 번호 표 갱신 (README.md)

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: 정적 grep/awk 검증 — 표 행 11개 (01~11), 07 bold+활성, 06 history, 08~11 구 번호 괄호, 시프트 주석 2줄 병렬 (M1+P4), 날짜 2026-05-03, arm_2week_plan.md (P3) 번호 정합 — 전 항목 PASS.
- **참고 파일**: `context/todos/P4/03_prod-test.md`

#### TODO-P5: 활성 영역 datacollector 잔재 grep 종합

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: bash -n / py_compile (×3) / json.tool 전 파일 PASS. orin/·dgx/·scripts/·docs/lerobot_study/·루트 파일 grep 활성 잔재 0건. 남아있는 매치 전수 분류 — 모두 의도된 이식 이력/정정/운영종료 주석 패턴. R#1 (dgx/README.md) 의미 재작성 확인. R#2 (training.py L284) 현 워크플로우 반영 안내 문구 확인.
- **참고 파일**: `context/todos/P5/03_prod-test.md`

---

### [그룹 P — 대기 중]

(Wave 1 TODO-P1 prod-test 완료 후 갱신)

---

### [그룹 D — NEEDS_USER_VERIFICATION]

#### TODO-D1: dgx/interactive_cli/ 수집 mode SSH_AUTO 검증 + 도구 정비 (06 V2 흡수)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 1, D 분기 통과 — PHYS BACKLOG)
- **사용자 검증 필요 사항** (모두 PHYS_REQUIRED — 시연장 이동 시):
  1. **[D-1]** flow 2 env_check 항목 6~9 실물 PASS — SO-ARM + 카메라 USB 직결 환경에서 `/dev/ttyACM0` (leader), `/dev/ttyACM1` (follower) 인식, `dialout` 그룹 확인, `/dev/video*` 인식, `serial.Serial` open PASS 확인
  2. **[D-2]** flow 3 텔레오퍼레이션 (`run_teleoperate.sh all`) — SO-ARM leader+follower 직결, 동작 추종 육안 확인
  3. **[D-3]** flow 6 `lerobot-record` (dummy 1~3 에피소드) — SO-ARM + 카메라 2대 직결. `cam_wrist_left=0`, `cam_overview=1` 실 인덱스 정합 확인
  4. **[D-4]** 04 BACKLOG #14 실물 확인 — SO-ARM 직결 환경에서 env_check.py 항목 9 (`serial.Serial` context manager) `NoneType` 에러 미발생 확인
- **prod-test-runner 결과 요약**: AUTO_LOCAL py_compile 8/8 PASS, ruff All checks passed, main.sh bash -n OK. deploy_dgx.sh 자율 배포 성공 (mode.py 등 5파일 신규 전송). SSH_AUTO — DGX spark-8434 정상, VALID_NODES ('orin','dgx') 확인, datacollector 제거 확인, flow2_env_check 시그니처 `(script_dir, scenario='smoke', mode='train')` 기대치 일치, SO-ARM 미연결 fallback `False` 반환 + 크래시 X, mode.py 패치 `mode="collect"` 호출 존재 확인. BACKLOG #14 정적 분석: port_handler 패턴 0건, `serial.Serial` context manager None-safe 원천 차단.
- **참고 파일**: `context/todos/D1/03_prod-test.md`

#### TODO-D2: dgx/interactive_cli/ 학습 mode 회귀 검증 (06 V3 + 05 X3 통합)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 1, D 분기 통과 — PHYS BACKLOG)
- **사용자 검증 필요 사항**:
  1. **[D2-1] smoke_test PASS (SSH_AUTO, T1 완료 후)** — T1 `svla_so100_pickplace` HF Hub 다운로드 완료 후 실행:
     ```bash
     ssh dgx "source ~/smolvla/dgx/.arm_finetune/bin/activate && \
         export HF_HOME=~/smolvla/.hf_cache && export CUDA_VISIBLE_DEVICES=0 && \
         bash ~/smolvla/dgx/scripts/smoke_test.sh"
     ```
     기대: exit 0 + 소요 시간·GPU util 출력. 소요 5~15분. T1 완료 시 SSH_AUTO 자율 가능.
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile PASS, ruff All checks passed, 구조 assertion 6건 ALL PASS, ckpt 4건 분기 코드 정합 ALL PASS, G-4 분기 정합 PASS, smoke consent gate PASS, lerobot upstream train.py L49·L84·L94-111 인용 정합 ALL PASS. deploy_dgx.sh 자율 배포 성공. SSH_AUTO — DGX py_compile PASS, 구조 assertion ALL PASS, preflight 5단계 PASS (RAM 100GB 가용·디스크 3314GB·Walking RL 미실행·Ollama 미점유). save_dummy_checkpoint 산출물 7개 파일 확인 (model.safetensors 865MB). smoke_test 는 svla_so100_pickplace 미캐시 → T1 선결 필요.
- **참고 파일**: `context/todos/D2/03_prod-test.md`

#### TODO-D3: DGX check_hardware.sh 5-step 도구 정비

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 1, D 분기 통과 — PHYS BACKLOG)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시):
  1. DGX 에 SO-ARM 2대 (follower + leader) + 카메라 2대 (top + wrist) USB 직결 후 `cd ~/smolvla && bash dgx/scripts/check_hardware.sh` 실행. 기대: `[DONE] 모든 점검 PASS (5단계)` + FAIL 0건. FAIL 발생 시 해결 힌트 블록 지시에 따라 처리.
  - 참고: 06 V1 BACKLOG (BACKLOG.md L125) 와 통합 — D3 verification 통과 시 06 V1 BACKLOG 완료 처리 가능. 이중 등록 X.
- **환경 레벨**: PHYS_REQUIRED
- **prod-test-runner 결과 요약**: bash -n exit 0 (devPC + DGX 양측), X4·X5 잔재 0건, setup_train_env.sh §3-c 갱신 메시지 L34·L249·L282·L345 4곳 확인, 5-step 함수 5건 (step_venv·step_dialout·step_soarm_port·step_v4l2·step_cameras). DGX SSH 실 실행 — Step 1(venv)·Step 2(dialout) PASS, Step 3~5 (SO-ARM·카메라 미연결) FAIL 안내 정상 출력 + 전체 중단 없이 진행 + exit code 1 확인. 해결 힌트 블록 §3-c 안내 포함.
- **참고 파일**: `context/todos/D3/03_prod-test.md`

#### TODO-D1a: DGX + Orin main.sh 회귀 패치 — 실 smoke 검증 (07-#2 SMOKE_TEST_GAP 해소)

- **상태**: ✅ AUTOMATED_PASS (2026-05-04 12:10 Orin SSH 복구 후 재검증 완료)
- **환경 레벨**: SSH_AUTO (양측 완료)
- **사용자 검증 필요 사항**: 없음 — 전 항목 자동 검증 충족
- **prod-test-runner 결과 요약**: DGX — bash -n 양측 PASS, git 인덱스 100755 양측 확인, 배포 성공 (755 보존), smoke echo '3' flow1 메뉴 정상+종료, smoke echo '2' flow1→preflight 5/5 PASS→flow3 진입, ModuleNotFoundError X (회귀 1 패치 실증). Orin (재검증 12:10) — SSH ubuntu/Python3.10.12 가용, 배포 성공 (26,744 bytes), ls -la -rwxr-xr-x 755 확인, flows.entry 직접 실행 flow1 메뉴 정상 출력 + "종료합니다." exit 0, import smoke 3모듈 ALL OK (entry·env_check·inference). DOD 10항목 전부 자동 충족. 사용자 실물 검증 필요 항목 0개.
- **참고 파일**: `context/todos/D1a/03_prod-test.md`

#### TODO-D4: dgx/interactive_cli/ 수집 mode teleop 사전 점검 (precheck) 신규 — 게이트 4

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — DGX SO-ARM+카메라 직결 PASS)
- **환경 레벨**: SSH_AUTO (walkthrough 완료) + PHYS_REQUIRED (실 포트·카메라 설정)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시):
  1. **[D4-1] pyserial 설치 환경 항목 9 PASS 확인** — DGX venv 에 pyserial 설치 후 env_check 항목 9 (`serial.Serial` 포트 응답) PASS 확인. 현재 DGX `.arm_finetune` venv 에 pyserial 미설치 → SKIP 처리 중. SO-ARM 직결 환경에서 `source ~/smolvla/dgx/.arm_finetune/bin/activate && cd ~/smolvla && echo -e '2\n1\nCtrl-C' | timeout 15 bash dgx/interactive_cli/main.sh 2>&1 | grep "항목 9"` 기대: PASS (또는 SKIP 사유 정합).
  2. **[D4-2] precheck 옵션(1) 실 포트·카메라 입력 → configs 갱신 확인** — 시연장 SO-ARM + 카메라 직결 환경에서 precheck 메뉴 (1) 선택 → lerobot-find-port 실 결과로 follower·leader 포트 입력 → lerobot-find-cameras 실 결과로 wrist_left·overview 인덱스 입력 → `cat ~/smolvla/dgx/interactive_cli/configs/ports.json` + `cameras.json` 갱신값 확인 → 이후 teleop 정상 진입 확인.
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile 9/9 ALL_OK, ruff All checks passed!, bash -n OK, import smoke (mode OK·precheck OK·calib_dir 정상). DGX 배포 성공 (precheck.py 18353B·ports.json 51B·cameras.json 67B·mode.py 9980B 전송). DGX SSH_AUTO — py_compile 9/9 ALL_OK, import smoke PASS (calib_dir: /home/laba/smolvla/.hf_cache/lerobot/calibration 존재), configs JSON placeholder 형식 정상. menu walkthrough (SO-ARM DGX 직결) — 시나리오 1 (취소): precheck UI 정상 도달·정보 표시·취소 return 0 정합 PASS. 시나리오 2 (기존 진행): proceed → _run_collect_flow → teleop 진입 흐름 정합 PASS. 시나리오 3 (옵션1 find-port+cameras): lerobot-find-port×2 + lerobot-find-cameras subprocess 실행, 캘리브 [y/N] N → proceed 반환 PASS. 회귀 1 (ModuleNotFoundError) 재발 없음 전 시나리오 확인.
- **참고 파일**: `context/todos/D4/03_prod-test.md`

#### TODO-D5: setup_train_env.sh §3 extras hardware,feetech 통합 (06 extras 누락 영구 fix)

- **상태**: NEEDS_USER_VERIFICATION (AUTO_LOCAL 정적 검증 전 항목 PASS — 실 재실행 검증은 시연장 셋업 시)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + PHYS_REQUIRED 류 (새 venv 재설치 실 실행 확인)
- **사용자 검증 필요 사항**:
  1. **[D5-1] 새 DGX venv 셋업 또는 setup_train_env.sh 재실행 시 lerobot-find-port 정상 동작 확인** — 시연장 셋업 또는 DGX venv 재생성 시:
     ```bash
     source ~/smolvla/dgx/.arm_finetune/bin/activate
     lerobot-find-port
     # 기대: pyserial ImportError X, 포트 탐색 UI 정상 진입 (또는 "장치 없음" 안내)
     ```
     현 DGX 환경은 D4 즉석 pip install pyserial 3.5 로 이미 해소됨. setup_train_env.sh 재실행 시 `lerobot[hardware,feetech]` extras 가 pyserial>=3.5,<4.0 범위 내 no-op 처리 예상 → 재실행 충돌 없음. 신규 venv 셋업 환경에서 자연 검증 기회 있음.
- **prod-test-runner 결과 요약**: bash -n exit 0. extras 갱신 라인 grep 1건 (L77: `[smolvla,training,hardware,feetech]`). lerobot upstream hardware L110·feetech L145 spot-check PASS. 04_dgx_lerobot_diff.md 2026-05-03 항목 확인 (before/after 표·이유·upstream 인용·Option B 선언 포함). BACKLOG 07 #3 항목 (§3-c 정리 후보) 확인. dgx/lerobot/·dgx/pyproject.toml·docs/reference/ 변경 0건 (Option B·Category A 준수). pyserial 충돌 분석 — pyserial-dep 범위 >=3.5,<4.0, DGX 즉석 3.5 범위 내 → pip no-op 보장.
- **참고 파일**: `context/todos/D5/03_prod-test.md`

#### TODO-D6: precheck 카메라 식별 강화 + entry SSH/직접 실행 분기 (D4 cycle 2 후속 패치, 게이트 4 통합)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — _run_find_cameras_split 실 USB 분리/재연결 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·walkthrough PASS) + PHYS_REQUIRED (실 카메라 USB 분리/재연결)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4 통합 검증 권장):
  1. **[D6-1] 실 카메라 USB 분리/재연결 walkthrough** — SO-ARM + 카메라 USB 직결 DGX 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow1 DGX 선택 → detect_display_mode (SSH 자동 검출 "ssh" 또는 사용자 선택) → flow2 env_check PASS → flow3 mode (1) 수집 → precheck (1) 새 수집 시작 → lerobot-find-port × 2 (follower·leader) → _run_find_cameras_split 실행:
     - baseline /dev/video* 기록 → wrist USB 단독 연결 → 신규 device 검출 → 1프레임 캡처 → ssh 모드: jpg 저장 경로 출력 → 영상 육안 확인 OK
     - overview USB 추가 연결 → 신규 device 검출 → 1프레임 캡처 → 영상 육안 확인 OK
     - `cat ~/smolvla/dgx/interactive_cli/configs/cameras.json` 갱신 확인:
       기대: `{"wrist_left": {"index": "/dev/videoN"}, "overview": {"index": "/dev/videoM"}}`
     - 캘리브레이션 prompt [y/N] → N (기존 재사용) 선택
     - teleop 진입 정상 확인
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile 3/3 ALL_OK, ruff All checks passed!, bash -n OK. devPC import smoke (precheck 5함수 + detect_display_mode) PASS. detect_display_mode 동작 검증 3종 PASS (SMOLVLA_DISPLAY_MODE=ssh → "ssh", SMOLVLA_DISPLAY_MODE=direct+DISPLAY=:0 → "direct", DISPLAY unset fallback → "ssh"). DGX 배포 성공 (entry.py 12606B·mode.py 10769B·precheck.py 33145B 전송). DGX import smoke PASS. DGX SSH_CLIENT 자동 검출 확인 (SSH_CLIENT: 172.16.141.201 47902 22 → auto_detected="ssh"). menu walkthrough — 시나리오 1 (학습 flow 진입): flow1→env_check 5/5 PASS→flow3 mode→학습 시나리오 도달 PASS. 시나리오 2 (수집 mode 취소): flow1→env_check(smoke) PASS→flow3(1)수집→env_check(collect) 수집 항목 6~9 PASS (leader/follower/dialout/4카메라/serial) → teleop 사전 점검 UI 정상 → 취소(3) 정상 종료 PASS.
- **참고 파일**: `context/todos/D6/03_prod-test.md`

#### TODO-D7: precheck 방향 반전 + find-port 자체 로직 + SSH X11 지원 (D4 cycle 3, 게이트 4 통합)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — _run_find_port_self + _run_find_cameras_split 방향 반전 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·walkthrough PASS) + PHYS_REQUIRED (실 카메라/포트 검출)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6 통합 검증 권장):
  1. **[D7-1] 실 카메라 분리/재연결 walkthrough — D7 방향 반전 확인 (D4 게이트 4 통합)** — DGX + SO-ARM + 카메라 USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow1 DGX 선택 → detect_display_mode (SSH=True → ssh-file 자동 검출 또는 ssh-x11 선택) → flow2 env_check PASS → flow3 mode (1) 수집 → precheck (1) 새 수집 시작:
     - `_run_find_port_self` — follower USB 분리 → 사라진 포트 검출 → 재연결 → leader 동일 패턴 → ports.json 갱신 확인
     - `_run_find_cameras_split` (D7 핵심 방향 반전) — wrist + overview 모두 연결 상태 baseline 취득 → wrist 분리 → 사라진 device 검출 → 재연결 → 영상 확인 → overview 분리 → 사라진 device 검출 → 재연결 → 영상 확인
     - `cat ~/smolvla/dgx/interactive_cli/configs/cameras.json` 기대: `{"wrist_left": {"index": "/dev/videoN"}, "overview": {"index": "/dev/videoM"}}`
     - calibrate [y/N] → N → teleop 진입 정상 확인 (feetech 설치로 ImportError X)
  2. **[D7-2] SSH X11 forwarding 모드 검증** (옵션 — ssh -Y dgx 접속 환경):
     ssh -Y dgx 접속 시 detect_display_mode → DISPLAY=localhost:N 자동 검출 → `ssh-x11` → cv2.imshow 시도. X11 실패 시 ssh-file fallback 안내 출력 확인.
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile 2/2 PASS (precheck·entry), ruff All checks passed!, bash -n deploy_dgx.sh OK. detect_display_mode 로직 단위 8종 ALL PASS (4종 override + 3종 자동검출 + direct/DISPLAY fallback 포함). DGX 배포 성공 (entry.py 15K·precheck.py 44K 전송, 2026-05-04 13:19). DGX SSH_AUTO — py_compile 2/2 PASS, 함수 7종 ALL PASS (_run_find_cameras_split·_run_find_port_self·_run_find_port·_get_video_devices·_capture_frame_to_file·_show_frame·teleop_precheck), detect_display_mode override 3종 PASS. menu walkthrough — flow1(2=DGX) → detect_display_mode(Enter=auto, SSH=True DISPLAY=''  → ssh-file) → flow2 env_check 5/5 PASS → flow3(3=종료) "[mode] 종료합니다." 정상 PASS.
- **참고 파일**: `context/todos/D7/03_prod-test.md`

#### TODO-D8: deepdiff·메타 필터·viewer 통합 (D7 cycle 2 통합)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — streamable filter + ssh-file 영상 안내 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·walkthrough PASS) + PHYS_REQUIRED (실 카메라 분리/재연결)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6·D7 통합 검증 권장):
  1. **[D8-1] 실 카메라 분리 시 메타 device 필터링 + 단일 device 검출 확인** — D7 walkthrough 재시도 환경 (DGX + SO-ARM + 카메라 USB 직결) 에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow3 mode (1) 수집 → precheck (1) 새 수집 시작 → _run_find_cameras_split:
     - `[사전 스캔] 영상 스트림 가능 device 확인 중...` 메시지 출력 확인
     - baseline 출력 예: `현재 연결된 /dev/video* 기기 (스트림 가능): ['/dev/video0', '/dev/video2']`
       (video1·video3 메타 device 가 baseline 에서 제외됨)
     - wrist USB 분리 후 Enter — 검출 결과 예: `[검출] wrist device: /dev/video0`
       (video0 만 사라짐 — video1 메타 device 는 after_disconnect 전체 glob 에 포함되나 baseline 부재로 removed 에 미포함)
     - `cat ~/smolvla/dgx/interactive_cli/configs/cameras.json` 갱신 확인:
       기대: `{"wrist_left": {"index": "/dev/video0"}, "overview": {"index": "/dev/video2"}}` (기기 번호는 환경마다 다를 수 있음)
  2. **[D8-2] ssh-file 모드 영상 확인 방법 안내 출력 확인** — 영상 capture 후:
     - `VSCode remote-ssh 사용 중이면:` 안내 메시지 출력 확인
     - `code -r /path/to/...jpg` 명령 출력 확인
     - `(xdg-open 실행됨 — VSCode remote 미리보기 창 확인)` 또는 rc 보고 출력 확인
     - VSCode remote-ssh 환경이면 Explorer 에서 jpg 파일 클릭 → 미리보기 가능 여부 육안 확인
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile PASS, ruff All checks passed!, bash -n main.sh PASS. devPC import smoke 6 함수 ALL OK, _get_streamable_video_devices() 호출 정상 (devPC video0·video1 2개 반환). DGX 배포 성공 (precheck.py + cameras.json 등 4파일, speedup=33.25, 2026-05-04 14:05 타임스탬프 확인). DGX py_compile PASS. DGX import smoke 4 함수 PASS. DGX _get_streamable_video_devices() 실 실행 — video0·video2 2개 반환 (video1·video3 메타 device 필터링 성공). deepdiff 9.0.0 기본 API PASS (values_changed 정상). deepdiff exclude_regex_paths 호환성 PASS (info 키 제외 + a 키 변경 감지). lerobot motors_bus.py·control_utils.py DeepDiff 사용 패턴 정적 grep — 기본 생성자·exclude_regex_paths 패턴 모두 9.x 안정 API 확인. menu walkthrough — flow1(2=DGX) → detect_display_mode(ssh-file 자동) → flow2 preflight 5/5 PASS → flow3 mode → flow4 데이터셋 → "[mode] 종료합니다." PASS.
- **참고 파일**: `context/todos/D8/03_prod-test.md`

#### TODO-D9: precheck _run_calibrate ports.json 로드 fix (D4 cycle 4 후속)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — calibrate prompt ports.json default + Enter 수락 + SerialException X PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·import·로드 시뮬 PASS) + PHYS_REQUIRED (find-port 완료 후 calibrate prompt 실 확인)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6·D7·D8 통합 walkthrough 내 자연 검증 권장):
  1. **[D9-1] find-port 완료 후 calibrate prompt default 확인** — SO-ARM + DGX USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow3 mode (1) 수집 → precheck (1) 새 수집 시작 → `_run_find_port_self` (follower·leader USB 분리/재연결 각각, ports.json 저장) → calibrate [y/N] → y → follower calibrate prompt:
     - `(Enter=/dev/ttyACM0, source: ports.json 검출 결과)` 표시 확인 (D9 핵심)
     - Enter (default 수락) → follower 캘리브레이션이 `/dev/ttyACM0` (실 follower 포트) 로 진행
     - `SerialException` 미발생 확인 (D9 fix 목적 — 기존 hardcoded ttyACM1 으로 follower 접근 시 발생하던 오류 해소)
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile PASS, ruff All checks passed!, import smoke PASS (signature: `(configs_dir: pathlib._local.Path) -> bool`). DGX 배포 성공 (precheck.py 50491B·ports.json·cameras.json 등 3파일 전송, speedup 66.62). DGX import smoke PASS (signature `(configs_dir: pathlib.Path) -> bool`). DGX ports.json 로드 시뮬 — exists: True, 현재 null 상태 (find-port 미완료) + null → hardcoded fallback `/dev/ttyACM1` 정상. 실 값 시뮬 (follower=/dev/ttyACM0) → prompt `(Enter=/dev/ttyACM0, source: ports.json 검출 결과)` 정상 출력. DOD 8항 자동 전체 충족.
- **참고 파일**: `context/todos/D9/03_prod-test.md`


#### TODO-D10: 사이클 흐름 분기점 강화 — G1 (teleop 안내) + G2 (single_task UI) + G3 (precheck 흐름 안내) + G4 (BACKLOG)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — G1·G2·G3 안내 출력 + 효과 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·walkthrough PASS) + PHYS_REQUIRED (게이트 4 실물 walkthrough)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6·D7·D8·D9 통합 walkthrough 내 자연 검증 권장):
  1. **[D10-1] 게이트 4 통합 walkthrough — G1·G2·G3 효과 직접 확인** — SO-ARM + 카메라 DGX USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     - G1: flow3 텔레오퍼레이션 시작 시 "흐름: 1. Enter → run_teleoperate.sh / 2. Ctrl+C *정상 종료* / 3. 종료 후 다음 단계" 출력 확인
     - G1-b: teleop 후 flow4 — 정상 종료 시 "Enter=다음 단계 (record + 학습)", 비정상 시 "Enter=강제 진행 (비권장)" 출력 확인
     - G2: flow6 record 진입 시 "학습 task 텍스트" UI — 기본값/커스텀 입력 분기 동작 확인. 커스텀 task 입력 후 lerobot-record 인자에 반영 확인
     - G3: precheck 옵션 2 선택 시 "다음 흐름: 1.teleop / 2.data_kind → record / 3.transfer / 4.학습 분기" 출력 확인
     - D9 효과: precheck 옵션 1 완료 후 calibrate prompt 에 ports.json 검출 결과 기본값 표시 확인
- **prod-test-runner 결과 요약**: devPC py_compile 3/3 PASS, ruff All checks passed!, bash -n main.sh PASS. devPC import smoke 3모듈 ALL OK + build_record_args 회귀 (기본값 True·커스텀 True). DGX 배포 성공 (teleop.py 6538B·record.py 17736B·precheck.py 51226B, speedup 39.72). DGX py_compile 3/3 PASS. DGX import smoke ALL OK. DGX build_record_args 시그니처 6파라미터 (single_task 포함) + 회귀 PASS. DGX G1/G2/G3 grep ALL PASS. BACKLOG 07 #10~#14 5건 확인. DGX menu walkthrough — flow1(2=DGX)→flow2 preflight 5/5 PASS→flow3 mode 정상, 수집 mode → precheck 옵션 2 → 4단계 흐름 안내 출력 → flow3 teleop 3단계 흐름 출력 → flow4 비정상 "강제 진행 (비권장)" 출력 ALL PASS.
- **참고 파일**: `context/todos/D10/03_prod-test.md`

#### TODO-D11: teleop.py KeyboardInterrupt catch + flow3 안내 강화 (게이트 4 walkthrough 재시도 후속)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — Ctrl+C 정상 종료 + flow4 prompt → record 진입 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·import PASS) + PHYS_REQUIRED (Ctrl+C 후 flow4 진입 실물 확인)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6·D7·D8·D9·D10 통합 walkthrough 내 자연 검증 권장):
  1. **[D11-E1] teleop walkthrough 재시도 — Ctrl+C 종료 후 flow4 정상 진입 확인** — SO-ARM + 카메라 DGX USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow1 DGX 선택 → flow2 env_check → flow3 mode (1) 수집 → precheck → flow3 텔레오퍼레이션 진입:
     - teleop 시작 시 "흐름: 1. Enter ... / 2. Ctrl+C 한 번 누르면 *정상 종료* / 3. ..." 안내 출력 확인
     - "※ teleop 도중에는 'Teleop loop time: ...' 출력만 보이고 종료 안내 X" 주석 출력 확인
     - run_teleoperate.sh 실행 중 Ctrl+C → "[teleop] Ctrl+C 감지 — teleop 정상 종료 처리." 출력 확인
     - entry.py 프로세스 미사망 → flow4_confirm_teleop prompt "입력 ['r'=teleop 재시도 / Enter=다음 단계 (record + 학습) / Ctrl+C=완전 종료]:" 정상 출력 확인
     - Enter → flow5 data_kind → flow6 record (G2 single_task UI) → 정상 진행 확인
- **prod-test-runner 결과 요약**: devPC — py_compile PASS, ruff All checks passed!, bash -n main.sh PASS, import smoke PASS. KeyboardInterrupt 시뮬 (SIGINT → subprocess sleep 100) → except KeyboardInterrupt → return 0 확인 PASS. grep — "흐름:" 3줄 후 "Ctrl+C 한 번 누르면 *정상 종료*" 존재, "teleop 도중에는" L109 존재. DGX 배포 성공 (teleop.py 1파일 2,709 bytes, 2026-05-04 16:25 타임스탬프). DGX — py_compile PASS, import smoke PASS. DGX 측 grep — 흐름·except KeyboardInterrupt·return 0 모두 일치.
- **참고 파일**: `context/todos/D11/03_prod-test.md`

#### TODO-D12: record.py cameras.json + ports.json 로드 (D9 패턴 record 확장 — OpenCVCamera 차단 방지)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — record cameras.json 검출 결과 반영 + 10 epi 16820 frames 수집 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·import·로드 시뮬 PASS) + PHYS_REQUIRED (게이트 4 walkthrough 재시도 — cameras.json 검출 결과 record 반영 확인)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6·D7·D8·D9·D10·D11 통합 walkthrough 내 자연 검증 권장):
  1. **[D12-F1] 게이트 4 walkthrough 재시도 — cameras.json 검출 결과 record 반영 확인** — SO-ARM + 카메라 USB 직결 DGX 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow1 DGX 선택 → precheck 옵션 1 (새 수집 시작) → `_run_find_cameras_split` 완료 → cameras.json 갱신 (`/dev/videoN`·`/dev/videoM`) → flow6 record 진입 시:
     - `[record] config 출처: cameras: wrist_left=/dev/videoN, overview=/dev/videoM (cameras.json 검출 결과)` 출력 확인
     - `lerobot-record` 인자에 `index_or_path: /dev/videoN` 경로 포함 확인 (hardcoded `0`·`1` 미사용)
     - ports.json 갱신 후 ports 출처도 "ports.json 검출 결과" 표시 확인
     - OpenCVCamera 차단 X 확인 (v4l2 메타 device 경고 미발생)
- **prod-test-runner 결과 요약**: devPC py_compile 2/2 PASS, ruff All checks passed!, bash -n main.sh PASS, import smoke 4함수 ALL OK. _validate_camera_indices 5케이스 ALL PASS (int 정상·int 음수·str 정상·str 비정규·str 빈 문자열). DGX 배포 성공 (mode.py 10794B·record.py 24533B, 2026-05-04 17:08-09). DGX import smoke ALL OK. DGX null placeholder fallback 시뮬 — cameras_source="hardcoded fallback", 경고 출력 정상. DGX 실 값 시뮬 (/dev/video0 등) — cameras_source="cameras.json 검출 결과" 정상 반영. BACKLOG 07 #4 완료 마킹·#15 신규 확인.
- **참고 파일**: `context/todos/D12/03_prod-test.md`

#### TODO-D13: precheck 옵션 2 streamable fallback + deploy_dgx.sh configs exclude (Part A+B+C)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 4 e2e 통합 walkthrough — precheck 옵션 2 streamable fallback + record 진입 PASS)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (DGX 배포·fallback 시뮬 PASS) + PHYS_REQUIRED (게이트 4 walkthrough — 실 카메라·record 진입 확인)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, D4·D6~D12 통합 walkthrough 내 자연 검증 권장):
  1. **[D13-G1] 게이트 4 walkthrough 재시도 — cameras.json null 시 streamable fallback 효과 + record 정상 진입 확인** — SO-ARM + 카메라 USB 직결 DGX 환경에서:
     - cameras.json null 상태 유지 또는 강제: `echo '{"wrist_left":{"index":null},"overview":{"index":null}}' > ~/smolvla/dgx/interactive_cli/configs/cameras.json`
     - `cd ~/smolvla && bash dgx/interactive_cli/main.sh`
     - flow1 DGX → precheck 옵션 2 선택
     - 기대: "[precheck] cameras.json 미설정 검출 — streamable device 자동 fallback 시도" 출력
     - 기대: "cameras.json 자동 갱신: wrist_left = /dev/videoN ..." 출력 (실 device 기반)
     - flow6 record 진입 시 "[record] config 출처: cameras: wrist_left=/dev/videoN ..." 출력 확인
     - OpenCVCamera 차단 미발생 확인 (v4l2 메타 device 경고 없음)
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile PASS, ruff All checks passed!, bash -n deploy_dgx.sh PASS. rsync dry-run — cameras.json·ports.json 전송 목록 제외 PASS (grep 0건), node.yaml + precheck.py 정상 포함 확인. Part A null 검출 로직 devPC 시뮬 — null 검출 True, cameras.json 갱신 성공. DGX 배포 성공 (precheck.py 1파일 전송, json 2종 제외 확인). DGX py_compile PASS. DGX import smoke PASS (teleop_precheck·_get_streamable_video_devices). DGX cameras.json·ports.json 배포 후 보존 확인 (null 상태 유지). DGX _get_streamable_video_devices 실 실행 — video0·video1·video2·video3 4개 검출, cameras.json 자동 갱신 (wrist=/dev/video0·overview=/dev/video1). Part F DGX ports null 안내 분기 출력 확인. BACKLOG 07 #15 완료 마킹 확인.
- **참고 파일**: `context/todos/D13/03_prod-test.md`


---

### [그룹 T — T1·T2·T3 완료]

#### TODO-T1: svla_so100_pickplace HF Hub 다운로드 prod 검증

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: `hf download lerobot/svla_so100_pickplace --repo-type dataset` 성공 (9/9 파일, 16초). 캐시 경로 `/home/laba/smolvla/.hf_cache/hub/datasets--lerobot--svla_so100_pickplace/`, 크기 449MB. LeRobotDataset 로드 — num_frames=19631, num_episodes=50, camera_keys=['observation.images.top', 'observation.images.wrist'], fps=30. D 분기 save_dummy_checkpoint (2026-05-04 09:25) 에서도 동일 다운로드 PASS 확인. 학교 WiFi 차단 미발생. T2 dispatch 가능.
- **참고 파일**: `context/todos/T1/03_prod-test.md`

#### TODO-T2: DGX 짧은 fine-tune 1회 완주 (--steps=2000 --save_freq=1000)

- **상태**: ✅ 사용자 통과 결정 (2026-05-04 게이트 2 — 학습 완주 + 002000 ckpt 7파일 865MB PASS, T3 sync 산출물로 입증, 추가로 게이트 4 walkthrough 의 smoke train 1 step PASS 도 학습 mode 정상 입증)
- **환경 레벨**: SSH_AUTO
- **사용자 검증 필요 사항**:
  1. **[T2-1] 학습 완주 + 체크포인트 확인 (SSH_AUTO)** — 학습 완주 후 (예상 09:43 시작 → ~10:03 완주):
     ```bash
     # 학습 완주 확인 (PID 소멸 = 완주 또는 실패)
     ssh dgx "pgrep -f 'lerobot-train.*07_pilot_2k' && echo 'ALIVE' || echo 'DONE_OR_FAIL'"
     # 로그 마지막 출력 (step 2000 + loss 확인)
     ssh dgx "tail -10 /home/laba/smolvla/dgx/outputs/train/07_pilot_2k.log"
     # 체크포인트 디렉터리 존재 확인
     ssh dgx "ls /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/"
     # 기대: 001000  002000  last
     ssh dgx "ls -lh /home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/002000/pretrained_model/"
     # 기대: model.safetensors (865MB 내외) 포함 7개 파일
     ```
  2. **[T2-2] 완주 후 T3 dispatch 승인** — 체크포인트 확인 후 orchestrator 에게 T3 진행 통보
- **prod-test-runner 결과 요약**: 학습 백그라운드 시작 PASS (PID 462216, 2026-05-04 09:43). 60초 후 로그 정상 — cfg dump + step 50 (loss=0.325, grdn=6.122) + step 100 (loss=0.313, grdn=6.003) 확인. step 132 진행 중, tqdm 예상 잔여 ~20분 (실제 throughput ~1.5~2.0 step/s). cycle 1 FileExistsError (빈 디렉터리 충돌) → rmdir 후 cycle 2 정상 시작. log 파일: `/home/laba/smolvla/dgx/outputs/train/07_pilot_2k.log`.
- **참고 파일**: `context/todos/T2/03_prod-test.md`

#### TODO-T3: scripts/sync_ckpt_dgx_to_orin.sh 실 실행 검증 + 06 BACKLOG #4 갱신

- **상태**: AUTOMATED_PASS (2026-05-04 13:30 — Orin SSH 복구 후 재시도 성공)
- **환경 레벨**: SSH_AUTO (devPC + DGX + Orin 3-hop 자율 완료)
- **사용자 검증 필요 사항**: 없음 — 모든 DOD 항목 자동 검증 충족
- **prod-test-runner 결과 요약**: bash -n PASS. dry-run PASS (7파일 목록 + total 906,732,067 bytes). 실 실행 PASS — DGX→devPC (14.9 MB/s) → Orin (5.5 MB/s), 7파일 전송. Orin `/home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000/` 7파일·865M 확인. safetensors 헤더 8 byte OK. 06 BACKLOG #4 "완료" 마킹 확인. 회귀 없음.
- **참고 파일**: `context/todos/T3/03_prod-test.md`

---

### [그룹 O — NEEDS_USER_VERIFICATION]

#### TODO-O1: orin/interactive_cli/ flow 0~5 SSH_AUTO 검증 (05 O3 흡수)

- **상태**: 사용자 무시 결정 (2026-05-04 — Orin SO-ARM 직결 부분 BACKLOG 이관, BACKLOG 07 #9 통합 PHYS_REQUIRED 묶음에 합류. ANOMALIES 07 #4 USER_OVERRIDE 누적)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (Orin 배포·walkthrough PASS) + PHYS_REQUIRED (SO-ARM 직결)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시):
  1. **[O1-1] check_hardware.sh first-time/resume SO-ARM 직결 완주** — SO-ARM 2대 + 카메라 Orin USB 직결 후 `bash ~/smolvla/orin/tests/check_hardware.sh --mode first-time` (또는 resume) 완주. 기대: `ports.json`·`cameras.json` 생성·갱신 + exit 0 + FAIL 0건.
  2. **[O1-2] flow 3 기본값 → hil_inference dry-run + JSON 생성** — SO-ARM 환경에서 `bash ~/smolvla/orin/interactive_cli/main.sh` → flow 3 기본값 선택 → hil_inference.py dry-run 실행. 기대: `/tmp/hil_dryrun.json` 생성, exit 0.
  3. **[O1-3] hil_inference 50-step SO-ARM live 모드 실 동작** — 04 G2 verification_queue 통합. leader 기울임 → follower 추종 50-step 완주 확인.
- **prod-test-runner 결과 요약**: AUTO_LOCAL — py_compile 4/4 PASS, bash -n PASS, ruff All checks passed. deploy_orin.sh 자율 배포 성공 (inference.py 등 전송). SSH_AUTO — Orin flows/ 4파일 확인, venv PASS, cusparseLt PASS (libcusparseLt.so.0), py_compile PASS, bash -n PASS, entry --help argparse 정상 (ModuleNotFoundError X), inference flow3/4/5 import_PASS, 3모듈 일괄 import "orin import OK". menu walkthrough (LD_LIBRARY_PATH='' 사전 초기화): flow1 Orin 선택 정상 → check_hardware.sh 진입 → CUDA/torch PASS (torch=2.5.0a0, cuda=12.6) → SO-ARM FAIL 예상 (미연결) → cameras 0 — 전체 flow 0~2 정상. hil_inference.py 인자 정합 grep — gate-json L315, model-id L326, ckpt-path L336, output-json L309, mode choices dry-run/live, parser.error 강제 L388 — 전 항목 PASS.
- **참고 파일**: `context/todos/O1/03_prod-test.md`

#### TODO-O3: orin/scripts/setup_env.sh 정비 (02 BACKLOG #7·#8)

- **상태**: AUTOMATED_PASS
- **환경 레벨**: AUTO_LOCAL (정적 검증 + 경로 시뮬 완료 — SSH 배포 불요)
- **사용자 검증 필요 사항**: 없음 (spec DOD 가 실 셋업 검증 BACKLOG 허용 명시)
- **prod-test-runner 결과 요약**: bash -n exit 0 (PASS). SMOLVLA_ROOT L28 정의 (`$(dirname "$0")/../..`) + L108 TORCHVISION_WHL 사용 확인. 경로 시뮬 — SMOLVLA_DIR=smolVLA/orin, SMOLVLA_ROOT=smolVLA/, `[ -f "$TORCHVISION_WHL" ]` = true (wheel 파일 devPC 실존). dpkg --audit L19 + sudo 안내만 echo L22 + exit 1 L24 확인. pip install "$TORCHVISION_WHL" L112 확인. BACKLOG 02 #7·#8 모두 "완료 (07 O3, ...2026-05-03)" 마킹 확인. orin/lerobot/ 미변경, orin/pyproject.toml 미변경 — Coupled File Rule 준수. DOD 3항 전부 자동 충족.
- **참고 파일**: `context/todos/O3/03_prod-test.md`

#### TODO-O4: hil_inference.py 카메라 자동 발견 + wrist flip 도구 정비 (03 BACKLOG #15·#16)

- **상태**: 사용자 무시 결정 (2026-05-04 — Orin 실 카메라 직결 검증 BACKLOG 이관, BACKLOG 07 #9 통합 PHYS_REQUIRED 묶음에 합류. ANOMALIES 07 #4 USER_OVERRIDE 누적)
- **환경 레벨**: AUTO_LOCAL (정적 PASS) + SSH_AUTO (Orin 배포·import·graceful 동작 PASS) + PHYS_REQUIRED (실 카메라 연결 자동 발견 확인)
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장 이동 시, O 분기 게이트 3 통합 검증 권장):
  1. **[O4-1] 실 카메라 2대 연결 시 `_auto_discover_cameras()` 정상 발견 + 인덱스 정합** — SO-ARM + 카메라 2대 USB 직결 Orin 환경에서:
     ```bash
     source ~/smolvla/orin/.hylion_arm/bin/activate
     lerobot-find-cameras opencv
     # 출력 확인: Camera #0: /dev/videoN, Camera #1: /dev/videoM
     python3 ~/smolvla/orin/inference/hil_inference.py \
         --mode dry-run \
         --gate-json ~/smolvla/orin/config/ \
         --max-steps 1 \
         --output-json /tmp/hil_o4_test.json
     # 기대: [camera] 자동 발견 성공 — top:N, wrist:M (2대 발견)
     # 또는 --cameras 생략 시 자동 발견 결과 확인
     # 인덱스가 lerobot-find-cameras opencv 출력과 일치하는지 육안 확인
     ```
- **prod-test-runner 결과 요약**: devPC py_compile PASS, ruff All checks passed!. deploy_orin.sh 자율 배포 성공 (rsync speedup 229.54, Orin hil_inference.py 2026-05-04 13:01 타임스탬프 확인). Orin SSH — py_compile PASS, --help 정상 출력 (`lerobot-find-cameras opencv` 안내 + `--flip-cameras wrist` 안내 포함). `_auto_discover_cameras` import OK. OpenCVCamera.find_cameras `<class 'function'>` 접근 확인. 카메라 미연결 graceful 처리 — `None` 반환 + `[camera] 연결된 카메라를 찾지 못했습니다. lerobot-find-cameras opencv 로 확인하세요.` 출력. README.md — L47 사전 단계 섹션 + L79 wrist 카메라 플립 섹션 존재 확인. BACKLOG.md L72·L73 각각 "완료 (07 O4, 2026-05-03)..." 마킹 확인. DOD 4항 전부 자동 충족.
- **참고 파일**: `context/todos/O4/03_prod-test.md`

#### TODO-O5: Orin ckpt 로드 + 더미 obs 추론 (Wave 4 / 게이트 3)

- **상태**: AUTOMATED_PASS
- **환경 레벨**: SSH_AUTO (Orin 배포·ckpt 복구·추론 완료)
- **사용자 검증 필요 사항**: 없음 — DOD 전 항목 자동 충족
- **prod-test-runner 결과 요약**: deploy_orin.sh 자율 배포 (run_python.sh + inference_baseline.py 갱신). 배포 --delete 로 Orin ckpt 삭제 → sync_ckpt_dgx_to_orin.sh 재실행으로 복구 (7파일 865M). run_python.sh `-u` 플래그 버그 발견 (activate 내 $LD_LIBRARY_PATH unset → exit 1) — BACKLOG 추가. 우회 (`export LD_LIBRARY_PATH=''`) + venv 직접 activate 양방향 확인: cuSPARSELt ImportError X, `Loading weights from local directory`, `[DOD] action shape (1, 6) OK`, exit 0. input_features: state(6,) + camera1/camera2/camera3(3,256,256) — T3 ckpt camera key smolvla_base 동일 구조 (shape 불일치 없음). SO-ARM 직결 hil_inference 50-step 은 PHYS_REQUIRED BACKLOG 유지 (기존 BACKLOG #1).
- **참고 파일**: `context/todos/O5/03_prod-test.md`

---

### [그룹 W — AUTOMATED_PASS (사용자 검증 불요)]

#### TODO-W1: SKILL.md L111 경로 확인 (Read 전용)

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: `.claude/skills/lerobot-reference-usage/SKILL.md` L111 — 기대 경로 `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 완전 일치 확인. 대상 파일 실존 확인. 변경 파일 없음 — Category A 미개입.
- **참고 파일**: `context/todos/W1/03_prod-test.md`

#### TODO-W2: 99_lerobot_upstream_Tracking.md 색인 섹션 신설

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: "디렉터리 파일 색인" 섹션 L7 존재 확인. 7개 파일 전체 등록 확인 (01~05 .md + check_update_diff.sh + 99_*.md). 04_dgx_lerobot_diff.md·05_datacollector_lerobot_diff.md 등록 + 05 향후 갱신 불요 사유 명시 확인. BACKLOG 06 #7 "완료 (07 W2 갱신, 2026-05-03)" 마킹 확인. bash 명령 예시 미추가 확인. docs/reference/ 변경 0건.
- **참고 파일**: `context/todos/W2/03_prod-test.md`

#### TODO-W3: 02_orin_pyproject_diff.md 동기화 절차 명문화

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: L216 "upstream 동기화 시 entrypoint 정리 절차 (07 W3 추가, 2026-05-03)" 섹션 존재 확인. 6단계 절차 완전 확인 (1=Read, 2=유지 9개 표, 3=제거 2개 표, 4=재추가 즉시 삭제, 5=신규 판단, 6=이력·Coupled File). 유지 9개·제거 2개 목록이 orin/pyproject.toml 실제 내용과 완전 일치. "(아래 절차 참조)" cross-ref 확인. BACKLOG 04 #1 "완료 (07 W3 명문화, 2026-05-03)" 마킹 확인.
- **참고 파일**: `context/todos/W3/03_prod-test.md`

#### TODO-W4: docs/storage/15_orin_config_policy.md 신규 작성

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: 15_orin_config_policy.md 135줄 실존 확인. §1~§8 8섹션 완전성 확인 (결정·추적 파일·결정 사유·충돌 가능성·override·갱신 절차·변경 이력·차후 후보). BACKLOG 04 #3 "완료 (07 W4 정책 문서 신규, 2026-05-03)" 마킹 확인. .gitignore 변경은 W4 산출물 아님 (TODO-P2 별도) — Category B 미개입 확인.
- **참고 파일**: `context/todos/W4/03_prod-test.md`

#### TODO-W5: 사이클 중 자연 처리된 BACKLOG 항목 일괄 마킹·정리 + spec 본문 체크박스 전수 마킹

- **상태**: AUTOMATED_PASS
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: BACKLOG.md "완료 (07..." 패턴 12건 확인 (02#5·#7·#8 / 03#14·#15·#16 / 04#1·#3 / 05#2·#3 / 06#6·#7). 신규 07#7·#8·#9 3건 존재 확인 (BACKLOG.md L149~L151). 표 헤더 7섹션 일관. spec 본문 [x] 27건·[ ] 0건 (grep -c 결과). "## 사이클 중 추가된 todo" 섹션 L397 존재 + D1a·D4~D8 6건 모두 확인. cycle 2 R1 (T3 "Phase 3 대기" 제거 + AUTOMATED_PASS 명시) / R2 (D1a~D8 trigger 경위 명시) / R3 (T2 "완주 확인 PASS" 명확화) 모두 반영 확인. Category A/B/D Hard Constraints 미위반. docs/storage/ bash 예시 추가 없음.
- **참고 파일**: `context/todos/W5/03_prod-test.md`
