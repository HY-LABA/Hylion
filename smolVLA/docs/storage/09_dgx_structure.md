# dgx/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획

> 작성일: 2026-05-01
> 출처: `04_infra_setup` 마일스톤 TODO-X1
> 목적: 04 사이클의 dgx/ 마이그레이션 (TODO-X2) 입력 + 후속 마일스톤 (05~08) 에서 어느 컴포넌트가 어떤 책임을 지는지 한 곳에 정리.
> 형제 문서: `docs/storage/08_orin_structure.md` (TODO-O1 산출물)

---

## 0) 본 문서의 위치

04 이전까지 dgx/ 는 학습 전용이었으나 단일 책임이 명시적으로 정의되지 않았음. 04 에서 **4-노드 분리 아키텍처 (devPC / DataCollector / DGX / 시연장 Orin)** 가 공식화되면서 DGX 의 역할을 명확히 한다:

<!-- 정정 (2026-05-02): 06_dgx_absorbs_datacollector 결정으로 4-노드 → 3-노드 구조로 단순화.
     DGX 가 DataCollector 의 데이터 수집 책임 흡수 — DGX 가 시연장 직접 이동 운영.
     본 §0 본문은 04 결정 시점 역사적 맥락 보존. 06 결정 후 변경 내용은 X2 todo 처리. -->

- **DGX 의 단일 책임: 학습 전용** (04 기준 — 06 결정으로 *학습 + 데이터 수집* 으로 확장됨)
  - SO-ARM 직접 연결 X (→ **정정**: 06 결정으로 DGX 가 시연장 이동 시 SO-ARM 직결 가능, V1 prod 검증 예정)
  - teleop 책임 X → DataCollector 로 이관 (→ **정정**: 06 결정으로 dgx/scripts/run_teleoperate.sh 이식, X3 처리)
  - 추론 책임 X → Orin 의 책임 (변경 없음)
  - 데이터 수집 책임 X → DataCollector 의 책임 (→ **정정**: DataCollector 운영 종료, DGX 흡수 확정 2026-05-02)

본 문서의 §5 (마이그레이션 계획) 가 TODO-X2 (마이그레이션 실행) 의 입력 사양이 된다.

**핵심 원칙 — upstream 코드 무수정**: DGX 는 `docs/reference/lerobot/` submodule 을 editable 설치하여 그대로 사용한다. `dgx/lerobot/` curated 디렉터리를 두지 않는다 (orin/ 과 달리 학습 entrypoint 를 수정할 필요 없음). lerobot 학습 CLI 실행 시 필요한 보정은 `dgx/scripts/` 래퍼로만 수행한다.

---

## 1) 디렉터리 트리 (현재 vs 새 구조)

### 1-1) 현재 (2026-05-01 시점)

```
dgx/
├── README.md                       # 디렉터리 책임 + 운영 가이드 (학습 체크리스트 포함)
├── .arm_finetune/                  # 학습 전용 venv (hidden, Python 3.12.3, torch 2.10.0+cu130)
│                                   # setup_train_env.sh 가 생성. rsync 배포 제외
├── scripts/                        # 환경 구축·운영 스크립트
│   ├── setup_train_env.sh          # venv 생성 + PyTorch + lerobot editable 설치 + 환경변수 자동 적용
│   ├── preflight_check.sh          # 학습 전 OOM/Walking RL 보호 게이트 (smoke/s1/s3/lora 시나리오)
│   ├── smoke_test.sh               # lerobot-train --steps=1 검증 (02 마일스톤 산출물)
│   └── save_dummy_checkpoint.sh    # dummy 체크포인트 생성 (ckpt 호환성 검증용, 02 산출물)
├── runs/                           # 마일스톤별 학습 실행 자료 (05 진입 시 채움)
│   └── README.md                   # 구조 안내
└── outputs/                        # 학습 출력 (체크포인트, 로그) — 자동 생성. rsync 배포 제외
```

추가 자산 (런타임 생성, 트리에 미포함):
- `dgx/.arm_finetune/` — venv (gitignore)
- `dgx/outputs/` — 학습 결과 (gitignore)
- `smolVLA/.hf_cache/` — HF 캐시 (HF_HOME, gitignore) — orin·dgx·datacollector 공유

비고: `docs/storage/06_dgx_venv_setting.md` 에서 실측 확인된 환경:
- Python 3.12.3 (DGX 시스템)
- torch 2.10.0+cu130 (Walking RL 검증 완료 wheel)
- lerobot editable (docs/reference/lerobot/ submodule, v0.5.1-52-g05a52238)
- GB10 CUDA capability 12.1 UserWarning — 기능 정상, 무시 가능
- smoke test throughput: 5.97 초/step, RAM peak 48 GiB (batch=8, Walking RL 동시 점유)

### 1-2) 새 구조 (04 마일스톤 종료 시점 목표)

```
dgx/
├── README.md                       # 갱신: DataCollector 인터페이스 + 새 디렉터리 안내 추가
├── .arm_finetune/                  # 유지 (변경 없음)
├── scripts/                        # 유지 (변경 없음)
│   ├── setup_train_env.sh
│   ├── preflight_check.sh
│   ├── smoke_test.sh
│   └── save_dummy_checkpoint.sh
├── runs/                           # 유지 (05 진입 시 채움)
│   └── README.md
├── tests/                          # ★ 신규 — dgx 측 환경 점검 + 회귀 검증 자산
│   └── README.md                   # tests/ 의 책임 + 자산 목록
├── config/                         # ★ 신규 — dgx 측 학습 관련 설정 캐시
│   ├── README.md                   # config/ 의 책임 + 스키마
│   └── dataset_repos.json          # DataCollector 에서 수신하는 HF 데이터셋 repo_id 목록 (placeholder)
└── outputs/                        # 유지 (자동 생성, rsync 배포 제외)
```

**추가 방향 (TODO-X2 실행 시)**:
- `run_teleoperate.sh.archive` 는 DataCollector 측으로 이관 (현재 `docs/storage/others/` 에 임시 보관 중 — TODO-D2 시점)
- `dgx/pyproject.toml` 은 현재 미존재 — 학습은 `docs/reference/lerobot/` editable 이므로 불필요. 신규 생성 여부는 TODO-X2 에서 재확인
- `dgx/lerobot/` curated 디렉터리는 도입 X (upstream 무수정 원칙 유지)

---

## 2) 핵심 컴포넌트 책임 표

| 컴포넌트 | 책임 | 04 이후 변경 |
|---|---|---|
| `dgx/scripts/setup_train_env.sh` | venv 생성 + PyTorch 2.10.0+cu130 설치 + lerobot editable 설치 + 환경변수 자동 적용 (HF_HOME / PYTORCH_CUDA_ALLOC_CONF / CUDA_VISIBLE_DEVICES). Jetson 제약 없음 (일반 pip wheel 사용 가능) | 유지. 04 에서 변경 없음 |
| `dgx/scripts/preflight_check.sh` | 학습 시작 전 필수 게이트. 5 항목: venv/환경변수 격리 / 메모리 가용성 (UMA pool) / Walking RL 프로세스 관찰 (kill 금지) / Ollama gemma3 GPU 점유 / 디스크 가용량. 시나리오별 임계치 (smoke/s1/s3/lora) | 유지. 04 에서 변경 없음 |
| `dgx/scripts/smoke_test.sh` | lerobot-train 1 step 검증. preflight → 1-step 학습 → nvidia-smi + free -m 샘플링. 02 마일스톤 prod 검증 산출물 | 유지. 04 에서 변경 없음 |
| `dgx/scripts/save_dummy_checkpoint.sh` | dummy ckpt 생성 (DGX→Orin 전송 검증용). --save_checkpoint=true, steps=1, output_dir=outputs/train/dummy_ckpt | 유지. 04 에서 변경 없음 |
| `dgx/runs/` | 마일스톤별 학습 실행 명령·하이퍼파라미터·메모 보관. 05 진입 시 05_leftarm/ 채움 | 05 진입 시 활성화 |
| `dgx/outputs/` (런타임) | 학습 결과 (체크포인트, 로그, resource samples). lerobot-train 이 자동 생성. gitignore + rsync 배포 제외 | 유지. 04 에서 변경 없음 |
| `dgx/.arm_finetune/` (런타임) | SmolVLA 학습 전용 venv. Python 3.12.3, torch 2.10.0+cu130. Walking RL venv (/home/laba/env_isaaclab/) 와 경로·환경변수 격리 | 유지. 04 에서 변경 없음 |
| `dgx/tests/` (신규) | dgx 측 환경 점검 자산. preflight 와 보완 관계. TODO-X2 에서 신규 생성 (실 스크립트는 TODO-X3 이전에 필요한 경우만) | 04 TODO-X2 에서 신규 |
| `dgx/config/` (신규) | 학습 관련 설정 캐시. DataCollector 로부터 수신하는 HF 데이터셋 repo_id 목록 등 | 04 TODO-X2 에서 신규 |

---

## 3) 마일스톤별 책임 매트릭스

각 마일스톤에서 어느 컴포넌트가 사용/수정되는지. (✓=사용, ✏️=수정·신규, -=무관)

| 컴포넌트 | 00_orin_setting | 01_teleoptest | 02_dgx_setting | 03_smolvla_test_on_orin | 04_infra_setup | 05_leftarmVLA | 06_biarm_teleop | 07_biarm_VLA | 08_biarm_deploy |
|---|---|---|---|---|---|---|---|---|---|
| `scripts/setup_train_env.sh` | - | - | ✏️ | - | - | ✓ (재실행) | - | ✓ (재실행) | - |
| `scripts/preflight_check.sh` | - | - | ✏️ | - | - | ✓ | ✓ | ✓ | ✓ |
| `scripts/smoke_test.sh` | - | - | ✏️ | - | ✓ (TODO-X3) | ✓ (학습 전 검증) | - | ✓ | - |
| `scripts/save_dummy_checkpoint.sh` | - | - | ✏️ | ✓ (TODO-10b) | ✓ (TODO-X3) | - | - | - | - |
| `runs/05_leftarm/` | - | - | - | - | - | ✏️ (진입 시 생성) | - | - | - |
| `runs/07_biarm/` | - | - | - | - | - | - | - | ✏️ (진입 시 생성) | - |
| `outputs/` | - | - | - | ✓ (dummy_ckpt) | ✓ (TODO-X3 smoke) | ✏️ (학습 결과 누적) | - | ✏️ | - |
| `tests/` (신규) | - | - | - | - | ✏️ (TODO-X2 신규) | ✓ | - | ✓ | - |
| `config/` (신규) | - | - | - | - | ✏️ (TODO-X2 신규) | ✓ (TODO-T1 결정 후) | ✓ | ✓ | ✓ |
| `README.md` | - | - | ✏️ | - | ✏️ (DataCollector 인터페이스 추가) | - | - | - | - |
| `dgx/.arm_finetune/` (venv) | - | - | ✏️ (최초 생성) | - | - | ✓ | ✓ | ✓ | ✓ |

**관찰**:
- `scripts/preflight_check.sh` 는 **모든 학습 마일스톤의 필수 게이트** — Walking RL 보호 정책상 생략 불가
- `runs/` 디렉터리는 각 VLA 마일스톤 진입 직전에 채워지는 YAGNI 패턴 — 04 에서는 비어 있음
- `outputs/` 는 gitignore + rsync 제외 — devPC 가 관여하지 않음 (ckpt 전송은 `sync_ckpt_dgx_to_orin.sh` 별도 경로)
- DGX 는 SO-ARM 직접 연결 없음 → `lerobot-record`, `lerobot-calibrate`, `lerobot-teleoperate` entrypoint 는 DGX 에서 사용하지 않음 (DataCollector 의 책임)

---

## 4) 외부 의존성

### 4-1) devPC sync hub

```
devPC scripts/                  DGX 측 효과
└── deploy_dgx.sh ──→ rsync    dgx/ + docs/reference/lerobot/ (editable 설치 대상)
                                ※ outputs/, .arm_finetune/ 는 rsync 배포 제외
```

<!-- 정정 (2026-05-02): DataCollector 운영 종료 (06 결정). DataCollector → DGX 전송 인터페이스 무효화.
     DGX 가 직접 데이터 수집하므로 sync 불필요. scripts/sync_dataset_collector_to_dgx.sh 는
     legacy 이관 완료 (docs/storage/legacy/02_datacollector_separate_node/). -->
DataCollector → DGX 데이터 전송 (TODO-T1 결정 후) — **정정: 06 결정으로 DataCollector 운영 종료, 아래 내용은 역사적 보존**:
- **HF Hub 경유 (권장)**: DataCollector 에서 `lerobot-record --push-to-hub` → DGX 에서 `lerobot-train --dataset.repo_id=<HF_USER>/...`
- **rsync 직접**: `scripts/sync_dataset_collector_to_dgx.sh` → **legacy 이관 완료 (L2, 2026-05-02)**

DGX → Orin 체크포인트 전송:
- `scripts/sync_ckpt_dgx_to_orin.sh` (devPC 경유 2-hop rsync)
- 시연장 시나리오 재확인은 TODO-T2

### 4-2) HuggingFace Hub

| 자산 | 흐름 |
|---|---|
| smolvla_base 사전학습 가중치 | Hub → DGX (HF_HOME=`~/smolvla/.hf_cache`) |
| 학습 데이터셋 | DataCollector → Hub → DGX (TODO-T1 결정에 따라) 또는 rsync 직접 |
| 학습 ckpt | DGX `outputs/train/` → (devPC 경유 rsync) → Orin `checkpoints/`. Hub 미경유 |

HF 캐시 격리: `HF_HOME=/home/laba/smolvla/.hf_cache` (Walking RL 시스템 디폴트 캐시와 격리, venv 활성화 시 자동 적용)

### 4-3) DataCollector ↔ DGX 인터페이스

```
DataCollector:
  lerobot-record → 데이터셋 (LeRobotDataset 포맷)
      ↓
  HF Hub push (lerobot-record --push-to-hub) 또는 rsync (TODO-T1 결정)
      ↓
DGX:
  lerobot-train --dataset.repo_id=<HF_USER>/... 또는 --dataset.local_path=...
      ↓
  outputs/train/<run_name>/checkpoints/<step>/pretrained_model/
```

**DataCollector ↔ DGX 인터페이스 미결 사항**: TODO-T1 (`awaits_user`) — HF Hub vs rsync 직접 vs 둘 다. 결정에 따라 §5 마이그레이션 계획의 config/dataset_repos.json 스키마가 영향받음.

### 4-4) DGX 시스템 의존성

DGX Spark (GB10, UMA, CUDA 13.0, Ubuntu 24.04.4 LTS) 환경:
- 시스템 Python 3.12.3 (Walking RL 동일)
- CUDA 13.0 (드라이버 580.142)
- cuDNN / NCCL: PyTorch wheel 번들 (시스템 별도 설치 X — Orin 와 다름)
- Walking RL 트랙 (`/home/laba/env_isaaclab/`) 동시 점유 — 리소스 공유 환경
- Ollama (gemma3 로드 시 17 GB GPU 점유 가능) — preflight 게이트로 관리

Orin 과의 차이 (체크포인트 호환성 핵심):
| 항목 | DGX | Orin |
|---|---|---|
| Python | 3.12.3 | 3.10 (JetPack 6.2.2) |
| torch | 2.10.0+cu130 | 2.5.0a0+nv24.08 |
| lerobot | editable submodule 무수정 | curated orin/lerobot/ (트리밍 적용) |
| safetensors | wheel 번들 | wheel 번들 |

safetensors 직렬화는 Python 마이너 버전 독립적 → ckpt 호환성 확인 완료 (02 TODO-10b).

### 4-5) Walking RL 보호 정책

DGX 는 팀 공용 머신. SmolVLA 학습은 Walking RL 잔여 자원만 사용:
- preflight_check.sh 의 Walking RL 프로세스 관찰 (kill 금지 — 절대 원칙)
- `CUDA_VISIBLE_DEVICES=0` — GPU 0 명시 사용
- 메모리 안전 마진 +10 GiB 자동 적용

---

## 5) 마이그레이션 계획 (TODO-X2 의 입력)

5개 카테고리로 분류. **원칙**: upstream 코드 무수정, dgx/lerobot/ curated 디렉터리 미도입.

### 5-1) 유지

| 항목 | 현재 위치 | 사유 |
|---|---|---|
| `dgx/scripts/setup_train_env.sh` | `dgx/scripts/` | 02 산출물. 학습 환경 셋업 핵심. 변경 시 회귀 위험 높음. 동작 이상 없음 |
| `dgx/scripts/preflight_check.sh` | `dgx/scripts/` | 02 산출물. Walking RL 보호 + OOM 방어 게이트. 변경 시 보호 정책 훼손 위험 |
| `dgx/scripts/smoke_test.sh` | `dgx/scripts/` | 02 산출물. 1-step 검증 + 자원 샘플링. 04 TODO-X3 에서 재사용 |
| `dgx/scripts/save_dummy_checkpoint.sh` | `dgx/scripts/` | 02 산출물. DGX→Orin ckpt 전송 검증용. 04 TODO-X3 에서 재사용 |
| `dgx/runs/README.md` | `dgx/runs/` | YAGNI. 05 진입 시 runs/ 하위 채움 |
| `dgx/README.md` | `dgx/` | 갱신만 (§4-4 참조) |
| `dgx/.arm_finetune/` | `dgx/` | venv. gitignore. 재생성 시 setup_train_env.sh 재실행 |

### 5-2) 이관 (out)

| 항목 | 현재 보관 위치 | 최종 위치 | 사유 |
|---|---|---|---|
| `run_teleoperate.sh` | `docs/storage/others/run_teleoperate.sh.archive` (임시 보관) | DataCollector 측 (TODO-D2 시점에 최종 이동) | DGX 는 SO-ARM 직접 연결 X. teleop 책임은 DataCollector. 현 시점 DataCollector 디렉터리 미존재 → TODO-D2 까지 archive 유지 |

**run_teleoperate.sh 최종 위치 결정 (본 TODO-X1 핵심 결정)**:

후보 (a) DataCollector (채택): SO-ARM teleop 은 시연장 인근 데이터 수집의 일부. DataCollector 가 SO-ARM 직접 연결. `datacollector/scripts/run_teleoperate.sh` 위치가 책임상 올바름.

후보 (b) DGX 보관: SO-ARM 직접 연결 없음 → 실행 불가. 부적합.

후보 (c) 임시 보관 유지: TODO-D2 결정까지 임시 유지 가능. 단, DataCollector 가 확정되는 시점 (TODO-D1~D2) 에 즉시 이동해야 함.

**권고**: (a) DataCollector. DGX 에서의 의미 없음. `docs/storage/others/run_teleoperate.sh.archive` 는 TODO-D2 시점에 `datacollector/scripts/run_teleoperate.sh` 로 최종 이동.

### 5-3) 신규 (in)

| 항목 | 신규 위치 | 초기 내용 |
|---|---|---|
| `dgx/tests/` + README.md | `dgx/tests/README.md` | tests/ 의 책임 + 자산 목록. 실 검증 스크립트는 TODO-X3 이전에 필요한 경우만 추가 |
| `dgx/config/` + README.md | `dgx/config/README.md` | config/ 의 책임 + dataset_repos.json 스키마. 실 값은 TODO-T1 결정 후 채움 |
| `dgx/config/dataset_repos.json` | `dgx/config/` | placeholder. DataCollector 에서 수신하는 HF 데이터셋 repo_id 목록 (TODO-T1 결정에 따라 스키마 변경 가능) |

### 5-4) 삭제 (rm)

현 시점 삭제 대상 없음.

비고: `dgx/outputs/` 는 런타임 생성 자산으로 git 추적 대상 아님. 정기 정리는 사용자 직접 수행 (rm 자동화 X — Walking RL 트랙 공용 환경).

### 5-5) entrypoint 정리

DGX 는 `pyproject.toml` 미존재 (`dgx/pyproject.toml` 없음). 학습 entrypoint 는 `docs/reference/lerobot/` editable 설치로 lerobot upstream 그대로 제공됨.

본 프로젝트에서 DGX 측에서 실제 사용하는 entrypoint:
- `lerobot-train` — 학습 (05 이후 본격 사용)
- (smoke_test.sh 와 save_dummy_checkpoint.sh 에서 호출)

DGX 에서 사용하지 않는 entrypoint (DataCollector 또는 Orin 의 책임):
- `lerobot-record` — DataCollector 의 책임
- `lerobot-calibrate`, `lerobot-teleoperate`, `lerobot-find-port`, `lerobot-find-cameras`, `lerobot-setup-motors` — DataCollector 또는 Orin 의 책임

비활성화 방법: DGX 에서는 entrypoint 비활성화 (pyproject.toml 미존재이므로 orin/ 의 논리적 비활성화 패턴 불필요). 단, 실수로 DataCollector 책임 entrypoint 를 DGX 에서 호출하는 것을 방지하기 위해 README.md 에 명시적 주의사항 추가 (TODO-X2).

**부수 작업 (TODO-X2 안에 포함)**:
- `dgx/README.md` 갱신: DataCollector 인터페이스 (§4-3) + 새 디렉터리 (tests/, config/) 안내 추가
- `.gitignore` 확인: `smolVLA/dgx/outputs/` 패턴 이미 존재 여부 확인 + 미존재 시 추가
- `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 확인: 이미 존재 (02 마일스톤 산출물). TODO-X2 에서 dgx/ 코드 변경 없으므로 갱신 불필요. 단, tests/, config/ 신규 생성은 이력 추가 권장

---

## 6) 후속 TODO 트리거 포인트

본 §1~§5 산출물이 다음 04 TODO 의 입력이 됨:

- **TODO-X2**: §5 마이그레이션 계획 그대로 실행. 신규 2건 (tests/, config/) + README.md 갱신 + .gitignore 확인
- **TODO-X3**: §2 컴포넌트 책임 표 + §4-4 DGX 시스템 의존성으로 smoke test 회귀 항목 도출. save_dummy_checkpoint.sh 재실행으로 ckpt 생성 검증
- **TODO-T1**: §4-3 DataCollector ↔ DGX 인터페이스 (HF Hub vs rsync 결정) → config/dataset_repos.json 스키마 확정
- **TODO-T2**: §4-1 devPC sync hub / sync_ckpt_dgx_to_orin.sh 시연장 시나리오 재확인
- **TODO-D2**: §5-2 이관 항목 — run_teleoperate.sh archive 가 DataCollector 디렉터리로 최종 이동

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 04 TODO-X1 산출물. 4-노드 분리 아키텍처에서 DGX 학습 전용 책임 명확화. run_teleoperate.sh DataCollector 이관 결정 (후보 a 채택). 5개 마이그레이션 카테고리 정의. DataCollector ↔ DGX 인터페이스는 TODO-T1 awaits_user 답에 따라 §5-3 config/ 스키마 갱신 필요 명시 |
| 2026-05-02 | `dgx/scripts/setup_train_env.sh` §3-c 블록 추가 — 06_dgx_absorbs_datacollector TODO-X5. record·hardware·feetech extras (torchcodec cu130 인덱스 별도 + 9개 PyPI 패키지) 설치 step 삽입. Option B 채택 (dgx/pyproject.toml 미변경). |
