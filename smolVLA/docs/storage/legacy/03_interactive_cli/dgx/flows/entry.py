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

"""

import argparse
import os
import sys
from pathlib import Path

from flows._back import is_back

try:
    import yaml
except ImportError:
    # PyYAML 없을 시 단순 파서로 대체
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 노드 종류 상수
# ---------------------------------------------------------------------------
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
        {"node": "orin"|"dgx", "venv": "~/..."} 또는 None.
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
# display mode 검출 (TODO-D6)
# ---------------------------------------------------------------------------

def _prompt_entry(message: str) -> str:
    """input() 래퍼 — EOFError·KeyboardInterrupt 보호 (entry.py 내부용)."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise KeyboardInterrupt


def detect_display_mode() -> str:
    """SSH 접속 vs 직접 실행 자동 검출 + 사용자 확인.

    카메라 영상을 어떻게 표시할지 결정:
      "direct"   — DGX 모니터에 OpenCV imshow (DISPLAY=:0 등 로컬 DISPLAY)
      "ssh-x11"  — SSH X11 forwarding 활성 (DISPLAY=localhost:N). cv2.imshow 시도.
                   X11 실패 시 precheck._show_frame() 이 ssh-file 로 자동 fallback.
                   전제: ssh -Y dgx 또는 ssh -X dgx 로 접속 필요.
      "ssh-file" — 이미지 파일 저장 + path 출력 (xdg-open 시도). SSH 파일 모드.

    자동 검출 기준:
      is_ssh: SSH_CLIENT 또는 SSH_TTY 환경변수 존재 여부 (표준 SSH 연결 시 셸이 설정)
      display: DISPLAY 환경변수
        - is_ssh + display.startswith("localhost:") → ssh-x11 (X11 forwarding 활성)
        - is_ssh + 그 외 → ssh-file
        - not is_ssh + display → direct
        - not is_ssh + not display → direct (DISPLAY=:0 시도 가능)

    SMOLVLA_DISPLAY_MODE 환경변수로 강제 override 가능:
      "direct" | "ssh-x11" | "ssh-file" | "ssh" (구형 compat → ssh-file 로 처리)

    DISPLAY fallback:
      direct 선택 시 DISPLAY 환경변수 미설정 → ssh-file 모드 자동 전환 + 안내.

    Returns:
        "direct", "ssh-x11", 또는 "ssh-file"
    """
    # 환경변수 강제 override (비대화형 테스트·스크립트 호출 시)
    env_override = os.environ.get("SMOLVLA_DISPLAY_MODE", "").lower()
    if env_override in ("direct", "ssh-x11", "ssh-file"):
        return env_override
    if env_override == "ssh":  # 구형 호환 — ssh-file 로 처리
        return "ssh-file"

    # 자동 검출
    is_ssh = bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))
    display = os.environ.get("DISPLAY", "")

    # SSH X11 forwarding: DISPLAY=localhost:N 패턴
    if is_ssh and display.startswith("localhost:"):
        auto_detected = "ssh-x11"
    elif is_ssh:
        auto_detected = "ssh-file"
    else:
        auto_detected = "direct"

    # 사용자 확인 prompt (+ SSH X11 안내)
    print()
    print("=" * 60)
    print(" 환경 모드 선택 (카메라 영상 표시 방법)")
    print("=" * 60)
    print()
    print(f"  현재 DISPLAY={display!r}  SSH={is_ssh}")
    print()
    print("  (1) direct    — DGX 모니터에 OpenCV 창 표시 (DISPLAY=:0 필요)")
    print("  (2) ssh-x11   — SSH X11 forwarding 으로 cv2.imshow")
    print("                  (ssh -Y dgx 또는 ssh -X dgx 로 접속 시 사용)")
    print("  (3) ssh-file  — 이미지 파일 저장 + path 출력 (xdg-open 시도)")
    print()
    print(f"  자동 검출: {auto_detected}")
    print()
    if is_ssh and auto_detected == "ssh-file":
        print("  * SSH X11 forwarding 을 사용하려면 ssh -Y dgx 로 재접속하세요.")
        print("    X11 forwarding 활성 시 DISPLAY=localhost:N 으로 자동 검출됩니다.")
        print()

    try:
        raw = _prompt_entry(f"번호 선택 [1~3, Enter={auto_detected}, b: 뒤로]: ")
    except KeyboardInterrupt:
        print("[entry] 인터럽트 — 자동 검출 값 사용: {}".format(auto_detected))
        raw = ""

    # 환경 모드 선택 최상위 — b/back 시 자동 검출값으로 진행 (되돌아갈 상위 없음)
    if is_back(raw):
        print("[entry] 환경 모드 선택 최상위 — 자동 검출값으로 진행합니다.")
        raw = ""

    if raw == "1":
        selected = "direct"
    elif raw == "2":
        selected = "ssh-x11"
    elif raw == "3":
        selected = "ssh-file"
    else:
        selected = auto_detected

    # DISPLAY fallback: direct 선택 + DISPLAY 미설정 → ssh-file 전환
    if selected == "direct" and not display:
        print()
        print(
            "[entry] 경고: DISPLAY 환경변수 미설정 — OpenCV imshow 동작 불가."
        )
        print("        ssh-file 모드(이미지 파일 저장)로 자동 전환합니다.")
        print("        DGX 모니터에서 직접 실행 시: export DISPLAY=:0")
        print("        SSH X11 forwarding 사용 시: ssh -Y dgx 로 재접속")
        selected = "ssh-file"

    print()
    print(f"[entry] 환경 모드 결정: {selected}")
    return selected


# ---------------------------------------------------------------------------
# flow 0 — 환경 확인
# ---------------------------------------------------------------------------

def flow0_confirm_environment(node: str) -> bool:
    """flow 0: 환경 확인 단계.

    orin / dgx: VSCode remote-ssh 로 이미 올바른 노드에서 실행 →
                확인 단계 없음 → True 즉시 반환.

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

    원칙: 본 노드만 active, 다른 노드는 안내만.
    — 어느 노드에서 실행하든 자신의 노드만 active, 나머지는 선택 불가 + 안내.

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
            raw = input("번호 선택 [1~{}, b: 뒤로(종료)]: ".format(len(VALID_NODES) + 1)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        # 진입 최상위(flow 1) — b/back 시 종료 (되돌아갈 상위 없음)
        if is_back(raw):
            print("종료합니다.")
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

    # flow 0: 환경 확인
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

        # display mode 결정 (TODO-D6) — flow 초반에 SSH/직접 분기 결정
        # flow3_mode_entry → precheck.py 카메라 영상 표시 방법 전달
        display_mode = detect_display_mode()

        # flow 2: 환경 체크 (기본 smoke 시나리오로 preflight — mode 선택 전 사전 점검)
        # mode 인자 없이 train 체크만 수행. 수집 환경 체크 (USB·카메라) 는
        # mode.py 에서 수집 mode 선택 시 env_check.py 재호출 (mode="collect") 로 처리.
        # 현재 env_check.py 는 preflight_check.sh 래퍼 (mode 파라미터 추가는 §1 명세 — TODO-X2 §7).
        if not flow2_env_check(script_dir, scenario="smoke"):
            return 1  # preflight FAIL — 종료

        # flow 3: mode 분기 (G-4 결정 — 수집/학습/종료)
        return flow3_mode_entry(script_dir, display_mode=display_mode)

    else:
        # orin: 후행 todo 에서 구현
        print()
        print(f"[TODO] flow 2+ ({selected} 노드 책임) — 후행 todo 에서 구현")
        print("       env_check.py → 노드별 책임 모듈 (inference.py 등)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
