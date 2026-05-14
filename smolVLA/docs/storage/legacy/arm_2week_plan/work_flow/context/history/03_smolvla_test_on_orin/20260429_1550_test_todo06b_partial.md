# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 15:37 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 06b

## 테스트 목표

TODO-06(PYTHONPATH 수정) 산출물인 `inference_baseline.py` / `measure_latency.py` 가 Orin prod 환경에서 실제로 동작하는지 확인하고, latency 측정 결과를 `docs/storage/07_smolvla_base_test_results.md` 로 정리한다.

이전 TODO-05 테스트에서 `ModuleNotFoundError: No module named 'orin'` 로 FAIL 된 개발자 직접 검증 step 1~5 를 재실행하는 것이 핵심.

## DOD (완료 조건)

아래를 모두 만족하면 완료:

1. `inference_baseline.py` Orin 실행 — forward pass PASS, action shape `(1, 50, *)` 출력, exit code 0
2. `measure_latency.py --num-steps 10` 실행 — latency p50/p95 + RAM peak 출력, `/tmp/latency_n10.json` 저장
3. `measure_latency.py --num-steps 5` 실행 — 동일 형식 결과, `/tmp/latency_n5.json` 저장
4. `docs/storage/07_smolvla_base_test_results.md` 신규 작성 완료 (§1~§6 포함)

## 환경

- Orin JetPack 6.2 | Python 3.10 | venv `~/smolvla/orin/.hylion_arm`
- 접근: devPC → `ssh orin` → Orin (`laba@ubuntu`)
- Orin 코드 경로: `/home/laba/smolvla/orin/`
- SO-ARM 연결 불필요 (더미 입력 사용)

---

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->
<!-- 스펙 파일은 직접 수정하지 않는다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` | syntax check 통과 (출력 없음) | PASS | 이번 세션 배포 전 확인 완료 |
| 2 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` | syntax check 통과 (출력 없음) | PASS | 이번 세션 배포 전 확인 완료 |
| 3 | devPC: `grep -rn "^from orin\|^import orin" orin/ --include="*.py"` | 검색 결과 0건 | PASS | 이번 세션 회귀 grep 0건 확인 |
| 4 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료, `inference_baseline.py` / `measure_latency.py` 전송 확인 | PASS | sandbox 네트워크 제한으로 1차 실패 후 승인된 재실행에서 rsync 정상 종료 |
| 5 | Orin: `ssh orin "~/smolvla/orin/.hylion_arm/bin/python -c \"from lerobot.policies.smolvla import SmolVLAPolicy; print('OK')\""` | `OK` 출력 | FAIL | direct venv python 실행 시 `ImportError: libcusparseLt.so.0`; `source .../activate` 후 동일 import 는 `OK` 출력 |

---

## 개발자 직접 검증 (대화형, 약 30~60 분 소요)
<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다 -->
<!-- 첫 실행 시 HF Hub 에서 lerobot/smolvla_base 다운로드 (5~15 분) 발생 가능 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate` | venv 활성화 (`(.hylion_arm)` 프롬프트) | PASS | activate 후 `SmolVLAPolicy` import `OK` 확인 |
| 2 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/inference_baseline.py` | 정책 로드 → forward pass PASS → action shape `(1, 50, *)` 출력, exit code 0 | PARTIAL | exit 0, dtype/range 출력. 실제 action shape `(1, 6)`으로 DOD 기대 shape와 불일치 |
| 3 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 10 --warmup 10 --repeats 50 --output-json /tmp/latency_n10.json` | latency p50/p95 + RAM peak 출력, `/tmp/latency_n10.json` 저장, exit code 0 | PASS | p50 5.59 ms, p95 5.82 ms, RAM peak 3068.30 MiB |
| 4 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 5 --warmup 10 --repeats 50 --output-json /tmp/latency_n5.json` | latency p50/p95 + RAM peak 출력, `/tmp/latency_n5.json` 저장, num_steps=10 대비 latency 감소 확인 | PARTIAL | JSON 저장 및 exit 0. p50 5.59 ms, p95 6.20 ms, RAM peak 3041.91 MiB; latency 감소는 확인되지 않음 |
| 5 | devPC: `scp orin:/tmp/latency_n10.json /tmp/ && scp orin:/tmp/latency_n5.json /tmp/` | 두 JSON 파일 devPC 로 회수 | PASS | `/tmp/latency_n10.json`, `/tmp/latency_n5.json` 회수 완료 |

### 결과 문서화 (JSON 회수 후)

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 6 | devPC: 회수된 JSON + inference_baseline 출력으로 `docs/storage/07_smolvla_base_test_results.md` 신규 작성 | §1~§6 완성 (입력 스펙 매칭 표, action shape/dtype/range, latency 비교 표, 자원 기준선, 잔여 리스크) | PASS | 신규 문서 작성 완료. DOD 불일치 2건(action shape, latency 감소 미확인)을 잔여 리스크로 기록 |

## 잔여 리스크 (참고)

- HF Hub 다운로드 네트워크 변동 (5~15 분 소요 가능, 이미 캐시됐으면 즉시)
- GB10 capability 12.1 UserWarning 출력 가능 — 무시 가능
- 더미 입력은 실 카메라 분포와 다름 → 본 측정은 "코드 경로 자원 점유" baseline. 실 카메라 latency 는 07b 에서 재측정
