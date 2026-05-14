# TODO-M2 — Implementation

> 작성: 2026-05-01 14:30 | task-executor | cycle: 1

## 목표

TODO-M1 의 가이드(11_demo_site_mirroring.md)를 따라 DataCollector 인근에 시연장 미러링 1차 셋업 완료. 사진·체크리스트로 결과 기록. 부족한 부분은 BACKLOG 로 관리.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/context/verification_queue.md` | M | `[TODO-M2]` 섹션 추가 — 물리 환경 셋업 시나리오 16개 단계 정의 |
| `docs/work_flow/context/todos/M2/01_implementation.md` | A | 본 파일 — 구현 보고서 |
| `docs/work_flow/context/history/04_infra_setup/20260501_1430_task_m2_setup_scenarios.md` | A | history 기록 |

## 적용 룰

- CLAUDE.md Hard Constraints: docs/reference/ 미변경 ✓
- Category A·B·C·D 모두 해당 없음 (코드 변경 없음, 물리 환경 시나리오 정의만)
- lerobot-reference-usage: 코드 구현 없음 — 레퍼런스 검색 불필요 ✓
- lerobot-upstream-check: orin/lerobot/ 미변경 ✓
- Coupled File Rules: pyproject.toml·setup_env.sh·03_orin_lerobot_diff.md 미변경 ✓

## 사전 점검 결과

**11_demo_site_mirroring.md 자체 충분성 평가**:
- §1 측정 항목: 책상(4개)·작업 영역(3개)·조명(5개)·top 카메라(7개)·wrist 카메라(4개)·토르소·SO-ARM(5개) 모두 표 형식으로 완결
- §2 측정 도구: 줄자·스마트폰 앱 대체 방법 포함, 사용자 책임 명시 ✓
- §3 DataCollector 재현 체크리스트: 7개 단위(책상/조명/top카메라/wrist카메라/토르소·SO-ARM/포트/카메라인덱스) 허용 오차 기준 명시 ✓
- §4 육안+사진 비교 절차: 시연장·DataCollector 사진 세트, 비교 항목, 합격 기준 표 ✓
- §5 05_leftarmVLA 진입 전 게이트: 환경미러링·하드웨어·소프트웨어 3개 게이트 ✓

**보강 필요 부분**: 결과 기록 위치가 11_demo_site_mirroring.md 에 명시되어 있지 않음 → verification_queue.md 에 `docs/storage/others/demo_site_mirroring_<YYYYMMDD>/` 위치 + 4개 파일 구조로 명시 (미세 보강, 별도 파일 수정 불필요)

## 핵심 결정

- 본 todo 는 사용자 직접 영역 — 자동화 워커 책임 X
- 11_demo_site_mirroring.md 가 §1~§5 자체 완결성 충분 → 별도 가이드 문서 추가 불필요
- 시나리오 정의 + verification_queue 위임만으로 task-executor 책임 완료
- 결과 기록 위치: `docs/storage/others/demo_site_mirroring_<YYYYMMDD>/` (사용자 책임)
  - `measurements.md` / `checklist.md` / `photos/` / `comparison_notes.md` 4개 자산

## 변경 내용 요약

본 todo 는 코드 구현이 없는 "사용자 직접 셋업 + 정성 기록" 타입이다. task-executor 의 역할은 사용자가 물리 환경 작업을 수행할 때 따를 수 있는 검증 시나리오를 명확하게 정의하고, 그 결과물의 저장 위치를 지정하는 것에 한정된다.

verification_queue.md 에 `[TODO-M2]` 섹션을 추가하였다. 시나리오는 A~D 4개 블록(총 16단계)으로 구성된다: (A) 시연장 방문+측정, (B) DataCollector 인근 재현, (C) 미러링 검증, (D) 결과 기록. 각 단계는 11_demo_site_mirroring.md 의 §1~§4 절과 1:1 대응하여 사용자가 두 문서를 교차 참조 없이 검증 큐만 보고도 작업을 완료할 수 있도록 구체화하였다.

## code-tester 입장에서 검증 권장 사항

- **시나리오 일관성**: verification_queue.md `[TODO-M2]` 의 16개 단계가 11_demo_site_mirroring.md §1~§4 와 cross-reference 일치 여부 확인
- **허용 오차 수치 정합성**: 단계 5~9 의 ±수치가 §3 체크리스트 원문 수치와 일치 여부 확인 (예: 책상 높이 ±2 cm, 조도 ±100 lux, 색온도 ±300 K, wrist 위치 ±0.5 cm)
- **결과 기록 위치 충돌 없음**: `docs/storage/others/demo_site_mirroring_<YYYYMMDD>/` 가 기존 storage 구조와 충돌하지 않는지 확인 (`docs/storage/others/` 기존 파일 목록과 비교)
- **BACKLOG 04 #6 우선순위**: spec 본문 및 BACKLOG.md 의 #6 항목이 현재 "낮음" — 사용자 미러링 작업 후 부족 발견 시 "중간" 으로 상향 권고 여부 code-tester 판단 (시나리오 정의 범위 내)
- **DOD 충족**: DOD "사진·체크리스트로 결과 기록" 요건이 verification_queue.md D 블록으로 전달되어 있는지 확인

## 잔여 리스크

- 첫 시도에서 정확한 미러링 어려움 (spec 본문 명시) — 05_leftarmVLA 학습 결과로 부족한 부분 진단 가능
- TODO-D3 미완료 시 DataCollector 측 재현 작업(B 블록)이 불완전 — 시연장 측정(A 블록)만 먼저 진행하고 DataCollector 셋업 완료 후 B~D 블록 진행하는 분리 실행 가능
- DataCollector 의 `config/` 경로 (TODO-D1·D2 결정에 따라 `datacollector/config/` 확정 여부) — verification_queue.md 에 `datacollector/config/ports.json` · `cameras.json` 으로 명시하였으나 TODO-D1 결과에 따라 경로 조정 필요할 수 있음
