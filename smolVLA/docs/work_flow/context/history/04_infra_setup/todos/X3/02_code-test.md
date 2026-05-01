# TODO-X3 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`MAJOR_REVISIONS`**

Critical 이슈 2건 확인: (1) `save_dummy_checkpoint.sh` 가 실제 1 step GPU 학습 + HF Hub 다운로드 포함(5~15분)이므로 사용자 동의 영역인데 자율 분류 오류. (2) 단계 6b 캐시 확인 경로가 `~/.cache/huggingface/hub/` 로 잘못 지정됨 — 실제 HF_HOME은 `/home/laba/smolvla/.hf_cache/` 임.

---

## 단위 테스트 결과

```
해당 없음 — test 타입 todo. task-executor 산출물은 시나리오 정의 문서만.
실 코드 변경 없음. pytest 실행 대상 없음.
```

## Lint·Type 결과

```
해당 없음 — 생성된 파일은 Markdown + Bash 스크립트 (task-executor 미수정, 기존 산출물).
task-executor 가 수정한 파일: 없음 (시나리오 정의 문서 2건만).
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. TODO-X2 후 02 산출물 모두 정상 동작 확인 (1 step smoke test 재실행) | ✅ | 단계 6b 에 smoke_test.sh 재실행 시나리오 정의됨 |
| 2. 02 산출물 4개 (setup_train_env, preflight_check, smoke_test, save_dummy_checkpoint) 시나리오에 포함 | ✅ | 단계 5 (파일 존재 + 실행 권한), 단계 6 (preflight), 단계 8 (save_dummy_checkpoint), 단계 6b (smoke_test) 각각 매핑 |
| 3. X2 + cycle 2 산출물 검증 포함 (신규 디렉터리·README·dataset_repos.json·dgx/README 갱신·.gitignore 패턴) | ✅ | 단계 2~4 (신규 디렉터리·JSON·README), 단계 7 (.gitignore) 포함 |
| 4. prod 검증 (DGX 접속 필요) 에 맞는 시나리오 형식 | ✅ | SSH alias `dgx`, 경로 `~/smolvla/dgx/` 일관. PASS 기준·FAIL 분기 명시 |

spec 의 DOD 항목 자체는 충족되나, 시나리오 내 자율성 분류 오류 2건이 Critical 수준으로 발견됨.

---

## Critical 이슈 (MAJOR_REVISIONS 사유)

### 1. save_dummy_checkpoint.sh — 실 동작 대비 자율성 분류 오류

- 위치: `docs/work_flow/context/todos/X3/01_implementation.md` 단계 8
- 사유:
  - task-executor 보고: "GPU 학습 불필요한 dummy 저장 → 자율 가능 (5분 미만 예상)"
  - 실제 `dgx/scripts/save_dummy_checkpoint.sh` 스크립트 주석 (14~16행): "소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)"
  - 스크립트 본문 (57~71행): `lerobot-train --policy.path=lerobot/smolvla_base --dataset.repo_id=lerobot/svla_so100_pickplace --steps=1 --save_checkpoint=true --policy.device=cuda` — GPU 학습 1 step 실행 + HF Hub 다운로드 포함
  - CLAUDE.md prod-test-runner 자율성 정책: "큰 다운로드 (>100MB)·긴 실행 (>5분) → 사용자 동의"
  - 판단: 5~15분 + HF Hub 다운로드 포함이므로 smoke_test.sh 와 동일 카테고리 (사용자 동의 영역). 단계 8 을 자율 항목 섹션에 배치한 것이 CLAUDE.md 위반.
- 수정 요청:
  - 단계 8 을 "자율 가능 항목" 섹션에서 제거하고 "긴 실행 항목 (prod-test-runner 자율성 결정 필요)" 섹션으로 이동.
  - 캐시 확인 분기 논리 추가 (smoke_test.sh 와 동일 — 두 캐시 모두 HIT 시 자율 가능, MISS 시 사용자 동의).
  - 단계 8 의 주의 문구 "5분 초과 시 동의 영역 전환" 은 이미 있으나, 초기 분류 자체가 자율 섹션이므로 prod-test-runner 가 정책 오해 없이 실행할 위험이 있음.

### 2. 단계 6b 캐시 확인 경로 오류

- 위치: `docs/work_flow/context/todos/X3/01_implementation.md` 단계 6b "캐시 확인 방법" 코드 블록
- 사유:
  - task-executor 가 제시한 캐시 확인 명령:
    ```
    ssh dgx "ls ~/.cache/huggingface/hub/ | grep smolvla_base ..."
    ssh dgx "ls ~/.cache/huggingface/hub/ | grep svla_so100_pickplace ..."
    ```
  - 실제 HF_HOME 경로: `dgx/scripts/setup_train_env.sh` 및 `dgx/scripts/preflight_check.sh` 기준, `HF_HOME=/home/laba/smolvla/.hf_cache` (또는 `${SMOLVLA_DIR}/.hf_cache`)
  - `dgx/README.md` 환경변수 표에도 "HF_HOME: /home/laba/smolvla/.hf_cache" 명시됨
  - `~/.cache/huggingface/hub/` 는 HF_HOME 미설정 시의 기본 경로이며, 본 프로젝트는 격리 경로를 사용함
  - HF_HOME 하의 모델 캐시 경로는 `$HF_HOME/hub/` 형태 (예: `/home/laba/smolvla/.hf_cache/hub/`)
  - 잘못된 경로를 확인하면 CACHE_MISS 로 오판단 → 사용자 동의 요청 경로로 회귀하므로 기능적 실패는 없으나, CACHE_HIT 임에도 MISS 로 판단하여 불필요한 사용자 동의 요청 가능성 + 경로 오류 자체가 논리적 결함
- 수정 요청:
  - 캐시 확인 명령을 `ssh dgx "ls /home/laba/smolvla/.hf_cache/hub/ | grep smolvla_base ..."`  
    또는 `ssh dgx "ls \${HF_HOME}/hub/ | grep smolvla_base ..."` 로 수정.
  - `setup_train_env.sh` 에서 `HF_HOME` 을 환경변수로 export 하므로 venv 활성화 후 확인 가능.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | 단계 6 — preflight_check.sh "메모리 점검만" 설명 | 실제 스크립트는 5가지 체크 (venv 격리·메모리·Walking RL·Ollama·디스크) 수행. 단 수초 내 완료라 자율 분류는 정확. 설명 문구 "메모리 점검만 (수초)" → "환경 격리 + 메모리 + 자원 보호 점검 (학습 실행 없음, 수초 이내)" 로 보완 권장. prod-test-runner 오해 방지 목적. |
| 2 | 04_dgx_lerobot_diff.md 시나리오 매핑 | X2 산출물 목록에 04_dgx_lerobot_diff.md 갱신이 포함되어 있으나 별도 검증 단계 없음. 단계 2 또는 별도 단계에서 `ssh dgx "cat ~/smolvla/docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md | head -10"` 으로 동기화 확인 추가 권장. 빠진 매핑이 시나리오 완전성에 영향. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | task-executor 가 `docs/reference/`, `.claude/` 하위 미변경. 시나리오 정의 문서만 작성. |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `deploy_*.sh`, `.gitignore` 변경 없음. 본 todo 는 시나리오 정의 전담으로 실 코드 수정 없음. |
| Coupled File Rules | ✅ | Category B 영역 미변경이므로 Coupled File Rules 해당 없음. |
| docs/storage/ bash 예시 규칙 | ✅ | history 문서 경로는 `docs/work_flow/context/history/` (docs/storage/ 하위 아님). 04_dgx_lerobot_diff.md (`docs/storage/lerobot_upstream_check/`) 는 X2 task-executor 가 갱신한 것이며, 본 todo 에서 추가 변경 없음. bash 명령 예시 추가 없음 확인. |
| prod-test-runner 자율성 정책 | ❌ | **단계 8 자율 분류 오류** (Critical #1) + 단계 6b 캐시 확인 경로 오류 (Critical #2). CLAUDE.md "긴 실행 (>5분) → 사용자 동의" 정책 미준수. |

---

## ANOMALIES.md 관련

- ANOMALIES `SKILL_GAP #1` (Bash 차단): task-executor 가 직접 스크립트를 실행할 수 없어 동작 보고를 파일 Read 기반으로 수행. code-tester 도 동일 제약하에 검증. save_dummy_checkpoint.sh 의 실행 시간은 스크립트 내 주석에서 확인 가능했으나, task-executor 가 주석보다 스크립트 이름("dummy") 에 의존한 추측 판단을 한 것으로 보임. prod-test-runner 입장에서도 단계 1·6·8·6b 모두 SSH 명령이므로 Bash 차단의 직접 영향은 없음 (devPC Bash 가 아닌 SSH). 단 devPC 측 배포·검증 명령 자체가 차단될 가능성은 orin-deploy-procedure 스킬 준수 시 SSH 경유로 우회 가능. 본 이슈는 기존 `SKILL_GAP #1` 에 이미 기록된 범위.

---

## 배포 권장

**MAJOR → no** — task-executor 재호출 필요.

- 본 todo 는 test 타입이므로 Category B 영역 미변경. 자동 재시도 OK (max 2 cycle).
- 수정 요청 사항:
  1. 단계 8 (`save_dummy_checkpoint.sh`) 을 "긴 실행 항목" 섹션으로 이동 + 캐시 확인 분기 추가.
  2. 단계 6b 캐시 확인 경로 수정: `~/.cache/huggingface/hub/` → `/home/laba/smolvla/.hf_cache/hub/` (또는 venv 활성화 후 `$HF_HOME/hub/`).
  3. (Recommended) 단계 6 preflight 설명 문구 보완.
  4. (Recommended) 04_dgx_lerobot_diff.md 동기화 확인 단계 추가.
- 2 cycle 후에도 MAJOR 이면 todo 실패 마킹 (다른 todo 계속 진행).

## 다음 단계

- MAJOR: task-executor 재호출 → 수정 후 02_code-test.md cycle 2 재작성 → READY 판정 시 prod-test-runner 진입.

---

## cycle 2 재검증 (2026-05-01 | code-tester | cycle: 2)

### Critical #1 해소 검증 — save_dummy_checkpoint.sh 자율성 재분류

- **단계 8 위치 변경 확인**: `01_implementation.md` 138~175행 "긴 실행 항목 (prod-test-runner 자율성 결정 필요)" 섹션 내에 단계 8 배치 확인. 자율 가능 항목 섹션에서 제거됨 — **해소 확인**.
- **캐시 HIT/MISS 분기 추가 확인**: 단계 8 (166~172행) 에 캐시 확인 방법 코드 블록 포함. "두 캐시 (smolvla_base + svla_so100_pickplace) 모두 HIT: 자율 진행 가능 / 어느 하나라도 MISS: 사용자 동의 요청 후 진행" 분기 명시 — smoke_test.sh 와 동일 패턴 — **해소 확인**.
- **직접 Read 인용 정확성 검증**:
  - `dgx/scripts/save_dummy_checkpoint.sh` 직접 Read 결과:
    - 14~16행: `# 소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)` — cycle 2 수정 절 (225행) 인용과 일치
    - 56~70행: `lerobot-train --policy.path=lerobot/smolvla_base ... --steps=1 --save_checkpoint=true ... --policy.device=cuda` — cycle 2 수정 절 인용과 일치. `--policy.device=cuda` GPU 학습 1 step 확인
  - 추측 없음. 직접 Read 기반 판단 확인 — **정확**.

### Critical #2 해소 검증 — HF cache 경로 정정

- **단계 6b 캐시 확인 경로**: `01_implementation.md` 151~154행:
  ```bash
  ssh dgx "ls ~/smolvla/.hf_cache/hub/ 2>/dev/null | grep -E 'smolvla_base|svla_so100' && echo CACHE_HIT || echo CACHE_MISS"
  ```
  `~/smolvla/.hf_cache/hub/` 사용 확인. 직전 cycle 의 `~/.cache/huggingface/hub/` 는 제거됨 — **해소 확인**.
- **단계 8 캐시 확인 경로**: `01_implementation.md` 170~173행 동일 명령 재사용 확인 — **해소 확인**.
- **직접 Read 인용 정확성 검증**:
  - `dgx/scripts/setup_train_env.sh` 19행: `HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"` → venv activate 시 `export HF_HOME="${HF_CACHE_DIR}"` 주입 (75~82행). SMOLVLA_DIR 기준 `/home/laba/smolvla` 이므로 `HF_HOME=/home/laba/smolvla/.hf_cache` — 인용 정확.
  - `dgx/scripts/preflight_check.sh` 43행: `HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"` — cycle 2 수정 절 (234행) 인용 일치.
  - `dgx/README.md` 163행: `HF_HOME: /home/laba/smolvla/.hf_cache` — cycle 2 수정 절 (233행) 인용 일치.
  - 캐시 확인 명령의 경로 `~/smolvla/.hf_cache/hub/` 는 `$HF_HOME/hub/` 에 해당 — **정확**.

### Recommended #1 해소 검증 — preflight 5가지 체크 명시

- **단계 6 설명 갱신**: `01_implementation.md` 120~122행:
  > "02 산출물 중 preflight_check.sh 단독 회귀 검증 (smoke_test 와 독립적) — 5가지 체크 수행: venv 격리 (HF_HOME + CUDA_VISIBLE_DEVICES 포함) / 메모리 가용성 (20 GB + 10 GB 마진) / Walking RL 프로세스 보호 (관찰만) / Ollama gemma3 GPU 점유 / 디스크 가용량"
  "메모리 점검만" → 5가지 체크 명시로 갱신됨 — **해소 확인**.
- **직접 Read 인용 정확성 검증**:
  - `dgx/scripts/preflight_check.sh` 직접 Read 결과:
    - 56행 `[1/5] venv / 환경변수 격리`: VIRTUAL_ENV + HF_HOME + CUDA_VISIBLE_DEVICES 3가지 체크
    - 79행 `[2/5] 메모리 가용성 (UMA pool)`: MemAvailable 기준 메모리 체크
    - 99행 `[3/5] Walking RL 프로세스 (정보만, 종료 금지)`: nvidia-smi env_isaaclab 관찰
    - 111행 `[4/5] Ollama gemma3 (로드 시 17 GB 점유 위험)`: nvidia-smi ollama 관찰
    - 124행 `[5/5] 디스크 가용량 (/home/laba)`: df -P 50 GB 임계치
  - 5가지 체크 확인됨 — **인용 정확**. cycle 2 수정 절 (239~240행) 의 [1/5]~[5/5] 열거 일치.

### Recommended #2 해소 검증 — 04_dgx_lerobot_diff.md 매핑 추가

- **단계 4b 신규 추가 확인**: `01_implementation.md` 103~113행에 단계 4b 존재:
  ```bash
  grep -E "2026-05-01.*TODO-X2" /home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md
  ```
  devPC 측 확인 명령. "2026-05-01 + TODO-X2 포함 행 최소 1건 출력" 기대 — **추가 확인**.
- **grep 패턴 유효성 검증**:
  - `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 직접 Read 결과, 91행:
    `### [2026-05-01] \`dgx/tests/\`, \`dgx/config/\` 신규 디렉터리 — 04 TODO-X2 마이그레이션`
  - `grep -E "2026-05-01.*TODO-X2"` 패턴은 이 행에서 매칭됨 (동일 행에 "2026-05-01" 과 "TODO-X2" 포함) — **패턴 유효**.
- **검증 순서에 4b 포함**: `01_implementation.md` 183행 `→ coupled file 갱신 확인 (단계 4b, devPC)` — 검증 순서에도 반영됨 — **해소 확인**.

### 다른 단계 회귀 X 확인

| 단계 | 기대 | cycle 2 후 상태 | 판정 |
|---|---|---|---|
| 단계 1 (deploy_dgx.sh) | 자율 분류 유지 | 57~66행 "자율 가능 항목" 섹션 내 유지 | ✅ |
| 단계 2~5 (read-only ssh) | 자율 분류 유지 | 67~101행 자율 섹션 내 유지 | ✅ |
| 단계 6 (preflight smoke) | 설명 정정, 자율 유지 | 114~123행 자율 섹션 내, 설명 5가지 체크로 갱신 | ✅ |
| 단계 6b (smoke_test.sh) | 캐시 HIT/MISS 분기, 긴 실행 섹션 유지 | 142~157행 긴 실행 섹션, 캐시 확인 경로 정정 | ✅ |
| 단계 7 (.gitignore) | 자율 분류 유지 | 125~136행 자율 섹션 내 유지 | ✅ |
| 단계 8 | 긴 실행 섹션 이동 + HIT/MISS 분기 추가 | 159~174행 긴 실행 섹션, 분기 추가, 경로 정정 | ✅ |

회귀 없음.

### 추측 위반 답습 X 검증

- **save_dummy_checkpoint.sh 직접 Read 확인**: cycle 2 수정 절 225~228행에 "직접 Read 확인: `dgx/scripts/save_dummy_checkpoint.sh` 주석 14~16행..." 인용 명시. code-tester 직접 Read 결과와 일치 — **추측 위반 없음**.
- **HF_HOME 경로 직접 Read 확인**: cycle 2 수정 절 232~235행에 `setup_train_env.sh` 19행, `dgx/README.md` 163행, `preflight_check.sh` 43행 인용 명시. code-tester 직접 Read 결과와 일치 — **추측 위반 없음**.
- **preflight 5가지 체크 직접 Read 확인**: cycle 2 수정 절 239행에 "직접 Read 확인: `preflight_check.sh` 5가지 체크 섹션 확인 ([1/5]~[5/5])" 명시 — **추측 위반 없음**.
- **cycle 1 의 "dummy 라 GPU 학습 X" 추측 패턴 반복 없음**: cycle 2 보고에서 스크립트 이름이 아닌 주석·본문 내용 기반 판단 확인 — **답습 없음**.

---

## verdict (cycle 2): READY_TO_SHIP

**근거**: Critical 2건 모두 해소 + Recommended 2건 모두 해소 + 회귀 없음 + 추측 위반 답습 없음.

- Critical #1 (save_dummy_checkpoint.sh 자율성 오류): 단계 8 이 "긴 실행 항목" 섹션으로 이동, 캐시 HIT/MISS 분기 추가, save_dummy_checkpoint.sh 직접 Read (14~16행 주석 + 56~70행 본문) 기반 판단 확인.
- Critical #2 (HF cache 경로 오류): 단계 6b + 단계 8 캐시 확인 명령 모두 `~/smolvla/.hf_cache/hub/` 로 정정. setup_train_env.sh (19행) + preflight_check.sh (43행) + README.md (163행) 직접 Read 인용 일치.
- Recommended #1: preflight 설명 "메모리 점검만" → 5가지 체크 (venv/메모리/Walking RL/Ollama/디스크) 명시. preflight_check.sh [1/5]~[5/5] 직접 Read 확인.
- Recommended #2: 단계 4b 신규 추가. 04_dgx_lerobot_diff.md 91행 grep 패턴 유효성 직접 Read 확인.
- Critical 0건, Recommended 0건 미해소 → READY_TO_SHIP 조건 충족.

## CLAUDE.md 준수 체크 (cycle 2)

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/` 하위 미변경 유지 |
| B (자동 재시도 X 영역) | ✅ | Category B 파일 (`deploy_*.sh`, `pyproject.toml`, `.gitignore`, `orin/lerobot/`, `dgx/lerobot/`) 미변경 유지 |
| Coupled File Rules | ✅ | Category B 미변경이므로 해당 없음. 단계 4b 는 기존 X2 task-executor 가 생성한 04_dgx_lerobot_diff.md 의 내용 확인 명령 (신규 수정 없음) |
| docs/storage/ bash 예시 규칙 | ✅ | 변경 없음 |
| prod-test-runner 자율성 정책 | ✅ | Critical #1·#2 해소로 단계 6b·8 자율성 분류 + 캐시 경로 모두 정정됨 |

## 다음 단계

- **READY_TO_SHIP → prod-test-runner X3 진입 권장**.
- prod-test-runner 는 단계 1~7 + 4b (자율) + 단계 6b·8 (캐시 확인 후 HIT 시 자율 / MISS 시 사용자 동의) 순서로 실행.
- 단계 6b 와 단계 8 의 캐시 확인 명령은 동일 (`~/smolvla/.hf_cache/hub/` 기준) — 한 번 확인으로 재사용 가능.
