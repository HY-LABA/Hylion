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

## 04_infra_setup

### [TODO-T2] DGX → 시연장 Orin ckpt 전송 경로 재확인

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - Read 직독 정적 분석: 문법·로직 이상 없음 (code-tester READY_TO_SHIP 재확인)
  - Bash 도구 차단으로 bash -n / shellcheck 직접 실행 불가 (SKILL_GAP #1 prod-test-runner T2 재현)
  - 기존 `sync_ckpt_dgx_to_orin.sh` 변경 없음 확인 (git diff 0줄, git status 미포함)
  - 인터페이스 일관성 (--run/--step/--dry-run/--help) 확인
  - DGX·DataCollector 미연결 — 시연장 환경 미확정 + DataCollector 미구매

- **사용자 검증 필요 사항**:
  1. **SSH alias 미등록 오류 동작 확인** (현재 즉시 가능):
     - `~/.ssh/config` 에 `Host datacollector` 없는 상태에서 `bash scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run` 실행
     - 예상: "[sync-ckpt-dc] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다. docs/storage/09_datacollector_setup.md §5-1 을 참조..." 출력 + exit 1 확인
  2. **시연장 네트워크 케이스 분류** (시연장 방문 시):
     - 시연장 WiFi 에 Orin 연결 후 `ssh orin "hostname"` 성공 여부 확인
     - 성공 → 케이스 1 또는 2 (기존 `sync_ckpt_dgx_to_orin.sh` 사용)
     - 실패 → 케이스 3 확인: DataCollector 에서 `ssh laba@<ORIN_IP> hostname` 성공 여부
     - 케이스 확정 후 `docs/storage/others/ckpt_transfer_scenarios.md` 사용 케이스 표시
  3. **케이스 3 실물 dry-run 검증** (DataCollector 구매 + 케이스 3 확정 시):
     - DataCollector → Orin SSH 키 배포 (`ssh-copy-id laba@<ORIN_IP>`)
     - `bash scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run` 실 실행
     - rsync dry-run 로그 출력 + DataCollector 측 `~/smolvla/ckpt_transfer/` 파일 미생성 확인

- **prod-test-runner 결과 요약**: Read 직독 정적 분석 PASS (DOD 2항목 모두 확인). 기존 스크립트 회귀 없음 (git diff 0줄). 인터페이스 5개 플래그 일관 확인. DRY_RUN 전파 정상. SSH alias pre-check 로직 확인. Bash 도구 sandbox 차단 — SKILL_GAP #1 T2 재현. 사용자 실물 검증 3건 verification_queue 추가.
- **참고 파일**: `context/todos/T2/03_prod-test.md`
- **전제 조건**: 1번은 현재 즉시 가능. 2번은 시연장 방문 시. 3번은 DataCollector 구매 + 케이스 3 확정 후.
- **주의**: 실 ckpt 전송 검증은 05_leftarmVLA 학습 시점 책임.

---

### [TODO-T3] devPC sync hub 갱신 (deploy_datacollector.sh)

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - Read 직독 정적 분석: 구문·로직 이상 없음 (code-tester READY_TO_SHIP 재확인)
  - Bash 도구 차단으로 bash -n / shellcheck / --dry-run 실 실행 불가 (SKILL_GAP #1 prod 재현)
  - DataCollector 머신 미존재로 실 SSH 연결 검증 불가 (예상된 상황)

- **사용자 검증 필요 사항**:
  1. **SSH alias 미등록 오류 동작 확인** (현재 즉시 가능):
     - `~/.ssh/config` 에 `Host datacollector` 없는 상태에서 `bash scripts/deploy_datacollector.sh --dry-run` 실행
     - 예상: "ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다. docs/storage/09_datacollector_setup.md §5-1 을 참조..." 출력 + exit 1 확인
  2. **dry-run 실 동작 확인** (TODO-D3 완료 + SSH alias 등록 후):
     - `~/.ssh/config` 에 `Host datacollector` alias 등록
     - `bash scripts/deploy_datacollector.sh --dry-run` 실행
     - rsync 전송 대상 파일 목록 출력 + 실 전송 없음 확인 ("--dry-run 완료" 메시지 출력)
  3. **실 배포 동작 확인** (TODO-D3 완료 + 사용자 동의 후):
     - `bash scripts/deploy_datacollector.sh` 실 실행
     - DataCollector 측 `ls ~/smolvla/datacollector/`, `ls ~/smolvla/docs/reference/lerobot/` 결과 확인

- **prod-test-runner 결과 요약**: Read 직독 정적 분석 PASS (DOD 3항목 모두 충족 확인). Bash 도구 sandbox 차단으로 bash -n / shellcheck / dry-run 실 실행 불가 — SKILL_GAP #1 prod-test-runner 환경 재현 확인. 사용자 실물 검증 3건 verification_queue 추가.
- **참고 파일**: `context/todos/T3/03_prod-test.md`
- **전제 조건**: 1번은 현재 즉시 가능. 2·3번은 TODO-D3 완료 후 가능.

---

### [TODO-G2] check_hardware.sh + hil_inference.py 통합 검증

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - Read 직독 정적 분석 6단계: 코드 구조·분기·인자 파싱·JSON schema 이상 없음
  - Bash 도구 차단으로 SSH 실 실행 불가 (SKILL_GAP #1 prod-test-runner G2 재현)
  - cycle 2 수정 반영 확인: `_to_idx` Path 반환, dead catch 제거, 시나리오 6번 보강
  - ports.json·cameras.json placeholder null 상태 — 실 하드웨어 연결 후 검증 필요

- **사용자 검증 필요 사항**:
  1. **Orin 콘솔 first-time 모드** (카메라 2대 + SO-ARM follower 연결 후):
     ```bash
     bash ~/smolvla/orin/tests/check_hardware.sh --mode first-time
     ```
     - 4단계 (venv → CUDA → soarm_port → cameras) 모두 PASS 확인
     - wrist 카메라 상하반전 여부 응답 (BACKLOG 03 #16 해소 확인)
     - 완료 후 `~/smolvla/orin/config/ports.json`·`cameras.json` 에 실 값 저장 확인
  2. **Orin 콘솔 resume 모드** (first-time 완료 후):
     ```bash
     bash ~/smolvla/orin/tests/check_hardware.sh --mode resume --output-json /tmp/hw_resume.json
     ```
     - exit=0 + 4단계 PASS 확인
     - `cat /tmp/hw_resume.json` 으로 JSON 구조 확인 (steps 4개 status=PASS, summary.exit_code=0)
  3. **hil_inference.py --gate-json 실 동작** (first-time 완료 후, SO-ARM + 카메라 연결 상태):
     ```bash
     source ~/smolvla/orin/.hylion_arm/bin/activate
     python ~/smolvla/orin/inference/hil_inference.py \
       --gate-json ~/smolvla/orin/config/ports.json \
       --mode dry-run --output-json /tmp/hil_gate_test.json --max-steps 5
     ```
     - `[gate] follower_port ←` 로그 출력 (ports.json 자동채움) 확인
     - `[gate] cameras ←` 로그 출력 (cameras.json 자동채움) 확인
     - `[gate] flip_cameras ←` 로그 출력 (wrist.flip=true 인 경우 — BACKLOG 03 #16 자동 해소 확인)
     - 5 step dry-run 완료 + `/tmp/hil_gate_test.json` 저장 확인

- **prod-test-runner 결과 요약**: Read 직독 정적 분석 6단계 PASS. check_hardware.sh 문법 구조 이상 없음 (set -uo pipefail, heredoc quoting, 환경변수 경유 Python 호출, resume null 분기 정상). hil_inference.py cycle 2 수정 반영 확인 (`_to_idx` Path 반환, dead catch 제거). `--gate-json` argparse 등록 + load/apply 헬퍼 흐름 정상. Bash 도구 sandbox 차단으로 실 SSH 실행 불가 — SKILL_GAP #1 G2 재현 확인. 사용자 실물 검증 3건 verification_queue 추가.
- **참고 파일**: `context/todos/G2/03_prod-test.md`
- **전제 조건**: 3건 모두 Orin + 카메라 2대 + SO-ARM follower 연결 필요. 1번 선행 후 2·3번 가능.
- **배포 선행 필요**: Phase 3 진입 전 `bash scripts/deploy_orin.sh` 실행으로 `orin/inference/hil_inference.py` (cycle 2 버전) Orin 에 배포 필요.

---

### [TODO-D3] DataCollector 환경 셋업 검증 (사용자 실물 필수)

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - prod-test-runner Read 직독 정적 분석: `deploy_datacollector.sh` 구문·로직·분기 이상 없음
  - SSH alias pre-check (line 38-42) + friendly error + exit 1 분기 정확성 정적 확인 완료
  - `--dry-run` + alias 미등록 실행 순서 분석: `--dry-run` 안내 메시지 출력 후 pre-check exit 1 발생 — 예상 동작 일치
  - Bash 도구 sandbox 차단으로 `--dry-run` 실 실행 불가 (SKILL_GAP #1 D3 재현)
  - DataCollector 머신 미존재 — 실 SSH + 환경 셋업 검증 불가

- **사용자 검증 필요 사항**:

  **A. DataCollector 머신 사전 준비** (사용자 책임):
  1. 별도 PC 신규 구매 + Ubuntu 22.04 LTS 설치 (D1 §1 결정 — x86_64)
  2. 네트워크 연결 (시연장 인접 또는 임시 위치 — D1 §4 가이드 참조)
  3. devPC 측 `~/.ssh/config` 에 `Host datacollector` alias 등록 (D1 §5 패턴 — `docs/storage/09_datacollector_setup.md §5-1`)

  **B. 코드 배포** (devPC):
  4. `bash scripts/deploy_datacollector.sh --dry-run` — rsync 전송 대상 목록 확인 (SSH alias 미등록 시 friendly error 출력 + exit 1 확인)
     - 정적 분석 완료: alias 미등록 → "ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다. docs/storage/09_datacollector_setup.md §5-1 을 참조..." + exit 1 동작 확인됨
  5. `bash scripts/deploy_datacollector.sh` — 실 배포 + DataCollector `~/smolvla/datacollector/` 동기화 확인

  **C. venv 셋업** (DataCollector 콘솔 또는 SSH):
  6. DataCollector 에서 `cd ~/smolvla/datacollector && bash scripts/setup_env.sh` 실행
     - 첫 실행 5~15분 소요 가능 (PyTorch 다운로드 등 — 사용자 직접 실행 권장)
     - cusparseLt 패치 없음 확인 (Jetson 전용 처리 제거됨 — D2 DOD)
     - 표준 PyPI torch wheel 설치 PASS 확인

  **D. lerobot import 검증** (DataCollector SSH):
  7. `ssh datacollector "source ~/smolvla/datacollector/.hylion_collector/bin/activate && python -c 'import lerobot; print(lerobot.__file__)'"` — import OK + 경로 출력 확인
  8. `ssh datacollector "source ~/smolvla/datacollector/.hylion_collector/bin/activate && which lerobot-calibrate lerobot-find-cameras lerobot-find-port lerobot-find-joint-limits lerobot-record lerobot-replay lerobot-setup-motors lerobot-teleoperate lerobot-info"` — 9개 entrypoint 모두 존재 확인
  9. `ssh datacollector "source ~/smolvla/datacollector/.hylion_collector/bin/activate && which lerobot-eval lerobot-train"` — exit 1 + 빈 결과 (eval·train 등록 해제 확인)

  **E. SO-ARM·카메라 임시 연결 검증** (사용자 직접 — DataCollector 콘솔):
  10. SO-ARM 1대 USB 연결 후 `ls /dev/ttyACM*` 인식 확인
  11. `source ~/smolvla/datacollector/.hylion_collector/bin/activate && lerobot-find-port` 실행 (대화형 stdin — 콘솔 직접 필요) → 포트 발견 PASS
  12. 카메라 1대 USB 연결 후 `ls /dev/video*` 인식 확인
  13. `source ~/smolvla/datacollector/.hylion_collector/bin/activate && lerobot-find-cameras opencv` 실행 → 카메라 인덱스·해상도 발견 PASS

  **F. 결과 기록**:
  14. 단계 7~13 결과를 `docs/work_flow/context/todos/D3/03_prod-test.md` 에 기록
  15. 미흡 사항 발견 시 `docs/work_flow/specs/BACKLOG.md` § [04_infra_setup] 에 추가

- **prod-test-runner 자율 가능 영역**:
  - 단계 4 (`deploy_datacollector.sh --dry-run`) — 자율 분류 정확 (Category B 외 변경). Bash 차단으로 실 실행 불가 (SKILL_GAP #1). Read 직독으로 friendly error + exit 1 분기 정적 확인 완료.
  - 단계 5 이후 모두 사용자 실물 (DataCollector 머신 + 하드웨어 임시 연결 필요)

- **prod-test-runner 결과 요약**: Read 직독 정적 분석 PASS — `deploy_datacollector.sh` 구문·로직·SSH alias pre-check (line 38-42)·friendly error + exit 1 분기·dry-run 플래그 처리·Category D 금지 명령 미포함 모두 확인. Bash 도구 sandbox 차단 (SKILL_GAP #1 D3 재현). DataCollector 머신 미존재 — 실 SSH 검증 불가. A~F 블록 사용자 실물 필요. Verdict: NEEDS_USER_VERIFICATION.
- **참고 파일**: `context/todos/D3/03_prod-test.md`, `context/todos/D3/01_implementation.md`, `docs/storage/09_datacollector_setup.md`
- **전제 조건**:
  - 단계 4 — 현재 즉시 실행 가능 (alias 미등록 시 friendly error 확인)
  - 단계 5 — `~/.ssh/config` 에 `Host datacollector` alias 등록 후 가능
  - 단계 6~13 — DataCollector 머신 구매·OS 설치 + 코드 배포 (단계 5) 완료 후 가능
  - 단계 11·13 — SO-ARM + 카메라 임시 연결 가용 시 가능

---

### [TODO-M2] 시연장 1차 미러링 셋업 (사용자 직접)

- **상태**: 사용자 직접 수행 필요 (자동화 영역 X)
  - 본 todo 는 실제 물리 환경 셋업·측정·사진 촬영이 필요 — 자동화 워커 책임 범위 밖
  - task-executor 책임: 시나리오 정의 + 결과 기록 위치 안내

- **사용자 검증 필요 사항**:

  **A. 시연장 방문 + 측정** (`docs/storage/11_demo_site_mirroring.md` §1·§2 가이드 따라):
  1. 시연장 방문 (사용자 일정에 따라)
  2. §1 표 전체 항목 측정·기록:
     - 1-1) 책상: 높이·가로×세로·재질·색·다리 형태
     - 1-2) 작업 영역: 크기·책상 기준 위치·바닥재
     - 1-3) 조명: 조도(lux)·색온도(K)·광원 방향·높이·자연광 유입
     - 1-4) top 카메라: 마운트 높이·전후좌우 위치·하향 각도·렌즈 종류·해상도·flip 여부
     - 1-5) wrist 카메라: 부착 위치·전방 각도·케이블 경로·flip 여부
     - 1-6) 토르소·SO-ARM: 전면 거리·좌우·마운트 각도·어깨 조인트 높이·follower 초기 포즈
  3. §2 측정 도구 준비: 줄자·스마트폰(카메라·조도계·색온도계·각도 앱)·메모지
  4. **시연장 기준 사진 세트** 촬영 (§4-1 기준):
     - top 카메라 뷰 (lerobot-record 실행 중 또는 스마트폰 캡처)
     - wrist 카메라 뷰
     - 전체 환경 사진 (정면·측면 2장)

  **B. DataCollector 인근 재현** (§3 체크리스트 7개 단위 모두):
  5. 3-1) 책상 재현: 높이 ±2 cm, 상판 재질·색 유사, 작업 영역 경계 표시
  6. 3-2) 조명 재현: 조도 ±100 lux, 색온도 ±300 K, 광원 방향 시각적 유사
  7. 3-3) top 카메라 재현: 마운트 높이·전후좌우 ±2 cm, 하향 각도 ±3°, flip 설정 확정
  8. 3-4) wrist 카메라 재현: 부착 위치 ±0.5 cm, 전방 각도 ±3°, flip 설정 확정 (BACKLOG 03 #16)
  9. 3-5) 토르소·SO-ARM 재현: 전면 거리·좌우 ±2 cm, 마운트 각도 ±2°, calibration 완료
  10. 3-6) SO-ARM 포트 확인: `lerobot-find-port` 실행 → `datacollector/config/ports.json` 기재
  11. 3-7) 카메라 인덱스 확인: `lerobot-find-cameras opencv` 실행 → `datacollector/config/cameras.json` 기재

  **C. 미러링 검증** (§4 육안+사진 비교):
  12. DataCollector 인근에서 동일 각도 사진 세트 촬영 (top 카메라 뷰 / wrist 카메라 뷰 / 전체 환경 정면·측면)
  13. 시연장 사진 세트 vs DataCollector 사진 세트 나란히 비교 — §4-2 합격 기준 4항목:
      - 책상 배경 색·질감 (카메라 프레임 내 육안 차이 없음)
      - 작업 영역 위치 (top 카메라 뷰에서 SO-ARM 그리퍼 도달 범위 유사)
      - 조명 색조 (색온도 차이 명백하지 않음)
      - 카메라 앵글 (top/wrist 카메라 뷰 시연장 사진 대비 육안 유사)
  14. 차이점 기록 → §3 체크리스트 해당 항목 재조정 → 반복 (§4-2 합격 기준 통과까지)

  **D. 결과 기록** (사용자 책임):
  15. 아래 위치에 결과물 저장 (날짜를 YYYYMMDD 로 치환):
      - `docs/storage/others/demo_site_mirroring_<YYYYMMDD>/`
        - `measurements.md` — §1 표 전체 측정값 기록
        - `checklist.md` — §3 체크리스트 7개 단위 완료 표시
        - `photos/` — 시연장 기준 사진 세트 + DataCollector 인근 사진 세트
        - `comparison_notes.md` — §4 비교 결과·차이점·재조정 이력
  16. 부족한 부분 (허용 오차 초과·재현 불가 항목) 은 `docs/work_flow/specs/BACKLOG.md` § [04_infra_setup] 에 항목 추가

- **prod-test-runner 결과 요약**: 자동화 영역 X — 물리 환경 셋업이므로 prod-test-runner 개입 불가. 시나리오 정의만으로 task-executor 책임 완료.
- **참고 파일**:
  - `docs/storage/11_demo_site_mirroring.md` — §1~§5 상세 가이드
  - `context/todos/M2/01_implementation.md`
- **전제 조건**: TODO-M1 완료 (READY_TO_SHIP). TODO-D3 완료 권장 (DataCollector 측 환경 셋업 완료 후 재현 작업이 효율적).
- **잔여 리스크**: 첫 시도에서 정확한 미러링 어려움 (spec 명시). 세밀한 도메인 일치는 05_leftarmVLA 학습 결과로 피드백받아 재조정. BACKLOG 04 #6 (자동 검증 스크립트) 트리거 조건: 05/06 학습 후 미러링 부족 진단 시.

---

### [TODO-T1] DataCollector → DGX 데이터 전송 방식 결정 + 스크립트

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - Read 직독 정적 분석 5단계: 문법 구조·인자 파싱·에러 처리·cycle 2 수정 반영 이상 없음
  - Bash 도구 차단으로 bash -n / shellcheck / dry-run 실 실행 불가 (SKILL_GAP #1 T1 재현)
  - cycle 2 R1·R2·R3 수정 모두 반영 확인 (dead code 제거, heredoc single-quote + os.environ, repo_id 주석)
  - `git diff -- scripts/sync_ckpt_dgx_to_orin.sh` 출력 0줄 — 기존 스크립트 미변경 확인
  - DataCollector 머신 미존재 — SSH alias `datacollector` 미등록 상태에서 friendly error 경로 코드 분석 확인

- **사용자 검증 필요 사항**:
  1. **SSH alias 미등록 오류 + exit 1 동작 확인** (현재 즉시 가능):
     - `~/.ssh/config` 에 `Host datacollector` 없는 상태에서:
       ```bash
       bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset dummy --dry-run
       ```
     - 예상: `[sync-dataset] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다.` 출력 + exit code 1 확인
  2. **TODO-D3 완료 후 dummy dataset 생성 + dry-run 실 실행**:
     - DataCollector 머신 셋업 + SSH alias 등록 후:
       ```bash
       bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <name> --dry-run
       ```
     - 예상: rsync dry-run 로그 출력 + 실 전송 없음 확인
  3. **HF_TOKEN 사용자 설정 + dummy dataset push --private 동작 확인**:
     - DataCollector 머신에서 (TODO-D3 완료 후):
       ```bash
       export HF_TOKEN=hf_xxxxxxxxxx
       bash datacollector/scripts/push_dataset_hub.sh \
           --dataset ~/smolvla/datacollector/data/<name> \
           --repo-id <HF_USER>/<name> \
           --private
       ```
     - 예상: HF Hub 에 private dataset 업로드 확인 (URL: `https://huggingface.co/datasets/<HF_USER>/<name>`)
  4. **cycle 2 R2 heredoc 정확성 검증 (공백 포함 경로 테스트)**:
     - 공백 포함 경로로 실 실행 테스트:
       ```bash
       bash datacollector/scripts/push_dataset_hub.sh \
           --dataset "/tmp/my dataset/test" \
           --repo-id myuser/test \
           --dry-run
       ```
     - 예상: Python syntax error 없이 경로 처리 정상 (`os.environ` 방식 검증)
  5. **실 dataset 전송 (rsync + HF Hub 양방향)** — 05_leftarmVLA 학습 시점 책임:
     - 실 데이터 수집 (lerobot-record) 완료 후 시점
     - rsync 전송: `sync_dataset_collector_to_dgx.sh --dataset <name>` 실 실행 + DGX 측 파일 수 확인
     - HF Hub push: push 완료 후 DGX 에서 `LeRobotDataset(repo_id=...)` 다운로드 확인
  6. **push_dataset_hub.sh `LeRobotDataset.push_to_hub` API 활용 정확성 (실 HF Hub 호출)**:
     - 정규 LeRobotDataset 포맷 dataset 으로 실 push 후:
       - DGX 에서 `LeRobotDataset(repo_id="<HF_USER>/<name>")` 다운로드
       - dataset frame 수·shape 이상 없음 확인
     - 시점: TODO-D3 완료 + 실 dataset 존재 후

- **prod-test-runner 결과 요약**: Read 직독 정적 분석 5단계 PASS. cycle 2 수정 (R1 dead code 제거, R2 heredoc single-quote + os.environ, R3 repo_id 의미 주석) 모두 반영 확인. `push_to_hub(private=, branch=)` 시그니처 일치 확인. 기존 `sync_ckpt_dgx_to_orin.sh` 미변경 (git diff 0줄). Bash 도구 sandbox 차단 — SKILL_GAP #1 T1 재현. 사용자 실물 검증 6건 verification_queue 추가.
- **참고 파일**: `context/todos/T1/03_prod-test.md`
- **전제 조건**:
  - 1번 — 현재 즉시 가능 (`~/.ssh/config` Host datacollector 미등록 확인 목적)
  - 2~4번 — TODO-D3 완료 + DataCollector 머신 셋업 후 가능
  - 5~6번 — TODO-D3 완료 + 실 lerobot-record 데이터 존재 (05_leftarmVLA 학습 시점)
- **주의**: 실 dataset 전송 (5·6번) 은 05_leftarmVLA 학습 시점 책임.

---

### [TODO-X3] dgx/ 마이그레이션 회귀 검증 (DGX prod)

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
  - deploy_dgx.sh 성공 (rsync 5개 신규 파일 전송 확인)
  - DGX SSH 실 실행 가능 — 단계 1~6 모두 성공 (다른 todo 와 달리 SSH 차단 없음)
  - 신규 파일 3개 존재 확인 (tests/README.md, config/README.md, config/dataset_repos.json)
  - JSON valid, README.md DataCollector+pyproject.toml 섹션 존재 확인
  - preflight_check.sh 5가지 체크 모두 PASS (venv·메모리·Walking RL·Ollama·디스크)
  - 04_dgx_lerobot_diff.md coupled file 갱신 확인 (2026-05-01 TODO-X2 항목 매칭)
  - .gitignore `smolVLA/dgx/outputs/` 패턴 존재 확인 (235행)
  - `svla_so100_pickplace` 데이터셋 캐시 MISS → 단계 6b·8 사용자 동의 필요

- **사용자 검증 필요 사항**:
  1. **smoke_test.sh 1 step 학습 회귀 검증** (단계 6b, 사용자 동의 후 즉시 실행 가능):
     ```bash
     ssh dgx "cd ~/smolvla/dgx && source .arm_finetune/bin/activate && bash scripts/smoke_test.sh"
     ```
     - 기대: 1 step 학습 완료, exit 0, 결과 요약 출력 (소요 시간·GPU 점유)
     - 소요: 최초 실행 (svla_so100_pickplace 다운로드 포함) 5~15분 예상
     - 주의: Walking RL (PID 3977895) 학습 진행 중. preflight 에서 메모리 104 GiB 가용 확인됨. GPU 자원 충돌 가능성 있으면 Walking RL 상태 재확인 후 실행 권장.
  2. **save_dummy_checkpoint.sh 동작 확인** (단계 8, 단계 6b 완료 후 권장):
     ```bash
     ssh dgx "cd ~/smolvla/dgx && source .arm_finetune/bin/activate && bash scripts/save_dummy_checkpoint.sh"
     ```
     - 기대: `~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/` 생성, exit 0
     - 소요: 단계 6b 완료 후 캐시 확보 시 ~30초~2분. 캐시 미확보 시 5~15분.
     - 권장 순서: 단계 6b 먼저 실행 → 캐시 확보 → 단계 8 실행 (총 소요 최소화)

- **prod-test-runner 결과 요약**: deploy_dgx.sh 성공 (6,611 bytes 전송). SSH 실 실행 8개 항목 PASS (신규 파일 3개 존재, JSON valid, README DataCollector+pyproject.toml 섹션 확인, coupled file 갱신 확인, 02 산출물 4개 파일 존재, preflight 5/5 PASS, .gitignore 패턴 확인). 캐시 확인: smolvla_base HIT, svla_so100_pickplace MISS → CLAUDE.md "긴 실행 >5분 + 큰 다운로드 → 동의" 정책 적용. 단계 6b·8 사용자 동의 대기.
- **참고 파일**: `context/todos/X3/03_prod-test.md`
- **전제 조건**: 사용자 동의 후 즉시 실행 가능 (DGX 접속 정상, 메모리·디스크 확인됨). DGX Walking RL 진행 중이므로 GPU 자원 상황 실행 전 재확인 권장.
- **주의**: 02 산출물 4개의 실행 권한 (`x` 비트) 미설정 (`-rw-rw-r--`). `bash scripts/...` 직접 호출로 우회 가능하여 기능 회귀 없음. `chmod +x` 적용 여부는 사용자 판단.
