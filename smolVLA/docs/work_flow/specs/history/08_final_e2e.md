# 08_final_e2e
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: so100/101 정합 + 신규 wrist 카메라 (U20CAM-720P) 흡수 + interactive-cli 뒤로가기 UX + 활성 spec 정합성 정리.
> 환경: orin (JetPack 6.2, `~/smolvla/orin/.hylion_arm`) + dgx (Ubuntu 24.04, Python 3.12.3, `~/smolvla/dgx/.arm_finetune`) + devPC. 3-노드.
> 접근: devPC → SSH (orin·dgx) — 본 사이클은 자율 검증 영역만.
> 코드 경로: `orin/`, `dgx/`, `docs/storage/`, `docs/work_flow/specs/`, `arm_2week_plan.md`. 신규 디렉터리 생성 X.
> 하드웨어: SO-101 follower (12V) x1 + SO-101 leader (7.4V) x1 + overview OV5648 x1 + **wrist U20CAM-720P x1 (신규)**
> 작성: 2026-05-04 | 자동화 종결: 2026-05-04 (Wave 1 게이트 1 통과)

---

## 본 마일스톤의 위치

본 spec 은 **정합 정리 사이클**. 07_e2e_pilot 이 도구 검증, 08 은 활성 코드의 SO101 마이그레이션 + 신규 wrist 카메라 (U20CAM-720P) 흡수 + interactive-cli 뒤로가기 UX 정비 + 활성 spec 번호 정합 갱신 4 축의 정합 정리 사이클.

- 본 사이클 삽입으로 기존 `08_leftarmVLA` → 09, `09_biarm_teleop_on_dgx` → 10, `10_biarm_VLA` → 11, `11_biarm_deploy` → 12 시프트
- **종착점**: 활성 코드 SO101 일괄 마이그레이션 완료 + U20CAM-720P 사양 문서화·코드 영향 검토 완료 + dgx + orin interactive_cli 공통 뒤로가기 (`b/back`) 패턴 적용 + arm_2week_plan / specs/README 정합 갱신

### 차기 사이클 (09_leftarmVLA) 과의 차이

| | 08 (이번) | 09 leftarmVLA |
|---|---|---|
| 본질 | 정합 정리 (SO101·U20CAM·뒤로가기·번호) | 첫 정식 e2e 사이클 (left arm, 책상 또는 토르소 mount) |
| 산출 | 코드·문서 정합 | 데이터 수집 + 학습 + 추론 풀 사이클 |
| 환경 | devPC + SSH (자율) | DGX 시연장 이동 + Orin 시연장 |

---

## 사용자 결정 사항 (Phase 1 합의, 2026-05-04)

| # | 결정 항목 | 결과 |
|---|---|---|
| A | spec 이름·시프트 | `08_final_e2e`. 기존 08~11 → 09~12 시프트 (07 패턴 따라) |
| B | wrist 카메라 모델 | INNO-MAKER **U20CAM-720P** (사양 PDF: 1/4" 1280×720, FOV-D 120°/H 102°, USB 2.0 UVC 1.0.0, MJPEG/YUY2 30fps, M12 mount, 32×32 mm, rolling shutter, F2.2 focal 2.79 mm) |
| G | so100/101 정합 범위 | 메인 자율 — upstream 두 클래스 차이 study 후 일괄 마이그레이션 (단 데이터셋 이름 `svla_so100_pickplace` 는 외부 자원이므로 그대로) |
| H | interactive-cli 뒤로가기 UX | dgx + orin 일괄 적용. 패턴: 각 prompt 에 **`b` 또는 `back` 입력 시 직전 분기점 복귀**, entry (0 단계) 에서는 종료. 모든 분기점 동일 |
| I | Phase 2 wave 모드 | 07 패턴 답습 — wave 의존성 + 게이트 분리 |

---

## 본 사이클 진행 모드

```
[Wave 1] S + R + H + N (Setup·정합 — 자율 병렬) ✅ 완료
    ↓
    Phase 3 게이트 1 (정합 결과 사용자 검증) ✅ 통과
```

---

## Todo

> 그룹: S=Setup, R=Robot type 정합, H=Hardware 신규 wrist 카메라, N=Navigation 뒤로가기

---

### [그룹 S — Setup·정합성 정리 (Wave 1, 자율)]

#### [x] TODO-S1: arm_2week_plan.md 04~07 [x] 마킹 + 08~12 시프트

**자동화 완료 (2026-05-04)**: 마킹 4건 (04~07) + 신규 08_final_e2e 항목 삽입 + 09~12 시프트 + 시프트 주석 누적 보존 + 09_leftarmVLA "팔 배치 차이만" 본문 갱신. code-tester READY + prod-test AUTOMATED_PASS.

- 타입: task
- DOD:
  - 기존 `[ ] 04_infra_setup`, `[ ] 05_interactive_cli`, `[ ] 06_dgx_absorbs_datacollector`, `[ ] 07_e2e_pilot_and_cleanup` → 모두 `[x]` (git history 기준 wrap 완료 4건)
  - 신규 `[ ] 08_final_e2e` 항목 추가 (07 다음 위치, 본 spec 의 목표·주요 작업·결정사항 요약)
  - 기존 08~11 → 09~12 시프트 (시프트 주석 누적: "구 08_leftarmVLA. 08_final_e2e (2026-05-04) 삽입으로 09 로 시프트.")
  - 기존 08_leftarmVLA 본문 중 "단일 팔 좌표계 재정의·작업 영역" 항목은 09 로 보존, 데이터 수집·학습·배포 책임은 09 본문에 "팔 배치 차이만" 명시
- 구현 대상: `arm_2week_plan.md`
- 테스트: code-tester — 마일스톤 번호 unique (06~12), 시프트 주석 누적 보존, [x] 4건 마킹, 신규 08 항목 존재
- 제약: —
- 잔여 리스크: —

#### [x] TODO-S2: specs/README.md "활성 spec 번호 현황" 갱신

**자동화 완료 (2026-05-04)**: 07 → history, 08_final_e2e → 활성, 09~12 시프트, 기준일 2026-05-04, 시프트 주석 추가. code-tester READY + prod-test AUTOMATED_PASS.

- 타입: task
- DOD:
  - 07_e2e_pilot_and_cleanup → "history" 마킹 (이미 history/ 이동 완료)
  - 신규 `08_final_e2e` → "활성 (현 사이클)" 표기
  - 09~12 시프트 반영 (S1 일관)
  - 기준일 갱신 (2026-05-03 → 2026-05-04)
  - 시프트 배경 주석 추가 (08_final_e2e 삽입)
- 구현 대상: `docs/work_flow/specs/README.md`
- 테스트: code-tester — 표 11 행 (01~12 + 활성 1) 정합, 표기 일치
- 제약: —
- 잔여 리스크: —

---

### [그룹 R — Robot type 정합 (Wave 1, 자율)]

#### [x] TODO-R1: SO100 vs SO101 upstream 차이 study → docs/lerobot_study/08_so100_vs_so101.md 신규

**자동화 완료 (2026-05-04)**: upstream 확인 결과 `SO100Follower = SOFollower`, `SO101Follower = SOFollower` (so_follower.py L232-233 alias 동일 인터페이스). 채택: SO101Follower / SO101Leader + robot_type "so101_follower"/"so101_leader". 영향 영역 6 파일 식별. 잔여 리스크: calibration JSON 경로 robot_type 의존 (R2 또는 운영 단계 처리). code-tester READY (Recommended: §3 파일수 오기 — R2 cycle 흡수) + prod-test AUTOMATED_PASS.
**ad-hoc 이관 (2026-05-04, 게이트 1 walkthrough)**: 컨벤션 정합 — `docs/storage/16_so100_vs_so101.md` → `docs/lerobot_study/08_so100_vs_so101.md` (lerobot 관련 study 는 lerobot_study 디렉터리 컨벤션 적용). 본 spec R1 DOD/구현대상 path 갱신 + context history 보존 (시점 사실 그대로).

- 타입: task (study)
- DOD:
  - upstream `lerobot/robots/so_follower/so_follower.py` (`SO100Follower`, `SO101Follower`) + `teleoperators/so_leader/so_leader.py` 비교
  - 모터 사양·gear ratio·calibration 차이·motor_id 매핑·class 인터페이스 차이 정리
  - 본 프로젝트 SO-101 Arm Kit Pro (follower 12V, leader 7.4V) 와 정합되는 클래스 결정
  - 마이그레이션 영향 영역 식별: hil_inference, tests, examples, dgx interactive_cli teleop·record flow
  - 신규 문서: `docs/lerobot_study/08_so100_vs_so101.md` (이관 후 — 원래 `docs/storage/16_so100_vs_so101.md` 로 작성, 게이트 1 walkthrough 시 컨벤션 정합 이관)
- 구현 대상: `docs/lerobot_study/08_so100_vs_so101.md` (신규 + ad-hoc 이관)
- 테스트: code-tester — 두 클래스 코드 인용 정합 + 결정 명시
- 제약: `docs/reference/lerobot/` 직접 수정 X (Category A)
- 잔여 리스크: lerobot upstream 의 SO101 지원이 미완 또는 제한적일 가능성 — study 결과 따라 마이그레이션 보류 결정 가능

#### [x] TODO-R2: 활성 코드 SO100 → SO101 일괄 마이그레이션

**자동화 완료 (2026-05-04)**: 13 파일 (활성 6 + Category B docstring 5 + docs 2). hil_inference·tests·examples·dgx record.py SO101 마이그레이션 + Category B docstring SO100|SO101 병기 보존 + lerobot_setup_motors COMPATIBLE_DEVICES 보존 + Coupled File Rule 03_orin_lerobot_diff.md 갱신 + R1 Recommended 정정 (4→6). code-tester READY (Recommended 2: hil_inference follower_so100 default + smoke_test ruff pre-existing — 모두 비차단) + prod-test AUTOMATED_PASS (orin SO101 import OK, dgx record.py ROBOT_TYPE so101_follower OK).
**잔여 리스크**: calibration JSON 경로 robot_type 의존 (사용자 운영 단계 — Orin 첫 SO101 연결 시 재calibration 또는 JSON 이전).

- 타입: task
- DOD: R1 결과 SO101 채택 결정 시:
  - `orin/inference/hil_inference.py` (SO100Follower → SO101Follower, ROBOT_TYPE 변경)
  - `orin/tests/measure_latency.py`, `orin/tests/smoke_test.py`, `orin/tests/inference_baseline.py`
  - `orin/examples/tutorial/smolvla/using_smolvla_example.py` (예제 코드)
  - `orin/lerobot/scripts/lerobot_*.py` docstring example (SO101 으로 수정 — Category B 영역, lerobot upstream check skill 적용)
  - `dgx/scripts/smoke_test.sh` (해당 시)
  - `dgx/interactive_cli/flows/training.py` (해당 시)
  - 데이터셋 이름 `lerobot/svla_so100_pickplace` 는 외부 자원 → **그대로 유지**
  - `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 갱신 (Coupled File Rule)
- 구현 대상: 위 파일들
- 테스트: code-tester — grep `SO100Follower` `SO100Leader` `so100_follower` `so100_leader` (active 영역, legacy 제외) 0 건. 단 데이터셋 ID `svla_so100_pickplace` 는 허용
- 제약: lerobot-upstream-check skill 적용 (Category B). 단 본 마이그레이션은 *클래스 이름 교체* 라 upstream 코드 직접 수정 X
- 잔여 리스크: SO101 클래스가 upstream 에서 SO100 인터페이스와 차이 있으면 추가 정합 필요 (R1 study 결과 의존)

#### [x] TODO-R3: SO101 마이그레이션 회귀 검증

**자동화 완료 (2026-05-04)**: SSH_AUTO — orin·dgx 양쪽 가용 + deploy_orin·deploy_dgx 자율 실행 + import 회귀 OK (orin: smoke_test·measure_latency·inference_baseline·hil_inference 4 모듈 / dgx: record·training 2 모듈) + SO100 잔재 grep 0건. prod-test AUTOMATED_PASS.

- 타입: test
- DOD: SSH_AUTO — orin·dgx 양쪽에서 import + smoke test 회귀 PASS
  - orin: `python -c "from orin.tests.smoke_test import *"` import 성공
  - dgx: training.py preflight `--steps=1` 더미 (DGX 자율, smoke level)
- 구현 대상: 검증 스크립트 — code-tester 가 grep + import check, prod-test-runner 가 SSH 실행
- 테스트: prod 검증 (SSH_AUTO)
- 제약: —
- 잔여 리스크: SO101 클래스 정합 미달 시 R2 재실행 (code-tester MAJOR cycle 1)

---

### [그룹 H — Hardware 신규 wrist 카메라 (Wave 1, 자율)]

#### [x] TODO-H1: U20CAM-720P 사양 02_hardware §7-1 신규 추가

**자동화 완료 (2026-05-04)**: §7-1 INNO-MAKER U20CAM-720P 사양 15 항목 신규 + §8 카메라 행 "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" 갱신. code-tester READY (Recommended: §7 OV5648 수량 2→1 갱신 — H2 cycle 흡수) + prod-test AUTOMATED_PASS.

- 타입: task
- DOD:
  - `docs/storage/02_hardware.md` §7 (현재 OV5648) 보존, 직후 §7-1 (또는 §7B) 신규 추가:
    - 모델: INNO-MAKER U20CAM-720P
    - 출처: `https://github.com/INNO-MAKER/U20CAM-720P` UserManual v1.0 (2023-10-20)
    - Sensor: 1/4 inch, 1280×720 colors, rolling shutter
    - Lens: F2.2, focal 2.79mm, M12 mount, 18mm seat spacing, FOV-D 120°/FOV-H 102°
    - PCBA: 32×32mm, 4 mounting holes (Φ2.2mm)
    - USB: 2.0 High-Speed, UVC 1.0.0, cable 1m
    - Format: MJPEG / YUY2, 30 fps
    - Resolution: 1280×720 / 800×600 / 640×480 / 320×240
    - 본 프로젝트 용도: **wrist 카메라 1대** (그리퍼 근거리 광각 촬영)
  - §8 "로봇 구성 수량" 카메라 항목에 "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" 명시
- 구현 대상: `docs/storage/02_hardware.md`
- 테스트: code-tester — 신규 §7-1 표 항목 정합, §8 갱신
- 제약: —
- 잔여 리스크: —

#### [x] TODO-H2: overview vs wrist 카메라 다름에 따른 코드·config 영향 검토 + 적용

**자동화 완료 (2026-05-04)**: 검토 결과 코드 변경 0건 — 두 카메라 모두 MJPG 640×480 호환 (record.py / cameras.json / hil_inference.py 분기 불요). 02_hardware §7 OV5648 수량 "1대 (overview, SO-ARM 관측용)" 갱신 (H1 Recommended 흡수) + §9 신규 카메라 비교·키 컨벤션 섹션. BACKLOG 2건 등록 (#1 wrist 광각 분포 차이, #2 wrist flip 미결). code-tester READY (Recommended 1: 카메라 키 불일치 BACKLOG 미등록 → orchestrator BACKLOG #3 흡수) + prod-test AUTOMATED_PASS.
**추가 발견**: DGX record.py `wrist_left`/`overview` 키 vs Orin 데이터셋 `top`/`wrist` 불일치 — BACKLOG #3 (orchestrator 직접 등록).

- 타입: task
- DOD:
  - 검토 영역:
    - `dgx/interactive_cli/flows/record.py` `--robot.cameras` 인자 (현재 overview·wrist 동일 사양 가정 가능성)
    - `orin/config/cameras.json` (slot 별 fourcc·해상도 분기 필요 시)
    - `orin/inference/hil_inference.py` flip 인자 기본값 (wrist 신규 카메라 방향 — wrist 광각이라 plain orientation 일 가능성)
    - 02_hardware §5-2 fourcc=MJPG 패턴 적용 — 두 카메라 모두 MJPEG 지원이므로 그대로
    - calibration: 광각 (102° H) wrist 는 데이터 수집 시 SmolVLM2 vision encoder 분포 차이 → 03 BACKLOG #11 (사전학습 분포 정합) 트리거 가능성 명시
  - 결과:
    - 코드 분기 필요 시 적용 (slot 별 fourcc·해상도 명시)
    - 사양 차이로 인한 향후 잠재 리스크 → BACKLOG 신규 항목 추가
    - 갱신 문서: `docs/storage/02_hardware.md`
- 구현 대상: 위 파일들 (검토 결과 따라)
- 테스트: code-tester — grep + 분기 정합 확인
- 제약: —
- 잔여 리스크: 광각 wrist 가 svla_so100_pickplace 사전학습 분포 (보통 표준 화각) 와 분포 차이 → 후속 사이클 데이터 수집·학습·추론에서 정성 차이 발생 가능. 사후 BACKLOG 추적

---

### [그룹 N — Navigation 뒤로가기 UX (Wave 1, 자율)]

#### [x] TODO-N1: dgx + orin interactive_cli 공통 뒤로가기 패턴 적용

**자동화 완료 (2026-05-04)**: 14 파일 (12 수정 + 2 신규 `flows/_back.py` helper). `b/back` 입력 처리 + 사용자 안내 `(b: 뒤로)`. Category C 회피 (common/ 미생성). MINOR cycle 1: teleop sentinel `return -1` (returncode 충돌 회피) + training `"CANCELED"` sentinel + flow5 early return. code-tester MINOR (3 Recommended) → cycle 1 적용 → prod-test AUTOMATED_PASS.

- 타입: task
- DOD:
  - 모든 prompt 분기점에 "**`b` 또는 `back` 입력 시 직전 분기점으로 복귀**" 동작 추가
  - 적용 영역:
    - `dgx/interactive_cli/flows/`: entry, env_check, mode, precheck, data_kind, record, teleop, training, transfer
    - `orin/interactive_cli/flows/`: entry, env_check, inference
  - entry (0 단계) 에서 `b/back` 입력 시 종료 (또는 메뉴 재표시)
  - 공통 helper 신규 (`flows/_back.py`) — 중복 최소화
  - 사용자 안내 문구: 각 prompt 라인 끝에 `(b: 뒤로)` 등 표기
  - README 갱신: `dgx/interactive_cli/README.md`, `orin/interactive_cli/README.md` UX 섹션
- 구현 대상: 위 flows 들
- 테스트: code-tester — 각 prompt 함수에 `b/back` 분기 존재, helper 호출 일관
- 제약: —
- 잔여 리스크: 일부 flow (예: lerobot-record subprocess 실행 도중) 는 외부 프로세스 진행 중이라 뒤로가기 불가 — 이 경우 "subprocess 종료 후 뒤로가기 가능" 명시 (Ctrl+C 권고)

#### [x] TODO-N2: 뒤로가기 회귀 검증

**자동화 완료 (2026-05-04)**: orin + dgx 배포 성공. _back.py is_back() assert 전 항목 통과 (SSH python/python3). entry.py import OK. 헤드리스 walkthrough orin + dgx 양쪽 b 입력 시 정상 종료. DOD 4항목 전 자동 충족. prod-test AUTOMATED_PASS.

- 타입: test
- DOD: SSH_AUTO — orin·dgx interactive_cli 자동 walkthrough 시 `b/back` 입력 분기 확인 (헤드리스 stdin pipe)
- 테스트: prod-test-runner — `echo -e "1\nb\n0" | bash dgx/interactive_cli/main.sh` 형태 자동 실행 + 종료 코드·로그 검사
- 제약: —
- 잔여 리스크: stdin pipe 와 input() 의 EOF 동작 — 검증 스크립트 신중 작성

---

## Backlog

> 본 spec 의 누적 BACKLOG 항목은 `docs/work_flow/specs/BACKLOG.md` 의 [08_final_e2e] 섹션 참조.
