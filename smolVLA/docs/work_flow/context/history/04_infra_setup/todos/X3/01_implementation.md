# TODO-X3 — dgx/ 마이그레이션 회귀 검증 (DGX prod) 시나리오 정의

> 작성: 2026-05-01 | task-executor | cycle: 2 (cycle 1 → MAJOR_REVISIONS 후 재수정)

## 목표

TODO-X2 + cycle 2 산출물 (dgx/tests/, dgx/config/, dgx/README.md 갱신, .gitignore 패턴 추가) 에 대해 DGX prod 환경 회귀 검증 시나리오를 정의한다. 02 마일스톤 산출물 4개 (setup_train_env.sh, preflight_check.sh, smoke_test.sh, save_dummy_checkpoint.sh) 의 동작 회귀 없음을 확인한다.

---

## 사전 점검 결과

### X2 + cycle 2 산출물 인벤토리

| 산출물 | 경로 | 상태 |
|---|---|---|
| dgx/tests/ 디렉터리 + README.md | `dgx/tests/README.md` | X2 신규 |
| dgx/config/ 디렉터리 + README.md | `dgx/config/README.md` | X2 신규 |
| dgx/config/dataset_repos.json | `dgx/config/dataset_repos.json` | X2 신규 (placeholder) |
| dgx/README.md 갱신 | `dgx/README.md` | X2 갱신 (pyproject 주의사항 + DataCollector 인터페이스) |
| 04_dgx_lerobot_diff.md 갱신 | `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | X2 갱신 (coupled file 규칙) |
| .gitignore smolVLA/dgx/outputs/ 패턴 | `.gitignore` (Hylion 루트) | X2 cycle 2 추가 확인 완료 |

### 02 산출물 4개 위치 확인 (devPC 로컬 확인)

| 파일 | 경로 | 미변경 여부 |
|---|---|---|
| setup_train_env.sh | `dgx/scripts/setup_train_env.sh` | X2 미변경 (code-tester DOD 2 ✅ 확인) |
| preflight_check.sh | `dgx/scripts/preflight_check.sh` | X2 미변경 ✅ |
| smoke_test.sh | `dgx/scripts/smoke_test.sh` | X2 미변경 ✅ |
| save_dummy_checkpoint.sh | `dgx/scripts/save_dummy_checkpoint.sh` | X2 미변경 ✅ |

### 검증 환경

- DGX 접속: SSH alias `dgx` (`~/.ssh/config` 등록 가정, orin-deploy-procedure 스킬 §SSH 설정)
- 배포 스크립트: `scripts/deploy_dgx.sh` (Category B 영역 — 스크립트 내용 변경 없음, 일반 배포)
- venv 경로 (DGX 측): `/home/laba/smolvla/dgx/.arm_finetune/`
- HF_HOME: `/home/laba/smolvla/.hf_cache/` (setup_train_env.sh 기준)
- .gitignore 는 devPC (Hylion 루트) 에만 존재하며 DGX 측엔 동기화되지 않음 — devPC 측 확인으로 충분

### smoke_test.sh 실행 시간 추정

smoke_test.sh 는 내부적으로 `lerobot-train --steps=1` + smolvla_base 모델 다운로드 + lerobot/svla_so100_pickplace 데이터셋 다운로드를 수행한다. 스크립트 주석에 "최초 실행 시 5~15분 소요" 명시됨 (최초: 모델·데이터셋 다운로드 포함). 재실행 시 캐시 히트 가정 시 1~3분으로 단축 가능하나 확실하지 않음. **CLAUDE.md prod-test-runner 자율성 정책상 긴 실행 (>5분 추정) → 사용자 동의 영역**.

---

## 산출물

본 TODO-X3 는 시나리오 정의 전담. 실제 prod 실행 (SSH, deploy, smoke_test) 은 prod-test-runner 의 책임.

---

## 검증 시나리오 정의 (prod-test-runner 입력)

### 자율 가능 항목 (prod-test-runner SSH — 즉시 실행)

#### 단계 1 — devPC deploy

```bash
# devPC 에서 실행 (Category B 외 변경 deploy → 자율)
bash scripts/deploy_dgx.sh
```

- 기대: rsync 성공, exit 0
- X2 + cycle 2 의 모든 변경 파일 (dgx/tests/, dgx/config/, dgx/README.md, 04_dgx_lerobot_diff.md) DGX 에 동기화

#### 단계 2 — 신규 디렉터리·파일 존재 확인

```bash
ssh dgx "ls ~/smolvla/dgx/tests/README.md ~/smolvla/dgx/config/README.md ~/smolvla/dgx/config/dataset_repos.json"
```

- 기대: 3개 파일 모두 경로 출력, exit 0
- TODO-X2 신규 산출물 DGX 동기화 확인

#### 단계 3 — dataset_repos.json valid JSON

```bash
ssh dgx "python3 -c 'import json; json.load(open(\"$HOME/smolvla/dgx/config/dataset_repos.json\")); print(\"OK\")'"
```

- 기대: `OK` 출력, exit 0
- 파일 내용이 유효한 JSON 임을 prod 환경 Python 으로 직접 확인

#### 단계 4 — dgx/README.md DataCollector 인터페이스 섹션 존재

```bash
ssh dgx "grep -E 'DataCollector|pyproject.toml' ~/smolvla/dgx/README.md | head -5"
```

- 기대: 'DataCollector' + 'pyproject.toml' 포함 행 최소 1건씩 출력
- TODO-X2 DOD §6 (pyproject 주의사항 + DataCollector 인터페이스 섹션) 동기화 확인

#### 단계 5 — 02 산출물 4개 파일 존재 + 실행 권한 확인

```bash
ssh dgx "ls -la ~/smolvla/dgx/scripts/setup_train_env.sh ~/smolvla/dgx/scripts/preflight_check.sh ~/smolvla/dgx/scripts/smoke_test.sh ~/smolvla/dgx/scripts/save_dummy_checkpoint.sh"
```

- 기대: 4개 파일 모두 존재, 실행 권한 (`-rwx`) 확인
- 02 산출물 DGX 측 무결성 확인 (X2 미변경 재확인)

#### 단계 4b — 04_dgx_lerobot_diff.md 갱신 확인 (devPC 측)

```bash
# devPC 에서 실행
grep -E "2026-05-01.*TODO-X2" /home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md
```

- 기대: 2026-05-01 + TODO-X2 포함 행 최소 1건 출력
- X2 산출물 인벤토리에 포함된 04_dgx_lerobot_diff.md 갱신 (coupled file 규칙 준수) 확인
- devPC 측 확인으로 충분 (DGX 에 동기화 후 SSH 확인도 가능하나 devPC 원본 기준으로 우선 확인)

#### 단계 6 — preflight_check.sh 동작 확인 (smoke 시나리오, 빠른 검증)

```bash
ssh dgx "cd ~/smolvla/dgx && source .arm_finetune/bin/activate && bash scripts/preflight_check.sh smoke"
```

- 기대: exit 0 (메모리 20 GB 이상 가용 시) 또는 실패 시 명시적 오류 메시지
- 02 산출물 중 preflight_check.sh 단독 회귀 검증 (smoke_test 와 독립적) — 5가지 체크 수행: venv 격리 (HF_HOME + CUDA_VISIBLE_DEVICES 포함) / 메모리 가용성 (20 GB + 10 GB 마진) / Walking RL 프로세스 보호 (관찰만) / Ollama gemma3 GPU 점유 / 디스크 가용량
- 소요: 수초 이내 (학습 실행 없음) → **자율 가능**
- 주의: Walking RL 학습 진행 중일 경우 가용 메모리가 30 GB (= 20 + 10 마진) 미달할 수 있음. 실패 시 이유 확인 후 orchestrator 에 보고

#### 단계 7 — .gitignore 패턴 확인 (devPC 측)

```bash
# devPC 에서 Read 툴 또는 직접 확인
# /home/babogaeguri/Desktop/Hylion/.gitignore 의 235행 부근
# 기대: "smolVLA/dgx/outputs/" 행 존재
```

- cycle 2 산출물 (`.gitignore` 패턴 추가) 확인
- DGX 측이 아닌 devPC 측 `.gitignore` 확인으로 충분 (gitignore 는 git 저장소 측 룰)
- 직접 확인 결과: `.gitignore` 235행에 `smolVLA/dgx/outputs/` 패턴 존재 확인 완료 (task-executor 사전 점검)

---

### 긴 실행 항목 (prod-test-runner 자율성 결정 필요)

#### 단계 6b — smoke_test.sh 1 step 학습 회귀 검증

```bash
ssh dgx "cd ~/smolvla/dgx && source .arm_finetune/bin/activate && bash scripts/smoke_test.sh"
```

- 기대: 1 step 학습 완료, exit 0, 결과 요약 출력 (소요 시간·GPU 점유)
- **실행 시간**: 최초 실행 (캐시 없음) 시 5~15분. 재실행 (캐시 히트) 시 1~3분 (불확실)
- **자율성 판단**: CLAUDE.md prod-test-runner 자율성 정책 "긴 실행 (>5분 추정) → 사용자 동의"
  - 캐시 존재 여부 불확실 → 캐시 확인 후 HIT 시 자율, MISS 시 사용자 동의 요청
- **캐시 확인 방법** (사전 확인 후 결정, HF_HOME = /home/laba/smolvla/.hf_cache):
  ```bash
  ssh dgx "ls ~/smolvla/.hf_cache/hub/ 2>/dev/null | grep -E 'smolvla_base|svla_so100' && echo CACHE_HIT || echo CACHE_MISS"
  ```
  - 두 캐시 모두 HIT (smolvla_base + svla_so100 모두 출력): 단계 6b 자율 진행 가능 (1~3분 예상)
  - 어느 하나라도 MISS: 사용자 동의 요청 후 진행

#### 단계 8 — save_dummy_checkpoint.sh 동작 확인

```bash
ssh dgx "cd ~/smolvla/dgx && source .arm_finetune/bin/activate && bash scripts/save_dummy_checkpoint.sh"
```

- 기대: dummy checkpoint 저장 성공 (`~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/` 생성), exit 0
- **실행 시간**: 스크립트 주석 (14~16행) 기준 "소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)" — GPU 학습 1 step + HF Hub 다운로드 포함
- **자율성 판단**: CLAUDE.md prod-test-runner 자율성 정책 "큰 다운로드 (>100MB)·긴 실행 (>5분) → 사용자 동의". smoke_test.sh 와 동일 카테고리.
  - 캐시 존재 여부에 따라 분기 (단계 6b 와 동일 논리):
  - 두 캐시 (smolvla_base + svla_so100_pickplace) 모두 HIT: 자율 진행 가능 (HF 다운로드 불필요, GPU 학습 1 step 만 ~30초~2분 예상)
  - 어느 하나라도 MISS: 사용자 동의 요청 후 진행 (HF Hub 다운로드 포함 5~15분)
- **캐시 확인 방법** (단계 6b 와 동일 명령으로 재사용 가능):
  ```bash
  ssh dgx "ls ~/smolvla/.hf_cache/hub/ 2>/dev/null | grep -E 'smolvla_base|svla_so100' && echo CACHE_HIT || echo CACHE_MISS"
  ```

---

### 검증 순서 권장

```
deploy (단계 1)
  → 파일 존재 확인 (단계 2, 3, 4, 5)   ← 병렬 가능
  → coupled file 갱신 확인 (단계 4b, devPC)
  → preflight 동작 (단계 6)            ← 자율, 수초 이내
  → .gitignore 확인 (단계 7, devPC)
  → [캐시 확인 후] smoke_test (단계 6b)   ← 사용자 동의 가능
  → [캐시 확인 후] save_dummy_checkpoint (단계 8)  ← 사용자 동의 가능
```

단계 2~5, 4b 는 read-only 존재 확인이므로 병렬 실행 가능.
단계 6b 와 단계 8 은 동일한 캐시 확인 명령 재사용 가능 (같은 캐시 경로 의존).

---

## 잔여 리스크 / SKILL_GAP

| 항목 | 내용 | 처리 |
|---|---|---|
| smoke_test.sh 캐시 여부 불확실 | 최초 실행 시 5~15분. 이전 02 검증에서 캐시 생성됐을 가능성 있음 | 단계 6b 전 캐시 확인 명령으로 prod-test-runner 가 판단. MISS 시 사용자 동의 요청 |
| save_dummy_checkpoint.sh 캐시 여부 불확실 | 동일 HF Hub 모델·데이터셋 의존. 5~15분 소요 가능 (스크립트 주석 기준) | 단계 8 전 캐시 확인 (단계 6b 와 동일 명령). MISS 시 사용자 동의 요청 |
| Walking RL 학습과의 자원 충돌 | preflight 단계 6 에서 메모리 30 GB (= 20 + 10 마진) 미달 가능 | 실패 시 이유 확인 + orchestrator 보고 (DGX 공유 정책 준수) |
| .gitignore DGX 미동기화 | devPC `.gitignore` 는 rsync 배포 대상 아님 (DGX 에 복사 X) | devPC 측 확인으로 충분. DGX 에서 git check-ignore 실행 시 "not active" 정상 (devPC 측 gitignore 라 OK) |

---

## 검증 필요 (다음 단계)

- **code-tester**: 시나리오 일관성·자율 가능 영역 분류 정확성. 특히 단계 6 (preflight 자율) vs 단계 6b·8 (동의 가능) 분류의 CLAUDE.md 정책 정합성 검토
- **prod-test-runner**: 단계 1~7 + 4b SSH/devPC 실행, 단계 6b·8 캐시 확인 후 smoke_test.sh·save_dummy_checkpoint.sh 결과 + verdict 결정

### prod-test-runner 최종 verdict 기준 (orin-deploy-procedure 스킬 기준)

| 결과 | Verdict |
|---|---|
| 단계 1~7 + 4b 모두 PASS + 단계 6b·8 캐시 HIT + 자율 실행 PASS | `AUTOMATED_PASS` |
| 단계 1~7 + 4b PASS + 단계 6b·8 캐시 MISS → 사용자 동의 후 실행 필요 | `NEEDS_USER_VERIFICATION` |
| 단계 1~5 PASS + 단계 6 또는 8 실패 (02 산출물 회귀 발견) | `FAIL` |
| 배포 실패 또는 신규 파일 미동기화 | `FAIL` |

---

## cycle 2 수정 (2026-05-01)

### Critical #1 해소 — save_dummy_checkpoint.sh 자율성 재분류

- 직접 Read 확인: `dgx/scripts/save_dummy_checkpoint.sh` 주석 14~16행 — "소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)", 본문 57~71행 — `lerobot-train --policy.device=cuda --steps=1 --save_checkpoint=true` GPU 학습 1 step 실행 확인
- 단계 8 을 "자율 가능 항목" 섹션에서 제거 → "긴 실행 항목 (prod-test-runner 자율성 결정 필요)" 섹션으로 이동
- smoke_test.sh 와 동일 카테고리 (CLAUDE.md "큰 다운로드 >100MB / 긴 실행 >5분 → 사용자 동의" 정책 준수)
- 캐시 HIT 시 자율 (GPU 학습 1 step 만, ~30초~2분) / MISS 시 사용자 동의 (5~15분 + HF Hub 다운로드) 분기 추가

### Critical #2 해소 — HF cache 경로 정정

- 직접 Read 확인: `dgx/scripts/setup_train_env.sh` 19행 — `HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"`, activate 스크립트에 `export HF_HOME="${HF_CACHE_DIR}"` 주입 확인
- `dgx/README.md` 환경변수 표 163행 — `HF_HOME: /home/laba/smolvla/.hf_cache` 명시 확인
- `dgx/scripts/preflight_check.sh` 43행 — `HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"` 확인
- 수정: `~/.cache/huggingface/hub/` → `~/smolvla/.hf_cache/hub/` (단계 6b 캐시 확인 명령 + 단계 8 캐시 확인 명령 모두)

### Recommended #1 해소 — preflight 설명 정확화

- 직접 Read 확인: `preflight_check.sh` 5가지 체크 섹션 확인 ([1/5] venv/HF_HOME/CUDA_VISIBLE_DEVICES, [2/5] 메모리, [3/5] Walking RL, [4/5] Ollama, [5/5] 디스크)
- 단계 6 설명 "메모리 점검만 (수초)" → "5가지 체크 수행: venv 격리 / 메모리 가용성 / Walking RL 보호 / Ollama GPU / 디스크 (학습 실행 없음, 수초 이내)" 로 정확화

### Recommended #2 해소 — 04_dgx_lerobot_diff.md 매핑 추가

- 단계 4b 신규 추가: devPC 측 `grep -E "2026-05-01.*TODO-X2"` 로 coupled file 갱신 확인
- 검증 순서 권장에 단계 4b 포함

### 다음 단계

- code-tester cycle 2 재검증
- READY 시 prod-test-runner X3 진입
- MAJOR 시 todo 실패 마킹 (max 2 cycle 도달, 다른 todo 는 계속 진행)
