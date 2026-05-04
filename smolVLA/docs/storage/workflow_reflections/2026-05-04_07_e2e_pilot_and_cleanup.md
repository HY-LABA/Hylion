# Reflection — 07_e2e_pilot_and_cleanup (2026-05-04)

> reflection 에이전트 자동 생성. 사용자 승인 후 메인이 갱신 적용.
> 직전 보고서: `docs/storage/workflow_reflections/2026-05-03_06_dgx_absorbs_datacollector.md`

---

## §1 사이클 요약

| 항목 | 내용 |
|---|---|
| 활성 spec | `07_e2e_pilot_and_cleanup` |
| 사이클 기간 | 2026-05-03 ~ 2026-05-04 |
| 총 todo | 36건 (spec 본문 21건 + 사이클 중 추가 D1a·D4~D13 = 11건 신규, W5 실질 완결 포함 총 계산 기준) |
| 자동 종결 (AUTOMATED_PASS) | P1~P5·W1~W5·T1·T3·O3·O5·D1a = 14건 |
| 사용자 검증 통과 (게이트) | D1~D3 (게이트 1), T2 (게이트 2), D4·D6~D13 (게이트 4) = 14건 |
| 사용자 무시/BACKLOG 이관 | O1·O4 (게이트 3 PHYS_REQUIRED → BACKLOG 07 #9) = 2건 |
| code-tester 1차 READY 비율 | O3 MAJOR 1건 외 전건 READY 또는 MINOR — 추정 약 85% |
| code-tester 2-cycle 발생 | O3 (MAJOR → cycle 2 수정), W5 (MINOR → cycle 2 수정) 2건 |
| prod-test AUTOMATED_PASS | 14건 (P 그룹·W 그룹·T1·T3·O3·O5·D1a) |
| prod-test NEEDS_USER_VERIFICATION | D1·D2·D3·D4·D5·D6·D7·D8·D9·D10·D11·D12·D13·T2·O1·O4 = 16건 |
| ANOMALY 누적 (본 사이클) | #1 PROMPT_FATIGUE_RESOLVED, #2 SMOKE_TEST_GAP, #3 ORCHESTRATOR_GAP, #4 USER_OVERRIDE |
| 사용자 개입 (USER_INPUT) | 12회 이상 (walkthrough 트리거 포함 — 매우 높음) |
| USER_OVERRIDE | 1회 (O1·O4 BACKLOG 이관) |
| ad-hoc 변경 | 2건 (.env 인프라 + main.sh 자동 source — 07 BACKLOG #17) |
| e2e 종착점 | record 10 epi 16820 frames → HF Hub push 491MB → smoke train 1 step PASS (loss 0.546, GPU 94%) → main.sh .env 자동 source 검증 PASS |

### 사이클 간 지표 비교

| 지표 | 05 | 06 | 07 | 비고 |
|---|---|---|---|---|
| 2-cycle 발생율 | 38% | 10% | ~6% (2/33) | 개선 추세 지속 |
| ORCHESTRATOR_GAP | 0건 | 0건 | 1건 (D4) | Phase 1 합의 갭에서 기인 |
| USER_OVERRIDE | 1건 | 1건 | 1건 | 환경 의존 PHYS fallback 패턴 지속 |
| walkthrough trigger todo | 0건 | 0건 | 11건 | 본 사이클 특이 패턴 |
| ad-hoc 변경 | 미기록 | 미기록 | 2건 | 신규 패턴 |
| AUTOMATED_PASS (prod 기준) | 0건 | 0건 | 14건 | 06 reflection #4 환경 레벨 분류 효과 첫 입증 |

---

## §2 발견 패턴

### 패턴 1 — 사용자 walkthrough 가 todo 폭증 트리거 (11건)

**발생**: D1a (회귀 2건) + D4 (precheck 미명세) + D5 (pyserial 누락) + D6 (카메라 식별 강화) + D7 (방향 반전) + D8 (deepdiff·메타 필터) + D9 (calibrate ports.json 로드) + D10 (G1·G2·G3 분기 안내) + D11 (Ctrl+C catch) + D12 (record cameras.json 로드) + D13 (streamable fallback + deploy exclude) = 11건

**영향**: Phase 2 예상 종료가 대폭 연장. 당초 Wave 2~4 각 3~5건에서 D 그룹이 11건 순증. 게이트 구조 외에 walkthrough 트리거 → dispatch → prod-test-runner → walkthrough 재시도 루프가 반복됐다.

**anomaly 출처**: SMOKE_TEST_GAP (07 #2) — D1 정적 검증 PASS 직후 사용자 SSH 직접 실행에서 회귀 2건 발견. ORCHESTRATOR_GAP (07 #3) — spec D 그룹 명세에 teleop 진입 직전 사전 점검 단계 누락.

**현재 룰 검토**:
- prod-test-runner.md §4 비대화형 검증에 "interactive entry runtime smoke (echo 입력 + timeout)" 절차 명시 없음. py_compile·ruff 통과 후 바로 NEEDS_USER_VERIFICATION 발급이 가능 — 단 runtime smoke (`echo "1" | timeout 10 bash main.sh`) 를 먼저 수행하면 import-time 에러를 자동 감지 가능.
- planner.md §6 Phase 3 검증 큐 작성 시 "menu walkthrough (echo 입력 시퀀스로 메뉴 분기 검증)" 를 SSH_AUTO 항목으로 분류 지침 없음.
- CLAUDE.md Phase 1 절에 "사용자 시점 main.sh 흐름 시뮬레이션" 의무 없음.

**06 reflection 비교**: 06 패턴 1 (환경 의존 fallback) 과 다른 축. 본 사이클에서는 사용자의 walkthrough 가 spec Phase 1 시점에 미명세된 UX 갭을 반복 발견하는 구조 자체가 문제다. 06 reflection #4 (환경 레벨 분류) 의 "SSH_AUTO walkthrough" 를 prod-test-runner 가 더 적극 수행했다면 사용자 walkthrough 이전에 일부 갭 자동 발견 가능했을 것.

**harness 원칙 매핑**: 원칙 5 (맞춤형 린터) — "interactive CLI entry 의 runtime smoke" 는 결정적 룰로 변환 가능한 패턴 (py_compile 이 정적 오류를 잡듯이, runtime smoke 가 import-time·실행-time 오류를 잡음). 원칙 3 (에이전트 가독성) — "CLI entry 는 정적 검증만으론 불충분" 이라는 지식이 prod-test-runner skill 에 명시 안 됨.

**제안 위치**: 갱신 제안 #1, #2

---

### 패턴 2 — ad-hoc 변경의 spec 외부 즉시 적용 (BACKLOG 07 #17)

**발생**: 1패턴 2건 — (a) 프로젝트 루트 `.env` + `.gitignore` 패턴 + `.env.example` 신규, (b) `dgx/interactive_cli/main.sh` + `orin/interactive_cli/main.sh` 1.5 블록 추가 (PROJECT_ROOT/.env 자동 source)

**영향**: spec 본문에 없는 변경 2건이 walkthrough 도중 즉석 적용됨. 코드 변경 자체는 안전하고 유용했으나, 해당 변경에 대한 code-test·prod-test 검증이 정식 흐름 없이 진행됐다. Phase 2 자동화 흐름 외부에서 발생하므로 BACKLOG·ANOMALIES 추적이 비공식적.

**anomaly 출처**: BACKLOG 07 #17 (reflection 후보 등록).

**현재 룰 검토**:
- CLAUDE.md Phase 2 절에 "spec 본문에 없는 변경은 즉시 적용 불가 — 반드시 todo 신규 등록 후 dispatch" 정책 없음.
- 워크플로우 정책은 "모든 변경은 todo → task-executor → code-tester → prod-test-runner 흐름" 을 함의하지만 명시적 금지 없음.
- walkthrough 상황에서 사용자가 즉석 변경을 요청하면 현재 정책상 처리 방법이 불명.

**05 reflection 비교**: 05 이후 처음 등장하는 패턴. 사용자와 협력적 walkthrough 가 활발해지면서 발생 빈도가 늘어날 가능성이 높다.

**harness 원칙 매핑**: 원칙 9 (최소 차단 병합 게이트) — ad-hoc 변경이 정식 검증 게이트를 우회하면 "수정 비용 저렴" 원칙이 오히려 품질 리스크로 전환. 원칙 4 (황금 원칙 + 가비지 컬렉션) — 즉시 적용된 변경이 BACKLOG #17 로만 추적되면 검증 이력이 남지 않아 기술 부채 누적.

**제안 위치**: 갱신 제안 #3

---

### 패턴 3 — lerobot extras 의존성 체인 누락 반복 (3회)

**발생**: D4 walkthrough (pyserial ImportError) → D8 walkthrough (deepdiff ImportError) → D5 통합 후에도 현 venv 에서 deepdiff 재발 — 총 3회, 동일 패턴

**영향**: 각 발생마다 즉석 pip install + 신규 todo dispatch (D5, D8 일부) 로 흐름이 끊김. extras transitive 의존성이 예상과 다르게 설치 상태 미확인으로 누적되는 구조.

**anomaly 출처**: BACKLOG 07 #6 (lerobot extras 누락 패턴 반복 반영).

**현재 룰 검토**:
- `setup_train_env.sh` 에 "critical extras import 체크" 블록 없음. 현재 설치 후 import 검증은 사용자 walkthrough 시점에 처음 발견.
- prod-test-runner 가 DGX SSH 배포 후 수행하는 smoke 검증 목록에 "critical CLI tool import (lerobot-find-port, lerobot-find-cameras)" 없음.
- spec Phase 1 에서 "어떤 lerobot extras 가 필요한가" 를 사전 grep 해서 확인하는 절차 없음.

**06 reflection 비교**: 해당 없음 (신규 패턴). 단 05 ANOMALIES #2 (Python 3.12 가정 오류) 와 유사한 "의존성 가정이 실 환경에서 반증" 카테고리.

**harness 원칙 매핑**: 원칙 5 (맞춤형 린터) — `lerobot-find-port`·`lerobot-find-cameras`·`lerobot-record` 등 CLI 진입점 import 를 결정적 체크로 자동화 가능. 원칙 6 (YOLO-style 금지) — "extras 설치 완료 = CLI 사용 가능" 이라는 가정 위에 빌드한 것이 YOLO 패턴의 의존성 버전.

**제안 위치**: 갱신 제안 #4

---

### 패턴 4 — deny-only settings.json 모델의 첫 사이클 평가

**발생**: 07 사이클 전체 (ANOMALIES 07 #1 PROMPT_FATIGUE_RESOLVED)

**영향**: Bash 광역 allow + deny 64건 전환 후 본 사이클에서 사고 사례 없음 (관찰됨). 동시에 deny 패턴 중 7건이 shell metachar 비호환으로 발견·패치됨 (71→64). 정확한 deny 패턴 범위 내에서 Bash 명령을 python3 으로 우회 시도해도 Category A hook 이 Write/Edit 만 차단하므로 Category A 내용을 Bash 로 수정하는 시나리오는 사고 미발생 (의도된 trade-off 수용 범위).

**현재 룰 검토**:
- BACKLOG 07 #1: allow 의 redundant `Bash(...)` 패턴 ~80건 아직 정리 미완.
- BACKLOG 07 #2: PreToolUse hook 에 Bash matcher 추가 (shell metachar 포함 패턴 차단) 미처리.
- settings.json `_comment` 에 deny-only 모델 전환 사유·날짜 기록됨 — 추적 가능 (양호).
- CLAUDE.md Memory 에 "deny-only model" 정책 결정 기록됨 (양호).

**05 reflection 비교**: 05 ANOMALIES #1 (HOOK_BLOCK — Bash 차단 과도) 의 해소 사이클. 05 wrap 시 settings.json 16건 추가 → 06 auto_grants 0건 효과 → 07 deny-only 전환으로 근본 해소. 하네스 발전 추세의 긍정적 이정표.

**harness 원칙 매핑**: 원칙 9 (최소 차단 병합 게이트) — "수정 비용 저렴, 대기 시간 비쌈" 원칙에 따라 prompt 마찰 제거는 처리량 향상에 기여. 단 deny 패턴 syntax 비호환 발견은 원칙 5 (린터) 관점에서 "deny 패턴 자체의 사전 syntax 검증" 필요성을 보여줌.

**제안 위치**: 갱신 제안 #5

---

### 패턴 5 — deploy 스크립트가 사용자 환경 파일을 덮어쓰는 반복 패턴

**발생**: BACKLOG 07 #8 (deploy_orin.sh --delete 가 Orin checkpoints 삭제) + BACKLOG 07 #15 (deploy_dgx.sh 가 configs/*.json 덮어씀) — 동일 사이클에서 2건 동시 발견. D13 Part B 로 configs 덮어쓰기는 해소됐으나 --delete 건은 미처리.

**영향**: O5 prod-test 에서 T3 ckpt 가 삭제되어 sync_ckpt_dgx_to_orin.sh 재실행으로 복구 필요했다. D12 walkthrough 에서 cameras.json null 이 deploy 로 덮어씌워져 record 진입 차단.

**현재 룰 검토**:
- deploy_orin.sh, deploy_dgx.sh 에 "사용자 환경 의존 파일 (config, checkpoint)" 보호 정책 없음.
- orin-deploy-procedure skill 에 rsync `--exclude` 패턴 지침 없음.
- BACKLOG 04 #3 (orin/config 정책) → 07 W4 에서 정책 문서 신규 작성됐으나 deploy 스크립트 exclude 반영까지는 안 됨.

**harness 원칙 매핑**: 원칙 7 (Architecture Fitness) — "deploy 스크립트는 사용자 환경 파일을 덮어쓰지 않는다" 는 invariant 이나 현재 자동 검증 없음. 원칙 5 (맞춤형 린터) — deploy 스크립트 실행 시 "exclude 패턴 유무" 를 사전 정적 검사로 자동화 가능.

**제안 위치**: 갱신 제안 #6

---

## §3 하네스 원칙 평가

### 10 원칙 매핑 (10점 척도)

| 원칙 | 07 점수 | 06 점수 | 변화 | 본 사이클 근거 |
|---|---|---|---|---|
| 1. CLAUDE.md = 목차 | 7/10 | 7/10 | 동일 | 분량 적정. 단 ad-hoc 변경 정책 미명시 |
| 2. Progressive Disclosure | 8/10 | 8/10 | 동일 | 환경 레벨 분류 (06 #4) 가 본 사이클에서 처음 적용 — 효과 입증 |
| 3. 에이전트 가독성 | 6/10 | 6/10 | 동일 | prod-test-runner "runtime smoke" 지식 미명시. Phase 1 흐름 시뮬레이션 미명시 |
| 4. 황금 원칙 + 가비지 컬렉션 | 7/10 | 7/10 | 동일 | 2-cycle 발생율 ~6% 양호. ad-hoc 변경 검증 이력 누락은 기술 부채 |
| 5. 맞춤형 린터 | 6/10 | 6/10 | 동일 | lerobot extras CLI import 체크 미자동화. runtime smoke 부재 |
| 6. YOLO-style 금지 | 7/10 | 7/10 | 동일 | extras 의존성 가정 3회 반증. deploy exclude 가정 2건 반증 |
| 7. Architecture Fitness | 6/10 | 6/10 | 동일 | deploy invariant (사용자 환경 파일 보호) 자동 검증 없음 |
| 8. 자체 구현 선호 | 7/10 | 7/10 | 동일 | lerobot wrapper 패턴 적절 유지 |
| 9. 최소 차단 병합 게이트 | 7/10 | 7/10 | 동일 | deny-only 전환으로 prompt 마찰 해소. walkthrough todo 폭증이 처리량 저하 |
| 10. 사람 입력의 방향성 | 7/10 | 7/10 | 동일 | walkthrough 에서 사용자가 UX 갭 발견 = 정당한 사람 개입. 단 spec Phase 1 에서 사전 발견 가능했던 갭이 포함됨 |

**평균**: 6.8/10 (06 동일 — 본 사이클은 "사이클 목표 완주 + 첫 e2e 입증" 의미가 크나 하네스 자체 발전은 05→06 대비 미미)

---

## §4 갱신 제안 (사용자 승인 필요)

| # | 대상 파일 | 변경 내용 요약 | 이유 (패턴) | 위험도 |
|---|---|---|---|---|
| 1 | `.claude/agents/prod-test-runner.md` | §4 비대화형 검증에 "interactive CLI entry runtime smoke" 절차 추가 — `echo "N" \| timeout 10 bash main.sh` 패턴, deploy 직후 의무 실행 항목으로 명시 | 패턴 1 (SMOKE_TEST_GAP — D1 정적 PASS 후 runtime 회귀 발견) | 낮음 |
| 2 | `.claude/agents/planner.md` | §6 Phase 3 검증 큐 후보 작성 지침에 "CLI entry 스크립트는 SSH_AUTO menu walkthrough (echo 입력 시퀀스) 를 반드시 포함" 항목 추가 | 패턴 1 (walkthrough 트리거 todo 11건 — spec 작성 시 walkthrough 시나리오 미명세) | 낮음 |
| 3 | `CLAUDE.md` Phase 2 절 | "spec 본문에 없는 변경 (ad-hoc) 처리 정책" 신규 절 추가 — (a) 즉시 필요한 즉석 변경 (pip install 등): 즉시 + BACKLOG 메모, (b) 코드 변경: todo 신규 등록 → code-test → prod-test 정식 흐름 의무 | 패턴 2 (ad-hoc 변경 처리 정책 미명문화) | 낮음 |
| 4 | `.claude/agents/prod-test-runner.md` | §4 비대화형 검증에 "lerobot CLI 진입점 import 체크 의무" 추가 — DGX SSH 배포 후 `lerobot-find-port`, `lerobot-find-cameras`, `lerobot-record` 등 사용 예정 CLI 의 import smoke 실행 항목 명시 | 패턴 3 (lerobot extras 누락 3회 반복 — import 체크 자동화 부재) | 낮음 |
| 5 | `.claude/settings.json` | `_comment` 의 "wrap 시 정리" BACKLOG 언급대로 redundant `Bash(...)` 패턴 ~80건 + datacollector 잔재 5건 일괄 정리. deny 64 유지. 가독성 향상 + 롤백 편의 | 패턴 4 (07 BACKLOG #1 — deny-only 안정 운영 확인 후 정리 트리거) | 낮음 |
| 6 | `.claude/skills/orin-deploy-procedure/SKILL.md` | "사용자 환경 의존 파일 rsync exclude 원칙" 절 추가 — `orin/checkpoints/`, `orin/config/*.json`, `dgx/interactive_cli/configs/*.json` 는 deploy 스크립트 rsync 에서 exclude 의무 패턴 명시 | 패턴 5 (deploy 스크립트 사용자 환경 파일 덮어쓰기 반복) | 낮음 |

### 상세 변경 명세

---

#### 제안 #1 — prod-test-runner.md: interactive CLI entry runtime smoke 추가

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/prod-test-runner.md` (Category A — 메인 수동 적용)

**도입 사유**: D1 prod-test-runner 가 py_compile·ruff·bash -n 통과 후 NEEDS_USER_VERIFICATION 발급 → 사용자 SSH 직접 실행에서 runtime 회귀 2건 발견 (07 ANOMALIES #2 SMOKE_TEST_GAP). import-time 에러는 `echo "N" | timeout 10 bash main.sh` 패턴으로 자동 감지 가능하다.

**변경 내용**:

prod-test-runner.md §4 "비대화형 검증" 의 기존 목록 하단에 추가:

```markdown
- interactive CLI entry (`main.sh` 류) 가 포함된 경우:
  - `echo "3" | timeout 10 bash ~/smolvla/dgx/interactive_cli/main.sh 2>&1 | head -20` 패턴으로 menu 진입·종료 smoke 실행
  - 기대: ModuleNotFoundError / ImportError 미발생, 메뉴 출력 정상 확인
  - 목적: import-time 에러를 정적 검증 (py_compile) 보다 더 가까운 환경에서 사전 탐지
  - ※ 대화형 입력 필요 부분은 `echo` 입력 + `timeout` 으로 처리. 응답 없으면 `SIGTERM` 정상.
```

---

#### 제안 #2 — planner.md: CLI entry walkthrough 시나리오 검증 큐 지침

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/planner.md` (Category A — 메인 수동 적용)

**도입 사유**: 본 사이클에서 D 그룹 검증 큐에 "menu walkthrough (echo 입력 시퀀스로 모든 메뉴 분기 검증)" 가 SSH_AUTO 항목으로 명시되지 않아 사용자 walkthrough 에서 갭이 발견됐다. planner 가 Phase 3 검증 큐 후보 작성 시 이 항목을 명시하면 prod-test-runner 가 사전에 수행 가능하다.

**변경 내용**:

planner.md §6 "Phase 3 검증 큐 후보" 작성 지침에 추가:

```markdown
- CLI entry 스크립트 (`main.sh`, interactive_cli/) 가 포함된 todo 는 SSH_AUTO 항목으로 반드시:
  - menu walkthrough 시나리오 (echo 입력 시퀀스 + timeout) 를 최소 1건 이상 포함
  - 각 주요 분기 (수집/학습/종료 등) 에 대한 smoke 입력 시퀀스 명시
  - 예: `echo -e "2\n1\n3" | timeout 30 bash main.sh 2>&1` — 메뉴 2 선택 → 수집 → 종료 흐름
```

---

#### 제안 #3 — CLAUDE.md: walkthrough ad-hoc 변경 처리 정책

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/CLAUDE.md` Phase 2 절

**도입 사유**: 07 사이클에서 walkthrough 중 사용자 즉석 요청으로 spec 본문에 없는 변경 2건이 정식 검증 없이 적용됐다 (07 BACKLOG #17). 이 패턴의 처리 정책이 CLAUDE.md 에 없어 사후 BACKLOG 등록만 됨.

**변경 내용**:

CLAUDE.md Phase 2 절 또는 `/wrap-spec` 절 하단에 신규 소절 추가:

```markdown
#### walkthrough 중 ad-hoc 변경 처리 정책

사용자 walkthrough 도중 spec 본문에 없는 즉석 변경 요청이 발생할 수 있음:

| 유형 | 정책 |
|---|---|
| **환경 즉석 조치** (pip install·즉석 export 등, 코드 미변경) | 즉시 실행 + BACKLOG 메모 (영구 fix 는 신규 todo) |
| **코드 변경** (소규모, 1~10줄, 회귀 위험 낮음) | todo 신규 등록 → task-executor dispatch → code-test → prod-test 정식 흐름 의무 |
| **코드 변경** (중규모 이상, 또는 Category B 해당) | 반드시 todo 등록 후 정식 흐름. 즉시 적용 X |

walkthrough ad-hoc 변경이 발생하면 orchestrator 가 BACKLOG 에 `[#N] ad-hoc: <내용>` 형식으로 즉시 등록 (나중에 누락 방지).
```

---

#### 제안 #4 — prod-test-runner.md: lerobot CLI 진입점 import 체크 의무

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/prod-test-runner.md` (Category A — 메인 수동 적용)

**도입 사유**: 본 사이클에서 pyserial·deepdiff ImportError 가 사용자 walkthrough 에서 3회 발견됐다. DGX SSH 배포 후 prod-test-runner 가 `python3 -c "from lerobot.scripts.find_motors import..."` 류의 import smoke 를 수행했다면 일부를 자동 감지 가능했다.

**변경 내용**:

prod-test-runner.md §4 비대화형 검증 목록에 추가:

```markdown
- DGX 배포 후 lerobot CLI 진입점 import 체크 (해당 todo 에서 사용 예정 CLI 에 한정):
  - `ssh dgx "source ~/smolvla/dgx/.arm_finetune/bin/activate && python3 -c 'import subprocess; subprocess.run([\"lerobot-find-port\", \"--help\"], capture_output=True)'"` 패턴
  - ImportError exit code 비정상 시 BACKLOG 후보 등록 + 검증 결과에 명시
  - 목적: extras transitive 의존성 누락을 사용자 walkthrough 이전에 탐지
```

---

#### 제안 #5 — settings.json: redundant 패턴 정리

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/settings.json`

**도입 사유**: deny-only 모델 전환 (07 Wave 1) 이후 `permissions.allow` 의 `Bash(ls:*)`, `Bash(cat:*)` 등 약 80건의 기존 개별 패턴이 redundant 상태 (상위 `"Bash"` 광역 토큰으로 이미 허용됨). BACKLOG 07 #1 의 "안정 운영 확인 후 정리" 조건이 충족됐다.

**변경 내용**:

`permissions.allow` 배열에서 `"Bash"` 광역 토큰 이후의 모든 `"Bash(...)"`  패턴 제거. 단 `"Read"`, `"Write"`, `"Edit"`, `"Grep"`, `"Glob"` 등 비-Bash 도구 항목은 유지. deny 배열은 변경 X.

결과: allow 배열이 `["Bash", "Read", "Grep", "Glob", "ToolSearch", "Write", "Edit", "WebSearch", "WebFetch"]` 수준으로 간결해짐.

**위험도 낮음**: Bash 광역 허용이 이미 활성화돼 있으므로 개별 패턴 제거는 실질 권한 변화 없음. `_comment` 의 관련 메모도 갱신.

---

#### 제안 #6 — orin-deploy-procedure SKILL.md: 사용자 환경 파일 rsync exclude 원칙

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/skills/orin-deploy-procedure/SKILL.md` (Category A — 메인 수동 적용)

**도입 사유**: 07 사이클에서 deploy 스크립트가 사용자 환경 의존 파일 (checkpoints, configs/*.json) 을 덮어쓰거나 삭제하는 사고가 2건 발생했다 (BACKLOG 07 #8·#15). D13 에서 configs exclude 는 수정됐으나 checkpoints exclude 는 미처리. 동일 패턴의 재발 방지를 위해 SKILL 에 원칙 명시.

**변경 내용**:

orin-deploy-procedure SKILL.md (파일 내 적절한 위치에) 다음 절 추가:

```markdown
## rsync 배포 시 사용자 환경 파일 보호 원칙

배포 스크립트 (`deploy_orin.sh`, `deploy_dgx.sh`) 에서 rsync 실행 시 다음 파일은 반드시 exclude:

| 경로 | 이유 |
|---|---|
| `orin/checkpoints/` | Orin 에서 sync_ckpt 로 동기화된 ckpt. devPC 미존재 → --delete 로 삭제 가능 |
| `orin/config/*.json` | 시연장 포트·카메라 설정. 사용자 환경마다 다름 |
| `dgx/interactive_cli/configs/*.json` | DGX 포트·카메라 설정. deploy 마다 placeholder 로 덮어쓰면 안 됨 |

exclude 추가 방법:
```bash
rsync ... --exclude 'checkpoints/' --exclude 'config/*.json' ...
```

신규 deploy 스크립트 작성 또는 수정 시 task-executor 가 위 목록 확인 의무. code-tester 가 rsync 명령에 위 exclude 미포함 시 Recommended 항목으로 지적.
```

---

## §5 사용자 승인 결과

| # | 결정 | 적용 시점 | 비고 |
|---|---|---|---|
| 1 | ✅ 적용 | 2026-05-04 wrap | prod-test-runner.md §4-a 신규 — interactive CLI runtime smoke 의무화. Bash+python 우회 (hook 차단) |
| 2 | ✅ 적용 (강도 조절) | 2026-05-04 wrap | planner.md §6-a 신규 — *대규모* CLI entry 만 시나리오 의무. 단순 wrapper 는 권고 수준. 오버 엔지니어링 회피 |
| 3 | ✅ 적용 (시나리오 A 형식) | 2026-05-04 wrap | CLAUDE.md Phase 2 절에 walkthrough ad-hoc 정책 신규. orchestrator 자율 판정 우선 — 사용자 prompt 는 모호 케이스 *only*. prompt fatigue 회피 (deny-only 모델 정신 일관) |
| 4 | ✅ 적용 | 2026-05-04 wrap | prod-test-runner.md §4-b 신규 — lerobot CLI 진입점 import 체크. 해당 todo 사용 예정 CLI 만 한정 (비용 ↑ 회피) |
| 5 | ✅ 적용 | 2026-05-04 wrap | settings.json — redundant `Bash(...)` 패턴 80건 일괄 제거. allow 9 items 로 단순화. deny 64 유지. _comment 갱신 |
| 6 | ✅ 적용 | 2026-05-04 wrap | orin-deploy-procedure SKILL.md — rsync exclude 원칙 신설. checkpoints/, config/*.json, interactive_cli/configs/*.json 보호 의무 |

---

## §6 관련 ANOMALIES.md 처리

본 보고서로 분석된 anomaly 항목들:

| ANOMALIES 항목 | 관련 제안 | 처리 상태 전환 |
|---|---|---|
| 07 #1 PROMPT_FATIGUE_RESOLVED | 제안 #5 (redundant 패턴 정리) | 갱신 적용 (#5 적용으로 BACKLOG 07 #1 처리 완료) |
| 07 #2 SMOKE_TEST_GAP | 제안 #1, #2 | 갱신 적용 (#1 prod-test-runner §4-a + #2 planner §6-a 양쪽으로 자동 차단 체계 구축) |
| 07 #3 ORCHESTRATOR_GAP | 제안 #2 (walkthrough 시나리오 명세) | 갱신 적용 (#2 planner 측 + 향후 spec Phase 1 흐름 시뮬은 BACKLOG 07 #17 정책 자체 명문화 → #3 도 함께 처리) |
| 07 #4 USER_OVERRIDE (O1·O4 BACKLOG) | — (환경 의존 fallback, 06 reflection #1 와 동일 패턴, 이미 정책화됨) | 갱신 적용 (07 내 처리 완료) |

---

## §7 06 reflection 제안 재발 여부 확인

| 06 제안 | 적용 여부 | 07 재발 |
|---|---|---|
| #1 wrap-spec 미처리 verification_queue 처리 정책 | 적용 (CLAUDE.md 명문화) | O1·O4 무시 분기 첫 명시 적용 사례 — 정책 정상 동작 확인 |
| #2 planner.md 파일 경로 실존 확인 | 적용 | 07 plan.md §경로 불일치 메모 섹션이 정확히 적용됨 (6건 사전 발견) — 효과 확인 |
| #3 task-executor.md spec 가정 반증 패턴 | 적용 | 07 사이클 awaits_user 3건 모두 사전 해소 — 효과 확인 |
| #4 verification_queue 환경 레벨 분류 | 적용 | AUTO_LOCAL·SSH_AUTO·PHYS_REQUIRED 분류가 본 사이클에서 처음 전면 적용 — AUTOMATED_PASS 14건 (이전 0건에서 비약적 개선) |
| #5 lerobot-reference-usage SKILL.md 경로 정정 | 적용 | W1 에서 "이미 올바름" 확인 — 효과 확인 |

**주목**: 06 reflection #4 (환경 레벨 분류) 가 07 사이클에서 처음 전면 적용됐고 AUTOMATED_PASS 14건을 달성했다. 이전 3 사이클 AUTOMATED_PASS 0%에서 본 사이클 14건으로 비약적 개선은 환경 레벨 분류의 직접 효과다.

---

## §8 다음 사이클 진입 권고

### 핵심 잔여 (08_leftarmVLA 진입 전)

| BACKLOG | 내용 | 추천 처리 |
|---|---|---|
| 07 #8 | deploy_orin.sh --delete 가 checkpoints 삭제 | 08 진입 전 수정 필수 (실 ckpt 삭제 위험) |
| 07 #9 | PHYS_REQUIRED 통합 묶음 (Orin·DGX SO-ARM 직결) | 시연장 이동 시 자연 처리 |
| 07 #7 | run_python.sh -u 버그 | Category B — 08 진입 전 권장 |
| 07 #2 | PreToolUse hook Bash matcher 추가 | 중간 우선순위 — deny 한계 보완 |

### 하네스 차기 개선

- 본 reflection 제안 #1·#4 (prod-test-runner runtime smoke + lerobot CLI import 체크) 적용 시 walkthrough todo 폭증 패턴의 일부를 자동화 단계에서 사전 차단 가능
- 제안 #6 (orin-deploy-procedure SKILL.md) 이 적용되면 deploy 스크립트 작성 시 code-tester 가 exclude 미포함을 자동 지적 — Architecture Fitness 향상
- `docs/QUALITY_SCORE.md` 신설 검토 (06 reflection 권고 유지) — 07 사이클 지표 (2-cycle ~6%, AUTOMATED_PASS 14건) 가 추가됨으로써 trend 시각화 가치 증가
