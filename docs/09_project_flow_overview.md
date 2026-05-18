# Hylion 프로젝트 전체 흐름 & 구조

기준 시점: 2026-05-18
기준 브랜치: `e1`
주 진입점: [scripts/run_coordinator.sh](../scripts/run_coordinator.sh) →
[jetson/core/coordinator.py](../jetson/core/coordinator.py)

---

## 0. 한눈에 보는 시스템 토폴로지

```
┌─────────────────────────── Jetson (Orin) ──────────────────────────────┐
│                                                                        │
│  systemd --user                                                        │
│   └─ hylion-coordinator.service  (B 서비스, 부팅 자동 실행)            │
│        └─ scripts/run_coordinator.sh                                   │
│             └─ python -m jetson.core.coordinator                       │
│                  ├─ wake_word listener  ("Hey Hyleon" tflite)          │
│                  ├─ EmergencyStopListener  ("stop" tflite, 동작중에만) │
│                  ├─ microphone (record/VAD) → STT (Whisper)            │
│                  ├─ LLM (Groq online ↔ Ollama offline)                 │
│                  ├─ TTS (Clova online ↔ MeloTTS offline) + 입 서보     │
│                  ├─ BhlClient ──TCP/NDJSON──▶ NUC bridge               │
│                  └─ subprocess: gesture_daemon (~/smolvla 별도 venv)   │
│                                  └─ Unix socket: 우측 SO-ARM 제어      │
│                                                                        │
│  하드웨어:  P5HD USB 마이크, USB 스피커, Jetson.GPIO Pin33 (입 서보)   │
│            우측 SO-ARM (USB CH340 시리얼)                              │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  TCP/NDJSON  (HYLION_BHL_HOST:PORT)
                                    │  10Hz keepalive + 단발 명령 + DONE
                                    ▼
┌──────────────────────────── NUC (BHL) ─────────────────────────────────┐
│  systemd: hylion-bhl-bridge.service                                    │
│   └─ python -m nuc.bhl.bridge                                          │
│        ├─ Jetson TCP listener (NDJSON)                                 │
│        ├─ duration_sec 타이머 → 만료 시 STOP + DONE 회신               │
│        └─ UDP ──▶ BHL lowlevel (mode/lin_vel/ang_vel)  20Hz            │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  UDP, BHL packet
                                    ▼
                       ┌────────────────────────────┐
                       │ BHL lowlevel (다리 제어)   │
                       │ Berkeley-Humanoid-Lite     │
                       └────────────────────────────┘

(외부 클라우드)
   Groq API ──◀─── coordinator(online LLM)
   Clova TTS ─◀─── speaker (online TTS)
```

---

## 1. 부팅 ~ 정지 라이프사이클

```
[전원 ON]
    │
    ▼
systemd 부팅 → graphical.target 또는 multi-user.target
    │                                       │
    │ (헤드리스 모드: A 켜졌을 때)          │ (개발 모드: A 꺼졌을 때)
    │                                       │
    ▼                                       ▼
multi-user.target (텍스트 콘솔)        graphical.target (GDM, GUI)
    │                                       │
    └───────────────────┬───────────────────┘
                        │
                        ▼
            systemd --user 가 user@1000 세션 시작
            (linger=yes 라서 로그인 없이도 시작됨)
                        │
                        ▼
            hylion-coordinator.service 시작
                ExecStartPre=sleep 5         ← USB 마이크 안정화
                ExecStart=run_coordinator.sh
                        │
                        ▼
            run_coordinator.sh
                ├─ LD_LIBRARY_PATH = libcusparseLt 포함
                ├─ env: HYLION_WAKEWORD_DEVICE_KEYWORD=P5HD
                ├─ env: HYLION_ESTOP_THRESHOLD=0.3 (튜닝중)
                └─ exec python -m jetson.core.coordinator
                        │
                        ▼
            coordinator.main()
                ├─ gesture_daemon subprocess fork (15s 대기)
                ├─ BhlClient.start() (NUC bridge TCP 연결, keepalive)
                ├─ wake_word listener 빌드
                ├─ Whisper warm_up
                └─ run_live_pipeline()
                        │
                        ▼
                  (메인 루프: §2)
                        │
                        ▼
            KeyboardInterrupt / systemctl stop
                ├─ wake_word.close()
                ├─ bhl_client.stop()
                ├─ gesture_daemon.stop() (Unix socket 종료 신호)
                └─ cleanup_gpio()
```

---

## 2. 메인 런타임 흐름 (turn-based)

```
        ╔═══════════════════════════════════════════════════════╗
        ║          [outer loop] 웨이크워드 대기                  ║
        ╠═══════════════════════════════════════════════════════╣
        ║  wakeword_listener.wait_for_wake_word()                ║
        ║  └─ openWakeWord(tflite) @ 16kHz                       ║
        ║     모델: checkpoints/wakeword/Hey_Hyleon.tflite       ║
        ╚═══════════════════════════════════════════════════════╝
                                │ "Hey Hyleon"
                                ▼
                ┌──────────────────────────┐
                │  is_online() probe       │ → online / offline 분기
                └──────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼ online                        ▼ offline
        Groq llama-3.1-8b              Ollama qwen2.5:1.5b
        Clova Premium TTS              MeloTTS (로컬 daemon)
                │                              │
                └──────────────┬───────────────┘
                               ▼
                "네, 말씀하세요!" greeting (TTS+lipsync)
                               │
                               ▼
   ╔══════════════════════════════════════════════════════════╗
   ║         [inner loop] 채팅 모드 - wake 없이 반복           ║
   ╠══════════════════════════════════════════════════════════╣
   ║  ① record_to_wav() (microphone.py)                       ║
   ║     - VAD 무음 게이트 + Whisper 환각 필터                ║
   ║                                                          ║
   ║  ② transcribe_wav() (stt_whisper / groq_whisper)         ║
   ║                                                          ║
   ║  ③ build_action_json_from_stt()                          ║
   ║     - prompt.py: extract_core / apply_hard_overrides /   ║
   ║       derive_full_action / assemble_action               ║
   ║     - online: Groq REST + JSON mode                      ║
   ║     - offline: Ollama qwen + 동일 derive 레이어          ║
   ║     - 둘 다 action.schema.json 으로 검증                 ║
   ║                                                          ║
   ║  ④ history append (최근 10턴) + session jsonl 로그       ║
   ║                                                          ║
   ║  ⑤ _play_gesture_if_any()  ← chat 턴만, non-blocking     ║
   ║     gesture_daemon.play(name) → Unix socket ACK 즉시 반환║
   ║     실패해도 대화 루프 안 끊김                           ║
   ║                                                          ║
   ║  ⑥ _speak_reply_if_any() TTS + 입 서보 lipsync (blocking)║
   ║                                                          ║
   ║  ⑦ intent 분기 ─────────────────────────────────────────╗║
   ║     │                                                   ║║
   ║     ├ chat / unknown      → ①로 (다음 발화 대기)         ║║
   ║     │                                                   ║║
   ║     ├ standby             → cooldown 1.2s → outer 복귀  ║║
   ║     │                                                   ║║
   ║     └ pick_place / move / stop                          ║║
   ║       └ _dispatch_to_bhl()                              ║║
   ║         ├─ EmergencyStopListener.start() (mic 점유 시작)║║
   ║         ├─ bhl_client.set_command(action_json)          ║║
   ║         │     → NUC bridge 로 TCP 송신                  ║║
   ║         │     → bridge 가 UDP 로 BHL lowlevel 송출      ║║
   ║         │     → duration_sec 타이머 시작                ║║
   ║         ├─ bhl_client.wait_for_done(timeout)            ║║
   ║         │     ◀ DONE 수신 (duration_elapsed /           ║║
   ║         │       stop_command / safety_or_emergency)     ║║
   ║         ├─ EmergencyStopListener.stop() (mic 해제)      ║║
   ║         └─ bhl_client.clear()                           ║║
   ║                                                         ║║
   ║         ├ done.reason=safety_or_emergency 면            ║║
   ║         │  standby reply 를 "비상정지했어요…" 로 교체    ║║
   ║         │                                                ║║
   ║         └ standby 액션 생성 + TTS + cooldown 1.5s →     ║║
   ║           outer 복귀                                    ║║
   ╚══════════════════════════════════════════════════════════╝
                                │
                          KeyboardInterrupt / stop signal
                                ▼
                       (cleanup, §1 참조)
```

### E-stop 흐름 (위 ⑦ 의 BHL 분기 안에서만 동작)

```
move 실행 시작:  EmergencyStopListener.start(on_trigger=push_emergency_action)
                                │
                                ▼ ("stop" 발화 검출)
            on_trigger 콜백:
              bhl_client.set_command(EMERGENCY action)
                                │
                                ▼
            bridge 가 map_json_to_packet 에서 state_current==EMERGENCY 보고
              ├─ STOP UDP 즉시 송신
              └─ 원래 action_id 에 대한 DONE(reason=safety_or_emergency) 회신
                                │
                                ▼
            coordinator wait_for_done 풀림
              → listener.stop() (mic 해제)
              → reason 전파 → reply 교체
```

**안전 원칙**: mic 점유는 정확히 BHL 동작 구간에만 (record/main wake listener 와
ALSA single-open 충돌 회피). threshold 0.3~0.4 (false negative 가 false positive
보다 위험하므로 살짝 민감하게). 모델/오디오 미가용이면 listener 가 disabled 상태로
빌드되고 dispatch 가 자동 우회.

---

## 3. 모듈/파일 인벤토리 (2026-05-18 기준)

범례: ✅ 동작 중 · ⚠ 부분 동작 · ❌ 빈 파일/스텁 · 📦 외부 시스템

```
Hylion/
├─ scripts/                              ◀ 운영 진입점/관리 스크립트
│  ├─ run_coordinator.sh                 ✅ 표준 런처 (venv + env + exec)
│  ├─ install-coordinator-service.sh     ✅ systemd user 서비스 설치/제거
│  ├─ headless-on.sh                     ✅ GUI 끄기 (multi-user.target)
│  ├─ headless-off.sh                    ✅ GUI 켜기 (graphical.target)
│  ├─ live_monitor.sh                    ✅ RAM/GPU/프로세스 모니터 (1s)
│  ├─ test_wakeword.sh / .py             ✅ 마이크+wakeword 격리 테스트
│  ├─ deploy_jetson.sh / deploy_nuc.sh   ❌ 빈 파일 (미사용)
│  └─ systemd/
│     └─ hylion-coordinator.service.in   ✅ unit 템플릿 (PROJECT_ROOT 치환)
│
├─ jetson/
│  ├─ core/                              ◀ 메인 런타임
│  │  ├─ coordinator.py                  ✅ 진입점 (run_live_pipeline)
│  │  ├─ bhl_client.py                   ✅ NUC bridge TCP 클라이언트
│  │  │                                     (송신/keepalive/DONE 수신 워커)
│  │  ├─ gesture_client.py               ✅ smolVLA 데몬 subprocess 관리
│  │  │                                     + Unix socket 명령 전송
│  │  ├─ gesture_registry.py             ✅ 유효 gesture 이름 단일 SoT
│  │  │                                     (~/smolvla/orin/gestures 스캔)
│  │  ├─ network.py                      ✅ is_online() probe (DNS)
│  │  ├─ llm/
│  │  │  ├─ prompt.py                    ✅ extract_core / hard_overrides /
│  │  │  │                                   derive_full_action / assemble
│  │  │  ├─ groq_llm.py                  ✅ Groq REST + JSON mode
│  │  │  ├─ ollama_llm.py                ✅ 로컬 qwen2.5:1.5b
│  │  │  ├─ base.py / factory.py         ✅ online/offline 선택
│  │  │  └─ eval/run_eval.py             ✅ 26 케이스 회귀 (80.8%)
│  │  ├─ stt/
│  │  │  ├─ local_whisper.py             ✅ openai-whisper (CUDA→CPU)
│  │  │  ├─ groq_whisper.py              ✅ Groq Whisper API
│  │  │  └─ base.py / factory.py         ✅
│  │  ├─ tts/melotts_client.py           ✅ 로컬 MeloTTS HTTP 클라이언트
│  │  ├─ brain/network_probe.py          ⚠ 일부만 coordinator 에서 사용
│  │  └─ hylion_brain_v2.py              ❌ 레거시 실험 코드
│  │
│  ├─ expression/                        ◀ 음성/모터 IO
│  │  ├─ wake_word.py                    ✅ openWakeWord + EmergencyStopListener
│  │  ├─ microphone.py                   ✅ sounddevice + VAD + 무음게이트
│  │  ├─ speaker.py                      ✅ Clova/gTTS/MeloTTS + mpg123 + lipsync
│  │  ├─ mouth_servo.py                  ✅ Jetson.GPIO Pin33 SW-PWM 50Hz
│  │  ├─ mock_mouth_servo.py             (테스트용)
│  │  ├─ factory.py                      ✅
│  │  └─ .venv/                          📦 PyTorch + openai-whisper venv
│  │
│  ├─ perception/                        ❌ 전부 빈 파일
│  ├─ arm/                               ❌ 전부 빈 파일 (gesture 는 smolVLA 측)
│  ├─ state_machine/fsm.py               ❌ 빈 파일
│  ├─ safety/                            ❌ 전부 빈 파일
│  │                                       (e-stop 는 wake_word.py 안에 구현)
│  └─ scenarios/                         ❌ 빈 파일
│
├─ nuc/bhl/                              ◀ NUC 머신에서 도는 BHL bridge
│  ├─ bridge.py                          ✅ Jetson TCP listener + UDP 출력
│  │                                       + duration_sec 타이머 + DONE 회신
│  ├─ Berkeley-Humanoid-Lite-Lowlevel-…  📦 BHL 원본 (서브트리)
│  ├─ tests/mock_coordinator.py          ✅ DoneReader + 시나리오 검증
│  ├─ Jetson_NUC_연결_가이드.md          ✅ 비전공자용 설명서
│  ├─ BHL_Bridge_Handoff.md              ✅ 인수인계 문서
│  └─ systemd/                           ✅ NUC 측 systemd unit
│
├─ smolVLA/scripts/gesture_daemon.py     ✅ 우측 SO-ARM 동작 재생 데몬
│  └─ (coordinator subprocess 로 띄움. ~/smolvla 별도 venv 사용)
│
├─ comm/                                 ◀ 메시지 계약
│  ├─ protocol.py                        ✅ MessageType, Header, ACK
│  ├─ schema_validator.py                ✅ jsonschema
│  └─ {nuc,orin,mock_bridge}.py          ❌ 빈 파일 (현재 bhl_client/bridge.py
│                                           가 자체 NDJSON 으로 처리)
│
├─ configs/schemas/                      ◀ 모든 메시지의 진실 소스
│  ├─ action.schema.json                 ✅ LLM 프롬프트+검증 양쪽 사용
│  │                                       (gesture_name, duration_sec 포함)
│  ├─ input_event.schema.json
│  ├─ executor_command.schema.json
│  ├─ emergency_event.schema.json
│  └─ smolvla_episode/session.schema.json
│
├─ checkpoints/wakeword/
│  ├─ Hey_Hyleon.tflite                  ✅ 메인 wake word
│  └─ stop.tflite (+ .onnx)              ✅ e-stop wake word (2026-05-18 추가)
│
├─ data/
│  ├─ episodes/   live_*.wav            ◀ 라이브 녹음 (gitignore)
│  ├─ reply/      *.mp3                 ◀ TTS 출력
│  └─ sessions/   <session_id>.jsonl    ◀ 턴 단위 로그
│
├─ services/tts_server/                  📦 MeloTTS HTTP server (별 systemd)
├─ sim/                                  ◀ MuJoCo/IsaacLab 학습 측
├─ tests/                                ◀ unit/interface/integration
├─ docs/                                 ◀ 이 문서를 포함한 기획서들
└─ legacy/ros2/                          ◀ ROS2 노드 보존 (미사용)
```

---

## 4. 데이터 흐름 한 줄 요약

```
USB Mic ─► wake_word(tflite) ─► record_to_wav ─► Whisper STT
                                                       │
                                                       ▼
                                          prompt.derive_full_action
                                          (Groq online / Ollama offline)
                                                       │
                                                       ▼
                          ACTION_JSON  {intent, gesture_name, duration_sec, …}
                                                       │
              ┌──────────────────┬───────────────────┬─┴──────────────┐
              ▼                  ▼                   ▼                ▼
       speak (TTS+lipsync)  gesture_daemon    bhl_client → NUC      history +
                            (chat 턴, 팔)      bridge → BHL UDP     session.jsonl
                                                (move/stop, 다리)
                                                       │
                                                       ▼
                                              EmergencyStopListener
                                              ("stop" 발화 → EMERGENCY
                                               action 푸시 → DONE 받고 종료)
```

---

## 5. 운영 (systemd / headless)

### 5.1 두 가지 직교 설정

| 설정 | 무엇? | 기본값 | 토글 방법 |
|---|---|---|---|
| **A. GUI 모드** | 부팅 시 GDM/그래픽 세션 띄울지 | `graphical.target` (켜짐) | `scripts/headless-on.sh` / `headless-off.sh` |
| **B. 자동 실행** | coordinator 를 부팅 시 자동 띄울지 | systemd user service (켜짐, 2026-05-18~) | `scripts/install-coordinator-service.sh [--uninstall]` |

B 는 A 와 독립적으로 동작. GUI 가 떠있어도 백그라운드에서 돌고, GUI 가 꺼져있어도
linger 덕분에 그대로 돈다.

### 5.2 systemd 의존 관계

```
[부팅]
  └─ systemd (system)
       ├─ default.target = graphical.target  또는  multi-user.target  ◀ A
       ├─ sound.target / network-online.target / …
       │
       └─ user@1000.service          (linger=yes 라서 로그인 없이 시작)
            └─ systemd --user
                 └─ hylion-coordinator.service  ◀ B
                      ExecStartPre=sleep 5
                      ExecStart=/bin/bash scripts/run_coordinator.sh
                      Restart=on-failure
                      WantedBy=default.target
```

`sudo loginctl enable-linger laba` 가 켜져 있어야 부팅 시 자동 실행됨.

### 5.3 조작 명령 빠른 참조

```
# 서비스
systemctl --user status hylion-coordinator         # 상태
systemctl --user restart hylion-coordinator        # 재시작
systemctl --user stop hylion-coordinator           # 정지 (다음 부팅 때 다시 뜸)
journalctl --user -u hylion-coordinator -f         # 실시간 로그

# 설치/제거
bash scripts/install-coordinator-service.sh        # 설치 + 활성화 + 시작
bash scripts/install-coordinator-service.sh --uninstall

# GUI 모드 토글 (현장 배치 / 개발 복귀)
bash scripts/headless-on.sh && sudo reboot         # GUI 끄기 + 재부팅
bash scripts/headless-off.sh && sudo reboot        # GUI 다시 켜기 + 재부팅

# 수동 실행 (디버깅) — 서비스 먼저 stop 필수
systemctl --user stop hylion-coordinator
bash scripts/run_coordinator.sh
```

---

## 6. 핵심 환경변수

`scripts/run_coordinator.sh` 가 기본값을 박아주는 것들 (셸 export 로 override 가능):

| 변수 | 기본 | 의미 |
|---|---|---|
| `HYLION_WAKEWORD_DEVICE_KEYWORD` | `P5HD` | 마이크 선택 키워드 |
| `HYLION_WAKEWORD_SAMPLE_RATE` | `44100` | wake word 입력 샘플레이트 |
| `HYLION_MIC_SAMPLE_RATE` | `44100` | 녹음 샘플레이트 |
| `HYLION_ESTOP_THRESHOLD` | `0.3` | e-stop wake 활성 임계값 (튜닝 중) |
| `HYLION_WAKEWORD_DEBUG_SCORES` | `0.1` | 콘솔에 score 출력 시작 임계 |

런타임 코드가 직접 보는 것들:

| 변수 | 의미 |
|---|---|
| `HYLION_BHL_HOST` / `_PORT` | NUC bridge 접속 (기본 127.0.0.1) |
| `HYLION_BHL_DISABLE=1` | BhlClient 미생성 (stub mode, 오프라인 테스트) |
| `HYLION_BHL_KEEPALIVE_HZ` | bridge keepalive 주기 (기본 10) |
| `ORIN_GESTURES_ROOT` | gesture 디렉토리 override |
| `PLAY_GESTURE_SCRIPT` | gesture 재생 스크립트 override |
| `GROQ_API_KEY` | online LLM/STT |
| `NCP_CLOVA_*` | online TTS (Clova) |

---

## 7. Mermaid 렌더용 다이어그램

```mermaid
flowchart TD
    PWR[전원 ON] --> SYSD[systemd]
    SYSD -->|A: graphical| GDM[GDM/GUI]
    SYSD -->|A: headless| TTY[텍스트 콘솔]
    SYSD --> USERD[systemd --user laba<br/>linger=yes]
    USERD --> SVC[hylion-coordinator.service]
    SVC --> RUNC[run_coordinator.sh]
    RUNC --> COORD[python -m jetson.core.coordinator]
    COORD --> GD[gesture_daemon subprocess]
    COORD --> BHLC[BhlClient]
    BHLC -.TCP/NDJSON.-> BRIDGE[NUC bridge]
    BRIDGE -.UDP.-> LOWLVL[BHL lowlevel]
    GD -.Unix socket.-> ARM[우측 SO-ARM]

    COORD --> OUTER{outer loop<br/>wake_word 대기}
    OUTER -->|Hey Hyleon| ONLINE{is_online?}
    ONLINE -->|yes| GREET1[Groq + Clova greeting]
    ONLINE -->|no| GREET2[Ollama + MeloTTS greeting]
    GREET1 --> INNER{inner loop<br/>chat 모드}
    GREET2 --> INNER
    INNER --> REC[record + Whisper STT]
    REC --> LLM[prompt.derive_full_action<br/>+ schema validate]
    LLM --> GEST[gesture (chat 턴, non-blocking)]
    GEST --> SAY[TTS + lipsync]
    SAY --> INTENT{intent?}
    INTENT -->|chat / unknown| INNER
    INTENT -->|standby| OUTER
    INTENT -->|pick_place / move / stop| DISP[_dispatch_to_bhl]
    DISP --> ESTOP[EmergencyStopListener start]
    ESTOP --> TX[bhl_client.set_command]
    TX --> WAIT[wait_for_done]
    WAIT --> ESTOP2[EmergencyStopListener stop]
    ESTOP2 --> REPLY[종료 reply: 정상 / 비상정지]
    REPLY --> OUTER
```

---

## 8. 한눈 요약

- **살아있는 라인**: `run_coordinator.sh` → `coordinator.py` →
  `wake_word` / `microphone` / `stt` / `llm/prompt` / `speaker` / `mouth_servo` /
  `bhl_client` / `gesture_client`. + NUC `bridge.py`. + smolVLA `gesture_daemon.py`.
- **계약 레이어**: `configs/schemas/action.schema.json` (`gesture_name`,
  `duration_sec` 포함) 가 LLM 프롬프트와 검증, NUC bridge 패킷 매핑 모두에 사용됨.
- **운영 레이어 (2026-05-18 추가)**: systemd user service + headless 토글 →
  로봇에 올리면 전원만 켜도 자동 진입.
- **여전히 스텁**: `perception/*`, `arm/*` (gesture 는 smolVLA 측 따로 있음),
  `safety/*` (e-stop 는 wake_word.py 안에 살아있음), `comm/{nuc,orin,mock_bridge}.py`
  (현재는 bhl_client/bridge.py 가 자체 NDJSON 처리).
- **레거시**: `core/brain/*` (ROS2 publish 경로 일부 함수만 import 됨),
  `core/hylion_brain_v2.py`, `legacy/ros2/`.
