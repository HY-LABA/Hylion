# TODO-F2 — Implementation

> 작성: 2026-05-01 | task-executor | cycle: 1

## 목표

F1 산출물 (main.sh + flows/entry.py) 을 3 노드에 동일 복사하고, 각 노드의 configs/node.yaml 에 환경 설정 분리.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/interactive_cli/main.sh` | 신규 | orin 전용 main.sh (cusparseLt 패치 포함) |
| `orin/interactive_cli/flows/__init__.py` | 신규 | flows 패키지 init |
| `orin/interactive_cli/flows/entry.py` | 신규 | F1 §3 코드 그대로 복사 (flow 0·1) |
| `orin/interactive_cli/configs/node.yaml` | 신규 | node: orin, venv 경로 명시 |
| `orin/interactive_cli/README.md` | 신규 | 3 노드 동기화 안내 + 호출법 |
| `dgx/interactive_cli/main.sh` | 신규 | dgx 전용 main.sh (cusparseLt 블록 없음) |
| `dgx/interactive_cli/flows/__init__.py` | 신규 | flows 패키지 init |
| `dgx/interactive_cli/flows/entry.py` | 신규 | F1 §3 코드 그대로 복사 (flow 0·1) |
| `dgx/interactive_cli/configs/node.yaml` | 신규 | node: dgx, venv 경로 명시 |
| `dgx/interactive_cli/README.md` | 신규 | 3 노드 동기화 안내 + 호출법 |
| `datacollector/interactive_cli/main.sh` | 신규 | datacollector 전용 main.sh (cusparseLt 블록 없음) |
| `datacollector/interactive_cli/flows/__init__.py` | 신규 | flows 패키지 init |
| `datacollector/interactive_cli/flows/entry.py` | 신규 | F1 §3 코드 그대로 복사 (flow 0·1) |
| `datacollector/interactive_cli/configs/node.yaml` | 신규 | node: datacollector, venv 경로 명시 |
| `datacollector/interactive_cli/README.md` | 신규 | 3 노드 동기화 안내 + 호출법 + D2 후행 todo |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. Category A 위반 없음.
- Coupled File Rule: `orin/lerobot/` 미변경 — 03_orin_lerobot_diff.md 갱신 불필요.
- `pyproject.toml` 미변경 — 02_orin_pyproject_diff.md 갱신 불필요.
- Category C (신규 디렉터리): spec 본문 라인 89~118 에서 사용자 합의 완료 — 자율 진행.
- lerobot-reference-usage: F1 산출물 (`docs/storage/12_interactive_cli_framework.md`) 이 이미 check_hardware.sh + hil_inference.py 를 직접 Read·인용 완료. F2 는 F1 §2·§3 코드 복사이므로 추가 레퍼런스 불필요.
- cusparseLt 라인 정정: `orin/tests/check_hardware.sh` 직접 Read 완료.
  - F1 §2 주석 인용 `line 162~168` → 실제 코드는 comment(line 164~165) + if 블록(line 166~168). 본 F2 main.sh 에서는 정확한 라인 표기로 교정: `step_venv() line 156~162` (source 블록) / `line 164~168` (cusparseLt if 블록).

## 3 노드 디렉터리 트리

```
orin/interactive_cli/
├── README.md
├── main.sh
├── flows/
│   ├── __init__.py
│   └── entry.py
└── configs/
    └── node.yaml

dgx/interactive_cli/
├── README.md
├── main.sh
├── flows/
│   ├── __init__.py
│   └── entry.py
└── configs/
    └── node.yaml

datacollector/interactive_cli/
├── README.md
├── main.sh
├── flows/
│   ├── __init__.py
│   └── entry.py
└── configs/
    └── node.yaml
```

## 노드별 차이점 표

| 항목 | orin | dgx | datacollector |
|---|---|---|---|
| `VENV_ACTIVATE` | `~/smolvla/orin/.hylion_arm/bin/activate` | `~/smolvla/dgx/.arm_finetune/bin/activate` | `~/smolvla/datacollector/.hylion_collector/bin/activate` |
| cusparseLt 블록 | 포함 (check_hardware.sh line 164~168 패턴) | 없음 | 없음 |
| `node.yaml` node 값 | `orin` | `dgx` | `datacollector` |
| `node.yaml` venv 값 | `~/smolvla/orin/.hylion_arm` | `~/smolvla/dgx/.arm_finetune` | `~/smolvla/datacollector/.hylion_collector` |
| flow 0 동작 | True 즉시 반환 (VSCode remote-ssh) | True 즉시 반환 (VSCode remote-ssh) | "이 환경 맞나요?" Y/n prompt |
| flow 1 active 노드 | orin | dgx | datacollector |
| 후행 flow 모듈 | inference.py (O2) | training.py (X2) | teleop/data_kind/record/transfer (D2) |

## F1 Recommended 사항 처리 결과

| F1 Recommended | 처리 |
|---|---|
| §5 `run_env_check()` 예시의 `--gate-json` 인자 — `check_hardware.sh` 미지원, 런타임 오류 가능 | F2 생성 파일 (main.sh, entry.py) 에 §5 코드 불포함. §2·§3 boilerplate 만 복사. `--gate-json` 패턴은 후행 todo (O2 env_check.py) 에서 별도 처리 |
| §2 cusparseLt 라인 인용 불일치 (`line 162~168` vs `line 164~168`) | `orin/tests/check_hardware.sh` 직접 Read 완료. 실제 cusparseLt if 블록은 line 164~168. main.sh 주석에 `line 164~168` 로 정확히 표기. F1 §2 문서 자체 정정은 별도 트랙 |

## 변경 내용 요약

F1 study 에서 정의한 boilerplate (`main.sh` + `flows/__init__.py` + `flows/entry.py`) 를 3 노드 디렉터리에 생성했다. 각 노드는 venv 경로와 cusparseLt 패치 유무만 다르며, python 레이어 (entry.py) 는 완전 동일 복사다.

`configs/node.yaml` 은 노드 식별자 (`node: orin/dgx/datacollector`) 와 venv 참조 경로를 담는다. bash 레이어 (main.sh) 는 venv 경로를 하드코드로 가지며 node.yaml 의 venv 는 python 레이어 참조 전용이다 (F1 §2 설계 결정 그대로). entry.py 가 node.yaml 의 `node` 값을 읽어 flow 0 (datacollector 전용 확인 단계) 과 flow 1 (본 노드만 active) 을 분기한다.

cusparseLt 패치는 check_hardware.sh step_venv() 와 동일하게 orin main.sh 에만 포함했다. dgx/datacollector 는 불필요하므로 해당 블록을 제거했다.

## code-tester 입장에서 검증 권장 사항

- bash 구문: `bash -n orin/interactive_cli/main.sh` (이미 통과 확인)
- bash 구문: `bash -n dgx/interactive_cli/main.sh` (이미 통과 확인)
- bash 구문: `bash -n datacollector/interactive_cli/main.sh` (이미 통과 확인)
- python 구문: `python3 -m py_compile orin/interactive_cli/flows/entry.py` (이미 통과 확인)
- python 구문: `python3 -m py_compile dgx/interactive_cli/flows/entry.py` (이미 통과 확인)
- python 구문: `python3 -m py_compile datacollector/interactive_cli/flows/entry.py` (이미 통과 확인)
- entry.py 단독 실행 (node.yaml --node-config 인자):
  ```bash
  # orin 기준 (devPC 에서 테스트 — 실 venv 없어도 python3 직접 호출 가능)
  python3 orin/interactive_cli/flows/entry.py --node-config orin/interactive_cli/configs/node.yaml
  ```
- 3 노드 node.yaml 값 일치 확인: `node` 키가 각 노드 이름과 일치하는지
- entry.py 3 파일 동일성 확인: `diff orin/interactive_cli/flows/entry.py dgx/interactive_cli/flows/entry.py`
- DOD 충족 확인:
  - F1 산출물 3 노드 복사: main.sh + flows/entry.py + flows/__init__.py
  - configs/node.yaml 노드별 환경 설정 분리: node 식별자 + venv 경로
  - main.sh 가 node.yaml 존재 확인 후 entry.py 에 --node-config 전달 (node.yaml 기반 분기)

## 잔여 리스크

- `__pycache__` 생성: devPC python3 구문 검사 과정에서 `__pycache__` 가 생성됨. 배포 전 `.gitignore` 또는 rsync `--exclude` 로 제외 필요 (기존 `.gitignore` 에 `__pycache__/` 항목 이미 포함 여부 확인 권장).
- entry.py 3 사본 동기화: 공통 코드를 3 사본으로 관리하므로, 한 곳 수정 시 나머지 2 곳 수동 갱신 또는 deploy 3 번 필수. README 에 명기함.
- flow 2+ 미구현: 현재 `[TODO] flow 2+ 후행 todo` 메시지만 출력. 실 기능은 D2/O2/X2 이후 todo 에서 구현.

## SKILL_GAP

없음. F1 산출물 복사 및 check_hardware.sh 직접 Read 로 충족.
