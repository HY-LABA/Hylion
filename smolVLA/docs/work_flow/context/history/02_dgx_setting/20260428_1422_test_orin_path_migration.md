# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-28 13:31 | 스펙: `docs/work_flow/specs/02_dgx_setting.md` | TODO: 09c

## 테스트 목표

학습 환경 세팅 — Orin 배포 경로 마이그레이션 검증.

TODO-09 부수 작업으로 Orin 측 배포 경로가 `~/smolvla/` → `~/smolvla/orin/` 으로 변경되었다 (DGX 와 형제 구조). 새 경로에 정상 배포되고, 옛 잔여물이 정리되며, 새 venv 가 정상 동작함을 확인한다. teleop 회귀 검증의 minimal 단계 (`--help` 출력) 까지 포함.

## DOD (완료 조건)

- TODO-09 부수 작업으로 Orin 측 배포 경로가 `~/smolvla/` → `~/smolvla/orin/` 으로 변경된 후, 옛 잔여 파일이 정리되고 새 venv 가 정상 동작함을 확인
- teleop 동작이 기존과 동일한지 확인 (01_teleoptest 기능 회귀 X)

## 환경

- devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)
- Orin: JetPack 6.2.2, Python 3.10, 신규 venv `~/smolvla/orin/.hylion_arm` (hidden)
- 변경된 배포 경로: `/home/laba/smolvla/orin/` (rsync 대상)

## 배경

- `scripts/deploy_orin.sh` 의 배포 대상 경로가 `~/smolvla/` → `~/smolvla/orin/` 로 변경됨
- 이전 배포로 Orin 머신에 옛 경로 잔존 가능성 있음. rsync 는 새 경로만 동기화하므로 옛 파일 자동 삭제 X
- 옛 잔여물은 개발자 직접 검증 단계에서 수동 정리

## Codex 검증 (비대화형)

<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다. 본 단계는 #2 Orin 잔여물 식별 결과를 개발자 직접 검증 #2 의 입력으로 사용한다. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC 에서 `cd C:/Users/admin/Desktop/Hylion/smolVLA && bash scripts/deploy_orin.sh` 실행 | rsync 정상 종료, `~/smolvla/orin/` 새로 생성/갱신, exit code 0 | PASS — 리눅스 devPC 경로 `/home/babogaeguri/Desktop/Hylion/smolVLA` 에서 `bash scripts/deploy_orin.sh` 실행. rsync exit code 0, Orin 대상 `/home/laba/smolvla/orin/` 생성/갱신 확인. | 2026-04-28 실행 |
| 2 | Orin: `ssh orin "ls -A ~/smolvla/"` | `orin/` 디렉터리 존재 확인. 옛 잔여물 후보 (`lerobot/`, `scripts/`, `calibration/`, `examples/`, `pyproject.toml`, `README.md`, `.venv/`) 출력 — 어느 것이 실제로 존재하는지 식별해 결과 컬럼에 명시 (`-A` 로 숨김 파일 `.venv/` 도 표시) | PASS — `orin/` 존재. 옛 잔여물 후보 중 `.venv/`, `README.md`, `calibration/`, `examples/`, `lerobot/`, `pyproject.toml`, `scripts/` 존재. 추가 잔여 후보 `lerobot.egg-info/` 도 존재. | 개발자 직접 검증 #2 삭제 대상에 `lerobot.egg-info/` 포함 여부 확인 필요 |
| 3 | Orin: `ssh orin "ls ~/smolvla/orin/scripts/"` | `setup_env.sh`, `run_teleoperate.sh` 두 파일 존재 | PASS — `run_teleoperate.sh`, `setup_env.sh` 존재. | |
| 4 | Orin: `ssh orin "ls ~/smolvla/orin/lerobot/policies/smolvla/"` | `configuration_smolvla.py`, `modeling_smolvla.py`, `processor_smolvla.py`, `smolvlm_with_expert.py`, `__init__.py` 5개 파일 존재 | PASS — 기대한 5개 파일 모두 존재. 추가로 `README.md` 존재. | |
| 5 | Orin: `ssh orin "bash -n ~/smolvla/orin/scripts/setup_env.sh"` | syntax check 통과 (출력 없음, exit code 0) | PASS — 출력 없음, exit code 0. | |

## 개발자 직접 검증 (대화형, 약 20~40 분 소요)

<!-- 개발자가 Orin Remote SSH 터미널에서 직접 실행하고 결과를 기록한다. -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | Orin SSH 터미널에서 `deactivate 2>/dev/null \|\| true` 실행 (옛 venv 활성 상태면 해제) | 영향 없음 (출력 없거나 "command not found") | PASS — 출력 없이 정상 종료. | 옛 venv 활성 상태였다면 prompt 의 `(.venv)` 표시가 사라짐 |
| 2 | Codex 검증 #2 에서 식별된 옛 잔여물만 삭제: `rm -rf ~/smolvla/.venv ~/smolvla/lerobot ~/smolvla/scripts ~/smolvla/calibration ~/smolvla/examples` + `rm -f ~/smolvla/pyproject.toml ~/smolvla/README.md` | 식별된 옛 파일 모두 제거 | PASS — `.venv/`, `lerobot/`, `lerobot.egg-info/`, `scripts/`, `calibration/`, `examples/`, `pyproject.toml`, `README.md` 삭제 실행. | Codex 검증 #2 에서 추가 식별된 `lerobot.egg-info/` 도 함께 삭제 |
| 3 | `ls ~/smolvla/` | `orin/`, 그리고 (있다면) `dgx/`, `docs/` 만 남음 | PASS — 출력 `orin` 만 확인. | 옛 잔여물이 모두 사라졌는지 확인 |
| 4 | `bash ~/smolvla/orin/scripts/setup_env.sh` | 새 venv `~/smolvla/orin/.hylion_arm` 생성, PyTorch + lerobot 설치 완료, 마지막에 CUDA 텐서 연산 검증 출력 (`✓` 표시 + 종료 메시지) | PASS — 최초 실행은 `dpkg` 중단 상태로 막혔으나 `sudo dpkg --configure -a` 후 재실행하여 설치 완료. `python -m venv` 는 `python3-venv` 미설치로 실패했지만 `virtualenv` fallback 으로 `.hylion_arm` 생성 완료. lerobot/PyTorch 설치 완료, CUDA available True, torch `2.5.0a0+872d972e41.nv24.08`, cuDNN `90300`, CUDA 텐서 연산 `✓`, 종료 메시지 확인. | `libcusparseLt` 시스템 미설치로 LD_LIBRARY_PATH 임시 패치 적용. `torchvision` 은 미설치로 수동 1회 설치 안내 출력됨: `torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl` |
| 5 | `source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/smoke_test.py` | smolVLA 모델 로드 + forward pass 성공. `action shape: torch.Size([1, 6])` + `모든 smoke test 통과. Orin 실행 환경 정상.` 메시지 출력. exit code 0. prompt 가 `(.hylion_arm)` 으로 표시됨 | PASS — `.hylion_arm` 활성 상태에서 재실행. `nvcc`/`ffmpeg` PASS, lerobot import 3종 PASS, `lerobot/smolvla_base` 모델 로드 완료(device `cuda`), dummy observation 기반 `select_action` 성공, `action shape: torch.Size([1, 6])`, `모든 smoke test 통과. Orin 실행 환경 정상.` 확인. | 시스템 체크 경고: `libcusparseLt` 시스템 등록 미확인. 다만 `grep -n "cusparselt" ~/smolvla/orin/.hylion_arm/bin/activate` 및 현재 `LD_LIBRARY_PATH` 에서 `/home/laba/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib` 확인되어 `venv` fallback 적용 상태. 최초 실패 원인인 `torchvision` 누락은 wheel 설치 후 해소됨 |
| 6 | `bash ~/smolvla/orin/scripts/run_teleoperate.sh --help` | help 출력 정상 (서브커맨드 `all`/`calibrate-follower`/`calibrate-leader`/`teleoperate`, 포트 인자 등) | PASS — help 출력 정상. `all`, `calibrate-follower`, `calibrate-leader`, `teleoperate` 서브커맨드 표시 확인. | teleop 회귀 검증의 minimal 단계. calibration 재실행이나 물리 조작 불필요 |

## 잔여 리스크 (실행 중 점검)

- 옛 venv 의 LD_LIBRARY_PATH 패치(cusparselt 우회) 가 새 venv 에 다시 적용돼야 함 → 개발자 직접 검증 #4/#5 에서 activate 스크립트와 현재 세션 LD_LIBRARY_PATH 모두 적용 확인
- calibration JSON 파일 (`~/.cache/huggingface/lerobot/calibration/...`) 은 사용자 홈 캐시에 저장되어 본 마이그레이션과 무관 — 그대로 유지됨
- teleop 풀 회귀 검증 (calibration + 물리 조작) 은 본 TODO 범위 밖. `--help` 출력만 minimal 검증
