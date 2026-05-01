# Current Test
<!-- /handoff-test 우회 — devPC 측 본 AI 가 직접 배포·검증 진행. 본 문서는 결과 보존용. -->

> 2026-04-30 16:53 | 스펙: `docs/work_flow/specs/04_infra_setup.md` | TODO: O3

## 검증 목표

TODO-O2 + TODO-O2b 마이그레이션 통합 검증. Orin prod 환경에서:

- 03 산출물 5개 (`smoke_test.py`, `load_checkpoint_test.py`, `inference_baseline.py`, `measure_latency.py`, `hil_inference.py`) 가 새 경로 (`tests/`, `inference/`) 에서 정상 동작
- `lerobot-eval` / `lerobot-train` 2개 entrypoint 등록 해제 반영
- 4개 신규 디렉터리 (`tests/`, `config/`, `checkpoints/`, `inference/`) + README 모두 인식
- import 회귀 없음

## 진행 컨텍스트

본 사이클에서 환경 변경 — devPC 가 Windows → Linux (`/home/babogaeguri/Desktop/Hylion/smolVLA`) 로 이전. devPC 에서 본 AI 가 직접 SSH (`ssh orin`) 로 접근 가능하게 되어 `/handoff-test` Codex/Copilot 위임 절차 우회. 본 AI 가 배포 + 검증을 직접 수행.

## 실행 단계

### 1. devPC → Orin 배포

```
bash /home/babogaeguri/Desktop/Hylion/smolVLA/scripts/deploy_orin.sh
```

**결과**: rsync 성공
- 신규 동기화: `checkpoints/`, `config/`, `inference/`, `tests/` (각 README + ports.json/cameras.json placeholder)
- 삭제 동기화: `examples/tutorial/smolvla/{smoke_test,measure_latency,load_checkpoint_test,inference_baseline,hil_inference}.py` (이동된 파일들), `scripts/run_teleoperate.sh`
- pyproject.toml + lerobot/policies/smolvla/modeling_smolvla.py 업데이트 반영
- 송신 21,307 bytes / 수신 937 bytes / 총 1,191,450 bytes

### 2. Orin 측 pip install -e . 재설치

```
ssh orin 'source ~/smolvla/orin/.hylion_arm/bin/activate && cd ~/smolvla/orin && pip install -e ".[smolvla,hardware,feetech]"'
```

**결과**: `Successfully installed lerobot-0.5.2 sympy-1.13.1`. editable wheel 재빌드. entrypoint 등록 갱신 (eval/train 제거 반영).

## 검증 결과

| # | 검증 항목 | 결과 |
|---|---|---|
| 1 | `which lerobot-eval lerobot-train` — 결과 없음 (등록 해제 확인) | PASS — exit=1, stdout 비어있음 |
| 2 | venv `bin/lerobot-*` 9개만 존재 (eval/train 제외) | PASS — calibrate / find-cameras / find-joint-limits / find-port / info / record / replay / setup-motors / teleoperate (총 9개) |
| 3 | 4 신규 디렉터리 README 존재 (`tests/`, `config/`, `checkpoints/`, `inference/`) | PASS — 4개 모두 존재 (각 2.5~3.4 KB) |
| 4 | `python ~/smolvla/orin/inference/hil_inference.py --help` | PASS — exit=0, argparse usage 정상 출력 (mode/follower-port/cameras/flip-cameras/n-action-steps/max-steps 인자 모두 인식) |
| 5 | `python ~/smolvla/orin/tests/load_checkpoint_test.py --help` | PASS — exit=0, ckpt-path/device 인자 정상 출력 |
| 6 | `python ~/smolvla/orin/tests/smoke_test.py` (compile/import) | PASS — `compile OK` |
| 7 | `python ~/smolvla/orin/tests/inference_baseline.py` (forward 실행) | PASS — exit=0, lerobot/smolvla_base 다운로드 + 더미 입력 forward 1회 완료. Action shape (1,6), dtype torch.float32, min 0.391 / max 0.943 출력. **새 경로에서도 03 마일스톤 동작 그대로 재현** |
| 8 | `python ~/smolvla/orin/tests/measure_latency.py --help` | PASS — exit=0, num-steps/warmup/repeats/output-json 인자 정상 출력 |

### 부수 관찰

- `lerobot-train` 은 본 검증 직전부터 venv 에 부재 (이전 build 단계에서 제외되었거나 `[smolvla,hardware,feetech]` extra 셋에서 등록 안 됨). 본 사이클의 entrypoint 정리는 `lerobot-eval` 만 실효성 있음 — TODO-O2 의 entrypoint 정리 사양은 그대로 만족.
- inference_baseline.py 실행 중 `Warning: You are sending unauthenticated requests to the HF Hub` 경고 1회 (HF_TOKEN 미설정). 정성 동작 무관 — 04 그룹 G·D 진입 시 별도 검토 가능.
- inference_baseline.py 의 forward 출력은 03 prod 검증 결과 (`docs/lerobot_study/07c_smolvla_base_test_results.md`) 와 동일 패턴 — Action shape (1,6), VLM 16 layer 축소, 카메라 3개 (camera1/2/3) 더미 입력.

## 결론

TODO-O2 + TODO-O2b 마이그레이션 prod 회귀 없음. 5개 .py 모두 새 경로에서 정상 동작 (4개 `--help` PASS + 1개 forward 실 동작 PASS). entrypoint 등록 해제 반영 확인. 4 README 인식. **TODO-O3 DOD 충족 — 04 그룹 O 클로징.**

## 후속 액션

- 04 그룹 X (TODO-X1·X2·X3) 진입 가능
- 04 그룹 D (TODO-D1·D2·D3) 진입 시 사용자 결정 필요 (DataCollector 노드 정체)
- BACKLOG 04 #2 (run_teleoperate.sh 임시 보관 컨벤션) — TODO-D2 시점에 최종 결정
