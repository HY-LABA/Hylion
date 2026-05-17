# orin

smolVLA의 Orin 커스텀 레이어입니다.

## 디렉터리 개요

- `lerobot/`: Orin 환경에 맞춘 lerobot 커스텀 런타임 레이어 (inference-only curated trim — 옵션 B 정책, `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 참조)
- `inference/`: **시연 환경 추론 entry** — 학습 ckpt 로드 + 실 SO-ARM + 카메라 HIL 추론 (`orin/inference/README.md` 참조)
- `scripts/`: 운영용 셸 스크립트 — venv·추론·텔레오프 wrapper (`orin/scripts/README.md` 참조)
- `tests/`: 환경 검증·호환성·baseline·latency 측정 스크립트
- `checkpoints/`: 학습 ckpt 다운로드 위치 (HF Hub `huggingface-cli/hf download` 대상)
- `config/`: 시연장 환경 설정 cache — `cameras.json`, `ports.json` (시연장에서 사용자가 채움)
- `examples/`: 로컬 실행 예제
- `pyproject.toml`: Orin 의존성 — `lerobot[smolvla]` + peft + 시스템 ABI 호환 (`docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 참조)

## 트리 구조

```text
orin/
|-- README.md
|-- pyproject.toml
|-- checkpoints/
|   `-- README.md           # ckpt 다운로드 안내 (HF Hub 캐시)
|-- config/
|   |-- README.md
|   |-- cameras.json        # {index, rotation, width, height, fps, fourcc, flip}
|   `-- ports.json          # {follower_port, leader_port}
|-- inference/
|   |-- README.md
|   |-- hil_inference.py            # 사전학습 ckpt 추론 (smolvla_base smoke)
|   |-- lego_v1_inference.py        # leftarm_v1 era entry
|   `-- leftarm_v2_inference.py     # leftarm_v2 학습 ckpt + LoRA adapter + rename_map (2026-05-18 신설)
|-- lerobot/
|   |-- __init__.py
|   |-- __version__.py
|   |-- types.py
|   |-- cameras/
|   |-- configs/
|   |-- envs/
|   |-- model/
|   |-- motors/
|   |-- optim/
|   |-- policies/
|   |-- processor/
|   |-- robots/
|   |-- scripts/
|   |-- teleoperators/
|   `-- utils/
|-- scripts/
|   |-- README.md
|   |-- setup_env.sh                # venv + Jetson PyTorch + lerobot[smolvla] + peft
|   |-- run_python.sh
|   |-- run_teleoperate.sh
|   `-- run_inference_leftarm_v2.sh # leftarm_v2 wrapper (download/check/dry-run/live)
|-- tests/
|   |-- README.md
|   |-- diagnose_motor_encoder.py   # 시리얼 매핑 + 모터 raw position
|   |-- load_checkpoint_test.py
|   |-- measure_latency.py
|   |-- inference_baseline.py
|   `-- smoke_test.py
`-- examples/
```
