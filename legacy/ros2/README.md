# ROS2 Legacy Inventory

목적: ROS2 폐기 결정 이후, 기존 ROS2 관련 파일을 안전하게 보관/추적한다.

기준일: 2026-04-21

## 기본 런타임 경로 (Non-ROS2)

- 기본 실행 진입점: `jetson/core/coordinator.py` (구현 예정, Non-ROS2 표준)
- 현재 임시 Brain 실행 경로: `jetson/core/brain/brain_main.py`
- 신규 구현 기본 원칙: ROS2 import 없이 동작해야 함

## 이동 완료

- `legacy/ros2/brain_node.py`

## ROS2 의존 파일 확정 목록

코드(실행 경로):

- `jetson/core/brain/action_router.py` (rclpy/std_msgs 의존)

코드(legacy 보관):

- `legacy/ros2/brain_node.py` (rclpy/std_msgs 의존)

문서(ROS2 중심 서술 포함):

- `docs/05_hylion_brain_architecture_and_topic_map.md` (상단에 legacy 안내 적용됨)
- `docs/smolvla_reference_and_architecture.md`
- `docs/01_하이리온_Physical_AI_로봇_기획서.md`

## 이관 예정 후보 (코드)

- `jetson/core/brain/action_router.py`
- `jetson/core/brain/brain_main.py` 내 ROS2 토픽 문구/경로

## 이관 예정 후보 (문서)

- `docs/smolvla_reference_and_architecture.md`
- `docs/01_하이리온_Physical_AI_로봇_기획서.md`

## 운영 원칙

- 신규 기능은 ROS2 의존 없이 구현한다.
- 기존 ROS2 파일은 삭제 대신 `legacy/ros2`로 이동한다.
- legacy 파일은 참조용이며 기본 런타임 경로에 포함하지 않는다.
