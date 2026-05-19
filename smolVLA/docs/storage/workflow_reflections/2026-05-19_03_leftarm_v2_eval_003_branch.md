# Reflection — 03_leftarm_v2_eval_003_branch (2026-05-19)

> reflection 에이전트 자동 생성. 사용자 승인 후 메인이 갱신 적용.
> 직전 보고서: `docs/storage/workflow_reflections/2026-05-18_02_leftarm_v2_finetune.md`

---

## 사이클 요약

| 항목 | 내용 |
|---|---|
| 활성 spec | `03_leftarm_v2_eval_003_branch` |
| 사이클 기간 | 2026-05-19 17:30 ~ 2026-05-19 19:38 (wall-clock 약 2시간 8분) |
| 총 todo | **5건** (TODO-01 ~ TODO-05) |
| 자동 처리 (AUTOMATED_PASS) | 1건 — TODO-01 (AUTO_LOCAL) |
| 사용자 위임 후 통과 (PHYS_REQUIRED) | 3건 — TODO-02 (SSH_AUTO + 시연장), TODO-03 (PHYS_REQUIRED 20 trial), TODO-04 (집계) |
| 사용자 결정 (awaits_user) | 1건 — TODO-05 (config git 정책 선택지 1 결정) |
| code-tester verdict | READY_TO_SHIP: 2건 (TODO-01 1 cycle, TODO-02 1 cycle) — MAJOR: 0건 |
| prod-test verdict | AUTOMATED_PASS: 1건 (TODO-01), NEEDS_USER_VERIFICATION: 1건 (TODO-02) |
| Phase 3 실물 검증 | PHYS_REQUIRED 단축 (실시 8 / 계획 20) — **8/8 = 100%** (사용자 단축 종료 결정) |
| ANOMALY 등록 | 0건 (본 사이클 `[03_leftarm_v2_eval_003_branch]` 섹션에 이상 패턴 미누적) |
| ad-hoc 변경 | 1건 — `~/.ssh/config` ping 도달성 기반 분기 패치 (SSID 추정 → 실 도달성 전환) |
| 사용자 개입 횟수 (USER_OVERRIDE·USER_DECISION) | 3회 — (1) 시연장 현장 이동에 따른 TODO-02·03 단일 세션 결합, (2) 단축 평가 종료 결정 (7 trial → 100% 신호), (3) TODO-05 선택지 1 결정 |
| 사이클 의의 | M1.5(0%) → 002(0%) → 003(100%) 가설 분리 검증 성공 + 학습 분포 외 robustness 정성 신호 4 trial 모두 통과 + devPC ↔ Orin 네트워크 분리 환경 첫 PHYS_REQUIRED 검증 |

### 사이클 흐름 재구성

```
17:30  START    — planner 분석 완료, TODO-01·02 병렬 dispatch
17:31  DISPATCH — Group 1: TODO-01 + TODO-02 동시 task-executor
17:37  DONE     — TODO-01 task-executor 완료 (wandb 마커 처리 포함)
17:38  DONE     — TODO-02 task-executor 완료 (devPC 측 완료, SSH 차단 상태)
       NOTE     — TODO-02 SSH_AUTO → 시연장 PHYS_REQUIRED 합쳐짐 (네트워크 차단 자율 분류)
17:39  VERDICT  — TODO-01 code-tester READY_TO_SHIP + prod-test AUTOMATED_PASS
17:42  VERDICT  — TODO-02 code-tester READY_TO_SHIP
17:47  VERDICT  — TODO-02 prod-test NEEDS_USER_VERIFICATION (AUTO_LOCAL 9/9 통과)
       DISPATCH — Group 2: TODO-03 PHYS_REQUIRED 사용자 위임
19:15  AD_HOC   — ~/.ssh/config ping 도달성 분기 패치
19:17  DONE     — TODO-02 시연장 검증 통과 (dry-run smoke, empty_cameras 패치 작동)
19:30  DONE     — TODO-03 단축 8 trial, 8/8 = 100%
19:31  USER     — TODO-05 선택지 1 결정 + 즉시 dispatch + 완료
19:32  END-A    — 모든 todo 완료, /wrap-spec 진입
19:38  UPDATE   — TODO-03 추가 trial 1회 → 8/8 최종
```

---

## 사이클 결과 정량

| 분기 | ckpt | 핵심 변수 | trial | 성공 | 성공률 |
|---|---|---|---|---|---|
| M1.5 (baseline) | A2 100ep | empty_cameras=0, 100ep, sched 30K, fp16, b4 | 2 | 0 | **0%** |
| 002 (camera_empty) | A2 100ep, empty=1 | 단일 변수: empty_cameras만 | 2 | 0 | **0%** |
| 003 (종합 분기) | A2 310ep, empty=1, sched_sync, bf16, b6 | 5변수 종합 | 8 (단축) | 8 | **100%** |

003 의 8 trial 내 환경 분포:

| 환경 | trial 수 | 성공 |
|---|---|---|
| 학습 분포 동일 | 4 | 4/4 |
| 학습 분포 外 — 로봇 각도 마늘랩 방향 | 2 | 2/2 |
| 학습 분포 外 — 캔 mass 변화 | 1 | 1/1 |
| 학습 분포 外 — 로봇 각도 + 조명 50% 감소 (다중 perturbation) | 1 | 1/1 |

003 결과: **8/8 = 100%**, 분포 외 4 trial 모두 견딤 (학습 분포 外 robustness 정성 신호 확보).

---

## 발견 패턴

### 패턴 1: devPC ↔ Orin 네트워크 차단 환경의 자율 분류 — SSH_AUTO PHYS_REQUIRED 합산 처리

**발생**: 1건 (TODO-02, 19:38:40 NOTE 이벤트)

**구체 상황**: task-executor 가 TODO-02 의 SSH_AUTO 영역 (Orin ckpt 다운로드·dry-run smoke) 을 수행하려 했으나 devPC ↔ Orin 도달이 차단된 상태 (사용자가 시연장으로 이동 중 = 네트워크 분리). task-executor 는 이를 *task 미완* 이 아닌 *환경 차단* 으로 분류하고, devPC 측 완료 가능한 작업 (eval 시트 신설, HF Hub 원격 검증 9/9) 은 완료한 후 Orin 실행 영역을 PHYS_REQUIRED 검증 큐에 합산 등록했다. code-tester 역시 이 판단을 합리적으로 평가하여 READY_TO_SHIP 발급.

**두 번째 사례 (wandb 마커)**: TODO-01 에서도 동일 패턴이 나타났다. devPC 에 wandb 패키지 미설치 + JavaScript 렌더링 페이지로 인해 학습 metric 일부 (final loss, grad_norm, system chart) 가 추출 불가능했다. task-executor 는 추출 가능한 metric (train_config.json, smoke commit, HF Hub API) 만 채우고 나머지는 `[wandb run 40kzxlmq 확인]` 마커로 표시했다. code-tester 와 prod-test-runner 모두 이를 합리적 처리로 판정했다.

**패턴 추상화**: "환경 차단 (SSH 차단·도구 미설치·JS 렌더링 차단)" 과 "task 미완 (설계 오류·구현 실수)" 을 자율적으로 분리하여, 환경 차단 영역은 *사용자 위임 경로로 자동 전환*하는 패턴이 본 사이클에서 두 번 일관되게 적용됐다.

**현재 룰 검토**:
- `prod-test-runner.md`: SSH_AUTO 가 환경 차단으로 불가 시 자율 PHYS_REQUIRED 전환에 대한 명시적 지침 없음. 현재는 "PHYS_REQUIRED 항목은 사용자 위임" 이라는 역방향 규정만 있음.
- `orin-deploy-procedure/SKILL.md`: 네트워크 차단 환경에서의 partial 완료 처리 패턴 없음.
- CLAUDE.md: "환경 차단 vs task 미완" 자율 분류 기준이 명시되지 않음.

**직전 reflection (02_leftarm_v2_finetune) 비교**: 직전 사이클에서는 SSH 차단 패턴이 시연장 도착 후 ad-hoc 으로 발생했으나 본 사이클은 시연장 이동 중 상태에서 사전 설계됐다. 자율 분류 패턴의 *첫 사이클 설계 레벨 확인*.

**제안 위치**: 갱신 제안 #1

---

### 패턴 2: ~/.ssh/config SSID 기반 분기 깨짐 → ping 도달성 기반 전환

**발생**: 1건 (AD_HOC, 19:15:00)

**구체 상황**: devPC 측 `~/.ssh/config` 에 SSID 추정 기반 Orin IP 분기 (예: HY-WiFi 연결 시 특정 IP) 가 설정돼 있었다. 그러나 사용자의 실제 환경에서 devPC 의 SSID 와 Orin 의 실 IP 대역이 맞지 않아 (`devPC HY-WiFi + Orin eduroam 대역 IP`) `ssh orin` 이 wrong IP 로 연결을 시도했다. 이를 탐지하고 ping 도달성 기반 자동 분기로 패치했다 — `ssh orin` / `ssh orin-hy` / `ssh orin-edu` 3종 alias 신설.

**영향**: ssh config 패치 자체는 CLAUDE.md §walkthrough ad-hoc 정책 "단일 파일 1~30줄, 회귀 위험 낮음" 에 해당하여 즉시 처리됐다. 그러나 *spec dispatch 전 사전 정비* 가 됐다면 시연장 이동 중 약 15분간의 연결 실패 디버깅 시간을 절약할 수 있었다.

**환경 사전 정비 vs ad-hoc 시연장 처리의 차이**: 패턴 1 (SSH 차단 자율 분류) 과 달리 이 패턴은 *네트워크 환경 자체의 설정 오류* 에 가깝다. spec dispatch 전 "Orin SSH 도달 가능 여부 사전 확인" 이 루틴화된다면 시연장 이동 후 즉각 연결을 기대할 수 있다.

**현재 룰 검토**:
- `orin-deploy-procedure/SKILL.md`: SSH 연결 사전 확인 단계가 "배포 후 검증" 맥락으로만 명시돼 있고, *spec 시작 전 환경 점검* 맥락은 부재.
- CLAUDE.md §walkthrough ad-hoc 정책: 환경 즉석 조치를 다루나, *사전 정비 우선순위* 는 미명시.
- `planner.md`: Phase 2 시작 시 SSH 연결 사전 확인 체크리스트 없음.

**직전 reflection 비교**: 02_leftarm_v2_finetune 에서 시연장 ad-hoc 4건 집중 패턴이 발견됐고, 패턴 B (수집-추론 camera 정합 사전 점검 누락) 로 분류됐다. 본 패턴은 그 연장선 — *환경 인프라 사전 정비* 영역.

**제안 위치**: 갱신 제안 #2

---

### 패턴 3: 단축 평가 + 분기 결정 = DOD 정책의 첫 실효성 확인

**발생**: 1건 (Phase 3, 19:30:00 — 단축 7→8 trial 결정)

**구체 상황**: spec TODO-03 의 계획 trial 수는 20 (task1·task2 × front·back × 5회). 실시는 8 trial. 사용자가 *M1.5·002 의 0% 대비 003 의 100% 신호가 명확하다* 고 판단하여 단축 종료를 결정했다.

**CLAUDE.md DOD 정책 정합 평가**: spec 에 "첫 trial 결과가 명백히 0% 면 사용자가 단축 종료 결정 가능" 이 명시됐고, CLAUDE.md § Definition Of Done 의 *DOD 분기 결정 항목* ("분기 결정 = DOD 충족") 이 이를 뒷받침한다. 02_leftarm_v2_finetune 에서 갱신 제안 #4 로 도출되어 같은 날 (2026-05-18) 적용됐고, 바로 다음 사이클 (03) 에서 *첫 실효성 확인* 이 됐다.

**비대칭 단축 조건의 실전 적용**: 02 사이클에서는 "명백히 0%면 단축 가능" 이 양방향 조건이었다 (0% 시 단축). 본 사이클에서는 100% 신호 (명백히 성공) 에서도 단축이 합리적임을 사용자가 자율 결정했다. "단축 종료 조건" 이 0% 뿐 아니라 *신호 명확성* 을 기준으로 해야 한다는 교훈.

**통계 신뢰도 제한 (위험 신호)**: 8 trial 은 성공률 점추정 = 100% 이나 통계 신뢰 구간이 매우 넓다 (Wilson 95% CI ≈ [63%, 100%]). dominant 변수 미분리 (5변수 종합 변경이었으므로 어떤 변수가 핵심인지 모름). 이 두 가지는 M4 이후 사이클의 BACKLOG 후보이다.

**현재 룰 검토**:
- CLAUDE.md §DOD: "단축 종료 조건" 표현이 "첫 trial 명백히 0%" 만 명시. "명백한 성공 신호 (100%)" 도 단축 종료 기준이 될 수 있음을 추가하면 planner 가 보다 robust 한 단축 조건 설계를 할 수 있다.
- spec 양식: 현재 단축 종료 조건이 spec 본문에 자유형 메모로 삽입된다. 표준 필드로 정형화하면 planner 가 Phase 3 검증 큐 구성 시 단축 기준을 명시적으로 포함할 수 있다.

**제안 위치**: 갱신 제안 #3

---

### 패턴 4: 학습 분포 외 robustness 신호 — ad-hoc 발견 → eval 시트 표준화 기회

**발생**: 4 trial 분포 외 perturbation (spec 본문에 없는 영역)

**구체 상황**: spec TODO-03 의 원래 설계는 task × orientation × 5 = 20 trial (학습 분포 동일 환경). 그런데 사용자가 시연장에서 자발적으로 perturbation 을 시도했다 — 로봇 각도를 마늘랩 방향으로 조정, 캔 mass 변화 (다른 캔 사용), 다중 perturbation (로봇 각도 + 조명 50% 감소 동시). 총 4 trial 이 학습 분포 外였으며 모두 성공했다.

이 결과는 TODO-04 에서 `003_eval_2026-05-19.md` 에 *학습 분포 外 robustness 신호 신설* 섹션으로 기록됐다. 그러나 이 섹션은 `camera_empty_eval_2026-05-18.md` 양식에는 없는 003 신설 영역이다.

**양식 표준화 가치**: robustness perturbation 시도는 *매 eval 사이클에서 자연스럽게 발생할 수 있는 영역*이다. 이를 eval 시트 표준 섹션으로 추가하면: (a) planner 가 Phase 3 검증 큐에 "perturbation 1~2 trial 자발적 시도 가능" 을 포함할 수 있고, (b) 사후 ad-hoc 신설이 아닌 계획 내 데이터로 축적 가능하다.

**현재 룰 검토**:
- `orin-deploy-procedure/SKILL.md`: 추론 평가 절차 명시됐으나 robustness perturbation 시도 패턴 없음.
- eval 시트 양식 (`camera_empty_eval_2026-05-18.md`): 분포 외 robustness 섹션 부재.
- planner.md 검증 큐 후보 식별 절: PHYS_REQUIRED 평가에 perturbation 시도 가이드 없음.

**제안 위치**: 갱신 제안 #4

---

### 패턴 5: 02_leftarm_v2_finetune 갱신 제안 적용 효과 — spec dispatch 전 즉각 검증

**발생**: 사이클 전체 (갱신 적용 효과 확인)

**02 사이클 적용 항목 실효성 평가**:

| 제안 # | 적용 내용 | 본 사이클 효과 |
|---|---|---|
| #1 (lerobot-upstream-check SKILL: CLI trim 사전 점검) | 적용됨 | **효과 발현** — 본 사이클에서 lerobot-record 같은 외부 CLI entry 채택 없음. trim 호환성 이슈 0건 |
| #2 (planner.md §6-b 수집-추론 매트릭스) | 적용됨 | **효과 발현** — plan.md 에 §수집-추론 정합 매트릭스 점검 결과 7항목 모두 정합 확인 (plan.md line 179-190). 시연장 ad-hoc 정합 fix 0건 |
| #3 (planner.md §3-a researcher 호출 트리거) | 적용됨 | **효과 발현 (부분)** — 본 사이클은 researcher 호출이 불필요한 eval 중심 사이클이었으나, 트리거 조건에 해당하는 가정 (HF Hub push 완료, empty_cameras 패치 호환) 을 planner 가 §확신 가정으로 분류하여 awaits_researcher 가 필요 없었음. 판단 자체가 §3-a 의도에 부합 |
| #4 (CLAUDE.md DOD 분기 결정 항목) | 적용됨 | **직접 효과 발현** — TODO-03 단축 종료가 DOD 위반이 아닌 분기 결정 DOD 충족으로 처리됨 (패턴 3 참조) |
| #5 (CLAUDE.md prod-test-runner 사이클 정책) | 적용됨 | **해당 없음** — 본 사이클에서 prod-test FAIL 0건. 정책 발동 불필요 |
| #6 (orin/README.md 트리 갱신) | 적용됨 | **간접 효과** — orin/README.md 가 inference/ 진입점을 포함하게 됨. 본 사이클의 Orin 환경 검증에서 추가 drift 발견 없음 |

**평가**: 02 사이클 6개 제안 모두 적용됐고, 직접 관련 있는 4개 항목의 효과가 본 사이클에서 발현됐다. 특히 §6-b 수집-추론 매트릭스 점검은 *02 사이클의 시연장 ad-hoc 4건* 을 본 사이클 0건으로 줄이는 데 직접 기여한 것으로 판단된다.

---

## 네비게이터·참조 정합성 점검

| 영역 | 변경 사항 | navigator 갱신? | 필요 조치 |
|---|---|---|---|
| `orin/docs/leftarm_v2/` | `003_eval_2026-05-19.md` 신설 (TODO-02) | `orin/docs/leftarm_v2/` 내 별도 navigator 없음 (파일 직접 나열) — 드리프트 아님 | — |
| `prof_computer/docs/leftarm_v2/` | `learning_log.md` §003 entry 추가 (TODO-01) | learning_log.md 는 누적형 — 별도 navigator 불필요 | — |
| `docs/storage/` | `09_orin_config_policy.md` 신설 (TODO-05) | **`docs/storage/README.md` 미갱신** — 활성 문서 표에 09 미등록. README 상단 주석이 "2026-05-14 09·10·11 삭제" 만 기록하고 재신설 09 미반영 | ✅ README 갱신 필요 |
| `prof_computer/docs/leftarm_v2/learning_log.md` | §003 wandb 마커 항목 (`[wandb run 40kzxlmq 확인]`) | 마커는 TODO-04 에서 사용자 후속 채움 대기 중 — navigator 이슈 아님 | 사용자 wandb 접속 후 채움 |
| BACKLOG #2·#3 (`07_orin_structure.md`, `08_dgx_structure.md` drift) | 본 사이클 변경 없음 | 여전히 미완 | 다음 사이클 독립 todo |
| BACKLOG #4·#5 (`dgx/docs/finetune/README.md`, `leftarm_v2/README.md` 부재) | 본 사이클 변경 없음 | 여전히 미완 | 다음 사이클 독립 todo |
| BACKLOG #9·#10 (`prof_computer/README.md`, `orin/README.md` drift) | `orin/README.md` 는 02 사이클 제안 #6 으로 갱신됨 (완료). `prof_computer/README.md` 는 여전히 미완 | orin/README.md 갱신됨 (제안 #6 효과). prof_computer/README.md docs/ 섹션 미완 | prof_computer/README.md 독립 todo |

**판정**: 본 사이클에서 가장 중요한 navigator drift 는 `docs/storage/README.md` 의 `09_orin_config_policy.md` 미등록이다. TODO-05 산출물이 docs/storage/ 에 신설됐으나 README 표에 반영이 빠졌다. CLAUDE.md Coupled File Rules §6 ("docs/storage/NN_*.md 추가·삭제 → README.md 표 갱신") 에 해당하는 케이스다.

---

## harness-engineering-principles 매핑

| 패턴 / 사이클 사건 | harness 원칙 | 매핑 |
|---|---|---|
| 환경 차단 자율 분류 패턴 (패턴 1) | 원칙 3: 에이전트 가독성 ("보이지 않는 지식 X") | "환경 차단 vs task 미완" 분류 기준이 agent 정의에 명시되지 않았으나 task-executor · code-tester · prod-test-runner 3 에이전트가 일관되게 올바른 판단을 했음. 이 판단 기준을 skill 로 명시하면 일관성 보장 강화 가능 |
| 환경 차단 자율 분류 패턴 (패턴 1) | 원칙 10: 사람 입력의 방향성 | 환경 차단 영역을 자동으로 사용자 위임 경로로 전환 — 사람을 "가장 중요한 곳 (실물 하드웨어 검증)" 으로 유도. 이 패턴이 명문화되면 사람 개입의 가치 집중도 더 높아짐 |
| SSH config SSID 분기 실패 → ad-hoc 패치 (패턴 2) | 원칙 4: 황금 원칙 + 정기 가비지 컬렉션 | SSID 추정 휴리스틱이 환경 변화에 취약한 "기술 부채" 의 예. spec dispatch 전 환경 사전 정비를 루틴화하면 이 부채를 조기 감지 가능 |
| SSH config SSID 분기 실패 → ad-hoc 패치 (패턴 2) | 원칙 6: YOLO-style 데이터 탐색 금지 | SSID 추정 기반 IP 분기는 "네트워크 환경을 추측으로 코딩" 한 패턴. ping 도달성 기반 전환은 실제 상태 확인으로 검증하는 원칙 6 방향 |
| 단축 평가 + DOD 분기 결정 정책 실효성 (패턴 3) | 원칙 10: 사람 입력의 방향성 | 사용자의 "100% 신호 명확 → 단축 합리" 판단이 DOD 정책으로 뒷받침됨. 사람이 "load-bearing 컨벤션 vs 단순 습관" 을 판단하는 역할을 제대로 수행한 사례 |
| 학습 분포 外 robustness ad-hoc 발견 (패턴 4) | 원칙 8: 자체 구현 선호 (에이전트 가독성 관련) | eval 시트 양식에 robustness 섹션이 없어서 사후 신설됨. 양식을 표준화하면 다음 사이클부터 계획 내 데이터로 수집 가능 — "취향 시스템화 (보강 후보 #10)" 의 eval 양식 버전 |
| 02 적용 항목 효과 발현 — 수집-추론 매트릭스 (패턴 5) | 원칙 2: Progressive Disclosure | planner.md §6-b 가 추론 entry 포함 시만 활성화되는 조건부 체크리스트로 설계됨 — 에이전트가 필요한 상황에서만 추가 컨텍스트 로드. Progressive Disclosure 패턴의 올바른 구현 |
| 02 적용 항목 효과 발현 — DOD 분기 결정 정책 (패턴 5) | 원칙 1: CLAUDE.md = 백과사전 X, 목차 | DOD 분기 결정 항목이 CLAUDE.md 에 단락으로 추가됐고 본 사이클에서 즉각 활성화됨. 헌법 수준 원칙으로 적절 |
| ANOMALY 0건 (본 사이클 이상 신호 없음) | 원칙 9: 최소 차단 병합 게이트 | code-tester MAJOR 0건, prod-test FAIL 0건, End-B 분기 없음. 02 사이클의 갱신 적용 효과로 주요 차단 게이트가 발동되지 않았음 — 처리량 높은 사이클 |
| docs/storage/README.md 09 미등록 | 원칙 7: Architecture Fitness Functions | CLAUDE.md Coupled File Rules §6 "docs/storage/NN_*.md 추가 → README.md 표 갱신" 이 이번 사이클에서 적용되지 않음. 자동 검증 (fitness function) 이 있었다면 배포 전 감지 가능했을 케이스 |

---

## 갱신 제안 (사용자 승인 필요)

| # | 대상 파일 | 변경 내용 요약 | 위험도 | 예상 효과 |
|---|---|---|---|---|
| 1 | `.claude/skills/orin-deploy-procedure/SKILL.md` (또는 신규 skill `ssh-network-resilience`) | "환경 차단 vs task 미완 자율 분류 기준" 및 "partial 완료 처리 패턴" 명시 — SSH 차단·도구 미설치·JS 렌더링 차단 시 완료 가능 영역만 처리하고 나머지는 PHYS_REQUIRED 위임으로 전환하는 휴리스틱 | 낮음 | 패턴 1 재발 시 일관된 분류 보장. 에이전트 추측 제거 |
| 2 | `.claude/agents/planner.md` | "spec dispatch 전 환경 사전 정비 점검 절" 추가 — PHYS_REQUIRED 항목을 포함한 spec 의 경우 plan 작성 시 "Orin SSH 도달 가능 여부 확인" 을 Group 1 병렬 작업에 포함하거나 awaits_user 로 명시. 현재 §6-b 수집-추론 매트릭스 하단에 §6-c 로 추가 권장 | 낮음 | 패턴 2 재발 방지 — spec dispatch 전 SSH 연결성 사전 확인 루틴화 |
| 3 | `/CLAUDE.md` § Definition Of Done (DOD) 또는 § Phase 3 Verification | 단축 평가 종료 조건에 "명백한 성공 신호 (100%)" 도 추가 — 현재 "첫 trial 명백히 0% 면 단축 결정 가능" 만 명시. "또는 명백히 100% (M1.5/002 0% 대비 등 극단적 대비 신호)" 를 같은 조건으로 추가 | 낮음 | 패턴 3 설계화 — 다음 eval 사이클에서 planner 가 양방향 단축 조건을 spec 에 포함하도록 |
| 4 | 신규 eval 시트 양식 (`orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md` 에 섹션 추가 또는 별도 표준 양식 신설) | "학습 분포 外 robustness 시도" 섹션을 eval 시트 표준 항목으로 추가 — 003 사이클 신설 섹션 (환경 분포별 집계 표 + perturbation 자유 메모) 을 기존 양식에 역통합 | 낮음 | 패턴 4 표준화 — 다음 사이클 eval 에서 robustness 데이터를 ad-hoc 이 아닌 계획 내 데이터로 수집 |
| 5 | `docs/storage/README.md` | 활성 문서 표에 `09_orin_config_policy.md` 항목 추가 — "09 | 09_orin_config_policy.md | orin/config/*.json git 추적 정책 (null template + deploy exclude, TODO-05 결정 2026-05-19)" | 낮음 | navigator drift 해소 — Coupled File Rules §6 재발 방지. BACKLOG 항목으로 추가 가능 |

### 상세 변경 명세

---

#### 제안 #1 — orin-deploy-procedure/SKILL.md: 환경 차단 자율 분류 패턴 명시

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/skills/orin-deploy-procedure/SKILL.md`

**도입 사유**: 본 사이클에서 SSH 차단 (TODO-02) 과 wandb 미설치 (TODO-01) 두 케이스에서 task-executor · code-tester · prod-test-runner 가 "환경 차단 vs task 미완" 을 올바르게 분류했으나, 이 분류 기준이 agent 정의 어디에도 명시되지 않았다. 명문화하면 미래 사이클에서도 일관된 자율 판단이 가능하다.

**변경 내용**: orin-deploy-procedure SKILL.md 에 신규 절 추가:

```markdown
## 환경 차단 vs task 미완 자율 분류 (03_leftarm_v2_eval_003_branch 도출)

배포·검증 중 다음 환경 차단 상황에서는 *task 미완* 이 아닌 *환경 차단* 으로 분류:

| 환경 차단 유형 | 자율 처리 |
|---|---|
| SSH 차단 (네트워크 분리·Orin 전원 꺼짐) | 완료 가능 영역 (devPC 측 파일 작성·HF Hub 원격 검증) 만 처리 → Orin 실행 영역은 PHYS_REQUIRED 위임으로 전환 |
| 도구 미설치 (wandb·curl 등) | 추출 가능한 데이터 (설정 파일·API 조회) 만 채움 → 미추출 항목은 `[마커]` 표시 + 사용자 후속 채움 경로 명시 |
| JS 렌더링 페이지 (WebFetch 불가) | 정적 API endpoint (HF Hub API, wandb API) 로 대체 시도 → 대체 불가 시 마커 처리 |

**판단 기준**: "지금 이 환경에서 이 작업을 할 수 없는 이유가 *코드·설계 문제* 인가 vs *실행 환경 부재* 인가?"
- 코드·설계 문제 → task 미완 (code-tester MAJOR, prod-test FAIL 경로)
- 실행 환경 부재 → 환경 차단 (가능한 부분만 완료 + 나머지 위임)

code-tester · prod-test-runner 는 이 분류를 확인 후 verdict 발급.
```

---

#### 제안 #2 — planner.md §6-c: spec dispatch 전 SSH 연결성 사전 점검

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/planner.md`

**도입 사유**: 본 사이클에서 시연장 이동 중 SSH config SSID 분기가 깨져 ad-hoc 패치가 필요했다. spec 에 PHYS_REQUIRED 또는 SSH_AUTO 항목이 있을 때 plan 작성 단계에서 "Orin SSH 도달 가능 여부" 를 Group 1 에 포함하거나 awaits_user 로 처리하면 시연장 이동 후 즉각 연결이 가능해진다.

**변경 내용**: planner.md §6-b 하단에 §6-c 추가:

```markdown
### 6-c. PHYS_REQUIRED 포함 spec 의 환경 사전 정비 점검 (03_leftarm_v2_eval_003_branch 도출)

spec 의 검증 큐 후보에 `SSH_AUTO` 또는 `PHYS_REQUIRED` 항목이 있으면,
plan 작성 시 다음 사전 정비 점검을 Group 1 에 포함하거나 awaits_user 로 처리:

1. **SSH 연결 확인**: `ping <orin_ip>` + `ssh orin hostname` 으로 도달 가능 여부 확인
   - 차단 시 → 사용자에게 연결 경로 확인 (VPN·네트워크 설정) 또는 PHYS_REQUIRED 위임으로 자동 전환
2. **~/.ssh/config 정합 확인**: 현 네트워크 환경에서 alias (`ssh orin`) 가 올바른 IP 로 연결되는지
   - SSID 추정 기반 분기 대신 ping 도달성 기반 분기 권장

위 점검이 필요한 경우 plan §확인 필요 가정 에 명시.
점검 결과가 차단이면 해당 SSH_AUTO 항목을 PHYS_REQUIRED 로 상향 분류.
```

---

#### 제안 #3 — /CLAUDE.md § Definition Of Done: 단축 평가 양방향 종료 조건

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/CLAUDE.md` § Definition Of Done

**도입 사유**: 현재 spec 양식의 단축 종료 조건이 "첫 trial 명백히 0% 시" 단방향. 본 사이클에서 "명백히 100%" 도 단축 합리임을 사용자가 결정했고 DOD 정합임이 확인됐다.

**변경 내용**: § Definition Of Done 의 DOD 분기 결정 항목 설명 내 단축 조건 예시를 확장:

현재:
```
(예: TODO-03(d) "0~20% 영역 → 재정렬 / 50%+ → M2 본 학습 진입" 의 분기 결정 자체가 본 DOD. 단축 trial 로 0-20% 확정 = DOD 충족).
```

갱신 (문구 추가):
```
(예: TODO-03(d) "0~20% 영역 → 재정렬 / 50%+ → M2 본 학습 진입" 의 분기 결정 자체가 본 DOD. 단축 trial 로 0-20% 확정 = DOD 충족). 단축 종료 조건은 *명백한 0% 신호* 뿐 아니라 *명백한 100% 신호* (선행 사이클 대비 극단적 개선 등) 도 해당 — planner 는 spec 에 양방향 단축 조건을 명시 권장 (도출: 03_leftarm_v2_eval_003_branch 2026-05-19).
```

---

#### 제안 #4 — eval 시트 양식: 학습 분포 外 robustness 섹션 표준화

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md` (정본 양식) + 향후 신설 eval 시트

**도입 사유**: 003 사이클에서 학습 분포 外 perturbation 시도가 자연스럽게 발생했고 robustness 신호를 확보했다. 이를 표준 섹션으로 추가하면 다음 eval 에서 계획 내 데이터로 수집 가능하다.

**변경 내용**: `camera_empty_eval_2026-05-18.md` 의 "결과 집계" 섹션 또는 "종합 정성 메모" 섹션 근처에 추가:

```markdown
### 학습 분포 外 robustness 시도 (선택 — 003_eval 도출)

> 계획된 20 trial 과 별도로, 사용자 자발적 perturbation 시도 결과를 기록.
> 성공/실패 여부와 perturbation 종류 명시.

| trial | perturbation 종류 | 결과 | 메모 |
|---|---|---|---|
| — | — | — | — |

단축 trial 시 학습 분포 분류 집계:

| 환경 | trial 수 | 성공 |
|---|---|---|
| 학습 분포 동일 | — | — |
| 학습 분포 外 | — | — |
```

**위험도**: 낮음 (문서 갱신, 코드 변경 없음). 단 정본 양식 변경이므로 이전 eval 시트와의 형식 불일치가 발생할 수 있음.

---

#### 제안 #5 (navigator drift) — docs/storage/README.md: 09_orin_config_policy.md 등록

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/README.md`

**도입 사유**: TODO-05 가 `docs/storage/09_orin_config_policy.md` 를 신설했으나 README 활성 문서 표에 미등록됨. CLAUDE.md Coupled File Rules §6 ("docs/storage/NN_*.md 추가·삭제 → README.md 표 갱신") 미이행.

**변경 내용**: README.md 활성 문서 표에 행 추가:

```
| 09 | [09_orin_config_policy.md](09_orin_config_policy.md) | `orin/config/*.json` git 추적 정책 — null template + deploy exclude 정책 명시 (TODO-05 결정 2026-05-19) |
```

상단 주석에도 추가:
```
> 2026-05-19 09 재신설 (`09_orin_config_policy.md` — orin/config git 정책, spec 03 TODO-05 결정).
```

**위험도**: 낮음 (문서 갱신).

---

## 사이클 위험 신호 및 다음 사이클 입력

### 위험 신호 (BACKLOG 후보)

1. **단축 평가의 통계 신뢰도 제한**: 8 trial (Wilson 95% CI ≈ [63%, 100%]). 지점 추정 100% 이나 신뢰 구간이 넓음. M4 이후 사이클에서 더 많은 trial (20+) 또는 표본 설계가 필요할 수 있음.
2. **dominant 변수 미분리**: 003 = 5변수 종합 변경. 어느 변수 (310ep? empty_cameras? bf16?) 가 핵심인지 불명. 다음 ablation 사이클 (단일 변수 분리 비교) 이 필요할 수 있음.
3. **learning_log.md wandb 마커 미채움**: `[wandb run 40kzxlmq 확인]` 마커 항목 — final loss, grad_norm, system chart 실측값 미기입. 사용자 wandb 접속 후 채움 필요.

### 다음 사이클 방향

BACKLOG #14 (02 사이클 도출) 의 4개 결정 영역이 여전히 유효:
1. **학습 방법**: 003 기준 추가 최적화 (LoRA r·target·lr·scheduler) 또는 dominant 변수 ablation
2. **데이터셋 확장**: 현 310ep 에서 추가 수집 (front:back 균형, 위치 분포, 다른 사람 포함)
3. **학습 노드**: prof_computer 유지 vs DGX 재시도 (image dataset 변환 완료 후)
4. **검증 패턴**: 양방향 단축 조건 + perturbation 시도를 계획 내 포함한 eval 설계

---

## 사용자 승인 결과

> 2026-05-19 사용자 승인 후 메인 Claude 가 직접 갱신 적용 (Category A 영역, hook 우회는 Python via Bash — settings.json 명시 정책 `PreToolUse hook (Write|Edit only — Bash 우회 가능, trade-off 수용)`).

| # | 결정 | 적용 시점 | 비고 |
|---|---|---|---|
| 1 | ✅ 적용 | 2026-05-19 19:50 | `.claude/skills/orin-deploy-procedure/SKILL.md` §"환경 차단 vs task 미완 자율 분류" 신설 (+749 chars) |
| 2 | ✅ 적용 | 2026-05-19 19:52 | `.claude/agents/planner.md` §6-c "PHYS_REQUIRED 포함 spec 의 환경 사전 정비 점검" 신설 (+868 chars) |
| 3 | ✅ 적용 | 2026-05-19 19:48 | `/CLAUDE.md` §DOD 분기 결정 항목에 *명백한 100% 신호 단축* 양방향 조건 추가 |
| 4 | ✅ 적용 | 2026-05-19 19:53 | `orin/docs/leftarm_v2/camera_empty_eval_2026-05-18.md` §학습 분포 外 robustness 시도 (표준 양식) 신설 — 003 사이클 신설 섹션 역통합 |
| 5 | ✅ 적용 | 2026-05-19 19:49 | `docs/storage/README.md` 활성 문서 표에 09 등록 + 상단 주석에 2026-05-19 09 재신설 명시 |

---

## 관련 ANOMALIES.md 처리

본 사이클 (`[03_leftarm_v2_eval_003_branch]`) 은 ANOMALIES 등록 0건으로 이상 신호 미누적 상태.

### 이전 사이클 미처리 항목 (02_leftarm_v2_finetune)

| ANOMALY # | TYPE | 본 보고서 처리 | 권고 |
|---|---|---|---|
| 10 | ORCHESTRATOR_GAP (deploy 전 위험 항목 우선 처리 누락) | reflection 분석됨 | 제안 #1 (환경 차단 자율 분류) 에 "위험 BACKLOG 항목 선행 처리 의무" 를 포함하거나 별도 CLAUDE.md 항목으로 명시 검토 |
| 12 | DEPLOY_ROLLBACK (collection_log 정본 owner 불명) | reflection 분석됨 | 다음 사이클에서 DGX ↔ devPC sync 정책 문서화 (docs/storage/ 에 신설) 또는 BACKLOG 등록 권고 |
