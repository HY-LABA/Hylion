---
name: project-hylion-overview
description: Hylion Physical AI 로봇 프로젝트의 핵심 구조, 트랙 분리, 그리고 사용자의 위치
metadata:
  type: project
---

**Hylion (하이리온) Physical AI 로봇** — 한양대 Biz Lab LABA5 프로젝트. NVIDIA GTC 2026 RobOlaf 레퍼런스. 약 1m 높이 쇼형 휴머노이드. 13주 개발(현재 v12 기획서, 2026-03 작성).

**핵심 구조**:
- **하반신**: Berkeley Humanoid Lite (BHL) 원본 — 5DOF × 2, 3D프린트 사이클로이드 기어박스 + BLDC, NUC + 4×CAN 250Hz, xanmod RT
- **상반신**: 커스텀 — SO-ARM101 × 2 + 캐릭터 머리, 토르소 ~25cm
- **컴퓨팅**: DGX Spark(학습) + Orin Nano Super(SmolVLA·MediaPipe·대화) + NUC(BHL lowlevel·Walking RL) + ESP32(낙상 감지)
- **듀얼 트랙**: Track A(상체, δ1·ε1·ε2 부분) + Track B(하체, δ2·δ3·ε2 부분) 병렬, Week 9 합류

**핵심 리스크**: 탑헤비 — BHL 원본보다 상부가 무거워서 직립 안정성과 sim-to-real gap이 최대 우려. Week 0 IsaacLab 파라메트릭 직립 테스트가 Go/No-Go 게이트.

**Why**: 검증된 오픈소스 컴포넌트(BHL·SO-ARM·SmolVLA·LeRobot·IsaacLab)의 통합이 핵심 설계 원칙("어셈블을 잘 하자"). 13주 안에 완성하려면 커스텀 최소화 + 시뮬 선행 + 듀얼 트랙이 필수.

**How to apply**: 
- 사용자가 BHL/하드웨어 관련 질문을 하면 이 맥락(탑헤비, 커스텀 상부, BHL 원본 변경 금지 원칙)에서 답할 것
- "brain쪽 작업"이라고 하면 [[user-role]] 참고 — STT/LLM/TTS, 상태머신, SmolVLA 인터페이스 영역
- 기획서 원본은 [docs/01_하이리온_Physical_AI_로봇_기획서.md](../docs/01_하이리온_Physical_AI_로봇_기획서.md). 다른 docs/ 파일들은 분야별 상세 문서
- 현재 시점이 어디인지 확인 필요할 때 git log + 최근 작성 docs 확인 (정적 기록이라 드리프트 가능)
