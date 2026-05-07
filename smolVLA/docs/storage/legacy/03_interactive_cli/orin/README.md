# orin/interactive_cli

smolVLA Interactive CLI — orin 노드 (추론 책임)

## 개요

<!-- 정정 (2026-05-02): 06_dgx_absorbs_datacollector 결정으로 3-노드 → 2-노드 (orin / dgx) 전환.
     datacollector 노드 운영 종료. deploy_datacollector.sh → legacy 이관 완료 (L2).
     flow 1 장치 옵션 갱신은 X2 todo 에서 처리 (orin/dgx 2 옵션). -->
본 디렉터리는 2 노드 (orin / dgx) CLI 의 orin 측입니다.
~~3 노드 (orin / dgx / datacollector)~~ → **06 결정으로 datacollector 제거.**
devPC 에서 한 곳 수정 후 deploy_orin, deploy_dgx 2 번으로 동기화하세요.

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

## 노드별 차이점 (2 노드 — 06 결정으로 datacollector 제거)

<!-- 정정 (2026-05-02): datacollector 열 삭제. 역사적 맥락은 아래 주석으로 보존. -->
<!-- datacollector: venv ~/smolvla/datacollector/.hylion_collector, node.yaml node=datacollector,
     flow 0 "이 환경 맞나요?" Y/n, flow 3+ teleop/record/transfer (D2). 운영 종료 2026-05-02. -->

| 항목 | orin | dgx |
|---|---|---|
| venv | `~/smolvla/orin/.hylion_arm` | `~/smolvla/dgx/.arm_finetune` |
| cusparseLt 패치 | main.sh 에 포함 | 없음 |
| node.yaml node 값 | `orin` | `dgx` |
| flow 0 확인 단계 | 없음 (VSCode remote-ssh) | 없음 (VSCode remote-ssh) |
| flow 3+ 모듈 | inference.py (O2 구현) | training.py + mode.py (X2 구현 — 학습/수집 분기) |

## deploy 동기화 절차

공통 코드 수정 후 2 노드 동기화 (06 결정 — datacollector 제거):

```bash
bash scripts/deploy_orin.sh
bash scripts/deploy_dgx.sh
# deploy_datacollector.sh → legacy 이관 완료 (2026-05-02)
```

각 deploy 스크립트가 devPC → 해당 노드로 rsync 수행합니다.

## UX — 뒤로가기 (b/back)

갱신 (2026-05-04, TODO-N1):

모든 prompt 분기점에서 `b` 또는 `back` 입력 시 직전 분기점으로 복귀합니다.

| 분기점 | b/back 동작 |
|---|---|
| flow 1 장치 선택 (entry.py) | 종료 (최상위 — 되돌아갈 상위 없음) |
| flow 3 ckpt 선택 (inference.py) | 종료 (최상위) |
| HF Hub repo_id 입력 (inference.py) | ckpt 선택 메뉴로 복귀 |
| 로컬 ckpt 경로 입력 (inference.py) | ckpt 선택 메뉴로 복귀 |
| flow 4 모드 선택 dry-run/live (inference.py) | ckpt 선택으로 복귀 |

**subprocess 실행 중에는 뒤로가기 불가** — Ctrl+C 로만 종료 가능:
- hil_inference.py (flow 4 실행 중)

helper: `flows/_back.py` — `is_back(raw)` 단일 함수 (Category C 회피: flows/ 기존 디렉터리 내 배치)

## 후행 todo

- F3 이후: `flows/env_check.py` — check_hardware.sh 패턴 wrapping
- O1 study: orin flow 3+ 책임 정의
- O2 task: `flows/inference.py` 구현
- O3 prod: 실 Orin 환경 통합 검증
- N1 task: orin interactive_cli 뒤로가기 b/back 패턴 적용 — **완료 (2026-05-04)**.
