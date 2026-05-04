# TODO-D1 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`dgx/interactive_cli/` 수집 mode SSH_AUTO 검증 + 도구 정비 (Wave 2 / 게이트 1, 06 V2 흡수)

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/mode.py` | M | 수집 mode 진입 시 env_check(mode="collect") 호출 누락 패치 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (읽기 전용 레퍼런스만 참조)
- `dgx/lerobot/` 미변경 — 옵션 B 원칙 준수
- Coupled File Rule: `dgx/interactive_cli/` 변경 → `dgx/lerobot/` 아님 (Coupled File 미해당)
- 레퍼런스 활용: 06 V2 prod-test 산출물 (`03_prod-test.md`) 직접 Read — 04 BACKLOG #14 사전 진단 결과 재확인
- 패치 근거: `env_check.py` docstring §1-4 ("mode="collect" 시 `_check_hardware_collect()` 호출") + mode.py 자체 주석 line 88-90 (TODO 명시)

---

## Step 1 — flow 0~7 정합 정적 검증 결과

### py_compile (8/8 파일)

| 파일 | 결과 |
|---|---|
| `dgx/interactive_cli/flows/entry.py` | OK |
| `dgx/interactive_cli/flows/env_check.py` | OK |
| `dgx/interactive_cli/flows/mode.py` | OK (패치 후) |
| `dgx/interactive_cli/flows/teleop.py` | OK |
| `dgx/interactive_cli/flows/data_kind.py` | OK |
| `dgx/interactive_cli/flows/record.py` | OK |
| `dgx/interactive_cli/flows/transfer.py` | OK |
| `dgx/interactive_cli/flows/training.py` | OK |

### ruff check (8/8 파일)

결과: `All checks passed!` (패치 전·후 모두)

### bash -n

| 파일 | 결과 |
|---|---|
| `dgx/interactive_cli/main.sh` | OK |

### flow 분기 정합 — 직접 Read 확인

**entry.py → env_check → mode 체인:**
- `entry.py` dgx 분기: `flow2_env_check(script_dir, scenario="smoke")` → `flow3_mode_entry(script_dir)` (line 238-242)
- 수집 mode 진입: `flow3_mode_entry` → `"(1) 수집"` 선택 → (패치 후) `flow2_env_check(script_dir, scenario="smoke", mode="collect")` → `_run_collect_flow(script_dir)`
- 학습 mode 진입: `flow3_mode_entry` → `"(2) 학습"` 선택 → `run_training_flow(script_dir)`

**수집 flow 체인 (_run_collect_flow):**
- `flow3_teleoperate(script_dir)` → `flow4_confirm_teleop(script_dir, rc)` → `flow5_select_data_kind()` → `flow6_record(...)` → `flow7_select_transfer(script_dir, ...)`

**G-4 학습 전환 체인:**
- `_run_collect_flow()` → `(0, dataset_name)` 반환
- `_prompt_transition_to_train(script_dir, dataset_name)` 호출
- Y 선택 시 → `run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)`

**정합 확인: 완전. (mode.py 패치 적용 후)**

---

## Step 2 — flow 0~2 SSH 자율 검증 명령 시퀀스 (prod-test-runner 인계)

아래 시퀀스는 DGX SSH 연결이 가용한 경우 prod-test-runner 가 비대화형으로 실행 가능한 검증 명령입니다.

### 사전 조건 확인

```bash
# DGX venv 존재 확인 (SSH 자율)
ssh dgx "test -f ~/smolvla/dgx/.arm_finetune/bin/activate && echo OK || echo FAIL"

# node.yaml 존재 확인 (SSH 자율)
ssh dgx "test -f ~/smolvla/dgx/interactive_cli/configs/node.yaml && cat ~/smolvla/dgx/interactive_cli/configs/node.yaml"
```

### flow 0 — 환경 확인 (정적 검증)

```bash
# entry.py flow0_confirm_environment 로직 확인 (항상 True 반환 — VSCode remote-ssh 전제)
ssh dgx "python3 -c \"
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / 'smolvla/dgx/interactive_cli'))
from flows.entry import flow0_confirm_environment, VALID_NODES
print('VALID_NODES:', VALID_NODES)
print('flow0 (dgx):', flow0_confirm_environment('dgx'))
print('flow0 (orin):', flow0_confirm_environment('orin'))
\""
```

기대 출력:
```
VALID_NODES: ('orin', 'dgx')
flow0 (dgx): True
flow0 (orin): True
```

### flow 1 — 장치 선택 메뉴 정합 (정적 검증)

```bash
# flow1_select_node 함수 시그니처·VALID_NODES 확인
ssh dgx "python3 -c \"
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / 'smolvla/dgx/interactive_cli'))
from flows.entry import VALID_NODES, NODE_DESCRIPTIONS
print('VALID_NODES:', VALID_NODES)
print('dgx 설명:', NODE_DESCRIPTIONS['dgx'])
print('orin 설명:', NODE_DESCRIPTIONS['orin'])
print('datacollector 없음:', 'datacollector' not in VALID_NODES)
\""
```

기대 출력:
```
VALID_NODES: ('orin', 'dgx')
dgx 설명: DGX (학습·수집 노드) — 데이터 수집 + 학습 + 체크포인트 관리
orin 설명: Orin (추론 노드) — 학습된 ckpt 로 hil_inference 실행
datacollector 없음: True
```

### flow 2 — env_check 7단계 정합 (정적 + 부분 SSH 자율)

```bash
# env_check.py 함수 목록 + preflight_check.sh 존재 확인
ssh dgx "python3 -c \"
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / 'smolvla/dgx/interactive_cli'))
from flows.env_check import flow2_env_check, _check_hardware_collect, run_env_check
print('flow2_env_check OK')
preflight = Path.home() / 'smolvla/dgx/scripts/preflight_check.sh'
print('preflight_check.sh 존재:', preflight.exists())
\""
```

```bash
# env_check mode 파라미터 시그니처 확인
ssh dgx "python3 -c \"
import inspect, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'smolvla/dgx/interactive_cli'))
from flows.env_check import flow2_env_check
sig = inspect.signature(flow2_env_check)
print('flow2_env_check 시그니처:', sig)
\""
```

기대 출력: `flow2_env_check 시그니처: (script_dir: pathlib.Path, scenario: str = 'smoke', mode: str = 'train') -> bool`

```bash
# env_check.py _check_hardware_collect 항목 6~9 fallback 동작 확인
# (SO-ARM 미연결 환경 — FAIL 출력 후 all_pass=False 반환, 크래시 X 보장)
ssh dgx "python3 -c \"
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'smolvla/dgx/interactive_cli'))
from flows.env_check import _check_hardware_collect
result = _check_hardware_collect()
print('결과 (SO-ARM 미연결):', result)
\""
```

기대 출력 (SO-ARM 미연결 환경):
```
  [항목 6] USB 포트 확인
    FAIL  leader  (/dev/ttyACM0) 미발견 — SO-ARM leader 연결 확인
    FAIL  follower (/dev/ttyACM1) 미발견 — SO-ARM follower 연결 확인
  ...
결과 (SO-ARM 미연결): False   ← 크래시 X, False 반환 — fallback 동작 PASS
```

**fallback 동작 보장**: `_check_hardware_collect()`는 SO-ARM 미연결 시 FAIL 안내 출력 + `False` 반환 (exception 미발생). `flow2_env_check(mode="collect")`에서 `hw_passed=False` → `return False` (flow 중단 + 안내 메시지). SO-ARM 없는 환경에서 크래시 X.

---

## Step 3 — flow 3~7 SO-ARM 직결 부분 도구 정합

### py_compile + ruff (위 Step 1 에서 이미 검증 완료)

모든 파일 PASS. 추가 확인 사항:

- `teleop.py`: `_run_teleop_script(script_dir)` — `run_teleoperate.sh` 경로 `script_dir.parent / "scripts" / "run_teleoperate.sh"` (dgx 경로 맞춤)
- `record.py`: `build_record_args()` — `data_root` 경로 `~/smolvla/dgx/data/{dataset_name}` (datacollector → dgx 이식 완료)
- `transfer.py`: H-(b) 2 옵션 메뉴 (`_guide_rsync_to_dgx` 완전 제거 확인) — `grep -n "_guide_rsync"` 결과 0건

### PHYS_REQUIRED 범위 (SO-ARM 직결 필수 — verification_queue D 그룹 마킹 항목)

| 검증 항목 | 환경 레벨 | 마킹 사유 |
|---|---|---|
| flow 3 텔레오퍼레이션 (`run_teleoperate.sh all`) | PHYS_REQUIRED | SO-ARM leader+follower USB 직결 필수 |
| flow 4 텔레오퍼레이션 완료 확인 (재시도 'r' 루프) | PHYS_REQUIRED | SO-ARM 동작 육안 확인 필수 |
| flow 5 학습 종류 선택 (5 옵션) | SSH_AUTO | SO-ARM 불필요 (메뉴 선택만) |
| flow 6 `lerobot-record` (calibrate·record·카메라) | PHYS_REQUIRED | SO-ARM 직결 + 카메라 연결 필수 |
| flow 7 (1) 로컬 저장 안내 | SSH_AUTO | 경로 안내만 |
| flow 7 (2) HF Hub push | SSH_AUTO (인터넷 가용 시) | 실 네트워크 의존 |
| G-4 학습 전환 prompt | SSH_AUTO | UI 분기 확인만 |
| env_check.py 항목 6~9 실물 PASS | PHYS_REQUIRED | SO-ARM + 카메라 USB 직결 필수 |

---

## Step 4 — 04 BACKLOG #14 진단·수정 결과

### 진단

**BACKLOG #14 현상**: `legacy/datacollector/interactive_cli/flows/env_check.py` 의 `_check_motor_ids()` 함수에서 `'NoneType' object has no attribute 'close'` 에러.

**원인 코드** (`legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/env_check.py` line 249~265):
```python
port_handler = PortHandler(port)
...
try:
    if not port_handler.openPort():
        results[label] = (False, f"{port}: 포트 열기 실패")
        continue   # ← finally 없이 continue — port_handler.closePort() 미호출
    ...
finally:
    port_handler.closePort()  # ← openPort() 전 None 가능성 X, but continue 분기에서 해당 블록 도달 X
```

실제로 문제가 발생한 분기: `openPort()` 실패 시 `continue`로 try 블록 탈출 → `finally`는 항상 실행 → `port_handler`는 None이 아니지만 `openPort()` 실패 상태에서 `closePort()` 호출 시 내부 `None` 상태 변수로 `AttributeError` 가능.

**DGX env_check.py 적용 여부**: `dgx/interactive_cli/flows/env_check.py` 는 `port_handler`·`closePort()`·`openPort()` 패턴 완전 미사용. 항목 9 (SO-ARM 포트 응답)은 `serial.Serial` context manager 패턴 사용:

```python
# dgx/interactive_cli/flows/env_check.py 항목 9 (line 134~143)
with serial.Serial(follower_port, timeout=0.5):
    pass
```

`with` 블록이 `__exit__` 보장 → `closePort()` 패턴 원천 차단. BACKLOG #14 패턴 재현 불가.

### 수정 결과

**DGX env_check.py 패치 불필요**: 구조적으로 다른 구현 (`serial.Serial` context manager).

**Legacy env_check.py 패치 대상 여부**: `docs/storage/legacy/` 하위 보관용 파일 — 운영 코드 아님. 패치 불필요 (datacollector 노드 운영 종료, 06 결정 C·F).

**BACKLOG #14 처리 결론**: DGX env_check.py 에서 재현 불가 확인 (정적 분석). 실물 확인은 verification_queue D 그룹 항목 포함.

---

## flow 분기 패치 (mode.py)

### 패치 배경

`env_check.py`에 `mode="collect"` 파라미터 (항목 6~9: USB·dialout·v4l2·SO-ARM 포트 응답)가 이미 구현되어 있으나, `mode.py` 수집 mode 분기에서 이를 호출하지 않는 미구현 상태였음.

`mode.py` 원본 주석 (line 88-90):
> "env_check 에서 수집 mode 시 카메라 인덱스 체크를 수행했어야 하나, 현재 구현에서는 기본값 (wrist_left=0, overview=1) 사용. V2 prod 검증에서 실제 인덱스 확인 후 수정 예정."

### 패치 내용 (mode.py line 211~220, 삽입)

```python
# 패치 전 (원본):
        if raw == "1":
            # 수집 mode
            print()
            print("[mode] 데이터 수집 mode 진입합니다.")
            print()

            rc, dataset_name = _run_collect_flow(script_dir)

# 패치 후:
        if raw == "1":
            # 수집 mode
            print()
            print("[mode] 데이터 수집 mode 진입합니다.")
            print()

            # env_check.py 수집 환경 체크 (항목 6~9: USB·dialout·v4l2·SO-ARM 포트 응답)
            # entry.py 에서는 scenario="smoke" 로 preflight 만 실행 (학습 mode 공통 사전 점검).
            # 수집 mode 에서는 SO-ARM·카메라 하드웨어 체크 추가 (env_check.py mode="collect").
            # 결정 (TODO-X2 §7, env_check.py docstring): selective check — 수집 mode 에서만 항목 6~9 실행.
            # FAIL 시 사용자 안내 후 종료 (실 SO-ARM 없는 환경 보호).
            from flows.env_check import flow2_env_check as _flow2_env_check_collect
            if not _flow2_env_check_collect(script_dir, scenario="smoke", mode="collect"):
                print()
                print("[mode] 수집 환경 체크 FAIL — SO-ARM·카메라 연결 후 재시작하세요.")
                return 1

            rc, dataset_name = _run_collect_flow(script_dir)
```

### 패치 후 검증

- `python3 -m py_compile dgx/interactive_cli/flows/mode.py`: OK
- `ruff check dgx/interactive_cli/flows/mode.py`: All checks passed!
- 전체 8파일 재검증: all OK

---

## PHYS_REQUIRED verification_queue D 그룹 마킹 항목

아래 항목은 verification_queue.md 의 D 그룹에 추가 필요:

```
[D-1] flow 2 env_check 항목 6~9 실물 PASS
  - 환경: PHYS_REQUIRED (SO-ARM + 카메라 USB 직결)
  - 확인 사항: /dev/ttyACM0 (leader), /dev/ttyACM1 (follower) 인식, dialout 그룹, /dev/video* 인식, serial.Serial open PASS
  - 시연장 이동 시

[D-2] flow 3 텔레오퍼레이션 (run_teleoperate.sh all)
  - 환경: PHYS_REQUIRED (SO-ARM leader+follower 직결)
  - 시연장 이동 시

[D-3] flow 6 lerobot-record (dummy 1~3 에피소드)
  - 환경: PHYS_REQUIRED (SO-ARM + 카메라 2대 직결)
  - 확인: cam_wrist_left=0, cam_overview=1 실제 인덱스 정합
  - 시연장 이동 시

[D-4] 04 BACKLOG #14 실물 확인
  - 환경: PHYS_REQUIRED (SO-ARM 직결)
  - 확인: env_check.py 항목 9 (SO-ARM 포트 응답) 실행 시 serial.Serial context manager 패턴으로 NoneType 에러 발생 X
  - 시연장 이동 시
```

---

## SSH_AUTO 검증 범위 (prod-test-runner 자율 처리 가능)

| 항목 | 명령 | 기대 결과 |
|---|---|---|
| py_compile 8파일 | `ssh dgx "cd ~/smolvla && python3 -m py_compile dgx/interactive_cli/flows/*.py"` | exit 0 |
| ruff check 8파일 | `ssh dgx "cd ~/smolvla && python3 -m ruff check dgx/interactive_cli/flows/*.py"` | All checks passed |
| main.sh bash -n | `ssh dgx "bash -n ~/smolvla/dgx/interactive_cli/main.sh"` | exit 0 |
| VALID_NODES 확인 | Step 2 flow 0~1 명령 | ('orin', 'dgx') |
| env_check 시그니처 | Step 2 flow 2 명령 | 위 시그니처 출력 |
| env_check fallback | `_check_hardware_collect()` — SO-ARM 미연결 | False 반환, 크래시 X |
| flow2 mode 파라미터 체인 | mode.py 패치 확인 (직접 Read) | collect 분기 env_check 호출 존재 |

---

## code-tester 인계 사항

### 검증 권장 사항

1. **py_compile + ruff 전체 재실행**:
   ```bash
   python3 -m py_compile dgx/interactive_cli/flows/*.py
   ruff check dgx/interactive_cli/flows/*.py
   bash -n dgx/interactive_cli/main.sh
   ```

2. **mode.py 패치 정합**:
   - `flow3_mode_entry()` 수집 분기에 `flow2_env_check(mode="collect")` 호출 추가 확인
   - 반환값 체인: `if not _flow2_env_check_collect(...)` → `return 1` (FAIL 시 종료)
   - `mode.py` 에서 `env_check.py` import: `from flows.env_check import flow2_env_check as _flow2_env_check_collect`

3. **BACKLOG #14 정적 분석 결과 재확인**:
   - `dgx/interactive_cli/flows/env_check.py` 에서 `port_handler` grep 결과 0건 확인
   - 항목 9 패턴: `with serial.Serial(follower_port, timeout=0.5): pass`

4. **flow 분기 import 체인 전수 확인**:
   - `mode.py` → `teleop.py`, `data_kind.py`, `record.py`, `transfer.py`, `training.py` 지연 import 모두 존재
   - `training.py` → `run_training_flow_with_dataset(script_dir, dataset_name)` 시그니처 확인

5. **DOD 항목 체크**:
   - flow 0~7 py_compile PASS: 완료
   - flow 분기 정합 (entry→env_check→mode→collect/train): 완료 (패치 포함)
   - flow 0~2 SSH 자율 검증 명령 시퀀스 작성: 완료 (본 문서 Step 2)
   - 04 BACKLOG #14 None-safe 진단: 완료 (DGX env_check.py 에서 패턴 미사용 확인)
   - PHYS_REQUIRED 마킹 항목 명시: 완료 (본 문서 Step 3·D 그룹)
