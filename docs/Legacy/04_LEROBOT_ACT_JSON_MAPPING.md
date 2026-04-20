# LeRobot ACT ↔ HYlion JSON 매핑 가이드

> **목표**: SO-ARM 101 Pro의 pick-and-place 학습에 사용한 LeRobot ACT 방식을 HYlion의 메인 명령 인터페이스로 통합

---

## 1. LeRobot ACT 데이터셋 구조 복습

### 1.1 저장 형식

```
datasets/so101_pick_place/
├── episode_0001/
│   ├── images/
│   │   ├── front_0000.jpg      ← 카메라 프레임
│   │   ├── front_0001.jpg
│   │   └── ...
│   ├── states.json              ← 관절 상태 시퀀스
│   └── texts.json               ← 태스크 설명 ("Pick up cup...")
├── episode_0002/
└── ...
```

### 1.2 상태 벡터 (states.json)

```json
{
  "joint_positions": [              // 각 timestep마다 6-DOF
    [0, 45, -60, 0, 0, 0],         // t=0: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
    [5, 50, -55, 2, 0, 0],         // t=1
    [10, 55, -50, 5, 0, 100],      // t=2 (gripper 계산: 0~100, 0=열림, 100=닫힘)
    ...
  ],
  "gripper_states": [100, 100, 100, ...]  // 대안: 별도 필드
}
```

### 1.3 액션 청크 (Action Chunk)

ACT 모델은 **N개 미래 스텝의 관절 명령을 한 번에 예측**:

```
[입력]
- 현재 카메라 프레임 (RGB)
- 현재 관절 상태 (6-DOF + gripper)
- 언어 지시 ("Pick up the starbucks_cup")

[출력] — Action Chunk (shape: [chunk_size, 7])
- chunk_size = 100 (기본값, 약 5초 @50ms per step)
- 각 row: [θ1, θ2, θ3, θ4, θ5, θ6, gripper_command]
```

---

## 2. HYlion action JSON 구조

### 2.1 핵심 필드

현재 프로젝트는 상위 Brain이 아래의 단순한 top-level action JSON을 발행한다.

필수 필드:
- `action_id`
- `timestamp`
- `session_id`
- `source`
- `network_online`
- `intent`
- `target_object`
- `reply_text`
- `requires_smolvla`
- `requires_bhl`
- `gait_cmd`
- `state_current`
- `safety_allowed`
- `fallback_policy`

```json
{
  "action_id": "abc-123",
  "timestamp": "2026-04-03T10:01:00Z",
  "session_id": "sess_2026_04_15_a",
  "source": "terminal",
  "network_online": true,
  "intent": "pick_place",
  "target_object": "starbucks_cup",
  "reply_text": "I am picking up the cup",
  "requires_smolvla": true,
  "requires_bhl": false,
  "gait_cmd": "stop",
  "state_current": "MANIPULATING",
  "safety_allowed": true,
  "fallback_policy": "precoded"
}
```

기본 원칙:
- `intent != pick_place` 인 경우 SO-ARM executor는 동작하지 않는다.
- `pick_place`일 때만 SO-ARM executor가 반응한다.
- 상세 팔 명령은 이 JSON에 넣지 않고, executor가 `fallback_policy`와 내부 규칙으로 처리한다.

### 2.2 SO-ARM 101 관절 순서 (중요!)

| 인덱스 | 관절명 | LeRobot ID | 범위 | 설명 |
|--------|--------|-----------|------|------|
| 0 | shoulder_pan | 1 | -180~180° | 수평 회전 |
| 1 | shoulder_lift | 2 | -90~90° | 상하 움직임 |
| 2 | elbow_flex | 3 | -150~0° | 팔꿈치 구부림 |
| 3 | wrist_flex | 4 | -90~90° | 손목 구부림 |
| 4 | wrist_roll | 5 | -180~180° | 손목 회전 |
| 5 | gripper | 6 | 0~100 | 그리퍼 (0=열림, 100=닫힘) |

> **주의**: 인덱스 번호가 모터 ID와 다름 (모터 ID = 1~6, 배열 인덱스 = 0~5)

---

## 3. 데이터 흐름도

### 3.1 학습 시 (Week 3~5)

```
[인간 텔레옵 수집]
  SO-ARM + 카메라 → LeRobot 데이터셋 (600 에피소드)
  
[LeRobot ACT 학습]
  DGX Spark에서 학습
  입력: (camera_frame, language_text)
  출력: action_chunk [N, 7]
  
[모델 저장]
  ~/lerobot/outputs/train/act_pick_place/checkpoints/last/
    → TensorRT로 변환 (Orin에서 실행 가능)

[HYlion 런타임 연동]
  Brain action JSON의 intent=pick_place, target_object=starbucks_cup
  → SO-ARM executor가 필요 시 ACT/IK/fallback 선택
```

### 3.2 런타임 (Week 6+)

```
[사용자 음성 명령]
"컵 줄 수 있어?"

[LLM 처리]
Groq LLaMA 3.1 → JSON 생성
{
  "action_id": "abc-123",
  "timestamp": "2026-04-03T10:01:00Z",
  "session_id": "sess_2026_04_15_a",
  "source": "mic",
  "network_online": true,
  "intent": "pick_place",
  "target_object": "starbucks_cup",
  "reply_text": "I will pick up the starbucks cup.",
  "requires_smolvla": true,
  "requires_bhl": false,
  "gait_cmd": "stop",
  "state_current": "MANIPULATING",
  "safety_allowed": true,
  "fallback_policy": "precoded"
}

[카메라 캡처 + ACT 추론]
현재 프레임 + "Pick up starbucks_cup" 
  → ACT 모델 (Orin TensorRT)
  → action_sequence [100, 7]

[로봇 실행]
SO-ARM executor:
  1. action JSON 확인
  2. intent == pick_place 인지 확인
  3. fallback_policy 또는 내부 정책으로 ACT/IK/precoded 선택
  4. `/hylion/soarm_command` 발행
```

---

## 4. 구현 타임라인

### Week 0~1: JSON 스키마 확정 ✅ 완료

- `hylion_brain_v2.py`의 JSON 형식 정의
- top-level action JSON 구조 설계

### Week 2: IK 모듈 구현

```python
# lerobot/lerobot/common/robot_devices/arms/so_arm_ik.py
import ikpy.chain

so_arm_chain = ikpy.chain.Chain.from_urdf_file("so_arm_101.urdf")

def position_to_joints(target_xyz, target_rpy):
    target_frame = pose_to_frame(target_xyz, target_rpy)
    joint_angles = so_arm_chain.inverse_kinematics(target_frame)
    return joint_angles  # [θ1, θ2, θ3, θ4, θ5, gripper=0]
```

테스트:
```bash
# hylion_brain_v2.py 실행
[You]: "Put your hand at 20cm forward"
→ IK 계산 → JSON fallback_joint_target 자동 채움
```

### Week 3~5: ACT 학습 + 배포

```python
# lerobot/scripts/train.py (기존 코드)
lerobot-train \
    --policy.type=act \
    --dataset.repo_id=<user>/so101_pick_place \
    --output_dir=outputs/train/act_pick_place \
    --training.num_epochs=100

# 중간에 hylion_brain_v2.py 업데이트
# call_lerobot_act_model() 함수 구현
```

테스트:
```bash
# hylion_brain_v2.py 실행
[You]: "Pick up the starbucks cup"
→ LLM: language_instruction 추출
→ ACT 모델: action_sequence [100, 7] 생성
→ JSON: intent=pick_place, target_object=starbucks_cup, fallback_policy=smolvla
```

### Week 6+: 상하체 통합 + 운영

```bash
# 상체는 SmolVLA (pick-and-place)
# 하체는 Walking RL (보행)
# 둘 다 JSON의 top-level intent / gait_cmd / fallback_policy로 분기
```

---

## 5. 테스트 시나리오

### 시나리오 A: ACT 모델 로드 전 (지금)

```bash
python hylion_brain_v2.py

[You]: "Pick up the cup at x=20 y=-5"
→ LLM: intent=pick_place, target_object=cup 생성
→ IK 모듈 (아직 없음): None 반환
→ JSON: fallback_joint_target = [0, 90, -90, 0, 0, 0]
```

예시 action JSON:

→ LLM: intent=pick_place, target_object=cup 생성
→ IK 모듈 (아직 없음): None 반환
→ JSON: fallback_policy=smolvla, requires_smolvla=true

**Q: 카메라가 없으면?**


### 6. JSON 예제

```json
{
  "action_id": "act_001",
  "timestamp": "2026-04-15T12:00:00Z",
  "session_id": "sess_2026_04_15_a",
  "source": "mic",
  "network_online": true,
  "intent": "pick_place",
  "target_object": "cup",
  "reply_text": "I am picking up the cup.",
  "requires_smolvla": true,
  "requires_bhl": false,
  "gait_cmd": "stop",
  "state_current": "MANIPULATING",
  "safety_allowed": true,
  "fallback_policy": "smolvla"
}
```
A: 시뮬레이션 카메라 프레임 또는 더미 프레임으로 대체. ACT는 언어만으로도 동작 예측 가능 (약간의 성능 저하).

**Q: 관절 순서를 틀리면?**

A: 로봇이 엉뚱한 방향으로 움직임. 필히 **Week 1 SO-ARM 실측으로 검증**.

## 7. ROS2 노드 구조

### 7.1 노드 분리

| 노드 | 파일 | 역할 | 입력 토픽 | 출력 토픽 |
|------|------|------|----------|----------|
| `brain_node` | `brain_node.py` | LLM 오케스트레이션 | `/hylion/user_input`, `/hylion/perception` | `/hylion/action_json`, `/hylion/tts` |
| `perception_node` | `perception_node.py` | 카메라 + YOLO 감지 | `/camera/image_raw` | `/hylion/perception` |
| `soarm_node` | `soarm_node.py` | SO-ARM 제어 생성 | `/hylion/action_json` | `/hylion/soarm_command` |

### 7.2 토픽 메시지

```python
# 사용자 입력 (String)
std_msgs/String: "Pick up the cup"

# 감지 결과 (String: JSON)
std_msgs/String: '[{"class": "starbucks_cup", "x_pixel": 300, ...}]'

# 액션 JSON (String: JSON)
std_msgs/String: '{"intent": "pick_place", "target_object": "starbucks_cup", ...}'

# SO-ARM 명령 (String: JSON)
std_msgs/String: '{"type": "joint_target", "joint_positions_deg": [...], ...}'

# TTS (String)
std_msgs/String: "I am picking up the cup"
```

### 7.3 실행 예시

```bash
# 터미널 1: Brain Node
ros2 run hylion brain_node

# 터미널 2: Perception Node
ros2 run hylion perception_node

# 터미널 3: SO-ARM Node
ros2 run hylion soarm_node

# 터미널 4: 사용자 입력 퍼블리시
ros2 topic pub /hylion/user_input std_msgs/String "data: 'Pick up the cup'"
```

### 7.4 장점

- **모듈화**: 각 노드 독립 실행/디버깅 가능
- **확장성**: 노드 추가/교체 용이 (예: 다중 카메라)
- **실시간성**: 토픽으로 비동기 통신
- **ROS2 생태계**: RViz, rqt 등 도구 활용 가능
