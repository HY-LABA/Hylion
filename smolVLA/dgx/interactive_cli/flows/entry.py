"""interactive_cli flow 0·1 — 진입 확인 + 장치 선택 메뉴.

flow 0: 환경 확인
  - orin / dgx: 확인 단계 없음 (VSCode remote-ssh 로 이미 올바른 노드에서 실행)

flow 1: 장치 선택 메뉴
  - 본 노드만 active (선택 가능)
  - 다른 노드 선택 시 안내 메시지 + 재선택 (CLI 가 ssh 자동 호출 X)

설계 기반:
  - node.yaml 로딩: hil_inference.py load_gate_config() line 80~120 패턴 응용
    (경로 처리: Path.is_dir() 분기 + 파일 미존재 시 None 반환)
  - 환경변수 경유 값 처리: check_hardware.sh record_step() line 128~144 패턴 응용
    (특수문자 안전 처리를 위해 환경변수 경유)

갱신 (2026-05-02, TODO-X2):
  - VALID_NODES: ("orin", "dgx", "datacollector") → ("orin", "dgx")
    datacollector 노드 운영 종료 (06_dgx_absorbs_datacollector 결정 C·F).
  - dgx 분기: flow 3 mode 분기 (mode.py) 호출로 변경
    (env_check 는 mode 인자 없이 smoke 로 사전 점검 — 수집/학습 분기는 mode.py 책임)
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
# 갱신 (2026-05-02, TODO-X2): datacollector 제거 (06 결정 C·F — 노드 운영 종료)
VALID_NODES = ("orin", "dgx")

NODE_DESCRIPTIONS = {
    "orin": "Orin (추론 노드) — 학습된 ckpt 로 hil_inference 실행",
    "dgx": "DGX (학습·수집 노드) — 데이터 수집 + 학습 + 체크포인트 관리",
}

NODE_GUIDE = {
    "orin": "Orin 에서 실행: bash orin/interactive_cli/main.sh",
    "dgx": "DGX 에서 실행: bash dgx/interactive_cli/main.sh",
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

    orin / dgx: VSCode remote-ssh 로 이미 올바른 노드에서 실행 →
                확인 단계 없음 → True 즉시 반환.

    갱신 (2026-05-02, TODO-X2):
      datacollector 분기 제거 (노드 운영 종료).
      node 가 VALID_NODES 내이면 항상 True 반환.

    Returns:
        True: 계속 진행 / False: 잘못된 노드 (이론상 도달 X)
    """
    # orin·dgx: 확인 단계 없음 (VSCode remote-ssh 로 이미 올바른 노드)
    return True


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
    if selected == "dgx":
        from flows.env_check import flow2_env_check
        from flows.mode import flow3_mode_entry

        script_dir = Path(args.node_config).parent.parent  # configs/ 상위 = interactive_cli/

        # flow 2: 환경 체크 (기본 smoke 시나리오로 preflight — mode 선택 전 사전 점검)
        # mode 인자 없이 train 체크만 수행. 수집 환경 체크 (USB·카메라) 는
        # mode.py 에서 수집 mode 선택 시 env_check.py 재호출 (mode="collect") 로 처리.
        # 현재 env_check.py 는 preflight_check.sh 래퍼 (mode 파라미터 추가는 §1 명세 — TODO-X2 §7).
        if not flow2_env_check(script_dir, scenario="smoke"):
            return 1  # preflight FAIL — 종료

        # flow 3: mode 분기 (G-4 결정 — 수집/학습/종료)
        return flow3_mode_entry(script_dir)

    else:
        # orin: 후행 todo 에서 구현
        print()
        print(f"[TODO] flow 2+ ({selected} 노드 책임) — 후행 todo 에서 구현")
        print("       env_check.py → 노드별 책임 모듈 (inference.py 등)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
