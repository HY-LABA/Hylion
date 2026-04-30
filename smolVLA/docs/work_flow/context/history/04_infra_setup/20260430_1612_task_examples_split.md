# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-30 16:00 | 스펙: `docs/work_flow/specs/04_infra_setup.md` | TODO: O2b

## 작업 목표

`orin/examples/` 책임 분리 — tutorial 미러 vs 본 프로젝트 자산.

03 산출물 5개를 책임별 적절한 위치로 이동:
- `hil_inference.py` → `orin/inference/hil_inference.py` (운영 진입점, 향후 마일스톤별 정책 아카이빙 디렉터리)
- `smoke_test.py` / `load_checkpoint_test.py` / `inference_baseline.py` / `measure_latency.py` → `orin/tests/` (검증·측정)
- `using_smolvla_example.py` → `orin/examples/tutorial/smolvla/` 그대로 유지 (upstream 미러)

결과: `orin/examples/` 는 upstream 미러 책임만 가짐. 본 프로젝트 검증·측정 자산은 `orin/tests/` 에, 운영 추론 진입점은 `orin/inference/` 에.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

1. `orin/inference/` 디렉터리 신규 + `orin/inference/README.md` 작성
2. 5개 .py 파일 이동 완료 (코드 내용 변경 X — 경로만 mv):
   - `orin/examples/tutorial/smolvla/hil_inference.py` → `orin/inference/hil_inference.py`
   - `orin/examples/tutorial/smolvla/smoke_test.py` → `orin/tests/smoke_test.py`
   - `orin/examples/tutorial/smolvla/load_checkpoint_test.py` → `orin/tests/load_checkpoint_test.py`
   - `orin/examples/tutorial/smolvla/inference_baseline.py` → `orin/tests/inference_baseline.py`
   - `orin/examples/tutorial/smolvla/measure_latency.py` → `orin/tests/measure_latency.py`
3. `orin/examples/tutorial/smolvla/` 에 `using_smolvla_example.py` 만 남음 (upstream 미러 그대로)
4. `orin/examples/tutorial/smolvla/__pycache__/` 정리 (이동된 파일들의 cache)
5. `orin/tests/README.md` 갱신 — 자산 표에 4개 신규 자산 추가
6. `docs/storage/07_orin_structure.md` 갱신:
   - §1 디렉터리 트리 (현재·새 구조 모두)
   - §2 컴포넌트 책임 표 (`orin/inference/` 추가, `orin/examples/` 책임 갱신)
   - §3 마일스톤 매트릭스 (5개 파일 위치 갱신)
   - §5 마이그레이션 계획 (5-2 이관에 5개 파일 추가, 5-3 신규에 inference/ 추가)
7. py_compile syntax check 5개 모두 PASS (이동 후)
8. 회귀 grep `^(from orin|import orin)` 0건 유지 (TODO-06 의 정책)

## 구현 대상

### 신규
- `orin/inference/` 디렉터리
- `orin/inference/README.md`

### 이동 (mv)
- 5개 .py 파일 (위 DOD #2 참조)

### 수정
- `orin/tests/README.md` — 자산 표 갱신
- `docs/storage/07_orin_structure.md` — §1 / §2 / §3 / §5 갱신

### 정리
- `orin/examples/tutorial/smolvla/__pycache__/` 의 .pyc 파일 (이동된 파일 분만)

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- `orin/examples/tutorial/smolvla/using_smolvla_example.py` — upstream 미러 그대로 유지 (이동 X)
- 5개 .py 파일의 코드 내용 — 절대 import (`from lerobot...`) 라 위치 무관하므로 코드 변경 불필요
- history 문서 (03 spec history, 03 context history 의 7개 .md) 의 경로 참조는 갱신 안 함 ("당시 사실" 보존 원칙)
- `orin/lerobot/` 하위 (옵션 B 트리밍 원칙)

## 작업 시작 전 확인

1. **현재 `orin/examples/tutorial/smolvla/` 구조 확인** — 6개 .py 파일 + __pycache__ 정상 존재 검증
2. **5개 .py 파일의 import 경로** 확인 — 모두 `from lerobot...` 절대 import 인지 (이동 안전성 검증)
3. **`docs/storage/07_orin_structure.md` 의 현재 §1/§2/§3/§5** 파악 — 갱신 범위 식별
4. **`orin/tests/README.md` 의 자산 표 형식** 파악 — 4개 신규 자산 추가 패턴

## 신규 README 콘텐츠 가이드

### `orin/inference/README.md`

- inference/ 의 책임 — 시연 환경에서 호출되는 추론 entry point. 운영 스크립트
- 향후 마일스톤별 정책 아카이빙 의도 (예: 05 leftarmVLA 진입 시 별도 entry 추가 가능, archive/ 신설 검토)
- 현재 자산:
  - `hil_inference.py` — 03_smolvla_test_on_orin TODO-07 산출물. SmolVLA 사전학습/학습 ckpt 로 실 SO-ARM hardware-in-the-loop 추론. dry-run / live 두 모드 + 안전 장치 (n_action_steps=5, SIGINT 핸들러, try/finally disconnect)
- 외부 의존성:
  - `orin/checkpoints/<run_name>/` — 학습된 ckpt 로드 위치 (05 TODO-13 시점부터)
  - `orin/config/{ports,cameras}.json` — SO-ARM·카메라 설정 cache
  - `orin/tests/check_hardware.sh --mode resume` — 운영 진입 직전 게이트 (TODO-G1 구현)
- 참고:
  - `docs/storage/07_orin_structure.md` §2 (inference/ 컴포넌트 책임)
  - `docs/work_flow/specs/04_infra_setup.md` TODO-O2b (본 디렉터리 신설 사유)
  - `docs/work_flow/specs/history/03_smolvla_test_on_orin.md` TODO-07 (hil_inference.py 의 출처)

## `orin/tests/README.md` 갱신 가이드

기존 README 의 §"자산 (현재)" 표에 4개 행 추가:

| 파일 | 책임 | 출처 |
|---|---|---|
| `diagnose_motor_encoder.py` | (기존) SO-ARM 모터 encoder 진단 | (기존) 01 TODO-03a |
| `smoke_test.py` | venv·CUDA·import·smolvla forward 환경 검증 | 01_teleoptest TODO-01 (04 TODO-O2b 에서 이관) |
| `load_checkpoint_test.py` | 임의 경로 ckpt 호환성 검증 (DGX→Orin 전송 후) | 02 TODO-10b (04 TODO-O2b 에서 이관) |
| `inference_baseline.py` | 더미 입력 1회 forward (입력 미러링) | 03 TODO-06 (04 TODO-O2b 에서 이관) |
| `measure_latency.py` | latency p50/p95 + RAM peak 측정 | 03 TODO-06 (04 TODO-O2b 에서 이관) |

## `docs/storage/07_orin_structure.md` 갱신 가이드

### §1-2 새 구조 트리에 inference/ 추가
```
orin/
├── ...
├── examples/
│   └── tutorial/smolvla/
│       └── using_smolvla_example.py   # upstream 미러 (단일 파일만)
├── inference/                         # ★ 신규 — 운영 진입점
│   ├── README.md
│   └── hil_inference.py               # 03 산출물 (이관)
├── tests/
│   ├── README.md
│   ├── diagnose_motor_encoder.py     # 01 산출물 (TODO-O2 이관)
│   ├── smoke_test.py                 # 01 산출물 (TODO-O2b 이관)
│   ├── load_checkpoint_test.py       # 02 산출물 (TODO-O2b 이관)
│   ├── inference_baseline.py         # 03 산출물 (TODO-O2b 이관)
│   ├── measure_latency.py            # 03 산출물 (TODO-O2b 이관)
│   └── (TODO-G1 예정 — check_hardware.sh, configs/)
└── ...
```

### §2 컴포넌트 책임 표에 한 행 추가
| `orin/inference/` (신규) | 시연 환경 추론 운영 entry point. 향후 마일스톤별 정책 아카이빙 디렉터리 역할 가능 | 04 TODO-O2b 에서 신규 + hil_inference.py 이관 |

### §2 의 `orin/examples/` 행 갱신
| `orin/examples/tutorial/smolvla/` | upstream lerobot examples/tutorial/smolvla/ 미러. SmolVLA 사용법 학습용 코드 | TODO-O2b 에서 본 프로젝트 5개 자산 분리 후 upstream 미러 책임만 가짐 |

### §3 마일스톤 매트릭스 — 5개 파일 행의 경로 prefix 갱신
- `examples/tutorial/smolvla/smoke_test.py` → `tests/smoke_test.py`
- `examples/tutorial/smolvla/inference_baseline.py` → `tests/inference_baseline.py`
- `examples/tutorial/smolvla/measure_latency.py` → `tests/measure_latency.py`
- `examples/tutorial/smolvla/load_checkpoint_test.py` → `tests/load_checkpoint_test.py`
- `examples/tutorial/smolvla/hil_inference.py` → `inference/hil_inference.py`

### §5 마이그레이션 계획 — 본 TODO-O2b 결과 추가
- 5-2 이관 표에 5개 행 추가 (TODO-O2b)
- 5-3 신규 표에 `orin/inference/` 추가
- 5-1 유지 표의 `orin/examples/` 항목 책임 명시 변경 (upstream 미러만)

## 참고 레퍼런스

- `docs/storage/07_orin_structure.md` — 기존 §1~§6 (본 TODO 의 갱신 대상)
- `docs/work_flow/specs/04_infra_setup.md` TODO-O2b — 본 작업 사양
- `docs/work_flow/context/history/04_infra_setup/20260430_1542_task_orin_migration.md` — 직전 TODO-O2 의 history (디렉터리 변경 사항 종합)
- `orin/tests/README.md` — 직전 TODO-O2 에서 신규 작성된 README (자산 표 형식 참고)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 업데이트

*작업 완료 후 아래 항목을 채운다.*

### 변경한 내용

작업 시작 전 사전 점검: 5개 파일의 import 경로가 모두 절대 import (`from lerobot...` 또는 표준 라이브러리) 임을 확인하여 디렉터리 이동 안전성 검증.

**1. 신규 디렉터리**:
- `orin/inference/` — 시연 환경 추론 운영 entry point. 향후 마일스톤별 정책 아카이빙 의도

**2. 파일 이동 5건** (mv — 코드 변경 X):
- `orin/examples/tutorial/smolvla/hil_inference.py` → `orin/inference/hil_inference.py`
- `orin/examples/tutorial/smolvla/smoke_test.py` → `orin/tests/smoke_test.py`
- `orin/examples/tutorial/smolvla/load_checkpoint_test.py` → `orin/tests/load_checkpoint_test.py`
- `orin/examples/tutorial/smolvla/inference_baseline.py` → `orin/tests/inference_baseline.py`
- `orin/examples/tutorial/smolvla/measure_latency.py` → `orin/tests/measure_latency.py`

**3. 결과 디렉터리 상태**:
- `orin/examples/tutorial/smolvla/` 에 `using_smolvla_example.py` 1개만 남음 (upstream 미러)
- `orin/inference/` 에 `hil_inference.py` + README.md
- `orin/tests/` 에 6개 자산 (`README.md` + `diagnose_motor_encoder.py` + 4개 신규 이관)

**4. 정리**:
- `orin/examples/tutorial/smolvla/__pycache__/` 4개 .pyc 정리 (rm -rf)

**5. 신규 README**:
- `orin/inference/README.md` — inference/ 책임 + tests/ 와의 구분 + 자산 (현재 hil_inference.py / 예정 마일스톤별 진화) + 외부 의존성 + 사용 예시 (dry-run / live)

**6. README 갱신**:
- `orin/tests/README.md` — 자산 (현재) 표에 4개 행 추가 (smoke_test / load_checkpoint_test / inference_baseline / measure_latency)

**7. `docs/storage/07_orin_structure.md` 갱신**:
- §1-2 새 구조 트리 — `inference/` 추가, `examples/tutorial/smolvla/` 가 upstream 미러 책임만 가짐 명시, 책임 분리 메모 추가
- §2 컴포넌트 책임 표 — `orin/inference/` 행 신규 추가, `orin/examples/tutorial/smolvla/` 행 책임 갱신, `orin/tests/` 행 책임 갱신 (4개 검증/측정 스크립트 추가 명시)
- §3 마일스톤 매트릭스 — 5개 파일 행의 경로 prefix 갱신 (`examples/tutorial/smolvla/` → `tests/` 또는 `inference/`), `using_smolvla_example.py` 행 추가, 04 컬럼에 ✏️ (TODO-O2b 이관) 표시
- §4-1 deploy_orin.sh 의 rsync 대상에 `inference/` 추가
- §5-1 유지 표 — `examples/tutorial/smolvla/` 항목을 `using_smolvla_example.py` 단일 파일로 명시
- §5-2 이관 표 — TODO-O2b 의 5개 파일 이관 추가 (각 사유 명시)
- §5-3 신규 표 — `orin/inference/` 항목 추가
- 변경 이력에 2026-04-30 (TODO-O2b) 항목 추가

### 검증 방법 및 결과

| # | 검증 항목 | 결과 |
|---|---|---|
| 1 | 5개 파일 import 경로 사전 점검 (절대 import) | PASS — 5개 모두 `from lerobot...` 또는 표준 라이브러리. 상대 import 없음 → 이동 안전 |
| 2 | `orin/examples/tutorial/smolvla/` 결과 — `using_smolvla_example.py` 1개만 남음 | PASS |
| 3 | `orin/inference/` 결과 — `hil_inference.py` + README.md | PASS |
| 4 | `orin/tests/` 결과 — 6개 자산 (README.md + diagnose_motor_encoder.py + 4개 이관) | PASS |
| 5 | `orin/examples/tutorial/smolvla/__pycache__/` 정리 | PASS — 4개 .pyc 제거 |
| 6 | `python -m py_compile` 6개 .py 모두 통과 | PASS — hil_inference / smoke_test / inference_baseline / measure_latency / load_checkpoint_test / diagnose_motor_encoder |
| 7 | 회귀 grep `^(from orin\|import orin)` (orin/ 전체) | PASS (0건 — TODO-06 정책 유지) |
| 8 | `orin/inference/README.md` 신규 작성 | PASS |
| 9 | `orin/tests/README.md` 자산 표 4행 추가 | PASS |
| 10 | `docs/storage/07_orin_structure.md` §1·§2·§3·§4-1·§5 갱신 + 변경 이력 추가 | PASS |

### 실 실행 검증 필요 여부

**필요.** TODO-O3 가 본 작업의 prod 검증을 통합 담당 (TODO-O2 + TODO-O2b 둘 다 검증). Orin 에서:

1. `bash scripts/deploy_orin.sh` (devPC) — TODO-O2 + O2b 의 모든 변경 일괄 배포
2. `pip install -e ~/smolvla/orin/[smolvla,hardware,feetech]` (Orin venv) — entrypoint 갱신
3. 새 경로로 6개 .py 실행 검증:
   - `python ~/smolvla/orin/tests/smoke_test.py`
   - `python ~/smolvla/orin/tests/load_checkpoint_test.py --help`
   - `python ~/smolvla/orin/tests/inference_baseline.py`
   - `python ~/smolvla/orin/tests/measure_latency.py --help`
   - `python ~/smolvla/orin/inference/hil_inference.py --help`
   - `python ~/smolvla/orin/tests/diagnose_motor_encoder.py --help`
4. 4개 README 존재 확인 (`tests/`, `config/`, `checkpoints/`, `inference/`)
5. `which lerobot-eval lerobot-train` — 결과 없어야 함 (TODO-O2 entrypoint 등록 해제 반영)

특히 점검할 잔여 리스크:
- `orin/examples/tutorial/smolvla/` 가 1개 파일만 남은 디렉터리 — 디렉터리 평탄화 (`examples/tutorial/using_smolvla_example.py`) 검토 가능. 단 upstream 구조 보존 원칙대로면 그대로 유지가 자연스러움 — TODO-O3 검증 시점에 사용자와 합의

## 배포

- 일시: 2026-04-30 16:00
- 결과: 미실행 (사용자가 추후 일괄 배포 — TODO-O2 / TODO-O2b 모두 한번에). TODO-O3 진입 시점에는 반드시 배포 선행 필요 (entrypoint 갱신 + 새 경로 .py 모두 Orin 측에 반영)
