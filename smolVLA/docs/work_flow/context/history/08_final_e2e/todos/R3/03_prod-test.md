# TODO-R3 — Prod Test

> 작성: 2026-05-04 16:30 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

---

## 배포 대상

- orin + dgx 둘 다

## 배포 결과

| 대상 | 명령 | 결과 |
|---|---|---|
| orin | `bash scripts/deploy_orin.sh` | 성공 (5,548 bytes sent, speedup 226.91) |
| dgx | `bash scripts/deploy_dgx.sh` | 성공 (dgx 1,174 bytes + lerobot 27,024 bytes, speedup 437.60) |

- orin 배포 소스 크기: 1.9MB (100MB 미만 — 자율 배포 해당)
- dgx + lerobot 소스 크기: 14MB (100MB 미만 — 자율 배포 해당)
- Category B 영역 변경 없음 (R3 는 검증 전용, 코드 변경 0)

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| SSH 가용 — orin | `ssh -o ConnectTimeout=5 orin "echo orin_ok"` | orin_ok (PASS) |
| SSH 가용 — dgx | `ssh -o ConnectTimeout=5 dgx "echo dgx_ok"` | dgx_ok (PASS) |
| orin smoke_test import | `ssh orin python -c "importlib.import_module('orin.tests.smoke_test')"` | import OK + 전체 smoke test 통과 (SmolVLAPolicy 더미 추론 성공) |
| orin measure_latency import | `ssh orin python -c "importlib.import_module('orin.tests.measure_latency')"` | import OK |
| orin inference_baseline import | `ssh orin python -c "importlib.import_module('orin.tests.inference_baseline')"` | import OK |
| orin hil_inference import | `ssh orin python -c "importlib.import_module('orin.inference.hil_inference')"` | import OK |
| dgx flows.record import | `ssh dgx (cd interactive_cli && python -c "importlib.import_module('flows.record')")` | import OK |
| dgx flows.training import | `ssh dgx (cd interactive_cli && python -c "importlib.import_module('flows.training')")` | import OK |
| SO100 잔재 0건 | `grep -rn "SO100Follower\|SO100Leader" ...` | 0건 (PASS) |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. orin: `from orin.tests.smoke_test import *` import 성공 | ssh orin importlib.import_module | ✅ |
| 2. orin: measure_latency, inference_baseline, hil_inference import 성공 | ssh orin importlib.import_module x3 | ✅ |
| 3. dgx: flows.record import 성공 | ssh dgx importlib.import_module | ✅ |
| 4. dgx: flows.training import 성공 | ssh dgx importlib.import_module | ✅ |
| 5. 활성 SO100 잔재 0건 | grep 안전망 | ✅ |

사용자 실물 검증 필요 항목: 0개

---

## 사용자 실물 검증 필요 사항

없음. R3 는 SSH_AUTO import 회귀 검증이며 전 항목 자동으로 충족.

---

## 검증 중 발견 사항

- **dgx import 경로 관찰**: `dgx/interactive_cli/` 에 `__init__.py` 없음 — `dgx.interactive_cli.flows.record` 방식 import 불가. `cd dgx/interactive_cli && python -c "from flows.record import ..."` 패턴 (R2 기준 동일) 이 올바른 방식. DOD 비차단 — R2 때와 동일 환경.
- **orin smoke_test import 시 전체 smoke 실행**: `importlib.import_module('orin.tests.smoke_test')` 가 module-level 코드를 실행하여 SmolVLAPolicy 로드 및 더미 추론까지 수행 — 추가 검증 가치 (DOD 초과 달성).

---

## CLAUDE.md 준수

- Category A 영역 수정: 없음 (검증 전용)
- Category B 영역 변경된 deploy: 없음 (R3 코드 변경 0)
- 자율 영역만 실행: yes (ssh read-only + import check + deploy — 100MB 미만, 5분 미만)
- 큰 다운로드 기준: orin 1.9MB + dgx 14MB — 자율 범위
