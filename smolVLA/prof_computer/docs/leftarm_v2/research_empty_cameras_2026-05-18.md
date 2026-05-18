# Research Report — SmolVLA `empty_cameras` 와 2-cam fine-tune 의 base 분포 정합성

> 작성: 2026-05-18 | researcher
> 호출자: 메인 — M1.5 (0/2 실패) 사후 분석 + 진행 중인 camera_empty 분기 학습 (~8h) 의 시간 가치 판단 + 3번째 카메라 추가 수집 우선순위 결정
> 관련 spec: [`prof_computer/docs/model_config.md`](../model_config.md)
> 관련 사이클: M1.5 (2026-05-17) — [learning_log.md](learning_log.md), [orin_a2_eval_2026-05-17.md](orin_a2_eval_2026-05-17.md), [orin_base_eval_2026-05-17.md](orin_base_eval_2026-05-17.md)
>
> **사후 메모 (2026-05-19 추가)**: 본 보고서 작성 시점 *진행 중* 이었던 분기 학습 (002_a2_100ep_empty1, run `8jkr7edb`) 은 2026-05-18 19:25 완주 (9시간 22분, 75000/75000 step). Orin 추론 비교 평가는 별도 사이클. 본 보고서의 *시점* 표현 (진행 중, ~8h 등) 은 *2026-05-18 오전 분석 시점* 기록으로 유지 — 결과 갱신은 [learning_log.md §camera_empty 본 학습](learning_log.md) 참조.
> 기존 자료 (중복 작업 회피): `smolVLA/docs/work_flow/context/history/02_prereq_dataset_video_to_image/research/lerobot_smolvla_training_best_practice.md` (학습 best practice 일반 — 본 보고서는 그 보고서의 *카메라 수 mismatch 공백 영역* 보강)

---

## §1 문제 정의

### 1-1. 호출자의 현재 가설

호출자 (메인) 가 사이클 도중 도달한 가설:

1. **upstream base `lerobot/smolvla_base` 의 Hub `config.json`** 이 `input_features` 에 `observation.images.camera1/2/3` *3 cam* 으로 정의돼 있음 + `empty_cameras: 0` default.
2. **우리 dataset 은 top + wrist 2 cam** (rename_map 으로 `camera1`, `camera2` 키 매핑).
3. **M1.5 학습 (2026-05-17)** 시 `empty_cameras` 미명시 → default `0` 적용 → `_prepare_images()` (`modeling_smolvla.py` L448-450) 의 zero-pad loop 가 `num_empty_cameras(0) >= self.config.empty_cameras(0)` 조건에서 *즉시 break* → camera3 슬롯이 *vision encoder forward 자체에 안 들어감*.
4. 가설: 이게 base 의 *3 cam 분포* 와 형식 mismatch 여서 M1.5 0/2 실패의 원인일 수 있다. `empty_cameras=1` 로 zero-pad 슬롯을 추가하면 base 분포와 정합 회복 → 성공 가능성.
5. 현재 그 가설 검증용 분기 학습 진행 중 (run `8jkr7edb`, ~8h, 다른 모든 변수 동결, `empty_cameras` 0→1 만 변경).

### 1-2. 직접 증명된 부분 (코드 + 자료 확인 완료)

| 사실 | 증거 |
|------|------|
| `empty_cameras` default = 0 | `docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py:49` |
| `validate_features()` 가 `empty_cameras` 만큼 `observation.images.empty_camera_{i}` (shape `(3,480,640)`) 를 `input_features` 에 추가 | 같은 파일 L123-130 |
| 코멘트 명시: **"Add empty images. Used by smolvla_aloha_sim which adds the empty left and right wrist cameras in addition to the top camera."** | 같은 파일 L47-48 |
| `prepare_images()` 의 zero-pad loop 가 `num_empty_cameras >= self.config.empty_cameras: break` → `empty_cameras=0` 시 *항상 첫 iteration 에서 break* → missing key 는 zero-pad 도 안 됨 | `modeling_smolvla.py:448-454` |
| zero-pad 값은 `torch.ones_like(img) * -1` (SigLIP normalize 후 -1 = 검정), `mask` 는 `torch.zeros_like(mask)` | 같은 파일 L451-452 |
| zero-pad 슬롯의 mask 는 `embed_prefix()` 에서 `pad_mask` 로 전달 → **vision encoder forward 는 하지만 attention layer 에서 토큰 단위 masking 됨** | 같은 파일 L646-676 |
| LIBERO 공식 benchmark CI 가 *2 cam (`agentview`, `eye_in_hand`) + `--policy.empty_cameras=1`* 로 `lerobot/smolvla_base` fine-tune 함 — *upstream maintainer 가 의도한 사용 패턴* | `docs/reference/lerobot/.github/workflows/benchmark_tests.yml:128-129, 194-195`, [GitHub workflow source](https://github.com/huggingface/lerobot/blob/main/.github/workflows/benchmark_tests.yml) |
| `lerobot/smolvla_libero` (공식 fine-tune 모델) 은 그 2-cam + empty=1 패턴으로 학습된 결과물 | [lerobot/smolvla_libero model card](https://huggingface.co/lerobot/smolvla_libero) |
| **`lerobot/svla_so100_pickplace` (base smolvla 가 fine-tune 받은 대표 dataset) 는 2 cam (`top`, `wrist`)** — *3 cam 아님* | [svla_so100_pickplace dataset card](https://huggingface.co/datasets/lerobot/svla_so100_pickplace) — WebFetch 확인 |
| **SmolVLA paper (arxiv 2506.01844)**: "manually mapped each camera to a standardized view type—prioritizing top, wrist, and side perspectives" (OBS_IMAGE_1/2/3) + **"for datasets with additional views, the order was preserved, but unused views were dropped during training"** + "For SO100, we use top and wrist cameras, where for SO101 we use top and side cameras" | [arxiv 2506.01844 HTML](https://arxiv.org/html/2506.01844v1) — WebFetch 확인 |
| Hub `lerobot/smolvla_base/config.json` 의 `input_features` = `camera1/2/3` 3 cam, `empty_cameras=0` | [config.json](https://huggingface.co/lerobot/smolvla_base/blob/main/config.json) — WebFetch 확인 |

### 1-3. 추정만 된 부분 (검증 안 됨 / 불확실)

| 추정 | 미해결 의문 |
|------|------------|
| "base smolvla 가 사전학습 시 *zero-padded empty camera 분포* 를 *실제로* 본 적이 있다 / 없다" | paper 는 *missing view 는 drop* 한다고 명시 → empty_cameras 의 zero-pad 는 *pretraining 시점에 없었던 패턴* 일 가능성. 단 그래도 *attention pad_mask 메커니즘 자체* 는 학습 시 lang token padding 등으로 항상 활성 — *마스킹된 토큰은 모델이 학습 중 일관되게 처리* 한 경험 있음. |
| "empty_cameras=0 (M1.5) 학습이 base 분포와 *얼마나* mismatch 됐는지 정량 평가" | mask 가 attention 단에서 무시되므로, 실제 vision encoder 가 *몇 개 슬롯을 본 것* 만이 차이. 2 vs 3 cam = *prefix length 가 다름* (각 cam = ~64 visual tokens) → cross-attn KV cache 길이 차이. 이 차이가 *치명* 인지 *경미* 인지 정량 증거 없음. |
| "M1.5 0/2 무반응의 근본 원인이 *카메라 mismatch* 다" | community 보고에 *2-cam + smolvla = 무반응/shaking* 패턴 다수 (§3-1 참고) 가 *closed-as-not-planned* 또는 *해결 안 됨* — *모두가 같은 함정에 빠지지만 누구도 단정적 해법 안 내놓음*. 다른 원인 (normalization stats 누락, dataset 품질, episode count, LoRA rank, action chunking) 도 잠재. |
| "ggando.com SO-101 100% 성공 사례가 *empty_cameras=1* 을 사용했는가" | ggando 블로그 본문에서 `empty_cameras` 파라미터 언급 *없음*. 2 cam 사용 + 100% 성공 — 그러나 그가 *어떤 config* 로 학습했는지 불명. lerobot 의 *그 시점 default 동작* 이 무엇이었는지 (PR 도입 시점) 추가 검증 필요. |

### 1-4. 호출 경로 검증 (M1.5 reflection 적용)

본 보고서 §3 의 `_prepare_images()` 분석은 *실제 호출 경로*. 검증:

1. config 명시 여부: M1.5 `train_config.yaml` 에 `policy.empty_cameras` 명시 *없음* → default `0` 적용.
2. default 추적: `configuration_smolvla.py:49` `empty_cameras: int = 0`.
3. 호출 path: `lerobot-train` → policy 초기화 → forward 시 `_prepare_images()` 호출 (`modeling_smolvla.py:415`) → `for num_empty_cameras in range(len(missing_img_keys)): if num_empty_cameras >= self.config.empty_cameras: break` → **empty_cameras=0 이면 즉시 break** ⇒ missing camera3 슬롯 zero-pad 도 안 됨 확인.
4. 학습 중 dataset batch 에 `observation.images.camera1`, `camera2` 만 들어옴 (rename_map 결과) → `present_img_keys = [camera1, camera2]`, `missing_img_keys = [camera3]` → camera3 zero-pad 안 됨 → vision encoder 가 2 cam 만 처리.

호출 경로 확정. 추가 fallback 경로 없음.

---

## §2 환경 진단

### 2-1. 우리 환경의 현 상태 (M1.5 학습·추론 사실)

- **prof_computer 학습 환경**: Win10 + WSL2 + RTX 3090 24GB, lerobot 0.5.x, LoRA r=16 all-linear, batch=4, steps=75000, dataset = 100ep balanced subset (task1 doll 50 + task2 can 50), `empty_cameras=0` (미명시). 100ep balanced subset 학습 완주, loss 0.04 수렴.
- **Orin 추론 환경**: 동일 ckpt 로 task1 front + task2 front 각 1회 평가 = **0/2 (0%)**. base smolvla_base 0-shot 도 무반응. → *우리 ckpt 만의 문제 아님*. base 자체가 우리 셋업에서 immediately reactive 아님 (참고: `orin_base_eval_2026-05-17.md`).
- **카메라 셋업**: dataset 의 `observation.images.top`, `observation.images.wrist` → rename_map 으로 `observation.images.camera1`, `observation.images.camera2` 매핑. `camera3` 슬롯은 *base config 가 요구* 하지만 dataset 에 *없음*.
- **현재 진행 사이클** (호출자 메시지에 명시): `run_train_camera_empty.py` (단일 변수 `--policy.empty_cameras=1` 만 다름), 같은 dataset / LoRA / batch / steps, wandb run `8jkr7edb` 진행 중 (~8h).

### 2-2. 관련 코드 review 결과

#### 2-2-1. `prepare_images()` (modeling_smolvla.py L415-455) — *핵심 함수*

```python
def prepare_images(self, batch):
    images = []
    img_masks = []
    present_img_keys = [key for key in self.config.image_features if key in batch]
    missing_img_keys = [key for key in self.config.image_features if key not in batch]

    if len(present_img_keys) == 0:
        raise ValueError(...)  # 최소 1 cam 필요

    # Preprocess image features present in the batch
    for key in present_img_keys:
        img = batch[key]...
        img = resize_with_pad(img, *self.config.resize_imgs_with_padding, pad_value=0)
        img = img * 2.0 - 1.0  # SigLIP 정규화 [-1, 1]
        mask = batch[f"{key}_padding_mask"].bool() if ... else torch.ones(bsize, ..., bool)
        images.append(img)
        img_masks.append(mask)  # ← 실제 cam: mask=True

    # Create image features not present in the batch as fully 0 padded images.
    for num_empty_cameras in range(len(missing_img_keys)):
        if num_empty_cameras >= self.config.empty_cameras:
            break                                # ← empty_cameras=0 시 *항상* break
        img = torch.ones_like(img) * -1          # -1 = SigLIP normalized 검정
        mask = torch.zeros_like(mask)            # ← zero-pad cam: mask=False
        images.append(img)
        img_masks.append(mask)
    return images, img_masks
```

**해석**:
- *empty_cameras=0* (M1.5) → missing camera3 슬롯 zero-pad **안 됨**. images list = [cam1, cam2] (2개) only.
- *empty_cameras=1* (현 분기) → missing camera3 슬롯 zero-pad **됨**. images list = [cam1, cam2, cam3_zero] (3개). cam3_zero 의 mask=False.

#### 2-2-2. `embed_prefix()` (modeling_smolvla.py L637-729) — *mask 가 어떻게 쓰이는가*

```python
for img, img_mask in zip(images, img_masks, ...):
    ...
    img_emb = self.vlm_with_expert.embed_image(img)  # SigLIP forward (mask=False 여도 실행됨)
    img_emb = img_emb * sqrt(img_emb_dim)
    bsize, num_img_embs = img_emb.shape[:2]
    img_mask = img_mask[:, None].expand(bsize, num_img_embs)  # ← 토큰별 mask 확장
    embs.append(img_emb)
    pad_masks.append(img_mask)  # ← pad_mask 로 transformer attention 에 전달
    att_masks += [0] * (num_img_embs)
```

**해석** (cross-attn 의 `pad_mask` 동작 — HuggingFace transformer 표준):
- `pad_mask=True` 인 토큰은 attention 에서 참여. `pad_mask=False` 인 토큰은 *모든 query 에서 무시* (softmax 전 -inf 추가).
- 따라서 *zero-padded camera 의 visual tokens 는 모든 후속 layer 에서 마스킹* — *실질적으로 attention 입장에서는 *2 cam 이나 다름없다*.
- 차이는: (a) prefix 의 *길이* 가 다르다 (= position embedding index 가 다르다), (b) SigLIP forward 가 zero image 도 실행 (작은 compute overhead). (c) pad_mask 의 *분포* 가 다르다 (학습 시 항상 cam1/cam2 가 True, cam3 가 False 인 일관된 패턴이면 모델이 이를 학습).

#### 2-2-3. `validate_features()` (configuration_smolvla.py L123-130)

```python
def validate_features(self) -> None:
    for i in range(self.empty_cameras):
        key = f"{OBS_IMAGES}.empty_camera_{i}"
        empty_camera = PolicyFeature(
            type=FeatureType.VISUAL,
            shape=(3, 480, 640),
        )
        self.input_features[key] = empty_camera
```

**중요한 발견**: `empty_cameras=N` 으로 두면 `input_features` 에 `observation.images.empty_camera_0`, `empty_camera_1`, ... 가 *추가* 됨. 즉 *우리 dataset 의 `camera1/2` 가 매핑된 base config 의 `camera1/2/3`* 와는 *별도로* `empty_camera_*` 키가 *덧붙여진다*.

→ 이건 호출자의 가설과 *미묘하게 다른 메커니즘*. `empty_cameras=1` 이 *camera3 슬롯을 채우는 게 아니라*, *camera1/2/3 + empty_camera_0* 4 슬롯이 되고 이 중 dataset 에 *없는 camera3 + empty_camera_0 두 개가 missing_img_keys* 가 된다. 그러면 `_prepare_images()` 의 zero-pad loop 가 *2 번 missing 중 1 번만 처리* (= 4 슬롯 중 cam1+cam2+1 zero-pad = 3 슬롯이 forward 됨, 마지막 missing 은 여전히 무시됨).

→ 이 경우 *prefix 토큰 길이는 3 cam* 분량으로 회복. 가설과 결과 동일 (3 cam 분량 prefix) 이나 *경로가 정확히 다름* — 추가 검증 가치 있음 (위험: 만약 `empty_cameras=1` 대신 base config 의 `camera3` 키를 정확히 채우려면 `dataset.rename_map` 으로 dummy mapping 이 더 깔끔할 수도).

→ **단순화**: `empty_cameras=1` 적용 시 *prefix 가 3 cam 분량 (~192 visual tokens)* 으로 학습됨. 이는 base 의 3-cam input_features 의 *prefix 길이* 와 일치. **호출자 가설의 끝 효과는 옳음**.

### 2-3. 가설 지지 여부 종합

| 가설 | 지지 정도 | 근거 |
|------|----------|------|
| "base 사전학습 분포가 항상 3 cam 이다" | **약함** (≈ 반증됨) | (a) paper: "missing view drop", (b) svla_so100_pickplace = 2 cam, (c) "It does not matter how many cameras as long as at least one" (community), (d) Hub config 의 camera1/2/3 는 *fine-tune 단계 의 schema* 일 가능성 — *pretraining batch 마다 카메라 수가 변했음* |
| "M1.5 empty_cameras=0 학습이 base 분포와 *큰 mismatch* 다" | **중간** | (a) prefix 길이는 base config (3 cam) 와 다름, (b) 그러나 base 가 *variable cam count* 로 pretrain 됐다면 2 cam 도 분포 내 — paper 인용이 이를 지지. (c) loss 0.04 수렴 = train data fit 의 증거지 base 분포 정합 증거 아님 |
| "empty_cameras=1 적용이 *근본 해결책* 이다" | **중간** | (a) upstream CI 가 이 패턴 사용 (LIBERO 2 cam + empty=1) — *maintainer 의도된 패턴*, (b) 그러나 ggando 100% 성공 사례가 *empty_cameras 사용 여부 불명* — 사용 안 했어도 성공한 거면 *empty_cameras 가 결정적 요인 아님*, (c) community 의 동일 실패 패턴 (issue #1270, #2753, #2210, 다수) 이 *모두 empty_cameras 미사용* 이지만 *해결책으로 empty_cameras 명시* 한 maintainer 답변 *없음* |
| "0/2 실패의 *유일한* 원인이 camera mismatch 다" | **약함** | base 0-shot 도 무반응 (`orin_base_eval_2026-05-17.md`) — base 자체가 우리 셋업에서 reactive 하지 않다. *다른 잠재 원인 모두 미배제* (normalization stats, action chunking n_action_steps=1 함정, dataset 품질, 100ep × 2 task 가 LoRA 수렴 부족, prompt 형식 불일치, state 차원 매핑) |

---

## §3 외부 검색 결과

### 3-1. GitHub issues (upstream lerobot) — 우리와 유사 패턴

| Issue | 관련도 | 요약 |
|-------|--------|------|
| [#1763 — best camera setup for SO101](https://github.com/huggingface/lerobot/issues/1763) | 높음 | SO-101 사용자가 paper ("top, wrist, side") vs dataset ("up, side") 불일치 보고. 카메라 순서가 학습/추론 일관성에 중요하다는 사용자 보고. **maintainer 답변 없음**. empty_cameras 언급 X. |
| [#2753 — Debugging poor eval with SmolVLA and two cameras](https://github.com/huggingface/lerobot/issues/2753) | **매우 높음 (우리 정확히)** | "I only have two cameras and had to remap the cameras and create a dummy third camera for the third camera parameter might have confused the model" — *우리 정확히 같은 상황*. Jetson Orin Nano 배포 + 무반응. **maintainer 답변 없음, 해결 안 됨**. |
| [#2259 — Clarifications on fine-tuning](https://github.com/huggingface/lerobot/issues/2259) | 중간 | Franka Panda + RLBench, loss 수렴 + eval 0%. "does the number of cameras affect the model performance?" 질문 — **답변 없음**. |
| [#2351 — Adapting SmolVLA to other arms](https://github.com/huggingface/lerobot/issues/2351) | 중간 | normalization stats infinity 에러 + joint mapping 의문. **답변 없음**. empty_cameras 언급 X. |
| [#2210 — Inference smolvla_base with so-101 failed](https://github.com/huggingface/lerobot/issues/2210) | 높음 | SO-101 inference 실패. *config 에 `empty_cameras: 0`* 명시 + 사용자가 3 cam 연결. **maintainer 답변 없음**. |
| [#1270 — smolvla not work](https://github.com/huggingface/lerobot/issues/1270) | **매우 높음 (거의 동일)** | 2 cam dataset, 100 ep, 20k steps, **loss 0.021** 수렴, **shaking + looping head movements at initial position**. ACT 는 같은 dataset 에서 정상 작동. **Closed as not planned**. — *우리 M1.5 (loss 0.04 + 무반응) 와 거의 동일 패턴*. |
| [#1351 — Need help about dataset and train](https://github.com/huggingface/lerobot/issues/1351) | 낮음 | 사용자 질문 (cameras 수, depth, dataset 크기 등). **답변 없음**. |
| [#1239 — smolvla model not working properly](https://github.com/huggingface/lerobot/issues/1239) | 중간 | smolvla 학습 후 inference 실패. ACT 는 정상. assigned to @danaaubakirova — **답변 없음**. |
| [#2418 — fine tune SmolVLA in libero tensor shape mismatch](https://github.com/huggingface/lerobot/issues/2418) | 낮음 | LIBERO fine-tune 시 tensor shape 오류. (직접 camera mismatch 아님) |

**핵심 패턴**:
- *2-cam + smolvla = 무반응/shaking* 보고가 **다수**.
- **모두 maintainer 가 명확한 fix 제공 안 함** (closed-as-not-planned, 답변 없음, 또는 미배정).
- 우리 가설 (empty_cameras=1 이 해결책) 을 *명시적으로 검증한 사례 = 0*.

### 3-2. lerobot 공식 CI / 코드 — *upstream 의도된 사용 패턴*

[`docs/reference/lerobot/.github/workflows/benchmark_tests.yml`](https://github.com/huggingface/lerobot/blob/main/.github/workflows/benchmark_tests.yml) (L128-129, 194-195):

```bash
# LIBERO eval — 2 cam dataset + empty_cameras=1
lerobot-eval \
  --policy.path=lerobot/smolvla_libero \
  --env.type=libero \
  '--env.camera_name_mapping={"agentview_image": "camera1", "robot0_eye_in_hand_image": "camera2"}' \
  --policy.empty_cameras=1 \
  ...

# LIBERO train+eval smoke — 2 cam dataset + empty_cameras=1, base = smolvla_base
accelerate launch ... lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --policy.load_vlm_weights=true \
  ...
  --policy.empty_cameras=1 \
  '--rename_map={"observation.images.image": "observation.images.camera1", "observation.images.image2": "observation.images.camera2"}'
```

**해석**: **upstream maintainer 가 의도한 *2 cam dataset + smolvla_base fine-tune 의 표준 패턴* 이 `empty_cameras=1`** 이다. 우리 가설과 *정확히 일치하는* 사용. 게다가 이 CI 가 *통과* 한다 = 공식 배포 환경에서 검증된 패턴.

### 3-3. 공식 문서 + paper

| 출처 | 내용 |
|------|------|
| [SmolVLA paper arxiv 2506.01844](https://arxiv.org/html/2506.01844v1) | "manually mapped each camera to a standardized view type—prioritizing top, wrist, and side perspectives" + **"for datasets with additional views, the order was preserved, but unused views were dropped during training"** + "For SO100, we use top and wrist cameras, where for SO101 we use top and side cameras". → *pretraining 데이터셋들이 1~3 cam 으로 variable*, *missing 은 drop*. |
| [lerobot/smolvla_base model card](https://huggingface.co/lerobot/smolvla_base) | camera 수 / empty_cameras 명시 X. "Inputs: images (multi-view)". |
| [lerobot/smolvla_base config.json](https://huggingface.co/lerobot/smolvla_base/blob/main/config.json) | `input_features`: camera1/2/3 (3 cam), shape `[3, 256, 256]`. `empty_cameras: 0`. |
| [lerobot/svla_so100_pickplace dataset](https://huggingface.co/datasets/lerobot/svla_so100_pickplace) | **2 cam**: `observation.images.top`, `observation.images.wrist`. shape `(480, 640, 3)`, AV1 codec. |
| [lerobot/smolvla_libero model card](https://huggingface.co/lerobot/smolvla_libero) | base 의 LIBERO fine-tune. (config 직접 확인 안 됨, CI 코드가 2 cam + empty=1 패턴 사용 확인) |
| [lerobot docs/source/smolvla.mdx](https://github.com/huggingface/lerobot/blob/main/docs/source/smolvla.mdx) | empty_cameras / 2 vs 3 cam 가이드 *없음*. |

**해석**:
- base 의 *실제 pretraining* 은 *variable camera count*. 3 cam 강제 아님.
- Hub config.json 의 `camera1/2/3` 는 *fine-tune 시점의 schema 정의* (multitask finetune 이 그 schema 였을 가능성 — paper 의 "additional views drop" 정책 적용 후).
- **공식 maintainer 가 명시적으로 "2 cam 시 empty_cameras=1" 가이드 문서를 발행하지 않음** — 그러나 CI 코드는 그렇게 동작.

### 3-4. 커뮤니티 사례

| 출처 | 셋업 | 결과 | empty_cameras 사용 |
|------|------|------|-------------------|
| [ggando.com SO-101 fine-tune](https://ggando.com/blog/smolvla-so101/) | 2 cam (wrist D405 + overhead C920), 75 ep clean, RTX 3090, batch=64, 20k steps | **100% (5/5)** | **블로그에 명시 없음** — 알 수 없음 |
| [Xavier O'Keefe Medium](https://medium.com/correll-lab/fine-tuning-smolvla-for-new-environments-code-included-af266c56d632) | L4 22GB, batch=64, 12k steps, 125 ep | ~40% | LIBERO stats 오사용이 가장 큰 실수 (자기 dataset stats 재계산이 핵심 fix) |
| GitHub issue #1270 (위) | 2 cam, 100 ep, 20k steps, loss 0.021 | **shaking + idle (≈0%)** | 미명시 (= 0) |
| Issue #2753 (위) | 2 cam + dummy 3rd, Orin 배포 | 무반응 | dummy 3rd 직접 만듦 (즉 dataset 단에서 zero 채움) — empty_cameras 파라미터는 미명시 |
| 검색 보고 (위) "30K steps 73 ep SO-101 2 cam → 1cm 움직임 후 idle" | 2 cam | ≈0% | 미명시 |
| 검색 보고 "2-Camera Setup Success: most common configuration; SmolVLA managed to work well" | 2 cam (일반) | 작동 (사례 다수 존재 시사) | 미명시 |

**핵심 패턴 분석**:
1. **2-cam 무반응 실패 보고가 다수**. 모두 empty_cameras 명시 X (= 0). 우리 M1.5 와 동일.
2. **2-cam 성공 사례 (ggando 100%)** 가 *empty_cameras 사용 여부 불명* — 사용 안 했어도 성공했다면 *empty_cameras 가 결정적 변수 아님* 일 가능성. 사용했다면 *우리 분기 학습이 옳은 길*.
3. **공통 해결책 패턴** 다른 변수: (a) normalization stats 재계산 (Xavier 의 fix), (b) clean episode 수 (ggando: 75ep 대신 quality 우선), (c) workspace 협소화 / 카메라 순서 일관성 (ggando + #1763), (d) Orin 배포 시 n_action_steps Hub config.json 수동 변경 (50, 우리 기존 보고서 §1-3 인용).

### 3-5. 검증 안 됐지만 가설 강화/약화 요소

- **강화**: upstream CI 의 LIBERO 2-cam + empty=1 패턴이 *작동 검증된 공식 path* — *우리 분기와 정확히 같음*.
- **강화**: `configuration_smolvla.py` 의 코멘트 "Used by smolvla_aloha_sim which adds the empty left and right wrist cameras" → empty_cameras 가 *원래 도입된 의도* 가 *부족한 카메라를 zero-pad 로 보충* 한 것. base 의 *학습 시점 분포* 에 zero-pad slot 이 *실제로 있었다* 는 의미. (smolvla_aloha_sim 이 *공식 모델* 이라면 — 단 smolvla_aloha_sim 의 model card 직접 확인 시간 부족, 추정만).
- **약화**: paper 의 "missing view drop" 표현 — pretraining 단계는 zero-pad 보다 drop 정책. → empty_cameras zero-pad 는 *pretraining 시점에는 안 본 분포* 일 수 있음. 단 그래도 fine-tune 의 *추가 학습* 이 그 분포에 빠르게 적응 가능.
- **약화**: ggando 100% 성공 사례의 empty_cameras 사용 여부 불명 — *empty_cameras 가 결정적 변수가 아닐* 가능성.

---

## §4 해결책 비교

호출자의 *진행 중 분기 학습 계속 / 중단 결정* + *3번째 카메라 실제 수집 우선순위* 를 위한 옵션:

| # | 옵션 | 비용 (시간) | 위험 | 효과 가능성 | Cat | 후속 영향 |
|---|------|-----------|------|----------|-----|---------|
| 1 | 현 분기 학습 (empty_cameras=1) 완주 + 추론 비교 | 8h (학습 잔여) + 30min (Orin 평가) | 낮음 (이미 진행 중) | **중간** (40-60%) | 없음 | 비교 데이터 확보. 실패 시 다음 분기 근거. |
| 2 | 현 분기 학습 즉시 중단 + 3번째 카메라 실제 수집부터 | 8h (분기 중단으로 절약) + 카메라 setup (1-3일) + dataset 재수집 (수일) + 재학습 (8h+) | 중간 (수집 비용 큼) | **중상** (50-70%) | 없음 | 가장 *근본적* 정합. 그러나 비용·시간 큼. |
| 3 | 현 분기 완주 *후* 추론 비교 결과로 분기 결정 (실패 시 → 옵션 2) | 옵션 1 + (실패 시) 옵션 2 | 낮음 | **높음** (정보 가치) | 없음 | 정보 비용 최소, 결정 근거 최대. **추천**. |
| 4 | 현 분기 + 다른 가설 (normalization stats 재계산, n_action_steps 점검 등) 병행 검증 | 옵션 1 + 추가 1-2h diagnostics | 낮음 | **중상** (다른 root cause 발견 가능성) | 없음 | empty_cameras 가 *유일 원인 아닐* 가능성 대비. 분기 추론 전·후로 함께 봐야. |
| 5 | 분기 학습 중단 + LoRA rank/steps/batch 등 다른 hyperparam 재시도 (3 cam 이슈 무시) | 8h+ × N 회 | 높음 (랜덤 search) | 낮음 | 없음 | 비추천 — empty_cameras 미해결로는 community 다수 실패 패턴 반복 위험. |
| 6 | 분기 학습 완주 후 *empty_cameras=2* 추가 분기 (smolvla_aloha_sim 패턴) | + 8h | 낮음 | 낮음 (3-cam input_features 와 형식 차이 추가됨) | 없음 | 정보 가치 낮음 — empty_cameras=1 이 base 형식과 가장 정합. |

### 옵션 상세

#### 옵션 1: 현 분기 학습 (empty_cameras=1) 완주 + 추론 비교
- **동작 원리**: M1.5 와 *단일 변수 (`empty_cameras` 0→1)* 만 다른 학습. 동일 dataset/LoRA/batch/steps. `_prepare_images()` 에서 missing camera3 슬롯이 zero-pad + mask=False 로 채워져 prefix 토큰 길이가 base config 의 3 cam 기대치와 일치.
- **검증 방법**: 학습 완료 후 Orin 동일 평가 (task1 front 1회 + task2 front 1회) → M1.5 0/2 와 직접 비교. *동일 환경 / 동일 카메라 / 동일 prompt* — 단일 변수 비교.
- **성공 정의**: 단축 평가에서 *최소 1/2 이상* 작동 + 무반응이 아닌 *의미 있는 motion* 발생.
- **미탐색 의문점**:
  - empty_cameras=1 적용으로도 여전히 *0/2* 가 나오면 → root cause 가 *카메라 mismatch 아닌 다른 곳* (normalization stats, n_action_steps, dataset 품질 등).
  - empty_cameras=1 이 작동하지만 *부분 성공 (1/2)* 이면 → mismatch 가 *기여 요인* 이나 *유일 원인 아님*.

#### 옵션 2: 현 분기 즉시 중단 + 3번째 카메라 실제 수집부터
- **동작 원리**: base config 의 camera1/2/3 형식을 *zero-pad 가 아닌 실제 이미지* 로 채움. 가장 *형식·분포 양쪽 정합*. SmolVLA paper 가 SO101 에 *top + side* 권장, SO100 에 *top + wrist* 권장. 우리는 SO-101 좌측 아암 → 권장은 top + side 일 수 있으나 우리 dataset 은 top + wrist. *세 번째 카메라 추가 시 side 권장* (front 도 가능).
- **검증 방법**: 새 카메라 setup → smoke 수집 (5-10 ep) → 형식 검증 → 본 수집 (50ep+ per task) → 재학습 (8h+) → Orin 평가.
- **비용**:
  - 카메라 하드웨어 setup: 1-3일 (mount + 인식 검증).
  - dataset 재수집: 100ep × 2 task ≈ 1-2일 teleoperation.
  - 재학습: 8h+ (M1.5 동일 setup 기준).
  - **총 4-6일 + 비용**.
- **미탐색 의문점**:
  - 3 cam 으로 했는데도 무반응이 다른 원인이면 (normalization, n_action_steps 등) — 큰 비용 손실.
  - 옵션 1 결과 *전* 에 옵션 2 시작 = *정보 없이 비싼 결정*.

#### 옵션 3 (추천): 현 분기 완주 + 결과로 옵션 2 결정
- **동작 원리**: 8h 분기 학습이 이미 진행 중 — *추가 sunk cost 없음*. 학습 끝나면 Orin 평가 30min 으로 *결정적 데이터* 확보:
  - 분기 결과 ≥ 1/2 작동 → empty_cameras=1 이 *작동하는 fix* 임 확인. 옵션 2 (3번째 카메라 수집) 의 우선순위 *대폭 낮춤*. M1.5 의 영향 영역만 보강 (예: full 학습 dataset 으로 본 학습 진행).
  - 분기 결과 0/2 무반응 → empty_cameras 가 *root cause 아님* 확정. 그제서야 옵션 2 또는 다른 가설 진행. *empty_cameras 가 답 아니라는 정보가 8h + 30min 으로 얻어진다 — 매우 비용 효율적*.
- **추천 근거**:
  1. 진행 중 학습 중단 시 *진단 정보 0* — 가치 손실.
  2. 분기 결과는 *어느 방향으로 나와도* 다음 행동 결정에 결정적 정보.
  3. 옵션 2 비용 (4-6일) 의 *합리적 정당화* 가 옵션 1 완료 *후* 에만 가능.

#### 옵션 4: 분기 + 다른 가설 병행 진단
- **동작 원리**: 분기 학습 진행 중 + Orin 평가 시 *다른 잠재 원인* 도 함께 점검:
  - **normalization stats**: ckpt 의 `policy_preprocessor_step_5_normalizer_processor.safetensors` 확인. infinity 값 또는 잘못된 stats 면 정정.
  - **n_action_steps**: ckpt 의 `config.json` 에서 `n_action_steps` 값 확인. 1 이면 50 으로 수동 변경 (기존 보고서 §1-3 인용).
  - **Hub config 의 input_features**: M1.5 ckpt 의 input_features 가 dataset 의 cam1/cam2 만으로 *축소* 됐을 수 있음 (`validate_features()` 동작 차이 — 확인 필요).
  - **prompt 형식**: task description 의 토크나이저 입력이 학습/추론 동일한지.
  - **state dim**: SO-101 6DOF 가 max_state_dim=32 로 zero-pad 되는데, 추론 시 동일 처리 되는지.
- **검증 방법**: 분기 학습 끝나기 전 (몇 시간 여유) 위 항목들 *코드 확인 또는 ckpt inspect*. 추가 시간 1-2h.
- **추천**: 옵션 3 와 *병행*. M1.5 의 0/2 가 *단일 원인이 아닐* 가능성 대비.

---

## §5 추천 + 근거

### 추천: **옵션 3 + 옵션 4 병행**

1. **현 분기 학습 (empty_cameras=1) 계속 진행 → 완주**.
2. **학습 완료 즉시 Orin 동일 평가** (task1 front + task2 front 각 1회) — M1.5 0/2 와 직접 비교.
3. **분기 학습 끝나기 전 (~8h 사이)** 다른 잠재 원인 *low-cost 진단* (옵션 4):
   - M1.5 ckpt 의 `config.json` 에서 `n_action_steps`, `input_features`, `empty_cameras` 값 직접 확인 (Read).
   - normalization stats safetensors 의 mean/std 값 sanity check (NaN/Inf 없는지).
   - 학습 시 사용된 task prompt 와 추론 시 prompt 동일성 검증.

### 근거

1. **upstream CI 의 *작동 검증된* 표준 패턴 (LIBERO 2-cam + empty=1) 이 우리 가설과 정확히 일치** — 위험 낮음 + 기대 효과 중간 이상. ([benchmark_tests.yml L194-195](https://github.com/huggingface/lerobot/blob/main/.github/workflows/benchmark_tests.yml))
2. **community 의 동일 실패 사례 (#1270, #2753, #2210) 가 모두 empty_cameras 미사용 + 무반응** — 통계적으로 강한 *correlated 신호*. 단 *causal 증명은 안 됨* (해결 사례 0).
3. **3번째 카메라 실제 수집 (옵션 2)** 의 비용 (4-6일) 이 *empty_cameras=1 분기 결과 없이는 정당화 불가*. 분기 결과가 *옵션 2 의 ROI 자체* 를 결정.
4. **M1.5 0/2 의 root cause 가 *복수* 일 가능성** — base 0-shot 도 무반응이라는 사실은 *카메라만의 문제 아닐* 가능성. 다른 진단 (옵션 4) 병행이 *분기 결과 해석* 에 필수.
5. **단순화·증분 변경 원칙** — 우리 분기는 *단일 변수* 만 변경 (empty_cameras 0→1). 결과 해석이 *명확*. 만약 동시에 *카메라 추가 + LoRA rank + LR* 등을 함께 바꾸면 *원인 분리 불가능*.

### Plan B (분기 결과 0/2 시)

empty_cameras=1 도 무반응이면:
1. **옵션 4 진단 결과 검토** — n_action_steps Hub config 함정, normalization stats 오류, prompt mismatch 등 *low-hanging fruit* 먼저.
2. **base smolvla_base 0-shot 무반응 자체** 의 원인 추적 — 우리 Orin 셋업 (카메라 driver, image pipeline, action 출력 경로) 의 *추론 인프라* 가 잘못됐을 가능성.
3. *그 후에* 옵션 2 (3번째 카메라 수집) 검토.

### 사용자 결정 필요 사항

- **3번째 카메라 위치 (옵션 2 시)**: SmolVLA paper 가 SO101 에 *top + side* 권장. 우리 dataset 의 *wrist* 를 유지하면 *top + wrist + side* 가 됨. 아니면 paper 권장대로 *top + side + (third)* 로 바꿀지. **사용자 (도메인 지식) 결정 필요**.
- **분기 결과 1/2 (부분 성공) 시 다음 행동**: empty_cameras 가 *부분 fix* 임이 확인되면, (a) 학습량 증대 (200ep, 더 많은 steps) 로 충분한지 / (b) 3번째 카메라 추가가 그래도 가치 있는지. **분기 결과 본 후 재논의**.

---

## §6 최소 비용 검증 제안

분기 학습 *진행 중* 에 *추가 시간 1-2h* 로 가능한 진단:

### 검증 A: M1.5 ckpt config 직접 inspect (15min)

```bash
# WSL2 또는 Orin 에서
cat <ckpt_dir>/config.json | jq '.n_action_steps, .empty_cameras, .input_features'
# 기대: n_action_steps=50 (또는 50 으로 수동 변경 필요), input_features 에 camera1/2 만 또는 camera1/2/3 인지
```

- 목적: M1.5 ckpt 의 *학습 시점 input_features* 가 실제 어떻게 저장됐는지 확인. base config 의 camera1/2/3 가 그대로 상속됐는지 (호출자 "직접 확인" 보고) vs dataset 의 cam1/cam2 만 으로 축소됐는지.

### 검증 B: M1.5 normalization stats sanity (10min)

```bash
python -c "
import safetensors.torch as st
d = st.load_file('<ckpt_dir>/policy_preprocessor_step_5_normalizer_processor.safetensors')
for k, v in d.items():
    if 'mean' in k or 'std' in k:
        print(k, v.float().mean().item(), v.float().min().item(), v.float().max().item())
"
```

- 목적: normalization stats 에 NaN/Inf 있는지. issue #2210 패턴 확인.

### 검증 C: base smolvla_base 0-shot 무반응의 *추론 인프라* 검증 (30min)

기존 보고서 (`orin_base_eval_2026-05-17.md`) 에서 base 0-shot 무반응 확정 — 이게 *우리 Orin 셋업의 추론 인프라 문제* 가 아닌지 점검:
- 카메라 raw 이미지가 모델에 *제대로 들어가는지* (이미지 dump → 시각 확인).
- 모델 출력 action vector 가 *robot 에 제대로 전달되는지* (action log 확인).
- prompt 가 *학습 시 task description 과 매칭* 되는지 (dataset meta/tasks.jsonl 와 inference prompt 비교).

### 검증 D: ggando 사례 재현 가능성 점검 (시간: 검토만)

ggando 가 *empty_cameras 명시 X* 로 100% 성공했다면, 다른 변수 (workspace 협소화, 카메라 위치, dataset clean 정도) 가 더 결정적. ggando 블로그 재독 + 우리 dataset 의 *workspace 크기 / clean episode 수* 비교 (1h). 만약 ggando 와 우리 dataset 의 *carousel motion variance* 가 크게 다르면 *dataset 품질* 이 root cause 가능성.

---

## §7 요약 (TL;DR for 호출자)

**Q1 (사전학습 분포 정합)**: base smolvla_base 의 사전학습 분포는 *항상 3 cam 아님*. paper 인용 "missing view drop" + svla_so100_pickplace = 2 cam = *variable cam count* 로 사전학습됨. Hub config 의 camera1/2/3 는 *fine-tune schema*. → *3번째 카메라 실제 수집은 base 분포 정합을 위해 필수 아님*. zero-padded slot (empty_cameras=1) 도 acceptable — upstream CI 가 이 패턴 사용 중. 단 zero-pad slot 분포가 *pretraining 에 정확히 있었다* 는 직접 증거 *없음* (smolvla_aloha_sim 사용 사례 추정만).

**Q2 (M1.5 학습이 base 분포 깨뜨렸나)**: M1.5 (empty_cameras=0) 는 camera3 슬롯이 *완전 무시* → prefix 토큰 길이 *2 cam 분량* 으로 학습. base config 가 *3 cam 분량 prefix* 를 기대하는 형식과 *형식 mismatch*. 그러나 base 자체가 *variable cam count* 로 사전학습됐다면 이는 *분포 내 상황*. **mismatch 가 *치명* 인지 *경미* 인지 정량 증거 없음**. loss 0.04 수렴은 *train data fit 의 증거지 base 정합 증거 아님* (호출자 지적 정확).

**행동 추천**:
1. **현 분기 학습 (empty_cameras=1) 계속 진행** — 진행 중 sunk cost + 결과가 결정적 정보 + upstream 검증된 패턴.
2. **학습 끝나기 전 *low-cost 진단* (검증 A/B/C) 병행** — 다른 잠재 root cause 배제.
3. **결과 보고 후 옵션 2 (3번째 카메라 수집) 결정** — 분기 ≥ 1/2 작동 시 우선순위 낮춤, 0/2 시 옵션 4 결과 보고 옵션 2 검토.

**비용·정보 trade-off**:
- 분기 학습 중단 시 8h 절약 + *진단 정보 0*.
- 분기 학습 완주 시 8h 사용 + *결정적 정보 (empty_cameras 가 fix 인지 아닌지)* + Plan B 비용 (3번째 카메라 수집 4-6일) 의 ROI 산정 가능.
- → **분기 완주가 정보 비용 효율 최적**.

---

## §8 출처 (Sources)

### lerobot 공식 코드 (직접 review)
- `docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py` — `empty_cameras` 정의, `validate_features()`
- `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py` — `prepare_images()`, `embed_prefix()`
- `docs/reference/lerobot/.github/workflows/benchmark_tests.yml` — LIBERO 2-cam + empty=1 공식 CI 패턴

### HuggingFace
- [lerobot/smolvla_base model card](https://huggingface.co/lerobot/smolvla_base)
- [lerobot/smolvla_base config.json](https://huggingface.co/lerobot/smolvla_base/blob/main/config.json)
- [lerobot/smolvla_libero model card](https://huggingface.co/lerobot/smolvla_libero)
- [lerobot/svla_so100_pickplace dataset](https://huggingface.co/datasets/lerobot/svla_so100_pickplace)
- [SmolVLA paper (arxiv 2506.01844 HTML)](https://arxiv.org/html/2506.01844v1)
- [SmolVLA paper (arxiv 2506.01844 abstract)](https://arxiv.org/abs/2506.01844)
- [SmolVLA blog post](https://huggingface.co/blog/smolvla)

### GitHub issues (lerobot upstream)
- [#1270 — smolvla not work (2 cam, loss 0.021, shaking idle)](https://github.com/huggingface/lerobot/issues/1270)
- [#1239 — smolvla model not working properly](https://github.com/huggingface/lerobot/issues/1239)
- [#1351 — Need help about dataset and train](https://github.com/huggingface/lerobot/issues/1351)
- [#1763 — best camera setup for SO101](https://github.com/huggingface/lerobot/issues/1763)
- [#2210 — Inference smolvla_base with so-101 failed](https://github.com/huggingface/lerobot/issues/2210)
- [#2259 — Clarifications on fine-tuning](https://github.com/huggingface/lerobot/issues/2259)
- [#2351 — Adapting SmolVLA to other arms](https://github.com/huggingface/lerobot/issues/2351)
- [#2418 — fine tune SmolVLA in libero tensor shape mismatch](https://github.com/huggingface/lerobot/issues/2418)
- [#2753 — Debugging poor eval with SmolVLA and two cameras](https://github.com/huggingface/lerobot/issues/2753)
- [lerobot benchmark_tests.yml workflow source](https://github.com/huggingface/lerobot/blob/main/.github/workflows/benchmark_tests.yml)
- [lerobot docs/source/smolvla.mdx](https://github.com/huggingface/lerobot/blob/main/docs/source/smolvla.mdx)

### 커뮤니티 사례
- [ggando.com — Fine-tuning SmolVLA for Cube Pick-and-Place on SO-101](https://ggando.com/blog/smolvla-so101/)
- [Xavier O'Keefe — Fine Tuning SmolVLA for New Environments (Medium)](https://medium.com/correll-lab/fine-tuning-smolvla-for-new-environments-code-included-af266c56d632)

### 우리 프로젝트 자료 (인용)
- [`prof_computer/docs/leftarm_v2/learning_log.md`](learning_log.md) — M1.5 학습 상세
- [`prof_computer/docs/leftarm_v2/orin_a2_eval_2026-05-17.md`](orin_a2_eval_2026-05-17.md) — M1.5 ckpt 추론 0/2
- [`prof_computer/docs/leftarm_v2/orin_base_eval_2026-05-17.md`](orin_base_eval_2026-05-17.md) — base smolvla_base 0-shot 무반응
- [`prof_computer/docs/model_config.md`](../model_config.md) — 학습 방법 매트릭스 + 결정 근거
- `smolVLA/prof_computer/finetune/leftarm_v2/run_train_camera_empty.py` — 현 분기 학습 wrapper (단일 변수 차이)
- `smolVLA/docs/work_flow/context/history/02_prereq_dataset_video_to_image/research/lerobot_smolvla_training_best_practice.md` — 기존 best practice 보고서 (본 보고서는 그 보고서의 *카메라 mismatch 공백 영역 보강*)

---

verdict: NEEDS_INVESTIGATION
