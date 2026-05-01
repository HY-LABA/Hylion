# Execution Plan — 04_infra_setup (후반 사이클)

> 작성: 2026-05-01 | planner
> Hard Constraints 체크: claude-md-constraints 스킬 적용 완료
> 레퍼런스 활용 의무: lerobot-reference-usage 스킬 적용 완료

---

## §1 사이클 메타

| 항목 | 내용 |
|---|---|
| spec | `docs/work_flow/specs/04_infra_setup.md` |
| 전체 todo | 17개 (O1·O2·O2b·O3 그룹 O 4건 완료) |
| 활성 todo | 13개 (X1·X2·X3 / D1·D2·D3 / G1·G2·G3·G4 / M1·M2 / T1·T2·T3) |
| 진입 시각 | 2026-05-01 |
| 전 사이클 잔재 | 없음 (context clean) |
| 참고 | 그룹 O 완료 산출물: orin/tests/ orin/config/ orin/checkpoints/ orin/inference/ 모두 존재 (TODO-O3 prod 검증 PASS) |

---

## §2 DAG (의존 관계)

### 그룹 X — dgx/ 구조 정리 (그룹 D 와 독립, 병렬 가능)

```
TODO-X1 (study: dgx/ 매트릭스)
  └─→ TODO-X2 (task: dgx/ 마이그레이션 실행)   [blockedBy: X1]
        └─→ TODO-X3 (test: dgx/ 회귀 검증)     [blockedBy: X2]
```

- X1 은 선결 의존 없음 (즉시 진입 가능)
- X2 는 X1 산출물 (`docs/storage/08_dgx_structure.md`) 필수
- X3 는 X2 실행 후 prod 검증 (DGX SSH 접속)

### 그룹 D — DataCollector 노드 신규 셋업

```
TODO-D1 ⚠️ awaits_user (노드 정체·OS·디렉터리·네트워크 결정)
  └─→ TODO-D2 (task: venv·lerobot 셋업 스크립트)   [blockedBy: D1]
        └─→ TODO-D3 (test: prod 환경 검증)          [blockedBy: D2, 실 하드웨어 필요]
```

- D1 은 사용자 결정 필수 (Category C: 새 디렉터리 `datacollector/` 생성 + venv 신규 생성 + 외부 의존성 추가 가능성)
- D2 는 D1 확정 후. `datacollector/pyproject.toml` 신규 시 Category C 추가 발동
- D3 는 DataCollector 노드 + SO-ARM + 카메라 실물 필요

### 그룹 G — 환경 점검 게이트 스크립트

```
TODO-G1 (task: orin/tests/check_hardware.sh 작성)   [blockedBy: O2 완료 — 이미 충족]
  └─→ TODO-G2 (test: Orin 측 prod 검증)             [blockedBy: G1, 카메라 2대 + SO-ARM follower 1대]

TODO-G3 (task: DataCollector 측 이식)               [blockedBy: G1·D2]
  └─→ TODO-G4 (test: DataCollector 측 prod 검증)    [blockedBy: G3, 실 하드웨어]
```

- G1 은 orin/tests/ 존재 조건 충족 (O2 완료). 즉시 진입 가능
- G2 는 Orin 에 카메라 2대 + SO-ARM follower 실 연결 필요 → 사용자 실물 검증
- G3 는 G1 (Orin 스크립트) + D2 (DataCollector 환경) 모두 완료 후
- G4 는 DataCollector 실 하드웨어 필요

### 그룹 M — 시연장 환경 미러링

```
TODO-M1 (study: 미러링 가이드 작성)
  └─→ TODO-M2 (both: 1차 미러링 셋업)   [blockedBy: M1, 사용자 시연장 직접 접근]
```

- M1 은 선결 의존 없음 (즉시 진입 가능). 사용자 결정 사항 1개 (검증 깊이)
- M2 는 사용자가 직접 시연장에서 수행 — 자동화 불가, 사용자 책임

### 그룹 T — 데이터·체크포인트 전송 경로

```
TODO-T1 ⚠️ awaits_user (전송 방식: HF Hub vs rsync vs 둘 다)   [blockedBy: D1 정체 결정 후 스크립트 경로 확정]
TODO-T2 (test: DGX → Orin ckpt 전송 재확인)                    [blockedBy: D1 (DataCollector 네트워크 위치)]
TODO-T3 (task: deploy_datacollector.sh 신규)                    [blockedBy: D1 (DataCollector SSH 설정)]
```

- T1, T2, T3 모두 D1 결정 후 진입 가능 (DataCollector 네트워크·디렉터리 확정 필요)
- T3 는 신규 deploy 스크립트 → Category B (`scripts/deploy_*.sh`) 영역
- T2 dummy ckpt dry-run 은 prod-test-runner 자율 가능, 단 시연장 Orin 네트워크 격리 확인은 사용자 책임

### 그룹 간 의존 요약

```
[X1 → X2 → X3]    독립 — D 와 병렬 가능

[D1⚠️ → D2 → D3]  D1 awaits_user 로 block

[G1 → G2]          즉시 시작 가능
[G3 → G4]          D2 완료 후

[M1 → M2]          M1 즉시 시작 가능, M2 사용자 직접

[D1⚠️ → T1, T2, T3]  D1 awaits_user 로 block
```

---

## §3 병렬 그룹 (동시 실행 가능 묶음)

### Wave 0 — awaits_user 질문 발송 (dispatch 전 병렬 질문)

D1 / T1 / M1 검증 깊이 / (필요 시) D2 Category C 추가 질문을 orchestrator 가 한 번에 묶어 사용자에게 전달. 답 받기 전까지 D·T 그룹 dispatch X.

### Wave 1 — 즉시 병렬 dispatch 가능 (awaits_user 무관)

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X1 | study | 없음 | dgx/ 매트릭스 문서 작성 |
| TODO-G1 | task | orin/tests/ 존재 (이미 충족) | check_hardware.sh 작성 |
| TODO-M1 | study | 없음 | 미러링 가이드 문서 작성 |

X1, G1, M1 을 동시 3개 dispatch.

### Wave 2 — Wave 1 완료 후 (일부 병렬 가능)

| todo | 타입 | 선결 조건 | 병렬 여부 |
|---|---|---|---|
| TODO-X2 | task | X1 완료 | X3 와 직렬 |
| TODO-G2 | test | G1 완료 + 실 하드웨어 | 사용자 실물 검증 포함 |

X2 와 G2 는 서로 독립 → 병렬 dispatch 가능 (단 G2 는 Orin 실 하드웨어 필요).

### Wave 3 — D1 awaits_user 해소 후

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-D2 | task | D1 완료 | datacollector/ 셋업 스크립트 |
| TODO-T3 | task | D1 완료 | deploy_datacollector.sh (Category B) |
| TODO-T2 | test | D1 완료 | dummy ckpt dry-run |

D2, T3, T2 는 모두 D1 해소 직후 병렬 dispatch 가능 (서로 의존 없음).

### Wave 4 — Wave 3 완료 후

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-X3 | test | X2 완료 | DGX prod 검증 |
| TODO-D3 | test | D2 완료 + 실 하드웨어 | DataCollector prod 검증 |
| TODO-G3 | task | G1·D2 완료 | DataCollector 측 게이트 이식 |
| TODO-T1 | both | D1 + T1 awaits_user 해소 | 전송 방식 결정 + 스크립트 |

X3, D3, G3, T1 병렬 가능 (서로 독립).

### Wave 5 — Wave 4 완료 후

| todo | 타입 | 선결 조건 | 비고 |
|---|---|---|---|
| TODO-G4 | test | G3 완료 + 실 하드웨어 | DataCollector 게이트 prod 검증 |
| TODO-M2 | both | M1 완료 + 사용자 시연장 접근 | 사용자 직접 수행 |

---

## §4 가정 (확신 vs 확인 필요)

### 확신 가정 (병렬 진행 OK)

1. `orin/tests/` 디렉터리 존재 — TODO-O2 완료 산출물 확인됨 (TODO-G1 즉시 진입 근거)
2. `orin/config/ports.json`, `cameras.json` placeholder 존재 — TODO-O2 완료 산출물
3. `orin/inference/hil_inference.py` 새 경로 동작 — TODO-O3 prod 검증 PASS 확인됨
4. DGX Spark SSH `laba@spark-8434` 접근 가능 — 03 사이클에서 사용됨
5. Orin SSH `laba@ubuntu` 접근 가능 — O3 prod 검증에서 직접 확인
6. `orin/lerobot/` 파일·디렉터리 변경 금지 원칙 — 옵션 B 확정 (TODO-O1 산출물)
7. lerobot CLI entrypoint 9개 (`lerobot-find-port`, `lerobot-find-cameras` 등) Orin 에서 활성 상태 — TODO-O3 PASS
8. BACKLOG 04 #2 (run_teleoperate.sh .archive 컨벤션) — TODO-O2 에서 `docs/storage/others/run_teleoperate.sh.archive` 로 이미 임시 보관 완료. TODO-D2 시점에 최종 이동하면 자연 해소
9. `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` 및 `lerobot_find_cameras.py` 존재 — TODO-G1 레퍼런스 활용 기반

### 확인 필요 가정 (awaits_user 항목에서 해소)

1. DataCollector 노드 하드웨어·OS — 전혀 미결 (TODO-D1 사용자 결정)
2. DataCollector 디렉터리 이름 및 위치 — `datacollector/` 권장이나 미확정
3. DataCollector 에 `datacollector/pyproject.toml` 신규가 필요한지, orin/pyproject.toml subset 인지 — D2 진입 전 결정 필요
4. DataCollector 의 lerobot 의존성 범위 — 학습 없음은 확실, 나머지는 D1 결정 후
5. 데이터 전송 방식 (HF Hub vs rsync vs 둘 다) — T1 전제
6. 시연장 Orin 이 연구실 DGX/devPC 와 같은 네트워크에 있는지 — T2 에 영향
7. 시연장 미러링 검증 깊이 (육안+사진 vs 자동 검증 스크립트) — M1 §4 작성 방향 결정
8. `run_teleoperate.sh` 최종 귀속 — DataCollector 가 확정되면 `datacollector/scripts/` 로 이동 (X1 study 에서 재확인: dgx 에는 SO-ARM 직접 연결 없으므로 dgx 귀속 부적합)

---

## §5 awaits_user 항목 (Phase 2 진입 전 일괄 질문)

orchestrator 가 Wave 0 에서 사용자에게 아래 5건을 한 번에 전달. 답 받은 항목부터 unblock.

| # | 관련 todo | 질문 | 상태 |
|---|---|---|---|
| A | TODO-D1 | DataCollector 노드 하드웨어는 무엇인가요? | ✅ 답: **별도 PC 신규 구매 / Ubuntu** (2026-05-01 14:18) |
| B | TODO-D1 | DataCollector 코드 디렉터리 이름은? | ✅ 답: **`datacollector/`** (2026-05-01 14:18) |
| C | TODO-D2 | DataCollector 환경 구성 방식? | ✅ 답: **`datacollector/pyproject.toml` 신규 (orin subset)** (2026-05-01 14:18, Category C 외부 의존성 추가 동의 포함) |
| D | TODO-T1 | DataCollector → DGX 데이터 전송 방식? | ✅ 답: **HF Hub + rsync 직접 (둘 다)** (2026-05-01 14:18) |
| E | TODO-M1 | 시연장 미러링 검증 깊이? | ✅ 답: **육안+사진 결정, 자동 검증은 BACKLOG** (2026-05-01 14:25) |

**A·B·C·D 답 확정으로 unblock 된 todo**: D1 (study 자체가 사용자 결정 입력으로 진행 가능), D2, D3, G3, G4, T1, T2, T3 — 총 7건 의존 해소.

### Category C 식별 — awaits_user 로 분류된 신규 작업

| 작업 | Category C 근거 | 해소 조건 |
|---|---|---|
| `datacollector/` 디렉터리 신규 생성 | 새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외) | 질문 B 사용자 동의 |
| `datacollector/pyproject.toml` 신규 | 외부 의존성 추가 가능성 | 질문 C 사용자 동의 |
| DataCollector venv 신규 생성 | 시스템 환경 변경 | 질문 A·C 동의 후 |
| `deploy_datacollector.sh` 신규 (Category B) | Category B 영역 (`scripts/deploy_*.sh`) | D1 완료 후 T3 진행, code-tester MAJOR 시 자동 재시도 X |

### Category B 식별 — code-tester MAJOR 시 자동 재시도 X, 사용자 보고 게이트

| todo | Category B 영역 변경 파일 | 주의사항 |
|---|---|---|
| TODO-X2 | `dgx/pyproject.toml` (변경 가능성) | X1 study 결과에 따라 pyproject 수정 포함될 수 있음 |
| TODO-T3 | `scripts/deploy_datacollector.sh` | deploy_*.sh 패턴 신규 → Category B. code-tester MAJOR 시 사용자 보고 |
| TODO-G1 | `.gitignore` (변경 가능성) | check_hardware.sh 에 config cache 파일 gitignore 추가 시 Category B |

---

## §6 검증 대기 큐 후보 (Phase 3 사용자 검증 대상)

| todo | 검증 방식 | 사유 |
|---|---|---|
| TODO-X3 | prod-test-runner 자율 (AUTOMATED_PASS 가능) | DGX SSH + smoke test 1 step 재실행 — 자동화 범위 |
| TODO-G2 | 사용자 실물 필수 | Orin + 카메라 2대 + SO-ARM follower 실 연결 first-time/resume 두 모드 확인 — 육안 관찰 필요 |
| TODO-D3 | 사용자 실물 필수 | DataCollector 머신 + SO-ARM + 카메라 임시 연결 — 자동화 범위 외 |
| TODO-G4 | 사용자 실물 필수 | DataCollector 실 하드웨어 연결 — 자동화 범위 외 |
| TODO-M2 | 사용자 직접 수행 (자동화 불가) | 시연장 물리 환경 셋업 — AI 워커 실행 불가 영역 |
| TODO-T1 | prod-test-runner 자율 (dry-run) + 사용자 실 데이터셋 확인 | dummy dataset dry-run 은 자율, 실 데이터셋 push는 05 책임 |
| TODO-T2 | prod-test-runner 자율 (dummy ckpt dry-run) + 사용자 시연장 네트워크 확인 | 시연장 Orin 네트워크 격리 여부 사용자 확인 필요 |

---

## §7 리스크·블로커 후보

| # | 리스크 | 관련 todo | 우선순위 | 비고 |
|---|---|---|---|---|
| R1 | DataCollector 노드 하드웨어 미확정 — D1 awaits_user 해소 전까지 D·T 그룹 전체 block | D1, D2, D3, G3, G4, T1, T2, T3 | 높음 (전체 후반 그룹의 gate) | 사용자 최우선 결정 필요 |
| R2 | 시연장 Orin 네트워크 격리 — 외부 인터넷 또는 연구실 VPN 불가 환경이면 DGX → Orin ckpt 전송 경로 우회 필요 (USB 또는 DataCollector 경유) | T2 | 중간 | 사용자가 시연장 환경 사전 확인 필요 |
| R3 | lerobot-find-port / lerobot-find-cameras 대화형 wrapping 난이도 — BACKLOG 01 #2: 비대화형 SSH 지원 불확실. G1 구현 시 OpenCV 직접 호출 또는 udevadm 우회 패턴 필요 | G1 | 중간 | spec 잔여 리스크에도 명시됨 |
| R4 | G1 first-time 모드 카메라 미리보기 — X11 forwarding 필요. SSH 비대화형 환경에서 불가 | G1, G2 | 낮음 | Orin 콘솔 직접 사용 가정으로 해소 가능 |
| R5 | DataCollector OS 가 Linux 외 (예: Windows) 일 경우 lerobot 호환성 이슈 | D1, D2 | 낮음 (D1 결정 시 해소) | Ubuntu 권장으로 질문 A 에 포함 |
| R6 | BACKLOG 04 #3 (ports.json·cameras.json git 추적 정책 미결) — G1 이 config/ 에 cache 쓰는 시점에 gitignore 처리 방식 결정 필요 | G1 | 낮음 | G1 진입 전 orchestrator 가 사용자에게 brief 확인 또는 기존 BACKLOG 정책 따라 git 추적으로 처리 |
| R7 | BACKLOG 04 #2 (.archive 컨벤션) — run_teleoperate.sh 이 `docs/storage/others/run_teleoperate.sh.archive` 에 임시 보관 중. D1 완료 후 D2 시점에 DataCollector 로 최종 이동하면 자연 해소. 본 사이클 중 처리 가능 | D2 | 낮음 | D2 task 에서 자연 해소 후보 |

### BACKLOG 자연 해소 후보 식별

| BACKLOG 항목 | 해소 가능 todo | 조건 |
|---|---|---|
| 04 #2 (.archive 컨벤션 결정) | TODO-D2 | DataCollector 디렉터리 확정 시 run_teleoperate.sh 최종 이동으로 해소 |
| 04 #3 (ports/cameras git 정책) | TODO-G1 | check_hardware.sh 가 config/ 에 cache 쓸 때 gitignore 처리 정책 결정으로 해소 가능 |
| 01 #1 (SO-ARM udev rule) | TODO-G1 | check_hardware.sh 의 포트 발견·cache 패턴이 udev 의존 없는 동적 발견으로 대체하면 실질 해소 |
| 01 #2 (lerobot-find-port 비대화형) | TODO-G1 | check_hardware.sh 구현에서 직접 해소 시도 (OpenCV/udevadm wrapping) |

---

## §8 레퍼런스 활용 의무 (task-executor 에게)

lerobot-reference-usage 스킬 적용 결과, 신규 스크립트 포함 todo 에 대한 의무 명시:

| todo | 신규 자산 | 레퍼런스 확인 의무 파일 |
|---|---|---|
| TODO-G1 | `orin/tests/check_hardware.sh` | `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` + `lerobot_find_cameras.py` — 포트·카메라 발견 패턴 기반 작성 필수 |
| TODO-T1 | `scripts/sync_dataset_collector_to_dgx.sh` 또는 `datacollector/scripts/push_dataset_hub.sh` | `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — HF Hub push 패턴 참조 (T1 방식 결정 후) |
| TODO-T3 | `scripts/deploy_datacollector.sh` | 기존 `scripts/deploy_orin.sh` / `deploy_dgx.sh` — 레퍼런스가 아닌 본 프로젝트 내부 패턴이므로 lerobot reference 검색 의무 없음, 단 형제 패턴 준수 필수 |
| TODO-G3 | `datacollector/tests/check_hardware.sh` | G1 산출물 기반 이식 (G1 완료 후 경로·venv 변수 갱신만) |

레퍼런스에 없는 신규 자산 필요 판단 시 task-executor 는 즉시 SKILL_GAP 보고 후 작업 보류.
