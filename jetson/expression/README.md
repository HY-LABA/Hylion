# jetson/expression

Hylion의 감각·표현 레이어.
마이크 입력, 웨이크워드 감지, TTS 음성 출력, 입 서보 립싱크를 담당한다.
`~/Hylion/.venv` (torch + whisper + openwakeword 등) 위에서 동작한다.

```
expression/
├── wake_word.py        # 웨이크워드 감지
│                       #   openwakeword 모델로 "Hey Hylion" / "Stop" 감지
│                       #   P5HD USB 마이크 44.1kHz 스트림 수신
│                       #   감지 시 coordinator 에 콜백 전달
│
├── microphone.py       # 마이크 녹음 및 오디오 처리
│                       #   USB 마이크 자동 선택 (device keyword 매칭)
│                       #   PCM16 변환, RMS 게이팅 (무음 구간 필터링)
│                       #   WAV 파일 저장 (~/Hylion/data/episodes/)
│
├── speaker.py          # TTS 음성 출력
│                       #   Clova TTS (온라인) / gTTS (오프라인 fallback)
│                       #   USB 스피커 자동 감지 (pactl sink 스캔)
│                       #   speak_with_lipsync() : 재생 + 입 서보 동기화
│
├── mouth_servo.py      # 입 서보 제어 (MG90S, GPIO pin 33)
│                       #   TTS 오디오 진폭에 맞춰 서보 각도 실시간 제어
│                       #   RPi.GPIO 기반, Jetson GPIO 호환
│
├── factory.py          # expression 컴포넌트 팩토리
│                       #   하드웨어 가용 여부에 따라 실제/mock 컴포넌트 선택
│
└── requirements.txt    # expression 레이어 Python 의존성 목록
```

## 사용 venv

| venv | 경로 | 용도 |
|---|---|---|
| 메인 | `~/Hylion/.venv` | torch, whisper, openwakeword, tflite, onnxruntime, sounddevice, groq |

## 주요 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `HYLION_WAKEWORD_DEVICE_KEYWORD` | `P5HD` | 웨이크워드용 마이크 키워드 |
| `HYLION_WAKEWORD_SAMPLE_RATE` | `44100` | 웨이크워드 스트림 샘플레이트 |
| `HYLION_MIC_SAMPLE_RATE` | `44100` | 녹음 샘플레이트 |

## 오디오 장치 선택 방식

- **마이크**: `sounddevice` 장치 목록에서 `HYLION_WAKEWORD_DEVICE_KEYWORD` 키워드 매칭
- **스피커**: `pactl list short sinks` 결과에서 `usb` 포함 sink 자동 감지
  - USB 스피커 미감지 시 수동 등록: `pactl load-module module-alsa-sink device=hw:3,0`
