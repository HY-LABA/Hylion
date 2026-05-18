# SmolVLA 단일팔 — 수집·학습·추론 사이클 로드맵 (leftarm_v2)

> 작성일: 2026-05-14
> 대체: 구 `arm_2week_plan.md` (→ `docs/storage/legacy/arm_2week_plan/` 아카이브). 본 문서는 fresh start 로드맵.
> 기한: 없음 — 단계별 완성 우선.

---

## 최종 목표 상태

접근 가능한 **dev 환경**(시연장이 아닌, 평소 작업 가능한 환경)에서 다음 전체 사이클을 돌려, **학습된 SmolVLA 정책이 실시간 추론으로 task 를 실제로 잘 수행**하게 만든다:

```
데이터 수집 → DGX 학습 → Orin 배포 → 실시간 추론으로 SO-101 이 task 수행
```

- **성공 기준 = 성능**: 사이클이 "돌아가는" 것이 아니라, 산출된 모델이 task 를 실제로 수행해 내는 것이 성공이다.
- **재현성**: 동일 task·동일 에피소드 개수·동일 절차로 사이클을 패키징해 둔다. 나중에 시연장 방문 시 **데이터만 새로 수집해 같은 절차를 마찰 없이 재실행** → 시연장에서도 좋은 성능을 재현하는 것이 목적.

---

## 핵심 전제

- **단일팔**: SO-101 좌측 single-arm. 양팔(bi-arm)은 본 로드맵 범위 밖. (우측팔 gesture 트랙은 별개 — 아래 참조)
- **데이터셋 계보**:
  - `leftarm_v1` — 구 task `"Pick up the doll and reach forward"` (40 episodes). **동결** — 개념적 체크포인트로 보존, 본 로드맵에서 끌어오지 않음.
  - `leftarm_v2` — **본 로드맵의 작업 대상**. 신규 2 task 멀티태스크 dataset (M1 에서 수집).
- **인프라 완료 간주**: 구 마일스톤 00~08 (Orin 추론 런타임, DGX 학습·수집 환경, SO-101 좌측 calibration) 은 완료로 보고 재구축하지 않는다. 필요 시 해당 마일스톤에서 재검증만.
- **VLA 정책**: SmolVLA (`smolvla_base` fine-tune 기반), 1 모델 / 다중 task (instruction 으로 구분). 구체 모델 구성은 M2 결정 포인트.
- **domain shift 인지**: SmolVLA 는 teleoperation 시연 모방학습 정책이라 fine-tune 데이터의 시각적 분포(조명·카메라 앵글·배경·물체 외형)에 성능이 민감하다. 그래서 dev 환경에서 좋은 성능을 먼저 확보하고, 시연장 데이터 재수집·재학습은 본 로드맵 이후로 분리한다.
- **별개 트랙 (로드맵 제외)**: 우측팔 gesture 시스템 (트리거 기반 replay), Berkeley Humanoid Lite 펌웨어 트랙 (`docs/storage/others/다리id다운/`).

---

## 장비 역할 분담

| 장비 | 역할 |
|---|---|
| devPC (Ubuntu) | 개발·배포 오케스트레이션, git 단일 진실 |
| DGX Spark | 데이터 수집 + 학습 (시연장 직접 이동 운영 가능) |
| Orin (Jetson) | 추론 실행·검증 |
| SO-101 좌측 | follower + leader (teleoperation 수집 / 추론 실행) |

---

## 진행 마일스톤

각 마일스톤은 Phase 1 에서 별도 spec 으로 분해된다 (milestone → spec → todo). M1~M4 = spec `01`~`04`. 아래는 milestone 계층의 골격.

### [ ] M1 — leftarm_v2 데이터 수집  (spec `01`)

- **목표**: leftarm_v2 학습용 dataset (2 task, 총 **400 episodes**) 을 dev 환경에서 수집·검증한다.
- **task (확정 2026-05-14)**: leftarm_v2 = 2 task 멀티태스크
  - ① 인형(doll) 을 집어 상자에 넣기
  - ② 캔(can) 을 집어 상자에 넣기
  - 한 SmolVLA 모델이 instruction 으로 두 task 를 구분해 수행 (M2).
- **에피소드 (2026-05-18 갱신)**: task 당 **200**, 총 **400** (fresh 수집 — leftarm_v1 끌어오지 않음). 100→200 조정 사유: researcher 추정 (300~500ep) 의 중간 영역 진입 + camera mismatch 확신 영역 도달 (자세한 근거: [prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md](smolVLA/prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md) 또는 본 사이클 대화).
- **주요 작업**:
  - leftarm_v2 dataset 설계 (task instruction 문자열 2종, dataset 구조, HF repo 명명, 에피소드 배분 200/200)
  - 수집 환경 최소 파라미터 기록 (카메라 위치·조명·작업영역 — 시연장 재현용 최소 셋) + 다양화 영역 (위치분포·조명·배경) 명시 기록 — 8차부터
  - 좌측 SO-101 + 카메라 calibration·포트·인덱스 재검증
  - teleoperation 으로 400 episodes 수집 → HF Hub push
  - dataset 검증 (400 ep, task 분포 200/200, frame shape·dtype)
- **결정 포인트 (M1)**: dev 수집환경 ↔ 시연장 정합 → **"최소 파라미터만 기록" 으로 결정 (2026-05-14)**. 카메라·조명·작업영역 핵심값만 기록하고 dev 환경 그대로 수집. *2026-05-18 보강*: vision encoder 의 task-irrelevant invariance 학습을 위해 위치분포·조명·배경 다양화 의식적 기록 ([collection_log.md §추가 다양화 영역](smolVLA/dgx/docs/finetune/leftarm_v2/collection_log.md) 참조).
- **DOD**: leftarm_v2 400 episodes (2 task × 200) 수집 완료 + HF Hub push + 검증 통과 → 학습 입력으로 사용 가능.
- **선택 중간점검 (권장)**: 200ep 시점에서 *M1.5 (100ep) 와 동일 학습 setup* 으로 1회 학습 + Orin 추론 — 데이터 양 효과 정량화 + 400ep 진입 가치 calibration.

### [ ] M1.5 — 데이터셋 학습 호환성 정비 (video decode 회피)  (spec `02_prereq`)

- **목표**: M2 학습 진입을 가능하게 — lerobot 의 video dataset 학습 시 pyav 의 video decode 자체 buffer leak 으로 인한 system-wide OOM 을 회피.
- **배경 (2026-05-15 발견)**: leftarm_v2 의 2A 학습 시도 1·2 가 둘 다 ~28분 후 global OOM (system 95GB 증발, 5GB/min 누수). wandb·dmesg 진단 결과:
  - main lerobot-train process 는 3.4 GB 안정 (안 자람)
  - leak 의 진짜 원인은 **lerobot 의 video dataset 학습 시 pyav 의 frame buffer 누적** — codec (h264 단일 확인) / num_workers (8→2 → 누수 30% 만 감소) / batch_size 와 모두 무관
  - 대안 backend 모두 막힘: `torchcodec` (aarch64 wheel 들이 PyTorch 2.10 + FFmpeg 6 와 ABI 미스매치 — DGX 의 PyTorch 2.10 + GB10 12.1 + FFmpeg 6 조합이 너무 신규), `video_reader` (torchvision 소스 빌드 + `ffmpeg<4.3` 필요 — 불가)
- **주요 작업**:
  - lerobot dataset API (image vs video format) 분석
  - video → image dataset 변환 스크립트 작성
  - 원본 `leftarm_v2` 보존 + 새 `leftarm_v2_image` dataset 생성
  - 변환된 dataset 의 lerobot-train 호환성 검증 (학습 진입 + 첫 ckpt 도달)
- **결정 포인트 (M1.5)**: lerobot video decode leak 회피 방식
  - 1차 결정 (2026-05-15): **"image dataset 변환"**. (대안: torchcodec 활성화, FFmpeg 업그레이드, lerobot upstream patch — 모두 DGX 환경상 비현실적이라 image 변환 채택.)
  - **2차 결정 (2026-05-16)**: 1차 결정 **폐기** → **"DGX 자체 학습 보류, 일반 x86 GPU 환경으로 이관"** (사용자 결정). image 변환·cleanup·GOP 재인코딩 등 우회로 산출물 모두 `docs/storage/legacy/realplaying/train_troubleshooting/` 로 이관. 가이드: [`docs/storage/prof_train_setting.md`](docs/storage/prof_train_setting.md).
- **DOD (2차 결정 반영)**: 일반 x86 환경 (= prof_train_setting §1 옵션 중 하나) 에서 `lerobot-train` 이 100ep subset 학습 진입 → OOM 없이 첫 ckpt 도달. 그 이상의 학습 완주·성능은 M2 의 책임.
- **본 사이클 결과 (2026-05-17)**: `smolVLA/prof_computer/` (RTX 3090 + WSL2, prof_train_setting §1 옵션 #1 인스턴스) 에서 **75000 step (5.5 epoch) 완주**. loss 0.04 수렴, VRAM peak 60.7%, RAM 누수 0.18 GB/h (DGX 시도 2 의 1.25 GB/min 대비 400× 감소). prereq spec 02 가설 ("torchcodec 정상 환경에선 DGX 의 OOM 메커니즘 재현 불가") 직접 증명. 산출물:
  - Local ckpt: `~/prof_computer_runs/leftarm_v2_2a_pc_2026-05-17_12-51-51/checkpoints/` (75개)
  - HF Hub: [`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`](https://huggingface.co/BaboGaeguri/leftarm_v2_A2_pc_2026-05-17) (LoRA adapter only, 46MB)
  - 상세: [smolVLA/prof_computer/docs/learning_log.md](smolVLA/prof_computer/docs/learning_log.md)
- **재사용성 노트**: 향후 rightarm 등 다른 dataset 도 prof_computer (또는 prof_train_setting §1 의 다른 옵션 — Colab/RunPod 등) 에서 동일 절차로 학습. DGX 의 aarch64 ecosystem 정비 (lerobot torchcodec aarch64 wheel 또는 PyTorch + FFmpeg ABI 정합) 전까지 prof_computer 가 학습 노드 대행.

### [ ] M2 — 학습 (DGX 또는 prof_computer)  (spec `02`)

- **목표**: leftarm_v2 dataset (M1 의 200 episodes 완성 후) 으로 SmolVLA 멀티태스크 정책을 fine-tune 한다 (1 모델 / 2 task).
- **학습 노드 선택** (M1.5 2차 결정 반영): DGX 의 aarch64 ecosystem 정비 전까지는 **prof_computer 우선**. DGX 가 정비되면 그쪽도 가능. M1.5 의 검증 학습 (100ep, 75k step) 은 prof_computer 에서 완주됨 — 동일 노드에서 200ep 으로 확장.
- **주요 작업**:
  - 모델 구성 결정 (M1.5 본 사이클의 검증 — LoRA r=16 / all-linear / batch 4 / steps 75000 / fp32 — 을 200ep 으로 확장. scheduler_decay_steps 동기화 적용)
  - prof_computer 또는 DGX 에서 학습 실행, 학습 곡선·메트릭 점검
  - 학습 산출 체크포인트 검증 (smoke / 로드 테스트)
- **결정 포인트 (M2)**: 모델 구성 — `smolvla_base` 기반 / LoRA 적용 여부·rank / 하이퍼파라미터 (구 `11_smolvla_model_decision` 주제). M1.5 검증값 (A2: LoRA all-linear r=16) 을 기본으로 하되 200ep 데이터 반영해 정밀 튜닝.
- **DOD**: 학습 완료, 체크포인트가 Orin 배포 가능한 형태로 산출, 두 task 모두에 대해 의미있는 수렴.

### [ ] M3 — 배포 + 추론 (Orin)  (spec `03`)

- **목표**: 학습 체크포인트를 Orin 에 배포하고 추론 파이프라인을 구동한다.
- **주요 작업**:
  - 체크포인트 DGX → Orin 전송
  - Orin 추론 파이프라인 구동 (카메라·SO-101 연결, 정책 로드 — LoRA adapter 케이스 시 로딩 검증)
  - 추론 latency·동작 기본 점검
- **결정 포인트 (M3)**: `orin/config/*.json` (포트·카메라) git 추적 정책 (구 `10_orin_config_policy` 주제).
- **DOD**: Orin 에서 정책 로드 + 실시간 추론 루프 동작 확인.

### [ ] M4 — E2E 검증 + 사이클 패키징  (spec `04`)

- **목표**: dev 환경에서 전체 사이클을 검증해 **모델이 두 task 를 실제로 수행**함을 확인하고, 시연장 재실행이 turnkey 가 되도록 절차를 패키징한다.
- **주요 작업**:
  - dev 환경에서 실시간 추론으로 SO-101 이 leftarm_v2 의 두 task 를 수행하는지 확인 (성공률 측정)
  - 수집→학습→배포→추론 전체 사이클 절차 문서화
  - 시연장 재실행 체크리스트 작성 (데이터만 교체하면 되도록)
- **DOD**: dev 환경 E2E 사이클 성공 (두 task 수행 확인), 재실행 절차 문서 완성.

---

## 결정 포인트 요약 (옛 결정 carry forward 금지)

아래는 구 `docs/storage/09·10·11` 이 다뤘던 주제 — fresh start 원칙상 **옛 결정 내용을 default 로 깔지 않고**, 해당 마일스톤 spec 작성 시 사용자에게 새로 질문한다. (메모리 `new-plan-decision-points` 참조. 옛 결정 내용은 git 히스토리에 보존.)

| 결정 포인트 | 배치 | 구 출처 | 상태 |
|---|---|---|---|
| dev 수집환경 ↔ 시연장 환경 정합 방식 | M1 | 구 09_demo_site_mirroring | ✅ "최소 파라미터만 기록" 으로 결정 (2026-05-14) |
| lerobot video decode 호환성 (pyav leak 회피 방식) | M1.5 | — (2026-05-15 발견) | ✅ "image dataset 변환" 으로 결정 (2026-05-15) |
| 모델 구성 (체크포인트·LoRA·하이퍼파라미터) | M2 | 구 11_smolvla_model_decision | ⚙️ 2A 학습 방법 (A2: LoRA all-linear) + subset (P) 결정 (2026-05-15). 정밀 hyperparameter 는 2B 시점 |
| `orin/config/*.json` git 추적 정책 | M3 | 구 10_orin_config_policy | 미결 — M3 spec 작성 시 질문 |

---

## 참고 — DGX 측 운영 문서

DGX 머신 `~/smolvla/dgx/docs/` 에 수집·학습 운영 상세 문서가 존재 (`status.md`, `data_collection.md`, `training.md`, `backlog.md` 등). 본 로드맵·spec 은 **milestone·todo 계층**, DGX docs 는 **수집·학습 운영 상세** — 역할이 다르다. devPC repo 와 DGX docs 사이 동기화 정책은 추후 정리 대상.

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-14 | 초안 작성 — fresh start 로드맵. 단일팔 / 기한 없음 / 인프라 00~08 완료 전제. |
| 2026-05-14 | 정정 — 최종 목표를 "재현성 검증" → **"실제 성능 확보 (+ 재현성)"** 로 수정. M1 을 현실 반영: task 확정 (leftarm_v2 = 2 task: 인형→상자, 캔→상자), 에피소드 100/task = 200, leftarm_v1(40ep) 은 동결 별개 체크포인트. M2 멀티태스크 1 모델 명시. M1 결정 포인트(환경 정합) "최소 파라미터만 기록" 으로 해소. DGX 운영 문서 참조 섹션 추가. |
| 2026-05-15 | M1 진행 중 task 정의 재정의 (인형→테이블 왼쪽 spatial reference, 캔→사람에게 hand-over) — top view 가동범위 제약 + task 다양성 확보 차원에서 "노란 플라스틱 상자" 폐기. 110ep (task1:50/task2:60) 시점에 M2-A (100ep balanced subset) 시도 진입. |
| 2026-05-15 | **M1.5 신설** — 데이터셋 학습 호환성 정비. M2-A 학습 시도 1·2 가 둘 다 ~28분 후 system-wide OOM. 진단 결과 lerobot 의 video dataset 학습 시 pyav 의 buffer leak (codec/workers 무관). DGX 의 PyTorch 2.10 + GB10 + FFmpeg 6 환경에서 torchcodec/video_reader 빌드 호환 불가 → **image dataset 변환** 을 정공법으로 채택. spec `02_prereq` 신규. M2 학습은 본 milestone 완료 후 재진입. |
| 2026-05-18 | **M1 목표 200→400ep 조정** (task 당 100→200). 사유: M1.5 추론 0/2 + researcher 보고서 ([prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md](smolVLA/prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md)) 의 데이터 양 추정 (300~500ep) 영역 진입 + camera mismatch 확신 영역 도달 (400ep 시점 데이터 부족 가설 신뢰도 ↑). 추가 도입: 수집 다양화 영역 (위치분포·조명·배경) — 8차부터 명시 ([collection_log.md §추가 다양화 영역](smolVLA/dgx/docs/finetune/leftarm_v2/collection_log.md)). |
