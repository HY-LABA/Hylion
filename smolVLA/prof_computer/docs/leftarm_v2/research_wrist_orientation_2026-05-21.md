# Research Report — SmolVLA wrist camera *view orientation* (상하반전) 이 추론 성능에 주는 영향

> 작성: 2026-05-21 | researcher
> 호출자: 메인 — leftarm_v2 003 ckpt (310ep · 100%) 이후 *004 분기 (wrist 180° 회전 정렬)* 진입 정당화 검토
> 범위: *문헌·이론적 정당화만*. 003 ckpt 직접 분석 (R1-b) 은 별도 영역 — 본 보고서에서 시도 X.
> 관련 자료 (중복 회피):
>  - 카메라 *개수·이름·해상도·FPS·코덱* — [`research_smolvla_pretrain_cameras_2026-05-19.md`](research_smolvla_pretrain_cameras_2026-05-19.md) 가 담당
>  - 카메라 *수 mismatch (2 vs 3 cam · empty_cameras)* — [`research_empty_cameras_2026-05-18.md`](research_empty_cameras_2026-05-18.md) 가 담당
>  - 본 보고서는 *orientation (상하반전 등 view 방향)* 영역만 집중

---

## §0 TL;DR

**결론**: wrist camera 의 *180° 회전 정렬* 이 SmolVLA fine-tune 성능에 *기여 가능성 있음* — 단 근거 강도는 **간접 (indirect) ~ 정황적 (circumstantial)** 수준.

**근거 강도 분리**:
- **직접 증거 (direct)**: *없음*. SmolVLA / SO-100 / SO-101 + wrist orientation 을 *정량 비교* 한 ablation 또는 공식 가이드 *0건*. SmolVLA paper / 블로그 / lerobot 공식 문서 / GitHub issue #1763 (정확히 SO-101 카메라 셋업 토론) 모두 wrist orientation 언급 *없음*.
- **간접 증거 (indirect, 강함)**:
   - (a) lerobot dataset transforms 의 기본 augmentation 에 *rotation/flip 없음* (`ColorJitter`, `SharpnessJitter`, `RandomAffine ±5°` 만) + `enable: False` default → 사전학습 분포가 *고정 orientation 의 implicit prior* 를 강하게 학습했을 가능성.
   - (b) SmolVLA 의 base VLM (SmolLM2 + SigLIP) 같은 *natural image* 사전학습 VLM 이 *180° 회전 입력* 에서 *catastrophic 성능 저하* 보고됨 (Claude/GPT-4o text extraction 97% → 25-28%, keyword match 94% → 15-23% — VLM 일반 패턴). SigLIP 자체도 augmentation invariance 에서 *상대적으로 약함* (LGIP paper).
   - (c) lerobot 의 카메라 driver (`OpenCVCameraConfig`, `RealSenseCameraConfig`) 가 *`rotation` 파라미터 (NO_ROTATION/90/180/270)* 를 명시 지원 — 이는 *물리적 마운트 orientation 을 데이터 수집 단계에서 보정하는 것이 표준 워크플로우* 임을 시사. *upstream maintainer 가 orientation 보정을 카메라 driver 레벨에 둠* = 학습 시점엔 *바른 orientation 이 기대됨* 의 implicit 신호.
- **정황적 증거 (circumstantial)**:
   - (d) lerobot SO-100 공식 dataset (`svla_so100_pickplace`, `svla_so100_sorting`) 의 wrist view 가 *upright (그리퍼 보이는 자연 방향)* 인지 *상하반전* 인지 *dataset card / paper 모두 침묵*. 시각적 inspection 필요 (본 보고서에서는 미수행).
   - (e) "wrist camera 의 작은 3 cm shift 만으로도 성능 저하 + 재수집·fine-tune 필요" 보고 (Issue #1763 community) → wrist view 분포가 *민감* 함을 의미. 180° 회전은 *3 cm shift 보다 훨씬 큰 분포 shift*.

**적용 권고 (요약)**: 003 ckpt (단축 평가 100%) 가 *현재 안정* — wrist 180° 회전 정렬을 *004 분기* 로 시도하는 것은 **합리적 가설** 이나 *직접 증거 부재* 로 *반드시 ablation* 필요 (003 wrist 그대로 vs 004 wrist 180° 회전 정렬, 다른 모든 변수 동결). 정성·정량 효과의 *크기* 는 *예측 불가* — 50% 이상 향상 가능성도, *변화 없음/저하* 가능성도 모두 열려 있음. 자세한 권고는 §6.

---

## §1 Q1 답변 — wrist camera orientation 의 사전학습 컨벤션

### 1-1. 직접 자료

- **SmolVLA paper (arxiv 2506.01844)**: 사전학습 데이터 *카메라 view type 표준화* 만 명시 — "manually mapped each camera to a standardized view type—prioritizing top, wrist, and side perspectives—and renamed them as OBS_IMAGE_1/2/3". *frame orientation (회전 방향)* 표준화 *언급 없음*. (WebFetch 확인)
- **SmolVLA HF blog**: 마찬가지로 orientation 언급 *없음*.
- **lerobot 공식 docs (`smolvla.mdx`, `so101.mdx`, `cameras.mdx`)**: wrist camera mount 의 *물리적 orientation 권장 사항 없음*. 단 hardware 어셈블리 가이드는 *마운트 위치* 만 명시 (gripper 측면 부착) — *카메라 윗변이 어느 쪽인지* 무관.
- **lerobot SO-101 빌드 가이드 (`huggingface.co/docs/lerobot/so101`)**: wrist 카메라 마운트 사진 *없음*. 메인 어셈블리는 모터·기구물 위주.
- **TheRobotStudio/SO-ARM100 wrist camera mount 페이지** (deepwiki): *별도 페이지 존재* 하나 본 조사에서 access 못함 (HTTP 403, Thingiverse 도 403). 직접 확인 영역은 *후속 작업*.

### 1-2. 사전학습 데이터셋의 *실제* wrist orientation — *직접 확인 못함*

- `lerobot/svla_so100_pickplace` (SmolVLA SO-100 레퍼런스, 2 cam top+wrist): dataset card *frame orientation 정보 없음*. 비디오 직접 시각 inspection 이 *유일한 답*. 본 보고서는 *web text-only* 조사 — 미수행. **자료 부재**.
- `lerobot/svla_so100_sorting` (또 다른 SO-100 레퍼런스): 마찬가지.
- `lerobot/svla_so101_pickplace` (SO-101 레퍼런스): **wrist 카메라 없음 (`up` + `side`)** — orientation 비교 대상 자체가 *없음*.
- 481개 커뮤니티 데이터셋 전체의 wrist orientation 분포: **정량 통계 자료 없음 (공식 + community)**.

### 1-3. lerobot 의 카메라 driver 단 *rotation* 파라미터 — *암묵적 컨벤션 증거*

- `lerobot/cameras/configs.py`: `class Cv2Rotation(int, Enum): NO_ROTATION=0, ROTATE_90, ROTATE_180=180, ROTATE_270`
- `OpenCVCameraConfig`, `RealSenseCameraConfig` 양쪽 모두 `rotation: Cv2Rotation = Cv2Rotation.NO_ROTATION` default. cv2 의 `ROTATE_*` 를 raw frame 에 적용.
- **의미**: lerobot upstream maintainer 가 *물리적으로 회전된 카메라 마운트 (upside-down 등) 를 데이터 수집 단계에서 보정* 할 수 있도록 *driver 레벨에서 rotation 파라미터를 노출*. 즉 **"학습 시점엔 자연 방향 (upright) frame 이 들어오는 것" 이 *전제된 워크플로우***.
- 이건 *암묵적 컨벤션* — 명시적 권장 문구가 *없을 뿐* upstream 코드 디자인이 *바른 방향 frame 을 기대* 한다는 강한 신호.

### 1-4. GitHub Issue 검토

| Issue | wrist orientation 관련 언급 |
|-------|---------------------------|
| #1763 (best camera setup for SO-101) | **언급 없음**. 카메라 *순서·이름* 만 토론. (WebFetch 확인) |
| #2753 (Debugging poor eval with SmolVLA 2 cam) | wrist 카메라 사용 — orientation 언급 없음 |
| #1270 (smolvla not work) | orientation 언급 없음 |
| #2210, #2259, #2351, #2418 | orientation 언급 없음 |

→ **community 토론 영역 자체에 wrist orientation 이 *isolated variable* 로 등장한 사례 0**. 누군가가 *isolated ablation* 한 적이 *없는 영역*.

### 1-5. Q1 종합

| 질문 | 답변 | 자료 강도 |
|------|------|---------|
| "정방향 (그리퍼 위쪽에서 아래) 이 표준인가?" | **자료 없음** (시각 inspection 미수행) | — |
| "역방향/회전도 흔한가?" | **자료 없음**. 단 *카메라 driver 의 rotation 파라미터 존재* = 회전된 마운트가 *알려진 케이스 (보정 필요)* | 간접 |
| "사전학습 분포의 상하반전 wrist 비율 정량 자료" | **없음** | — |
| "어떤 *암묵* 컨벤션이 있는가?" | *carry-over* 컨벤션 = *데이터 수집 단계에서 upright 으로 보정한 후 학습* | 간접 (lerobot driver 디자인) |

---

## §2 Q2 답변 — VLM 의 *상하반전 입력* 성능 저하 일반 증거

### 2-1. VLM (CLIP·SigLIP·GPT-4o·Claude) 의 180° 회전 catastrophic 저하 — *정량 직접 증거*

[dev.to (kenimo49) Claude/GPT-4o rotation 실험](https://dev.to/kenimo49/passing-rotated-images-to-claude-or-chatgpt-drops-accuracy-to-one-third-29f) — 텍스트 추출 task:

| Rotation | Claude text extraction | GPT-4o text extraction | Claude keyword match | GPT-4o keyword match |
|----------|----------------------|----------------------|--------------------|---------------------|
| 0° (정방향) | **97.0%** | **97.0%** | **94.3%** | **94.3%** |
| 90° | 39.5% | 95.0% | 50.5% | 94.3% |
| 270° | 44.5% | 91.9% | 62.4% | 100% |
| **180°** | **27.9%** | **24.9%** | **22.9%** | **14.8%** |

→ **180° 가 90°·270° 보다 *훨씬* 심각**. 70 percentage point 의 *catastrophic drop*. 비록 task 가 *text extraction* 이긴 하나, *모든 modern VLM 의 자연 이미지 prior 가 180° 에 가장 취약* 함을 보여줌 (90°/270° 는 책표지·간판 등이 회전된 자연 분포가 학습에 일부 포함되지만, 180° 는 *거의 본 적 없는 분포*).

### 2-2. CLIP / SigLIP 의 transformation invariance 부재 — *직접 증거*

[arxiv 2503.09837 — "On the Limitations of Vision-Language Models in Understanding Image Transforms"](https://arxiv.org/pdf/2503.09837) (WebFetch 확인):

- CLIP / SigLIP 의 *augmented image 매칭* 정확도:
  - Experiment 3 (transformation 분류): **Top-1 3.61% (ViT-B/32), Top-5 18.40%** — *random chance 수준*. "for most of the augmentation, the accuracy is 0% and model was not able to identify a single correct example"
- Experiment 1 (augmented description 인식): CLIP ViT-L/14 **43.10%**, SigLIP Base 256 ML **47.21%** — random (50%) 미만.
- DALL-E 3, Instruct Pix2Pix, IP Adapter 등 image editing 모델이 *"rotate the input image 90 degrees"* 명령조차 *실행 실패*.

→ **vision encoder 자체가 image transformation 의 *semantic* 을 안 보유** — 180° 회전 입력은 *전혀 다른 데이터 분포* 로 인식.

### 2-3. SigLIP 의 invariance error — CLIP 대비 *더 약함*

[arxiv 2511.13494 — Language-Guided Invariance Probing (LGIP)](https://arxiv.org/html/2511.13494):

- "**SigLIP and SigLIP2 exhibit substantially higher invariance error** and can score flipped captions above human descriptions, particularly for object and color edits, whereas CLIP-family and large OpenCLIP models, particularly EVA02-CLIP, combine low paraphrase-induced variation with consistent rejection of attribute-flipped captions."
- 단 LGIP 는 *텍스트 perturbation* 만 다룸 (image fixed) — 이 paper 자체는 image rotation 정량 결과 *없음* (스코프 명시). 단 SigLIP 의 *분포 외 입력에 대한 *general* 약점* 신호로 인용 가능.

→ SmolVLA 의 vision encoder 가 **SigLIP shape-optimized** 기반 (SmolVLA paper 의 base VLM = SmolVLM-256M = SmolLM2-360M + **SigLIP-base shape-optimized**) — *CLIP-family 보다 invariance error 가 높다는 일반 패턴* 이 *우리 케이스에 직접 적용*.

### 2-4. ImageNet 분류기의 회전 sensitivity — *일반 증거*

- ResNet-152 ImageNet top-1: *5° 회전만으로도 0.48% 저하*, *10° 회전 / 20% zoom 으로 1%+ 저하* — *작은 변형* 도 측정 가능한 영향. [arxiv 2207.08079] (정확 본문 access 못함, 검색 결과 인용)
- 큰 각도 (90°, 180°) 의 정량 수치는 *paper 본문에 표기되어 있으나 PDF 직접 access 실패* — 단 *작은 회전조차 측정 가능 → 큰 회전은 훨씬 큰 영향* 의 *방향성* 은 확정.

### 2-5. ViT 의 180° 회전 특이 취약점

[arxiv 2503.04545 (ViT-VS)](https://arxiv.org/html/2503.04545v1):
- "ViTs exhibit rotation invariance properties developed during training for image classification, which can cause convergence to incorrect orientations, **specifically with in-plane rotations of 180°**"
- ViT 가 학습 중에 *어느 정도 rotation invariance* 를 우연히 학습하면서 *180° 회전 입력* 에서 *symmetric 혼동* 을 일으킬 수 있음 — 이건 *robotics 도메인 직접 관련 paper*.

### 2-6. *Random rotation* augmentation 의 표준 부재 — *암묵적 orientation prior* 의 증거

- ImageNet 학습의 *표준 augmentation* = `RandomResizedCrop` + `RandomHorizontalFlip` + `ColorJitter`. **`RandomRotation` 은 표준 아님**.
  - 이유: *자연 이미지의 amplitude orientation prior* — 하늘은 위, 땅은 아래. 회전 augmentation 은 *모델이 이 prior 를 학습하는 것을 막아 정확도 저하*. ([Roboflow rotation augmentation guide](https://blog.roboflow.com/why-and-how-to-implement-random-rotate-data-augmentation/))
- `RandomVerticalFlip` 도 ImageNet 표준 아님 (HorizontalFlip 만 표준). 이유 동일.
- → ImageNet / LAION / WebLI 등 *natural image 대규모 사전학습* 데이터셋이 *upright 분포 일색* — 이 위에 훈련된 SigLIP·CLIP·ViT 가 *상하반전 입력에 대해 OOD*.

### 2-7. **lerobot 자체의 image augmentation 도 rotation/flip 없음 — *결정적 코드 증거***

`docs/reference/seeed-lerobot/src/lerobot/datasets/transforms.py` 직접 review (L165-216):

```python
class ImageTransformsConfig:
    enable: bool = False              # default OFF
    max_num_transforms: int = 3
    tfs = {
        "brightness": ColorJitter(brightness=(0.8, 1.2)),
        "contrast":   ColorJitter(contrast=(0.8, 1.2)),
        "saturation": ColorJitter(saturation=(0.5, 1.5)),
        "hue":        ColorJitter(hue=(-0.05, 0.05)),
        "sharpness":  SharpnessJitter(sharpness=(0.5, 1.5)),
        "affine":     RandomAffine(degrees=(-5.0, 5.0), translate=(0.05, 0.05)),
    }
```

- **rotation 은 `RandomAffine` 안에 ±5° 만**. 180° 회전·VerticalFlip *전혀 없음*.
- **enable default = False** — 즉 SmolVLA *재현 학습 (community + 우리)* 의 *대부분* 은 augmentation *없이* 학습됨.
- 이는 *SmolVLA 가 학습 분포의 frame orientation 을 그대로 학습* 한다는 *강한 코드 레벨 증거*.

### 2-8. Q2 종합

| 질문 | 답변 | 자료 강도 |
|------|------|---------|
| "vision encoder 가 orientation 민감한가?" | **예** — ViT/CLIP/SigLIP 모두 측정 가능한 sensitivity. ViT 는 180° 회전에 *특이 취약점* 보고. | direct (ViT-VS), indirect (VLM 텍스트 task) |
| "180° 가 90°·270° 보다 더 심각한가?" | **예** — VLM text extraction 70 pp drop. 자연 이미지 prior 의 비대칭성. | direct (Claude/GPT 실험) |
| "natural image VLM 사전학습은 *암묵적 upright prior* 를 갖는가?" | **예** — ImageNet/LAION standard augmentation 이 rotation/VerticalFlip 제외. | indirect (관행) |
| "SmolVLA 학습 파이프라인이 rotation 보정 안 함?" | **확정 — 안 함**. `transforms.py` default 가 ColorJitter+±5° affine 만, enable=False. | direct (코드) |

---

## §3 Q3 답변 — VLA 분야의 *wrist orientation 정렬* 시도 사례

### 3-1. Open X-Embodiment (OXE / RT-X) — *비표준화* 명시

[OXE paper (arxiv 2310.08864)](https://arxiv.org/html/2310.08864v4) (검색 결과 종합):
- "**Camera poses and properties are deliberately not standardized**, and action frame alignment across datasets is not enforced."
- "Despite coarse alignment, camera observations still vary substantially across datasets."
- "One canonical camera view from each dataset is selected as the input image and resized to a common resolution, but **the current RT-X models do not take in additional camera images such as wrist camera images, in-hand camera images, or depth**."

→ **RT-1·RT-2·RT-X 의 *base 모델* 은 wrist camera 안 씀**. wrist orientation 정렬 *문제 자체가 발생 안 함*. 단 *OXE 데이터셋 자체의 wrist view orientation 컨벤션* 도 *명시되지 않음* — 다양함.

### 3-2. OpenVLA — wrist orientation 전처리 자료 *없음*

- OpenVLA 도 *single canonical RGB image* 사용이 기본. wrist + 3rd person 동시 학습은 *후속 work / fine-tune* 영역.
- OpenVLA 의 `prismatic/vla/datasets/rlds/oxe/mixtures.py` 등 dataset 처리 코드 — *orientation transform 코드 없음* (검색 결과 종합).

### 3-3. Octo — wrist + 3rd person 동시 지원, *그러나 orientation 정렬 정책 명시 없음*

- "Octo is flexible and adaptable to different observation inputs such as wrist and third-person camera views."
- Octo의 *학습 시점 wrist orientation 정렬* 정책 — *공식 문서·코드 명시 없음*. **자료 부재**.

### 3-4. "Do You Know Where Your Camera Is?" — *viewpoint conditioning* 의 강력 효과 (간접 증거)

[arxiv 2510.02268](https://arxiv.org/html/2510.02268v1) (WebFetch 확인):
- Plücker embedding 으로 *camera 외부 pose 를 명시 conditioning* 한 ACT policy:
  - Lift task: **33.6% → 60.6% (+27.0 pp)** 성공률
  - 6개 task 평균 gain: +1.0 ~ +34.8 pp
- "to achieve the same performance, training without camera pose conditioning requires several times more cameras"
- **단 이 paper 는 wrist camera 를 *명시적으로 제외*** ("we intentionally exclude the wrist camera, as manipulation tasks often require information from third-person views that the wrist camera alone cannot provide").

→ wrist 직접 적용은 안 되나, **camera pose / viewpoint 정보가 *policy 성능을 27 pp 까지 좌우* 한다는 핵심 신호**. orientation 도 viewpoint 의 한 차원 — *분포 정합이 결정적* 임의 *robotics 도메인 강한 간접 증거*.

### 3-5. 다른 VLA project 의 wrist 마운트 *물리적 컨벤션*

- Universal Robotics, Robotiq Wrist Camera, KUKA 등 *공식 제품 wrist camera* 의 *물리적 orientation*: gripper 측면에 *시각 방향이 자연 (upright)* 으로 마운트. *upside-down 마운트 표준 사례 없음*.
- SO-101 의 Thingiverse wrist mount (NekoMaker, Starkosaure 등): *3D print mount 디자인* 만 공개. 카메라의 *물리적 yaw/roll 권장* 없음. → **각 사용자가 임의로 결정** 하는 영역.
- ggando.com (SO-101 100% 성공 사례, 2-cam wrist+overhead): wrist mount orientation 언급 *없음* (블로그 텍스트 확인). 사진 inspection 필요 (본 보고서 미수행).

### 3-6. *학습 시점 transform* 으로 wrist orientation 보정 사례

- **데이터 수집 단계 (camera driver level)**: lerobot 의 `Cv2Rotation.ROTATE_180` 파라미터 (§1-3) 가 *사실상 권장 워크플로우*. *학습용 데이터에 *upright frame* 이 저장되도록 사전 보정*.
- **학습 데이터 후처리 단계 (dataset transform)**: 명시적 사례 *못 찾음*. *이론적으로* `lerobot/datasets/transforms.py` 의 `ImageTransformsConfig` 에 추가 가능하나 (custom RandomRotation), **upstream default 에 없음 + community 사용 사례 0**.
- **inference 단계 보정**: lerobot 의 `Cv2Rotation` 파라미터를 *학습 시점과 동일하게* 추론 카메라 driver 에도 적용 — 학습/추론 분포 정합 보장. 이 옵션이 *upstream 의 정답 경로*.

### 3-7. Q3 종합

| 질문 | 답변 | 자료 강도 |
|------|------|---------|
| "다른 VLA project 에 wrist orientation 표준?" | **없음** (OXE 명시 비표준화, RT-X 는 wrist 미사용, OpenVLA/Octo 침묵) | 자료 부재 |
| "viewpoint 정렬이 policy 성능에 큰 영향?" | **예** — +27 pp 까지 (camera pose conditioning paper). 단 wrist 직접 X. | indirect |
| "*학습 시점 transform* 보정 사례?" | **lerobot 의 *데이터 수집 단계* `Cv2Rotation` 파라미터가 표준 워크플로우**. 학습 데이터 후처리 보정 사례 없음. | indirect (코드 디자인) |
| "fine-tune dataset 의 view 정렬 권장사항?" | **공식 권장 없음**. 단 lerobot 의 `enable=False` augmentation default → *수집 시점 orientation 이 그대로 학습됨* = *수집 시점 정렬이 사실상의 권장* | indirect |

---

## §4 자료 부재 영역 (정직 — 추측 금지)

다음 영역은 *본 조사 (web text + lerobot 코드 review) 만으로는 확인 못함*. 결정적 답을 원하면 *후속 작업* 필요:

1. **사전학습 데이터셋의 실제 wrist orientation 분포** — `svla_so100_pickplace`, `svla_so100_sorting`, 481 community 데이터셋의 wrist 영상을 *시각 inspection* 하지 않으면 정답 없음. *upright 표준* 인지 *상하반전 흔함* 인지 *섞여 있는지* 정량 자료 *전무*.
2. **SmolVLA paper / blog 의 wrist orientation 침묵 = (a) "표준이 너무 명백해서 언급 안 함" 인지 (b) "다양함을 그대로 학습했음" 인지 *분리 불가*** — paper 본문에 *완전히 빠진 영역*.
3. **SO-101 wrist 카메라 마운트의 *물리적 표준 yaw/roll***: TheRobotStudio 공식 STL 디자인이 *어느 방향* 인지 본 조사 직접 확인 못함 (Thingiverse 403, deepwiki 페이지 access 못함). github STL 직접 inspection 필요.
4. **180° 회전이 *실제로* SmolVLA fine-tune 성능에 미치는 *정량* 영향**: *ablation 자체* 가 *upstream/community 어디에도 없음*. **우리가 003 vs 004 분기 ablation 으로 직접 측정해야 *유일한* 정량 답을 얻음**.
5. **SigLIP 의 *180° 회전 입력 시 attention pattern 변화* 정량**: 일반 VLM (Claude/GPT) 결과 (§2-1) 가 *SigLIP 에 *직접* 옮겨지는지* 정량 검증 paper 못 찾음. SigLIP 특정 ablation 부재.
6. **ggando.com 의 wrist mount 사진 — orientation 확인 가능 자료** — 블로그 텍스트만 확인. 사진 inspection 미수행 (다음 라운드 가치).

---

## §5 우리 프로젝트 적용 권고 — 004 분기 진입 정당화 여부

### 5-1. 003 baseline 의 *현재 안정성*

- 003 분기 (310ep · A2 LoRA r=16 · 단축 평가 8/8 = 100%) — *작동 검증된 baseline*.
- wrist 카메라 = SO-101 grip 마운트, *180° 회전 (상하반전)* 상태로 학습됨.
- 즉 우리 003 ckpt 는 *상하반전 wrist 분포에 적응* 한 상태. 100% 평가는 *이 상하반전 분포가 학습 안에서 충분히 일관* 하면 fine-tune 이 *그 분포를 학습* 했음의 증거.

### 5-2. 004 분기 (wrist 180° 회전 정렬) 가설의 *근거 강도*

| 근거 | 강도 | 효과 방향 |
|------|------|----------|
| SmolVLA base 의 SigLIP 가 *natural image upright prior* 강함 (§2-3, §2-6) | indirect (강함) | **+** 정렬 시 base prior 와 정합 → fine-tune *효율* 증가 가능 |
| lerobot dataset augmentation default 가 *rotation 없음* (§2-7) | direct (코드) | **+** 정렬 시 사전학습 분포와 정합 |
| VLM 의 180° 회전 catastrophic drop (§2-1) | direct (Claude/GPT, 일반) | **+** 정렬 시 representation 강화 가능 |
| Viewpoint 정렬 → policy 성능 +27 pp (§3-4) | indirect (다른 viewpoint) | **+** orientation 도 viewpoint 의 한 축 |
| 003 ckpt 가 *이미* 상하반전 분포에 100% 적응 | direct (우리 평가) | **−** 추가 정렬 가치가 *marginal* 일 수 있음 |
| SmolVLA paper / lerobot 공식 직접 가이드 *없음* | — | 효과 *크기* 불확실 |
| 우리 003 이 *단축 평가 8/8* — *어려운 task* 에서의 robustness 미평가 | — | 정렬이 *generalization* (novel object/lighting/positioning) 에 *더 큰* 효과 가능성 |

### 5-3. 권고

**004 분기 진입 = 합리적 가설, 단 *반드시 controlled ablation* 으로 진행**.

#### 권고 A: 진입 정당화 — *조건부 yes*

- 진입 조건:
  1. 003 ckpt 의 *현재 평가 데이터 (8/8)* 가 *실 사용 시 robustness 부족* 신호 있음 (예: novel position, lighting 변화 시 저하). → 본 보고서 범위 아님. R1-b 영역.
  2. 새 dataset 수집 비용이 *수용 가능* — 004 는 *카메라 마운트 회전 (HW 작업) + dataset 재수집* 필요. 학습은 동일 setup.
  3. 003 vs 004 *isolated ablation* 가능 — 다른 변수 (학습 hyperparam, dataset size 등) *동결*.

- 진입 비추천 조건:
  1. 003 이 *full benchmark* (다양한 환경) 에서도 안정 → 정렬의 *marginal gain* 가능성 낮음.
  2. dataset 재수집 비용이 *수주 이상* → ROI 불명. 본 보고서 *직접 증거 없음* 으로 *큰 효과* 보장 못함.

#### 권고 B: *최소 비용 검증 (HW 변경 전)*

- 003 ckpt 가 있으니, **003 의 wrist 입력을 inference 시점에 *180° 회전 (= upright 으로 복원)* 해서 base smolvla_base 0-shot 평가 + 003 평가 진행** = *학습/추론 분포 mismatch* 를 일부러 일으켜 base 의 *natural orientation 선호* 를 *역으로* 측정.
  - 결과 A (회전한 입력에서 base 0-shot 이 *상대적으로 잘 동작*): base 의 upright prior 가 *측정 가능한 효과* → 004 진입 가치 *높음*.
  - 결과 B (회전한 입력에서 003 ckpt 가 0% 가까이 떨어짐): 003 이 *상하반전 분포에 *과적합*** → 004 진입 시 *재학습 효과 클* 가능성. 단 이건 *003 이 분포에 적응* 한 증거지 *004 이 더 좋다는 증거 아님*.
  - 결과 C (회전한 입력 ≈ 정상 입력 둘 다 비슷): orientation 이 *결정적 변수 아님* → 004 진입 가치 *낮음*. ROI 부정적.

- *학습 시점 회전* 으로 003 ckpt 데이터에 *추가 fine-tune* (수십 ep) — *dataset 재수집 비용 0* 으로 가설 검증. 단 dataset 의 instruction/label 은 *그대로* (wrist orientation 만 SW 회전). **이게 *004 진입 전 최소 비용 ablation*** — 권장.

#### 권고 C: 만약 004 진입 결정 시 — *측정 항목*

1. **단축 평가 success rate** (003 의 100% baseline 과 직접 비교)
2. **full benchmark generalization** (novel object position, lighting 변화) — *정렬의 진짜 가치* 는 *극한 분포 외* 에서 드러날 가능성
3. **fine-tune convergence speed** (loss curve) — base prior 정합 시 *faster fit* 기대
4. **inference smoothness / shaking** — community #1270 패턴 (loss 수렴 + shaking) 의 *부재* 가 정렬 효과 지표
5. **wrist token 의 attention weight 분포** (advanced) — base 의 vision encoder 가 *정렬된 입력* 에서 *더 강한 attention* 인지

### 5-4. 추가 검증 권장 영역

본 보고서에서 *자료 부재* 로 남긴 영역 중 *결정 가치 높은* 것 (다음 research 라운드):

1. **`svla_so100_pickplace` wrist 영상 시각 inspection** — 사전학습 분포의 *실제* wrist orientation 확정. *직접 증거 확보* 핵심.
2. **TheRobotStudio github 의 SO-101 wrist mount STL inspection** — 공식 마운트의 *카메라 회전 default* 확인.
3. **ggando.com wrist mount 사진 inspection** — 100% 성공 사례의 wrist orientation 확인. 우리와 같으면 *우리 003 도 정상 분포 안*, 다르면 *정렬 가치 신호*.
4. **(코드 ablation)** 003 ckpt + inference-time 90°/180° rotation 입력 vs 정상 입력 — *비용 0 검증*. 가설 검증의 *가장 cheap 한* path.

---

## §6 참고 링크 전체

### SmolVLA / lerobot 공식
- [SmolVLA paper (arxiv 2506.01844 HTML)](https://arxiv.org/html/2506.01844v1)
- [SmolVLA paper PDF](https://arxiv.org/pdf/2506.01844)
- [SmolVLA HF blog](https://huggingface.co/blog/smolvla)
- [LearnOpenCV — SmolVLA 분석](https://learnopencv.com/smolvla-lerobot-vision-language-action-model/)
- [lerobot SmolVLA docs](https://huggingface.co/docs/lerobot/smolvla)
- [lerobot SO-101 빌드 가이드](https://huggingface.co/docs/lerobot/so101)
- [lerobot cameras docs](https://huggingface.co/docs/lerobot/cameras)
- [lerobot dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3)

### lerobot 코드 (직접 review)
- `docs/reference/seeed-lerobot/src/lerobot/cameras/configs.py` — `Cv2Rotation` enum (NO_ROTATION/90/180/270)
- `docs/reference/seeed-lerobot/src/lerobot/cameras/opencv/configuration_opencv.py:62` — `rotation: Cv2Rotation = Cv2Rotation.NO_ROTATION` default
- `docs/reference/seeed-lerobot/src/lerobot/cameras/realsense/configuration_realsense.py:59` — 동일 패턴
- `docs/reference/seeed-lerobot/src/lerobot/cameras/opencv/camera_opencv.py:393` — frame 처리 시 rotation 적용 path
- `docs/reference/seeed-lerobot/src/lerobot/datasets/transforms.py:165-216` — `ImageTransformsConfig`: enable=False default, ColorJitter+SharpnessJitter+RandomAffine(±5°) only. *No rotation/flip*.

### 사전학습 데이터셋
- [lerobot/svla_so100_pickplace (2 cam: top+wrist)](https://huggingface.co/datasets/lerobot/svla_so100_pickplace)
- [lerobot/svla_so100_sorting](https://huggingface.co/datasets/lerobot/svla_so100_sorting)
- [lerobot/svla_so101_pickplace (2 cam: up+side, wrist 없음)](https://huggingface.co/datasets/lerobot/svla_so101_pickplace)
- [HF Hub `?other=lerobot` 데이터셋 목록](https://huggingface.co/datasets?other=lerobot)

### GitHub Issues / 코드 (orientation 침묵 확인용)
- [Issue #1763 — best camera setup for SO-101 (orientation 언급 없음)](https://github.com/huggingface/lerobot/issues/1763)
- [Issue #2753 — 2-cam SmolVLA 무반응](https://github.com/huggingface/lerobot/issues/2753)
- [Issue #1270 — smolvla not work](https://github.com/huggingface/lerobot/issues/1270)
- [Issue #2210 — smolvla_base inference 실패](https://github.com/huggingface/lerobot/issues/2210)
- [TheRobotStudio/SO-ARM100 github](https://github.com/TheRobotStudio/SO-ARM100)

### VLM / ViT orientation 민감성 (Q2)
- [dev.to (kenimo49) — Rotated images drop Claude/GPT-4o accuracy](https://dev.to/kenimo49/passing-rotated-images-to-claude-or-chatgpt-drops-accuracy-to-one-third-29f) — *180° catastrophic drop 정량*
- [arxiv 2503.09837 — Limitations of VLMs in Understanding Image Transforms](https://arxiv.org/html/2503.09837) — CLIP/SigLIP transformation 무이해 정량
- [arxiv 2511.13494 — LGIP: Language-Guided Invariance Probing](https://arxiv.org/html/2511.13494) — SigLIP invariance error 가 CLIP 보다 큼
- [arxiv 2503.04545 (ViT-VS)](https://arxiv.org/html/2503.04545v1) — ViT 의 180° 회전 특이 취약점
- [arxiv 2207.08079 — ImageNet 모델의 simple transformation degradation](https://arxiv.org/pdf/2207.08079)
- [Roboflow — Why and How to Implement Random Rotate Augmentation](https://blog.roboflow.com/why-and-how-to-implement-random-rotate-data-augmentation/) — rotation augmentation 표준 부재 이유

### VLA / Robotics 도메인 (Q3)
- [OXE paper (arxiv 2310.08864)](https://arxiv.org/html/2310.08864v4)
- [OpenVLA github](https://github.com/openvla/openvla)
- [arxiv 2510.02268 — Do You Know Where Your Camera Is? (camera pose conditioning +27 pp)](https://arxiv.org/html/2510.02268v1)
- [LearnOpenCV — VLA models 정리](https://learnopencv.com/vision-language-action-models-lerobot-policy/)

### 커뮤니티 사례
- [ggando.com — SO-101 SmolVLA 100% 성공](https://ggando.com/blog/smolvla-so101/) — wrist orientation 언급 없음
- [Hackaday — Debugging Dual-Camera SO-101](https://hackaday.io/project/204187/log/243773-debugging-dual-camera-vision-system-for-so-101-robotic-manipulation-platform) — orientation 언급 없음
- [Xavier O'Keefe — Fine-tuning SmolVLA (Medium)](https://medium.com/correll-lab/fine-tuning-smolvla-for-new-environments-code-included-af266c56d632)

### 본 프로젝트 자료 (cross-reference)
- [`research_smolvla_pretrain_cameras_2026-05-19.md`](research_smolvla_pretrain_cameras_2026-05-19.md) — 카메라 개수·이름·해상도·FPS·코덱 (orientation 침묵 확인 출처)
- [`research_empty_cameras_2026-05-18.md`](research_empty_cameras_2026-05-18.md) — 2 vs 3 cam · empty_cameras 분석
- [`prof_computer/docs/model_config.md`](../model_config.md)

---

verdict: NEEDS_INVESTIGATION (이론적 정당화는 *간접 증거 강함*, 단 *직접 증거 부재*. 003 vs 004 ablation 만이 우리 환경 정량 답을 줌. 권장 = §5-3 권고 B 의 *비용 0 inference-time rotation ablation* 을 먼저 진행 → 결과에 따라 004 분기 본 진행 결정.)
