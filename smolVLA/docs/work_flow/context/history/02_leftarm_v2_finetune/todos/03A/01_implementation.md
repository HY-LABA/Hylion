# TODO-03-A — Implementation

> 작성: 2026-05-17 | task-executor | cycle: 1

## 목표

M1.5 prof_computer 학습 결과 (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) 의 Orin 추론 성능평가를 위한 평가 시트 문서 신규 작성. 사용자가 Phase 3 시연장에서 실 Orin + 좌측 SO-101 으로 20 trial 추론 수행 시 직접 기록하는 양식.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `prof_computer/docs/orin_a2_eval_2026-05-17.md` | 신규 (N) | 20 trial 평가 시트 — 메타·기준 안내·trial 표·집계 표·정성 메모·다음 단계 섹션 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/`, `.claude/` 미변경 ✓
- Category B 미해당: `orin/lerobot/`, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `scripts/deploy_*.sh` 모두 미수정 ✓
- Category C 미해당: `prof_computer/docs/` 는 실존 디렉터리 — 신규 디렉터리 생성 없음 ✓
- Coupled File Rules: 코드·pyproject.toml·orin/lerobot/ 미변경으로 02·03 diff 문서 갱신 의무 미해당 ✓
- 레퍼런스 활용 (lerobot-reference-usage skill): 본 작업은 문서 작성 — 코드 구현 아님. task instruction 문자열은 `dgx/docs/finetune/leftarm_v2/collection_log.md` §데이터셋 개요 정본 직접 Read 및 인용.
  - task1: `"Pick up the blue and yellow doll and place it on the left side of the table"` (collection_log.md line 15)
  - task2: `"Hand the yellow can to the person"` (collection_log.md line 16)

## 변경 내용 요약

`prof_computer/docs/orin_a2_eval_2026-05-17.md` 를 신규 작성했다. 평가 시트는 6개 섹션으로 구성된다: (1) 메타 — ckpt 정보·학습 요약·spec/plan 링크, (2) 평가 기준 안내 — 지표·시나리오·task instruction 정본·성공 정의·실패 원인 분류 5종·재시도 정책, (3) trial 기록 표 — 4개 그룹 헤더 (task1×front, task1×back, task2×front, task2×back) × 5행씩 20행, 열은 trial#·task·orientation·성공(✅/❌)·실패 원인 분류·자유 메모, (4) 결과 집계 표 — task×orientation 별 성공/총 + success rate 행 + task1 total·task2 total·전체 total, (5) 종합 정성 메모 — task 구분 응답성·6:4 편향 관찰·동작 품질·M2 진입 가치 판단, (6) 다음 단계 — `/verify-result` 명령 형식과 결과별 분기 안내.

task instruction 은 `collection_log.md` 정본 직접 Read 로 확인했으며, 6:4 편향 (front:back) 수치는 동일 문서의 Orientation 합계 표 기반 (task1: front 30/back 20, task2: front 40/back 20). 학습 메타 (75K step, loss 0.04, 100ep subset) 는 `prof_computer/docs/learning_log.md` §M1.5 중간점검 학습 직접 Read 로 인용.

## code-tester 입장에서 검증 권장 사항

- 문서 구조: 20 trial 표 (4개 그룹 헤더 + 각 5행) 존재 여부
- task instruction 정합: `collection_log.md` 의 task1·task2 문자열과 시트 내 기재 일치 여부
- 집계 표: 7행 (task1 front, task1 back, task1 total, task2 front, task2 back, task2 total, 전체 total) 구조 확인
- 성공 정의·실패 분류: task1 (테이블 왼쪽), task2 (사람에게 전달) 정의 명시 여부
- 다음 단계 `/verify-result` 안내 + 50%+/0~20% 분기 기준 포함 여부
- 링크 정합: spec (`docs/work_flow/specs/02_leftarm_v2_finetune.md`) + plan (`docs/work_flow/context/plan.md`) + learning_log 상대 링크 형식 확인

## 결정 / 가정

| 항목 | 결정 | 근거 |
|---|---|---|
| task instruction 문자열 | `collection_log.md` 정본 직접 인용 | plan.md 가정 1 확인 완료 |
| trial 번호 연속성 | 1~20 연속 (그룹 내 재시작 X) | 집계 시 추적 용이 |
| ✅/❌ 선택 형식 | 두 심볼 모두 표기, 사용자가 해당 심볼 삭제 방식으로 기록 | 모바일·노트북 양쪽 편의 |
| 무효 trial 처리 | 분모 조정 방식 (집계 표 각주로 안내) | 하드웨어 귀책 이슈 대비 |
| Coupled Rules §6 (README 신설) | 생략 | `prof_computer/docs/` 단순 파일 추가 — 디렉터리 구조 변경 아님. BACKLOG 메모 권장 |

## 잔여 리스크

- `prof_computer/docs/` 에 README.md 가 없음 — 파일 목적·구조 파악에 불편 가능성. 향후 README 신설 권장 (BACKLOG 후보).
- 평가 시트의 집계 표는 사용자가 수동 계산하여 채우는 방식 — 자동화 계산 없음. 20 trial 이므로 수동 집계 부담 낮음.
