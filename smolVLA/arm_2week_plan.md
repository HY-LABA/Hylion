# Bi-arm VLA 최종 프로젝트 로드맵

> 기준일: 2026-04-21 | 마감: 2026-05-06 | 역할: δ1 (팔 하드웨어 오너, Track A 리드)

---

## 최종 목표 상태 (2026-05-06)

**양팔 SO-ARM 하드웨어에서 Bi-arm VLA 가 Orin 위에서 추론·실행되고, DGX 에서 학습된 정책이 배포되어 데모 가능한 상태.**

---

## 장비 역할 분담 (병렬 운영)

- `devPC`: 코드 정리/문서화/설정 관리/배포 패키지 준비
- `Orin`: 배포 대상, 실행/검증 전용 (실제 SO-ARM 연결 테스트 포함)
- `DGX Spark`: 학습/튜닝 주력 환경
- `교수님 연구실 PC (Windows + GPU)`: 백업/오버플로우 전용 (DGX 병목 시 학습 분산)

운영 원칙:
- 실시간 제어 및 현장 검증은 Orin 기준으로 판단한다.
- 학습 성능 실험은 DGX 기준으로 판단하며, 백업 시에만 연구실 PC 를 동원한다.
- 코드는 devPC 에서 정리 → Orin/DGX 로 배포한다.

---

## 레퍼런스

### 관련자료

| 항목 | 링크 |
|------|------|
| lerobot 레포 | `github.com/huggingface/lerobot` |
| SmolVLA 블로그 | `huggingface.co/blog/smolvla` |
| LeRobot Hub | `huggingface.co/lerobot` |

### 논문

| 항목 | 링크 |
|------|------|
| 기초 VLA 논문 (1세대) | `RT-1: Robotics Transformer for Real-World Control at Scale (arXiv:2212.06817)` |
| 기초 VLA 논문 (2세대) | `RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control (arXiv:2307.15818)` |
| SmolVLA 논문 | `SmolVLA: Efficient Vision-Language-Action Model trained on LeRobot Community Data (arXiv:2506.01844)` |
| 트랜스포머 논문 | `Attention is All You Need (Vaswani et al., 2017)` |

---

## 진행 마일스톤

### [x] 00_orin_setting

- 목표: Orin 환경 초기 셋업 — JetPack, venv, lerobot 설치까지 완료
- DOD: Orin 에서 lerobot 패키지 임포트 및 smolVLA 모델 로딩 성공
- 결정사항:
  - Ubuntu vs Windows? → **Ubuntu 필수** (lerobot Dynamixel USB 가 WSL2 에서 불안정, native Ubuntu 권장)

### [x] 01_teleoptest

- 목표: SO-ARM 단일 쌍 (follower 1 + leader 1) teleoperation 동작 검증 + 카메라 인식
- DOD: leader → follower 실시간 추종 육안 확인, 카메라 2 대 스트림 정상 출력
- 결정사항:
  - 리더 암 새로 사야 하나? → **랩미팅 후 교수님께 주문 요청** (Week 2 단일 팔 검증 → Week 2 말 양팔 전환 Go/No-Go)

### [ ] 02_dgx_setting

- 목표: DGX Spark 학습 환경 구축 + 양팔 / 자유도 / 병렬학습 가능성 결정
- 학습 (Claude 와 대화로 선행 이해):
  - smolVLA 구조
  - 데이터셋 구조
  - 허깅페이스 모델 선택 기준
  - 파인튜닝 가능성
- 작업 (실제 산출물):
  - Bootcamp → HYlion 으로 레포 이관 (4단계 새 레포 이관과 동일)
  - DGX 실측 (스펙·가용 자원 확인)
  - 환경관리 / 버전 호환성 결정
  - 학습 환경 세팅
  - 배포 환경 세팅
- 결정사항:
  - Walking RL 과 병렬학습 가능 여부?
  - 자유도 낮추기 가능 여부?
  - 양 팔 가능 여부?

### [ ] 03_smolvla_test_on_orin

- 목표: Orin 위에서 사전학습 smolVLA 추론 동작 확인

### [ ] 04_leftarmVLA

- 목표: 단일 팔 (left arm) 기준 smolVLA 파인튜닝 → Orin 배포까지 한 사이클 완주
- 주요 작업:
  - 자유도 낮추기까지 (02 결정사항 적용)

### [ ] 05_biarm_teleop_on_dgx

- 목표: 양팔 teleoperation 데이터 수집 환경 (DGX 기준) 구축

### [ ] 06_biarm_VLA

- 목표: 양팔 데이터로 smolVLA 파인튜닝 → 양팔 추론 동작 검증
- 비상 옵션:
  - 잘 안되면 머리 위에 더듬이 카메라 다는 것 고려

### [ ] 07_biarm_deploy

- 목표: 양팔 VLA 정책을 Orin 에 배포하여 최종 데모 가능 상태로 완성
