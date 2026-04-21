# Hylion

Non-ROS2(UDP 기반) 파이프라인을 기본 실행 기준으로 사용합니다.

## 기본 실행 기준

- 기본 아키텍처: Non-ROS2
- Jetson <-> NUC 통신: UDP
- 기준 계획 문서: `docs/07_non_ros2_pipeline_master_plan.md`
- ROS2 이력/정리 문서: `legacy/ros2/README.md`

## 현재 기본 런타임 경로

- 목표 진입점(표준): `jetson/core/coordinator.py`
- 현재 임시 Brain 루프: `jetson/core/brain/brain_main.py`

## 기본 실행 흐름

1. USB 마이크 입력 수집
2. Whisper STT로 텍스트 변환
3. LLM이 action JSON 생성
4. Orchestrator가 의도 분기
5. SmolVLA 실행 또는 BHL 실행 또는 답변 출력

## 원칙

- 신규 구현은 ROS2 의존을 추가하지 않습니다.
- ROS2 관련 파일은 삭제 대신 `legacy/ros2/`에 이관합니다.
