# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-25 20:58 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 01

## 테스트 목표

Orin 환경 재검증 — `smoke_test.py` 에러 없이 완료되고 smolVLA 모델 forward pass 성공 확인

**배경:** 이전 blocked는 devPC에서 직접 실행 시도한 오탐. `/home/babogaeguri/smolvla/.venv`는 devPC 경로로 없는 것이 정상. SSH 경유 Orin에서 재테스트 필요.

## DOD (완료 조건)

- `smoke_test.py` 에러 없이 완료
- smolVLA 모델 forward pass 성공 (action tensor 출력 또는 성공 메시지 확인)

## 환경

- Orin JetPack 6.2.2 | Python 3.10 | venv `~/smolvla/.venv`
- 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/`

## prod 코드 검증

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC에서 `ssh orin` 접속 | 프롬프트 `laba@ubuntu` 표시 | pass | SSH 명령이 Orin `HOST=ubuntu`에서 실행됨 |
| 2 | Orin에서 `source ~/smolvla/.venv/bin/activate` | 프롬프트에 `(.venv)` 표시 | pass | `VIRTUAL_ENV=/home/laba/smolvla/.venv` 확인 |
| 3 | `python ~/smolvla/examples/tutorial/smolvla/smoke_test.py` 실행 | 에러 없이 완료 | pass | Orin 배포 구조 기준 corrected path로 실행, exit code 0 |
| 4 | forward pass 출력 확인 | action tensor 출력 또는 성공 메시지 | pass | `[PASS] select_action 성공 — action shape: torch.Size([1, 6])`, `모든 smoke test 통과. Orin 실행 환경 정상.` |

## 테스트 메모

- 2026-04-25: Orin 접속과 venv 활성화는 성공했으나, 지정된 smoke test 경로가 Orin에 없어 실행 실패. 테스트 지시 또는 스펙에서 Orin 상의 실제 `smoke_test.py` 경로 확인/업데이트 필요.
- 2026-04-25: Orin 실제 경로 `~/smolvla/examples/tutorial/smolvla/smoke_test.py`로 재실행하여 통과. 시스템 체크 경고는 `nvcc 미탐지`, `libcusparseLt 시스템 등록 미확인`이 있으나 venv fallback으로 smoke test는 정상 완료.
