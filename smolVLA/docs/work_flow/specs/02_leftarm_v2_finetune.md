# 02_leftarm_v2_finetune

> 목표: leftarm_v2 dataset 으로 SmolVLA 멀티태스크 정책을 fine-tune. **2 패스 구조** — 2A (현재 110ep 중 task 50:50 = 100ep balanced) → 추론 smoke → M1 잔여 수집 → 2B (200ep 완성) → 추론 smoke.
> 환경: DGX Spark 학습 (venv `~/smolvla/dgx/.arm_finetune`) + Orin 추론 smoke (venv `~/smolvla/orin/.hylion_arm`)
> 접근: devPC → `ssh dgx` / `ssh orin`
> 코드 경로: DGX `~/smolvla/dgx/finetune/leftarm_v2/`, Orin `~/smolvla/orin/`
> 로드맵: `realplaying.md` M2
> 작성: 2026-05-15

---

## 배경

- **M1 (spec 01) 진행 중** — leftarm_v2 dataset 200ep 목표 수집 중. **2026-05-15 현재 110ep** (task1: 50 / task2: 60). 차수 로그: [`dgx/docs/finetune/leftarm_v2/collection_log.md`](../../../dgx/docs/finetune/leftarm_v2/collection_log.md).
- **M2 = 두 패스로 분할**:
  - **2A — 100ep first pass**: 현재 dataset 에서 **task1: 50ep + task2: 50ep = balanced 100ep** 로 학습 1회 → 체크포인트 → Orin smoke 추론. 목적: **사이클 검증 + 조기 성능 관찰** → 200ep 추가 수집 가치 판단.
  - **2B — 200ep second pass**: M1 완성 (task1: 100 / task2: 100) 후 재학습 → 재추론. M2 최종 산출.
- **v1 학습 이력** — `lerobot/smolvla_base` + LoRA (`r=16`, `all-linear`), batch 16, 의도 5000 step 중 500 step 조기 중단, adapter 46MB (run `leftarm_v1_explore_2026-05-11_17-04-20`). 2A 출발점.
- **결정 포인트 (M2 작성 시)**: 모델 구성 — `smolvla_base` 기반 / LoRA 적용 여부·rank / 하이퍼파라미터 / 학습 step 수. v1 의 LoRA 구성을 출발점으로, 2A 의 안정성·수렴 관찰 후 2B 재튜닝.
- **DGX 학습 산출 위치** — `~/smolvla/dgx/outputs/<run>/` flat 컨벤션 (`dgx/docs/finetune/leftarm_v1/training.md`, `leftarm_v1/data_collection.md` 기준; 옛 `outputs/train/` 혼재 정리됨).
- **DGX→Orin 체크포인트 전송 절차** — `docs/storage/06_dgx_venv_setting.md` §9.
- **🚧 2026-05-15 진행 정지 — M1.5 (`02_prereq`) 신설 후 학습 재진입**: M2-A 시도 1·2 가 둘 다 system-wide OOM (lerobot 의 video dataset 학습 시 pyav buffer leak, codec/workers 무관). 상세 [`dgx/docs/finetune/leftarm_v2/training_log.md`](../../../dgx/docs/finetune/leftarm_v2/training_log.md). 해결책: video → image dataset 변환 ([`02_prereq_dataset_video_to_image.md`](02_prereq_dataset_video_to_image.md)). 본 spec 의 TODO-02 (2A 학습 실행) 는 M1.5 완료 후 진입.

---

## Todo

### [x] TODO-01: 2A 학습 구성 확정 + 100ep balanced 서브셋 정의 — **완료 (2026-05-15)**

> **완료 (2026-05-15)**: 사용자와 Phase 1 대화로 학습 방법·subset·subset 지정 방법 확정. `train_config.yaml` 갱신·`model_config.md` 신규 작성·`run_train.py` 신규 작성·dry-run 정합 검증 완료 (v1 lerobot-train 명령과 인자 정합, `--peft.*`/`--rename_map`/`--policy.{device,push_to_hub}` 모두 v1 패턴 일치).

- DOD:
  - (a) **2A 학습 구성 결정** — **완료**: A2 (LoRA all-linear, r=16) / batch 16 / steps 20,000 / save_freq 1000 / wandb enable / smolvla 기본 lr·optimizer. 4축 매트릭스 [LoRA/Full FT] × [VLM frozen/trainable] 분석 후 A2 채택 (v1 검증값 + step 만 0.13 → 5.3 epoch 로 ↑). 상세·근거: [`dgx/docs/finetune/leftarm_v2/model_config.md`](../../../dgx/docs/finetune/leftarm_v2/model_config.md).
  - (b) **100ep balanced 서브셋 정의** — **완료**: **P 방식** — task 1 ep [0..49] + task 2 ep [50..99] = ep 0~99 연속. 양 task 모두 front:back = 30:20 (6:4 동일 편향, task 간 비교 깔끔). 진짜 균형(25:25) 은 task 2 back 5ep 부족이라 추가 수집 필요 → 2A 는 P 로 진행, 2B 에서 자연히 균형.
  - (c) **lerobot-train episode subset 지정 방법** — **완료**: `docs/reference/lerobot/src/lerobot/configs/default.py:33` 의 `episodes: list[int] | None` 사용. `--dataset.episodes='[0,1,...,99]'` draccus 인자로 직접 전달. 별도 subset dataset 생성 불필요.
- 구현 대상:
  - `dgx/finetune/leftarm_v2/config/train_config.yaml` — **갱신 완료** (2A 값 + dataset_subset_2a range).
  - `dgx/finetune/leftarm_v2/run_train.py` — **미작성**: config 읽어 `lerobot-train` 명령 구성·실행. `run_record.py`·`run_teleop.py` 패턴 (`_lib.py` 헬퍼). `dataset_subset_2a.episode_ranges_inclusive` 를 list 로 expand 해 `--dataset.episodes` 로 전달. lerobot-train draccus 인자 경로 (`--policy.*`/`--training.*`/`--wandb.*`/`--output_dir`) 정합 검토 후 작성.
  - `dgx/docs/finetune/leftarm_v2/model_config.md` — **신규 완료** (4축 분석·A2 결정 근거·hyperparameter 상세·subset P 근거·2B 튜닝 계획·실행 기록 §).
- 테스트: `run_train.py --dry-run` 으로 구성된 lerobot-train 명령이 `--help` 와 정합한지 검토. 실 DGX 검증은 TODO-02.
- 제약: `docs/reference/` 수정 금지. lerobot-train draccus 인자 준수. 학습 산출 `outputs/<run>/` flat. base_config.yaml hardware/accounts 활용.
- 잔여 리스크: lerobot-train 의 정확한 draccus 인자 경로 (`--training.steps` 인지 `--steps` 인지 등) 는 `run_train.py` 작성 시 코드 조사 후 확정.

### [ ] TODO-02: 2A 학습 실행 + 체크포인트 smoke

- DOD: 2A 학습 완료. 학습 곡선·loss 메트릭 정상 (조기 발산 X). 체크포인트가 lerobot CLI (`--policy.path` 등) 로 로드 가능 (smoke).
- 구현 대상: `run_train.py` (TODO-01 산출물) 실행. wandb 로 학습 곡선 추적. 학습 후 체크포인트 로드 smoke (간단 import 또는 명령).
- 테스트: DGX 학습 실행 모니터링 (PHYS_REQUIRED — 장시간). 학습 첫 100 step 내 loss · throughput · 메모리 점검 (v1 의 500 step 조기 중단 / disconnect 이력 회피). wandb run · `outputs/<run>/` 산출물 확인. ckpt 로드 smoke.
- 제약: Walking RL GPU 점유 가능성 모니터링. DGX 시연장 이동 일정과 충돌 회피. 학습 산출은 `outputs/<run>/` flat.
- 잔여 리스크: disconnect / OOM / NaN — 학습 중간 정기 점검 필수. v1 의 push 크래시 같은 부수 이력도 재발 가능.

### [ ] TODO-03: 2A 체크포인트 Orin smoke 추론

- DOD: 2A 체크포인트가 Orin 으로 전송됨. Orin venv 에서 lerobot CLI 로 **두 task instruction 각각** 정책 실행 — 정책이 의도된 형태로 모터 명령을 내는지 시각적 확인 (정성 평가). "task 를 시도는 한다 / 두 task 구분이 보인다" 정성 관찰.
- 구현 대상: DGX→Orin 체크포인트 전송 (`docs/storage/06_dgx_venv_setting.md` §9 절차). Orin 추론 명령 (lerobot-record eval 모드 또는 동등).
- 테스트: PHYS_REQUIRED — 사용자가 실 Orin + 좌측 SO-101 으로 두 task instruction 별도 시도. 결과 정성 메모.
- 제약: Orin 메모리 (실 device) · 추론 fps 제약. 본 todo 는 *smoke* 라 성능 평가 목적 아님 (M3 본격 배포 영역).
- 잔여 리스크: 100ep 데이터로 두 task 다 약할 수 있음 — 본 todo 의 목적이 "사이클이 끝까지 도는가 + 데이터 추가 가치 판단" 임을 잊지 말 것. 결과로 200ep 추가 수집 의사결정.

> 본 todo 완료 후 → **M1 spec (01) 의 잔여 수집**: task 1 +50ep (front+20 / back+30), task 2 +40ep (인혁이형 back / 새 사람 C 등). `collection_log.md` §다음 차수 계획. **M2 spec 의 todo 아님** — M1 의 TODO-03 연장.

### [ ] TODO-04: 2B 학습 구성 갱신 + 200ep 학습 실행

- DOD: 2A 추론 관찰 결과 반영해 2B 학습 구성 갱신 (필요 시 LoRA rank · steps · lr · batch 조정). 200ep 전체 (task1: 100 + task2: 100) 학습 실행 → 체크포인트 산출 + smoke.
- 구현 대상: `train_config.yaml` 2B 값으로 갱신. `run_train.py` 실행 (subset 인자 없이 전체 dataset).
- 테스트: TODO-02 동일 절차 (loss · throughput · 메모리 · ckpt 로드 smoke). 데이터량 ↑ 로 학습 시간 ↑ — wall-clock 모니터링.
- 제약: TODO-02 동일.
- 잔여 리스크: 학습 시간 ↑ → 시연장 이동 일정 충돌 위험. wandb 로 진행 추적 필수.

### [ ] TODO-05: 2B 체크포인트 Orin 추론 — M2 최종

- DOD: 2B 체크포인트 Orin 배포 + 두 task instruction 추론. **2A 대비 개선 정성 비교** (수렴 품질). 두 task 모두 의미있는 수렴 관찰 — `realplaying.md` M2 DOD 충족.
- 구현 대상: 체크포인트 전송 + Orin 추론 (TODO-03 절차).
- 테스트: PHYS_REQUIRED — 사용자. 2A 와 **동일 조건** (인혁이형 / 성래 / orientation front·back 별) 추론 시도 → 2A vs 2B 비교 메모.
- 제약: TODO-03 동일.
- 잔여 리스크: 2A 대비 개선이 미미하면 데이터·하이퍼파라미터·추론 환경 어디가 병목인지 판단 필요 — M3 (배포) 진입 전 재정렬 가능성. BACKLOG 누적.

---

## Backlog

> 본 spec 진행 중 발견된 추후 과제.

| # | 항목 | 발견 출처 | 우선순위 |
|---|------|-----------|----------|
| 1 | (진행 중 누적) | — | — |
