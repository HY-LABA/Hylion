# Hylion Hybrid Online/Offline 리팩터 계획

기준 시점: 2026-05-06
기준 브랜치: `e1`
관련 문서: [09_project_flow_overview.md](09_project_flow_overview.md) (현재 상태)

---

## 0. 목적

현재 파이프라인은 **wakeword(오프라인)** → **STT(오프라인 whisper)** → **LLM(온라인 Groq)** 으로 환경이 섞여 있음. 인터넷이 끊기면 LLM만 stub으로 폴백되고 STT는 무관하게 로컬에서 돌아가는 상태.

목표:
1. 웨이크워드는 **항상 오프라인** (현재 그대로)
2. 웨이크워드 활성화 직후 **online 측정 1회** → 그 turn 사이클 동안 모든 후속 백엔드(STT/LLM/TTS) 선택에 일관 적용
3. 온라인이면 **Groq Whisper + Groq LLM + CLOVA TTS**, 오프라인이면 **로컬 Whisper + 로컬 LLM + 로컬 TTS** 로 깨끗하게 양쪽 라인 분리
4. coordinator(메인 플로우 파일)는 1개를 유지하고, 분기는 **백엔드 객체 선택**에서만 일어나도록 추상화
5. 명확한 기능 단위는 모듈 분해 (`core/stt/`, `core/llm/`)

---

## 1. 결정사항 (F1 ~ F7)

### F1. STT 온라인 백엔드 선택

| 옵션 | 속도 | 한국어 정확도 | 가격 | 비고 |
|---|---|---|---|---|
| **Groq `whisper-large-v3`** | ~189x realtime | ★★★★★ (Whisper 풀모델) | $0.111 / 시간 | 한국어 학습 풍부, 가장 정확 |
| **Groq `whisper-large-v3-turbo`** | ~216x realtime | ★★★★☆ (large-v3 대비 미세 ↓) | $0.04 / 시간 | 가장 빠름, 번역 미지원 (우리는 transcribe만 쓰므로 무관) |
| **Groq `distil-whisper-large-v3-en`** | ~250x realtime | ✗ (영어 전용) | $0.02 / 시간 | 한국어 미지원, 제외 |
| OpenAI `whisper-1` (Whisper API) | ~10-20x realtime | ★★★★☆ | $0.006 / 분 | 느리고 비쌈, 제외 |
| Deepgram Nova-3 | 매우 빠름 | ★★★★☆ (다국어) | $0.0043 / 분 | 한국어 품질 Whisper 대비 약간 떨어진다는 후기 |
| **CLOVA Speech (Naver)** | 빠름 (실시간) | ★★★★★ (한국어 native) | NCloud 종량제 | 이미 NCloud 결제수단 등록됨 (CLOVA Voice Premium 사용 중), 한국어 STT는 일반적으로 Whisper보다 한국어 인식률 우위 |
| ElevenLabs Scribe | 보통 | ★★★☆☆ | $$$ | 영어 외 약함 |

**권장: `Groq whisper-large-v3-turbo`**
- 4-6초 발화 기준 응답 < 0.5초 (Groq 인프라가 압도적으로 빠름)
- 한국어 정확도는 large-v3 대비 거의 차이 없음 (영어 외 다국어는 둘 다 Whisper-large-v3 베이스)
- LLM도 Groq을 쓰므로 인증/지연/장애 표면을 한 곳으로 모으는 운영적 이점
- **무료 티어로 충분**: 20 RPM / 7,200 audio sec per hour / 28,800 audio sec per day / 2,000 RPD. 한 turn 4초 발화 기준 일일 7,200턴 가능 → 일상 사용에 압도적 여유. STT와 LLM은 모델별 별도 버킷이라 같은 API 키로 둘 다 호출해도 한도가 겹치지 않음.

**대안 (한국어 정확도 최우선이면)**: CLOVA Speech.
- 이미 NCloud 결제 채널 사용 중이라 추가 가입 불필요
- 한국어 STT는 보통 Whisper 한국어 < CLOVA 한국어 (CLOVA가 자체 한국어 corpus로 학습)
- 단점: 키 관리 + 응답 시간이 Groq보다 길음 (수백 ms 추가)

→ **1차로 Groq turbo 채택, 한국어 정확도 불만족 시 CLOVA Speech로 교체** (인터페이스가 추상화돼 있으니 백엔드 1파일만 갈아끼우면 됨).

### F2. LLM 오프라인 백엔드 선택

Jetson Orin Nano Super 8GB 기준 — RAM은 CPU/GPU 공유 7.4 GiB. 시스템(2.6GB) + Whisper(0.5GB) + TTS(2GB) + 음성 버퍼/기타(0.5GB) 제하면 **LLM에 쓸 수 있는 마진은 1.5 ~ 2.5 GB**.

| 모델 | 크기 (Q4_K_M) | 한국어 | JSON 모드 | 추론 속도 (Orin Nano 추정) | 비고 |
|---|---|---|---|---|---|
| **EXAONE 3.5 2.4B** (LG) | ~1.5 GB | ★★★★★ (한국어 native 학습) | ★★★★ | 30-40 tok/s | Ollama 라이브러리에 등록됨 (`exaone3.5:2.4b`), 라이센스 비상업 OK |
| Qwen2.5 3B Instruct | ~2 GB | ★★★★ | ★★★★★ (JSON 잘 지킴) | 25-35 tok/s | 다국어 강함, 한국어도 준수 |
| Gemma 2 2B | ~1.6 GB | ★★★ | ★★★ | 35-45 tok/s | 한국어 약점, 영어 메인 |
| Llama 3.2 3B | ~2 GB | ★★★ | ★★★★ | 25-35 tok/s | 한국어 학습 비중 낮음 |
| Phi-3.5 mini 3.8B | ~2.4 GB | ★★ | ★★★★ | 20-30 tok/s | 한국어 매우 약함 |
| **Qwen2.5 7B Instruct** | ~4.7 GB | ★★★★☆ | ★★★★★ | 8-12 tok/s | 정확도는 좋지만 메모리 빠듯, 스왑 위험 |
| EXAONE 3.5 7.8B | ~4.9 GB | ★★★★★ | ★★★★ | 8-12 tok/s | 동일하게 메모리 빠듯 |

런타임 옵션:
- **Ollama**: 가장 간단, llama.cpp 백엔드, JSON 모드(`format: "json"`) 내장, HTTP API
- llama.cpp 직접: Ollama보다 약 5-10% 빠르지만 직접 구동 + GGUF 관리 필요
- MLC-LLM: Jetson 최적화 가능하지만 모델 변환 + 셋업 비용
- TensorRT-LLM: 가장 빠르지만 모델별 엔진 빌드 필요, 운영 복잡

**권장: Ollama + `exaone3.5:2.4b` (Q4_K_M)**
- 한국어 응답 품질이 동급 모델 중 가장 뛰어남 (LG가 한국어 corpus로 사전학습)
- 메모리 1.5 GB는 다른 컴포넌트와 공존 가능
- Ollama JSON 모드로 `action.schema.json` 강제 가능
- 실패 시 대안: Qwen2.5 3B (JSON 안정성 더 좋음)

### F3. Ollama 엔드포인트 의미

"엔드포인트" = Ollama가 제공하는 **HTTP API의 URL**.

- Ollama는 `ollama serve`로 시작하는 데몬 프로세스 (systemd 서비스로 자동 기동 가능)
- 기본 listen: `http://127.0.0.1:11434`
- 우리 코드는 이 URL로 HTTP POST를 보내서 LLM 추론을 요청 (`/api/chat`, `/api/generate`)
- → **별도 머신 없이 Jetson 내부 localhost에서 호출**, 따라서 환경변수 등 설정 불필요. 기본값 그대로 사용.

설치/기동:
```bash
curl -fsSL https://ollama.com/install.sh | sh   # JetPack 6 aarch64 지원
ollama pull exaone3.5:2.4b
sudo systemctl enable --now ollama              # 부팅 시 자동 기동
```

### F4. online 측정 빈도 — 확정

**outer 루프 (웨이크워드 활성화 직후) 1회**. inner 채팅 루프 안에서는 재측정 없음.
예외: STT/LLM 호출이 네트워크 예외를 던지면 그 자리에서 1회 재프로브 후 강등 (§3 graceful degradation).

### F5. warm-up 정책 의미 + 결정

**의미**:
- "한쪽만 로드": 부팅 시 `is_online()` 1회 측정 → True면 Groq 쪽만 (Groq STT는 사실 로드할 모델 없음, API 키 점검만), False면 로컬 whisper + Ollama 모델만 메모리에 미리 로드. 반대편은 lazy.
- "양쪽 다 로드": 양쪽 백엔드 + 모델을 부팅 시 전부 메모리에 적재. 네트워크 끊기면 즉시 폴백 가능하지만 메모리 약 2GB 상시 점유.

**8GB 시스템에서 양쪽 다 로드는 비현실적**. 결정:
- 부팅 시 `is_online()` 1회 측정
- **online이면**: 로컬 whisper / Ollama 모델 **로드 안 함** (Groq API 키 + Ollama 데몬 응답 헬스체크만)
- **offline이면**: 로컬 whisper warm-up (현재 동작) + Ollama 모델 ping (`/api/generate`로 1토큰 생성해 메모리 적재)
- 운영 중 강등 발생 시 lazy load: 첫 폴백 호출에서 모델 로드 (콜드 스타트 한 턴은 늦어짐을 감수)

### F6. 오프라인 TTS — 어린아이 목소리

| 옵션 | 메모리 | 속도 (Orin Nano) | 한국어 | 어린아이 음성 | 비고 |
|---|---|---|---|---|---|
| **Coqui XTTS-v2** | ~2 GB VRAM | 1-2x realtime | ★★★★ | ✅ voice cloning | CLOVA `ndain`/`nhajun` mp3를 reference clip으로 클론 가능, 17개 언어 지원 |
| Piper TTS | ~50 MB | 5-10x realtime | ★★★ | ✗ (커뮤니티 한국어 voice 한정) | 압도적으로 빠르고 가볍지만 한국어 어린아이 voice 없음 |
| F5-TTS | ~2 GB | 1-2x realtime | ★★★★ | ✅ voice cloning | XTTS와 비슷, 신규 모델로 약간 더 자연스러움. 한국어 학습량은 XTTS가 더 검증됨 |
| OpenVoice v2 | ~1.5 GB | 2-3x realtime | ★★★ | ✅ voice cloning | 영어 외 발음 약점 보고 있음 |
| Bark | ~4 GB | 0.3x realtime (느림) | ★★★ | ✅ | 메모리/속도 모두 부담 |
| Korean glow-tts / VITS | ~200 MB | 5x realtime | ★★★★ | ✗ (성인 voice만) | 빠르지만 voice 고정 |

**권장: Coqui XTTS-v2 + CLOVA child voice clip을 reference로 사용**
- 이미 보유한 `ndain_final_test.mp3` 또는 `nhajun_final_test.mp3` (6초 이상이면 충분)을 reference로 등록 → 톤은 유지하면서 클론
- 메모리 2 GB는 LLM과 동시 적재가 빠듯 → **순차 사용 패턴**으로 운영:
  - LLM 추론 중에는 TTS 모델 unload
  - TTS 합성 중에는 LLM 응답 이미 생성 완료된 후
  - (실제로 우리 파이프라인은 LLM → TTS 순차 호출이라 자연스러움)
- 만약 메모리 부족이 실측에서 심각하면 **fallback: Piper + 한국어 성인 voice + 피치/속도 조정으로 어린아이 톤 모방**

추가 검토 거리: F5-TTS의 한국어 발음 품질을 XTTS와 비교 측정 후 갈아끼우는 것은 인터페이스 추상화 덕분에 1파일 교체로 가능.

### F7. TTS 추상화

`build_tts_backend(is_online=...)` 패턴은 이미 [jetson/expression/speaker.py](../jetson/expression/speaker.py)에 있어서 그대로 유지. 다만:
- 현재 offline TTS 경로는 gTTS(인터넷 필요)에 가까운 구현일 가능성이 있어 → **진정한 오프라인 백엔드(XTTS-v2)** 로 교체 필요
- 위치: `jetson/expression/tts/` 패키지로 재배치도 가능하지만, 현재 speaker.py 한 파일에 Clova가 들어있음. STT/LLM 리팩터 마무리 후 별도 단계에서 정리.

---

## 2. 새 모듈 구조 (확정)

```
jetson/
├─ core/
│  ├─ coordinator.py            ◀ 메인 플로우 (얇아짐)
│  ├─ network.py                ◀ network_probe.py 이전 (is_online)
│  │
│  ├─ stt/                      ◀ 신규
│  │  ├─ __init__.py            ◀ STTBackend, STTResult, build_input_event re-export
│  │  ├─ base.py                ◀ STTBackend Protocol + STTResult dataclass
│  │  ├─ local_whisper.py       ◀ 기존 stt_whisper.py 이전 (openai-whisper)
│  │  ├─ groq_whisper.py        ◀ 신규 (Groq audio.transcriptions API)
│  │  └─ factory.py             ◀ build_stt_backend(online) → STTBackend
│  │
│  └─ llm/                      ◀ 신규
│     ├─ __init__.py
│     ├─ base.py                ◀ LLMBackend Protocol
│     ├─ prompt.py              ◀ BASE_SYSTEM_PROMPT, schema 주입, validator, conversation policy
│     ├─ groq_llm.py            ◀ Groq llama-3.1-8b-instant
│     ├─ ollama_llm.py          ◀ 신규 (Ollama HTTP, exaone3.5:2.4b)
│     └─ factory.py             ◀ build_llm_backend(online) → LLMBackend
│
└─ expression/
   ├─ wake_word.py              (그대로, 항상 offline)
   ├─ microphone.py             (그대로)
   ├─ speaker.py                (그대로 — 단계 1에서는 손대지 않음)
   ├─ mouth_servo.py            (그대로)
   └─ stt_whisper.py            ◀ 폐기 (core/stt/local_whisper.py로 이동)
```

레거시 정리:
- `jetson/cloud/groq_client.py` → 분해 후 `jetson/cloud/` 디렉토리는 **비움 (또는 삭제)**.
  Groq HTTP wrapper는 `core/llm/groq_llm.py` 안에 통합.
- `jetson/core/brain/network_probe.py` → `jetson/core/network.py`로 이동, 기존 위치는 re-export shim 유지(brain 내부 import 안 끊기게).
- `jetson/core/coordinator.py`의 `LocalLLM` 더미 클래스 → 삭제.

---

## 3. 인터페이스 정의

### `core/stt/base.py`
```python
@dataclass(frozen=True)
class STTResult:
    text: str
    language: str

class STTBackend(Protocol):
    name: str   # "groq-whisper-large-v3-turbo" / "local-whisper-small"
    def transcribe(self, wav_path: str, *, language: str = "ko") -> STTResult: ...
    def warm_up(self) -> None: ...   # local: 모델 로드 / groq: API 키 점검 핑
```

### `core/llm/base.py`
```python
class LLMBackend(Protocol):
    name: str   # "groq-llama-3.1-8b" / "ollama-exaone3.5-2.4b"
    def build_action(
        self,
        stt_text: str,
        *,
        session_id: str,
        history: list[dict],
        in_chat_mode: bool,
    ) -> dict: ...   # ACTION_JSON 스키마에 맞는 dict
    def warm_up(self) -> None: ...   # ollama: 1토큰 핑 / groq: 연결 점검
```

### `core/stt/factory.py`
```python
def build_stt_backend(online: bool) -> STTBackend:
    if online:
        return GroqWhisperBackend(model="whisper-large-v3-turbo")
    return LocalWhisperBackend(model_size="small", language="ko")
```

### `core/llm/factory.py`
```python
def build_llm_backend(online: bool) -> LLMBackend:
    if online:
        return GroqLLMBackend(model="llama-3.1-8b-instant")
    return OllamaLLMBackend(model="exaone3.5:2.4b", host="http://127.0.0.1:11434")
```

`prompt.py`는 두 LLM 백엔드 공통: `build_system_prompt`, `parse_and_validate_action_json`, `apply_conversation_policy`, `offline_action_json` 헬퍼.

---

## 4. 새 메인 플로우 (`coordinator.py`)

```
main()
 ├─ wakeword listener build (항상 offline)
 ├─ initial_online = is_online()
 ├─ if initial_online:
 │    pre-create groq backends (light, no model load)
 │  else:
 │    stt_backend.warm_up() / llm_backend.warm_up()   (heavy)
 └─ run_live_pipeline(...)

run_live_pipeline()
  outer loop:
    ├─ activation = wakeword_listener.wait_for_wake_word()
    ├─ online = is_online()                              ◀ 1회
    ├─ stt_backend = build_stt_backend(online)
    ├─ llm_backend = build_llm_backend(online)
    ├─ tts_backend = build_tts_backend(is_online=online, ...)
    ├─ greeting → tts_backend.speak_with_lipsync(...)
    │
    └─ inner loop (in_chat_mode):
        ├─ wav = record_to_wav(...)
        ├─ stt_result = stt_backend.transcribe(wav)      ◀ 분기 X
        ├─ input_event = build_input_event(stt_result, ...)
        ├─ action_json = llm_backend.build_action(...)   ◀ 분기 X
        ├─ history append + session log
        ├─ tts_backend.speak_with_lipsync(reply_text)
        └─ intent 분기 (chat / standby / pick_place / move / stop) — 기존 그대로
```

→ 현재 [coordinator.py:109-125 `_build_turn_services`](../jetson/core/coordinator.py#L109-L125), [255-268 if online 분기](../jetson/core/coordinator.py#L255-L268), [85-106 `LocalLLM` stub](../jetson/core/coordinator.py#L85-L106)이 모두 사라지고 백엔드 메서드 호출로 평탄화됨.

---

## 5. Graceful Degradation (1단계만)

inner 루프에서 `stt_backend.transcribe()` 또는 `llm_backend.build_action()`이 **네트워크 예외**(timeout / connection error / 5xx)를 던지면:

1. 그 자리에서 `is_online()` 즉석 재프로브
2. False면 그 turn에 한해 오프라인 백엔드로 강등 (lazy load) + 다음 outer 사이클부터는 새 측정 결과로 재선택
3. True인데도 실패 → 일시 장애로 간주, 1회 재시도 후 실패 시 turn skip + 사용자에게 "잠시 후 다시 말씀해주세요" 멘트 (이때 TTS는 현재 backend 그대로 사용)

**다른 종류 예외**(GPU OOM, 파일 IO 등)는 위로 던져서 정상 에러 흐름.

→ 백엔드 내부에 다단 폴백을 넣지 않음. fallback 책임은 coordinator에만.

---

## 6. 구현 순서 (체크리스트 형태)

각 단계 끝마다 동작 확인 후 다음 단계로.

- [ ] **단계 1 — 디렉토리 골격**
  - `jetson/core/stt/{__init__.py, base.py, factory.py}` 빈 껍데기
  - `jetson/core/llm/{__init__.py, base.py, factory.py}` 빈 껍데기
  - `jetson/core/network.py` (network_probe.py 이전, 기존 위치는 re-export)
- [ ] **단계 2 — 기존 코드 이전 (기능 변화 0)**
  - `jetson/expression/stt_whisper.py` → `jetson/core/stt/local_whisper.py`로 이전, `LocalWhisperBackend` 클래스화
  - `jetson/cloud/groq_client.py` 분해:
    - 프롬프트/스키마/validator → `jetson/core/llm/prompt.py`
    - Groq HTTP → `jetson/core/llm/groq_llm.py` 안 `GroqLLMBackend`
  - 기존 import 전부 갱신, **현재 동작과 동일** 검증
- [ ] **단계 3 — coordinator 평탄화**
  - `_build_turn_services`, inner-loop if online, `LocalLLM` 클래스 삭제
  - `build_stt_backend(online)` / `build_llm_backend(online)` / `build_tts_backend(is_online)` 3개 호출로 단순화
  - 기능 변화는 여전히 0 (online 시 Groq, offline 시 로컬 whisper + 기존 stub LLM)
- [ ] **단계 4 — Groq Whisper 라이브**
  - `core/stt/groq_whisper.py` (`GroqWhisperBackend`) 구현
  - `build_stt_backend(online=True)` → `GroqWhisperBackend` 반환
  - 실측: 한국어 인식률, latency, 비용 추적
- [ ] **단계 5 — Ollama 라이브**
  - `ollama` 설치 + `exaone3.5:2.4b` pull + systemd enable
  - `core/llm/ollama_llm.py` (`OllamaLLMBackend`) 구현, JSON 모드 사용
  - schema validator 통과 검증, JSON 실패 시 1회 retry, 그래도 실패 시 `offline_action_json`
- [ ] **단계 6 — graceful degradation 1단계**
  - coordinator inner 루프에 try/except + 재프로브 + 강등 로직
  - 폐기된 fallback chain 코드 (`groq_client.build_action_json_from_stt`의 cloud→local→stub) 정리
- [ ] **단계 7 — 오프라인 TTS (별도 단계)**
  - `core/tts/` 또는 `expression/tts/`로 speaker.py 분해
  - XTTS-v2 백엔드 + CLOVA child voice (`ndain_final_test.mp3`) 를 reference로 등록
  - 메모리 사용량 실측 (LLM 동시 적재 가능 여부)
- [ ] **단계 8 — 문서/로그**
  - `09_project_flow_overview.md` 새 구조 반영해서 갱신
  - `WORKLOG.md` 항목 추가 + commit/push

---

## 7. 잠재 리스크

| 리스크 | 영향 | 대응 |
|---|---|---|
| Orin Nano 8GB 메모리 부족 (Ollama + XTTS 동시) | 스왑 발생 → 응답 수 초 지연 | 단계 5/7에서 실측, LLM 추론 후 unload (Ollama `keep_alive=0`) → TTS 적재 패턴 검토 |
| Ollama JSON 모드가 schema 외 필드 누락 | action.schema 검증 실패 | retry 1회 + 실패 시 `offline_action_json` (현재 동일 정책) |
| Groq Whisper turbo 한국어 인식률 부족 | UX 저하 | `whisper-large-v3` 풀모델로 백엔드 model 옵션만 변경, 또는 CLOVA Speech로 교체 |
| EXAONE 라이센스 (비상업) | 상업화 차단 | 상업화 단계 진입 시 Qwen2.5 3B 또는 Llama 3.2 3B로 교체 (Apache 2.0 / Llama 라이센스) |
| Ollama 데몬 부팅 지연 | 첫 turn 콜드 스타트 | systemd `--now` + warm-up 1토큰 핑 |

---

## 8. 다음 액션

이 문서 검토 → 확인되면 **단계 1 ~ 3** (구조 잡기 + 기존 코드 이전 + coordinator 평탄화) 부터 구현 시작. 기능 변화 없이 리팩터만 들어가는 단계라 안전하게 갈 수 있음.
