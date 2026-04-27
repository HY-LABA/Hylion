# lerobot 레포 구조 파악

> 기준: `LABA5_Bootcamp/lerobot/` (로컬 클론, v0.5.1 / 2026-03-28)  
> Python >= 3.12 필요

---

## 루트 디렉토리

```
lerobot/
├── src/                      # 메인 패키지 소스
├── tests/                    # 테스트
├── examples/                 # 사용 예제 (tutorial, training 등)
├── docs/                     # 문서 (mdx 형식)
├── docker/                   # Docker 설정
├── benchmarks/               # 벤치마크
├── media/                    # 이미지/영상 에셋
├── pyproject.toml            # 패키지 메타데이터 + CLI 진입점 정의
├── requirements-ubuntu.txt   # Ubuntu 의존성 고정
├── requirements-macos.txt    # macOS 의존성 고정
├── Makefile                  # 개발용 빌드/테스트 명령
└── README.md
```

### pyproject.toml — CLI 진입점 전체 목록

```toml
[project.scripts]
lerobot-calibrate          # 캘리브레이션
lerobot-find-cameras       # 카메라 탐색
lerobot-find-port          # 시리얼 포트 탐색
lerobot-find-joint-limits  # 관절 한계 탐색
lerobot-setup-motors       # 모터 ID·baudrate 설정
lerobot-setup-can          # CAN 설정
lerobot-teleoperate        # 텔레옵
lerobot-record             # 데이터 수집
lerobot-replay             # 에피소드 재생
lerobot-train              # 학습
lerobot-train-tokenizer    # 토크나이저 학습
lerobot-eval               # 평가/추론
lerobot-dataset-viz        # 데이터셋 시각화
lerobot-edit-dataset       # 데이터셋 편집
lerobot-imgtransform-viz   # 이미지 변환 시각화
lerobot-info               # 패키지 정보
```

### 설치 방법 (Ubuntu 기준)

```bash
# 1. 환경 생성
conda create -y -n lerobot python=3.12
conda activate lerobot
conda install ffmpeg -c conda-forge   # ffmpeg 7.X (8.X 미지원)

# 2. 소스 설치
cd lerobot
pip install -e .

# 3. SO-101 모터 SDK 추가 설치
pip install -e ".[feetech]"    # SO-100/SO-101 표준 (Feetech 모터)
# pip install -e ".[dynamixel]"  # Dynamixel 모터 사용 시
```

---

## docs/ — 주요 문서

```
docs/source/
├── installation.mdx         # 설치 가이드
├── so100.mdx / so101.mdx    # SO-ARM 하드웨어 가이드 ← 핵심
├── smolvla.mdx              # smolVLA 가이드
├── il_robots.mdx            # Imitation Learning 실물 로봇 가이드
├── cameras.mdx              # 카메라 설정
├── async.mdx                # 비동기 추론 (Orin 배포 관련)
└── ...
```

---

## src/lerobot/ 패키지 구조

```
src/lerobot/
├── async_inference/       # 서버-클라이언트 비동기 추론 (Orin 배포 핵심)
│   ├── policy_server.py   # 추론 전담 서버 (GPU 머신에서 실행)
│   └── robot_client.py    # 로봇 제어 클라이언트
├── cameras/               # 카메라 드라이버
│   ├── opencv/            # OpenCV (USB 카메라) ← 우리 것
│   ├── realsense/         # Intel RealSense
│   └── zmq/               # ZMQ 원격 카메라
├── configs/               # 학습/평가/정책 설정 클래스
├── datasets/              # 데이터셋 로드·저장·스트리밍
├── data_processing/       # SARM 어노테이션 도구
├── envs/                  # 시뮬레이션 환경 (Libero, MetaWorld)
├── model/                 # 키네마틱스
├── motors/                # 모터 드라이버
│   ├── dynamixel/         # Dynamixel (XL430, XM430 등)
│   ├── feetech/           # Feetech STS3215 ← SO-101 표준
│   ├── damiao/            # Damiao
│   └── robstride/         # Robstride
├── policies/              # 정책 모델들
│   ├── smolvla/           # SmolVLA ← 우리 것
│   ├── act/               # ACT
│   ├── diffusion/         # Diffusion Policy
│   ├── pi0/ pi05/         # π0, π0.5
│   └── groot/             # GR00T N1.5
├── robots/                # 로봇 config·클래스
│   ├── so_follower/       # SO-100/101 follower ← 우리 것
│   └── bi_so_follower/    # 양팔 SO follower
├── scripts/               # CLI 진입점 (위 pyproject.toml 참고)
├── teleoperators/         # 텔레옵 인터페이스
│   ├── so_leader/         # SO-100/101 leader ← 우리 것
│   ├── bi_so_leader/      # 양팔 SO leader
│   └── keyboard/gamepad/phone/  # 대체 텔레옵
├── transport/             # gRPC 통신 (async_inference용)
└── utils/

examples/
├── tutorial/smolvla/      # smolVLA 실사용 예제 ← 반드시 읽을 것
│   └── using_smolvla_example.py
└── training/              # 학습 예제
```

---

---

## ⚠️ 중요: 모터 종류 불일치 확인 필요

| 항목 | lerobot SO-101 표준 | 우리 기획서 |
|------|---------------------|------------|
| 모터 | **Feetech STS3215** | **Dynamixel** (U2D2 사용) |
| 컨트롤러 | Waveshare 버스 서보 어댑터 | U2D2 (USB-to-Dynamixel) |
| SDK | `pip install -e ".[feetech]"` | `pip install -e ".[dynamixel]"` |
| 포트 예시 | `/dev/ttyACM0` | `/dev/ttyUSB0` |

lerobot의 `so_follower`가 Feetech 기준으로 작성돼 있어서,  
**우리 팔이 Dynamixel이라면 motors/dynamixel/ 드라이버를 써야 하고 로봇 config도 따로 만들어야 함.**  
→ 실제 팔 부품 확인 후 이 부분을 명확히 해야 한다.

---

## 우리 팔에 관련된 핵심 모듈

### 1. 로봇 (Follower) — `robots/so_follower/`

```python
# config_so_follower.py
@dataclass
class SOFollowerRobotConfig(RobotConfig):
    port: str                        # /dev/ttyUSB0 같은 시리얼 포트
    cameras: dict[str, CameraConfig] # 카메라 딕셔너리
    max_relative_target: float | None = None  # 안전 제한
    use_degrees: bool = True
    disable_torque_on_disconnect: bool = True

# so100_follower, so101_follower 둘 다 동일 클래스로 등록됨
```

### 2. 텔레오퍼레이터 (Leader) — `teleoperators/so_leader/`

```python
# config_so_leader.py
@dataclass
class SOLeaderTeleopConfig(TeleoperatorConfig):
    port: str           # leader arm 포트
    use_degrees: bool = True

# so100_leader, so101_leader 둘 다 동일 클래스로 등록됨
```

### 3. SmolVLA 정책 — `policies/smolvla/`

```
smolvla/
├── modeling_smolvla.py         # SmolVLAPolicy 클래스 (핵심 모델)
├── configuration_smolvla.py    # SmolVLAConfig (하이퍼파라미터)
├── processor_smolvla.py        # 전처리/후처리
└── smolvlm_with_expert.py      # VLM + expert action head 구조
```

핵심 설정값:
```python
chunk_size: int = 50       # 한 번에 예측하는 액션 시퀀스 길이
n_action_steps: int = 50   # 실행할 스텝 수
n_obs_steps: int = 1       # 관찰 히스토리 길이
resize_imgs_with_padding = (512, 512)  # 이미지 입력 크기
freeze_vision_encoder: bool = True     # 파인튜닝 시 VLM 인코더 동결
train_expert_only: bool = True         # expert head만 학습
```

---

## 주요 CLI 스크립트 — `scripts/`

| 스크립트 | CLI 명령어 | 용도 |
|---------|-----------|------|
| `lerobot_find_port.py` | `lerobot-find-port` | 시리얼 포트 탐색 |
| `lerobot_setup_motors.py` | `lerobot-setup-motors` | 모터 ID 설정 |
| `lerobot_calibrate.py` | `lerobot-calibrate` | 캘리브레이션 |
| `lerobot_find_cameras.py` | `lerobot-find-cameras` | 카메라 탐색 |
| `lerobot_teleoperate.py` | `lerobot-teleoperate` | 텔레옵 실행 |
| `lerobot_record.py` | `lerobot-record` | 데이터 수집 |
| `lerobot_replay.py` | `lerobot-replay` | 에피소드 재생 |
| `lerobot_train.py` | `lerobot-train` | 학습 |
| `lerobot_eval.py` | `lerobot-eval` | 평가/추론 |

---

## 워크플로우 — 실제 순서 (docs/source/so101.mdx 기반)

### Step 1. 포트 확인
```bash
lerobot-find-port
# Linux에서 USB 권한 필요 시:
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
```

### Step 2. 모터 ID·baudrate 설정 (최초 1회)
```bash
# Follower
lerobot-setup-motors \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0

# Leader
lerobot-setup-motors \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1
```
→ 스크립트가 모터를 하나씩 연결하라고 안내함. gripper(6)부터 shoulder_pan(1)까지 역순으로.

### Step 3. 캘리브레이션 (최초 1회)
```bash
# Follower
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=my_follower

# Leader
lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=my_leader
```
→ 먼저 모든 관절을 중립 위치로 이동, Enter 후 각 관절을 전체 범위로 움직임

### Step 4. 텔레옵 테스트
```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --robot.id=my_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=my_leader \
  --display_data=true
```

### Step 5. 데이터 수집
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
  --robot.id=my_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=my_leader \
  --dataset.repo_id=<username>/<dataset_name> \
  --dataset.num_episodes=30 \
  --dataset.single_task="Pick the starbucks cup" \
  --dataset.streaming_encoding=true
```

### Step 6. 학습
```bash
lerobot-train \
  --policy=smolvla \
  --dataset.repo_id=<username>/<dataset_name>
```

### Step 7. smolVLA 추론 코드 (`examples/tutorial/smolvla/using_smolvla_example.py`)
```python
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.robots.so_follower import SO100Follower, SO100FollowerConfig

model = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")
robot = SO100Follower(SO100FollowerConfig(port=..., cameras=...))
robot.connect()

obs = robot.get_observation()
action = model.select_action(preprocess(obs))
robot.send_action(postprocess(action))
```

---

## Orin 배포 — `async_inference/`

Orin에서 smolVLA를 실행하는 방법이 **두 가지**다:

### 방법 A. 단일 머신 (simple)
Orin에 직접 lerobot 설치 + SO-ARM USB 연결 → 위 Step 5 코드 그대로 실행

### 방법 B. 서버-클라이언트 분리 (async_inference)
```
[Orin] policy_server.py  ←→  [다른 머신] robot_client.py
   smolVLA 추론만                SO-ARM 제어만
```
- `policy_server.py`: 모델 로드·추론 담당
- `robot_client.py`: 로봇 연결·관찰 전송·액션 수신 담당
- gRPC로 통신 (`transport/services_pb2_grpc.py`)

우리 구조에서는 **방법 A가 기본** (Orin이 SO-ARM USB도 직접 연결).  
방법 B는 Orin 부하가 클 때 DGX에서 추론하고 Orin은 로봇 제어만 할 때 유용.

---

## 모터 드라이버 — `motors/dynamixel/`

SO-ARM은 Dynamixel 서보 사용. 관련 파일:
- `dynamixel.py` — 버스 통신, sync read/write
- `tables.py` — 레지스터 주소 테이블

---

## 다른 정책들 (참고용)

| 폴더 | 정책 |
|------|------|
| `policies/act/` | ACT (Action Chunking Transformer) |
| `policies/diffusion/` | Diffusion Policy |
| `policies/pi0/` | π0 (Physical Intelligence) |
| `policies/sarm/` | SARM |
| `policies/smolvla/` | **SmolVLA ← 우리 것** |

---

## 텔레오퍼레이터 종류 (참고용)

| 폴더 | 설명 |
|------|------|
| `so_leader/` | **SO-ARM leader ← 우리 것** |
| `bi_so_leader/` | SO-ARM 양팔 leader |
| `keyboard/` | 키보드 텔레옵 |
| `gamepad/` | 게임패드 텔레옵 |
| `phone/` | 폰 텔레옵 |

---

## 핵심 파악 포인트 요약

1. **SO-ARM 진입점**: `robots/so_follower/so_follower.py` → `get_observation()`, `send_action()`
2. **smolVLA 추론**: `policies/smolvla/modeling_smolvla.py` → `select_action()`
3. **데이터 수집 흐름**: `lerobot-record` → `datasets/dataset_writer.py`
4. **학습 흐름**: `lerobot-train` → `scripts/lerobot_train.py` → `policies/smolvla/modeling_smolvla.py`
5. **실제 사용 예시**: `examples/tutorial/smolvla/using_smolvla_example.py`
