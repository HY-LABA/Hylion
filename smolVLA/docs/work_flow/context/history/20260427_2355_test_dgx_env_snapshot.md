# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 23:42 | 스펙: `docs/work_flow/specs/02_dgx_setting.md` | TODO: 02

## 테스트 목표

DGX Spark 환경 실측 재진행 — 하드웨어/소프트웨어 현황을 측정하고 신규 스냅샷 파일로 저장한 뒤 `docs/storage/03_software.md`에 반영한다.

## DOD (완료 조건)

- DGX 실측값이 `docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt` 로 저장됨
- `docs/storage/03_software.md` (필요 시 `02_hardware.md`) 가 실측값 기준으로 최신화됨
- TODO-06·07·08 진행에 필요한 정보(GPU VRAM, CUDA/cuDNN/TensorRT 상태, Python·pip, 디스크 가용량, 외장 SSD 여부)가 명확화됨

## 환경

DGX Spark | Ubuntu 24.04 | `laba@spark-8434` | `ssh dgx` 접속 (172.16.136.60)

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->
<!-- 모든 명령은 ssh dgx "..." 형태로 devPC에서 실행한다 -->
o
| # | 단계 | 명령 (ssh dgx "...") | 결과 | 비고 |
|---|------|----------------------|------|------|
| 1 | SSH 접속 확인 | `echo ok` | PASS: `ok` | |
| 2 | OS / 커널 / hostname / arch | `uname -a && lsb_release -a` | PASS: `spark-8434`, `aarch64`, kernel `6.17.0-1014-nvidia`, Ubuntu `24.04.4 LTS` | |
| 3 | CPU 모델·코어 수 | `lscpu \| grep -E 'Model name\|^CPU\(s\)'` | PASS: `20` CPUs, `Cortex-X925` + `Cortex-A725` | |
| 4 | 메모리 총량·가용량 | `free -h` | PASS: total `121Gi`, used `31Gi`, free `60Gi`, available `90Gi`, swap `0B` | |
| 5 | GPU 모델·VRAM·드라이버 버전 | `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader` | PASS: `NVIDIA GB10`, memory.total `[N/A]`, driver `580.142` | DGX Spark는 UMA 구조라 전용 VRAM으로 기록하지 않음 |
| 6 | nvidia-smi 전체 출력 | `nvidia-smi` | PASS: NVIDIA-SMI `580.142`, CUDA `13.0`, GPU `NVIDIA GB10`, memory usage `Not Supported`, compute process 2개 확인 | UMA/iGPU 플랫폼의 정상 표시 |
| 7 | CUDA SDK 버전·nvcc 경로 | `nvcc --version 2>/dev/null \|\| echo 'nvcc not found'; which nvcc 2>/dev/null` | PASS: CUDA compilation tools `13.0`, `V13.0.88`; path `/usr/local/cuda/bin/nvcc` | |
| 8 | cuDNN 설치 여부 | `dpkg -l \| grep -i cudnn \|\| echo 'not found'` | PASS: `not found` | 별도 설치 필요 여부 결정 필요 |
| 9 | TensorRT 설치 여부 | `dpkg -l \| grep -i tensorrt \|\| echo 'not found'` | PASS: `not found` | 별도 설치 필요 여부 결정 필요 |
| 10 | Python 버전·경로 | `python3 --version && which python3` | PASS: Python `3.12.3`, `/usr/bin/python3` | |
| 11 | pip 설치 여부 | `pip3 --version 2>/dev/null \|\| echo 'not found'` | PASS: pip `24.0` from `/usr/lib/python3/dist-packages/pip` | |
| 12 | venv / conda 사용 가능 여부 | `python3 -m venv --help > /dev/null 2>&1 && echo 'venv ok'; conda --version 2>/dev/null \|\| echo 'conda not found'` | PASS: `venv ok`, `conda not found` | |
| 13 | Docker 설치 여부 | `docker --version 2>/dev/null \|\| echo 'not found'` | PASS: Docker `29.1.3`, build `f52814d` | |
| 14 | NVIDIA Container Toolkit | `nvidia-ctk --version 2>/dev/null \|\| echo 'not found'` | PASS: NVIDIA Container Toolkit CLI `1.19.0` | |
| 15 | 디스크 용량 전체 | `df -h` | PASS: root `/dev/nvme0n1p2` size `3.7T`, used `228G`, avail `3.3T`, use `7%` | |
| 16 | 외장 SSD 마운트 여부 | `lsblk -o NAME,SIZE,TYPE,MOUNTPOINT \| grep -E 'disk\|part'` | PASS: `nvme0n1` 3.7T with `/boot/efi` and `/`; `sda`/`sdb` are `0B`; 외장 SSD 마운트 없음 | |
| 17 | 네트워크 인터페이스 / IP | `ip addr show \| grep -E 'inet ' ` | PASS: `192.168.0.7`, `172.16.136.60`, docker `172.17.0.1`, tailscale `100.121.174.9` | |
| 18 | 동작 중 서비스 (Ollama 등) | `systemctl list-units --state=running --no-pager \| grep -E 'ollama\|jupyter\|mlflow' \|\| echo 'none found'` | PASS: `ollama.service` running | |
| 19 | 전체 출력을 스냅샷 파일로 저장 | 위 #2~18 출력을 모아 `docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt` 에 저장 | PASS: 스냅샷 파일 생성 완료 | 파일 생성 확인 |
| 20 | `docs/storage/03_software.md` 업데이트 | 실측값을 반영하여 DGX 항목 최신화 | PASS: DGX 소프트웨어 항목을 2026-04-27 실측값으로 갱신 | `02_hardware.md`도 DOD에 맞춰 DGX 섹션만 갱신 |
