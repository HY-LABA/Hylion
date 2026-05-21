# orin/tests/ — 시나리오 점검 + 환경 게이트

> 책임: 시연장 진입 전 SO-ARM 포트 / 카메라 인덱스·flip / venv·CUDA / ckpt 호환성 등 *Orin 운영 전제* 를 점검. 결과는 `orin/config/` 의 cached config 와 비교/갱신.
> 형제: `orin/docs/legacy/` (옛 era 의 latency·baseline 측정 도구 보존)

---

## check_hardware 의 두 모드

| 모드 | 동작 | 사용 시점 |
|---|---|---|
| `--mode first-time` | 모든 항목 새로 발견 + 사용자 확인 + `orin/config/` 에 cache 저장 | 초기 셋업 / 시연장 이동 후 / 하드웨어 교체 후 |
| `--mode resume` | `orin/config/` 의 cached 값으로 검증만 (변동 시 FAIL) | 이후 매 운영 진입 직전 |

운영 스크립트 (`leftarm_v2_inference.py` 등) 가 시작 시 `tests/check_hardware.sh --mode resume --quiet` sub-call 로 게이트 통과 후 진입하는 게 *의도된 흐름*. (현 시점엔 wrapper 가 자동 호출 안 함 — 사용자 수기 호출이 표준)

---

## 자산 (현행 — 시연장 운영 도구)

| 파일 | 책임 |
|---|---|
| `check_hardware.sh` | **단일 진입점** — first-time/resume 두 모드로 venv·CUDA·SO-ARM 포트·카메라 인덱스·flip 통합 점검 |
| `configs/first_time.yaml` | first-time 모드의 점검 항목·임계치 정의 |
| `configs/resume.yaml` | resume 모드의 cached 값 검증 룰 정의 |
| `smoke_test.py` | venv·CUDA·import·smolvla forward 환경 검증 (hardware 없이 동작) |
| `load_checkpoint_test.py` | 임의 경로 ckpt 호환성 검증 (prof_computer/DGX → Orin 전송 후 forward + action shape) |
| `diagnose_motor_encoder.py` | SO-ARM 모터 encoder 진단 (관절별 raw Present_Position read·검증) — 모터 이상 시 디버깅 도구 |

---

## Legacy 자산 (참조용 — `orin/docs/legacy/`)

| 파일 | 옛 책임 | 이관 사유 |
|---|---|---|
| `orin/docs/legacy/inference_baseline.py` | 더미 입력 1회 forward (사전학습 분포 미러링 + action shape/dtype/range 출력) | `smoke_test.py` + `load_checkpoint_test.py` 가 동일 책임 흡수. 현 era 호출 0 |
| `orin/docs/legacy/measure_latency.py` | latency p50/p95 + RAM peak 측정. `--num-steps` 인자로 flow matching steps 분기 | 현 era 평가 흐름 외부 (003 의 trial 평가 + wandb 메트릭으로 진행). 다음 era 의 성능 분석 시점에 재활용 가능 |

→ 두 파일은 현 시연·평가에서 호출 X. 다음 era 진입 시 패턴 참조 또는 재활용 가능.

---

## 외부 의존성

- `orin/config/ports.json` — SO-ARM 포트 cache (resume 모드 검증 대상)
- `orin/config/cameras.json` — 카메라 인덱스·flip cache (resume 모드 검증 대상)
- `lerobot-find-port` / `lerobot-find-cameras` — first-time 모드의 발견 도구 (CLI wrapping)
- `~/.cache/huggingface/lerobot/calibration/<robot_id>.json` — lerobot 표준 캘리브레이션 위치 (참조만)

---

## 참고

- 추론 운영 entry: [`orin/inference/README.md`](../inference/README.md)
- Legacy 자산: [`orin/docs/legacy/README.md`](../docs/legacy/README.md)
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
