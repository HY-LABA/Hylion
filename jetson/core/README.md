# jetson/core

Hylion의 메인 brain·coordinator 레이어.
웨이크워드 감지 이후 STT → LLM → gesture + TTS 실행까지의 전체 파이프라인을 담당한다.

```
core/
├── coordinator.py          # 메인 루프 (run_coordinator.sh 의 진입점)
│                           #   wake_word → 마이크 녹음 → STT → LLM → action 실행
│                           #   gesture(non-blocking) + TTS(blocking) 병렬 실행
│                           #   온라인/오프라인 자동 분기, BHL bridge 연동
│
├── gesture_client.py       # gesture_daemon 프로세스 관리
│                           #   gesture_daemon.py 를 .hylion_arm venv 서브프로세스로 기동
│                           #   Unix 소켓으로 play/ping/status 명령 전송
│
├── gesture_registry.py     # 유효 gesture 목록 스캔·캐시
│                           #   ORIN_GESTURES_ROOT 하위 디렉토리를 스캔
│                           #   meta/info.json 존재 여부로 유효성 판단
│                           #   prompt.py 의 키워드 매칭과 연동
│
├── client/                  # 외부 서비스 클라이언트 모음
│   ├── bhl_client.py        #   NUC bridge TCP/NDJSON 클라이언트
│   │                        #   Jetson ↔ NUC 유선 직결(10.42.0.0/24), 송수신 스레드 분리
│   ├── gesture_client.py    #   gesture_daemon 프로세스 관리 + Unix 소켓 IPC
│   └── gesture_registry.py  #   유효 gesture 목록 스캔·캐시
│                             #   ORIN_GESTURES_ROOT 하위 meta/info.json 존재 여부로 판단
│
├── llm/                    # LLM 백엔드
│   ├── prompt.py           #   시스템 프롬프트 정의
│   │                       #   gesture 키워드 매칭 (GESTURE_KEYWORD_OVERRIDES)
│   │                       #   detect_gesture() : STT 텍스트 → gesture_name 주입
│   │                       #   derive_full_action() : 4필드 core → 16필드 action JSON
│   ├── groq_llm.py         #   Groq API 클라이언트 (온라인)
│   ├── ollama_llm.py       #   Ollama 로컬 LLM (오프라인 fallback)
│   ├── factory.py          #   온라인 상태에 따라 Groq / Ollama 자동 선택
│   ├── base.py             #   LLMBackend Protocol 인터페이스 정의
│   └── eval/
│       ├── cases.jsonl     #   LLM 응답 평가 케이스 목록
│       └── run_eval.py     #   케이스 기반 LLM 평가 실행기
│
├── stt/                    # STT 백엔드
│   ├── groq_whisper.py     #   Groq Whisper API (온라인)
│   ├── local_whisper.py    #   로컬 OpenAI Whisper (오프라인, CUDA fallback)
│   ├── factory.py          #   온라인 상태에 따라 자동 선택
│   └── base.py             #   STTBackend Protocol + STTResult 데이터클래스
│
└── tts/
    └── melotts_client.py   # MeloTTS 데몬 클라이언트
                            #   .venv-melotts 서브프로세스로 MeloTTS 데몬 기동
                            #   loopback HTTP로 음성 합성 요청
                            #   PulseAudio sink 자동 감지 + 재생
```

## 실행 흐름

```
coordinator.py
  ├─ expression/wake_word.py    "Hey Hylion" 감지
  ├─ expression/microphone.py   음성 녹음 (RMS 게이팅)
  ├─ stt/                       Whisper STT
  ├─ llm/prompt.py              LLM 호출 + gesture 키워드 주입
  └─ 병렬 실행
       ├─ gesture_client.py     → gesture_daemon (팔 동작)
       └─ expression/speaker.py → TTS 재생 + 입 서보 립싱크
```

## gesture 키워드 매핑 (`llm/prompt.py`)

| 발화 키워드 | gesture |
|---|---|
| 인사해 / 인사 해 / 인사하 | `wave_hello` |
| 손 흔들 / 흔들어 / 손 인사 | `wave_hello_2` |
