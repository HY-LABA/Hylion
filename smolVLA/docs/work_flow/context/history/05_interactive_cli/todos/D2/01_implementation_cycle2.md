# TODO-D2 — Implementation

> 작성: 2026-05-01 | task-executor | cycle: 2

## 목표

datacollector interactive_cli flow 2~7 구현 — cycle 1 critical 1건 + recommended 3건 수정

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `datacollector/interactive_cli/flows/entry.py` | M | 상대 import 제거 + sys.path 주입 + 절대 import 로 교체 (Critical #1) |
| `datacollector/interactive_cli/flows/record.py` | M | `_validate_camera_indices` 자기비교 제거 + 2-param 유효성 검증으로 교체; `_validate_data_kind_choice` 이중 호출 제거 (Rec 1·2) |
| `datacollector/interactive_cli/flows/env_check.py` | M | flow2_env_check 5단계 순서 D1 §1 정합 재배치 (venv→USB→camera→lerobot→data_dir) (Rec 3) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경, `.claude/` 미변경
- Category B 비해당: `orin/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh` 모두 미변경
- Coupled File Rules: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요
- 레퍼런스 활용: `orin/interactive_cli/flows/entry.py` line 28~31 의 sys.path 주입 패턴 직접 인용

## 변경 내용 요약

### Critical #1 — entry.py 상대 import 수정

`from .env_check import ...` 형태의 상대 import 5줄을 제거하고, orin/entry.py line 28~31 동일 패턴으로 교체.

```python
# 추가된 블록 (entry.py line 22~26 교체)
_THIS_DIR = Path(__file__).parent
_CLI_DIR = _THIS_DIR.parent
if str(_CLI_DIR) not in sys.path:
    sys.path.insert(0, str(_CLI_DIR))

from flows.env_check import flow2_env_check
from flows.teleop import flow3_teleoperate, flow4_confirm_teleop
from flows.data_kind import flow5_select_data_kind
from flows.record import flow6_record
from flows.transfer import flow7_select_transfer
```

`python3 datacollector/interactive_cli/flows/entry.py --help` 실측 결과 usage 정상 출력 확인.

### Rec 1 — `_validate_camera_indices` 자기비교 수정

기존 시그니처 `(cam_wrist_left_index, cam_overview_index, env_check_wrist, env_check_overview)` 에서
`flow6_record` 호출 시 `cam_wrist_left_index, cam_overview_index, cam_wrist_left_index, cam_overview_index`
를 전달 — 동일 값끼리 비교 (항상 True).

수정: 시그니처를 `(cam_wrist_left_index, cam_overview_index)` 2-param 으로 변경.
검증 내용: flow 2 env_check 가 probe 해서 전달한 인덱스의 유효 범위 (0 이상) 확인.
이유: entry.py 가 `env_result.cam_wrist_left_index` 를 그대로 전달하므로 별도 "일치" 비교가 불필요.
대신 OpenCV probe 오류 시 음수 반환 가능성에 대한 방어 검증으로 대체.

`flow6_record` validations 블록도 함께 갱신:
```python
validations = [
    _validate_repo_id(repo_id),
    _validate_num_episodes(num_episodes),
    _validate_camera_indices(cam_wrist_left_index, cam_overview_index),
]
```

### Rec 2 — `_validate_data_kind_choice` 이중 호출 제거

기존 코드: line 314 early-exit + line 335 validations 리스트에 재포함 (2회 호출).
수정: validations 리스트에서 제거. line 314 early-exit 단독 처리로 정리.
`_validate_data_kind_choice` 는 line 317 에서 1회만 호출됨 (AST 검증 완료).

### Rec 3 — env_check.py 5단계 순서 재배치

기존 구현: venv → USB → lerobot → data_dir (4단계 루프) + 카메라 별도 (루프 밖).
D1 §1 스펙 순서: venv(1) → USB(2) → camera(3) → lerobot(4) → data_dir(5).

수정: `flow2_env_check` 를 5단계 인라인 블록으로 재구성. 카메라(Step 3)를 lerobot(Step 4) 이전으로 이동.
각 단계의 `KeyboardInterrupt` / `Exception` 핸들링은 기존과 동일하게 유지.

## code-tester 입장에서 검증 권장 사항

- 단위: `python3 -m py_compile datacollector/interactive_cli/flows/*.py`
- entry.py 직접 실행: `python3 datacollector/interactive_cli/flows/entry.py --help`
- record.py: `_validate_camera_indices` 2-param 시그니처 확인 + `_validate_data_kind_choice` 단일 호출 확인
- env_check.py: 5단계 순서 D1 §1 정합 확인

## cycle 2 피드백 반영

| Critical / Rec | 수정 내용 |
|---|---|
| Critical #1: entry.py 상대 import → ImportError | `_THIS_DIR`/`_CLI_DIR` sys.path 패턴 + 절대 import 로 교체. orin/entry.py line 28~31 동일 패턴 직접 인용 |
| Rec 1: `_validate_camera_indices` 자기 자신 비교 | 시그니처 4→2 param. 유효 범위(0 이상) 방어 검증으로 교체 |
| Rec 2: `_validate_data_kind_choice` 이중 호출 | validations 리스트에서 제거. line 317 단독 호출만 유지 |
| Rec 3: env_check.py 단계 순서 불일치 | 5단계 인라인 블록으로 재구성. camera(3) → lerobot(4) 순서로 D1 §1 정합 |

## self-check 결과

1. `python3 -m py_compile datacollector/interactive_cli/flows/*.py` → ALL OK
2. `python3 datacollector/interactive_cli/flows/entry.py --help` → usage 정상 출력 (ImportError 없음)
3. `_validate_camera_indices` 2-param 시그니처, 음수 인덱스 검증 (자기비교 제거) → AST 검증 확인
4. `_validate_data_kind_choice` line 317 단일 호출 → AST walk 결과 `[317]` 1개만 확인
5. env_check.py 단계 순서 → step line positions `[225, 239, 253, 270, 284]` 오름차순 확인 (D1 §1 정합)

## 회귀 영향

변경 파일 모두 `datacollector/interactive_cli/flows/` 내부. `orin/`, `dgx/`, `docs/reference/` 미변경.
`orin/lerobot/` 미변경 → Coupled File Rules 불필요.
D2 는 datacollector 전용 todo — 다른 노드 회귀 없음.
