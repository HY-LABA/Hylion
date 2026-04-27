# lerobot src/ 구조 파악

> `src/lerobot/` 안의 각 모듈이 무슨 역할인지 정리

---

## 전체 구조

```
src/lerobot/
├── __init__.py          ← 패키지 진입점. 사용 가능한 로봇/정책/카메라 목록 등록
├── __version__.py       ← 버전 문자열 관리
├── types.py             ← 시스템 전체에서 쓰는 핵심 타입 정의
│
├── robots/              ← 로봇 하드웨어 인터페이스
├── teleoperators/       ← 텔레옵 장치 인터페이스
├── motors/              ← 모터 드라이버 (저수준 통신)
├── cameras/             ← 카메라 드라이버
│
├── policies/            ← AI 정책 모델 (smolVLA 등)
├── processor/           ← 정책 입출력 전처리/후처리
├── configs/             ← 학습·평가 설정 클래스
│
├── datasets/            ← 데이터셋 저장·로드·스트리밍
├── data_processing/     ← 데이터 후가공 도구
│
├── scripts/             ← CLI 명령어 진입점
├── async_inference/     ← 서버-클라이언트 분리 추론
│
├── common/              ← 학습 루프 공통 유틸 ★ 신규
│   ├── control_utils.py ← 로봇 제어 루프 헬퍼
│   ├── train_utils.py   ← 학습 루프 헬퍼
│   └── wandb_utils.py   ← WandB 로깅 유틸
├── transforms/          ← 데이터 변환 파이프라인 ★ 신규
│   └── transforms.py    ← 이미지·텐서 변환 모음
│
├── envs/                ← 시뮬레이션 환경 (Libero, MetaWorld)
├── rl/                  ← 강화학습 컴포넌트
├── optim/               ← 옵티마이저·스케줄러
├── model/               ← 키네마틱스 계산
├── transport/           ← gRPC 통신 (async_inference용)
├── templates/           ← 커스텀 로봇/정책 추가용 템플릿
└── utils/               ← 공통 유틸 함수
```

---

## 모듈별 상세 설명

### `types.py`
시스템 전체에서 흐르는 핵심 데이터 타입 정의. 한 번 파악해두면 코드 읽기가 훨씬 쉬워짐.

```python
PolicyAction    # 정책이 출력하는 액션 (torch.Tensor)
RobotAction     # 로봇에 보내는 액션 (dict)
RobotObservation # 로봇에서 읽어오는 관찰값 (dict)
EnvTransition   # observation / action / reward / done 묶음
```

---

### `robots/` — 로봇 하드웨어 인터페이스
"로봇과 대화하는 창구". `get_observation()`으로 센서값 읽고, `send_action()`으로 명령 보냄.

```
robots/
├── robot.py          ← Robot 추상 클래스 (모든 로봇이 상속)
├── config.py         ← RobotConfig 기반 클래스
├── so_follower/      ← SO-100 / SO-101 follower ★ 우리 것
├── bi_so_follower/   ← SO 양팔 follower
├── koch_follower/    ← Koch 로봇
├── lekiwi/           ← LeKiwi 모바일 로봇
├── reachy2/          ← Reachy2 휴머노이드
└── unitree_g1/       ← Unitree G1 휴머노이드
```

### `teleoperators/` — 텔레옵 장치 인터페이스
leader arm, 키보드, 게임패드 등 "사람이 조종하는 입력 장치"를 추상화.

```
teleoperators/
├── teleoperator.py   ← Teleoperator 추상 클래스
├── so_leader/        ← SO-100 / SO-101 leader ★ 우리 것
├── bi_so_leader/     ← SO 양팔 leader
├── keyboard/         ← 키보드 텔레옵
├── gamepad/          ← 게임패드 텔레옵
└── phone/            ← 스마트폰 텔레옵
```

### `motors/` — 모터 드라이버 (저수준)
robots/teleoperators가 내부적으로 사용. 직접 건드릴 일은 거의 없음.

```
motors/
├── motors_bus.py     ← MotorsBus 추상 클래스 (sync read/write)
├── dynamixel/        ← Dynamixel 프로토콜 ★ U2D2 사용 시
├── feetech/          ← Feetech STS3215 ★ SO-101 표준
├── damiao/           ← Damiao 모터
└── robstride/        ← Robstride 모터
```

### `cameras/` — 카메라 드라이버

```
cameras/
├── camera.py         ← Camera 추상 클래스
├── opencv/           ← USB 카메라 (OpenCV) ★ 우리 것
├── realsense/        ← Intel RealSense 깊이 카메라
└── zmq/              ← 네트워크로 연결된 원격 카메라
```

---

### `policies/` — AI 정책 모델
"관찰값 → 액션"을 계산하는 두뇌. 각 폴더가 하나의 독립된 정책 모델.

```
policies/
├── factory.py        ← 정책 이름으로 인스턴스 생성하는 팩토리
├── pretrained.py     ← HuggingFace Hub에서 모델 로드
├── smolvla/          ← SmolVLA ★ 우리 것
├── act/              ← ACT (Action Chunking Transformer)
├── diffusion/        ← Diffusion Policy
├── pi0/ pi05/        ← π0, π0.5 (Physical Intelligence)
├── groot/            ← GR00T N1.5 (NVIDIA)
└── ...
```

각 정책 폴더 구조 (smolvla 예시):
```
smolvla/
├── modeling_smolvla.py       ← 모델 클래스 (SmolVLAPolicy)
├── configuration_smolvla.py  ← 하이퍼파라미터 설정
└── processor_smolvla.py      ← 입출력 전처리
```

### `processor/` — 입출력 전처리/후처리
정책에 넣기 전 관찰값을 정규화하고, 출력된 액션을 로봇 명령으로 변환하는 레이어.

### `configs/` — 설정 클래스

```
configs/
├── train.py      ← 학습 설정 (batch_size, lr, steps 등)
├── eval.py       ← 평가 설정
├── policies.py   ← PreTrainedConfig 기반 클래스
└── types.py      ← NormalizationMode 등 설정 관련 타입
```

---

### `datasets/` — 데이터셋 관리
수집된 에피소드를 저장하고, 학습 시 불러오는 파이프라인.

```
datasets/
├── lerobot_dataset.py   ← LeRobotDataset 메인 클래스
├── dataset_writer.py    ← 에피소드 저장 (lerobot-record가 사용)
├── dataset_reader.py    ← 에피소드 로드
├── streaming_dataset.py ← HuggingFace Hub에서 스트리밍 로드
├── compute_stats.py     ← 정규화용 통계 계산
└── video_utils.py       ← MP4 인코딩/디코딩
```

포맷: **Parquet(state/action) + MP4(카메라)** 쌍으로 저장됨.

---

### `scripts/` — CLI 명령어 진입점
`pyproject.toml`에 등록된 `lerobot-*` 명령어들의 실제 구현체.  
코드 흐름을 파악하고 싶을 때 여기서 시작하면 됨.

```
scripts/
├── lerobot_find_port.py      ← lerobot-find-port
├── lerobot_setup_motors.py   ← lerobot-setup-motors
├── lerobot_calibrate.py      ← lerobot-calibrate
├── lerobot_teleoperate.py    ← lerobot-teleoperate
├── lerobot_record.py         ← lerobot-record ★ 데이터 수집
├── lerobot_train.py          ← lerobot-train ★ 학습
└── lerobot_eval.py           ← lerobot-eval ★ 추론/평가
```

### `async_inference/` — 비동기 추론 (Orin 배포 옵션)
smolVLA 추론과 로봇 제어를 **다른 머신에서 분리**해서 실행할 때 사용.

```
async_inference/
├── policy_server.py  ← 추론 전담 서버 (GPU 머신에서 실행)
└── robot_client.py   ← 로봇 제어 클라이언트 (로봇 옆 머신에서 실행)
```

---

### 나머지 (참고만)

| 폴더 | 역할 |
|------|------|
| `envs/` | 시뮬레이션 환경 (Libero, MetaWorld). 실물 로봇엔 불필요 |
| `rl/` | 강화학습. imitation learning인 우리 프로젝트엔 불필요 |
| `optim/` | AdamW 등 옵티마이저 래퍼. 학습 코드가 내부적으로 사용 |
| `model/` | 키네마틱스 계산 유틸 |
| `transport/` | async_inference의 gRPC 통신 구현체 |
| `templates/` | 새 로봇/정책 추가할 때 복사해서 쓰는 보일러플레이트 |
| `utils/` | 로깅, 시드, 디바이스 설정 등 공통 유틸 |

---

## 우리 프로젝트 관점 요약

```
건드릴 것:
  robots/so_follower/       ← 팔 config (포트, 카메라, 안전 제한)
  teleoperators/so_leader/  ← leader arm config
  motors/dynamixel/ or feetech/  ← 실제 모터 종류 확인 후 선택
  policies/smolvla/         ← 필요 시 파인튜닝 설정 조정

읽을 것:
  scripts/lerobot_record.py ← 수집 흐름 파악
  scripts/lerobot_train.py  ← 학습 흐름 파악
  examples/tutorial/smolvla/using_smolvla_example.py ← 추론 예시

안 건드려도 되는 것:
  envs/, rl/, transport/, templates/
  datasets/ (내부 동작 알 필요 없음, CLI로 충분)
```
