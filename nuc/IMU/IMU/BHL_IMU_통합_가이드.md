# BHL × 우리 IMU 통합 가이드 (Python 경로)

> **목적**: Berkeley Humanoid Lite(BHL) 의 **Python 컨트롤 경로** ([scripts/run_locomotion.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/scripts/run_locomotion.py)) 를 기준으로, 우리가 사용할 IMU(WitMotion 계열, CP2102 USB-UART) 를 통합하기 위해 어디를 어떻게 손봐야 하는지 단계별로 정리.
>
> **C++ 경로(`make run` + `csrc/imu.cpp`) 는 사용하지 않음.** Python 경로의 [SerialImu](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py) 가 이미 WitMotion 프로토콜로 작성돼 있어 드라이버 재작성이 필요 없음.
>
> 작성일: 2026-05-19 (Python 경로로 재작성)
>
> **정정: 2026-05-20** — 실측 하드웨어 반영: IMU USB 칩 CP2102→CH340, brltty 채감 함정 추가, quat 순서 (w,x,y,z) 검증 완료, §4.D `stop()` 보강.

---

## 1. 우리 IMU 정체

- **USB-UART 칩**: WinChipHead **CH340** (`idVendor=1a86 idProduct=7523`)
  - ⚠️ **정정 (2026-05-20 실측)**: 튜토리얼의 [imu_usb.rules](1.%20Tutorials/Program%20Files%20/6.ROS2%20Application%20Program/wit_ros2_imu/imu_usb.rules) 는 CP2102(`10c4:ea60`)를 가정하지만, **우리가 가진 metal-shell 버전은 CH340**이다. udev 규칙(§4.B)·인식 절차(Step 1/2)를 모두 CH340 기준으로 정정함.
  - CH340 은 시리얼 번호가 없어(`serial=''`) `ATTRS{serial}` 로 구분 불가 — 다만 CANable2(`16d0:117e`, ttyACM)와 칩이 달라 충돌은 없음.
- **프로토콜**: **WitMotion 11바이트 프레임**
  - 헤더 `0x55` + frame type 1B (`0x51` acc, `0x52` gyro, `0x53` euler, `0x54` mag, `0x59` quaternion) + 8B payload + 1B 체크섬(앞 10B 합 & 0xff)
  - 근거: [1. Tutorials/Program Files /3.Raspberry Pi-USB Application Program/imu_usb/imu_usb/imu_usb.py:25-80](1.%20Tutorials/Program%20Files%20/3.Raspberry%20Pi-USB%20Application%20Program/imu_usb/imu_usb/imu_usb.py)
- **기본 baud**: 9600 (레지스터로 460800/921600 까지 상향 가능)
- **출력 단위**:
  - 가속도: `int16/32768 × 16 g`
  - 각속도: `int16/32768 × 2000 °/s`
  - 오일러각: `int16/32768 × 180 °`
  - 쿼터니언: `int16/32768` (RSW 레지스터에서 enable 시 0x59 프레임으로 출력)
- **마운트 도면**: [3. Drawing/IMU Module Model Schematic.pdf](3.%20Drawing/IMU%20Module%20Model%20Schematic.pdf), [3. Drawing/IMU.stp](3.%20Drawing/IMU.stp)

---

## 2. BHL Python 경로가 IMU 에 기대하는 것

[run_locomotion.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/scripts/run_locomotion.py) → [Humanoid()](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/humanoid.py) → [SerialImu](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py) 흐름.

[humanoid.py:175-198](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/humanoid.py) 의 `get_observations()` 이 매 step 마다 `lowlevel_states[0:7]` 에 채우는 IMU 슬롯:

| 슬롯 | 필드 | 단위/형식 |
|---|---|---|
| `[0:4]` | `base_quat` ← `self.imu.quaternion[:]` | **(w, x, y, z)**, normalized |
| `[4:7]` | `base_ang_vel` ← `np.deg2rad(self.imu.angular_velocity[:])` | **rad/s** (Python 단에서 자동 변환) |

> **이미 잘 돼 있는 것**: rad/s 변환이 `np.deg2rad()` 로 자동 적용됨 ([humanoid.py:186](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/humanoid.py#L186)). 우리가 추가로 손댈 일 없음.

`projected_gravity` 는 [rl_controller.py:171](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/rl_controller.py#L171) 에서 quat 으로부터 직접 계산. quat 만 정상이면 됨.

---

## 3. 격차 한눈에 보기 (Python 경로 기준)

| 항목 | BHL Python 기본값 | 우리 환경 | 조치 |
|---|---|---|---|
| 프로토콜 | WitMotion 11B (`SerialImu.__read_frame` 가 직접 파싱) | WitMotion 11B | **동일, 코드 무수정** |
| Baud | `Baudrate.BAUD_460800` ([humanoid.py:65](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L65)) | 460800 으로 IMU 설정 필요 (기본 9600) | IMU 1회 설정 (§4.A) |
| 각속도 단위 | rad/s (humanoid.py 에서 deg2rad) | OK | **이미 처리됨** |
| Quat 단위 | int16/32768 → float | OK | **이미 처리됨** |
| Quat 순서 | (Q0,Q1,Q2,Q3) 를 (w,x,y,z) 가정 ([imu.py:272-276](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L272-L276)) | ✅ **(w,x,y,z) 정상 — 2026-05-20 실측 검증 완료** | imu.py 무수정 |
| 디바이스 경로 | `"/dev/ttyUSB0"` ([imu.py:200](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L200) 기본값) | CAN-USB 와 공존 시 번호 흔들림 | udev rule 로 `/dev/hylion_imu` 고정 (§4.B) |
| 명령 입력 | `Se2Gamepad` (**물리 USB 게임패드**, `inputs.get_gamepad()`) | Coordinator NDJSON → bridge.py → UDP `:10011` | `command_controller` 를 UDP 수신기로 교체 (§4.D) |
| 실행 단위 | `python run_locomotion.py` 수동 | systemd 자동 기동 원함 | unit 작성 (§4.E) |

---

## 4. 고려할 점 · 수정할 점

### A. IMU 자체 1회 설정 (윈도우 PC 툴, 필수)

[2. Software/imu Module PC Software](2.%20Software/imu%20Module%20PC%20Software) 로 IMU 연결 후 다음 레지스터 설정하고 **반드시 SAVE 커밋**:

- **RSW (0x02)**: `acceleration + angular_velocity + quaternion` enable
  - quat 안 켜면 `0x59` 프레임 안 나오고 `imu.quaternion` 영원히 (0,0,0,0) → 정책 입력 박살
- **RRATE (0x03)**: 200 Hz (모델 최대치)
  - 정책 obs 가 25 Hz 라 200 Hz IMU 면 8× 오버샘플 충분
- **BAUD (0x04)**: 460800
  - `SerialImu` 기본값과 일치. 9600 으로는 200 Hz 데이터량 못 보냄
- **ORIENT (0x23)**: 로봇 `base_link` (전방=+X, 왼쪽=+Y, 위=+Z) 와 IMU 장착 방향 일치
- **AXIS6 (0x24)**: 6축(가속+자이로) 모드 권장 — 실내 자기장 간섭 회피
- **CALSW (0x01)**: 자이로 정지 캘리브레이션 1회 + 가속도 6면 캘리브레이션

> **꿀팁**: `SerialImu` 자체에 [`unlock()`/`save()`/`set_output_content()`/`set_sampling_rate()`/`set_baudrate()`](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L309-L399) 가 다 구현돼 있어 윈도우 PC 없이 NUC 에서 Python 만으로도 설정 가능. [imu.py:402-426](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L402-L426) 의 `if __name__ == "__main__"` 블록에 예시 있음.

### B. udev rule (USB 경로 고정)

```
# /etc/udev/rules.d/99-hylion-imu.rules  (CH340 기준 — 2026-05-20 정정판)
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE:="0666", SYMLINK+="hylion_imu"
```

> **⚠️ brltty 가 CH340 을 가로챈다 (실측 함정)**: Ubuntu 의 `brltty`(점자 디스플레이 SW)가 `/usr/lib/udev/rules.d/85-brltty.rules` 에서 `1a86/7523` 을 점자기로 오인해 채간다 → `ch341` 드라이버가 못 붙고 `/dev/ttyUSB*` 자체가 안 생긴다. 로봇 NUC 에선 `sudo apt-get purge brltty libbrlapi0.8 python3-brlapi` 로 제거 후 USB 재삽입. (Step 1 에서 ttyUSB 가 안 보이면 1순위 의심)
>
> **주의**: 우리 IMU(CH340)와 CANable2(`16d0:117e`)는 칩이 달라 충돌 없음. 단 다른 CH340 장치(아두이노·ESP32 dev board 등)를 NUC 에 추가로 꽂으면 같은 규칙에 잡히므로, 그땐 `KERNELS=="1-5.2"` 식으로 USB 포트 경로를 고정할 것.

### C. `SerialImu` 인스턴스화 시 port 지정

[humanoid.py:65](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L65):

```python
# 변경 전
self.imu = SerialImu(baudrate=Baudrate.BAUD_460800)

# 변경 후
self.imu = SerialImu(port="/dev/hylion_imu", baudrate=Baudrate.BAUD_460800)
```

또는 [imu.py:200](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L200) 의 default 자체를 `"/dev/hylion_imu"` 로 바꿔도 됨.

### D. `command_controller` 교체 (Hylion 명령 입력 연결) — **필수**

> **왜 필수인가**: C++ 경로의 `loop_joystick` 은 UDP `:10011` 을 직접 수신했지만, Python 경로의 기본 명령 소스 `Se2Gamepad` 는 [gamepad.py:83](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/gamepad.py#L83) `inputs.get_gamepad()` 로 **물리 USB 게임패드**를 읽음 (UDP 수신 아님). 즉 이 교체를 안 하면 [bridge.py](../bhl/bridge.py) 가 쏜 UDP `:10011` 을 받는 사람이 없어 Coordinator 명령이 로봇에 도달하지 못함.
>
> **반대로, Coordinator(Jetson) 와 bridge.py 는 손대지 않아도 됨.** bridge.py 가 보내는 13-byte `<Bfff` UDP 포맷을 아래 `UdpCommandReceiver` 가 그대로 받도록 설계했기 때문. "Python 에 맞게 바꾼다" = 신호 프로토콜이 아니라 NUC 안의 *수신 코드*를 바꾸는 것.

[humanoid.py:71-72](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L71-L72) 에서 `Se2Gamepad` 가 `self.commands` dict 를 채움:

```python
self.commands = {
    "velocity_x":   ...,  # m/s
    "velocity_y":   ...,
    "velocity_yaw": ...,  # rad/s
    "mode_switch":  ...,  # 1=IDLE / 2=RL_INIT / 3=RL_RUNNING
}
```

[humanoid.py:191-196](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L191-L196) 이 매 `get_observations()` 때 이 dict 를 읽어감.

**방향 1 (권장, 변경폭 최소)**: `Se2Gamepad` 와 동일한 인터페이스 (`.commands` dict + `run()` 메서드) 를 가진 클래스를 만들어 교체. 내부는 [nuc/bhl/bridge.py](../bhl/bridge.py) 가 보내는 UDP `:10011` 13-byte 패킷(`<Bfff` = mode + vx + vy + vyaw) 을 수신.

```python
# berkeley_humanoid_lite_lowlevel/policy/udp_command.py (신규)
import socket, struct, threading

class UdpCommandReceiver:
    def __init__(self, port: int = 10011):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", port))
        self.commands = {
            "velocity_x": 0.0, "velocity_y": 0.0,
            "velocity_yaw": 0.0, "mode_switch": 1,
        }

    def run(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            data, _ = self.sock.recvfrom(13)
            mode, vx, vy, vyaw = struct.unpack("<Bfff", data)
            self.commands["mode_switch"]  = int(mode)
            self.commands["velocity_x"]   = float(vx)
            self.commands["velocity_y"]   = float(vy)
            self.commands["velocity_yaw"] = float(vyaw)
```

> **정정 (2026-05-20)**: 위 최소 스니펫엔 `stop()` 이 빠져 있다. `Humanoid.stop()` 이 `command_controller.stop()` 을 호출하므로([humanoid.py:152](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/humanoid.py#L152)), `stop()`(쓰레드 종료 + 소켓 close)·패킷 길이 검증·`socket.timeout` 처리를 갖춘 완성본을 [udp_command.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/udp_command.py) 로 작성해 두었다. 실제 파일은 그쪽을 참조.

그리고 [humanoid.py:71-72](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L71-L72) 를:

```python
# 변경 전
self.command_controller = Se2Gamepad()
self.command_controller.run()

# 변경 후
from berkeley_humanoid_lite_lowlevel.policy.udp_command import UdpCommandReceiver
self.command_controller = UdpCommandReceiver(port=10011)
self.command_controller.run()
```

**방향 2**: bridge.py 자체를 Coordinator NDJSON 을 직접 NDJSON→dict 로 변환해 Python 컨트롤러에 넘기는 형태로 재작성. 변경폭 크지만 UDP 한 단계 없앨 수 있음. 지금 단계에선 방향 1 추천.

> **cold_start 트리거 시점 (설계 노트, 2026-05-20)**
>
> [bridge.py](../bhl/bridge.py) 의 `cold_start()` 는 **소프트웨어 핸드셰이크가 아니라 로봇이 다리를 물리적으로 활성화하는 시퀀스**다 — RL_INIT(default 자세로 이동, ~1초) → RL_RUNNING(균형 정책 가동). 현재는 **coordinator 의 첫 유효 명령 수신 시** 1회 실행된다 (재연결 시 재실행).
>
> - **현행 유지 (안전 인터락)**: 명령이 와야(= 시스템이 다 떴고 운영자가 동작 의도가 있음) 다리가 활성화된다. bridge 시작 시점·부팅 시 자동으로 cold_start 를 돌리면 **무명령 상태에서 로봇이 다리를 펴고 균형정책을 돌려 위험**하다 — 특히 §4.E systemd 자동기동과 결합하면 NUC 전원을 넣을 때마다 활성화된다. **자동 트리거로 바꾸지 말 것.**
> - 무거운 셋업(IMU/CAN/소켓/ONNX 로드)은 `run_locomotion.py` 시작 시 이미 끝나므로 "미리 준비"는 되어 있다. cold_start 의 ~1.6초는 다리가 실제로 움직이는 물리 시간이라 줄일 수 없고, **맨 첫 명령 1회만** 발생한다 (이후 명령은 즉시).
> - **향후 옵션 — 명시적 "준비(prepare)" 명령**: 첫 walk 명령의 1.6초 지연마저 없애려면, coordinator 가 운영자 준비 완료(거치대 거치 등) 시 보내는 명시적 prepare 메시지(예: `intent == "prepare"`)를 추가하고 그때 cold_start 를 유도하면 된다 — 이후 move 명령은 즉시 실행. 단 트리거는 여전히 "명시적 명령 수신"이어야 하며 자동 기동이면 안 된다. 구현 시 [bridge.py](../bhl/bridge.py) `handle_client()` 의 cold_start 트리거 지점 + `map_json_to_packet()` + `tests/mock_coordinator.py` 시나리오를 함께 손볼 것.

### E. systemd unit

C++ `make run` 대신 Python 스크립트를 띄우는 unit. [systemd/hylion-bridge.service](../bhl/systemd/hylion-bridge.service) 와 같은 위치에 추가:

```ini
# /etc/systemd/system/hylion-locomotion.service
[Unit]
Description=Hylion BHL Locomotion (Python policy + low-level)
After=network-online.target hylion-bridge.service
Wants=network-online.target
Requires=hylion-bridge.service
ConditionPathExists=/dev/hylion_imu

[Service]
Type=simple
User=nuc
Group=nuc
WorkingDirectory=/opt/hylion/nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main
ExecStart=/usr/bin/python3 -u scripts/run_locomotion.py
Restart=on-failure
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hylion-locomotion

[Install]
WantedBy=multi-user.target
```

`ConditionPathExists=/dev/hylion_imu` 가 udev 심볼릭 생성 전 기동 → init 실패 케이스를 막아줌.

### F. 좌표계 / 축 검증 (Quat 순서 포함)

학습 obs 의 `base_ang_vel` 은 body frame, `projected_gravity` 는 quat 으로 계산됨 ([docs/11_bhl_reference_flow.md:192-194](../../docs/11_bhl_reference_flow.md)).

- IMU 의 +X = 로봇 전방, +Y = 로봇 왼쪽, +Z = 위 (URDF `base_link` 일치)
- 안 맞으면 ORIENT 레지스터 또는 [humanoid.py:183](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L183) 단계에서 부호/축 재배치
- 직립 정지 시 검증:
  - `angular_velocity ≈ (0, 0, 0)`
  - quat → `projected_gravity ≈ (0, 0, -1)`

[imu.py:272-276](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L272-L276) 은 펌웨어가 (w,x,y,z) 순서로 보낸다고 가정. 만약 펌웨어가 (x,y,z,w) 면 직립인데도 quat ≈ (0,0,0,1) 이 나옴 → 매핑 순서 교체 필요.

### G. 레이트 / 결정성 메모

- Python 의 `SerialImu.run_forever()` 가 별도 쓰레드로 200 Hz IMU 읽기. 메인 25 Hz 정책 루프와 분리돼 GIL 영향 작음 (serial read 는 I/O 라 GIL 양보).
- 정책 obs 주기 25 Hz vs IMU 200 Hz → 8× 오버샘플로 stale obs 위험 낮음.
- jitter 가 신경 쓰이면 시스템 차원에서 `nice -n -5` 또는 `chrt -f 50` 으로 RT 우선순위 부여. (BHL Python 도 [imu.py:294-301](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L294-L301) 에서 `process.nice(0)` 만 시도하는 수준이므로 부족하면 직접 올려야 함)

---

## 5. 진행 순서 (step-by-step)

> **전제**: NUC 에 IMU USB 1개 + CAN-USB 2개를 모두 꽂은 상태. 로봇 다리는 처음 검증 단계에서는 **분리하거나 전원 OFF** 권장.

### Step 1. USB 인식 확인 `[NUC]`

```bash
lsusb | grep -iE "1a86|ch340|10c4|cp210"
# 우리 IMU 예시: Bus 001 Device 010: ID 1a86:7523 QinHeng Electronics CH340 serial converter

ls -l /dev/ttyUSB*
# ttyUSB 가 하나도 없으면 brltty 가 CH340 을 채간 것 (§4.B 참고)
```

CAN-USB 와 vendor/product 겹치면 시리얼로 구분:

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -E "idVendor|idProduct|serial"
# 각 ttyUSB* 반복해서 IMU 의 serial 메모
```

### Step 2. udev rule 등록 `[NUC]`

```bash
sudo tee /etc/udev/rules.d/99-hylion-imu.rules > /dev/null <<'EOF'
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE:="0666", SYMLINK+="hylion_imu"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

USB 빼고 다시 꽂은 뒤 `ls -l /dev/hylion_imu` 가 ttyUSB* 로 가는 심볼릭이면 성공.

### Step 3. IMU 1회 설정 `[NUC or 별도 윈도우 PC]`

**옵션 A: 윈도우 PC 툴 사용**

[2. Software/imu Module PC Software](2.%20Software/imu%20Module%20PC%20Software) 로:
1. RSW: acc + gyro + quat 체크
2. RRATE: 200 Hz
3. BAUD: 460800
4. AXIS6: 6축
5. ORIENT: 로봇 장착 방향
6. 자이로 정지 캘리브 → 가속도 6면 캘리브
7. **SAVE 클릭**

**옵션 B: NUC 에서 Python 으로 직접 설정 (PC 안 거치고)**

```python
# 임시 스크립트 (NUC 에서 실행)
from berkeley_humanoid_lite_lowlevel.robot.imu import SerialImu, Baudrate, SamplingRate
import time

# 우선 현재 baud 로 연결 (공장 출하시 9600 또는 115200)
imu = SerialImu(port="/dev/hylion_imu", baudrate=Baudrate.BAUD_9600)

imu.unlock(); time.sleep(0.1)
imu.set_output_content(acceleration=True, angular_velocity=True, quaternion=True)
time.sleep(0.1)
imu.set_sampling_rate(SamplingRate.RATE_200_HZ)
time.sleep(0.1)
imu.set_baudrate(Baudrate.BAUD_460800)   # 이 시점 이후 통신은 460800
time.sleep(0.1)
imu.save()
```

> ORIENT/AXIS6/캘리브는 PC 툴이 편함 (UI 안내 있음). 옵션 B 는 RSW/RRATE/BAUD 만 권장.

### Step 4. 통신 빠른 확인 `[NUC]`

```bash
stty -F /dev/hylion_imu 460800 raw -echo
hexdump -C /dev/hylion_imu | head -20
# 0x55 로 시작하는 11B 프레임들이 흘러나오면 정상
```

또는 `SerialImu` 단독 실행:

```bash
cd /opt/hylion/nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main
python3 -m berkeley_humanoid_lite_lowlevel.robot.imu
# ax/ay/az  gx/gy/gz  qw/qx/qy/qz  계속 찍히면 OK
```

> **정정 (2026-05-20)**: `robot/__init__.py` 가 `humanoid.py` 를 끌어와 `omegaconf` 를 import 하므로, omegaconf 미설치 환경에선 위 `-m` 실행이 `ModuleNotFoundError` 로 실패한다. IMU 만 따로 확인할 땐 omegaconf 를 먼저 설치하거나, `imu.py` 를 단독 로드(`sys.path` 에 `.../robot/` 추가 후 `import imu`)할 것.

### Step 5. Quat 순서 / 축 검증 (가장 중요) `[NUC]`

위 `python3 -m ...` 실행 상태에서 IMU 만 손으로 들고:

| 자세 | 기대 quat | 기대 ang_vel (deg/s 그대로 보고됨) |
|---|---|---|
| 직립 정지 | `(1, 0, 0, 0)` 근처 (yaw 차이는 무시) | `(0, 0, 0)` |
| 전방으로 90° pitch | qx 또는 qy 가 약 ±0.7, qw ≈ 0.7 | 회전 중 한 축에 ang_vel 봉우리 |
| 왼쪽으로 90° yaw | qz 가 약 ±0.7, qw ≈ 0.7 | gz 봉우리 |

직립인데 `qw ≈ 0` 이고 `qz ≈ 1` 이면 → 펌웨어가 (x,y,z,w) 순. [imu.py:272-276](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L272-L276) 의 인덱싱을 다음처럼 패치:

```python
elif frame_type == FrameType.QUATERNION:
    self.quaternion[1] = data1 * 1.0 / 32768.0  # x
    self.quaternion[2] = data2 * 1.0 / 32768.0  # y
    self.quaternion[3] = data3 * 1.0 / 32768.0  # z
    self.quaternion[0] = data4 * 1.0 / 32768.0  # w
```

축이 어긋나면 ORIENT 레지스터에서 우선 맞춰보고, 안 되면 `humanoid.py:183` 단계에서 swap.

### Step 6. `Humanoid` 클래스에 우리 IMU 경로 + 명령 입력 패치 `[NUC]`

[humanoid.py:65](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L65) 의 `SerialImu(baudrate=...)` 를 `SerialImu(port="/dev/hylion_imu", baudrate=...)` 로.

`Se2Gamepad` 교체는 §4.D 의 `UdpCommandReceiver` 작성 후 [humanoid.py:71-72](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L71-L72) 의 두 줄을 교체.

### Step 7. **다리 분리 상태에서** 정책 루프 동작 확인 `[NUC]`

```bash
# 터미널 1: bridge 띄움 (Coordinator 없으면 mock 으로 STOP 명령만 보내도 됨)
sudo systemctl start hylion-bridge

# 터미널 2: 정책 루프 실행 (수동)
cd /opt/hylion/nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main
python3 scripts/run_locomotion.py

# 터미널 3: obs UDP 흘러나오는지 (run_locomotion.py 가 11000 으로 send)
# obs 안에 quat/ang_vel 정상값인지 확인
```

- IMU 가만히 두면 `ang_vel ≈ (0, 0, 0)` rad/s
- 직립 자세면 quat 가 대략 `(1, 0, 0, 0)` 근처
- 값이 안 변하거나 NaN 이면 Step 3 RSW 설정 또는 Step 5 quat 매핑 의심

### Step 8. systemd 자동 기동 활성화 `[NUC]`

§4.E 의 unit 을 `/etc/systemd/system/hylion-locomotion.service` 로 저장 후:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hylion-locomotion
sudo systemctl start hylion-locomotion
journalctl -u hylion-locomotion -f
```

### Step 9. RL_INIT → RL_RUNNING 진입 시험 (거치대 매단 상태) `[NUC + Jetson]`

- 로봇을 거치대(또는 호이스트)에 매단 상태에서 진행
- Coordinator (또는 mock NDJSON sender) 로 `mode_switch=2` (RL_INIT) → 1.5 s 후 `mode_switch=3` (RL_RUNNING)
- 다리가 default pose 근처에 머무는지, 정책 action 이 ±2 이상으로 폭주하지 않는지 확인
- 폭주 시:
  - quat 부호 통째 반전 가능성 (q 와 -q 는 같은 회전이지만 학습 분포에 따라 ±이슈) → [humanoid.py:183](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py#L183) 에서 `imu_quaternion[:] = -self.imu.quaternion[:]` 로 부호 반전 시도
  - ORIENT/축 매핑 재검토

### Step 10. 실측 보행 시험 (최종) `[NUC + Jetson]`

- 거치대 매단 상태에서 Coordinator 로 `walk_forward` 명령 → 다리 패턴 확인
- 거치대 내려서 짧은 거리 보행 → 쓰러지지 않으면 통합 완료

---

## 6. 자주 박히는 함정

1. **Quat 순서 (w,x,y,z) ↔ (x,y,z,w) 오매핑** → 정책이 "거꾸로 서있다" 로 판단해서 init 자세에서 곧장 쓰러뜨림. Step 5 에서 직접 확인할 것.
2. **RSW 에서 quat 미활성**: 0x59 프레임 자체가 안 나옴 → `imu.quaternion` 영원히 `(0,0,0,0)` (`SerialImu` 가 zeros 로 초기화하므로). 직립인데 quat 모두 0 이면 이 케이스.
3. **BAUD 미저장**: PC 툴/Python 으로 460800 으로 바꿔놓고 SAVE 안 누른 채 전원 끄면 9600 으로 원복 → `SerialImu` 가 460800 으로 열려서 깨진 바이트 수신.
4. **CAN-USB 어댑터와 vendor/product 충돌**: udev rule 이 엉뚱한 디바이스를 `/dev/hylion_imu` 로 잡음. `ATTRS{serial}` 로 구분.
5. **IMU 출력 레이트 < 50 Hz**: 정책 obs 가 stale 해서 보행 발진. RRATE 200 Hz 권장.
6. **ORIENT 미설정 + 코드에서도 remap 안 함**: 직립인데도 정책은 누워있다고 판단.
7. **`SerialImu` port 기본값 그대로**: `"/dev/ttyUSB0"` 가 CAN-USB 일 수도 있음. §4.C 처럼 `/dev/hylion_imu` 로 명시.
8. **C++ 경로와 혼동**: [csrc/imu.cpp](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/csrc/imu.cpp) 는 손대지 않음. Python 경로에서 C++ 빌드는 사용 안 함 (헷갈리면 `csrc/` 디렉토리 자체를 `csrc.unused/` 로 리네임해도 됨).
9. **brltty 가 CH340 IMU 를 가로챔** (2026-05-20 실측): `lsusb` 엔 `1a86:7523` 이 보이는데 `/dev/ttyUSB*` 가 안 생기면 99% `brltty`. `ch341` 모듈은 떠 있어도 refcount 0, 인터페이스가 `usbfs` 에 묶인다. `sudo apt-get purge brltty libbrlapi0.8 python3-brlapi` 후 USB 재삽입. (§4.B 참고)
10. **`dialout` 그룹 미가입**: `/dev/ttyUSB*` 가 `crw-rw---- root dialout` 라 일반 계정은 못 연다. udev 규칙의 `MODE:="0666"` 이 적용되면 해소되지만, 적용 전 단계라면 `sudo usermod -aG dialout <user>` (재로그인 필요).

---

## 7. 참고 파일

- BHL Python 정책 루프 (메인 엔트리): [scripts/run_locomotion.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/scripts/run_locomotion.py)
- BHL Python 로봇 클래스: [berkeley_humanoid_lite_lowlevel/robot/humanoid.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py)
- BHL WitMotion 드라이버: [berkeley_humanoid_lite_lowlevel/robot/imu.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/robot/imu.py)
- BHL 정책 컨트롤러 (ONNX 추론): [berkeley_humanoid_lite_lowlevel/policy/rl_controller.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/rl_controller.py)
- 조이스틱 (교체 대상): [berkeley_humanoid_lite_lowlevel/policy/gamepad.py](../bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/gamepad.py)
- Hylion bridge (Coordinator → UDP): [nuc/bhl/bridge.py](../bhl/bridge.py)
- WitMotion 원본 파서 (참고용): [1. Tutorials/Program Files /3.Raspberry Pi-USB Application Program/imu_usb/imu_usb/imu_usb.py](1.%20Tutorials/Program%20Files%20/3.Raspberry%20Pi-USB%20Application%20Program/imu_usb/imu_usb/imu_usb.py)
- 정책 obs 흐름 문서: [../../docs/11_bhl_reference_flow.md](../../docs/11_bhl_reference_flow.md)
- 사용자 매뉴얼(우리 IMU): [1. Tutorials/1. User Manual.pdf](1.%20Tutorials/1.%20User%20Manual.pdf)
