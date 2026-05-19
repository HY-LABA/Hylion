# SmolVLA 커뮤니티 사전학습 데이터셋의 카메라 뷰 구성 리서치 보고서

**작성일:** 2026-05-19
**대상:** leftarm_v2 파인튜닝 데이터 설계용 레퍼런스
**범위:** HuggingFace `lerobot/smolvla_base` 사전학습에 쓰인 커뮤니티 데이터셋의 영상 구성 분석

---

## 한줄 요약 (TL;DR)

SmolVLA 사전학습은 **SO-100 위주의 481개 커뮤니티 데이터셋 · 약 22.9K 에피소드 · 10.6M 프레임**을 사용했고, 다양한 카메라 이름을 **`OBS_IMAGE_1`(top) / `OBS_IMAGE_2`(wrist) / `OBS_IMAGE_3`(side)** 의 3단 우선순위로 수동 매핑했다. 실제 커뮤니티 데이터셋 키는 `observation.images.top` + `observation.images.wrist` 조합이 가장 흔하고, **480×640 @ 30 fps, AV1 코덱**이 사실상의 표준이다. 파인튜닝 시에는 카메라 이름 자체보다 **카메라 개수·순서·해상도·FPS의 일관성**이 결정적이다.

---

## 1. 카메라 뷰 구성 개요 (가장 흔한 패턴)

- **2-카메라 셋업이 사실상 표준**이다. SmolVLA 공식 학습/평가에 사용된 레퍼런스 데이터셋 `lerobot/svla_so100_pickplace`, `lerobot/svla_so100_sorting`, `lerobot/svla_so101_pickplace` 가 모두 2-카메라 구성이다.
- 가장 흔한 조합:
  - **SO-100 계열**: `top` + `wrist` (overhead + 손목 장착)
  - **SO-101 계열**: `up` + `side` (overhead + 측면)
- 논문이 "prioritizing top, wrist, and side perspectives"라고 명시했으므로, 일부 데이터셋은 **3-카메라(top + wrist + side / front)** 까지 가는 경우도 있지만 수적 비율로는 소수다.
- 단일 카메라 데이터셋도 존재하나(low-quality 또는 phone teleop 기반), SmolVLA의 필터는 의도적으로 다중 카메라 쪽을 우대했다 (블로그가 명시한 "visual quality, task coverage" 기준에 부합).

> **주의:** 커뮤니티 데이터셋 전체(481개)에 대해 단일/2/3-카메라 비율의 공식 통계 표는 논문/블로그에서 **공개된 적 없다**. 위 비율은 SmolVLA 팀이 직접 공개한 SO-100/SO-101 레퍼런스 데이터셋과, HF Hub `?other=lerobot` 트렌딩 샘플을 정성적으로 본 결과다.

---

## 2. 자주 등장하는 view key 목록 (실제 예시)

| view key | 의미 | 실제 데이터셋 예시 |
|---|---|---|
| `observation.images.top` | overhead/top-down | `lerobot/svla_so100_sorting`, `Tomas0413/so100_screw_lid_v0` |
| `observation.images.wrist` | gripper/손목 장착 | `lerobot/svla_so100_sorting`, `Tomas0413/so100_screw_lid_v0` |
| `observation.images.up` | overhead (SO-101 컨벤션) | `lerobot/svla_so101_pickplace` |
| `observation.images.side` | 측면 | `lerobot/svla_so101_pickplace` |
| `observation.images.front` | 정면 | SmolVLA 공식 SO-101 inference 예제 (`--robot.cameras="{ front: ... }"`) |
| `observation.images.laptop` | 노트북 내장 카메라 | SO-100 공식 튜토리얼 (Seeed/AIFITLAB) 기본 셋업 |
| `observation.images.phone` | 폰 카메라 | LeRobot Phone teleop 문서 |
| `OBS_IMAGE_1/2/3` | **사전학습 시 내부 표준 키** (top/wrist/side로 매핑) | SmolVLA 논문 내부 표준화 |

**핵심:** 사전학습은 `OBS_IMAGE_*` 라는 정규화된 이름으로 진행됐지만, **모델이 카메라 이름의 semantic을 보지는 않는다**. 코드 레벨에서는 모든 이미지 토큰을 단순 concat 하므로 (huggingface/lerobot Issue #1763의 사용자 분석), 실제로 중요한 건 **순서와 개수**다.

---

## 3. 비디오 사양 (해상도/FPS/코덱)

3개 SmolVLA 레퍼런스 데이터셋의 `meta/info.json` 직접 확인 결과 사실상의 표준은 다음과 같다:

| 항목 | 값 |
|---|---|
| 해상도 | **480 × 640 × 3** (H×W×C). 일부 커뮤니티 데이터셋은 720p (예: `Tomas0413/so100_screw_lid_v0` 1280×720). |
| FPS | **30 fps** (논문 본문 "real-world frame-rate of 30 frames per second, Δt=33 ms" 와 일치) |
| 코덱 | **AV1, pix_fmt=yuv420p** (HF SVLA 레퍼런스 데이터셋 기본값). 일부 커스텀 데이터셋은 MJPEG/H.264. |
| 모델 입력 변환 | 학습 파이프라인에서 **(3, 256, 256)** 으로 리사이즈 (LearnOpenCV 분석 + Issue #2210 policy config 로그 확인). 블로그/논문 별도 표기로 SigLIP global image는 내부적으로 512×512 처리 단계도 존재. |
| 오디오 | 없음 |

---

## 4. SmolVLA 논문의 필터링 기준

블로그/논문 문구를 종합하면 (출처: HF Blog "SmolVLA: Efficient Vision-Language-Action Model trained on Lerobot Community Data"):

- 시작점: HF Hub `?other=lerobot` 태그 데이터셋 전체.
- 필터 축:
  - **(a) embodiment type** — 대부분 SO-100으로 한정
  - **(b) episode count**
  - **(c) visual quality**
  - **(d) frame coverage / task coverage**
- 결과: **481개 데이터셋, 22.9K 에피소드, 10.6M 프레임** (논문/LearnOpenCV). 블로그 본문에서는 manual review 기준 "487개"라는 표현도 있어 약간의 표기 차이가 존재.
- 카메라 표준화: *"We manually mapped each camera to a standardized view type — prioritizing top, wrist, and side perspectives — and renamed them as OBS_IMAGE_1, OBS_IMAGE_2, and OBS_IMAGE_3, respectively."*
- 30 fps로 통일.
- Task 라벨은 **Qwen2.5-VL-3B-Instruct**로 짧고 행동 시작 verb(Pick/Place/Open)로 재생성.

**카메라 개수에 대한 hard cutoff(예: "2개 이상만")는 논문/블로그에 명시되어 있지 않다.** Top/wrist/side 우선순위만 명문화되어 있으며, "single-camera 데이터셋 비율"의 공식 통계도 보고되지 않았다 — 모르는 것은 모른다고 표시한다.

---

## 5. SO-100 / SO-101 컨벤션

- **하드웨어**: SO-100은 "low-cost, 3D-printable, 6-DoF" arm. SO-101은 후속이며 조립이 빠르고 모터가 더 부드러운 개선판 (논문 본문).
- **공식 SO-100 튜토리얼 (Seeed Studio Wiki, AIFITLAB)** 의 기본 카메라 이름은 `laptop` (노트북 내장) + `phone` (폰)인 경우가 많고, 이후 사용자가 학습용으로 `top` + `wrist`로 리네임하는 흐름이다.
- **공식 SmolVLA SO-101 inference 예제** (HF docs `lerobot/smolvla`)는 단일 카메라 이름으로 `front`를 사용한다:

  ```bash
  --robot.cameras="{ front: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30}}"
  ```

  즉 HuggingFace 공식 가이드조차 데이터셋 컨벤션(top/wrist 또는 up/side)과 다른 이름을 평가 명령에 그대로 쓴다. → **이름의 자유도**가 사실상 보장된다는 또 다른 증거.

- SO-101의 SmolVLA 레퍼런스 데이터셋 `lerobot/svla_so101_pickplace`는 `up` + `side` (top 대신 up).
- GitHub Issue #1763 (정확히 본 질문과 같은 케이스: "best camera setup for fine-tuning SmolVLA with so101"): **공식 maintainer의 단정적 답변은 아직 없다**. 사용자 자체 결론은 *"train·inference에서 카메라 순서가 동일하면 성능이 좋아진다"* 였다.

---

## 6. 파인튜닝 시 주의점 / view 이름 매칭 권장사항

1. **이름은 자유**, 그러나 **개수와 순서는 고정**: SmolVLA는 image token을 단순 concat 하므로 (Issue #1763 분석), 학습 dataset의 `features` 순서가 inference의 `--robot.cameras` 순서와 동일하지 않으면 성능이 무너진다.

2. **"empty camera" 이슈** (현재 leftarm_v2의 한쪽 스트림이 검정 상태): 다음 중 하나로 처리할 것을 권장 —
   - **(a) 그 카메라를 데이터셋 features에서 아예 제거 (권장).** SmolVLA는 카메라 1개로도 동작한다 (`smolvla_base`는 multi-view, proprio, optional language를 입력 받지만, 카메라 수는 데이터셋에 맞춰 변경됨).
   - (b) 빈 텐서를 그대로 두면 image token이 zero에 가까운 분포가 되어, 사전학습에서 본 적 없는 입력 분포라 generalization을 해친다.

3. **해상도/FPS는 480×640 @ 30fps** 로 맞추는 것이 가장 안전 (사전학습 분포에 가장 가까움). 720p로 수집해도 학습 파이프라인이 256×256으로 리사이즈하므로 큰 영향은 없으나 disk/IO 비용이 늘 뿐이다.

4. **뷰 이름**은 `top` + `wrist` 조합이 사전학습 분포에 가장 자주 등장했을 가능성이 높다 (SmolVLA가 OBS_IMAGE_1=top, OBS_IMAGE_2=wrist로 0순위 매핑). 단, **모델 입력 단계에서는 어차피 익명 토큰**이라 이름 그 자체는 학습 동력이 아니다 — 의미는 "수집 시 어떤 시점을 기록했는가"에 있다. **첫번째 카메라를 overhead, 두번째 카메라를 wrist로 두는 물리적 셋업**을 권장.

5. SO-101이라면 공식 레퍼런스 `svla_so101_pickplace`처럼 `up + side` 도 검증된 조합이지만, **wrist 카메라가 없다는 점에서 occlusion에 약해진다**는 단점이 있다.

6. `Inference lerobot/smolvla_base with so-101 failed` (Issue #2210)처럼 정규화 통계(`mean is infinity`) 에러는 카메라 이슈가 아니라 weight load 문제. 카메라 셋업과 별개로 발생할 수 있음을 분리해서 진단할 것.

---

## 7. 참고 링크

- SmolVLA 논문: https://arxiv.org/abs/2506.01844  (HTML: https://arxiv.org/html/2506.01844v1)
- HF Blog: https://huggingface.co/blog/smolvla
- LearnOpenCV 정리: https://learnopencv.com/smolvla-lerobot-vision-language-action-model/
- 공식 SmolVLA 문서: https://huggingface.co/docs/lerobot/smolvla
- 모델 카드: https://huggingface.co/lerobot/smolvla_base
- 레퍼런스 데이터셋 (SO-100, top+wrist): https://huggingface.co/datasets/lerobot/svla_so100_sorting
- 레퍼런스 데이터셋 (SO-101, up+side): https://huggingface.co/datasets/lerobot/svla_so101_pickplace
- 커뮤니티 SO-100 (720p MJPEG 사례): https://huggingface.co/datasets/Tomas0413/so100_screw_lid_v0
- GitHub Issue #1763 (best camera setup for SO-101 + SmolVLA): https://github.com/huggingface/lerobot/issues/1763
- GitHub Issue #2210 (smolvla_base inference 실패 사례): https://github.com/huggingface/lerobot/issues/2210
- LeRobot Dataset v3 문서: https://huggingface.co/docs/lerobot/lerobot-dataset-v3
- HF Hub 커뮤니티 데이터셋 목록: https://huggingface.co/datasets?other=lerobot
- Phone teleop 문서: https://huggingface.co/docs/lerobot/phone_teleop

---

## 핵심 발견 요약 (leftarm_v2 적용 관점)

- 본 프로젝트의 **"empty camera" 문제**는 SmolVLA 분포 측면에서 위험하므로 **빈 카메라를 데이터셋에서 제거하고 단일/이중 카메라로 재정의하는 쪽이 안전**하다.
- 카메라 이름은 `top` / `wrist` 컨벤션 권장하되, 결정적인 건 **카메라 개수와 순서를 학습-추론 사이에서 동일하게 유지**하는 것.
- 해상도/FPS는 **480×640 @ 30 fps** 이 사실상 표준 — 새로 수집하거나 리캡처할 때 이 스펙 우선.

관련 문서: [research_empty_cameras_2026-05-18.md](research_empty_cameras_2026-05-18.md), [lerobot_smolvla_training_best_practice.md](lerobot_smolvla_training_best_practice.md)
