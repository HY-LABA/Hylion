# TODO-M2 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

`docs/work_flow/specs/BACKLOG.md` 정리 — datacollector 관련 항목 모두 "완료(불요)" 마킹 + 사유.
사용자 결정 D (Phase 1 합의) 적용. 05_interactive_cli 섹션 신규 추가.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/specs/BACKLOG.md` | M | 04 #7~#14 상태 갱신 + 05_interactive_cli 섹션 신규 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (Category A) ✓
- BACKLOG.md 는 일반 마크다운 문서 — Category B 비해당, 자율 진행 가능 ✓
- 항목 통째 삭제 X — 사용자 결정 D 에 따라 결정 이력 보존 ✓
- Coupled File Rule: `orin/lerobot/`, `pyproject.toml` 등 미변경 — 갱신 불필요 ✓
- 레퍼런스 활용: 본 todo 는 문서 정합 작업 (마크다운 편집) — lerobot 레퍼런스 코드 참조 불필요. SKILL_GAP 없음 ✓

## §1 처리 항목 표

### 04_infra_setup 섹션 처리 결과

| BACKLOG 행# | 항목 요약 | 처리 결과 | 변경 사유 |
|---|---|---|---|
| 04 #7 | Phase 3 검증 대기 7건 (D3·X3·G2·T1·T2 등) | 일부 완료 (06 결정 적용), 잔여 → 06 V 그룹 통합 | D3 관련 DataCollector 항목 → 불요 (운영 종료). X3·O3·G2·T1·T2 → 06 V 그룹 prod 검증 통합 |
| 04 #8 | G3 — DataCollector check_hardware.sh 이식 | 완료 (06 결정 — 불요, 2026-05-02) | DataCollector 머신 운영 종료. DGX 가 check_hardware 책임 흡수 (06 X3) |
| 04 #9 | G4 — DataCollector check_hardware.sh prod 검증 | 완료 (06 결정 — 불요, 2026-05-02) | DataCollector 머신 운영 종료. DGX 측 검증은 06 V2 통합 |
| 04 #10 | datacollector/scripts/setup_env.sh CPU wheel | 완료 (06 결정 — 불요, 2026-05-02) | datacollector/ 노드 legacy 이관. 해당 파일 legacy/02_datacollector_separate_node/ 에 보관 |
| 04 #11 | DataCollector Python 3.12 셋업 또는 lerobot 옵션 B | 완료 (06 결정 — 불요, 2026-05-02) | DGX 가 데이터 수집 흡수. DGX 는 이미 Python 3.12.3 운영 중 — PEP 695 차단 무관 |
| 04 #12 | DataCollector lerobot-calibrate + flow 0~7 완주 | 완료 (06 결정 — 불요, 2026-05-02) | DataCollector 머신 운영 종료. DGX 측 calibrate 는 06 V2 prod 검증으로 통합 |
| 04 #13 | DataCollector flow 7 분기 3건 실 검증 | 완료 (06 결정 — 불요, 2026-05-02) | DGX flow 7 옵션 H 재정의로 흡수 (06 X1 study). 분기 옵션 재정의 (HF Hub / 로컬 dgx / Orin rsync) |
| 04 #14 | env_check.py NoneType 에러 | 상태 갱신만 (유지) | DGX 환경에서도 재현 가능. 상태: "미완 (06 V2 통합 처리)" — DGX env_check.py 통합 시 진단·수정 |

### 05_interactive_cli 섹션 신규 추가 결과

05 spec 에 "Backlog → BACKLOG.md 에 본 스펙 섹션을 추가하여 운영" 명시되어 있었으나 섹션이 미작성 상태였음. TODO-M2 에서 함께 처리.

| BACKLOG 행# | 항목 요약 | 처리 결과 | 변경 사유 |
|---|---|---|---|
| 05 #1 (신규) | TODO-D3 미완 — datacollector prod 검증 | 완료 (06 결정 — 불요, 2026-05-02) | DataCollector 머신 운영 종료. DGX 측 검증은 06 V2 통합 |
| 05 #2 (신규) | TODO-O3 미완 — orin interactive_cli prod 검증 | 미완 — 06 V 그룹 통합 처리 안내 | Orin 추론 책임 변동 없음. 06 V 그룹 prod 검증에서 통합. 04 G2 포함 |
| 05 #3 (신규) | TODO-X3 미완 — dgx interactive_cli prod 검증 | 미완 — 06 V3 통합 처리 안내 | 06 TODO-V3 (dgx 학습 mode 회귀 검증) 에서 통합. smoke_test·ckpt 케이스 검증 포함 |

## 변경 내용 요약

사용자 결정 D (Phase 1 합의, 2026-05-02) 에 따라 BACKLOG.md 의 04_infra_setup 섹션 datacollector 관련 항목 (#7~#14) 을 처리했다. 핵심 결정은 **DGX 가 데이터 수집 책임을 흡수하고 DataCollector 머신을 운영 종료**하는 것으로, 이에 따라 DataCollector 전용 BACKLOG 항목 (#8·#9·#10·#11·#12·#13) 은 "완료 (06 결정 — 불요)" 로 마킹되었다. #7 은 DataCollector 관련 항목(D3)과 비관련 항목(X3·O3·G2·T1·T2)이 혼재하여 부분 완료 처리했다. #14 (env_check.py NoneType 에러) 는 DGX 환경에서도 재현 가능하여 "미완 (06 V2 통합 처리)" 상태로 유지하고 06 V2 prod 검증 시 진단하도록 안내를 추가했다.

또한 05 spec 에서 "BACKLOG.md 에 섹션 추가" 를 명시했으나 실제로 섹션이 작성되지 않은 상태였음을 발견, 05_interactive_cli 섹션을 신규 추가했다. D3 (DataCollector prod 검증) 은 완료(불요) 처리, O3 (Orin prod 검증) 과 X3 (DGX prod 검증) 는 06 V 그룹 통합 처리 안내를 기록했다.

## code-tester 입장에서 검증 권장 사항

- BACKLOG.md 구조 정합 확인: 표 헤더·행 갱신이 마크다운 테이블 파싱 오류 없이 렌더링되는지
- grep 잔여 확인: `grep -n "미완$" docs/work_flow/specs/BACKLOG.md` — #14, 05 #2, 05 #3 외 datacollector 관련 "미완" 행 없는지 확인
- 결정 이력 보존: 항목 원문이 삭제되지 않고 상태 컬럼만 갱신되었는지 확인
- DOD 충족:
  - 04 #11: "완료 (06 결정 — 불요, 2026-05-02)" 마킹 ✓
  - 04 #12: "완료 (06 결정 — 불요, 2026-05-02)" 마킹 ✓
  - 04 #13: "완료 (06 결정 — 불요, 2026-05-02)" 마킹 ✓
  - 04 #14: "미완 (06 V2 통합 처리)" 상태 갱신 ✓
  - 05 섹션 신규 추가 (D3 완료(불요) / O3·X3 06 V 그룹 통합) ✓

## §2 처리 누락 가능성

### #14 유지 결정 근거

spec DOD 에서 명시: "#14 (env_check.py NoneType) — **유지**: DGX 환경에서도 재현 가능. 06 V2 prod 검증에서 함께 진단·수정". DGX 의 dgx/interactive_cli/flows/env_check.py 가 datacollector/interactive_cli/flows/env_check.py 를 이식하는 구조 (06 X2 todo) 이므로, 동일 NoneType 버그가 DGX 측에서도 재현될 가능성이 높다. 따라서 04 #14 는 "완료(불요)" 가 아닌 "미완 (06 V2 통합 처리)" 로 정확하게 처리했다.

### 04 #7 부분 완료 처리

04 #7 은 DataCollector 관련(D3) + 비관련(X3·G2·T1·T2·시연장·O3) 항목이 단일 행에 혼재. DataCollector 관련 부분만 완료(불요) 처리하고, 나머지는 "06 V 그룹 통합" 안내를 상태 컬럼에 병기했다. 항목 원문은 보존.

### 04 #8·#9·#10 처리 판단

spec DOD 에서 명시적으로 처리 대상이 아니지만 "BACKLOG.md 전체 grep 으로 datacollector·DataCollector 등 모든 행 검출 후 처리" 지시에 따라 처리했다. #8·#9 는 DataCollector check_hardware.sh 전용 항목 (06 결정으로 완전 불요), #10 은 datacollector/scripts/setup_env.sh 전용 항목 (legacy 이관으로 불요).

## §3 잔여 리스크

- **O3·X3 BACKLOG 05 #2·#3**: "06 V 그룹 통합" 으로만 안내됨. 06 spec 의 V 그룹 todo (V1·V2·V3) 가 실물 검증 단계이므로 Phase 3 사용자 검증 시점까지 잔여 상태. 이것은 정상적인 잔여임 (사용자 결정 D 가 "완료(불요)" 지정한 항목이 아님).
- **04 #2 상태 컬럼**: "완료 (2026-05-01 TODO-D2: datacollector/scripts/run_teleoperate.sh 로 최종 이관)" — 이 경로가 이제 legacy 이관되었으므로 상태 설명이 구 경로를 가리킴. 결정 이력 보존 원칙상 수정 불필요 (과거 이력), 단 독자 혼란 가능성 있음. M3 docs/storage 정합 갱신 시 참고 후보.
- **04 #6 "DataCollector 측"**: 04 #6 ("DataCollector 측 사진·조도·색온도 자동 측정") 의 상태는 "미완" 이지만 06 결정으로 이 항목의 맥락이 변경됨. 그러나 항목 자체는 "시연장 미러링 자동 검증 스크립트" 로서 DGX 가 시연장에서 직접 운영할 때도 유효한 개선 항목이라 상태 변경 없이 유지했다.
