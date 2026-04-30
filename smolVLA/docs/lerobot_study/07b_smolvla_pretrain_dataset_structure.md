# 사전학습 데이터셋 구조 분석

> 기준: HuggingFace `lerobot/svla_so100_pickplace` + lerobot/seeed-lerobot 코드 레퍼런스
> 작성일: 2026-04-29
> 목적: 03 마일스톤 추론 환경의 입력 스펙 확정 + 06 양팔 진입 시 결정 사항 정리
> 선행 읽기: `07_smolvla_base_weight_inspection.md` (smolvla_base config 실측값)

---

## 1) 단일팔: `lerobot/svla_so100_pickplace`

### 1-1) 핵심 주의사항 — 카메라 키 불일치

> **smolvla_base config.json의 입력 카메라 키**는 `camera1 / camera2 / camera3` (3대)
> **svla_so100_pickplace 데이터셋의 카메라 키**는 `top / wrist` (2대)

두 키가 다르다. 즉 smolvla_base는 svla_so100_pickplace 단독이 아닌 **LeRobot Community Datasets를 집계한 더 큰 데이터셋**으로 학습된 것으로 추정된다. camera1/2/3는 커뮤니티 데이터셋 통합 시 사용된 키 컨벤션.

03 추론 환경의 입력 스펙은 아래 §1-2에 기반해 결정하되, 카메라 키 결정은 §4 정리 참조.

### 1-2) meta/info.json 실측값

| 항목 | 값 |
|---|---|
| codebase_version | v3.0 |
| robot_type | `so100` |
| total_episodes | **50** |
| total_frames | 19,631 |
| total_tasks | 1 |
| fps | **30** |
| splits | train: 0\~50 |

### 1-3) 카메라 스펙

| 키 | shape (H×W×C) | 해상도 | codec | fps |
|---|---|---|---|---|
| `observation.images.top` | 480 × 640 × 3 | 640×480 | av1 | 30.0 |
| `observation.images.wrist` | 480 × 640 × 3 | 640×480 | av1 | 30.0 |

- 카메라 2대
- 원본 해상도 640×480 → SmolVLA `resize_imgs_with_padding=[512,512]`로 전처리됨
- normalization_mapping: VISUAL = **IDENTITY** (픽셀값 정규화 없이 그대로)

### 1-4) state / action 스펙

| 항목 | shape | 이름 (6 DOF) | dtype |
|---|---|---|---|
| `observation.state` | `[6]` | main_shoulder_pan, main_shoulder_lift, main_elbow_flex, main_wrist_flex, main_wrist_roll, main_gripper | float32 |
| `action` | `[6]` | (동일) | float32 |

- `max_state_dim=32`, `max_action_dim=32` — 6 DOF → 32 dim으로 zero-padding 후 모델 입력
- normalization_mapping: STATE = **MEAN_STD**, ACTION = **MEAN_STD** (`policy_preprocessor_step_5_normalizer_processor.safetensors`에 통계 저장)

### 1-5) 태스크 instruction

```
"Pick up the cube and place it in the box."
```

- `meta/tasks.parquet`에서 실측. task_index=0, 단일 태스크.
- `config.json`의 `tokenizer_max_length=48` 기준 약 9 tokens — 여유 충분.

---

## 2) 양팔: bi_so_follower / bi_so_leader 코드 분석

### 2-1) 구조 개요

`BiSOFollower`는 두 `SOFollower` (단일팔) 인스턴스를 합성하는 래퍼.

```
BiSOFollower
├── self.left_arm  = SOFollower(left_arm_config)
└── self.right_arm = SOFollower(right_arm_config)
```

카메라는 두 팔의 카메라를 단순 merge: `self.cameras = {**left.cameras, **right.cameras}`

### 2-2) state / action 키 컨벤션

단일팔 `SOLeader/SOFollower`의 모터 이름 (6개):
```
shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
```

양팔에서는 `left_` / `right_` prefix를 붙여 12 DOF로 확장:

| 컴포넌트 | 키 패턴 | 개수 |
|---|---|---|
| 좌팔 state / action | `left_shoulder_pan.pos`, `left_shoulder_lift.pos`, … `left_gripper.pos` | 6 |
| 우팔 state / action | `right_shoulder_pan.pos`, `right_shoulder_lift.pos`, … `right_gripper.pos` | 6 |
| **합계** | | **12 DOF** |

`action_features`도 동일 구조 — `BiSOLeader.action_features`에서 좌/우 각 6개를 prefix 붙여 반환.

### 2-3) 카메라 키 컨벤션

카메라는 각 팔의 config에서 지정한 카메라 이름에 `left_` / `right_` prefix:

```python
# bi_so_follower.py
self.cameras = {**self.left_arm.cameras, **self.right_arm.cameras}
# → {"left_<cam_name>": ..., "right_<cam_name>": ...}
```

실제 키 이름은 각 `SOFollowerConfig.cameras` dict에서 결정 — 예시: `left_top`, `right_wrist` 등. 공식 컨벤션은 데이터 수집 시 사용자가 지정.

### 2-4) SmolVLA max_state_dim 대응

| 구성 | DOF | max_state_dim=32 대응 |
|---|---|---|
| 단일팔 (SO-ARM 6 DOF) | 6 | → 32 zero-padding (26 padding) |
| **양팔 (12 DOF)** | **12** | → **32 zero-padding (20 padding)** |

`03_smolvla_architecture.md §E` 확인: "SO-ARM 12 DOF → 32 padding — 동일 모델로 처리 가능." 코드 차원에서 양팔 지원은 문제없음.

### 2-5) lerobot upstream vs seeed-lerobot fork 비교

| 항목 | lerobot upstream | seeed-lerobot fork |
|---|---|---|
| `BiSOFollower` 구조 | 동일 | 동일 |
| `BiSOLeaderConfig` | `SOLeaderConfig` 기반 | 동일 |
| 모터 구성 | 좌/우 각 6 DOF | 동일 |
| 카메라 prefix 컨벤션 | `left_*` / `right_*` | 동일 |
| 데코레이터 (`@check_if_not_connected`) | `connect`, `get_observation`, `send_action`, `disconnect`에 적용 | `connect`에만 적용 (나머지 생략) |
| import 경로 | 상대 import (`.`) | 일부 절대 import (`lerobot.*`) |
| 실질 동작 차이 | 없음 | 없음 |

**결론**: 두 fork의 양팔 구현은 구조·키 컨벤션·DOF 모두 동일. 07_biarm_VLA 진입 시 어느 쪽을 기준으로 해도 무방.

---

## 3) `empty_cameras` 동작 분석

### 3-1) 등록 단계 (`configuration_smolvla.py:123-130`)

```python
def validate_features(self) -> None:
    for i in range(self.empty_cameras):
        key = f"observation.images.empty_camera_{i}"
        empty_camera = PolicyFeature(
            type=FeatureType.VISUAL,
            shape=(3, 480, 640),   # 더미 카메라 기본 shape
        )
        self.input_features[key] = empty_camera
```

`empty_cameras=N`으로 설정하면 `observation.images.empty_camera_0` ~ `empty_camera_{N-1}` 키가 `input_features`에 등록됨.

### 3-2) forward 단계 (`modeling_smolvla.py:421-455`)

```python
present_img_keys  = [key for key in self.config.image_features if key in batch]
missing_img_keys  = [key for key in self.config.image_features if key not in batch]

# 실제 이미지 처리 (present)
for key in present_img_keys:
    img = ...resize_with_pad...
    img = img * 2.0 - 1.0   # [0,1] → [-1,1]
    images.append(img)
    img_masks.append(mask)   # mask=True (유효)

# 더미 이미지 생성 (missing → empty_cameras 개수만큼)
for num_empty_cameras in range(len(missing_img_keys)):
    if num_empty_cameras >= self.config.empty_cameras:
        break
    img = torch.ones_like(img) * -1    # 완전 검정 이미지 (-1)
    mask = torch.zeros_like(mask)      # mask=False (무효)
    images.append(img)
    img_masks.append(mask)
```

`mask=0`인 이미지는 attention에서 무시됨. 즉 모델이 "카메라가 없는 슬롯"임을 인식하고 해당 시각 정보를 배제하는 구조.

### 3-3) smolvla_aloha_sim 선례

`configuration_smolvla.py:47-48` 주석:
> "Add empty images. Used by smolvla_aloha_sim which adds the empty left and right wrist cameras in addition to the top camera."

`smolvla_aloha_sim`은 사전학습이 3대 가정인데 추론 환경에 카메라 1대(top)만 있어 나머지 2대를 더미로 채우는 케이스. 이 선례로 `empty_cameras` 메커니즘이 코드에 검증되어 있음.

### 3-4) 본 프로젝트에서의 적용 판단

| 상황 | smolvla_base 학습 시 카메라 | 추론 환경 카메라 | empty_cameras 설정 |
|---|---|---|---|
| 03 마일스톤 (더미 입력) | 3대 (camera1/2/3) | 더미 2대 사용 가능 | `empty_cameras=1` 또는 2 (§4 참조) |
| 05 마일스톤 이후 (실 하드웨어) | 3대 | 실제 카메라 N대 | 3-N 설정 (05 진입 시 결정) |

**중요 미결 사항**: `empty_cameras`로 카메라 수를 맞출 수 있어 forward 자체는 가능하다. 그러나 **학습 수렴에도 잘 동작하는지**는 03에서 검증 불가 (더미 입력이라 실 도메인 검증 아님) → **05_leftarmVLA 진입 시 검증 항목**.

---

## 4) 03 마일스톤 추론 환경 입력 스펙 확정

### 4-1) 카메라 키 결정 근거

smolvla_base의 config.json 카메라 키(`camera1/2/3`)와 svla_so100_pickplace 데이터셋 키(`top/wrist`)가 불일치함. 두 가지 접근 가능:

| 접근 | 카메라 키 | 비고 |
|---|---|---|
| **A. smolvla_base config 그대로** | `camera1`, `camera2`, `camera3` | config.json 학습 환경 재현 |
| B. svla_so100_pickplace 데이터 키 | `top`, `wrist` + `empty_cameras=1` | 단일팔 데이터셋에 맞춤 |

**접근 A 선택**: 03 마일스톤의 목표가 "smolvla_base 사전학습 환경에 최대한 가깝게" 추론을 검증하는 것이므로, config.json에 기록된 `camera1/2/3` 키와 normalization 통계를 그대로 사용한다. 더미 입력 생성 시 이 키 이름으로 zero 텐서를 생성.

### 4-2) 확정 입력 스펙 (inference_baseline.py 구현 기준)

| 항목 | 값 | 출처 |
|---|---|---|
| 카메라 키 | `observation.images.camera1`, `camera2`, `camera3` | smolvla_base config.json |
| 이미지 shape (입력 전) | `[B, 3, 480, 640]` (→ 512×512 resize+pad) | config.json `resize_imgs_with_padding` |
| 카메라 수 | 3 | config.json `input_features` |
| `empty_cameras` | **0** (더미 입력이므로 3개 모두 zero 텐서로 직접 생성) | 03 마일스톤 전략 |
| state shape | `[B, 6]` → zero-pad → `[B, 32]` | config.json, info.json |
| action shape (출력) | `(B, 50, 6)` (chunk_size=50, 6 DOF) | config.json |
| language instruction | `"Pick up the cube and place it in the box."` | tasks.parquet 실측 |
| fps | 30 | info.json |
| `num_steps` | 10 | config.json (denoising) |
| `n_action_steps` | 50 | config.json |

---

## 5) 07_biarm_VLA 진입 시 결정 체크리스트

양팔 데이터 수집 및 학습 진입 전 반드시 결정해야 할 사항:

| # | 결정 항목 | 현재 파악 상태 | 결정 시점 |
|---|---|---|---|
| 1 | 양팔 데이터셋 카메라 키 이름 규칙 | `left_<cam>` / `right_<cam>` prefix 사용 예상 (코드 추정) | 데이터 수집 시 확정 |
| 2 | 양팔 state/action dim (12 DOF) → `max_state_dim=32` padding | 12 → 32 zero-padding으로 처리 가능 확인 | 코드 차원 OK, 학습 수렴은 04에서 검증 후 판단 |
| 3 | smolvla_base(단일팔 사전학습)에서 양팔 파인튜닝 가능한지 | max_state_dim=32이므로 코드는 가능. 수렴은 미검증 | 06 직전 실험 |
| 4 | 양팔 카메라 수 (실제 부착 카메라 대수) | 미결 (하드웨어 구성에 따라 다름) | 하드웨어 확정 시 |
| 5 | lerobot upstream vs seeed-lerobot fork 선택 | 구조 동일, 어느 쪽이든 무방 | 06 진입 시 |
| 6 | `empty_cameras` 학습 수렴 검증 | 03에서 불가 → 05 검증 항목 | 05_leftarmVLA 완료 후 |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-29 | 초안 작성. svla_so100_pickplace info.json/tasks.parquet 실측. bi_so_follower/leader 코드 분석. empty_cameras 동작 분석. 03 추론 환경 입력 스펙 확정. |
