# orin

smolVLA의 Orin 커스텀 레이어입니다.

## 디렉터리 개요

- `calibration/`: 캘리브레이션 및 진단 스크립트
  - `diagnose_motor_encoder.py`: `/dev/serial/by-id` -> `/dev/ttyACM*` 매핑을 출력하고, motor id 1~6의 raw `Present_Position` 값을 읽어 출력
- `lerobot/`: Orin 환경에 맞춘 lerobot 커스텀 런타임 레이어 (추론 중심)
- `scripts/`: 운영용 셸 스크립트 (`run_teleoperate.sh`, `setup_env.sh` 등)
- `examples/`: 로컬 실행 예제

## 트리 구조

```text
orin/
|-- README.md
|-- pyproject.toml
|-- calibration/
|   `-- diagnose_motor_encoder.py
|-- lerobot/
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
|   |-- utils/
|   |-- __init__.py
|   |-- __version__.py
|   `-- types.py
|-- scripts/
|   |-- run_teleoperate.sh
|   `-- setup_env.sh
`-- examples/
```
