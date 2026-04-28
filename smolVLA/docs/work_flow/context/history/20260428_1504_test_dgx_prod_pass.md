# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-28 14:38 | 스펙: `docs/work_flow/specs/02_dgx_setting.md` | TODO: 09b

## 테스트 목표

학습 환경 세팅 — DGX prod 검증 (재테스트).

`deploy_dgx.sh` 버그(BACKLOG #9) 수정 완료 후 재테스트. TODO-09 에서 작성한 세 스크립트(`setup_train_env.sh` → `preflight_check.sh` → `smoke_test.sh`)가 DGX Spark 에서 실제 동작함을 확인한다. GB10 throughput 실측치 기록까지 완료 조건.

## DOD (완료 조건)

- `setup_train_env.sh` 실행 완료: venv `~/smolvla/dgx/.arm_finetune` 생성, PyTorch 2.10.0+cu130 설치, lerobot editable 설치, `torch.cuda.is_available()=True` + `GPU name: NVIDIA GB10` + `lerobot import OK` 확인
- `preflight_check.sh smoke` PASS (HF_HOME / venv / 메모리 / Walking RL / Ollama / 디스크 모두 PASS)
- `smoke_test.sh` PASS: lerobot-train 1 step 통과, loss 값 출력, exit code 0
- smoke test 출력의 GPU util peak / GPU mem peak / 소요 시간 기록 → `docs/lerobot_study/06_smolvla_finetune_feasibility.md §5.2` 갱신

## 환경

- devPC (`babogaeguri@babogaeguri-950QED`) → `ssh dgx` → DGX Spark (`laba@spark-8434`)
- DGX: Ubuntu 24.04.4 / aarch64, Python 3.12.3 (시스템), CUDA 13.0, GPU NVIDIA GB10 UMA
- 학습 venv: `~/smolvla/dgx/.arm_finetune` (신규 생성)
- **주의: Walking RL 프로세스(`env_isaaclab`) 절대 건드리지 말 것**

## Codex 검증 (비대화형)

<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC: `bash scripts/deploy_dgx.sh` | rsync 정상 종료, DGX 측 `~/smolvla/dgx/` 와 `~/smolvla/docs/reference/lerobot/` 갱신, exit code 0 | PASS | 2026-04-28: 최초 샌드박스 실행은 SSH socket 제한으로 실패, 승인 후 재실행 성공. `dgx/`, `docs/reference/lerobot/` rsync 정상 종료, exit code 0 |
| 2 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/setup_train_env.sh"` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 3 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/preflight_check.sh"` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 4 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/smoke_test.sh"` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 5 | DGX: `ssh dgx "ls ~/smolvla/dgx/scripts/"` | `setup_train_env.sh`, `preflight_check.sh`, `smoke_test.sh` 3개 파일 존재 | PASS | 3개 파일 모두 확인 |
| 6 | DGX: `ssh dgx "ls ~/smolvla/docs/reference/lerobot/src/lerobot/policies/smolvla/"` | `configuration_smolvla.py`, `modeling_smolvla.py`, `processor_smolvla.py`, `smolvlm_with_expert.py`, `__init__.py` 5개 파일 존재 | PASS | 기대 5개 파일 모두 확인 (`README.md`도 함께 존재) |

## 개발자 직접 검증 (대화형, 약 30~60 분 소요)

<!-- 개발자가 DGX SSH 터미널에서 직접 실행하고 결과를 기록한다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | DGX: `bash ~/smolvla/dgx/scripts/setup_train_env.sh` | venv `~/smolvla/dgx/.arm_finetune` 생성, PyTorch 2.10.0+cu130 설치, lerobot editable 설치 완료. 출력 마지막에 `torch.cuda.is_available()=True`, `GPU name: NVIDIA GB10`, `lerobot import OK` 확인 | PASS | 2026-04-28: venv 생성 완료, `torch 2.10.0+cu130`, `CUDA available: True`, `GPU name: NVIDIA GB10`, `lerobot import: OK`. GB10 capability 12.1 UserWarning 출력됨(무시) |
| 2 | DGX: `source ~/smolvla/dgx/.arm_finetune/bin/activate && bash ~/smolvla/dgx/scripts/preflight_check.sh smoke` | preflight 전 항목 PASS (HF_HOME / venv / 메모리 / Walking RL / Ollama / 디스크) | PASS | HF_HOME/venv/CUDA_VISIBLE_DEVICES OK, 가용 RAM 76 GiB 이상, Ollama GPU 미점유, 디스크 3330 GiB. Walking RL(`env_isaaclab`)은 관찰만 하고 건드리지 않음 |
| 3 | DGX: `bash ~/smolvla/dgx/scripts/smoke_test.sh` | preflight 자동 통과 + lerobot-train 1 step 완료, loss 값 출력, exit code 0 | PASS | 최종 실행 exit code 0. `loss:0.545`, `5.97s/step`, 전체 smoke 소요 48초. 중간 실패 원인 4건(`venv` 활성 순서, output dir 선생성, `policy.push_to_hub`, camera `rename_map`)은 `dgx/scripts/smoke_test.sh` 수정 후 재배포하여 해소 |
| 4 | smoke_test 출력에서 GPU util peak / GPU mem peak / 소요 시간 기록 후 `docs/lerobot_study/06_smolvla_finetune_feasibility.md §5.2` 표 갱신 | 실측값 기록 완료 | PASS | §5.2 갱신 완료. 최종 실측: GPU util peak 90%, GPU mem peak N/A(GB10 UMA), System RAM used peak 48226 MiB, 전체 소요 48초 |

## Codex 수정 반영 확인

| 파일 | 반영 내용 | 확인 상태 |
|---|---|---|
| `scripts/deploy_dgx.sh` | DGX 대상 디렉터리를 rsync 전에 생성하고 `set -e`로 rsync 실패가 exit code에 반영되도록 한 기존 BACKLOG #9 수정 사항. 본 테스트의 Codex 검증 #1에서 재배포 PASS로 확인 | 반영됨 |
| `dgx/scripts/smoke_test.sh` | 단독 실행 가능하도록 venv 활성화 순서를 preflight 앞으로 이동. lerobot output dir 선생성 방지. smoke test용 `policy.push_to_hub=false`, camera `rename_map`, `log_freq=1` 추가. GB10 UMA 자원 기록을 위해 resource sample 별도 저장, 1초 샘플링, GPU mem N/A 및 system RAM peak 출력 보강 | 반영됨 |
| `docs/lerobot_study/06_smolvla_finetune_feasibility.md` | §5.2를 추정 표에서 2026-04-28 DGX Spark GB10 smoke test 실측 표로 갱신. loss, train step, 전체 smoke 소요, GPU util peak, GPU mem N/A, system RAM peak 기록 | 반영됨 |
| `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | DGX에서는 upstream lerobot을 직접 수정하지 않고 `dgx/` wrapper로 보정했다는 원칙과 `smoke_test.sh` 변경 이유/영향/검증 결과를 기존 `02/03` 문서 양식에 맞춰 신규 작성 | 반영됨 |
| `docs/work_flow/context/current_task.md` | 마지막 완료 history 포인터가 `20260428_1437`로 갱신된 상태임을 확인 | 반영됨 |

스펙 파일(`docs/work_flow/specs/`)은 이번 정리 과정에서 직접 수정하지 않음. 현재 worktree에 보이는 스펙 파일 diff는 기존 변경분으로만 남아 있음.

## 잔여 리스크 (실행 중 점검)

- HF Hub 다운로드가 네트워크 상황에 따라 길어질 수 있음 — 타임아웃 시 재실행
- lerobot extras (`smolvla`, `training`) 의 `transformers` / `accelerate` / `wandb` 가 PyTorch 2.10.0+cu130 과 호환 안 될 가능성 → 1 step smoke test 가 검증 역할
- Ollama 서비스 상시 실행 중 — preflight 에서 점검됨. FAIL 시 `sudo systemctl stop ollama` 고려
- **후행 작업 (TODO-09b 완료 후)**: `docs/storage/06_dgx_venv_setting.md` 신규 작성 (형식: `docs/storage/05_orin_venv_setting.md` 대칭)
