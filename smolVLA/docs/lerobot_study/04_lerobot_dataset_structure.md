# LeRobotDataset 데이터셋 구조

> 기준: `docs/reference/lerobot/` (v0.5.1-52-g05a52238) `src/lerobot/datasets/`, `src/lerobot/utils/constants.py`
> 작성일: 2026-04-27
> 목적: lerobot 데이터셋 포맷·키 컨벤션·SmolVLA 와의 매핑을 본 프로젝트(SO-ARM teleop 기반 양팔 + 카메라 3대) 관점에서 정리. 06_biarm_teleop_on_dgx 의 데이터 수집 단계에서 결정해야 할 사항 식별.
> 선행 읽기: `docs/lerobot_study/03_smolvla_architecture.md` (SmolVLA 입력 포맷)

---

## 1) LeRobotDataset 파일 구조

`lerobot_dataset.py:97-138` 에서 정의되는 표준 디렉터리 구조:

```
<dataset_root>/
├── data/                          # 시계열 데이터 (state, action, timestamps)
│   ├── chunk-000/
│   │   ├── file-000.parquet       # 여러 에피소드를 묶은 parquet
│   │   └── ...
│   └── chunk-001/
│       └── ...
├── meta/
│   ├── info.json                  # 스키마 (features 정의, fps, robot_type 등)
│   ├── stats.json                 # 정규화 통계 (mean/std/min/max)
│   ├── tasks.parquet              # task_index → task instruction (자연어) 매핑
│   └── episodes/
│       └── chunk-000/
│           └── file-000.parquet   # 에피소드 메타 (start/end frame, length 등)
└── videos/                        # 카메라 이미지 (mp4 인코딩)
    ├── observation.images.<cam_name_1>/
    │   └── chunk-000/
    │       ├── file-000.mp4
    │       └── ...
    └── observation.images.<cam_name_2>/
        └── ...
```

핵심:
- **data/**: state·action·timestamp 등 비-비디오 데이터. parquet 포맷
- **videos/**: 카메라마다 별도 디렉터리. **디렉터리 이름이 곧 키 이름** (`observation.images.<cam_name>`)
- **meta/info.json**: 데이터셋 스키마. SmolVLA 가 이걸 읽어 `config.input_features` 구성

`CODEBASE_VERSION = "v3.0"` (`dataset_metadata.py:55`). v2.1 이전 데이터셋은 `convert_dataset_v21_to_v30.py` 로 변환 필요.

## 2) 표준 키 컨벤션

`utils/constants.py:20-39` 에 정의된 표준 키:

| 키 | 정의 | 본 프로젝트 적용 |
|---|---|---|
| `observation.state` | 로봇 state 벡터 | SO-ARM 6 DOF (단일팔) / 12 DOF (양팔) |
| `observation.images.<camera_name>` | 카메라 이미지 (videos/ 디렉터리에 mp4) | `observation.images.{wrist_left, wrist_right, overview}` |
| `observation.environment_state` | 환경 state (시뮬레이션용) | 사용 안 함 |
| `observation.language.tokens` | 토크나이즈된 task instruction | SmolVLA processor 가 자동 생성 — 데이터셋에 직접 저장 안 함 |
| `observation.language.attention_mask` | 토큰 attention mask | 위와 동일, processor 자동 |
| `action` | action 벡터 | 단일팔 6 DOF / 양팔 12 DOF |
| `next.reward`, `next.done`, `next.truncated` | RL 용 | SmolVLA 학습엔 불필요 |

자동 생성되는 메타 키 (`DEFAULT_FEATURES`, `constants.py:79-85`):

| 키 | 정의 |
|---|---|
| `timestamp` | 프레임 타임스탬프 (float32) |
| `frame_index` | 에피소드 내 프레임 인덱스 (int64) |
| `episode_index` | 에피소드 인덱스 (int64) |
| `index` | 글로벌 프레임 인덱스 (int64) |
| `task_index` | task 인덱스 → tasks.parquet 매핑 (int64) |

## 3) 카메라 키 명명 규칙 (중요)

### 표준 형식

`observation.images.<camera_name>` — **prefix 부분 (`observation.images.`) 은 LeRobot 표준 고정**, 뒤의 카메라 이름은 자유. `lerobot_dataset.py:122,130` 의 표준 예시: `observation.images.laptop`, `observation.images.phone`.

### 카메라 이름은 SO-ARM teleop 시 dict 키로 결정

`smolvla.mdx:104` 의 SO-101 예시:
```bash
--robot.cameras="{ front: {type: opencv, ...}}"
```

→ teleop 시 카메라 dict 의 키 (`front`) 가 그대로 데이터셋의 `observation.images.front` 로 저장됨. **05 데이터 수집 시 결정해야 할 카메라 이름이 곧 학습/추론 시 키가 된다.**

### 정렬 동작 — 이전 답변 정정

SmolVLA 의 `image_features` 는 dict 삽입 순서를 보존하며, **알파벳/숫자 정렬 안 함**:

`policies.py:148-152`:
```python
@property
def image_features(self) -> dict[str, PolicyFeature]:
    if not self.input_features:
        return {}
    return {key: ft for key, ft in self.input_features.items() if ft.type is FeatureType.VISUAL}
```

`modeling_smolvla.py:421-422`:
```python
present_img_keys = [key for key in self.config.image_features if key in batch]
```

→ **`config.input_features` 의 dict 순서대로 처리**. 그리고 `input_features` 순서는 데이터셋 `info.json` 의 features 정의 순서로 결정.

**시사점**: 숫자 prefix (`cam_0_*`, `cam_1_*`) 로 정렬 강제할 필요 없음. 다만 **04 와 05/06 사이에서 카메라 이름을 일관되게** 유지하는 것은 중요 — 같은 이름이 같은 부착 위치 카메라를 가리키도록.

### 본 프로젝트 권장 카메라 이름

| 마일스톤 | 카메라 키 |
|---|---|
| 05_leftarmVLA | `observation.images.wrist_left`, `observation.images.overview` (총 2대) |
| 05/06/07 | `observation.images.{wrist_left, wrist_right, overview}` (총 3대) |

`overview` 는 base 미포함 전체 조망 카메라. 04 의 2대 구성은 left arm 단독이므로 `wrist_left` + `overview`.

## 4) state / action 차원 매핑

### SO-ARM 6 DOF 단일팔 (04)

| 키 | shape | 의미 |
|---|---|---|
| `observation.state` | (6,) | follower joint position 6 DOF |
| `action` | (6,) | leader joint position 6 DOF (teleop 추종 타겟) |

### SO-ARM 12 DOF 양팔 (05/06/07)

권장 매핑:

| 키 | shape | 의미 |
|---|---|---|
| `observation.state` | (12,) | `[left_6, right_6]` 단일 키 — left 6 DOF 먼저, right 6 DOF 뒤 |
| `action` | (12,) | 동일 매핑 |

**왜 단일 키 12 DOF (vs 좌·우 분리 키)**:
- SmolVLA `pad_vector` (`modeling_smolvla.py:158-169`) 가 `max_state_dim=32`, `max_action_dim=32` 로 zero-padding 한 번에 처리
- 분리 키 (`observation.state.left_arm`, `observation.state.right_arm`) 는 LeRobot 표준에서 벗어남 — `RobotStateFeature` 는 단일 `observation.state` 만 인식 (`policies.py:131-137`)

**SO-ARM 6 DOF 의 관절 순서** (`docs/work_flow/specs/history/01_teleoptest.md` TODO-03a 기준):
1. `shoulder_pan`
2. `shoulder_lift`
3. `elbow_flex`
4. `wrist_flex`
5. `wrist_roll`
6. `gripper`

→ 12 DOF 는 `[L_shoulder_pan, L_shoulder_lift, ..., L_gripper, R_shoulder_pan, ..., R_gripper]` 순서.

## 5) Task instruction (language) 처리

### 데이터셋에는 자연어 문자열로 저장

`meta/tasks.parquet` 에 `task_index → task_string` 매핑. 각 에피소드는 `task_index` 로 어느 task 인지 식별 (`constants.py:84` `DEFAULT_FEATURES["task_index"]`).

### 학습/추론 시 SmolVLA processor 가 토크나이즈

`processor_smolvla.py:69-85` 의 입력 전처리 파이프라인:

1. `RenameObservationsProcessorStep` — 키 rename (현재 SmolVLA 빈 map)
2. `AddBatchDimensionProcessorStep` — batch 차원
3. `NewLineTaskProcessorStep` — task 문자열 끝에 `\n` 추가
4. `TokenizerProcessorStep` — language tokenize (`tokenizer_max_length=48`, padding side `right`)
5. `DeviceProcessorStep` — GPU 이동
6. `NormalizerProcessorStep` — `observation.state`/`action` MEAN_STD 정규화, `observation.images.*` IDENTITY (smolvla 가 내부적으로 [-1, 1] 변환)

**시사점**:
- 데이터셋 수집 시 task instruction 은 자연어 문자열 그대로 ("Pick up the red cube and place it in the bin." 등)
- `tokenizer_max_length=48` 안에 들어가는 길이로 작성. 영문 기준 한 문장 정도
- 한 데이터셋 안에 여러 task 가 있어도 됨 (`task_index` 로 구분)

## 6) Stats / 정규화

### 자동 계산

`compute_stats.py` — 데이터셋 빌드 시 각 feature 별 mean/std/min/max 자동 계산하여 `meta/stats.json` 에 저장.

### SmolVLA 의 정규화 적용

`03_smolvla_architecture.md` §G + `processor_smolvla.py:80-84`:

| Feature | 정규화 모드 | 의미 |
|---|---|---|
| `observation.images.*` | `IDENTITY` | smolvla 가 내부적으로 [0,1] → [-1,1] 변환 (`modeling_smolvla.py:435`) |
| `observation.state` | `MEAN_STD` | (state - mean) / std |
| `action` | `MEAN_STD` | 학습 시 정규화, 추론 시 unnormalize |

**중요**: 정규화 통계는 **본 프로젝트 데이터셋의 stats** 로 계산됨 (사전학습 smolvla_base 의 stats 가 아님). → 도메인 시프트 일부가 정규화 단에서 흡수.

## 7) FPS / 시간 정렬

### info.json 에 fps 저장

데이터셋 빌드 시 카메라 fps + 제어 주기를 명시. SmolVLA 의 `chunk_size=50` 은 50 step 의 미래 action 을 의미하므로 **fps 와 함께 해석**해야 시간 길이 결정:
- fps=30 → 50 step = 1.67 초의 action chunk
- fps=60 → 50 step = 0.83 초의 action chunk

### 본 프로젝트 권장 fps

| 항목 | 권장값 | 근거 |
|---|---|---|
| 카메라 캡처 fps | 30 또는 60 | OV5648 native 가능 fps. 60 권장 (제어 빈도와 일치) |
| 제어/state·action 기록 fps | 60 | Orin teleop 60Hz (`01_teleoptest.md` TODO-04 검증 결과) |

학습 시 `delta_timestamps` 로 다운샘플링 가능 (`lerobot_dataset.py:53`).

## 8) SmolVLA 가 받는 vs 데이터셋이 주는 키 매핑 (자동 처리)

| SmolVLA 가 사용하는 키 | 데이터셋이 제공하는 키 | 변환 위치 |
|---|---|---|
| `OBS_STATE` (`observation.state`) | 동일 | 매핑 불필요 |
| `OBS_LANGUAGE_TOKENS` (`observation.language.tokens`) | 데이터셋엔 자연어 task 문자열만 (`tasks.parquet`) | processor `TokenizerProcessorStep` 가 자동 생성 |
| `OBS_LANGUAGE_ATTENTION_MASK` | 동일 | processor 자동 |
| `image_features` (config 기반 dict) | `observation.images.*` 모든 키 | config.input_features 가 데이터셋 info.json 으로부터 자동 구성 |
| `ACTION` (`action`) | 동일 | 매핑 불필요 |

**우리가 결정하는 것**:
1. 카메라 이름 (`wrist_left`, `wrist_right`, `overview`)
2. state/action 차원 (12 DOF, 단일 키 매핑)
3. task instruction 자연어 문장

## 9) 06_biarm_teleop_on_dgx 에서 결정해야 할 사항 체크리스트

본 문서를 근거로 05 진입 시 다음을 확정한다:

- [ ] **카메라 이름 3종 확정**: `wrist_left`, `wrist_right`, `overview` (또는 다른 이름) — 04 와 일관성 유지
- [ ] **카메라 해상도**: OV5648 native (예: 640×480) — 학습 시 SmolVLA 가 자동으로 (512,512) 로 리사이즈+패딩
- [ ] **카메라 fps**: 30 vs 60 결정 (제어 빈도와 일치 권장)
- [ ] **state/action 12 DOF 매핑 순서**: `[L_shoulder_pan, L_shoulder_lift, ..., L_gripper, R_*]`
- [ ] **task instruction 작성**: `tokenizer_max_length=48` 토큰 안에 들어가는 자연어 문장
- [ ] **에피소드 수 목표**: SmolVLA 공식 권장 ~50 에피소드 / variation (`smolvla.mdx:32`)
- [ ] **데이터셋 repo_id**: HF Hub 에 push 할 이름 (예: `<HF_USER>/biarm_so_arm_humanoid_v1`)

## 10) 잔여 리스크 / 후속 검증

- **휴머노이드 토르소 부착 SO-ARM 의 작업 영역** 이 표준 SO-ARM 책상 mount 와 다름 → state 분포가 사전학습과 어긋남. stats.json 정규화로 일부 흡수되지만 도메인 시프트 잔존
- **카메라 3대 구성** 이 사전학습 분포(보통 1~2대) 와 다름 — 06 학습 시 `image_features` 토큰 시퀀스 길이 증가, attention 분포 변화. `03b_smolvla_milestone_config_guide.md §2 06` 1차/2차 전환 트리거 참조
- **손목 카메라의 그리퍼 클로즈업 시야** 가 SmolVLM2 사전학습 분포(자연 장면) 와 큰 차이 — vision encoder 까지 푸는 S3 가 필요할 수 있음
- **양팔 12 DOF 의 좌·우 대칭성** 을 SmolVLA 가 학습할 수 있는지 미검증 — `[L_6, R_6]` 순서가 임의 결정이라, 좌·우 swap 시 학습 결과가 동일한지 (모델이 좌·우 구조를 implicit 하게 학습) 06 단계에서 정성 평가 필요
