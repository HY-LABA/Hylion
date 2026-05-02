# Reflection — 05_interactive_cli (2026-05-02)

> reflection 에이전트 자동 생성. 사용자 승인 후 메인이 갱신 적용.
> 직전 보고서: `docs/storage/workflow_reflections/2026-05-01_04_infra_setup.md`

---

## §1 사이클 요약

| 항목 | 내용 |
|---|---|
| 활성 spec | `05_interactive_cli` |
| 사이클 기간 | 2026-05-01 17:25 ~ 2026-05-02 18:00 (약 24h 35m) |
| 총 todo | 11 (F1·F2·D1·D2·O1·O2·X1·X2·D3·O3·X3) |
| 자동 1-cycle 성공 | 5 (F1·F2·D1·X1·O2) |
| cycle 2 진입 후 성공 | 3 (O1·D2·X2) |
| AUTOMATED_PASS | 0 |
| NEEDS_USER_VERIFICATION | 3 (D3·O3·X3) |
| 실패 | 0 |
| code-tester 1차 verdict 분포 | READY_TO_SHIP 5 / MINOR_REVISIONS 1 (X2) / MAJOR_REVISIONS 2 (O1·D2) |
| code-tester cycle 2 발생율 | 3/8 = 38% (study/task 8건 기준; 04 대비 45% → 38% 소폭 개선) |
| prod-test verdict 분포 | NEEDS_USER_VERIFICATION 3 / AUTOMATED_PASS 0 / FAIL 0 |
| ANOMALY 누적 (본 사이클) | HOOK_BLOCK 1 / CONSTRAINT_AMBIGUITY 1 / DEPLOY_ROLLBACK 1 / USER_OVERRIDE 1 (총 4건) |
| auto_grants 누적 | 17건 (사용자 명시 권한 부여 + 메인 자율 결정) |
| 사용자 개입 (USER_INPUT) | 6회 (권한 우회 선언 1, awaits_user 답변 일괄 1, D3 Phase 3 절차 다수, Python 3.12 결정 2, wrap 결정 1) |
| USER_OVERRIDE | 1회 (옵션 A → 옵션 B fallback) |
| ORCHESTRATOR_GAP | 0건 (04 wrap 갱신 #1·#2 효과 — spec 체크박스 누락 없음) |

### 04 reflection 기준치 대비 지표 변화

| 지표 | 04 기준치 | 05 결과 | 개선 여부 |
|---|---|---|---|
| 2-cycle 발생율 | 5/11 = 45% | 3/8 = 38% | 소폭 개선 |
| AUTOMATED_PASS 비율 | 0/11 = 0% | 0/11 = 0% | 변동 없음 (test 타입 3건 모두 실물 의존) |
| NEEDS_USER_VERIFICATION 비율 | 6/11 = 55% | 3/11 = 27% | 개선 (test 타입만 Phase 3 이관) |
| ORCHESTRATOR_GAP | 2건 | 0건 | 완전 해소 |
| HOOK_BLOCK 빈도 | 1건 (04 #4) | 1건 (05 #1) | 동일 (구조적 미해결) |

### 하네스 원칙 평가 (10점 척도)

| 원칙 | 05 점수 | 04 점수 | 변화 | 비고 |
|---|---|---|---|---|
| 1. CLAUDE.md = 목차 | 7/10 | 7/10 | 동일 | 적절 분량 유지 |
| 2. Progressive Disclosure | 8/10 | 7/10 | +1 | start-spec TaskCreate 게이트 효과 (ORCHESTRATOR_GAP 0건) |
| 3. 에이전트 가독성 (보이지 않는 지식 X) | 5/10 | 5/10 | 동일 | Python 3.12 가정 문서 불일치, 학교 WiFi 차단 endpoint 미문서화 |
| 4. 황금 원칙 + 가비지 컬렉션 | 6/10 | 6/10 | 동일 | reflection 1회만, 백그라운드 없음 |
| 5. 맞춤형 린터 | 5/10 | 4/10 | +1 | bash -n / shellcheck 화이트리스트 효과 (정적 검증 일부 가능) |
| 6. YOLO-style 금지 | 6/10 | 5/10 | +1 | 레퍼런스 인용 의무 강화 (04 wrap 갱신 #4) 효과 — D2 cycle 1 Critical 은 import 이슈 |
| 7. Architecture Fitness | 6/10 | 6/10 | 동일 | lerobot upstream Python 버전 invariant 미명세 지속 |
| 8. 자체 구현 선호 | 7/10 | 7/10 | 동일 | 옵션 B 구조 유지 양호 |
| 9. 최소 차단 병합 게이트 | 6/10 | 6/10 | 동일 | auto_grants 17건 — hook 우회 부담 여전 |
| 10. 사람 입력의 방향성 | 7/10 | 6/10 | +1 | ORCHESTRATOR_GAP 0건으로 gap 채우기 사라짐. 단 권한 우회 선언은 자동화 설계 문제 |

---

## §2 Phase 별 정량 통계

### Phase 1 (사용자 + 메인)

- spec 작성 기간: 2026-05-01 (하루 내 완료)
- 사용자 결정 4건 (Phase 1 에서 확정): 공통 코드 공유 방식 / CLI 구현 언어 / flow 0 진입 형태 / flow 1 장치 선택 의미
- 나머지 3건 (5단계 옵션 / orin flow / dgx flow) 은 Phase 2 awaits_user 로 이관

### Phase 2 (자동화)

- Wave 1 → Wave 2 → Wave 3 → Wave 4(prod) 순차 완료
- Wave 2 내 O1 MAJOR_REVISIONS: hil_inference.py Category B 오분류 + check_hardware.sh --gate-json 잘못된 호출 (2건 Critical) → cycle 2 로 해소
- Wave 3 내 D2 MAJOR_REVISIONS: entry.py 상대 import → main.sh 호출 시 ImportError → cycle 2 로 해소
- Wave 3 내 X2 MINOR_REVISIONS: ruff F401·F541 6건 + CKPT_CASES 케이스 4 누락 → 1회 patch 후 prod-test 진입
- PHASE2_DONE: 2026-05-02 13:30 (11 todo 모두 처리 완료)

### Phase 3 (사용자)

- D3 부분 검증 (flow 0~2 + USB·모터·env_check 7단계): ✅ 완료
- D3 미완 (flow 3~7, Python 3.12 셋업): ❌ BACKLOG #11·#12·#13 이관
- O3: ❌ BACKLOG 이관 (Orin SSH 불통)
- X3: ❌ BACKLOG 이관 (사용자 결정 변경)
- USER_OVERRIDE: 옵션 A (끝까지) → 옵션 B (부분 검증 + wrap) fallback — 학교 WiFi 차단이 트리거

---

## §3 발견 패턴

### 패턴 1 — HOOK_BLOCK 구조적 미해결: auto_grants 17건 누적

**발생**: 1건 ANOMALIES 기록 (연속 신호는 04 #1 SKILL_GAP + 04 #4 HOOK_BLOCK 에서 이어짐)

**구체 상황**:
사이클 시작 직후 (2026-05-01 18:30) 사용자 명시: "이번 작업에서 내가 allow 해야되는거 풀어줄테니까 너가 하고 기록만 따로 파일을 생성해서 기록해줘". 이에 따라 메인이 자율 진행 + `auto_grants_05_interactive_cli.md` 17건 누적. 누적된 17건 중 Category B 영역 (deploy_*.sh / pyproject.toml / setup_env.sh) 은 5건, SSH 작업 (키 배포·read-only 진단) 은 2건, docs/storage 재정렬 (task-executor 위임) 은 2건, 메타 작업 (auto_grants 파일 생성 / ANOMALIES 추가) 은 2건, 사용자 명시 요청 기반 env_check 확장 2건, 기타 6건.

**영향**:
- 04 wrap 에서 `bash -n` / `shellcheck` 화이트리스트 추가만으로 불충분 증명
- auto_grants 17건 중 상당수가 settings.json permissions.allow 에 패턴 없는 작업 (ssh 키 배포, py_compile 실행 등)
- 사이클마다 "사용자 allow 선언" 이 관례화될 위험 — 자동화 설계의 구조적 결함

**현재 룰 검토**:
- settings.json `permissions.allow` 에 `Bash(ssh datacollector:*)` / `Bash(python3 -m py_compile:*)` / `Bash(python3 -c "*:*")` 패턴 없음
- PreToolUse hook 이 메인/워커를 구분하지 않고 차단 (04 #4 구조 미해결)
- CLAUDE.md prod-test-runner 자율성 표에 `ssh datacollector` read-only 검증이 명시 X

**04 reflection 비교**: 04 #4 HOOK_BLOCK (메인 세션 차단 구조) → META 제안 #8 (hook 에 메인 우회 조건 추가) 으로 이관됨. 05 사이클에서 동일 패턴 재현 + 심화 (17건 누적).

**harness 원칙 매핑**: 원칙 9 (최소 차단 병합 게이트) 위반 — 안전한 도구가 차단되어 자동화 처리량 저하. 원칙 10 (사람 입력의 방향성) 부분 위반 — 사람 개입이 "본질적 판단" 이 아닌 "허가 버튼 누르기" 로 반복 소비.

**제안 위치**: 갱신 제안 #1, #2

---

### 패턴 2 — 가정 오류 + 환경 불일치: Python 3.12 우회 후 재정정

**발생**: 1건 ANOMALIES (CONSTRAINT_AMBIGUITY #2) + auto_grants 항목 #8·#10·#17 연계

**구체 상황**:
1. 04 D1 의 폐기된 문서 (`09_datacollector_setup.md §2-1`) 가 "Python 3.12 권장" 명시 → 본 사이클의 `datacollector/setup_env.sh` + `pyproject.toml` 이 Python 3.12 전제로 작성됨
2. 실 datacollector 머신 (Ubuntu 22.04 LTS x86_64) 의 시스템 Python 이 3.10.12 → `pyproject.toml: requires-python >=3.12` 가 lerobot 설치 차단
3. 메인이 "옵션 B 우회" (`>=3.10` 으로 완화) 결정 — auto_grants #10 기록
4. venv 셋업 후 `lerobot import SyntaxError` 발생 → lerobot upstream 5개 파일이 PEP 695 generic syntax (Python 3.12+) 사용 확인
5. 결론: 옵션 B 우회가 잘못된 판단. `>=3.12` 복구 + deadsnakes PPA 방향 — 학교 WiFi 가 launchpad.net 차단하여 BACKLOG #11 이관

**영향**:
- setup_env.sh + pyproject.toml 을 2회 수정 (옵션 B 적용 → 재정정) — Category B 영역 사용자 동의 2회 소비
- DataCollector Python 3.12 셋업 미완으로 D3 flow 3~7 전체 차단
- lerobot upstream 가정 (Python 버전·신규 syntax) 을 사전에 코드 단위로 검증하지 않으면 반복 가능한 패턴

**현재 룰 검토**:
- `lerobot-upstream-check/SKILL.md` 에 Python 버전 invariant (lerobot 이 요구하는 Python 최소 버전, PEP 695 등 신규 syntax 사용 파일) 명시 X
- CLAUDE.md 나 plan.md 어디에도 "새 환경 (datacollector/dgx) 셋업 전 lerobot upstream 의 Python 요구사항 사전 grep 검증" 절차 없음
- `setup_env.sh` Category B 등록만으로는 부족 — 버전 결정 이전에 upstream 코드 단위 검증이 필요

**04 reflection 비교**: 04 패턴 3 (레퍼런스 추측) 과 동류 — "선언만 하고 실제로 확인하지 않음". 04 #4 갱신으로 lerobot-reference-usage 강화됐지만 Python 버전 불일치 패턴은 커버 범위 밖.

**harness 원칙 매핑**: 원칙 3 (에이전트 가독성 — 보이지 않는 지식) 위반 — "datacollector 의 Python 3.12 요구는 lerobot upstream 코드 수준에서 강제됨" 이라는 지식이 어느 문서에도 없었음. 원칙 6 (YOLO-style 금지 — 추측한 모양 위에 빌드 X) 위반 — 시스템 Python 버전과 pyproject.toml 의 불일치를 코드 확인 없이 우회.

**제안 위치**: 갱신 제안 #3

---

### 패턴 3 — DEPLOY_ROLLBACK: 학교 WiFi 외부 endpoint 차단

**발생**: 1건 ANOMALIES (DEPLOY_ROLLBACK #3) + USER_OVERRIDE #4 연계

**구체 상황**:
datacollector Python 3.12 셋업 과정에서 `add-apt-repository ppa:deadsnakes/ppa` 호출 시 launchpad.net API 에 `TimeoutError [Errno 110] Connection timed out` 발생. Ubuntu 22.04 의 `add-apt-repository` 가 launchpadlib 를 통해 launchpad.net 에 메타데이터 쿼리를 보내는데, 학교 WiFi 방화벽이 이를 차단. 동일 패턴이 04 사이클 DGX DHCP 고정 작업에서도 관찰됨 (외부 환경 의존 차단).

**영향**:
- D3 검증이 flow 0~2 에서 멈춤 → BACKLOG #11·#12·#13 이관
- 사용자 옵션 A (끝까지 검증) → 옵션 B (wrap) 결정 변경 (USER_OVERRIDE)
- 학교 WiFi 환경의 차단 endpoint 가 어디에도 문서화 안 됨 → 향후 동일 차단 반복 가능

**현재 룰 검토**:
- 학교 WiFi 환경 차단 endpoint 목록이 어디에도 없음 (`docs/storage/04_devnetwork.md` 에 네트워크 구성은 있지만 차단 정책 없음)
- CLAUDE.md Category C 의 "외부 시스템 호출 → 사용자 동의" 는 deploy 수준에 초점. PPA / pypi 등 패키지 인프라의 네트워크 의존성 분류 정책 없음

**04 reflection 비교**: 04 패턴 없음 (신규 패턴). 04 #2 (DGX DHCP 변경 외부 의존) 와 동류이나 별도 ANOMALIES 미등록.

**harness 원칙 매핑**: 원칙 3 (에이전트 가독성) — "학교 WiFi 에서 차단되는 작업" 이라는 지식이 문서화 안 됨. 원칙 10 (사람 입력의 방향성) — 사람이 "환경 차단 감지" 라는 본질적 판단을 했으나, 사전 문서화가 있었다면 planner 단계에서 자동 분류 가능했을 것.

**제안 위치**: 갱신 제안 #4

---

### 패턴 4 (보조) — USB 2.0 hub 대역폭 + MJPG fourcc 진단 지식

**발생**: auto_grants #13·#14·#15 (ANOMALIES 미등록, 자율 진단·수정)

**구체 상황**:
datacollector 머신에서 외부 USB 디바이스 (카메라 2대 + SO-ARM 2대) 가 단일 USB hub 를 통해 Bus 01 (USB 2.0, 480Mbps) 에 enum됨. lerobot-find-cameras 동시 capture 시 `video4 read_failed` 발생 → MJPG fourcc 강제로 해결 (`record.py cameras_str 에 fourcc: MJPG 추가`). 또한 `env_check.py` 가 range(4) 로 카메라 인덱스 탐색하다가 외부 카메라 (video4) 를 못 찾는 문제 → range(10) + 외부 카메라 우선 로직으로 수정.

**영향**: 이 지식 (USB 2.0 hub 대역폭 한계 + MJPG 해결 + 카메라 인덱스 확장 패턴) 이 어디에도 문서화되지 않으면 orin 또는 다음 사이클에서 동일 진단 반복 가능.

**현재 룰 검토**:
- `docs/storage/02_hardware.md` 에 USB hub 대역폭 관련 명시 없음
- `lerobot-reference-usage/SKILL.md` 나 orin-deploy-procedure 에 카메라 진단 패턴 없음

**harness 원칙 매핑**: 원칙 3 (보이지 않는 지식) — 이 진단 지식은 반드시 storage 에 문서화돼야 함. 원칙 4 (황금 원칙 + 가비지 컬렉션) — 기존 환경 문서 (`02_hardware.md`) 에 USB 토폴로지·대역폭·해결책이 누락된 채 드리프트.

**제안 위치**: 갱신 제안 #5

---

### 패턴 5 (보조) — env_check 7단계 + setup_motors/calibration 통합 패턴

**발생**: auto_grants #14 (사용자 명시 요청 — "모터 ID·calibration 도 env_check 에 포함")

**구체 상황**:
04 G3·G4 에서 dispatch 누락됐던 DataCollector check_hardware 이식이 본 사이클 D2 에서 자연 처리됨. 사용자가 추가로 env_check 에 §6 모터 ID ping + §7 calibration JSON 존재 확인 요청 → 5단계 → 7단계로 확장. 04 BACKLOG #8·#9 자연 처리 완료. 이 7단계 패턴이 datacollector 환경 자체완결성을 높이는 모범 사례가 됨.

**영향**: orin·dgx 의 env_check 에도 동일 §6·§7 통합 가능성 (BACKLOG 후보). 단 orin 은 이미 check_hardware.sh 패턴이 있으므로 대응 업데이트 고려.

**harness 원칙 매핑**: 원칙 10 (사람 입력의 방향성) — 사용자의 "모터 ID·calibration 포함" 요청이 "load-bearing 컨벤션" 수준의 결정. 문서화돼야 재현 가능.

**제안 위치**: 갱신 제안 #5 (hardware.md 에 USB + 모터 진단 패턴 통합)

---

### 패턴 6 — lerobot upstream 옵션 B 적용 범위 미명세

**발생**: ANOMALIES #2 CONSTRAINT_AMBIGUITY 에서 파생 (패턴 2 와 연계)

**구체 상황**:
orin/lerobot/ 이 이미 PEP 695 syntax 5개 파일을 옵션 B 로 backport 한 사실 확인 (orin/lerobot/ 안의 io_utils.py · streaming_dataset.py 등). datacollector 도 동일 패턴 적용 가능 (BACKLOG #11 (c) 옵션). 단 `lerobot-upstream-check/SKILL.md` 에 "어떤 노드가 옵션 B 적용 영역인가" 명시 없음 — orin/lerobot/ 은 명시됐지만 `datacollector/lerobot/` / `dgx/lerobot/` 의 옵션 B 적용 여부·범위 불명.

**현재 룰 검토**:
- `lerobot-upstream-check/SKILL.md` 의 § Coupled File Rules 는 orin/dgx 만 명시. datacollector/lerobot/ 은 언급 없음
- CLAUDE.md Category B 도 `orin/lerobot/`, `dgx/lerobot/` 만 명시. `datacollector/lerobot/` 없음

**harness 원칙 매핑**: 원칙 7 (Architecture Fitness) — orin/dgx/datacollector 의 lerobot/ 각 인스턴스의 역할·invariant 이 명문화되지 않음. 옵션 B 적용 범위가 명확하지 않으면 워커가 매번 CONSTRAINT_AMBIGUITY 누적.

**제안 위치**: 갱신 제안 #6

---

## §4 04 reflection 제안 재발 여부 확인

| 04 제안 | 적용 여부 | 05 재발 |
|---|---|---|
| #1 CLAUDE.md spec 갱신 의무 | 적용 | ORCHESTRATOR_GAP 0건 — 효과 확인 |
| #2 start-spec TaskCreate 게이트 | 적용 | dispatch 누락 0건 — 효과 확인 |
| #3 ANOMALIES ORCHESTRATOR_GAP TYPE | 적용 | 본 사이클 ORCHESTRATOR_GAP 발생 없음 |
| #4 lerobot-reference-usage 인용 의무 | 적용 | D2 cycle 1 Critical 은 import 이슈 (레퍼런스 추측 X) — 효과 확인 |
| #5 orin-deploy-procedure 스크립트 Read | 적용 | O1 cycle 1 Critical 은 Category B 오분류 (추측 아님) — 부분 효과 |
| #6 bash -n / shellcheck 허용 | 적용 | 정적 검증 일부 가능 → code-tester / prod-test 보고서에 py_compile / bash -n 실행 결과 포함됨 — 효과 확인 |
| #7 .gitignore Category B 명확화 | 적용 | 본 사이클 .gitignore 이슈 없음 — 효과 확인 |
| META 제안 #8 hook 메인 우회 | 미적용 | 05 HOOK_BLOCK #1 반복 — 구조적 미해결 지속 |

---

## §5 갱신 제안 (사용자 승인 필요)

| # | 대상 파일 | 변경 내용 | 위험도 | 의존성 | 예상 효과 |
|---|---|---|---|---|---|
| 1 | `.claude/settings.json` permissions.allow | `Bash(ssh datacollector:*)` + `Bash(python3 -m py_compile:*)` + `Bash(python3 -c "*:*")` 추가 | 중간 (`python3 -c` 임의 코드 실행) | 없음 | auto_grants 중 반복 패턴 17건 → settings.json 화이트리스트 흡수. 사이클마다 "allow 선언" 관례 해소 |
| 2 | `.claude/settings.json` PreToolUse hook | hook command 에 "메인 세션 우회 조건" 추가 — `CLAUDE_SESSION_TYPE` 환경 변수 체크 (예: `if [ "$CLAUDE_SESSION_TYPE" = "subagent" ]` 시만 차단, 메인은 통과) | 높음 (hook 정의 자체 변경) | 제안 #1 이후 적용 권장 | 04 META #8 해소. wrap-spec 시 hook matcher 임시 변경 → 복원 흐름 제거 |
| 3 | `.claude/skills/lerobot-upstream-check/SKILL.md` | "Python 버전 사전 검증" 절 추가 — "새 노드 (datacollector 등) 의 lerobot 설치 전 upstream pyproject.toml 의 `requires-python` + PEP 695 등 신규 syntax 사용 파일 수 grep 검증 의무. 시스템 Python 버전 ≥ upstream 요구 충족 미확인 시 setup_env.sh 작성 X" | 낮음 | 없음 | Python 3.12 우회 → 재정정 패턴 재발 방지. 새 노드 셋업 시 사전 검증 강제 |
| 4 | `docs/storage/04_devnetwork.md` | "학교 WiFi 차단 endpoint 알려진 목록" 섹션 신규 추가 — launchpad.net (deadsnakes PPA), 기타 발견된 차단 패턴 기록. 차단 작업 분류 정책: "PPA 추가 / 대용량 다운로드 / GitHub API 등 외부 endpoint 의존 작업은 학교 WiFi 외 네트워크 (집·핫스팟) 로 분류 표시" | 낮음 | 없음 | DEPLOY_ROLLBACK 패턴 사전 감지. planner 가 네트워크 의존 작업 분류 시 참조 가능 |
| 5 | `docs/storage/02_hardware.md` | USB 토폴로지 진단 섹션 추가 — "datacollector USB hub (USB 3.0 hub, but 카메라·SO-ARM 은 USB 2.0) → Bus 01 (480Mbps) 단일 공유. 해결 패턴: OpenCVCameraConfig.fourcc='MJPG' 강제 (압축 ~1/10), range(10) + 외부 카메라 우선 인덱스. orin 동일 패턴 적용 가능성 있음". env_check §6·§7 (모터 ID ping + calibration JSON) 확장 패턴도 동일 섹션 또는 별도 항목으로 기록 | 낮음 | 없음 | USB 2.0 대역폭 진단 지식 문서화 → 다음 사이클 동일 진단 반복 방지 |
| 6 | `.claude/skills/lerobot-upstream-check/SKILL.md` + `CLAUDE.md` Category B | `datacollector/lerobot/` 를 Category B 영역에 추가 + skill 의 Coupled File Rules 에 datacollector 인스턴스 명시 (`05_datacollector_lerobot_diff.md` 신규 생성 의무) | 낮음 | 없음 | 옵션 B 적용 범위 Architecture Fitness 강화. datacollector/lerobot/ 수정 시 추적 의무화 |

---

### 상세 변경 명세

#### 제안 #1 — settings.json permissions.allow 확장

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/settings.json`

현재 allow 목록에서 없는 패턴:
```json
"Bash(ssh datacollector:*)",
"Bash(python3 -m py_compile:*)"
```

`python3 -c "*:*"` 추가 여부는 별도 검토 권장 (임의 코드 실행 위험). 우선 두 가지만 추가.

**사유**: auto_grants 17건 중 `ssh datacollector` read-only 검증 (항목 5·13·16) 과 py_compile 실행 (prod-test 보고서 내 반복 확인) 이 화이트리스트 부재로 매번 사용자 confirm 또는 자율 진행 기록 필요. `ssh orin`·`ssh dgx` 는 이미 있으므로 datacollector 추가가 자연스러운 확장.

---

#### 제안 #2 — settings.json hook 메인 세션 우회 (META 제안 #8)

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/settings.json` hooks PreToolUse

현재 hook command 는 `FILE` 패턴 매칭 후 `exit 2` 로 무조건 차단. 제안:

```bash
# 환경 변수 기반 메인 세션 우회 (예시 — 실제 Claude Code API 에서 제공하는 변수 확인 필요)
if [ "${CLAUDE_AGENT_TYPE:-subagent}" = "subagent" ]; then
  # Category A 영역 차단 (워커만)
  if echo "$FILE" | grep -qE '/docs/reference/|...'; then
    echo '[hook] 차단' >&2; exit 2
  fi
fi
exit 0
```

**주의**: Claude Code 의 환경 변수 API 가 메인/서브에이전트를 구분하는 변수를 제공하는지 확인 필요. 제공하지 않는다면 대안: `SMOLVLA_REFLECTION_MODE=1 bash -c 'cmd'` 와 같이 래퍼 스크립트로 우회. **이 제안은 Claude Code 의 실제 환경 변수 API 확인 후 구체화 필요 — 구현 전 사용자와 합의 권장**.

**위험도 높음** — hook 정의 자체가 Category A 영역이고, 잘못 적용 시 모든 Category A 차단이 무력화될 수 있음.

---

#### 제안 #3 — lerobot-upstream-check Python 버전 사전 검증

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/skills/lerobot-upstream-check/SKILL.md`

`## 변경 시 체크리스트` 다음에 추가할 섹션:

```markdown
## 새 노드 lerobot 설치 전 Python 버전 사전 검증

새 노드 (datacollector, orin, dgx 외 추가 등) 에 lerobot 설치 시 반드시:

1. `docs/reference/lerobot/pyproject.toml` 의 `requires-python` 확인
2. lerobot upstream 코드 내 신규 Python syntax 사용 파일 grep:
   ```bash
   grep -rn "type " docs/reference/lerobot/src/lerobot/ --include="*.py" | head -20
   # PEP 695 generic syntax: "type X = ..." 패턴
   ```
3. 확인된 최소 Python 버전 ≥ 타겟 노드의 시스템 Python 이면 setup_env.sh 작성 가능
4. 미충족 시: deadsnakes PPA (학교 WiFi 차단 가능성 있음 — docs/storage/04_devnetwork.md 참조) 또는 옵션 B backport 중 선택 → 사용자 awaits_user

**위반 패턴 추가**:
- ❌ 타겟 노드의 시스템 Python 버전 확인 없이 pyproject.toml `requires-python` 작성
- ❌ lerobot upstream syntax 확인 없이 Python 버전 우회 (requires-python 완화)
```

---

#### 제안 #4 — docs/storage/04_devnetwork.md 학교 WiFi 차단 섹션 추가

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/04_devnetwork.md`

기존 §8·§9 이후 신규 섹션:

```markdown
## §N 학교 WiFi 환경 차단 endpoint 알려진 목록

> 학교 WiFi 사용 시 차단 확인된 외부 endpoint. 해당 작업은 집·핫스팟·다른 네트워크 에서 수행 권장.

| endpoint | 관련 작업 | 차단 증상 | 발견 사이클 |
|---|---|---|---|
| launchpad.net (PPA API) | `add-apt-repository ppa:deadsnakes/ppa` | TimeoutError [Errno 110] Connection timed out | 05_interactive_cli (2026-05-02) |

**planner 용 분류 기준**: 다음 작업은 네트워크 의존 → awaits_user (학교 WiFi 차단 가능성 명시 후 사용자 확인):
- PPA 추가 (`add-apt-repository`)
- 100MB 이상 다운로드 (PyPI, HF Hub, GitHub archive)
- 외부 Git remote 클론
```

---

#### 제안 #6 — Category B + lerobot-upstream-check datacollector 추가

**CLAUDE.md 변경**:

Category B 목록에 추가:
```
- `datacollector/lerobot/` (upstream 옵션 B — orin/lerobot/ 패턴 동일 적용)
```

**lerobot-upstream-check/SKILL.md 변경**:

`### 3. dgx/lerobot/ 코드 수정 시 (있으면)` 다음에 추가:

```markdown
### 4. `datacollector/lerobot/` 코드 수정 시

`docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` (신규 생성 의무)

형식은 03_orin_lerobot_diff.md 와 동일. backport 한 파일·이유·PEP 695 여부 명시.
```

---

## §6 사용자 승인 결과

| # | 결정 | 적용 시점 | 비고 |
|---|---|---|---|
| 1 | **부분 적용** | 2026-05-02 wrap | settings.json permissions.allow 16건 추가 (ssh datacollector·python3 -m py_compile·deploy_*·sync_*·chmod·touch·awk·sed·pip·rm /tmp/). settings.local.json 누적 33+ 항목 정리는 보류 (다음 사이클 후보) |
| 2 | **보류 (META #9)** | — | hook 메인 세션 우회 조건 — Claude Code hook API 의 메인/워커 구분 변수 미확인. 차기 사이클에서 정식 검토. 사용자 의도: "wrap-spec 시점 skill·settings.json 갱신은 hook matcher 임시 비활성화 흐름 OK, 사이클 도중 prompt 빈도가 진짜 문제" |
| 3 | **적용** | 2026-05-02 wrap | `lerobot-upstream-check/SKILL.md` 에 "Python 버전 사전 grep 검증 (옵션 B 우회 시 필수)" 절 신규 추가 (line 20~). PEP 695·match·type alias 등 syntax-level 사전 grep 절차 명시 + 본 사이클 학습 신호 (옵션 B 잘못된 우회) 기록 |
| 4 | **적용** | 2026-05-02 wrap | `04_devnetwork.md` §11 "학교 WiFi 차단 endpoint 목록" 신규 추가. launchpad.net 차단 사례 + pypi·HF·GitHub·astral.sh·Ubuntu mirror 정상 동작 분류 + 차단 발견 시 대응 절차 + 본 사이클 학습 신호 기록 |
| 5 | **적용** | 2026-05-02 wrap | `02_hardware.md` §5-1·5-2·5-3 신규 추가. USB tree 토폴로지 + USB 2.0 hub 대역폭 한계 분석 + MJPG fourcc 강제 패턴 + env_check 7단계 통합 (사용자 요청 §6·§7 — 모터 ID·calibration JSON) |
| 6 | **적용** | 2026-05-02 wrap | (a) `CLAUDE.md` Category B 영역에 `datacollector/lerobot/` 추가 (line 146). (b) `CLAUDE.md` Coupled File Rules 에 `05_datacollector_lerobot_diff.md` 의무 추가 (line 202·204). (c) `lerobot-upstream-check/SKILL.md` line 8·12·108·126 datacollector/lerobot/ 영역 + backport 절차 추가. BACKLOG #11 (c) 옵션 진행 시 활성화 |

---

## §7 관련 ANOMALIES.md 처리

본 보고서로 분석된 anomaly 항목들 (05_interactive_cli 섹션):

| ANOMALIES 항목 | 관련 제안 | wrap 후 처리 상태 |
|---|---|---|
| #1 HOOK_BLOCK — auto_grants 17건 누적 | 제안 #1·#2 | **갱신 부분 적용** — 제안 #1 (settings.json 16건 추가) 적용 / 제안 #2 (메인 세션 우회 hook) META #9 보류 |
| #2 CONSTRAINT_AMBIGUITY — Python 3.12 우회 잘못된 판단 | 제안 #3 | **갱신 적용** — `lerobot-upstream-check/SKILL.md` Python 버전 grep 검증 절 신규 + datacollector/lerobot/ 옵션 B 영역 추가. CLAUDE.md Category B + Coupled File Rules 동시 갱신. BACKLOG #11 다음 사이클 처리 유지 |
| #3 DEPLOY_ROLLBACK — launchpad.net timeout | 제안 #4 | **갱신 적용** — `04_devnetwork.md §11` 신규 (학교 WiFi 차단 endpoint 목록) |
| #4 USER_OVERRIDE — 옵션 A → B fallback | 별도 제안 없음 (정책 문서화 수준) | **갱신 보류** — 재발 패턴이 명확해지면 META #9 와 함께 차기 사이클 정책 정리 (사용자 결정 변경 가능 명시 + fallback 패턴 표준화) |

---

## §8 다음 사이클 진입 권고

### 즉시 처리 필요 (BACKLOG 높음)

| BACKLOG | 내용 | 추천 처리 방식 |
|---|---|---|
| 04 #11 | DataCollector Python 3.12 셋업 — deadsnakes PPA 또는 옵션 B backport | 다른 네트워크에서 시도. 06 진입 전 필수 (D3 flow 3~7 차단) |
| 04 #12 | DataCollector lerobot-calibrate + flow 3~7 완주 | #11 해소 후 진입 |
| 03 #1 | 카메라 키 매핑 (smolvla_base camera1/2/3 vs top/wrist) | 06_leftarmVLA 데이터 수집 전 결정 필수 |

### 차기 spec 권고

06_leftarmVLA 진입 전 조건:
1. DataCollector Python 3.12 셋업 완료 (BACKLOG 04 #11)
2. 실물 teleoperation 한 번이라도 완주 (D3 flow 3~7)
3. 카메라 키 매핑 결정 (BACKLOG 03 #1)

위 3건이 충족되지 않으면 "06_datacollector_validation" 단기 spec 을 먼저 작성 후 06_leftarmVLA 진입 권장.

### 하네스 차기 개선 권고 (제안 외)

- `docs/QUALITY_SCORE.md` 신설 검토 (harness-engineering-principles § 보강 후보 #2) — 사이클별 2-cycle 발생율·AUTOMATED_PASS 비율·ANOMALIES 빈도 추적 테이블
- env_check 7단계 패턴이 datacollector 에서 검증됨 → orin·dgx 에도 §6·§7 동일 통합 가능성 (다음 사이클 spec 에 포함 권고)
