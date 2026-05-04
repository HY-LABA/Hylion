# TODO-W5 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

본 사이클 (07_e2e_pilot_and_cleanup) 동안 처리·발견된 BACKLOG 항목 일괄 정리 + 신규 항목 누적 + spec 본문 todo 체크박스 마킹.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/specs/BACKLOG.md` | M | 누락 완료 마킹 4건 + 신규 항목 3건 추가 |
| `docs/work_flow/specs/07_e2e_pilot_and_cleanup.md` | M | todo 체크박스 전수 마킹 + 신규 todo 섹션 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (Category A) ✓
- lerobot-reference-usage: 본 TODO 는 문서 마킹 작업 — 코드 구현 없음, 레퍼런스 스킬 미해당
- lerobot-upstream-check: `orin/lerobot/`, `dgx/lerobot/` 미변경 → Coupled File Rule 미해당 ✓

## Step 1 — BACKLOG 전수 점검 결과

### 마킹 확인 (이미 완료 — 다른 task-executor 처리)

| BACKLOG 항목 | 처리 todo | 마킹 상태 |
|---|---|---|
| 02 #7 torchvision wheel 자동 설치 | O3 | 이미 마킹됨 ✓ |
| 02 #8 dpkg 사전 체크 | O3 | 이미 마킹됨 ✓ |
| 03 #14 SSH 비대화형 LD_LIBRARY_PATH | O2 | 이미 마킹됨 ✓ |
| 03 #15 hil_inference 카메라 인덱스 | O4 | 이미 마킹됨 ✓ |
| 03 #16 hil_inference wrist flip | O4 | 이미 마킹됨 ✓ |
| 04 #1 upstream 동기화 entrypoint 절차 | W3 | 이미 마킹됨 ✓ |
| 04 #3 ports.json/cameras.json 정책 | W4 | 이미 마킹됨 ✓ |
| 06 #4 sync_ckpt_dgx_to_orin.sh 검증 | T3 | 이미 마킹됨 ✓ |
| 06 #7 lerobot_upstream_check 색인 | W2 | 이미 마킹됨 ✓ |

### 누락 마킹 → 본 W5 처리

| BACKLOG 항목 | 처리 todo | 조치 | 마킹 내용 |
|---|---|---|---|
| 02 #5 ollama 서비스 중단 절차 | T2 + D2 preflight | 마킹 추가 | `완료 (07 T2 + D2, preflight_check.sh §4 Ollama GPU 점유 체크 + training.py preflight 5단계 흡수, 2026-05-04)` |
| 05 #2 orin/interactive_cli/ flow 0~5 | O1 | 마킹 추가 | `완료 (07 O1, orin/interactive_cli/ flow 0~5 SSH_AUTO PASS + hil_inference PHYS_REQUIRED BACKLOG, 2026-05-04)` |
| 05 #3 dgx/interactive_cli/ 학습 mode 회귀 | D2 | 마킹 갱신 (미완 → 완료) | `완료 (07 D2, dgx/interactive_cli/ 학습 mode 회귀 검증 PASS — preflight 5단계·save_dummy·smoke_test·ckpt 4건 분기·G-4 단발 종료 전 항목 자동 검증 PASS, 2026-05-04)` |
| 06 #6 SKILL.md L111 경로 | W1 Read 확인 | 마킹 갱신 (미완 → 완료) | `완료 (07 W1 Read 확인, 이미 올바른 경로 반영 — 변경 불요, 2026-05-03)` |

### 판단 근거

- **02 #5 (ollama)**: T2 prod-test에서 "ollama GPU 점유 없음 확인" + `preflight_check.sh §4 Ollama GPU 점유 체크` 자동 수행. D2 `training.py` preflight 5단계에 Ollama 체크 통합. 절차 문서화: `dgx/interactive_cli/flows/training.py` preflight 함수 + `dgx/scripts/preflight_check.sh §4` 에 흡수됨.
- **05 #2 (orin/interactive_cli/)**: O1 verification_queue.md 에 "AUTO_LOCAL + SSH_AUTO 전 항목 PASS" 확인. flow 0~5 SSH_AUTO 완료. 05 BACKLOG #2 DOD ("orin/interactive_cli/ flow 0~5 완주") 충족.
- **05 #3 (dgx/interactive_cli/ 학습 mode)**: D2 verification_queue.md 에 "구조 assertion 6건 PASS, ckpt 4건 분기 PASS, G-4 PASS, save_dummy 7파일 확인" 기록. 06 V3 통합 처리 완료.
- **06 #6 (SKILL.md 경로)**: W1 prod-test에서 "L111 기대 경로 완전 일치 확인, 변경 파일 없음" 보고. 이미 올바른 경로가 반영되어 있어 수정 불요.

## Step 2 — 신규 BACKLOG 항목 추가

| # | 항목 | 발견 출처 | 우선순위 |
|---|---|---|---|
| 07 #7 | `run_python.sh` `-u` flag 버그 — venv activate 내 `$LD_LIBRARY_PATH` unset 참조 시 exit 1 | O5 prod-test-runner | 중간 |
| 07 #8 | `deploy_orin.sh --delete` Orin-only 디렉터리 삭제 — devPC 미존재 디렉터리를 Orin 측에서 삭제 | O5 prod-test-runner | 중간 |
| 07 #9 | 07 게이트 4 PHYS_REQUIRED 통합 — D1~D8·O1·O4·O5 PHYS 항목 시연장 이동 시 일괄 검증 | W5 통합 정리 | 중간 (시연장 이동 트리거) |

## Step 3 — PHYS_REQUIRED 통합 정리

verification_queue.md 의 PHYS_REQUIRED 항목들이 07 #9 으로 통합됨:

### DGX 측 PHYS_REQUIRED

| 항목 ID | todo | 내용 |
|---|---|---|
| D-1 ~ D-4 | D1 | SO-ARM·카메라 직결 env_check 6~9 + teleop + record + BACKLOG #14 실물 |
| D3 | D3 | SO-ARM·카메라 직결 check_hardware.sh 5-step 완주 |
| D4-2 | D4 | precheck 옵션(1) 실 포트·카메라 입력 → configs 갱신 |
| D6-1 | D6 | 실 카메라 USB 분리/재연결 walkthrough |
| D7-1~D7-2 | D7 | 방향 반전 confirm + SSH X11 forwarding |
| D8-1~D8-2 | D8 | 메타 device 필터링 확인 + ssh-file 모드 영상 확인 |

### Orin 측 PHYS_REQUIRED

| 항목 ID | todo | 내용 |
|---|---|---|
| O1-1 | O1 | check_hardware.sh first-time/resume SO-ARM 직결 완주 |
| O1-2 | O1 | flow 3 기본값 → hil_inference dry-run + JSON 생성 |
| O1-3 | O1 | hil_inference 50-step SO-ARM live 모드 |
| O4-1 | O4 | `_auto_discover_cameras()` 실 카메라 2대 연결 정상 발견 |

### 주목: 사용자 walkthrough (2026-05-04) 자동 처리 확인

사용자 DGX 직결 walkthrough (2026-05-04) 에서 확인된 내용:
- DGX env_check 항목 1~5 (CUDA, PyTorch, venv, disk, RAM) SSH_AUTO PASS
- env_check 항목 6~9 (SO-ARM, camera) — DGX 직결 환경에서 일부 PASS 확인 (verification_queue.md D2 walkthrough 항목)
- 완전 처리는 시연장 이동 시 SO-ARM·카메라 물리 직결 환경 필요

## Step 4 — spec 본문 todo 체크박스 마킹 결과

### 마킹 완료

| todo | 환경 레벨 | 마킹 | 메모 |
|---|---|---|---|
| P1 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | bash -n + grep 0건 |
| P2 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | grep 잔재 0건, 5줄 제거 |
| P3 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 마일스톤 번호 unique, 07 항목 7건 |
| P4 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 표 행 11개, 07 bold+활성 |
| P5 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 활성 영역 grep 잔재 0건 |
| D1 | SSH_AUTO + PHYS | `[x]` **자동화 완료, Phase 3 대기** | PHYS 4건 → #9 BACKLOG |
| D2 | SSH_AUTO | `[x]` **자동화 완료, Phase 3 대기** | ckpt 4건 분기 PASS |
| D3 | AUTO_LOCAL + SSH | `[x]` **자동화 완료, Phase 3 대기** | 5-step PASS (SO-ARM 미연결) |
| T1 | SSH_AUTO | `[x]` (이미 마킹) | HF 9/9 파일 PASS |
| T2 | SSH_AUTO | `[x]` **자동화 완료, Phase 3 대기** | step 2000 완주, ckpt 3개 확인 |
| T3 | SSH_AUTO | `[x]` (이미 마킹) | 906MB 전송 PASS |
| O1 | SSH_AUTO + PHYS | `[x]` **자동화 완료, Phase 3 대기** | PHYS 3건 → #9 BACKLOG |
| O2 | SSH_AUTO | `[x]` **자동화 완료 (2026-05-03)** | run_python.sh + SSH 실검증 PASS |
| O3 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | bash -n PASS, 경로 시뮬 PASS |
| O4 | SSH_AUTO + PHYS | `[x]` **자동화 완료, Phase 3 대기** | PHYS 1건 → #9 BACKLOG |
| O5 | SSH_AUTO | `[x]` **자동화 완료 (2026-05-04)** | action (1,6) OK, exit 0 |
| W1 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 이미 올바른 경로, 변경 불요 |
| W2 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 색인 7개 파일 등록 |
| W3 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 6단계 절차 추가 |
| W4 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 15_orin_config_policy.md 신규 |
| W5 | AUTO_LOCAL | `[x]` **자동화 완료 (2026-05-03)** | 본 작업 |

### 신규 todo 섹션 추가 (spec 명세 X → 사후 명시)

spec 본문에 "## 사이클 중 추가된 todo" 섹션 신설:
- D1a: DGX + Orin main.sh 회귀 패치 → AUTOMATED_PASS
- D4: precheck 신규 → NEEDS_USER_VERIFICATION (PHYS 2건)
- D5: setup_train_env.sh extras 통합 → NEEDS_USER_VERIFICATION (PHYS 류)
- D6: 카메라 식별 강화 + SSH/직접 실행 분기 → NEEDS_USER_VERIFICATION (PHYS 1건)
- D7: precheck 방향 반전 + find-port 자체 로직 → NEEDS_USER_VERIFICATION (PHYS 2건)
- D8: deepdiff·메타 필터·viewer 통합 → NEEDS_USER_VERIFICATION (PHYS 2건)

## 변경 내용 요약

사이클 07 의 모든 todo 가 완료 또는 NEEDS_USER_VERIFICATION 상태로 전환되었다. BACKLOG.md 에서 4건의 누락 마킹을 추가했다 (02 #5, 05 #2, 05 #3, 06 #6). 새로 발견된 버그 2건 (run_python.sh -u, deploy_orin.sh --delete) 과 게이트 4 PHYS_REQUIRED 통합 항목 1건을 07 섹션에 신규 추가했다.

spec 본문의 모든 원래 todo (P1~P5, D1~D3, T1~T3, O1~O5, W1~W5) 를 체크박스 마킹했고, 사이클 중 자동 추가된 D1a·D4~D8 todo 들을 "사이클 중 추가된 todo" 섹션으로 명시했다.

미처리 PHYS_REQUIRED 항목들은 07 #9 으로 통합 이관되어 시연장 이동 시 일괄 처리 예정이다.

## code-tester 입장에서 검증 권장 사항

- BACKLOG 일관성: 02~07 각 섹션에서 완료 마킹 항목의 "완료 (07 XX, 2026-05-XX)" 패턴 일관성 확인
- spec 체크박스: 모든 `[ ]` → `[x]` 전환 (단 사이클 중 추가된 D4~D8 의 PHYS_REQUIRED 상태는 `[x]` + "Phase 3 대기" 유지)
- 신규 항목 번호 연속성: 07 #7, #8, #9 가 06 #6 이후 연속 번호인지 확인
- PHYS 통합 내용: 07 #9 의 항목 목록이 verification_queue.md 의 PHYS_REQUIRED 항목과 일치하는지 확인
- Step 4 항목: 마킹이 누락된 todo 없는지 spec 본문 전수 grep 확인

---

## Cycle 2 (MINOR R1·R2·R3 처리)

> 작성: 2026-05-03 | task-executor | cycle: 2

### 변경 라인 (spec `07_e2e_pilot_and_cleanup.md`)

| 위치 | 변경 전 (핵심) | 변경 후 (핵심) |
|---|---|---|
| L219 (T2 메모) | "백그라운드 시작 PASS ... checkpoints/{001000,002000,last}/ 완주 확인" | "백그라운드 실행 후 step 2000 완주 확인 PASS (PID 462216 → 정상 종료) ... checkpoints/{001000,002000,last}/ 3개 모두 생성 확인" |
| L241 (T3 메모) | "**자동화 완료, Phase 3 대기 (2026-05-04)**" | "**자동화 완료 (2026-05-04)** ... verdict: AUTOMATED_PASS — 사용자 검증 미요" |
| L407 (D1a 메모) | 상태 메모만 | 끝에 "trigger: ANOMALIES 07-#2 (SMOKE_TEST_GAP ...)" 추가 |
| L411 (D4 메모) | 상태 메모만 | 끝에 "trigger: ANOMALIES 07-#3 (ORCHESTRATOR_GAP ...)" 추가 |
| L415 (D5 메모) | 상태 메모만 | 끝에 "trigger: D4 dispatch 중 setup_train_env.sh extras 누락 발견 (06 사이클 잔류 버그)" 추가 |
| L419 (D6 메모) | 상태 메모만 | 끝에 "trigger: D4 code-tester MINOR ..." 추가 |
| L423 (D7 메모) | 상태 메모만 | 끝에 "trigger: D6 code-tester MINOR ..." 추가 |
| L427 (D8 메모) | 상태 메모만 | 끝에 "trigger: D7 cycle 2 ..." 추가 |

### 직전 피드백 반영

| Recommended 이슈 | 수정 |
|---|---|
| R1 — T3 L241 "Phase 3 대기" 표현 불필요 포함 (AUTOMATED_PASS 인데) | "**자동화 완료 (2026-05-04)**" + "verdict: AUTOMATED_PASS — 사용자 검증 미요" 로 교체. "Phase 3 대기" 문구 제거 |
| R2 — D1a·D4~D8 6건 ANOMALIES 번호·trigger 링크 미명시 | 각 메모 끝에 "trigger: ANOMALIES 07-#N (...)" 또는 "trigger: ..." 추가. D1a·D4 는 ANOMALIES 번호 직접 명시, D5~D8 은 발생 trigger 경위 명시 |
| R3 — T2 L219 메모 "완주 확인" 표현이 verification_queue 상태 (polling 대기) 와 미세 불일치 | "백그라운드 실행 후 step 2000 완주 확인 PASS (PID 462216 → 정상 종료)" 로 정정 — 완주 확인 사실 명확화 |
