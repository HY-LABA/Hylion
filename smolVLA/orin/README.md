# orin

smolVLA의 Orin 커스텀 레이어입니다.

## 디렉터리 개요

- `lerobot/`: Orin 환경에 맞춘 lerobot 커스텀 런타임 레이어 (inference-only curated trim — 옵션 B 정책, `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` 참조)
- `inference/`: **현행 era 추론 운영 entry** — 학습 ckpt 로드 + 실 SO-ARM + 카메라 HIL 추론 (`orin/inference/README.md` 참조)
- `scripts/`: 운영용 셸 스크립트 — venv·추론·텔레오프 wrapper (`orin/scripts/README.md` 참조)
- `tests/`: 환경 검증·호환성·baseline·latency 측정 스크립트
- `checkpoints/`: 학습 ckpt 다운로드 위치 (HF Hub `huggingface-cli/hf download` 대상)
- `config/`: 시연장 환경 설정 cache — `cameras.json`, `ports.json` (시연장에서 사용자가 채움)
- `docs/leftarm_v2/`: 추론 평가 시트 (분기별)
- `docs/legacy/`: 옛 era 추론 entry 보존 — `hil_inference.py`, `lego_v1_inference.py` (참조만, 현 시연 호출 X)
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
|-- inference/                      # 현행 era (leftarm_v2)
|   |-- README.md
|   |-- leftarm_base_inference.py   # zero-shot 검증 entry (base smolvla_base 만)
|   `-- leftarm_v2_inference.py     # LoRA ckpt 추론 (CKPT_REPO_ID env override)
|-- docs/
|   |-- leftarm_v2/                 # 추론 평가 시트 (000_base, 001, 002, 003 분기별)
|   `-- legacy/                     # 옛 era 추론·측정 자산 보존
|       |-- README.md
|       |-- hil_inference.py        # era 무관 환경 검증 추론
|       |-- lego_v1_inference.py    # lego_v1 era 추론
|       |-- inference_baseline.py   # 더미 입력 forward 검증 (legacy)
|       `-- measure_latency.py      # latency p50/p95 측정 (legacy)
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
|   |-- run_python.sh               # 일반 Python wrapper (venv 활성화 + 인자 전달)
|   `-- run_inference_leftarm_v2.sh # leftarm_v2 era wrapper (download/check/dry-run/live/zero-shot)
`-- tests/
    |-- README.md
    |-- check_hardware.sh           # 단일 진입점 (first-time/resume 모드)
    |-- configs/
    |   |-- first_time.yaml         # first-time 모드 점검 항목·임계치
    |   `-- resume.yaml             # resume 모드 cached 값 검증 룰
    |-- smoke_test.py               # venv/CUDA/import/smolvla forward 환경 검증
    |-- load_checkpoint_test.py     # ckpt 호환성 검증 (forward + action shape)
    `-- diagnose_motor_encoder.py   # SO-ARM 모터 encoder 진단 (관절별 raw position)
```
