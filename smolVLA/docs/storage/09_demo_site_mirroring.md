# 시연장 환경 미러링 가이드

> 작성일: 2026-05-01
> 출처: `04_infra_setup` 마일스톤 TODO-M1
> 목적: 시연장 환경을 DataCollector 인근에 재현하기 위한 절차·체크리스트 문서.
>       사용자(인간) 책임 영역과 자동화 가능 영역을 분리하여 05_leftarmVLA 진입 전
>       1차 미러링 셋업을 완료할 수 있도록 안내한다.
> 형제 문서: ~~`docs/storage/10_datacollector_structure.md`~~ → **legacy 이관**: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_10_datacollector_structure.md`
> 정정 (2026-05-02): 06_dgx_absorbs_datacollector 결정으로 DataCollector 노드 운영 종료.
>       본 문서의 "DataCollector 인근 재현" 절차는 역사적 결정으로 보존.
>       실제 운영: DGX 가 시연장 직접 이동하여 데이터 수집 수행 (미러링 = DGX 직접 이동으로 충족).

---

## 0) 배경 및 목적

smolVLA 학습 정확도는 **시연장 환경과 데이터 수집 환경의 일치도**에 크게 의존한다.
훈련 데이터를 수집하는 DataCollector 와 추론이 이루어지는 시연장 Orin 의 물리 환경이
다를수록 도메인 시프트(domain shift)가 커져 추론 성능이 저하된다.

본 가이드는 세 단계로 구성된다:

1. **무엇을 측정해야 하는가** (§1·§2) — 시연장 방문 시 기록할 항목
2. **어떻게 재현하는가** (§3) — DataCollector 인근 배치 시 재현 절차·체크리스트
3. **어떻게 검증하는가** (§4) — 육안 + 사진 비교로 미러링 완성도 확인

> **사용자 책임 알림**: §1·§2·§3·§4 의 실측 작업은 모두 **사용자가 직접** 시연장 및
> DataCollector 인근에서 수행한다. 자동화 가능 영역은 §5 의 `lerobot-record dry-run` 에
> 한정된다.

> **시연장 접근 가능성**: 시연장 방문·측정 시점은 사용자 일정에 따라 조정 필요.
> 05_leftarmVLA 진입 전까지 완료하면 됨. 급하지 않다면 DataCollector 셋업(TODO-D3)
> 완료 후 한 번에 현장 측정 + 재현 병행 권장.

---

## §1 시연장 환경 측정 항목

시연장 방문 시 아래 표의 모든 항목을 측정·기록한다. 측정값은 §3 재현 시 기준값이 된다.

### 1-1) 책상

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| 책상 | 높이 (바닥~상판) | cm | 줄자 | 작업자 서 있을 때 팔꿈치 높이와 비교 |
| 책상 | 상판 가로×세로 | cm × cm | 줄자 | 작업 영역 결정의 기준 |
| 책상 | 상판 재질·색 | 사진 + 텍스트 | 카메라 | 예: 흰색 목재 멜라민, 반광 등 |
| 책상 | 다리 형태 | 사진 + 텍스트 | 카메라 | 4각 vs A형 — SO-ARM 배치 간섭 여부 |

### 1-2) 작업 영역

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| 작업 영역 | 크기 (가로×세로) | cm × cm | 줄자 | SO-ARM 도달 범위 내 유효 작업 공간 |
| 작업 영역 | 책상 기준 위치 (가장자리 여백) | cm | 줄자 | 전면·좌·우 여백 |
| 작업 영역 | 바닥재 (패드·마커 여부) | 사진 + 텍스트 | 카메라 | 그립 위치 마커 있으면 촬영 |

### 1-3) 조명

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| 조명 | 작업 영역 조도 | lux | 조도계 (스마트폰 앱 대체 가능) | 작업 영역 중앙 측정 |
| 조명 | 색온도 | K | 색온도계 (스마트폰 앱 대체 가능) | 형광등(4000~6500K) / 백열등(~3000K) 구분 |
| 조명 | 광원 방향·각도 | 사진 + 상대 방향 기술 | 카메라 | 정면·측면·위 등. 그림자 방향으로 파악 가능 |
| 조명 | 광원 위치 (바닥 기준 높이) | cm | 줄자 | 천장 조명이면 "천장 고정" 기재 |
| 조명 | 자연광 유입 여부 | 있음/없음 + 방향 | 목측 | 창문 위치·블라인드 사용 여부 |

### 1-4) 카메라 — top 카메라

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| top 카메라 | 마운트 위치 (책상 기준 높이) | cm | 줄자 | 상판~카메라 렌즈 중심 거리 |
| top 카메라 | 마운트 위치 (책상 전면 기준 전후) | cm | 줄자 | 작업 영역 중앙 대비 전후 오프셋 |
| top 카메라 | 마운트 위치 (좌우 오프셋) | cm | 줄자 | 작업 영역 중앙선 기준 |
| top 카메라 | 하향 각도 (수평 기준) | 도 | 각도계 또는 스마트폰 각도 앱 | 90°=수직 하향 |
| top 카메라 | 렌즈 종류·화각 | 텍스트 (모델명) | 육안 | OV5648 등 모델명 기재 |
| top 카메라 | 해상도·프레임레이트 설정 | px × px @ fps | lerobot-find-cameras 결과 | 데이터 수집 시 동일 설정 필수 |
| top 카메라 | flip 필요 여부 | 있음/없음 | 육안 (영상 확인) | BACKLOG 03 #16 참조 — 수집 시와 추론 시 동일해야 함 |

### 1-5) 카메라 — wrist 카메라

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| wrist 카메라 | SO-ARM wrist 링크 부착 위치 | cm (링크 끝단 기준) | 줄자 | 링크 끝에서 몇 cm 위 |
| wrist 카메라 | 카메라 전방 각도 (팔 방향 기준) | 도 | 각도계 | 팔 전면 정방향=0° |
| wrist 카메라 | 케이블 배선 경로 | 사진 | 카메라 | 움직임 간섭 여부 파악용 |
| wrist 카메라 | flip 필요 여부 | 있음/없음 | 육안 (영상 확인) | BACKLOG 03 #16 — `--flip-cameras wrist` 확인 |

### 1-6) 토르소 · SO-ARM 배치

| 카테고리 | 항목 | 단위·기준 | 도구 | 비고 |
|---|---|---|---|---|
| 토르소 | 책상 기준 부착 위치 (전면 거리) | cm | 줄자 | 토르소 마운트 전면~책상 전면 |
| 토르소 | 책상 기준 부착 위치 (좌우) | cm | 줄자 | 책상 중앙선 기준 |
| 토르소 | 마운트 각도 (책상 평면 기준) | 도 | 각도계 | 정면=0°. 비틀림 각도 |
| SO-ARM | 어깨 조인트 높이 (책상 기준) | cm | 줄자 | 토르소 부착 시 팔 작업 공간의 기준 |
| SO-ARM | follower 암 초기 포즈 | 사진 | 카메라 | calibration 완료 후 home pose |

---

## §2 측정 도구 (사용자 책임)

아래 도구는 모두 **사용자가 시연장 방문 시 직접 준비·사용**한다.

| 도구 | 용도 | 대체 방법 |
|---|---|---|
| 줄자 (2m 이상 권장) | 책상 높이·크기·카메라 위치 등 모든 거리 측정 | 없음 — 필수 |
| 스마트폰 (카메라) | 책상·조명·카메라 배치·토르소 위치 사진 촬영 | 디지털 카메라 |
| 스마트폰 조도계 앱 | 작업 영역 조도 측정 (단위: lux) | 조도계 장비 |
| 스마트폰 색온도 앱 | 조명 색온도 측정 (단위: K) | 색온도계 장비 |
| 스마트폰 각도 앱 | 카메라·토르소 각도 측정 | 아날로그 각도계 |
| 메모지 또는 스프레드시트 | 측정값 즉시 기록 | 없음 — 필수 |

> **팁**: 스마트폰 앱(조도계·색온도계·각도계)은 무료 앱으로 대부분 대체 가능. 정밀도는
> 전용 장비보다 낮으나 상대적 재현(±10~20%) 수준에서는 충분하다.

> **촬영 권장**: 측정값 기록과 별개로, 모든 항목에 대해 사진을 촬영해 둔다.
> §4 육안 비교 시 시연장 기준 사진이 필수적으로 필요하다.

---

## §3 DataCollector 측 재현 절차

DataCollector 인근에서 시연장 측정값을 기준으로 환경을 재현한다.
아래 체크리스트를 순서대로 진행한다.

### DataCollector 인근 재현 체크리스트

#### 3-1. 책상 재현

- [ ] 책상 높이 시연장 측정값 ±2 cm 이내로 조정 (높이 조절 책상 사용 권장)
- [ ] 상판 재질·색이 시연장과 유사 (동일 재질 또는 동일 색상 시트 부착 고려)
- [ ] 작업 영역 크기 ±5 cm 이내 (마스킹 테이프 등으로 경계 표시)
- [ ] 작업 영역 책상 기준 위치 ±3 cm 이내 (전면·좌우 여백 일치)

#### 3-2. 조명 재현

- [ ] 작업 영역 조도 시연장 측정값 ±100 lux 이내
- [ ] 색온도 시연장 측정값 ±300 K 이내 (LED 전구 교체 또는 색온도 조절 가능 조명 사용)
- [ ] 광원 방향·각도 시연장 사진 대비 시각적으로 유사 (그림자 방향 비교)
- [ ] 자연광 유입이 시연장과 유사한 조건 (같은 시간대 비교 또는 블라인드로 차단)

> **실용 팁**: 조도·색온도는 LED 작업등(색온도 조절 가능 제품 권장)으로 가장 쉽게
> 맞출 수 있다. 시연장이 형광등(5000K) 환경이라면 동일한 주광색 LED 사용 권장.

#### 3-3. top 카메라 재현

- [ ] 마운트 높이 시연장 측정값 ±2 cm 이내
- [ ] 마운트 전후·좌우 위치 시연장 측정값 ±2 cm 이내
- [ ] 하향 각도 시연장 측정값 ±3° 이내
- [ ] 해상도·프레임레이트 설정 시연장과 동일 (`lerobot-find-cameras opencv` 결과 확인)
- [ ] flip 설정 시연장과 동일 (`config/cameras.json` 에 기재)

#### 3-4. wrist 카메라 재현

- [ ] SO-ARM wrist 부착 위치 시연장 측정값 ±0.5 cm 이내
- [ ] 카메라 전방 각도 시연장 측정값 ±3° 이내
- [ ] 케이블 배선 경로 시연장 사진 대비 간섭 없음 확인
- [ ] flip 설정 시연장과 동일 — **BACKLOG 03 #16 참조**: wrist 카메라는 `--flip-cameras wrist` 필요 여부를 시연장에서 확인 후 DataCollector 수집 스크립트와 Orin 추론 스크립트 양쪽에 동일하게 적용

#### 3-5. 토르소 · SO-ARM 배치 재현

- [ ] 토르소 전면 거리 시연장 측정값 ±2 cm 이내
- [ ] 토르소 좌우 위치 시연장 측정값 ±2 cm 이내
- [ ] 토르소 마운트 각도 시연장 측정값 ±2° 이내
- [ ] SO-ARM calibration 완료 (DataCollector 환경에서 새로 calibrate)
- [ ] follower 암 초기 포즈(home pose) 시연장 사진 대비 시각적으로 유사

#### 3-6. SO-ARM 포트 확인

- [ ] `lerobot-find-port` 로 follower/leader 포트 확인
  - **BACKLOG 03 #15 참조**: 카메라 인덱스와 마찬가지로 포트 번호도 매번 변동 가능.
    first-time 모드 (TODO-G3) 미완성 시 수동으로 `lerobot-find-port` 실행하여 확인
- [ ] 확인된 포트를 `config/ports.json` 에 기재

#### 3-7. 카메라 인덱스 확인

- [ ] `lerobot-find-cameras opencv` 로 top/wrist 카메라 인덱스 확인
  - **BACKLOG 03 #15 참조**: 카메라 인덱스 기본값(top:0, wrist:1)이 실제와 다를 수 있음.
    실행 전 반드시 인덱스 발견 단계 수행
- [ ] 확인된 인덱스를 `config/cameras.json` 에 기재 (flip 설정 포함)

---

## §4 미러링 검증 방법

> **본 사이클 결정 (2026-05-01, 사용자 답 E)**: 검증 방식 = **육안 + 사진 비교**.
> 자동 검증 스크립트는 본 사이클 진행 X (아래 BACKLOG 참조).

### 4-1) 육안 + 사진 비교 절차

1. **시연장 기준 사진 세트 촬영** (사용자 책임 — 시연장 방문 시)
   - top 카메라 뷰: 카메라가 보는 작업 영역 정면 (lerobot-record 실행 중 캡처 또는 스마트폰)
   - wrist 카메라 뷰: wrist 카메라가 보는 손목 전방 시점
   - 전체 환경 사진: 책상·조명·토르소·SO-ARM 전체가 보이는 정면·측면 2장

2. **DataCollector 인근 동일 각도 사진 세트 촬영** (사용자 책임)
   - top 카메라 뷰: `lerobot-find-cameras` 또는 lerobot-record 실행 중 캡처
   - wrist 카메라 뷰: wrist 카메라 출력 캡처
   - 전체 환경 사진: 시연장과 동일 각도·거리에서 촬영

3. **나란히 비교** (사용자 책임)
   - 사진 편집 앱 또는 단순 좌우 배치로 시연장 세트 vs DataCollector 세트 비교
   - 비교 항목:
     - 책상 상판 색·질감 (카메라 프레임 내 배경)
     - 작업 영역 크기·위치 (화각 내 비율)
     - 조명 색조·밝기 (영상의 전체적 색온도)
     - SO-ARM 배치·포즈 (캘리브레이션 후 home pose)
     - 카메라 앵글 (시야각·기울기)

4. **차이점 기록 및 재조정** (사용자 책임)
   - 눈에 띄는 차이점을 메모
   - §3 체크리스트로 돌아가 해당 항목 재조정
   - 허용 오차 이내로 맞춰질 때까지 반복

### 4-2) 합격 기준 (육안 판단)

| 항목 | 합격 기준 |
|---|---|
| 책상 배경 색·질감 | 카메라 프레임 내 육안으로 명백한 차이 없음 |
| 작업 영역 위치 | top 카메라 뷰에서 SO-ARM 그리퍼 도달 범위가 유사 |
| 조명 색조 | 영상의 전반적 색온도 차이가 명백하지 않음 (흰색 대상이 흰색으로 보임) |
| 카메라 앵글 | top/wrist 카메라 뷰가 시연장 사진과 육안으로 유사 |

> **주의**: 육안 비교는 명백한 오류(책상 색이 완전히 다름, 카메라가 전혀 다른 각도 등)를
> 걸러내는 수준이다. 세밀한 도메인 일치는 05_leftarmVLA 학습 결과로 피드백받아 재조정.

### 4-3) 자동 검증 스크립트 — BACKLOG

현 사이클에서 자동 검증 스크립트는 구현하지 않는다.
05_leftarmVLA 학습·추론 사이클 완주 후 환경 미러링 부족으로 진단될 경우 트리거:

> **BACKLOG 04 — 자동 미러링 검증 스크립트**
> - 내용: 시연장·DataCollector 카메라 영상을 자동으로 비교하는 스크립트
>   (예: 히스토그램 분포 비교, SSIM, 컬러 분포 KL-divergence 등)
> - 트리거 조건: 05_leftarmVLA 학습 후 추론 성능 부족 → 환경 미러링 원인으로 진단
> - 우선순위: 낮음 (현 사이클 진행 X)
> - 참조: 사용자 답 E (2026-05-01) — "자동 검증은 05/06 트리거 시 복귀"

---

## §5 05_leftarmVLA 진입 전 점검 항목

본 섹션은 05_leftarmVLA 시작 전 최종 확인 게이트다.

### 환경 미러링 완성 게이트

- [ ] **책상 재현**: 높이·상판·작업 영역 모두 §3 허용 오차 이내
- [ ] **조명 재현**: 조도 ±100 lux, 색온도 ±300 K 이내
- [ ] **top 카메라 재현**: 위치·각도 §3 허용 오차 이내 + flip 설정 확정
- [ ] **wrist 카메라 재현**: 부착 위치·각도 §3 허용 오차 이내 + flip 설정 확정
  - BACKLOG 03 #16: `--flip-cameras wrist` 필요 여부 확정 필수
- [ ] **토르소·SO-ARM 배치 재현**: 위치·각도 §3 허용 오차 이내
- [ ] **§4 사진 비교 합격**: top/wrist 카메라 뷰 및 전체 환경 사진 시연장 대비 육안 합격

### 하드웨어 게이트

- [ ] **DataCollector SO-ARM calibration 완료** (DataCollector 환경 기준 새로 calibrate)
- [ ] **config/ports.json 갱신**: follower/leader 포트 확인 + 기재
  - BACKLOG 03 #15: 카메라 인덱스 사전 발견 단계 필수
- [ ] **config/cameras.json 갱신**: top/wrist 인덱스 + flip 설정 확인 + 기재
- [ ] **SO-ARM 도달 범위 검증**: home pose 에서 작업 영역 내 목표 위치 도달 가능 확인

### 소프트웨어 게이트

### 자동화 가능 영역 (DataCollector 셋업 후 검증)

- [ ] DataCollector 측 venv 활성화 + lerobot import OK
- [ ] `lerobot-record --help` 정상 출력 (entrypoint 등록 확인)
- [ ] 1회 테스트 에피소드 수집 가능 여부 확인 (실 명령어는 SO-ARM·카메라 연결 시 04_infra_setup TODO-D3 검증에서 결정)
- [ ] 수집된 dataset 의 카메라 frame shape·dtype 확인 (사용자 직접 — 사진 비교)

> 구체 `lerobot-record` 호출은 draccus dataclass 인자 (`--robot.type`, `--robot.cameras`, `--dataset.repo_id` 등) 방식이라 환경별 조합 필요. 레퍼런스: `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py`. 실 호출 명령은 TODO-D3 prod 검증 시 사용자가 환경 맞춰 결정.

> **05 진입 조건**: 위 3개 게이트의 모든 체크박스 완료 후 05_leftarmVLA 진입 가능.
> 일부 항목이 미완료인 경우 TODO-M2 를 먼저 완료할 것.

---

## §6 관련 BACKLOG 및 후속 참조

| BACKLOG | 내용 | 트리거 조건 |
|---|---|---|
| BACKLOG 03 #15 | 카메라 인덱스 사전 발견 단계 — `lerobot-find-cameras opencv` 실행 필수 | 05 진입 전 (TODO-G1 완료 시 자동화) |
| BACKLOG 03 #16 | wrist 카메라 상하반전 — `--flip-cameras wrist` 필요 여부 확정 필수 | 05 데이터 수집 전 |
| BACKLOG 04 (본 §4) | 자동 미러링 검증 스크립트 | 05_leftarmVLA 추론 성능 부족 진단 시 |

### 후속 TODO

| TODO | 내용 | 본 문서 연결 절 |
|---|---|---|
| TODO-M2 | 시연장 1차 미러링 셋업 (사용자 직접 수행) | 본 문서 전체 |
| TODO-G1 | Orin check_hardware.sh (카메라·포트 자동 발견) | §3 체크리스트 3-6·3-7 의 자동화 |
| TODO-G3 | DataCollector check_hardware.sh 이식 | §5 소프트웨어 게이트 의 자동화 |
| TODO-D3 | DataCollector 환경 셋업 검증 | §5 진입 전 DataCollector 셋업 완료 선제 조건 |

---

## §6 시연장 배치 시 추가 고려사항 (흡수: 09_datacollector_setup.md §4-2·§4-3)

### 6-1) 인터넷 격리 vs HF Hub 가용 여부

DataCollector 에서 `lerobot-record --push-to-hub` 로 HF Hub 업로드 시 인터넷 접근 필요.

| 시연장 환경 | HF Hub 업로드 | 대응 |
|---|---|---|
| 인터넷 가용 WiFi | 가능 | `lerobot-record --push-to-hub` 직접 실행 |
| 인터넷 격리 WiFi (학내 방화벽 등) | 불가 | rsync 직접 전송 (HF Hub + rsync 양방향 지원 — TODO-T1 결정 완료) |
| 오프라인 | 불가 | 로컬 저장 후 나중에 devPC 경유 업로드 |

**사전 확인 권장**: 시연장 배치 전 WiFi 에서 `curl https://huggingface.co` 로 HF Hub 접근 가능 여부 테스트.

### 6-2) 전원·배선·물리 보안

- DataCollector PC + SO-ARM 전원 → 시연장 전원 포트 확인 (멀티탭 필요 여부 사전 확인)
- SO-ARM USB 케이블 길이 및 배선 정리 — 시연 중 케이블 빠짐 방지
- DataCollector PC 물리적 고정 (이동 중 낙하, USB 연결 단락 방지)
- 시연 종료 후 데이터 백업 확인 (HF Hub 또는 rsync 완료 여부 확인 후 전원 차단)

---

## §7 본 사이클 (08_final_e2e) 시연장 실측 — 2026-05-04

> 출처: `08_final_e2e` C1 시연장 셋업 (DGX 직접 이동 운영)
> 책임: 사용자 + 메인 Claude 협업 작성
> 본 사이클은 DataCollector 별도 노드 가정 (§1~§5) 과 달리 **DGX 가 시연장 직접 이동** — 미러링 = DGX 운반으로 충족. §1 측정 항목은 **데이터 수집 재현성** 위해 그대로 기록 가치 유지.

### 7-1) USB 토폴로지 (2026-05-04 ssh dgx 실측)

**관찰 사실**: 사용자 USB 3.0 포트에 hub + 디바이스 연결. 단 디바이스 사양 상 USB 2.0 path 로 enum.

```
Bus 001 (xhci, 480M)           USB 2.0
Bus 002 (xhci, 20000M/x2)      USB 3.2 path — 비어있음
Bus 003 (xhci, 480M)           USB 2.0 — 모든 디바이스 여기
  └─ Hub Dev 074 (480M)
       └─ Hub Dev 077 (480M)
            ├─ Dev 078 (uvcvideo + snd, 480M)   카메라 1
            ├─ Hub Dev 079 (480M)
            │    ├─ Dev 081 (cdc_acm, 12M)      ttyACM0 (SO-101 #1)
            │    └─ Dev 083 (cdc_acm, 12M)      ttyACM1 (SO-101 #2)
            └─ Dev 080 (uvcvideo + snd, 480M)   카메라 2
Bus 004 (xhci, 20000M/x2)      USB 3.2 path — 별도 hub (디바이스 X)
```

**디바이스 사양 (02_hardware §7·§7-1)**:
- OV5648 + U20CAM-720P 모두 **USB 2.0 High Speed only** — USB 3.0 path enum 불가
- SO-ARM ttyACM (cdc_acm) — USB 1.1 12M
- → USB 3.0 포트 사용해도 디바이스 자체가 USB 2.0 라 자동으로 USB 2.0 path 로 enum (DataCollector legacy §5-1 와 같은 구조)

**대역폭 사용량 추정 (480M 한계 대비)**:

| 디바이스 | 사용 대역폭 | 비율 |
|---|---|---|
| MJPG 640×480@30fps × 2 카메라 | ~30 Mbps | ~6% |
| SO-ARM ttyACM × 2 (실 baud ~1 Mbps) | ~4 Mbps | ~1% |
| **총** | **~34 Mbps** | **~7%** |

→ **여유 충분**, read_failed 위험 거의 없음.

**대응 (사용자 결정, 2026-05-04)**: `fourcc=MJPG` 강제 패턴 (§5-2 — `dgx/interactive_cli/flows/record.py` 에 적용 중) 그대로 유지. 본 USB 2.0 path 환경에서 데이터 수집 영향 없음 — **그냥 기록하고 진행**.

검증 명령 (재현용):
```bash
ssh dgx "lsusb -t | head -25"
ssh dgx "ls /dev/video*"
ssh dgx "ls /dev/ttyACM*"
```

### 7-1b) SO-101 ttyACM 매핑 (2026-05-04 실측)

| 디바이스 | 경로 | 비고 |
|---|---|---|
| SO-101 #1 | `/dev/ttyACM0` (Dev 081) | follower 또는 leader — `lerobot-find-port` 실행 후 확정 |
| SO-101 #2 | `/dev/ttyACM1` (Dev 083) | 다른 한쪽 |

ttyACM 번호는 연결 순서 의존 (01 BACKLOG #1 udev rule 미적용) — 데이터 수집 진입 전 `lerobot-find-port` 로 follower/leader 매핑 확인 필수.

### 7-2) 책상 (협업 작성 — 사용자 측정 대기)

| 항목 | 측정값 | 비고 |
|---|---|---|
| 높이 (바닥~상판) | _ cm | |
| 상판 가로×세로 | _ × _ cm | |
| 상판 재질·색 | _ | |
| 다리 형태 | _ | |

### 7-3) 작업 영역 (사용자 측정 2026-05-04)

| 항목 | 측정값 | 비고 |
|---|---|---|
| 크기 (가로×세로) | **42 × 30 cm** | Seeed AI Robotics Lab 매트 (노란 테두리 + 짙은 중앙) |
| 작업 표면 | Seeed 매트 | 색 균일 → pick object 색 대비 좋음 |
| pick target | 분홍색 큐브 (lego 또는 foam 큐브) | 매트 좌측 중앙 |
| place destination | 갈색 종이 박스 | 매트 우측 위 |
| frame 내 고정 사물 | SO-101 follower (가운데), SO-101 leader (오른쪽 — 파란색 키트), USB hub (왼쪽), 멀티탭·케이블 (외곽) | 모두 위치 고정 → 학습 noise 영향 X |
| frame 내 비고정 검토 | PCB 보드 (Seeed 로고 옆 작업영역 일부 침범) — 데이터 수집 전 빼는 게 권장 | 03 BACKLOG #1 (사전학습 분포 정합) |

### 7-4) 조명 (사용자 확인 2026-05-04)

| 항목 | 측정값·종류 | 비고 |
|---|---|---|
| 광원 종류 | **형광등** ✅ | 사용자 확인 — 색온도 추정 4000~6500K (형광등 일반 범위) |
| 작업 영역 조도 | (미측정 — overview 캡처에서 충분히 밝음 정합) | 추정 ≥300 lux (실내 작업 표준) |
| 광원 방향 | (미측정) — overview 캡처에서 우상단 광원 강함 | 단일 방향 광원으로 보임. 그림자 진하면 디퓨저 검토 |
| 자연광 유입 | (미측정) | 시연장 시간대 의존 — 데이터 수집 시간대 일관성 권장 |

### 7-5) overview 카메라 (OV5648 sensor / USB 모듈명 YJX-C5) — 마운트 (사용자 셋업 2026-05-04)

> **모델 표기 정정 (2026-05-04)**: USB descriptor 차원으로는 `0bda:0565 YJX-C5` (v4l2 Card type "YJX-C5: YJX-C5") — 02_hardware §7 보강 참조. OV5648 는 image sensor chip, YJX-C5 는 USB 모듈명. 동일 카메라.

| 항목 | 측정값 | 비고 |
|---|---|---|
| 마운트 형태 | **카메라 스탠드 고정** ✅ | 사용자 확인 — 데이터 수집 중 흔들림 X 보장 |
| 시점 (cheese 캡처 분석) | SO-101 위·앞에서 약 45~60° 하향 | 분홍 큐브·박스·그리퍼 모두 frame 에 들어옴 |
| 화각 점유율 | 작업 매트 약 60%, 외곽 leader arm + USB hub | svla_so100_pickplace 사전학습 분포 (정면 top view) 와 유사 |
| 카메라 인덱스 | `/dev/video0` 또는 `/dev/video1` (실측 2026-05-04) | Bus info `usb-NVDA8000:01-1.1.4` (Hub Dev 077 Port 4). `lerobot-find-cameras opencv` 로 최종 확정 |
| 캡처 해상도·fourcc | 640×480 MJPG (record.py default) | `dgx/interactive_cli/flows/record.py` 가 fourcc=MJPG 강제 |
| flip 설정 | 불요 (기본 방향 자연스러움) — cheese 캡처에서 반전 없음 확인 | `cameras.json.overview.flip=false` (default 유지) |
| 캡처 검증 사진 | `~/사진/웹카메라/2026-05-04-212104.jpg` | overview 시점 정합 PASS |

### 7-6) wrist 카메라 (U20CAM-720P) — 마운트 + flip 결정 (협업 작성, **BACKLOG #2 처리**)

| 항목 | 측정값 | 비고 |
|---|---|---|
| SO-101 wrist 링크 부착 위치 | _ cm (링크 끝단 기준) | |
| 카메라 전방 각도 | _ ° (팔 방향 기준) | |
| 케이블 배선 경로 | _ | 움직임 간섭 X 확인 |
| 카메라 인덱스 | `/dev/video2` 또는 `/dev/video3` (실측 2026-05-04) | Bus info `usb-NVDA8000:01-1.1.1` (Hub Dev 077 Port 1). `lerobot-find-cameras opencv` 로 최종 확정. v4l2 Card type "Innomaker-U20CAM-720P" (`0c45:6367`) |
| **flip 결정 (BACKLOG #2)** | flip=false (상하반전 X) — 단 **90° 회전 의심** | wrist cheese 캡처 (`2026-05-04-213206.jpg`) 분석: Seeed 로고 텍스트가 세로 방향으로 읽힘 → 카메라 USB 모듈 90° 회전 장착 추정 |
| **rotate 결정 (사용자 결정 2026-05-04)** | **A — 그대로 진행** ✅ | 회전된 wrist 영상 그대로 lerobot-record dataset 저장. 추론 시 동일 마운트 유지로 일관성 보장. 사전학습 분포 차이 수렴 부진 트리거 시 BACKLOG #8 (rotate 사후 재검토) 격상 |
| 사전학습 분포 정합 (BACKLOG #1) | wrist 광각 (FOV-H 102°) + 회전 차이 가능 | smolvla_base 의 wrist/camera2 슬롯 사전학습 화각·방향 미확인 — I1 추론 시 트리거 평가 |
| 캡처 검증 사진 | `~/사진/웹카메라/2026-05-04-213206.jpg` | wrist 시점 정합 (lego 큐브 + 박스 + 그리퍼 끝 보임) — 회전 의심 외 OK |
| lego 큐브 확정 | 분홍색 lego 블록 (스터드 패턴) | svla_so100_pickplace 사전학습 재질 정합 ✅ — 색만 다름 |

### 7-7) SO-101 배치 + calibration (사용자 셋업 2026-05-04, **BACKLOG #6 처리 대기**)

| 항목 | 측정값·결정 | 비고 |
|---|---|---|
| follower mount | **책상 직접 mount (토르소 부착 X)** | 본 사이클 — 09 사이클에서 토르소 부착으로 변경 예정 |
| follower 색상 | 흰색 (Seeed Arm Kit Pro) | cheese 캡처 frame 가운데 |
| leader 색상·위치 | **파란색 키트, frame 우측 고정** | overview 카메라 frame 안에 leader 도 들어옴 — 위치 고정이라 학습 noise X |
| follower home pose 사진 | `~/사진/웹카메라/2026-05-04-212104.jpg` (그리퍼 open 상태) | calibration 완료 후 home pose 재캡처 권장 |
| **calibration JSON 처리 (BACKLOG #6)** | _ (사용자 처리 대기) | (a) 기존 so100_* JSON → so101_* 복사 / (b) `lerobot-calibrate` 재실행 / (c) 기존 SO101 JSON 활용 |
| follower 포트 | `/dev/ttyACM0` 또는 `/dev/ttyACM1` (Dev 081 또는 083) | `lerobot-find-port` 로 최종 매핑 — 01 BACKLOG #1 (udev rule 미적용) 따라 연결 순서 의존 |
| leader 포트 | (다른 한쪽) | 동일 |
| USB hub | 매트 좌측 외곽 고정 (4 디바이스 — 카메라 2 + ttyACM 2 모두 동일 hub Dev 077) | §7-1 USB 토폴로지 참조 |

### 7-8) 사진 기록 (2026-05-04 cheese 캡처)

| 사진 | 경로 | 시점 |
|---|---|---|
| overview 카메라 | `dgx:/home/laba/사진/웹카메라/2026-05-04-212104.jpg` | 책상 위 SO-101 + 매트 + 분홍 큐브 + 박스 + leader arm + USB hub. 정면 살짝 위에서 45~60° 하향 |
| wrist 카메라 | `dgx:/home/laba/사진/웹카메라/2026-05-04-213206.jpg` | 그리퍼 fingers 끝 시점, 매트 위 분홍 lego 큐브. **90° 회전 의심** (Seeed 로고 세로 표시) |
| (선택) 전체 환경 사진 | _ | 사용자 추후 보강 — §4-1 시연장 기준 사진 세트 |

> 사진들은 dgx 본체 home 의 `~/사진/웹카메라/` 에 저장됨 (cheese 한국어 데스크톱 default). devPC 로 가져올 시 `scp 'dgx:/home/laba/사진/웹카메라/<file>' /local/path/`

---

## 7-X) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 04 TODO-M1 산출물. 사용자 결정 (육안+사진 비교, 자동 검증 BACKLOG) 반영. §1 측정 항목 표 (책상/조명/top카메라/wrist카메라/토르소), §2 측정 도구 (사용자 책임), §3 DataCollector 재현 체크리스트 (7개 단위), §4 육안+사진 비교 절차 + 합격 기준 + 자동 검증 BACKLOG 명시, §5 05_leftarmVLA 진입 게이트 3개 (환경미러링/하드웨어/소프트웨어) + lerobot-record dry-run 포함. BACKLOG 03 #15·#16 연계 명시. |
| 2026-05-01 (cycle 2) | §5 소프트웨어 게이트 lerobot-record dry-run 추측 CLI 교체 — `--robot-path`, `--cameras top,wrist`, `--num-frames`, `--dry-run` 등 레퍼런스 미존재 플래그 제거. draccus dataclass 방식 안내 + 구체 호출은 TODO-D3 시점으로 이관 (옵션 B 채택). code-tester Critical #2 해소. |
| 2026-05-02 | §0 형제 문서 갱신 (`09_datacollector_setup.md` → `10_datacollector_structure.md`). §6 신규 추가 — `09_datacollector_setup.md §4-2·§4-3` (HF Hub 격리 대응 + 전원·배선·물리 보안) 흡수. docs/storage 재정렬 작업. |
| 2026-05-04 | §7 신규 — 08_final_e2e C1 시연장 실측 (DGX 직접 이동, 미러링 = 운반). §7-1 USB 토폴로지: 시연장 모든 카메라 USB 3.0 path (DataCollector legacy USB 2.0 path 와 차이). §7-2~§7-8 협업 작성 표 골격 (사용자 측정값 대기). |
