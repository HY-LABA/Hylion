# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 14:48 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 05

## 테스트 목표

Orin prod 검증 — `inference_baseline.py` + `measure_latency.py` 실 실행 확인 및 결과 문서화.

TODO-03·04 에서 syntax check 만 통과한 두 스크립트가 Orin 위에서 실제로 동작하는지 확인한다.
`num_steps∈{10, 5}` 두 설정으로 latency(p50/p95) 및 RAM(UMA) peak 를 측정하고,
결과를 `docs/storage/07_smolvla_base_test_results.md` 로 정리한다.

## DOD (완료 조건)

아래를 모두 만족하면 완료:

1. `inference_baseline.py` Orin 실행 — forward pass PASS, action shape `(1, 50, *)` 출력, exit code 0
2. `measure_latency.py --num-steps 10` 실행 — latency p50/p95 + RAM peak 출력, `latency_n10.json` 저장
3. `measure_latency.py --num-steps 5` 실행 — 동일 형식 결과, `latency_n5.json` 저장
4. `docs/storage/07_smolvla_base_test_results.md` 신규 작성 완료 (§1~§6 포함)

## 환경

- Orin JetPack 6.2 | Python 3.10 | venv `~/smolvla/orin/.hylion_arm`
- 접근: devPC → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/orin/`

---

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->
<!-- 스펙 파일은 직접 수정하지 않는다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` | syntax check 통과 (출력 없음) | PASS | 출력 없음, exit code 0 |
| 2 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` | syntax check 통과 (출력 없음) | PASS | 출력 없음, exit code 0 |
| 3 | devPC: `ssh orin "ls ~/smolvla/orin/examples/tutorial/smolvla/"` | `inference_baseline.py`, `measure_latency.py` 목록 포함 | PASS | 목록에 `inference_baseline.py`, `measure_latency.py` 포함, exit code 0 |
| 4 | devPC: `ssh orin "~/smolvla/orin/.hylion_arm/bin/python -m py_compile ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py && echo OK"` | `OK` 출력 | PASS | `OK` 출력, exit code 0 |

---

## 개발자 직접 검증 (대화형, 약 30~60 분 소요)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- 첫 실행 시 HF Hub 에서 lerobot/smolvla_base 다운로드 (5~15 분) 발생 가능 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate` | venv 활성화 (`(.hylion_arm)` 프롬프트) | PASS | `sys.prefix=/home/laba/smolvla/orin/.hylion_arm` 확인 |
| 2 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/inference_baseline.py` | 정책 로드 → forward pass PASS → action shape `(1, 50, *)` 출력, exit code 0 | FAIL | `ModuleNotFoundError: No module named 'orin'`, exit code 1. `cd ~/smolvla` 후에도 동일. GB10 단계 전 import 실패 |
| 3 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 10 --warmup 10 --repeats 50 --output-json /tmp/latency_n10.json` | latency p50/p95 + RAM peak 출력, `/tmp/latency_n10.json` 저장, exit code 0 | FAIL | `ModuleNotFoundError: No module named 'orin'`, exit code 1. `/tmp/latency_n10.json` 미생성 |
| 4 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 5 --warmup 10 --repeats 50 --output-json /tmp/latency_n5.json` | latency p50/p95 + RAM peak 출력, `/tmp/latency_n5.json` 저장. num_steps=10 대비 latency 감소 확인 | FAIL | `ModuleNotFoundError: No module named 'orin'`, exit code 1. `/tmp/latency_n5.json` 미생성 |
| 5 | devPC: `scp orin:/tmp/latency_n10.json /tmp/ && scp orin:/tmp/latency_n5.json /tmp/` | 두 JSON 파일 devPC 로 회수 | FAIL | `scp: /tmp/latency_n10.json: No such file or directory` |

### 결과 문서화 (JSON 회수 후)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 6 | devPC: 회수된 JSON + inference_baseline 출력으로 `docs/storage/07_smolvla_base_test_results.md` 신규 작성 | §1~§6 완성 (입력 스펙 매칭 표, action shape/dtype/range, latency 비교 표, 기준선, 잔여 리스크) | BLOCKED | Orin 실행 실패로 inference 출력과 latency JSON 없음. `docs/storage/07_smolvla_base_test_results.md` 미작성 |

## 테스트 이슈 / 스펙 업데이트 요청

- 2026-04-29: Orin prod 실행 명령이 `ModuleNotFoundError: No module named 'orin'`로 실패한다. `inference_baseline.py`와 `measure_latency.py`는 `from orin.lerobot...`를 import하지만, 현재 스펙의 직접 실행 명령(`python ~/smolvla/orin/examples/...`)에서는 `/home/laba/smolvla`가 `sys.path`에 포함되지 않는다. 실행 명령에 `PYTHONPATH=/home/laba/smolvla`를 명시하거나, 스크립트/패키지 구조에서 직접 실행 시 import 경로를 보장하도록 후속 TODO/spec 업데이트가 필요하다.

## 잔여 리스크 (참고)

- HF Hub 다운로드 네트워크 변동 (5~15 분 소요 가능)
- GB10 capability 12.1 UserWarning 출력 가능 — 무시 가능
- 더미 입력은 실 카메라 분포와 다름 → 본 측정은 "코드 경로 자원 점유" baseline. 실 카메라 latency 는 07_biarm_deploy 에서 재측정
