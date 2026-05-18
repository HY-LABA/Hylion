# 2단계 — Jetson coordinator와 NUC bridge 연결 가이드

> 비전공자도 이해할 수 있게 풀어 쓴 작업 설명서.
> 코드 작성 전에 "무엇을, 왜, 어떻게" 결정하기 위한 문서.

---

## 0. 한 줄 요약

**한 번에 한 가지만 한다 (턴제). "앞으로 가" → 음성 응답 → 다리 N초 걷기 → 다리가 끝났다고 알림 → "도착했습니다" → 다음 명령 대기.**

---

## 1. 용어부터 정리

| 단어 | 비전공자용 풀이 | 이 프로젝트에서 |
|---|---|---|
| **Jetson** | 작은 컴퓨터 (손바닥만함). AI 두뇌 | 사용자 목소리 듣고 "어떻게 행동할지" 결정 |
| **NUC** | 작은 PC | 로봇 다리에 붙어서 실제 모터를 돌리는 컴퓨터 |
| **BHL** | Berkeley Humanoid Lite. 오픈소스 휴머노이드 | 우리가 쓰는 다리 로봇 본체 |
| **coordinator.py** | "지휘자". 사용자 말 → 행동 결정 | Jetson에서 도는 메인 프로그램 |
| **bridge.py** | "통역사". 한글 주문서를 기계 명령으로 번역 | NUC에서 돌면서 Jetson↔BHL 사이 중계 |
| **JSON** | 글자로 적은 주문서 | `{"명령": "앞으로", "지속시간": 3.0}` |
| **TCP** | 전화선 (한 번 연결하면 유지) | Jetson ↔ NUC 사이의 통신선 |
| **UDP** | 우편 (한 통씩 던지고 끝) | NUC ↔ BHL 본체 사이 통신 |
| **NDJSON** | "주문서 한 장 = 한 줄". 줄바꿈으로 구분 | TCP 위에 흘리는 형식 |
| **턴제(turn-based)** | 보드게임처럼 차례 지키기. 한 명이 끝나야 다음 차례 | 우리 프로젝트의 동작 방식 |
| **duration_sec** | "몇 초 동안 할지" | JSON에 새로 추가할 필드 (예: 3.0) |
| **DONE 신호** | "끝났어요" 알림 | NUC가 동작 끝내고 Jetson에 보내는 메시지 |
| **keepalive** | "이 명령 아직 유효해요" 신호 반복 | 같은 명령을 0.1초마다 송신 (다리가 멈추지 않게) |
| **watchdog** | 안전장치. 일정 시간 신호 없으면 자동 정지 | 200ms 신호 끊기면 bridge가 STOP 송신 |
| **wake word** | 호출어 ("시리야" 같은) | 평소엔 자고 있다가 이 단어 들으면 깸 |

---

## 2. 식당 비유로 보는 전체 시스템

```
┌─────────────────────────────────────────────────────────────────┐
│                        🍴 식당 비유                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   손님(사용자)                                                    │
│      │ "스테이크 미디엄으로 3분 동안 구워주세요"                   │
│      ▼                                                           │
│   ┌─────────────┐                                                │
│   │ 홀 매니저    │  ← Jetson coordinator.py                       │
│   │             │  ① 손님 주문 받기                               │
│   │             │  ② "네 주문 들어갔습니다" 답변                   │
│   │             │  ③ 주방에 주문서 전달                            │
│   │             │  ⑥ 주방에서 "완성!" 받으면                       │
│   │             │  ⑦ "음식 나왔습니다" 손님께 안내                  │
│   └─────┬──▲────┘                                                │
│         │  │                                                     │
│   주문서 │  │ "완성!" 신호 (DONE)                                  │
│   (TCP) │  │ (TCP, 같은 전화선)                                    │
│         ▼  │                                                     │
│   ┌─────────────┐                                                │
│   │ 통역사       │  ← NUC bridge.py                              │
│   │             │  ④ 주문서를 주방 코드로 번역                     │
│   │             │  ⑤ 3분 후 자동으로 "완성!" 알림                  │
│   └─────┬───────┘                                                │
│         │ 기계 명령 (UDP)                                         │
│         ▼                                                        │
│   ┌─────────────┐                                                │
│   │ 주방장       │  ← BHL C 코드 + 모터/IMU                       │
│   │             │     실제 요리 (걷기)                             │
│   └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**중요**:
- 홀 매니저는 주문 받고 → 잠시 기다리고 → 완성 알림 → 손님 안내. 한 번에 한 손님만.
- 통역사가 "3분 후 알림 보내기" 시계 기능 담당.
- 손님이 중간에 "그만 구워!" 외치면 매니저가 즉시 주방에 stop 전달 (비상 정지).

---

## 3. 전체 흐름 (사용자 시나리오)

```
[사용자]   "앞으로 가"
              ↓
┌──────────────────────────────────────────────────────────────┐
│ Jetson coordinator                                            │
│                                                               │
│  ① wake word "하이리온" 듣고 깨어남                            │
│  ② 사용자 음성 녹음 → STT → LLM                                │
│  ③ action_json 생성                                            │
│     {                                                         │
│       "intent": "move",                                       │
│       "gait_cmd": "walk_forward",                             │
│       "duration_sec": 3.0,    ← 새 필드                       │
│       "reply_text": "네, 앞으로 가겠습니다",                    │
│       ...                                                     │
│     }                                                         │
│  ④ 🔊 "네, 앞으로 가겠습니다" 음성 출력 + 입 서보 움직임         │
│  ⑤ NUC에 action_json 송신 (TCP)                                │
│  ⑥ ⏳ NUC에서 DONE 신호 올 때까지 대기                          │
│                                                               │
│      ↕ 이 동안에도 "멈춰" 키워드 마이크로 listen 중              │
│                                                               │
│  ⑪ DONE 받음                                                   │
│  ⑫ 🔊 "도착했습니다" 음성 출력 + 입 서보                        │
│  ⑬ 다시 wake word 대기 모드                                    │
└──────────────────────────────────────────────────────────────┘
                ↓ TCP NDJSON
┌──────────────────────────────────────────────────────────────┐
│ NUC bridge                                                    │
│                                                               │
│  ⑦ action_json 받음                                            │
│  ⑧ UDP로 BHL에 "앞으로 가" 명령 20Hz로 송신 시작                │
│      + 3초 타이머 시작                                          │
│  ⑨ 3초 경과 → BHL에 STOP 송신                                  │
│  ⑩ Jetson에 DONE 송신 (TCP, 같은 연결)                          │
│     {"event": "done", "action_id": "..."}                     │
└──────────────────────────────────────────────────────────────┘
                ↓ UDP 13바이트
            🤖 BHL 다리 걷는 중...
```

---

## 4. 기존 가정 vs 새 가정 (사용자 정정 반영)

| 항목 | 처음 가정 (틀림) | 사용자가 정정한 흐름 (맞음) |
|---|---|---|
| 작업 방식 | 멀티태스킹 (걸으면서 챗) | **턴제** (한 번에 하나) |
| 명령 지속 | "다음 명령 올 때까지 무한 keepalive" | **N초만 걷고 자동 종료** |
| coordinator의 종료 시점 인지 | "다음 명령 결정할 때만 알 수 있음" | **NUC가 DONE 알림 보내줌** |
| 통신 방향 | Jetson → NUC 단방향 | **양방향** (NUC → Jetson DONE 추가) |
| 비상정지 | "다음 명령 받을 때만 가능" | **걷는 동안에도 "멈춰" 키워드 감지** |

---

## 5. 추가할 컴포넌트 4개

### 5-1. Jetson 측 — BhlSender (송신 일꾼)

```
┌─────────────────────────────────────────────────────┐
│ BhlSender (백그라운드 스레드)                         │
│                                                     │
│  📋 보관 중인 명령 (action_json 또는 None)            │
│                                                     │
│  🔁 무한 반복:                                       │
│     1. NUC에 TCP 연결 (없으면 재연결)                 │
│     2. 보관 명령 있으면 → 한 줄 송신 (10Hz)            │
│     3. 0.1초 자기                                    │
│                                                     │
│  🛑 송신 실패해도 절대 죽지 않음 (try/except)         │
└─────────────────────────────────────────────────────┘

[coordinator가 호출]
  sender.set_command(action_json)  ← 즉시 반환, 일꾼이 알아서 송신
  sender.clear()                    ← 일꾼 멈춤 (DONE 받았을 때)
```

### 5-2. Jetson 측 — BhlReceiver (DONE 수신 일꾼)

```
┌─────────────────────────────────────────────────────┐
│ BhlReceiver (백그라운드 스레드)                       │
│                                                     │
│  같은 TCP 연결에서 NDJSON 수신                       │
│  → {"event": "done", ...} 받으면                    │
│     coordinator 메인 스레드에 신호 전달               │
│     (threading.Event 또는 queue)                   │
└─────────────────────────────────────────────────────┘

[coordinator가 호출]
  receiver.wait_for_done(timeout=10) → DONE 받을 때까지 대기
```

### 5-3. NUC 측 — bridge.py에 시간 타이머 + DONE 송신 추가

```
기존 bridge.py:                          확장 후:
─────────────                            ─────────
TCP 받음 → UDP 변환 → 송신                  TCP 받음 → UDP 변환 → 송신
                                          + duration_sec 타이머 시작
                                          + 시간 다 되면 STOP 송신
                                          + TCP로 DONE 회신
```

### 5-4. Jetson 측 — "멈춰" 키워드 listener (걷는 중에만 활성화)

```
┌─────────────────────────────────────────────────────┐
│ StopWordListener (별도 스레드)                       │
│                                                     │
│  걷기 시작하면 활성화                                │
│  마이크 항상 켜놓고 "멈춰"/"정지" 키워드만 감지         │
│  → 감지되면 즉시 sender에 stop 명령 set              │
│  걷기 끝나면 비활성화                                │
└─────────────────────────────────────────────────────┘

* 구현: 기존 wake_word.py 패턴 활용. 키워드만 다르게.
```

---

## 6. JSON 스키마 확장 — 새 필드 1개만 추가

[`configs/schemas/action.schema.json`](../../configs/schemas/action.schema.json)에 추가:

```json
"duration_sec": {
  "type": "number",
  "minimum": 0,
  "maximum": 30,
  "default": 3.0
}
```

- intent가 `move`일 때만 필수. 그 외 무시.
- 기본값 3초. LLM이 사용자 요청에 따라 조정 가능 ("멀리 가" → 5초 등).
- 최대 30초로 제한 (안전).

---

## 7. coordinator 메인 흐름 (의사코드)

```python
def handle_user_input(user_text):
    action = llm.build_action(user_text)
    intent = action["intent"]

    # 1단계: 응답 음성 (시작 알림)
    tts.speak(action["reply_text"], mouth_servo)

    # 2단계: 행동이 BHL 관련이면 송신 + 대기
    if intent in {"move", "stop"} or action.get("requires_bhl"):
        sender.set_command(action)
        stop_listener.start()                    # "멈춰" 마이크 listen 시작

        done = receiver.wait_for_done(timeout=action.get("duration_sec", 3) + 2)
        # +2초 = 네트워크 여유. 그래도 안 오면 강제 stop.

        stop_listener.stop()
        sender.clear()

        # 3단계: 완료 음성 (종료 알림)
        if done:
            tts.speak("도착했습니다", mouth_servo)
        else:
            tts.speak("동작에 문제가 있었어요", mouth_servo)

    # 4단계: 대기 모드 복귀
    return_to_standby()
```

**핵심 포인트**:
- `intent`가 chat이면 sender 호출 자체를 안 함 → 다리 영향 없음.
- "멈춰" listener는 걷는 동안만 켬 (배터리/CPU 절약).
- DONE이 timeout 안에 안 오면 안전을 위해 강제 stop 음성 + 다음 명령으로.

---

## 8. NUC bridge.py 확장 (의사코드)

```python
# 기존 handle_client에 추가
def handle_client(conn):
    while True:
        msg = recv_ndjson_line(conn)

        if msg["intent"] == "stop":
            send_udp(STOP_PACKET)
            send_done(conn, msg["action_id"])    # 즉시 DONE
            continue

        if msg["gait_cmd"] in {"walk_forward", "turn_left"}:
            duration = msg.get("duration_sec", 3.0)
            current_packet = make_packet(msg)
            action_id = msg["action_id"]

            # 백그라운드 타이머 시작
            timer = threading.Timer(duration, lambda: on_done(conn, action_id))
            timer.start()

def on_done(conn, action_id):
    current_packet = STOP_PACKET                  # UDP sender가 자동으로 STOP 송신
    send_done(conn, action_id)                    # TCP로 회신

def send_done(conn, action_id):
    msg = {"event": "done", "action_id": action_id, "timestamp": now_iso()}
    conn.sendall((json.dumps(msg) + "\n").encode())
```

**비상정지 처리**: 일꾼이 보내는 keepalive 중 `intent="stop"`이 오면 즉시 타이머 cancel + STOP 송신 + DONE 회신.

---

## 9. 안전 장치 3중 구조

```
1차 (가장 안쪽): bridge.py watchdog 200ms
   → coordinator 죽거나 LAN 끊기면 자동 STOP

2차: bridge.py 시간 타이머
   → duration_sec 끝나면 자동 STOP + DONE

3차 (가장 바깥쪽): coordinator의 "멈춰" listener
   → 사용자가 직접 외치면 즉시 stop 송신

추가 보호: DONE 신호가 timeout 안에 안 오면
   → coordinator가 강제로 sender.clear() + 음성 안내
```

세 가지가 모두 독립적으로 작동. 하나 실패해도 다른 것이 멈춤.

---

## 10. 작업 분해 (코드 짤 때 순서)

```
✅ 0단계: 결정 사항 확정 (이 문서)
   - 시간 기반 종료 ✓
   - wake word 없이 "멈춰" 감지 ✓

📝 1단계: JSON 스키마 확장
   - configs/schemas/action.schema.json에 duration_sec 추가
   - LLM 프롬프트에 "intent=move면 duration_sec 채워줘" 안내 추가

📝 2단계: NUC bridge.py 확장
   - 시간 타이머 추가
   - DONE 송신 함수 추가
   - 단위 테스트: mock_coordinator로 duration_sec 보내고 DONE 회신 확인

📝 3단계: Jetson BhlSender 작성
   - jetson/core/bhl_sender.py 새 파일
   - set_command / clear / start / stop API
   - 백그라운드 송신 스레드 + 재연결 로직

📝 4단계: Jetson BhlReceiver 작성
   - 같은 TCP 연결에서 DONE 메시지 listen
   - wait_for_done(timeout) API

📝 5단계: coordinator에 통합
   - main()에서 sender/receiver 생성
   - _route_action 또는 새 함수에서 set_command → wait_for_done → clear
   - chat/standby는 건너뛰는 분기

📝 6단계: "멈춰" listener (별도 PR 추천)
   - wake_word 시스템 활용
   - 걷는 중에만 활성화/비활성화

✅ 7단계: 끝-to-끝 검증 (다음 섹션)
```

---

## 11. 검증 방법 (NUC 없이 Jetson 한 대로)

```
터미널 1 (가짜 NUC bridge):
   $ python nuc/bhl/bridge.py
   → "TCP listening on 0.0.0.0:9000" 보임

터미널 2 (가짜 BHL 로봇):
   $ python nuc/bhl/tests/mock_bhl_receiver.py
   → "listening on UDP 0.0.0.0:10011" 보임

터미널 3 (진짜 coordinator):
   $ python -m jetson.core.coordinator
```

### 시나리오별 기대 동작

| 시나리오 | 사용자 행동 | 기대 결과 |
|---|---|---|
| ① 정상 보행 | "앞으로 가" | 🔊 시작 음성 → T2에 vx=0.5 3초간 → T1에 DONE 송신 로그 → 🔊 "도착" |
| ② 잡담 | "오늘 날씨 어때?" | 🔊 응답만, T1/T2 무반응 |
| ③ 비상정지 | "앞으로 가" 후 1초 뒤 "멈춰" | 보행 중단 → 🔊 "정지했어요" |
| ④ NUC 죽음 | NUC bridge kill | sender가 재연결 시도, coordinator 음성은 정상 |
| ⑤ DONE 안 옴 | bridge에서 일부러 DONE 안 보내게 | timeout 후 강제 stop + 🔊 "문제 발생" |

---

## 12. Q&A

**Q1. 같은 TCP 연결로 양방향이면 뒤섞이지 않나?**
→ TCP는 양방향 스트림이라 send/recv가 독립. 한쪽이 보내는 중에 다른 쪽도 보낼 수 있음. 메시지마다 줄바꿈으로 끊으니 파싱도 안 섞임.

**Q2. coordinator가 ⑥번에서 대기하는 동안 다른 wake word 무시되나?**
→ 네. 의도된 동작 (턴제). 단 "멈춰" 키워드만 별도 listener로 받음.

**Q3. duration_sec은 LLM이 어떻게 결정하나?**
→ 시스템 프롬프트에 "사용자 요청을 보고 적절한 시간(1~10초) 정해라" 안내. 예: "한 발만" → 1.0, "쭉 가" → 5.0. 모호하면 기본 3.0.

**Q4. NUC가 DONE 보냈는데 네트워크 지연으로 늦게 오면?**
→ coordinator는 `duration + 2초`까지 기다림. 그래도 안 오면 강제 stop. 늦게 도착한 DONE은 무시.

**Q5. 한 번 BhlSender 만들면 평생 같이 사는 건가?**
→ 네. coordinator 시작 시 1회 생성, 종료 시 stop. 그 사이엔 set_command/clear만 반복.

**Q6. 걷는 도중 "왼쪽으로 가" 같은 새 명령은?**
→ 턴제 원칙상 무시 (현재 동작 끝날 때까지). 단 "멈춰"만 예외. 추후 확장 시 "걷는 중 방향 변경 받기"가 필요하면 별도 설계.

---

## 13. 한 줄로 다시 요약

> **"홀 매니저(Jetson)가 통역사(NUC)에게 '3분 동안 스테이크 구워' 주문서 보내고 기다림. 통역사는 주방장(BHL)에게 굽기 명령 + 3분 타이머 작동. 3분 후 주방장 멈추고 매니저에게 '완성!' 회신. 그 사이 손님이 '그만!' 외치면 매니저가 통역사에게 즉시 stop 전달."**

---

## 14. 다음 단계 (이 작업 끝난 후)

- **3,4번** (다른 팀원): DGX에서 학습 → checkpoint를 NUC `Berkeley-Humanoid-Lite-Lowlevel-main/checkpoints/`에 복사
- **5번** (다른 팀원): NUC에서 `make run` + `rl_controller.py` 실행 → 실제 BHL 다리 제어
- **6번 (추가 튜닝)**: 학습된 명령 범위에 맞춰 bridge.py의 `VEL_FORWARD_MPS` 등 환경변수로 조정
- **(추가)** 걷는 중 방향 변경 받기, IMU telemetry 기반 자동 EMERGENCY 등 — 데모 검증 후 결정

---
