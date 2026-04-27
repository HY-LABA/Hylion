# SO-ARM100 / SO-ARM101 로봇팔과 LeRobot 시작하기

> 원문: [SeeedStudio Wiki — LeRobot SO-100M 튜토리얼](https://wiki.seeedstudio.com/lerobot_so100m_new/)
> 본 문서는 위 페이지 내용을 빠짐없이 한국어로 번역한 것입니다.

---

## 머리말 / 내비게이션

Seeed Studio Wiki의 `Quick Links`, `Explore with Topics`, `FAQs` 및 다국어(中文 / 日本語 / Español) 링크 영역.

---

## 메인 타이틀

**SO-ARM100 및 SO-ARM101 로봇팔과 LeRobot으로 시작하기**

---

## 소개

SO-10xARM은 TheRobotStudio에서 공개한 오픈소스 로봇팔 프로젝트로, **팔로워(Follower)와 리더(Leader) 암** 및 3D 프린트 파일과 조작 가이드를 제공합니다.
LeRobot은 PyTorch 기반 프레임워크로, **모방 학습(Imitation Learning)** 을 활용한 실제 로보틱스를 위한 모델, 데이터셋, 도구를 제공하며 로보틱스 진입 장벽을 낮추는 것을 목표로 합니다.

---

## 프로젝트 소개

SO-ARM10x과 reComputer Jetson을 결합하면, **고정밀 로봇팔 제어**와 **강력한 AI 연산 능력**을 통합한 AI 지능형 로봇 키트를 구성할 수 있으며, 교육, 연구, 산업 자동화에 적용됩니다.

## 주요 특징

1. TheRobotStudio가 제공하는 오픈소스 · 저비용 솔루션
2. LeRobot 플랫폼과 통합
3. 포괄적 학습 자료 제공 (조립, 캘리브레이션, 테스트 가이드)
4. **Nvidia reComputer Mini J4012 Orin NX 16GB**와 호환
5. 다양한 활용 분야 (교육, 연구, 생산, 로보틱스)

## 새로워진 점 (What's New)

- Joint 3 분리 문제를 방지하는 **배선 개선**
- 리더 암 모터의 **다른 기어비** 적용
- 리더 암이 팔로워 암을 **실시간으로 추종(follow)** 할 수 있게 됨

---

## 스펙 표

| 항목 | SO-ARM100 | SO-ARM101 |
|---|---|---|
| **리더 암** | 12x ST-3215-C001 (7.4V) 모터, 모든 조인트 기어비 1:345 | 혼합 모터 구성: ST-3215-C044 (1:191, 조인트 1·3), ST-3215-C001 (1:345, 조인트 2), ST-3215-C046 (1:147, 조인트 4–6) |
| **팔로워 암** | SO-ARM100과 동일 | SO-ARM100과 동일 |
| **전원 공급** | 5.5mm × 2.1mm DC 5V 4A | 팔로워 12V, 리더 5V |
| **각도 센서** | 12비트 자기 엔코더 | 12비트 자기 엔코더 |
| **동작 온도** | 0°C ~ 40°C | 0°C ~ 40°C |
| **통신 방식** | UART | UART |

---

## 초기 시스템 환경

**Ubuntu x86:**
- Ubuntu 22.04
- CUDA 12 이상
- Python 3.10
- Torch 2.6 이상

**Jetson Orin:**
- JetPack 6.0 및 6.1 (단, 6.1 제외)
- Python 3.10
- Torch 2.3 이상

---

## 목차

A부터 L까지 다음 항목을 다룹니다:
3D 프린팅 → LeRobot 설치 → 모터 설정 → 조립 → 캘리브레이션 → 원격조작(Teleoperation) → 카메라 추가 → 데이터셋 기록 → 시각화 → 에피소드 리플레이 → 정책(Policy) 학습 → 평가

---

## 3D 프린팅 가이드

### 1단계: 프린터 선택
- 소재: **PLA+**
- 노즐: 0.4mm (레이어 높이 0.2mm) 또는 0.6mm (레이어 높이 0.4mm)
- 채움(Infill): **15%**

### 2단계: 프린터 세팅
- 베드 평탄화 및 레벨링
- 베드 철저히 청소
- 권장될 경우 접착용 풀 도포
- 필라멘트 적재
- **45도 이상의 경사면을 제외한 모든 곳에 서포트 설정**
- 수평축 나사 구멍에는 서포트 넣지 않기

### 3단계: 파트 출력
- **220×220mm 베드 (Ender 계열)**: `Ender_Follower_SO101.stl`, `Ender_Leader_SO101.stl`
- **205×250mm 베드 (Prusa/Up 계열)**: `Prusa_Follower_SO101.stl`, `Prusa_Leader_SO101.stl`

---

## LeRobot 설치

### 1단계: Miniconda 설치

**Jetson용:**
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
chmod +x Miniconda3-latest-Linux-aarch64.sh
./Miniconda3-latest-Linux-aarch64.sh
source ~/.bashrc
```

**X86 Ubuntu 22.04용:**
```bash
mkdir -p ~/miniconda3
cd miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
source ~/miniconda3/bin/activate
conda init --all
```

### 2단계: Conda 환경 생성
```bash
conda create -y -n lerobot python=3.10 && conda activate lerobot
```

### 3단계: Lerobot 클론
```bash
git clone https://github.com/Seeed-Projects/lerobot.git ~/lerobot
```

### 4단계: ffmpeg 설치
```bash
conda install ffmpeg -c conda-forge
```

ffmpeg 7.X 대안 설치:
```bash
conda install ffmpeg=7.1.1 -c conda-forge
```

### 5단계: LeRobot을 feetech 모터 의존성 포함하여 설치
```bash
cd ~/lerobot && pip install -e ".[feetech]"
```

**Jetson JetPack 6.0 이상:**
```bash
conda install -y -c conda-forge "opencv>=4.10.0.84"
conda remove opencv
pip3 install opencv-python==4.10.0.84
conda install -y -c conda-forge ffmpeg
conda uninstall numpy
pip3 install numpy==1.26.0
```

### 6단계: PyTorch와 Torchvision 확인
```python
import torch
print(torch.cuda.is_available())
```

결과가 `False`이면 공식 웹사이트에서 PyTorch와 Torchvision을 재설치하거나, Jetson의 경우 관련 튜토리얼을 참고해 재설치합니다.

---

## 모터 설정

### SO101 모터 스펙

| 서보 모델 | 기어비 | 해당 조인트 |
|---|---|---|
| ST-3215-C044 (7.4V) | 1:191 | L1 |
| ST-3215-C001 (7.4V) | 1:345 | L2 |
| ST-3215-C044 (7.4V) | 1:191 | L3 |
| ST-3215-C046 (7.4V) | 1:147 | L4 – L6 |
| ST-3215-C001 (7.4V) / C018 (12V) / C047 (12V) | 1:345 | F1 – F6 |

### USB 포트 찾기
```bash
lerobot-find-port
```

예제 출력은 사용 가능한 포트를 보여줍니다. 안내가 뜨면 USB 케이블을 제거하고, 식별 후 다시 연결합니다.

### USB 포트 접근 권한 부여
```bash
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
```

### 모터 설정 — 리더 암
캘리브레이션에는 **5V 전원 공급장치**를 사용합니다. 이미지들은 각 조인트 L1–L6의 위치를 보여줍니다.

캘리브레이션 명령:
```bash
lerobot-setup-motors \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM0
```

스크립트가 각 모터를 한 번에 하나씩 연결하도록 안내합니다 (gripper → wrist_roll → ...).

### 모터 설정 — 팔로워 암
**Arm Kit Pro**는 12V, **Arm Kit Standard**는 5V 전원을 사용합니다. 이미지들은 각 조인트 F1–F6의 위치를 보여줍니다.

```bash
lerobot-setup-motors \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0
```

---

## 조립

### 리더 암 조립
이미지(`install_L1.jpg` ~ `install_L23.jpg`)와 함께 18단계로 조인트 조립과 케이블 정리까지 설명합니다.

### 팔로워 암 조립
이미지(`install_F1.jpg` ~ `install_F17.jpg`)와 함께 17단계로 설명합니다. **12단계 이후부터 엔드 이펙터(end-effector) 장착이 리더 암과 달라집니다.**

---

## 캘리브레이션

캘리브레이션은 팔로워와 리더 암이 **동일한 물리적 위치에서 동일한 위치 값을 갖도록** 보장합니다. 이는 로봇 간 신경망 이식(transfer)에 필수입니다.

**캘리브레이션 리셋:**
`~/.cache/huggingface/lerobot/calibration/robots` 또는 `~/.cache/huggingface/lerobot/calibration/teleoperators` 하위 파일을 삭제합니다.

**포트 권한 부여:**
```bash
sudo chmod 666 /dev/ttyACM*
```

**팔로워 암 캘리브레이션:**
```bash
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm
```

로봇을 **가동 범위의 중간 위치**로 옮긴 후 Enter를 누르고, 각 조인트를 전체 범위에 걸쳐 움직입니다.

**리더 암 캘리브레이션:**
```bash
lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm
```

### (선택) Seeed Studio SoARM 도구로 중간 위치 캘리브레이션

도구 클론:
```bash
git clone https://github.com/Seeed-Projects/Seeed_RoboController.git
cd Seeed_RoboController
pip install -r requirements.txt
```

스크립트 실행 순서:
1. `src/tools/servo_disable.py` — 토크 해제
2. `src/tools/servo_middle_calibration.py` — 2048로 캘리브레이션
3. `src/tools/servo_center_test.py` — 검증

```bash
python -m src.tools.servo_disable
python -m src.tools.servo_middle_calibration
python -m src.tools.servo_center_test
```

---

## 원격조작 (Teleoperate)

**카메라 없이 간단한 원격조작:**
```bash
sudo chmod 666 /dev/ttyACM*

lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm
```

캘리브레이션이 누락된 경우 자동으로 인식하여 캘리브레이션 절차를 시작합니다.

---

## 카메라 추가

### RealSense D405 & D435i

**D405:** 근거리 스테레오 깊이 카메라. 작동 범위 7–50cm. 탁상(tabletop) 매니퓰레이션에 적합.

**D435i:** 깊이 센싱, RGB 이미징, IMU 결합. 중거리 용도에 적합.

#### 카메라 브랜치로 전환
```bash
git checkout DepthCameraSupport
git pull origin DepthCameraSupport
git branch --show-current
```

#### RealSense 지원으로 LeRobot 설치
```bash
pip install -e ".[realsense]"
```

#### 카메라 탐지
```bash
lerobot-find-cameras realsense
```

#### RealSense 예제 — 듀얼 카메라 원격조작
```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=my_awesome_follower_arm \
  --robot.cameras='{ 
    d435i_color: {
      type: realsense_d435i_color,
      serial_number_or_name: "419522072950",
      width: 640,
      height: 480,
      fps: 30,
      color_mode: rgb,
      color_stream_format: rgb8,
      rotation: 0,
      warmup_s: 1
    },
    d435i_depth: {
      type: realsense_d435i_depth,
      serial_number_or_name: "419522072950",
      width: 640,
      height: 480,
      fps: 30,
      max_depth_m: 2.0,
      depth_alpha: 0.2,
      rotation: 0,
      warmup_s: 5
    },
    d405_color: {
      type: realsense_d405_color,
      serial_number_or_name: "409122273421",
      width: 640,
      height: 480,
      fps: 30,
      color_mode: rgb,
      color_stream_format: rgb8,
      rotation: 0,
      warmup_s: 1
    },
    d405_depth: {
      type: realsense_d405_depth,
      serial_number_or_name: "409122273421",
      width: 640,
      height: 480,
      fps: 30,
      depth_alpha: 0.03,
      rotation: 0,
      warmup_s: 5
    }
  }' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=my_awesome_leader_arm \
  --display_data=true
```

#### RealSense 파라미터 주의사항
- `depth_alpha`는 깊이 이미지 스케일링을 제어합니다 (타겟 거리에 따라 조정).
- 깊이 카메라가 3개 이상이면 **fps를 15로 낮춥니다**.
- 권장 해상도: 안정성 위해 **640×480**.

### Orbbec Gemini2 / Gemini336 카메라

Orbbec Gemini 2: 로보틱스용 고성능 RGB-D 카메라. 동기화된 스트림 및 6축 IMU 지원.
Orbbec Gemini 336: 반사·어두운·밝은 환경에서 깊이 성능이 향상된 모델.

#### 카메라 브랜치로 전환
```bash
git checkout DepthCameraSupport
git pull origin DepthCameraSupport
git branch --show-current
```

#### Orbbec 지원으로 LeRobot 설치
```bash
pip install -e ".[orbbec]"
```

#### 카메라 탐지
```bash
lerobot-find-cameras orbbec
```

#### Orbbec 예제 — 단일 카메라
```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=my_awesome_follower_arm \
  --robot.cameras='{
    orbbec_color: {
      type: orbbec_color,
      serial_number_or_name: "CP9JA530003A",
      width: 640,
      height: 480,
      fps: 30,
      color_mode: rgb,
      rotation: 0,
      warmup_s: 1
    },
    orbbec_depth: {
      type: orbbec_depth,
      serial_number_or_name: "CP9JA530003A",
      width: 640,
      height: 400,
      fps: 30,
      depth_alpha: 0.2,
      rotation: 0,
      warmup_s: 5
    }
  }' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=my_awesome_leader_arm \
  --display_data=true
```

#### Orbbec 파라미터 주의사항
- `depth_alpha` 시작 값: **0.2**, 화면 확인 후 미세 조정.
- 깊이 카메라 3개 이상이면 fps를 15로 낮춤.
- 권장 해상도: 640×480.

#### Orbbec 자주 발생하는 문제
`"No Orbbec camera found"` 오류는 시리얼 번호 불일치를 의미합니다. 아래를 실행한 뒤:
```bash
lerobot-find-cameras orbbec
```
명령의 `serial_number_or_name` 을 업데이트하세요.

### 일반 카메라 (OpenCV)

**카메라 인덱스 찾기:**
```bash
lerobot-find-cameras opencv
```

카메라 정보와 인덱스를 출력하고, `outputs` 디렉토리에 `captured_images` 를 생성합니다.

**원격조작 중 카메라 표시:**
```bash
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true
```

**여러 카메라 추가:**
```bash
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true
```

**카메라 관련 주의사항:**
- MJPG 포맷: 1920×1080, 30FPS로 카메라 3개 지원.
- YUYV 포맷: 해상도와 FPS가 감소.
- **같은 USB 허브에 카메라 2개를 연결하지 말 것.**
- rerun 버전 문제 시 다운그레이드: `pip3 install rerun-sdk==0.23`

---

## 데이터셋 기록 (Record the Dataset)

**로컬에 데이터셋 저장:**
```bash
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true \
    --dataset.repo_id=seeedstudio123/test \
    --dataset.num_episodes=5 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=false \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=30
```

데이터셋은 `~/.cache/huggingface/lerobot` 하위의 사용자 지정 폴더에 저장됩니다.

**Hugging Face 로그인:**
```bash
huggingface-cli login --token ${HUGGINGFACE_TOKEN} --add-to-git-credential
```

**HF 유저명 저장:**
```bash
HF_USER=$(huggingface-cli whoami | head -n 1)
echo $HF_USER
```

**기록 및 허브 업로드:**
```bash
lerobot-record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"}, side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm \
    --display_data=true \
    --dataset.repo_id=${HF_USER}/record-test \
    --dataset.num_episodes=5 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=true \
    --dataset.episode_time_s=30 \
    --dataset.reset_time_s=30
```

터미널 출력 예시에 타이밍 정보(`dt`, `hz` 값)가 표시됩니다.

### Record 기능의 특징

**1. 데이터 저장**
- 기록 중 디스크에 **LeRobotDataset 포맷**으로 저장.
- 기본적으로 Hugging Face 페이지로 업로드.
- 업로드 비활성화: `--dataset.push_to_hub=False`

**2. 체크포인트 및 재개(Resuming)**
- 기록 중 **자동 체크포인트** 생성.
- 재개: `--resume=true`
- 주의: `--dataset.num_episodes`는 **총 개수가 아니라 추가로 기록할 에피소드 수**로 설정.
- 처음부터 다시 시작하려면 데이터셋 디렉토리 삭제.

**3. 기록 파라미터**

| 파라미터 | 설명 | 기본값 |
|---|---|---|
| `--dataset.episode_time_s` | 에피소드당 지속 시간 (초) | 60 |
| `--dataset.reset_time_s` | 환경 리셋 시간 (초) | 60 |
| `--dataset.num_episodes` | 총 기록 에피소드 수 | 50 |

**4. 키보드 컨트롤**

| 키 | 동작 |
|---|---|
| → (오른쪽 화살표) | 현재 에피소드 조기 종료 후 다음 에피소드로 이동 |
| ← (왼쪽 화살표) | 현재 에피소드 취소 후 다시 기록 |
| ESC | 세션 중단, 영상 인코딩 및 데이터셋 업로드 |

키보드가 동작하지 않으면: `pip install pynput==1.6.8`

### 데이터 수집 팁

- **태스크**: 서로 다른 위치에서 물체를 잡아 빈(bin)에 놓기.
- **규모**: 최소 50 에피소드 이상 기록 (위치당 10 에피소드).
- **일관성**: 카메라는 고정, 동일한 파지 동작 유지, 물체는 항상 가시(visible) 상태.
- **난이도 점진적 증가**: 안정적인 파지를 먼저 확보한 뒤 변형(variation) 추가.

**경험 법칙(Rule of Thumb):** "카메라 이미지만 보고도 자신이 그 태스크를 수행할 수 있어야 한다."

### 문제 해결

Linux 한정: 화살표/ESC 키가 반응하지 않으면 `$DISPLAY` 환경 변수가 설정되어 있는지 확인.

---

## 데이터셋 시각화 (Visualize the Dataset)

**허브에서 온라인 시각화:**
```bash
echo ${HF_USER}/so101_test
```
Repo ID를 복사해 https://huggingface.co/spaces/lerobot/visualize_dataset 에 입력.

**로컬에서 시각화 (업로드한 데이터셋):**
```bash
lerobot-dataset-viz \
  --repo-id ${HF_USER}/so101_test
```

**로컬에서 시각화 (업로드하지 않은 데이터셋):**
```bash
lerobot-dataset-viz \
  --repo-id seeed_123/so101_test
```

(`seeed_123`은 데이터 수집 시 사용한 사용자 지정 `repo_id`)

---

## 에피소드 리플레이

**첫 번째 에피소드 리플레이:**
```bash
lerobot-replay \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --dataset.repo_id=${HF_USER}/record-test \
    --dataset.episode=0
```

로봇이 기록된 동작을 그대로 재현합니다.

---

## 학습 및 평가 (Train And Evaluate)

### ACT 정책

**허브 데이터셋으로 학습:**
```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/so101_test \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_test \
  --job_name=act_so101_test \
  --policy.device=cuda \
  --wandb.enable=false \
  --steps=300000
```

**로컬 데이터셋으로 학습:**
```bash
lerobot-train \
  --dataset.repo_id=seeedstudio123/test \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_test \
  --job_name=act_so101_test \
  --policy.device=cuda \
  --wandb.enable=false \
  --policy.push_to_hub=false\
  --steps=300000
```

파라미터 설명:
- `--dataset.repo_id`: 데이터셋 지정
- `--steps`: 학습 스텝 수 (기본값 800000)
- `--policy.type`: 정책 종류 (`act`, `diffusion`, `pi0`, `pi0fast`, `sac`, `smolvla`)
- `--policy.device`: `cuda`, `mps` (Apple Silicon), `cpu`
- `--wandb.enable`: Weights & Biases 시각화 활성화

### ACT 평가

**정책 평가:**
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"},   side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
  --robot.id=my_awesome_follower_arm \
  --display_data=false \
  --dataset.repo_id=seeed/eval_test123 \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=outputs/train/act_so101_test/checkpoints/last/pretrained_model
```

주의사항:
- `--policy.path`는 로컬 경로 또는 허브 repo (`${HF_USER}/act_so100_test`) 사용 가능.
- `dataset.repo_id`는 `eval_` 로 시작해야 합니다.
- "File exists" 오류 발생 시 기존 `eval_` 폴더를 삭제하세요.
- **카메라 파라미터 키워드는 데이터 수집 시 사용한 키워드와 정확히 일치해야 합니다.**

### SmolVLA 정책

SmolVLA는 로보틱스용 **450M 규모의 경량 파운데이션 모델**입니다.

**환경 준비:**
```bash
pip install -e ".[smolvla]"
```

**SmolVLA 파인튜닝 (20k 스텝, A100에서 약 4시간):**
```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/mydataset \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/my_smolvla \
  --job_name=my_smolvla_training \
  --policy.device=cuda \
  --wandb.enable=true
```

**Google Colab에서 테스트:** https://colab.research.google.com/github/huggingface/notebooks/blob/main/lerobot/training-smolvla.ipynb

**파인튜닝 모델 평가:**
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=my_blue_follower_arm \
  --robot.cameras="{ front: {type: opencv, index_or_path: 8, width: 640, height: 480, fps: 30, fourcc: "MJPG"}}" \
  --dataset.single_task="Grasp a lego block and put it in the bin." \
  --dataset.repo_id=${HF_USER}/eval_DATASET_NAME_test \
  --dataset.episode_time_s=50 \
  --dataset.num_episodes=10 \
  --policy.path=HF_USER/FINETUNE_MODEL_NAME
```

### LIBERO 벤치마크

LIBERO는 여러 태스크 스위트에 걸쳐 정책을 평가하기 위한 **평생학습(lifelong learning) 로봇 벤치마크**입니다.

**설치:**
```bash
pip install -e ".[libero]"
```

**단일 스위트 평가:**
```bash
lerobot-eval \
  --policy.path="your-policy-id" \
  --env.type=libero \
  --env.task=libero_object \
  --eval.batch_size=2 \
  --eval.n_episodes=3
```

**다중 스위트 평가:**
```bash
lerobot-eval \
  --policy.path="your-policy-id" \
  --env.type=libero \
  --env.task=libero_object,libero_spatial \
  --eval.batch_size=1 \
  --eval.n_episodes=2
```

**학습 예시 명령어:**
```bash
lerobot-train \
  --policy.type=smolvla \
  --policy.repo_id=${HF_USER}/libero-test \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --env.type=libero \
  --env.task=libero_10 \
  --output_dir=./outputs/ \
  --steps=100000 \
  --batch_size=4 \
  --eval.batch_size=1 \
  --eval.n_episodes=1 \
  --eval_freq=1000
```

**MuJoCo 렌더링 백엔드:**
```bash
export MUJOCO_GL=egl  # 헤드리스 서버용
```

### Pi0 정책

**설치:**
```bash
pip install -e ".[pi]"
```

**학습:**
```bash
lerobot-train \
  --policy.type=pi0 \
  --dataset.repo_id=seeed/eval_test123 \
  --job_name=pi0_training \
  --output_dir=outputs/pi0_training \
  --policy.pretrained_path=lerobot/pi0_base \
  --policy.compile_model=true \
  --policy.gradient_checkpointing=true \
  --policy.dtype=bfloat16 \
  --steps=20000 \
  --policy.device=cuda \
  --batch_size=32 \
  --wandb.enable=false
```

**평가:**
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"},   side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30,fourcc: "MJPG"}}" \
  --robot.id=my_awesome_follower_arm \
  --display_data=false \
  --dataset.repo_id=seeed/eval_test123 \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=outputs/pi0_training/checkpoints/last/pretrained_model
```

### Pi0.5 정책

**설치:**
```bash
pip install -e ".[pi]"
```

**학습:**
```bash
lerobot-train \
    --dataset.repo_id=seeed/eval_test123 \
    --policy.type=pi05 \
    --output_dir=outputs/pi05_training \
    --job_name=pi05_training \
    --policy.pretrained_path=lerobot/pi05_base \
    --policy.compile_model=true \
    --policy.gradient_checkpointing=true \
    --wandb.enable=false \
    --policy.dtype=bfloat16 \
    --steps=3000 \
    --policy.device=cuda \
    --batch_size=32
```

**평가:**
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"},   side: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30,fourcc: "MJPG"}}" \
  --robot.id=my_awesome_follower_arm \
  --display_data=false \
  --dataset.repo_id=seeed/eval_test123 \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=outputs/pi05_training/checkpoints/last/pretrained_model
```

### GR00T N1.5 정책

GR00T N1.5는 NVIDIA에서 공개한 **크로스 임바디먼트(cross-embodiment) 파운데이션 모델**로, 로봇 추론과 스킬 학습을 지원합니다.

**참고자료:**
- 공식 문서: https://huggingface.co/docs/lerobot/groot
- GR00T N1.5 논문: https://arxiv.org/abs/2306.03310

**설치 (CUDA, FlashAttention 필요):**

1. 베이스 환경 준비 (Python, CUDA, 드라이버)
2. PyTorch 설치:
```bash
pip install "torch>=2.2.1,<2.8.0" "torchvision>=0.21.0,<0.23.0"
```

3. FlashAttention 설치:
```bash
pip install ninja "packaging>=24.2,<26.0"
pip install "flash-attn>=2.5.9,<3.0.0" --no-build-isolation
python -c "import flash_attn; print(f'Flash Attention {flash_attn.__version__} imported successfully')"
```

4. groot 포함해 LeRobot 설치:
```bash
pip install "lerobot[groot]"
```

**설치 문제 해결:**
PyTorch/CUDA 버전 일치, 빌드 의존성, 환경의 노후화 여부를 확인. 공식 GR00T 및 PyTorch 문서를 먼저 검토할 것.

**학습 (다중 GPU 파인튜닝):**
```bash
accelerate launch \
  --multi_gpu \
  --num_processes=$NUM_GPUS \
  $(which lerobot-train) \
  --output_dir=$OUTPUT_DIR \
  --save_checkpoint=true \
  --batch_size=$BATCH_SIZE \
  --steps=$NUM_STEPS \
  --save_freq=$SAVE_FREQ \
  --log_freq=$LOG_FREQ \
  --policy.push_to_hub=true \
  --policy.type=groot \
  --policy.repo_id=$REPO_ID \
  --policy.tune_diffusion_model=false \
  --dataset.repo_id=$DATASET_ID \
  --wandb.enable=true \
  --wandb.disable_artifact=true \
  --job_name=$JOB_NAME
```

**온로봇 검증 (단일 암):**
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=follower \
  --robot.cameras='{ right: {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, left: {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}, top: {"type": "opencv", "index_or_path": 4, "width": 640, "height": 480, "fps": 30} }' \
  --display_data=true \
  --dataset.repo_id=${HF_USER}/eval_groot_test \
  --dataset.num_episodes=10 \
  --dataset.single_task="Grab and place the red cube" \
  --policy.path=${HF_USER}/groot-test \
  --dataset.episode_time_s=30 \
  --dataset.reset_time_s=10
```

**라이선스:** Apache 2.0 (원본 GR00T 저장소와 동일)

### (선택) 파라미터 효율적 파인튜닝 (PEFT)

PEFT는 대형 사전학습 모델을 작은 **어댑터(adapter) 파라미터**만 업데이트하여 새로운 태스크에 적응시키는 기법입니다.

**설치:**
```bash
pip install -e ".[peft]"
```

**예제: LIBERO에서 LoRA로 SmolVLA 파인튜닝:**
```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --policy.repo_id=${HF_USER}/my_libero_smolvla_peft \
  --dataset.repo_id=HuggingFaceVLA/libero \
  --env.type=libero \
  --env.task=libero_spatial \
  --output_dir=outputs/train/my_libero_smolvla_peft \
  --job_name=my_libero_smolvla_peft \
  --policy.device=cuda \
  --steps=10000 \
  --batch_size=32 \
  --optimizer.lr=1e-3 \
  --peft.method_type=LORA \
  --peft.r=64
```

**주요 PEFT 인자:**
- `--peft.method_type`: PEFT 방법 (예: `LORA`)
- `--peft.r`: LoRA rank (값이 클수록 용량 증가, VRAM도 증가)

**타겟 모듈 커스터마이즈 (선택):**

리스트 형식:
```bash
--peft.target_modules="['q_proj', 'v_proj']"
```

정규식 형식:
```bash
--peft.target_modules='(model\\.vlm_with_expert\\.lm_expert\\..*\\.(down|gate|up)_proj|.*\\.(state_proj|action_in_proj|action_out_proj|action_time_mlp_in|action_time_mlp_out))'
```

**특정 모듈을 전체 학습:**
```bash
--peft.full_training_modules="['state_proj']"
```

**학습률 권장:** LoRA의 학습률은 전체 파인튜닝보다 **약 10배 높게** 설정 (예: 1e-3 vs 1e-4).

### (선택) Accelerate를 이용한 다중 GPU 학습

**Accelerate 설치:**
```bash
pip install accelerate
```

**방법 1: CLI 플래그 사용:**
```bash
accelerate launch \
--multi_gpu \
--num_processes=2 \
$(which lerobot-train) \
--dataset.repo_id=${HF_USER}/my_dataset \
--policy.type=act \
--policy.repo_id=${HF_USER}/my_trained_policy \
--output_dir=outputs/train/act_multi_gpu \
--job_name=act_multi_gpu \
--wandb.enable=true
```

**Accelerate 플래그:**
- `--multi_gpu`: 다중 GPU 활성화
- `--num_processes`: GPU 개수
- `--mixed_precision=fp16`: fp16 사용 (지원되면 bf16 가능)

**정밀도 지원:**

| 정밀도 | 지원 범위 |
|---|---|
| fp16 | 거의 모든 NVIDIA GPU |
| bf16 | 최신 GPU (Ampere 이후) |

**방법 2: 설정 파일 사용 (선택):**
```bash
accelerate config
```

인터랙티브 설정으로 저장하여 반복적인 CLI 입력을 피할 수 있습니다.

이후 실행:
```bash
accelerate launch $(which lerobot-train) \
--dataset.repo_id=${HF_USER}/my_dataset \
--policy.type=act \
--policy.repo_id=${HF_USER}/my_trained_policy \
--output_dir=outputs/train/act_multi_gpu \
--job_name=act_multi_gpu \
--wandb.enable=true
```

**다중 GPU용 하이퍼파라미터 조정:**
- **Steps**: 유효 배치가 증가하므로 `1 / num_gpus` 비율로 감소.
- **Learning rate**: GPU 수에 비례해 선형 스케일링 (`new_lr = single_gpu_lr × num_gpus`).

예시:
```bash
accelerate launch --num_processes=2 $(which lerobot-train) \
--batch_size=8 \
--steps=50000 \
--optimizer.lr=2e-4 \
--dataset.repo_id=lerobot/pusht \
--policy=act
```

Accelerate 공식 문서 참조: https://huggingface.co/docs/accelerate/index

### (선택) 비동기 추론 (Asynchronous Inference)

비동기 추론은 **정책 예측(policy prediction)** 과 **로봇 실행(robot execution)** 을 분리하여 유휴(idle) 시간을 줄입니다.

**개념:**
- **클라이언트(Client):** 로봇팔·카메라에 연결되어 관측값을 서버로 전송하고, 반환된 액션을 실행.
- **서버(Server):** 데이터를 수신하여 추론을 돌리고, 액션 청크(chunk)를 전송.
- **액션 청크(Action chunk):** 정책 추론으로 생성되는 로봇팔 명령 시퀀스.

**배포 시나리오:**
1. **단일 머신**: 로봇·카메라·클라이언트·서버가 동일 장치.
2. **LAN 배포**: 로봇팔은 경량 장치, 서버는 고성능 머신.
3. **크로스 네트워크**: 서버는 퍼블릭 클라우드, 클라이언트는 인터넷 경유 접속.

**보안 주의:** LeRobot의 비동기 추론은 gRPC + pickle 역직렬화 리스크가 존재합니다. 퍼블릭 배포 시 **VPN/SSH 터널링** 이나 **소스 IP 제한**을 사용하세요.

#### 시작하기

**1단계: 의존성 설치**
```bash
pip install -e ".[async]"
```

**2단계: 네트워크 설정**

프록시 이슈 — 프록시 임시 해제:
```bash
unset http_proxy https_proxy ftp_proxy all_proxy HTTP_PROXY HTTPS_PROXY FTP_PROXY ALL_PROXY
```

방화벽 포트 개방 (LAN/클라우드 배포용):
```bash
sudo ufw allow 8080/tcp
```

서버 IP 확인:

Linux / Jetson / Raspberry Pi:
```bash
hostname -I
```

또는:
```bash
ip addr
```

Windows:
```bash
ipconfig
```

macOS:
```bash
ifconfig
```

연결 테스트 (LAN 예시):
```bash
nc -vz <LAN IP address> 8080
```

**3단계: 서비스 시작**

단일 머신:
```bash
python -m lerobot.async_inference.policy_server \
--host=127.0.0.1 \
--port=8080
```

LAN 배포:
```bash
python -m lerobot.async_inference.policy_server \
--host=0.0.0.0 \
--port=8080
```

클라이언트는 `<LAN IP address>:8080`에 연결.

클라우드 배포:
```bash
python -m lerobot.async_inference.policy_server \
--host=0.0.0.0 \
--port=8080
```

클라이언트는 `<서버 퍼블릭 IP>:8080` 에 연결.

**4단계: 추론 파라미터 선택 (클라이언트 측)**
```bash
python -m lerobot.async_inference.robot_client \
--server_address=<ip address>:8080 \
--robot.type=so100_follower \
--robot.port=/dev/tty.usbmodem585A0076841 \
--robot.id=follower_so100 \
--robot.cameras="{ laptop: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}, phone: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}}" \
--task="dummy" \
--policy_type=your_policy_type \
--pretrained_name_or_path=user/model \
--policy_device=cuda \
--actions_per_chunk=50 \
--chunk_size_threshold=0.5 \
--aggregate_fn_name=weighted_average \
--debug_visualize_queue_size=True
```

**파라미터 설명:**
- `--server_address`: 정책 서버의 주소:포트 (`127.0.0.1`, LAN IP, 클라우드 IP)
- `--robot.type`, `--robot.port`, `--robot.id`, `--robot.cameras`: 하드웨어 파라미터 (데이터 수집 시와 일치해야 함)
- `--task`: 태스크 설명 (비전-언어 정책용)
- `--policy_type`: 정책 이름 (`smolvla`, `act` 등)
- `--pretrained_name_or_path`: 서버의 모델 경로 또는 Hugging Face 경로
- `--policy_device`: `cuda`, `mps`, `cpu`
- `--actions_per_chunk`: 추론당 액션 수 (클수록 버퍼 충분, 호라이즌(horizon) 증가)
- `--chunk_size_threshold`: 큐 비율이 이 값 이하로 떨어지면 새 청크 요청 (0–1 범위)
- `--aggregate_fn_name`: 오버랩 집계 방식 (부드러운 전환엔 `weighted_average` 권장)
- `--debug_visualize_queue_size`: 실행 중 액션 큐 시각화

**5단계: 파라미터 튜닝**

| 파라미터 | 권장값 | 설명 |
|---|---|---|
| `actions_per_chunk` | 50 | 추론당 액션 수. 일반적으로 10–50 |
| `chunk_size_threshold` | 0.5 | 큐 임계치. 범위 [0, 1] |

**원칙:** 서버 생성 속도 ≥ 클라이언트 소비 속도.

큐가 자주 비워진다면:
- `actions_per_chunk` 증가
- `chunk_size_threshold` 증가
- fps 감소

경험적 범위: `actions_per_chunk` 10–50, `chunk_size_threshold` 0.5–0.7

**문제 해결:**
스택 에러 발생 시:
```bash
pip install datasets==2.19
```

---

## 학습 체크포인트 및 업로드

**학습은 수 시간이 소요됩니다.** 체크포인트는 `outputs/train/act_so101_test/checkpoints`에 저장됩니다.

**체크포인트에서 재개:**
```bash
lerobot-train \
  --config_path=outputs/train/act_so101_test/checkpoints/last/pretrained_model/train_config.json \
  --resume=true
```

**정책 체크포인트 업로드:**
```bash
huggingface-cli upload ${HF_USER}/act_so101_test \
  outputs/train/act_so101_test/checkpoints/last/pretrained_model
```

중간 체크포인트 업로드:
```bash
CKPT=010000
huggingface-cli upload ${HF_USER}/act_so101_test${CKPT} \
  outputs/train/act_so101_test/checkpoints/${CKPT}/pretrained_model
```

---

## FAQ

**일반 팁:**
- 권장 저장소 클론: https://github.com/Seeed-Projects/lerobot.git (**공식 repo가 아닌 안정 버전**)
- 공식 repo는 계속 업데이트되어 버전 불일치가 발생할 수 있음.

**서보 설정 오류:**

`"Motor 'gripper' was not found"` → 통신 케이블 연결 및 전원 전압 확인.

**시리얼 포트 문제:**

`"Could not connect on port '/dev/ttyACM0'"` + 포트 존재 확인됨 → 실행: `sudo chmod 666 /dev/ttyACM*`

**비디오 인코딩 오류:**

`"No valid stream found in input file"` → ffmpeg 7.1.1 설치: `conda install ffmpeg=7.1.1 -c conda-forge`

**모터 통신:**

`"ConnectionError: Failed to sync read 'Present_Position'"` → 전원 확인, 버스 서보 데이터 케이블(느슨/분리 여부) 점검.

**캘리브레이션 오류:**

`"Magnitude 30841 exceeds 2047"` → 로봇팔 전원을 껐다가 재시작 후 재캘리브레이션. MAX 각도가 수만 단위로 표시된다면, **중간 위치 캘리브레이션과 ID 쓰기(ID writing)** 를 포함한 서보 재캘리브레이션을 수행.

**평가 오류:**

`"File exists: 'home/xxxx/.cache/huggingface/lerobot/xxxxx/seeed/eval_xxxx'"` → 해당 `eval_` 폴더 삭제 후 재시도.

`"mean is infinity. You should either initialize with stats as argument or use pretrained model"` → 카메라 키워드(예: `"front"`, `"side"`)가 데이터 수집 시와 정확히 일치하는지 확인.

**하드웨어 유지보수:**

로봇팔 부품 수리/교체 후 → `~/.cache/huggingface/lerobot/calibration/robots` 또는 `~/.cache/huggingface/lerobot/calibration/teleoperators` 의 캘리브레이션 파일 삭제 후 재캘리브레이션.

**학습 시간:**
- 50 에피소드 기준 ACT: RTX 3060 8GB에서 약 6시간, RTX 4090/A100에서 2–3시간.

**데이터 수집 베스트 프랙티스:**
- 카메라 위치·각도·조명 안정화.
- 불안정한 배경과 지나가는 사람 최소화.
- `num_episodes` 파라미터를 충분히 설정.
- **수동으로 일시정지하지 말 것** — 평균/분산은 완료 시점에 계산됨.
- 학습 전 데이터 수집을 완전히 마칠 것.

---

**페이지 내용 끝**
