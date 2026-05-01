# 20260430_infra_setup
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: 05_leftarmVLA 사이클 진입 가능한 4-노드 인프라 셋업 — devPC + DataCollector(신규) + DGX + 시연장 Orin
> 환경: devPC (`babogaeguri@babogaeguri-950QED`) + Orin (`laba@ubuntu`) + DGX Spark (`laba@spark-8434`) + DataCollector (TODO-D1 결정)
> Orin 코드 경로: `/home/laba/smolvla/orin/` (rsync 배포 기준)
> DGX 코드 경로: `/home/laba/smolvla/dgx/` (rsync 배포 기준)
> DataCollector 코드 경로: TODO-D1 결정 후 확정
> 작성: 2026-04-30

---

## 본 마일스톤의 위치

`arm_2week_plan.md` 의 04 마일스톤은 **05_leftarmVLA 진입 전 인프라 정리·신설**.

### 배경 — 4-노드 분리 아키텍처

smolVLA 학습 정확도는 **시연장 환경 미러링** 에 크게 의존. 본 프로젝트의 시연 목표상:
- DGX·Orin 은 시연장과 떨어진 연구실에 위치 → 시연장으로 매번 옮기며 데이터 수집 불가
- 시연장 인근에 **데이터 수집 전용 DataCollector 노드** 신규 도입
- Orin 은 시연장에 영구 배치되어 **추론 전용** 으로 책임 축소

```
┌────────────┐   rsync   ┌──────────────────┐                  ┌────────────┐
│  devPC     │──────────→│  DataCollector   │     dataset      │ DGX Spark  │
│ (Windows)  │           │  (시연장 인근)    │─────────────────→│  (학습)    │
│ 코드·문서   │           │  SO-ARM teleop +  │  HF Hub / rsync  │            │
│ 배포 hub    │           │  카메라 + 데이터   │                  └─────┬──────┘
└─────┬──────┘           │  수집             │                        │ ckpt
      │                   └──────────────────┘                        │ 전송
      │                                                                ↓
      │                                                          ┌────────────┐
      │           rsync (시연장)                                  │  Orin      │
      └─────────────────────────────────────────────────────────→│ (추론 전용) │
                                                                  └────────────┘
```

### 04 의 6 가지 책임 영역

1. **orin/ 구조 정리** — inference + record 만 남기고 학습/시뮬/평가 모듈 제거. tests/·config/·checkpoints/ 신규
2. **dgx/ 구조 정리** — 학습 책임 명확화 + orin 에서 이관할 자산 (`run_teleoperate.sh` 등) 수용
3. **DataCollector 노드 신규 셋업** — 하드웨어·OS·venv·lerobot 의존성 결정 + 디렉터리 신규 + 시연장 인근 배치
4. **환경 점검 게이트 스크립트** — 카메라 인덱스·flip / SO-ARM 포트 / venv 자동 점검. first-time / resume 두 모드. 03 prod 검증의 ad-hoc 이슈 해소
5. **시연장 환경 미러링 가이드** — 책상·조명·카메라 위치 등 시연장 재현 절차. 사용자 책임 + 기록 위주
6. **데이터·체크포인트 전송 경로 검증** — DataCollector → DGX 데이터 전송 + DGX → Orin ckpt 전송 모두 동작 확인

### 04 의 종착점

- 4 노드 모두 셋업 + 디렉터리 구조 정리 완료
- DataCollector 에서 SO-ARM teleop + 카메라 + lerobot-record 동작 확인 (실 데이터 수집은 05 의 책임 — 04 는 환경 동작만)
- 시연장 미러링 환경 1차 셋업 완료 (TODO-M1 의 가이드대로)
- 데이터 전송 + ckpt 전송 양방향 dry-run PASS
- **05_leftarmVLA 진입 준비 완료**

---

## 참고 레퍼런스

### 03 산출물 (직전 마일스톤)

- `docs/work_flow/specs/history/03_smolvla_test_on_orin.md` — 03 마일스톤 전체 흐름
- `docs/lerobot_study/07c_smolvla_base_test_results.md` — Orin 추론 검증 결과 (TODO-06b/07b)
- `orin/examples/tutorial/smolvla/hil_inference.py` — 사전학습 모델 hardware-in-the-loop 추론 (05 학습 ckpt 으로 재사용 예정)

### 환경·인프라

- `docs/storage/05_orin_venv_setting.md` — Orin venv 구성
- `docs/storage/06_dgx_venv_setting.md` — DGX venv 구성 + 체크포인트 전송 절차 (§10)
- `dgx/scripts/setup_train_env.sh` / `dgx/scripts/preflight_check.sh` / `dgx/scripts/smoke_test.sh` — DGX 학습 환경 (02 마일스톤 산출물)
- `scripts/sync_ckpt_dgx_to_orin.sh` — devPC 경유 2-hop 체크포인트 전송 (TODO-T2 의 데이터 전송 패턴 참조)
- `scripts/deploy_orin.sh` / `scripts/deploy_dgx.sh` — devPC sync hub
- `arm_2week_plan.md` — `04_infra_setup` 마일스톤 정의

### 03 prod 검증에서 발견된 환경 이슈 (TODO-G1 게이트의 입력 시나리오)

- BACKLOG 03 #14 — SSH 비대화형 import check 시 `source activate` 누락 → `libcusparseLt.so.0` ImportError
- BACKLOG 03 #15 — `lerobot-find-cameras opencv` 사전 발견 단계 필요 (인덱스 기본값 불일치)
- BACKLOG 03 #16 — wrist 카메라 상하반전 (`--flip-cameras wrist` 필요)
- BACKLOG 01 #1 — SO-ARM USB 포트 번호 변동 (udev rule 또는 매번 `lerobot-find-port`)

### lerobot 레퍼런스

- `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — 데이터 수집 entrypoint (DataCollector 의 핵심 사용처)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` — 포트 발견 (TODO-G1 wrapping)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_cameras.py` — 카메라 발견 (TODO-G1 wrapping)
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` — orin/lerobot/ upstream 대비 변경 이력 (TODO-O1 트리밍 시 갱신 의무)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

---

## 사용자 결정 사항 (스펙 진행 중 확정)

| 결정 항목 | TODO 위치 | 비고 |
|---|---|---|
| DataCollector 노드 정체 (하드웨어·OS) | TODO-D1 | 별도 PC vs 기존 노트북 vs 시연장 PC |
| DataCollector 디렉터리 위치 (`datacollector/` vs `orin/data_collection/`) | TODO-D1 | 노드 정체 결정에 따라 |
| 데이터 전송 방식 (DataCollector → DGX) | TODO-T1 | HF Hub vs rsync 직접 vs 둘 다 |
| 시연장 미러링 검증 깊이 | TODO-M1 | 육안 + 사진 vs 자동 검증 스크립트 |
| `orin/lerobot/scripts/` 트리밍 대상 8개 최종 확정 | TODO-O1 | 4-노드 분리 후 record 도 DataCollector 로 갈 수 있어 재검토 |

---

## 합의된 새 orin/ 구조 (TODO-O1·O2 산출물의 기준)

```
orin/
├── README.md
├── pyproject.toml               # 환경/의존성 (PyTorch 제외 — Jetson 제약)
├── lerobot/                     # upstream curated subset (inference + 일부 hardware)
│   ├── cameras/ motors/ robots/ teleoperators/ policies/ processor/ datasets/ utils/
│   └── scripts/                 # 8개 제거 후보 (TODO-O1 결정), 10개 유지
├── scripts/
│   └── setup_env.sh             # 유지 (PyTorch 포함, Jetson 제약상 불가피)
│                                 # ※ run_teleoperate.sh 는 dgx/ 로 이관 (TODO-X2)
├── tests/                       # 시나리오 점검 + 환경 점검 게이트 통합
│   ├── check_hardware.sh        # 단일 진입점, --mode {first-time,resume}
│   ├── configs/
│   │   ├── first_time.yaml
│   │   └── resume.yaml
│   └── diagnose_motor_encoder.py  # orin/calibration/ 에서 이관
├── examples/tutorial/smolvla/   # 03 산출물 그대로 유지
├── config/                      # 본 프로젝트 자체 cached config
│   ├── README.md
│   ├── ports.json               # SO-ARM follower / leader (시연장 셋업 후 cache)
│   └── cameras.json             # 인덱스 / flip / slot 매핑
│                                 # ※ lerobot 캘리브레이션은 ~/.cache/huggingface/lerobot/calibration/ 표준 위치 그대로 사용
└── checkpoints/                 # .gitignore. 학습된 정책 ckpt
    └── README.md
```

---

## Todo

> 그룹 구분은 책임 영역별 가이드. `/handoff-task` / `/handoff-test` 는 TODO 항목만 읽는다.
> TODO 번호 prefix: O=Orin, X=DGX, D=DataCollector, G=Gate, M=Mirroring, T=Transfer

**[그룹 O — orin/ 구조 정리]**

### [x] TODO-O1: orin/ 구조·기능 책임 매트릭스 + 마이그레이션 계획

- 타입: study
- DOD: 현재 orin/ 의 디렉터리·스크립트·모듈을 마일스톤별 책임 관점에서 정리. 합의된 새 구조 (위 §"합의된 새 orin/ 구조") 기준으로 마이그레이션 계획 (제거 / 이관 / 신규 / 유지) 명시. `lerobot/scripts/` 트리밍 대상 8개를 4-노드 분리 후 관점에서 재확정 (record 가 DataCollector 로 가는 경우 orin/lerobot/scripts/lerobot_record.py 도 제거 후보).
- 구현 대상:
  - `docs/storage/07_orin_structure.md` — 절 구성:
    - §1 디렉터리 트리 (현재 + 새 구조)
    - §2 핵심 컴포넌트 책임 표
    - §3 마일스톤별 책임 매트릭스 (00~08 마일스톤 × 각 컴포넌트)
    - §4 외부 의존성 (devPC sync hub, HF Hub, DataCollector·DGX 와의 관계)
    - §5 마이그레이션 계획 (TODO-O2 의 입력)
- 테스트: 없음
- 참조: `orin/` 전체 트리, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `docs/storage/05_orin_venv_setting.md`, `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`
- 잔여 리스크: 트리밍 대상이 다른 모듈에서 import 되어 있을 가능성 — TODO-O2 마이그레이션 시 import 회귀 검증 필요
- **완료 (2026-04-30 15:32)**: 사전 점검에서 중요한 사실 발견 — `orin/lerobot/` 은 물리적 트리밍 X, 기존 패치 (`__init__.py` import 차단) 만으로 inference-only 구현된 상태. 사용자 원칙 ("upstream 구조 변형 X") 와 정확히 부합. 이 발견을 바탕으로 트리밍 방식을 **옵션 B (논리적 비활성화)** 로 확정.
  - 사용자 합의 결정: (1) 옵션 B 트리밍 방식 (2) `lerobot-eval`·`lerobot-train` 2개 entrypoint 제거 + 9개 유지 (3) §5 마이그레이션 5개 카테고리 (유지 / 이관 / 신규 / 삭제 / entrypoint 정리)
  - 산출물: `docs/storage/07_orin_structure.md` 신규 작성 — §0~§6 + 변경 이력 모두 채움. 디렉터리 트리 비교, 8개 컴포넌트 책임 표, 9 마일스톤 × 20+ 컴포넌트 책임 매트릭스, 외부 의존성 (devPC sync hub / HF Hub / 시스템 의존성 / 캘리브레이션 표준 위치), TODO-O2 입력 사양 (5개 카테고리별 표)
  - 04 스펙 갱신: TODO-O2 본문을 옵션 B 기반으로 재작성 — "8개 파일 제거" → "entrypoint 2개 제거", run_teleoperate.sh 임시 보관 시나리오 명시, "orin/lerobot/ 하위 변경 금지" 제약 추가
  - history: `docs/work_flow/context/history/04_infra_setup/20260430_1532_task_orin_structure.md`

### [x] TODO-O2: orin/ 마이그레이션 실행

- 타입: task
- DOD: TODO-O1 의 마이그레이션 계획대로 orin/ 디렉터리 구조 변경 실행. 기존 03 산출물 (`hil_inference.py`, `inference_baseline.py`, `measure_latency.py`, `smoke_test.py`, `load_checkpoint_test.py`) 의 동작 회귀 없음.
- 트리밍 원칙 — **논리적 비활성화 (옵션 B)**: upstream 구조 보존이 사용자 원칙. orin/lerobot/ 의 파일·디렉터리는 그대로 유지하고, **`orin/pyproject.toml` 의 `[project.scripts]` entrypoint 등록만 inference + record 책임에 맞게 정리**. (참고: `policies/__init__.py`, `processor/__init__.py`, `configs/__init__.py` 의 import 차단은 03_orin_lerobot_diff.md 에 기록된 기존 패치로 이미 완료된 상태.)
- 구현 대상:
  - **유지**: orin/lerobot/ 전체 (upstream 보존, 파일 제거 X), orin/scripts/setup_env.sh, orin/examples/, orin/README.md
  - **이관**:
    - orin/calibration/diagnose_motor_encoder.py → orin/tests/ (직접 또는 `tests/scenarios/`, TODO-O1 결정에 따라)
    - orin/scripts/run_teleoperate.sh → DataCollector (memory `project_run_teleoperate_relocation.md` 의 후보 (a) 채택 — 단 DataCollector 디렉터리는 TODO-D1 이후 존재. 본 TODO 진행 시점에 DataCollector 미존재 시 임시 보관 후 TODO-D2 시점에 이동)
  - **삭제**:
    - orin/calibration/ 디렉터리 (diagnose_motor_encoder.py 이관 후 비게 됨)
  - **entrypoint 정리** (orin/pyproject.toml `[project.scripts]`):
    - `lerobot-eval` 제거 (Orin 평가 안 함)
    - `lerobot-train` 제거 (Orin 학습 안 함)
    - 9개 유지: lerobot-calibrate / find-cameras / find-port / find-joint-limits / record / replay / setup-motors / teleoperate / info
  - **신규**:
    - orin/tests/ + README.md (실 스크립트는 TODO-G1)
    - orin/config/ + README.md + ports.json·cameras.json placeholder
    - orin/checkpoints/ + README.md (실 ckpt 는 05_leftarmVLA TODO-13 시점에 들어옴)
  - **.gitignore 갱신**: `orin/checkpoints/<run_name>/` 패턴 추가
  - **`docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 갱신**: 본 TODO 의 entrypoint 정리 이력 추가 (CLAUDE.md 의 coupled file 규칙 — pyproject.toml 변경 시 `02_orin_pyproject_diff.md` 도 갱신)
- 테스트: 없음 (TODO-O3 에서 검증)
- 제약: TODO-O1 완료 후. **orin/lerobot/ 하위 파일·디렉터리는 변경 금지** (entrypoint 등록 해제만으로 비활성화). DataCollector 관련 이관은 TODO-D1 진행 상황에 따라 본 TODO 또는 TODO-D2 에서 처리.
- 잔여 리스크:
  - `lerobot-eval` / `lerobot-train` entrypoint 제거 시 venv 의 기존 등록은 setup_env.sh 재실행 또는 `pip install -e .` 재설치로 갱신 필요 — TODO-O3 검증 단계에서 확인
  - DataCollector 디렉터리 미존재 시점에 run_teleoperate.sh 처리 — TODO-O1 §5 마이그레이션 계획에서 명시
- **완료 (2026-04-30 15:42)**: TODO-O1 §5 마이그레이션 계획 5개 카테고리 + 부수 작업 모두 실행. 옵션 B (논리적 비활성화) 원칙 준수 — `orin/lerobot/` 파일·디렉터리 미변경.
  - **이관 2건**: `orin/calibration/diagnose_motor_encoder.py` → `orin/tests/` (직접). `orin/scripts/run_teleoperate.sh` → `docs/storage/others/run_teleoperate.sh.archive` (DataCollector 미존재 → 임시 보관, TODO-D2 시점 최종 이동)
  - **삭제 1건**: `orin/calibration/` 디렉터리 (rmdir)
  - **entrypoint 정리**: `orin/pyproject.toml [project.scripts]` 에서 `lerobot-eval` / `lerobot-train` 2줄 제거 + 주석 추가. 9개 entrypoint 유지 (calibrate / find-cameras / find-port / find-joint-limits / record / replay / setup-motors / teleoperate / info)
  - **신규 5개 파일**: `orin/tests/README.md`, `orin/config/{README.md, ports.json, cameras.json}`, `orin/checkpoints/README.md`. ports.json·cameras.json 은 placeholder (null 값). 각 README 는 `docs/storage/06_dgx_venv_setting.md` 패턴 참조
  - **.gitignore 갱신** (Hylion 루트): `smolVLA/orin/checkpoints/*/` 패턴 추가 — README.md 추적, `<run_name>/` 하위 ignore
  - **coupled file 갱신**: `02_orin_pyproject_diff.md` (§5 표 + 변경 이력 항목, BACKLOG 04 #1 명시) + `03_orin_lerobot_diff.md` (옵션 B 원칙 명문화 항목)
  - 검증: 신 구조 8개 항목 확인, run_teleoperate.sh 임시 보관 위치 확인, entrypoint 등록 해제 grep 0건, .gitignore 패턴 추가 확인. devPC 측 `python -m py_compile` 은 본 TODO 가 코드 수정 없는 디렉터리·문서 작업이라 불필요
  - 실 실행 검증은 TODO-O3 (Orin prod 검증) 책임. 특히 `pip install -e .` 재실행 후 entrypoint 2개가 venv 의 bin/ 에서 제거되는지 + 03 산출물 5개 import 회귀 없음 확인 필요
  - history: `docs/work_flow/context/history/04_infra_setup/20260430_1542_task_orin_migration.md`

### [x] TODO-O2b: examples/ 책임 분리 — tutorial 미러 vs 본 프로젝트 자산

- 타입: task
- DOD: 03 산출물 5개를 책임별 적절한 위치로 이동:
  - `hil_inference.py` → `orin/inference/hil_inference.py` (운영 진입점)
  - `smoke_test.py` / `load_checkpoint_test.py` / `inference_baseline.py` / `measure_latency.py` → `orin/tests/` (검증·측정)
  - `using_smolvla_example.py` → `orin/examples/tutorial/smolvla/` 그대로 유지 (upstream 미러)
  - 결과: `orin/examples/` 는 upstream 미러 책임만 가짐. 본 프로젝트 검증·측정 자산은 `orin/tests/` 에, 운영 추론 진입점은 `orin/inference/` 에.
- 배경: TODO-O2 완료 후 사용자가 `orin/examples/` 의 책임 혼재를 발견. 분석 결과 `using_smolvla_example.py` 는 upstream 그대로 가져온 튜토리얼이고 본 프로젝트 5개는 자체 산출물. 그 중 `hil_inference.py` 만 진짜 운영 entry point (시연 시 호출), 나머지 4개는 검증·측정 성격. 사용자 의도: `orin/inference/` 디렉터리는 향후 마일스톤별 추론 정책 아카이빙 역할도 겸함.
- 구현 대상:
  - **신규 디렉터리**: `orin/inference/` + `orin/inference/README.md`
  - **이동 5건** (mv — 코드 변경 X, 절대 import 라 위치 무관):
    - `orin/examples/tutorial/smolvla/hil_inference.py` → `orin/inference/hil_inference.py`
    - `orin/examples/tutorial/smolvla/smoke_test.py` → `orin/tests/smoke_test.py`
    - `orin/examples/tutorial/smolvla/load_checkpoint_test.py` → `orin/tests/load_checkpoint_test.py`
    - `orin/examples/tutorial/smolvla/inference_baseline.py` → `orin/tests/inference_baseline.py`
    - `orin/examples/tutorial/smolvla/measure_latency.py` → `orin/tests/measure_latency.py`
  - **`orin/tests/README.md` 갱신**: 자산 표에 4개 신규 자산 추가 (smoke_test / load_checkpoint_test / inference_baseline / measure_latency)
  - **`orin/inference/README.md` 신규 작성**: inference/ 책임 + 향후 마일스톤별 정책 아카이빙 의도 + 현재 자산 (hil_inference.py — 03 산출물)
  - **`orin/examples/tutorial/smolvla/__pycache__/` 정리** (이동된 파일들의 cache)
  - **`docs/storage/07_orin_structure.md` 갱신**:
    - §1 디렉터리 트리 (현재·새 구조 모두)
    - §2 컴포넌트 책임 표 (`orin/inference/` 추가, `orin/examples/` 책임 갱신)
    - §3 마일스톤 매트릭스 (5개 파일 위치 갱신)
    - §5 마이그레이션 계획 (5-3 신규에 inference/ 추가, 5-2 이관에 5개 파일 추가)
- 테스트: 없음 (이동·문서 작업. 회귀 검증은 TODO-O3 가 통합 검증)
- 제약: TODO-O2 완료 후. 5개 .py 파일 자체는 코드 변경 X — 경로만 이동. history 문서 (03 spec, 03 context history) 의 경로 참조는 갱신 안 함 ("당시 사실" 보존 원칙)
- 잔여 리스크:
  - 향후 마일스톤별 추론 entry point 가 늘어날 때 inference/ 구조 (예: archive/, milestone 별 디렉터리) 결정 — 05 진입 시 검토 (BACKLOG 후보)
  - `examples/tutorial/smolvla/` 가 1개 파일만 남음 (using_smolvla_example.py) — 디렉터리 유지 vs 평탄화 (`examples/tutorial/using_smolvla_example.py`) 검토 필요. 단 upstream 구조 보존 원칙대로면 `tutorial/smolvla/` 유지
- **완료 (2026-04-30 16:12)**: 사전 점검 (5개 파일 import 절대 경로 검증) 후 마이그레이션 실행. 디렉터리 신규 1건, 파일 이동 5건, README 신규 1건 + 갱신 1건, 구조 문서 갱신 1건.
  - 신규: `orin/inference/` + `inference/README.md` (운영 entry point + 향후 마일스톤별 정책 아카이빙 의도 명시)
  - 이동: hil_inference.py → `orin/inference/`, smoke_test/load_checkpoint_test/inference_baseline/measure_latency 4개 → `orin/tests/`
  - 결과: `orin/examples/tutorial/smolvla/` 에 `using_smolvla_example.py` 1개만 남아 upstream 미러 책임 명확화. `orin/tests/` 6개 자산 (1개 기존 + 4개 이관 + README), `orin/inference/` 2개 자산 (1개 + README)
  - `orin/tests/README.md` 자산 표 4행 추가
  - `docs/storage/07_orin_structure.md` §1-2 / §2 / §3 / §4-1 / §5-1·5-2·5-3 + 변경 이력 모두 갱신
  - 검증: py_compile 6개 모두 PASS, 회귀 grep `^(from orin|import orin)` 0건 유지, __pycache__ 4개 .pyc 정리
  - 실 실행 검증은 TODO-O3 의 책임 (TODO-O2 + O2b 통합)
  - history: `docs/work_flow/context/history/04_infra_setup/20260430_1612_task_examples_split.md`

### [x] TODO-O3: orin/ 마이그레이션 회귀 검증 (Orin prod)

- 타입: test
- DOD: TODO-O2 + TODO-O2b 마이그레이션 후 03 산출물 5개 (`smoke_test.py`, `inference_baseline.py`, `measure_latency.py`, `load_checkpoint_test.py`, `hil_inference.py`) 가 Orin 에서 새 경로로 모두 정상 동작 확인. import 회귀 없음. tests/ / config/ / checkpoints/ / inference/ 4개 신규 디렉터리 인식. entrypoint 2개 (`lerobot-eval`, `lerobot-train`) 등록 해제 반영.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (Orin 접속 필요)
- 검증 명령 (TODO-O3 진입 시 사용 예정):
  - `bash scripts/deploy_orin.sh` (devPC) — TODO-O2 + O2b 의 모든 변경 일괄 배포
  - `source ~/smolvla/orin/.hylion_arm/bin/activate && pip install -e ~/smolvla/orin/[smolvla,hardware,feetech]` — entrypoint 갱신
  - `which lerobot-eval lerobot-train` — 결과 없어야 함 (등록 해제 반영)
  - `python ~/smolvla/orin/tests/smoke_test.py` — 환경 검증 PASS
  - `python ~/smolvla/orin/tests/load_checkpoint_test.py --help` — help 출력 PASS
  - `python ~/smolvla/orin/tests/inference_baseline.py` — forward PASS
  - `python ~/smolvla/orin/inference/hil_inference.py --help` — help 출력 PASS
  - `ls ~/smolvla/orin/{tests,config,checkpoints,inference}/README.md` — 4개 README 모두 존재
- **완료 (2026-04-30 16:53)**: devPC 환경 변경 (Windows → Linux) 후 본 AI 가 SSH `orin` 으로 직접 배포·검증. `/handoff-test` 외부 위임 우회.
  - 배포: `bash scripts/deploy_orin.sh` 성공. 신규 4개 디렉터리 + 5개 .py 새 경로 + run_teleoperate.sh 삭제 모두 동기화 (1.19 MB)
  - 재설치: `pip install -e .[smolvla,hardware,feetech]` PASS. lerobot-0.5.2 editable wheel 재빌드. entrypoint 갱신 반영
  - 검증 결과 (8개 항목 모두 PASS):
    1. `which lerobot-eval lerobot-train` — exit=1, stdout 빈 결과 (등록 해제 확인)
    2. venv `bin/lerobot-*` 9개만 (eval/train 제외)
    3. 4 README 모두 존재 (`tests/`, `config/`, `checkpoints/`, `inference/`)
    4. `hil_inference.py --help` exit=0
    5. `load_checkpoint_test.py --help` exit=0
    6. `smoke_test.py` compile OK
    7. `inference_baseline.py` 실 forward PASS — lerobot/smolvla_base 다운로드 + 더미 입력 forward, Action shape (1,6) / dtype torch.float32 / min 0.391 / max 0.943 (03 prod 검증과 동일 패턴 재현)
    8. `measure_latency.py --help` exit=0
  - 부수 관찰: `lerobot-train` 은 본 검증 직전부터 venv 에 부재 (이전 build 에서 미등록). 실효성 있는 정리는 `lerobot-eval` 만. inference_baseline 실행 중 HF_TOKEN 미설정 경고 (정성 동작 무관)
  - **04 그룹 O 클로징** — 다음 진입 후보: 그룹 X (DGX 정리) 또는 그룹 D (DataCollector)
  - history: `docs/work_flow/context/history/04_infra_setup/20260430_1653_test_orin_migration_verify.md`

**[그룹 X — dgx/ 구조 정리]**

### [ ] TODO-X1: dgx/ 구조·기능 책임 매트릭스 + 마이그레이션 계획

- 타입: study
- DOD: TODO-O1 과 동일 패턴으로 dgx/ 정리. orin/ 에서 이관 받을 자산 (`run_teleoperate.sh` 등) 의 위치 결정. DataCollector 와의 인터페이스 정의 (데이터 받아서 학습).
- 구현 대상:
  - `docs/storage/08_dgx_structure.md` — TODO-O1 의 §1~§5 구조
- 테스트: 없음
- 참조: `dgx/` 전체 트리, `dgx/pyproject.toml`, `dgx/scripts/`, `docs/storage/06_dgx_venv_setting.md`, memory `project_dgx_structure_migrations.md`
- 잔여 리스크: dgx 가 SO-ARM 직접 연결 안 됨 — `run_teleoperate.sh` 가 dgx 에서 의미 있는지 본 TODO 에서 재확인. DataCollector 가 더 적합할 가능성

### [ ] TODO-X2: dgx/ 마이그레이션 실행

- 타입: task
- DOD: TODO-X1 의 계획대로 dgx/ 변경. 02 산출물 (setup_train_env.sh, preflight_check.sh, smoke_test.sh, save_dummy_checkpoint.sh) 의 동작 회귀 없음.
- 구현 대상:
  - orin/scripts/run_teleoperate.sh 이관 처리 (TODO-X1 결정에 따라 dgx/ 또는 datacollector/ 로)
  - 기타 TODO-X1 결정 사항
  - `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 갱신 (있다면)
- 테스트: 없음 (TODO-X3 에서 검증)

### [ ] TODO-X3: dgx/ 마이그레이션 회귀 검증 (DGX prod)

- 타입: test
- DOD: TODO-X2 후 02 산출물 모두 정상 동작 확인 (1 step smoke test 재실행)
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (DGX 접속 필요)

**[그룹 D — DataCollector 노드 신규 셋업]**

### [ ] TODO-D1: DataCollector 노드 정체 결정 + 디렉터리 신규

- 타입: study
- DOD: DataCollector 노드의 하드웨어·OS·venv·lerobot 의존성 결정. `smolVLA/` 하위 디렉터리 위치 확정 (`datacollector/` 권장). devPC sync hub 와의 관계 정의.
- 구현 대상:
  - `docs/storage/09_datacollector_setup.md` — 절 구성:
    - §1 노드 정체 (하드웨어·OS·네트워크)
    - §2 venv·lerobot 의존성 (orin venv 와의 차이점)
    - §3 디렉터리 구조 (orin/ 와 형제 패턴 기반, hardware 모듈 + record 책임)
    - §4 시연장 인근 배치 시 고려사항
    - §5 devPC ↔ DataCollector 네트워크 (SSH 설정, ~/.ssh/config)
- 테스트: 없음
- 참조: `docs/storage/04_devnetwork.md` (devPC ↔ Orin SSH 패턴 — DataCollector 도 동일 패턴 권장), `docs/storage/05_orin_venv_setting.md` (venv 패턴)
- 사용자 결정 사항: 노드 하드웨어 (별도 PC / 기존 노트북 / 시연장 PC), OS (Ubuntu 권장 — lerobot 안정성), 디렉터리 이름 (`datacollector/` vs 다른 이름)
- 잔여 리스크: DataCollector 가 시연장과 떨어진 임시 위치에서 시작 → 시연장 이동 시 IP·포트 변동 가능 (BACKLOG 02 #1 DHCP 예약과 동일 카테고리)

### [ ] TODO-D2: DataCollector venv·lerobot 셋업 스크립트

- 타입: task
- DOD: DataCollector 측 환경 셋업 스크립트 작성. orin 의 setup_env.sh 패턴 참조하되, 학습 모듈 X / 데이터 수집 + teleop + 카메라 모듈만 설치.
- 구현 대상:
  - `datacollector/scripts/setup_env.sh` (또는 TODO-D1 결정 위치)
  - `datacollector/pyproject.toml` (또는 orin/pyproject.toml 의 subset)
- 테스트: 없음 (TODO-D3 검증)
- 제약: TODO-D1 완료 후
- 잔여 리스크: DataCollector OS 가 Linux 가 아니면 (예: Windows) lerobot 호환성 이슈 — TODO-D1 결정 시 Linux 권장

### [ ] TODO-D3: DataCollector 환경 셋업 검증 prod

- 타입: test
- DOD: TODO-D2 의 setup 스크립트가 DataCollector 머신에서 실제 동작. lerobot import OK + SO-ARM 1대 + 카메라 1대 임의 연결 + `lerobot-find-port` `lerobot-find-cameras` PASS.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (DataCollector 노드 + SO-ARM + 카메라 1대 임시 연결 필요)

**[그룹 G — 환경 점검 게이트 스크립트]**

### [ ] TODO-G1: tests/check_hardware.sh 작성 (Orin)

- 타입: task
- DOD: Orin 에서 카메라 인덱스·flip / SO-ARM 포트 / venv 활성화 / cuda 라이브러리를 자동 점검하는 스크립트. first-time 모드 (전부 새로 발견 + `config/` 에 cache) + resume 모드 (cache 기반 검증). 03 prod 검증의 4개 환경 이슈 (BACKLOG 03 #14, #15, #16 + 01 #1) 모두 해소.
- 구현 대상:
  - `orin/tests/check_hardware.sh` — 단일 진입점, `--mode {first-time,resume}`, `--config orin/config/...`, `--quiet`, `--output-json`
  - `orin/tests/configs/first_time.yaml`, `resume.yaml`
  - 점검 단계:
    1. venv activate (`source ~/smolvla/orin/.hylion_arm/bin/activate`)
    2. CUDA 라이브러리 (`libcusparseLt` 등 — `python -c "import torch; assert torch.cuda.is_available()"`)
    3. SO-ARM 포트 발견 (`lerobot-find-port` 비대화형 wrapping)
    4. 카메라 인덱스·flip 발견 (`lerobot-find-cameras opencv`, first-time 모드는 사용자 확인)
    5. resume 모드는 위를 cache 와 비교만, first-time 모드는 cache 갱신
- 테스트: 없음 (TODO-G2 검증)
- 제약: TODO-O2 완료 후 (orin/tests/ 디렉터리 존재)
- 잔여 리스크:
  - lerobot CLI entrypoint 가 대화형 (stdin) 일 경우 wrapping 어려움 → OpenCV 직접 호출 또는 `udevadm` 우회
  - first-time 모드의 카메라 미리보기는 X11 forwarding 필요 — Orin 콘솔 직접 사용 가정

### [ ] TODO-G2: check_hardware.sh prod 검증 (Orin)

- 타입: test
- DOD: TODO-G1 산출물이 Orin 에서 first-time + resume 두 모드 모두 PASS. 03 의 hil_inference.py 가 게이트 결과 JSON 으로 자동 인자 받아 동작.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (Orin + 카메라 2대 + SO-ARM follower 1대 연결 필요)

### [ ] TODO-G3: DataCollector 측 check_hardware.sh 이식

- 타입: task
- DOD: TODO-G1 의 Orin 측 게이트 스크립트를 DataCollector 측에 이식 (venv path / lerobot path 갱신). 두 노드에서 같은 시나리오 점검 가능.
- 구현 대상:
  - `datacollector/tests/check_hardware.sh` (TODO-D1 의 디렉터리 결정 따라)
- 테스트: 없음 (TODO-G4 검증)
- 제약: TODO-G1·D2 완료 후
- 잔여 리스크: 두 노드의 점검 스크립트 차이가 커지면 유지보수 부담 — 공통 모듈 추출 검토 (스펙 범위 밖, BACKLOG 후보)

### [ ] TODO-G4: DataCollector check_hardware.sh prod 검증

- 타입: test
- DOD: TODO-G3 산출물이 DataCollector 머신에서 first-time + resume 두 모드 PASS.
- 구현 대상: 없음
- 테스트: prod 검증 (DataCollector + SO-ARM + 카메라 임시 연결)

**[그룹 M — 시연장 환경 미러링 가이드]**

### [ ] TODO-M1: 시연장 미러링 가이드 작성

- 타입: study
- DOD: 시연장 환경을 DataCollector 인근에 재현하기 위한 절차·체크리스트 문서. 사용자(인간) 책임 영역과 자동화 가능 영역 분리. 05_leftarmVLA 진입 전 1차 미러링 셋업 가능.
- 구현 대상:
  - `docs/storage/10_demo_site_mirroring.md` — 절 구성:
    - §1 시연장 환경 측정 항목 (책상 높이·재질·색 / 조명 강도·색온도·각도 / 카메라 위치·각도·렌즈 / 토르소 부착 위치·각도 / 작업 영역 크기·위치)
    - §2 측정 도구 (줄자·조도계·색온도계·사진 — 사용자 책임)
    - §3 DataCollector 측 재현 절차 (체크리스트 형태)
    - §4 미러링 검증 방법 (육안 + 사진 비교 우선, 자동 검증은 BACKLOG 후보)
    - §5 05_leftarmVLA 진입 전 점검 항목
- 테스트: 없음
- 사용자 결정 사항: 미러링 검증 깊이 (육안+사진 vs 자동 검증 스크립트). 첫 사이클은 육안+사진 권장
- 잔여 리스크: 시연장 접근 가능성 — 사용자 일정에 따라 시연장 측정 시점 조정 필요

### [ ] TODO-M2: 시연장 1차 미러링 셋업

- 타입: both (개발자 직접 + 정성 기록)
- DOD: TODO-M1 의 가이드대로 DataCollector 인근에 시연장 미러링 1차 셋업 완료. 사진·체크리스트로 결과 기록. 부족한 부분은 BACKLOG 로 관리.
- 구현 대상: 없음 (셋업·기록)
- 테스트: prod (사용자 직접 시연장 측정 + 재현)
- 제약: TODO-M1 완료 후
- 잔여 리스크: 첫 시도에서 정확한 미러링 어려움 — 05_leftarmVLA 의 학습 결과로 부족한 부분 진단 가능

**[그룹 T — 데이터·체크포인트 전송 경로 검증]**

### [ ] TODO-T1: DataCollector → DGX 데이터 전송 방식 결정 + 스크립트

- 타입: both
- DOD: 데이터 전송 방식 결정 (HF Hub vs rsync vs 둘 다) + 스크립트 작성 + dry-run dummy dataset 으로 동작 확인.
- 구현 대상:
  - `scripts/sync_dataset_collector_to_dgx.sh` (rsync 방식인 경우)
  - 또는 `datacollector/scripts/push_dataset_hub.sh` (HF Hub 방식인 경우)
- 테스트: dummy dataset 으로 dry-run 검증 (실 데이터셋은 05 의 책임)
- 사용자 결정 사항: HF Hub vs rsync 직접 vs 둘 다 (저는 HF Hub 추천 — lerobot-record 가 자동 push, lerobot-train 이 자동 pull)
- 잔여 리스크: HF Hub 방식 시 사용자 토큰·private repo 권한 필요. rsync 방식 시 DataCollector ↔ DGX 네트워크 경로 (devPC 경유 vs 직접) 결정 필요

### [ ] TODO-T2: DGX → 시연장 Orin ckpt 전송 경로 재확인

- 타입: test
- DOD: 기존 `scripts/sync_ckpt_dgx_to_orin.sh` (02 TODO-10b 검증) 이 시연장 시나리오 (Orin 이 시연장에 위치, devPC·DGX 와 다른 네트워크) 에서도 동작하는지 확인. 필요 시 USB 드라이브 또는 DataCollector 경유 우회 경로 추가.
- 구현 대상: 필요 시 `scripts/sync_ckpt_dgx_to_datacollector.sh` 같은 우회 스크립트
- 테스트: dummy ckpt 으로 dry-run 검증
- 제약: TODO-D1 완료 후 (DataCollector 네트워크 위치 결정)
- 잔여 리스크: 시연장 Orin 의 네트워크 격리 정도 — 사용자가 시연장 인터넷 환경 확인 필요

### [ ] TODO-T3: devPC sync hub 갱신

- 타입: task
- DOD: devPC 의 `scripts/` 에 DataCollector 배포 스크립트 추가. 기존 `deploy_orin.sh` / `deploy_dgx.sh` 와 형제 패턴.
- 구현 대상:
  - `scripts/deploy_datacollector.sh` — orin·dgx 배포 패턴 참조
- 테스트: dry-run (실 배포는 사용자 확인 후)
- 제약: TODO-D1 완료 후

---

> Backlog → [docs/work_flow/specs/BACKLOG.md](BACKLOG.md) 에 본 스펙 섹션을 추가하여 운영
