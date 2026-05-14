# Execution Plan — 07_e2e_pilot_and_cleanup

> 작성: 2026-05-03 | planner

---

## 경로 불일치 사전 정정 메모

spec 작성 시점 가정과 실제 코드베이스 불일치 발견 (task-executor 진입 전 차단):

| todo | spec 기재 경로 | 실제 경로 | 처리 |
|---|---|---|---|
| W1 | `.claude/skills/lerobot-reference-usage/SKILL.md` L111 을 구 경로에서 신규 경로로 갱신 필요 | L111 이미 `legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 로 올바르게 갱신되어 있음 (06 wrap 적용) | **W1 실질 작업 없음** — task-executor 가 Read 후 확인, DOD 달성 확인으로 완료 처리 |
| O5 | `orin/examples/tutorial/smolvla/inference_baseline.py` | `orin/tests/inference_baseline.py` | task-executor 가 올바른 경로(`orin/tests/inference_baseline.py`)로 작업 |
| W2 | `docs/storage/lerobot_upstream_check/README.md` 또는 `00_*` 에 색인 등록 | 해당 디렉터리에 README.md·00_* 없음. `99_lerobot_upstream_Tracking.md` 존재 | task-executor 가 `99_lerobot_upstream_Tracking.md` 를 색인 역할 파일로 판단, 04_dgx·05_datacollector diff 미등록 항목 추가 또는 미등록 사유 명시 |
| P4 | `docs/work_flow/specs/README.md` L107~122 갱신 | 현재 06 기준 표 (07 시프트 미반영 상태) | 정상 — 본 todo 작업 대상 맞음 |
| O2 | `orin/scripts/run_python.sh` | 미존재 | 정상 — 신규 작성 대상 |
| W4 | `docs/storage/15_orin_config_policy.md` | 미존재 | 정상 — 신규 작성 대상 |

---

## DAG / Wave 구조

```
[Wave 1 — P 그룹, 5 todo, 모두 병렬]
  P1  P2  P3  P4  P5
   \   \   \   \   \
    └───┴───┴───┴───┘
            ↓
     Wave 1 모두 PASS
            ↓
[Wave 2 — D 그룹, 3 todo, 모두 병렬]
  D1      D2      D3
   \       \       \
    └───────┴───────┘
            ↓
     Wave 2 모두 PASS → Phase 3 게이트 1 (사용자 /verify-result "D 분기")
            ↓
[Wave 3 — T 그룹, 3 todo, 순차 의존]
  T1 → T2 → T3
            ↓
     Wave 3 모두 PASS → Phase 3 게이트 2 (사용자 /verify-result "T 분기")
            ↓
[Wave 4 — O 그룹, 5 todo, O1~O4 병렬 + O5 는 O2·T3 의존]
  O1   O2   O3   O4
   \    \    \    \
    └────┴────┴────┘
         ↓ (O2 PASS + T3 PASS 확보 후)
        O5
            ↓
     Wave 4 모두 PASS → Phase 3 게이트 3 (사용자 /verify-result "O 분기")
            ↓
[Wave 5 — W 그룹, 5 todo, W1~W4 병렬 + W5 는 전체 완료 후 마지막]
  W1   W2   W3   W4
   \    \    \    \
    └────┴────┴────┘
            ↓ (W1~W4 + 모든 이전 wave 완료 후)
           W5
            ↓
     /wrap-spec
```

Wave 간 직렬 원칙: 이전 Wave 의 모든 todo verdict `AUTOMATED_PASS` 또는 `NEEDS_USER_VERIFICATION` (게이트 통과 포함) 시 다음 Wave 진입. D Wave 에서 MAJOR 미해결 시 T Wave 시작 X.

---

## 병렬 그룹

### Wave 1 — P 그룹 (동시 실행 가능 5 todo)

| todo | 작업 요약 | 영향 파일 |
|---|---|---|
| P1 | `scripts/dev-connect.sh` L4 datacollector 라인 제거 | `scripts/dev-connect.sh` |
| P2 | `.gitignore` L6·L10 datacollector 패턴 제거 (Category B 동의 완료) | `.gitignore` |
| P3 | `arm_2week_plan.md` 07 시프트 + 신규 항목 추가 | `arm_2week_plan.md` |
| P4 | `docs/work_flow/specs/README.md` 활성 spec 번호 표 갱신 | `docs/work_flow/specs/README.md` |
| P5 | 활성 영역 datacollector 잔재 grep 종합 + 제거 | 발견된 잔재 파일들 (다수 가능) |

영향 파일 중복 없음 — 5 todo 완전 병렬 가능.

### Wave 2 — D 그룹 (동시 실행 가능 3 todo)

| todo | 작업 요약 | 영향 파일 |
|---|---|---|
| D1 | `dgx/interactive_cli/` 수집 mode SSH_AUTO 검증 + 도구 정비 | `dgx/interactive_cli/flows/*.py` (필요 시 패치) |
| D2 | `dgx/interactive_cli/` 학습 mode 회귀 검증 | `dgx/interactive_cli/flows/training.py` (필요 시 패치) |
| D3 | `dgx/scripts/check_hardware.sh` 도구 정합 정적 검증 | `dgx/scripts/check_hardware.sh` (필요 시 패치) |

D2 는 HF Hub 의존 부분 (svla_so100_pickplace 다운로드) 을 T1 의존으로 두고, 해당 부분 제외하고 진행 가능. D1·D2·D3 완전 병렬.

### Wave 3 — T 그룹 (순차 의존)

| todo | 작업 요약 | 선결 조건 |
|---|---|---|
| T1 | DGX HF Hub 다운로드 검증 (`lerobot/svla_so100_pickplace`) | Wave 2 완료 |
| T2 | DGX fine-tune 1 회 완주 (`--steps=2000`) + ollama 사전 체크 | T1 PASS |
| T3 | `scripts/sync_ckpt_dgx_to_orin.sh` 실 실행 검증 + BACKLOG #4 갱신 | T2 PASS (산출물 의존) |

T2 는 1.5~3 시간 소요 — prod-test-runner 비대화형 장기 실행 또는 백그라운드 실행 후 결과 확인 패턴 적용.

T1 학교 WiFi 차단 시: FAIL 보고 + spec 일시 보류 (사용자 결정 G-a). T1 FAIL 이면 T2·T3 dispatch X.

### Wave 4 — O 그룹 (O1~O4 병렬, O5 후발)

| todo | 작업 요약 | 선결 조건 |
|---|---|---|
| O1 | `orin/interactive_cli/` flow 0~5 SSH_AUTO 검증 + 도구 정비 | Wave 3 완료 |
| O2 | `orin/scripts/run_python.sh` 신규 + settings.json 화이트리스트 (Category A, 패턴 I) | Wave 3 완료 |
| O3 | `orin/scripts/setup_env.sh` 정비 — torchvision wheel 자동 설치 + dpkg 체크 (Category B) | Wave 3 완료 |
| O4 | `orin/inference/hil_inference.py` 카메라 인덱스/wrist flip 도구 정비 | Wave 3 완료 |
| O5 | Orin 사전학습 ckpt 로드 + 더미 obs forward 검증 | **O2 PASS** + **T3 PASS** |

O1·O2·O3·O4 는 동시 실행. O5 는 O2 wrapper 의존이므로 O2 PASS 확인 후 dispatch.

### Wave 5 — W 그룹 (W1~W4 병렬, W5 마지막)

| todo | 작업 요약 | 선결 조건 |
|---|---|---|
| W1 | SKILL.md L111 경로 확인 (실제로는 이미 갱신됨 — Read 후 확인 완료 처리) | Wave 4 완료 |
| W2 | `docs/storage/lerobot_upstream_check/` 색인 갱신 (`99_lerobot_upstream_Tracking.md` 대상) | Wave 4 완료 |
| W3 | upstream 동기화 entrypoint 정리 절차 명문화 (Category A 영역 변경 시 패턴 I, 또는 storage 문서) | Wave 4 완료 |
| W4 | `orin/config/ports.json`·`cameras.json` git 추적 정책 결정 + 정책 문서 신규 작성 | Wave 4 완료 |
| W5 | 사이클 중 자연 처리된 모든 BACKLOG 항목 일괄 마킹·정리 | **P~O + W1~W4 모두 완료** |

---

## 확신 가정 (병렬 진행 OK)

1. **P 그룹 파일 존재**: `scripts/dev-connect.sh`, `.gitignore`, `arm_2week_plan.md`, `docs/work_flow/specs/README.md` 모두 실존 확인. P1~P4 실행 가능.
2. **P2 Category B 동의 완료**: 사용자 결정 E — `.gitignore` L6·L10 패턴 제거 사전 동의. 별도 awaits_user 불요.
3. **D3 정적 검증 전제**: `dgx/scripts/check_hardware.sh` 실존 확인. bash -n + shellcheck 자율 가능.
4. **T3 대상 스크립트 존재**: `scripts/sync_ckpt_dgx_to_orin.sh` 실존 확인. dry-run 자율 가능.
5. **O3 Category B 사전 동의**: spec 합의로 setup_env.sh 한 번 작성 OK. code-tester MAJOR 시 자동 재시도 X (사용자 보고).
6. **O4 PHYS_REQUIRED 부분 BACKLOG 처리**: 실 카메라 검증 없이 argparse/README 정비만으로 DOD 달성 가능.
7. **O5 fallback ckpt**: T3 실패 시 `lerobot/smolvla_base` 으로 fallback 가능 — HF Hub 접근 가능하다면.
8. **W1 실질 작업 없음**: L111 이미 올바른 경로로 갱신됨 (06 wrap 시 적용). Read 확인 후 완료 처리.
9. **W2 색인 파일**: `99_lerobot_upstream_Tracking.md` 가 색인 역할 대행 — `04_dgx_lerobot_diff.md`, `05_datacollector_lerobot_diff.md` 등록 추가.
10. **orin 3-노드 구성 안정**: devPC + DGX SSH + Orin SSH 경로 정상 가정 (직전 사이클 정상 운영 확인).
11. **DGX 디스크 공간 충분**: 06 기준 3.3 TB 여유 — T1 다운로드 (~100MB) + T2 학습 산출물 수용 가능.

---

## 확인 필요 가정 (awaits_user)

### 추가 사용자 결정이 필요한 항목 분석

Phase 1 합의 (결정 A~J) 에서 10건 모두 결정 완료. 다음 항목들이 추가 awaits_user 해당 여부 검토:

| todo | 검토 대상 | 판단 | 이유 |
|---|---|---|---|
| O2 | settings.json Category A 변경 — 패턴 I (hook matcher 임시 비활성화 → 메인 적용 → 복원) | **awaits_user X** — 단 **메인 Claude 직접 실행 필수** | 결정 I 에서 패턴 I 자동 진행 승인. 단 워커 dispatch X, 메인이 직접 수행 (Category A). orchestrator 가 O2 실행 시 패턴 I 직접 처리 |
| W1 | Category A (SKILL.md) — 그러나 실제 작업 없음 | **awaits_user X** | 실존 파일 L111 이미 갱신됨. Read 확인만 필요 |
| W3 | Category A 변경 시 (lerobot-upstream-check SKILL.md) 또는 storage 문서 | **분기 선택 필요** | storage 문서 선택 시 Category A 불요 → 자율. SKILL.md 선택 시 패턴 I 필요. task-executor 가 storage 문서 우선 선택 권장 — 단 메인이 선택 확인 필요 |
| W4 | .gitignore 변경 시 Category B | **awaits_user 조건부** | ports.json·cameras.json 정책이 "gitignore 추가" 방향으로 결정되면 Category B 변경 발생 → 사용자 동의 필요. "git 추적 유지" 결정이면 Category B 불요. task-executor 가 정책 결정 후 gitignore 변경 필요 시 orchestrator 에 보고 |
| T2 | 1.5~3 시간 장기 실행 (>5분) | **awaits_user 조건부** | CLAUDE.md prod-test-runner 자율성 표 — "긴 실행 (>5분) 사용자 동의". T2 는 최소 1.5 시간. 사용자 동의 필요 |
| T1 | HF Hub 차단 시 spec 일시 보류 | **T1 FAIL 시 즉시 사용자 보고** | 결정 G-a: 다른 네트워크 재개. 차단 확인 즉시 orchestrator 가 사용자 보고 + Phase 2 정지 |

### 요약 테이블 — 추가 awaits_user 항목

| # | todo | 질문 | 영향 |
|---|---|---|---|
| 1 | T2 | prod-test-runner 장기 실행 동의 — DGX fine-tune 1.5~3 시간 (`--steps=2000`) 비대화형 백그라운드 실행 OK? | T2·T3 dispatch 진입 (T1 PASS 후) |
| 2 | W3 | `04 BACKLOG #1` 절차 명문화 위치 — `.claude/skills/lerobot-upstream-check/SKILL.md` (Category A 패턴 I) vs `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` (Category B X) ? | W3 task-executor 구현 방향 |
| 3 | W4 | `orin/config/ports.json`·`cameras.json` git 추적 정책 결정 — (a) git 추적 유지 + 정책 문서만 신규 작성 / (b) `.gitignore` 에 추가 (Category B 동의 필요) | W4 완료 후 .gitignore 변경 여부 |

**O2 (settings.json 화이트리스트)**: 사용자 동의 불요 (결정 I 완료). 단 orchestrator 가 패턴 I 직접 수행. 워커 dispatch X.

---

## Phase 3 검증 큐 후보

verification_queue.md 를 D / T / O 3 그룹으로 분리 구성 (게이트 3 회 대비).

### 게이트 1 — D 그룹 (Wave 2 종료 후)

| todo | 항목 | 환경 레벨 | 검증 방식 |
|---|---|---|---|
| D1 | `dgx/interactive_cli/` flow 0~2 SSH 비대화형 smoke | `SSH_AUTO` | prod-test-runner ssh dgx `python3 -m py_compile *.py` + flow 0~2 비대화형 인자 실행 PASS |
| D1 | flow 3~7 정적 (py_compile·ruff·bash -n) | `AUTO_LOCAL` | devPC 로컬 ruff·py_compile PASS |
| D1 | SO-ARM 직결 calibrate·record 실물 검증 | `PHYS_REQUIRED` | 시연장 이동 시 SO-ARM 직결 후 실행 — 본 사이클 BACKLOG 유지 |
| D2 | preflight·smoke_test·save_dummy_checkpoint SSH 검증 | `SSH_AUTO` | prod-test-runner ssh dgx — DGX 가용 시 5~15분 smoke |
| D2 | ckpt 케이스 4건 코드 분기 정합 | `AUTO_LOCAL` | devPC 정적 코드 분기 확인 |
| D3 | `check_hardware.sh` bash -n + shellcheck | `AUTO_LOCAL` | devPC 로컬 정적 검증 PASS |
| D3 | SO-ARM·카메라 직결 5-step 실물 검증 | `PHYS_REQUIRED` | 시연장 이동 시 — 본 사이클 BACKLOG 유지 |

**게이트 1 통과 조건**: SSH_AUTO + AUTO_LOCAL 항목 모두 AUTOMATED_PASS. PHYS_REQUIRED 항목 BACKLOG 마킹.

### 게이트 2 — T 그룹 (Wave 3 종료 후)

| todo | 항목 | 환경 레벨 | 검증 방식 |
|---|---|---|---|
| T1 | HF Hub 다운로드 성공 여부 + 캐시 경로·크기 보고 | `SSH_AUTO` | prod-test-runner ssh dgx `huggingface-cli download lerobot/svla_so100_pickplace` PASS |
| T2 | fine-tune 완주 — checkpoint/{001000,002000,last} 존재 확인 | `SSH_AUTO` | prod-test-runner ssh dgx ls 확인 (학습은 백그라운드) |
| T2 | ollama 사전 체크 절차 문서화 | `AUTO_LOCAL` | devPC 코드 패치 + BACKLOG #5 갱신 확인 |
| T3 | sync_ckpt dry-run + 실 실행 safetensors 헤더 검증 | `SSH_AUTO` | prod-test-runner devPC→DGX→Orin rsync PASS + 헤더 8 byte 확인 |

**게이트 2 통과 조건**: T1 PASS (HF Hub 접근 가능 전제). T2 1.5~3시간 완주 확인. T3 safetensors 헤더 검증.

T1 학교 WiFi 차단 시: 게이트 2 진입 불가 → spec 일시 보류 (결정 G-a). 메인이 사용자 보고 + 다른 네트워크 재개 대기.

### 게이트 3 — O 그룹 (Wave 4 종료 후)

| todo | 항목 | 환경 레벨 | 검증 방식 |
|---|---|---|---|
| O1 | `orin/interactive_cli/` flow 0~5 SSH 비대화형 검증 | `SSH_AUTO` | prod-test-runner ssh orin py_compile + flow 0~2 비대화형 PASS |
| O1 | hil_inference 50-step SO-ARM 직결 검증 | `PHYS_REQUIRED` | 시연장 이동 시 — 본 사이클 BACKLOG 유지 |
| O2 | `run_python.sh` wrapper 동작 확인 | `SSH_AUTO` | prod-test-runner ssh orin `~/smolvla/orin/scripts/run_python.sh -c 'import torch; print(torch.cuda.is_available())'` PASS (cuSPARSELt ImportError X) |
| O3 | `setup_env.sh` bash -n + dry-run | `AUTO_LOCAL` | devPC bash -n PASS |
| O4 | `hil_inference.py` argparse 검증 | `AUTO_LOCAL` | devPC python -m py_compile + argparse PASS |
| O5 | 더미 obs forward 1 회 — exit 0 + action shape `(1, 6)` | `SSH_AUTO` | prod-test-runner ssh orin `run_python.sh orin/tests/inference_baseline.py --ckpt <path>` PASS |
| O5 | SO-ARM 직결 hil_inference 50-step | `PHYS_REQUIRED` | 시연장 이동 시 — 본 사이클 BACKLOG 유지 |

**게이트 3 통과 조건**: SSH_AUTO + AUTO_LOCAL 항목 모두 AUTOMATED_PASS. PHYS_REQUIRED 항목 BACKLOG 마킹. 특히 O2 wrapper PASS 가 O5 선결 조건.

---

## dispatch 순서 — 구체

### Wave 1 (동시 dispatch)

```
task-executor: P1  (scripts/dev-connect.sh L4 제거)
task-executor: P2  (Category B — .gitignore 패턴 제거)
task-executor: P3  (arm_2week_plan.md 07 시프트)
task-executor: P4  (docs/work_flow/specs/README.md 갱신)
task-executor: P5  (활성 영역 datacollector 잔재 grep + 제거)

→ 각 code-tester 순차 (각 task 완료 후)
→ P5 타입 both: code-tester PASS 후 prod-test-runner 자율 grep 검증
→ 5건 모두 PASS → Wave 2 진입
```

### Wave 2 (동시 dispatch)

```
task-executor: D1  (dgx interactive_cli 수집 mode 도구 정비)
task-executor: D2  (dgx interactive_cli 학습 mode 회귀 검증 — HF Hub 부분 보류)
task-executor: D3  (check_hardware.sh 도구 정합 정적 검증)

→ D1: code-tester → prod-test-runner ssh dgx (SSH_AUTO + AUTO_LOCAL)
→ D2: code-tester → prod-test-runner ssh dgx (smoke_test 5~15분 — DGX 가용 시)
→ D3: code-tester (bash -n + shellcheck)
→ 3건 모두 PASS → verification_queue.md D 그룹 섹션 작성
→ orchestrator 가 사용자에게 게이트 1 /verify-result 요청
→ 사용자 /verify-result "D 분기 통과" → Wave 3 진입
```

### Wave 3 (순차 dispatch)

```
[T1 먼저]
prod-test-runner: T1  (ssh dgx huggingface-cli download 시도)
  → PASS: Wave 3 계속
  → FAIL (학교 WiFi 차단): orchestrator 사용자 보고 + spec 일시 보류

[T1 PASS 후]
prod-test-runner: T2  (ssh dgx lerobot-train --steps=2000)
  ※ 장기 실행 (1.5~3시간) — 사용자 동의 확인 (awaits_user #1) 후 dispatch
  → 백그라운드 실행 또는 비대화형 모니터링
  → PASS: checkpoint/{001000,002000,last} 존재 확인

[T2 PASS 후]
task-executor + prod-test-runner: T3  (sync_ckpt_dgx_to_orin.sh dry-run + 실 실행)
  → PASS: safetensors 헤더 검증 + BACKLOG #4 갱신

→ 3건 모두 PASS → verification_queue.md T 그룹 섹션 작성
→ orchestrator 가 사용자에게 게이트 2 /verify-result 요청
→ 사용자 /verify-result "T 분기 통과" → Wave 4 진입
```

### Wave 4 (O1~O4 동시, O5 후발)

```
[O1~O4 동시 dispatch]
task-executor: O1  (orin interactive_cli flow 0~5 SSH_AUTO 검증 + 도구 정비)
orchestrator:  O2  (패턴 I 직접 실행 — run_python.sh 신규 + settings.json 화이트리스트)
               ※ O2 는 워커 dispatch X. orchestrator 가 hook matcher 임시 비활성화 → 직접 Write → 복원
task-executor: O3  (setup_env.sh Category B 정비)
task-executor: O4  (hil_inference.py 카메라 도구 정비)

→ O1: code-tester → prod-test-runner ssh orin
→ O2: 메인 직접 처리 (패턴 I) → 검증: ssh orin run_python.sh -c 'import torch; ...' PASS
→ O3: code-tester (bash -n)
→ O4: code-tester (py_compile + argparse)

[O2 PASS + T3 PASS 확인 후]
task-executor: O5  (orin/tests/inference_baseline.py 확장 + 더미 obs forward 검증)
               ※ O5 대상 경로: orin/tests/inference_baseline.py (spec 기재 orin/examples/... 는 오기재)
  → prod-test-runner ssh orin run_python.sh orin/tests/inference_baseline.py --ckpt <path>

→ 5건 모두 PASS → verification_queue.md O 그룹 섹션 작성
→ orchestrator 가 사용자에게 게이트 3 /verify-result 요청
→ 사용자 /verify-result "O 분기 통과" → Wave 5 진입
```

### Wave 5 (W1~W4 동시, W5 마지막)

```
[W1~W4 동시 dispatch]
task-executor: W1  (SKILL.md L111 Read 확인 → 이미 갱신됨 확인 후 완료 처리)
               ※ Category A 이지만 실작업 없음 — Read 후 "이미 올바름" 보고로 DOD 달성
task-executor: W2  (docs/storage/lerobot_upstream_check/99_lerobot_upstream_Tracking.md 색인 갱신)
task-executor: W3  (사용자 결정 awaits_user #2 답 받은 후 dispatch)
               - storage 문서 선택 시: docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md 에 절차 추가
               - SKILL.md 선택 시: 패턴 I (orchestrator 직접)
task-executor: W4  (orin/config 정책 결정 + docs/storage/15_orin_config_policy.md 신규 작성)
               ※ .gitignore 변경 시 awaits_user #3 답 확인 후 Category B 처리

[W1~W4 모두 PASS 후]
task-executor: W5  (BACKLOG.md 일괄 마킹·정리)
  → 흡수 대상: 06 V1·V2·V3 도구 정비분 / 06 #4 / 03 #14·#15·#16 / 02 #5·#7·#8 / 04 #1·#3 / 05 O3·X3 / 06 #6·#7
  → code-tester BACKLOG 일관성 검토
  → 완료 → /wrap-spec 준비
```

---

## 특수 처리 항목 요약

### O2 — Category A 패턴 I (orchestrator 직접 실행)

1. orchestrator 가 `.claude/settings.json` 의 hook matcher 를 임시 비활성화 (`Write|Edit` → `NEVER_MATCH`)
2. orchestrator 가 `orin/scripts/run_python.sh` 신규 작성 (직접 Write)
3. orchestrator 가 `.claude/settings.json` permissions.allow 에 wrapper 호출 패턴 추가 (직접 Edit)
4. orchestrator 가 hook matcher 복원
5. prod-test-runner 가 ssh orin 비대화형 wrapper 검증

워커 dispatch 금지 (Category A). ANOMALIES HOOK_BLOCK 차단 방지.

### T1 WiFi 차단 fallback

- T1 FAIL (학교 WiFi HF Hub 차단) 시: orchestrator 가 즉시 사용자 보고
- Phase 2 T2·T3 dispatch 정지
- 사용자 결정 G-a: 다른 네트워크 (집·핫스팟) 이동 후 재개
- 재개 시 T1 부터 재시작

### T2 장기 실행 동의

- CLAUDE.md prod-test-runner 자율성: "긴 실행 (>5분) 사용자 동의"
- T2 dispatch 전 orchestrator 가 사용자에게 동의 요청 (awaits_user #1)
- 동의 후 prod-test-runner 비대화형 백그라운드 실행

---

## awaits_user 항목 일람 (메인이 사용자 일괄 질문용)

Phase 2 dispatch 시작 전 또는 해당 Wave 진입 전 메인이 사용자에게 확인해야 할 항목:

### [시작 전 확인] — Wave 5 진입 전까지 필요한 결정 2건

**질문 1 (W3 관련 — Wave 5 진입 전)**

`04 BACKLOG #1` "upstream 동기화 시 entrypoint 정리 절차" 명문화 위치를 결정해 주세요.

- **(a) storage 문서** — `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 에 절차 추가 (Category A 불요, 자율 dispatch 가능)
- **(b) SKILL.md** — `.claude/skills/lerobot-upstream-check/SKILL.md` 갱신 (Category A — 패턴 I, orchestrator 직접)

권장: (a) — 자율화 가능, 효과 동일.

**질문 2 (W4 관련 — Wave 5 진입 전)**

`orin/config/ports.json`·`cameras.json` git 추적 정책을 결정해 주세요.

- **(a) git 추적 유지** — 정책 문서 `docs/storage/15_orin_config_policy.md` 신규 작성만, .gitignore 변경 X
- **(b) .gitignore 추가** — 시스템별 환경 파일이므로 gitignore 처리. Category B (.gitignore 변경) 동의 필요

### [T2 dispatch 전 — Wave 3 T1 PASS 후] — 동의 1건

**동의 1 (T2 관련)**

DGX 에서 smolVLA fine-tune 장기 실행 (예상 1.5~3시간) 을 비대화형 백그라운드로 실행해도 됩니까?

- lerobot-train `--steps=2000 --save_freq=1000 --batch_size=8`
- DGX Walking RL 동시 실행 여부 사전 확인 권장 (메모리 경합)
- **(a) OK** — prod-test-runner 백그라운드 실행 후 완료 확인
- **(b) 직접 실행** — 사용자가 DGX 에서 직접 실행, 완료 후 `/verify-result "T2 완료"` 입력

---

## 사용자 결정 반영 (2026-05-03 — awaits_user 3건 모두 위임)

사용자 답: "위임할게" → 메인이 default 적용:

| awaits_user | 결정 | 처리 |
|---|---|---|
| 질문 1 (W3) | **(a) storage 문서** — `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 에 절차 추가. Category A 회피 → 자율 dispatch | W3 task-executor 자율 진행 |
| 질문 2 (W4) | **(a) git 추적 유지** + 정책 문서 신규 (`docs/storage/15_orin_config_policy.md`). `.gitignore` 변경 X → Category B 회피 | W4 task-executor 자율 진행 |
| 동의 1 (T2) | **(a) prod-test-runner 백그라운드 실행** — DGX fine-tune 1.5~3시간 비대화형 | T2 dispatch 시 사용자 추가 동의 불요, 백그라운드 모드 진행 |

→ 모든 awaits_user 해소. Wave 1~5 자율 dispatch 가능.
