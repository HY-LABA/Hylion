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

### [x] 02_dgx_setting

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

### [x] 03_smolvla_test_on_orin

- 목표: Orin 위에서 사전학습 smolVLA 추론 동작 확인

### [ ] 04_infra_setup

- 목표: leftarmVLA 사이클 진입 가능한 4-노드 인프라 셋업 — devPC + DataCollector(신규) + DGX + Orin
- 배경: smolVLA 학습 정확도는 시연장 환경 미러링에 크게 의존. DGX·Orin 은 시연장과 떨어져 있어 시연장 인근의 데이터 수집 전용 노드(DataCollector) 가 필요. 결과적으로 데이터 수집(DataCollector) → 학습(DGX) → 추론(시연장 Orin) 의 분리된 흐름이 됨.
- 주요 작업:
  - orin/ 디렉터리 구조 정리 (lerobot inference-only 트리밍, tests/·config/·checkpoints/ 신규, calibration/ 제거)
  - dgx/ 디렉터리 구조 정리 (orin/scripts/run_teleoperate.sh 이관 등)
  - DataCollector 노드 신규 셋업 (하드웨어·OS·venv·lerobot 의존성 결정 + 디렉터리 신규)
  - 환경 점검 게이트 스크립트 (시나리오 점검: 카메라 인덱스·flip / SO-ARM 포트 / venv. first-time / resume 두 모드)
  - 시연장 환경 미러링 가이드 (사용자 책임 + 기록 위주)
  - DataCollector → DGX 데이터 전송 경로 + DGX → Orin ckpt 전송 경로 모두 동작 확인
- 결정사항 (04 진행 중 확정):
  - DataCollector 노드 정체 (별도 PC vs 기존 노트북 vs 시연장 PC)
  - 데이터 전송 방식 (HuggingFace Hub vs rsync 직접 vs 둘 다)
  - 시연장 미러링 검증 깊이 (육안 + 사진 vs 자동 검증 스크립트)

### [ ] 05_leftarmVLA

- 목표: 단일 팔 (left arm, 휴머노이드 토르소 부착) 기준 smolVLA 파인튜닝 → Orin 배포까지 한 사이클 완주
- 주요 작업:
  - 휴머노이드 토르소 부착 SO-ARM (left arm) calibration 및 작업 영역 재정의
  - 풀 6 DOF 유지로 데이터 수집(DataCollector) → 학습(DGX) → 시연장 Orin 배포까지 한 사이클 완주 (자유도 축소는 적용하지 않음, 02 TODO-11 결론)
- 고려사항:
  - 표준 SO-ARM 책상 mount 와 다른 좌표계·관절 한계 (어깨가 토르소에 부착되어 가용 작업 공간 변화)
  - 사전학습 smolvla_base 가 표준 SO-ARM 분포로 학습된 점 → 도메인 시프트 존재
  - 04 에서 셋업된 DataCollector 의 시연장 미러링 환경에서 데이터 수집 (학습 정확도의 핵심)
- 위치: 본 마일스톤은 "left arm 단일팔 사이클 자체의 검증·데모" 가 목적이며, 07 양팔 학습의 사전 단계가 아니다 (07 은 양팔 데이터로 처음부터 학습).

### [ ] 06_biarm_teleop_on_dgx

- 목표: 양팔 (left + right SO-ARM, 토르소 부착) teleoperation 데이터 수집 환경 구축 (DataCollector 기준)
- 주요 작업:
  - 양팔 teleop 동작 검증 (좌·우 leader → 좌·우 follower)
  - 카메라 3대 구성 확정 및 데이터 수집 (손목 좌·우 2대 + 전체 조망 1대, base 미포함)
- 결정사항 (06 진행 중 확정):
  - 데이터셋 카메라 키 컨벤션: `observation.images.{wrist_left, wrist_right, overview}` (또는 동등)
  - `observation.state` / `action` 12 DOF 매핑: `[left_6, right_6]` 단일 키 vs 좌·우 분리 키
- 고려사항:
  - 카메라 3대 구성은 smolvla_base 사전학습 분포 (보통 1~2 카메라) 와 다름 → 07 학습 시 expert 학습에 가장 큰 영향
  - 손목 카메라는 그리퍼 동작을 가까이서 촬영 → 사전학습된 SmolVLM2 vision encoder 분포와 차이
  - 양팔이 토르소에 부착된 상태에서 teleop 시 좌·우 팔 충돌 회피 작업 영역 정의 필요

### [ ] 07_biarm_VLA

- 목표: 양팔 데이터로 smolVLA 파인튜닝 → 양팔 추론 동작 검증
- 주요 작업:
  - 06 에서 수집한 양팔 12 DOF + 카메라 3대 구성 데이터로 smolVLA 파인튜닝 (단일팔에서 전이하지 않고 양팔 데이터로 처음부터 학습)
- 고려사항:
  - SmolVLA `max_state_dim=32` / `max_action_dim=32` padding 으로 12 DOF 양팔 수용 가능 (코드 차원 확인 완료, `docs/lerobot_study/03_smolvla_architecture.md` §A·§E 참조)
  - 카메라 3대 → smolvla_base 사전학습 분포 차이로 vision/connector 까지 푸는 풀 파인튜닝(S3) 검토 필요할 수 있음. 첫 시도는 표준 파인튜닝(S1) 부터.
  - 토르소 부착 양팔 좌표계가 사전학습 분포와 다름 → 도메인 시프트 큼. 학습 step 수 / 데이터 양 충분히 확보 필요.
- 비상 옵션:
  - 잘 안되면 머리 위에 더듬이 카메라 다는 것 고려 (조망 카메라 보강)

### [ ] 08_biarm_deploy

- 목표: 양팔 VLA 정책을 시연장 Orin 에 배포하여 최종 데모 가능 상태로 완성
- 고려사항:
  - 카메라 3대 + 양팔 SO-ARM 보드 2대 + 토르소 측 추가 USB 가능성 → Orin USB 포트 / 허브 구성 점검 (02_hardware 와 연동)
  - `num_steps` / `n_action_steps` 튜닝으로 Orin 추론 latency 최적화 (`docs/lerobot_study/03_smolvla_architecture.md` §F·§E 참조)
