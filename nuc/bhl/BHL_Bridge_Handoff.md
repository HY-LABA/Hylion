# BHL Bridge 구현 인수인계 문서

> **이 문서의 목적**: 이 파일만으로 다른 AI 어시스턴트가 Berkeley Humanoid Lite(BHL)와 Jetson coordinator를 연결하는 브리지 코드를 처음부터 끝까지 구현할 수 있도록, 필요한 모든 컨텍스트·사양·결정사항·미해결 질문을 정리한 인수인계 문서.

---

## 0. AI 어시스턴트를 위한 프롬프트 (먼저 읽어주세요)

```
당신은 로보틱스 프로젝트의 통신 브리지 코드를 작성하는 AI 어시스턴트입니다.

[프로젝트 개요]
- 사용자는 Berkeley Humanoid Lite (BHL)이라는 오픈소스 휴머노이드 로봇을 운용 중
- 시스템 구성: Jetson Orin Nano Super Dev Kit (coordinator) + Intel NUC (BHL lowlevel)
- 두 컴퓨터는 이더넷으로 직접 연결됨
- BHL의 기존 제어 입력은 게임패드(USB)이지만, 사용자는 게임패드 대신
  Jetson의 coordinator가 출력하는 JSON 명령으로 로봇을 제어하고자 함

[당신의 작업]
1. 이 문서의 모든 섹션을 정독하여 시스템 아키텍처와 통신 사양을 완전히 이해할 것
2. 섹션 11의 "미해결 사항"을 사용자에게 먼저 확인할 것 (필수)
3. 섹션 12의 체크리스트에 따라 `bridge.py` 파이썬 스크립트를 작성할 것
4. 섹션 13의 테스트 방법으로 검증 가능한 코드를 제공할 것

[중요 원칙]
- BHL의 UDP 패킷 포맷은 정확히 13바이트, little-endian, "<Bfff" 구조로 깨지면 안 됨
- 안전이 최우선: safety_allowed=false 또는 EMERGENCY 상태 시 즉시 stop 명령 전송
- Watchdog 필수: coordinator로부터 일정 시간 메시지가 없으면 자동 stop
- BHL의 C 컨트롤러 코드는 절대 수정하지 않음 (브리지가 100% 호환되어야 함)

[작업 시 추측 금지 사항]
다음 값들은 추측하지 말고 반드시 사용자에게 물어볼 것:
- walk_forward, turn_left의 정확한 속도값 (vx, vyaw)
- TCP 서버 포트 번호
- watchdog timeout 값
- heartbeat 주기
- IMU telemetry 채널 설계 (별도 채널인지, 같은 채널의 다른 메시지 타입인지)
```

---

## 1. 프로젝트 컨텍스트

### 1.1 무엇을 하려는가
- 사용자 프로젝트 이름: HYlion (코드네임)
- 목표: Jetson Orin Nano에서 실행되는 coordinator 프로그램이 음성/터미널 입력을 받아 JSON 형태로 행동 결정을 내림. 이 JSON을 BHL 로봇이 받아 실제 보행/조작을 수행
- 현재 BHL은 게임패드(XInput 표준 호환 컨트롤러) 입력만 받도록 코드가 짜여 있음
- 게임패드를 JSON 입력 채널로 대체하는 브리지 코드가 필요

### 1.2 하드웨어 구성
| 장비 | 역할 | OS/스택 |
|---|---|---|
| Jetson Orin Nano Super Dev Kit | Coordinator (HYlion) | Ubuntu, Python |
| Intel NUC (BHL onboard) | Robot lowlevel control | Ubuntu, Python + C++ |
| Berkeley Humanoid Lite | 로봇 본체 | 12-DoF biped (현재 빌드 기준) |
| 이더넷 케이블 | Jetson ↔ NUC 직결 | Cat 5e 이상 |

### 1.3 네트워크 가정
- 직결 또는 작은 스위치 경유
- 권장 IP: Jetson `192.168.10.1/24`, NUC `192.168.10.2/24` (사용자가 변경 가능)
- 같은 서브넷에서 `ping`이 동작해야 함

---

## 2. BHL Lowlevel 시스템 구조

### 2.1 진짜 중요한 사실: 3-프로세스 구조

BHL의 lowlevel은 단일 프로그램이 아니라 **3개의 독립 프로세스가 UDP로 통신하는 분산 시스템**임. 게임패드 입력은 그 중 하나의 입력 채널에 불과함.

```
┌──────────────────┐    UDP 10011    ┌─────────────────────┐
│  gamepad.py      │ ───────────────→│                     │
│  (또는 bridge.py) │  13 bytes        │                     │
│  사용자 명령 입력  │  (mode + vels)  │                     │
└──────────────────┘                 │   C 메인 컨트롤러     │
                                     │   (csrc/, real_      │
┌──────────────────┐    UDP 10001    │    humanoid.cpp)    │
│  rl_controller.py │ ───────────────→│                     │
│  ONNX 정책 추론    │  N_LOWLEVEL_   │   250 Hz control    │
│  (별도 프로세스)   │  COMMANDS=12   │   500 Hz UDP/IMU    │
│                  │←──────────────  │   2 CAN buses       │
│                  │    UDP 10000    │                     │
│                  │  N_LOWLEVEL_    │                     │
│                  │  STATES=35      │                     │
└──────────────────┘                 └─────────┬───────────┘
                                               │ CAN @1Mbps
                                               ▼
                                         12개 actuator
                                       (B-G431B-ESC1 + BLDC)
```

### 2.2 각 프로세스 역할

**프로세스 A: 입력 (gamepad.py 또는 bridge.py)**
- 사용자 명령(속도 + 모드 전환)을 UDP로 송신
- 송신 주기: 20 Hz (control loop이 받는 측에서 그 주기로 polling)
- **이 문서의 작업 대상이 바로 이 프로세스를 새로 만드는 것**

**프로세스 B: 정책 추론 (rl_controller.py)**
- C에서 observation을 UDP로 받음
- ONNX 또는 PyTorch로 forward
- action(12개 float, 각 joint의 desired position)을 UDP로 C에 돌려줌
- **이 프로세스는 이미 존재. 수정 불필요**

**프로세스 C: C 메인 컨트롤러 (csrc/)**
- 250 Hz로 CAN 통신, IMU 읽기, FSM 관리
- A에서 받은 명령을 정책에 전달
- B에서 받은 action을 actuator로 전달
- **이 프로세스도 수정 절대 금지** (브리지는 이걸 그대로 받아주는 호환 인터페이스를 제공해야 함)

### 2.3 데이터 주기
| 채널 | 주파수 | 비고 |
|---|---|---|
| Control loop (C) | 250 Hz | `0.004s` (consts.h) |
| UDP receive (C) | 500 Hz | action 수신 |
| IMU loop (C) | 500 Hz | BNO085 시리얼 |
| Joystick loop (C) | 20 Hz | 새 명령 polling |
| Keyboard loop (C) | 20 Hz | 'r','t','q' 키 |
| Policy inference (rl_controller.py) | ~50 Hz | 실제 정책 주기 |

---

## 3. UDP 패킷 사양 (구현의 핵심)

### 3.1 Joystick 채널 (브리지가 송신해야 할 채널)

**포트**: `10011` (consts.h의 `JOYSTICK_PORT`)

**C 측 수신 코드** (`real_humanoid.cpp` 발췌):
```c
// 초기화
initialize_udp(&udp_joystick, "0.0.0.0", JOYSTICK_PORT, "127.0.0.1", JOYSTICK_PORT);
// → recv bind: 0.0.0.0:10011 (외부 IP에서도 수신 가능)

// 수신 루프 (20 Hz)
size_t expected_bytes = 13;
uint8_t udp_buffer[13];
recvfrom(udp_joystick.sockfd, udp_buffer, 13, MSG_WAITALL, NULL, NULL);

uint8_t command_mode         = udp_buffer[0];
stick_command_velocity_x_    = *(float *)(udp_buffer + 1);
stick_command_velocity_y_    = *(float *)(udp_buffer + 5);
stick_command_velocity_yaw_  = *(float *)(udp_buffer + 9);
```

**정확한 패킷 구조 (총 13바이트, little-endian)**:

| 오프셋 | 크기 | 타입 | 필드 | 의미 |
|---|---|---|---|---|
| 0 | 1 | `uint8_t` | `command_mode` | 모드 전환 신호 (0=변화없음, 1=IDLE, 2=RL_INIT, 3=RL_RUNNING) |
| 1 | 4 | `float32 LE` | `velocity_x` | 전후 속도 (m/s), 양수=전진 |
| 5 | 4 | `float32 LE` | `velocity_y` | 좌우 속도 (m/s), 양수=왼쪽 추정 (검증 필요) |
| 9 | 4 | `float32 LE` | `velocity_yaw` | 회전 속도 (rad/s), 양수=좌회전 추정 (검증 필요) |

**Python struct 포맷**:
```python
import struct
packet = struct.pack("<Bfff", command_mode, vx, vy, vyaw)
# 항상 정확히 13바이트
assert len(packet) == 13
```

**송신 목적지**:
- 옵션 A (브리지를 NUC에서 실행): `127.0.0.1:10011`
- 옵션 B (브리지를 Jetson에서 실행): `<NUC_IP>:10011` — C가 `0.0.0.0`에 bind되어 있어 외부 IP도 받음

### 3.2 다른 채널 (참고용 — 브리지가 직접 다루지는 않음)

**Observation 채널** (port 10000, C → rl_controller.py):
- 크기: `N_LOWLEVEL_STATES = 4+3+12+12+1+3 = 35` floats = 140 bytes
- 내용: base_quat[4] + base_ang_vel[3] + joint_pos[12] + joint_vel[12] + state[1] + cmd_vel[3]
- 주기: 정책 dt마다 (약 50 Hz)

**Action 채널** (port 10001, rl_controller.py → C):
- 크기: `N_LOWLEVEL_COMMANDS = 12` floats = 48 bytes
- 내용: 각 joint의 desired position (12개)

**Visualize 채널** (port 10002): 시각화용 tap. 브리지 관련 없음.

### 3.3 BHL의 IP/주소 기본값 (consts.h)
```c
#define HOST_IP_ADDR    "127.0.0.1"
#define ROBOT_IP_ADDR   "127.0.0.1"
#define POLICY_OBS_PORT 10000
#define POLICY_ACS_PORT 10001
#define VISUALIZE_PORT  10002
#define JOYSTICK_PORT   10011
```

모든 IP가 localhost로 하드코딩되어 있음. 단, `udp_joystick`은 `0.0.0.0`에 bind되어 외부에서 수신 가능.

---

## 4. FSM 상태와 모드 전환

### 4.1 C 컨트롤러의 상태 (real_humanoid.h)
```c
enum ControllerState {
  STATE_ERROR = 0,
  STATE_IDLE = 1,        // 현재 joint position 그대로 유지
  STATE_RL_INIT = 2,     // default pose로 1초간 linear 이동
  STATE_RL_RUNNING = 3,  // 정책이 보내는 명령 따름
  STATE_GETUP = 4,       // 정의는 있으나 control_loop에서 미사용
  STATE_HOLD = 5,
  STATE_GETDOWN = 6,
};
```

### 4.2 브리지가 알아야 할 모드 매핑

`command_mode` 바이트는 `next_state`를 설정하는 데 사용됨 (real_humanoid.cpp):
```c
switch (command_mode) {
  case 1: next_state = STATE_IDLE;        break;  // 정지/대기
  case 2: next_state = STATE_RL_INIT;     break;  // RL init pose로 이동
  case 3: next_state = STATE_RL_RUNNING;  break;  // 보행 시작
  default: next_state = STATE_IDLE;
}
// command_mode = 0이면 if 진입 안 함 → 상태 변화 없음
```

### 4.3 정상 작동 시퀀스 (cold start)
브리지가 부팅 후 처음 로봇을 움직이려면 이 순서를 따라야 함:

```
1. C 컨트롤러 시작 → 자동으로 STATE_IDLE 진입
2. 브리지가 command_mode=2 송신 → STATE_RL_INIT 전환
3. 약 1초 대기 (init_percentage가 1.0에 도달할 때까지)
4. 브리지가 command_mode=3 송신 → STATE_RL_RUNNING 전환
5. 이후 velocity 명령 송신 가능
```

**중요**: 매 패킷마다 command_mode를 채울 필요 없음. 한 번 모드 전환 후엔 `command_mode=0`으로 유지하고 velocity만 갱신하면 됨.

### 4.4 정지 시퀀스
- `command_mode=1` 송신 → STATE_IDLE 복귀
- C가 자동으로 actuator를 DAMPING 모드로 전환

---

## 5. Coordinator의 JSON 입력 스키마

Coordinator가 출력하는 JSON의 정식 스키마 (`action.schema.json` 기준):

```json
{
  "action_id": "string",
  "timestamp": "string",
  "session_id": "string",
  "schema_version": "string",
  "source": "terminal | mic | stt",
  "network_online": true,
  "intent": "chat | pick_place | move | stop | standby | unknown",
  "target_object": "string",
  "reply_text": "string",
  "requires_smolvla": false,
  "requires_bhl": false,
  "gait_cmd": "walk_forward | turn_left | stop | none",
  "state_current": "IDLE | TALKING | MANIPULATING | WALKING | EMERGENCY",
  "safety_allowed": true,
  "fallback_policy": "string"
}
```

### 5.1 브리지가 직접 사용할 필드 (★ 핵심)
| 필드 | 타입 | 용도 |
|---|---|---|
| `gait_cmd` | enum | 보행 명령 → velocity 패킷의 vx/vy/vyaw 결정 |
| `requires_bhl` | bool | false면 BHL 비활성화 (패킷 안 보내거나 stop) |
| `state_current` | enum | EMERGENCY면 즉시 stop |
| `safety_allowed` | bool | false면 즉시 stop |
| `intent` | enum | `stop`인 경우 추가 검증 |

### 5.2 브리지가 무시할 필드
`reply_text`, `target_object`, `requires_smolvla`, `network_online`, `source`, `session_id`, `fallback_policy`, `schema_version`, `action_id`, `timestamp` 등 — 단, **로깅 시 `action_id`, `timestamp`는 trace용으로 기록 권장**.

---

## 6. JSON → UDP 매핑 로직

### 6.1 결정 우선순위 (위→아래로 체크)
```
1. safety_allowed == false       → STOP 패킷 (강제 정지)
2. state_current == "EMERGENCY"  → STOP 패킷 (강제 정지)
3. requires_bhl == false         → 패킷 미송신 OR STOP 패킷
4. intent == "stop"              → STOP 패킷
5. gait_cmd 값에 따라 매핑        → 정상 명령 패킷
```

### 6.2 gait_cmd → velocity 매핑 테이블 (값은 ★확인 필요★)
| gait_cmd | command_mode | velocity_x | velocity_y | velocity_yaw |
|---|---|---|---|---|
| `"walk_forward"` | 0 또는 3 | 0.3 (예시) | 0.0 | 0.0 |
| `"turn_left"` | 0 또는 3 | 0.0 | 0.0 | 0.5 (예시) |
| `"stop"` | 1 (IDLE) | 0.0 | 0.0 | 0.0 |
| `"none"` | 0 (변화없음) | 0.0 | 0.0 | 0.0 |

**경고**: 위의 0.3, 0.5 수치는 **추측값**임. 실제 BHL이 학습된 명령 범위 안에 있어야 정책이 정상 작동함. 일반적으로 휴머노이드 RL policy는 `vx ∈ [-0.5, 1.0] m/s`, `vyaw ∈ [-1.0, 1.0] rad/s` 정도 범위에서 학습되지만 BHL의 정확한 학습 범위는 코드 확인 필요 (`policy_latest.yaml` 또는 학습 config 참조).

### 6.3 STOP 패킷 정의
```python
STOP_PACKET = struct.pack("<Bfff", 1, 0.0, 0.0, 0.0)
# command_mode=1 (IDLE), 모든 속도 0
```

### 6.4 모드 전환 처리
- 첫 부팅 시: 브리지는 cold start sequence 실행 (섹션 4.3)
- 정상 운용 중: `gait_cmd`가 `"stop"`이 아닌 한 `command_mode=0`으로 보냄
- 비상 시 또는 stop: `command_mode=1` 보냄
- RL_INIT(2)와 RL_RUNNING(3)은 startup/recovery 외에는 거의 송신할 필요 없음

---

## 7. Coordinator ↔ Bridge 통신 프로토콜

### 7.1 결정 사항
- **프로토콜**: TCP (사용자가 선택)
- **포맷**: NDJSON (newline-delimited JSON, 한 줄에 JSON 객체 하나)
- **방향**: Coordinator → Bridge (단방향이 주, 단 heartbeat 응답이나 telemetry 필요 시 양방향 확장)
- **포트**: ★ 사용자 확인 필요 (제안: 9000)

### 7.2 메시지 포맷 예시
```
{"action_id":"a1","timestamp":"2026-05-11T10:00:00Z","gait_cmd":"walk_forward","intent":"move","state_current":"WALKING","safety_allowed":true,"requires_bhl":true,...}\n
{"action_id":"a2","timestamp":"2026-05-11T10:00:00.1Z","gait_cmd":"stop","intent":"stop","state_current":"IDLE","safety_allowed":true,"requires_bhl":false,...}\n
```

### 7.3 연결 관리
- TCP 연결이 끊기면 브리지는 즉시 STOP 패킷을 BHL로 송신해야 함 (안전 기본값)
- 재연결 시 cold start sequence 다시 실행
- Coordinator의 명령 주기는 ~10 Hz로 가정 (확정 필요)

---

## 8. 브리지 아키텍처

### 8.1 권장 구조: 브리지를 NUC에서 실행 (옵션 A)

```
┌─────────────────────┐                    ┌──────────────────────────────────┐
│   Jetson Orin Nano  │                    │           Intel NUC               │
│                     │                    │                                   │
│  ┌──────────────┐   │  TCP/NDJSON        │  ┌──────────────┐                 │
│  │ coordinator  │   │  (port 9000)       │  │  bridge.py   │  UDP            │
│  │              │ ──┼────────────────────┼─→│              │ ──→ 127.0.0.1   │
│  │ JSON 출력    │   │                    │  │  - TCP recv  │      :10011     │
│  └──────────────┘   │                    │  │  - JSON 파싱  │     (13 bytes) │
│                     │                    │  │  - 매핑      │                  │
└─────────────────────┘                    │  │  - UDP send  │                 │
                                           │  │  - watchdog  │                 │
                                           │  └──────────────┘                 │
                                           │                       ↓           │
                                           │              ┌─────────────────┐  │
                                           │              │ C 컨트롤러       │  │
                                           │              │ (real_humanoid) │  │
                                           │              └─────────────────┘  │
                                           └──────────────────────────────────┘
```

**선택 이유**:
- 관심사 분리: coordinator는 JSON만, bridge가 BHL 포맷을 책임
- BHL 코드 수정 0줄 (`127.0.0.1` 그대로 사용)
- 디버깅 쉬움 (NUC에서 bridge 로그만 보면 됨)

### 8.2 옵션 B (참고): 브리지를 Jetson에서 실행
- Jetson에서 직접 `<NUC_IP>:10011`로 UDP 송신
- 가능하지만 권장하지 않음 (coordinator가 BHL UDP 포맷에 결합됨)

### 8.3 브리지 내부 스레드/태스크 구성 (제안)
```
- Thread 1: TCP server (accept + recv NDJSON)
  → 파싱된 명령을 내부 큐에 enqueue + last_command_time 갱신
- Thread 2: UDP sender (20 Hz)
  → 큐에서 최신 명령 꺼내 13-byte UDP 송신
  → 큐 비어있으면 마지막 명령 재송신
- Thread 3: Watchdog (10 Hz)
  → now - last_command_time > timeout이면 STOP_PACKET 강제 송신
- Main: 시그널 처리, graceful shutdown
```

비동기로 구현하고 싶다면 `asyncio`로 같은 구조 가능.

---

## 9. 안전 고려사항

### 9.1 다층 안전 (3-layer)
```
Layer 1: 물리 E-stop (배터리/relay) — 이 작업 범위 밖
Layer 2: Watchdog (브리지 + C 컨트롤러)
Layer 3: 소프트웨어 emergency 감지 (coordinator의 IMU 모니터)
```

### 9.2 브리지의 안전 책임
- **Watchdog 필수**: coordinator에서 일정 시간(예: 200ms) 메시지 없으면 자동 STOP
- **TCP 연결 끊김 = 즉시 STOP**: 명시적 종료가 아니어도
- **safety_allowed=false 즉시 처리**: 큐잉 없이 우선 송신
- **EMERGENCY 상태 우선**: gait_cmd가 뭐든 무시하고 STOP
- **부팅 직후 STOP 상태 유지**: cold start sequence 끝나기 전엔 절대 임의 명령 송신 금지

### 9.3 watchdog timeout 권장값
- 너무 짧으면: false positive 잦음 (네트워크 지터)
- 너무 길면: 위험 노출 시간 증가
- 제안: 200ms (사용자 확인 필요)

### 9.4 향후 추가 예정 (사용자가 계획 중)
- Coordinator가 BHL의 IMU 데이터를 받아 모니터링
- pitch/roll이 임계값 초과 시 `state_current=EMERGENCY`로 자동 전환
- 즉 IMU telemetry 채널이 별도로 필요 — **이 부분은 미해결, 섹션 11 참조**

---

## 10. 로깅과 디버깅

### 10.1 권장 로깅 항목
- 모든 수신 JSON (timestamp, action_id 포함)
- 모든 송신 UDP 패킷 (binary는 hex로)
- 모드 전환 이벤트
- Watchdog 발동
- TCP 연결/해제
- 에러 (파싱 실패, UDP 송신 실패 등)

### 10.2 로그 포맷 제안
```
2026-05-11T10:00:00.123 INFO [bridge] TCP connection from 192.168.10.1:54321
2026-05-11T10:00:00.234 RECV  {"action_id":"a1","gait_cmd":"walk_forward",...}
2026-05-11T10:00:00.235 SEND  mode=0 vx=0.30 vy=0.00 vyaw=0.00 (hex: 00 9a99...)
2026-05-11T10:00:01.000 WARN  [watchdog] no message for 250ms, sending STOP
```

---

## 11. 미해결 사항 / 사용자에게 확인할 질문

브리지 코드 작성 전에 반드시 사용자에게 물어볼 것:

### 11.1 매핑 파라미터
- [ ] `walk_forward` 시 정확한 `velocity_x` 값 (BHL 학습 범위 안)
- [ ] `turn_left` 시 정확한 `velocity_yaw` 값
- [ ] BHL의 RL policy가 학습된 명령 범위 (vx, vy, vyaw의 min/max)
- [ ] `velocity_y`의 방향 (왼쪽이 양수인지 음수인지)
- [ ] `velocity_yaw`의 방향 (좌회전이 양수인지)

### 11.2 통신 설정
- [ ] TCP 서버 포트 번호 (제안: 9000)
- [ ] 브리지가 listen할 IP (`0.0.0.0` vs `192.168.10.2` 특정)
- [ ] Coordinator의 명령 주기 (10 Hz? 더 빠름? 비주기적?)
- [ ] NDJSON 외 다른 포맷 선호 여부 (예: MessagePack, protobuf)

### 11.3 Watchdog/안전
- [ ] Watchdog timeout 정확한 값 (제안: 200ms)
- [ ] 부팅 시 자동 cold start 할지, 사용자가 명시 명령 줘야 시작할지
- [ ] TCP 끊김 시 동작 (STOP 후 재연결 기다리기 vs 프로세스 종료)

### 11.4 IMU/Telemetry (향후 확장)
- [ ] IMU 데이터를 Jetson coordinator로 보낼 것인지
- [ ] 보낸다면 어떤 채널로? (TCP 같은 채널 양방향? 별도 채널? UDP?)
- [ ] 주기? (현재 C는 50Hz로 visualize port에 송신 중)
- [ ] 어떤 데이터? (quaternion만? joint state까지?)

### 11.5 운용
- [ ] 브리지를 systemd 서비스로 실행할지, 수동 실행할지
- [ ] 로그 출력 위치 (stdout? 파일? journald?)
- [ ] 실패 시 자동 재시작 여부

---

## 12. 구현 체크리스트

브리지 코드(`bridge.py`)가 충족해야 할 항목:

### 핵심 기능
- [ ] TCP 서버 (지정 포트 listen, 1개 클라이언트 연결만 받아도 됨)
- [ ] NDJSON 파싱 (한 줄씩 분리, JSON 객체로 파싱)
- [ ] 스키마 검증 (`requires_bhl`, `safety_allowed`, `state_current`, `gait_cmd` 필드 존재 확인)
- [ ] JSON → 13-byte UDP 매핑 (섹션 6 로직)
- [ ] `struct.pack("<Bfff", ...)`로 정확한 바이트 생성
- [ ] UDP socket 송신 (`127.0.0.1:10011` 또는 설정값)
- [ ] 매 송신 주기 20 Hz 보장 (C가 그 주기로 polling함)

### 안전
- [ ] Watchdog timer (timeout 시 STOP 패킷 송신)
- [ ] TCP 연결 끊김 감지 → 즉시 STOP
- [ ] `safety_allowed=false` 즉시 처리
- [ ] `state_current=EMERGENCY` 즉시 처리
- [ ] 부팅 시 STOP 상태로 시작

### Cold start
- [ ] 첫 메시지 수신 시 IDLE → RL_INIT → RL_RUNNING 자동 시퀀스
- [ ] 또는 사용자가 명시 명령 줄 때만 시작 (선택)
- [ ] RL_INIT 진입 후 1.5초 대기 (init_percentage 1.0 도달 보장)

### 로깅
- [ ] 모든 RX/TX 로그
- [ ] 모드 전환 로그
- [ ] 에러 로그 (stderr 또는 별도 파일)

### 강건성
- [ ] JSON 파싱 실패해도 프로세스 죽지 않음 (이전 명령 유지 또는 STOP)
- [ ] UDP 송신 실패해도 다음 사이클에 재시도
- [ ] SIGINT/SIGTERM 시 graceful shutdown (STOP 송신 후 종료)

### 설정 가능
- [ ] TCP 포트, UDP 대상 IP/포트, watchdog timeout 등이 CLI 인자 또는 config 파일로 변경 가능
- [ ] 매핑 테이블(gait_cmd → velocity)이 config에 분리되면 더 좋음

---

## 13. 테스트 방법

### 13.1 단위 테스트 (브리지 단독)

**Mock coordinator 클라이언트** (실제 Jetson 없이):
```python
import socket, json, time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 9000))
cmd = {
    "action_id": "test1",
    "timestamp": "2026-01-01T00:00:00Z",
    "session_id": "s1",
    "schema_version": "1.0",
    "source": "terminal",
    "network_online": True,
    "intent": "move",
    "target_object": "",
    "reply_text": "go",
    "requires_smolvla": False,
    "requires_bhl": True,
    "gait_cmd": "walk_forward",
    "state_current": "WALKING",
    "safety_allowed": True,
    "fallback_policy": ""
}
s.sendall((json.dumps(cmd) + "\n").encode())
time.sleep(2)
```

**Mock BHL UDP receiver** (실제 C 컨트롤러 없이):
```python
import socket, struct
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", 10011))
while True:
    data, addr = s.recvfrom(13)
    assert len(data) == 13
    mode, vx, vy, vyaw = struct.unpack("<Bfff", data)
    print(f"mode={mode} vx={vx:.3f} vy={vy:.3f} vyaw={vyaw:.3f}")
```

### 13.2 통합 테스트 (브리지 + 실제 C 컨트롤러)
```bash
# 터미널 1: C 컨트롤러 실행 (BHL NUC에서)
cd Berkeley-Humanoid-Lite-Lowlevel
make run

# 터미널 2: rl_controller.py 실행 (별도 프로세스)
python -m berkeley_humanoid_lite_lowlevel.policy.rl_controller

# 터미널 3: 브리지 실행
python bridge.py --tcp-port 9000 --udp-port 10011

# 터미널 4: mock coordinator로 명령 송신
python tests/mock_coordinator.py
```

### 13.3 검증 시나리오
1. **Cold start**: 브리지 시작 → 첫 명령 받으면 RL_INIT → RL_RUNNING 진입 확인
2. **정상 보행**: `walk_forward` 송신 → C 컨트롤러가 vx에 반응 확인
3. **회전**: `turn_left` 송신 → vyaw 반응 확인
4. **정상 정지**: `stop` 송신 → IDLE 진입 확인
5. **Safety stop**: `safety_allowed=false` 송신 → 즉시 STOP 확인
6. **Emergency**: `state_current=EMERGENCY` 송신 → 즉시 STOP 확인
7. **Watchdog**: 명령 송신 중단 → 200ms 후 자동 STOP 확인
8. **TCP 끊김**: coordinator 프로세스 kill → 브리지가 STOP 송신 확인
9. **잘못된 JSON**: 깨진 JSON 송신 → 브리지 죽지 않고 STOP 송신 확인
10. **재연결**: TCP 끊김 후 재연결 → cold start sequence 다시 실행 확인

---

## 14. 참고 자료 (원본 코드 위치)

### 14.1 BHL 코드 (이 문서 작성 시점)
- 메인 레포: `https://github.com/HybridRobotics/Berkeley-Humanoid-Lite`
- Lowlevel 서브모듈: `https://github.com/HybridRobotics/Berkeley-Humanoid-Lite-Lowlevel`
- 핵심 파일:
  - `csrc/consts.h` — 포트 번호, IP 주소
  - `csrc/real_humanoid.h` — FSM enum, 상태 정의
  - `csrc/real_humanoid.cpp` — 메인 컨트롤러, joystick_loop 함수 (UDP 수신 코드)
  - `csrc/udp.c`, `csrc/udp.h` — UDP wrapper
  - `berkeley_humanoid_lite_lowlevel/policy/gamepad.py` — 게임패드 입력 (UDP 직접 송신 안 함, 별도 통합 필요)
  - `berkeley_humanoid_lite_lowlevel/policy/rl_controller.py` — 정책 추론 프로세스
  - `berkeley_humanoid_lite_lowlevel/policy/config.py` — 정책 설정

### 14.2 BHL 논문
- arXiv 2504.17249 — "Demonstrating Berkeley Humanoid Lite"
- 핵심 사실: zero-shot sim-to-real, 25 Hz 정책 (실제 코드는 50Hz), 12-DoF biped 모드 사용 중

### 14.3 BHL 공식 문서
- `https://berkeley-humanoid-lite.gitbook.io/docs/`
- **주의**: GitBook 문서가 실제 코드와 다른 부분 있음 (예: `udp_joystick.py`는 존재하지 않고 `gamepad.py`임. Isaac Sim 버전도 다름)

### 14.4 관련 라이브러리
- `inputs` (게임패드 읽기, Python) — 브리지는 사용 안 함
- `onnxruntime`, `torch` — rl_controller.py에서 사용
- `omegaconf` — 정책 설정 파싱

---

## 15. 흔한 함정 (브리지 작성 시 주의)

### 15.1 절대 하면 안 되는 것
- **C 컨트롤러 코드 수정**: 브리지는 100% 호환 인터페이스만 제공
- **패킷 크기 변경**: 13바이트 정확히 (덧붙이거나 줄이면 C가 `MSG_WAITALL`로 막힘)
- **endianness 가정**: 반드시 little-endian (`<` prefix), x86은 기본이지만 명시
- **연결 끊긴 채로 로봇 활성 상태 유지**: 사람이 못 멈춰서 사고남

### 15.2 흔한 실수
- `struct.pack("Bfff", ...)`로 prefix 빼먹기 → 패딩 들어가서 13바이트가 아님 (반드시 `"<Bfff"`)
- 모드 전환 후 즉시 velocity 명령 송신 → RL_INIT 진행 중이라 무시됨, 1초 대기 필요
- watchdog만 있고 TCP 끊김 감지 없음 → TCP 끊겨도 마지막 명령으로 계속 걸어감
- exception 처리 안 해서 한 번 JSON 파싱 실패하면 프로세스 죽음

### 15.3 검증 우선순위
1. 가장 먼저: STOP 패킷이 정확히 동작하는지 (안전 기본값)
2. 그 다음: cold start sequence
3. 마지막: 정상 보행

---

## 16. 코드 스켈레톤 (참고용 — 구현 시 자유롭게 수정)

```python
#!/usr/bin/env python3
"""bridge.py - Jetson coordinator JSON → BHL UDP 변환"""

import socket
import struct
import json
import threading
import time
import logging
import signal
import sys

# === 설정 (config 파일이나 CLI 인자로 분리 권장) ===
TCP_PORT = 9000
UDP_TARGET = ("127.0.0.1", 10011)
WATCHDOG_TIMEOUT = 0.2  # 200ms
SEND_RATE = 20.0  # Hz

# 매핑 (★사용자 확인 필요★)
VEL_FORWARD = 0.3
VEL_YAW = 0.5

STOP_PACKET = struct.pack("<Bfff", 1, 0.0, 0.0, 0.0)
NEUTRAL_PACKET = struct.pack("<Bfff", 0, 0.0, 0.0, 0.0)

class Bridge:
    def __init__(self):
        self.last_cmd_time = 0
        self.current_packet = STOP_PACKET
        self.running = True
        self.lock = threading.Lock()
        self.cold_start_done = False
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def map_json_to_packet(self, msg: dict) -> bytes:
        # 우선순위 1: 안전 게이트
        if not msg.get("safety_allowed", False):
            return STOP_PACKET
        if msg.get("state_current") == "EMERGENCY":
            return STOP_PACKET
        if not msg.get("requires_bhl", False):
            return STOP_PACKET
        if msg.get("intent") == "stop":
            return STOP_PACKET

        gait = msg.get("gait_cmd", "none")
        if gait == "walk_forward":
            return struct.pack("<Bfff", 0, VEL_FORWARD, 0.0, 0.0)
        elif gait == "turn_left":
            return struct.pack("<Bfff", 0, 0.0, 0.0, VEL_YAW)
        elif gait == "stop":
            return STOP_PACKET
        else:  # "none" 또는 기타
            return NEUTRAL_PACKET

    def cold_start(self):
        """IDLE → RL_INIT → RL_RUNNING"""
        logging.info("Cold start: RL_INIT")
        self.udp_sock.sendto(struct.pack("<Bfff", 2, 0.0, 0.0, 0.0), UDP_TARGET)
        time.sleep(1.5)
        logging.info("Cold start: RL_RUNNING")
        self.udp_sock.sendto(struct.pack("<Bfff", 3, 0.0, 0.0, 0.0), UDP_TARGET)
        time.sleep(0.1)
        self.cold_start_done = True

    def tcp_server_loop(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", TCP_PORT))
        srv.listen(1)
        logging.info(f"TCP listening on {TCP_PORT}")
        while self.running:
            try:
                conn, addr = srv.accept()
                logging.info(f"Connected from {addr}")
                self.handle_client(conn)
            except Exception as e:
                logging.error(f"TCP error: {e}")
            with self.lock:
                self.current_packet = STOP_PACKET  # 연결 끊기면 STOP
            logging.warning("Client disconnected → STOP")

    def handle_client(self, conn):
        buf = b""
        while self.running:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(line.decode())
                    if not self.cold_start_done:
                        self.cold_start()
                    packet = self.map_json_to_packet(msg)
                    with self.lock:
                        self.current_packet = packet
                        self.last_cmd_time = time.time()
                    logging.info(f"RX {msg.get('action_id')}: gait={msg.get('gait_cmd')}")
                except Exception as e:
                    logging.error(f"Parse error: {e}")
        conn.close()

    def udp_sender_loop(self):
        period = 1.0 / SEND_RATE
        while self.running:
            with self.lock:
                packet = self.current_packet
                last = self.last_cmd_time
            # Watchdog
            if self.cold_start_done and time.time() - last > WATCHDOG_TIMEOUT:
                packet = STOP_PACKET
            self.udp_sock.sendto(packet, UDP_TARGET)
            time.sleep(period)

    def shutdown(self, *args):
        logging.info("Shutdown: sending STOP")
        self.udp_sock.sendto(STOP_PACKET, UDP_TARGET)
        self.running = False
        time.sleep(0.1)
        sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    bridge = Bridge()
    signal.signal(signal.SIGINT, bridge.shutdown)
    signal.signal(signal.SIGTERM, bridge.shutdown)
    threading.Thread(target=bridge.tcp_server_loop, daemon=True).start()
    bridge.udp_sender_loop()
```

**주의**: 위 스켈레톤은 시작점일 뿐. 다음 항목은 반드시 보강해야 함:
- 매핑 상수값 (사용자 확인)
- 에러 처리 강화
- 로깅 더 자세히
- TCP 재연결 후 cold start 재실행
- IMU telemetry 채널 (확장 시)
- 단위 테스트

---

## 17. 끝 / 요약

이 문서를 읽은 AI가 해야 할 일:
1. **섹션 11의 모든 미해결 질문을 사용자에게 먼저 물어볼 것**
2. 답을 받은 후, 섹션 12의 체크리스트에 따라 `bridge.py` 작성
3. 섹션 13의 테스트 방법으로 검증
4. 섹션 15의 함정 피하기

가장 중요한 단 하나: **13바이트 little-endian `<Bfff` 패킷이 `127.0.0.1:10011`로 정확히 송신되어야 한다. 이게 깨지면 모든 것이 무용지물.**

