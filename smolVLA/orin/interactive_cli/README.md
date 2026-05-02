# orin/interactive_cli

smolVLA Interactive CLI — orin 노드 (추론 책임)

## 개요

본 디렉터리는 3 노드 (orin / dgx / datacollector) 공통 boilerplate 를 동일 복사한 것입니다.
devPC 에서 한 곳 수정 후 deploy_orin, deploy_dgx, deploy_datacollector 3 번으로 동기화하세요.

## 호출법

```bash
bash orin/interactive_cli/main.sh
```

VSCode remote-ssh 로 Orin 에 SSH 연결 후 터미널에서 실행.

## 디렉터리 구조

```
orin/interactive_cli/
├── README.md                  # 본 파일
├── main.sh                    # bash 진입점 (venv activate + cusparseLt 패치 + python 호출)
├── flows/
│   ├── __init__.py
│   ├── entry.py               # flow 0 (진입 확인) + flow 1 (장치 선택)  <- F1/F2 boilerplate
│   ├── env_check.py           # flow 2 (환경 체크)                        <- F2 이후 todo
│   └── inference.py           # flow 3+ (추론 책임)                       <- O2 구현
└── configs/
    └── node.yaml              # 노드 식별자 (node: orin) + venv 경로
```

## 노드별 차이점 (3 노드 동일 복사 중 orin 특화 항목)

| 항목 | orin | dgx | datacollector |
|---|---|---|---|
| venv | `~/smolvla/orin/.hylion_arm` | `~/smolvla/dgx/.arm_finetune` | `~/smolvla/datacollector/.hylion_collector` |
| cusparseLt 패치 | main.sh 에 포함 | 없음 | 없음 |
| node.yaml node 값 | `orin` | `dgx` | `datacollector` |
| flow 0 확인 단계 | 없음 (VSCode remote-ssh) | 없음 (VSCode remote-ssh) | "이 환경 맞나요?" Y/n |
| flow 3+ 모듈 | inference.py (O2 구현) | training.py (X2 구현) | teleop/record/transfer (D2 구현) |

## deploy 동기화 절차

공통 코드 수정 후 3 노드 동기화:

```bash
bash scripts/deploy_orin.sh
bash scripts/deploy_dgx.sh
bash scripts/deploy_datacollector.sh
```

각 deploy 스크립트가 devPC → 해당 노드로 rsync 수행합니다.

## 후행 todo

- F3 이후: `flows/env_check.py` — check_hardware.sh 패턴 wrapping
- O1 study: orin flow 3+ 책임 정의
- O2 task: `flows/inference.py` 구현
- O3 prod: 실 Orin 환경 통합 검증
