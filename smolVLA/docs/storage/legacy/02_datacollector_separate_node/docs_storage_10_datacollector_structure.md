# datacollector/ 디렉터리 구조·기능 책임 매트릭스 + 마이그레이션 계획

> 작성일: 2026-05-02
> 출처: `05_interactive_cli` 마일스톤 Phase 3 검증 중 사용자 요청 문서 정리
> 목적: datacollector/ 의 현재 구조 명문화 + 후속 마일스톤 (06~09) 에서 어느 컴포넌트가 어떤 책임을 지는지 한 곳에 정리
> 형제 문서: `docs/storage/08_orin_structure.md` (TODO-O1 산출물) / `docs/storage/09_dgx_structure.md` (TODO-X1 산출물)
> 설계 기준: 04·05 사이클 실 산출물 (09_datacollector_setup.md §3 설계 기준 — 파일 삭제 후 본 문서에 정보 흡수)

---

## 0) 본 문서의 위치

04 마일스톤에서 4-노드 분리 아키텍처 (devPC / DataCollector / DGX / 시연장 Orin) 가 공식화되었다. DataCollector 는 신규 도입 노드로, **데이터 수집 전용** 책임을 가진다.

### DataCollector 의 단일 책임

- SO-ARM 직접 연결 (리더 암 + 팔로워 암)
- 카메라 입력 (시연장 카메라)
- `lerobot-record` / `lerobot-teleoperate` / `lerobot-calibrate` 실행 (데이터 수집)
- 수집 데이터셋 → HF Hub 또는 rsync 로 DGX 전달 (둘 다 지원 — TODO-T1 결정 완료)

**DataCollector 가 담당하지 않는 것:**
- 추론 (Orin 의 책임)
- 학습 (DGX 의 책임)
- devPC 코드 배포 허브 역할 (devPC 의 책임)

**핵심 원칙 — upstream 구조 보존**: `datacollector/lerobot/` 도 orin/ 과 동일한 **옵션 B 원칙** 적용 예정 — upstream 파일 변경 X, `pyproject.toml [project.scripts]` entrypoint 등록만으로 비활성화 범위 제한. 단, 04·05 사이클 모두 `datacollector/lerobot/` curated subset 구성이 **미진행**. 향후 별도 todo 로 처리 예정 (§5 참조).

---

## 1) 디렉터리 트리 (현재)

### 1-1) 현재 (2026-05-02 실측)

```
datacollector/
├── README.md                        # 디렉터리 책임 + 운영 가이드
├── pyproject.toml                   # 의존성 정의 (record+hardware+feetech, smolvla·training 제외)
├── config/                          # 하드웨어 설정 캐시 (orin/config/ 패턴 미러)
│   └── README.md                    # config/ 의 책임 + 스키마
├── data/                            # 수집된 LeRobotDataset (.gitignore)
│   └── README.md
├── interactive_cli/                 # ← 05 F2·D2 산출물 (main.sh + flows/)
│   ├── main.sh                      # 사용자 대화형 CLI 진입점
│   ├── README.md
│   ├── configs/
│   │   └── node.yaml                # 노드 설정 (IP, 포트 등)
│   └── flows/
│       ├── __init__.py
│       ├── env_check.py             # 환경 점검 (venv, lerobot, HW)
│       ├── teleop.py                # teleop 흐름
│       ├── data_kind.py             # 데이터 종류 선택
│       ├── record.py                # 녹화 흐름
│       ├── transfer.py              # 데이터 전송 흐름
│       └── entry.py                 # CLI 진입 흐름
├── scripts/                         # 운영 스크립트
│   ├── setup_env.sh                 # venv 생성 (04 D2 산출물)
│   ├── run_teleoperate.sh           # SO-ARM teleop (04 D2 산출물 — archive 에서 이관)
│   └── push_dataset_hub.sh          # HF Hub 업로드 (04 D2 산출물)
└── tests/                           # 환경 점검 게이트 (예정)
    └── README.md
```

**런타임 생성 자산 (트리 미포함)**:
- `datacollector/.hylion_collector/` — venv (gitignore)
- `datacollector/data/` 하위 실제 데이터 — (gitignore, 수백 MB ~ GB)
- `datacollector/interactive_cli/flows/__pycache__/` — bytecode (gitignore)

**현재 미존재 (향후 추가 예정)**:
- `datacollector/lerobot/` — upstream curated subset. 04·05 사이클 모두 미진행. 향후 별도 todo.

### 1-2) 목표 구조 (09_datacollector_setup.md §3-2 기준)

```
datacollector/
├── README.md
├── pyproject.toml                   # 신규 작성 완료 (04 D2)
├── lerobot/                         # upstream curated subset (미진행 — 향후 todo)
│   └── ...                          # 옵션 B 원칙 적용 예정
├── scripts/
│   ├── setup_env.sh                 # 완료 (04 D2)
│   ├── run_teleoperate.sh           # 완료 (04 D2)
│   └── push_dataset_hub.sh          # 완료 (04 D2)
├── interactive_cli/                 # 완료 (05 D2·F2)
│   ├── main.sh
│   ├── configs/node.yaml
│   └── flows/
├── tests/                           # README.md 만 존재 (실 스크립트 TODO-G3 예정)
│   └── README.md
├── config/                          # README.md 만 존재 (실측값 TODO-G3 채움)
│   ├── README.md
│   ├── ports.json                   # (미생성 — TODO-G3 first-time 모드)
│   └── cameras.json                 # (미생성 — TODO-G3 first-time 모드)
└── data/                            # gitignore
    └── README.md
```

---

## 2) 핵심 컴포넌트 책임 표

| 컴포넌트 | 책임 | 현재 상태 | 도입 시점 |
|---|---|---|---|
| `pyproject.toml` | 의존성 정의 (record + hardware + feetech). orin subset. smolvla·training 제외. 9개 entrypoint (lerobot-eval·lerobot-train 제외) | **완료** (04 D2) | 04 마일스톤 |
| `scripts/setup_env.sh` | venv `.hylion_collector` 생성 + lerobot `[record,hardware,feetech]` editable install + x86_64 표준 torch 설치 + 환경변수 설정. Jetson 특수 처리 없음 | **완료** (04 D2) | 04 마일스톤 |
| `scripts/run_teleoperate.sh` | SO-ARM teleop 실행 래퍼 (orin/scripts/ archive 에서 최종 이관) | **완료** (04 D2) | 04 마일스톤 |
| `scripts/push_dataset_hub.sh` | 수집된 LeRobotDataset → HF Hub push | **완료** (04 D2) | 04 마일스톤 |
| `interactive_cli/` | 사용자 대화형 CLI. main.sh (bash) + flows/ (Python). 환경점검·teleop·녹화·전송 흐름 통합 | **완료** (05 D2·F2) | 05 마일스톤 |
| `interactive_cli/configs/node.yaml` | 노드 설정 (IP, 포트, 카메라 등) | **완료** (05 F2) | 05 마일스톤 |
| `tests/` | 환경 점검 게이트. orin/tests/check_hardware.sh DataCollector 버전 이식 예정 | README.md 만 존재 | TODO-G3 |
| `config/ports.json` | SO-ARM 포트 캐시 (lerobot-find-port 결과) | **미생성** | TODO-G3 first-time 모드 |
| `config/cameras.json` | 카메라 인덱스/flip/slot 매핑 캐시 | **미생성** | TODO-G3 first-time 모드|
| `data/` | 수집된 LeRobotDataset. gitignore. lerobot-record 가 자동 생성 | README.md 만 존재 | 05~06 마일스톤 (첫 데이터 수집) |
| `.hylion_collector/` | venv (런타임, gitignore) | **미생성** (실물 셋업 전) | setup_env.sh 실행 후 |
| `lerobot/` | upstream curated subset (옵션 B 적용 예정) | **미존재** | 향후 별도 todo |

---

## 3) 마일스톤별 책임 매트릭스

각 마일스톤에서 어느 컴포넌트가 사용/수정되는지. (✓=사용, ✏️=수정·신규, -=무관)

| 컴포넌트 | 04_infra_setup | 05_interactive_cli | 06_biarm_teleop | 07_biarm_VLA | 08_biarm_deploy |
|---|---|---|---|---|---|
| `pyproject.toml` | ✏️ (D2 신규) | - | - | - | - |
| `scripts/setup_env.sh` | ✏️ (D2 신규) | - | ✓ (재실행) | - | ✓ |
| `scripts/run_teleoperate.sh` | ✏️ (D2 이관) | ✓ (interactive_cli 에서 호출) | ✓ | - | - |
| `scripts/push_dataset_hub.sh` | ✏️ (D2 신규) | ✓ (transfer 흐름) | ✓ | - | - |
| `interactive_cli/` | - | ✏️ (D2·F2 신규) | ✓ | - | - |
| `interactive_cli/configs/node.yaml` | - | ✏️ (F2 신규) | ✓ | - | - |
| `tests/` | ✏️ (D2: README.md) | - | ✏️ (TODO-G3) | - | ✓ |
| `config/ports.json` | - | - | ✏️ (TODO-G3 first-time) | ✓ | ✓ |
| `config/cameras.json` | - | - | ✏️ (TODO-G3 first-time) | ✓ | ✓ |
| `data/` | - | - | ✏️ (첫 데이터 수집) | ✓ | - |
| `.hylion_collector/` (venv) | ✏️ (최초 생성) | - | ✓ | ✓ | ✓ |
| `lerobot/` (미존재) | - | - | ✏️ (향후 todo) | - | - |

**관찰**:
- `scripts/setup_env.sh` 는 실물 셋업 시 최초 1회 + 환경 재구성 시 재실행
- `interactive_cli/` 는 05 마일스톤의 핵심 산출물 — 06 이후 실제 데이터 수집 운영에 활용
- `lerobot/` curated subset 은 04·05 모두 미진행. 현재 `setup_env.sh` 의 upstream symlink 로 임시 처리
- `tests/`, `config/` 의 실 자산은 TODO-G3 (DataCollector hardware check) 시점에 채워짐

---

## 4) 외부 의존성

### 4-1) devPC sync hub

```
devPC scripts/                        DataCollector 측 효과
├── deploy_datacollector.sh ──→ rsync  datacollector/* (lerobot/ + scripts/ + interactive_cli/ +
│                                       config/ — .hylion_collector/, data/ 제외)
└── sync_dataset_collector_to_dgx.sh   DataCollector data/ → DGX (rsync 직접 경로 — TODO-T1 완료)
```

devPC sync hub 전체 구성 (흡수: 09_datacollector_setup.md §5-5):

```
devPC scripts/
├── deploy_orin.sh              → rsync orin/* → Orin
├── deploy_dgx.sh               → rsync dgx/ + docs/reference/lerobot/ → DGX
├── deploy_datacollector.sh     → rsync datacollector/* → DataCollector (TODO-T3 완료)
├── sync_ckpt_dgx_to_orin.sh    → DGX outputs/ → Orin checkpoints/ (devPC 경유)
└── sync_dataset_collector_to_dgx.sh  → DataCollector data/ → DGX (TODO-T1, rsync 경로)
```

`deploy_datacollector.sh` 의 rsync 제외 패턴 (설계 기준):
- `--exclude '.hylion_collector'`
- `--exclude '__pycache__'`
- `--exclude '*.pyc'`
- `--exclude 'data/'`

### 4-2) HuggingFace Hub

| 자산 | 흐름 |
|---|---|
| 수집 데이터셋 | DataCollector `lerobot-record --push-to-hub` → Hub → DGX `lerobot-train --dataset.repo_id=...` |
| DataCollector 가중치 | 해당 없음 (추론·학습 X) |

### 4-3) DataCollector → DGX 데이터 전송 (TODO-T1 결정 완료 — 둘 다 지원, 흡수: 09_datacollector_setup.md §5-3)

| 전송 방식 | 시나리오 | 구현 상태 |
|---|---|---|
| HF Hub | 인터넷 가용 환경 (일반적) | `scripts/push_dataset_hub.sh` (04 D2 완료) |
| rsync 직접 | 인터넷 격리 환경 또는 대용량 | `scripts/sync_dataset_collector_to_dgx.sh` (devPC 경유) |

### 4-4) DataCollector → DGX 네트워크 토폴로지 (흡수: 09_datacollector_setup.md §5-4)

```
DataCollector (시연장 WiFi)
    │
    ├── HF Hub (인터넷 경유)
    │       ↓
    │   DGX: lerobot-train --dataset.repo_id=<HF_USER>/...
    │
    └── rsync 직접 (devPC 경유 또는 직접)
            ↓
        DGX: ~/smolvla/.hf_cache/datasets/ 또는 지정 경로
             lerobot-train --dataset.local_path=...
```

DataCollector 와 DGX 가 같은 WiFi 서브넷 내에 있으면 직접 rsync 가능.
다른 서브넷 (시연장 ↔ 연구실) 이면 devPC 2-hop 경유 또는 HF Hub 사용.
`04_devnetwork.md §2` 에서 DataCollector (시연장 WiFi) 와 DGX (연구실 WiFi) 가 별도 서브넷인 경우를 설명.

### 4-5) 시스템 의존성

DataCollector (`smallgaint`) 2026-05-02 실측 기준:

| 의존성 | 상태 | 비고 |
|---|---|---|
| git | 설치됨 | 코드 배포 |
| rsync | 설치됨 | devPC deploy |
| libusb-1.0-0 | 설치됨 | USB 장치 접근 |
| build-essential | 설치됨 | 빌드 도구 |
| python3 | 설치됨 (3.10.12) | 시스템 Python |
| python3-venv | **미설치** | venv 생성 필요 — 셋업 전 설치 필요 |
| python3-pip | **미설치** | pip 사용 필요 |
| ffmpeg | **미설치** | lerobot-record 비디오 인코딩 필요 |
| v4l-utils | **미설치** | lerobot-find-cameras 필요 |
| dialout 그룹 | **미포함** | SO-ARM USB 직렬 포트 접근 필요 |

DataCollector 는 Jetson (aarch64) 이 아니므로:
- CUDA 관련 패키지 불필요 (`libcudnn`, `libcusparseLt` 등)
- `libopenblas-dev`, `libopenmpi-dev` 는 setup_env.sh §0 에서 설치

---

## 5) 마이그레이션 계획

### 5-1) 완료

| 항목 | 위치 | 완료 시점 |
|---|---|---|
| `pyproject.toml` 신규 작성 | `datacollector/pyproject.toml` | 04 D2 |
| `scripts/setup_env.sh` 신규 작성 | `datacollector/scripts/setup_env.sh` | 04 D2 |
| `scripts/run_teleoperate.sh` 이관 | `datacollector/scripts/run_teleoperate.sh` | 04 D2 (archive 에서 최종 이동) |
| `scripts/push_dataset_hub.sh` 신규 작성 | `datacollector/scripts/push_dataset_hub.sh` | 04 D2 |
| `interactive_cli/` 신규 작성 | `datacollector/interactive_cli/` | 05 D2·F2 |
| `config/README.md` 신규 | `datacollector/config/README.md` | 04 D2 |
| `data/README.md` 신규 | `datacollector/data/README.md` | 04 D2 |
| `tests/README.md` 신규 | `datacollector/tests/README.md` | 04 D2 |

### 5-2) 미진행 (향후 todo)

| 항목 | 예정 위치 | 담당 todo | 사유 |
|---|---|---|---|
| `lerobot/` curated subset 구성 | `datacollector/lerobot/` | 향후 별도 todo | 04·05 사이클 모두 스코프 외. 현재 setup_env.sh 의 upstream symlink 로 임시 처리. orin/lerobot/ 옵션 B 패턴 동일 적용 예정 |
| `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 | docs/storage/lerobot_upstream_check/ | 향후 별도 todo (lerobot/ 구성 시 동시) | lerobot/ curated subset 구성 전까지 불필요 |
| `config/ports.json` | `datacollector/config/` | TODO-G3 | lerobot-find-port 실물 실행 후 캐시 |
| `config/cameras.json` | `datacollector/config/` | TODO-G3 | lerobot-find-cameras 실물 실행 후 캐시 |
| `tests/check_hardware.sh` 이식 | `datacollector/tests/` | TODO-G3 | orin/tests/check_hardware.sh DataCollector 버전 |
| 실물 venv 셋업 | `~/smolvla/datacollector/` 에서 실행 | 실물 DataCollector 셋업 시 | 현재 DataCollector 미설치 상태 |

### 5-3) datacollector/lerobot/ 옵션 B 적용 계획 (향후)

`datacollector/lerobot/` 는 orin/lerobot/ 과 동일한 옵션 B 원칙을 따를 예정:

- upstream 파일 변경 X (파일·디렉터리 단에서 수정 금지)
- `pyproject.toml [project.scripts]` 의 entrypoint 등록으로만 활성화 범위 제한
- `lerobot-eval`, `lerobot-train` 등 DataCollector 미사용 entrypoint 는 등록 제외

활성화 예정 entrypoint (09_datacollector_setup.md §3-4):
```
lerobot-record, lerobot-replay, lerobot-teleoperate, lerobot-calibrate,
lerobot-setup-motors, lerobot-find-cameras, lerobot-find-port,
lerobot-find-joint-limits, lerobot-info
```

coupled file 의무: `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 작성 (orin 의 `03_orin_lerobot_diff.md` 패턴 동일 적용).

---

## 6) 후속 TODO 트리거 포인트

| TODO | 본 문서 연결 절 | 내용 |
|---|---|---|
| 실물 셋업 | §4-4, §5-2 | python3-venv/pip 등 사전 패키지 설치 + dialout 그룹 + setup_env.sh 실행 |
| TODO-G3 | §2, §5-2 | orin/tests/check_hardware.sh DataCollector 버전 이식 + config/ first-time 캐시 생성 |
| lerobot/ 옵션 B | §5-3 | datacollector/lerobot/ curated subset 구성 + 05_datacollector_lerobot_diff.md 신규 작성 |
| 06 마일스톤 진입 | §3 마트릭스 | 첫 biarm teleop 데이터 수집 — interactive_cli + scripts 본격 사용 |
| TODO-T2 | §4-1 | devPC sync_ckpt_dgx_to_orin.sh 시연장 시나리오 재확인 (DataCollector 관련) |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-02 | 초안 작성 — `05_interactive_cli` Phase 3 검증 중 사용자 요청으로 신규 작성. 2026-05-02 SSH read-only 실측값 반영 + 04·05 사이클 실 산출물 (D2·F2) 기반 현재 트리 문서화. `datacollector/lerobot/` 미진행 상태 명시 — 향후 별도 todo 로 처리 예정. `08_orin_structure.md` / `09_dgx_structure.md` 패턴 미러. |
| 2026-05-02 (재정렬) | docs/storage 재정렬에 따라 번호 `16` → `10` 으로 변경. 형제 문서 참조 `07/08_*` → `08/09_*` 갱신. 설계 기준 주석 갱신 (09_datacollector_setup.md 삭제 명시). §4-1 에 devPC sync hub 전체 구성 (§5-5 흡수) 추가. §4-3 에 09 §5-3 흡수 명시. §4-4 신규 추가 (DataCollector → DGX 네트워크 토폴로지, §5-4 흡수). §4-4→§4-5 로 번호 시프트 (시스템 의존성). |
