# Walking RL × SmolVLA DGX Spark 공유 점검 결과

> 작성: 2026-04-28  
> 측정 시점: 훈련 진행 중 (D4 스테이지)

---

## 1-A. PyTorch / CUDA 환경

| # | 질문 | 답변 |
|---|---|---|
| 1 | PyTorch 버전 | **2.10.0+cu130** |
| 2 | CUDA 빌드 | **cu130 (CUDA 13.0)** |
| 3 | PyTorch 설치 방식 | **pip** (nvidia 공식 wheel, cu130 빌드) |
| 4 | cuDNN 별도 시스템 설치? | **없음** — `nvidia-cudnn-cu13==9.15.1.9` wheel로 번들링 |
| 5 | 기타 시스템 라이브러리 | NCCL `nvidia-nccl-cu13==2.28.9`, cuSPARSELt, nvSHMEM 모두 pip wheel로 설치됨 |

> ⚠️ **경고**: PyTorch 2.10.0+cu130은 GB10(CUDA capability 12.1)을 공식 지원 범위(8.0–12.0) 밖으로 표시하지만, 실제로는 동작 중입니다. SmolVLA도 동일 wheel 사용 시 같은 UserWarning이 뜨나 기능적으로는 문제없을 가능성이 높습니다.

---

## 1-B. Python 환경 격리

| # | 질문 | 답변 |
|---|---|---|
| 6 | 격리 방식 | **venv** (`uv`로 생성, conda 없음) |
| 7 | 환경 경로 | `/home/laba/env_isaaclab/` |
| 8 | Python 버전 | **3.12.3** |

> SmolVLA가 `/home/laba/smolvla_env/` 같은 별도 경로에 venv 생성하면 충돌 없음.

---

## 1-C. 자원 점유 (훈련 진행 중 실측)

| # | 질문 | 답변 |
|---|---|---|
| 9 | GPU(GB10) 사용률 | **88%** (D4 스테이지 훈련 중 측정) |
| 10 | 메모리(UMA) 점유 | Walking RL: **~7.3 GB RAM + 2,490 MiB GPU** / 총 RAM 124GB 중 38GB 사용, ~86GB 가용 |
| 11 | CPU 사용 코어/비율 | **~1.7코어(170%)** — 전체 20코어 중 idle 91.5%, 부담 거의 없음 |
| 12 | 디스크 I/O 집중도 | **낮음** — 체크포인트: `/home/laba/DGX-NUC/checkpoints/biped/`, 로그: `/tmp/hylion_*.log` |
| 13 | Ollama 상태 | **실행 중이나 GPU 미사용** (CPU/RAM 274MB만 사용) — 훈련 중 stop 불필요 |

---

## 1-D. 훈련 운영

| # | 질문 | 답변 |
|---|---|---|
| 14 | 다른 프로세스와 GPU 공유? | **Yes** — `Artifical-Intelligence/.venv` Jupyter kernel 2개가 **8,525 + 4,413 = 12,938 MiB** 점유 중. Walking RL은 2,490 MiB. MPS/MIG 미사용, 단순 다중 프로세스 공유 |
| 15 | 다른 팀 훈련 시 영향 | **GPU 메모리 경합이 핵심 위험** — GB10 UMA 특성상 총 메모리 제한. SmolVLA가 큰 모델 올리면 OOM 가능 |
| 16 | 훈련 일시 중단 가능? | **가능** — `Ctrl+C` 또는 kill로 중단 후 `--pretrained_checkpoint`로 재시작 지원 |
| 17 | 체크포인트/로그 저장 위치 | 체크포인트: `/home/laba/DGX-NUC/checkpoints/biped/stage_*/` / 로그: `/tmp/hylion_*.log` |
| 18 | 모니터링 도구 | `nvidia-smi` 직접 사용 (별도 daemon/exporter 없음) |

---

## 1-E. 결정 의견

| # | 질문 | 답변 |
|---|---|---|
| 19 | SmolVLA 동일 DGX 훈련 의견 | **시간대 분리 조건부 가능** — 현재 Jupyter kernel 2개가 ~13GB 점유 중인 상태에서 SmolVLA까지 올리면 OOM 위험. Jupyter kernel 정리 후 또는 Walking RL 훈련 없는 시간대에 실행 권장 |
| 20 | 격리 방식 권장 | **venv 분리로 충분** — Walking RL: `/home/laba/env_isaaclab/`, SmolVLA: 별도 경로(예: `/home/laba/smolvla_env/`) 생성하면 패키지 충돌 없음 |

---

## 추가 분석: Ollama / Jupyter 커널 실행 원인

### Ollama
- `systemctl enable` 로 등록된 **부팅 자동시작 서비스** — 재부팅마다 자동으로 켜짐
- 설치 모델: `gemma3:27b` (17 GB)
- 현재 GPU 점유: **없음** (모델 미로드 상태)
- 마지막 API 호출: 2026-04-22 (측정 시점 기준 6일 전), 이후 미사용
- 현재 RAM: 274 MB만 사용 (대기 중인 서버)
- **위험**: 누군가 gemma3:27b 를 로드하면 순간적으로 ~17 GB 추가 점유

### Jupyter 커널 2개
- 위치: `/home/laba/Artifical-Intelligence/` — DETR 과제 노트북
  - `assignment2_DETR.ipynb`, `assignment2_DETR_exp1.ipynb`, `assignment2_DETR_exp2.ipynb`
- PID 2814697: 4월 26일 시작, GPU **8,525 MiB** 점유
- PID 2979278: 4월 27일 시작, GPU **4,413 MiB** 점유
- 현재 상태: **Sleeping** (셀 실행 중 아님) — 노트북에서 PyTorch 모델을 GPU에 올린 채 커널을 종료하지 않아 12.9 GB 낭비 중
- VSCode Jupyter 탭이 열려 있어 커널이 살아있는 상태
- **조치**: VSCode에서 해당 노트북 커널 Shutdown 시 12.9 GB 즉시 반환

---

## 추가 분석: 실제 사용 가능한 여유 메모리

### 스왑(Swap)이란?
RAM이 부족할 때 OS가 디스크 일부를 임시 RAM처럼 사용하는 공간. **DGX Spark는 스왑 0 B** — RAM 초과 시 완충 없이 프로세스가 즉시 OOM Kill됨. 고성능 ML 서버에서 학습 속도 저하를 방지하기 위해 의도적으로 비활성화된 경우가 많음.

### 메모리 현황 (실측)

```
전체 UMA:     121 GiB
├── 사용 중:   37 GiB  ← 실제 점유
├── 버퍼/캐시: 31 GiB  ← OS 디스크 캐시 (필요시 반환 가능)
├── 여분:      54 GiB  ← 순수 빈 공간
└── 가용:      84 GiB  ← 버퍼/캐시 반환 시 확보 가능한 최대치
```

### Walking RL 메모리 사용량이 적은 이유
- `--num_envs 4096` 기준 RAM 7.3 GB + GPU 2.5 GB = ~10 GB (정상, 효율적인 편)
- GB10 UMA 아키텍처에서는 CPU RAM과 GPU VRAM이 동일 물리 풀을 공유하므로 nvidia-smi에 잡히는 수치가 실제보다 작게 표시됨
- num_envs를 8,192~16,384로 늘려도 메모리 여유 있음

### SmolVLA 동시 실행 시 실질 가용량

| 조건 | 안전 사용 가능 추정 |
|---|---|
| 현재 상태 그대로 (Jupyter 커널 유지) | **~35~45 GiB** |
| Jupyter 커널 정리 후 | **~50~60 GiB** |
| Walking RL 훈련 종료 후 + Jupyter 정리 | **~70~80 GiB** |

> ⚠️ 학습은 초기화 시 메모리를 한꺼번에 할당하므로 **peak 사용량이 평균보다 훨씬 높을 수 있음**. 스왑 없으므로 초과 시 OOM Kill 발생.

---

## 핵심 요약

1. **PyTorch 2.10.0+cu130, Python 3.12.3, CUDA 13.0** — SmolVLA가 동일 버전 사용 시 wheel 호환성 좋음
2. **venv 분리만으로 충분** — Docker 불필요, 경로만 다르게 잡으면 됨
3. **GPU 메모리가 병목** — 현재 Jupyter kernel 2개가 ~13 GB 낭비 중. **SmolVLA 훈련 전 반드시 Jupyter 커널 Shutdown 필요**
4. **CPU / 디스크는 여유 충분** — 걱정 없음
5. **Ollama는 현재 GPU 비사용** — 단, gemma3:27b 로드 시 ~17 GB 순간 점유 주의
6. **스왑 없음** — 메모리 초과 시 OOM Kill 즉시 발생, 안전 마진 확보 필수

---

## 실측 환경 상세

```
GPU:      NVIDIA GB10 (DGX Spark), Driver 580.142, CUDA 13.0
Python:   3.12.3 (GCC 13.3.0)
PyTorch:  2.10.0+cu130
cuDNN:    9.15.1 (nvidia-cudnn-cu13 wheel)
venv:     /home/laba/env_isaaclab/ (uv 생성)
디스크:   /dev/nvme0n1p2  3.7T 총 / 228G 사용 / 3.3T 가용 (7%)
RAM:      121 GiB UMA / 37 GiB 사용 / 84 GiB 가용 (버퍼/캐시 포함)
스왑:     0 B (비활성화)
```

```
# 측정 시점 GPU compute 프로세스
PID 2814697  Artifical-Intelligence/.venv/python  8,525 MiB  (Jupyter kernel — DETR 과제, Sleeping)
PID 2979278  Artifical-Intelligence/.venv/python  4,413 MiB  (Jupyter kernel — DETR 과제, Sleeping)
PID 3196087  env_isaaclab/python                  2,490 MiB  (Walking RL D4 훈련, 33102/36695 iter)
```
