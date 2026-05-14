# TODO-N2 — Prod Test

> 작성: 2026-05-04 15:30 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

## 배포 대상

- orin + dgx 양쪽

## 배포 결과

| 대상 | 명령 | 결과 |
|---|---|---|
| orin | `bash scripts/deploy_orin.sh` | 성공 — 16,107 bytes sent, speedup 70.60 |
| dgx | `bash scripts/deploy_dgx.sh` | 성공 — 15,521 bytes sent (dgx 코드), 26,840 bytes (lerobot ref) |

## 자동 비대화형 검증 결과

### 1. is_back() 시그니처 확인 (코드 리뷰)

함수 정의: `return raw.lower() in ("b", "back")`
Docstring: `raw: input().strip() 결과 문자열` — strip 은 caller 책임.
`"  B  "` (미strip) → `False` (설계 의도: 정상 동작, caller 가 strip 후 전달)

### 2. _back.py assert 검증 (orin + dgx SSH)

| 검증 | 명령 | 결과 |
|---|---|---|
| orin _back assert | `ssh orin python -c "assert is_back('b'); is_back('back'); ..."` | PASS (전 assert 통과) |
| dgx _back assert | `ssh dgx python3 -c "assert is_back('b'); is_back('back'); ..."` | PASS (전 assert 통과) |

검증 항목:
- `is_back("b")` → `True`
- `is_back("back")` → `True`
- `is_back("B")` → `True` (대소문자 무관)
- `is_back("BACK")` → `True`
- `is_back("1")` → `False`
- `is_back("")` → `False`
- `is_back("b ")` → `False` (trailing space — strip 은 caller 책임, 정상)

### 3. entry.py import 검증

| 검증 | 명령 | 결과 |
|---|---|---|
| orin entry import | `ssh orin python -m flows.entry` (import only) | OK — VALID_NODES: ('orin', 'dgx') |
| dgx entry import | `ssh dgx python3 -m flows.entry` (import only) | OK — VALID_NODES: ('orin', 'dgx') |

### 4. SSH 헤드리스 walkthrough — b 입력 뒤로가기 (flow 1 진입 최상위 → 종료)

| 검증 | 명령 | 결과 |
|---|---|---|
| orin b → 종료 | `printf "b\n" \| python3 -m flows.entry --node-config <abs>` | "종료합니다." 출력 후 정상 종료 |
| dgx b → 종료 | `SMOLVLA_DISPLAY_MODE=ssh-file printf "b\n" \| python3 -m flows.entry --node-config <abs>` | "종료합니다." 출력 후 정상 종료 |
| dgx main.sh b → 종료 | `printf "b\n" \| bash interactive_cli/main.sh` | "종료합니다." 출력 후 정상 종료 |

### 5. SSH 연결 상태

| 노드 | 결과 |
|---|---|
| orin | `orin_ok` 응답 확인 |
| dgx | `dgx_ok` 응답 확인 |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| orin·dgx interactive_cli 자동 walkthrough `b/back` 분기 확인 | SSH 헤드리스 (stdin pipe) | ✅ |
| flow 1 진입 최상위에서 b → 종료 | orin + dgx 양쪽 확인 | ✅ |
| _back helper 동작 정합 | SSH assert 검증 | ✅ |
| entry.py 양쪽 정상 import | SSH import 테스트 | ✅ |

## 비차단 관찰 사항

- orin `main.sh` 실행 시 `LD_LIBRARY_PATH: 바인딩 해제한 변수` 경고 출력 (set -u 에서 venv activate 의 LD_LIBRARY_PATH 미초기화 변수 경고). Python 실행은 정상 진행되므로 기능 차단 아님. N1 변경과 무관한 기존 동작.
- dgx `--node-config configs/node.yaml` (상대 경로) 직접 호출 시 `preflight_check.sh` 경로 해석 실패. `main.sh` 경유 (절대 경로 자동 전달) 시 정상. N2 DOD 범위 외 (N1 변경과 무관).

## 사용자 실물 검증 필요 사항

없음. DOD 항목 모두 자동으로 충족 가능.

## CLAUDE.md 준수

- Category B 영역 변경된 배포: 해당 없음 (N1 변경 영역은 `interactive_cli/flows/` — Category B 외)
- 자율 영역만 사용: yes (ssh read-only 검증 + pytest/python -c + deploy_*.sh 자율 범위)
- 큰 다운로드·긴 실행 없음
