# TODO-01 — 003 학습 결과 정리

> 작성: 2026-05-19 | task-executor | cycle: 1

## 목표

wandb run 40kzxlmq 학습 메트릭 추출 + learning_log.md §003 entry 신설 + M1.5/002/003 비교 표 작성 + HF Hub repo 파일 구조 검증

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `prof_computer/docs/leftarm_v2/learning_log.md` | M | §003 entry 신설 (line 570~657) + M1.5/002/003 비교 표 신설 (line 660~715) |
| `docs/work_flow/context/todos/TODO-01/01_implementation.md` | A | 작업 보고서 (신규) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `.claude/` 미변경 ✓
- Category B 미해당: `orin/lerobot/`, `pyproject.toml`, `deploy_*.sh`, `.gitignore` 미변경 ✓
- Coupled Rules §6: `learning_log.md` 본문에 직접 entry 추가 — ⚠️ 박스 누적 패턴 회피 ✓
- 레퍼런스 활용: `lerobot-reference-usage` 스킬 — 본 todo 는 코드 변경 없는 문서 작업. 레퍼런스 기반 코드 패턴 불필요 ✓

## 변경 내용 요약

`prof_computer/docs/leftarm_v2/learning_log.md` 에 §003 분기 학습 entry (line 568~656) 와 M1.5/002/003 3-way 비교 표 (line 658~715) 를 추가했다. entry 구조는 기존 §002 (camera_empty) entry 양식을 mirror: smoke 검증 단계 → 본 학습 메트릭 → 시스템 메트릭 → HF Hub 검증 → 추론 평가 결과 메모 순서. HF Hub API curl 검증 (`config.json.empty_cameras=1`, siblings 10개, adapter_config LoRA r=16 등) 은 직접 실행해 확인했다.

wandb run 40kzxlmq 의 일부 메트릭 (final loss, loss steady band, grad_norm, system metrics 실측값) 은 devPC 환경에 `wandb` 패키지가 미설치돼 있어 추출 불가능했다 (wandb 페이지는 JavaScript 렌더링 필요, WebFetch 접근 불가). 해당 항목은 entry 내 `[wandb run 40kzxlmq 확인]` 마커로 표시해 사용자 후속 기입 형태로 남겼다. 확인 가능한 값 (step time, lr schedule, ckpt 수, VRAM peak at smoke) 은 train_config.json + smoke 결과 + commit 5715da5 message 에서 추출해 채웠다.

## DOD 충족 검증

- [x] `learning_log.md` §003 entry 추가됨 (line 570~657)
- [x] M1.5/002/003 비교 표 신설 (line 660~715)
- [x] HF Hub repo 검증 — siblings 10개 정합 + `config.json.empty_cameras=1` 확인
- [x] wandb metric 추출 — **부분 성공** (train_config.json + smoke commit 메트릭 채움, 실측 학습 chart 값은 `[wandb run 40kzxlmq 확인]` 마커 처리)

## wandb 추출 메트릭 (요약)

| 항목 | 값 | 출처 |
|---|---|---|
| output_dir timestamp | `2026-05-18_23-06-14` | `train_config.json.job_name` |
| steps | 120,000 | `train_config.json.steps` |
| batch_size | 6 | `train_config.json.batch_size` |
| epoch | ~4.39 | spec + train_config |
| step time (smoke 3) | ~0.48 s/step | commit 5715da5 |
| lr 마지막 | 2.5e-6 | `train_config.json.scheduler_decay_lr` |
| scheduler_decay_steps | 120,000 (=steps) | `train_config.json` |
| ckpt 저장 수 | 60개 (save_freq=2000) | `train_config.json.save_freq` |
| VRAM peak (smoke 3) | 79.52% (~20.49 GB) | commit 5715da5 |
| final loss | [wandb 40kzxlmq] | wandb 미설치 |
| loss steady (last 20K) | [wandb 40kzxlmq] | wandb 미설치 |
| grad_norm 후반 | [wandb 40kzxlmq] | wandb 미설치 |
| GPU power / util / temp | [wandb 40kzxlmq] | wandb 미설치 |
| System RAM / disk | [wandb 40kzxlmq] | wandb 미설치 |

## HF Hub 검증 결과

- siblings 10개 확인 OK: `.gitattributes`, `README.md`, `adapter_config.json`, `adapter_model.safetensors`, `config.json`, `policy_postprocessor.json`, `policy_postprocessor_step_0_unnormalizer_processor.safetensors`, `policy_preprocessor.json`, `policy_preprocessor_step_5_normalizer_processor.safetensors`, `train_config.json`
- `config.json.empty_cameras` = 1 확인 OK (003 분기 정합)
- `config.json.n_action_steps` = 50 (Hub 함정 회피 확인)
- `adapter_config.json.r` = 16 (LoRA r=16 정합)
- `train_config.json.scheduler_decay_steps` = 120000 (= steps, 전 구간 cosine decay 확인)

spec 이 요구한 9개 파일 (`adapter_model.safetensors`, `adapter_config.json`, `config.json`, `policy_preprocessor.json`, `policy_postprocessor.json`, `policy_preprocessor_step_5_normalizer_processor.safetensors`, `policy_postprocessor_step_0_unnormalizer_processor.safetensors`, `train_config.json`) 은 모두 존재함. `README.md`, `.gitattributes` 2개 추가.

## 잔여 리스크

- wandb 실측 메트릭 (final loss, loss band, grad_norm, system chart) 미채움 — 사용자가 [wandb run 40kzxlmq](https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq) 에서 직접 확인 후 entry 의 `[wandb run 40kzxlmq 확인]` 마커 항목 갱신 필요. TODO-04 (결과 집계 보고) 에서 처리 권장.
- last ckpt 크기 미확인 — prof_computer 로컬 또는 HF Hub safetensors 파일 크기로 확인 가능.

## code-tester 검증 권고

- `learning_log.md` §003 entry 양식이 §001 (M1.5) · §002 (camera_empty) entry 와 일관성 있는지 (smoke 단계 → 본 학습 메트릭 → 시스템 메트릭 → HF Hub → 추론 메모 구조)
- M1.5/002/003 비교 표가 §002 entry 내 `### M1.5 (001) 와의 비교` 표 양식과 mirror 되는지
- HF Hub 검증 결과가 spec DOD (c) 의 요구 파일 목록과 일치하는지
- `[wandb run 40kzxlmq 확인]` 마커 항목이 누락이 아닌 미추출 표시임이 보고서에 명시돼 있는지
- line 범위가 실제 파일 내용과 일치하는지 (`wc -l` 기준 570~657, 660~715)
