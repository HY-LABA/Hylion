# TODO-M1 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

`arm_2week_plan.md` 본문 갱신 — 4-노드 (DataCollector 별도) 가정 → 3-노드 (DGX 흡수) 로 정정 + spec 시프트 반영.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `/home/babogaeguri/Desktop/Hylion/smolVLA/arm_2week_plan.md` | M | 장비 역할 분담 갱신 + 04·05 마일스톤 주석 + 06 신규 추가 + 06~09 → 07~10 시프트 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: 해당 없음 (arm_2week_plan.md 는 단순 마크다운 문서, Category B 비해당) ✓
- 레퍼런스 활용: 코드 변경 없음 — 문서 갱신만. lerobot-reference-usage SKILL 비적용 (마크다운 갱신) ✓
- 역사적 결정 보존 원칙: 04·05 본문 텍스트 완전 삭제 X — HTML 주석으로 정정 경위 추가 ✓

## §1 변경 위치

### 장비 역할 분담 절

- `DGX Spark` 항목에 `+ 데이터 수집 + 시연장 직접 이동 운영` 명시
- HTML 주석으로 DataCollector → DGX 흡수 결정 경위 + legacy 경로 안내
- blockquote(`> *legacy:...`) 로 DataCollector 자산 위치 (`docs/storage/legacy/02_datacollector_separate_node/`) 참조
- 운영 원칙 "학습 성능 실험" → "학습 성능 실험 및 데이터 수집" 으로 1 줄 갱신

### 04_infra_setup 마일스톤 본문

- 마일스톤 제목 직후 HTML 주석 삽입: 06_dgx_absorbs_datacollector 사이클에서 DGX 흡수로 정정됨 + 본문 텍스트는 04 결정 시점 그대로 보존 안내
- 본문 텍스트 (목표·배경·주요 작업·결정사항) 완전 보존 — 삭제 X

### 05_interactive_cli 마일스톤 본문

- 마일스톤 제목 직후 HTML 주석 삽입: datacollector 측 flow (datacollector/interactive_cli/) 는 06 흡수로 전환됨 + 장치 선택 옵션 orin/dgx 2 옵션으로 축소 (06 X2 처리) 안내
- 마일스톤 `위치` 절 문장 갱신: 06 흡수 후 dgx/interactive_cli/ 가 수집·학습 두 모드 통합 + 07_leftarmVLA 진입 준비 완료로 정정

### 06_dgx_absorbs_datacollector 마일스톤 신규 추가

- 위치: 05_interactive_cli 와 07_leftarmVLA(구 06) 사이
- 내용: 목표·주요 결정 사항 (A~F, spec §사용자 결정 사항 표 핵심 인용) + 주요 작업 그룹 (L·M·X·V) + 배경 (Python 3.12 차단·시연장 미러링 원칙) + spec 파일 경로

## §2 시프트 매핑 표

| 구 번호 | 신 번호 | 마일스톤명 | 시프트 사유 | 주석 추가 위치 |
|---|---|---|---|---|
| 06 | 07 | leftarmVLA | 06_dgx_absorbs_datacollector 삽입 | 마일스톤 제목 직후 HTML 주석 |
| 07 | 08 | biarm_teleop_on_dgx | 동상 | 마일스톤 제목 직후 HTML 주석 |
| 08 | 09 | biarm_VLA | 동상 | 마일스톤 제목 직후 HTML 주석 |
| 09 | 10 | biarm_deploy | 동상 | 마일스톤 제목 직후 HTML 주석 |

각 시프트 마일스톤 내 DataCollector 언급 정정:

| 마일스톤 | 기존 표현 | 정정 표현 |
|---|---|---|
| 07_leftarmVLA | `데이터 수집(DataCollector)` | `데이터 수집 (DGX 데이터 수집 흡수)` |
| 07_leftarmVLA | `04 에서 셋업된 DataCollector 의 시연장 미러링 환경에서 데이터 수집` | `DGX (데이터 수집 흡수) 가 시연장 이동 환경에서 데이터 수집 (06 결정으로 DataCollector 역할 통합)` |
| 08_biarm_teleop_on_dgx | `DataCollector 기준` | `DGX 데이터 수집 흡수 기준` |
| 08_biarm_teleop_on_dgx 내 결정사항 번호 | `07 진행 중 확정` | `08 진행 중 확정` |
| 08_biarm_teleop_on_dgx 고려사항 | `08 학습 시` | `09 학습 시` |
| 07_leftarmVLA 위치 절 | `08 양팔 학습의 사전 단계가 아니다 (08 은 양팔 데이터로...)` | `09 양팔 학습의 사전 단계가 아니다 (09 는 양팔 데이터로...)` |

## §3 역사적 결정 보존 방식

모든 역사적 결정 (04·05 결정 시점 가정) 은 **본문 텍스트 완전 보존** 원칙으로 처리:

1. **삭제 X**: 04 의 "DataCollector 별도 노드" 가정 본문 (목표·배경·주요 작업·결정사항) 은 원문 그대로 유지
2. **HTML 주석으로 정정 경위 추가**: `<!-- *본 가정은 06_dgx_absorbs_datacollector 사이클에서 DGX 흡수로 정정됨 (2026-05-02). 본문 텍스트는 04 결정 시점 그대로 보존...* -->` 방식
3. **blockquote 로 legacy 경로 안내**: 장비 역할 분담 절에 `> *legacy: DataCollector...` 로 이관 경로 명시
4. **시프트 마일스톤 내부 정정은 인라인**: 07~10 마일스톤 내 DataCollector 언급은 본문 내 표현 직접 교체 + 마일스톤 제목 직후 HTML 주석으로 "구 번호·정정 사유" 명시

이 방식으로 04·05 진행 시점 의사결정 맥락을 잃지 않으면서, 현재 상태 (3-노드) 를 명확히 반영.

## §4 잔여 리스크

| 항목 | 내용 | 담당 |
|---|---|---|
| README 색인 갱신 | `docs/work_flow/specs/README.md` 의 spec 시프트 (06→07 등) 반영 미완 | M3 |
| docs/storage/README.md | datacollector 관련 3 파일 (07·10·15) legacy 이관 표기 미완 | M3 |
| BACKLOG.md 정리 | 04 BACKLOG #11·#12·#13 + 05 미검증 항목 "완료(불요)" 마킹 미완 | M2 |
| arm_2week_plan.md 내 기존 datacollector 경로 하드코딩 잔재 | `scripts/sync_dataset_collector_to_dgx.sh` 등이 05_interactive_cli 본문에 남아 있지 않은지 추가 grep 권고 | M3 또는 code-tester |
| 07_leftarmVLA 위치 절 "06_leftarmVLA" 명시 여부 | spec README 에 spec 번호 색인 갱신 전까지 과거 번호 혼재 가능 | M3 |

## 변경 내용 요약

`arm_2week_plan.md` 는 프로젝트 전체 마일스톤 로드맵 문서로, 06_dgx_absorbs_datacollector spec 의 결정 (DataCollector → DGX 흡수, 3-노드 구조) 이 반영되지 않은 상태였다. 본 TODO 에서 (1) 장비 역할 분담 절을 DGX 3-노드 구조로 정정하고, (2) 04·05 마일스톤에 역사적 결정 보존 주석을 삽입하고, (3) 06_dgx_absorbs_datacollector 신규 마일스톤을 추가하고, (4) 기존 06~09 를 07~10 으로 시프트하면서 내부 DataCollector 언급을 DGX 흡수 표현으로 정정했다. 본문 텍스트 완전 삭제 없이 HTML 주석 + blockquote 방식으로 역사적 결정 정보 손실을 방지했다.

## code-tester 입장에서 검증 권장 사항

- 마일스톤 번호 연속성: 00→01→02→03→04→05→06→07→08→09→10 순서 확인
- 06_dgx_absorbs_datacollector 마일스톤 내 §사용자 결정 사항 인용 (A~F) 이 spec 원문과 일치하는지 확인
- 04 마일스톤 본문 텍스트 완전 보존 여부 (DataCollector 별도 노드 가정 4-노드 표현 존재 확인)
- 05 마일스톤 내 datacollector/interactive_cli/ 경로 언급이 그대로 보존되어 있는지 (역사적 보존) + HTML 주석으로 흡수 안내 추가 여부 확인
- 07~10 마일스톤 각각에 "구 번호·시프트 사유" HTML 주석 존재 여부
- DataCollector 미언급 잔재: 07_leftarmVLA 이후 마일스톤 내부 DataCollector 언급이 DGX 흡수 표현으로 정정되었는지
- legacy 경로 참조 정확성: `docs/storage/legacy/02_datacollector_separate_node/` 경로가 실제 L2 이관 결과와 일치하는지
