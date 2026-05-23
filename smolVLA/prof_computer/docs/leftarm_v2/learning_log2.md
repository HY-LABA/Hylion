# prof_computer — 학습 로그 2 (004+ 사이클)

> 📌 **현행 사이클** — 004 분기부터 본 파일에 누적.
> **출발점**: 003 (loss 0.0324, 8/8 = 100%, 5변수 종합) 으로 *base 학습 방법 유효성* 증명 완료. 본 파일부터는 *성능 향상* 영역.
> **이전 아카이브**: [learning_log1.md](learning_log1.md) — M1.5 ~ 003 사이클 (2026-05-21 freeze).
>
> ⚠️ **cold start 진입자 필독**: 본 파일은 *계층 3 분기 인스턴스* 의 실행 기록만 담음. *계층 1~2* (학습 방법·hp 인자) + 시간 라벨 (마일스톤) 의 정의는 [prof_computer/README §7 명명 3-계층 + 시간 라벨](../../README.md) 참조 — *반드시 본 파일 진입 전 1회독*.
>
> ---
>
> 본 노드 (Windows 10 + WSL2 + RTX 3090) 의 fine-tune 시도별 실행 기록.
> 결정 근거: [model_config.md](../model_config.md) — leftarm_v2/v3+ 공통 학습 방법론.

---

## 출발점 — 003 baseline 요약

> 본 사이클 (004+) 의 *비교 기준*. 상세는 [learning_log1.md §003 분기 학습](learning_log1.md).

| 항목 | 값 |
|---|---|
| HF Hub repo | [`BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`](https://huggingface.co/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6) |
| 분기명 | `003_a2_310ep_empty1_sched_sync_bf16_b6` |
| 학습 메트릭 | 120000 step / 4.38 epoch / **final loss 0.0324** / 16h 11m / VRAM peak 84.77% |
| 추론 평가 | **8/8 = 100%** (단축, 학습 분포 외 perturbation 4 trial 포함) — [`orin/docs/leftarm_v2/003_eval_2026-05-19.md`](../../../orin/docs/leftarm_v2/003_eval_2026-05-19.md) |
| 5변수 종합 (vs M1.5) | dataset 110→310ep · empty_cameras 0→1 · sched_sync 30k→120k · bf16 · batch 4→6 |

---

## 004+ 사이클 entry

> 새 분기 학습이 시작되면 본 섹션 하위에 entry 추가. §003 entry (learning_log1.md L570~) 양식 mirror 권장:
> - 분기 식별 + 변경 변수 + 가설
> - smoke 검증
> - 본 학습 (메트릭 표 + 시스템 메트릭 표)
> - HF Hub 검증
> - 추론 평가 결과 메모 (Orin eval 시트 링크)

---

### 004 분기 학습 — 2026-05-21 ~ 2026-05-22

> **분기 식별**: `004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180`
>
> **vs 003 변경 변수 1개**:
> 1) wrist camera 학습 시점 180° 회전 적용 (사전학습 분포 정합)
>
> 003 의 모든 인자 유지 (310ep · empty_cameras=1 · scheduler_decay_steps=120000 · bf16 · batch 6 · steps 120000).
>
> **가설**: SmolVLA base VLM (SigLIP) 의 natural image 사전학습 prior 가 *상하반전 입력* 에 약함. 우리 wrist 카메라 = SO-101 그리퍼 마운트로 *상하반전 상태* 수집됨 → upright 정렬 시 base prior 활용 ↑ 기대.
>
> **근거**: [`research_wrist_orientation_2026-05-21.md`](research_wrist_orientation_2026-05-21.md) (verdict: NEEDS_INVESTIGATION)
> - VLM 의 180° 입력 catastrophic drop 정량 (Claude 97→27.9%, GPT-4o 97→24.9%)
> - lerobot 의 `Cv2Rotation` 파라미터 = 수집 단계 보정 표준 워크플로우 정황
> - 시각 검증: 원본 wrist 가 *상하반전 자세* (인형 거꾸로 매달림 등), patch 후 자연 방향 복원 — rotation_check_image/ 3 trial 보존
>
> **구현 경로**: lerobot upstream 의 `image_transforms` API 가 *카메라별 selective* 미지원. `custom_train.py` 가 `LeRobotDataset.__getitem__` 에 monkey-patch 적용 (5줄) — `observation.images.wrist` 키만 `TF.rotate(180)`. lerobot upstream 무수정 (옵션 B 보존), lerobot-train 의 모든 흐름 (PEFT, accelerate, wandb, ckpt, scheduler) 재사용.

#### smoke 검증 (2026-05-21)

2회 진행 — *patch 대상 키 정정* 후 통과:

| smoke | 패치 대상 | 결과 | 사유 |
|---|---|---|---|
| smoke 1 | `observation.images.camera2` (rename 후 key) | ⚠️ 100/100 step 완주 — 단 patch 실제 미적용 | rename_map 이 `__getitem__` *밖에서* 적용됨 → patch 매칭 실패. loss 003 smoke 와 동일 |
| smoke 2 | `observation.images.wrist` (rename 전 원본 key) | ✅ PASS — patch 정상 작동 | 수치 검증: `patched ≡ manual_rotate(180)` 완벽 일치 (diff 0.000000). 시각 검증 (5 frame grid) 도 회전 확정 |

→ patch 키 정정 후 본 학습 진입.

#### 본 학습 — 2026-05-21 14:51 ~ 2026-05-22 ~09:34 · ✅ COMPLETED (120000 step 완주)

- 명령: `python run_train.py train --pass full` (`accelerate launch --mixed_precision=bf16 custom_train.py ...`)
- run name: `leftarm_v2_004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180_full_2026-05-21_14-51-42`
- output_dir: `~/prof_computer_runs/leftarm_v2_004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180_full_2026-05-21_14-51-42/`
- HF Hub push: 예정 (`BaboGaeguri/leftarm_v2_004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180`)

**학습 메트릭** (실측 — `metrics.scalar.csv` 추출):

| 지표 | 값 |
|---|---|
| 시작 / 종료 | 2026-05-21 14:51 / 2026-05-22 ~09:34 KST |
| 총 시간 | **18h 42m 45s** (63705 s) |
| 도달 step | 120000 / 120000 (100%) ✅ |
| 도달 sample | 720,000 |
| epoch | 4.38 |
| step time (avg) | **0.526 s/step** (update 0.521 + dataload 0.006) |
| final loss | **0.0375** |
| loss steady (last 20K, n=401) | min 0.009 / avg 0.044 / max 0.171 |
| grad_norm 후반 (last 20K) | 0.41 ~ 0.57 |
| lr 마지막 | 2.5e-6 (cosine min — scheduler_decay_steps=120000=steps, 전 구간 decay) |
| ckpt 저장 | **60개** (save_freq=2000, step 010000~066000) |
| last ckpt 크기 | **124.32 MB** (optimizer state 80MB + LoRA adapter 44MB + meta) |

**시스템 메트릭** (실측 — `metrics.system.csv`):

| 지표 | 값 |
|---|---|
| VRAM peak | **81.77%** (~20.20 GB / 24 GB) — 003 84.77% 대비 -3%p (더 안정) |
| VRAM avg | 80.15% |
| GPU power | avg 345W / max 360W |
| GPU util | avg 77% / max 96% |
| GPU temp | peak **83°C** (avg 81°C) |
| System Memory | avg 19.1% / max 20.5% |
| Process RSS | 1392 MB → 2169 MB (peak 2279 MB) |
| RAM 누수율 | **0.043 GB/h** (778 MB / 17.83h — 003 의 0.062 GB/h 대비 ↓) |
| Disk delta | **+9.92 GB** (96.63 → 106.56 GB — 60 ckpt × 124MB + wandb cache) |

#### vs 003 baseline 비교 — 학습 메트릭 차원

| 지표 | 003 baseline | **004 (+ wrist_rot180)** | 차이 |
|---|---|---|---|
| 총 시간 | 16h 11m | **18h 42m** | +15.5% (TF.rotate overhead) |
| step time | 0.481 s | **0.526 s** | +9.4% |
| final loss | 0.0324 | **0.0375** | +16% (004 약간 ↑) |
| loss steady avg | 0.044 | **0.044** | 동등 |
| loss steady min | 0.010 | **0.009** | 거의 동등 (004 약간 ↓) |
| grad_norm 후반 | 0.42-0.55 | **0.41-0.57** | 동등 |
| VRAM peak | 84.77% | **81.77%** | -3%p (004 안정) |
| RAM 누수율 | 0.062 GB/h | **0.043 GB/h** | -31% (004 ↓) |
| ckpt 크기 | 124.32 MB | **124.32 MB** | 동등 |

→ **학습 메트릭 차원에선 003 과 거의 동등** (final loss 만 약간 ↑, steady 영역 동등). VRAM/RAM 누수는 004 가 더 안정. **wrist 회전 정합 효과의 *결정적 검증* 은 Orin 시연장 평가** — 학습 fit 수준에선 차이 보이지 않음.

#### 다음 단계

- [ ] **HF Hub push** — `BaboGaeguri/leftarm_v2_004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180`
- [ ] **Orin 추론 평가** — 003 과 동일 시나리오 단축 평가 (task1·task2 front/back). cameras.json wrist rotation 을 학습-추론 정합 위해 *+180 상쇄* 적용 필요
- [ ] **`orin/docs/leftarm_v2/004_eval_2026-05-22.md`** 신설 — 평가 시트 (003 양식 mirror)
- [ ] **결과 분기**:
  - 003 보다 유의미 ↑: 사전학습 prior 활용 효과 확정 → 학습 input 분포 정합 우선순위 ↑
  - 003 와 비슷: 003 의 적응이 이미 충분 — null result, 정보 가치 있음
  - 003 보다 ↓: 학습 분포 변경 비용 > 사전학습 prior 이득 — 시도 가치 영역 재검토

#### 본 분기 의의

학습 결과와 무관하게 본 분기가 확보하는 *방법론적 가치*:

1. **단일 변수 비교 가능** — 003 과 hyperparameter 100% 동일, 단일 변수 (wrist 180°) 만 차이. 결과 해석 깔끔.
2. **lerobot upstream 무수정** — monkey-patch 경로 (5줄) 로 옵션 B 정책 준수 + custom_train.py 자체는 분기 한정 격리.
3. **wrist 회전 가설 검증 기준점** — 003 baseline 의 *상하반전 wrist 학습* vs 004 의 *upright wrist 학습* 직접 비교 (시연장 평가에서 결정적 차이 측정).
4. **patch 키 정정 사고 학습** — smoke 1 에서 *rename 시점 가정 오류* (rename_map 이 `__getitem__` 안에서 적용된다고 잘못 가정) 로 patch 미적용 발견 → smoke 2 에서 원본 키 (`wrist`) 로 정정 + 수치/시각 검증 완료. 다음 분기 patch 작성 시 *수치 검증 (manual_rotate 와 diff)* 패턴 표준화 가치.
