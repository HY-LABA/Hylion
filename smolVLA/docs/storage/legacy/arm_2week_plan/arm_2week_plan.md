# Bi-arm VLA 최종 프로젝트 로드맵

> 기준일: 2026-04-21 | 마감: 2026-05-06 | 역할: δ1 (팔 하드웨어 오너, Track A 리드)

---

## 최종 목표 상태 (2026-05-06)

**양팔 SO-ARM 하드웨어에서 Bi-arm VLA 가 Orin 위에서 추론·실행되고, DGX 에서 학습된 정책이 배포되어 데모 가능한 상태.**

---

## 장비 역할 분담 (병렬 운영)

<!-- 06_dgx_absorbs_datacollector (2026-05-02): DataCollector 별도 노드 폐기 → 3-노드 구조로 정정.
     DataCollector (smallgaint) 자산은 docs/storage/legacy/02_datacollector_separate_node/ 로 이관.
     DGX 가 시연장 직접 이동 운영 + 데이터 수집 + 학습 세 책임 통합. -->

- `devPC`: 코드 정리/문서화/설정 관리/배포 패키지 준비
- `Orin`: 배포 대상, 실행/검증 전용 (실제 SO-ARM 연결 테스트 포함)
- `DGX Spark`: 학습/튜닝 주력 환경 + **데이터 수집 + 시연장 직접 이동 운영** (06_dgx_absorbs_datacollector 결정 — DataCollector 역할 통합)
- `교수님 연구실 PC (Windows + GPU)`: 백업/오버플로우 전용 (DGX 병목 시 학습 분산)

> *legacy: DataCollector (smallgaint Ubuntu 22.04 PC) 는 04_infra_setup 결정 시점에 별도 노드로 운영되었으나, 06_dgx_absorbs_datacollector (2026-05-02) 사이클에서 DGX 로 흡수 결정. DataCollector 자산: `docs/storage/legacy/02_datacollector_separate_node/`*

운영 원칙:
- 실시간 제어 및 현장 검증은 Orin 기준으로 판단한다.
- 학습 성능 실험 및 데이터 수집은 DGX 기준으로 판단하며, 백업 시에만 연구실 PC 를 동원한다.
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

### [x] 04_infra_setup

<!-- *본 가정은 06_dgx_absorbs_datacollector 사이클에서 DGX 흡수로 정정됨 (2026-05-02). 본문 텍스트는 04 결정 시점 그대로 보존. DataCollector 별도 노드 가정은 이 시점에서의 역사적 결정이며, 실제 구현 단계에서 DGX 단일 노드 흡수로 전환되었음.* -->

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

### [x] 05_interactive_cli

<!-- *본 마일스톤의 datacollector 측 flow 구현 (datacollector/interactive_cli/) 은 06_dgx_absorbs_datacollector (2026-05-02) 사이클에서 DGX 흡수로 전환됨. 05 사이클 완료 시점 기준 datacollector 노드 구현은 미완 상태 (BACKLOG D3). DGX 흡수 후 통합: dgx/interactive_cli/ 가 수집/학습 두 모드 분기 담당. 장치 선택 옵션도 datacollector 제거 → orin/dgx 2 옵션으로 축소 (06 X2 처리).* -->

- 목표: orin·dgx·datacollector 세 노드 공통 대화형 CLI 게이트웨이 — 환경 체크부터 데이터 수집·전송까지 한 명령으로 진행 가능. 04 산출물 (check_hardware·run_teleoperate·sync_dataset·push_dataset_hub) 을 사용자 친화 인터페이스로 통합.
- 주요 작업:
  - 공통 console 프레임워크 설계 (3 노드 공통 구조 — 진입 → 장치 선택 → 환경 체크 → 노드별 후속 flow)
  - 신규 디렉터리: `orin/interactive_cli/`, `dgx/interactive_cli/`, `datacollector/interactive_cli/` (마일스톤 이름과 동일 폴더, 각 노드 루트에 형제)
  - flow 0~7 단계 (datacollector 기준 — orin·dgx flow 는 spec 진행 중 협의):
    - 0. 인터페이스 진입 (orin·dgx 는 SSH, datacollector 는 직접 터미널)
    - 1. 장치 선택 질문 (orin / dgx / datacollector)
    - 2. 환경 체크 (04 TODO-G1 `check_hardware.sh` 패턴 미러 — 각 노드 환경 맞춤)
    - 3. "텔레오퍼레이션 진행 (이 작업 끝나면 학습 준비 완료)" 안내 + enter 시 실행 (04 TODO-D2 `run_teleoperate.sh` 활용)
    - 4. 사용자 동작 확인 후 enter 입력 ("잘 작동하면 enter")
    - 5. "어떤 학습 데이터를 모을건가요?" 학습 종류 질문 (옵션은 spec 진행 중 정의)
    - 6. 데이터 수집 시나리오 진행 (간단한 설명서 + lerobot-record 호출)
    - 7. "[저장경로]에 저장됨" 출력 + 전송 방식 사용자 선택 (HF Hub / rsync DGX / 안함) — 04 TODO-T1 산출물 활용
- 결정사항 (05 진행 중 확정):
  - 5단계 학습 데이터 종류 옵션 (예: 단순 pick-place / 복잡 manipulation / dual-arm coordination 등)
  - orin·dgx 측 flow 의 3~7 단계 (datacollector 와 어떤 차이점 — orin 추론 검증·dgx 학습 trigger 등)
  - 공통 console 프레임워크 코드 공유 방식 (각 노드별 중복 vs 공통 모듈 import)
- 위치: 본 마일스톤은 04 인프라의 사용자 인터페이스 통합. 06_dgx_absorbs_datacollector 흡수 후에는 **DGX (데이터 수집 흡수)** 가 수집·학습 두 모드를 단일 진입점 (`bash dgx/interactive_cli/main.sh`) 으로 통합하여 07_leftarmVLA 진입 준비 완료.

### [x] 06_dgx_absorbs_datacollector

<!-- 신규 삽입 (2026-05-02). 기존 06~09 → 07~10 시프트. -->

- 목표: DataCollector 책임을 DGX 가 흡수 — DGX 가 시연장 직접 이동 운영하며 데이터 수집 + 학습 두 책임을 모두 수행. 기존 datacollector/ 노드 자산을 legacy 이관, dgx/interactive_cli/ 가 수집·학습 두 모드 분기 지원, dgx/ 의존성·scripts 에 데이터 수집 도구 흡수.
- 주요 결정 사항 (Phase 1 합의, 2026-05-02):
  - A. DGX 가 시연장 직접 이동 — 04 의 "DataCollector 별도 노드" 가정 폐기
  - B. DGX SO-ARM·카메라 USB 직결 가능 확인 (USB·dialout·v4l2 실 검증은 V1 prod)
  - C. 옵션 α 채택 — 단일 진입점 `bash dgx/interactive_cli/main.sh`, flow 3 단계에서 수집/학습/종료 mode 분기
  - D. 04 BACKLOG #11·#12·#13 + 05 미검증 항목 → "완료(불요)" 마킹 (M2 처리)
  - E. CLAUDE.md 4곳 정합 갱신 완료 (Phase 1 시점 메인 직접 수정)
  - F. 본 spec 번호 = 06, 기존 06_leftarmVLA → 07 시프트
- 주요 작업:
  - [그룹 L] datacollector/ 자산 → `docs/storage/legacy/02_datacollector_separate_node/` 이관
  - [그룹 M] arm_2week_plan.md + BACKLOG.md + docs/storage/README 정합 갱신
  - [그룹 X] dgx/interactive_cli/ 재구현 (mode.py 신규 + 수집 flow 이식) + dgx/scripts/ 흡수 + dgx/pyproject.toml + setup_env.sh extras 추가
  - [그룹 V] DGX 시연장 이동 하드웨어 직결 검증 + 수집/학습 mode 완주 실물 검증
- 배경:
  - Python 3.12 차단: 05 D3 단계에서 DataCollector (Python 3.10) 가 lerobot upstream PEP 695 syntax 로 import 실패. 학교 WiFi 가 deadsnakes PPA 차단 → 우회 불가
  - DGX 는 이미 Python 3.12.3 + `.arm_finetune` venv 운영 중 (06_dgx_venv_setting) → BACKLOG #11 자연 우회
  - 시연장 미러링 원칙 유지: DGX 자체가 시연장 이동 → 미러링 원칙 충족. 데이터 수집 → 학습이 DGX 한 곳으로 통합, Orin 추론과 합쳐 단순 2-step 흐름
- spec 파일: `docs/work_flow/specs/06_dgx_absorbs_datacollector.md`

### [x] 07_e2e_pilot_and_cleanup

<!-- 신규 삽입 (2026-05-03). 기존 07~10 → 08~11 시프트. -->

- 목표: 팔만 시연장에 달면 즉시 데이터수집 → 학습 → 추론 한 사이클을 돌릴 수 있도록 모든 도구·스크립트·문서 완비 + devPC/SSH 자율 가능 영역에서 한 사이클 (svla_so100_pickplace 짧은 fine-tune → DGX→Orin ckpt 전송 → Orin 더미 추론) 실 실행 검증 + datacollector 잔재 활성 영역 0 건 정리. 시연장 이동 X.
- 주요 결정 사항 (Phase 1 합의, 2026-05-03):
  - A. spec 이름·시프트: `07_e2e_pilot_and_cleanup`. 기존 07~10 → 08~11
  - B. E 그룹 학습 깊이: SO-ARM 단일/페어 그대로. 토르소·정식 학습은 08 위임. 이번은 파이프라인 검증 + interactive-cli 동작 검증
  - C. BACKLOG 흡수 범위: 옵션 C (최대) — 도구·운영 정비까지. 시연장 PHYS_REQUIRED 항목은 BACKLOG 유지
  - D. 시연장 이동: 본 사이클 X. 도구만 완비
  - E. `.gitignore` datacollector 패턴 제거 (L6·L10 2 줄 제거, Category B 동의)
  - F. 학습 step: `--steps=2000 --save_freq=1000` (예상 1.5~3 시간, ckpt 2 회 저장)
  - G. HF Hub 차단 fallback: 작업 보류 → 다른 네트워크 재시도
  - H. LD_LIBRARY_PATH 패치 방향: wrapper 스크립트 + settings.json 화이트리스트
  - I. Category A 자동화 패턴: 06 wrap 시 패턴 그대로 — hook matcher 임시 비활성화 → 메인 적용 → 복원
  - J. 진행 모드: 5 그룹 (P→D→T→O→W) + 게이트 3 회 (D·T·O 분기 종료마다 사용자 `/verify-result`)
- 주요 작업 (그룹별 요약):
  - [그룹 P] Cleanup·시프트 prep — dev-connect.sh datacollector 라인 제거, .gitignore 패턴 제거, arm_2week_plan.md 시프트, specs/README.md 시프트, 활성 영역 datacollector 잔재 grep 종합
  - [그룹 D] DGX interactive-cli 검증 + 게이트 1 — dgx 수집 mode SSH_AUTO 검증 (06 V2 흡수), 학습 mode 회귀 검증 (06 V3 + 05 X3 통합), 5-step 하드웨어 검증 도구 정비 (06 V1)
  - [그룹 T] DGX 학습 사이클 검증 + 게이트 2 — svla_so100_pickplace HF Hub 다운로드 prod 검증, DGX 짧은 fine-tune 1 회 완주 (2,000 step), sync_ckpt_dgx_to_orin.sh 실 실행 검증
  - [그룹 O] Orin interactive-cli + 추론 + 게이트 3 — orin flow 0~5 SSH_AUTO 검증 (05 O3 흡수), run_python.sh wrapper + settings.json 화이트리스트 (03 BACKLOG #14), setup_env.sh 정비 (02 BACKLOG #7·#8), hil_inference.py 카메라 도구 정비 (03 BACKLOG #15·#16), Orin 더미 obs 추론
  - [그룹 W] Wrap-up 일괄 정리 — SKILL.md 경로 정정 (06 BACKLOG #6, Category A), lerobot_upstream_check 색인 갱신 (06 BACKLOG #7), upstream 동기화 entrypoint 정리 절차 명문화 (04 BACKLOG #1), ports.json/cameras.json 추적 정책 명문화 (04 BACKLOG #3), 자연 처리된 BACKLOG 항목 일괄 마킹
- 종착점: 시연장에서 SO-ARM 만 달면 `dgx/interactive_cli/main.sh` → 수집 → 학습 → `sync_ckpt_dgx_to_orin.sh` → `orin/interactive_cli/main.sh` → hil_inference 흐름이 검증된 도구 위에서 즉시 가능
- spec 파일: `docs/work_flow/specs/07_e2e_pilot_and_cleanup.md`

### [x] 08_final_e2e

<!-- 신규 삽입 (2026-05-04). 기존 08~11 → 09~12 시프트. -->

- 목표: 활성 코드 so100/101 정합 + 신규 wrist 카메라 (U20CAM-720P) 흡수 + interactive-cli 뒤로가기 UX + 활성 spec 정합성 정리
- 주요 결정 사항 (Phase 1 합의, 2026-05-04):
  - A. spec 이름·시프트: `08_final_e2e`. 기존 08~11 → 09~12 시프트 (07 패턴 따라)
  - B. wrist 카메라 모델: INNO-MAKER U20CAM-720P (1280×720, FOV-H 102°, USB 2.0 UVC 1.0.0, MJPEG/YUY2 30fps)
  - G. so100/101 정합 범위: upstream 두 클래스 차이 study 후 일괄 마이그레이션 (데이터셋 ID `svla_so100_pickplace` 는 그대로 유지)
  - H. interactive-cli 뒤로가기 UX: dgx + orin 일괄 적용 (`b/back` 입력 시 직전 분기점 복귀, entry 에서는 종료)
  - I. Phase 2 wave 모드: 07 패턴 답습 (wave 의존성 + 게이트 분리)
- 주요 작업 (그룹별 요약):
  - [그룹 S] Setup·정합성 정리 — arm_2week_plan.md·specs/README.md 시프트, BACKLOG 정합
  - [그룹 R] Robot type 정합 — SO100 vs SO101 upstream 차이 study → 활성 코드 SO101 일괄 마이그레이션
  - [그룹 H] Hardware 신규 wrist 카메라 — U20CAM-720P 사양 문서화 + 코드·config 영향 적용
  - [그룹 N] Navigation 뒤로가기 UX — dgx + orin interactive_cli 공통 뒤로가기 패턴
- 종착점: 활성 코드 SO101 일괄 마이그레이션 완료 + U20CAM-720P 사양 문서화·코드 영향 검토 완료 + dgx + orin interactive_cli 공통 뒤로가기 (`b/back`) 패턴 적용 + arm_2week_plan / specs/README 정합 갱신
- spec 파일: `docs/work_flow/specs/08_final_e2e.md`

### [ ] 09_leftarmVLA

<!-- 구 08_leftarmVLA. 08_final_e2e (2026-05-04) 삽입으로 09 로 시프트.
     구 07_leftarmVLA. 07_e2e_pilot_and_cleanup (2026-05-03) 삽입으로 인해 08 로 시프트.
     구 06_leftarmVLA. 06_dgx_absorbs_datacollector (2026-05-02) 삽입으로 인해 07 로 시프트.
     "DataCollector" 역할은 DGX (데이터 수집 흡수) 로 대체됨.
     "데이터 수집·학습·배포 한 사이클 완주" 책임은 08_final_e2e 로 이전. 본 마일스톤은 팔 배치 차이만 (휴머노이드 토르소 부착 좌표계 재정의·작업 영역) 담당. -->

- 목표: 단일 팔 (left arm, 휴머노이드 토르소 부착) 기준 smolVLA 파인튜닝 → Orin 배포까지 한 사이클 — 팔 배치 차이만 (책상 mount → 토르소 부착 좌표계 재정의·작업 영역)
- 전제: 08_final_e2e 에서 데이터 수집·학습·배포 한 사이클 완주 + 도구·정합 정리 완료 후 진입. 본 마일스톤은 "토르소 부착 팔 배치"가 추가되는 차이만 담당.
- 주요 작업:
  - 휴머노이드 토르소 부착 SO-ARM (left arm) calibration 및 작업 영역 재정의 (08 책상 mount 대비 좌표계·관절 한계 차이)
  - 08_final_e2e 사이클과 동일한 흐름으로 실행 (데이터 수집·학습 2,000+ step·Orin 추론) — 토르소 좌표계가 유일한 차이
  - 데이터 수집·전송은 dgx/interactive_cli/ 활용 (08 검증 완료 도구)
- 고려사항:
  - 표준 SO-ARM 책상 mount 와 다른 좌표계·관절 한계 (어깨가 토르소에 부착되어 가용 작업 공간 변화)
  - 사전학습 smolvla_base 가 표준 SO-ARM 분포로 학습된 점 → 도메인 시프트 존재
  - **DGX (데이터 수집 흡수)** 가 시연장 이동 환경에서 데이터 수집 (06 결정으로 DataCollector 역할 통합)
- 위치: 본 마일스톤은 08 의 "팔 배치 변경" 버전. 10 양팔 학습의 사전 단계가 아니다 (10 은 양팔 데이터로 처음부터 학습).

### [ ] 10_biarm_teleop_on_dgx

<!-- 구 09_biarm_teleop_on_dgx. 08_final_e2e (2026-05-04) 삽입으로 10 으로 시프트.
     구 08_biarm_teleop_on_dgx. 07_e2e_pilot_and_cleanup (2026-05-03) 삽입으로 인해 09 로 시프트.
     구 07_biarm_teleop_on_dgx. 06_dgx_absorbs_datacollector (2026-05-02) 삽입으로 인해 08 로 시프트.
     "DataCollector 기준" → "DGX (데이터 수집 흡수) 기준" 으로 정정. -->

- 목표: 양팔 (left + right SO-ARM, 토르소 부착) teleoperation 데이터 수집 환경 구축 (DGX 데이터 수집 흡수 기준)
- 주요 작업:
  - 양팔 teleop 동작 검증 (좌·우 leader → 좌·우 follower)
  - 카메라 3대 구성 확정 및 데이터 수집 (손목 좌·우 2대 + 전체 조망 1대, base 미포함)
- 결정사항 (10 진행 중 확정):
  - 데이터셋 카메라 키 컨벤션: `observation.images.{wrist_left, wrist_right, overview}` (또는 동등)
  - `observation.state` / `action` 12 DOF 매핑: `[left_6, right_6]` 단일 키 vs 좌·우 분리 키
- 고려사항:
  - 카메라 3대 구성은 smolvla_base 사전학습 분포 (보통 1~2 카메라) 와 다름 → 10 학습 시 expert 학습에 가장 큰 영향
  - 손목 카메라는 그리퍼 동작을 가까이서 촬영 → 사전학습된 SmolVLM2 vision encoder 분포와 차이
  - 양팔이 토르소에 부착된 상태에서 teleop 시 좌·우 팔 충돌 회피 작업 영역 정의 필요

### [ ] 11_biarm_VLA

<!-- 구 10_biarm_VLA. 08_final_e2e (2026-05-04) 삽입으로 11 로 시프트.
     구 09_biarm_VLA. 07_e2e_pilot_and_cleanup (2026-05-03) 삽입으로 인해 10 으로 시프트.
     구 08_biarm_VLA. 06_dgx_absorbs_datacollector (2026-05-02) 삽입으로 인해 09 로 시프트. -->

- 목표: 양팔 데이터로 smolVLA 파인튜닝 → 양팔 추론 동작 검증
- 주요 작업:
  - 10 에서 수집한 양팔 12 DOF + 카메라 3대 구성 데이터로 smolVLA 파인튜닝 (단일팔에서 전이하지 않고 양팔 데이터로 처음부터 학습)
- 고려사항:
  - SmolVLA `max_state_dim=32` / `max_action_dim=32` padding 으로 12 DOF 양팔 수용 가능 (코드 차원 확인 완료, `docs/lerobot_study/03_smolvla_architecture.md` §A·§E 참조)
  - 카메라 3대 → smolvla_base 사전학습 분포 차이로 vision/connector 까지 푸는 풀 파인튜닝(S3) 검토 필요할 수 있음. 첫 시도는 표준 파인튜닝(S1) 부터.
  - 토르소 부착 양팔 좌표계가 사전학습 분포와 다름 → 도메인 시프트 큼. 학습 step 수 / 데이터 양 충분히 확보 필요.
- 비상 옵션:
  - 잘 안되면 머리 위에 더듬이 카메라 다는 것 고려 (조망 카메라 보강)

### [ ] 12_biarm_deploy

<!-- 구 11_biarm_deploy. 08_final_e2e (2026-05-04) 삽입으로 12 로 시프트.
     구 10_biarm_deploy. 07_e2e_pilot_and_cleanup (2026-05-03) 삽입으로 인해 11 로 시프트.
     구 09_biarm_deploy. 06_dgx_absorbs_datacollector (2026-05-02) 삽입으로 인해 10 으로 시프트. -->

- 목표: 양팔 VLA 정책을 시연장 Orin 에 배포하여 최종 데모 가능 상태로 완성
- 고려사항:
  - 카메라 3대 + 양팔 SO-ARM 보드 2대 + 토르소 측 추가 USB 가능성 → Orin USB 포트 / 허브 구성 점검 (02_hardware 와 연동)
  - `num_steps` / `n_action_steps` 튜닝으로 Orin 추론 latency 최적화 (`docs/lerobot_study/03_smolvla_architecture.md` §F·§E 참조)
