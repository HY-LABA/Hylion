# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-28 14:24 | 스펙: `docs/work_flow/specs/02_dgx_setting.md` | TODO: 09b

## 테스트 목표

학습 환경 세팅 — DGX prod 검증.

TODO-09 에서 작성한 세 스크립트(`setup_train_env.sh` → `preflight_check.sh` → `smoke_test.sh`)가 DGX Spark 에서 실제 동작함을 확인한다. setup 완료 후 preflight PASS, lerobot-train 1 step smoke test PASS, GB10 throughput 실측치를 기록하는 것까지 완료 조건으로 한다.

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
| 1 | devPC: `bash scripts/deploy_dgx.sh` | rsync 정상 종료, DGX 측 `~/smolvla/dgx/` 와 `~/smolvla/docs/reference/lerobot/` 갱신, exit code 0 | FAIL | 2026-04-28 실행. 스크립트 최종 exit code는 0이지만 rsync가 각각 `mkdir "/home/laba/smolvla/dgx" failed: No such file or directory (2)`, `mkdir "/home/laba/smolvla/docs/reference/lerobot" failed: No such file or directory (2)` 및 `rsync error: code 11` 출력. 실제 배포 실패 |
| 2 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/setup_train_env.sh"` | syntax check 통과 (출력 없음, exit code 0) | FAIL | exit code 127. `bash: /home/laba/smolvla/dgx/scripts/setup_train_env.sh: No such file or directory` |
| 3 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/preflight_check.sh"` | syntax check 통과 (출력 없음, exit code 0) | FAIL | exit code 127. `bash: /home/laba/smolvla/dgx/scripts/preflight_check.sh: No such file or directory` |
| 4 | DGX: `ssh dgx "bash -n ~/smolvla/dgx/scripts/smoke_test.sh"` | syntax check 통과 (출력 없음, exit code 0) | FAIL | exit code 127. `bash: /home/laba/smolvla/dgx/scripts/smoke_test.sh: No such file or directory` |
| 5 | DGX: `ssh dgx "ls ~/smolvla/dgx/scripts/"` | `setup_train_env.sh`, `preflight_check.sh`, `smoke_test.sh` 3개 파일 존재 | FAIL | exit code 2. `ls: cannot access '/home/laba/smolvla/dgx/scripts/': No such file or directory` |
| 6 | DGX: `ssh dgx "ls ~/smolvla/docs/reference/lerobot/src/lerobot/policies/smolvla/"` | `configuration_smolvla.py`, `modeling_smolvla.py`, `processor_smolvla.py`, `smolvlm_with_expert.py`, `__init__.py` 5개 파일 존재 (submodule 정상 배포) | FAIL | exit code 2. `ls: cannot access '/home/laba/smolvla/docs/reference/lerobot/src/lerobot/policies/smolvla/': No such file or directory` |

## 개발자 직접 검증 (대화형, 약 30~60 분 소요)

<!-- 개발자가 DGX SSH 터미널에서 직접 실행하고 결과를 기록한다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | DGX: `bash ~/smolvla/dgx/scripts/setup_train_env.sh` | venv `~/smolvla/dgx/.arm_finetune` 생성, PyTorch 2.10.0+cu130 설치, lerobot editable 설치 완료. 출력 마지막에 `torch.cuda.is_available()=True`, `GPU name: NVIDIA GB10`, `lerobot import OK` 확인 | | HF Hub 다운로드 포함 약 5~15 분 소요. GB10 capability 12.1 UserWarning 출력될 수 있으나 무시 가능 |
| 2 | DGX: `source ~/smolvla/dgx/.arm_finetune/bin/activate && bash ~/smolvla/dgx/scripts/preflight_check.sh smoke` | preflight 전 항목 PASS (HF_HOME / venv / 메모리 / Walking RL / Ollama / 디스크) | | preflight FAIL 시 본인 프로세스(Jupyter 커널, 본인 Ollama 등)만 정리. Walking RL(`env_isaaclab`) 건드리지 말 것 |
| 3 | DGX: `bash ~/smolvla/dgx/scripts/smoke_test.sh` | preflight 자동 통과 + lerobot-train 1 step 완료. loss 값 출력, exit code 0 | | HF Hub 모델 다운로드 약 5~15 분 + 학습 1~3 분 소요. smoke_test 가 preflight 를 내부 호출하므로 별도 venv 활성화 불필요 |
| 4 | smoke_test 출력에서 GPU util peak / GPU mem peak / 소요 시간 기록 후 `docs/lerobot_study/06_smolvla_finetune_feasibility.md §5.2` 표 갱신 | 실측값 기록 완료 | | UMA 구조 특성상 `nvidia-smi memory.total` 은 N/A. `free -h` 로 시스템 RAM 점유 병행 관찰 권장 |

## 잔여 리스크 (실행 중 점검)

- HF Hub 다운로드가 네트워크 상황에 따라 길어질 수 있음 — 타임아웃 시 재실행
- lerobot extras (`smolvla`, `training`) 의 `transformers` / `accelerate` / `wandb` 가 PyTorch 2.10.0+cu130 과 호환 안 될 가능성 → 1 step smoke test 가 검증 역할
- Ollama 서비스 상시 실행 중 — preflight 에서 점검됨. FAIL 시 `sudo systemctl stop ollama` 고려
- **후행 작업 (TODO-09b 완료 후)**: `docs/storage/06_dgx_venv_setting.md` 신규 작성 (형식: `docs/storage/05_orin_venv_setting.md` 대칭)

## 테스트 메모

- 2026-04-28 Codex 비대화형 검증 결과, DGX 원격 기본 경로 `/home/laba/smolvla` 하위 디렉터리가 없어 `scripts/deploy_dgx.sh`의 rsync 배포가 실패했다.
- `scripts/deploy_dgx.sh`는 rsync 실패(code 11) 후에도 마지막 `echo`까지 진행되어 최종 exit code 0을 반환했다. 배포 실패가 성공처럼 보이지 않도록 원격 디렉터리 생성(`mkdir -p`) 및 실패 시 non-zero exit 처리 업데이트가 필요하다.
- 선행 배포 실패로 인해 대화형 setup/preflight/smoke 검증은 아직 수행하지 않았다. Walking RL 프로세스(`env_isaaclab`)는 건드리지 않았다.
