# TODO-M2 — Code Test

> 작성: 2026-05-01 14:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 2건 이하 — 즉시 prod-test-runner 진입 가능.
(단, prod-test-runner 자율 영역이 거의 없는 물리 환경 todo 이므로 실질적으로 M2 종료 + verification_queue 사용자 처리로 이행)

## 단위 테스트 결과

```
코드 변경 없음 (순수 문서·시나리오 정의 작업) — pytest 대상 없음.
N.A.
```

## Lint·Type 결과

```
코드 변경 없음 — ruff check / mypy 대상 없음.
N.A.
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. TODO-M1 가이드대로 1차 셋업 완료 시나리오 정의 | ✅ | verification_queue.md [TODO-M2] A~D 4블록 16단계로 정의. §1·§2·§3·§4 cross-reference 명확 |
| 2. 사진·체크리스트 결과 기록 가이드 | ✅ | D블록 15번에 4파일(measurements.md / checklist.md / photos/ / comparison_notes.md) 저장 위치 및 내용 명시 |
| 3. 부족한 부분 BACKLOG 관리 안내 | ✅ | D블록 16번에 BACKLOG.md § [04_infra_setup] 추가 안내. BACKLOG 04 #6 우선순위 "낮음" 유지 (01_implementation.md 명시) |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `verification_queue.md` [TODO-M2] B블록 10·11번 | `datacollector/config/ports.json`·`cameras.json` 경로가 TODO-D1 미결 상태에서 단정 기재됨. 잔여 리스크로 01_implementation.md 에 명시되어 있으나 verification_queue 내에도 "TODO-D1 결과에 따라 경로 조정 필요" 주석 한 줄 추가 권장 |
| 2 | `verification_queue.md` [TODO-M2] prod-test-runner 결과 요약 | §5 소프트웨어 게이트의 자동화 가능 영역(DataCollector 셋업 후 lerobot-record dry-run 등)이 M2 섹션 어디에도 언급되지 않음. 이 영역은 TODO-D3 담당이어서 M2 DOD 범위 밖이지만, 전제 조건 또는 잔여 리스크 항목에 "§5 소프트웨어 게이트는 TODO-D3 완료 후 별도 처리" 한 줄 명시하면 사용자 혼란 방지 가능 |

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/ 미변경 |
| B (자동 재시도 X) | ✅ | orin/lerobot/, pyproject.toml, setup_env.sh, deploy_*.sh, .gitignore 모두 미변경 |
| Coupled File Rules | ✅ | Category B 영역 미변경이므로 coupled file 갱신 의무 없음 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | task-executor 가 docs/storage/ 직접 수정한 파일 없음. verification_queue.md 는 docs/work_flow/context/ 하위라 이 룰 무관 |

## M1 §1~§4 Cross-Reference 검증

| M1 섹션 | verification_queue 대응 | 수치 정합성 |
|---|---|---|
| §1 시연장 측정 항목 (1-1~1-6) | A블록 2번 — 6개 카테고리 전체 열거 | ✅ 항목 누락 없음 |
| §2 측정 도구 | A블록 3번 — 줄자·스마트폰·조도계·색온도계·각도 앱·메모지 | ✅ 일치 |
| §3 체크리스트 7단위 (3-1~3-7) | B블록 5~11번 — 7단계 1:1 매핑 | ✅ 허용 오차 수치 완전 일치 (±2 cm / ±100 lux / ±300 K / ±3° / ±0.5 cm / ±2°) |
| §4-1 사진 비교 절차 | A블록 4번(시연장 사진) + C블록 12번(DataCollector 사진) + 13번(나란히 비교) | ✅ 3단계 구조 충실히 재현 |
| §4-2 합격 기준 4항목 | C블록 13번 4개 항목 | ✅ 책상 배경·작업 영역·조명 색조·카메라 앵글 4항목 원문과 일치 |
| §3 결과 기록 | D블록 15번 4파일 구조 | ✅ M1 §4-3 BACKLOG 메모 + 01_implementation.md 핵심 결정과 일관 |

## 사용자 책임·자동화 영역 분리 검증

| 영역 | 상태 |
|---|---|
| 시연장 방문 (사용자 일정) | ✅ A블록 1번 — 사용자 일정 명시 |
| 사진 촬영 (사용자 직접) | ✅ A블록 4번, C블록 12번 — 사용자 책임 명시 |
| DataCollector 인근 셋업 (사용자 직접) | ✅ B블록 5~11번 — 사용자 직접 작업 |
| 사진 비교·재조정 (사용자 직접) | ✅ C블록 13~14번 — 사용자 책임 명시 |
| 결과 기록 (사용자 직접) | ✅ D블록 — "(사용자 책임)" 명시 |
| 자동화 가능 영역 명시 | ⚠️ prod-test-runner 결과 요약에 "자동화 영역 X"로만 기재. §5 lerobot-record dry-run 자동화 영역이 M2 섹션 내에서 비가시적 (Recommended #2) |

## 결과 저장 위치 합리성

- `docs/storage/others/demo_site_mirroring_<YYYYMMDD>/` 채택 — docs/storage/others/ 기존 파일 목록과 충돌 없음 (ckpt_transfer_scenarios.md, run_teleoperate.sh.archive 등 별도 파일명)
- 날짜 기반 디렉터리 분리로 재방문 시 결과 누적 가능
- 4파일 구조(measurements.md / checklist.md / photos/ / comparison_notes.md)가 §1·§3·§4 각 결과물과 1:1 대응 — 합리적

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장. 단, 본 todo 특성상 prod-test-runner 자율 실행 가능 영역이 없음 (물리 환경 셋업). verification_queue.md [TODO-M2] 사용자 처리로 바로 이행 가능.
