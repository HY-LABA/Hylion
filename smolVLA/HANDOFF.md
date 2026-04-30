# HANDOFF — 다음 AI 를 위한 본 세션 (2026-04-30) 컨텍스트

> 본 문서는 2026-04-30 사용자 + AI 가 함께 진행한 작업의 핵심 결정·산출물·다음 액션을 정리. 새 AI 가 본 세션 컨텍스트를 빠르게 잡고 후속 작업 (TODO-O3 또는 TODO-X1) 에 진입할 수 있도록 함.
>
> 본 세션 이전 컨텍스트는 본 문서 §0 의 읽기 순서대로 기존 문서들을 참조.

---

## 0) 새 AI 가 읽어야 할 문서 — 읽는 순서

본 세션 컨텍스트만으로는 부족하므로, 다음 순서로 기존 문서를 함께 읽어야 한다.

### 0-1) 필수 (10분 이내)

1. **`CLAUDE.md`** (smolVLA 루트) — 프로젝트 운영 원칙, 핸드오프 워크플로우, 디렉터리 책임, coupled file 규칙
2. **`arm_2week_plan.md`** (smolVLA 루트) — 마일스톤 정의 (00~08). 각 마일스톤의 목표·고려사항·결정사항
3. **본 문서 (`HANDOFF.md`)** — 본 세션의 결정·산출물

### 0-2) 본 세션 직접 산출물 (30분)

4. **`docs/work_flow/specs/04_infra_setup.md`** — 현재 활성 스펙. 19개 TODO 중 3개 완료 (O1·O2·O2b), 16개 미완. **TODO-O3 가 다음 액션**
5. **`docs/storage/07_orin_structure.md`** — 본 세션 핵심 산출물. orin/ 디렉터리 책임 매트릭스 + 마이그레이션 계획. 본 세션 이후의 모든 orin/ 변경은 이 문서 §5 가 진실의 출처
6. **`docs/work_flow/specs/BACKLOG.md`** — 04 섹션 5건 신규 (#1~#5)

### 0-3) 직전 03 마일스톤 컨텍스트 (필요 시)

7. **`docs/work_flow/specs/history/03_smolvla_test_on_orin.md`** — 03 사이클 전체 흐름 + prod 검증 결과
8. **`docs/lerobot_study/07c_smolvla_base_test_results.md`** — 03 prod 검증 정성 기록 (실행 인자, 카메라 매핑, 행동 관찰)
9. **`docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`** — pyproject 변경 이력 (본 세션에서 entrypoint 2개 제거 이력 추가됨)
10. **`docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`** — orin/lerobot/ 변경 이력 (본 세션에서 옵션 B 원칙 명문화 추가)

### 0-4) memory (자동 로드)

`~/.claude/projects/c--Users-admin-Desktop-Hylion/memory/` 의 모든 .md 는 다음 세션 시작 시 자동 로드됨. 현재 1개:
- **`project_run_teleoperate_relocation.md`** — `orin/scripts/run_teleoperate.sh` 의 최종 위치 결정 후보 (a/b/c). 본 세션에서 임시 보관 위치 (`docs/storage/others/run_teleoperate.sh.archive`) 로 이동 처리 후 TODO-D2 시점에 최종 위치 결정 예정

### 0-5) 마일스톤 / 정책 가이드 (TODO 진행 시 참조)

- `docs/lerobot_study/03b_smolvla_milestone_config_guide.md` — 마일스톤별 SmolVLA config 분기. 05_leftarmVLA / 07_biarm_VLA 진입 시 필독
- `docs/lerobot_study/06_smolvla_finetune_feasibility.md` — DGX 학습 비용·자원 추정
- `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md` — 사전학습 데이터셋 구조 (카메라 키 매핑 등)

---

## 1) 본 세션의 큰 그림 — 4-노드 아키텍처 도입

### 1-1) 배경

03 마일스톤 종료 후 04 마일스톤 (`04_leftarmVLA`) 스펙 작성 진입. 그러나 사용자가 작성 중 **시연장 환경 미러링** 요구를 도입.

핵심 통찰 (사용자 발언):
> "smolVLA 학습 자체를 최대한 시연장과 비슷한 환경에서 진행해야 정확도가 올라간다. 그런데 dgx와 orin은 시연장과 떨어져 있어 매번 옮길 수 없다. 데이터 수집 컴퓨터를 따로 만들어야 할 것 같다."

이로 인해 기존 3-노드 (devPC + Orin + DGX) → **4-노드 아키텍처** 로 확장:

```
┌────────────┐   rsync   ┌──────────────────┐   dataset   ┌────────────┐
│  devPC     │──────────→│  DataCollector   │────────────→│ DGX Spark  │
│ (Windows)  │           │  (시연장 인근)    │             │  (학습)    │
│ 코드·문서   │           │  SO-ARM teleop +  │             │            │
│ 배포 hub    │           │  카메라 + 데이터   │             └─────┬──────┘
└─────┬──────┘           │  수집             │                   │ ckpt
      │                   └──────────────────┘                   │
      └───────────────────────────────────────→ ┌────────────────┴──┐
                                                │  Orin (시연장)     │
                                                │  추론 전용         │
                                                └───────────────────┘
```

### 1-2) 마일스톤 인덱스 변경

기존 04 (`04_leftarmVLA`) 가 너무 비대해져 분리:

| 변경 전 | 변경 후 |
|---|---|
| 04 leftarmVLA | **04 infra_setup** (구조 정리 + DataCollector 신설) |
| 05 biarm_teleop_on_dgx | 05 leftarmVLA (구 04 내용 그대로) |
| 06 biarm_VLA | 06 biarm_teleop (구 05) |
| 07 biarm_deploy | 07 biarm_VLA (구 06) |
| — | 08 biarm_deploy (구 07) |

`arm_2week_plan.md` + 활성 study/storage 문서 6개 + 메모리 모두 신 인덱스로 갱신 완료. **history/ 안 문서는 "당시 사실 보존" 으로 미갱신**.

---

## 2) 04 마일스톤 (`04_infra_setup`) 의 윤곽

`05_leftarmVLA` 진입 가능한 4-노드 인프라 셋업이 04 의 종착점.

### 2-1) 6 그룹 구조 (총 19 TODO)

| 그룹 | 책임 | TODO | 진행 |
|---|---|---|---|
| **O — orin 구조** | orin/ 정리 (lerobot 옵션B 트리밍, tests/·config/·checkpoints/·inference/ 신규) | O1, O2, O2b, O3 | **3/4 완료** |
| **X — dgx 구조** | dgx/ 정리 + orin 이관 자산 수용 | X1, X2, X3 | 0/3 |
| **D — DataCollector** | 신규 노드 셋업 (하드웨어·OS·venv·디렉터리) | D1, D2, D3 | 0/3 |
| **G — 환경 점검 게이트** | tests/check_hardware.sh — first-time/resume 두 모드 | G1, G2, G3, G4 | 0/4 |
| **M — 시연장 미러링** | 시연장 환경 재현 가이드 + 1차 셋업 | M1, M2 | 0/2 |
| **T — 데이터·ckpt 전송** | DataCollector→DGX 데이터 + DGX→Orin ckpt 경로 검증 | T1, T2, T3 | 0/3 |

### 2-2) 사용자 결정 사항 (스펙 진행 중 확정)

| 결정 항목 | TODO 위치 | 비고 |
|---|---|---|
| DataCollector 노드 정체 (하드웨어·OS) | TODO-D1 | 별도 PC vs 노트북 vs 시연장 PC |
| DataCollector 디렉터리 위치 | TODO-D1 | `datacollector/` 권장 |
| 데이터 전송 방식 | TODO-T1 | HF Hub vs rsync vs 둘 다 |
| 시연장 미러링 검증 깊이 | TODO-M1 | 육안+사진 vs 자동 검증 |

---

## 3) 본 세션에서 완료한 작업 — Orin 그룹 (O1, O2, O2b)

### 3-1) TODO-O1: orin/ 구조·기능 책임 매트릭스 + 마이그레이션 계획 (study)

**산출물**: `docs/storage/07_orin_structure.md` (신규, 6개 절 + 변경 이력)

핵심 발견:
- **`orin/lerobot/scripts/` 18 개 = upstream 18 개 그대로** — 한 번도 트리밍 안 됨
- 다른 모듈도 마찬가지 — 디렉터리/파일은 보존, **`__init__.py` 의 import 만 비활성화** 한 상태
- 사용자 원칙 "**upstream 구조 최대한 변형 안 함**" 과 정확히 부합

**옵션 B (논리적 비활성화) 채택**:
- `orin/lerobot/` 파일·디렉터리는 변경 X
- `orin/pyproject.toml [project.scripts]` 에서 entrypoint 등록 해제로만 비활성화
- 사유: upstream 동기화 부담 ↓

### 3-2) TODO-O2: orin/ 마이그레이션 실행 (task)

옵션 B 원칙대로 5개 카테고리 처리:

| 카테고리 | 처리 |
|---|---|
| 이관 (out) | `calibration/diagnose_motor_encoder.py` → `tests/`, `scripts/run_teleoperate.sh` → `docs/storage/others/run_teleoperate.sh.archive` (임시 보관) |
| 삭제 | `orin/calibration/` 디렉터리 (rmdir) |
| entrypoint 정리 | `orin/pyproject.toml` 에서 `lerobot-eval`, `lerobot-train` 2개 제거 (9개 유지) |
| 신규 | `orin/tests/`, `orin/config/`, `orin/checkpoints/` + 각 README + ports.json/cameras.json placeholder |
| .gitignore | Hylion 루트 `.gitignore` 에 `smolVLA/orin/checkpoints/*/` 패턴 추가 |
| coupled file | `02_orin_pyproject_diff.md` + `03_orin_lerobot_diff.md` 변경 이력 갱신 |

### 3-3) TODO-O2b: examples/ 책임 분리 (task)

TODO-O2 완료 후 사용자가 `orin/examples/` 책임 혼재 발견 (upstream 미러 + 본 프로젝트 5개 자산이 한 디렉터리).

**해결**:
- `orin/inference/` 신규 — 시연 환경 추론 운영 entry point + 향후 마일스톤별 정책 아카이빙 의도
- 5개 .py 이동 — `hil_inference.py` → `inference/`, 4개 검증/측정 스크립트 (`smoke_test`, `load_checkpoint_test`, `inference_baseline`, `measure_latency`) → `tests/`
- `orin/examples/tutorial/smolvla/` 에 `using_smolvla_example.py` 1개만 남아 upstream 미러 책임 명확화

### 3-4) 현재 orin/ 새 구조 (TODO-O2 + O2b 완료 후)

```
orin/
├── README.md
├── pyproject.toml                      # entrypoint 9개 (eval/train 제외)
├── lerobot/                            # ★ upstream 보존 — 변경 X (옵션 B)
├── scripts/setup_env.sh                # Jetson PyTorch wheel 직접 설치 (pyproject 분리 불가)
├── tests/
│   ├── README.md
│   ├── diagnose_motor_encoder.py       # 01 산출물 (TODO-O2 이관)
│   ├── smoke_test.py                   # 01 산출물 (TODO-O2b 이관)
│   ├── load_checkpoint_test.py         # 02 산출물 (TODO-O2b 이관)
│   ├── inference_baseline.py           # 03 산출물 (TODO-O2b 이관)
│   ├── measure_latency.py              # 03 산출물 (TODO-O2b 이관)
│   └── (TODO-G1 예정 — check_hardware.sh, configs/)
├── inference/                          # ★ 신규 — 시연 환경 운영 entry point
│   ├── README.md
│   └── hil_inference.py                # 03 산출물 (TODO-O2b 이관)
├── examples/tutorial/smolvla/
│   └── using_smolvla_example.py        # upstream 미러 (단일 파일)
├── config/
│   ├── README.md
│   ├── ports.json                      # placeholder (TODO-G1 first-time 모드가 채움)
│   └── cameras.json                    # placeholder
└── checkpoints/                        # gitignore (README 만 추적)
    └── README.md
```

---

## 4) 본 세션에서 만든 메모리

### 4-1) 활성 메모리

- **`project_run_teleoperate_relocation.md`** — `orin/scripts/run_teleoperate.sh` 의 최종 위치 결정 후보 정리. 본 세션에서 임시 보관 (`docs/storage/others/run_teleoperate.sh.archive`) 로 옮긴 후 TODO-D2 진입 시 최종 결정 (DataCollector 후보 a 가장 유력)

### 4-2) 삭제된 메모리 (참고)

- ~~`project_04_leftarmVLA_seed_todos.md`~~ — 04 스펙 신설 후 흡수되어 archive 처리. 04 스펙이 진실의 출처가 됨

---

## 5) BACKLOG.md 04 섹션 신규 항목 5건

| # | 항목 | 우선순위 | 출처 |
|---|---|---|---|
| 1 | upstream 동기화 시 `pyproject.toml [project.scripts]` 의 entrypoint 정리 (lerobot-eval/lerobot-train 제거) 가 덮어씌워질 수 있음 | 중간 | TODO-O1 |
| 2 | run_teleoperate.sh 임시 보관 위치 컨벤션 — `.archive` 확장자 일관 적용 검토 | 낮음 | TODO-O1 |
| 3 | `orin/config/ports.json`, `cameras.json` 의 git 추적 vs gitignore 정책 결정 | 낮음 | TODO-O1 |
| 4 | `orin/examples/tutorial/smolvla/` 1개 파일 디렉터리 평탄화 검토 (upstream 보존 원칙대로면 그대로 유지가 자연스러움) | 낮음 | TODO-O2b |
| 5 | `orin/inference/` 하위 구조 (archive/, milestone 별 디렉터리) 결정 — 05 TODO-14 진입 시 검토 | 낮음 (05 트리거 시 중간) | TODO-O2b |

기존 03 BACKLOG 의 "높음" 미완 항목 5건 (`#1`, `#2`, `#15`, `#16` + 01 `#1`) 은 변경 없음 — 모두 05_leftarmVLA 진입 시 트리거.

---

## 6) 다음 액션 — 새 AI 가 결정해야 할 것

본 세션 종료 시점에 사용자에게 두 가지 옵션 제안 후 답변 보류 상태.

### 옵션 A: Orin 그룹 클로징 (TODO-O3)

- 사용자가 devPC 로 이동 → `bash scripts/deploy_orin.sh` 일괄 배포
- Orin 측 `pip install -e ~/smolvla/orin/[smolvla,hardware,feetech]` 재설치 (entrypoint 갱신)
- 6개 .py 새 경로 실행 검증 + 4개 README 존재 확인 + `which lerobot-eval lerobot-train` 결과 없음 확인
- TODO-O3 `/handoff-test` 진입

### 옵션 B: DGX 그룹 study 먼저 (TODO-X1) — **AI 추천**

- 배포 대기 동안 study 작업 진행 — 본 환경에서 즉시 가능
- Orin 패턴 (`07_orin_structure.md`) 이 신선해서 dgx 도 빠르게 정리
- TODO-X1 + X2 까지 끝내면 배포 시점에 dgx + orin 변경을 한꺼번에 푸시 가능 (배포 횟수 ↓)

**사용자 결정 대기 중**. 본 문서 작성 시점에는 미결.

### 4-노드 아키텍처 진입의 다른 의존성

옵션 B 진행 시에도 결국 다음 그룹들이 줄지어 있음:
- TODO-D1 (DataCollector 노드 정체 결정) — **사용자 답변 필수** — 새 PC vs 노트북 vs 시연장 PC
- TODO-T1 (데이터 전송 방식) — **사용자 답변 필요** — HF Hub 추천
- TODO-M1 (시연장 미러링 가이드) — 시연장 접근 가능 시점에 의존

---

## 7) 본 세션에서 합의된 운영 원칙 (새 AI 가 따라야 할 것)

본 세션 대화 중 사용자가 명시적으로 합의한 원칙들. 후속 작업에서도 유지.

### 7-1) upstream 구조 보존 원칙 (옵션 B)

`orin/lerobot/` 의 파일·디렉터리는 변경하지 않는다. inference-only 책임 외 모듈은 다음으로만 비활성화:
1. `__init__.py` 의 import 차단
2. `pyproject.toml [project.scripts]` 의 entrypoint 등록 해제

→ `dgx/lerobot/` 도 동일 원칙 적용 예상 (TODO-X1 진행 시 확인)

### 7-2) PyTorch 위치 — setup_env.sh 유지

Jetson 제약상 PyTorch 는 pyproject.toml 이 아닌 setup_env.sh 에서 NVIDIA redist URL 로 직접 설치. 사유: PyPI 의 일반 wheel 이 CPU-only 라 pyproject 에 두면 덮어쓰기 발생. 본 결정은 `orin/pyproject.toml:11-13` 의 주석 + `setup_env.sh:74-77` 에 명시.

### 7-3) lerobot 캘리브레이션 표준 위치

`~/.cache/huggingface/lerobot/calibration/<robot_id>.json` (lerobot 표준) 그대로 사용. `orin/config/` 는 본 프로젝트 자체 cached config (ports.json, cameras.json) 만 관리. 복사·심볼릭 링크 X.

### 7-4) 시연장 환경 미러링 = 학습 정확도의 핵심

DataCollector 가 시연장을 얼마나 정확히 재현하느냐가 05_leftarmVLA / 07_biarm_VLA 의 성패. 04 의 그룹 M 이 본 사항을 가이드.

### 7-5) history 문서는 "당시 사실 보존" — 갱신 안 함

마일스톤 인덱스 변경 시 활성 문서는 갱신하나 history/ 안 문서는 그대로 둠. 새 AI 가 history 문서를 읽을 때는 **그 시점의 마일스톤 번호와 현재의 마일스톤 번호가 다를 수 있다** 는 점 인지 필요.

---

## 8) 본 세션 워크플로우 흐름 — 새 AI 도 같은 패턴 유지

본 프로젝트는 다음 4 슬래시 커맨드로 운영:

| 커맨드 | 책임 |
|---|---|
| `/handoff-task` | 활성 스펙의 미완 task TODO 를 `current_task.md` 로 핸드오프 |
| `/complete-task` | `current_task.md` 의 업데이트 섹션을 스펙에 반영 + history 보관 |
| `/handoff-test` | 활성 스펙의 미완 test TODO 핸드오프 |
| `/complete-test` | test 결과를 스펙에 반영 + history 보관 |

본 세션에서는 사용자가 코딩을 본 AI 와 함께 진행 (Copilot 미사용). prod 검증은 사용자가 Codex 와 함께 진행 — 본 세션은 task / study 중심.

### 본 세션 완료된 핸드오프 사이클

1. `/handoff-task` TODO-O1 → 산출물 작성 → `/complete-task`
2. `/handoff-task` TODO-O2 → 마이그레이션 실행 → `/complete-task`
3. (사용자가 examples/ 책임 혼재 발견 → TODO-O2b 신설) → `/handoff-task` TODO-O2b → 이동 작업 → `/complete-task`

배포는 사용자가 추후 일괄 (devPC 측에서) — 본 세션 시점 미실행.

---

## 9) 빠른 진입 체크리스트 (새 AI 가 첫 응답 전 검증)

1. ☐ `CLAUDE.md` 읽음 — 프로젝트 운영 원칙 인지
2. ☐ `arm_2week_plan.md` 읽음 — 마일스톤 정의 인지
3. ☐ 본 `HANDOFF.md` 끝까지 읽음
4. ☐ `04_infra_setup.md` 읽음 — 활성 스펙. 19 TODO 중 3 완료
5. ☐ `07_orin_structure.md` 읽음 — orin/ 구조 진실의 출처
6. ☐ memory `project_run_teleoperate_relocation.md` 인지 (자동 로드됨)
7. ☐ 사용자에게 "옵션 A (TODO-O3) vs 옵션 B (TODO-X1) 중 어느 쪽으로 진행?" 확인 (본 세션 종료 시점에 답변 보류 상태)
8. ☐ 새 마일스톤·TODO 진입 시 §7 의 5개 운영 원칙 준수

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-30 | 초안 작성 — 본 세션 (orin 구조 정리 + 4-노드 아키텍처 도입) 컨텍스트 정리 |
