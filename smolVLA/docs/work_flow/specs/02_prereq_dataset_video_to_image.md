# 02_prereq_dataset_video_to_image

> 목표: lerobot 의 video dataset 학습 시 pyav 의 video decode buffer leak 으로 인한 system-wide OOM 을 회피 — `leftarm_v2` (video) 를 `leftarm_v2_image` (image) 로 변환해 M2 학습 진입 가능하게 한다.
> 환경: DGX Spark (변환 + 학습), devPC (스크립트 작성)
> 접근: devPC → `ssh dgx`
> 코드 경로: DGX `~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/` (원본 video dataset, **보존**), `~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/` (신규 image dataset)
> 로드맵: `realplaying.md` M1.5
> 작성: 2026-05-15

---

## 배경

### M1.5 의 발단

M2 의 2A 학습 시도 1·2 (2026-05-15, 상세 `dgx/docs/finetune/leftarm_v2/training_log.md`) 가 둘 다 **~28분 후 global OOM (system 95GB 증발, 5GB/min 누수)**. wandb·dmesg 진단:

- main lerobot-train process RSS **3.4 GB 안정** — main 안 자람
- system memory 선형 누적 (1차 patterns) — `task=code` (VSCode) 2회 OOM-kill 거쳐 lerobot-train 도달
- `CONSTRAINT_NONE / global_oom` — cgroup 한도 아닌 시스템 전체 부족 (UMA 128GB 단일 풀)
- 시도 2 (num_workers 8→2, prefetch 2→1, buffer 1/8) → 누수 30% 만 감소 → **dataloader workers 자체는 주범 아님**

### 진짜 원인 — lerobot 의 video decode 경로

- leftarm_v2 의 mp4 14개 *전부 h264* (ffprobe 실증, codec mix 가설 부정)
- 즉 **단일 codec 환경에서도 pyav 의 frame buffer 누적** = lerobot 의 video dataset 학습 시 pyav 사용 패턴 자체가 leak
- pyav 15.1.0 (최신) 인데도 발생 — pyav 자체 버그라기보다 *random-access seek 시 keyframe 부터 순차 디코딩* 패턴이 buffer release 안 함

### 대안 backend 모두 막힘

lerobot 지원 backend 3 종 (`docs/reference/lerobot/src/lerobot/datasets/video_utils.py`):

| backend | DGX 호환성 | 비고 |
|---|---|---|
| `torchcodec` | ❌ | aarch64 wheel 들 (0.11.x / 0.12.0) 모두 `torch 2.10 + FFmpeg 6` 와 ABI 미스매치 (`torch_from_blob` undefined symbol) |
| `video_reader` | ❌ | torchvision 소스 빌드 + `ffmpeg<4.3` 필요. DGX 의 FFmpeg 6 와 충돌 |
| `pyav` (현재) | ⚠️ | leak 발생 — 사용 중 |

→ DGX 의 PyTorch 2.10 + GB10 (cuda capability 12.1) + FFmpeg 6 조합이 *PyTorch 생태계 최신 stable 보다 앞서있어* video decoder 정비 불가.

### 결정 (잠정, 2026-05-15)

**video decode 자체를 회피 — image dataset 변환** (사용자 결정, 잠정).
- 원본 `leftarm_v2` 는 보존 (M1 수집 잔여 90ep 계속 진행 가능)
- 학습 전용 새 `leftarm_v2_image` 생성

### ⚠️ 결정 *검증 필요* — TODO-01 의 researcher 보고서가 선결

**본 결정 (image 변환) 은 cleanup 강화·lerobot patch·chunk 재인코딩·streaming 등 *대안을 미탐색* 한 상태에서 내려졌다.** 메인 + 사용자 검토 후 사용자 지적 (2026-05-15) — 큰 작업이 정말 최선인지 *체계적 진단 + 외부 사례 검색 + 해결책 비교* 가 선행되어야. 따라서 TODO-01 을 `researcher` 에이전트 호출로 재정의 — 보고서 verdict 에 따라 TODO-02·03 의 작업 내용이 *유지·재정의·폐기* 될 수 있다.

### 재사용성

- 변환 스크립트 채택 시: 향후 rightarm 등 다른 dataset 에 같은 문제 발생 시 재사용
- 다른 해결책 채택 시: 그 해결책의 적용 절차가 본 spec 의 산출물

### 미해결 차원 (Backlog)

- torchcodec ABI 호환 환경 정비 (PyTorch 다운그레이드 또는 FFmpeg 7 설치)
- lerobot upstream 에 video decode buffer leak 보고/patch
- 모두 *장기적* 정비 — 본 spec 의 우회로 단기 해소

---

## Todo

### [ ] TODO-01: 문제 명확화 + 해결책 비교 연구 보고서 (researcher 호출)

> 본 todo 는 `researcher` 에이전트 (`.claude/agents/researcher.md`, 2026-05-15 신설) 가 수행. **코드 작성 0**. 산출은 보고서. M2-A OOM 사고의 *진짜 원인* 과 *최선의 해결책* 을 직접 증거 기반으로 정리해 TODO-02 (실행) 의 입력으로 제공.

- DOD:
  - (a) **문제 명확화**: v1 (40ep, libsvtav1) 완주 vs v2 (110ep, h264) OOM 의 *변수 분리* — 데이터셋 크기 / codec / 환경 점유 (VSCode·Firefox·Claude Code agent) 중 결정타 식별. pyav leak 가설 *직접 증명 또는 부정*:
    - lerobot `src/lerobot/datasets/video_utils.py` 의 pyav 호출 패턴 코드 review (close/free 명시 여부, random-access keyframe 디코딩 로직)
    - lerobot upstream commit history 에서 video decode 메모리 개선 patch 검색
    - `num_workers=0` 실측 실험 *제안* (실행은 사용자 또는 task-executor)
  - (b) **외부 사례 검색**: HuggingFace forum, lerobot GitHub issues (`huggingface/lerobot`), pyav GitHub issues (`PyAV-Org/PyAV`), DGX Spark + lerobot 학습 사례, PyTorch 2.10 + GB10 (capability 12.1) 환경의 호환성 보고. 각 발견 사례를 우리 환경과의 정합성 (관련/부분/무관) 으로 평가.
  - (c) **해결책 비교 표**: 적어도 다음 6 옵션 비교 — 비용·위험·효과 가능성·Cat 분류·후속 영향:
    1. image dataset 변환 (현 잠정 결정)
    2. **환경 cleanup 강화** (VSCode/Firefox/agent 완전 종료 후 재시도) — *가장 가벼움, 미시도*
    3. lerobot `video_utils.py` 의 pyav 사용 패턴 수정 (fork 또는 monkey-patch)
    4. mp4 chunk size 조정 후 재인코딩 (per-decode buffer ↓)
    5. `--dataset.streaming=true` 시도 (lerobot streaming dataset)
    6. DGX 환경 다운그레이드 (PyTorch 2.9 또는 FFmpeg 7) — torchcodec 활성화
  - (d) **추천 + 근거**: 단일 추천 또는 다중 옵션 (사용자 결정 받기 위함). *최소 비용 검증* 제안 (큰 작업 전 작은 실험으로 가설 줄임 — 예: cleanup 강화 후 시도 3 만으로 OOM 안 나면 image 변환 불요).
- 구현 대상:
  - 보고서 → `docs/work_flow/context/research/m1.5_video_decode_oom.md` (researcher 가 Write)
  - 코드 변경 0
- 테스트: 보고서 §3 외부 검색 결과의 *원본 링크* 검증 (출처 명확), §4 비교 표 정합성 (Cat 분류 정확), §5 추천 근거가 §1~§4 의 증거에 기반.
- 제약: 코드 작성 0. WebSearch/WebFetch + read-only Bash (`git log`, `ls`, `grep`, `find`, `cat`) + Grep/Glob/Read 만. 활성 파일 수정 X.
- 잔여 리스크: 본 보고서가 *대안 추천* 시 TODO-02·03 의 작업 내용이 *재정의* 가능 (변환 스크립트 아닐 수 있음).

> **researcher verdict 분기** (마지막 줄):
> - `NO_BLOCKER` → image 변환 결정 valid, TODO-02 그대로 진행
> - `RECOMMENDS_ALTERNATIVE` → 다른 해결책 추천, TODO-02 재정의 필요 (메인이 사용자 결정 받음)
> - `AMBIGUOUS` → 사용자 결정 (메인이 AskUserQuestion)
> - `NEEDS_INVESTIGATION` → 메인이 추가 실험 (cleanup 강화 등 최소 비용 검증) 또는 사용자 결정

### [ ] TODO-02: video → image 변환 스크립트 작성 + DGX 실행

> **선결 의존**: TODO-01 의 researcher 보고서 verdict 가 `NO_BLOCKER` 또는 `RECOMMENDS_ALTERNATIVE` 에서 *image 변환 채택* 일 때만 본 todo 그대로 진행. 다른 해결책 (cleanup·patch·streaming 등) 추천 시 본 todo 는 *재정의* 또는 *폐기* — 메인이 사용자와 함께 spec 갱신.

- DOD:
  - (a) `dgx/finetune/leftarm_v2/convert_to_image.py` 신규 — pyav 또는 ffmpeg 로 원본 mp4 frame 추출, parquet 재작성, meta/info.json 갱신. lerobot 의 `_keep_episodes_from_video_with_av` (line 576) + `convert_image_to_video_dataset` (line 1648) 패턴 참조.
  - (b) DGX 실행 — 원본 `leftarm_v2` → 새 `leftarm_v2_image` (원본 무손상). 110ep 전체 변환.
  - (c) 새 dataset 디스크 사용량 측정·기록.
- 구현 대상: `dgx/finetune/leftarm_v2/convert_to_image.py`.
- 테스트: 변환 후 새 dataset 의 `LeRobotDataset(...)` 로드 가능 검증 — `image_keys` 인식, frame shape·dtype 정합, episode/frame count 원본과 일치.
- 제약: 원본 dataset 손상 금지 (사본 작업, 새 path). lerobot dataset format 정확히 맞춤.
- 잔여 리스크: lerobot dataset format 정확히 못 맞추면 학습 시 dataset 로드 실패. TODO-01 의 분석 정확성에 의존.

### [ ] TODO-03: train_config / run_train.py 갱신 + 시도 3 학습 진입

- DOD:
  - (a) `dgx/finetune/leftarm_v2/config/{base,train}_config.yaml` 갱신 — dataset repo_id/root 가 `leftarm_v2_image` 가리키도록. `dataset.video_backend` 인자 무의미해지므로 제거 또는 무시.
  - (b) `run_train.py` 검토 — image dataset 인식 자동 (lerobot 가 features dtype 으로 판단). 명령 구성에 변경 필요 시 갱신.
  - (c) `--dry-run` 검증 — 새 dataset 으로 명령 정합.
  - (d) **시도 3 학습 진입** — DGX 에서 실행. 첫 ckpt (save_freq=1000 step) 도달 + OOM 없음 확인. wandb run URL 기록.
- 구현 대상: `train_config.yaml`, 필요 시 `run_train.py`.
- 테스트: dry-run + DGX 실 학습 (PHYS_REQUIRED — 학습 진입 사용자 직접). 첫 1000 step 의 wandb system memory peak / data_load_time / step_time 기록.
- 제약: **시도 1·2 와 변수 비교 가능하게** — 학습 인자 (`steps=20000`, `batch=16`, LoRA r=16 등) 는 시도 2 그대로 유지. `video → image` 변경 *만* 적용해 결과 해석 깔끔.
- 잔여 리스크: image dataset 학습이 OOM 안 나도 다른 issue 가능 — image loading 이 video decode 보다 *느릴* 가능성 (디코딩 오버헤드 없지만 디스크 I/O ↑), memory pattern 이 video 와 다른 새 leak 패턴 발생 가능.

---

## Backlog

> 본 spec 진행 중 발견된 추후 과제. 본 사이클 블로킹 X.

| # | 항목 | 발견 출처 | 우선순위 |
|---|------|-----------|----------|
| 1 | torchcodec ABI 호환 환경 — PyTorch 2.9 다운그레이드 또는 FFmpeg 7 설치로 video dataset 학습 가능하게 (장기적 정공법) | M1.5 작성 (2026-05-15) | 낮음 |
| 2 | lerobot upstream 에 video decode buffer leak issue 보고/patch 시도 | M1.5 작성 (2026-05-15) | 낮음 |
| 3 | 변환 스크립트의 *incremental* 모드 — 200ep 완성 후 M1 잔여 90ep 만 추가 변환 (전체 재변환 회피) | M1.5 작성 (2026-05-15) | 중간 (M2-B 진입 전 필요) |
| 4 | run_train.py preflight 가드레일 (MemAvailable < 80GB 경고) — 이전 backlog 항목 유지 | training_log.md §시도1 | 중간 |
