# SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics

> **논문 출처**: arXiv:2506.01844v1 [cs.LG] (2025년 6월 2일)  
> **저자**: Mustafa Shukor, Dana Aubakirova, Francesco Capuano 외 (Hugging Face, Sorbonne University, valeo.ai, ENS Paris-Saclay)

---

## 📌 핵심 요약 (Abstract)

VLM(Vision-Language Model)을 로보틱스에 적용하는 VLA(Vision-Language-Action) 모델은 기존에 수십억 개의 파라미터를 가진 거대 모델 위주였으나, 이는 높은 훈련 비용과 실세계 배포의 어려움을 초래했다.

**SmolVLA**는 이를 해결하기 위해 제안된 **소형, 효율적, 커뮤니티 중심** VLA 모델이다.

### 주요 특징
- 단일 GPU로 학습 가능, 일반 소비자용 GPU 또는 CPU에서 배포 가능
- **비동기 추론(Asynchronous Inference)** 스택 도입으로 지연 없는 빠른 제어 실현
- 10배 큰 모델과 비교해도 경쟁력 있는 성능
- 모든 코드, 사전학습 모델, 학습 데이터 공개(오픈소스)

---

## 🏗️ 모델 아키텍처

SmolVLA는 두 가지 주요 컴포넌트로 구성된다.

### 1. Vision-Language Model (VLM) 백본

- **SmolVLM-2** 사용: 멀티이미지 및 비디오 입력에 최적화된 효율적 모델
- **SigLIP** 비전 인코더 + **SmolLM2** 언어 디코더 구조
- 입력: RGB 이미지 시퀀스, 언어 명령어, 로봇 감각운동 상태(sensorimotor state)
- 토큰 셔플링(Token Shuffling)으로 시각 토큰 수를 **프레임당 64개**로 제한

### 2. Action Expert (행동 전문가)

- **Flow Matching Transformer** 기반
- **Cross-Attention(CA) ↔ Self-Attention(SA) 교차 구조** 사용
  - CA: VLM feature를 key/value로 받아 action token과 교차 주의
  - SA: action token끼리 인과적(causal) 마스크로 상호 참조
  - 이 교차 구조가 CA 단독 또는 SA 단독보다 성능 우수
- 출력: action chunk $A_t = (a_t, a_{t+1}, \ldots, a_{t+n})$

### 효율화 설계 선택

| 기법 | 내용 |
|------|------|
| **레이어 스킵** | VLM 전체 레이어 L 중 첫 L/2 레이어만 사용 → 연산량 절반 |
| **타일링 미사용** | 글로벌 이미지만 사용, 시각 토큰 64개로 제한 |
| **축소된 hidden size** | Action Expert의 hidden size를 VLM의 0.75× 적용 |
| **소형 VLM 활용** | 대형 모델 대신 SmolVLM-2 사용 |

---

## 📦 사전학습 데이터 (Community Datasets)

### 데이터 구성

| 구분 | 수치 |
|------|------|
| 데이터셋 수 | 481개 |
| 에피소드 수 | 22,900개 |
| 프레임 수 | 10,600,000개 |

- 전부 **Hugging Face에서 수집된 커뮤니티 공개 데이터셋** 활용
- 기존 SOTA 대비 **최소 10배 이상 적은 데이터** 사용

### 데이터 정제 과정

1. **Task Annotation 정제**: Qwen2.5-VL-3B-Instruct 모델로 모호한 태스크 설명 자동 재생성
2. **카메라 시점 정규화**: 다양한 카메라 네이밍 규칙을 `OBS_IMAGE_1/2/3`으로 표준화

---

## ⚡ 비동기 추론 (Asynchronous Inference)

### 기존 방식의 문제

- **동기(Sync) 추론**: 전체 action chunk 실행 후 다음 관측 → 추론 중 로봇이 대기(idle) 발생

### SmolVLA의 해결책: Async 추론

- **RobotClient**와 **PolicyServer**를 분리
- action queue가 임계값 $g$ 이하로 떨어지면, 현재 chunk 실행 중에도 **비동기적으로 새 chunk 예측** 시작
- 근접 중복 관측(joint-space 유사도 기반)은 필터링하여 불필요한 서버 호출 방지

### 임계값 g에 따른 동작

| g 값 | 동작 |
|------|------|
| g = 0 | 완전 순차 처리, chunk 소진 후 다음 예측 → idle 발생 |
| g = 0.7 | 적절한 균형, idle 없이 안정적 제어 |
| g = 1 | 매 타임스텝 추론, 최대 반응성이지만 연산 비용 큼 |

### 성능 비교 (Pick-Place 태스크)

| 지표 | Sync | Async |
|------|------|-------|
| 평균 완료 시간 | 13.75s | **9.70s** (약 30% 빠름) |
| 60초 내 완료 횟수 | 9회 | **19회** |

---

## 🧪 실험 결과

### 시뮬레이션 (LIBERO 벤치마크)

| 모델 | 파라미터 | VLA 사전학습 | 평균 성공률 |
|------|---------|------------|-----------|
| Diffusion Policy | - | No | 72.4% |
| Octo | 0.09B | Yes | 75.1% |
| OpenVLA | 7B | Yes | 76.5% |
| π0 (Paligemma) | 3.3B | No | 71.8% |
| π0 | 3.3B | **Yes** | 86.0% |
| **SmolVLA** | **0.24B** | No | **82.75%** |
| **SmolVLA** | **0.45B** | No | **87.3%** |
| **SmolVLA** | **2.25B** | No | **88.75%** |

### 실세계 평가 (SO100 로봇)

| 모델 | Pick-Place | Stacking | Sorting | 평균 |
|------|-----------|---------|---------|------|
| ACT (단일 태스크) | 70% | 50% | 25% | 48.3% |
| π0 (3.5B) | 100% | 40% | 45% | 61.7% |
| **SmolVLA (0.45B)** | **75%** | **90%** | **70%** | **78.3%** |

> SmolVLA는 자신보다 7배 큰 π0를 실세계 평균 성능에서 앞섬

### 사전학습 및 멀티태스크 학습 효과

| 설정 | 평균 성공률 |
|------|-----------|
| 단일 태스크, 사전학습 없음 | 40% |
| 멀티 태스크, 사전학습 없음 | 51.7% |
| **멀티 태스크 + 커뮤니티 데이터 사전학습** | **78.3%** |

---

## 🔬 Ablation Study 주요 결과

### 어텐션 메커니즘 비교 (LIBERO)

| 설정 | 평균 성공률 |
|------|-----------|
| Cross-Attention만 | 79.0% |
| Self-Attention만 | 74.5% |
| **CA + SA 교차 (SmolVLA)** | **85.5%** |

### VLM 레이어 수 (N) 비교

| N (사용 레이어 수) | 평균 성공률 |
|-----------------|-----------|
| 8 | 75.0% |
| 16 | 78.5% |
| 24 | 79.5% |
| 32 (전체) | 80.3% |
| **16 (L/2, SmolVLA 기본)** | **78.5%** (연산 절반) |

→ 레이어 절반만 사용해도 성능 손실 최소화

### Flow Matching vs Regression

| 학습 목표 | 평균 성공률 |
|---------|-----------|
| **Flow Matching** | **80.25%** |
| Regression (L1) | 75.25% |

### Action Chunk 크기

| Chunk 크기 | 평균 성공률 |
|-----------|-----------|
| 1 | 50.0% |
| **10~50 (권장)** | **~80-84%** |
| 100 | 74.5% |

---

## 🤖 실험에 사용된 로봇 플랫폼

| 로봇 | 자유도 | 특징 |
|------|--------|------|
| **SO-100** | 6-DOF | 저비용 3D 프린팅 가능, 오픈소스 |
| **SO-101** | 6-DOF | SO-100 개선판, 더 정밀한 동작 |
| **Franka Panda** | 7-DOF | 고정밀 토크 제어, LIBERO 시뮬레이션 사용 |
| **Sawyer** | 4-DOF | Meta-World 시뮬레이터 사용 |

---

## ⚠️ 한계점 (Limitations)

1. **단일 로봇 타입 데이터**: 사전학습 데이터가 SO100 기반으로만 구성
2. **데이터 규모**: 약 23k trajectories (OpenVLA는 약 100만 개)
3. **모델 크기**: 0.5B 이하 → 스케일업 시 속도와 접근성 간 트레이드오프 필요
4. **VLM 백본 특성**: 문서 읽기/OCR 위주로 사전학습된 VLM이 로봇 환경에 최적이 아닐 수 있음
5. **멀티모달 공동 학습 미적용**: 로보틱스 데이터와 멀티모달 데이터 혼합 학습 미실시
6. **장기 태스크 한계**: 긴 horizon의 복잡한 태스크에서는 성능 저하 가능
7. **모방 학습 중심**: 강화학습(RL) 미적용 → 복잡 태스크 대응 능력 제한

---

## 🔗 관련 리소스

- **논문**: [arXiv:2506.01844](https://arxiv.org/abs/2506.01844)
- **모델 및 코드**: Hugging Face 공개 (LeRobot 프레임워크)
- **학습 프레임워크**: LeRobot (PyTorch 기반)
- **학습 설정**: 200,000 steps, batch size 256, AdamW (lr=1e-4), 4 GPU (사전학습) / 단일 GPU 가능
- **총 GPU 사용량**: 약 30,000 GPU hours
