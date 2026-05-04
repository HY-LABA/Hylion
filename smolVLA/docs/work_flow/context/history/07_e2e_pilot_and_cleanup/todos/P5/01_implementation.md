# TODO-P5 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

활성 영역 `datacollector|smallgaint` 잔재 grep 종합 + 활성 잔재 제거 (Wave 1)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/interactive_cli/main.sh` | M | L16 `datacollector:` 노드 항목 → 운영 종료 주석으로 교체 |
| `orin/interactive_cli/flows/entry.py` | M | L88 docstring Return type `"datacollector"` 제거 / L137 spec인용 → 일반 설명 / L212 `dgx / datacollector` → `dgx` / L262 `(datacollector 전용)` 제거 |
| `dgx/interactive_cli/flows/entry.py` | M | L77 docstring Return type `"datacollector"` 제거 / L127 spec인용 → 일반 설명 / L219 `(datacollector 전용)` 제거 |
| `dgx/config/dataset_repos.json` | M | L2 comment `DataCollector -> DGX` → DGX 학습 데이터셋 + 운영종료 명시 / L13 rsync source `datacollector:` → `dgx:` |
| `dgx/config/README.md` | M | L1·L3·L31 `DataCollector ↔ DGX` 언급 → 현 2-노드 구조 반영 갱신 |
| `docs/storage/13_orin_cli_flow.md` | M | L150 `sync_ckpt_dgx_to_datacollector.sh` → `sync_ckpt_dgx_to_orin.sh` + 정정 주석 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불요 ✓
- `orin/pyproject.toml` 미변경 → `setup_env.sh`·`02_orin_pyproject_diff.md` 갱신 불요 ✓
- 레퍼런스 활용: 본 todo 는 코드 신규 작성 X, 잔재 텍스트 정리 작업

## Step 1 — grep 결과 (전체)

### orin/ 결과

```
orin/interactive_cli/main.sh:16:    datacollector: VENV_ACTIVATE 만 변경, cusparseLt 블록 없음
orin/interactive_cli/flows/entry.py:21: - VALID_NODES: ("orin", "dgx", "datacollector") → ("orin", "dgx")
orin/interactive_cli/flows/entry.py:22:   datacollector 노드 운영 종료 (06_dgx_absorbs_datacollector 결정 C·F).
orin/interactive_cli/flows/entry.py:23: - flow 0 datacollector 확인 분기 제거.
orin/interactive_cli/flows/entry.py:48: # 갱신 (2026-05-02, TODO-X2): datacollector 제거 (06 결정 C·F — 노드 운영 종료)
orin/interactive_cli/flows/entry.py:88:     {"node": "orin"|"dgx"|"datacollector", "venv": "~/..."} 또는 None.
orin/interactive_cli/flows/entry.py:121:   datacollector 분기 제거 (노드 운영 종료 — 06 결정 C·F).
orin/interactive_cli/flows/entry.py:137:   spec line 51: "본 노드인 datacollector 만 활성, 다른 노드는 안내만"
orin/interactive_cli/flows/entry.py:212:   dgx / datacollector: 후행 todo 에서 구현.
orin/interactive_cli/flows/entry.py:262:   # flow 0: 환경 확인 (datacollector 전용)
orin/interactive_cli/README.md:7~58: (이관·정정 주석 다수)
```

### dgx/ 결과 (주요 활성 잔재 후보만)

```
dgx/interactive_cli/flows/entry.py:77:     {"node": "orin"|"dgx"|"datacollector", "venv": "~/..."} 또는 None.
dgx/interactive_cli/flows/entry.py:127:   spec line 51: "본 노드인 datacollector 만 활성, 다른 노드는 안내만"
dgx/interactive_cli/flows/entry.py:219:   # flow 0: 환경 확인 (datacollector 전용)
dgx/config/dataset_repos.json:2:  "_comment": "DataCollector -> DGX 데이터셋 전송 설정..."
dgx/config/dataset_repos.json:13: "source": "datacollector:/home/user/..."
dgx/config/README.md:3: DataCollector 로부터 수신하는 HF 데이터셋...
dgx/config/README.md:31: "source": "<datacollector_host>:<dataset_local_path>",
(나머지: 이식 이력 주석, legacy 참조 — 의도됨)
```

### docs/storage/13_orin_cli_flow.md

```
docs/storage/13_orin_cli_flow.md:150: sync_ckpt_dgx_to_datacollector.sh 는 DGX_OUTPUTS/... 경로 구조를 그대로 DataCollector 로 전송
```

### scripts/, docs/lerobot_study/ 결과

```
(0건)
```

### 루트 파일 (pyproject.toml, Makefile) 결과

```
(0건)
```

## Step 2 — 발견 잔재 분류

### 분류 1 — 활성 잔재 (정리 대상, 총 10건)

| 파일 | 라인 | 내용 | 처리 방식 |
|---|---|---|---|
| `orin/interactive_cli/main.sh` | 16 | `datacollector: VENV_ACTIVATE 만 변경, cusparseLt 블록 없음` | 운영 종료 주석으로 교체 |
| `orin/interactive_cli/flows/entry.py` | 88 | docstring Return type에 `"datacollector"` | 현 VALID_NODES 반영 (`"orin"|"dgx"`) |
| `orin/interactive_cli/flows/entry.py` | 137 | `spec line 51: "본 노드인 datacollector 만 활성..."` | 원칙 설명으로 교체 (spec 인용 불필요) |
| `orin/interactive_cli/flows/entry.py` | 212 | `dgx / datacollector: 후행 todo 에서 구현` | `dgx:` 만으로 축소 |
| `orin/interactive_cli/flows/entry.py` | 262 | `# flow 0: 환경 확인 (datacollector 전용)` | `(datacollector 전용)` 제거 |
| `dgx/interactive_cli/flows/entry.py` | 77 | docstring Return type에 `"datacollector"` | 동일 처리 |
| `dgx/interactive_cli/flows/entry.py` | 127 | `spec line 51: "본 노드인 datacollector 만 활성..."` | 동일 처리 |
| `dgx/interactive_cli/flows/entry.py` | 219 | `# flow 0: 환경 확인 (datacollector 전용)` | 동일 처리 |
| `dgx/config/dataset_repos.json` | 2·13 | comment/rsync source에 `datacollector` 호스트명 | comment 갱신 + rsync source를 dgx 경로로 교체 |
| `dgx/config/README.md` | 3·19·31 | `DataCollector ↔ DGX` 설명, `<datacollector_host>` 스키마 | 현 2-노드 구조 반영 |
| `docs/storage/13_orin_cli_flow.md` | 150 | `sync_ckpt_dgx_to_datacollector.sh` 가 활성처럼 서술 | `sync_ckpt_dgx_to_orin.sh` 로 교체 + 정정 주석 |

### 분류 2 — 의도된 history 참조 (변경 X)

| 파일 | 성격 |
|---|---|
| `orin/interactive_cli/flows/entry.py` L21~23, L48, L121 | 갱신 이력 주석 (`갱신 (2026-05-02, TODO-X2)`) |
| `orin/interactive_cli/README.md` 전체 | 정정 주석, 이관 이력, 2-노드 전환 설명 |
| `dgx/interactive_cli/README.md` 전체 | 동일 패턴 |
| `dgx/interactive_cli/flows/entry.py` L17~18, L37, L110 | 갱신 이력 주석 |
| `dgx/scripts/push_dataset_hub.sh`, `run_teleoperate.sh` | 이식 이력 주석 (`원본: legacy/...`, `이식: 06_dgx_absorbs_datacollector`) |
| `dgx/interactive_cli/flows/record.py`, `teleop.py`, `data_kind.py` | 이식 이력, 원본 경로 비교 |
| `dgx/scripts/setup_train_env.sh` | 결정 이력 주석 |
| `dgx/interactive_cli/flows/training.py` | 인용 제거 이력 주석 |
| `dgx/interactive_cli/flows/mode.py`, `env_check.py`, `transfer.py` | 이식 패턴 참조 |
| `dgx/interactive_cli/configs/node.yaml` | 결정 이력 주석 |
| `docs/storage/02_hardware.md` §5 | DataCollector 실측 기록 보존 섹션 (`smallgaint` 호스트명) |
| `docs/storage/02_hardware.md` §5-2, §5-3 | MJPG 패턴, env_check 이식 패턴 — 역사적 구현 근거 |
| `docs/storage/03_software.md`, `04_devnetwork.md`, `08_orin_structure.md`, `09_dgx_structure.md` | 정정 주석, legacy 이관 기록 |
| `docs/storage/11_demo_site_mirroring.md` | 정정 주석 |
| `docs/storage/12_interactive_cli_framework.md` | 05 시점 3-노드 boilerplate 역사적 보존 |
| `docs/storage/14_dgx_cli_flow.md` | 이식 비교표 (`datacollector 원본 vs dgx 이식`) |
| `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` | legacy diff 파일명 자체 |
| `docs/storage/others/ckpt_transfer_scenarios.md` | legacy 케이스 3 역사적 보존 |
| `docs/storage/workflow_reflections/2026-05-02_05_*`, `2026-05-03_06_*` | 사이클 회고 보고서 |
| `docs/storage/README.md` | legacy 이관 색인 |
| `docs/work_flow/specs/README.md` | spec 이름 (`dgx_absorbs_datacollector`) 등록 |
| `docs/work_flow/context/plan.md` | 워크플로우 작업 문서 |
| `docs/work_flow/context/todos/P1/01_implementation.md`, `P2/`, `P3/`, `P4/` | 직전 todo 산출물 |

### 분류 3 — 모호 항목 (사용자 검토 권고)

없음. 모든 발견 항목이 명확하게 분류됨.

## Step 3 — 정리 내역 (변경 전/후)

### 1. `orin/interactive_cli/main.sh` L16

**Before:**
```
#   datacollector: VENV_ACTIVATE 만 변경, cusparseLt 블록 없음
```
**After:**
```
#   (datacollector 노드는 06_dgx_absorbs_datacollector 결정으로 운영 종료)
```

### 2. `orin/interactive_cli/flows/entry.py` L88 (docstring)

**Before:**
```python
        {"node": "orin"|"dgx"|"datacollector", "venv": "~/..."} 또는 None.
```
**After:**
```python
        {"node": "orin"|"dgx", "venv": "~/..."} 또는 None.
```

### 3. `orin/interactive_cli/flows/entry.py` L137 (spec 인용)

**Before:**
```python
    spec line 51: "본 노드인 datacollector 만 활성, 다른 노드는 안내만"
    — 이 규칙이 모든 노드에 공통 적용: 어느 노드에서 실행하든
      자신의 노드만 active, 나머지는 선택 불가 + 안내.
```
**After:**
```python
    원칙: 본 노드만 active, 다른 노드는 안내만.
    — 어느 노드에서 실행하든 자신의 노드만 active, 나머지는 선택 불가 + 안내.
```

### 4. `orin/interactive_cli/flows/entry.py` L212 (함수 docstring)

**Before:**
```python
    dgx / datacollector: 후행 todo 에서 구현.
```
**After:**
```python
    dgx: 후행 todo 에서 구현.
```

### 5. `orin/interactive_cli/flows/entry.py` L262 (인라인 주석)

**Before:**
```python
    # flow 0: 환경 확인 (datacollector 전용)
```
**After:**
```python
    # flow 0: 환경 확인
```

### 6. `dgx/interactive_cli/flows/entry.py` L77 (docstring)

**Before:**
```python
        {"node": "orin"|"dgx"|"datacollector", "venv": "~/..."} 또는 None.
```
**After:**
```python
        {"node": "orin"|"dgx", "venv": "~/..."} 또는 None.
```

### 7. `dgx/interactive_cli/flows/entry.py` L127 (spec 인용)

**Before:**
```python
    spec line 51: "본 노드인 datacollector 만 활성, 다른 노드는 안내만"
    — 이 규칙이 모든 노드에 공통 적용: 어느 노드에서 실행하든
      자신의 노드만 active, 나머지는 선택 불가 + 안내.
```
**After:**
```python
    원칙: 본 노드만 active, 다른 노드는 안내만.
    — 어느 노드에서 실행하든 자신의 노드만 active, 나머지는 선택 불가 + 안내.
```

### 8. `dgx/interactive_cli/flows/entry.py` L219 (인라인 주석)

**Before:**
```python
    # flow 0: 환경 확인 (datacollector 전용)
```
**After:**
```python
    # flow 0: 환경 확인
```

### 9. `dgx/config/dataset_repos.json` L2, L13

**Before:**
```json
"_comment": "DataCollector -> DGX 데이터셋 전송 설정 (placeholder). 실 값은 TODO-T1 결정 후 사용자가 채울 것.",
...
"source": "datacollector:/home/user/smolvla/.hf_cache/lerobot/${HF_USER}/example_dataset",
```
**After:**
```json
"_comment": "DGX 학습 데이터셋 설정 (placeholder). 실 값은 TODO-T1 결정 후 사용자가 채울 것. (06_dgx_absorbs_datacollector: DataCollector 노드 운영 종료 — rsync 방식은 hf_hub 로 통일)",
...
"source": "dgx:/home/laba/smolvla/dgx/data/${HF_USER}/example_dataset",
```

### 10. `dgx/config/README.md` L3, L19, L31

**Before:**
```
> 책임: DataCollector 로부터 수신하는 HF 데이터셋 repo_id 목록 등 ...
DataCollector ↔ DGX 데이터 전송 방식은 HF Hub + rsync 둘 다...
"source": "<datacollector_host>:<dataset_local_path>",
```
**After:**
```
> 책임: HF 데이터셋 repo_id 목록 등 ... (06_dgx_absorbs_datacollector 결정으로 DataCollector 노드 운영 종료 — DGX 가 데이터 수집 책임 흡수)
데이터 전송 방식은 HF Hub + rsync 둘 다...
"source": "<src_host>:<dataset_local_path>",
```

### 11. `docs/storage/13_orin_cli_flow.md` L150~152

**Before:**
```
`sync_ckpt_dgx_to_datacollector.sh` 는 `DGX_OUTPUTS/<run>/checkpoints/<step>/pretrained_model`
경로 구조를 그대로 DataCollector 로 전송. Orin 에 동일 구조로 복사되므로...
```
**After:**
```
`sync_ckpt_dgx_to_orin.sh` 는 `DGX_OUTPUTS/<run>/checkpoints/<step>/pretrained_model`
경로 구조를 그대로 Orin 으로 전송. Orin 에 동일 구조로 복사되므로...
<!-- 정정 (2026-05-03): sync_ckpt_dgx_to_datacollector.sh → legacy 이관 완료.
     현재 유효 스크립트: scripts/sync_ckpt_dgx_to_orin.sh (06_dgx_absorbs_datacollector 결정). -->
```

## Step 4 — 검증 결과

재실행 grep 후 활성 잔재 0건 확인. 남아있는 매치는 모두 분류 2 (의도된 history 참조):
- 갱신/정정 주석 (`갱신 (2026-05-02, TODO-X2):...`, `<!-- 정정 (2026-05-02):...`)
- 이식 이력 주석 (`원본: legacy/...`, `이식: 06_dgx_absorbs_datacollector`)
- legacy 이관 기록 (`docs/storage/README.md`, `docs/storage/lerobot_upstream_check/`)
- DataCollector 실측 기록 (`docs/storage/02_hardware.md §5`, `smallgaint` 호스트명)
- 사이클 회고 보고서 (`docs/storage/workflow_reflections/`)

## 분류 3 — 모호 항목 사용자 검토 권고

없음.

## code-tester 입장에서 검증 권장 사항

- bash -n: `bash -n /home/babogaeguri/Desktop/Hylion/smolVLA/orin/interactive_cli/main.sh`
- py_compile: `python3 -m py_compile /home/babogaeguri/Desktop/Hylion/smolVLA/orin/interactive_cli/flows/entry.py /home/babogaeguri/Desktop/Hylion/smolVLA/dgx/interactive_cli/flows/entry.py`
- ruff: `ruff check /home/babogaeguri/Desktop/Hylion/smolVLA/orin/interactive_cli/flows/entry.py /home/babogaeguri/Desktop/Hylion/smolVLA/dgx/interactive_cli/flows/entry.py`
- json 유효성: `python3 -m json.tool /home/babogaeguri/Desktop/Hylion/smolVLA/dgx/config/dataset_repos.json`
- 잔재 0건 재검증: `grep -rIn -E "datacollector|smallgaint" --include="*.sh" --include="*.py" --include="*.toml" --include="*.json" --include="*.md" /home/babogaeguri/Desktop/Hylion/smolVLA/orin/ /home/babogaeguri/Desktop/Hylion/smolVLA/dgx/ /home/babogaeguri/Desktop/Hylion/smolVLA/scripts/` — 의도된 이력 주석만 남아야 함 (갱신/정정/이식/이관/원본 패턴)
- DOD: `orin/`·`dgx/`·`scripts/`·`docs/`·루트 파일 활성 잔재 0건 ✓

---

## Cycle 2 (MINOR revisions) — 2026-05-03

> code-tester MINOR_REVISIONS (R#1, R#2) 처리. CLAUDE.md 정책상 재검증 없이 prod-test-runner 진입.

### R#1 처리 — `dgx/README.md`

**처리 방식**: (b) 의미 재작성 — "DataCollector ↔ DGX 인터페이스" 섹션을 현 3-노드(devPC + DGX + Orin) 구조 반영하여 재작성. 추가로 헤더 갱신 노트 (L5), L16, L44 도 동시 최신화.

**변경 1 — L5 헤더 갱신 노트 추가**

Before:
```
> 갱신: 04_infra_setup TODO-X2 (2026-05-01) — tests/, config/ 신규 디렉터리 추가 + DataCollector 인터페이스 안내 추가
```
After:
```
> 갱신: 04_infra_setup TODO-X2 (2026-05-01) — tests/, config/ 신규 디렉터리 추가 + 데이터 수집 인터페이스 안내 추가
> 갱신: 07_cleanup_datacollector_refs TODO-P5 (2026-05-03) — 06_dgx_absorbs_datacollector 결정 반영: DataCollector 노드 운영 종료, DGX 단일 노드 데이터 수집·학습 통합 구조로 갱신
```

**변경 2 — L16 entrypoint 설명 갱신**

Before:
```
- DGX 에서 직접 사용하는 entrypoint: `lerobot-train` 만 (나머지는 DataCollector / Orin 의 책임)
```
After:
```
- DGX 에서 직접 사용하는 entrypoint: `lerobot-train` 만 (데이터 수집·텔레오퍼레이션은 DGX 가 직접 담당, 추론은 Orin 의 책임)
```

**변경 3 — L44 dataset_repos.json 설명 갱신**

Before:
```
│   └── dataset_repos.json   # DataCollector 로부터 수신할 HF 데이터셋 repo_id 목록 (placeholder)
```
After:
```
│   └── dataset_repos.json   # DGX 학습에 사용할 HF 데이터셋 repo_id 목록 (placeholder)
```

**변경 4 — L184~202 섹션 재작성**

Before:
```markdown
## DataCollector ↔ DGX 인터페이스

DataCollector 로부터 학습 데이터를 수신하는 방식은 **HF Hub + rsync 둘 다** (TODO-T1 결정). ...

DataCollector:
  lerobot-record → 데이터셋 (LeRobotDataset 포맷)
      ↓
  HF Hub push ... 또는 rsync (TODO-T1 결정)
      ↓
DGX:
  lerobot-train ...
```
After:
```markdown
## DGX 단일 노드 데이터 수집·학습 인터페이스

<!-- 06_dgx_absorbs_datacollector 결정 (2026-05-03): DataCollector 노드 운영 종료.
     DGX 가 데이터 수집 + 학습 책임을 단일 노드에서 담당. -->

DGX 에서 직접 데이터 수집 후 학습을 진행한다. ...

DGX (데이터 수집):
  lerobot-teleoperate → 텔레오퍼레이션
  lerobot-record → 데이터셋 (LeRobotDataset 포맷)
      ↓
  HF Hub push 또는 로컬 저장
      ↓
DGX (학습):
  lerobot-train ...
      ↓
Orin (추론):
  sync_ckpt_dgx_to_orin.sh → Orin 체크포인트 배포
```

---

### R#2 처리 — `dgx/interactive_cli/flows/training.py` L284

**처리 방식**: 사용자 노출 print 문을 현 구조(DGX 단일 노드 수집) 반영 안내로 교체.

Before:
```python
print("  로컬 데이터셋이 없습니다. 먼저 DataCollector 에서 rsync 를 실행하세요.")
```
After:
```python
print("  로컬 데이터셋이 없습니다. DGX 에서 lerobot-record 로 데이터 수집 후 학습을 진행하세요.")
```

---

### 재 grep 결과 (Cycle 2 완료 후)

대상: `dgx/README.md`, `dgx/interactive_cli/flows/training.py`

```
dgx/README.md:6: → 갱신 이력 주석 (의도됨)
dgx/README.md:187: → HTML 주석 이력 (의도됨)
training.py:17,62,64,504: → 기존 이력 주석 (cycle 1 에서 의도된 history 참조로 분류됨)
```

활성 잔재 0건. 모두 이력/정정 주석 패턴.

**py_compile 회귀**: `python3 -m py_compile dgx/interactive_cli/flows/training.py` → PASS

---

### prod-test-runner 인계 사항

- CLAUDE.md 정책: MINOR_REVISIONS → task-executor 1회 수정 → code-tester 재검증 X → prod-test-runner 직행
- 변경 파일 2건: `dgx/README.md` (문서 갱신), `dgx/interactive_cli/flows/training.py` (사용자 안내 문구)
- 모두 Category B 외 영역 (lerobot/, pyproject.toml, setup_env.sh, deploy_*.sh 미해당)
- prod-test 권장:
  - `bash -n` + `py_compile` 전 파일 회귀 PASS 확인
  - grep 재검증: `grep -rIn -E "datacollector|smallgaint" dgx/README.md dgx/interactive_cli/flows/training.py` — 활성 잔재 0건
  - DOD 2 항목: `dgx/` 활성 잔재 0건 충족 확인
