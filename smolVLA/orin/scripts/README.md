# orin/scripts/ — Orin 유틸리티 스크립트

Orin (NVIDIA Jetson AGX) 에서 직접 실행하는 셸 스크립트 모음.

## 스크립트 목록

| 파일 | 역할 | 실행 위치 |
|---|---|---|
| `setup_env.sh` | Orin venv 초기 셋업 (PyTorch wheel, lerobot install) | Orin SSH |
| `run_python.sh` | 일반 Python 래퍼 (venv 활성화 + 인자 전달) | Orin SSH |
| `run_inference_leftarm_v2.sh` | leftarm_v2_A2_pc_2026-05-17 체크포인트 추론 단일 진입점 | Orin SSH |

## run_inference_leftarm_v2.sh

leftarm_v2 2A checkpoint (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) 를 Orin 에서 추론하기 위한 thin shell wrapper.
내부적으로 `lerobot-record` (lerobot.scripts.lerobot_record:main) 를 policy 모드로 호출.

### Subcommands

```bash
# 1. HF Hub 에서 ckpt 다운로드 + n_action_steps 자동 점검·수정
./run_inference_leftarm_v2.sh download

# 2. config.json 정합 점검 (n_action_steps, image feature 키)
./run_inference_leftarm_v2.sh check

# 3. lerobot-record CLI 확인 + 명령 골자 출력
./run_inference_leftarm_v2.sh dry-run

# 4. 실 SO-ARM + 카메라 추론 — task1
./run_inference_leftarm_v2.sh live task1

# 5. 실 SO-ARM + 카메라 추론 — task2
./run_inference_leftarm_v2.sh live task2
```

### 사전 조건

- `orin/config/ports.json` 의 `follower_port` 채워져 있어야 함
- `orin/config/cameras.json` 의 `top.index`, `wrist.index` 채워져 있어야 함
- 또는 환경 변수로 override: `FOLLOWER_PORT=/dev/ttyUSB0 TOP_IDX=0 WRIST_IDX=2 ./run_inference_leftarm_v2.sh live task1`

### 관련 문서

- spec: `docs/work_flow/specs/02_leftarm_v2_finetune.md` § TODO-03
- ckpt 학습 가이드: `docs/storage/prof_train_setting.md`
- 구현 보고: `docs/work_flow/context/todos/03B/01_implementation.md`
