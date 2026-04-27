# smolVLA Orin 환경 개선 TODO

> 작성일: 2026-04-23
> 범위: Orin(JetPack 6.2.2) 상에서 lerobot smolVLA 실행 환경 점검
> 근거: 관련 공식 문서·실측 기록·현재 설치 스크립트 교차 분석

---

## 배경

현재 Orin 환경은 **실행 동작 확인** 상태. 초기에는 "PyTorch 버전이 불필요하게 낮다"고 판단했으나,
NVIDIA 공식 JP 6.2 배포가 **컨테이너 전용**으로 전환된 점과 우리 개발/배포 방식이 겹치면서
**현재의 JP 6.0 wheel 이식 전략이 오히려 합리적**이라는 재평가가 나옴. 아래 §1 참고.

---

## 1. PyTorch 버전 경로 재평가 — 현재 유지로 확정 권장

### 현재 상태

- 설치된 wheel: `torch 2.5.0a0+872d972e41.nv24.08` (JP 6.0용)
- 설치 경로: `developer.download.nvidia.com/compute/redist/jp/v61/pytorch/`
- 근거: [orin/scripts/setup_env.sh:58](orin/scripts/setup_env.sh#L58),
  [docs/storage/05_orin_venv_setting.md:55-67](docs/storage/05_orin_venv_setting.md#L55-L67)

### NVIDIA 공식 호환 매트릭스

[docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md:38-66](docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md#L38-L66)

| PyTorch | **Container** | **Wheel** | JetPack |
|---|---|---|---|
| 2.8.0a0 | **25.06 / 25.05** ✅ | **— (공급 안 함)** | 6.2 |
| 2.7.0a0 | **25.02–25.04** ✅ | **— (공급 안 함)** | 6.2 |
| 2.5.0a0+b465a5843b | 24.09 | **24.09** ✅ | 6.1 |
| **2.5.0a0+872d972e41** | 24.08 | **— (공급 안 함)** | **6.0** ← 현재 이식 사용 중 |
| 2.4.0a0 | 24.05–24.07 | **24.05–24.07** ✅ | 6.0 |

**JP 6.2 행은 Wheel 컬럼이 전부 `-`, Container 컬럼만 채워짐 = NVIDIA의 JP 6.2 공식 배포 = Docker 컨테이너.**

### 왜 컨테이너 경로를 선택하지 않는가 — 6가지 복잡도

우리 개발 환경은 네이티브 venv + lerobot editable + SO-ARM UART + USB 카메라 조합이며,
컨테이너로 전환하면 아래 문제가 한꺼번에 발생함.

1. **L4T 버전 mismatch**
   - JP 6.2 PyTorch 컨테이너(`25.02`–`25.06`)는 **L4T R36.4 기반** 빌드
   - 우리 Orin은 **L4T R36.5.0 / JetPack 6.2.2** ([docs/storage/03_software.md:21](docs/storage/03_software.md#L21))
   - 드라이버 minor 차이로 CUDA/cuDNN/TensorRT mismatch 경고 및 일부 기능 오동작 가능

2. **하드웨어 통과(passthrough) 복잡도**
   - SO-ARM 제어를 위해 컨테이너에서 호스트 장치 접근 필요:
     - `/dev/ttyACM*` (Feetech 서보 USB 시리얼 2개: 리더·팔로워)
     - `/dev/video*` (카메라)
     - `/dev/bus/usb/*` (RealSense/Orbbec 사용 시)
   - `--device=` 단순 나열로는 USB hotplug 대응 불가 → `--privileged` 또는 `/dev` 바인드
     마운트 필요. udev 이벤트 전파·보안 면에서 venv보다 훨씬 번거로움

3. **GPU/그래픽 스택 추가 설정**
   - `nvidia-container-toolkit` 또는 `--runtime nvidia` 설정
   - Jetson 컨테이너는 `/etc/nvidia-container-runtime/host-files-for-container.d/`의
     CSV 목록을 통해 호스트 라이브러리를 바인드 마운트 — JP 6.2.2 경로와 컨테이너 base의
     `/usr/lib/aarch64-linux-gnu` 기대 경로가 다르면 `libnvinfer.so.x` 로드 실패

4. **lerobot editable 설치와의 충돌**
   - 현재 `pip install -e ${SMOLVLA_DIR}[smolvla,hardware,feetech]` ([orin/scripts/setup_env.sh:49](orin/scripts/setup_env.sh#L49))로
     호스트 `~/smolvla/`를 editable 참조
   - 컨테이너 전환 시 소스 디렉토리 bind mount, 컨테이너 내부 Python path 동기화, editable
     재설치 필요 → 코드 수정/컨테이너 재시작 루프로 개발 속도 저하

5. **디스크/메모리 비용**
   - `l4t-pytorch` 이미지는 **10–20GB** 수준
   - Orin NVMe는 256GB급 ([docs/storage/02_hardware.md:37](docs/storage/02_hardware.md#L37)) —
     SmolVLM 체크포인트·데이터셋과 경쟁
   - Unified Memory 환경에서 컨테이너 오버헤드가 추론 지연에 직접 영향

6. **배포 스크립트와의 충돌**
   - `deploy_orin.sh`는 호스트 파일시스템(`~/smolvla/`) 대상 rsync 구조 ([README.md:85-90](README.md#L85-L90))
   - 컨테이너 전환 시 배포 방식을 이미지 빌드/푸시/풀로 재설계 필요

### NVIDIA의 결정적 경고

[Release Notes L30](docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md#L30):
> **26.03 release (Note)**: NVIDIA will **no longer produce** the standalone iGPU containers starting from this release.

NVIDIA 자체도 **2026-03부터 Jetson용 standalone iGPU 컨테이너 생산 중단**. 지금 시점에
컨테이너 기반으로 전환하는 것은 **수명이 짧은 선택**.

### 선택지 전체 비교

| 경로 | PyTorch | 배포 방식 | 우리 환경 적합성 |
|---|---|---|---|
| NVIDIA 공식 JP 6.2 | 2.7 / 2.8 | **컨테이너 only** | ❌ SO-ARM hotplug·editable dev·rsync 배포와 충돌, 2026-03 생산 중단 |
| NVIDIA JP 6.1 nv24.09 | 2.5.0a0+b465a5843b | wheel | ❌ 시도: nv24.09 URL **404** — `v61` 디렉토리에 nv24.08만 실제 존재, nv24.09 미배포 |
| **NVIDIA JP 6.0 nv24.08 (현재)** | **2.5.0a0+872d972e41** | **wheel** | ✅ **동작 검증 완료** |
| **Seeed SharePoint JP 6.1 & 6.2 (L4T R36.4)** | **2.7 / 2.5** (JP 6.2 재빌드) | **wheel** | 🔍 **미시도** — 같은 2.5라도 JP 6.2용 빌드면 cusparselt 이슈 해소 가능성. [Seeed 가이드](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L50-L63) L50-63 공식 제시 |
| Jetson AI Lab `jp6/cu126` | 2.8–2.11 | wheel | ❌ libcudss/libcusparseLt 결손 ([docs/storage/05_orin_venv_setting.md:46-49](docs/storage/05_orin_venv_setting.md#L46-L49)) |
| 소스 컴파일 | 2.7 / 2.8 | 자체 빌드 wheel | ⚠️ 6–12시간 빌드, 유지보수 부담, smolVLA가 2.7+ 전용 기능 필요할 때만 정당화 |

### 결론 및 할 일

**현재 JP 6.0 wheel 경로를 의도적 선택으로 확정.** 단, 선택 근거를 문서에 남겨야 함.

- [x] [orin/scripts/setup_env.sh](orin/scripts/setup_env.sh) 헤더 주석 정정 (2026-04-23)
  - "JP 6.2 공식 배포는 컨테이너 전용. 네이티브 venv + SO-ARM UART hotplug + lerobot editable dev 조합과 맞지 않아 JP 6.0 wheel을 의도적으로 선택."
- [x] [docs/storage/05_orin_venv_setting.md](docs/storage/05_orin_venv_setting.md)에 JP 6.0 선택 근거 6가지 + NVIDIA 컨테이너 단종 추가 (2026-04-23)
- [x] smolVLA PyTorch 2.7+ 전용 기능 의존 여부 확인 (2026-04-23) — **의존 없음**
  - `torch.compile`: `compile_model=False` 기본값으로 비활성. 활성화해도 2.5에서 동작
  - FlashAttention, `torch._dynamo`, `torch.export` 등 2.7 전용 API 미사용 확인
  - → PyTorch 버전 업그레이드는 선택적 개선, 강제 요건 아님

- [x] **Seeed SharePoint 재빌드 wheel 가치 평가 — 결론 도출 (2026-04-23)**

  | 경로 | cusparselt | 교체 가치 |
  |---|---|---|
  | Seeed JP 6.2 PyTorch **2.5** | **이슈 있음** (가이드 L58 명시 — deb 설치 필요) | ❌ 현재와 동일 문제, 교체 의미 없음 |
  | Seeed JP 6.2 PyTorch **2.7** | 가이드에 언급 없음 → 해소됐을 가능성 | 🔍 Orin 실제 테스트 필요 |

  - **JP 6.2 Python 2.5 wheel 교체: 불필요** — 동일한 cusparselt 이슈, cusparselt deb 설치 필요
  - **JP 6.2 PyTorch 2.7 wheel 시도: Orin에서 직접 테스트 필요** — smolVLA 코드 변경 없이 적용 가능
  - 결정 기준: Orin에서 `torch.cuda.FloatTensor(2).zero_()` 통과 여부 확인 후 결정

---

## 2. 설치 방식이 NVIDIA 공식 문서와 다름

### 공식 설치 절차

**NVIDIA 공식 문서**
[docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform.md:76-107](docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform.md#L76-L107)

1. `sudo apt-get install libopenblas-dev` (현재 스크립트엔 없음)
2. 24.06 이상 wheel 설치 시 **cusparselt를 시스템에 먼저 설치** (옵션 A — 스크립트):
   ```bash
   wget raw.githubusercontent.com/pytorch/pytorch/.../install_cusparselt.sh
   export CUDA_VERSION=12.6
   bash ./install_cusparselt.sh
   ```
3. `numpy==1.26.x` 고정 후 torch 설치

**Seeed 가이드 권장** (옵션 B — NVIDIA deb local 패키지)

[Seeed 가이드 L58](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L58)은 `ImportError: libcusparseLt.so.0` 발생 시 다음을 설치하라고 제시:

- **cuSPARSELt 0.8.1 (aarch64-jetson / Ubuntu 22.04 / deb Local)**: https://developer.nvidia.com/cusparselt-downloads
- **CUDA 12.6 deb local (aarch64-jetson / Ubuntu 22.04)**: https://developer.nvidia.com/cuda-12-6-0-download-archive

**두 옵션 비교:**

| 옵션 | 장점 | 단점 |
|---|---|---|
| A. `install_cusparselt.sh` | 자동화, `setup_env.sh`에 통합 용이 | 스크립트 URL이 PyTorch repo commit에 고정됨 |
| B. NVIDIA deb local | **공식 배포 경로, 재현성 높음, apt 관리** | 사전 다운로드 필요 |

→ **Orin 단일 장비에선 옵션 B(deb) 권장**. 이미지 자동화/CI에선 옵션 A.

### 현재 setup_env.sh 상태 (2026-04-23 최종)

- ✅ `libopenblas-dev`, `libopenmpi-dev`, `libomp-dev` §0에 추가 (Orin 실행 확인)
- ✅ cusparselt: Option A (CUDA 12.6 미지원 확인) 스킵 + LD_LIBRARY_PATH fallback 적용
- ✅ LD_LIBRARY_PATH 패치 → **사실상 유일한 해결책** (pip `nvidia-cusparselt-cu12` 경로를 venv activate에 등록)
- ✅ numpy `<2` 고정
- ✅ nvcc PATH ~/.bashrc 등록 §5에 추가
- ✅ CUDA 텐서 연산 검증 블록 §6에 추가
- ✅ torchvision §3-b 수동 wheel 안내 블록으로 단순화

### 우회 방식(LD_LIBRARY_PATH)의 리스크

- venv 바깥의 터미널/프로세스에서 실행 시 `libcusparseLt.so.0 not found`
- `nvidia-cusparselt-cu12` pip 패키지 메이저 버전 변경 시 경로 깨짐
- systemd 서비스·외부 launcher에서 라이브러리 로드 실패 가능

### 할 일

- [x] `libopenblas-dev`, `libopenmpi-dev`, `libomp-dev` setup_env.sh §0에 추가 (2026-04-23)
- [x] cusparselt 처리 방식 확정 (2026-04-23)
  - Option A (`install_cusparselt.sh`) **CUDA 12.6 미지원** — 스크립트 버전 분기가 12.1~12.4만 처리
  - setup_env.sh: Option A 시도 제거, 안내 메시지 + LD_LIBRARY_PATH fallback으로 변경
  - **Option B (NVIDIA deb local)만 실질적 해결책** — Orin에서 수동 설치 필요
    - `https://developer.nvidia.com/cusparselt-downloads` → aarch64-jetson / Ubuntu 22.04 / deb local
    - `sudo dpkg -i libcusparselt*.deb && sudo ldconfig`
- [ ] **Orin에서** Option B (NVIDIA deb local) 수동 설치 후 `setup_env.sh` 재실행 ← **보류 (문제 발생 시 재시도)**
- [x] 검증: venv activate 없이 `python -c "import torch; torch.cuda.FloatTensor(2).zero_()"` 성공 확인 (2026-04-23)

---

## 3. torchvision을 완전히 포기하지 않아도 됐음

### 현재 판단

[docs/storage/05_orin_venv_setting.md:26](docs/storage/05_orin_venv_setting.md#L26)

> `torchvision: 미설치 — Orin 호환 버전 없음 (smolVLA 추론 경로에서 미사용)`

### 반박 근거

- **Seeed / NVIDIA 양쪽 모두 torchvision wheel을 제공**
  - JP 6.1 & 6.2: torchvision **0.22.0** (Seeed SharePoint)
  - JP 6.0: torchvision **0.20** (Seeed SharePoint, 필요 시 소스 빌드)
  - 근거: [docs/reference/seeedwiki/seeedwiki_so101.md:54](docs/reference/seeedwiki/seeedwiki_so101.md#L54),
    [docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md:50-62](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L50-L62)
- 즉 **"Orin 호환 없음"이 아니라 "우리가 설치를 안 함"**이 정확.

### 실제 코드에서의 torchvision 사용처

| 파일 | 용도 | smolVLA 추론 영향 |
|---|---|---|
| [orin/lerobot/policies/smolvla/smolvlm_with_expert.py](orin/lerobot/policies/smolvla/smolvlm_with_expert.py) | SmolVLM `AutoProcessor`의 video processor가 torchvision 요구 | **있음 (AutoProcessor 복원 완료)** |
| [orin/lerobot/processor/hil_processor.py:25](orin/lerobot/processor/hil_processor.py#L25) | `torchvision.transforms.functional` 직접 import | HIL 학습 경로, 추론엔 미사용 |
| [orin/lerobot/scripts/lerobot_imgtransform_viz.py](orin/lerobot/scripts/lerobot_imgtransform_viz.py) | 데이터 증강 시각화 | 추론엔 미사용 |

### torchvision 설치 시 효과

1. SmolVLM 공식 `AutoProcessor`를 그대로 사용 가능 → `_TokenizerOnlyProcessor` 우회 클래스 제거
2. Seeed 튜토리얼의 데이터 기록/시각화 명령(`lerobot-record`, `lerobot-dataset-viz`) Orin에서 직접 동작
3. `hil_processor` 경로가 필요해져도 import 에러 없음
4. upstream lerobot과의 diff 감소 → 유지보수 부담 ↓

### 결정 (2026-04-23 확정)

- **PyTorch 2.5 유지** (NVIDIA 공식 wheel)
- torchvision 설치 여부: **§A-4 Seeed 포크 확인 후 결정**
  - Seeed 포크가 torchvision 의존성을 이미 처리했으면 → 포크 교체와 함께 torchvision 설치 방향 재검토
  - Seeed 포크가 해결 안 했거나 upstream 유지 결정이면 → **torchvision 0.20** (Seeed SharePoint, PyTorch 2.5 대응) 설치
  - 추후 필요 시: PyTorch 2.7 + torchvision 0.22로 업그레이드 가능

### 할 일

- [x] PyTorch 버전 확정: **2.5 유지** (2026-04-23)
- [x] §A-4 Seeed 포크 조사 완료 → torchvision **0.20** 설치 확정 (Seeed 포크도 torchvision 필요) (2026-04-23)
- [x] Seeed SharePoint에서 torchvision 0.20 wheel 다운로드 완료 (2026-04-23)
  - 경로: [docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl](docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl)
  - 파일명 검증: `cp310` + `aarch64` + PyTorch 2.5 대응 0.20.0a0 ✅
- [x] **Orin에 wheel 1회 수동 설치** (2026-04-23 완료)
  - `.venv`에 한 번 설치되면 영구 유지 — `deploy_orin.sh`가 `.venv`를 건드리지 않으므로
    재배포해도 재설치 불필요. wheel을 `deploy_orin.sh` rsync 범위에 넣지 않는다.
  - devPC에서:
    ```bash
    scp smolVLA/docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl orin:~/
    ```
  - Orin에서:
    ```bash
    source ~/smolvla/.venv/bin/activate
    pip install ~/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl --no-deps --force-reinstall
    ```
- [x] 설치 검증 (2026-04-23 완료):
  ```bash
  python -c "import torch, torchvision, torchvision.ops; from torchvision.transforms.v2 import functional; boxes=torch.tensor([[0.0,0.0,10.0,10.0]]).cuda(); scores=torch.tensor([0.9]).cuda(); print(torchvision.__version__, torchvision.ops.nms(boxes, scores, 0.5))"
  ```
  - 결과: `0.20.0a0+afc54f7 tensor([0], device='cuda:0')`
- [x] **setup_env.sh §3-b 정리** — PyPI 0.20.0 시도 블록 제거, 수동 wheel 안내로 단순화 (2026-04-23)
  ```bash
  # § 3-b. torchvision (Jetson aarch64 + CUDA 12.6 + PyTorch 2.5 대응 사전빌드 wheel)
  # PyPI 제공 wheel은 CUDA 빌드 아님 → ABI 불일치. 수동 1회 설치 필요.
  # wheel 경로: docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl
  if ! python -c "import torchvision" 2>/dev/null; then
      echo "[setup] torchvision 미설치 — 수동 1회 설치 필요"
      echo "         devPC:  scp smolVLA/docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl orin:~/"
      echo "         Orin:   pip install ~/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl --no-deps"
  else
      echo "[setup] torchvision 설치 확인: $(python -c 'import torchvision; print(torchvision.__version__)')"
  fi
  ```
- [x] 설치 후 `_TokenizerOnlyProcessor` 제거, `AutoProcessor.from_pretrained()` 복원 (2026-04-23)
  - [smolvlm_with_expert.py:41-51](orin/lerobot/policies/smolvla/smolvlm_with_expert.py#L41-L51) `_TokenizerOnlyProcessor` 클래스 전체 제거
  - [smolvlm_with_expert.py:114](orin/lerobot/policies/smolvla/smolvlm_with_expert.py#L114) `= _TokenizerOnlyProcessor(model_id)` → `= AutoProcessor.from_pretrained(model_id)`
- [x] 제거 후 [docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md](docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md) 변경 이력 추가 (2026-04-23)

---

## 4. 기타 정리 항목

### 4-1. nvcc PATH 미등록

- 근거: [docs/storage/03_software.md:23](docs/storage/03_software.md#L23)
  > `nvcc: PATH에 미탐지 (패키지로 설치됨, SDK 12.6.11)`
- Seeed 가이드 검증 절차 [3.5-Pytorch/README.md:34](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L34)의
  `nvcc -V` 명령이 그대로 통과되지 않음
- 할 일:
  - [x] `/usr/local/cuda/bin` + `/usr/local/cuda/lib64` → setup_env.sh §5에서 `~/.bashrc` 자동 등록 (2026-04-23)
  - [x] Orin에서 `nvcc -V` 동작 확인 (2026-04-23)

---

## 5. 설치 검증 스크립트 강화

### 현재 검증 수준

[orin/scripts/setup_env.sh:78-82](orin/scripts/setup_env.sh#L78-L82):

```bash
python -c "import torch; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available())"
```

### 문제점

- `torch.__version__`과 `torch.cuda.is_available()`은 **GPU 연산 능력을 보장하지 않음**
- `libcusparseLt.so.0`는 **lazy load** — 실제 tensor 연산 시점에야 로드됨
- 현재 검증은 통과하고 smolVLA 실행 시 `libcusparseLt not found` 가 터지는 시나리오 가능

### Seeed 가이드의 검증 절차

[3.5-Pytorch/README.md:107-120](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L107-L120):

```python
import torch
print(torch.__version__)
print('CUDA available: ' + str(torch.cuda.is_available()))
print('cuDNN version: ' + str(torch.backends.cudnn.version()))
a = torch.cuda.FloatTensor(2).zero_()      # 실제 cuda 텐서 할당
print('Tensor a = ' + str(a))
b = torch.randn(2).cuda()                  # CPU→GPU 복사
print('Tensor b = ' + str(b))
c = a + b                                  # cuda 연산
print('Tensor c = ' + str(c))
```

**할당 + 복사 + 연산** 3단계를 모두 실행해야 cusparselt·cuDNN 로드까지 검증됨.

### 할 일

- [x] `setup_env.sh` §6에 CUDA 텐서 연산 검증 블록 추가 (2026-04-23)
  - `FloatTensor(2).zero_()`, `randn(2).cuda()`, `a + b`, `cudnn.version()` 포함
  - `set -e` + `sys.exit(1)` 으로 실패 시 스크립트 중단
- [x] Orin에서 실제 실행하여 검증 통과 확인 (2026-04-23)

---

## 잘 된 부분 (변경 불필요)

- Python 3.10 (cp310 wheel에 정확히 일치)
- numpy `<2.0.0` 고정 (torch 2.5.0a0 NumPy 1.x ABI 요건)
- venv 구조 (conda env 폐기 결정 타당)
- [orin/pyproject.toml](orin/pyproject.toml)에서 torch/torchvision을 의존성에서 빼고
  setup_env.sh에서 직접 설치 (pip CPU-only wheel 덮어쓰기 방지)
- `-e [smolvla,hardware,feetech]` extras 구성

---

## 우선순위 요약

| # | 조치 | 대응 § | 상태 | 위험도 |
|---|---|---|---|---|
| 1 | setup_env.sh 주석 정정 + 05_orin_venv_setting.md JP 6.0 선택 근거 기록 | §1 | ✅ 완료 (2026-04-23) | — |
| 2 | apt 시스템 패키지 + cusparselt Option A 자동화 + LD 패치 조건화 | §2 | ✅ 스크립트 완료 / Option B는 보류(문제 발생 시 재시도) | — |
| 3 | nvcc PATH ~/.bashrc 자동 등록 | §4-1 | ✅ 등록 + `nvcc -V` 확인 완료 (2026-04-23) | — |
| 4 | 검증 스크립트 강화 (실제 CUDA 텐서 연산) | §5 | ✅ 스크립트 + Orin 실검증 완료 (2026-04-23) | — |
| 5 | Seeed JP 6.2 2.5 wheel → ❌ 동일 cusparselt 이슈 / **2.7 wheel → Orin 테스트** | §1 | ✅ 분석 완료 / Orin 테스트 대기 | 낮음 |
| 6 | Seeed 포크 조사 → upstream 유지 결정 + torchvision 0.20 설치 확정 | §A-4 | ✅ 완료 (2026-04-23) | — |
| 7 | torchvision **0.20** 설치 (Seeed SharePoint) → `_TokenizerOnlyProcessor` 제거 | §3 | ✅ 설치/검증/코드복원 완료 (2026-04-23) | 낮음 |

---

## 현재 상태 및 다음 단계 (2026-04-23 기준)

**완료 (결정 + 스크립트 레벨):**
- setup_env.sh: 시스템 패키지 / cusparselt Option A / nvcc PATH / CUDA 텐서 검증 블록 추가
- 05_orin_venv_setting.md: JP 6.0 선택 근거 / venv 근거 / torchvision 업그레이드 경로 명시
- PyTorch 2.5 유지 확정 + torchvision 0.20 설치 방향 결정
- JP 6.1 nv24.09 URL 404 사실 기록

**Orin 접속 후 수행:**
- [x] `setup_env.sh` 재실행 → CUDA 텐서 검증 통과 확인 (2026-04-23)
- [x] `nvcc -V` 동작 확인 (2026-04-23)
- [ ] (권장) Option B: NVIDIA cuSPARSELt deb 수동 설치 → LD_LIBRARY_PATH 패치 완전 제거 (**보류: 문제 발생 시 재시도**)
- [x] Seeed SharePoint에서 torchvision **0.20** wheel 브라우저 다운로드 → `pip install`
- [x] `_TokenizerOnlyProcessor` 제거 → `AutoProcessor.from_pretrained()` 복원 → 동작 확인
- [x] `ffmpeg -version` 확인 (2026-04-23) → 미설치 확인 (`command not found`)
- [x] `ffmpeg` 설치 (`sudo apt install -y ffmpeg`) (2026-04-23)
- [ ] (선택) Seeed JP 6.2 PyTorch 2.7 wheel 별도 test venv 설치 → cusparselt 해소 여부 확인

**조사 완료:**
- [x] Seeed 포크 조사 → upstream 유지 결정, torchvision 0.20 설치 확정 (2026-04-23)
- [x] [docs/storage/lerobot_upstream_check/01_compatibility_check.md](docs/storage/lerobot_upstream_check/01_compatibility_check.md) 에 결과 기록 (2026-04-23)

---

## 부록 A. 자주 올라온 설계 질문과 답변 (2026-04-23)

세 가지 환경 선택에 대한 검증. 각 항목은 **결정 + 근거 + 조치** 구조.

### A-1. PyTorch 버전을 올려도 Python 3.10 고정인가?

**답: 그렇다. 그리고 Python 3.10 고정의 근본 원인은 "Jetson용 PyTorch wheel이 cp310만 제공"하기 때문.**

인과 사슬:

```
JetPack 6.x 선택 (Orin 현 시점 안정 버전)
    ↓ Ubuntu 22.04 base
시스템 Python 3.10 고정
    ↓
NVIDIA / Seeed / Jetson AI Lab 모든 aarch64 wheel이 cp310만 제공
    ↓  (파일명의 "-cp310-cp310-" 고정)
Orin에서 Python 3.11/3.12 선택지 자체가 존재하지 않음
    ↓
upstream lerobot (Python 3.12+ 요구)의 3.12 전용 문법이 SyntaxError
    ↓
Python 3.12 문법 3곳 패치가 영구적으로 필요
  (io_utils.py / motors_bus.py / factory+pretrained.py)
```

**즉 lerobot 수정 부담의 진짜 출발점은 "JetPack 6.x → cp310 wheel 제약" 이며,
PyTorch 버전(2.5 → 2.7/2.8)을 올려도 이 사슬은 풀리지 않는다.**

근거:

1. **JetPack 6.x 시스템 Python이 3.10**
   - Ubuntu 22.04 기반 → 기본 파이썬 3.10
   - [orin/scripts/setup_env.sh:17-22](orin/scripts/setup_env.sh#L17-L22) — venv 생성 시
     `python3.10` 우선 선택

2. **NVIDIA 공식 JP 6.x용 PyTorch wheel은 전부 `cp310`만 제공**
   - 현재 wheel 파일명: `torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl`
   - JP 6.0 / 6.1 / 6.2 대응 wheel 모두 cp310 (파일명의 `cp310-cp310` 부분)
   - Seeed 가이드 [3.5-Pytorch/README.md:69-70](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L69-L70)도
     `torch-2.3.0-cp310-cp310-linux_aarch64.whl` 명시

3. **PyTorch 버전을 올려도 JP 6.x + cp310 조합은 유지**
   - JP 6.2 컨테이너 경로(2.7/2.8) — 컨테이너 내부 Python도 3.10
   - Python 3.11/3.12로 가려면 **JetPack 7.x로 OS 전체 재설치** 필요
     (JP 7.x는 L4T R38 기반 — 하드웨어 지원 매트릭스 상이)

4. **Seeed 튜토리얼도 Python 3.10 명시**
   - [so101.md:72](docs/reference/seeedwiki/seeedwiki_so101.md#L72) — `conda create -y -n lerobot python=3.10`
   - [so101.md:66-67](docs/reference/seeedwiki/seeedwiki_so101.md#L66-L67) — "Jetson Orin: Python 3.10"

결론:
- ✅ Python 3.10 사용은 **Jetson aarch64 PyTorch wheel이 cp310만 제공**해서 발생하는 제약
- PyTorch 버전(2.5 ↔ 2.7/2.8)과 Python 버전(3.10 고정)은 **독립적인 두 축이지만,
  Python 축은 JetPack 6.x 안에서는 변경 불가**
- Python 3.12 전용 문법 패치(3곳)는 **JetPack 6.x를 쓰는 한 영구적 비용**
- 이 비용을 없애는 유일한 길 = **JetPack 7.x 전환** (lerobot 호환성 미검증으로 현 시점 보류)

조치:
- [x] 현재 Python 3.10 유지. 추가 작업 없음

---

### A-2. 학습을 DGX에서 한다면 Orin에 torchvision이 정말 필요 없는가?

**답: torchvision은 추론 경로에서도 필요하며, 현재는 Orin에 torchvision 0.20 설치 후
`AutoProcessor` 경로를 복원한 상태다.**

Orin 내 torchvision 사용처 (실측):

| 파일 | 경로 | 추론 필수? | 현재 처리 |
|---|---|---|---|
| [orin/lerobot/policies/smolvla/smolvlm_with_expert.py](orin/lerobot/policies/smolvla/smolvlm_with_expert.py) | SmolVLM `AutoProcessor`의 video processor가 torchvision 요구 | ✅ **추론 핵심** | torchvision 설치 후 `AutoProcessor` 복원 완료 |
| [orin/lerobot/processor/hil_processor.py:25](orin/lerobot/processor/hil_processor.py#L25) | `torchvision.transforms.functional` | ❌ HIL 학습 전용 | Orin에서 미사용 |
| [orin/lerobot/scripts/lerobot_imgtransform_viz.py](orin/lerobot/scripts/lerobot_imgtransform_viz.py) | 이미지 증강 시각화 | ❌ 학습/디버깅 | Orin에서 미사용 |

핵심: **`AutoProcessor` 복원 완료 상태 자체가 torchvision이 추론 경로에서 실사용된다는 증거**다.

양측 관점:

**"미설치 유지" 측**
- 학습은 DGX에서 → `hil_processor`, `lerobot_imgtransform_viz` 미사용
- 단, 현재는 추론 경로 안정화/업스트림 diff 축소를 위해 이 선택지를 채택하지 않음

**"설치 권장" 측**
- upstream lerobot과의 diff 감소 → 우회 클래스 제거 가능 →
  [docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md](docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md)
  유지보수 부담 ↓
- SmolVLM upstream 업데이트 대응 — 향후 video processor가 다른 기능
  (비디오 전처리, 프레임 샘플링 등) 추가 시 우회 클래스로 감당 불가
- Seeed 튜토리얼의 `lerobot-record`, `lerobot-dataset-viz` 명령이 Orin에서 직접 동작
  (Orin에서 데이터 수집할 경우 필요)
- 설치 난이도 낮음 — Seeed SharePoint에 JP 6.0/6.1/6.2용 wheel 제공
  ([so101.md:54-60](docs/reference/seeedwiki/seeedwiki_so101.md#L54-L60))

결정 기준:

| 질문 | Yes | No |
|---|---|---|
| Orin에서 **데이터 수집**(teleop 녹화) 수행? | 설치 권장 | 설치 불요 |
| SmolVLM upstream 업데이트를 꾸준히 따라갈 것? | 설치 권장 | 설치 불요 |

현재 답변: **학습 DGX / Orin 추론 전용** 전제는 유지하되, 유지보수성 개선을 위해
torchvision을 설치하고 `AutoProcessor`를 복원함.

조치:
- [x] [docs/storage/05_orin_venv_setting.md](docs/storage/05_orin_venv_setting.md) torchvision 표현 수정 (2026-04-23)
- [x] 업그레이드 경로 05_orin_venv_setting.md에 명시 (2.5→0.20 / 2.7→0.22) (2026-04-23)
- [x] torchvision 0.20 설치 + `AutoProcessor.from_pretrained()` 복원 완료 (2026-04-23)

---

### A-3. venv 사용이 잘못되었는가? Seeed는 conda를 권장하는데?

**답: 틀리지 않았다. 우리 환경에서는 venv가 더 적합하다.**

Seeed가 conda를 쓰는 실제 이유:

[so101.md:69-75, 80-90](docs/reference/seeedwiki/seeedwiki_so101.md#L69-L90)
```bash
conda create -y -n lerobot python=3.10
conda install ffmpeg -c conda-forge
conda install -y -c conda-forge "opencv>=4.10.0.84"
```

- `ffmpeg=7.1.1`을 pip로 설치하기 어려움 → conda-forge의 prebuilt binary 사용
- aarch64용 `opencv>=4.10.0.84`를 conda-forge에서 한 번에 확보하기 위함

우리가 venv로 갈 수 있던 이유:

1. **opencv는 pip wheel로 해결**
   - [orin/pyproject.toml:15](orin/pyproject.toml#L15): `opencv-python-headless>=4.9.0,<4.14.0`
   - PyPI의 aarch64 manylinux wheel 정상 설치

2. **ffmpeg Python 바인딩 불필요**
   - Orin은 추론 전용 → 비디오 인코딩/디코딩은 학습/기록 시점 작업
   - ffmpeg CLI만 필요하며 JetPack이 시스템 패키지로 제공

3. **NVIDIA 공식 PyTorch wheel은 pip 기반 설치 전제**
   - [Install-PyTorch-Jetson-Platform.md:104-107](docs/reference/nvidia_official/Install-PyTorch-Jetson-Platform.md#L104-L107):
     `python3 -m pip install --no-cache $TORCH_INSTALL`
   - pip이 공식 경로이며, conda는 선택적 wrapper

4. **Jetson 상 conda의 단점**
   - conda-forge aarch64 채널의 패키지 커버리지가 불완전 (특히 NVIDIA 쪽)
   - conda env의 Python이 시스템 Python과 분리되어 **JetPack 번들 라이브러리
     호출 시 경로 이슈** 발생 가능
   - Miniconda 자체가 수백 MB → Orin NVMe 공간 비용
   - conda + pip 혼용 시 의존성 충돌 (ffmpeg가 대표적 사례)

프로젝트 내 선행 검증:

[docs/storage/05_orin_venv_setting.md:12-14](docs/storage/05_orin_venv_setting.md#L12-L14)
> "conda env 방식은 폐기. setup_env.sh가 생성하는 venv를 사용."

devPC에 conda `lerobot` env가 이미 있음
([docs/storage/03_software.md:46-48](docs/storage/03_software.md#L46-L48))에도 불구하고
Orin에선 venv를 새로 만든 결정 — 위 4번 단점이 실제 경험으로 축적됨.

결론:
- ✅ venv 선택 타당. Seeed의 conda 절차는 "처음 접하는 사용자에게 ffmpeg/opencv 설치
  허들을 낮추기 위한 간편 경로"이며, 기술적 우위 때문이 아님
- 우리는 NVIDIA 공식 pip 설치 경로 + opencv-headless wheel로 충분 → venv가 자연스러움

조치:
- [x] venv 방침을 [docs/storage/05_orin_venv_setting.md](docs/storage/05_orin_venv_setting.md) §2에 근거와 함께 명시 (2026-04-23)
- [x] Orin에 `ffmpeg` 시스템 패키지 설치 여부 확인 (`ffmpeg -version`) (2026-04-23) — 미설치 확인
- [x] Orin에 `ffmpeg` 설치 (`sudo apt install -y ffmpeg`) (2026-04-23)
- [x] `pip install 'Cython<3'` 불필요 확인 — torchvision 소스 컴파일 아닌 Seeed SharePoint wheel 사용으로 결정됨 (2026-04-23)

---

### A-4. lerobot 수정 부담을 줄이려면 Seeed 포크를 써야 하나?

**답: 현재 upstream 서브모듈 방식의 대안으로 검증해볼 가치가 있다. 단, 포크가 실제로
Python 3.10 문법 패치와 Jetson torchvision 의존성을 해결해뒀는지 **코드 확인 선행 필요**.**

### 현재 상황

- 우리 서브모듈: https://github.com/huggingface/lerobot (upstream, Python 3.12+ 요구)
- 관리 중인 Orin 패치: **8개** ([docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md](docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md))
  - Python 3.12 전용 문법 3곳 (io_utils / motors_bus / factory+pretrained)
  - torchvision 의존성 우회 5곳 (hil_processor / gym_action_processor / configs / smolvlm_with_expert / policies)

### Seeed 포크

**URL:** https://github.com/Seeed-Projects/lerobot

Seeed 튜토리얼이 **공식 repo 대신 명시적으로 권장**하는 저장소:

[seeedwiki_so101.md:1218](docs/reference/seeedwiki/seeedwiki_so101.md#L1218):
> 권장 저장소 클론: https://github.com/Seeed-Projects/lerobot.git (**공식 repo가 아닌 안정 버전**)
> 공식 repo는 계속 업데이트되어 버전 불일치가 발생할 수 있음.

본문 설치 명령 [seeedwiki_so101.md:133](docs/reference/seeedwiki/seeedwiki_so101.md#L133):
```bash
git clone https://github.com/Seeed-Projects/lerobot.git ~/lerobot
```

### 기대하는 것

Seeed 튜토리얼이 **Jetson Orin + Python 3.10** 조합을 전제로 작성되었으므로, 포크가 다음을 **이미 처리했을 가능성** 있음:

- Python 3.12 전용 문법(`def func[T](...)`, `type X = ...`, `typing.Unpack` 등) → 3.10 호환으로 downgrade
- torchvision 의존성 조정 (Seeed SharePoint wheel 사용 전제)

사실이면 **우리가 지고 있는 8개 패치 중 3~5개 제거 가능**.

### 검증 방법 (설치 전 코드 확인만으로 가능)

https://github.com/Seeed-Projects/lerobot 에서 아래 항목 확인:

1. **`pyproject.toml`의 `requires-python`**
   - `>=3.12`이면 upstream과 동일 — **포크 의미 제한적**
   - `>=3.10`이면 포크가 downgrade 작업을 한 것 — **기대 유효**

2. **`src/lerobot/utils/io_utils.py`의 `deserialize_json_into_object` 시그니처**
   - `def ...[T: JsonLike](...)` 유지면 → 3.10 패치 안 됨
   - `TypeVar` 사용으로 바뀌었으면 → 3.10 패치 완료

3. **`src/lerobot/motors/motors_bus.py`의 type alias**
   - `type NameOrID = str | int` 유지면 → 3.10 패치 안 됨
   - `Union[str, int]` 사용이면 → 3.10 패치 완료

4. **`src/lerobot/processor/hil_processor.py` torchvision import**
   - 그대로 유지 + 설치 가이드에서 torchvision 필수화했는지 확인

5. **최근 커밋 빈도** — upstream 대비 얼마나 후행인지

### 판단 기준

| 확인 결과 | 결정 |
|---|---|
| `requires-python >= 3.10` + 주요 3곳 모두 3.10 호환 | Seeed 포크로 서브모듈 **교체 검토** |
| `requires-python >= 3.12` 또는 3.10 패치 없음 | 현재 upstream + 우리 패치 **유지** |
| 혼합 (일부만 패치) | 우리가 부족분만 추가 패치 — 현재보다 이득인지 재평가 |

### 조사 결과 (2026-04-23 완료)

서브모듈 `docs/reference/seeed-lerobot` 추가 후 직접 코드 확인.

| 체크 항목 | Seeed 포크 결과 | 판단 |
|---|---|---|
| `requires-python` | `>=3.10` | ✅ Python 3.10 지원 확인 |
| `io_utils.py` | `TypeVar("T", bound=JsonLike)` 사용 | ✅ 3.10 호환 패치 완료 |
| `motors_bus.py` | `NameOrID: TypeAlias = str \| int` 사용 | ✅ 3.10 호환 패치 완료 |
| `factory.py` / `pretrained.py` | `TypeVar` from typing 사용 | ✅ 3.10 호환 패치 완료 |
| `hil_processor.py` torchvision | `import torchvision` **그대로 유지** | ❌ torchvision 필요 |
| 커밋 lag | 최신 PR `#2847` vs upstream `#3427` | ⚠️ 약 600 PR 후행 |

### 결정

- **Seeed 포크로 서브모듈 교체: ❌ 미채택**
  - 이유: upstream 대비 ~600 PR 후행 — 최신 smolVLA 기능·버그픽스 누락 위험
- **Python 3.10 패치 3곳**: Seeed 포크가 동일한 방식으로 패치 → **우리 방향 검증됨**, 현행 유지
- **torchvision**: Seeed 포크도 설치 전제로 동작 → **torchvision 0.20 설치 결정 확정**

### 할 일

- [x] `docs/reference/seeed-lerobot` 서브모듈 추가 + 5개 항목 코드 확인 (2026-04-23)
- [x] 결정: upstream 유지 + Python 3.10 패치 현행 유지 (2026-04-23)
- [x] 결정: torchvision 0.20 설치 확정 → §3 진행 (2026-04-23)
- [x] 확인 결과를 [docs/storage/lerobot_upstream_check/01_compatibility_check.md](docs/storage/lerobot_upstream_check/01_compatibility_check.md) 에 기록 (2026-04-23)
