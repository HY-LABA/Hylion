# datacollector/interactive_cli

smolVLA Interactive CLI — datacollector 노드 (수집 책임)

## 개요

본 디렉터리는 3 노드 (orin / dgx / datacollector) 공통 boilerplate 를 동일 복사한 것입니다.
devPC 에서 한 곳 수정 후 deploy_orin, deploy_dgx, deploy_datacollector 3 번으로 동기화하세요.

## 호출법

```bash
bash datacollector/interactive_cli/main.sh
```

DataCollector 머신 **직접 터미널**에서 실행. 스크립트 시작 시 "이 환경에서 실행하시는 게 맞나요? [Y/n]" 확인 단계가 있습니다.

## 디렉터리 구조

```
datacollector/interactive_cli/
├── README.md                  # 본 파일
├── main.sh                    # bash 진입점 (venv activate + python 호출, cusparseLt 패치 없음)
├── flows/
│   ├── __init__.py
│   ├── entry.py               # flow 0 (이 환경 맞나요?) + flow 1 (장치 선택)  <- F1/F2 boilerplate
│   ├── env_check.py           # flow 2 (환경 체크 — 04 G3·G4 책임 흡수)        <- D2 구현
│   ├── teleop.py              # flow 3·4 (텔레오퍼레이션 + 확인)               <- D2 구현
│   ├── data_kind.py           # flow 5 (학습 종류 질문)                         <- D1·D2 결정
│   ├── record.py              # flow 6 (lerobot-record draccus 인자 생성)       <- D2 구현
│   └── transfer.py            # flow 7 (HF Hub / rsync / 안함 선택)            <- D2 구현
└── configs/
    └── node.yaml              # 노드 식별자 (node: datacollector) + venv 경로
```

## 노드별 차이점 (3 노드 동일 복사 중 datacollector 특화 항목)

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

- D1 study: flow 5 학습 종류 옵션 결정 (사용자 합의 필요)
- D2 task: `flows/env_check.py`, `teleop.py`, `data_kind.py`, `record.py`, `transfer.py` 구현
- D3 prod: 실 DataCollector 환경 통합 검증 (04 BACKLOG #7·#8·#9 통합)
