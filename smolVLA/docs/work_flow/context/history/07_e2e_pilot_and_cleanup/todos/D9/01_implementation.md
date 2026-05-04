# TODO-D9 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

precheck.py `_run_calibrate` 가 ports.json 로드 + default 적용하도록 수정 (docstring 의도 누락 fix)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/precheck.py` | M | `_run_calibrate` 시그니처 변경 + ports.json 로드 로직 추가 + 호출 위치 수정 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: `orin/lerobot/` 미변경 — 03_orin_lerobot_diff.md 갱신 불필요 ✓
- 레퍼런스 활용: 동일 파일 내 `_run_find_port_self` (L375~379) 의 ports.json 로드/저장 패턴 기반 구현. 별도 레퍼런스 파일 참조 불필요 — 기존 `_load_json_or_default`, `_PORTS_FILENAME`, `_PORTS_DEFAULT` 상수 이미 존재.
- Category B 해당 없음 (precheck.py 는 `dgx/interactive_cli/flows/` — orin/lerobot 이나 pyproject.toml 아님)

## 변경 내용 요약

`_run_calibrate()` 는 docstring (L967) 에서 "포트값은 configs/ports.json 에서 로드. 미설정 시 사용자에게 입력 요청"이라고 명시했으나, 실제 구현은 ports.json 를 전혀 읽지 않고 `_prompt(...) or "/dev/ttyACM1"` (hardcoded fallback) 을 사용했다. 이로 인해 precheck 의 `_run_find_port_self` 가 follower=/dev/ttyACM0 을 ports.json 에 저장했음에도, 이후 calibrate 단계에서 hardcoded ttyACM1 을 follower 포트로 사용 → SerialException.

수정 내용:
1. `_run_calibrate` 시그니처 `() → (configs_dir: Path)` 로 변경
2. 함수 내부에 ports.json 로드 블록 추가 (D9 fix 주석 명시):
   - `ports_path.exists()` 확인 후 `json.load` → `follower_port` / `leader_port` 키 읽기
   - 읽기 성공 시 `ports_source = "ports.json 검출 결과"` — prompt 안내 문자열에 source 표시
   - `json.JSONDecodeError | OSError` 시 경고 출력 + hardcoded fallback 유지
3. `_prompt` 인자를 f-string 으로 변경 — `(Enter={ports_default_follower}, source: {ports_source})`
4. `teleop_precheck` 내 호출 위치 L1139 를 `_run_calibrate(configs_dir)` 로 수정
   (`configs_dir` 는 `teleop_precheck` 에서 L1064 에 이미 정의됨)

## code-tester 입장에서 검증 권장 사항

- 문법: `python -m py_compile dgx/interactive_cli/flows/precheck.py` → PASS 확인
- lint: `ruff check dgx/interactive_cli/flows/precheck.py` → All checks passed 확인
- 시뮬 시나리오 (인라인 스크립트):
  1. ports.json 존재 + follower=/dev/ttyACM0 → prompt default 가 ttyACM0 (PASS)
  2. ports.json 미존재 → hardcoded ttyACM1 fallback (PASS)
  3. ports.json JSON 파싱 실패 → 경고 + hardcoded fallback (PASS)
  4. 사용자 override (직접 입력) → 입력값 우선 (PASS)
- DOD 항목 확인:
  - ports.json 로드 + default 적용 ✓ (시나리오 1)
  - ports.json 미존재/파싱 실패 시 hardcoded fallback + 경고 ✓ (시나리오 2/3)
  - 시그니처 변경 + 호출 위치 수정 ✓ (L960, L1156)
  - py_compile + ruff PASS ✓

## DGX deploy 준비

- prod-test-runner 가 `deploy_dgx.sh` 실행 후 walkthrough 재시도
- 검증 포인트: `teleop_precheck` 옵션 (1) 선택 → find-port 완료 후 calibrate 재실행 → follower prompt 에 ports.json 검출 결과 (ttyACM0) 가 default 로 표시되는지 확인
