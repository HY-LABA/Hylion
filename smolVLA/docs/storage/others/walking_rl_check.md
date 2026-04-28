# Walking RL ↔ SmolVLA DGX Spark 공유 점검 요청

> 대상: Walking RL 트랙 담당자
> 작성: 2026-04-28
> 요청자: SmolVLA 트랙 (δ1)
> 회신 기한: (협의)

---

## 배경

SmolVLA 트랙도 같은 DGX Spark 머신(`spark-8434`, `laba` 계정)을 학습용으로 사용할 예정입니다. Walking RL 은 이미 DGX 를 하루 종일 점유하고 있다고 들었습니다. 두 트랙이 같은 머신에서 학습을 진행할 때 **자원 경합 / 환경 충돌** 이 어떤 수준인지 파악하기 위해 본 점검을 요청드립니다.

본 점검 결과로 SmolVLA 트랙에서 결정할 사항:

1. **자원 격리 방식**: venv 만 사용해도 되는지 / Docker 컨테이너 격리가 필요한지
2. **PyTorch / CUDA 버전 조합**: 두 트랙이 같은 wheel 을 쓸 수 있는지
3. **학습 스케줄링 전략**: 시간대 분할 / 동시 진행 / SmolVLA 별도 머신 검토

---

## 1. 질문 (답변 부탁드립니다)

### 1-A. PyTorch / CUDA 환경

| # | 질문 | 답변 |
|---|---|---|
| 1 | Walking RL 학습에 사용 중인 PyTorch 버전은? | |
| 2 | PyTorch 가 사용하는 CUDA 빌드 (cu118 / cu121 / cu124 / cu128 / cu130 등)? | |
| 3 | PyTorch 설치 방식 (`pip` / `conda` / 사전 빌드 wheel / nightly)? | |
| 4 | cuDNN 별도 시스템 설치 여부 (PyTorch 번들만 사용하는지)? | |
| 5 | 그 외 학습에 영향 주는 시스템 라이브러리 설치 (TensorRT, NCCL 등)? | |

### 1-B. Python 환경 격리

| # | 질문 | 답변 |
|---|---|---|
| 6 | Python 환경을 어떻게 격리하고 있나요 (시스템 Python / venv / conda / Docker / 기타)? | |
| 7 | 환경 경로 (예: `~/walking_rl/.venv`)? — 같은 위치 충돌 회피용 | |
| 8 | 사용 중인 Python 버전? | |

### 1-C. 자원 점유

| # | 질문 | 답변 |
|---|---|---|
| 9 | 학습 시 GPU(GB10) 사용률은 평균 몇 % 정도? | |
| 10 | 학습 시 메모리(UMA 121 GiB pool) 점유는 얼마? | |
| 11 | 학습 시 CPU(20 코어) 사용 코어 수 또는 비율은? | |
| 12 | 학습이 디스크 I/O 를 많이 쓰나요 (대량 dataloader / 체크포인트 자주 저장)? | |
| 13 | Ollama 가 DGX 에서 실행 중인데 (포트 11434), Walking RL 과 관련이 있나요? 학습 시 stop 해도 되나요? | |

### 1-D. 학습 운영

| # | 질문 | 답변 |
|---|---|---|
| 14 | Walking RL 학습이 동시에 다른 학습 프로세스가 GPU 를 같이 쓰는 것을 허용하나요 (MPS, MIG, 단순 동시 점유)? | |
| 15 | 다른 트랙이 같은 DGX 에서 학습할 때 영향 받나요 (학습 안정성 / 재현성 측면)? | |
| 16 | 학습 작업이 일시 중단 가능한가요 (예: SmolVLA 가 짧게 점유할 때 일시 정지 후 재개)? | |
| 17 | 체크포인트·로그·데이터셋 저장 위치 (`/home/laba/...` 어느 경로)? — 디스크 충돌 회피용 | |
| 18 | 자원 점유 모니터링을 위해 추가로 켜둔 도구가 있나요 (nvidia-smi 데몬, prometheus exporter 등)? | |

### 1-E. 결정 의견

| # | 질문 | 답변 |
|---|---|---|
| 19 | SmolVLA 트랙이 같은 DGX 에서 학습하는 것에 대한 의견은? (가능 / 시간대 분할 권장 / 별도 머신 권장 / 기타) | |
| 20 | 격리 방식 권장 (venv 분리만 OK / Docker 컨테이너 권장 / 기타)? | |

---

## 2. 실측 명령 스크립트 (DGX 에서 실행 부탁드립니다)

위 질문 답변에 도움이 되도록, 아래 명령들을 DGX Spark 에서 직접 실행하시고 결과를 함께 회신 부탁드립니다. **학습이 진행 중인 시점에 실행**하면 자원 점유 실측이 가장 정확합니다.

### 2-A. PyTorch / CUDA 환경 (Walking RL venv/conda 활성화 후 실행)

```bash
# Python·PyTorch·CUDA·cuDNN 한꺼번에 확인
python - <<'EOF'
import sys, torch
print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA build: {torch.version.cuda}")
print(f"cuDNN version: {torch.backends.cudnn.version()}")
print(f"GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
print(f"GPU count: {torch.cuda.device_count()}")
EOF

# pip 패키지 중 핵심 의존성
pip list 2>/dev/null | grep -iE "torch|cuda|nvidia|accelerate|transformers"

# Python 실행 파일 경로 (어느 환경인지 식별)
which python
echo "VIRTUAL_ENV=$VIRTUAL_ENV"
echo "CONDA_PREFIX=$CONDA_PREFIX"
```

### 2-B. 시스템 CUDA / 드라이버

```bash
# 시스템 CUDA SDK
nvcc --version 2>/dev/null || echo "nvcc not in PATH"

# 드라이버 / GPU 정보
nvidia-smi

# CUDA 라이브러리 위치
ls /usr/local/cuda* 2>/dev/null
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
```

### 2-C. 학습 진행 중 자원 점유 (학습 중에 실행)

```bash
# GPU / 메모리 / 프로세스 — 5초 간격 3회 샘플링
for i in 1 2 3; do
  echo "=== Sample $i / 3 ==="
  nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free --format=csv
  free -h | grep -E "Mem|Swap"
  echo
  sleep 5
done

# 어느 프로세스가 GPU 를 쓰는지
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

# 어느 프로세스가 RAM 을 많이 쓰는지 (상위 10개)
ps aux --sort=-%mem | head -11

# CPU 사용률
top -bn1 | head -20
```

### 2-D. 디스크 사용량 / 저장 위치

```bash
# 디스크 가용량
df -h /home/laba

# Walking RL 관련 디렉터리 크기 (경로는 본인 환경에 맞게 조정 부탁드립니다)
du -sh ~/walking_rl* 2>/dev/null
du -sh ~/checkpoints* 2>/dev/null
du -sh ~/datasets* 2>/dev/null

# 홈 디렉터리 상위 디렉터리별 크기
du -sh ~/* 2>/dev/null | sort -h | tail -20
```

### 2-E. Ollama 상태

```bash
# Ollama 서비스 상태
systemctl status ollama 2>/dev/null | head -10

# Ollama 가 GPU 를 쓰는지
nvidia-smi --query-compute-apps=pid,process_name --format=csv | grep -i ollama

# Ollama 가 점유한 메모리
ps aux | grep -i ollama | grep -v grep
```

---

## 3. 회신 방법

답변은 본 파일을 복사해서 채워넣은 형태로 회신 주시거나, 별도 메시지로 위 질문 번호별 답변과 실측 명령 결과를 보내주시면 됩니다. 이슈/우려사항이 있으면 19~20 번 항목에 자유롭게 적어주세요.

감사합니다.
