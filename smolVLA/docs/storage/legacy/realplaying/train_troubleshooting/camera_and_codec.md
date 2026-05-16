# 카메라 해상도 · 모델 입력 · 비디오 코덱 — config 값 해설

> **목적**: `base_config.yaml` / `record_config.yaml` 의 카메라·코덱 설정값이 "무엇을 기준으로 정해지는지", "무엇이 고정이고 무엇이 튜닝 가능한지" 정리. 자매 문서: [data_collection.md](data_collection.md), [training.md](training.md), [backlog.md](backlog.md).
> **작성**: 2026-05-14 — leftarm_v2 수집 준비 중 Q&A 정리.

---

## 1) 카메라 해상도 ↔ 화각 (FOV)

### 핵심 — 해상도를 낮추면 둘 중 하나

`base_config.yaml` 의 `cameras.<name>.width/height` 를 낮출 때, 카메라/드라이버에 따라 **두 가지 다른 동작** 중 하나가 일어난다:

| 방식 | 화각 (FOV) | 디테일 |
|---|---|---|
| **다운스케일** — 전체 센서를 읽고 축소 | 동일 | ↓ |
| **크롭 (windowing)** — 센서 중앙 일부만 읽음 | **좁아짐** | 픽셀 밀도 유지 |

→ "해상도 = 화질" 이 아니다. 해상도가 **화각(무엇이 보이느냐)** 까지 바꿀 수 있다.

### 판단 단서 — aspect ratio

같은 aspect ratio 끼리의 해상도 변경은 보통 다운스케일 (FOV 동일). aspect ratio 가 바뀌면 크롭일 가능성이 높다.

### 카메라별 지원 해상도 (2026-05-14 `v4l2-ctl --list-formats-ext` 확인, MJPG @ 30fps)

| 카메라 | 30fps 지원 해상도 | 현재 설정 | aspect |
|---|---|---|---|
| **top (YJX-C5)** `/dev/video0` | 1920×1080, 1280×720, **640×480**, 640×360 | 640×480 | 640×480 = 4:3 |
| **wrist (Innomaker U20CAM-720P)** `/dev/video2` | 1280×720, 800×600, **640×480**, 320×240 | 640×480 | 640×480 = 4:3 |

추정 (미검증):
- **top (YJX-C5)**: 640×480 (4:3) — 최대 4:3 인 2592×1944 도 4:3 → 같은 4:3 다운스케일이면 FOV 동일 가능성. 16:9 모드 (1920×1080 등) 는 FOV 다를 수 있음.
- **wrist (Innomaker U20CAM-720P)**: 이름이 "720P" = native 1280×720 (16:9) 추정. 4:3 모드 (640×480 등) 가 센서 native 16:9 의 좌우 크롭이라면 → **640×480 이 1280×720 보다 가로 화각이 좁을 수 있음**.

### ⚠️ 미해결 — 화각 테스트 필요

다운스케일인지 크롭인지는 **실제 캡처해서 비교해야 확정**된다. 수집 전에 task 작업 영역(물체·박스)이 화각에 다 들어오는지 확인 필수:

```bash
# 같은 장면을 640x480 / 1280x720 으로 캡처해서 가장자리 범위 비교
ffmpeg -f v4l2 -input_format mjpeg -video_size 640x480  -i /dev/video2 -frames:v 1 /tmp/wrist_640.png -y
ffmpeg -f v4l2 -input_format mjpeg -video_size 1280x720 -i /dev/video2 -frames:v 1 /tmp/wrist_1280.png -y
# 1280 쪽이 더 넓은 범위를 담으면 → 크롭 (640 은 좁은 화각)
# 같은 범위면 → 다운스케일 (640 은 같은 화각, 낮은 디테일)
```

→ 크롭이 맞다면 task 영역이 다 들어오는 최소 해상도를 선택. **화질이 아니라 "무엇이 보이느냐" 의 문제라 수집 시작 전 확정 권장.**

---

## 2) 모델 입력 config — `resize_imgs_with_padding` / `input_features`

학습/추론 시 보이는 SmolVLA policy config:
```
resize_imgs_with_padding: (512, 512)
input_features: observation.images.camera1: shape (3, 256, 256)
```

| 값 | 변경 가능? | 권장 |
|---|---|---|
| `resize_imgs_with_padding: (512,512)` | 기술적으로는 가능 (`--policy.resize_imgs_with_padding`) | ❌ **fine-tune 시 건드리지 말 것** — `smolvla_base` 가 (512,512) 로 사전학습됨. 바꾸면 사전학습 가중치와 미스매치 |
| `input_features shape (3,256,256)` | dataset features + policy config 에서 **파생** | 직접 설정값 아님 — 데이터셋/모델 구조에서 결정 |

### 핵심 — 카메라 캡처 해상도 ≠ 모델 입력 해상도 (별개 레이어)

```
카메라 캡처 (640×480, base_config.yaml 에서 조정 가능)
        ↓
SmolVLA 내부 resize (→ 512×512 / 256×256, 사전학습에 고정)
        ↓
모델이 보는 입력
```

→ 카메라 캡처 해상도를 올려도 모델은 어차피 ~256~512 로 축소된 이미지만 본다. **policy 학습 성능 관점에선 고해상도 캡처가 거의 무의미**. 단 §1 의 화각 문제는 별개 — 화각이 좁아 task 영역이 안 들어오면 그건 해상도(캡처)로 해결해야 함.

fine-tune 워크플로우에선 이 두 값은 사전학습 모델에 묶인 상수로 취급. 바꾸려면 from-scratch 학습 영역이 되어 LoRA / smolvla_base 의 이점이 사라짐.

---

## 3) 비디오 코덱 — libsvtav1 (CPU) vs NVENC (GPU)

### 배경

| 코덱 | 인코딩 위치 | 선택 이유 |
|---|---|---|
| `libsvtav1` | CPU (Grace) | Walking RL 이 GPU 점유 중일 때 GPU 코덱 회피 (CLAUDE.md Walking RL 보호 원칙). leftarm_v1 에서 사용 |
| `h264_nvenc` / `hevc_nvenc` / `av1_nvenc` | **GPU 전용 NVENC 하드웨어 블록** | Walking RL 미가동 시 더 적합 |

### 관찰된 문제 (2026-05-11, leftarm_v1 수집 중)

`libsvtav1` + `streaming_encoding=true` 조합에서 record loop 이 30fps 미달 ("Record loop is running slower than target FPS" 경고 다수). **CPU 인코딩이 병목**.

### NVENC 가용성 (2026-05-14 확인)

- ✅ ffmpeg 에 `h264_nvenc`, `hevc_nvenc`, `av1_nvenc` 모두 존재
- ✅ lerobot `VALID_VIDEO_CODECS` 가 NVENC 인코더 포함 ([video_utils.py:55](../../docs/reference/lerobot/src/lerobot/datasets/video_utils.py#L55))
- ✅ DGX GB10 하드웨어 인코더 존재

### 핵심 — NVENC 은 CUDA/tensor 코어와 별개 하드웨어 블록

NVENC 은 GPU 의 별도 전용 인코딩 블록이라, **Walking RL 학습이 가동 중이어도 tensor 코어 throughput 에 거의 영향 없음**. CLAUDE.md 의 "Walking RL 가동 시 GPU 코덱 회피" 는 보수적 규칙 — 실제 영향은 작지만 규칙 자체는 존중.

### 의사결정 (leftarm_v2) — 2026-05-15 실측 후 갱신

| 상황 | 권장 코덱 |
|---|---|
| **Walking RL 미가동** (현재) | **`h264_nvenc`** — CPU 부하 분리(인코딩이 GPU NVENC ASIC 으로 빠짐, Grace CPU 는 record loop · MJPG 디코딩 · display_data 에 집중) + **학습 단계 디코딩 효율**(h.264 디코더가 av1 보다 가벼움 — PyAV/decord 경로). `av1_nvenc` 은 디코딩 부담 ↑ |
| Walking RL 가동 중 | `libsvtav1` (CLAUDE.md 원칙 준수) |

설정 위치: [record_config.yaml](../../finetune/leftarm_v2/config/record_config.yaml) 의 `dataset.vcodec`.

> ⚠️ **실측 정정 (2026-05-15, [collection_log.md 발견된 이슈 §](leftarm_v2/collection_log.md))**: 원래 NVENC 채택 동기는 "30fps 회복" (libsvtav1 CPU 병목 가설) 이었으나, h264_nvenc 1·2·3차 수집 결과 record loop sub-30Hz 가 동일하게 지속 → **인코더가 병목이 아님** 이 확인됨. 진짜 원인은 입력단 (USB topology / display_data / Corrupt JPEG) 추정. 단 **dataset 의 timestamp 는 `frame_index/fps` 로 이상값 저장되어 무결성 유지** (전수 분석 std 0.00ms, gap 0) → **학습 영향 경미, polish 격하**. NVENC 의 가치는 위 표의 두 가지 (CPU 부하 분리 + 학습 디코딩 효율) 로 재정립.

### 주의

- leftarm_v2 는 **신규 dataset** 이라 코덱 자유 선택 가능 (leftarm_v1 의 libsvtav1 과 일치 불필요).
- 단 **leftarm_v2 내 모든 수집 차수는 같은 코덱 유지** — 차수마다 코덱 바뀌면 dataset 포맷 비일관.
- 수집 도중 Walking RL 재개 가능성이 높으면 처음부터 `libsvtav1` 유지가 안전. "당분간 Walking RL 안 함" 이 확실하면 NVENC 권장.

---

## 결정 상태 요약

| # | 주제 | 상태 |
|---|---|---|
| 1 | 카메라 해상도 ↔ 화각 | ⚠️ **미해결** — 다운스케일/크롭 여부 ffmpeg 테스트로 확정 필요. 수집 시작 전 권장 |
| 2 | `resize_imgs_with_padding` / `input_features` | ✅ **확정** — 사전학습 모델에 묶인 상수. fine-tune 시 변경 금지 |
| 3 | 비디오 코덱 | ✅ **확정 (2026-05-15)** — Walking RL 미가동 → `h264_nvenc` 채택 (record_config.yaml `dataset.vcodec`). 권장 이유: 30fps 회복 가설 반박됨 (실측), **CPU 부하 분리 + 학습 디코딩 효율**로 재정립 |
