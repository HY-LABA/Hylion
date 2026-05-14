"""interactive_cli flow 3·4 — 텔레오퍼레이션 + 사용자 확인.

flow 3: run_teleoperate.sh all subprocess 호출
flow 4: 텔레오퍼레이션 완료 후 사용자 확인 (재시도 'r' / 진행 Enter)

레퍼런스 (이식 원본):
  docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/teleop.py
  함수 시그니처·로직 그대로 재사용 (14_dgx_cli_flow.md §3-2 명세 준수).

이식 변경 사항 (14_dgx_cli_flow.md §3-2 표):
  - scripts 경로: script_dir.parent.parent / "scripts" / "run_teleoperate.sh"
    → dgx 디렉터리 구조에서 interactive_cli/ 가 dgx/ 하위이므로:
      script_dir.parent / "scripts" / "run_teleoperate.sh" 로 변경.
    (원본: datacollector/interactive_cli/flows/ 에서 ../.. → datacollector/scripts/)
    (dgx: dgx/interactive_cli/flows/ 에서 .. → dgx/interactive_cli/, .. → dgx/scripts/ X
     실제 dgx/scripts/ 는 interactive_cli/ 의 형제 — script_dir.parent / "scripts")
  - venv 전제: .hylion_collector → .arm_finetune (main.sh 에서 이미 activate)
  - 스크립트: run_teleoperate.sh (X3 이식 대상)
  - flow 번호 표기: mode 분기 후 수집 flow 로서 flow 3·4 번호 유지 (G-4 결정)

원본 teleop.py line 37:
    teleop_script = script_dir.parent.parent / "scripts" / "run_teleoperate.sh"
dgx 이식 후:
    teleop_script = script_dir.parent / "scripts" / "run_teleoperate.sh"

"""

import json
import os
import subprocess
import sys
from pathlib import Path

from flows._back import is_back


# ---------------------------------------------------------------------------
# flow 3 — 텔레오퍼레이션 실행
# ---------------------------------------------------------------------------

def _run_teleop_script(script_dir: Path, env: "dict | None" = None) -> int:
    """run_teleoperate.sh all 을 subprocess 로 호출.

    원본 D1 §2 에서 정의한 subprocess 호출 패턴 그대로:
      subprocess.run(["bash", str(teleop_script), "all"], check=False)
      + return result.returncode

    이식 변경: script_dir.parent.parent → script_dir.parent
      (dgx/interactive_cli/flows/ → dgx/scripts/ 경로)

    lerobot-teleoperate 는 Ctrl+C 가 표준 종료 방법 (lerobot upstream 표준):
      upstream lerobot_teleoperate.py L239: except KeyboardInterrupt: pass
    Ctrl+C 발생 시 subprocess (lerobot-teleoperate) 도 SIGINT 를 받아 자체 정리 후 종료.
    부모 프로세스 (Python) 에도 KeyboardInterrupt 가 raise → 여기서 catch → return 0.
    → flow4_confirm_teleop 정상 분기 (returncode=0) 진입 보장.

    Args:
        script_dir: dgx/interactive_cli/flows/ 경로.
                    scripts/ 은 script_dir.parent / "scripts" 에 위치.
        env: subprocess 에 전달할 환경변수 dict. None 이면 os.environ 그대로.

    Returns:
        subprocess returncode (0=성공·Ctrl+C 정상 종료, 비0=실패)
    """
    teleop_script = script_dir.parent / "scripts" / "run_teleoperate.sh"

    if not teleop_script.exists():
        print(f"[flow 3] ERROR: run_teleoperate.sh 미발견: {teleop_script}", file=sys.stderr)
        print("         dgx/scripts/run_teleoperate.sh 를 확인하세요. (X3 이식 대상)", file=sys.stderr)
        return 1

    print()
    print(f"[flow 3] 실행: bash {teleop_script} all")
    print()

    try:
        result = subprocess.run(
            ["bash", str(teleop_script), "all"],
            env=env,
            check=False,
        )
        return result.returncode
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C 로 정상 종료 — lerobot-teleoperate 의 표준 종료 방법.
        # subprocess (lerobot-teleoperate) 도 SIGINT 받아 자체 정리 후 종료됨
        # (upstream lerobot_teleoperate.py: except KeyboardInterrupt: pass → finally 정리).
        print()
        print("[teleop] Ctrl+C 감지 — teleop 정상 종료 처리.")
        print("         (lerobot-teleoperate 가 Ctrl+C 로 정상 종료됨)")
        return 0  # 0 으로 반환 → flow4_confirm_teleop 정상 완료 분기 진입


def flow3_teleoperate(script_dir: Path) -> int:
    """flow 3: 텔레오퍼레이션 진행.

    원본 teleop.py flow3_teleoperate 함수 그대로.
    "텔레오퍼레이션을 진행하겠습니다 (이 작업이 끝나면 학습 준비가 완료됩니다)" 출력 + enter 시 실행.

    Returns:
        subprocess returncode (0=성공·Ctrl+C 정상 종료, -1=b/back 취소, 비0=실패)
    """
    print()
    print("=" * 60)
    print(" flow 3 — 텔레오퍼레이션")
    print("=" * 60)
    print()
    print("텔레오퍼레이션을 진행하겠습니다.")
    print("이 작업이 끝나면 학습 준비가 완료됩니다.")
    print()
    print("흐름:")
    print("  1. Enter 를 누르면 run_teleoperate.sh 실행 — leader 팔로 follower 팔 조종 가능")
    print("  2. 충분히 시연한 후 Ctrl+C 한 번 누르면 *정상 종료* (lerobot 표준 종료 키)")
    print("     (다른 종료 키 X — Ctrl+C 가 lerobot-teleoperate 의 유일한 종료 방법)")
    print("  3. 종료 후 다음 단계: flow4 prompt → data_kind → record (epi 수집) → transfer → 학습 분기")
    print()
    print("  ※ teleop 도중에는 'Teleop loop time: ...' 출력만 보이고 종료 안내 X (lerobot 표준 출력).")
    print("    충분한 시연 후 Ctrl+C 한 번 누르면 됩니다.")
    print("  ※ run_teleoperate.sh 실행 중에는 뒤로가기 불가 — Ctrl+C 로만 종료 가능.")
    print()

    try:
        pre_raw = input("Enter 시작 / b: 뒤로(취소): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[flow 3] 취소됨.")
        return 1

    # b/back: precheck 단계로 복귀 신호
    # sentinel = -1: Python 측 전용 값 — bash returncode 범위 (0~255) 와 충돌 없음
    # run_teleoperate.sh 는 exit 0 (Ctrl+C 정상 종료) 또는 exit 1 (오류) 반환.
    # exit 2 를 명시적으로 사용할 수 있으므로 -1 사용 (shell 범위 초과 → 충돌 불가).
    if is_back(pre_raw):
        print()
        print("[flow 3] 뒤로가기 — teleop 사전 점검으로 돌아갑니다.")
        return -1  # Python 전용 sentinel: b/back 취소 (flow4_confirm_teleop 에서 처리)

    # calibration.json 로드 → FOLLOWER_ID / LEADER_ID 환경변수 주입
    # script_dir = dgx/interactive_cli/flows/  →  configs/ = dgx/interactive_cli/configs/
    configs_dir = script_dir.parent / "configs"
    calib_path = configs_dir / "calibration.json"
    env = os.environ.copy()

    if calib_path.exists():
        try:
            with calib_path.open() as f:
                calib = json.load(f)
            if calib.get("follower_id"):
                env["FOLLOWER_ID"] = calib["follower_id"]
            if calib.get("leader_id"):
                env["LEADER_ID"] = calib["leader_id"]
            print(
                f"[teleop] calibration.json 로드: "
                f"follower={env.get('FOLLOWER_ID', '(없음, hardcoded fallback)')}, "
                f"leader={env.get('LEADER_ID', '(없음, hardcoded fallback)')}"
            )
        except (json.JSONDecodeError, OSError) as e:
            print(f"[teleop] calibration.json 로드 실패 ({e}) — hardcoded fallback")
            env = None  # type: ignore[assignment]
    else:
        print("[teleop] calibration.json 미존재 — hardcoded fallback")
        env = None  # type: ignore[assignment]

    return _run_teleop_script(script_dir, env=env)


# ---------------------------------------------------------------------------
# flow 4 — 사용자 확인 (재시도 / 진행)
# ---------------------------------------------------------------------------

def flow4_confirm_teleop(script_dir: Path, prev_returncode: int) -> bool:
    """flow 4: 텔레오퍼레이션 완료 후 사용자 확인.

    원본 teleop.py flow4_confirm_teleop 함수 그대로.
    - returncode == 0: 정상 완료 메시지 → 재시도('r') / 진행(Enter)
    - returncode != 0: 에러 메시지 → 재시도('r') / 종료(Enter)

    Returns:
        True: flow 5 로 진행 / False: 종료 (사용자 거부 또는 Ctrl+C)
    """
    # teleop flow3 가 b/back 으로 취소된 경우 (sentinel = -1)
    if prev_returncode == -1:
        print()
        print("[flow 4] teleop 이 취소되었습니다 — 수집 mode 를 종료합니다.")
        return False

    while True:
        print()
        print("=" * 60)
        print(" flow 4 — 텔레오퍼레이션 확인")
        print("=" * 60)
        print()

        if prev_returncode == 0:
            print("텔레오퍼레이션이 완료되었습니다.")
            print()
            print("잘 작동했다면 Enter 를 눌러 데이터 수집 단계로 진행하세요.")
            print("다시 실행하려면 'r' 을 입력하세요.")
        else:
            print(f"텔레오퍼레이션이 비정상 종료되었습니다. (returncode={prev_returncode})")
            print()
            print("다시 시도하려면 'r' 을 입력하세요.")
            print("그냥 진행하려면 Enter 를 누르세요. (권장하지 않음)")
        print()

        try:
            if prev_returncode == 0:
                raw = input(
                    "입력 ['r'=teleop 재시도 / Enter=다음 단계 (record + 학습) / b=뒤로(취소) / Ctrl+C=완전 종료]: "
                ).strip().lower()
            else:
                raw = input(
                    "입력 ['r'=teleop 재시도 / Enter=강제 진행 (비권장) / b=뒤로(취소) / Ctrl+C=완전 종료]: "
                ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 4] 종료됩니다.")
            return False

        # b/back: 수집 mode 취소 (precheck 재진입은 mode.py 에서 처리)
        if is_back(raw):
            print()
            print("[flow 4] 뒤로가기 — 수집 mode 를 종료합니다.")
            return False

        if raw == "r":
            print()
            print("[flow 4] 텔레오퍼레이션을 다시 실행합니다.")
            prev_returncode = flow3_teleoperate(script_dir)
            # b/back 으로 취소된 경우 재처리 (sentinel = -1)
            if prev_returncode == -1:
                print()
                print("[flow 4] teleop 이 취소되었습니다 — 수집 mode 를 종료합니다.")
                return False
            continue

        # Enter (빈 문자열) 또는 다른 입력 → 진행
        if prev_returncode != 0:
            print()
            print("[flow 4] 경고: 텔레오퍼레이션이 정상 종료되지 않았습니다. 그래도 진행합니다.")

        print()
        print("[flow 4] flow 5 (학습 종류 선택) 로 진행합니다.")
        return True
