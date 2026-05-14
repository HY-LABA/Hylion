# TODO-P2 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`.gitignore` 에서 datacollector 관련 패턴 2 줄 제거 (Category B, 사용자 동의 완료).

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `.gitignore` | M | L6 `datacollector/.hylion_collector/`, L10 `datacollector/data/` 2 줄 + 수집 데이터셋 comment block 제거 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (read-only 영역 비접촉) ✓
- Category B (.gitignore 패턴 변경): spec 결정 E 사용자 동의 완료 — 1 회 작성 OK ✓
- Coupled File Rule: `.gitignore` 변경은 `orin/pyproject.toml` / `orin/lerobot/` 결합 규칙 해당 없음 ✓
- 레퍼런스 활용: 본 todo 는 파일 패턴 제거 작업 — lerobot reference 패턴 조회 불필요 (SKILL_GAP 없음) ✓

## 변경 내용 요약

`smolVLA/.gitignore` 에서 datacollector 노드가 사용하던 venv 경로 (`datacollector/.hylion_collector/`) 와 수집 데이터셋 경로 (`datacollector/data/`) 를 제거했다. datacollector 는 06 사이클에서 DGX 가 흡수 완료하여 더 이상 독립 노드로 존재하지 않으므로, 해당 패턴은 잔재다.

`datacollector/data/` 항목만 있던 "── 수집 데이터셋 ──" 섹션 header comment (2 줄) 도 함께 제거하여 orphaned comment 가 남지 않도록 했다. 나머지 라인의 정렬·comment 는 손상 없음. venv 섹션은 `orin/.hylion_arm/` + `dgx/.arm_finetune/` 2 줄만 남아 현재 2-노드 구조와 일치한다.

## code-tester 입장에서 검증 권장 사항

- diff 정합성: `git diff .gitignore` 로 L6·L10 (+ comment block) 제거 확인
- 잔재 grep:
  ```
  grep -n "datacollector\|smallgaint" /home/babogaeguri/Desktop/Hylion/smolVLA/.gitignore
  ```
  결과 0 건 확인
- 구문 검증: `.gitignore` 는 별도 lint 불필요 — 빈 줄·주석·패턴 구조 Read 로 육안 확인
- DOD 체크:
  1. L6·L10 2 줄 제거 완료 ✓
  2. `datacollector|smallgaint` 패턴 잔재 grep 0 건 ✓
  3. 다른 라인의 정렬·comment 깨짐 X ✓
