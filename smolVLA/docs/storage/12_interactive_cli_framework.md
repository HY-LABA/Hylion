# 12_interactive_cli_framework.md

> 작성: 2026-05-01 | task-executor | TODO-F1 study cycle 1
> 목적: 3 노드 (orin / dgx / datacollector) 공통 boilerplate 코드 정의.
>       F2 task 가 이 문서의 §2·§3·§4 코드를 각 노드에 그대로 복사한다.

---

## §1 디렉터리 구조 (3 노드 형제 동일 — 결정됨)

spec 라인 89~118 에서 확정. 각 노드 루트 하위에 동일 이름 폴더 신설.
공통 모듈 디렉터리 없음 — 각 노드 자체 완결 (devPC 한 곳 수정 후 deploy 3 번 동기화).

```
orin/interactive_cli/
├── README.md
├── main.sh                  # bash 진입점 (venv activate + python 호출)
├── flows/
│   ├── __init__.py
│   ├── entry.py             # flow 0 (진입·확인) + flow 1 (장치 선택)  ← F1 boilerplate
│   ├── env_check.py         # flow 2 (check_hardware 호출)             ← F2 이후
│   └── inference.py         # flow 3+ (추론 책임)                       ← O2 구현
└── configs/
    └── node.yaml            # 노드 식별자 + venv 경로                    ← F2 작성

dgx/interactive_cli/
├── main.sh
├── flows/
│   ├── __init__.py
│   ├── entry.py             # (동일 복사)
│   ├── env_check.py
│   └── training.py          # flow 3+ (학습 책임)                       ← X2 구현
└── configs/
    └── node.yaml

datacollector/interactive_cli/
├── main.sh
├── flows/
│   ├── __init__.py
│   ├── entry.py             # (동일 복사)
│   ├── env_check.py
│   ├── teleop.py
│   ├── data_kind.py
│   ├── record.py
│   └── transfer.py
└── configs/
    └── node.yaml
```

F1 boilerplate 범위: `main.sh` + `flows/__init__.py` + `flows/entry.py`.
나머지 flow 모듈 (`env_check.py`, `inference.py`, `training.py`, `teleop.py`, `data_kind.py`, `record.py`, `transfer.py`) 은 후행 todo 에서 작성.

---

## §2 진입점 main.sh 패턴

### 설계 근거

`orin/tests/check_hardware.sh` (TODO-G1) 를 직접 Read 하여 다음 패턴 인용:

1. **경로 상수 블록** (check_hardware.sh line 41~49 패턴):
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   VENV_ACTIVATE="${HOME}/smolvla/orin/.hylion_arm/bin/activate"
   ```
2. **venv source + cusparseLt LD_LIBRARY_PATH 패치** (check_hardware.sh line 162~168 패턴):
   ```bash
   source "$VENV_ACTIVATE"
   if [[ -d "$CUSPARSELT_PATH" ]]; then
       export LD_LIBRARY_PATH="${CUSPARSELT_PATH}:${LD_LIBRARY_PATH:-}"
   fi
   ```
3. **python3 heredoc 호출** (check_hardware.sh line 185~203, 226~244 패턴):
   - bash 에서 직접 python 인라인 스크립트를 실행할 때 `python3 - <<'PYEOF' ... PYEOF` 형식

main.sh 는 위 패턴을 그대로 가져오되 흐름을 단순화:
- venv activate (orin 전용 cusparseLt 패치 포함)
- python3 으로 `flows/entry.py` 호출 (node.yaml 경로 전달)
- entry.py 의 종료 코드를 그대로 전달

### 노드 식별 메커니즘

`configs/node.yaml` 에 노드 식별자를 선언. main.sh 가 파일 존재를 확인하고 python 에 경로 전달. entry.py 가 YAML 을 읽어 노드 종류 분기.

```yaml
# orin 용 node.yaml
node: orin
venv: ~/smolvla/orin/.hylion_arm
```

```yaml
# dgx 용 node.yaml
node: dgx
venv: ~/smolvla/dgx/.arm_finetune
```

```yaml
# datacollector 용 node.yaml
node: datacollector
venv: ~/smolvla/datacollector/.hylion_collector
```

main.sh 는 venv 경로를 node.yaml 에서 읽지 않고 **하드코드** (각 노드 복사 시 노드별로 다름). node.yaml 은 python 레이어에서 노드 식별 전용.

### main.sh 완성 코드

```bash
#!/usr/bin/env bash
# =============================================================================
# main.sh — interactive_cli 진입점
#
# 사용법:
#   bash <node>/interactive_cli/main.sh
#
# 동작:
#   1. venv activate (노드별 경로 하드코드)
#   2. orin 한정 cusparseLt LD_LIBRARY_PATH 패치
#   3. flows/entry.py 호출 (node.yaml 경로 전달)
#
# 노드별 복사 시 변경 항목:
#   - VENV_ACTIVATE: 노드별 venv 경로
#   - CUSPARSELT_PATH: orin 전용 (dgx·datacollector 는 해당 블록 제거)
#   - NODE_LABEL: 노드 이름 (로그 표시용)
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# 0. 경로 상수
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_CONFIG="${SCRIPT_DIR}/configs/node.yaml"

# ★ 노드별 복사 시 변경:
#   orin:          ~/smolvla/orin/.hylion_arm/bin/activate
#   dgx:           ~/smolvla/dgx/.arm_finetune/bin/activate
#   datacollector: ~/smolvla/datacollector/.hylion_collector/bin/activate
VENV_ACTIVATE="${HOME}/smolvla/orin/.hylion_arm/bin/activate"

# ★ orin 전용 — cusparseLt LD_LIBRARY_PATH 패치
#   dgx·datacollector 복사 시 이 블록 전체 삭제
CUSPARSELT_PATH="${HOME}/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib"

# ---------------------------------------------------------------------------
# 1. venv 활성화
#    check_hardware.sh step_venv() line 152~172 패턴 그대로
# ---------------------------------------------------------------------------
if [[ ! -f "${VENV_ACTIVATE}" ]]; then
    echo "[ERROR] venv not found: ${VENV_ACTIVATE}"
    echo "        setup_env.sh 를 먼저 실행하세요."
    exit 1
fi

# shellcheck source=/dev/null
source "${VENV_ACTIVATE}"

# orin 전용: cusparseLt fallback (check_hardware.sh line 164~168 패턴)
if [[ -d "${CUSPARSELT_PATH}" ]]; then
    export LD_LIBRARY_PATH="${CUSPARSELT_PATH}:${LD_LIBRARY_PATH:-}"
fi

# ---------------------------------------------------------------------------
# 2. node.yaml 존재 확인
# ---------------------------------------------------------------------------
if [[ ! -f "${NODE_CONFIG}" ]]; then
    echo "[ERROR] configs/node.yaml 미존재: ${NODE_CONFIG}"
    echo "        F2 task 가 각 노드 configs/ 에 node.yaml 을 생성합니다."
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. flows/entry.py 호출
# ---------------------------------------------------------------------------
exec python3 "${SCRIPT_DIR}/flows/entry.py" --node-config "${NODE_CONFIG}"
```

---

## §3 flow 0 entry.py — 환경 확인 단계

### 설계 근거

**hil_inference.py `--gate-json` 패턴** (line 80~177) 을 직접 Read 하여 인용:

```python
# hil_inference.py line 80~120: load_gate_config()
def load_gate_config(gate_json_path: str) -> tuple[dict | None, dict | None]:
    p = Path(gate_json_path)
    if p.is_dir():
        config_dir = p
    else:
        config_dir = p.parent
    ports_path = config_dir / "ports.json"
    cameras_path = config_dir / "cameras.json"
    ...
```

```python
# hil_inference.py line 122~177: apply_gate_config()
# CLI 직접 인자가 기본값과 동일한 경우에만 gate 값으로 덮어씀
# → 우선순위: CLI 직접 지정 > gate 파일 > 기본값
```

entry.py 는 이 패턴을 응용하여:
- `node.yaml` 에서 `node` 키를 읽어 노드 종류 분기
- CLI 직접 인자 우선 / 파일 기반 자동 채움 패턴 유지
- `--gate-json` 스타일로 설정 파일 경로를 인자로 받음

**datacollector 확인 단계** (spec line 47~50):
- datacollector 노드만: flow 0 시작 시 "이 환경에서 실행하시는 게 맞나요? [Y/n]" 확인
- 사용자 N 응답 시 올바른 환경 안내 + exit 0 (오류 아님)
- orin·dgx 는 VSCode remote-ssh 자체 연결이므로 이 확인 단계 없음

### flows/__init__.py

```python
# flows/__init__.py
# interactive_cli flows 패키지
```

### flows/entry.py 완성 코드

```python
"""interactive_cli flow 0·1 — 진입 확인 + 장치 선택 메뉴.

flow 0: 환경 확인
  - datacollector 노드: "이 환경에서 실행하시는 게 맞나요? [Y/n]" 확인 단계
  - orin / dgx: 확인 단계 없음 (VSCode remote-ssh 로 이미 올바른 노드에서 실행)

flow 1: 장치 선택 메뉴
  - 본 노드만 active (선택 가능)
  - 다른 노드 선택 시 안내 메시지 + 재선택 (CLI 가 ssh 자동 호출 X)

설계 기반:
  - node.yaml 로딩: hil_inference.py load_gate_config() line 80~120 패턴 응용
    (경로 처리: Path.is_dir() 분기 + 파일 미존재 시 None 반환)
  - 환경변수 경유 값 처리: check_hardware.sh record_step() line 128~144 패턴 응용
    (특수문자 안전 처리를 위해 환경변수 경유)
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # PyYAML 없을 시 단순 파서로 대체
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 노드 종류 상수
# ---------------------------------------------------------------------------
VALID_NODES = ("orin", "dgx", "datacollector")

NODE_DESCRIPTIONS = {
    "orin": "Orin (추론 노드) — 학습된 ckpt 로 hil_inference 실행",
    "dgx": "DGX (학습 노드) — 데이터셋 학습 + 체크포인트 관리",
    "datacollector": "DataCollector (수집 노드) — teleoperation + lerobot-record + 전송",
}

NODE_GUIDE = {
    "orin": "Orin 에서 실행: bash orin/interactive_cli/main.sh",
    "dgx": "DGX 에서 실행: bash dgx/interactive_cli/main.sh",
    "datacollector": "DataCollector 머신 터미널에서: bash datacollector/interactive_cli/main.sh",
}


# ---------------------------------------------------------------------------
# node.yaml 로딩
#   hil_inference.py load_gate_config() (line 80~120) 패턴 응용:
#   - 경로가 디렉터리이면 그 안의 node.yaml 을 찾음
#   - 파일 경로이면 그대로 사용
#   - 파일 미존재 또는 파싱 실패 시 None 반환 (오류 전파 X)
# ---------------------------------------------------------------------------

def _simple_yaml_load(path: Path) -> dict:
    """PyYAML 미설치 환경 대비 단순 key: value 파서."""
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                result[k.strip()] = v.strip()
    return result


def load_node_config(node_config_path: str) -> dict | None:
    """configs/node.yaml 로드.

    Returns:
        {"node": "orin"|"dgx"|"datacollector", "venv": "~/..."} 또는 None.
    """
    p = Path(node_config_path)
    if p.is_dir():
        p = p / "node.yaml"

    if not p.exists():
        print(f"[ERROR] node.yaml 미존재: {p}", file=sys.stderr)
        return None

    try:
        if yaml is not None:
            with open(p) as f:
                data = yaml.safe_load(f)
        else:
            data = _simple_yaml_load(p)
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[ERROR] node.yaml 파싱 실패 ({p}): {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# flow 0 — 환경 확인
# ---------------------------------------------------------------------------

def flow0_confirm_environment(node: str) -> bool:
    """flow 0: 환경 확인 단계.

    datacollector 노드 전용 확인 단계 (spec line 47~50):
      "이 환경(datacollector)에서 실행하시는 게 맞나요? [Y/n]"
      N 응답 → 올바른 환경 안내 + False 반환

    orin / dgx: 확인 단계 없음 → True 즉시 반환.

    Returns:
        True: 계속 진행 / False: 사용자 거부 또는 잘못된 환경
    """
    if node != "datacollector":
        return True

    print()
    print("=" * 60)
    print(" smolVLA Interactive CLI — DataCollector 노드")
    print("=" * 60)
    print()
    print("이 환경(DataCollector)에서 실행하시는 게 맞나요?")
    print(f"  현재 노드: {NODE_DESCRIPTIONS['datacollector']}")
    print()

    try:
        answer = input("[Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer in ("", "y", "yes"):
        return True
    else:
        print()
        print("[안내] 다른 노드를 사용하시려면:")
        for n, guide in NODE_GUIDE.items():
            print(f"  - {guide}")
        print()
        return False


# ---------------------------------------------------------------------------
# flow 1 — 장치 선택 메뉴
# ---------------------------------------------------------------------------

def flow1_select_node(current_node: str) -> str | None:
    """flow 1: 장치 선택 메뉴.

    spec line 51: "본 노드인 datacollector 만 활성, 다른 노드는 안내만"
    — 이 규칙이 모든 노드에 공통 적용: 어느 노드에서 실행하든
      자신의 노드만 active, 나머지는 선택 불가 + 안내.

    Returns:
        선택된 노드 이름 (현재 노드와 동일) 또는 None (종료 선택)
    """
    print()
    print("=" * 60)
    print(" flow 1 — 장치 선택")
    print("=" * 60)
    print()
    print("어떤 노드 작업을 진행하시겠습니까?")
    print()

    options = []
    for i, node in enumerate(VALID_NODES, start=1):
        if node == current_node:
            marker = "[*]"  # active
            label = f"{i}. {marker} {NODE_DESCRIPTIONS[node]}"
        else:
            marker = "[ ]"  # 안내만
            label = f"{i}. {marker} {NODE_DESCRIPTIONS[node]}  (이 노드에서는 선택 불가)"
        options.append((node, node == current_node))
        print(label)

    print(f"{len(VALID_NODES) + 1}. 종료")
    print()
    print(f"본 노드({current_node})만 활성 상태입니다.")
    print("다른 노드를 선택하시려면 해당 노드 머신에서 직접 실행하세요.")
    print()

    while True:
        try:
            raw = input("번호 선택 [1~{}]: ".format(len(VALID_NODES) + 1)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not raw.isdigit():
            print("  숫자를 입력하세요.")
            continue

        choice = int(raw)

        if choice == len(VALID_NODES) + 1:
            print("종료합니다.")
            return None

        if 1 <= choice <= len(VALID_NODES):
            chosen_node = VALID_NODES[choice - 1]
            if chosen_node == current_node:
                print(f"\n[선택] {NODE_DESCRIPTIONS[current_node]}")
                return current_node
            else:
                print()
                print(f"[안내] {chosen_node} 노드는 {NODE_GUIDE[chosen_node]}")
                print("       현재 노드({})에서는 선택할 수 없습니다.".format(current_node))
                print()
                # 재선택 루프 계속
        else:
            print("  유효한 번호를 입력하세요 (1~{}).".format(len(VALID_NODES) + 1))


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="interactive_cli flow 0·1 — 진입 확인 + 장치 선택"
    )
    parser.add_argument(
        "--node-config",
        type=str,
        required=True,
        help="configs/node.yaml 경로 (main.sh 가 전달)",
    )
    args = parser.parse_args()

    # node.yaml 로드 (hil_inference.py load_gate_config 패턴)
    config = load_node_config(args.node_config)
    if config is None:
        print("[ERROR] node.yaml 로드 실패 — F2 task 가 configs/node.yaml 을 생성했는지 확인.")
        return 1

    node = config.get("node", "").strip()
    if node not in VALID_NODES:
        print(f"[ERROR] node.yaml 의 node 값 '{node}' 가 유효하지 않습니다.")
        print(f"        유효 값: {VALID_NODES}")
        return 1

    # flow 0: 환경 확인 (datacollector 전용)
    if not flow0_confirm_environment(node):
        return 0  # 사용자 거부 — 정상 종료 (오류 X)

    # flow 1: 장치 선택
    selected = flow1_select_node(node)
    if selected is None:
        return 0  # 종료 선택 — 정상 종료

    # flow 2+: 각 노드별 책임 모듈 호출
    # (F2 이후 todo 에서 env_check.py + 노드별 모듈 추가)
    print()
    print(f"[TODO] flow 2+ ({selected} 노드 책임) — 후행 todo 에서 구현")
    print("       env_check.py → 노드별 책임 모듈 (inference.py / training.py / teleop.py 등)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## §4 flow 1 장치 선택 메뉴 — 노드별 동작 정리

flow 1 은 `flows/entry.py` 의 `flow1_select_node()` 함수로 구현. 요약:

| 노드 | active 상태 | 선택 결과 |
|---|---|---|
| 현재 노드 (본 머신) | [*] active | 선택 가능 → flow 2+ 진행 |
| 다른 노드 | [ ] 안내만 | 선택 불가 → 안내 메시지 + 재선택 루프 |
| 종료 | — | exit 0 |

재선택 루프 동작 (spec line 178~179 결정 반영):
- "다른 노드에서 직접 실행하세요" 안내 + 다시 메뉴 표시
- CLI 가 SSH 자동 호출 X (사용자가 다른 노드에 직접 접속)

---

## §5 노드별 차이점 — flow 2+ 분기점

본 boilerplate (F1 범위) 이후 각 노드가 이어받는 분기점:

| 노드 | flow 2 | flow 3+ |
|---|---|---|
| **datacollector** | `env_check.py` — datacollector 환경 체크 (04 G3·G4 책임 흡수) | `teleop.py` → `data_kind.py` → `record.py` → `transfer.py` (D1·D2 결정) |
| **orin** | `env_check.py` — check_hardware.sh `--mode resume` 호출 | `inference.py` — ckpt 선택·hil_inference 실행·시연 데모 (O1·O2 결정) |
| **dgx** | `env_check.py` — preflight 체크 (GPU·메모리·디스크) | `training.py` — 데이터셋 선택·학습 trigger·체크포인트 관리 (X1·X2 결정) |

`env_check.py` 의 orin 구현 예시 (후행 F2/O2 참고용):
```python
# orin env_check.py 가 check_hardware.sh 를 subprocess 로 호출하는 패턴
import subprocess, sys
from pathlib import Path

def run_env_check(script_dir: Path) -> bool:
    check_script = script_dir.parent.parent / "tests" / "check_hardware.sh"
    # check_hardware.sh 지원 인자: --mode, --config, --quiet, --output-json (line 68~83)
    # --gate-json 은 hil_inference.py 전용 — check_hardware.sh 에 전달하면 exit 2 로 실패
    # 경로 상수 (PORTS_JSON, CAMERAS_JSON) 는 스크립트 내부에서 자동 결정 (line 41~46)
    result = subprocess.run(
        ["bash", str(check_script), "--mode", "resume"],
        check=False
    )
    return result.returncode == 0
```

---

## 설계 결정 요약

| 항목 | 결정 | 근거 |
|---|---|---|
| main.sh venv activate 순서 | source 후 python 호출 | check_hardware.sh step_venv() line 152~172 패턴 |
| cusparseLt 패치 위치 | main.sh (orin 전용) | check_hardware.sh line 164~168 패턴 (SSH 비대화형 ImportError 해소) |
| node.yaml 로딩 방식 | `Path.is_dir()` 분기 + None 반환 | hil_inference.py load_gate_config() line 92~119 패턴 |
| 인자 우선순위 | CLI 직접 > 파일 > 기본값 | hil_inference.py apply_gate_config() line 122~177 패턴 |
| datacollector 확인 단계 | flow 0 에서 Y/n prompt | spec line 47~50 (datacollector 직접 터미널 확인) |
| 다른 노드 선택 처리 | 안내 + 재선택 (ssh 호출 X) | spec line 178~179 결정 사항 |
| PyYAML 미설치 대비 | `_simple_yaml_load()` 폴백 | datacollector venv 는 lerobot[hardware,feetech] 이 주 — yaml 미포함 가능성 |

---

## SKILL_GAP 보고

본 todo 범위 내 SKILL_GAP 없음.

- `main.sh` 패턴: check_hardware.sh (lerobot-reference-usage 준수, 직접 Read + 인용)
- `entry.py` 패턴: hil_inference.py load_gate_config / apply_gate_config (직접 Read + 인용)
- 신규 자산 (interactive_cli) 은 spec 에서 사용자 명시 확정 후 작성하는 것으로 이미 합의됨 (spec 라인 166~168)

후행 todo 에서 SKILL_GAP 발생 가능 영역:
- `env_check.py` (datacollector 환경 체크): 04 G1 패턴 재구현 — 레퍼런스 있음 (check_hardware.sh)
- `record.py` 의 lerobot-record draccus 인자 동적 생성: D1 study 에서 `lerobot_record.py` 직접 Read 필수
