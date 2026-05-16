# 실험 C — GOP 가설 검증 (file-000.mp4 만 GOP=2 재인코딩)

> **목적**: pyav `keyframes_only` seek 의 *중간 frame 누적 버퍼* 가 누수의 결정타인지 검증. v1 (libsvtav1, GOP=2) 완주 vs v2 (h264_nvenc, GOP=250) OOM 의 *125배 GOP 차이* 가 leak 의 진짜 원인 가설.
> **위치**: `dgx/docs/finetune/leftarm_v2/exp_c_gop/` (실험 A·B 와 sibling — 사용자 지정 별도 폴더)
> **변수 분리**: 시도 1·2·3 (실험 A) 대비 *유일 변경* = `file-000.mp4` 의 GOP. cleanup·workers·prefetch·batch 등 다른 변수 동일.

---

## 배경

researcher 보고서 §3 의 코드 리뷰가 짚었으나 *실측 GOP 를 모르고* 평가:

> "GOP 기본값 g=2 이면 2프레임마다 키프레임이지만, 실제 녹화된 영상의 GOP 가 길면 수십 프레임을 항상 추가 디코딩"

→ 메인 Claude 의 실측 (2026-05-16):

| dataset | codec | **실측 GOP** | 한 seek 당 추가 디코딩 frame |
|---|---|---|---|
| v1 | libsvtav1 (av1) | **2** (1, 3, 5, 7, ...) | ~1 |
| v2 | h264 (h264_nvenc) | **250** (1, 251, ...) | ~125 |

→ **125× 차이**. researcher 의 옵션 6 (mp4 chunk 재인코딩) 이 "우선순위 낮음, 효과 불확실 (20~30%)" 으로 평가됐는데 *실측 모르고 평가*. 본 실험으로 재평가.

## 가설

`file-000.mp4` (top + wrist) 만 GOP=2 로 재인코딩 + `--dataset.episodes=[0..9]` 로 file-000 만 디코딩 → 누수율이 v1 수준 (수십 MB/min) 으로 떨어지면 **GOP 가 결정타 확정**.

## 절차

### 1. dataset 사본 만들기 (symlink 기반, 디스크 ~수MB)

```bash
cd ~/smolvla/.hf_cache/lerobot/BaboGaeguri
cp -as $PWD/leftarm_v2/. $PWD/leftarm_v2_gopcheck/
# cp -as: 디렉터리는 mkdir, 파일은 absolute symlink. 원본 보존.
```

### 2. file-000.mp4 (top + wrist) 만 GOP=2 로 재인코딩

`reencode_file_000.sh` 실행. 동작:
- 두 카메라의 file-000.mp4 의 symlink 해제
- 원본을 `-c:v libx264 -g 2 -keyint_min 2 -preset fast` 로 재인코딩 — symlink 위치에 새 파일 저장
- 결과: dataset 의 *file-000.mp4 만* GOP=2, 나머지 mp4 는 symlink (원본 GOP=250)

### 3. 학습 5분 모니터링 (다른 AI 의 학습 종료 후 진입)

본 실험의 학습 명령은 *시도 3 (실험 A) 과 동일* 하되 단 2가지 변경:
- `--dataset.root=~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_gopcheck`
- `--dataset.episodes=[0,1,2,3,4,5,6,7,8,9]` (10ep, file-000.mp4 만 디코딩)

cleanup 강화 (실험 A 기준) 동일하게 적용 — 변수 분리: GOP 만 변경.

명령은 `train_command.sh` 참조. 학습 5분 + wandb `system/memory` 모니터링.

## 성공 / 실패 판정

| 누수율 (Q4 steady-state) | 판정 | 후속 |
|---|---|---|
| **< 100 MB/min** | ✅ 가설 확정 (v1 수준 회복) | 전체 14 mp4 재인코딩 진행 (~30분~1h, 디스크 ~3GB) |
| 100~500 MB/min | ⚠️ 부분 효과 — GOP + 다른 요인 복합 | 추가 실험 (cleanup vs no-cleanup 변수 분리) |
| > 500 MB/min | ❌ 가설 부정 — codec/GOP 가 아닌 다른 원인 (pyav 자체 leak 우선) | image 변환 (옵션 3) 으로 fallback |

(시도 2 의 Q4 누수율 = 1,254 MB/min, 시도 1 = 1,805 MB/min — 비교 baseline)

## 결과 (실행 후 기입)

### 실행 메타

| 항목 | 값 |
|---|---|
| 실행 시각 | (TBD) |
| 다른 AI 의 시도 3 결과 | (TBD — 종료·OOM·완주) |
| 우리 실험 C run name | (TBD) |
| wandb run URL | (TBD) |

### file-000.mp4 재인코딩 결과

| view | 원본 크기 | 재인코딩 후 크기 | 비율 |
|---|---|---|---|
| top | (TBD) | (TBD) | (TBD) |
| wrist | (TBD) | (TBD) | (TBD) |

### 5분 학습 모니터링

| 시각 | step | MemAvailable | system 누수율 (MB/min) | 관찰 |
|---|---|---|---|---|
| t=0 | 0 | (TBD) | — | 학습 시작 |
| t=1 | (TBD) | (TBD) | (TBD) | |
| t=3 | (TBD) | (TBD) | (TBD) | |
| t=5 | (TBD) | (TBD) | (TBD) | Q1 누수율 |

### 판정

(TBD — 위 성공/실패 표 기준)

### 결정

(TBD)
