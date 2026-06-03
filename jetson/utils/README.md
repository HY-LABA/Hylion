# jetson/utils

jetson 레이어 전반에서 공유하는 횡단 유틸리티 모음.
특정 도메인(arm/core/expression)에 속하지 않는 공통 기능을 담는다.

```
utils/
├── env_secrets.py   # API 키 등 환경변수 로딩
│                    #   .env 파일 탐색 및 캐싱
│                    #   사용처: core/llm/groq_llm.py, core/stt/groq_whisper.py
│
├── network.py       # 인터넷 연결 상태 probe
│                    #   Google/Cloudflare/Naver 소켓 연결 시도
│                    #   사용처: utils/online_gate.py
│
└── online_gate.py   # 온라인/오프라인 sticky 상태 머신
                     #   network.py probe 결과를 60초 캐싱 (매 호출마다 probe 방지)
                     #   Groq 실패 시 report_online_failure() → 60초 오프라인 강제
                     #   사용처: core/coordinator.py
```
