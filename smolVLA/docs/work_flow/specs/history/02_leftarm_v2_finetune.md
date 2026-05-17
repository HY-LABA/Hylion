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
- **🔀 2026-05-16 경로 변경 — image 변환 폐기 → prof_computer (일반 x86 GPU) 학습 이관**: M1.5 우회 시도 (image 변환·cleanup·GOP 재인코딩) 모두 폐기. 새 표준 [`docs/storage/prof_train_setting.md`](../../storage/prof_train_setting.md) 작성 + [`prof_computer/`](../../../prof_computer/) 디렉토리 신설 (Windows 10 + WSL2 + RTX 3090). DGX 학습 책임 일시 이관.
- **✅ 2026-05-17 prof_computer 학습 완주** (M1.5 중간점검): 100ep subset (`[0..99]`) · LoRA r=16 all-linear · batch 4 fp32 · **75000 step** · 7시간 34분 · **loss 0.04 수렴** · VRAM peak 60.7%. HF Hub push 완료: [`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`](https://huggingface.co/BaboGaeguri/leftarm_v2_A2_pc_2026-05-17) (LoRA adapter 125MB). 상세: [`prof_computer/docs/learning_log.md`](../../../prof_computer/docs/learning_log.md).
- **현재 사이클 범위 (2026-05-17~)**: TODO-03 (Orin smoke 추론) **only**. 위 prof_computer ckpt 로 두 task instruction 별 정성 추론. TODO-02 는 prof_computer 학습으로 *대체 충족* — DGX 본 학습 (TODO-02 원안) 은 M2 본 학습 (TODO-04·05) 사이클로 미룸. TODO-04·05 는 본 spec 에 보존하되 **본 사이클 범위 외** (M1 잔여 100ep 수집 완성 후 별도 사이클 진입).

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

### [x] TODO-02: 2A 학습 실행 + 체크포인트 smoke — **M1.5 우회 (prof_computer) 로 대체 충족 (2026-05-17)**

> **DGX 학습 (원안) → prof_computer 학습 (대체)**: DGX 시도 1·2 OOM (pyav buffer leak) → M1.5 결정 (2026-05-16, prof_train_setting.md) → prof_computer (WSL2 + RTX 3090) 에서 학습 완주.
> 원안의 *DGX 본 학습 (200ep, 20K step, batch 16)* 은 본 TODO 범위 밖으로 이관 — 본 spec 의 TODO-04 (2B 본 학습) 사이클에서 *200ep 완성 후* 진행. 본 TODO 는 M1.5 *중간점검* 학습 (100ep subset, 75K step, batch 4) 으로 *부분 대체 충족*.

- 실 산출:
  - ckpt: HF Hub [`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`](https://huggingface.co/BaboGaeguri/leftarm_v2_A2_pc_2026-05-17) (LoRA adapter 125MB)
  - 학습 메트릭: 75000/75000 step 완주 · loss 0.04 수렴 · grad_norm 안정 (0.55-0.65) · VRAM peak 60.7% · 7시간 34분
  - 시스템 메트릭: System RAM 누수 0.18 GB/h (DGX 시도 2 의 1660× 감소 — M1.5 prereq 가설 직접 증명)
  - run name: `leftarm_v2_2a_pc_2026-05-17_12-51-51` · wandb `babogaeguri-hanyang-university/leftarm_v2`
- 검증 절차: prof_computer 학습 종료 후 사용자 측 ckpt push 확인 + HF Hub 접근 가능 ([learning_log.md](../../../prof_computer/docs/learning_log.md) §M1.5 중간점검 학습).
- 차이 (원안 대비):
  - 노드: DGX → prof_computer (M1.5 결정으로 학습 책임 일시 이관)
  - subset: 200ep → 100ep subset (M1 잔여 100ep 미수집)
  - step: 20K (batch 16) → 75K (batch 4) — sample 수 동등 (300,000)
  - dtype: 미명시 → fp32 (smoke 3 에서 bf16 효과 없음 확인 → 변수 제거)
- 잔여 리스크 (TODO-03 에서 점검): n_action_steps 함정 (prof_train_setting §7-5), config.json 의 정책 키 정합성 (rename_map 학습 시 적용된 → 추론 시 동일 매핑 필요).

### [x] TODO-03: 2A 체크포인트 Orin 추론 + 성능평가 (success rate) — **최종 완료 (2026-05-18)**

> **자동화 완료 (2026-05-18)**: 모든 sub-step (03-A 평가 시트 / 03-B wrapper / 03-C cycle 3 Orin SSH 통합 검증 / 03-E F1·F2·F3 fix / 03-F leftarm_v2_inference.py 신규 + USER_OVERRIDE 옵션 W / 03-G peft 정식 추가 / 03-H rotation 정합 ad-hoc fix) 통과.
>
> **Phase 3 사용자 검증 (2026-05-18)**: 단축 trial (각 task front 1회 = 총 2 trial) 실시. 결과 0/2 = 0% — task1 ❌ 잡기 실패 (헛스윙), task2 ❌ 동작 불완전 (캔 방향 이동만). 정성: 동작 자체 부드러움 (하드웨어 이상 X), 정책 *판단력* 한계가 핵심. DGX cal 파일 transfer + cameras.json 채움 + max-steps 500→1000 ad-hoc 조정 모두 진행됨.
>
> **DOD (d) 충족**: M2 본 학습 진입 가치 정량 판단 → **0-20% 영역 확정**. 단순 200ep 본 학습 직진 X. 학습 방법 점검 + 데이터셋 확장 (개수·다양성) 필요. 다음 사이클 Phase 1 결정 영역: (1) 학습 방법 (LoRA·VLM·epoch·lr), (2) 데이터셋 확장 (M1 잔여 + 다른 사람 + orientation 균형 + 위치 분포), (3) 학습 노드 (prof_computer vs DGX), (4) 검증 시점 패턴.
>
> **인프라 검증 부가 가치**: Orin SSH·deploy·lerobot trim·LoRA 로드·cal·rotation·camera config 파이프라인 모두 *작동* 확인. 다음 사이클은 데이터·학습 방법 만 바꾸면 됨 (인프라 재작업 X).
>
> **평가 시트**: [`prof_computer/docs/orin_a2_eval_2026-05-17.md`](../../../prof_computer/docs/orin_a2_eval_2026-05-17.md).

> **입력**: TODO-02 의 prof_computer ckpt ([`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`](https://huggingface.co/BaboGaeguri/leftarm_v2_A2_pc_2026-05-17), HF Hub).
> **변경 (2026-05-17 사용자 결정)**:
> - ckpt 전송 경로 DGX→Orin (원안) → **HF Hub→Orin**.
> - ~~명령 형태: `lerobot-record` + `--policy.path` (prof_train_setting §5-3).~~ **폐기 (2026-05-18 00:05 USER_OVERRIDE)** — Orin trim 정책 (inference-only) 과 lerobot-record (수집 명령) 본질적 양립 불가. F1·F4·F5·F6 연쇄 ImportError 노출 (`lerobot.common.control_utils`, `lerobot.datasets`, `lerobot.teleoperators.keyboard`, `lerobot.cameras.reachy2_camera`).
> - **신규 entry**: `orin/inference/leftarm_v2_inference.py` (신규 파일, 마일스톤 v2 전용). `hil_inference.py` 갱신 X (사전학습 ckpt 책임 보존). 학습 ckpt + LoRA adapter 로드 + rename_map 적용 + task instruction 인자.
> - 평가 격상: 정성 관찰 (원안 *smoke*) → **정량 success rate 측정**. M3 영역 일부를 본 사이클로 당김.

- DOD:
  - (a) Orin 에서 ckpt 다운로드 + 사전 점검 (n_action_steps · config.json 키 정합성).
  - (b) Orin venv (`~/smolvla/orin/.hylion_arm`) 에서 lerobot-record eval 모드로 **두 task instruction 별** 정책 실행. dry-run → live 단계 진행.
  - (c) **성능평가 (success rate)** — 시나리오: **task1 5회 × {front, back} + task2 5회 × {front, back} = 각 10 trial, 총 20 trial, 1명 (사용자 본인)**. 각 trial 의 *성공/실패* 수동 카운트. 산출: task1·task2 별 success rate (M/N) + orientation 별 breakdown + 정성 메모 (실패 원인 분류).
  - (d) 결과로 *M2 본 학습 (200ep) 진입 가치* 정량 판단 — success rate 가 (예) 50% 이상이면 데이터 추가 가치 명확, 0~20% 이면 데이터·하이퍼파라미터·추론 환경 어디가 병목인지 재정렬 필요.
- 구현 대상:
  - Orin ckpt 다운로드: `huggingface-cli download BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 --local-dir ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17` (prof_train_setting §5-2).
  - n_action_steps 함정 점검: `grep "n_action_steps" ~/smolvla/orin/checkpoints/<run>/config.json` — `1` 이면 `50` 으로 수정 (prof_train_setting §7-5).
  - rename_map 정합 점검: 학습 시 `top→camera1`, `wrist→camera2` 적용됨. 추론 시 `lerobot-record` 의 dataset 키와 정합 — 학습 시 ckpt 가 `observation.images.camera{N}` 기대.
  - **신규 entry 작성**: `orin/inference/leftarm_v2_inference.py` — `hil_inference.py` 패턴 참조 + 학습 ckpt + LoRA adapter 로드 + rename_map (`top→camera1`, `wrist→camera2`) + task instruction 인자 (task1/task2).
  - 추론 명령 wrapper: `orin/scripts/run_inference_leftarm_v2.sh` 재조정 — lerobot-record 호출 → `python ~/smolvla/orin/inference/leftarm_v2_inference.py` 호출.
  - 두 task instruction 정의 — collection_log 의 task1·task2 instruction 본문 확인 후 명령 인자로 전달.
  - **평가 시트** — `prof_computer/docs/orin_a2_eval_2026-05-17.md` (또는 동등 위치) 신설: trial 번호 × {task, orientation, 성공·실패, 실패 원인 메모} 표. 사용자가 시연 중 직접 기록.
- 테스트:
  - **AUTO_LOCAL/SSH_AUTO**: ckpt 다운로드 성공 + config.json 점검 + dry-run mode 1-2 step 동작 + lerobot CLI 인자 정합 (`--policy.path`/`--policy.device`/instruction 인자).
  - **PHYS_REQUIRED**: 사용자가 실 Orin + 좌측 SO-101 으로 두 task instruction × 5회 × {front, back} = 총 20 trial live 추론. 각 trial 성공·실패·실패 원인 시트 기록. verification_queue 에 success rate 결과 입력.
- 제약:
  - 추론 fps·latency 자체는 본 사이클 *2차 메트릭* (필요 시 lerobot eval 자동 출력 기록만). 본 사이클 *1차 메트릭* = success rate.
  - `orin/checkpoints/`·`orin/config/*.json` 은 Orin 실 자산 — deploy_orin.sh `--delete` BACKLOG #1 미해결 상태이므로 본 사이클 동안 `deploy_orin.sh` 호출 X (ckpt 다운로드는 SSH 로 Orin 에서 직접).
  - 추론 명령은 사용자 시연장 환경 의존 (카메라 인덱스·port·flip 설정).
  - 시연장 소요 시간 1-2시간 예상 — 시연장 이동 일정과 충돌 회피.
- 잔여 리스크: 100ep + 6:4 편향 데이터로 두 task 다 약할 수 있음. 0~20% success rate 도 *결과로서 의미* (M1 잔여 수집 + 균형 보정 + M2 본 학습으로 진입 결정 근거).

> 본 todo 완료 후 → **M1 spec (01) 의 잔여 수집**: task 1 +50ep (front+20 / back+30), task 2 +40ep (인혁이형 back / 새 사람 C 등). `collection_log.md` §다음 차수 계획. **M2 spec 의 todo 아님** — M1 의 TODO-03 연장.

### [ ] TODO-04: 2B 학습 구성 갱신 + 200ep 학습 실행 — **본 사이클 범위 외 (M1 잔여 100ep 수집 완성 후 별도 사이클)**

- DOD: 2A 추론 관찰 결과 반영해 2B 학습 구성 갱신 (필요 시 LoRA rank · steps · lr · batch 조정). 200ep 전체 (task1: 100 + task2: 100) 학습 실행 → 체크포인트 산출 + smoke.
- 구현 대상: `train_config.yaml` 2B 값으로 갱신. `run_train.py` 실행 (subset 인자 없이 전체 dataset).
- 테스트: TODO-02 동일 절차 (loss · throughput · 메모리 · ckpt 로드 smoke). 데이터량 ↑ 로 학습 시간 ↑ — wall-clock 모니터링.
- 제약: TODO-02 동일.
- 잔여 리스크: 학습 시간 ↑ → 시연장 이동 일정 충돌 위험. wandb 로 진행 추적 필수.

### [ ] TODO-05: 2B 체크포인트 Orin 추론 — M2 최종 — **본 사이클 범위 외 (TODO-04 이후 진입)**

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
