# Execution Plan — 05_interactive_cli

> 작성: 2026-05-01 | planner
> Hard Constraints 체크: claude-md-constraints 스킬 적용 완료
> 레퍼런스 활용 의무: lerobot-reference-usage 스킬 적용 완료

---

## §1 사이클 메타

| 항목 | 내용 |
|---|---|
| spec | `docs/work_flow/specs/05_interactive_cli.md` |
| 전체 todo | 11개 (F1·F2 / D1·D2·D3 / O1·O2·O3 / X1·X2·X3) |
| 활성 todo | 11개 (전부 미착수) |
| 진입 시각 | 2026-05-01 |
| 전 사이클 잔재 | BACKLOG #7·#8·#9 — 본 spec D3·O3·X3 prod 에 자연 통합 |
| 참고 | `datacollector/` 디렉터리 이미 존재 (04 D1·D2 산출물). `orin/`·`dgx/` 구조 정리 완료. `bash -n` / `shellcheck` settings.json 화이트리스트 추가됨 (04 wrap) |

---

## §2 DAG (의존 관계)

### 그룹 F — 공통 framework boilerplate

```
TODO-F1 (study: main.sh + flows/entry.py boilerplate 정의)
  └─→ TODO-F2 (task: 3 노드에 동일 복사 + configs/ 분리)   [blockedBy: F1]
```

- F1 은 선결 의존 없음 (즉시 진입)
- F2 는 F1 산출물 (`docs/storage/12_interactive_cli_framework.md`) 필수
- F2 는 `orin/interactive_cli/`, `dgx/interactive_cli/`, `datacollector/interactive_cli/` 3개 신규 디렉터리 생성 포함

### 그룹 D — DataCollector (사용자 우선)

```
TODO-D1 (study: flow 2~7 정의 + 5단계 옵션 제안)   [blockedBy: F1 권장, F2 필수 아님]
  └─→ TODO-D2 (task: flow 2~7 구현)                [blockedBy: F1·F2·D1]
        └─→ TODO-D3 (test: prod 검증)               [blockedBy: D2 + DataCollector 실물]
```

- D1 의 study 진입은 F1 완료 전에도 레퍼런스 Read 시작 가능 (독립 study — lerobot_study/ Read 는 F1 무관)
  단 최종 산출물 (`docs/storage/15_datacollector_cli_flow.md`) 완성은 F1 참조 후 권장
- D1 의 5단계 옵션은 `docs/lerobot_study/` 전체 Read 후 task-executor 가 후보 5개 이하 제안 → awaits_user (사용자 합의 필요)
- D2 는 F1·F2·D1 모두 완료 후 (boilerplate 복사 전제 + D1 옵션 확정 전제)
- D3 는 DataCollector 머신 실물 + 04 BACKLOG #7 DataCollector 셋업 16단계 완료 전제 → NEEDS_USER_VERIFICATION 정상

### 그룹 O — Orin (추론 책임)

```
TODO-O1 (study: flow 3~ 단계 정의)   [blockedBy: F1 권장]
  └─→ TODO-O2 (task: flow 3~ 구현)   [blockedBy: F1·F2·O1]
        └─→ TODO-O3 (test: prod 검증) [blockedBy: O2 + Orin 실물 + 04 G2 verification_queue 처리]
```

- O1 의 study 진입은 F1 완료 전에도 기존 레퍼런스 Read 시작 가능 (hil_inference.py 등)
- O1 의 flow 3~ 구체 단계 결정은 awaits_user (task-executor 후보 제안 후 사용자 합의 필요)
- O3 는 Orin SSH + 카메라 2대 + SO-ARM follower 실물 필요 → NEEDS_USER_VERIFICATION 정상

### 그룹 X — DGX (학습 책임)

```
TODO-X1 (study: flow 3~ 단계 정의)   [blockedBy: F1 권장]
  └─→ TODO-X2 (task: flow 3~ 구현)   [blockedBy: F1·F2·X1]
        └─→ TODO-X3 (test: prod 검증) [blockedBy: X2]
```

- X1 의 study 진입은 F1 완료 전에도 기존 레퍼런스 Read 시작 가능
- X1 의 flow 3~ 구체 단계 결정은 awaits_user (task-executor 후보 제안 후 사용자 합의 필요)
- X3 는 DGX SSH 자율 접근 가능하나 smoke_test 5~15분 사용자 동의 + 데이터셋 다운로드 포함 → NEEDS_USER_VERIFICATION 정상

### 그룹 간 의존 요약

```
[F1 → F2]                          모든 그룹의 선결 (F2 완료 후 구현 진입)

[F1·F2·D1(awaits_user) → D2 → D3]   D1 awaits_user 로 D2 block
[F1·F2·O1(awaits_user) → O2 → O3]   O1 awaits_user 로 O2 block
[F1·F2·X1(awaits_user) → X2 → X3]   X1 awaits_user 로 X2 block

D1·O1·X1 은 서로 독립 (병렬 study 가능)
D2·O2·X2 는 서로 독립 (병렬 task 가능, 각 awaits_user 해소 조건)
D3·O3·X3 는 서로 독립 (병렬 prod 가능, 각 실물 조건 별도)
```

---

## §3 병렬 그룹 (Wave)

### Wave 0 — awaits_user 질문 준비 (F1 dispatch 동시 시작)

orchestrator 가 Wave 1 시작과 동시에 D1·O1·X1 study 를 dispatch. study 완료 시 task-executor 가 후보를 제안하면 orchestrator 가 사용자에게 일괄 발송. F1 완료 전 준비 단계.

### Wave 1 — F1 즉시 dispatch

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-F1 | study | 없음 | `docs/storage/12_interactive_cli_framework.md` 작성. 04 G1 bash·python 혼합 패턴 직접 Read + 인용 |

단독 dispatch. F1 완료가 이후 모든 그룹의 선결.

### Wave 2 — F1 완료 후 병렬 dispatch (4개 동시)

| todo | 타입 | 선결 조건 | 병렬 여부 |
|---|---|---|---|
| TODO-F2 | task | F1 완료 | D1·O1·X1 과 병렬 가능 |
| TODO-D1 | study | F1 완료 | O1·X1 과 병렬, awaits_user 포함 |
| TODO-O1 | study | F1 완료 | D1·X1 과 병렬, awaits_user 포함 |
| TODO-X1 | study | F1 완료 | D1·O1 과 병렬, awaits_user 포함 |

F2·D1·O1·X1 동시 4개 dispatch 가능.
- F2: 3 노드에 boilerplate 파일 실제 생성 (Category C 동의 이미 충족)
- D1·O1·X1: 각 노드 flow 후반부 정의 study. task-executor 가 study 완료 시 awaits_user 후보 포함하여 제안

### Wave 3 — awaits_user 해소 후 구현 dispatch (D·O·X 독립 진행)

각 study 의 awaits_user 가 사용자 답으로 해소되는 즉시 해당 구현 todo unblock. 서로 독립이므로 순서 무관.

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-D2 | task | F1·F2·D1 완료 + D1 awaits_user 해소 | datacollector flow 2~7 구현 (env_check·teleop·data_kind·record·transfer) |
| TODO-O2 | task | F1·F2·O1 완료 + O1 awaits_user 해소 | orin 추론 flow 구현 |
| TODO-X2 | task | F1·F2·X1 완료 + X1 awaits_user 해소 | dgx 학습 flow 구현 |

D2·O2·X2 는 서로 독립 — 각 awaits_user 해소 즉시 개별 dispatch (3개 동시 가능).

### Wave 4 — code-tester 검증 (Wave 2·3 각 완료 후 바로)

| 검증 대상 | 선결 | 비고 |
|---|---|---|
| code-tester for F1 | F1 완료 | study 타입 |
| code-tester for F2 | F2 완료 | task 타입 — bash + python 파일 정적 분석 (`bash -n`, `shellcheck`) |
| code-tester for D1·O1·X1 | 각 study 완료 | study 타입 |
| code-tester for D2·O2·X2 | 각 task 완료 | task 타입 — lerobot-reference-usage 인용 체크 포함 |

### Wave 5 — prod 검증 (각 code-tester PASS 후, 실물 조건별 독립)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-D3 | test | D2 code-tester PASS + DataCollector 실물 셋업 | 04 BACKLOG #7·#8·#9 통합 |
| TODO-O3 | test | O2 code-tester PASS + Orin 실물 | 04 G2 verification_queue 통합 |
| TODO-X3 | test | X2 code-tester PASS | DGX SSH 자율 가능 (smoke_test 사용자 동의 필요) |

D3·O3·X3 는 서로 독립 — 각 실물 조건 충족 즉시 개별 dispatch 가능.
DataCollector 실물 미셋업 시 D3 진입 불가이나 O3·X3 는 계속 진행.

---

## §4 확신 가정 (병렬 진행 OK)

1. `orin/interactive_cli/`·`dgx/interactive_cli/`·`datacollector/interactive_cli/` 3개 신규 디렉터리 생성 — spec 본문 (라인 89~118) 에 사용자 합의 명시됨. Category C 동의 이미 충족 → 자율 진행
2. `orin/`·`dgx/`·`datacollector/` 루트 디렉터리 모두 이미 존재 — 04 D1·D2 산출물로 확인
3. `orin/tests/check_hardware.sh` 존재 — F1 의 bash·python 혼합 패턴 참조 기반 (04 G1 완료)
4. `orin/inference/hil_inference.py` `--gate-json` 패턴 존재 — 04 G2 cycle 2 완료 산출물 (O1 참조 기반)
5. `datacollector/scripts/run_teleoperate.sh` 존재 — 04 D2 에서 최종 이관 완료
6. `datacollector/scripts/push_dataset_hub.sh`, `scripts/sync_dataset_collector_to_dgx.sh` 존재 — 04 T1 cycle 2 완료 산출물
7. DGX SSH `laba@spark-8434`, Orin SSH `laba@ubuntu` 접근 가능 — 04 사이클에서 반복 확인
8. `docs/lerobot_study/` 10개 파일 존재 — D1 study 의 5단계 옵션 후보 입력 자료
9. `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` 존재 — D1 의 draccus 인자 매핑 레퍼런스
10. 신규 pyproject.toml·setup_env.sh·deploy_*.sh 변경 없음 — 본 spec 은 interactive_cli/ 신규 파일만 (Category B 영역 비해당)
11. `bash -n` / `shellcheck` Bash 화이트리스트 추가됨 (04 wrap) — code-tester 가 정적 분석 실행 가능

---

## §5 확인 필요 가정 (awaits_user)

| # | 관련 todo | 질문 내용 | 영향 | 현재 상태 |
|---|---|---|---|---|
| A | TODO-D1 | 5단계 "어떤 학습 데이터를 모을건가요?" 옵션. task-executor 가 `docs/lerobot_study/` 전체 Read 후 후보 5개 이하 제안 → 사용자 답 | D2 의 `data_kind.py` + `record.py` draccus 인자 매핑 직결 | D1 study 완료 후 발송 |
| B | TODO-O1 | orin 측 flow 3~ 단계 구체 책임 — 후보: (1) ckpt 선택·hil_inference 실행·시연 데모 3단계 순차 / (2) ckpt 선택 + hil_inference 1단계 통합 / (3) 기타. task-executor 후보 제안 후 사용자 합의 | O2 의 `flows/inference.py` 구조 직결 | O1 study 완료 후 발송 |
| C | TODO-X1 | dgx 측 flow 3~ 단계 구체 책임 — 후보: (1) preflight·데이터셋 선택·학습 trigger·체크포인트 관리 4단계 / (2) preflight + 학습 trigger 2단계 통합 (데이터셋 선택·ckpt 관리는 CLI 외부) / (3) 기타. task-executor 후보 제안 후 사용자 합의 | X2 의 `flows/training.py` 구조 직결 | X1 study 완료 후 발송 |

awaits_user 운영 원칙:
- D1·O1·X1 study 는 awaits_user 답 없이 진행 (후보 제안이 study 산출물의 일부)
- D2·O2·X2 구현은 각 awaits_user 해소 전 dispatch X
- D1·O1·X1 은 서로 독립 — 하나의 awaits_user 가 지연되어도 다른 study 는 계속 진행

awaits_user 재판단 결과 (planner 분석):
spec 본문 라인 180~182 의 "study 시점 결정" 3건은 모두 task-executor 가 후보 제안 후 사용자 합의 필요한 구조. 다음 이유로 자율 진행 불가 판단:
- D1 의 5단계 옵션은 `record.py` 의 draccus 인자 동적 생성 로직과 직결 — 옵션 확정 없이 구현하면 코드 구조 전면 재작성 위험
- O1 의 flow 3~ 는 `hil_inference.py` 의 `--gate-json` 인자 자동 채움 방식과 직결 — ckpt 선택 UI 포함 여부가 inference.py 복잡도를 크게 좌우
- X1 의 flow 3~ 는 `smoke_test.sh` 호출 방식 + 사용자 동의 게이트 위치와 직결 — 학습 trigger 단계에서 사용자 동의가 CLI 내부인지 외부인지가 구현 구조 결정

세 항목 모두 awaits_user 유지. task-executor study 완료 후 즉시 사용자 발송.

---

## §6 Phase 3 검증 큐 후보

| todo | 검증 방식 | 04 BACKLOG 통합 항목 | 비고 |
|---|---|---|---|
| TODO-D3 | 사용자 실물 필수 — DataCollector 머신 직접 터미널, flow 0~7 완주, SO-ARM + 카메라 임시 연결, dummy dataset 수집 | 04 BACKLOG #7 (DataCollector 16단계), #8 (G3 env_check.py 이식), #9 (G4 DataCollector check_hardware prod) | DataCollector 머신 미셋업 시 NEEDS_USER_VERIFICATION 이관. 7단계 3분기 (HF Hub / rsync / 안함) 모두 동작 확인 필요 |
| TODO-O3 | 사용자 실물 필수 — Orin SSH, flow 0~추론 완주, 카메라 2대 + SO-ARM follower 실 연결 | 04 BACKLOG #7 G2 (first-time/resume + hil_inference 50-step) | 04 G2 verification_queue 의 환경 그대로 활용. 추론 flow 완주 후 정성 관찰 포함 |
| TODO-X3 | prod-test-runner 자율 (DGX SSH) + 사용자 동의 필요 항목 | 04 BACKLOG #7 X3 (smoke_test 캐시 MISS 동의), T1 (HF Hub push 실 검증), T2 (시연장 네트워크 케이스) | smoke_test 5~15분 실행 전 사용자 동의 필요 (NEEDS_USER_VERIFICATION). svla_so100_pickplace 데이터셋 다운로드 100MB 초과 → 사용자 동의 필요 |
| TODO-F2 (간접) | code-tester 자동 + deploy_datacollector.sh 실 사용 검증 | 04 BACKLOG #7 T3 (deploy_datacollector dry-run·실배포) | F2 task 에서 3 노드 deploy 실 사용 시 04 T3 자연 검증 |

검증 큐 운영 원칙:
- D3·O3 는 실물 환경 필수 → NEEDS_USER_VERIFICATION 정상 (자동화 종료 시점에 사용자에게 Phase 3 안내)
- X3 는 DGX SSH 자율 가능하나 smoke_test 사용자 동의 + 대용량 다운로드 포함 → NEEDS_USER_VERIFICATION
- DataCollector 실물 미셋업 시 D3 는 큐에 대기, O3·X3 는 별도 진행

---

## §7 Hard Constraints 적용 메모

### Category A 해당 없음

본 spec 11개 todo 는 모두 `orin/interactive_cli/`·`dgx/interactive_cli/`·`datacollector/interactive_cli/`·`docs/storage/` 신규 파일 생성. `docs/reference/`·`.claude/` 영역 비해당.

### Category B 식별 — code-tester MAJOR 시 사용자 보고 게이트

| todo | Category B 영역 접촉 가능성 | 비고 |
|---|---|---|
| TODO-D2 (env_check.py) | `datacollector/scripts/check_hardware.sh` 신규 생성 가능성 | 신규 생성 파일이며 `deploy_*.sh` 패턴 아님 — Category B 해당 없음. pyproject.toml 수정 없음 전제 |
| 전체 | `orin/pyproject.toml`·`dgx/pyproject.toml` 수정 없음 예상 | interactive_cli 는 신규 파일이며 기존 pyproject.toml entrypoint 추가 없이 `bash main.sh` 직접 호출 — Category B 비해당 확인됨 |

현재 분석 결과 Category B 영역 변경 todo 없음. D2 구현 중 환경 의존성 추가 결정이 발생하면 즉시 orchestrator 보고.

### Category C — spec 본문 합의로 이미 해소된 항목

| 신규 생성 | Category C 근거 | 해소 근거 |
|---|---|---|
| `orin/interactive_cli/` | 새 디렉터리 생성 | spec 라인 93~102 사용자 합의 명시 (완료) |
| `dgx/interactive_cli/` | 새 디렉터리 생성 | spec 라인 104~108 사용자 합의 명시 (완료) |
| `datacollector/interactive_cli/` | 새 디렉터리 생성 | spec 라인 110~117 사용자 합의 명시 (완료) |

3개 신규 디렉터리 모두 Category C 동의 사전 충족 → F2 자율 진행 가능.

### Category C — 추가 발생 가능성 (게이트 포함)

| 상황 | 조건 | 처리 |
|---|---|---|
| D2 구현 중 `datacollector/pyproject.toml` 에 신규 의존성 추가 결정 | interactive_cli 의존성 추가 여부 미확정 | awaits_user 발동 필요. D2 task-executor 가 판단 후 orchestrator 보고 |
| F1·F2 구현 중 spec 합의 범위 외 신규 디렉터리 발생 | spec 합의 범위 외 | awaits_user 발동 필요 |

### Category D 해당 없음

bash 스크립트는 `bash -n` / `shellcheck` (화이트리스트) 검증 대상. `rm -rf`·`sudo`·`chmod 777` 등 deny 패턴 사용 없음.

---

## §8 레퍼런스 활용 의무 (task-executor 에게)

lerobot-reference-usage 스킬 적용 결과:

| todo | 신규 자산 | 레퍼런스 확인 의무 파일 | 비고 |
|---|---|---|---|
| TODO-F1 | `docs/storage/12_interactive_cli_framework.md` | `orin/tests/check_hardware.sh` (bash·python 혼합 패턴 직접 Read + 인용 필수) | 04 G1 산출물 기반 |
| TODO-F1 | 동상 | `orin/inference/hil_inference.py` (`--gate-json` JSON 로딩 패턴 직접 Read + 인용 필수) | gate-json 패턴이 flow 설계에 영향 |
| TODO-D1 | `docs/storage/15_datacollector_cli_flow.md` | `docs/lerobot_study/` 전체 + `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` (draccus 인자 직접 Read + 인용 필수) | 추측 작성 금지 |
| TODO-D2 | `datacollector/interactive_cli/flows/*.py` | `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` + 04 T1 산출물 (`push_dataset_hub.sh`, `sync_dataset_collector_to_dgx.sh`) 직접 Read | subprocess 호출 인자 추측 금지 |
| TODO-O1 | `docs/storage/13_orin_cli_flow.md` | `orin/inference/hil_inference.py` (전체 직접 Read + 인용 필수) | --gate-json 활용 구조 기반 |
| TODO-X1 | `docs/storage/14_dgx_cli_flow.md` | `dgx/scripts/{setup_train_env,preflight_check,smoke_test,save_dummy_checkpoint}.sh` 직접 Read | 기존 스크립트 패턴 기반 구현 필수 |

레퍼런스에 없는 신규 자산 필요 시 task-executor 는 즉시 SKILL_GAP 보고 후 작업 보류.

---

## §9 리스크 및 주의사항

| # | 리스크 | 관련 todo | 우선순위 | 비고 |
|---|---|---|---|---|
| R1 | D1·O1·X1 awaits_user 지연 시 D2·O2·X2 전체 block — study 빠른 완료 후 사용자 일괄 질문 처리 권장 | D2·O2·X2 | 중간 | Wave 2 병렬 study 동시 dispatch 로 지연 최소화 |
| R2 | DataCollector 실물 미셋업 — D3 진입 불가. O3·X3 는 계속 진행 가능 | D3 | 중간 | 사전 조건 명시, 사용자에게 셋업 안내 |
| R3 | 5단계 lerobot-record draccus 인자 동적 생성 — D1 옵션 확정 후 D2 구현 시 인자 매핑 정확성 필수 (04 M1 cycle 1 추측 작성 답습 X) | D2 | 중간 | lerobot_record.py 직접 Read 후 인용 의무 |
| R4 | F1 boilerplate 가 3 노드의 venv 경로 차이를 흡수해야 함 — orin: `.hylion_arm` / dgx: `.arm_finetune` / datacollector: `.hylion_collector`. F1 에서 venv 경로를 configs/node.yaml 로 분리하여 main.sh 가 읽는 구조 권장 | F1·F2 | 낮음 | spec 라인 121~124 에 설계 방향 명시 |
| R5 | 04 BACKLOG #7 DataCollector 실물 셋업 16단계 미완 — D3 사전 조건. Phase 3 전 사용자에게 셋업 필요 명시 필요 | D3 | 중간 | Phase 3 안내 시 포함 |
| R6 | 신규 자산 비중이 크므로 SKILL_GAP 발생 가능성 높음 (spec 라인 339) — F1 study 단계에서 미리 식별 | F1 | 낮음 | F1 task-executor 에게 SKILL_GAP 조기 식별 지시 |
