# datacollector/tests

DataCollector 환경 점검 스크립트 위치.

## 현재 상태

환경 점검 게이트 스크립트 이식 예정 (TODO-G3).

`orin/tests/check_hardware.sh` 의 DataCollector 버전을 TODO-G3 시점에 이식한다.

## 예정 내용 (TODO-G3)

- SO-ARM 포트 자동 발견 + 검증
- 카메라 인덱스 자동 발견 + 검증
- venv 의존성 점검 (lerobot, torch, datasets import)
- first-time 모드 / resume 모드 분기

## 현재 수동 검증 명령

```bash
# venv 활성화 후
source ~/smolvla/datacollector/.hylion_collector/bin/activate

# lerobot import 확인
python -c "import lerobot; print(lerobot.__version__)"

# torch 확인
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"

# SO-ARM 포트 발견
lerobot-find-port

# 카메라 발견
lerobot-find-cameras opencv
```
