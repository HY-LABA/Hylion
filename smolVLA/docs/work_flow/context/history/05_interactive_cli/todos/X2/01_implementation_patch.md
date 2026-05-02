# TODO-X2 — Implementation Patch

> 작성: 2026-05-01 | task-executor | MINOR_REVISIONS patch (재검증 X)

## 목표

code-tester MINOR_REVISIONS Recommended 4건 수정 — ruff F401·F541 제거 + CKPT_CASES 케이스 4 추가.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/training.py` | M | F401 (import os 제거) + F541 5건 + CKPT_CASES 케이스 4 추가 + _show_ckpt_management 종료 번호 동적 처리 |

## 적용 룰

- CLAUDE.md Hard Constraints: docs/reference/ 미변경, .claude/ 미변경
- Coupled File Rules: dgx/lerobot/ 미변경 → 04_dgx_lerobot_diff.md 갱신 불필요. pyproject.toml 미변경 → 02_orin_pyproject_diff.md 갱신 불필요
- Category B: dgx/interactive_cli/ 는 Category B 비해당 (신규 파일 영역)

## 변경 내용 요약

### Rec 1 — F401 `import os` 제거

`_run_real_training` 함수 내 line 435 의 `import os` 지역 import 제거. `dgx_dir = str(script_dir.parent)` 는 `script_dir` 이 `Path` 객체이므로 `os` 없이 동작. 기능 변경 없음.

### Rec 2 — F541 f-string prefix 5건 제거

다음 5개 위치에서 placeholder 없는 불필요한 `f` prefix 제거 (`f"..."` → `"..."`):
- line 213: `print(f"  smoke test 는 고정 데이터셋을 사용합니다:")`
- line 227: `print(f"     예: lerobot/svla_so100_pickplace")`
- line 235: `print(f"  4. 종료")`
- line 503: `print(f"  학습 출력 디렉터리:")`
- line 518: `print(f"  4. 종료 (전송 안 함)")`  (구조 변경으로 내용도 갱신됨)

기능 변경 없음.

### Rec 3 — CKPT_CASES 케이스 4 (USB) 추가

`sync_ckpt_dgx_to_datacollector.sh` line 22 인용:
```
케이스 4: Orin USB 드라이브만 가능 → USB 절차 (docs/storage/others/ckpt_transfer_scenarios.md §4)
```

CKPT_CASES 딕셔너리에 키 `"4"` 항목 추가:
- `label`: "케이스 4 — USB 드라이브 전송"
- `guide`: `ckpt_transfer_scenarios.md §4` 참조 안내 + 스크립트 line 22 인용

`_show_ckpt_management` 내 종료 번호를 하드코딩 `"4"` 에서 `len(case_keys) + 1` 동적 계산으로 변경. 케이스 4 추가 후 종료는 "5" 로 자동 변환. 프롬프트 `[1~4]` 도 `[1~{quit_num}]` 동적 처리.

이로써 14_dgx_cli_flow.md §5-2 케이스 분류(1~4) 와 CKPT_CASES 가 완전 정합됨.

### Rec 4 — flow5 smoke 실패 안내

code-tester 판정: "현재 '`smoke test 실패. smoke_test.sh 출력을 확인하세요.`' 는 있음 — 문제 없음, trivial". 추가 변경 불필요.

## self-check 결과

```
python3 -m py_compile dgx/interactive_cli/flows/training.py  -> OK
python3 -m ruff check dgx/interactive_cli/flows/training.py  -> All checks passed!
CKPT_CASES keys: ['1', '2', '3', '4']  -> 케이스 1·2·3·4 모두 포함 확인
```
