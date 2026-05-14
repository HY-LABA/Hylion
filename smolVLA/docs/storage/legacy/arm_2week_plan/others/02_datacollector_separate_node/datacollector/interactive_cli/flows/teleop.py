"""interactive_cli flow 3·4 — 텔레오퍼레이션 + 사용자 확인.

flow 3: run_teleoperate.sh all subprocess 호출
flow 4: 텔레오퍼레이션 완료 후 사용자 확인 (재시도 'r' / 진행 Enter)

레퍼런스:
  - datacollector/scripts/run_teleoperate.sh main() (line 67~94):
      all 커맨드: calibrate_follower → calibrate_leader → teleoperate (line 70~74)
      FOLLOWER_PORT="/dev/ttyACM1" (line 19)
      LEADER_PORT="/dev/ttyACM0" (line 20)
      선행 조건: .hylion_collector venv 활성화 (line 8~10)
"""

import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# flow 3 — 텔레오퍼레이션 실행
# ---------------------------------------------------------------------------

def _run_teleop_script(script_dir: Path) -> int:
    """run_teleoperate.sh all 을 subprocess 로 호출.

    D1 §2 에서 정의한 subprocess 호출 패턴:
      subprocess.run(["bash", str(teleop_script), "all"], check=False)
      + return result.returncode

    Args:
        script_dir: datacollector/interactive_cli/flows/ 경로.
                    scripts/ 은 script_dir.parent.parent / "scripts" 에 위치.

    Returns:
        subprocess returncode (0=성공, 비0=실패)
    """
    teleop_script = script_dir.parent.parent / "scripts" / "run_teleoperate.sh"

    if not teleop_script.exists():
        print(f"[flow 3] ERROR: run_teleoperate.sh 미발견: {teleop_script}", file=sys.stderr)
        return 1

    print()
    print(f"[flow 3] 실행: bash {teleop_script} all")
    print()

    result = subprocess.run(
        ["bash", str(teleop_script), "all"],
        check=False,
    )
    return result.returncode


def flow3_teleoperate(script_dir: Path) -> int:
    """flow 3: 텔레오퍼레이션 진행.

    spec line 53:
      "텔레오퍼레이션을 진행하겠습니다 (이 작업이 끝나면 학습 준비가 완료됩니다)" 출력 + enter 시 실행

    Returns:
        subprocess returncode
    """
    print()
    print("=" * 60)
    print(" flow 3 — 텔레오퍼레이션")
    print("=" * 60)
    print()
    print("텔레오퍼레이션을 진행하겠습니다.")
    print("이 작업이 끝나면 학습 준비가 완료됩니다.")
    print()
    print("Enter 를 누르면 run_teleoperate.sh 가 실행됩니다.")
    print("(종료하려면 Ctrl+C)")
    print()

    try:
        input()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[flow 3] 취소됨.")
        return 1

    return _run_teleop_script(script_dir)


# ---------------------------------------------------------------------------
# flow 4 — 사용자 확인 (재시도 / 진행)
# ---------------------------------------------------------------------------

def flow4_confirm_teleop(script_dir: Path, prev_returncode: int) -> bool:
    """flow 4: 텔레오퍼레이션 완료 후 사용자 확인.

    spec line 54: "잘 작동하면 enter를 눌러주세요" + enter 입력
    D1 §2 flow 4 동작:
      - returncode == 0: 정상 완료 메시지 → 재시도('r') / 진행(Enter)
      - returncode != 0: 에러 메시지 → 재시도('r') / 종료(Enter)

    Returns:
        True: flow 5 로 진행 / False: 종료 (사용자 거부 또는 Ctrl+C)
    """
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
            raw = input("입력 ['r'=재시도 / Enter=진행 / Ctrl+C=종료]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 4] 종료됩니다.")
            return False

        if raw == "r":
            print()
            print("[flow 4] 텔레오퍼레이션을 다시 실행합니다.")
            prev_returncode = flow3_teleoperate(script_dir)
            continue

        # Enter (빈 문자열) 또는 다른 입력 → 진행
        if prev_returncode != 0:
            print()
            print("[flow 4] 경고: 텔레오퍼레이션이 정상 종료되지 않았습니다. 그래도 진행합니다.")

        print()
        print("[flow 4] flow 5 (학습 종류 선택) 로 진행합니다.")
        return True
