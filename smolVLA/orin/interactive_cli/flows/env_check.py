"""interactive_cli flow 2 — orin 환경 체크 (check_hardware.sh 호출).

설계 기반:
  - check_hardware.sh 지원 인자: --mode, --config, --quiet, --output-json (line 68~83)
  - --gate-json 은 hil_inference.py 전용 인자 — check_hardware.sh 에 전달하면 exit 2 로 실패
  - 경로 상수 (PORTS_JSON, CAMERAS_JSON) 는 스크립트 내부에서 자동 결정 (line 41~46)
  - 11_interactive_cli_framework.md §5 orin env_check 예시 + 13_orin_cli_flow.md §1 그대로 적용
"""

import subprocess
import sys
from pathlib import Path


def run_env_check(script_dir: Path) -> bool:
    """check_hardware.sh --mode resume 을 실행하여 orin 환경을 검증한다.

    check_hardware.sh 경로: script_dir.parent.parent / "tests" / "check_hardware.sh"
    (flows/ → interactive_cli/ → orin/ → tests/check_hardware.sh)

    지원 인자 (check_hardware.sh line 68~83):
      --mode {first-time|resume}, --config, --quiet, --output-json
    주의: --gate-json 은 hil_inference.py 전용 — 여기에는 절대 전달하지 않는다.

    Returns:
        True: exit 0 (환경 준비 완료) / False: exit != 0 (오류 또는 미충족 항목 있음)
    """
    check_script = script_dir.parent.parent / "tests" / "check_hardware.sh"

    if not check_script.exists():
        print(f"[ERROR] check_hardware.sh 미존재: {check_script}", file=sys.stderr)
        return False

    print()
    print("=" * 60)
    print(" flow 2 — 환경 체크")
    print("=" * 60)
    print()
    print("[flow 2] 환경 체크 중...")
    print(f"  script: {check_script}")
    print()

    result = subprocess.run(
        ["bash", str(check_script), "--mode", "resume"],
        check=False,
    )

    if result.returncode == 0:
        print()
        print("[flow 2] 환경 체크 완료 — 추론 준비 완료")
        return True
    else:
        print()
        print(f"[ERROR] 환경 체크 실패 (exit {result.returncode})")
        print("        check_hardware.sh 를 수동 실행하여 오류를 확인하세요:")
        print(f"          bash {check_script} --mode resume")
        print()
        print("        first-time 설정이 필요한 경우:")
        print(f"          bash {check_script} --mode first-time")
        return False
