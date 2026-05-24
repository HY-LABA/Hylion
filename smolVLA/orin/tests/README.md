# orin/tests/ — 시나리오 점검 + 환경 게이트

> 책임: venv·CUDA·ckpt 호환성 등 *Orin 운영 전제* 의 정적 점검. 디바이스 발견·매핑은 **udev rule (`orin/config/udev/99-hylion.rules`)** 이 담당 — 추론 wrapper (`scripts/run_inference_leftarm_v2.sh`) 의 `validate_devices()` 가 진입 시 노드 존재만 확인.
> 형제: `orin/docs/legacy/` (옛 era 의 발견·캐시 게이트 + latency·baseline 측정 도구 보존)

---

## 디바이스 게이트 (udev 도입 후, 2026-05-24)

| 항목 | 처리 |
|---|---|
| SO-ARM follower 포트 발견 | udev rule 이 `/dev/so_arm_left`, `/dev/so_arm_right` 생성 (시리얼 매칭). 발견 단계 불요 |
| 카메라 인덱스 매핑 | udev rule 이 `/dev/cam_top`, `/dev/cam_wrist` 생성. cameras.json 은 rotation/fps/fourcc/flip 부가 설정만 |
| 진입 시 검증 | `scripts/run_inference_leftarm_v2.sh` 의 `validate_devices()` 가 4개 노드 존재 확인 + 실패 시 reload 안내 |

---

## 자산 (현행 — Orin 운영 도구)

| 파일 | 책임 |
|---|---|
| `smoke_test.py` | venv·CUDA·import·smolvla forward 환경 검증 (hardware 없이 동작) |
| `load_checkpoint_test.py` | 임의 경로 ckpt 호환성 검증 (prof_computer/DGX → Orin 전송 후 forward + action shape) |
| `diagnose_motor_encoder.py` | SO-ARM 모터 encoder 진단 (관절별 raw Present_Position read·검증) — 모터 이상 시 디버깅 도구. default `/dev/so_arm_left` |

---

## Legacy 자산 (참조용 — `orin/docs/legacy/`)

| 파일 | 옛 책임 | 이관 사유 |
|---|---|---|
| `orin/docs/legacy/check_hardware.sh` | first-time (발견 + cache) + resume (cache vs 현재 검증) 두 모드의 디바이스 게이트 통합 진입점 | 2026-05-24 udev rule 도입으로 발견·매핑 책임이 `/etc/udev/rules.d/99-hylion.rules` 로 이관. cache (`ports.json`) 폐기 + cameras.json index 필드 제거. `validate_devices()` (run_inference_leftarm_v2.sh) 가 진입 시 검증 책임 흡수 |
| `orin/docs/legacy/check_hardware_configs/` | `first_time.yaml`·`resume.yaml` — check_hardware.sh 모드별 점검 항목·임계치 | 위와 한 셋트로 이관 |
| `orin/docs/legacy/inference_baseline.py` | 더미 입력 1회 forward (사전학습 분포 미러링 + action shape/dtype/range 출력) | `smoke_test.py` + `load_checkpoint_test.py` 가 동일 책임 흡수. 현 era 호출 0 |
| `orin/docs/legacy/measure_latency.py` | latency p50/p95 + RAM peak 측정. `--num-steps` 인자로 flow matching steps 분기 | 현 era 평가 흐름 외부 (003 의 trial 평가 + wandb 메트릭으로 진행). 다음 era 의 성능 분석 시점에 재활용 가능 |

→ 위 자산은 현 시연·평가에서 호출 X. 다음 era 진입 시 패턴 참조 또는 재활용 가능.

---

## 외부 의존성

- `orin/config/udev/99-hylion.rules` — 디바이스 심볼릭 링크 생성 (4개)
- `orin/config/cameras.json` — 카메라 부가 설정 (rotation/fps/fourcc/flip)
- `~/.cache/huggingface/lerobot/calibration/<robot_id>.json` — lerobot 표준 캘리브레이션 위치 (참조만)

---

## 참고

- 추론 운영 entry: [`orin/inference/README.md`](../inference/README.md)
- Legacy 자산: [`orin/docs/legacy/README.md`](../docs/legacy/README.md)
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
