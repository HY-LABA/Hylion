# 하이리온 Physical AI 로봇 프로젝트 기획서 v12

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | HYlion Robot — 하이리온 Physical AI |
| 목표 | 한양대 하이리온 캐릭터 기반 쇼형 Physical AI 로봇 |
| 레퍼런스 | NVIDIA GTC 2026 RobOlaf (Jetson + 캐릭터 외장) |
| 전체 높이 | ~1m |
| 하반신 | Berkeley Humanoid Lite (BHL) 이족보행 플랫폼 |
| 상반신 | SO-ARM101×2 + 하이리온 캐릭터 머리 |
| 개발 기간 | 13주 (Week 0 포함) |
| 팀 | δ1·δ2·δ3 + ε1·ε2 |
| 개발 구조 | **듀얼 트랙** — Track A(상체) + Track B(하체) 병렬 진행 |

---

## 2. 설계 원칙

### 2.1 "어셈블을 잘 하자"

이 프로젝트는 검증된 오픈소스 컴포넌트의 통합이 핵심이다. 모든 설계 결정에서 다음 우선순위를 따른다:

1. 상용 구매 (서보, 센서, 보드, 배터리, PDB, BMS, DC-DC 컨버터)
2. 오픈소스 설계 그대로 사용 (BHL 다리, SO-ARM, IsaacLab 환경)
3. 3D 프린트로 제작 (BHL 액추에이터 기어박스, 마운트 브래킷)
4. 오픈소스 코드/모델 활용 (SmolVLA, Walking RL, MediaPipe, Whisper, ROS2)
5. 최소한의 커스텀 (토르소 브래킷, 머리 조형, 상태 머신)

### 2.2 소프트웨어 플랫폼 통일 원칙

| 영역 | 플랫폼 |
|------|--------|
| 시뮬레이션 | IsaacLab (USD) |
| 모델 포맷 | URDF → USD |
| VLA 모델 | SmolVLA (LeRobot 생태계) |
| 상태 머신 | ε1이 Week 0에서 smach/FlexBE 중 선정, Week 1에 공유 |
| BHL lowlevel | BHL 원본 C 코드베이스 (NUC) |

### 2.3 Sim-to-Real 전략

BHL 다리는 URDF·USD, IsaacLab 환경, sim-to-real 전이가 모두 검증되어 있다. 커스텀 상부는 시뮬에서 mass/CoM/inertia만 정확히 반영하면 되므로, 불확실성이 "상부 mass 영향"으로 한정된다.

**시뮬 선행 원칙:** 물리 부품이 도착하기 전에 시뮬레이션·소프트웨어·인프라를 최대한 선행한다. 부품 도착 시 조립 → 즉시 테스트로 직행할 수 있는 상태를 만든다.

### 2.4 듀얼 트랙 개발 구조

상체와 하체를 병렬로 개발하여 13주 내 완성 확률을 극대화한다.

```
Track A (상체): δ1(리드) + ε1 + ε2(부분)
  → 조작, 대화, 감정, 상태 머신, 상반신 통합

Track B (하체): δ2(리드) + δ3 + ε2(부분)
  → 다리 조립, Walking RL, sim-to-real, 보행 안정화

교차 역할:
  δ3: 양쪽 AI 설계·판단 (SmolVLA 아키텍처 결정 + Walking RL 환경 설계)
  ε2: 양쪽 평가/검증 (SmolVLA 평가 + sim-to-real 분석 + 데이터 수집)
```

두 트랙은 **Week 9에서 합류**하여 상체-하체 결합 후 풀 시나리오 통합으로 진행한다.

---

## 3. 시연 시나리오

발표 당일 시연의 전체 흐름. 이 시나리오가 모든 서브시스템의 요구사항을 결정한다.

```
1. 관객이 다가옴
   → 하이리온이 시선 추적으로 바라봄 (MediaPipe → 목 PID)

2. 인사
   → "안녕하세요" TTS + 손 흔들기 (precoded)
   → 감정: happy, LED 눈 + 입 서보 동기

3. 대화 → 물체 집기
   → 관객: "저 빨간 컵 줄 수 있어?"
   → LLM이 SmolVLA 트리거 결정 → 스타벅스 컵 pick-place
   → 관객: "텀블러도 줘봐" → 텀블러 pick-place
   → 관객: "인형도 줄 수 있어?" → 인형 pick-place

4. (보행 트랙) 대화하면서 걷기
   → 보행 중 SmolVLA 중단, precoded 팔 스윙
   → 멈추면 SmolVLA 재개
```

**시연 시나리오 B (보행 미달 시):** 받침대 고정 상태에서 1~3번 시연. Week 7에 준비.

---

## 4. SmolVLA 태스크 정의

### 4.1 물체 및 수집 조건

| 물체 | 에피소드 수 | 고정 방식 |
|------|------------|-----------|
| 스타벅스 테이크아웃 컵 (빈 컵+뚜껑) | 200개 | 테이블 마커 |
| 텀블러 | 200개 | 테이블 마커 |
| 하이리온 인형 | 200개 | 테이블 마커 |

- 총 600 에피소드 (시연 조건 특화 비율 60% 이상)
- 의도적 변형 축: 마커 내 위치(±3cm), 물체 회전(0°/90°/180°), 그리퍼 접근 방향(정면/측면)
- 에피소드마다 변형 조건 메타데이터 기록
- 테이블 높이·물체 위치: Week 1 SO-ARM 작업 공간 실측 후 확정
- 시연 당일 조건(동일 테이블, 동일 조명, 동일 카메라 위치) 에피소드를 전체의 60% 이상 유지

### 4.2 수집 전략: 미니 파인튜닝 피드백 루프

Week 2에 초기 30개를 수집하고 미니 파인튜닝으로 치명적 결함을 조기 발견한 뒤, Week 3부터 확정 전략으로 본격 수집한다. Week 3부터 ε2가 수집에 투입(δ1 인수인계 후).

수집 인수인계 프로토콜: δ1이 수집 프로토콜(조작 스타일, 접근 방향, 속도, 메타데이터 기록 방식)을 문서화하고 ε2에게 인수인계 세션 진행. ε2는 δ1 수집 영상을 시청하고 동일한 패턴을 훈련한 후 수집 시작.

### 4.3 2-Stage 파인튜닝 전략 (오픈소스 데이터 최대 활용)

```
Stage 1: LeRobot Hub SO-100 공개 pick-place 데이터 (수천 에피소드)
  → SmolVLA 사전 파인튜닝 (manipulation primitive 학습)

Stage 2: 자체 600 에피소드
  → Stage 1 모델에서 추가 파인튜닝 (시연 조건 특화)
```

공개 데이터가 카메라 위치와 물체가 달라도, 접근-그립-리프트 패턴을 사전 학습하면 자체 데이터 효율이 올라간다.

### 4.4 언어→동작 연결

- 온라인: LLM이 물체 종류 추출 → SmolVLA에 전달
- 오프라인 서바이벌: 키워드 기반 로컬 매칭 (Orin) — "컵"→starbucks_cup, "텀블러"→tumbler, "인형"→doll

---

## 5. 시스템 아키텍처

### 5.1 상태 머신

```
상태:
  IDLE          대기. 시선 추적만 동작
  TALKING       대화 파이프라인 활성화
  MANIPULATING  SmolVLA 실행 중. 대화 요청은 완료 후 처리
  WALKING       보행 중. SmolVLA 중단, precoded 팔 스윙
  LOW_BATTERY   SOC 20% 이하. 안전 자세, 대화만 가능
  EMERGENCY     비상정지. BHL 전원 차단, Orin 로그 유지

전환 규칙:
  WALKING 중 집기 명령    → WALKING 중단 → IDLE → MANIPULATING
  MANIPULATING 중 대화   → 완료 후 TALKING
  TALKING 중 보행 명령   → 발화 완료 후 WALKING
  어느 상태에서나 비상정지 → EMERGENCY
```

프레임워크: ε1이 Week 0에서 smach/FlexBE를 직접 평가·선정하고, Week 1 합의 미팅에서 공유.

### 5.2 상태별 프로세스-리소스 매핑

| 상태 | Orin GPU | Orin CPU | NUC | ESP32 | 네트워크 |
|------|----------|----------|-----|-------|----------|
| IDLE | 비어있음 | MediaPipe(CPU, 10fps) + ROS2 + 상태머신 + LED | BHL lowlevel 대기 | IMU 모니터링 | 없음 |
| TALKING | 없음 | 오디오 캡처 + ROS2 + TTS 재생 + LED + 입 서보 | BHL lowlevel 대기 | IMU | STT+LLM+TTS (Groq) |
| MANIPULATING | SmolVLA (TensorRT) | 카메라 캡처 + MediaPipe(CPU, 2~3fps) + ROS2 + LED | BHL lowlevel 대기 | IMU | LLM 대기(선택) |
| WALKING | 없음 | MediaPipe(CPU) + ROS2 + LED | Walking policy + CAN write | IMU + 낙상 감지 | 대화 시 STT+LLM |

핵심 원칙:
- MediaPipe는 항상 CPU 모드 (GPU는 SmolVLA 전용)
- MANIPULATING 중에도 MediaPipe 저주파(2~3fps) 유지
- STT/LLM/TTS 전부 클라우드 (Groq). 로컬 fallback은 Whisper tiny + 키워드 매칭
- TTS 재생·LED·입 서보는 Orin 전담 (보행 중 NUC의 실시간성 보장)

### 5.3 컴퓨팅 분배

| 보드 | 역할 |
|------|------|
| DGX Spark | SmolVLA 파인튜닝 + Walking RL 학습 |
| Orin Nano Super | SmolVLA 추론(TensorRT), MediaPipe(CPU), ROS2, 상태 머신, TTS, LED, 입 서보, SO-ARM Dynamixel |
| NUC (BeeLink N95) | Walking RL policy (C 코드), BHL lowlevel 제어(CAN). BHL 공식 문서 검증 구성, 4 CAN 버스 250Hz |
| ESP32 | 낙상 감지 HW 인터럽트 → MOSFET 전원 차단 |

```
[DGX Spark]
  SmolVLA 파인튜닝     Walking RL 학습
        ↓                    ↓
  Orin (TensorRT)       NUC (BHL lowlevel C)

[Orin]                 [NUC]                [ESP32]
SmolVLA 추론      ↔   Walking policy (C)    ← IMU (낙상 전용)
MediaPipe(CPU)         BHL CAN 통신          → MOSFET 전원 차단
ROS2 + 상태 머신       IMU (policy용)
네트워크 I/O
TTS/LED/입 서보
SO-ARM Dynamixel
```

**Orin↔NUC 통신:** Ethernet 직결 (ROS2 토픽). `/gait/cmd` (Orin→NUC), `/gait/status` (NUC→Orin).

### 5.4 네트워크

| 우선순위 | 연결 | 용도 |
|----------|------|------|
| 1차 | 5GHz 휴대폰 핫스팟 | STT + LLM + TTS |
| 2차 | 시설 WiFi | 핫스팟 장애 시 |
| 서바이벌 | 로컬 오프라인 | 아래 5.5절 참조 |

### 5.5 Fallback 계층 설계

**계층 1 — 스크립트 시연 모드 (발표 안전망):**
진행자가 관객 유도. 키워드 매칭 + 사전 녹음 오디오 재생.

**계층 2 — 오프라인 자율 모드:**
Whisper tiny (Orin) + 확장 키워드 사전 + 사전 Q&A 30개 + Piper TTS (경량 오픈소스).

### 5.6 인터페이스 명세

- Week 0: ε1 JSON 액션 스키마 초안 + δ3 ROS2 토픽 리스트 초안 + ε1 리소스 매핑표 초안
- Week 1: 전체 합의 미팅 → 인터페이스 + 리소스 할당 확정 (Orin↔NUC 토픽, U2D2 버스, 카메라 마운트 포함)
- Week 1 이후 변경 시 전체 공지 필수

### 5.7 U2D2 버스 분배

- U2D2 #1: 왼팔 SO-ARM 6개 (ID 1~6)
- U2D2 #2: 오른팔 SO-ARM 6개 (ID 7~12) + 목 XL430 2개 (ID 13~14)

Protocol 2.0 1Mbps 기준 8개 서보 sync read/write ~5ms 이내, 200Hz 제어 충분.

---

## 6. 팀 구성

### 6.1 정체성

| 멤버 | 정체성 | 트랙 | 소유권 |
|------|--------|------|--------|
| δ1 | 하드웨어 오너 | A(리드) | 상체 HW·토르소·SO-ARM·SmolVLA 실물 피드백·상하체 결합 |
| δ2 | 보행 시스템 오너 | B(리드) | 액추에이터~보행까지 E2E: 조립·전원·안전·BHL lowlevel·Walking RL 실행·NUC 배포 |
| δ3 | AI 인프라 오너 (**설계·판단 전담**) | A+B | SmolVLA 아키텍처·Walking RL 환경 설계·보상 함수·핵심 기술 결정. **학습 실행은 ε1/δ2** |
| ε1 | 데이터·대화·통합 오너 | A(리드) | SmolVLA 데이터·DGX 학습 실행·TensorRT·Orin 관리·상태 머신·최종 통합 |
| ε2 | 검증·캐릭터·데이터 오너 | A+B | 평가·URDF 검증·sim-to-real 분석·감정 엔진·외장·Week 3~ 데이터 수집 |

### 6.2 협업 구조

```
δ1  → 에피소드 원본      → ε1 (전처리·ablation·DGX 학습 실행)
δ1  → 액추에이터 조립 노트 → δ2 (다리 조립 인수인계)
ε1  → 학습 설정 요청      → δ3 (아키텍처·하이퍼파라미터 결정)
δ3  → 학습 설정 전달      → ε1 (DGX 실행·TensorRT·Orin 배포)
ε1  → 학습 결과           → δ3 (검토·재학습 판단), ε2 (평가)
ε2  → 분석 결과           → δ3 (설정 조정), δ2 (현장 튜닝)
δ2  → 실물 보행 로그      → ε2 (sim-to-real 분석)
δ1  → 상체 실측 무게      → δ2 (더미 웨이트 업데이트)
ε2  → IsaacLab 검증      → δ1 (CAD 수정), δ3 (URDF 조정)
```

---

## 7. 하드웨어

### 7.1 하반신: Berkeley Humanoid Lite (BHL)

| 항목 | 내용 |
|------|------|
| 다리 DOF | 5DOF × 2 = 10개 액추에이터 |
| 액추에이터 | 3D프린트 사이클로이드 기어박스 + BLDC (MAD M6C12/5010) |
| 모터 드라이버 | B-G431B-ESC1 × 10 |
| 통신 | CAN 버스 (CAN-USB × 2), 4개 버스 1Mbps, 250Hz |
| 제어 | NUC(BeeLink N95) + xanmod RT 커널 + BHL lowlevel C 코드 |
| 특성 | 백드라이버블 — 전원 차단 시 관절이 풀리며 안전하게 주저앉음 |

### 7.2 토르소

```
토르소 (~25cm, 알루미늄 프로파일 프레임):
  2020 알루미늄 프로파일
  3D프린트 브래킷: SO-ARM 어깨 마운트, Orin/NUC 마운트,
    배터리 슬롯(최하단), 머리 목 마운트(상단), BHL hip 연결부(하단)
  환기: Orin 방열판 위 40mm 팬 + 배기구(상단), 흡기구(하단)
```

**상하체 결합부:** 퀵릴리즈 핀 또는 나비너트. 운송 시 분리 운반 → 현장 10분 조립.

**카메라 마운트:** Week 1에서 위치·각도 확정 후 변경 금지. 수집/추론 동일 조건 보장.

**Orin 물리 연결:** SO-ARM Dynamixel ×12 + 목 XL430 ×2 → U2D2 ×2 → USB, LED 눈 → GPIO, 입 서보 → PWM, 카메라·스피커·마이크 → USB

**NUC 물리 연결:** BHL CAN-USB ×2 → USB, IMU → I2C, Orin ↔ NUC → Ethernet

**토르소 조립 순서 (δ1 주도):**

δ1이 물리 장착 전담, 각 오너가 자기 부품 배선·소프트웨어. 아래→위 순서:

```
 1. 프로파일 프레임 (δ1)
 2. 배터리 A+B 슬롯 (δ1) → δ2 배선
 3. PDB + DC-DC (δ1) → δ2 전원 배선
 4. NUC 마운트 (δ1) → δ2 전원·Ethernet·USB
 5. Orin + carrier + 방열판 (δ1) → ε1 전원·USB
 6. 환기팬 + 배기구/흡기구 (δ1)
 7. SO-ARM ×2 어깨 마운트 (δ1) → ε1 U2D2 USB
 8. 목 서보 XL430 ×2 (δ1) → ε1 U2D2 데이지체인
 9. 스피커 + 마이크 (δ1) → ε1 Orin USB 오디오
10. Orin↔NUC Ethernet (δ2)
11. 케이블 정리 + 간섭 확인 (δ1)
```

### 7.3 머리 (하이리온 캐릭터)

```
머리 (~25cm, 게이트 ≤700g):
  외주 스티로폼 조형물 (≤300g) + 내부 전자부품 (≤400g)
  XL430 목 서보 ×2는 토르소 상단 배치 (머리 무게 미포함)

내부 전자부품:
  카메라 1개 (정면, USB), LED 눈 2개 (NeoPixel), 입 서보 MG90S 1개
  모든 배선은 목 내부를 통해 토르소로 내려감
```

**머리 제작 파이프라인:**

| 시점 | 작업 | 담당 |
|------|------|------|
| Week 0 | 외주 사양 준비 (외형 스케치 + 내부 치수 + 개구부 + 무게 ≤300g) | δ1+ε2 공동 |
| Week 1 | 사양서 최종 → 외주 발주 (납기 목표 Week 5~6) | ε2 |
| Week 2 | 간이 목업 (스티로폼 블록, 전자부품 임시 배치, 계량 ≤700g) | δ1 |
| Week 6~7 | 외주 납품 → 전자부품 통합 8단계 (피팅→카메라→LED→입서보→배선→결합→계량→테스트) | δ1 장착 + ε1·ε2 배선 |

디자인-구조 조율: ε2가 외형, δ1이 내부. 충돌 시 내부 공간 확보 우선 (기능 > 외형).

플랜 B: 외주 미도착 시 Week 2 목업으로 시연 (기능 동일, 외형만 다름).

### 7.4 무게 예산

```
Week 0: IsaacLab 파라메트릭 직립 테스트 (δ3)
  → 테스트 조합: 상부 3/4/5/6kg × CoM 높이 40/50/60cm × 배터리 배치 변형
  → 조합당 수 시간, 전체 1~2일
  → "상체 총 Xkg 이하, CoM Ycm 이하에서 직립 가능" + 배터리 배치 권장안
Week 0: 스펙시트 기반 상체 무게 사전 적산 (δ2, 직립 테스트 결과와 즉시 대조)
Week 1: 상체 무게 예산 확정 → 서브시스템별 할당
Week 7: 실측 → 예산 초과 시 경량화
```

### 7.5 배터리 배치

상체 CoM을 낮추기 위해 배터리를 토르소 최하단에 집중 배치. 직립 테스트 결과에 따라 배터리 A를 hip 프레임에 마운트하는 것도 검토.

| 배터리 | 대상 | 구성 | 배치 |
|:------:|------|------|------|
| A | Orin + NUC + LED + 입 서보 + 스피커 | 3S2P 이상 | 토르소 최하단 또는 hip |
| B | SO-ARM Dynamixel ×12 + 목 XL430×2 | 3S3P | 토르소 최하단 |
| C | BHL 다리 BLDC ×10 + ESP32 | BHL 원본 | 다리 프레임 |

전원 분배: 기성 드론용 PDB + 기성 BMS + DC-DC 벅 컨버터(5V, 12V, 19V).

비상정지: B+C 양극 직렬 NC 차단 + ESP32 MOSFET C 라인 차단. A 유지.

### 7.6 외장 (ε2)

머리 외주는 7.3절 참조. 바디 외장 커버는 Week 2 발주 (납기 목표 Week 8~9), Week 13 부착. 납기 지연 시 구조 노출 상태 진행.

### 7.7 전원 시퀀싱

```
투입: A ON → Orin/NUC 부팅 → B ON → Dynamixel 토크 → C ON → BHL 캘리브레이션
비상정지 후: 원인 확인 → 안전 자세 → C 재투입 → B 재투입 → IDLE 복귀
```

### 7.8 안전

팔: 토크 60%, 속도 90°/s, 소프트 리미트, 전류 충돌 감지, 비상정지.

보행: ESP32 낙상 감지(MPU6050 → MOSFET OFF), NUC 소프트 리미트, EVA 보호대, 보행 중 SmolVLA 중단.

### 7.9 열관리

Orin TDP 25W, 토르소 밀폐 시 써멀 스로틀링 위험. 40mm 팬 + 배기구(상단) + 흡기구(하단) 구조.

### 7.10 그리퍼 검증

SO-ARM101 그리퍼 jaw ~5~6cm. Week 1에서 실물체 3개로 그립 테스트. 필요 시 고무 패드 또는 물체 교체.

### 7.11 운송

상체+다리 분리 운반, 현장 조립. 퀵릴리즈 hip 구조, 10분 이내 결합.

---

## 8. Sim → Hardware → Real 파이프라인

```
[Week 0]  BHL IsaacLab 환경 로드 + 파라메트릭 직립 테스트
[Week 1]  커스텀 상부 추가 + IsaacLab 환경 완성
[Week 2]  직립 최종 확인 (Go/No-Go) + Walking RL 학습 시작
[Week 3]  Sim2sim 검증 (IsaacLab → MuJoCo)
[Week 4~5] 다리 조립 → 공중 보행 → sim-to-real 1차 비교
[Week 6]  더미 웨이트 지면 보행 → gap 분석 → 재학습 루프
[Week 7~8] 실측 반영 → URDF 업데이트 → 재학습 반복
[Week 9~10] 실체 장착 → 보행 재검증
[Week 11~12] 풀 시나리오 안정화
```

---

## 9. 부품 조달 및 예산

### 9.1 조달 채널

| 채널 | 대상 부품 |
|------|----------|
| 심천: MAD Components 직접 | BLDC 모터 (M6C12 ×6, 5010 ×4) |
| 심천: 화창베이 현지 | ESP32, MPU6050, CAN-USB, 베어링, DC-DC, MOSFET, 비상정지, 마이크, 스피커, LED, 히트인서트, 배선 등 |
| 심천: 배터리 상가 | 배터리 A·B·C + BMS ×3 + PDB |
| 한국 온라인 | Orin, NUC, XL430, U2D2, 카메라, ESC, 알루미늄 프로파일 |
| 랩 3D프린트 | 기어박스, 다리 구조물, SO-ARM, 마운트 브래킷, 지그 (프린터 2대 병렬) |

### 9.2 예산

| 구분 | 금액 |
|------|------|
| 메인 (상체+토르소+전자) | ~148만원 (예비비 15% 포함) |
| 보행 (BHL 다리) | ~62만원 (예비비 15% 포함) |
| **총계** | **~210만원** (SO-ARM·DGX Spark 기보유) |

---

## 10. 타임라인 요약

상세 주차별 작업은 **실행 가이드** 참조.

```
Week 0    SO-ARM 커리큘럼 + 킥오프 (4일)
          ──────────────────────────────────────────
Week 1    Track A: SO-ARM 실측, 텔레옵 │ Track B: NUC 셋업, BHL 코드 숙달
                   카메라·그립 확정    │          Sim2sim, 전원 조립
Week 2    Track A: 토르소, 수집 30개   │ Track B: ★Walking RL 시작★ 지그 설계
          ▲ Go/No-Go (직립)           │         (부품 없음 = 시뮬+후가공 집중)
          ──────────────────────────────────────────
Week 3    Track A: 본격 수집 130개     │ Track B: ★부품 도착★ Sim2sim 검증
                   ε2 수집 투입       │
Week 4    Track A: 수집 계속, ablation │ Track B: ★액추에이터+다리 조립★
Week 5    Track A: 수집 600개, 서바이벌│ Track B: ★공중 보행★
          ──────────────────────────────────────────
Week 6    ★상반신 통합 테스트★         │ ★더미 지면 보행 첫 시도★
          ──────────────────────────────────────────
Week 7    상반신 계측, v2, 머리 통합   │ sim-to-real 재학습 루프
Week 8    ★상반신 리허설★              │ 재학습 루프 계속
          ══════════════════════════════════════════
Week 9    ★★ 트랙 합류: 상체-하체 결합 ★★
Week 10   실체 장착 보행 + 보행 중 SmolVLA 정지
          ──────────────────────────────────────────
Week 11   풀 시나리오 통합 (걷기+대화+집기)
Week 12   안정화 + 답사 + ★리허설 1차★
Week 13   ★리허설 2차★ + ★★발표★★
```

### 게이트 조건

| 게이트 | 시점 | 조건 |
|--------|------|------|
| 보행 Go/No-Go | Week 2 | IsaacLab 상부 mass 직립 확인. 불가 시 경량화 → 최악 보행 축소 |
| Phase 1 | Week 3 말 | 토르소 완성, SmolVLA v1 동작, ESP32 차단 동작, Sim2sim 완료, NUC 준비 |
| Phase 2 | Week 5 말 | 대화 TTFT <500ms, 공중 보행 성공, NUC 안정, 수집 600개 또는 충분 판단 |
| Week 6 | Week 6 말 | 상반신 통합 통과 + 더미 지면 보행 달성 (또는 gap 분석 시작) |
| Phase 3 | Week 8 말 | 상반신 리허설 1회, 머리 통합, SmolVLA v2, 더미 보행 안정화 중 |
| 합류 | Week 10 말 | 상하체 결합, 실체 보행, MOSFET 차단 실측, sim-to-real 리포트 |
| 통합 | Week 12 말 | 10보 직진+회전, 5분 낙상 없음, 답사 완료, 리허설 1차 |
| 최종 필수 | Week 13 | 시연 전체 동작, 10보+, MOSFET 정상, 비상정지 정상, 리허설 2회+ |
| 최종 선택 | Week 13 | 보행+대화 동시, 30분 보행 |

---

## 11. 리스크

| 리스크 | 발견 시점 | 대응 |
|--------|----------|------|
| BHL IsaacLab 환경 로드 실패 | Week 0 | 디버깅 → 최악 시 플랫폼 재검토 |
| 탑헤비 직립 불가 | Week 0~2 | 배터리 hip 배치·경량화 → 최악 시 보행 축소 |
| BHL 모터 구매 지연 | Week 0 | MAD 직접 연락, 대체 KV 조사 |
| SmolVLA Orin Hz 부족 | Week 3 | TensorRT INT8 → UX 보완 → 다운사이즈 |
| NUC 실시간성 부족 | Week 5 | Week 1 xanmod RT 선설치로 감소 |
| 배터리 30분 미달 | Week 0 | 구성 변경 |
| Actuator sim-to-real gap | Week 5~8 | **조기 발견 (기존 대비 6주↑), 재학습 7주 가용** |
| 에코 캔슬링 | Week 1 | AEC 모듈 |
| 외주 납기 지연 | Week 5~6 | 목업 유지 (기능 동일) |
| 네트워크 불량 | Week 12 | 서바이벌 계층 1+2 |
| 보행 전체 실패 | Week 6~8 | **시나리오 B (Week 6 판단, 기존 대비 5주↑)** |
| 3D프린트 문제 | Week 0~2 | 프린터 2대 병렬 |
| 두 트랙 무게 비동기 | Week 7 | 더미 웨이트 조절식 (100g 단위) + 즉시 업데이트 |
| 조립 품질 편차 | Week 1~3 | δ1 조립 기준서 + 인수인계 |
| Orin 써멀 스로틀링 | Week 3~ | 환기 구조 Week 2 반영 |
| 카메라 위치 변경 | Week 1~ | Week 1 확정 후 변경 금지 |
| 그리퍼 jaw 부족 | Week 1 | 실물 테스트, 고무 패드/물체 교체 |

---

## 12. 참고

| 항목 | 링크 |
|------|------|
| Berkeley Humanoid Lite | `lite.berkeley-humanoid.org` |
| BHL GitHub | `github.com/HybridRobotics/Berkeley-Humanoid-Lite` |
| BHL Docs | `berkeley-humanoid-lite.gitbook.io/docs` |
| SO-ARM101 | `github.com/TheRobotStudio/SO-ARM100` |
| SmolVLA | `huggingface.co/blog/smolvla` |
| LeRobot Hub | `huggingface.co/lerobot` |
| Groq | `console.groq.com` |
| Gemini | `ai.google.dev` |
| Piper TTS | `github.com/rhasspy/piper` |

---

*v12 — 2026년 3월.*
