# TODO-N2 — Implementation

> 작성: 2026-05-04 | prod-test-runner (N2 는 test 타입 — task-executor 구현 없음, prod-test-runner 가 간략 작성)

## 개요

N2 는 N1 (뒤로가기 b/back 일괄 적용) 의 **회귀 검증** todo. 코드 구현 없음. prod-test-runner 가 직접 검증 수행.

## N1 에서 생성된 검증 대상 파일

- `dgx/interactive_cli/flows/_back.py` (신규) — `is_back(raw: str) -> bool` helper
- `orin/interactive_cli/flows/_back.py` (신규) — 동일 코드 (두 노드 독립)
- `dgx/interactive_cli/flows/entry.py` — `is_back()` 호출 2곳 (flow1, detect_display_mode)
- `orin/interactive_cli/flows/entry.py` — `is_back()` 호출 1곳 (flow1)
- 기타 flows 7개 (dgx) + 2개 (orin) — `is_back()` 분기 포함

## 핵심 설계

- `is_back(raw: str) -> bool`: `raw.lower() in ("b", "back")` — strip 은 **caller 책임** (docstring 명시: "input().strip() 결과 문자열")
- entry 최상위(flow 1) 에서 `b` 입력 시 종료 (되돌아갈 상위 없음)
- entry `detect_display_mode()` 에서 `b` 입력 시 자동 검출값으로 진행 (최상위)
