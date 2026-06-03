# tui

Orin에서 직접 실행하는 3단계 TUI 런처.
`rich` 라이브러리 기반, 모듈식 구조.

## 실행

```bash
# Orin에서 (SSH 접속 후)
cd ~/Hylion
python3 -m tui.main
```

## 파일 구조

```
tui/
├── main.py                   # 진입점. stage 순서 제어
│
├── stages/
│   ├── config.py             # 경로·환경변수·공통 타입 (CheckResult, Status)
│   ├── stage1_preflight.py   # Stage 1 — 사전 점검
│   ├── stage2_verify.py      # Stage 2 — 실제 대화 검증 + 로그 스트리밍
│   └── utils/
│       └── checks.py         # Stage 1 개별 점검 함수 모음
│
├── ui/
│   └── panels.py             # rich Panel/Table 공통 컴포넌트
│
├── scenarios/                # Stage 3용 시나리오 정의 (미구현)
│
└── legacy/                   # 이전 shell 스크립트 (참조용)
    ├── run_coordinator.sh    # coordinator tmux 재시작 시 사용
    ├── live_monitor.sh
    ├── preflight.sh
    └── hylion-tui.py
```

## Stage 개요

### Stage 1 — Preflight 점검
FAIL 항목이 있으면 Stage 2 진입을 차단한다.

```
프로세스  coordinator 중복 실행 여부 (pgrep 'jetson.core.coordinator')
하드웨어  udev 심볼릭 링크 (/dev/so_arm_left, so_arm_right)
          마이크(P5HD) + 스피커 감지
          Jetson.GPIO (서보 접근)
소프트웨어 웨이크워드 모델 파일 존재
          venv (expression / arm)
          gesture 데이터
네트워크  인터넷 (Groq + Clova 도달)
          API 키 (GROQ_API_KEY, Naver Clova)
```

### Stage 2 — 실제 대화 검증
coordinator를 tmux 세션(`hylion-coordinator`)으로 기동하고,
stdout 로그와 session JSONL을 실시간으로 표시한다.
"Hey Hylion → 명령" 을 말해 각 컴포넌트(웨이크워드·STT·LLM·TTS)가
정상 동작하는지 체크한다.  Enter로 Stage 3 진행.

### Stage 3 — 시나리오 실행 (미구현)
`scenarios/*.yaml`에 정의된 시나리오를 순서대로 실행한다.

## 의존성

```
Orin:  pip install rich   # TUI
       tmux               # coordinator detach 실행
```

## 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `HYLION_ORIN_PROJECT` | `~/Hylion` | 프로젝트 루트 경로 |
| `HYLION_WAKEWORD_DEVICE_KEYWORD` | `P5HD` | 마이크 디바이스 키워드 |
| `HYLION_MOUTH_SERVO_PIN` | `7` | 입 서보 GPIO 핀 번호 |
| `HYLION_SPEAKER_SINK_KEYWORD` | `usb` | PulseAudio sink 키워드 |
