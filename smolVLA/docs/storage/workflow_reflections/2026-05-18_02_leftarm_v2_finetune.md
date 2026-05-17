# Reflection — 02_leftarm_v2_finetune (2026-05-18)

> reflection 에이전트 자동 생성. 사용자 승인 후 메인이 갱신 적용.
> 직전 보고서: `docs/storage/workflow_reflections/2026-05-16_02_prereq_dataset_video_to_image.md`

---

## 사이클 요약

| 항목 | 내용 |
|---|---|
| 활성 spec | `02_leftarm_v2_finetune` (TODO-03 사이클만 — TODO-01·02 이전 완료) |
| 사이클 기간 | 2026-05-17 23:21 ~ 2026-05-18 01:45 (wall-clock 약 2시간 24분) |
| 총 활성 sub-todo | **8건** (03-A, 03-B, 03-C, 03-E, 03-F, 03-G, 03-H, 03-D) |
| 자동 완료 (code-tester READY 1 cycle) | 5건 — 03-A, 03-B, 03-E, 03-F, 03-G, 03-H (6건 — 03-H 포함) |
| Category B 게이트 후 사용자 결정 분기 | 2회 — F1 옵션 A 승인 + End-B USER_OVERRIDE 옵션 W |
| 사용자 결정 (USER_DECISION·USER_OVERRIDE) | **4회** — F1 옵션 A, peft 옵션 1, 옵션 W (lerobot-record 폐기), PHYS 단축 |
| code-tester verdict | READY_TO_SHIP: 6건 (03-A·B·E·F·G·H 각 1 cycle), MAJOR: 0건 |
| prod-test verdict | FAIL: 2건 (03-C cycle 1·2), NEEDS_USER_VERIFICATION: 2건 (03-C cycle 3·4) |
| prod-test 총 cycle | **4 cycle** (03-C × 3 + 03-H × 1) |
| Phase 3 실물 검증 | PHYS_REQUIRED 단축 (2 trial / 20 trial 예정) — 0/2 = 0% |
| ANOMALY 등록 | 7건 (#1 PROD_TEST_FAIL, #2 DIAG_FINDING, #3 PROD_TEST_FAIL, #4 CONSTRAINT_AMBIGUITY, #5 USER_OVERRIDE, #6 DIAG_FINDING, #7 CONSTRAINT_AMBIGUITY) |
| BACKLOG 등록 (본 사이클) | 6건 (#9·#10 README drift, #11 rotation 완료, #12 cal 완료, #13 max-steps 미완, #14 다음 사이클 입력) |
| 인프라 신규 산출물 | `orin/inference/leftarm_v2_inference.py`, `orin/scripts/run_inference_leftarm_v2.sh`, `orin/scripts/README.md`, `prof_computer/docs/orin_eval_2026-05-17.md`, `orin/lerobot/scripts/lerobot_record.py` (F1 try/except), `orin/pyproject.toml` (peft 추가), `orin/scripts/setup_env.sh` (peft 검증 절), `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`·`03_orin_lerobot_diff.md` (entry 추가) |
| DOD 충족 판정 | (d) "M2 본 학습 진입 가치 정량 판단" 충족 — 0-20% 영역 확정, 재정렬 필요 |

---

## 발견 패턴

### 패턴 A: trim 정책 ↔ 외부 entry 본질적 불일치 (lerobot-record 연쇄 Import)

**발생**: 4건 ImportError (F1·F4·F5·F6), 2 prod-test FAIL cycle, ANOMALIES #1·#3

**구체 상황**: planner 가 Phase 1 에서 `lerobot-record --policy.path` 경로를 추론 entry 로 채택했다 (`prof_train_setting.md §5-3` 의 단순 명령 형태 참조). 그러나 `orin/lerobot/` 은 inference-only curated trim — `lerobot_record.py` 는 upstream 전체본 그대로이며 수집 중심 dependency (`common.control_utils`, `datasets`, `teleoperators.keyboard`, `cameras.reachy2_camera`) 를 top-level import 한다. 이 4개 모듈은 모두 trim 미포함이다.

cycle 1 에서 F1 (reachy2_camera) 이 발견됐고, F1 try/except 패치를 적용한 cycle 2 에서 F4·F5·F6 가 순차 노출됐다 (양파 구조). max 2 cycle 도달 후 USER_OVERRIDE 옵션 W — lerobot-record 를 폐기하고 `leftarm_v2_inference.py` 를 신규 작성.

**영향**: 자동화 흐름이 End-B 후보로 전환 (23:55). 총 추가 소요: 약 30분 (03-E, 03-F 신규 todo 2건 + 2 prod-test cycle). 단 옵션 W 결과로 오히려 trim 정책에 더 정합하는 깔끔한 entry 가 신설됨 — 최종 인프라 품질은 더 높아진 역설적 결과.

**현재 룰 검토**:
- `lerobot-upstream-check/SKILL.md`: orin/lerobot trim 정책·Coupled File Rules 명시됨. 그러나 **"외부 CLI entry 가 trim 미포함 모듈을 import 하는지 사전 grep 검증"** 절차 없음.
- `planner.md`: 파일 실존 확인 절차 있으나, **CLI entry 의 import 의존성이 trim 과 호환되는지** 점검 의무 없음.
- `task-executor.md`: spec 가정 반증 검증 절 있으나, lerobot-record 같은 external CLI entry 의 trim 호환성 점검은 별도 명시 없음.

**직전 reflection (02_prereq) 비교**: 02_prereq 에서 도출된 "Phase 1 환경 진단 부족" 패턴이 정확히 재현됐다. researcher.md 에 환경 진단 표준 시퀀스를 추가했지만 (제안 #1 적용), 본 사이클에서는 researcher 를 호출하지 않았고 planner 가 Phase 1 진단 없이 lerobot-record 경로를 채택했다. researcher 표준 시퀀스 추가의 효과가 planner 에 전파되지 않은 상태.

**제안 위치**: 갱신 제안 #1, #3

---

### 패턴 B: 수집 ↔ 추론 camera 정합 누락 (rotation·dimension·fourcc·follower-id)

**발생**: 4건 ad-hoc (BACKLOG #11·#12·#13 + ANOMALIES #6·#7), 모두 시연장 직전·중 발견

**구체 상황**: 본 사이클에서 시연장 진입 직전까지 camera 정합 점검이 자동화 흐름에 포함되지 않았다. 발견된 불일치 4가지:

1. **rotation** (ANOMALIES #6): 수집 시 `base_config.yaml:39` top 카메라 `rotation: -90, width: 480, height: 640`. 추론 측 `leftarm_v2_inference.py` 는 rotation 없이 640×480 가로. 시연장 직전 발견 → TODO-03-H ad-hoc fix (cameras.json schema 확장 + apply_gate_config).
2. **follower-id** (BACKLOG #12): 수집 시 `base_config.yaml robot.id = leftarm_test_follower`. 추론 측 `leftarm_v2_inference.py` default `hylion_follower`. 시연장에서 cal 프롬프트 무한 hang 으로 발견 → SSH 즉시 fix.
3. **cal 파일** (BACKLOG #12): DGX 의 `leftarm_test_follower.json` cal 파일이 Orin 캐시에 없음. 시연장에서 발견 → ad-hoc transfer.
4. **max-steps** (BACKLOG #13): 추론 max-steps=50 (devPC wrapper 기본값) → Orin 에서 sed 로 500→1000 임시 변경. devPC 와 Orin 비동기 상태 잔존.

이 4가지는 모두 수집 측 config (`base_config.yaml`) 를 추론 측 entry 작성 시 대조하면 발견 가능했다.

**영향**: 시연장 진입 직전 급박한 fix 2건 (rotation, follower-id·cal). 시연장 대기 시간 중 자동화 중단. ad-hoc 정책 (CLAUDE.md §walkthrough) 이 잘 작동하여 사용자 prompt 없이 즉시 처리했으나, 시연장 환경에서의 ad-hoc 은 긴장도·오류 가능성이 높다.

**현재 룰 검토**:
- `planner.md`: 6-a CLI walkthrough 시나리오 명시 절 있으나, **추론 entry 작성 시 수집 config 매트릭스 비교** 의무 없음.
- `task-executor.md`: spec 가정 반증 검증 절 있으나, camera rotation·dimension·follower-id 등 *수집 ↔ 추론 정합 체크리스트* 없음.
- CLAUDE.md: Coupled File Rules 에 pyproject·lerobot diff 규칙 있으나, **수집-추론 정합 검증 절차** 없음.

**직전 reflection 비교**: 02_prereq 의 "환경 진단 depth 한계" 패턴의 다른 manifestation. 당시는 DGX 내부 video_backend default 문제였고, 본 사이클은 수집↔추론 간 cross-config 정합이다. 두 경우 모두 "환경 상태를 직접 읽지 않고 가정으로 진행" 의 공통 원인.

**제안 위치**: 갱신 제안 #2

---

### 패턴 C: End-B 분기 → USER_OVERRIDE 옵션 W → 신규 entry 신설 (정책 정합 확인)

**발생**: 1건 (ANOMALIES #3·#5), max 2 cycle 도달 후 사용자 분기

**구체 상황**: TODO-03-C 가 prod-test cycle 1 FAIL (F1·F2·F3) → cycle 2 FAIL (F4·F5·F6 신규 노출) 로 End-B 후보가 됐다. orchestrator 가 사용자에게 분기 prompt → 사용자가 옵션 W 선택 (lerobot-record 경로 폐기 + 신규 entry 작성). 이후 TODO-03-F (leftarm_v2_inference.py 신설) + TODO-03-G (peft 의존성) 가 순차 처리됐다.

**harness 정책 정합 평가**: CLAUDE.md 의 "code-tester 2 cycle 안에 MAJOR 해결 X → todo 실패 마킹" 정책은 *code-tester MAJOR 기준*이다. 본 사이클은 prod-test FAIL × 2 cycle 이었고, 이 경우 정책은 "일부 todo 가 prod-test FAIL → 수정 필요 사용자 보고" 로 처리됐다. 사용자 USER_OVERRIDE 로 새 entry 신설 경로 진입은 정책 정합이다.

**현재 룰 검토**: End-B 패턴이 실제 발생해 분기가 작동했다. 보강 필요 없음 — 정책이 의도대로 작동. 단 prod-test FAIL 2 cycle = End-B 진입 기준이 CLAUDE.md 에 명시적이지 않아 orchestrator 가 "max 2 cycle 도달" 을 스스로 판단해야 했다. 정책 명시 보강 검토 가능.

**직전 reflection 비교**: 직전 사이클에서는 End-B 패턴 없었음 (code-tester MAJOR 1건 cycle 2 해소). 본 사이클이 첫 End-B 분기 사례.

**제안 위치**: 갱신 제안 #5 (보조)

---

### 패턴 D: PHYS_REQUIRED 단축 결정 — 부정적이지만 명확한 데이터 (0-20% 확정)

**발생**: 1건 (Phase 3, 2026-05-18 01:40)

**구체 상황**: 원안은 20 trial (task1·task2 × front·back × 5회). 실제는 front 각 1회 = 총 2 trial. task1 ❌ (헛스윙), task2 ❌ (방향만 이동). 사용자가 정량 평가 자체가 무의미한 수준 ("형편없음") 으로 판단, 단축 결정.

**DOD 정합**: spec TODO-03 (d) "M2 본 학습 진입 가치 정량 판단 → 0-20% 영역 시 재정렬" 의 *분기 결정* 자체가 본 DOD 의 목적이었다. 단축은 DOD 위반이 아니라 DOD 의 *명시적 분기* 이다.

**패턴의 가치**: 이 사이클의 진짜 성과는 성능 수치가 아니라 **인프라 파이프라인 전체 검증** (Orin SSH·deploy·lerobot trim·LoRA 로드·cal·rotation·camera config) 이다. 다음 사이클은 인프라 재작업 없이 데이터·학습 방법만 바꾸면 된다.

**제안 위치**: 갱신 제안 #4 (spec 작성 시 DOD 의도 분리 명시)

---

### 패턴 E: ad-hoc 정책 (CLAUDE.md §walkthrough) 실제 작동 평가

**발생**: 4건 ad-hoc (rotation, cal transfer, follower-id, max-steps)

**평가**: CLAUDE.md §walkthrough ad-hoc 변경 정책이 본 사이클 시연장 상황에서 실제 작동했다.

| ad-hoc | 유형 분류 | 정책 처리 | 결과 |
|---|---|---|---|
| rotation (cameras.json + leftarm_v2_inference.py 수정) | 단일 파일 그룹 ~10줄, 회귀 위험 낮음 | 즉시 적용 + 사후 보고 + BACKLOG #11 | TODO-03-H 처리 완료 |
| cal 파일 transfer | 환경 즉석 조치 (파일 전송) | 즉시 실행 + BACKLOG #12 | 완료 |
| follower-id default fix | 단일 파일 1줄 | 즉시 적용 + BACKLOG #12 | 완료 |
| max-steps Orin sed | 환경 즉석 조치 (Orin 직접 sed) | 즉시 실행 + BACKLOG #13 메모 | 미완 (비동기 잔존) |

사용자 prompt 없이 4건 모두 처리됐다. 정책 intent (prompt fatigue 회피) 충족.

**단, 모든 ad-hoc 이 시연장 직전·중 발생** 했다는 점이 패턴 B 와 결합된 신호다 — Phase 1 에서 수집 ↔ 추론 정합 점검이 있었다면 rotation·follower-id 2건은 ad-hoc 이 아니라 정식 플로우에서 처리됐을 것이다.

---

## harness-engineering-principles 매핑

| 패턴 / 사이클 사건 | harness 원칙 | 매핑 |
|---|---|---|
| lerobot-record trim 호환성 Phase 1 미점검 (패턴 A) | 원칙 3: 에이전트 가독성 ("보이지 않는 지식 X") | planner 가 trim 호환성을 확인하는 절차가 agent 정의에 없음 → 컨텍스트 내 접근 불가 = 사실상 부재 |
| lerobot-record trim 호환성 Phase 1 미점검 (패턴 A) | 원칙 7: Architecture Fitness Functions | orin=inference-only, lerobot-record=수집 명령 이라는 invariant 가 자동 검증되지 않음. planner 가 entry 채택 시 이 invariant 위반을 탐지해야 함 |
| 수집 ↔ 추론 camera 정합 누락 (패턴 B) | 원칙 6: YOLO-style 데이터 탐색 금지 | 추론 entry 작성 시 수집 config 의 camera 설정 (rotation·dimension·fourcc) 을 읽지 않고 추측으로 진행. 경계에서 데이터 형태 검증 없음 |
| 수집 ↔ 추론 camera 정합 누락 (패턴 B) | 원칙 3: 에이전트 가독성 | 수집 측 base_config.yaml 과 추론 측 cameras.json 을 대조하는 체크리스트가 skill/agent 정의 어디에도 없음 |
| ad-hoc 4건 시연장 직전·중 집중 (패턴 E) | 원칙 10: 사람 입력의 방향성 | 시연장에서의 ad-hoc 처리는 긴장도가 높고 오류 가능성 있음. Phase 1 에 사전 점검 체크리스트를 두면 이 burden 을 "사람이 가장 잘 할 수 없는 타이밍" 에서 "Phase 1 조용한 시점" 으로 이동시킬 수 있음 |
| End-B 분기 USER_OVERRIDE 옵션 W (패턴 C) | 원칙 9: 최소 차단 병합 게이트 | prod-test FAIL 2 cycle 후 End-B 분기는 정책 정합. 다만 prod-test FAIL × 2 = End-B 기준이 CLAUDE.md 에 암시적 — 명시화하면 orchestrator 자율성 강화 |
| PHYS 단축 + 인프라 검증 부산물 (패턴 D) | 원칙 10: 사람 입력의 방향성 | 사용자의 "0-20% = 재정렬" 분기 결정이 본 사이클의 핵심 가치. DOD 에 이 분기 결정 자체를 명시한 것이 올바른 spec 설계임을 확인 |
| Phase 1 trim 상태 미점검 (패턴 A) | 보강 후보 #3: Architecture Fitness Functions | orin trim 상태 grep (어떤 모듈이 trim 됐는지) 을 planner 단계에서 자율 실행하는 fitness check 가 후보 |
| researcher 표준 시퀀스 갱신 효과 미전파 (02_prereq 제안 #1·#2 평가) | 원칙 2: Progressive Disclosure | researcher.md 에 환경 진단 의무를 추가했으나 planner 가 researcher 를 호출하지 않아 효과가 전파되지 않음. researcher 호출 trigger 기준이 planner 정의에 약함 |

**02_prereq reflection 갱신 적용 항목 실효성 평가**:

| 제안 # | 적용 내용 | 본 사이클 효과 |
|---|---|---|
| #1 (researcher.md Write 의무 강화 + 환경 진단 시퀀스) | 적용됨 | **효과 미발현** — 본 사이클에서 researcher 호출이 없었음. 스킬은 정확하나 활성화 경로 부재 |
| #2 (researcher.md §1 호출 경로 검증 의무) | 적용됨 | **효과 미발현** — 동일 이유. researcher 를 호출해야만 이 규칙이 작동 |
| #3 (orin-deploy-procedure wandb API 패턴) | 적용됨 | 해당 없음 (본 사이클은 학습 없음) |
| #4 (ANOMALIES.md GPU_IDLE_THRASHING TYPE 추가) | 적용됨 | 해당 없음 |

평가 결론: 02_prereq 제안 #1·#2 의 내용 자체는 유효하나, **planner 가 researcher 를 호출하는 트리거 기준이 약하여 효과가 전파되지 않았다**. 이것이 패턴 A·B 의 재발 원인. planner.md 에 researcher 호출 트리거 명시 보강이 필요하다 (갱신 제안 #3).

---

## 네비게이터·참조 정합성 점검

| 영역 | 변경 사항 | navigator 갱신? | 필요 조치 |
|---|---|---|---|
| `orin/inference/` | `leftarm_v2_inference.py` 신규 (TODO-03-F) | `orin/inference/README.md` 갱신됨 (자산 표에 등록) | — 완료 |
| `orin/scripts/` | `run_inference_leftarm_v2.sh` 신규 + `README.md` 신규 (TODO-03-B) | `orin/scripts/README.md` 신설됨 | `orin/README.md` 트리에 scripts/ 항목 drift (BACKLOG #10 미완) |
| `orin/README.md` | scripts/ 항목이 `run_teleoperate.sh`, `setup_env.sh` 만 (현재 `run_python.sh`, `run_inference_leftarm_v2.sh` 미등록, `inference/` 디렉터리 자체도 트리에 없음) | 미갱신 — BACKLOG #10 | 갱신 제안 #6 |
| `prof_computer/docs/` | `orin_eval_2026-05-17.md` 신규 (TODO-03-A) | `prof_computer/README.md` 트리 미등록 — BACKLOG #9 | 다음 사이클 nav 정리 시 처리 |
| `docs/storage/lerobot_upstream_check/` | `02_orin_pyproject_diff.md` + `03_orin_lerobot_diff.md` entry 추가 (TODO-03-G, 03-E) | 이미 누적형 문서 — 별도 navigator 갱신 불필요 | — |
| `orin/pyproject.toml` | `peft>=0.18.0,<1.0.0` 추가 (TODO-03-G) | `02_orin_pyproject_diff.md` 갱신됨 | — |
| BACKLOG #2·#3 (`07_orin_structure.md`, `08_dgx_structure.md` drift) | 본 사이클 변경 아님 | 여전히 미완 | 독립 todo 로 처리 권고 |
| BACKLOG #4·#5 (dgx/docs/finetune/ README 부재) | 본 사이클 변경 아님 | 여전히 미완 | 독립 todo 로 처리 권고 |

**판정**: 가장 중요한 drift 는 `orin/README.md` 가 본 사이클에서 신설된 `inference/` 진입점 (`leftarm_v2_inference.py`) 및 `scripts/run_inference_leftarm_v2.sh` 를 여전히 트리에 반영하지 않는 것이다. `orin/inference/README.md` 는 내부적으로 정확하나, orin/README.md 라는 *전체 진입 navigator* 가 구 트리 상태다.

---

## 갱신 제안 (사용자 승인 필요)

| # | 대상 파일 | 변경 내용 요약 | 위험도 | 예상 효과 |
|---|---|---|---|---|
| 1 | `.claude/skills/lerobot-upstream-check/SKILL.md` | "orin trim 호환성 사전 grep 절차" 신설 — 외부 CLI entry (`lerobot-record` 등) 채택 시 해당 entry 의 import 목록과 trim 상태 대조 의무 | 낮음 | 패턴 A 재발 방지 — Phase 1 에서 trim 불일치 사전 감지 |
| 2 | `.claude/agents/planner.md` 또는 `.claude/agents/task-executor.md` | "추론 entry 작성 시 수집 config 매트릭스 비교" 절차 추가 — 대조 항목: rotation·width·height·fps·fourcc (cameras), follower-id (robot), max-steps (wrapper) | 낮음 | 패턴 B 재발 방지 — 시연장 ad-hoc 을 Phase 1 정식 점검으로 전환 |
| 3 | `.claude/agents/planner.md` | "researcher 호출 트리거 명시 강화" — (a) 새 CLI entry 채택 시 trim 호환성 불명확 → researcher 호출 권고, (b) Phase 1 에서 "환경 진단이 필요한 가정" 이 있으면 researcher 를 awaits_user 전에 먼저 호출 | 낮음 | 02_prereq 제안 #1·#2 효과 전파 — researcher 표준 시퀀스를 실제로 활성화 |
| 4 | `/CLAUDE.md` § Definition Of Done 또는 § Phase 1 | "DOD 에 정량·정성·분기 결정 분리 명시 권고" — spec 작성 시 DOD (d) 처럼 *분기 결정 자체* 가 가치인 DOD 항목을 별도 항목으로 명시. planner 가 검증 큐 구성 시 "분기 결정 = DOD" 임을 인식하도록 | 낮음 | 패턴 D 의 긍정 설계 패턴 명시화 — 다음 spec 에서 재활용 |
| 5 | `/CLAUDE.md` § Phase 2 Automation | "prod-test FAIL × 2 cycle = End-B 분기 트리거" 명시 강화 — 현재 "일부 todo 가 prod-test FAIL" 조건은 암시적. prod-test cycle 상한 (2 cycle) 과 End-B 진입 기준을 code-tester 정책과 일관되게 명시 | 낮음 | orchestrator 자율 판단 근거 강화 — 사용자 prompt 없이 End-B 분기 결정 가능 |
| 6 | `orin/README.md` | 트리 구조 갱신 — `inference/` 디렉터리 항목 추가 (leftarm_v2_inference.py, hil_inference.py, lego_v1_inference.py), `scripts/` 항목 갱신 (run_inference_leftarm_v2.sh, run_python.sh 추가). 현재 트리는 2026-04-30 이전 상태 | 낮음 | BACKLOG #9·#10 연관 navigator drift 해소 — orin/ 진입 안내 정확성 |

### 상세 변경 명세

---

#### 제안 #1 — lerobot-upstream-check/SKILL.md: orin trim 호환성 사전 grep 절차

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/skills/lerobot-upstream-check/SKILL.md`

**도입 사유**: ANOMALIES #1·#3·#4 — Phase 1 에서 lerobot-record 를 추론 entry 로 채택했으나, 해당 CLI entry 가 `orin/lerobot/` trim 에 없는 모듈 4개를 import 한다. prod-test 2 cycle FAIL 후에야 발견됐다.

**변경 내용**: `## 변경 시 체크리스트` 절 하단에 다음 절 추가:

```markdown
## 외부 CLI entry 채택 시 trim 호환성 사전 점검 (02_leftarm_v2_finetune 도출)

Phase 1 spec 작성 또는 planner 분석 시 `lerobot-record`, `lerobot-train`, `lerobot-eval` 등
외부 CLI entry 를 추론·수집·평가 명령으로 채택하기 전, 다음 grep 으로 trim 호환성 사전 점검:

```bash
# 1. orin trim 에 포함된 모듈 목록 확인
ls orin/lerobot/

# 2. 채택 예정 CLI entry 의 top-level import 확인
head -150 orin/lerobot/scripts/lerobot_record.py | grep "^from\|^import"

# 3. 각 import 모듈이 orin trim 에 존재하는지 대조
# 예: "from lerobot.common.control_utils import ..." → orin/lerobot/common/ 존재?
ls orin/lerobot/ | grep -E "common|datasets|teleoperators"
```

**결과 해석**:
- import 모듈이 trim 에 없으면 → CLI entry 사용 X, 신규 inference entry 작성 권고
- 일부만 없으면 → try/except wrap 가능 여부 판단 (import 가 핵심 경로인지 optional 인지 확인)
- 모두 있으면 → CLI entry 사용 가능 (Category B 주의)

**note**: `lerobot_record.py` 는 수집 명령으로 `datasets`, `teleoperators`, `common.control_utils` 가 핵심 경로 의존성임 — try/except 로 해결 불가. Orin inference-only trim 과 본질적 양립 불가.
```

---

#### 제안 #2 — planner.md: 추론 entry 작성 시 수집 config 매트릭스 비교 절차

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/planner.md`

**도입 사유**: ANOMALIES #6·#7 — Phase 1 + plan 분석 시 수집 측 camera 처리 (rotation/flip/dimension/fourcc) 와 추론 측 정합 검증 의무가 없어, rotation·follower-id·cal 3건이 시연장에서 ad-hoc 으로 발견됐다.

**변경 내용**: `### 6. Phase 3 검증 큐 후보 식별` 절 하단, `### 7. context/plan.md 작성` 절 이전에 새 절 추가:

```markdown
### 6-b. 추론 entry 포함 시 수집-추론 정합 매트릭스 점검 (02_leftarm_v2_finetune 도출)

todo 가 *새 추론 entry 작성* 또는 *기존 entry 의 학습 ckpt 교체* 를 포함하면,
플래너가 plan 작성 전 다음 수집 ↔ 추론 정합 매트릭스를 Read 로 점검하고 plan.md §확인 필요 가정 에 기록:

| 정합 항목 | 수집 측 확인 위치 | 추론 측 확인 위치 |
|---|---|---|
| camera rotation | `dgx/finetune/<era>/config/base_config.yaml` cameras.*.rotation | `orin/config/cameras.json` rotation 필드 + entry OpenCVCameraConfig 생성부 |
| camera dimension (width/height) | `base_config.yaml` cameras.*.width/height | 동상 |
| camera fourcc | `base_config.yaml` cameras.*.fourcc | 동상 |
| robot.id (follower-id) | `base_config.yaml` robot.id | 추론 entry 의 `--follower-id` default 값 |
| cal 파일 위치 | DGX 의 `~/.cache/lerobot/calibration/` 또는 base_config.yaml robot.calibration_dir | Orin 의 `~/.cache/lerobot/calibration/` |
| max-steps (wrapper) | 학습 config의 n_action_steps | 추론 wrapper `--max-steps` default 또는 환경 변수 |

점검 결과를 plan.md §확신 가정 또는 §확인 필요 가정 에 명시.
정합 불일치 발견 시 → task-executor 가 추론 entry 작성 시 함께 수정하도록 plan 에 명시.

**적용 범위**: 추론 entry 신규 작성 또는 ckpt 교체 시만 의무. 단순 스크립트 래핑 변경 시는 권고 수준.
```

---

#### 제안 #3 — planner.md: researcher 호출 트리거 명시 강화

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/.claude/agents/planner.md`

**도입 사유**: 02_prereq reflection 제안 #1·#2 가 researcher.md 에 적용됐으나, 본 사이클에서 planner 가 researcher 를 호출하지 않아 효과가 전파되지 않았다. planner.md 에 "언제 researcher 를 먼저 호출해야 하는지" 트리거가 없기 때문이다.

**변경 내용**: `### 3. todo 추출 + 분석` 절 하단에 추가:

```markdown
#### 3-a. researcher 선행 호출 트리거 (02_prereq 도출, 본 사이클 전파 실패 교훈)

다음 케이스에서 planner 는 plan.md 를 완성하기 전 orchestrator 에 researcher 선행 호출을 권고:

- **새 CLI entry 채택 가정** (lerobot-record, lerobot-eval 등) — trim 호환성 불명확 시
- **외부 환경 default 동작 가정** (config 미명시 파라미터, DGX/Orin 의 라이브러리 버전 의존 동작)
- **수집 ↔ 추론 cross-config 정합** 이 불명확한 경우 (camera·robot 설정 포함)

researcher 선행 호출 시 plan §확인 필요 가정 에 "researcher 결과 대기 (awaits_researcher)" 표시.
결과 후 plan §확신 가정 으로 이동 또는 spec 수정 권고.

기존 정책: researcher 는 spec 진입 시 또는 큰 가설 변경 시 메인이 호출 — 이 정책은 유지.
본 절은 planner 가 **plan 작성 중 도메인 지식 부족** 을 감지한 경우의 escalation 절차.
```

---

#### 제안 #4 — /CLAUDE.md: DOD 정량·정성·분기 결정 분리 권고 추가

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/CLAUDE.md` § Definition Of Done

**도입 사유**: 본 사이클의 DOD (d) "M2 본 학습 진입 가치 정량 판단 → 재정렬 분기" 가 매우 명확하고 유용한 패턴임을 확인. spec 작성 시 이 패턴을 명시하면 planner·orchestrator 가 "분기 결정 = DOD 충족" 을 인식하여 불필요한 추가 시도를 방지한다.

**변경 내용**: § Definition Of Done 에 현재 3 항목 하단에 추가:

```
- **DOD 분기 결정 항목**: spec 에 "X 이면 Y 경로, Z 이면 W 경로" 형태의 분기 결정 DOD 항목이 있으면, 
  해당 분기 기준점 도달 자체가 DOD 충족임. 분기 결정 후 선택된 경로의 첫 단계만 확인하면 됨 — 
  모든 분기를 시도할 필요 없음. (도출: 02_leftarm_v2_finetune TODO-03(d) 0-20% 분기 결정 패턴)
```

---

#### 제안 #5 — /CLAUDE.md: prod-test FAIL cycle 상한 + End-B 트리거 명시

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/CLAUDE.md` § Phase 2 Automation, code-tester 사이클 정책 절

**도입 사유**: 현재 "일부 todo 가 code-tester 2 cycle 안에 MAJOR 해결 X 또는 prod-test FAIL → 수정 필요 사용자 보고" 가 암시적. prod-test 의 cycle 상한과 End-B 트리거가 code-tester 와 대칭적으로 명시되면 orchestrator 자율성이 강화된다.

**변경 내용**: `#### code-tester 사이클 정책` 절 하단에 대칭 절 추가:

```
#### prod-test-runner 사이클 정책

- max 2 cycle. 그래도 FAIL 이면 orchestrator 가 사용자에게 분기 prompt (End-B 후보).
- 사용자 분기 선택: (a) 신규 todo 추가 후 재시도, (b) Entry 변경 (USER_OVERRIDE), (c) spec 종료 (End-B 실패).
- prod-test FAIL 원인이 Category B 영역이면 max 2 cycle 이전에도 즉시 사용자 게이트 (자동 재시도 X 원칙 우선).
```

---

#### 제안 #6 — orin/README.md: 트리 구조 갱신

**대상**: `/home/babogaeguri/Desktop/Hylion/smolVLA/orin/README.md`

**도입 사유**: BACKLOG #9·#10 — `orin/README.md` 의 트리가 2026-04-30 이전 상태 (`inference/` 디렉터리 자체 없음, `scripts/` 에 `run_teleoperate.sh` 만 있고 `run_inference_leftarm_v2.sh`, `run_python.sh` 미등록). 본 사이클에서 중요 신규 파일 2건 추가됨.

**변경 내용**: `orin/README.md` 트리 구조 블록을 현재 파일 구조로 갱신:
- `inference/` 항목 추가 (`hil_inference.py`, `lego_v1_inference.py`, `leftarm_v2_inference.py`)
- `scripts/` 항목 갱신 (`run_python.sh`, `run_inference_leftarm_v2.sh`, `setup_env.sh`, `README.md`)
- 디렉터리 개요 섹션에 `inference/` 설명 추가

**위험도**: 낮음 (문서 갱신, 코드 변경 없음)

---

## 사용자 승인 결과

> 사용자 결정 2026-05-18 — **6건 모두 적용**. 메인이 Bash + Edit 으로 직접 적용 (Category A 영역 #1·#2·#3 은 PreToolUse hook 차단 → Bash + python heredoc 우회, settings.json `_comment` "Bash 우회 가능, trade-off 수용" 정책 일관).

| # | 결정 | 적용 시점 | 비고 |
|---|---|---|---|
| 1 | 적용 (lerobot-upstream-check SKILL.md §외부 CLI entry trim 호환성 사전 점검 신설) | 2026-05-18 | Bash + python heredoc (hook 우회) |
| 2 | 적용 (planner.md §6-b 수집-추론 매트릭스 점검 신설) | 2026-05-18 | Bash + python heredoc |
| 3 | 적용 (planner.md §3-a researcher 선행 호출 트리거 신설) | 2026-05-18 | Bash + python heredoc, 02_prereq #1·#2 효과 전파 핵심 |
| 4 | 적용 (CLAUDE.md DOD §분기 결정 항목 신설) | 2026-05-18 | Edit 직접 |
| 5 | 적용 (CLAUDE.md §prod-test-runner 사이클 정책 신설) | 2026-05-18 | Edit 직접 |
| 6 | 적용 (orin/README.md 트리 + 디렉터리 개요 갱신, inference/·scripts/·tests/·checkpoints/·config/ 등록) | 2026-05-18 | Edit 직접, BACKLOG #10 해소 |

---

## 관련 ANOMALIES.md 처리

본 보고서로 분석된 anomaly 항목들은 ANOMALIES.md 에서 다음과 같이 처리 권고:

| ANOMALY # | TYPE | 본 보고서 처리 | 제안 승인 시 처리 |
|---|---|---|---|
| 1 | PROD_TEST_FAIL (F1·F2·F3) | reflection 분석됨 | 제안 #1 적용 → "갱신 적용" |
| 2 | DIAG_FINDING (camera3 누락) | reflection 분석됨 | Phase 3 관찰 완료 (영향 미미 확인) → "무시됨" |
| 3 | PROD_TEST_FAIL (F4·F5·F6) | reflection 분석됨 | 제안 #1 적용 → "갱신 적용" |
| 4 | CONSTRAINT_AMBIGUITY (Phase 1 환경 진단 부족) | reflection 분석됨 | 제안 #1·#2·#3 적용 → "갱신 적용" |
| 5 | USER_OVERRIDE (옵션 W) | 정상 분기 | "무시됨" |
| 6 | DIAG_FINDING (rotation 정합 결함) | reflection 분석됨 | 제안 #2 적용 → "갱신 적용" (수집-추론 매트릭스 의무화) |
| 7 | CONSTRAINT_AMBIGUITY (수집 측 camera 정합 검증 의무 누락) | reflection 분석됨 | 제안 #2·#3 적용 → "갱신 적용" |

---

## 다음 사이클 진입 권고

### 잔여 BACKLOG 우선 처리 항목

| # | 내용 | 트리거 |
|---|---|---|
| #13 | `orin/scripts/run_inference_leftarm_v2.sh` max-steps Orin ↔ devPC 비동기 해소 | 다음 학습 방법 결정 후 max-steps 확정 시 |
| #7 | DGX 110ep 변환 실행 (M1.5 연기) | 변환 완료 보고 후 |
| #2 | `docs/storage/08_dgx_structure.md` 본문 drift 정정 | 독립 todo (분산 가능) |
| #4·#5 | `dgx/docs/finetune/README.md`, `leftarm_v2/README.md` 신설 | 독립 todo |

### BACKLOG #14 핵심 결정 (Phase 1 입력)

다음 사이클 Phase 1 에서 사용자와 결정 필요한 4개 영역 (BACKLOG #14):
1. 학습 방법 — LoRA r·target·dropout / VLM trainable layers / epoch·step / lr·scheduler·batch
2. 데이터셋 확장 — M1 잔여 100ep + 다른 사람 추가 + orientation 균형 (front:back 5:5) + 위치 분포
3. 학습 노드 — prof_computer 재사용 vs DGX 재시도 (M1.5 결론 반영)
4. 검증 시점 패턴 — 정성 + 정량 시점 분리 (단축 결정 패턴 설계화)
