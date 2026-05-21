# orin/scripts/ — Orin 유틸리티 스크립트

Orin (NVIDIA Jetson AGX) 에서 직접 실행하는 셸 스크립트 모음.

## 스크립트 목록

| 파일 | 역할 | 실행 위치 |
|---|---|---|
| `setup_env.sh` | Orin venv 초기 셋업 (PyTorch wheel, lerobot install) | Orin SSH |
| `run_python.sh` | 일반 Python 래퍼 (venv 활성화 + 인자 전달) | Orin SSH |
| `run_inference_leftarm_v2.sh` | leftarm_v2 era 추론 단일 진입점 (분기 ckpt 는 env override 로 선택) | Orin SSH |

## run_inference_leftarm_v2.sh

leftarm_v2 era 의 학습 ckpt 를 Orin 에서 추론하는 thin shell wrapper.
내부적으로 `orin/inference/leftarm_v2_inference.py` 호출 (zero-shot subcommand 는 `leftarm_base_inference.py`).

**분기 ckpt 선택**: `CKPT_REPO_ID` 환경변수로 override. default = 001 분기 (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`). 다른 분기 평가 시:

```bash
CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 \
  ./run_inference_leftarm_v2.sh live task1
```

### Subcommands

```bash
# 1. HF Hub 에서 ckpt 다운로드 + n_action_steps 자동 점검·수정
./run_inference_leftarm_v2.sh download

# 2. config.json 정합 점검 (n_action_steps, image feature 키)
./run_inference_leftarm_v2.sh check

# 3. lerobot CLI 확인 + 명령 골자 출력
./run_inference_leftarm_v2.sh dry-run

# 4. 실 SO-ARM + 카메라 추론 — task1
./run_inference_leftarm_v2.sh live task1

# 5. 실 SO-ARM + 카메라 추론 — task2
./run_inference_leftarm_v2.sh live task2

# 6. zero-shot 검증 — base smolvla_base 만 로딩 (LoRA adapter X)
./run_inference_leftarm_v2.sh zero-shot task1
./run_inference_leftarm_v2.sh zero-shot task2
```

### 사전 조건

- `orin/config/ports.json` 의 `follower_port` 채워져 있어야 함
- `orin/config/cameras.json` 의 `top.index`, `wrist.index` 채워져 있어야 함
- 또는 환경 변수로 override: `FOLLOWER_PORT=/dev/ttyUSB0 TOP_IDX=0 WRIST_IDX=2 ./run_inference_leftarm_v2.sh live task1`

### 관련 문서

- 추론 entry: [`orin/inference/README.md`](../inference/README.md)
- 추론 평가 시트: `orin/docs/leftarm_v2/{000_base,001,002,003}_eval_*.md`
- ckpt 학습 가이드: [`docs/storage/prof_train_setting.md`](../../docs/storage/prof_train_setting.md)
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
