# TODO-D4 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

dgx/interactive_cli/ 수집 mode 의 teleop 진입 직전 사용자 사전 점검 단계 추가 (ANOMALIES 07-#3 ORCHESTRATOR_GAP 후속)

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/precheck.py` | A (신규) | teleop_precheck() 함수 — 모터 포트·카메라·캘리브 표시 + 3-way 분기 |
| `dgx/interactive_cli/flows/mode.py` | M | env_check PASS 후, _run_collect_flow 직전 teleop_precheck() 호출 삽입 |
| `dgx/interactive_cli/configs/ports.json` | A (신규) | DGX 모터 포트 캐시 placeholder (orin/config/ports.json 패턴 미러) |
| `dgx/interactive_cli/configs/cameras.json` | A (신규) | DGX 카메라 인덱스 캐시 placeholder (orin/config/cameras.json 패턴 미러) |

---

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 (읽기 전용 레퍼런스만 참조)
- `dgx/lerobot/` 미변경 — 옵션 B 원칙 준수 (lerobot-upstream-check SKILL)
- Coupled File Rule: `dgx/interactive_cli/flows/` 변경이므로 `dgx/lerobot/` Coupled File 미해당
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/utils/constants.py` line 66-75 — 캘리브레이션 저장 위치
    인용: `HF_LEROBOT_CALIBRATION = Path(os.getenv("HF_LEROBOT_CALIBRATION", default_calibration_path)).expanduser()`
    → 기본값 `~/.cache/huggingface/lerobot/calibration/`
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` — find_port() 패턴
    인용: 사용자에게 USB 케이블 제거/재연결 요청 → 포트 차이 감지 (대화형)
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_cameras.py` — argparse `camera_type` 인자
    인용: `parser.add_argument("camera_type", nargs="?", choices=["realsense", "opencv"])` → `lerobot-find-cameras opencv`
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_calibrate.py` — CalibrateConfig 시그니처
    인용: `--robot.type=so101_follower`, `--teleop.type=so101_leader` (run_teleoperate.sh 패턴과 정합)
- 저장 파일 패턴: `orin/config/ports.json` · `cameras.json` 미러 (15_orin_config_policy.md §2)
- mode.py 기존 패턴 따라 지연 import (함수 내부 `from flows.precheck import ...`)

---

## Step 1 — 저장 위치 grep + 확인 결과

### 모터 포트 파일

**기존 상태 확인**:
- `orin/config/ports.json`: 존재 (placeholder `{"follower_port": null, "leader_port": null}`)
- `dgx/interactive_cli/configs/ports.json`: 기존 미존재 → 본 todo 에서 신규 생성
- `dgx/scripts/run_teleoperate.sh`: `FOLLOWER_PORT="/dev/ttyACM1"`, `LEADER_PORT="/dev/ttyACM0"` 하드코드 (JSON 파일 미참조)

**결정**: `dgx/interactive_cli/configs/ports.json` 신규 생성 (placeholder null). orin/config 패턴 미러. 시연장 셋업 후 precheck 옵션 (1) 선택 시 갱신.

### 카메라 인덱스 파일

**기존 상태 확인**:
- `orin/config/cameras.json`: 존재 (형식: `{"top": {"index": null, "flip": false}, "wrist": {"index": null, "flip": false}}`)
- `dgx/interactive_cli/configs/cameras.json`: 기존 미존재 → 본 todo 에서 신규 생성
- `dgx/interactive_cli/flows/record.py`: `cam_wrist_left_index` · `cam_overview_index` 명칭 사용 (hil_inference.py 의 top/wrist 와 상이)

**결정**: `dgx/interactive_cli/configs/cameras.json` 신규 생성. 형식은 record.py 명칭 기반:
```json
{
  "wrist_left": {"index": null},
  "overview": {"index": null}
}
```
(orin의 flip 필드는 dgx 수집 시 기본 미사용 — 단순화)

### 캘리브레이션 저장 위치

**lerobot upstream 직접 인용** (`docs/reference/lerobot/src/lerobot/utils/constants.py` line 66-75):

```python
from huggingface_hub.constants import HF_HOME

default_cache_path = Path(HF_HOME) / "lerobot"
HF_LEROBOT_HOME = Path(os.getenv("HF_LEROBOT_HOME", default_cache_path)).expanduser()
default_calibration_path = HF_LEROBOT_HOME / "calibration"
HF_LEROBOT_CALIBRATION = Path(os.getenv("HF_LEROBOT_CALIBRATION", default_calibration_path)).expanduser()
```

**기본 경로**: `~/.cache/huggingface/lerobot/calibration/`

**환경변수 우선순위** (`precheck.py:_get_calib_dir()`):
1. `HF_LEROBOT_CALIBRATION` (직접 override)
2. `HF_LEROBOT_HOME`/calibration
3. `HF_HOME`/lerobot/calibration (기본값)

**import smoke 검증**:
```
$ python3 -c "from flows.precheck import _get_calib_dir; print(_get_calib_dir())"
/home/babogaeguri/.cache/huggingface/lerobot/calibration
```
→ 정상 (lerobot upstream 상수 로직 완전 미러)

---

## Step 2 — 신규 사전 점검 helper (precheck.py)

**파일 위치**: `dgx/interactive_cli/flows/precheck.py`

**핵심 함수**: `teleop_precheck(script_dir: Path) -> str`

**반환값 3종**:
- `"proceed"` — 기존 설정 또는 재발견 완료 후 teleop 진행
- `"cancel"` — 취소 (수집 mode 정상 종료)

**내부 함수**:
- `_get_configs_dir(script_dir)`: `script_dir / "configs"` → `dgx/interactive_cli/configs/`
- `_load_json_or_default(path, default)`: JSON 로드 실패 시 default 반환 (크래시 방지)
- `_save_json(path, data)`: configs 저장 + 경로 자동 생성
- `_get_calib_dir()`: 환경변수 우선, 기본값 `~/.cache/huggingface/lerobot/calibration`
- `_format_ports(ports)`: 표시용 문자열 (`(미설정)` 또는 `follower=... leader=...`)
- `_format_cameras(cameras)`: 표시용 문자열
- `_run_find_port(configs_dir)`: `lerobot-find-port` × 2회 subprocess (대화형) + 사용자 포트 입력 → ports.json 저장
- `_run_find_cameras(configs_dir)`: `lerobot-find-cameras opencv` subprocess + 사용자 인덱스 입력 → cameras.json 저장
- `_run_calibrate()`: `lerobot-calibrate --robot.type=so101_follower` + `--teleop.type=so101_leader` (run_teleoperate.sh 패턴 동일)

**표시 UI**:
```
============================================================
 teleop 사전 점검
============================================================

  모터 포트     : follower=/dev/ttyACM1  leader=/dev/ttyACM0
  카메라 인덱스 : wrist_left=0  overview=1
  캘리브 위치   : /home/user/.cache/huggingface/lerobot/calibration (존재)

  ※ 캘리브레이션 값은 웬만하면 변하지 않음.
    같은 SO-ARM 으로 이어서 작업 시 재사용 가능.

어떻게 진행할까요?

  (1) 새 학습 데이터 수집 시작 — 포트·카메라 다시 발견 추천
       lerobot-find-port (2회) + lerobot-find-cameras 자동 재실행
       캘리브레이션 재실행 여부는 별도 확인
  (2) 기존 설정 그대로 진행 (캘리브 재사용)
  (3) 취소

번호 선택 [1~3]:
```

---

## Step 3 — mode.py 분기 호출 삽입

**삽입 위치**: `flow3_mode_entry()` 수집 분기 — env_check PASS 직후, `_run_collect_flow()` 직전

**패치 내용** (mode.py line 229~238 삽입):

```python
# teleop 진입 직전 사전 점검 (TODO-D4 신규 단계)
# 저장된 모터 포트·카메라 인덱스·캘리브 위치 표시 + 분기:
#   "proceed" → teleop 진행
#   "cancel"  → 수집 mode 종료
from flows.precheck import teleop_precheck as _teleop_precheck
precheck_result = _teleop_precheck(script_dir)
if precheck_result == "cancel":
    print()
    print("[mode] 사전 점검에서 취소를 선택했습니다. 수집 mode 를 종료합니다.")
    return 0
```

**분기 결과**:
- `"proceed"` → `_run_collect_flow(script_dir)` 진행 (기존 흐름)
- `"cancel"` → `return 0` (수집 mode 정상 종료)

**흐름 순서 (갱신 후)**:
```
[수집 mode] entry → flow1(장치) → flow2(env_check, mode="collect")
  → teleop_precheck() [신규, D4]
  → _run_collect_flow() → teleop → data_kind → record → transfer
  → _prompt_transition_to_train()
```

---

## Step 4 — orin/interactive_cli 동일 처리 여부

Orin 은 추론 전용 노드 — teleop 없음. 본 todo 의 teleop_precheck 패턴은 dgx 수집 흐름에만 해당.

orin 측에 유사한 사전 점검 (ckpt 경로 확인 등) 이 필요한 경우는 별도 TODO (08_leftarmVLA 이후 검토) 로 분리. 본 사이클 BACKLOG 후보로 보고.

---

## Step 5 — 정적 검증 결과

### py_compile

| 파일 | 결과 |
|---|---|
| `dgx/interactive_cli/flows/precheck.py` | OK |
| `dgx/interactive_cli/flows/mode.py` | OK |
| `dgx/interactive_cli/flows/*.py` (전체 9파일) | ALL OK |

### ruff check

| 대상 | 결과 |
|---|---|
| `flows/precheck.py` + `flows/mode.py` | All checks passed! |
| `flows/*.py` (전체 9파일) | All checks passed! |

### bash -n

| 파일 | 결과 |
|---|---|
| `dgx/interactive_cli/main.sh` | OK |

### import smoke

```bash
python3 -c "
import sys
sys.path.insert(0, 'dgx/interactive_cli')
from flows import mode; print('mode OK')
from flows import precheck; print('precheck OK')
from flows.precheck import teleop_precheck, _get_calib_dir
calib = _get_calib_dir()
print(f'calib_dir: {calib}')
"
```

결과:
```
mode OK
precheck OK
calib_dir: /home/babogaeguri/.cache/huggingface/lerobot/calibration
```

→ lerobot upstream `HF_LEROBOT_HOME / "calibration"` 기본값 정상 반환.

### DGX SSH walkthrough

DGX SSH 가용 시 prod-test-runner 가 실행할 명령 시퀀스:

```bash
# py_compile 전체 (9파일)
ssh dgx "cd ~/smolvla && python3 -m py_compile dgx/interactive_cli/flows/*.py && echo ALL_OK"

# ruff (9파일)
ssh dgx "cd ~/smolvla && python3 -m ruff check dgx/interactive_cli/flows/*.py"

# main.sh bash -n
ssh dgx "bash -n ~/smolvla/dgx/interactive_cli/main.sh"

# import smoke (precheck + calib_dir)
ssh dgx "cd ~/smolvla && python3 -c \"
import sys
sys.path.insert(0, 'dgx/interactive_cli')
from flows import precheck
from flows.precheck import _get_calib_dir, teleop_precheck
print('import OK')
print('calib_dir:', _get_calib_dir())
\""

# configs 파일 존재 확인
ssh dgx "cat ~/smolvla/dgx/interactive_cli/configs/ports.json && cat ~/smolvla/dgx/interactive_cli/configs/cameras.json"

# 비대화형 menu walkthrough (수집 mode → precheck → 옵션 2=기존진행 → 이후 단계 도달 확인)
# echo '1\n2' : 수집 mode 선택(1) → precheck 옵션 2(기존진행)
# env_check SO-ARM 미연결 시 FAIL 후 종료 — precheck 표시까지 도달 X (정상)
# (시연장 SO-ARM 직결 환경에서만 precheck 표시 도달 가능)
# → 정적 검증으로 대체
```

**비대화형 walkthrough 제한**: env_check(mode="collect") 가 SO-ARM 미연결 시 FAIL 반환 → precheck 단계에 도달하지 않음 (정상 동작). DGX SSH 환경에서 precheck UI 도달 검증은 SO-ARM 직결 환경 (PHYS_REQUIRED) 필요.

---

## lerobot 레퍼런스 인용 요약

| 레퍼런스 | 인용 내용 |
|---|---|
| `constants.py` line 74-75 | `HF_LEROBOT_CALIBRATION = Path(os.getenv("HF_LEROBOT_CALIBRATION", default_calibration_path)).expanduser()` |
| `lerobot_find_port.py` | `find_port()` 대화형 패턴 (USB 분리/재연결) — subprocess 호출로 래핑 |
| `lerobot_find_cameras.py` | `main()` argparse `camera_type=None|"opencv"|"realsense"` → `lerobot-find-cameras opencv` |
| `lerobot_calibrate.py` | `CalibrateConfig`: `--robot.type=so101_follower`, `--teleop.type=so101_leader` |
| `run_teleoperate.sh` | `FOLLOWER_ID/LEADER_ID` 기본값 (`my_awesome_follower_arm/my_awesome_leader_arm`) |

---

## DOD 항목 체크

| DOD 항목 | 상태 |
|---|---|
| mode.py + precheck.py py_compile PASS | 완료 |
| ruff PASS | 완료 |
| main.sh bash -n PASS | 완료 |
| 흐름: 수집 mode → env_check → precheck(신규) → _run_collect_flow 순서 | 완료 |
| 표시 정보 (모터 포트·카메라 인덱스·캘리브 위치) 실 저장 위치 인용 | 완료 (grep + lerobot upstream 직접 Read) |
| 메뉴 분기 3개 (1·2·3) 코드 정합 | 완료 |
| 옵션 (1) find-port + find-cameras 자동 재실행 + 캘리브 별도 묻기 | 완료 |
| DGX SSH walkthrough smoke (precheck 도달까지): SO-ARM 미연결로 env_check FAIL 단계에서 중단 (정상) | PHYS_REQUIRED — 시연장 이동 시 |

---

## code-tester 입장에서 검증 권장 사항

1. **py_compile + ruff 전체 재실행**:
   ```bash
   python3 -m py_compile dgx/interactive_cli/flows/*.py
   python3 -m ruff check dgx/interactive_cli/flows/*.py
   bash -n dgx/interactive_cli/main.sh
   ```

2. **mode.py 패치 정합**:
   - `flow3_mode_entry()` 수집 분기에서 env_check PASS 후, `_run_collect_flow` 직전 `teleop_precheck()` 호출 존재 확인
   - `precheck_result == "cancel"` 시 `return 0` (정상 종료)
   - `"proceed"` 시 `_run_collect_flow()` 진행

3. **precheck.py 구조 확인**:
   - `_get_calib_dir()` 환경변수 우선 순서 (HF_LEROBOT_CALIBRATION > HF_LEROBOT_HOME > HF_HOME)
   - `_load_json_or_default()` 파일 미존재 시 크래시 X 보장
   - `_run_find_port()` / `_run_find_cameras()` FileNotFoundError 처리 (lerobot-find-port 미설치 환경 대비)

4. **configs JSON 파일**:
   - `dgx/interactive_cli/configs/ports.json`: `{"follower_port": null, "leader_port": null}` 형식
   - `dgx/interactive_cli/configs/cameras.json`: `{"wrist_left": {"index": null}, "overview": {"index": null}}` 형식

5. **lerobot-reference-usage 준수**:
   - `constants.py` line 74-75 직접 Read 후 `_get_calib_dir()` 구현 — 인용 확인
   - `lerobot-find-cameras opencv` 인자: `lerobot_find_cameras.py` argparse `camera_type` choices 인용 확인

6. **import smoke**:
   ```bash
   python3 -c "
   import sys
   sys.path.insert(0, 'dgx/interactive_cli')
   from flows import mode, precheck
   from flows.precheck import _get_calib_dir
   print(_get_calib_dir())
   "
   ```

7. **DOD 검토**:
   - `env_check PASS → precheck → _run_collect_flow` 순서 흐름 정합: mode.py Read 확인
   - 표시 정보 인용 출처: precheck.py docstring + 본 문서 Step 1·레퍼런스 인용 요약 대조

---

## 잔여 리스크

| 항목 | 수준 | 비고 |
|---|---|---|
| precheck UI walkthrough (SO-ARM 직결 환경) | PHYS_REQUIRED | 시연장 이동 시 verification_queue D4 항목으로 등록 권장 |
| options (1) 캘리브 재실행 후 ports.json 반영 | 기능상 OK | _run_find_port 가 포트 사용자 입력 받아 저장 — 단 lerobot-find-port 가 포트 이름을 stdout 으로 출력할 때 파싱 X (사용자 직접 입력). 추후 stdout 파싱으로 자동화 가능 |
| lerobot-find-cameras 미설치 환경 | FileNotFoundError 처리 완료 | 오류 메시지 + venv 활성화 안내 출력 |
| orin 측 유사 사전 점검 필요 여부 | BACKLOG 후보 | 추론 mode 진입 전 ckpt 경로 확인 단계 — 08 이후 검토 |
