# Orin Legacy 추론 entry 보존 (2026-05-21 정리)

> **결론**: leftarm_v2 era 진입 후 Orin 의 *현행 추론 운영* 책임은 [`orin/inference/`](../../inference/) 의 두 entry (`leftarm_v2_inference.py`, `leftarm_base_inference.py`) 가 담당. 본 디렉터리는 *옛 era 의 추론 entry* 를 *read-only 역사 자료* 로 보존.
>
> **git 정책**: `.gitignore` 의 `Legacy/` 일반 무시에서 예외 처리 (line 215+ 의 dgx/legacy/ 와 동일 패턴). 본 디렉터리만 git 추적 유지.
>
> 본 디렉터리 자산은 *현 시연·평가에서 호출하지 않음*. 코드 패턴 참조용으로만 잔존.

---

## 1) 보존 자산

### 1-1) 옛 inference entry

| 파일 | 옛 책임 | 보존 사유 |
|---|---|---|
| `hil_inference.py` | (era 무관) SmolVLA 사전학습 ckpt 로 Orin 환경 셋업 동작 검증. dry-run / live 두 모드 + 안전 장치 (n_action_steps=5, SIGINT 핸들러, try/finally disconnect, `--flip-cameras`). | 현 era (leftarm_v2) 에서는 `leftarm_base_inference.py` 가 *task-conditional zero-shot 검증* 책임 흡수. `hil_inference.py` 의 *환경 셋업 검증* 책임은 *task instruction 없이 base 추론* 영역 — 다음 era 환경 변화 시 패턴 참조 자산. |
| `lego_v1_inference.py` | lego_v1 era 의 fine-tune ckpt HIL 추론. fourcc=MJPG (USB 2.0 hub), overview/wrist 카메라 키, GATE_CAMERA_ALIAS. | lego_v1 era 산출물. 동일 패턴 (LoRA + camera config + rename_map) 이 *leftarm_v2_inference.py* 에 적용·진화됨. 역사 자료. |

### 1-2) 옛 tests 자산 (2026-05-21 tests/ 에서 이관)

| 파일 | 옛 책임 | 이관 사유 |
|---|---|---|
| `inference_baseline.py` | 사전학습 분포 미러링 더미 입력 1회 forward — `model.config.input_features` 자동 추출. action shape/dtype/range 출력 | 현 era 의 `smoke_test.py` (환경 forward 검증) + `load_checkpoint_test.py` (ckpt 호환성 + action shape) 가 동일 책임 흡수. 현 era 호출 0건. 옛 spec 산출물 (`03_smolvla_test_on_orin TODO-03`). |
| `measure_latency.py` | latency p50/p95 + RAM peak 측정. warmup N회 + 측정 N회 forward. `--num-steps` 로 flow matching steps 분기 | 현 era 평가 흐름은 *Orin trial 결과 (003 의 8/8 = 100%) + wandb 메트릭*. latency 측정은 *별도 영역* 으로 분리. 다음 era 의 성능 분석 시점에 재활용 가능. |

---

## 2) 현 era 와의 관계 — 책임 이관

| 영역 | 옛 (legacy) | 현행 (leftarm_v2 era) |
|---|---|---|
| 환경 셋업 검증 | `hil_inference.py` (era 무관 generic) | `leftarm_base_inference.py` (leftarm_v2 task instruction + rename_map 적용) |
| LoRA ckpt 추론 | `lego_v1_inference.py` (lego_v1 era hard-coded) | `leftarm_v2_inference.py` (CKPT_REPO_ID env override 로 분기 ckpt 선택) |
| HIL 추론 패턴 (camera config, gate-json, rename_map 등) | 두 inference 파일 모두 *원형 패턴* 제공 | 두 파일의 패턴이 *현행 entry* 에 차용·진화 |
| 더미 forward 검증 | `inference_baseline.py` (분리 도구) | `smoke_test.py` + `load_checkpoint_test.py` 흡수 |
| latency 측정 | `measure_latency.py` | 현 era 평가는 trial 결과 + wandb 메트릭. latency 별도 측정 영역 분리 |

→ 현 era entry 두 개 (`leftarm_v2_inference.py`, `leftarm_base_inference.py`) + tests 영구 3개 (`smoke_test.py`, `load_checkpoint_test.py`, `check_hardware.sh`) 가 legacy 4 파일의 *책임 + 패턴* 을 흡수. legacy 자산은 *진화의 출발점 + 다음 era 재활용 후보* 로 보존.

---

## 3) 호출 정책

본 디렉터리 파일은 **직접 호출하지 않는다**:

- 시연·평가 호출 = 현행 `orin/inference/` 의 entry 두 개
- legacy 파일 직접 호출은 *과거 동작 재현* 같은 특수 목적 한정 — 권장 X

---

## 4) 외부 참조 매핑 (이동 전 → 이동 후)

| 옛 경로 | 현 경로 |
|---|---|
| `orin/inference/hil_inference.py` | `orin/docs/legacy/hil_inference.py` |
| `orin/inference/lego_v1_inference.py` | `orin/docs/legacy/lego_v1_inference.py` |
| `orin/tests/inference_baseline.py` | `orin/docs/legacy/inference_baseline.py` |
| `orin/tests/measure_latency.py` | `orin/docs/legacy/measure_latency.py` |

코드 안의 *옛 경로 인용* (예: 주석 "패턴 출처: hil_inference.py") 은 *새 경로* (`orin/docs/legacy/hil_inference.py`) 로 갱신됨 (2026-05-21).

---

## 참고

- 현행 추론 entry: [`orin/inference/README.md`](../../inference/README.md)
- DGX 의 동일 패턴 (학습 시도 legacy): [`dgx/legacy/train_trial_2026-05-17/README.md`](../../../dgx/legacy/train_trial_2026-05-17/README.md)
- 명명 컨벤션: [`prof_computer/README.md` §7](../../../prof_computer/README.md)
