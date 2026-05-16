# leftarm_v2 — Image Dataset 변환 절차

> **목적**: `BaboGaeguri/leftarm_v2` (video, mp4) 를 `BaboGaeguri/leftarm_v2_image` (image, PNG) 로 변환. 학습 중 발생하는 video-decode 메모리 누수를 근본 제거.
> **스크립트**: `dgx/finetune/leftarm_v2/convert_to_image.py`
> **대상 환경**: DGX — `~/smolvla/dgx/.arm_finetune` venv

---

## 1. 배경 — 왜 image 변환인가

### 실험 A 결과 (TODO-1a-fix)

| 항목 | 측정값 |
|---|---|
| pyav backend 누수율 | 1.07 GB/min (step 0-1000 구간) |
| torchcodec 누수율 (시도 1·2) | 1.25 GB/min |
| main process RSS | 2.89 GB (안정 — 증가 없음) |
| worker process RSS | 1.5-1.6 GB (안정) |
| 결론 | 누수는 process 외부 (libav OS buffer / shmem). workers 가 주체 아님 |

**pyav 로 교체해도 동일한 속도로 메모리 증가** → video decode 계층 자체가 원인. image pre-extraction 만이 근본 해법.

### 해법

- ffmpeg CLI subprocess 로 episode 별 PNG 추출 → process 종료 시 libav OS buffer 완전 해제
- `leftarm_v2_image` 로 학습 시 DataLoader 가 PNG 를 직접 읽음 → video decode 0

---

## 2. 사전 조건

### 2-1. 환경 확인

```bash
# DGX venv 활성화
source ~/smolvla/dgx/.arm_finetune/bin/activate

# ffmpeg 설치 확인
which ffmpeg && ffmpeg -version | head -1
# 예상: /usr/bin/ffmpeg  또는  conda 경로
# 없으면: conda install -c conda-forge ffmpeg  또는  sudo apt-get install ffmpeg
```

### 2-2. 소스 dataset 존재 확인

```bash
ls ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/meta/info.json
# 있어야 함. 없으면 lerobot-download 로 먼저 받기
```

### 2-3. 디스크 여유 공간 확인

```bash
df -h ~/smolvla/.hf_cache/
# 필요 공간 추정: 60,000 frames × 2 cameras × ~100KB/PNG ≈ 12 GB (PNG 기준)
# JPG 사용 시: ~2-3 GB
```

### 2-4. 현재 학습 종료 대기

이 변환 작업은 DGX GPU 를 사용하지 않으나 **디스크 I/O 가 집중**됨.
학습이 돌고 있으면 종료 후 실행 권장.

```bash
# 학습 진행 중 확인
ps aux | grep lerobot-train
# 또는
nvidia-smi
```

---

## 3. 실행 순서

### Step 0 — Dry-run (계획 확인, 파일 미변경)

```bash
cd ~/smolvla
python dgx/finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --dry-run
```

예상 출력:
```
HH:MM:SS | INFO | Video keys: ['observation.images.top', 'observation.images.wrist']
HH:MM:SS | INFO | Total episodes in source: 110
HH:MM:SS | INFO | Episodes to convert: 110  (indices 0 .. 109)
HH:MM:SS | INFO | [DRY-RUN] No files will be written.
```

### Step 1 — 소규모 검증 (10 episodes)

전체 변환 전에 10 episodes 로 형식 정합성 확인.

```bash
python dgx/finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --episodes 0-9 \
    --loglevel INFO
```

완료 후 검증 (Step 4 참조) → 이상 없으면 Step 2 진행.

### Step 2 — 전체 110 episodes 변환

```bash
python dgx/finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --skip-existing \
    --loglevel INFO
```

- `--skip-existing`: 이미 변환된 episode 건너뜀 (Step 1 에서 변환한 0-9 재사용)
- 예상 소요 시간: 60,000 frames × 2 cameras ÷ ~200 frames/s ≈ 10-15 분

### Step 3 — 특정 range 추가 변환 (incremental, 신규 episode 시)

나중에 `leftarm_v2` 에 episode 를 추가한 경우:

```bash
python dgx/finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --episodes 110-119 \
    --skip-existing
```

---

## 4. 검증 절차

### 4-1. 디렉터리 구조 확인

```bash
# image 파일 존재 확인
ls ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/images/ | head
# 예상: observation.images.top  observation.images.wrist

ls ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/images/observation.images.top/ | head -5
# 예상: episode-000000/  episode-000001/  ...

ls ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/images/observation.images.top/episode-000000/ | head -5
# 예상: frame-000000.png  frame-000001.png  ...

# info.json dtype 확인
python -c "
import json
info = json.load(open('$HOME/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/meta/info.json'))
for k, ft in info['features'].items():
    print(k, '->', ft.get('dtype'))
"
# 예상: observation.images.top -> image
#        observation.images.wrist -> image
```

### 4-2. Episode·Frame count 비교

```bash
python -c "
import json, pathlib

src = pathlib.Path('$HOME/.hf_cache/lerobot/BaboGaeguri/leftarm_v2')
dst = pathlib.Path('$HOME/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image')

src_info = json.load(open(src / 'meta/info.json'))
dst_info = json.load(open(dst / 'meta/info.json'))

print('Source  episodes:', src_info.get('total_episodes'), '  frames:', src_info.get('total_frames'))
print('Target  episodes:', dst_info.get('total_episodes'), '  frames:', dst_info.get('total_frames'))
print('Frame count match:', src_info.get('total_frames') == dst_info.get('total_frames'))
"
```

### 4-3. LeRobotDataset 로드 테스트

```bash
python -c "
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import pathlib

root = pathlib.Path('$HOME/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image')
ds = LeRobotDataset(repo_id='BaboGaeguri/leftarm_v2_image', root=root)
print('total_episodes:', ds.meta.total_episodes)
print('total_frames  :', ds.meta.total_frames)
print('image_keys    :', ds.meta.image_keys)
print('video_keys    :', ds.meta.video_keys)  # should be []

# 첫 프레임 로드 테스트
sample = ds[0]
print('sample keys:', list(sample.keys()))
print('image shape (top):', sample['observation.images.top'].shape)
"
```

### 4-4. 디스크 사용량

```bash
du -sh ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/
du -sh ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/
```

---

## 5. 결과 기록

변환 완료 후 `training_log.md` 에 다음 양식으로 "변환 결과" 섹션을 추가:

```markdown
## 변환 결과 — YYYY-MM-DD

| 항목 | 값 |
|---|---|
| 변환 일시 | YYYY-MM-DD HH:MM |
| 소스 dataset | BaboGaeguri/leftarm_v2 (video, mp4) |
| 타깃 dataset | BaboGaeguri/leftarm_v2_image (image, PNG) |
| 변환 episode 수 | 110 / 110 |
| 총 frame 수 | ______ (top) / ______ (wrist) |
| 소스 디스크 사용량 | du 결과 |
| 타깃 디스크 사용량 | du 결과 |
| 변환 소요 시간 | ______ 분 |
| LeRobotDataset 로드 | OK / FAIL |
| 비고 | |
```

---

## 6. 트러블슈팅

### ffmpeg 없음

```
ffmpeg not found in PATH
```

해결:
```bash
# conda 환경에 설치
conda install -c conda-forge ffmpeg

# 또는 시스템 패키지
# (venv 외부에서 sudo 필요 — DGX sysadmin 에게 요청 또는 conda 방식 권장)
```

### 권한 오류

```
PermissionError: [Errno 13] Permission denied: '...'
```

해결:
- `~/.hf_cache/` 의 소유자 확인: `ls -la ~/.hf_cache/`
- 타깃 경로가 다른 사용자 소유이면 다른 target-root 지정

### 디스크 부족

```
OSError: [Errno 28] No space left on device
```

해결:
```bash
# 여유 공간 확인
df -h ~/smolvla/.hf_cache/

# JPEG 사용 (PNG 대비 약 1/5 용량):
python convert_to_image.py ... --image-format jpg
# 주의: JPEG 는 lossy — lerobot 표준은 PNG. 학습 품질 차이 미검증.

# 또는 다른 파티션에 target-root 지정
python convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root /data/datasets/leftarm_v2_image \
    --skip-existing
```

### codec 인식 실패 (드묾)

```
ffmpeg failed: Invalid data found when processing input
```

해결:
```bash
# 수동으로 특정 episode 비디오 확인
ffprobe -v error -show_streams \
    ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/videos/observation.images.top/chunk-000/file-000.mp4

# 손상된 episode 는 --fail-fast 없이 실행하면 skip 후 계속 진행됨
python convert_to_image.py ... # (--fail-fast 옵션 없이)
```

### LeRobotDataset 로드 실패 (partial conversion 후)

부분 변환 후 로드 테스트 실패는 정상 (일부 episode 만 변환된 상태).
전체 변환 완료 후 재시도.

```bash
# 변환 완료 episode 수 확인
ls ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/images/observation.images.top/ | wc -l
```

### 중단 후 재시작 (resumable)

```bash
# 기존 진행 유지하며 나머지만 변환
python convert_to_image.py \
    --source-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --skip-existing
```

---

## 7. 이후 학습 실행

변환 완료 후 `run_train.py` 에서 dataset 을 교체:

```bash
# train_config.yaml 수정 또는 CLI override
python run_train.py train --pass 2a \
    -- dataset.repo_id=BaboGaeguri/leftarm_v2_image \
       dataset.root=~/.hf_cache/lerobot
```

또는 `config/train_config.yaml` 에서:

```yaml
dataset:
  repo_id: BaboGaeguri/leftarm_v2_image   # was: BaboGaeguri/leftarm_v2
  root: ~/smolvla/.hf_cache/lerobot
```

image dataset 사용 시 lerobot 이 자동으로 `image_keys` 를 인식하고 PNG 파일을 직접 로드함.
`video_backend` 설정 불필요 (video decode 경로 비활성).
