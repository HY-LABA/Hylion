# Execution Plan — 06_dgx_absorbs_datacollector

> 작성: 2026-05-02 | planner
> Hard Constraints 체크: claude-md-constraints 스킬 적용 완료
> 참고 패턴: 05_interactive_cli plan.md (history/)

---

## §1 활성 spec 요약

| 항목 | 내용 |
|---|---|
| spec | `docs/work_flow/specs/06_dgx_absorbs_datacollector.md` |
| 전체 todo | 13개 (L1·L2 / M1·M2·M3 / X1·X2·X3·X4·X5 / V1·V2·V3) |
| 핵심 목표 | DataCollector 별도 노드 폐기 → DGX 가 데이터 수집 + 학습 두 책임 흡수. 3-노드 (devPC + DGX + Orin) 로 재정의 |
| Phase 1 확정 결정 | A~F 6건 (CLAUDE.md 정합, spec 시프트, DGX 직결, 옵션 α 통합 등) Phase 1 완료 |
| Phase 2 미확정 결정 | G (flow mode 라벨), H (flow 7 전송 옵션 재정의), I (pyproject 의존성 추가 — Category B), J (setup_env.sh extras 설치 — Coupled File Rule) |
| 전 사이클 잔재 통합 | 04 BACKLOG #11~#14 + 05 D3·O3·X3 verification_queue → M2 + V 그룹으로 자연 흡수 |
| 참고 | ANOMALIES 05 #1: settings.json permissions.allow 16건 추가 완료 — 06 자동화에서 이전 사이클보다 Bash 도구 접근 환경 개선. ANOMALIES 05 #4: hook 메인 세션 차단 META #9 차기 보류 유지 |

---

## §2 DAG (의존 관계)

### 그룹 L — datacollector 자산 legacy 이관

```
TODO-L1 (task: 기존 legacy/ 8 파일 → 01_pre_subagent_workflow/ 이동)
TODO-L2 (task: datacollector 통째 → 02_datacollector_separate_node/ 이동)
  L1·L2 서로 독립 (병렬 가능)
  단 legacy/README.md 에 두 하위 폴더 색인 포함 — L1 이 README 작성 시 L2 결과도 반영해야
  → 실질 의존: L1 과 L2 동시 dispatch 후, README 최종 작성 시 L2 결과 참조 (순차 권고)
```

### 그룹 M — Plan/Doc 정합 갱신

```
TODO-M1 (task: arm_2week_plan.md 갱신)   [blockedBy: L1·L2 완료]
TODO-M2 (task: BACKLOG.md 정리)          [blockedBy: L1·L2 완료]
TODO-M3 (task: docs/storage/README.md + specs/README.md 정합 갱신)   [blockedBy: L1·L2·M1 완료]
  M1·M2 는 서로 독립 (병렬 가능, L1·L2 완료 후)
  M3 는 M1 후속 의존 (시프트 결정이 README 에 반영되어야)
```

### 그룹 X — DGX 흡수 구현

```
TODO-X1 (study: dgx flow 재설계 — mode.py + 수집 flow 설계 문서화)   [blockedBy: L2 완료]
  X1 은 G·H 사용자 결정 포함 study — 설계 후보 제안 후 awaits_user 발동 가능
  └─→ TODO-X2 (task: dgx/interactive_cli/ mode.py + 수집 flow 이식)   [blockedBy: L2·X1·G·H 결정]
        └─→ TODO-X3 (task: dgx/scripts/ 수집 스크립트 이식)             [blockedBy: L2·X2 완료]
              └─→ TODO-X4 (task: dgx/pyproject.toml extras 추가)        [blockedBy: X3 완료 + I 사용자 동의 awaits_user]
                    └─→ TODO-X5 (task: dgx/scripts/setup_env.sh extras 설치 추가)   [blockedBy: X4 완료]
```

### 그룹 V — Phase 3 사용자 실물 검증

```
TODO-V1 (test: DGX SO-ARM·카메라 직결 하드웨어 검증)   [blockedBy: X4·X5 완료 + DGX 시연장 이동]
  └─→ TODO-V2 (test: dgx/interactive_cli/ 수집 mode flow 0~7 완주)   [blockedBy: V1 완료]
        └─→ TODO-V3 (test: 학습 mode 회귀 검증)                        [blockedBy: V2 완료 (or 독립 HF Hub 데이터셋 활용 가능)]
```

### 그룹 간 의존 요약

```
[L1·L2 병렬]
    └─→ [M1·M2 병렬, M3 sequential after M1]
    └─→ [X1 (awaits_user G·H)] → [X2] → [X3] → [X4 (awaits_user I)] → [X5]
                                                         └─→ [V1 → V2 → V3]

L 그룹과 M·X 그룹은 L 완료 후 M·X 병렬 진입 가능
M 그룹과 X 그룹은 서로 독립 (병렬 가능)
V 그룹은 X4·X5 완료 후 진입 (Phase 3 사용자 실물 검증)
```

---

## §3 병렬 그룹 (Wave)

### Wave 1 — L1·L2 병렬 dispatch (즉시 진입)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-L1 | task | 없음 | `docs/storage/legacy/01_pre_subagent_workflow/` 신규 + 기존 8 파일 git mv. `legacy/README.md` 신규 작성 (02 폴더 색인도 포함 — L2 결과 반영 전 skeleton 또는 L2 완료 후 최종화) |
| TODO-L2 | task | 없음 | `docs/storage/legacy/02_datacollector_separate_node/` 신규 + datacollector 전체 + docs/storage 3 파일 + scripts 3 파일 git mv. `02.../README.md` 신규 작성 |

L1·L2 동시 dispatch 가능. 단 L1 의 `legacy/README.md` 최종 작성 시 L2 산출물 참조 권장 → orchestrator 는 L1·L2 완료 확인 후 README 최종 패치 처리 (또는 L2 먼저 완료 신호 수신 후 L1 README 최종화).

### Wave 2 — M1·M2 병렬 + X1 dispatch (L1·L2 완료 후)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-M1 | task | L1·L2 완료 | `arm_2week_plan.md` 04·05·06~ 마일스톤 갱신 + spec 시프트 반영 |
| TODO-M2 | task | L1·L2 완료 | `BACKLOG.md` 04 #11·#12·#13 + 05 미검증 항목 "완료(불요)" 마킹. #14 유지 |
| TODO-X1 | study | L2 완료 | `docs/storage/14_dgx_cli_flow.md` 학습+수집 통합 flow 설계 문서화. G·H 후보 제안 포함 → awaits_user 트리거 |

M1·M2·X1 세 가지 동시 dispatch 가능. X1 은 L2 완료 직후 진입 가능 (datacollector 자산을 legacy 에서 직접 Read 하기 위해).

### Wave 3 — M3 dispatch (M1 완료 후) + awaits_user G·H 해소 대기

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-M3 | task | L1·L2·M1 완료 | `docs/storage/README.md`, `docs/work_flow/specs/README.md`, `lerobot_upstream_check/README.md` 색인 정합 갱신 |

X1 study 완료 후 orchestrator 가 G·H 사용자 답 수신 → X2 dispatch 조건 충족.
M3 와 X2 는 서로 독립 — 병렬 진행 가능.

### Wave 4 — X2 dispatch (X1 완료 + G·H 결정 후)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X2 | task | L2·X1 완료 + G·H 결정 | `dgx/interactive_cli/flows/mode.py` 신규 + 수집 flow 4종 이식 + `entry.py`·`env_check.py`·`training.py` 수정 + `orin/interactive_cli/flows/entry.py` flow 1 장치 옵션 갱신 |

Category B 비해당 (dgx/lerobot/ 미접촉, pyproject.toml 미접촉). code-tester 1 cycle 자율 진행.

### Wave 5 — X3 dispatch (X2 완료 후)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X3 | task | L2·X2 완료 | `dgx/scripts/` 수집 스크립트 3종 신규 (datacollector/scripts/ 이식 + dgx venv 갱신). `bash -n` + shellcheck 정적 검증 |

Category B 비해당 (`deploy_*.sh` 패턴 아님). code-tester 1 cycle 자율 진행.

### Wave 6 — X4 awaits_user I 해소 후 dispatch

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X4 | task | X3 완료 + I 사용자 동의 | `dgx/pyproject.toml` record + hardware + feetech extras 3종 추가. **Category B 영역 — 사용자 동의 필수 (awaits_user I)**. torchcodec 호환성 사전 grep + uv pip resolve dry-run 결과 보고 후 동의 수신 |

Category B 영역 (dgx/pyproject.toml 의존성 추가). code-tester MAJOR 시 자동 재시도 X — 사용자 보고 게이트.

### Wave 7 — X5 dispatch (X4 완료 후)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X5 | task | X4 완료 | `dgx/scripts/setup_env.sh` extras 설치 step 추가. Coupled File Rule 1 (X4 의존성 결정 반영). `bash -n` + shellcheck 정적 검증 |

Category B 영역 (`dgx/scripts/setup_env.sh`). code-tester MAJOR 시 사용자 보고 게이트.

### Wave 8 — code-tester 검증 (각 task/study 완료 즉시)

| 검증 대상 | 타입 | 선결 | 비고 |
|---|---|---|---|
| code-tester for L1 | task | L1 완료 | git mv 성공, README 정합, 하드코딩 경로 grep 확인 |
| code-tester for L2 | task | L2 완료 | git mv 성공, datacollector 경로 하드코딩 grep, README 정합 |
| code-tester for M1 | task | M1 완료 | arm_2week_plan.md 내용 정합 (역사적 결정 보존 포함) |
| code-tester for M2 | task | M2 완료 | BACKLOG.md 항목 처리 정합 (#14 유지 확인) |
| code-tester for M3 | task | M3 완료 | README 색인 정합 |
| code-tester for X1 | study | X1 완료 | flow 설계 문서 정합, G·H 후보 명시 |
| code-tester for X2 | task | X2 완료 | ruff 린트, import 경로, venv 경로 정합, orin entry.py 갱신 포함 |
| code-tester for X3 | task | X3 완료 | bash -n + shellcheck, dgx venv 경로 정합 |
| code-tester for X4 | task (Category B) | X4 완료 | TOML parse 정합, 충돌 사전 검증 결과 포함. MAJOR 시 사용자 보고 게이트 |
| code-tester for X5 | task (Category B) | X5 완료 | bash -n + shellcheck. MAJOR 시 사용자 보고 게이트 |

### Wave 9 — prod-test V1·V2·V3 (Phase 3 사용자 실물 검증)

| todo | 타입 | 선결 | 비고 |
|---|---|---|---|
| TODO-V1 | test (prod) | X4·X5 code-tester PASS + DGX 시연장 이동 가능 | DGX SO-ARM + 카메라 직결 하드웨어 검증. prod-test-runner DGX SSH 자율 가능 (read-only 확인). dialout 그룹·v4l2 인식은 사용자 실물 필요 |
| TODO-V2 | test (prod) | V1 완료 | 수집 mode flow 0~7 완주. HF Hub push + 로컬 보관 + Orin rsync 3분기 검증 |
| TODO-V3 | test (prod) | V2 완료 (또는 HF Hub 데이터셋 별도 활용 시 독립 가능) | 학습 mode 회귀. 05 X3 NEEDS_USER_VERIFICATION 통합 처리 |

V1·V2·V3 는 순차 (V1 하드웨어 검증 → V2 수집 flow → V3 학습 회귀). V3 는 V2 수집 데이터셋 또는 HF Hub 데이터셋으로 독립 진입 가능.

---

## §4 가정

### 확신 가정 (병렬 진행 OK)

1. `docs/storage/legacy/` 하위 신규 디렉터리 생성은 Category C 비해당 — CLAUDE.md "새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외)" 조건에서 `docs/` 내부는 자유. `docs/storage/legacy/01_*/` 및 `02_*/` 생성 자율 진행 가능
2. `datacollector/` 루트 디렉터리는 `smolVLA/` 직하 (docs/ 외) — git mv 로 `docs/storage/legacy/02_*/` 하위로 이동 시 Category C "새 디렉터리 생성" 은 위에서 자율 처리 가능. 단 `smolVLA/datacollector/` 자체 삭제는 git mv 로 자동 처리되므로 Category D (rm -rf) 비해당
3. `dgx/interactive_cli/flows/` 신규 파일 (mode.py, teleop.py 등) 은 `dgx/` 내부 신규 파일 — Category C "새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외)" 조건 비해당 (dgx/ 내부라 자율 진행)
4. `dgx/scripts/` 신규 스크립트 3종 — 기존 디렉터리 내 신규 파일, Category C 비해당
5. `orin/interactive_cli/flows/entry.py` 수정 — orin/ 내부 기존 파일 수정, Category B·C 비해당
6. DGX SSH `laba@spark-8434` 접근 가능 — 04·05 사이클 반복 확인
7. `docs/storage/legacy/02_.../docs_storage_15_datacollector_cli_flow.md` 에서 X1 study 시 직접 Read 가능 — L2 완료 후 경로 변경됨 (X1 이 L2 의존하는 핵심 이유)
8. `dgx/interactive_cli/` 디렉터리는 05 사이클에서 이미 생성됨 — X2 는 기존 디렉터리 내 파일 신규/수정
9. settings.json permissions.allow 05 wrap 시 16건 추가 완료 — 06 자동화에서 Bash 도구 환경 개선됨 (Bash(ssh datacollector*:*) 포함 — datacollector 관련 권한은 무해, 사용 없음)
10. CLAUDE.md §Hard Constraints Category B 에서 `datacollector/lerobot/` 항목 제거 완료 (Phase 1 결정 E) — 06 plan 에서 datacollector/lerobot/ 고려 불필요

### 확인 필요 가정 (awaits_user)

| # | 관련 todo | 질문 | 영향 |
|---|---|---|---|
| G | TODO-X1 → X2 | flow 3 mode 질문 라벨 확정: "(1) 데이터 수집 / (2) 학습 / (3) 종료" 또는 다른 형식? 재진입(루프) vs 단발 종료? | X2 의 `mode.py` 구조 직결. X1 study 후보 제안 시 사용자 답 필요 |
| H | TODO-X1 → X2 | flow 7 전송 분기 옵션 재정의: "HF Hub / 로컬 dgx 보관 / Orin rsync" 3건 그대로? 다른 구성? | X2 의 `transfer.py` 구조 직결. X1 study 후보 제안 시 사용자 답 필요 |
| I | TODO-X4 | dgx/pyproject.toml 에 record + hardware + feetech extras 추가 동의. torchcodec ≥0.3.0 이 DGX PyTorch 2.10.0+cu130 와 호환되는지 사전 grep + uv pip resolve dry-run 결과 보고 후 동의 필요 | Category B — 사용자 동의 없이 dispatch X. X4·X5 전체 block |

---

## §5 awaits_user 항목 (dispatch 전 사용자 답 받기)

| # | todo | 내용 | 해소 조건 | 해소 전 영향 |
|---|---|---|---|---|
| G | X1 (study 산출물 내) | flow 3 mode 분기 라벨·종료 방식 확정 | X1 study 완료 후 orchestrator 가 후보 제안 → 사용자 답 수신 | X2 dispatch X (mode.py 구조 미확정) |
| H | X1 (study 산출물 내) | flow 7 전송 분기 옵션 재정의 | G 와 동시 수신 가능 | X2 dispatch X (transfer.py 구조 미확정) |
| I | X3 → X4 사이 | dgx/pyproject.toml extras 추가 동의 (torchcodec 호환 결과 보고 필수) | torchcodec 호환 결과 보고 + 사용자 OK | X4·X5 dispatch X |

awaits_user 운영 원칙:
- G·H 는 X1 study 완료 후 동시 사용자 발송 → 한 번의 답으로 두 결정 해소 권장
- I 는 X3 완료 후 task-executor 가 torchcodec 호환 grep 결과 + uv pip resolve dry-run 결과를 orchestrator 에 보고 → orchestrator 가 사용자 발송 → 동의 수신 후 X4 dispatch
- G·H 미해소 동안 M1·M2·M3·L1·L2 는 계속 진행 (독립 그룹)
- I 미해소 동안 V1·V2·V3 는 진입 불가이나 M 그룹은 계속 진행

---

## §6 검증 대기 큐 후보 (Phase 3)

| todo | 검증 방식 | 04·05 BACKLOG 통합 항목 | 비고 |
|---|---|---|---|
| TODO-V1 | 사용자 실물 필수 — DGX 시연장 이동 후 SO-ARM 2대 + 카메라 2대 USB 직결, dialout 그룹 권한 확인, lerobot-find-port + lerobot-find-cameras 비대화형 호출 | 04 BACKLOG #11·#12 (DataCollector 환경) → DGX 직결로 우회. CLAUDE.md 결정 B (DGX SO-ARM 직결 가능) 실 검증 | dialout 그룹 미설정 시 sudo 필요 (Category D — sudo 금지) → 사전 확인 권고 |
| TODO-V2 | 사용자 실물 필수 — `bash dgx/interactive_cli/main.sh` flow 0~7 완주, flow 3 mode = 수집 선택, calibrate·record·transfer 3분기 전체 실 수행 | 04 BACKLOG #12 (calibrate 실 수행), #13 (flow 7 분기), 05 D3 (flow 0~7 완주), 04 BACKLOG #14 (env_check.py NoneType) 진단 포함 | HF Hub push 는 학교 WiFi 차단 가능성 — 다른 네트워크에서 처리 권고 (ANOMALIES 05 #3) |
| TODO-V3 | prod-test-runner DGX SSH 자율 (smoke 부분) + 사용자 실물 (데이터셋 다운 동의·결과 관찰) — `bash dgx/interactive_cli/main.sh` flow 3 mode = 학습 완주, V2 수집 데이터셋 또는 HF Hub 데이터셋 학습 | 05 X3 NEEDS_USER_VERIFICATION (save_dummy_checkpoint + ckpt 케이스 출력), 04 BACKLOG #7 X3·T1·T2 통합 | smoke_test 5~15분 사용자 동의 필요 (>5분 실행). HF Hub 데이터셋 다운로드 >100MB 사용자 동의 필요 |

검증 큐 운영 원칙:
- V1·V2·V3 는 Phase 3 사용자 실물 검증 — prod-test-runner 가 DGX SSH read-only 검증 선행 후 NEEDS_USER_VERIFICATION 발급
- V2 의 flow 7 HF Hub push 는 학교 WiFi 환경에서 실패 가능 (ANOMALIES 05 #3 패턴) — 검증 큐 안내 시 네트워크 조건 명시
- V3 의 smoke_test 는 DGX SSH 자율 가능이나 5~15분 실행 → 사용자 동의 게이트 적용 (CLAUDE.md prod-test-runner 자율성 표)

---

## §7 위험 신호

### ANOMALIES 05 후속 + 본 spec 자체 리스크

| # | 리스크 | 관련 todo | 우선순위 | 사전 조치 권고 |
|---|---|---|---|---|
| R1 | **torchcodec 호환성** — torchcodec ≥0.3.0 이 DGX PyTorch 2.10.0+cu130 와 비호환일 가능성. 비호환 시 record extras 구성 재정의 필요 (feetech·hardware 만 추가, torchcodec 제외) | X4·X5 | 높음 | X3 완료 후 I awaits_user 전 task-executor 가 `dgx/pyproject.toml` + `datacollector/pyproject.toml` torchcodec 버전 grep + PyPI 호환 matrix 확인 후 결과 보고. 비호환 확인 시 extras 에서 torchcodec 조건부 제외 옵션 제시 |
| R2 | **G·H awaits_user 지연 시 X2~X5 전체 block** — X1 study 후 사용자 답 지연 시 DGX 흡수 구현 전체 정지 | X2·X3·X4·X5 | 중간 | X1 study 완료 즉시 G·H 를 한 번에 사용자 발송 (일괄 질문). L·M 그룹은 계속 진행하여 대기 시간 활용 |
| R3 | **orin entry.py 망각 위험** — X2 구현 시 `orin/interactive_cli/flows/entry.py` flow 1 장치 옵션 갱신도 포함해야 하나 누락 가능성 | X2 | 중간 | code-tester X2 DOD 체크리스트에 orin entry.py 갱신 포함 여부 명시 |
| R4 | **datacollector 경로 하드코딩 잔재** — L2 이후 arm_2week_plan / BACKLOG / 기타 docs 에 `smolVLA/datacollector/` 또는 `docs/storage/07/10/15_datacollector_*` 경로가 남을 가능성 | L2·M1·M2·M3 | 중간 | L2 code-tester 가 git 저장소 전체 grep 수행 → 발견 항목을 M1·M2·M3 에 전달 |
| R5 | **ANOMALIES 05 #1 — settings.json permissions.allow 남은 datacollector 권한** — `Bash(ssh datacollector*:*)` 등이 남아 있어도 실사용 X 이므로 무해. 단 사용자 prompt 에서 혼란 가능 | 전체 | 낮음 | 본 spec 진행 중 별도 조치 불필요. wrap-spec 시 reflection 후보로 누적 |
| R6 | **ANOMALIES 05 #4 — hook 메인 세션 차단 META #9 미해결** — 본 spec 에서 Category A 수정 없음이므로 직접 영향 없음. 단 Phase 2 중 reflection 성격 작업이 필요 발생 시 05 와 동일 hook 충돌 재현 가능 | 전체 | 낮음 | 본 spec 에서 Category A 영역 수정 없음 확인됨 (E 결정 Phase 1 시점 완료). META #9 차기 사이클 보류 유지 |
| R7 | **Category B setup_env.sh MAJOR 시 게이트** — X5 가 MAJOR 받으면 자동 재시도 X. orchestrator 가 사용자 보고 후 결정 대기 | X5 | 중간 | X4 의존성 결정 확정 후 X5 구현 진입 (J Coupled File Rule 선결 충족). code-tester X5 MAJOR 기준을 "bash -n 실패 또는 venv 경로 오류" 수준으로 한정 |
| R8 | **V2 flow 7 HF Hub + 학교 WiFi** — ANOMALIES 05 #3 패턴 재현 가능 (huggingface.co timeout). V2 검증 환경을 다른 네트워크로 계획 필요 | V2 | 중간 | Phase 3 진입 시 사용자에게 V2 HF Hub push 항목은 학교 WiFi 외 환경 권고. 로컬 dgx 보관 분기는 학교 WiFi 무관하게 검증 가능 |

---

> 본 plan 은 `/start-spec` 시점 1회 작성. Phase 3 실패 후 todo 추가 또는 사용자 자연어 수정 요청 시 planner 재호출 + overwrite.
