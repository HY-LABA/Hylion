# orin/tests/ — 시나리오 점검 + 환경 게이트

> 책임: SO-ARM 포트 / 카메라 인덱스·flip / venv·CUDA 라이브러리 등 Orin 운영 전 환경을 시나리오 단위로 점검. 결과는 `orin/config/` 의 cached config 와 비교/갱신.
> 신설: 04_infra_setup TODO-O2 (2026-04-30)
> 형제: `dgx/scripts/preflight_check.sh` (DGX 측 학습 전 자원 점검)

---

## 두 모드

| 모드 | 동작 | 사용 시점 |
|---|---|---|
| `--mode first-time` | 모든 항목 새로 발견 + 사용자 확인 + `orin/config/` 에 cache 저장 | 초기 셋업 / 시연장 이동 후 / 하드웨어 교체 후 |
| `--mode resume` | `orin/config/` 의 cached 값으로 검증만 (변동 시 FAIL) | 이후 매 운영 진입 직전 |

운영 스크립트 (`hil_inference.py`, `record_dataset.sh` 등) 가 시작 시 `tests/check_hardware.sh --mode resume --quiet` sub-call 로 게이트 통과 후 진입.

---

## 자산 (현재)

| 파일 | 책임 | 출처 |
|---|---|---|
| `diagnose_motor_encoder.py` | SO-ARM 모터 encoder 진단 (관절별 위치 read·검증) | 01_teleoptest TODO-03a 산출물 (2026-04-27 작성, 04 TODO-O2 에서 `orin/calibration/` 으로부터 이관) |
| `smoke_test.py` | venv·CUDA·import·smolvla forward 환경 검증 | 01_teleoptest TODO-01 산출물 (04 TODO-O2b 에서 `orin/examples/tutorial/smolvla/` 로부터 이관) |
| `load_checkpoint_test.py` | 임의 경로 ckpt 호환성 검증 (DGX→Orin 전송 후 forward + action shape) | 02_dgx_setting TODO-10b 산출물 (04 TODO-O2b 에서 이관) |
| `inference_baseline.py` | 더미 입력 1회 forward (사전학습 분포 미러링 + action shape/dtype/range 출력) | 03_smolvla_test_on_orin TODO-06 산출물 (04 TODO-O2b 에서 이관) |
| `measure_latency.py` | latency p50/p95 + RAM(UMA) peak 측정. `--num-steps` 인자로 flow matching steps 분기 | 03_smolvla_test_on_orin TODO-06 산출물 (04 TODO-O2b 에서 이관) |

## 자산 (예정 — 04 진행 중 추가)

| 파일 | 책임 | 추가 시점 |
|---|---|---|
| `check_hardware.sh` | 단일 진입점. 4단계 점검 (venv·CUDA / SO-ARM 포트 / 카메라 인덱스 / 카메라 방향) | TODO-G1 |
| `configs/first_time.yaml` | first-time 모드의 점검 항목·임계치 정의 | TODO-G1 |
| `configs/resume.yaml` | resume 모드의 cached 값 검증 룰 정의 | TODO-G1 |

---

## 외부 의존성

- `orin/config/ports.json` — SO-ARM 포트 cache (resume 모드 검증 대상)
- `orin/config/cameras.json` — 카메라 인덱스·flip cache (resume 모드 검증 대상)
- `lerobot-find-port` / `lerobot-find-cameras` — first-time 모드의 발견 도구 (CLI wrapping)
- `~/.cache/huggingface/lerobot/calibration/<robot_id>.json` — lerobot 표준 캘리브레이션 위치 (참조만)

---

## 참고

- `docs/storage/07_orin_structure.md` §2 (tests/ 컴포넌트 책임) + §3 (마일스톤별 책임 매트릭스)
- `docs/work_flow/specs/04_infra_setup.md` TODO-G1 / TODO-G2 (실 구현·검증)
- BACKLOG 03 #14·#15·#16 — 본 게이트가 해소할 환경 이슈 4건 (venv import / 카메라 인덱스 / wrist flip)
