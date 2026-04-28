# smolVLA Orin 환경 세팅 기록

> 작성일: 2026-04-21 (최초) / 2026-04-23 (업데이트) / 2026-04-28 (venv 위치·이름 변경 반영)
> 목적: lerobot을 Orin에서 실행하기 위한 환경 구성 과정과 현재 상태를 기록
> DGX 학습 환경 세팅은 별도 문서 `06_dgx_venv_setting.md` (TODO-09b 완료 후 작성 예정)

## 1) 개요

- 실행 대상: Orin (JetPack 6.2.2, L4T R36.5.0, CUDA 12.6)
- 환경 관리 방식: venv (`~/smolvla/orin/.hylion_arm`, hidden) — DGX venv `~/smolvla/dgx/.arm_finetune` 과 형제 구조로 격리
- 소프트웨어 실측 현황 근거: `docs/storage/03_software.md`

### 디렉터리 형제 구조 (2026-04-28 변경)

```
/home/laba/smolvla/
├── orin/                       # 추론 (본 문서)
│   ├── .hylion_arm/            # ← venv (hidden, Python 3.10, JP 6.0 wheel)
│   ├── lerobot/
│   ├── scripts/
│   └── ...
└── dgx/                        # 학습 (06_dgx_venv_setting.md 예정)
    ├── .arm_finetune/          # ← venv (hidden, Python 3.12, torch 2.10.0+cu130)
    └── ...
```

이전 컨벤션 (`~/smolvla/.venv` 단일) 에서 `orin/`·`dgx/` 형제로 분리한 이유:
- DGX 학습 환경 추가로 두 venv 가 같은 머신에 공존 가능 (실제 머신은 다르지만 동일 컨벤션 유지)
- 디렉터리 이름이 venv 용도 (추론 vs 학습) 를 즉시 표현
- rsync 배포 시 venv 자동 제외 (`--exclude '.hylion_arm'` / `--exclude '.arm_finetune'`)

## 2) venv 환경 구성 (2026-04-23 확정)

### venv 선택 근거 (Seeed conda 권장 대비)

Seeed 튜토리얼은 `conda`를 권장하지만 이는 `ffmpeg=7.1.1`, `opencv>=4.10` pip 설치 허들을 낮추기 위한 간편 경로. 우리 환경에서는 venv가 더 적합하다:

- opencv는 PyPI manylinux aarch64 wheel(`opencv-python-headless`)로 해결
- ffmpeg CLI는 JetPack 시스템 패키지로 제공되며, Orin은 추론 전용이라 인코딩/디코딩 불필요
- NVIDIA 공식 PyTorch 설치 경로가 pip 기반 (`python3 -m pip install --no-cache`)
- conda-forge aarch64 채널 커버리지 불완전 + Miniconda 수백MB 공간 비용

conda env 방식은 폐기. `setup_env.sh`가 생성하는 venv를 사용.

- venv 경로: `~/smolvla/orin/.hylion_arm`
- Python 버전: `3.10` (JetPack 6.2.2 시스템 Python)
- 설치 스크립트: `~/smolvla/orin/scripts/setup_env.sh`

**실측 설치 패키지 (2026-04-23 기준):**

| 패키지 | 버전 | 비고 |
|---|---|---|
| lerobot (smolVLA orin/) | editable | `~/smolvla/` — `[smolvla,hardware,feetech]` extras |
| torch | `2.5.0a0+872d972e41` | NVIDIA JP 6.0 nv24.08 wheel, CUDA avail: True (12.6) |
| torchvision | `0.20.0a0+afc54f7` | Seeed SharePoint wheel 수동 설치 완료 (`--no-deps --force-reinstall`), `AutoProcessor.from_pretrained()` 복원 완료 |
| numpy | `<2.0.0` | torch 2.5.0a0 NumPy 1.x ABI 요건으로 고정 |
| transformers | lerobot deps 포함 | smolVLA extras 설치 시 자동 설치 |
| accelerate | lerobot deps 포함 | |
| opencv-python-headless | lerobot deps 포함 | |
| feetech-servo-sdk | lerobot deps 포함 | |

## 3) PyTorch 설치 방식

### JP 6.0 wheel 의도적 선택 근거 (2026-04-23 확정)

**JP 6.2 공식 배포는 컨테이너 전용** (wheel 컬럼 전부 `-`). 그러나 우리 환경은 네이티브 venv + SO-ARM UART hotplug + lerobot editable dev 조합이라 컨테이너 경로를 선택하지 않았다:

1. **L4T mismatch**: JP 6.2 컨테이너(`25.02–25.06`)는 L4T R36.4 기반 → 우리 Orin(L4T R36.5.0)과 minor 차이로 CUDA/cuDNN mismatch 가능
2. **하드웨어 passthrough 복잡도**: `/dev/ttyACM*`(Feetech 서보 2개), `/dev/video*` USB hotplug → `--privileged` 또는 `/dev` bind mount 필요
3. **GPU 스택 추가 설정**: `nvidia-container-toolkit`, 호스트 라이브러리 bind mount 경로 불일치 위험
4. **lerobot editable 충돌**: `pip install -e` editable 설치 + 컨테이너 재시작 루프로 개발 속도 저하
5. **디스크/메모리 비용**: `l4t-pytorch` 이미지 10–20GB, Unified Memory 환경에서 추론 지연 영향
6. **배포 스크립트 충돌**: `scripts/deploy_orin.sh`는 rsync 구조 → 컨테이너 전환 시 이미지 빌드/푸시/풀로 재설계 필요

추가로 **NVIDIA가 2026-03부터 Jetson용 standalone iGPU 컨테이너 생산 중단** 발표. 현 시점에 컨테이너 경로 전환은 수명이 짧은 선택.

→ **JP 6.0 wheel (nv24.08, cu12.6 forward-compatible)을 의도적으로 선택.**

### 배경

- JetPack 6.2부터 NVIDIA 공식 standalone wheel 공급 중단
- `docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md` Compatibility Matrix 확인 결과, JP 6.2 전체 항목의 wheel 컬럼 `-` (공급 없음)

### 시도한 경로와 실패 사유

**1차 시도: Jetson AI Lab PyPI 인덱스 (`pypi.jetson-ai-lab.io/jp6/cu126`)**

NVIDIA 엔지니어(Dusty Franklin)가 관리하는 준공식 인덱스.

| 버전 | 실패 사유 |
|---|---|
| torch 2.11.0+cu130 | CUDA 13.0 빌드 — Orin CUDA 12.6 드라이버와 불일치, `CUDA avail: False` |
| torch 2.8.0 ~ 2.10.0 | `libcudss.so.0` 의존성 — JP 6.2.2에 libcudss 미설치, apt로도 설치 불가 |

**2차 시도: NVIDIA JP 6.1 공식 wheel (`nv24.09`)**

URL 404 — `v61` 디렉토리에는 `nv24.08` wheel만 존재, `nv24.09`는 제공 안 됨.

### 확정 설치 방식: NVIDIA JP 6.0 공식 redist wheel (2026-04-23)

`v61` 디렉토리의 `nv24.08` wheel이 JP 6.2.2에서도 정상 동작.

**wheel 정보:**

| 항목 | 값 |
|---|---|
| torch 버전 | `2.5.0a0+872d972e41` |
| 빌드 태그 | `nv24.08.17622132` |
| Python | cp310 |
| arch | aarch64 |
| CUDA avail | True (12.6) |

**설치 순서 (`setup_env.sh` 기준):**

1. lerobot (orin/) editable 먼저 설치 — pip가 CPU-only torch를 덮어쓰지 못하도록
2. torch wheel 설치 (`--force-reinstall --no-deps`)
3. numpy `<2` 재고정 (`--force-reinstall`)
4. venv activate 스크립트에 LD_LIBRARY_PATH 자동 패치

**LD_LIBRARY_PATH 패치 이유:**

torch 2.5.0a0 pip 설치 시 `nvidia-cusparselt-cu12` 패키지가 함께 설치되는데, `libcusparseLt.so.0`가 시스템 경로에 없음. venv activate 시 아래 경로를 자동 추가:

`{venv}/lib/python3.10/site-packages/nvidia/cusparselt/lib`

**근거 자료:**
- [NVIDIA Developer Forums — Installing Pytorch & Torchvision for JetPack 6.2 and CUDA 12.6](https://forums.developer.nvidia.com/t/installing-pytorch-torchvision-for-jetpack-6-2-and-cuda-12-6/346074)
- [NVIDIA Developer Forums — PyTorch for Jetson (공식 스레드)](https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048)
- `docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md`

---

## 4) setup_env.sh 구성 세팅

### 시스템 의존 패키지

NVIDIA 공식 설치 요건(`Install-PyTorch-Jetson-Platform.md §2`):

```bash
sudo apt-get install -y libopenblas-dev libopenmpi-dev libomp-dev
```

### cusparselt 처리 방식

torch 2.5.0a0 설치 시 `nvidia-cusparselt-cu12` pip 패키지가 함께 들어오는데, `libcusparseLt.so.0`가 시스템 경로에 없으면 CUDA 연산 시점(lazy load)에 로드 실패.

**권장 — Option B (Orin 단일 장비, 재현성 높음):**

1. `https://developer.nvidia.com/cusparselt-downloads` → `Linux / aarch64-jetson / Native / Ubuntu / 22.04 / deb (local)` 선택 후 다운로드
2. `sudo dpkg -i libcusparselt*.deb && sudo ldconfig`
3. 이후 `setup_env.sh` 재실행 시 §0이 이미 설치됨을 감지하고 자동 스킵

**Option A 상태 (2026-04-23):**

CUDA 12.6 환경에서는 `install_cusparselt.sh` 버전 분기(12.1~12.4)와 맞지 않아,
`setup_env.sh`는 Option A 자동 실행을 하지 않고 스킵한다.

**LD_LIBRARY_PATH 패치:**

cusparselt 시스템 설치가 감지되면 패치 불필요. 시스템 미설치 상태인 경우에만 pip 번들 경로(`{venv}/lib/python3.10/site-packages/nvidia/cusparselt/lib`)를 venv activate에 임시 추가하며 경고 메시지 출력.

현재 venv 상태 (2026-04-23):
- LD_LIBRARY_PATH fallback 적용 상태에서 CUDA 텐서 연산 검증 통과
- `ldconfig -p | grep -i cusparseLt` 기준 시스템 등록은 미확인
- Option B(deb 설치)는 보류, 관련 에러 재발 시 재시도

### nvcc PATH

`setup_env.sh §5`에서 `/usr/local/cuda/bin` 디렉토리 존재 시 `~/.bashrc`에 자동 등록:

```bash
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

이미 등록된 경우 스킵. 등록 후 `source ~/.bashrc` 또는 재로그인 필요.

### CUDA 연산 검증

`setup_env.sh §6`에서 단순 `import torch` 대신 실제 CUDA 텐서 연산까지 검증 (`libcusparseLt` lazy load 포함):

```python
a = torch.cuda.FloatTensor(2).zero_()   # cusparselt lazy load 트리거
b = torch.randn(2).cuda()               # CPU → GPU 메모리 전송
c = a + b                               # CUDA 커널 실행
torch.backends.cudnn.version()          # cuDNN 확인
```

검증 실패 시 `sys.exit(1)` + `set -e`로 스크립트 전체 중단.

추가 검증 (2026-04-23):
- `torchvision.ops.nms` CUDA 실행 성공 (`0.20.0a0+afc54f7`)
- `~/smolvla/orin/.hylion_arm/bin/python` 직접 실행으로 venv activate 없이도 CUDA 텐서 연산 성공
