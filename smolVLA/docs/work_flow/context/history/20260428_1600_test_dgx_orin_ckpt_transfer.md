# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-28 15:46 | 스펙: `docs/work_flow/specs/02_dgx_setting.md` | TODO: 10b

## 테스트 목표

배포 환경 세팅 — DGX→Orin 체크포인트 전송 prod 검증.

TODO-10 에서 작성한 세 스크립트(`save_dummy_checkpoint.sh` → `sync_ckpt_dgx_to_orin.sh` → `load_checkpoint_test.py`)가 실제 동작함을 확인한다. DGX 에서 dummy 체크포인트를 생성하고, devPC 경유 2-hop 으로 Orin 에 전송한 뒤, Orin 에서 정책 로드 + forward pass 까지 PASS 하면 완료. bf16/safetensors 호환성 및 lerobot SHA 호환성 검증이 핵심.

## DOD (완료 조건)

- `save_dummy_checkpoint.sh` PASS: preflight 통과 + 1 step 학습 + 체크포인트 저장 확인
- `sync_ckpt_dgx_to_orin.sh` PASS: DGX → devPC → Orin 2-hop 전송 정상 종료, Orin 측 safetensors 헤더 검증 PASS
- `load_checkpoint_test.py` PASS: 정책 로드 → config 출력 → forward pass → action shape 출력, exit code 0
- 호환성 결과 기록 (DGX PyTorch 버전 / Orin PyTorch 버전 / action dtype / action range)

## 환경

- devPC (`babogaeguri@babogaeguri-950QED`) — 전송 허브
- DGX Spark (`laba@spark-8434`): 체크포인트 생성 환경, venv `~/smolvla/dgx/.arm_finetune`
- Orin (`laba@ubuntu`): 추론 검증 환경, venv `~/smolvla/orin/.hylion_arm`
- 전송 경로: DGX → devPC 임시 → Orin (2-hop, `sync_ckpt_dgx_to_orin.sh`)

## Codex 검증 (비대화형)

<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->
<!-- 주의: #8은 개발자 직접 검증 #1 (dummy 체크포인트 생성) 완료 후 실행할 것 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | devPC: `bash -n scripts/sync_ckpt_dgx_to_orin.sh` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 2 | devPC: `bash -n dgx/scripts/save_dummy_checkpoint.sh` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 3 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/load_checkpoint_test.py` | syntax check 통과 (출력 없음, exit code 0) | PASS | 출력 없음, exit code 0 |
| 4 | devPC: `bash scripts/deploy_dgx.sh` | rsync 정상 종료, `save_dummy_checkpoint.sh` DGX 배포 완료, exit code 0 | PASS | sandbox network 차단으로 1차 실패 후 승인 실행. `scripts/save_dummy_checkpoint.sh` 및 `docs/reference/lerobot/` rsync 완료, exit code 0 |
| 5 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료, `load_checkpoint_test.py` Orin 배포 완료, exit code 0 | PASS | sandbox network 차단으로 1차 실패 후 승인 실행. `examples/tutorial/smolvla/load_checkpoint_test.py` rsync 완료, exit code 0 |
| 6 | DGX: `ssh dgx "ls ~/smolvla/dgx/scripts/"` | `save_dummy_checkpoint.sh` 존재 | PASS | `preflight_check.sh`, `save_dummy_checkpoint.sh`, `setup_train_env.sh`, `smoke_test.sh` 확인 |
| 7 | Orin: `ssh orin "ls ~/smolvla/orin/examples/tutorial/smolvla/"` | `load_checkpoint_test.py` 존재 | PASS | `load_checkpoint_test.py`, `smoke_test.py`, `using_smolvla_example.py` 확인 |
| 8 | devPC: `bash scripts/sync_ckpt_dgx_to_orin.sh --dry-run` | dry-run 모드 정상 종료, 전송 대상 파일 목록 출력, exit code 0 | PASS | run=`dummy_ckpt`, step=`000001` 자동 선택. DGX→devPC 대상: `config.json`, `model.safetensors`, `train_config.json`, processor 파일들 확인. exit code 0 |

## 개발자 직접 검증 (대화형, 약 30~60 분 소요)

<!-- 개발자가 DGX/Orin SSH 터미널과 devPC 에서 직접 실행하고 결과를 기록한다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | DGX: `bash ~/smolvla/dgx/scripts/save_dummy_checkpoint.sh` | preflight PASS + 1 step 학습 + 체크포인트 저장 완료 (`~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/`) | PASS | 개발자 실행 로그 확인. preflight PASS, 1 step 학습 완료, 소요 55초, checkpoint 저장 완료. 환경: venv `.arm_finetune`, `HF_HOME=/home/laba/smolvla/.hf_cache`, `CUDA_VISIBLE_DEVICES=0` |
| 2 | DGX: `ls -la ~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/` | `config.json`, `train_config.json`, `model.safetensors` (≈ 900 MB) 존재 | PASS | 개발자 로그에서 `config.json`, `train_config.json`, `model.safetensors` 906,712,520 bytes 및 processor 파일들 확인 |
| 3 | devPC: `bash scripts/sync_ckpt_dgx_to_orin.sh --run dummy_ckpt` | DGX → devPC → Orin 2-hop 전송 정상 종료, Orin 측 safetensors 헤더 검증 PASS 메시지 | PASS | 개발자 실행 로그 확인. DGX→devPC 및 devPC→Orin 전송 완료, total size 906,732,058 bytes, `model.safetensors 헤더 읽기 OK` |
| 4 | Orin: `ls -la ~/smolvla/orin/checkpoints/dummy_ckpt/000001/` | safetensors 파일 크기가 DGX 측과 동일 | PASS | 개발자 실행 로그의 Orin 측 파일 검증에서 `model.safetensors` 906,712,520 bytes 확인. DGX 측 생성 로그와 byte 단위 동일 |
| 5 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py --ckpt-path ~/smolvla/orin/checkpoints/dummy_ckpt/000001/` | 4단계 모두 통과: 정책 로드 → config 출력 → forward pass → action shape `(1, 50, *)` 출력. exit code 0 | PASS | 개발자 실행 로그 확인. `SmolVLAPolicy.from_pretrained` 로드, config 출력, forward pass 성공, action shape `(1, 50, 6)`, 최종 `체크포인트 호환성 검증 PASS` |
| 6 | 결과 기록: DGX 학습 PyTorch 버전 / Orin 추론 PyTorch 버전 / action 출력 dtype / action range | 호환성 결과 기록 완료 | PASS | DGX PyTorch `2.10.0+cu130`; Orin PyTorch `2.5.0a0+872d972e41.nv24.08`; policy dtype `torch.bfloat16`; action dtype `torch.float32`; action range `[-2.3179, 2.6352]` |

## 잔여 리스크 (실행 중 점검)

- lerobot SHA mismatch — DGX editable submodule SHA = Orin curated `orin/lerobot/` SHA 라야 모델 클래스 호환. orin/lerobot/ 트리밍이 SmolVLA policy 일부를 빠뜨렸으면 로드 실패
- DGX bf16 (cu130) → Orin bf16 (cu126 + JP 6.0 wheel) 미세 numerical 차이 가능성 (로드는 OK 여도 출력값 차이) — 본 TODO 에서는 로드/forward 성공 여부만 검증
- Orin 측 `image_features` 키 매핑 — `load_checkpoint_test.py` 의 `cfg.image_features` 가 자동 처리하지만 실 환경 검증 필요
