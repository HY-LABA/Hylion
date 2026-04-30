# orin/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획

> 작성일: 2026-04-30
> 출처: `04_infra_setup` 마일스톤 TODO-O1
> 목적: 04 사이클의 orin/ 마이그레이션 (TODO-O2) 입력 + 후속 마일스톤 (05~08) 에서 어느 컴포넌트가 어떤 책임을 지는지 한 곳에 정리.
> 형제 문서: `docs/storage/08_dgx_structure.md` (TODO-X1 산출물 예정)

---

## 0) 본 문서의 위치

03 까지 orin/ 은 학습은 안 하지만 추론·데이터 수집·환경 점검을 모두 담당하는 multi-purpose 노드였음. 04 부터 4-노드 분리 (devPC / DataCollector / DGX / 시연장 Orin) 가 도입되면서 **Orin 의 책임이 추론 전용으로 축소**된다. 본 문서는 그 축소 후의 orin/ 디렉터리 책임을 명문화한다.

본 문서의 §5 (마이그레이션 계획) 가 TODO-O2 (마이그레이션 실행) 의 입력 사양이 된다.

**핵심 원칙 — upstream 구조 보존**: lerobot upstream 으로부터 가져온 `orin/lerobot/` 디렉터리는 **파일·디렉터리 단에서 변경하지 않는다**. 대신 `orin/pyproject.toml` 의 `[project.scripts]` entrypoint 등록과 `__init__.py` 의 import 차단으로 책임 외 기능을 비활성화한다 (논리적 비활성화). 사유: upstream 동기화 시 매번 재트리밍하는 부담 회피.

---

## 1) 디렉터리 트리 (현재 vs 새 구조)

### 1-1) 현재 (2026-04-30 시점)

```
orin/
├── README.md
├── pyproject.toml                  # 환경/의존성 정의 (PyTorch 제외)
├── calibration/                    # ※ 04 진행 중 제거 예정
│   └── diagnose_motor_encoder.py   # 01_teleoptest TODO-03a 산출물
├── examples/
│   └── tutorial/
│       └── smolvla/                # 03 마일스톤 산출물 6개 + tutorial 1개
│           ├── smoke_test.py                # 환경 검증 (01_teleoptest)
│           ├── using_smolvla_example.py     # tutorial (lerobot upstream 참조)
│           ├── inference_baseline.py        # 03 TODO-06 산출물 (forward baseline)
│           ├── measure_latency.py           # 03 TODO-06 산출물 (latency 측정)
│           ├── load_checkpoint_test.py      # 02 TODO-10b 산출물 (ckpt 호환성)
│           └── hil_inference.py             # 03 TODO-07 산출물 (HW-in-the-loop 추론)
├── lerobot/                        # upstream curated subset (논리적 비활성화 적용)
│   ├── __init__.py / __version__.py / types.py
│   ├── cameras/                    # opencv / realsense / zmq
│   ├── configs/                    # 학습 전용 Config 는 import 차단됨 (03_orin_lerobot_diff.md)
│   ├── envs/                       # gym 환경 (Orin 미사용, 파일은 보존)
│   ├── model/
│   ├── motors/                     # feetech (SO-ARM 모터)
│   ├── optim/
│   ├── policies/
│   │   ├── rtc/                    # 07/08 latency 튜닝 시 검토
│   │   └── smolvla/                # 추론 entrypoint
│   ├── processor/                  # hil_processor 는 import 차단됨
│   ├── robots/so_follower/         # SO-ARM 추상화
│   ├── scripts/                    # upstream 18 entrypoint 그대로 보존 (논리적 비활성화)
│   ├── teleoperators/so_leader/
│   └── utils/
└── scripts/
    ├── setup_env.sh                # 환경 셋업 (PyTorch 포함, Jetson 제약상 pyproject 분리 불가)
    └── run_teleoperate.sh          # ※ 04 진행 중 DataCollector 로 이관 예정 (memory 후보 a)
```

추가 자산 (런타임 생성, 트리에 미포함):
- `orin/.hylion_arm/` — venv (gitignore)
- `__pycache__/` — bytecode (gitignore)

### 1-2) 새 구조 (04 마일스톤 종료 시점 목표)

```
orin/
├── README.md                       # 디렉터리 책임 + 운영 가이드 (04 종료 시 갱신)
├── pyproject.toml                  # entrypoint 9개 (eval / train 제외)
├── lerobot/                        # ★ upstream 보존 (변경 X)
│   └── ... (현재와 동일)
├── scripts/
│   └── setup_env.sh                # 유지
│                                    # ※ run_teleoperate.sh 는 DataCollector 로 이관됨
├── tests/                          # ★ 신규 — 시나리오 점검 + 환경 게이트 + 검증/측정 스크립트
│   ├── README.md
│   ├── check_hardware.sh           # TODO-G1 산출물
│   ├── configs/
│   │   ├── first_time.yaml
│   │   └── resume.yaml
│   ├── diagnose_motor_encoder.py   # 01 산출물 — orin/calibration/ 에서 이관 (TODO-O2)
│   ├── smoke_test.py               # 01 산출물 — examples/tutorial/smolvla/ 에서 이관 (TODO-O2b)
│   ├── load_checkpoint_test.py     # 02 산출물 — 동일 출처에서 이관 (TODO-O2b)
│   ├── inference_baseline.py       # 03 산출물 — 동일 출처에서 이관 (TODO-O2b)
│   └── measure_latency.py          # 03 산출물 — 동일 출처에서 이관 (TODO-O2b)
├── inference/                      # ★ 신규 — 시연 환경 추론 운영 entry point
│   ├── README.md
│   └── hil_inference.py            # 03 산출물 — examples/tutorial/smolvla/ 에서 이관 (TODO-O2b)
│                                    # ※ 향후 마일스톤별 추론 정책 아카이빙 디렉터리 역할 가능 (05 진입 시 검토)
├── examples/                       # upstream 미러만 (본 프로젝트 자산은 tests/ 와 inference/ 로 분리됨)
│   └── tutorial/smolvla/
│       └── using_smolvla_example.py    # upstream lerobot examples/tutorial/smolvla/ 미러 (단일 파일)
├── config/                         # ★ 신규 — 본 프로젝트 cached config
│   ├── README.md
│   ├── ports.json                  # SO-ARM 포트 (시연장 셋업 후 cache)
│   └── cameras.json                # 카메라 인덱스/flip/slot 매핑
│                                    # ※ lerobot 캘리브레이션은 ~/.cache/huggingface/lerobot/calibration/
└── checkpoints/                    # ★ 신규 — .gitignore. 학습된 정책 ckpt
    └── README.md                   # 05_leftarmVLA TODO-13 시점에 채워짐
```

**제거된 항목**: `orin/calibration/` 디렉터리 (diagnose_motor_encoder.py 이관 후 비게 됨)
**이관된 항목**: `orin/scripts/run_teleoperate.sh` → DataCollector
**책임 분리**: `orin/examples/` 는 upstream 미러만, 본 프로젝트 자산은 `orin/tests/` (검증·측정) + `orin/inference/` (운영 entry point) 로 분리됨 (TODO-O2b)

---

## 2) 핵심 컴포넌트 책임 표

| 컴포넌트 | 책임 | 04 이후 변경 |
|---|---|---|
| `orin/lerobot/` | upstream curated subset. inference + 일부 hardware 제어 모듈의 추상화 도구. 실 진입점은 examples/ 와 hil_inference.py 가 조합 | **파일 제거 X**. 논리적 비활성화만 (`__init__.py` import 차단, pyproject entrypoint 정리) |
| `orin/scripts/setup_env.sh` | venv 생성 + lerobot editable install + Jetson PyTorch wheel 직접 설치. Jetson 제약상 PyTorch 는 pyproject 가 아닌 본 스크립트에서 NVIDIA redist URL 로 받음 | 유지. 04 의 운영 변화 없음 |
| `orin/pyproject.toml` | 의존성 정의 + entrypoint 등록 | `[project.scripts]` 에서 lerobot-eval / lerobot-train 2개 제거 (9개 유지) |
| `orin/examples/tutorial/smolvla/` | upstream `lerobot/examples/tutorial/smolvla/` 미러 — SmolVLA 사용법 학습용 코드 (`using_smolvla_example.py`) | TODO-O2b 에서 본 프로젝트 5개 자산 분리 → upstream 미러 책임만 가짐 |
| `orin/inference/` (신규) | 시연 환경 추론 운영 entry point (`hil_inference.py`). 향후 마일스톤별 정책 아카이빙 디렉터리 역할 가능 | 04 TODO-O2b 에서 신규 + hil_inference.py 이관 |
| `orin/tests/` (신규) | 시나리오 점검 (카메라·포트·venv) + 환경 게이트 + 검증/측정 스크립트. first-time / resume 두 모드. 운영 스크립트가 sub-call | 04 TODO-O2 에서 신규 + TODO-O2b 에서 4개 검증/측정 스크립트 추가 + TODO-G1 에서 check_hardware.sh 구현 |
| `orin/config/` (신규) | 본 프로젝트 자체 cached config (ports.json, cameras.json). git 추적 (사용자 환경 의존하나 시연장 셋업 후엔 안정적) | 04 TODO-O2 에서 신규 |
| `orin/checkpoints/` (신규) | 학습된 정책 ckpt 보관. .gitignore (수백 MB ~ GB) | 04 TODO-O2 에서 신규 + 05 TODO-13 에서 첫 ckpt 도착 |
| `orin/.hylion_arm/` | venv (런타임). gitignore | 변경 없음 |

---

## 3) 마일스톤별 책임 매트릭스

각 마일스톤에서 어느 컴포넌트가 사용/수정되는지. (✓=사용, ✏️=수정·신규, -=무관)

| 컴포넌트 | 00_orin_setting | 01_teleoptest | 02_dgx_setting | 03_smolvla_test_on_orin | 04_infra_setup | 05_leftarmVLA | 06_biarm_teleop | 07_biarm_VLA | 08_biarm_deploy |
|---|---|---|---|---|---|---|---|---|---|
| `lerobot/cameras/` | - | ✓ | - | ✓ | - | ✓ (DataCollector) | ✓ (DataCollector) | - | ✓ |
| `lerobot/motors/` | - | ✓ | - | ✓ | - | ✓ | ✓ | - | ✓ |
| `lerobot/robots/so_follower/` | - | ✓ | - | ✓ | - | ✓ | ✓ | - | ✓ |
| `lerobot/teleoperators/so_leader/` | - | ✓ | - | - | - | ✓ (DataCollector) | ✓ (DataCollector) | - | - |
| `lerobot/policies/smolvla/` | ✓ | - | - | ✓ | - | ✓ | - | ✓ | ✓ |
| `lerobot/policies/rtc/` | - | - | - | - | - | - | - | - | ✓ (latency 튜닝) |
| `lerobot/scripts/lerobot-record` | - | - | - | - | - | ✓ (DataCollector) | ✓ (DataCollector) | - | - |
| `lerobot/scripts/lerobot-replay` | - | - | - | - | - | ✓ (검증) | ✓ (검증) | - | - |
| `scripts/setup_env.sh` | ✏️ | ✓ | - | ✓ | - | - | - | - | ✓ |
| `scripts/run_teleoperate.sh` | - | ✏️ | - | - | ✏️ (이관) | - | - | - | - |
| `examples/tutorial/smolvla/using_smolvla_example.py` | - | - | - | - | - | - | - | - | - | (upstream 미러, 참조만)
| `tests/smoke_test.py` | - | ✏️ | - | ✓ | ✏️ (TODO-O2b 이관) | - | - | - | - |
| `tests/inference_baseline.py` | - | - | - | ✏️ | ✏️ (TODO-O2b 이관) | - | - | - | - |
| `tests/measure_latency.py` | - | - | - | ✏️ | ✏️ (TODO-O2b 이관) | - | - | - | ✓ (실 카메라 입력 재측정) |
| `tests/load_checkpoint_test.py` | - | - | ✏️ | ✓ | ✏️ (TODO-O2b 이관) | ✓ (학습 ckpt 호환성) | - | ✓ | ✓ |
| `inference/hil_inference.py` | - | - | - | ✏️ | ✏️ (TODO-O2b 이관) | ✏️ (TODO-14: ckpt 인자) | - | - | ✓ (시연장 추론) |
| `tests/check_hardware.sh` | - | - | - | - | ✏️ (TODO-G1) | ✓ | ✓ | - | ✓ |
| `tests/diagnose_motor_encoder.py` | - | ✏️ | - | - | ✏️ (이관) | ✓ | ✓ | - | - |
| `config/ports.json`, `cameras.json` | - | - | - | - | ✏️ (TODO-G1 cache) | ✓ | ✓ | - | ✓ |
| `checkpoints/` | - | - | - | - | ✏️ (신규) | ✏️ (05 ckpt 도착) | - | - | ✏️ (07 ckpt 도착) |
| `pyproject.toml` | ✏️ | - | - | - | ✏️ (entrypoint 정리) | - | - | - | - |

**관찰**:
- `lerobot/cameras/`, `lerobot/motors/`, `lerobot/robots/so_follower/`, `lerobot/teleoperators/so_leader/`, `lerobot/policies/smolvla/` 가 **모든 SO-ARM 사이클의 공통 의존성** — 이 모듈들이 inference + 데이터 수집의 추상화 도구
- `tests/`, `config/` 는 04 신설 후 **모든 후속 마일스톤이 활용**하는 공통 인프라
- `lerobot/scripts/lerobot-record` / `lerobot-replay` 는 **DataCollector 측에서 호출** (Orin 도 동일 lerobot 패키지 가지나 호출자는 DataCollector). 4-노드 분리 후 Orin 자체에서는 거의 호출 안 함

---

## 4) 외부 의존성

### 4-1) devPC sync hub

```
devPC scripts/                  Orin 측 효과
├── deploy_orin.sh ──→ rsync   orin/* (lerobot/ + scripts/ + examples/ + tests/ + inference/ + config/ — checkpoints 제외)
└── sync_ckpt_dgx_to_orin.sh    DGX 학습 ckpt → orin/checkpoints/<run_name>/
```

본 04 마일스톤 종료 후 추가될 것 (TODO-T3):
- `scripts/deploy_datacollector.sh` (DataCollector 측 배포)
- `scripts/sync_dataset_collector_to_dgx.sh` (TODO-T1 결정에 따라 — HF Hub 면 미작성)

### 4-2) HuggingFace Hub

| 자산 | 흐름 |
|---|---|
| smolvla_base 가중치 | Hub → Orin (HF cache `~/.cache/huggingface/hub/`) |
| 학습 데이터셋 | DataCollector → Hub → DGX (TODO-T1 결정에 따라) |
| 학습 ckpt | DGX → (devPC 경유 rsync) → Orin checkpoints/. Hub 미경유 |

### 4-3) Orin ↔ DataCollector ↔ DGX 인터페이스

```
DataCollector → DGX:    데이터셋 (TODO-T1 결정 — HF Hub 권장)
DGX → 시연장 Orin:      학습 ckpt (sync_ckpt_dgx_to_orin.sh, 시연장 시나리오는 TODO-T2 재확인)
Orin → 시연장 운영:     hil_inference.py 가 학습 ckpt + 실 카메라 + SO-ARM 으로 추론
```

### 4-4) 시스템 의존성 (lerobot 외)

`scripts/setup_env.sh:31-54` 에 명시:
- `libopenblas-dev`, `libopenmpi-dev`, `libomp-dev` (NVIDIA PyTorch on Jetson 요건)
- `libcusparseLt` (CUDA 12.6 forward-compat. NVIDIA cuSPARSELt 0.8.1 deb 권장, 미설치 시 venv pip wheel 의 LD_LIBRARY_PATH 패치로 우회)
- `python3.10` (jp6/cu126 wheel 이 cp310 만 제공)

### 4-5) 캘리브레이션 파일 위치 (lerobot 표준)

`~/.cache/huggingface/lerobot/calibration/<robot_id>.json` — `lerobot-calibrate` 가 자동 저장. orin/config/ 에 복사·심볼릭 링크 안 함 (lerobot 표준 그대로 사용).

---

## 5) 마이그레이션 계획 (TODO-O2 의 입력)

5개 카테고리로 분류. **트리밍 원칙**: upstream 구조 보존 — 파일 제거 대신 `pyproject.toml` entrypoint 등록 해제만으로 비활성화 (옵션 B).

### 5-1) 유지

| 항목 | 현재 위치 | 사유 |
|---|---|---|
| orin/lerobot/ 전체 트리 | orin/lerobot/ | upstream 구조 보존 원칙. 논리적 비활성화는 03_orin_lerobot_diff.md 에 기록된 기존 패치 + 본 TODO 의 entrypoint 정리로 충분 |
| orin/scripts/setup_env.sh | orin/scripts/ | Jetson PyTorch wheel 설치 패턴 — pyproject 로 옮기면 PyPI CPU-only wheel 덮어쓰기 발생 |
| orin/examples/tutorial/smolvla/using_smolvla_example.py | 동일 | upstream 미러. TODO-O2b 후 examples/ 는 upstream 미러 책임만 |
| orin/pyproject.toml 의 9개 entrypoint | 동일 | lerobot-calibrate / find-cameras / find-port / find-joint-limits / record / replay / setup-motors / teleoperate / info — inference + 데이터 수집 + 환경 점검 책임 |
| orin/README.md | 동일 | 본 04 종료 시점에 새 디렉터리 (tests/, config/, checkpoints/, inference/) 안내 추가 |
| orin/.hylion_arm/ | 동일 | venv. gitignore. 4 노드 모두 본인 venv 격리 |

### 5-2) 이관 (out)

| 항목 | 현재 → 새 위치 | 사유 |
|---|---|---|
| orin/calibration/diagnose_motor_encoder.py | → orin/tests/ (직접) | 시나리오 점검 성격. tests/ 의 첫 자산 (TODO-O2) |
| orin/scripts/run_teleoperate.sh | → DataCollector 측 (memory `project_run_teleoperate_relocation.md` 후보 a) | Orin 추론 전용 축소. SO-ARM 직접 연결은 DataCollector 책임. 단 본 TODO-O2 진행 시점에 DataCollector 디렉터리 미존재 시 임시 보관 (`docs/storage/others/run_teleoperate.sh.archive`) 후 TODO-D2 시점에 최종 이동 |
| orin/examples/tutorial/smolvla/smoke_test.py | → orin/tests/ | 환경 검증 성격. tests/ 의 책임 (TODO-O2b) |
| orin/examples/tutorial/smolvla/load_checkpoint_test.py | → orin/tests/ | ckpt 호환성 검증 성격. tests/ 의 책임 (TODO-O2b) |
| orin/examples/tutorial/smolvla/inference_baseline.py | → orin/tests/ | 더미 입력 baseline 검증 성격. tests/ 의 책임 (TODO-O2b) |
| orin/examples/tutorial/smolvla/measure_latency.py | → orin/tests/ | latency 측정 성격. tests/ 의 책임 (TODO-O2b) |
| orin/examples/tutorial/smolvla/hil_inference.py | → orin/inference/ | 시연 환경 운영 entry point. inference/ 의 책임 (TODO-O2b) |

### 5-3) 신규 (in)

| 항목 | 신규 위치 | 초기 내용 |
|---|---|---|
| orin/tests/ + README.md | orin/tests/README.md | tests/ 의 책임 + first-time / resume 모드 가이드. 자산: diagnose_motor_encoder.py (TODO-O2 이관) + 4개 검증/측정 스크립트 (TODO-O2b 이관). 실 게이트 스크립트 (check_hardware.sh, configs/) 는 TODO-G1 이 채움 |
| orin/config/ + README.md | orin/config/README.md | config/ 의 책임 + ports.json / cameras.json 의 스키마 + 재생성 방법. ports.json, cameras.json 은 placeholder (TODO-G1 first-time 모드가 채움) |
| orin/checkpoints/ + README.md | orin/checkpoints/README.md | 학습 ckpt 보관 정책 + 디렉터리 구조 (`<run_name>/<step>/pretrained_model/`) + sync_ckpt_dgx_to_orin.sh 사용법. 실 ckpt 는 05 TODO-13 시점에 도착 |
| orin/inference/ + README.md | orin/inference/README.md | inference/ 의 책임 (시연 환경 추론 운영 entry point) + 향후 마일스톤별 정책 아카이빙 의도. 자산: hil_inference.py (TODO-O2b 이관). 05 TODO-14 에서 ckpt 인자 추가 예정 |

### 5-4) 삭제 (rm)

| 항목 | 사유 |
|---|---|
| orin/calibration/ 디렉터리 | diagnose_motor_encoder.py 이관 후 비게 됨 |

### 5-5) entrypoint 정리 (orin/pyproject.toml `[project.scripts]`)

| entrypoint | 처리 | 사유 |
|---|---|---|
| lerobot-calibrate | 유지 | tests/ 에서 사용 |
| lerobot-find-cameras | 유지 | tests/check_hardware.sh 가 wrapping (TODO-G1) |
| lerobot-find-port | 유지 | tests/check_hardware.sh 가 wrapping (TODO-G1) |
| lerobot-find-joint-limits | 유지 | calibrate 의존성 + tests/ |
| lerobot-record | 유지 | DataCollector 측에서 호출 (Orin 도 동일 패키지 가짐) |
| lerobot-replay | 유지 | 디버그·검증용 |
| lerobot-setup-motors | 유지 | first-time 셋업 |
| lerobot-teleoperate | 유지 | record 의존성 |
| lerobot-info | 유지 | 환경 정보 출력 |
| **lerobot-eval** | **제거** | Orin 평가 안 함 (DGX 또는 hil_inference.py 가 대체) |
| **lerobot-train** | **제거** | Orin 학습 안 함 (DGX 책임) |

**부수 작업 (TODO-O2 안에 포함)**:
- `.gitignore` 갱신: `orin/checkpoints/<run_name>/` 패턴 추가 (단 README.md 는 추적)
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 갱신: entrypoint 2개 제거 이력 (CLAUDE.md coupled file 규칙)
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 갱신: 04 진입 시점의 추가 트리밍 기록 (옵션 B 원칙 명시)

---

## 6) 04 진입 시 활용 포인트 (후속 TODO 트리거)

본 §1~§5 산출물이 다음 04 TODO 의 입력이 됨:

- **TODO-O2**: §5 마이그레이션 계획 그대로 실행
- **TODO-O3**: §1-2 새 트리 + §2 컴포넌트 책임으로 회귀 검증 항목 도출
- **TODO-G1**: §2 의 tests/check_hardware.sh 책임 + §4-2 외부 의존성 (lerobot 표준 캘리브레이션 위치) 활용
- **TODO-D1**: §3 마일스톤별 책임 매트릭스의 "DataCollector" 표시된 항목들이 DataCollector 디렉터리에 와야 할 자산
- **TODO-X1** (dgx 구조): 본 문서의 형제 위치 (08_dgx_structure.md) 에서 동일 패턴 적용

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-30 | 초안 작성 — 04 TODO-O1 산출물. 옵션 B (논리적 비활성화) 채택, 5개 마이그레이션 카테고리 정의 |
| 2026-04-30 (TODO-O2b) | examples/ 책임 분리 반영 — orin/inference/ 신규, 5개 .py 이관 (1개 → inference/, 4개 → tests/), orin/examples/ 는 upstream 미러 책임만. §1-2 새 구조 + §2 컴포넌트 책임 + §3 매트릭스 + §5-1·5-2·5-3 갱신 |
