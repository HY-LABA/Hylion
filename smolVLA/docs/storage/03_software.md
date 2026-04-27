# smolVLA 소프트웨어 현황 (현재 설정/실측)

> 작성일: 2026-04-21  
> 업데이트: 2026-04-23
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
- PyTorch: venv에 설치 (`~/smolvla/.venv`) — 시스템 패키지 아님
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

- 스냅샷 파일: `smolVLA/docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-22_0043.txt`
- OS: `Ubuntu 24.04.4 LTS`
- 커널: `6.17.0-1014-nvidia`
- CUDA:
  - `nvcc`: PATH에 미탐지 (패키지로 설치됨, SDK `13.0.2`)
  - GPU 드라이버: `580.142`
- cuDNN: 미탐지 (별도 설치 필요)
- TensorRT: 미탐지 (별도 설치 필요)
- PyTorch: 미설치
- Python: `3.12.3` (pip3 미탐지)
- conda: 미설치
- Docker: 미탐지
- ROS2: 미설치
- 특이사항: 포트 `11434` 리슨 중 (Ollama 실행 중인 것으로 추정)

## 6) 추가 확인 필요 항목

- [x] Orin 시스템 소프트웨어 재검증 완료 (2026-04-23)
  - `nvcc -V` 정상 출력 (`release 12.6, V12.6.68`)
  - `ffmpeg` 설치 완료 (`4.4.2-0ubuntu0.22.04.1`)
- [ ] DGX cuDNN / TensorRT 설치 필요 여부 확인
- [ ] 학습 PC(DGX)와 Orin 간 모델 반입/실행 절차 확정
- [ ] 외장 SSD 사용 시 데이터셋/체크포인트 경로 확정
