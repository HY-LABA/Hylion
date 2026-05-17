# smolVLA 소프트웨어 현황 (현재 설정/실측)

> 작성일: 2026-04-21  
> 업데이트: 2026-04-27
> 목적: 실제 설정된 소프트웨어 환경 값을 기록

## 1) 기본 개발 환경

- 개발 기준 OS: `Ubuntu 22.04`
- Python 기준: `3.10` (Orin JP 6.2.2 시스템 Python 및 cp310 wheel 요건)
- 사용 의존성 그룹:
  - `smolvla`
  - `training`
  - `feetech`

## 2) Orin 실측 소프트웨어 정보

- 스냅샷 파일: `smolVLA/docs/storage/devices_snapshot/orin_env_snapshot_2026-04-22_0043.txt`
- OS: `Ubuntu 22.04.5 LTS`
- JetPack: `6.2.2` (nvidia-jetpack `6.2.2+b24`, L4T `R36.5.0` 기준)
- L4T: `R36.5.0`
- 커널: `5.15.185-tegra`
- CUDA:
  - `nvcc`: PATH 등록 및 동작 확인 (`Cuda compilation tools, release 12.6, V12.6.68`)
  - cudart: `12.6.68`
- cuDNN: `9.3.0.75-1` (for CUDA 12.6)
- TensorRT: `10.3.0.30-1+cuda12.5`
- GPU 드라이버: `540.5.0`
- nvpmodel 현재 모드: `25W` (mode id `1`)
- ffmpeg: 설치됨 (`4.4.2-0ubuntu0.22.04.1`)

JetPack 판별 근거:
- 장비 식별: `aarch64` + `5.15.185-tegra` 커널로 Jetson Orin 환경 확인.
- 릴리스 식별: `/etc/nv_tegra_release` 실측값이 `R36 (release), REVISION: 5.0`.
- 패키지 식별: `nvidia-l4t-core` 및 다수 `nvidia-l4t-*` 패키지가 `36.5.0`으로 설치됨.
- 해석: L4T `R36.5.0`은 JetPack `6.2.2`와 대응. `apt-cache show nvidia-jetpack` 실측값 `6.2.2+b24`로 확정됨.
- 참고: `nvidia-jetpack` 메타패키지가 `6.2.2+b24`로 설치 확인됨.

## 3) 컨테이너/ML 런타임 상태

- Docker 실행 중 컨테이너: 없음 (스냅샷 시점)
- PyTorch: venv에 설치 (`~/smolvla/orin/.hylion_arm`) — 시스템 패키지 아님 (DGX venv `~/smolvla/dgx/.arm_finetune` 과 격리)
  - 설치 방식 및 패키지 버전 상세: `docs/storage/05_orin_venv_setting.md`

## 4) 노트북 의존성 실측 결과 (기록용)

- 점검일: `2026-04-21`
- 환경명: `lerobot` (conda)
- Python: `3.10.20`
- pip 경로: `/home/babogaeguri/miniconda3/envs/lerobot/lib/python3.10/site-packages/pip`

| 항목 | 설치 여부 | 버전 | 비고 |
|---|---|---|---|
| lerobot | 설치됨 | `0.4.4` | editable project location: `/home/babogaeguri/lerobot` |
| torch | 설치됨 | `2.7.1` |  |
| torchvision | 설치됨 | `0.22.1` |  |
| transformers | 미설치 | - | devPC에서는 설치하지 않음 (실행은 Orin) |
| accelerate | 설치됨 | `1.13.0` |  |
| opencv-python-headless | 설치됨 | `4.12.0.88` |  |
| feetech-servo-sdk | 설치됨 | `1.0.0` |  |

점검 메모:
- 같은 날 `base` 환경(`Python 3.13.12`)에서는 핵심 패키지들이 미설치로 확인됨.
- 실제 텔레옵/실행에 사용된 환경은 `lerobot` conda env로 판단됨.
- 현재 실행 환경 Python은 `3.10.20`으로 문서 기준(`3.10`)과 일치.
- devPC에는 smolVLA/transformers 등을 설치하지 않음 (실행은 Orin에서 수행). devPC는 코드 정리·문서화·배포 관리 전용.

## 5) DGX Spark 실측 소프트웨어 정보

- 스냅샷 파일: `smolVLA/docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt`
- OS: `Ubuntu 24.04.4 LTS`
- 커널: `6.17.0-1014-nvidia`
- CUDA:
  - `nvcc`: PATH 등록 및 동작 확인 (`Cuda compilation tools, release 13.0, V13.0.88`, `/usr/local/cuda/bin/nvcc`)
  - `nvidia-smi` CUDA 표시: `13.0`
  - GPU 드라이버: `580.142`
- cuDNN: 미탐지 (별도 설치 필요)
- TensorRT: 미탐지 (별도 설치 필요)
- PyTorch: 시스템 `python3` 기준 미설치
- Python: `3.12.3`
- pip: `24.0` (`/usr/lib/python3/dist-packages/pip`, Python 3.12)
- venv: 사용 가능
- conda: 미설치
- Docker: 설치됨 (`29.1.3`)
- NVIDIA Container Toolkit: 설치됨 (`1.19.0`)
- ROS2: 미설치
- 특이사항:
  - `ollama.service` 실행 중
  - DGX Spark는 CPU와 integrated Blackwell GPU가 동일 LPDDR5x 풀을 공유하는 UMA 구조. GPU 전용 VRAM으로 기록하지 않음.
  - 공식 메모리 사양은 `128 GB LPDDR5x unified system memory`; Linux 실측은 `121Gi`, 스냅샷 시점 `MemAvailable` 약 `90Gi`, swap `0B`.
  - `nvidia-smi`에서 GPU 메모리 총량은 `[N/A]`, 상세 메모리 사용량은 `Not Supported`로 표시되며 UMA/iGPU 구조의 정상 표시로 취급.
  - GPU 워크로드 가용 메모리 추정은 VRAM 총량이 아니라 OS `MemAvailable + SwapFree` 기준으로 기록.

## 6) DataCollector 실측 소프트웨어 정보 (2026-05-02)

- OS: `Ubuntu 22.04 LTS` (x86_64, kernel `6.8.0-106-generic` HWE)
- Python: `3.10.12` (시스템) — venv 별도 (`.hylion_collector`, 셋업 후 갱신)
- GPU 드라이버: 없음 (Intel HD 620 only — NVIDIA 미탑재)
- CUDA / cuDNN / TensorRT: 미해당 (GPU 없음)
- PyTorch: 셋업 시 표준 PyPI CPU wheel 설치 예정 (`torch` cp310 x86_64 — venv `setup_env.sh`)
- ssh: `openssh-server 1:8.9p1-3ubuntu0.15` 설치·active·enabled (2026-05-02)
- 설치된 핵심 패키지: `git`, `python3`, `build-essential`, `rsync`, `usbutils`, `libusb-1.0-0`
- **셋업 시점 추가 설치 필요**: `python3-venv`, `python3-pip`, `python3-dev`, `curl`, `ffmpeg`, `v4l-utils`
- 사용자 그룹 추가 필요: `dialout` (SO-ARM `/dev/ttyACM*` 접근용)
- conda: 미설치 (시스템 Python + venv 직접 사용)
- Docker: 미확인 (DataCollector 책임상 불필요 — lerobot-record + push 만 수행)
- ROS2: 미설치 (DataCollector 는 lerobot 단독)

<!-- 정정 (2026-05-02): DataCollector 노드 운영 종료 (06_dgx_absorbs_datacollector 결정).
     07_datacollector_venv_setting.md 는 legacy 이관됨.
     참조 경로: docs/storage/legacy/arm_2week_plan/others/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md -->
DataCollector venv 상세는 ~~`docs/storage/07_datacollector_venv_setting.md`~~ → **legacy 이관**: `docs/storage/legacy/arm_2week_plan/others/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md` 참조 (DataCollector 노드 운영 종료 — 06 결정).

## 7) prof_computer 실측 소프트웨어 정보 (2026-05-16 등록, 2026-05-17 본 학습 완주) — DGX 보조 학습 노드

> [02_hardware.md §6](02_hardware.md) 의 소프트웨어 측 대응. [prof_train_setting.md](prof_train_setting.md) §1 옵션 #1 (로컬 GPU PC) 의 구체 구현. 작업 영역: `smolVLA/prof_computer/`. venv·의존성은 `smolVLA/prof_computer/scripts/setup_env.sh` 에서 관리.

### 7-1) 호스트 (Windows) 측

- OS: `Windows 10 Home 22H2` (build `19045.6466`)
- WSL2: `2.7.3.0`, kernel `6.6.114.1-microsoft-standard-WSL2`, WSLg `1.0.73`
- WSL distro: `Ubuntu-22.04` (학습용, §7-2), `docker-desktop` (자체 distro — 학습 무관)
- NVIDIA 드라이버 (Windows): `560.94` (CUDA 13 지원, WSL2 GPU passthrough 노출)
- `.wslconfig` (2026-05-16 작성, `C:\Users\admin\.wslconfig`):
  - `memory=48GB` / `processors=12` / `swap=16GB` / `localhostForwarding=true`
  - 근거: DGX training_log 의 5GB/min 누수 가설 잔존 시 헤드룸 확보. 본 학습 (2026-05-17) 에서 누수 0 확인 — 32GB 영역에서도 충분함 입증
- Python (Windows side): `3.12.x` (`C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe`) — 학습 미사용 (코드 편집·문서 작업용)

### 7-2) WSL Ubuntu 측 (학습 distro)

- OS: `Ubuntu 22.04.5 LTS` (jammy), kernel `6.6.114.1-microsoft-standard-WSL2`
- 사용자: `laba` (uid=1000, `sudo`·`docker` 그룹 소속)
- Python:
  - 시스템 default: `3.10.12` (Ubuntu 22.04 표준) — **lerobot 요구 미달**
  - **학습용**: `3.12.x` (deadsnakes PPA, 시스템 3.10 과 병존) — lerobot 0.5.2 `requires-python = ">=3.12"` (`docs/reference/lerobot/pyproject.toml:32`) 충족용
  - venv: `prof_computer/.venv_arm_finetune` (`python3.12 -m venv` 로 생성)
- GPU 접근: `nvidia-smi` WSL 내 동작 확인 (RTX 3090 24576 MiB, driver 560.94)
- CUDA toolkit (nvcc): **미설치** (학습엔 PyTorch wheel 의 bundled CUDA runtime 사용)
- 설치된 핵심 apt 패키지: `git 2.34.1`, `curl 7.81.0`, `rsync 3.2.7`
- **셋업 시 추가 설치** (`prof_computer/scripts/setup_env.sh` 가 안내):
  - `software-properties-common` (PPA 추가용)
  - deadsnakes PPA → `python3.12`, `python3.12-venv`, `python3.12-dev`
  - `python3-pip`, `build-essential`, `ffmpeg`, `v4l-utils`
- HF Hub / wandb 로그인: `.venv_arm_finetune/.env` 에 `HF_TOKEN` + `WANDB_API_KEY` 저장 → venv activate 시 자동 `set -a` source (`.gitignore` 의 `.env` 패턴으로 git push 차단)

### 7-3) 의존성 트랙 — DGX 와의 정합성

**핵심 원칙**: `smolVLA/docs/reference/lerobot/` 의 editable install — DGX (`dgx/`) 와 동일.

| 항목 | DGX (시연장) | prof_computer (PC) | 비고 |
|---|---|---|---|
| Python | `3.12.3` (시스템 — Ubuntu 24.04) | `3.12.x` (deadsnakes PPA — Ubuntu 22.04) | 메이저.마이너 동일 |
| lerobot | `docs/reference/lerobot/` editable | 동일 | submodule 공유 |
| **PyTorch** | `torch==2.10.0+cu130` (GB10 Blackwell) | **`torch==2.10.0` (cu128 wheel)** | torch 메이저·마이너 동일, CUDA wheel 만 칩 차이. lerobot 공식 `requirements-ubuntu.txt` 가 cu128 영역 lock |
| extras | `[smolvla,training,hardware,feetech]` | `[smolvla,training,peft]` | PC 는 학습 전용 (hardware/feetech 제외), peft 명시 (LoRA fine-tune 필수 — setup 초기 누락으로 본 학습 진입 시 발견) |
| **video backend** | pyav default (torchcodec aarch64 ABI 미스매치) | **torchcodec 0.10.0** ✅ | DGX OOM 사고 직접 원인 vs PC 정상 — prereq spec 02 가설 직접 검증 |
| 데이터셋 캐시 | `~/smolvla/.hf_cache` (DGX 로컬) | `~/.cache/huggingface` (WSL `/dev/sdd` 가상디스크) | 둘 다 HF Hub lazy fetch |
| 학습 산출물 | `~/smolvla/dgx/outputs/<run>/` | `~/prof_computer_runs/<run>/` | wandb run name `_pc_` 접두로 구분 |

### 7-4) 본 학습 검증 (2026-05-17, leftarm_v2 2A)

| 항목 | 값 |
|---|---|
| 도달 step | 75000 / 75000 (5.5 epoch) |
| 학습 시간 | 7시간 34분 |
| step time | 0.343 s/step (DGX 시도 1 의 2.7 s/step 대비 5× 빠름) |
| VRAM peak | 60.67% (~14.7 GB / 24 GB) |
| System RAM 누수 | 0.18 GB/h (DGX 시도 2 의 1.25 GB/min 대비 400× 감소) |
| GPU temp peak | 83°C |
| loss min / final | 0.013 / 0.04 (DGX 시도 1 step 350 loss 0.292 대비 압도적 수렴) |

→ `prereq spec 02_prereq_dataset_video_to_image` 가설 (torchcodec 정상 환경에선 DGX OOM 재현 불가) 직접 증명. 상세: `smolVLA/prof_computer/docs/learning_log.md`.

## 8) 추가 확인 필요 항목

- [x] Orin 시스템 소프트웨어 재검증 완료 (2026-04-23)
  - `nvcc -V` 정상 출력 (`release 12.6, V12.6.68`)
  - `ffmpeg` 설치 완료 (`4.4.2-0ubuntu0.22.04.1`)
- [x] DGX cuDNN / TensorRT 설치 상태 확인 (2026-04-27)
  - `dpkg -l` 기준 cuDNN/TensorRT 모두 미탐지. TODO-06/07/08 진행 전 설치 필요 여부 결정 필요.
- [ ] 학습 PC(DGX)와 Orin 간 모델 반입/실행 절차 확정
- [ ] 외장 SSD 사용 시 데이터셋/체크포인트 경로 확정
