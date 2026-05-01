# DataCollector 노드 셋업 — 정체·venv·디렉터리·네트워크

> 작성일: 2026-05-01
> 출처: `04_infra_setup` 마일스톤 TODO-D1
> 목적: DataCollector 노드의 하드웨어·OS·venv·lerobot 의존성·디렉터리 구조 결정 문서화.
>       devPC sync hub 및 DGX 와의 관계를 정의하고, 후속 TODO-D2 (실제 셋업 실행) 의 입력 사양을 제공.
> 형제 문서: `docs/storage/07_orin_structure.md` (TODO-O1 산출물) / `docs/storage/08_dgx_structure.md` (TODO-X1 산출물)

---

## 0) 본 문서의 위치

04 마일스톤에서 4-노드 분리 아키텍처 (devPC / DataCollector / DGX / 시연장 Orin) 가 공식화되었다.
그 중 DataCollector 는 **신규 도입 노드**로, 본 문서가 그 설계 기준을 확립한다.

### DataCollector 의 단일 책임

- SO-ARM 직접 연결 (리더 암 + 팔로워 암)
- 카메라 입력 (시연장 카메라)
- `lerobot-record` / `lerobot-teleoperate` / `lerobot-calibrate` 실행 (데이터 수집)
- 수집 데이터셋 → HF Hub 또는 rsync 로 DGX 전달 (TODO-T1 결정 완료: 둘 다 지원)

**DataCollector 가 담당하지 않는 것:**
- 추론 (Orin 의 책임)
- 학습 (DGX 의 책임)
- devPC 코드 배포 허브 역할 (devPC 의 책임)

---

## 1) 노드 정체 (하드웨어·OS·네트워크)

### 1-1) 하드웨어 결정

| 항목 | 결정 | 결정 근거 |
|---|---|---|
| 하드웨어 형태 | **별도 PC 신규 구매** | 기존 노트북 재활용 대비 안정적 시연장 고정 배치 가능, SO-ARM USB 포트 전용 확보 |
| OS | **Ubuntu 22.04 LTS** | lerobot upstream 안정성 (Python 3.12 표준 venv, ubuntu 22.04 LTS 장기 지원), Orin/DGX 와 동일 OS 패밀리 |
| 아키텍처 | **x86_64** | 신규 PC 구매 시 표준 x86_64 — Jetson 제약 없음, 표준 PyPI wheel 사용 가능 |

### 1-2) 네트워크 설계

DataCollector 는 시연장 인근에 배치된다. 네트워크 환경은 시연장 WiFi (학교 HY-WiFi 또는 별도 공유기) 에 의존.

| 장비 | 역할 | 예상 네트워크 |
|---|---|---|
| devPC | 코드 배포 hub + SSH 연결 관리 | 학교 WiFi (DHCP) |
| DataCollector | SO-ARM teleop + 데이터 수집 | 시연장 WiFi (DHCP) |
| DGX | 학습 전용 | 연구실 WiFi (DHCP) |
| Orin | 추론 전용 (시연장 영구 배치) | 시연장 WiFi (DHCP) |

**시연장 WiFi 구성 시 고려사항 (§4 참조)**:
- DataCollector ↔ devPC 모두 동일 네트워크 서브넷 필요 (mDNS 불가 시 IP 직접 기재)
- HF Hub 업로드가 필요한 경우 인터넷 접근 가능 WiFi 필요
- DHCP 변동 리스크 — §4 에서 상세 기술

### 1-3) 장비 정보 (예정, 실물 구매 후 갱신)

| 항목 | 값 |
|---|---|
| 호스트명 | `datacollector` (권장 — 확정 후 업데이트) |
| 유저명 | `laba` (orin·dgx 와 통일, 권장) |
| WiFi IP | 구매·배치 후 확인 |
| SSH 포트 | `22` |

---

## 2) venv·lerobot 의존성 (orin venv 와의 차이점)

### 2-1) venv 설계 원칙

DataCollector 는 x86_64 Ubuntu 22.04 환경이므로 **Jetson 제약이 없다**:
- PyTorch: 표준 PyPI wheel (`torch`, `torchvision`) 사용 가능 — NVIDIA JP 6.0 redist URL 불필요
- Python: 시스템 Python 3.12 (Ubuntu 22.04 에서 Python 3.10/3.12 모두 가능 — 3.12 권장)
- venv 관리: `python3 -m venv` 또는 `uv venv` — DGX 패턴 미러

### 2-2) venv 이름 정책

형제 노드들의 venv 네이밍 컨벤션을 따른다:

| 노드 | venv 이름 | 위치 |
|---|---|---|
| Orin | `.hylion_arm` | `~/smolvla/orin/.hylion_arm` |
| DGX | `.arm_finetune` | `~/smolvla/dgx/.arm_finetune` |
| DataCollector | `.hylion_collector` | `~/smolvla/datacollector/.hylion_collector` |

이유: 디렉터리 이름이 venv 용도 (수집 전용) 를 즉시 표현. rsync 배포 시 자동 제외 패턴 적용.

### 2-3) lerobot extras 선택 (orin/pyproject.toml subset)

lerobot upstream `pyproject.toml [project.optional-dependencies]` 에서 DataCollector 에 필요한 extras:

| Extra 키 | 포함 패키지 | DataCollector 필요 여부 | 사유 |
|---|---|---|---|
| `dataset` | datasets, pandas, pyarrow, av-dep, jsonlines | **필요** | `lerobot-record` 가 LeRobotDataset 포맷으로 저장 + HF Hub 업로드 |
| `hardware` | pynput, pyserial, deepdiff | **필요** | SO-ARM 모터 제어·키보드 입력 |
| `feetech` | feetech-servo-sdk, pyserial, deepdiff | **필요** | SO-ARM Feetech 서보 직접 구동 |
| `viz` | rerun-sdk | 선택적 | 시각화 필요 시 추가 (기본 미포함) |
| `core_scripts` | dataset + hardware + viz | **부분 필요** | viz 제외하면 record/teleoperate 동작 가능 |
| `smolvla` | transformers, num2words, accelerate | **제외** | DataCollector 는 추론 X |
| `training` | dataset + accelerate + wandb | **제외** | 학습은 DGX 책임 |
| `intelrealsense` | pyrealsense2 | 선택적 | Intel RealSense 카메라 사용 시만 추가 |

**DataCollector pyproject.toml extras 권장 구성**:

```toml
[project.optional-dependencies]
record = [
    "datasets>=4.0.0,<5.0.0",
    "pandas>=2.0.0,<3.0.0",
    "pyarrow>=21.0.0,<30.0.0",
    "av>=15.0.0,<16.0.0",
    "jsonlines>=4.0.0,<5.0.0",
]
hardware = [
    "pynput>=1.7.8,<1.9.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]
feetech = [
    "feetech-servo-sdk>=1.0.0,<2.0.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]
```

실제 pyproject.toml 신규 작성은 **TODO-D2** 의 책임. 본 절의 extras 정의가 TODO-D2 의 입력 사양.

### 2-4) orin venv 와의 핵심 차이

| 항목 | Orin (.hylion_arm) | DataCollector (.hylion_collector) |
|---|---|---|
| Python | 3.10 (JetPack 제약) | 3.12 (Ubuntu 22.04 시스템 권장) |
| PyTorch 설치 | NVIDIA JP 6.0 redist URL (setup_env.sh 직접 관리) | 표준 PyPI `torch` wheel — setup_env.sh 또는 pyproject.toml 가능 |
| lerobot extras | smolvla + hardware + feetech | record + hardware + feetech (smolvla 제외) |
| 주요 entrypoint | lerobot-calibrate, lerobot-find-cameras, lerobot-find-port, lerobot-record, lerobot-replay, lerobot-setup-motors, lerobot-teleoperate, lerobot-info | lerobot-record, lerobot-teleoperate, lerobot-calibrate, lerobot-setup-motors, lerobot-find-cameras, lerobot-find-port |
| gymnasium | 포함 (core deps) | 제외 검토 가능 (시뮬 불필요) |
| 추론 의존성 | transformers, num2words, accelerate | 제외 |

### 2-5) setup_env.sh 패턴 (orin 미러)

DataCollector 의 `datacollector/scripts/setup_env.sh` 은 orin 의 패턴을 따르되 Jetson 특수 처리를 제거:

```
§0. 시스템 의존 패키지 (libopenblas-dev 등 — x86_64에서도 권장)
§1. venv 생성 (python3.12 -m venv .hylion_collector)
§2. lerobot editable install (-e ".[record,hardware,feetech]")
§3. torch wheel 설치 (표준 PyPI — pip install torch torchvision)
§4. venv activate 스크립트 환경변수 설정 (HF_HOME 등)
§5. 설치 검증 (import torch + import lerobot)
```

Orin 과 달리:
- `§0` 에서 `libcusparseLt` 관련 처리 불필요
- `§3` 에서 NVIDIA redist URL 불필요 — 표준 `pip install torch torchvision` 사용 가능

실제 setup_env.sh 신규 작성은 **TODO-D2** 의 책임.

---

## 3) 디렉터리 구조 (orin/ 형제 패턴)

### 3-1) DataCollector 디렉터리 위치

```
smolVLA/
├── orin/           # 추론 전용 (Jetson Orin)
├── dgx/            # 학습 전용 (DGX Spark)
└── datacollector/  # 데이터 수집 전용 (DataCollector PC) ← 신규
```

`smolVLA/datacollector/` 가 확정 위치. orin·dgx 와 동일 계층 (형제 패턴).

### 3-2) datacollector/ 내부 구조 (목표)

```
datacollector/
├── README.md                       # 디렉터리 책임 + 운영 가이드
├── pyproject.toml                  # 신규 작성 (orin subset — record+hardware+feetech)
├── lerobot/                        # upstream curated subset (record + hardware 책임)
│   └── ...                         # 옵션 B: 파일 변경 X, entrypoint 만 정리
├── scripts/
│   ├── setup_env.sh                # venv 생성 (orin 패턴 미러, Jetson 제약 제거)
│   └── run_teleoperate.sh          # orin/scripts/에서 이관 (TODO-D2 시점)
├── tests/                          # 환경 점검 스크립트 이식 예정 (TODO-G3)
│   └── README.md
├── config/                         # 하드웨어 설정 캐시 (orin/config/ 패턴 미러)
│   ├── README.md
│   ├── ports.json                  # SO-ARM 포트 (시연장 셋업 후 cache)
│   └── cameras.json                # 카메라 인덱스/flip/slot 매핑
└── data/                           # 수집된 dataset (.gitignore)
    └── README.md
```

**런타임 생성 자산 (트리 미포함)**:
- `datacollector/.hylion_collector/` — venv (gitignore)
- `datacollector/data/` — 수집 dataset (gitignore, 수백 MB ~ GB)

### 3-3) 컴포넌트 책임 표

| 컴포넌트 | 책임 | 도입 시점 |
|---|---|---|
| `pyproject.toml` | 의존성 정의 (record + hardware + feetech extras). Orin subset. smolvla·training 제외 | TODO-D2 |
| `lerobot/` | upstream curated subset. record + hardware + teleoperators 책임 외 비활성화. 옵션 B 원칙 (파일 변경 X) | TODO-D2 |
| `scripts/setup_env.sh` | venv 생성 + lerobot editable install + x86_64 표준 torch 설치 + 환경변수 설정 | TODO-D2 |
| `scripts/run_teleoperate.sh` | SO-ARM teleop 실행 (orin/scripts/ 에서 이관) | TODO-D2 (archive 에서 최종 이동) |
| `tests/` | 환경 점검 게이트. orin/tests/check_hardware.sh 의 DataCollector 버전 | TODO-G3 |
| `config/ports.json` | SO-ARM 포트 (lerobot-find-port 결과 캐시) | TODO-G3 first-time 모드 |
| `config/cameras.json` | 카메라 인덱스/flip/slot (lerobot-find-cameras 결과 캐시) | TODO-G3 first-time 모드 |
| `data/` | 수집된 LeRobotDataset (gitignore). lerobot-record 가 자동 생성 | 05 마일스톤 (첫 데이터 수집) |
| `.hylion_collector/` | venv (런타임, gitignore) | TODO-D2 setup_env.sh 실행 후 |

### 3-4) lerobot/ 옵션 B 원칙 적용

DataCollector 의 `datacollector/lerobot/` 도 **orin 과 동일한 옵션 B 원칙**:

- upstream 파일 변경 X
- `pyproject.toml [project.scripts]` entrypoint 등록으로만 활성화 범위 제한
- DataCollector 에서 사용하지 않는 entrypoint (lerobot-eval, lerobot-train) 는 등록 제외

활성화할 entrypoint:
```toml
[project.scripts]
lerobot-record            = "lerobot.scripts.lerobot_record:main"
lerobot-replay            = "lerobot.scripts.lerobot_replay:main"
lerobot-teleoperate       = "lerobot.scripts.lerobot_teleoperate:main"
lerobot-calibrate         = "lerobot.scripts.lerobot_calibrate:main"
lerobot-setup-motors      = "lerobot.scripts.lerobot_setup_motors:main"
lerobot-find-cameras      = "lerobot.scripts.lerobot_find_cameras:main"
lerobot-find-port         = "lerobot.scripts.lerobot_find_port:main"
lerobot-find-joint-limits = "lerobot.scripts.lerobot_find_joint_limits:main"
lerobot-info              = "lerobot.scripts.lerobot_info:main"
```

비활성화 (등록 X):
- `lerobot-eval` — DataCollector 는 추론/평가 X
- `lerobot-train` — 학습은 DGX 책임

### 3-5) coupled file — 05_datacollector_lerobot_diff.md (TODO-D2 신규 의무)

TODO-D2 에서 `datacollector/lerobot/` curated subset 을 구성할 때:
- `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 작성 의무
- orin 의 `03_orin_lerobot_diff.md` 패턴 동일 적용
- entrypoint 비활성화 내역 + 논리적 비활성화 기록

---

## 4) 시연장 인근 배치 시 고려사항

### 4-1) DHCP 변동 리스크

DataCollector 는 시연장 WiFi 에 의존한다. `04_devnetwork.md` §2 에서 이미 Orin·DGX 모두 DHCP 변동 문제를 경험함 (DGX: 2026-04-22 IP 변경 사례).

| 상황 | 증상 | 대처 |
|---|---|---|
| 시연장 WiFi 재연결 | DataCollector IP 변경 → devPC SSH 단절 | DataCollector 에서 `ip addr show` 확인 후 `~/.ssh/config` HostName 업데이트 |
| 평소와 다른 시연장 WiFi | IP 대역 변경 가능 | SSH 접속 전 IP 재확인 필수 (§5 시연 체크리스트 참조) |

**DHCP 예약 권장**: Orin·DGX 와 동일 카테고리 (`04_devnetwork.md §2` BACKLOG 02 #1). 시연장 공유기 접근 가능 시 DataCollector MAC 주소 기반 IP 예약 요청 — 사용자 책임.

> 현재는 IP 직접 기재 방식 (soft 고정 기대) 을 사용. 연결 실패 시 IP 변경 여부 먼저 확인.

### 4-2) 인터넷 격리 vs HF Hub 가용 여부

DataCollector 에서 `lerobot-record --push-to-hub` 로 HF Hub 업로드 시 인터넷 접근 필요.

| 시연장 환경 | HF Hub 업로드 | 대응 |
|---|---|---|
| 인터넷 가용 WiFi | 가능 | `lerobot-record --push-to-hub` 직접 실행 |
| 인터넷 격리 WiFi (학내 방화벽 등) | 불가 | rsync 직접 전송 (TODO-T1 에서 결정된 양방향 지원 활용) |
| 오프라인 | 불가 | 로컬 저장 후 나중에 devPC 경유 업로드 |

**사전 확인 필요**: 시연장 배치 전에 WiFi 에서 `curl https://huggingface.co` 로 HF Hub 접근 가능 여부 테스트 권장.

### 4-3) 전원·배선·물리 보안

- DataCollector PC + SO-ARM 전원 → 시연장 전원 포트 확인 (M1·M2 시연장 미러링 가이드와 연계)
- SO-ARM USB 케이블 길이 및 배선 정리 — 시연 중 케이블 빠짐 방지
- DataCollector PC 물리적 고정 (이동 중 낙하, USB 연결 단락 방지)
- 시연 종료 후 데이터 백업 확인 (HF Hub 또는 rsync 완료 여부)

### 4-4) 시연장 이동 체크리스트

```
[ ] 시연장 WiFi 에 DataCollector 연결 확인
[ ] DataCollector 현재 WiFi IP 확인 (ip addr show)
[ ] devPC ~/.ssh/config datacollector HostName 업데이트
[ ] ssh datacollector 접속 테스트
[ ] lerobot-find-port 로 SO-ARM 포트 재확인 (USB 순서 변동 가능)
[ ] lerobot-find-cameras 로 카메라 인덱스 재확인
[ ] HF Hub 접근 가능 여부 확인 (curl https://huggingface.co)
[ ] (장기) 시연장 공유기 DHCP 예약 요청 (DataCollector MAC 주소)
```

---

## 5) devPC ↔ DataCollector 네트워크 (SSH 설정, ~/.ssh/config)

### 5-1) SSH 설정 (04_devnetwork.md 패턴 미러)

DataCollector SSH 설정은 Orin·DGX 와 동일 패턴. devPC 의 `~/.ssh/config` 에 추가:

```
Host datacollector
    HostName <DataCollector 현재 WiFi IP>   # 실물 확인 후 기재
    User laba                               # 권장 (orin·dgx 통일)
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 5
```

| 항목 | 값 |
|---|---|
| Host alias | `datacollector` |
| HostName | DataCollector WiFi IP (구매·배치 후 확인) |
| User | `laba` (orin·dgx 와 동일 컨벤션 권장) |
| Port | `22` |
| IdentityFile | `~/.ssh/id_ed25519` |
| ServerAliveInterval | `30` (WiFi 환경 idle 세션 끊김 방지) |
| ServerAliveCountMax | `5` |

**초기 SSH 셋업 순서**:
1. devPC 에서 `ssh-copy-id -i ~/.ssh/id_ed25519.pub laba@<DataCollector IP>`
2. `~/.ssh/config` 에 위 항목 추가 후 `ssh datacollector` 접속 테스트
3. VS Code Remote-SSH 로 `datacollector` 선택 → 플랫폼 `Linux` 선택

**SSH 서버 설치 (신규 PC)**:
```
sudo apt-get install -y openssh-server
sudo systemctl enable ssh && sudo systemctl start ssh
```

### 5-2) devPC → DataCollector rsync (deploy 패턴)

`scripts/deploy_datacollector.sh` 신규 스크립트가 TODO-T3 의 책임. 패턴은 기존 `scripts/deploy_orin.sh` 미러:

```bash
# deploy_datacollector.sh (TODO-T3 구현 예정)
rsync -avz --delete \
    --exclude '.hylion_collector' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'data/' \
    smolVLA/datacollector/ \
    datacollector:/home/laba/smolvla/datacollector/
```

### 5-3) DataCollector → DGX 데이터 전송 (TODO-T1 결정 완료)

사용자 답 (2026-05-01): **HF Hub + rsync 직접 둘 다 지원**.

| 전송 방식 | 시나리오 | 구현 |
|---|---|---|
| HF Hub | 인터넷 가용 환경 (일반적) | `lerobot-record --push-to-hub --repo-id=<HF_USER>/...` |
| rsync 직접 | 인터넷 격리 환경 또는 대용량 | `scripts/sync_dataset_collector_to_dgx.sh` (TODO-T1 입력) |

### 5-4) DataCollector → DGX 네트워크 토폴로지

```
DataCollector (시연장)
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

### 5-5) devPC sync hub 전체 구성 (04 완성 시점)

```
devPC scripts/
├── deploy_orin.sh              → rsync orin/* → Orin
├── deploy_dgx.sh               → rsync dgx/ + docs/reference/lerobot/ → DGX
├── deploy_datacollector.sh     → rsync datacollector/* → DataCollector (TODO-T3)
├── sync_ckpt_dgx_to_orin.sh    → DGX outputs/ → Orin checkpoints/ (devPC 경유)
└── sync_dataset_collector_to_dgx.sh  → DataCollector data/ → DGX (TODO-T1, rsync 경우)
```

---

## 6) 향후 작업 (후속 TODO 트리거)

본 문서의 각 절이 다음 TODO 의 입력이 된다:

| TODO | 본 문서 연결 절 | 내용 |
|---|---|---|
| TODO-D2 | §2 (venv·pyproject), §3 (디렉터리 구조) | datacollector/ 실제 셋업 실행: pyproject.toml 신규 작성, setup_env.sh 작성, lerobot curated subset 구성, 05_datacollector_lerobot_diff.md 신규 작성 |
| TODO-G3 | §3-2 (tests/ 구조) | orin/tests/check_hardware.sh DataCollector 버전 이식 |
| TODO-T1 | §5-3 (전송 방식) | HF Hub + rsync 양방향 지원 구현 (사용자 결정 완료 — 둘 다) |
| TODO-T3 | §5-2 (deploy 패턴) | deploy_datacollector.sh 신규 작성 |
| M1 (시연장 미러링) | §4 (시연장 배치) | 시연장 환경 미러링 가이드 작성 (카메라·조명·배치 등) |

**run_teleoperate.sh 최종 이동 (TODO-D2)**:
현재 `docs/storage/others/run_teleoperate.sh.archive` 에 임시 보관. TODO-D2 실행 시점에 `datacollector/scripts/run_teleoperate.sh` 으로 최종 이동.

---

## 7) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 04 TODO-D1 산출물. 사용자 결정 (별도 PC 신규 구매, Ubuntu 22.04 LTS, datacollector/ 디렉터리, pyproject.toml 신규 작성) 반영. §2 venv 설계·extras 분석 (smolvla·training 제외), §3 디렉터리 구조 (orin 형제 패턴), §4 시연장 배치 고려사항, §5 devPC↔DataCollector 네트워크 (SSH/rsync/HF Hub) 정의. TODO-D2 입력 사양 제공. |
