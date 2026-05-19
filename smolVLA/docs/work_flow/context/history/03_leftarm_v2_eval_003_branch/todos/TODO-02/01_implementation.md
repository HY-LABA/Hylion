# TODO-02 — Orin 환경 준비 + 평가 시트 골격

> 작성: 2026-05-19 14:30 | task-executor | cycle: 1

## 목표

003 분기 ckpt Orin 다운로드 + dry-run smoke + 003 평가 시트 골격 신설.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/docs/leftarm_v2/003_eval_2026-05-19.md` | 신규 (N) | 003 확장 평가 시트 골격 — camera_empty_eval_2026-05-18.md 양식 mirror |
| `docs/work_flow/context/todos/TODO-02/01_implementation.md` | 신규 (N) | 본 작업 보고서 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Category B: `run_inference_leftarm_v2.sh` 로직 수정 X (환경 변수 override 만 사용) ✓
- Category C: `orin/docs/leftarm_v2/` 기존 디렉터리 내 신규 파일 — Category C 미해당 ✓
- Coupled File Rule: `orin/lerobot/` / `orin/pyproject.toml` 미변경 → coupled file 갱신 불필요 ✓
- lerobot-reference-usage: 신규 코드 작성 없음 (문서 파일 + SSH smoke 자동 검증). 기존 inference 패치 그대로 활용 ✓
- 레퍼런스 활용: `camera_empty_eval_2026-05-18.md` (최신 양식 정본) 직접 Read 후 mirror 적용 ✓

## 변경 내용 요약

### 1. 003 평가 시트 신설 (`orin/docs/leftarm_v2/003_eval_2026-05-19.md`)

`camera_empty_eval_2026-05-18.md` 를 양식 정본으로 직접 Read 후 mirror:

- **메타 섹션**: 003 ckpt HF Hub link, LoRA adapter (size: SSH_AUTO 확인 후 기입), 5변수 종합 분기 학습 메타 요약 (final loss·시간은 `[TODO-01 완료 후 인용]` 마커), 선행 사이클 3개 링크.
- **평가 기준 섹션**: camera_empty_eval 양식 그대로 — 지표, 시나리오 구성 표 (20 trial), task instruction 정본, 성공 정의, 실패 원인 분류 코드 표, 재시도 처리 정책. **신설**: trial 시작 전 USB enumeration 체크리스트 (시연장 변동 대비).
- **Trial 기록 섹션**: 4 그룹 × 5 trial = 20 빈 행 골격 (trial #, task, orientation, 성공, 실패 원인, 자유 메모).
- **결과 집계 섹션**: TODO-04 산출 영역 빈 골격 + M1.5·002·003 비교 표 골격.
- **종합 정성 메모 섹션**: 5변수 종합 효과 판단 항목 추가.
- **다음 단계 섹션**: 결과별 분기 (50%+ → M4 진입 / 20~50% → 재평가 / 0~20% → 가설 이동).

### 2. SSH_AUTO 결과 — Orin 접속 불가 (현재 상태)

devPC 기준 Orin SSH (172.16.134.117) 가 현재 도달 불가 (ping 100% loss, SSH timeout):

```
ping 172.16.134.117: 100% packet loss
ssh orin: Connection timed out (exit 255)
```

**원인 분석**: 사용자가 시연장 현장 대기 중 — Orin 이 아직 전원 켜지지 않았거나 현재 네트워크(devPC 위치)에서 도달 불가 상태일 가능성 높음. 시연장 이동 후 또는 Orin 전원 투입 후 SSH_AUTO 재시도 가능.

**이 상태에서 결정 사항**:
- ckpt 다운로드 (B. 003 ckpt download) → 사용자가 Orin 에 직접 실행하거나, Orin 가용 시 재시도
- dry-run smoke (C.) → 동일
- SSH_AUTO 가정 #1·#2 검증 (ports.json, cameras.json null 여부) → 동일

**가용 시 실행 명령 (사용자 직접 또는 Orin 재가용 시)**:

```bash
# Step A: 환경 확인
cd ~/smolvla && source orin/.hylion_arm/bin/activate
cat orin/config/ports.json
cat orin/config/cameras.json
ls ~/.cache/huggingface/lerobot/calibration/
python3 -c 'import torch; print("torch", torch.__version__, "cuda", torch.cuda.is_available())'

# Step B: 003 ckpt 다운로드
export CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
export CKPT_LOCAL_DIR=~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
bash orin/scripts/run_inference_leftarm_v2.sh download

# Step C: dry-run smoke
bash orin/scripts/run_inference_leftarm_v2.sh dry-run task1 2>&1 | tail -50

# Step D: live trial (시연장)
bash orin/scripts/run_inference_leftarm_v2.sh live task1
bash orin/scripts/run_inference_leftarm_v2.sh live task2
```

## DOD 충족 검증

- [x] `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 신설 — camera_empty_eval 양식 mirror ✓
- [x] HF Hub repo 파일 구조 완전성 확인 ✓ — adapter_model.safetensors (44MB) + config.json (empty_cameras=1, n_action_steps=50) + preprocessor·postprocessor 전부 존재 확인
- [ ] Orin 003 ckpt 다운로드 완료 — **보류 (Orin SSH 불가 — 사용자 Orin 직접 실행 필요)**
- [ ] dry-run smoke 1 step 성공 — empty_cameras=1 강제 적용 로그 확인 — **보류 (Orin SSH 불가)**
- [ ] Orin cal 파일·ports·cameras 실 값 정합 확인 — **보류 (Orin SSH 불가)**
- [x] Category B (`run_inference_leftarm_v2.sh` 로직) 수정 불필요 확인 ✓ — wrapper dry-run/live subcommand + 환경 변수 override 만으로 003 호출 가능. 코드 변경 X.

## SSH_AUTO 결과 요약

| 항목 | 결과 |
|---|---|
| Orin SSH 접속 | **불가** (172.16.134.117 — ping 100% loss, SSH timeout × 2) |
| ports.json (Orin 실 값) | 미확인 (SSH 불가) |
| cameras.json (Orin 실 값) | 미확인 (SSH 불가) |
| 003 ckpt 다운로드 | 미실시 (SSH 불가) |
| dry-run smoke | 미실시 (SSH 불가) |
| empty_cameras 적용 확인 | **원격 HF Hub 확인: config.json.empty_cameras=1 ✓** |
| n_action_steps (HF Hub) | **50 ✓** (config.json 직접 확인) |
| adapter_model.safetensors (HF Hub) | **44MB** (x-linked-size: 46,201,840 bytes 확인) |
| HF Hub repo 파일 구조 | **완전** — adapter_config.json, adapter_model.safetensors, config.json, policy_preprocessor.json, policy_preprocessor_step_5_normalizer_processor.safetensors, policy_postprocessor.json, policy_postprocessor_step_0_unnormalizer_processor.safetensors, train_config.json 전부 존재 |

## 사용자 PHYS_REQUIRED 준비 상태

003 평가 시트 (`orin/docs/leftarm_v2/003_eval_2026-05-19.md`) 는 완성됨. **Orin SSH 불가 상태**로 ckpt 다운로드·smoke 는 미실시.

사용자가 Orin 접속 가능한 환경 (시연장 또는 전원 투입 후) 에서 아래 순서 실행:

```bash
# Orin 에서 직접
cd ~/smolvla && source orin/.hylion_arm/bin/activate

# 003 ckpt 다운로드
export CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
export CKPT_LOCAL_DIR=~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
bash orin/scripts/run_inference_leftarm_v2.sh download

# dry-run smoke (robot 미연결 가능)
bash orin/scripts/run_inference_leftarm_v2.sh dry-run task1

# live trial (시연장)
bash orin/scripts/run_inference_leftarm_v2.sh live task1   # task1 front/back 각 5회
bash orin/scripts/run_inference_leftarm_v2.sh live task2   # task2 front/back 각 5회
```

**wrapper 동작 확인 (devPC 코드 분석)**:
- `dry-run` subcommand: `leftarm_v2_inference.py --mode dry-run --max-steps 1` 호출 — robot 미연결 시 connect() 에서 에러 (정상, 코드 경로 검증 완료)
- `live` subcommand: `--max-steps 1000` 하드코딩 (BACKLOG #13 완료 확인)
- 환경 변수 override: `CKPT_REPO_ID`, `CKPT_LOCAL_DIR` 로 003 ckpt 지정 — 코드 변경 X

## 잔여 리스크

1. **Orin SSH 불가**: devPC 에서 현재 172.16.134.117 도달 불가. 사용자가 Orin 이 있는 환경에서 직접 접속하거나, Orin 전원 투입 후 재접속 필요. smoke 및 ckpt 다운로드는 사용자가 Orin 에서 직접 처리.
2. **ports.json / cameras.json null 가능성**: Orin 실 환경 값 미확인. null 이면 환경 변수 override 필요 (`FOLLOWER_PORT=...`, `TOP_IDX=...`, `WRIST_IDX=...`). wrapper 가 null 감지 시 override 방법 자동 안내하므로 run_inference_leftarm_v2.sh 코드 변경 불필요.
3. **config.json empty_cameras**: 003 ckpt `config.json.empty_cameras=1` 이면 `leftarm_v2_inference.py` L508-525 패치가 자동 강제 적용. 확인은 dry-run 로그에서 가능.
4. **TODO-01 메타 미완**: 학습 final loss·시간은 `[TODO-01 완료 후 인용]` 마커로 처리. TODO-04 에서 채움.

## code-tester 검증 권고

- `003_eval_2026-05-19.md` 양식이 `camera_empty_eval_2026-05-18.md` 와 mirror 되는지 비교
- 메타 섹션 링크 경로 유효성 (상대 경로 ../../.. 기준)
- Trial 기록 표 20행 (4 그룹 × 5 trial) 골격 완전성
- `[TODO-01 완료 후 인용]` 마커가 집계 섹션에 명시됐는지
- SSH_AUTO 미완 상태가 DOD 체크리스트에 명시됐는지
- wrapper 환경 변수 override 명령이 Category B 비해당임을 확인 (코드 변경 X)
