"""interactive_cli flow 0·1·2+ — 진입 확인 + 장치 선택 + 노드별 책임 모듈 호출.

flow 0: 환경 확인
  - datacollector 노드: "이 환경에서 실행하시는 게 맞나요? [Y/n]" 확인 단계
  - orin / dgx: 확인 단계 없음 (VSCode remote-ssh 로 이미 올바른 노드에서 실행)

flow 1: 장치 선택 메뉴
  - 본 노드만 active (선택 가능)
  - 다른 노드 선택 시 안내 메시지 + 재선택 (CLI 가 ssh 자동 호출 X)

flow 2+: 노드별 책임 모듈 호출 (O2 에서 orin 분기 구현)
  - orin: env_check.py (flow 2) → inference.py (flow 3·4·5)
  - dgx / datacollector: 후행 todo 에서 구현

설계 기반:
  - node.yaml 로딩: hil_inference.py load_gate_config() line 80~120 패턴 응용
    (경로 처리: Path.is_dir() 분기 + 파일 미존재 시 None 반환)
  - 환경변수 경유 값 처리: check_hardware.sh record_step() line 128~144 패턴 응용
    (특수문자 안전 처리를 위해 환경변수 경유)
"""

import argparse
import sys
from pathlib import Path

# entry.py 는 main.sh 로부터 직접 경로로 실행되므로
# flows/ 패키지 부모 디렉터리(interactive_cli/)를 sys.path 에 추가
_THIS_DIR = Path(__file__).parent
_CLI_DIR = _THIS_DIR.parent
if str(_CLI_DIR) not in sys.path:
    sys.path.insert(0, str(_CLI_DIR))

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
# flow 2+ — 노드별 책임 모듈 디스패치
# ---------------------------------------------------------------------------

def _run_node_flows(node: str, script_dir: Path) -> int:
    """flow 2 이후 노드별 책임 모듈을 순차 호출한다.

    orin 분기 (O2 구현):
      flow 2: env_check.py — check_hardware.sh --mode resume
      flow 3~5: inference.py — ckpt 선택 + hil_inference 실행 + 결과 보고

    dgx / datacollector: 후행 todo 에서 구현.
    """
    if node == "orin":
        from flows.env_check import run_env_check
        from flows.inference import run_inference_flow

        # flow 2: 환경 체크
        if not run_env_check(script_dir):
            print("[ERROR] 환경 체크 실패 — 추론을 시작할 수 없습니다.")
            return 1

        # flow 3·4·5: 추론 (ckpt 선택 → hil_inference 실행 → 결과)
        return run_inference_flow(script_dir)

    else:
        # dgx / datacollector: 후행 todo 에서 구현
        print()
        print(f"[TODO] flow 2+ ({node} 노드 책임) — 후행 todo 에서 구현")
        print("       env_check.py → 노드별 책임 모듈 (training.py / teleop.py 등)")
        return 0


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
    script_dir = Path(__file__).parent
    return _run_node_flows(selected, script_dir)


if __name__ == "__main__":
    sys.exit(main())
