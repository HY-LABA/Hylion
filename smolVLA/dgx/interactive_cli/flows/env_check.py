"""interactive_cli flow 2 — DGX 환경 체크 (preflight_check.sh 래퍼).

flow 2: 환경 체크
  - dgx/scripts/preflight_check.sh 를 subprocess 로 호출
  - 5체크 항목 (venv·메모리·Walking RL·Ollama·디스크) 결과 출력
  - exit 0 통과 / exit != 0 오류 안내 + False 반환

설계 기반:
  - 11_interactive_cli_framework.md §5 orin env_check.py 패턴 (check_hardware.sh 래퍼)
    그대로 dgx 용으로 변형:
      script_dir.parent / "scripts" / "preflight_check.sh"
      subprocess.run([...], check=False)
  - preflight_check.sh 사용: bash preflight_check.sh {smoke|s1|s3|lora}
    (14_dgx_cli_flow.md §1-2 인용)
"""

import subprocess
import sys
from pathlib import Path


def run_env_check(script_dir: Path, scenario: str = "smoke") -> bool:
    """preflight_check.sh 를 subprocess 로 호출.

    11_interactive_cli_framework.md §5 orin env_check.py 패턴 응용:
      subprocess.run(["bash", str(check_script), "--mode", "resume"], check=False)
    dgx 용 변형: 시나리오 인자 (smoke|s1|s3|lora) 전달.

    preflight_check.sh line 5~9 사용법:
      bash preflight_check.sh smoke   # 1 step 검증용 (필요 메모리 20 GB)
      bash preflight_check.sh s1      # 04 / 06 1차 학습 (35 GB)
      bash preflight_check.sh s3      # 06 2차 학습 - VLM 까지 풀 학습 (65 GB)
      bash preflight_check.sh lora    # LoRA fallback (28 GB)

    Args:
        script_dir: dgx/interactive_cli/ 디렉터리 경로
        scenario:   "smoke"|"s1"|"s3"|"lora"

    Returns:
        True: preflight PASS (exit 0) / False: FAIL (exit != 0)
    """
    preflight = script_dir.parent / "scripts" / "preflight_check.sh"

    if not preflight.exists():
        print(f"[ERROR] preflight_check.sh 미존재: {preflight}", file=sys.stderr)
        print("        dgx/scripts/preflight_check.sh 를 확인하세요.", file=sys.stderr)
        return False

    result = subprocess.run(
        ["bash", str(preflight), scenario],
        check=False,
    )
    return result.returncode == 0


def flow2_env_check(script_dir: Path, scenario: str = "smoke") -> bool:
    """flow 2: DGX 환경 체크 단계.

    preflight_check.sh 5체크 결과를 사용자에게 출력 후
    PASS / FAIL 을 반환.

    Returns:
        True: 환경 체크 통과 / False: FAIL (후속 flow 중단 필요)
    """
    print()
    print("=" * 60)
    print(" flow 2 — DGX 환경 체크 (preflight)")
    print("=" * 60)
    print()
    print(f"  시나리오: {scenario}")
    print()

    passed = run_env_check(script_dir, scenario)

    if passed:
        print()
        print("[flow 2] preflight PASS — 학습 진행 가능합니다.")
    else:
        print()
        print("[flow 2] preflight FAIL — 위 [FAIL] 항목을 해결 후 다시 실행하세요.")
        print()
        print("  주의: Walking RL / 다른 사용자 프로세스는 절대 건드리지 마세요.")
        print("        본인 프로세스(Jupyter 커널, 본인 Ollama) 만 정리하세요.")

    return passed
