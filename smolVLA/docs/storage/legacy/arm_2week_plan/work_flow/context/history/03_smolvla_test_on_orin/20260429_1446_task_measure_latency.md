# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 14:34 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 04

## 작업 목표

`orin/examples/tutorial/smolvla/measure_latency.py` 작성.

`inference_baseline.py`의 입력 미러링 로직을 재사용하여 warmup + 반복 forward로 latency 분포(p50/p95)와 RAM(UMA) peak를 측정. `num_steps∈{10, 5}` 두 설정 비교 가능하게 argparse 지원. 결과를 JSON으로 저장.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

아래 두 조건을 모두 만족하면 완료:

1. `orin/examples/tutorial/smolvla/measure_latency.py` 파일이 존재하고 `python -m py_compile` syntax check 통과
2. 스크립트가 아래 기능을 모두 포함:
   - argparse: `--num-steps` (기본 10), `--warmup` (기본 10), `--repeats` (기본 50), `--output-json`
   - `time.perf_counter()` + `torch.cuda.synchronize()` 기반 latency 측정
   - latency 분포 p50 / p95 계산 출력
   - `psutil` 기반 RAM(시스템 메모리) peak 측정
   - 결과를 `--output-json` 경로에 JSON으로 저장

실 실행 검증은 TODO-05 (Orin prod 검증) 에서 수행. 여기서는 syntax check 만.

## 구현 대상

- `orin/examples/tutorial/smolvla/measure_latency.py` — **신규 작성**

## 구현 참고사항

- `inference_baseline.py`의 더미 입력 생성 로직을 그대로 재사용 (카메라 3개, state 6DOF, instruction)
- Orin은 UMA 아키텍처라 GPU/CPU 메모리 공유 → `torch.cuda.memory_*` 단독으로는 부족, `psutil.Process().memory_info().rss` 또는 `psutil.virtual_memory()` 로 시스템 메모리 peak 측정
- 첫 forward는 cuDNN kernel autotuning으로 매우 느림 → warmup 회수 충분히 (기본 10회)
- 측정 대상은 `select_action` 1회 호출 전체 시간 (`torch.cuda.synchronize()` 후 타이밍)
- `num_steps=10` / `num_steps=5` 비교는 CLI `--num-steps` 인자로 각각 실행하여 비교

## 참고 레퍼런스

- `orin/examples/tutorial/smolvla/inference_baseline.py` — 더미 입력 생성 로직 재사용 기준
- `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py` — `select_action` 시그니처
- `docs/work_flow/specs/03_smolvla_test_on_orin.md` §TODO-05 — 기대 출력 형식 (latency_n10.json, latency_n5.json)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only, upstream submodule)
- `orin/examples/tutorial/smolvla/inference_baseline.py` — 수정 금지 (sibling 스크립트)
- `orin/examples/tutorial/smolvla/smoke_test.py` — 수정 금지
- smolvla_base config 플래그 변경 금지 (num_steps 등은 argparse로 override, 모델 자체 config 수정 아님)

## 업데이트
<!-- Copilot이 작업 완료 후 여기에 기록:
변경한 내용
- orin/examples/tutorial/smolvla/measure_latency.py 신규 작성 (입력 생성, warmup, 반복 latency/RAM 측정, JSON 저장, argparse 지원)

검증 방법 및 결과
- python3 -m py_compile orin/examples/tutorial/smolvla/measure_latency.py 통과 (syntax check OK)

실 실행 검증 필요 여부
- Orin prod 환경에서 실 실행 및 결과 확인 필요 (TODO-05에서 진행)

## 배포
- 일시: 2026-04-29 14:46
- 결과: 완료 (`measure_latency.py` → `orin:/home/laba/smolvla/orin/examples/tutorial/smolvla/`)
