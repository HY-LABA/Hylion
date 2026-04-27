# 20260425_teleoptest
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: Orin 환경 재검증 + SO-ARM 단일 쌍 teleoperation 동작 확인  
> 환경: Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`  
> 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)  
> Orin 코드 경로: `/home/laba/smolvla/` (rsync 배포 기준)  
> 하드웨어: SO-101 follower (12V, STS3215) x1 + SO-101 leader (7.4V, STS3215) x1  
> 작성: 2026-04-25

---

## Todo

### [x] TODO-01: Orin 환경 재검증

- 타입: test
- DOD: smoke_test.py 에러 없이 완료, smolVLA 모델 forward pass 성공 확인
- 구현 대상: 없음 (코드 수정 불필요)
- 테스트: prod 코드 검증 (`~/smolvla/examples/tutorial/smolvla/smoke_test.py`) ← 실제 경로 확인됨
- 제약: devPC에서 `ssh orin` 접속 후 Orin 내부에서 실행. rsync 배포로 코드가 Orin에 있어야 함.
- 완료: 20260425_2105 — 4단계 all pass, DOD 충족
- 잔여 경고: `nvcc` 미탐지, `libcusparseLt` 시스템 등록 미확인 — venv fallback으로 smoke test 정상 완료. 추후 필요시 별도 확인.

#### 테스트 단계

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC에서 `ssh orin` 접속 | 프롬프트 `laba@ubuntu` 표시 | pass | SSH 명령이 Orin `HOST=ubuntu`에서 실행됨 |
| 2 | Orin에서 `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | pass | `VIRTUAL_ENV=/home/laba/smolvla/.venv` 확인 |
| 3 | `python ~/smolvla/examples/tutorial/smolvla/smoke_test.py` 실행 | 에러 없이 완료 | pass | 실제 배포 경로로 수정 후 실행, exit code 0 |
| 4 | forward pass 출력 확인 | action tensor 출력 또는 성공 메시지 | pass | `action shape: torch.Size([1, 6])`, `모든 smoke test 통과. Orin 실행 환경 정상.` |

### [x] TODO-02: SO-ARM 포트 탐지 및 런커맨드 문서화

- 타입: both
- DOD: follower/leader 포트가 확인되고, calibrate·teleoperate 실행에 필요한 포트 포함 커맨드가 `orin/scripts/` 또는 docs에 기록됨
- 구현 대상:
  - `orin/scripts/run_teleoperate.sh` (또는 동등한 위치) — 포트 포함 lerobot-calibrate·lerobot-teleoperate 커맨드 작성
- 테스트: prod 검증 — 작성된 스크립트를 Orin에서 실행해 정상 동작 확인
- 제약: `config_so_follower.py`·`config_so_leader.py` 수정 불필요 (port 필드는 required CLI arg 설계이며 기본값 없는 것이 의도적)
- 잔여 리스크: USB 연결 순서에 따라 ttyACM 번호가 바뀔 수 있음 — udev rule 필요 여부 추후 확인
- **포트 확인 완료 (20260425_2309)**: follower=`/dev/ttyACM0` (serial `5B42138563`), leader=`/dev/ttyACM1` (serial `5B42138566`)
- **구현 완료 (20260425_2325)**: `orin/scripts/run_teleoperate.sh` 작성, `bash -n` 문법 검증 통과, `--help` 출력 확인. `all|calibrate-follower|calibrate-leader|teleoperate` 서브커맨드 지원
- **prod 검증 FAIL (20260425_2332)**: 배포 미완료, sudo 권한 문제
- **prod 검증 재테스트 FAIL (20260426_0019)**: `[ ]` 유지
  - PASS: SSH·venv 활성화, /dev/ttyACM* 장치 확인, --help 출력
  - FAIL: calibrate-follower·calibrate-leader·teleoperate 모두 `sudo chmod 666 /dev/ttyACM*` 단계에서 비밀번호 요구로 중단
  - 원인: `laba`가 `dialout` 그룹에 있고 포트 접근 권한은 이미 충족됨에도 스크립트가 매번 `sudo chmod`를 실행 → **`run_teleoperate.sh`에서 sudo chmod 제거 또는 조건부 처리 필요** → `/handoff-task` 코드 수정 요청
- **sudo chmod 제거 완료 (20260426_0024)**: `chmod_ports()` 함수 및 모든 호출 제거, `bash -n` 검증 통과 → **배포 후 prod 재테스트 필요**
- **prod 재테스트 FAIL (20260426_0035)**: `[ ]` 유지
  - PASS: SSH·venv·포트 확인, sudo 없이 lerobot entrypoint 진입 확인 — sudo 문제 해결됨
  - FAIL: `lerobot-calibrate`·`lerobot-teleoperate` 모두 `ImportError: cannot import name 'bi_openarm_follower' from 'lerobot.robots'` 로 중단 → **orin/lerobot inference-only 레이어에서 누락된 robot 클래스 문제, 별도 조사 필요**
  - 경로 정정: 테스트 커맨드 경로 `~/smolvla/orin/scripts/` → `~/smolvla/scripts/` (배포 구조 반영)
- **ImportError 수정 완료 (2026-04-26)**: `orin/lerobot/scripts/` 4개 파일(calibrate, teleoperate, record, replay)에서 존재하지 않는 robot/teleoperator 임포트 제거 → `so_follower`·`so_leader` 만 유지. `py_compile` 검증 통과.
- **완료 (20260426_0045)**: calibrate-follower·calibrate-leader sudo 없이 calibration 절차 진입 확인. teleoperate는 calibration 파일 미생성으로 BLOCKED — TODO-03 선행 조건이므로 TODO-02 DOD 충족.

### [x] TODO-03a: motor encoder 진단 스크립트 구현

- 타입: both
- DOD: follower 포트에서 motor id 1~6 `Present_Position` 값을 주기적으로 출력하며, 관절을 손으로 움직일 때 해당 값이 실시간으로 변하는지 확인할 수 있는 스크립트가 `orin/calibration/` 에 배포 가능한 형태로 작성됨
- 구현 대상:
  - `orin/calibration/diagnose_motor_encoder.py` (신규) — follower 포트 연결, motor id 1~6 `Present_Position` 1Hz 주기 출력
- 테스트: prod 검증 — Orin에서 follower 연결 후 스크립트 실행, 각 관절 수동 구동 시 값 변화 확인
- 제약: TODO-02 완료 후 진행. `docs/reference/` 하위 수정 금지.
- 배경: calibration 2회 FAIL (20260426, 20260427) — 관절을 손으로 구동해도 일부 `Present_Position`이 2047 고정. encoder 미응답이 원인으로 추정. calibration 재시도 전 하드웨어 응답 여부를 진단 후 진행.
- 진단 확인 항목:
  1. `/dev/serial/by-id/` 기준 follower/leader serial → `/dev/ttyACM*` 매핑 출력
  2. follower 포트 motor id 1~6 `Present_Position` raw 값 주기 출력
  3. 각 관절을 하나씩 움직일 때 해당 motor id 값이 변하는지 확인
  4. 관절명(`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`)과 motor id(1~6) 매핑이 실제 응답과 일치하는지 확인
- **구현 완료 (20260427_1035)**: `orin/calibration/diagnose_motor_encoder.py` 작성. `/dev/serial/by-id/` 매핑 출력, Joint/ID/Raw/Delta 테이블 1Hz 루프, Ctrl+C 정상 종료. `python -m py_compile` PASS. → **Orin 배포 후 prod 검증 필요**
- **테스트 BLOCKED (20260427_1050)**: `[ ]` 유지
  - Codex 비대화형 6단계 전부 PASS (SSH·venv·장치·파일·문법·serial/by-id 확인)
  - 개발자 직접 검증(#1-10) 전체 미실행 — `lerobot-find-port` 포트 식별 + 물리 encoder 진단 필요
  - **⚠️ 신규 발견 — 포트 역전**: `/dev/serial/by-id/` 확인 결과 `ttyACM0`=serial `5B42138566`(leader), `ttyACM1`=serial `5B42138563`(follower) → **TODO-02 기록값과 역전**. USB 연결 순서 변경으로 ttyACM 번호가 바뀐 것으로 추정. `run_teleoperate.sh` 하드코딩 포트(`--follower-port /dev/ttyACM0`)가 실제로는 leader에 연결되어 있을 가능성 높음. **calibration 2회 FAIL의 실제 원인일 수 있음.**
  - **다음 액션**: `lerobot-find-port`로 follower/leader 포트 재식별 → `run_teleoperate.sh` 포트 값 수정 → encoder 진단 → calibration 재시도
- **prod 검증 완료 (20260427_1103)**: `[x]` 처리
  - `lerobot-find-port` 물리 분리로 포트 확정: **follower=`/dev/ttyACM1`** (serial `5B42138563`), **leader=`/dev/ttyACM0`** (serial `5B42138566`)
  - follower·leader 두 팔 모두 motor id 1~6 Raw/Delta 정상 변화 확인 (encoder 하드웨어 정상)
  - Ctrl+C 정상 종료 확인
  - **calibration FAIL 원인 확정**: encoder 이상이 아닌 포트 역전 — `run_teleoperate.sh` 포트 수정 필요

### [x] TODO-03: SO-ARM calibration 파일 생성

- 타입: test
- DOD: follower + leader calibration 파일이 각각 생성되어 지정 경로에 저장됨
- 구현 대상: 없음 (calibration은 스크립트 실행으로 파일 자동 생성)
- 테스트: prod 검증 (`lerobot_calibrate` — follower/leader 순서로 실행, 양 팔 연결 필요)
- 제약: TODO-02 완료 후 진행. **TODO-03a 완료. `run_teleoperate.sh` 포트 수정 후 진행 필요.**
- **⚠️ 포트 수정 필수 (20260427_1103 확정)**: `run_teleoperate.sh` 내 follower/leader 포트 하드코딩이 역전되어 있음 → calibration 재시도 전 `/handoff-task`로 수정 필요
  - 수정 전: `follower=/dev/ttyACM0`, `leader=/dev/ttyACM1`
  - 수정 후: `follower=/dev/ttyACM1`, `leader=/dev/ttyACM0`
- **[Codex 주의] 이 TODO는 비대화형 SSH로 실행 불가:**
  - `lerobot-calibrate`는 내부적으로 `input()` 호출 → 비대화형 SSH에서 `EOFError` 발생
  - 팔 관절을 손으로 직접 min→max→min 구동하는 물리 조작 필요
  - **Codex 역할**: 개발자 직접 검증 완료 후 calibration JSON 파일 존재 여부만 SSH로 확인
  - **개발자 역할**: Orin Remote SSH 터미널(VS Code Remote SSH 또는 직접 접속)에서 calibration 대화형 실행 + 물리 조작
- 잔여 리스크: 모터 초기 위치가 맞지 않으면 calibration 실패 가능
- **테스트 FAIL (20260426_0110)**: `[ ]` 유지
  - FAIL: follower calibration 중 모든 관절 min=max=2047 → `ValueError: Some motors have the same min and max values`
  - 원인: calibration range 기록 단계에서 관절을 전체 범위로 물리적으로 움직이지 않음 → **재시도 시 팔 관절을 직접 손으로 전체 범위 구동 필요**
  - leader calibration·파일 생성 미수행
- **테스트 BLOCKED (20260427_1003)**: `[ ]` 유지
  - Codex 비대화형 환경 확인 (SSH·venv·장치·스크립트) 5단계 전부 PASS
  - BLOCKED: 개발자 대화형 단계(#1-7) 미실행 — 물리 조작 필요 (관절 전체 범위 구동)
  - FAIL: calibration JSON 파일 미생성 (Codex 검증 #6, #7 모두 출력 없음)
  - **다음 액션**: 개발자가 Orin Remote SSH 터미널에서 follower→leader 순서로 calibration 직접 수행 필요. 각 관절을 min→max→min 전체 범위로 천천히 구동할 것.
- **테스트 FAIL (20260427_1021)**: `[ ]` 유지
  - 관절을 물리적으로 구동했으나 일부 관절 `Present_Position` 값이 2047 근처에서 변하지 않음
  - 동일 에러 재발: `ValueError: Some motors have the same min and max values`
  - **신규 원인**: 물리 조작 부족이 아닌 encoder 미응답 — 하드웨어/배선/모터 ID 문제 가능성
  - **선행 진단 필요**: 모터 encoder raw 값 실시간 모니터링으로 관절 움직임 → 값 변화 여부 확인 후 calibration 재시도
  - **다음 액션**: motor encoder 진단 스크립트 구현 → `/handoff-task` 로 요청 (Backlog #8 참조)
- **완료 (20260427_1300)**: `[x]` 처리
  - follower: `/home/laba/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json` 생성 완료
  - leader: `/home/laba/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/my_awesome_leader_arm.json` 생성 완료
  - 모든 관절 min ≠ max 확인 (range 정상 기록)

### [x] TODO-04: Teleoperation 동작 검증

- 타입: test
- DOD: leader 움직임에 follower가 실시간으로 추종함을 육안 확인
- 구현 대상: 없음
- 테스트: prod 검증 (`lerobot_teleoperate` — 양 팔 연결 필요)
- 제약: TODO-03 완료 후 진행
- 잔여 리스크: follower 응답 지연 또는 모터 토크 부족 가능성
- **완료 (20260427_1310)**: `[x]` 처리
  - 60Hz 텔레오페레이션 루프 정상 동작, 개발자 육안 추종 확인 완료
  - 잔여 리스크: follower `id_=3` (elbow_flex 추정) `Torque_Enable` write 실패 간헐 발생 — 최초 시도 실패 후 재실행으로 복구. 원인 미확정 (Backlog #10 참조)

### [x] TODO-05: 카메라 인식 및 스트림 확인

- 타입: test
- DOD: Orin에서 OV5648 카메라 2대가 `/dev/video*`로 인식되고, 각각 이미지 스트림이 정상 출력됨. 화각·포커스 실물 사양 확정.
- 구현 대상: 없음 (카메라 인식은 커널/드라이버 레벨, 코드 수정 불필요)
- 테스트: prod 검증 — Orin에 카메라 2대 USB 연결 후 아래 순서로 확인
  1. `/dev/video*` 장치 목록 확인 (카메라 2대 탐지 여부)
  2. 각 장치에서 이미지 스트림 출력 확인 (`v4l2-ctl` 또는 OpenCV 캡처)
  3. 실물 확인: 화각이 68°인지 120°인지 육안·스트림으로 식별 (스펙 시트상 72°, 제품 표기 68°로 불일치)
  4. 실물 확인: Fixed Focus인지 Auto Focus인지 확인 (스펙 시트 Fixed, 제품명 Auto로 불일치)
- 제약: devPC에서 `ssh orin` 접속 후 Orin에서 실행. 카메라(OV5648 USB, 2대) Orin에 연결 필요.
- 잔여 리스크:
  - USB 포트 수 부족 시 허브 필요 (SO-ARM 보드 2개 + 카메라 2대 동시 연결)
  - `/dev/video*` 번호가 연결 순서에 따라 바뀔 수 있음 — udev rule 필요 여부 추후 확인
  - 화각(68° vs 72°)·포커스(Fixed vs Auto) 표기 불일치 → 실물 확인 후 `02_hardware.md` 업데이트 필요
- **완료 (20260427_1347)**: `[x]` 처리
  - `/dev/video0~3` 인식 (카메라 1대당 노드 2개, `/dev/video0`·`/dev/video2` 사용)
  - `gst-launch-1.0`으로 실시간 스트리밍 정상 확인 (`v4l2-ctl` 미설치로 대체)
  - 화각: 120° 광각 아님. 수평 FOV 실측 약 53° (50cm 거리에서 가로 약 50cm). 68° 표기는 대각 FOV로 추정
  - 포커스: Auto Focus 확인 (스펙 시트의 Fixed 표기는 오류)
  - **후속 필요**: `02_hardware.md` 화각·포커스 실측값 업데이트, `v4l2-ctl` 설치 검토 (Backlog #11)

---

## Backlog

> 스펙 진행 중 발견된 추후 개발 과제. 현재 워크플로우를 블로킹하지 않으나 향후 대응 필요.

| # | 항목 | 발견 출처 | 우선순위 |
|---|------|-----------|----------|
| 1 | SO-ARM USB 포트 고정을 위한 udev rule 검토 (`ttyACM*` 번호가 연결 순서에 따라 바뀜) — **20260427 포트 역전 실제 발생으로 우선순위 상향** | TODO-02 / TODO-03a | 높음 |
| 2 | `lerobot-find-port` 대화형 스크립트 → 비대화형 SSH 실행 지원 방법 확인 | TODO-02 | 낮음 |
| 3 | `orin/scripts/` 파일구조 재편: 레퍼런스(lerobot upstream·seeed-lerobot)에서 가져와 문법 수정한 스크립트와 신규 작성 스크립트를 디렉터리 또는 네이밍으로 명확히 구분 (예: `adapted/`, `custom/` 또는 접두사 규칙) — Copilot 구현 | TODO-02 | 중간 |
| 4 | `laba` 사용자를 `dialout` 그룹에 추가 (`sudo usermod -aG dialout laba`) — 완료 (2026-04-26) | TODO-02 prod 검증 | 완료 |
| 5 | rsync 배포 플로우 명문화 — devPC에서 코드 수정 후 Orin 배포까지의 절차를 `docs/` 또는 스크립트로 정리 (현재 암묵적으로 운영 중) | TODO-02 prod 검증 | 중간 |
| 6 | `ImportError: cannot import name 'bi_openarm_follower' from 'lerobot.robots'` — 수정 완료 (2026-04-26) | TODO-02 prod 검증 | 완료 |
| 7 | `lerobot-calibrate`는 `input()` 호출 대화형 스크립트 — 비대화형 SSH에서 EOFError 발생. 실제 calibration은 interactive 터미널(Remote SSH VSCode 또는 직접 접속)에서 실행 필요. 문서화 또는 주석 추가 고려 | TODO-02 prod 검증 | 낮음 |
| 8 | motor encoder 진단 스크립트 구현 → **TODO-03a로 승격 (2026-04-27)** | TODO-03 prod 검증 | 완료 |
| 9 | `포트 식별 → 저장 → encoder 진단` 통합 스크립트 개선 — 현재는 `lerobot-find-port` 결과를 수동 복사하여 `diagnose_motor_encoder.py --port`에 입력해야 함. 통합 시 수동 입력 실수 및 포트 역전 위험 감소 | TODO-03a prod 검증 | 낮음 |
| 10 | follower `id_=3` (elbow_flex 추정) `Torque_Enable` write 실패 간헐 발생 — 최초 teleoperate 시도 시 루프 시작 불가, 재실행으로 복구됨. 원인 미확정 (케이블 접촉 불량, 모터 초기화 타이밍, firmware 이슈 가능성). 재현 조건 및 원인 조사 필요 | TODO-04 prod 검증 | 중간 |
| 11 | Orin에 `v4l2-ctl` 미설치 — 카메라 장치 포맷·드라이버 확인 불가. `sudo apt install v4l-utils` 로 설치 가능. `setup_env.sh` 또는 설치 문서에 추가 고려 | TODO-05 prod 검증 | 낮음 |
| 12 | OV5648 카메라 화각·포커스 실측값을 `docs/storage/02_hardware.md`에 반영 필요 — 화각: 수평 FOV 약 53°(68°는 대각), 포커스: Auto Focus(스펙 시트의 Fixed는 오류) | TODO-05 prod 검증 | 중간 |
