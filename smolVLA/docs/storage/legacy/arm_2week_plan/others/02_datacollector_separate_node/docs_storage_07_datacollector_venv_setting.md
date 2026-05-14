# smolVLA DataCollector 환경 세팅 기록

> 작성일: 2026-05-02
> 목적: smolVLA DataCollector 노드에서 lerobot 을 실행하기 위한 환경 구성 과정과 현재 상태를 기록
> 형제 문서: `05_orin_venv_setting.md` (Orin 추론 환경) / `06_dgx_venv_setting.md` (DGX 학습 환경)
> 설계 근거: 09_datacollector_setup.md §2 (venv·lerobot 의존성 결정) 를 분해·정리한 문서 — 09 파일은 삭제됨, 본 문서가 venv 정보 주소

## 1) 개요

- 실행 대상: DataCollector (`smallgaint`, Intel Core i3-7100U @ 2.40GHz, Ubuntu 22.04 LTS x86_64, **GPU 없음 — Intel HD Graphics 620 only**)
- 환경 관리 방식: venv (`~/smolvla/datacollector/.hylion_collector`, hidden) — Orin venv `~/smolvla/orin/.hylion_arm`, DGX venv `~/smolvla/dgx/.arm_finetune` 와 형제 구조로 격리
- 소프트웨어 실측 현황 근거: 2026-05-02 SSH read-only 검증 (본 문서 §5 참조)
- Python 버전: 시스템 Python 3.10.12 (Ubuntu 22.04 기본) — DGX 의 Python 3.12 와 다른 점 §3 에서 상세 기술

### 디렉터리 형제 구조

```
/home/<user>/smolvla/
├── orin/                        # 추론 (05_orin_venv_setting.md)
│   ├── .hylion_arm/             # venv (hidden, Python 3.10, JP 6.0 wheel, CUDA 12.6)
│   └── ...
├── dgx/                         # 학습 (06_dgx_venv_setting.md)
│   ├── .arm_finetune/           # venv (hidden, Python 3.12.3, torch 2.10.0+cu130)
│   └── ...
└── datacollector/               # 데이터 수집 (본 문서)
    ├── .hylion_collector/       # ← venv (hidden, Python 3.10 시스템, CPU-only torch)
    └── ...
```

venv 네이밍 컨벤션 일람:

| 노드 | venv 이름 | 위치 | Python | GPU |
|---|---|---|---|---|
| Orin | `.hylion_arm` | `~/smolvla/orin/.hylion_arm` | 3.10 (JetPack 제약) | CUDA 12.6 |
| DGX | `.arm_finetune` | `~/smolvla/dgx/.arm_finetune` | 3.12.3 (시스템) | CUDA 13.0 |
| DataCollector | `.hylion_collector` | `~/smolvla/datacollector/.hylion_collector` | 3.10 (시스템) | CPU-only |

이유: 디렉터리 이름이 venv 용도 (수집 전용) 를 즉시 표현. rsync 배포 시 venv 자동 제외 (`--exclude '.hylion_collector'`).

**venv 위치 결정 근거**:
- 04 D1 설계 (구 09_datacollector_setup.md §2-2, 삭제됨) 에서 형제 노드들의 컨벤션을 따라 `.hylion_collector` 로 확정.
- 04 D1 설계 (구 §3-1) 에서 `~/smolvla/datacollector/.hylion_collector` 위치 명시.

**핵심 격리 원칙**:
- DataCollector 단일 책임: SO-ARM teleop + 데이터 수집 전용. 추론 (Orin 책임) · 학습 (DGX 책임) 제외.
- smolvla extras, training extras 는 DataCollector venv 에 설치 X.

---

## 2) venv 환경 구성

### venv 선택 근거 (Orin·DGX 일관성)

DataCollector 는 x86_64 Ubuntu 22.04 환경이므로 Jetson 제약이 없다. venv 를 선택한 이유:

- Orin (`05_orin_venv_setting.md`) / DGX (`06_dgx_venv_setting.md`) 모두 venv 를 사용 — 운영 일관성 (활성화 명령 패턴 동일, hidden 컨벤션 동일)
- conda 는 시스템 미설치, 본 프로젝트 단일 환경에서는 venv 의 디스크/속도 이점이 우세
- NVIDIA 공식 PyTorch 설치 경로가 pip 기반 — venv 와 호환

venv 경로: `~/smolvla/datacollector/.hylion_collector`

Python 버전: `3.10.12` (Ubuntu 22.04 시스템 Python)

설치 스크립트: `~/smolvla/datacollector/scripts/setup_env.sh`

### extras 선택 (orin/pyproject.toml subset)

lerobot upstream `pyproject.toml` 의 optional-dependencies 중 DataCollector 에 필요한 것만 선택. 04 D1 설계 (구 09_datacollector_setup.md §2-3, 삭제됨) 의 결정을 따른다:

| Extra 키 | 필요 여부 | 사유 |
|---|---|---|
| `record` | **필요** | `lerobot-record` 가 LeRobotDataset 포맷 저장 + HF Hub 업로드 + 비디오 인코딩 |
| `hardware` | **필요** | SO-ARM 모터 제어·키보드 입력 |
| `feetech` | **필요** | SO-ARM Feetech 서보 직접 구동 |
| `smolvla` | **제외** | DataCollector 는 추론 X (Orin 의 책임) |
| `training` | **제외** | 학습은 DGX 책임 |
| `viz` | 선택적 | 시각화 필요 시 추가 (기본 미포함) |
| `intelrealsense` | 선택적 | Intel RealSense 카메라 사용 시만 추가 |

### dependency 매트릭스 (datacollector/pyproject.toml 기준, 2026-05-01 작성)

`datacollector/pyproject.toml` 에서 발췌 (orin/pyproject.toml subset, smolvla·training 제외):

```toml
[project]
requires-python = ">=3.10"   # 2026-05-02 갱신: 시스템 Python 3.10.12 정합 (orin/pyproject.toml 일관)

dependencies = [
    "numpy>=2.0.0,<2.3.0",
    "opencv-python-headless>=4.9.0,<4.14.0",
    "Pillow>=10.0.0,<13.0.0",
    "einops>=0.8.0,<0.9.0",
    "draccus==0.10.0",
    "huggingface-hub>=1.0.0,<2.0.0",
    "requests>=2.32.0,<3.0.0",
    "gymnasium>=1.1.1,<2.0.0",
    "safetensors>=0.4.3,<1.0.0",
    ...
]

[project.optional-dependencies]
record = [
    "datasets>=4.0.0,<5.0.0",
    "pandas>=2.0.0,<3.0.0",
    "pyarrow>=21.0.0,<30.0.0",
    "av>=15.0.0,<16.0.0",
    "torchcodec>=0.3.0,<0.11.0; sys_platform == 'linux' and platform_machine == 'x86_64'",
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

`torchcodec` 은 x86_64 Linux 환경에서만 설치되는 조건부 의존성 (`sys_platform == 'linux' and platform_machine == 'x86_64'`). Jetson (aarch64) 에서는 동작하지 않으므로 DataCollector 만의 차별점.

**Orin subset 으로서의 위치**: DataCollector 의 pyproject.toml 은 orin/pyproject.toml 에서 smolvla extras 와 추론 관련 의존성을 제거한 subset. 동일한 `[project.scripts]` 패턴 (9개 entrypoint, lerobot-eval·lerobot-train 제외) 적용.

### 실측 설치 패키지 (2026-05-02 셋업 완료)

| 패키지 | 버전 | 비고 |
|---|---|---|
| lerobot (datacollector/) | `0.5.2` | editable, `[record,hardware,feetech]` extras |
| torch | `2.11.0+cu130` | PyPI default — CUDA 13 wheel 받힘. GPU 없어 `cuda_avail=False` 로 CPU-only 동작. nvidia-* dep 2.7GB dead weight (BACKLOG #10 — CPU index 적용 시 제거) |
| torchvision | `0.26.0+cu130` | torch 동반 |
| datasets | `4.8.5` | record extras |
| scservo-sdk | OK (feetech alias) | feetech-servo-sdk 의 별칭 모듈 — import 검증 통과 |

### 디스크 사용량 (2026-05-02 실측)

| 항목 | 크기 |
|---|---|
| `~/smolvla/datacollector/.hylion_collector` (venv) | **5.3G** |
| 그중 `site-packages/torch/` | 1.2G |
| 그중 `site-packages/nvidia/` (CUDA libs, 사용 안 함) | **2.7G** ← BACKLOG #10 적용 시 제거 |
| `~/.cache/pip` | 2.8G (재실행 시 재사용) |

---

## 3) PyTorch 설치 방식

### GPU 없음 → CPU wheel 선택

DataCollector 는 **Intel HD Graphics 620 만 탑재, NVIDIA GPU 없음**. 따라서:
- CUDA wheel 불필요
- 표준 PyPI CPU-only wheel: `pip install torch torchvision`

이것이 Orin 및 DGX 와의 핵심 차이점이다.

### 노드별 PyTorch 설치 방식 비교

| 항목 | DataCollector | Orin | DGX |
|---|---|---|---|
| GPU | **없음 (CPU-only)** | NVIDIA Jetson (CUDA 12.6) | NVIDIA GB10 (CUDA 13.0) |
| PyTorch 설치 경로 | **표준 PyPI CPU wheel** | NVIDIA JP 6.0 redist URL (`v61/nv24.08`) | NVIDIA 공식 wheel (`cu130`) |
| 설치 명령 | `pip install torch torchvision` | NVIDIA redist URL + `--force-reinstall --no-deps` | `pip install torch==2.10.0+cu130 --index-url https://download.pytorch.org/whl/cu130` |
| Python | **3.10 (시스템)** | 3.10 (JetPack 제약) | 3.12.3 (시스템) |
| CUDA avail | **False** | True (12.6) | True (13.0) |
| LD_LIBRARY_PATH 패치 | **불필요** | cusparselt 처리 필요 (`05_orin_venv_setting.md §3`) | 불필요 |

DataCollector 의 PyTorch 는 **추론·학습에 쓰이지 않는다**. `lerobot-record` 의 데이터셋 처리 (영상 인코딩, tensor 직렬화) 에만 사용된다. 따라서 CPU-only wheel 로 충분.

### 실측 PyTorch 버전 (2026-05-02)

| 항목 | 값 |
|---|---|
| torch 버전 | `2.11.0+cu130` |
| torchvision 버전 | `0.26.0+cu130` |
| `torch.cuda.is_available()` | `False` (GPU 없음 정상) |
| `torch.version.cuda` | `13.0` (wheel 자체는 CUDA 13 build — runtime 미사용) |

PyTorch wheel 자체는 PyPI default 가 CUDA build 라 받혀짐 (~1.2GB) + nvidia-cudnn/cublas/cufft 등 자동 dep (~2.7GB). 단 GPU 없어 사용 안 함 → **dead weight**. BACKLOG #10 (`--index-url https://download.pytorch.org/whl/cpu`) 다음 사이클 적용 시 ~250MB CPU wheel 만 받혀 디스크 ~3.7GB 절약.

---

## 4) setup_env.sh 구성 세팅

`datacollector/scripts/setup_env.sh` 의 구성. Orin 의 `setup_env.sh` 패턴을 따르되 Jetson 특수 처리를 제거한다 (04 D1 설계 기반, 구 09_datacollector_setup.md §2-5 삭제됨).

### 섹션 구성

| 섹션 | 역할 | Orin 대비 차이 |
|---|---|---|
| §0. 시스템 의존 패키지 | `libopenblas-dev`, `libusb-1.0-0-dev`, `python3.12-venv` | cusparseLt 관련 처리 없음 |
| §0-b. lerobot/ symlink | devPC 개발 환경용 upstream src symlink 설정 | 신규 — rsync 배포 후에는 자동 해소 |
| §1. venv 생성 | `python3.12 -m venv .hylion_collector` (python3.12 미탐지 시 python3 폴백) | Python 버전 탐지 로직 상이 |
| §2. lerobot editable install | `pip install -e ".[record,hardware,feetech]"` | extras 집합 상이 (smolvla 제외) |
| §3. PyTorch 설치 | `pip install "torch>=2.0.0" torchvision` (표준 PyPI) | Jetson redist URL 불필요 |
| §4. 환경변수 설정 | `HF_HOME` 를 venv `bin/activate` 에 추가 | `PYTORCH_CUDA_ALLOC_CONF`, `CUDA_VISIBLE_DEVICES` 없음 (GPU 없음) |
| §5. 설치 검증 | lerobot / torch / datasets / feetech-servo-sdk / entrypoints | CUDA 텐서 연산 검증 없음 |

### 환경변수 자동 적용 (venv activate 시)

| 변수 | 값 | 의미 |
|---|---|---|
| `HF_HOME` | `${HOME}/.cache/huggingface` | HF 캐시 위치 (셋업 후 실측값 확인) |

DGX 의 `PYTORCH_CUDA_ALLOC_CONF`, `CUDA_VISIBLE_DEVICES` 는 GPU 없음으로 미설정.

### 셋업 결과 요약 (2026-05-02 완료)

| 항목 | 값 |
|---|---|
| Python 실제 버전 | `3.10.12` (Ubuntu 22.04 시스템) |
| torch / torchvision | `2.11.0+cu130` / `0.26.0+cu130` (CPU-only 동작) |
| lerobot / datasets | `0.5.2` / `4.8.5` |
| feetech / scservo | feetech-servo-sdk → `scservo_sdk` 모듈 import OK |
| entrypoint 9개 | 모두 OK (record·teleoperate·calibrate·find-cameras·find-port·info·setup-motors·replay·find-joint-limits) |
| 셋업 소요 시간 | 약 11~12분 (PyPI 다운로드 ~700MB torch wheel + 2.7GB nvidia deps) |
| 디스크 사용량 | venv 5.3GB / pip cache 2.8GB |

### 시스템 사전 설치 필요 패키지 (DataCollector 실측 2026-05-02 기준)

현재 DataCollector (`smallgaint`) 에 미설치 상태 — `setup_env.sh` 실행 전 사전 설치 필요:

| 패키지 | 상태 | 비고 |
|---|---|---|
| `python3-venv` | **미설치** | venv 생성에 필요 |
| `python3-pip` | **미설치** | pip 사용에 필요 |
| `python3-dev` | **미설치** | 일부 패키지 빌드에 필요 |
| `curl` | **미설치** | 다운로드 시 필요 |
| `ffmpeg` | **미설치** | 비디오 인코딩 (lerobot-record) 에 필요 |
| `v4l-utils` | **미설치** | 카메라 확인 (`lerobot-find-cameras`) 에 필요 |
| `libopenblas-dev` | (미확인) | setup_env.sh §0 에서 자동 설치 |
| `libusb-1.0-0-dev` | 설치됨 (`libusb-1.0-0`) | USB 장치 접근 |
| `rsync` | 설치됨 | deploy_datacollector.sh 에서 사용 |

**dialout 그룹 추가 필요**: 현재 `smallgaint` 유저는 `dialout` 그룹 미포함. SO-ARM USB 직렬 포트 접근을 위해 셋업 전 추가 필요.

---

## 5) 잔여 리스크 / 후속 검증

### 5-1) 셋업 진행 상태 (2026-05-02 갱신)

| 항목 | 상태 | 비고 |
|---|---|---|
| venv 생성 + lerobot 설치 | ✅ 완료 | `~/smolvla/datacollector/.hylion_collector` |
| PyTorch wheel 설치 | ⚠️ 완료 (CUDA 13 wheel 받힘 — CPU 만 사용. BACKLOG #10) | `2.11.0+cu130` (`cuda_avail=False`) |
| dialout 그룹 추가 | ✅ 완료 | `groups=...,20(dialout),...` 새 SSH 세션 적용 확인 |
| python3-venv·pip·dev·curl·ffmpeg·v4l-utils | ✅ 완료 | 트랙 A 에서 일괄 설치 |
| 외부 USB 웹캠 연결 | ❌ 미연결 — 내장 카메라 2대만 (Namuga 720p) | lerobot-record 위해 외부 USB 웹캠 1~2대 (top·wrist) 필요 |
| SO-ARM 임시 연결 | ❌ 미연결 | lerobot-find-port + lerobot-find-cameras 실 검증 필요 |
| `lerobot-find-port` 실 검증 | ❌ 미실행 | SO-ARM 연결 후 |
| `lerobot-find-cameras opencv` 실 검증 | ❌ 미실행 | USB 웹캠 연결 후 |
| `bash datacollector/interactive_cli/main.sh` flow 0~7 완주 | ❌ 미실행 | 위 사전 조건 충족 후 |

### 5-2) Python 버전 — 옵션 B → 옵션 A 재정정 (2026-05-02)

**전말**:
1. 04 D1 의 09_datacollector_setup.md §2-1 (폐기됨) 가 "Python 3.12 권장" 명시
2. 실물 셋업 시 datacollector 머신 = Python 3.10.12 시스템 default (Ubuntu 22.04). 메인이 "옵션 B" 적용 — `requires-python >=3.10` 완화 + setup_env.sh Python 3.10 fallback (auto_grants 항목 8·10·11)
3. setup_env.sh 실행 시 lerobot install 자체는 통과 (datacollector/pyproject.toml 만 체크) 하지만 **lerobot import 시 `SyntaxError`** 발생 — lerobot upstream 5+ 파일 (utils/io_utils.py:93, datasets/streaming_dataset.py:58, processor/pipeline.py:255, motors/motors_bus.py:51,52) 이 PEP 695 generic syntax (`def fn[T: ...]`, `type X = ...`) 사용
4. **옵션 B 가 잘못된 우회로 입증** — pyproject.toml `requires-python` 우회만으론 실제 코드 동작 보장 X. 04 D1 의 "Python 3.12 권장" 가정이 사실 정답
5. 메인이 옵션 A 로 재정정 — pyproject.toml `>=3.12` 복구 + setup_env.sh Python 3.12 강제 + python3.12-venv 의존성 (auto_grants 항목 17)
6. 사용자 직접 deadsnakes PPA 추가 시도 → **학교 WiFi 가 launchpad.net timeout** (ANOMALIES #2·#3) — 본 사이클에선 미해소
7. 사용자 결정: "interactive-cli 작동하는지까지만 05 에서 진행" → 본 사이클은 lerobot import FAIL 상태 그대로 wrap (BACKLOG #11 다음 사이클 처리)

**다음 사이클 진행 후보** (BACKLOG #11):
- (a) 다른 네트워크 (집·핫스팟) 에서 deadsnakes PPA 추가 — 가장 단순
- (b) `uv` standalone Python 3.12 — PyPI·GitHub 만 접근하면 OK (학교 WiFi 통과 가능)
- (c) `datacollector/lerobot/` 옵션 B 직접 작성 — orin/lerobot/ 패턴 미러로 5개 파일 backport (`datasets/streaming_dataset.py` 는 신규 작성 필요). `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 의무. **04 D1 §3-5 미진행 통합 처리 가능** — 단 향후 lerobot upstream 동기화 시 매번 backport burden

**학습 신호 (reflection 분석 대상)**:
- lerobot upstream 가정 (Python 버전·syntax) 은 코드 단위로 사전 grep 검증 필요 — 가정 단순 명시 (09 §2-1 같은) 만으론 부족
- pyproject.toml `requires-python` 완화 ≠ 코드 호환성 보장 (PEP 695 같은 syntax-level 제약은 별도 검증)
- 학교 WiFi 차단 endpoint (launchpad·HF Hub·일부 GitHub repo 등) 사전 정리 → 다른 네트워크 작업 분류

기록: `docs/work_flow/context/auto_grants_05_interactive_cli.md` 항목 8·10·11·17 / `ANOMALIES.md` #2·#3·#4 / `BACKLOG.md` #11·#12·#13.

### 5-3) datacollector/lerobot/ 옵션 B 미진행

04 D1 설계 (구 09_datacollector_setup.md §3-4, 삭제됨) 에서 옵션 B 원칙 명시: `datacollector/lerobot/` 을 구성하고 `05_datacollector_lerobot_diff.md` 를 신규 작성해야 함. 그러나 **04 및 05 사이클 모두 미진행**. 현재 `setup_env.sh` 에 symlink 로 임시 처리되어 있으나, 실물 셋업 전에 datacollector/lerobot/ 의 실제 curated subset 구성이 필요 (향후 별도 todo).

### 5-4) DHCP 변동 리스크

DataCollector 는 시연장 WiFi 에 의존. DHCP 변동 시 devPC `~/.ssh/config` 의 HostName 업데이트 필요 (`04_devnetwork.md §10` 참조).

### 5-5) HF Hub 업로드 가용 여부

시연장 WiFi 에서 인터넷 접근 가능 여부에 따라 `lerobot-record --push-to-hub` 동작 결정. 격리 환경에서는 rsync 직접 전송으로 대체 (`11_demo_site_mirroring.md §6-1` 참조).

---

## 6) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-02 | 초안 작성 — `05_interactive_cli` Phase 3 검증 중 사용자 요청으로 신규 작성. 04 D1 설계 (구 09_datacollector_setup.md §2) venv 결정 + 2026-05-02 SSH read-only 실측값 반영. §3 PyTorch CPU-only 선택 근거 명시 (Orin JP 6.0 wheel / DGX cu130 wheel 과의 차이). 미셋업 항목은 TODO 로 마킹. |
| 2026-05-02 (재정렬) | docs/storage 재정렬에 따라 번호 `15` → `07` 으로 변경. 09_datacollector_setup.md 삭제에 따른 내부 참조 갱신 (09 §X-X → "04 D1 설계 (삭제됨)" + 현행 문서 참조로 교체). |
| 2026-05-02 (셋업 완료) | DataCollector 실 머신 (`smallgaint`) 에 venv 셋업 완료. `requires-python` 옵션 B (`>=3.10` 완화) 적용. setup_env.sh Python 3.12 우선순위 → 3.10 정정. PyTorch CUDA 13 wheel (CPU-only 동작) 설치, nvidia-* dep 2.7GB dead weight 는 BACKLOG #10 다음 사이클 정리. §2·§3·§4·§5-1 실측값 반영. 잔여: USB 웹캠·SO-ARM 연결 후 lerobot-find-port·lerobot-find-cameras 실 검증. |
