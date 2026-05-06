"""interactive_cli flow 2 — DGX 환경 체크 (학습 + 수집 통합).

flow 2: 환경 체크
  - mode="train": dgx/scripts/preflight_check.sh 5체크 (기존 학습 환경 체크)
  - mode="collect": preflight_check.sh + 수집 환경 하드웨어 체크 (USB·dialout·v4l2·SO-ARM)
  - mode=None (기본): preflight_check.sh 만 실행 (entry.py 사전 점검)

설계 기반:
  - 14_dgx_cli_flow.md §1 통합 체크 명세
    §1-2: 학습 환경 5단계 (preflight_check.sh 그대로)
    §1-3: 수집 환경 4단계 (항목 6~9 — USB 포트·dialout·v4l2·SO-ARM 포트)
    §1-4: env_check.py 구현 패턴 (mode="collect" 시 _check_hardware_collect() 호출)
  - 11_interactive_cli_framework.md §5 orin env_check.py 패턴 (check_hardware.sh 래퍼)
    그대로 dgx 용으로 변형:
      script_dir.parent / "scripts" / "preflight_check.sh"
      subprocess.run([...], check=False)

"""

import subprocess
import sys
from pathlib import Path


def run_env_check(script_dir: Path, scenario: str = "smoke") -> bool:
    """preflight_check.sh 를 subprocess 로 호출.

    14_dgx_cli_flow.md §1-2 학습 환경 체크 (preflight_check.sh 5단계).

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


def _check_hardware_collect() -> bool:
    """수집 환경 하드웨어 체크 (항목 6~9).

    14_dgx_cli_flow.md §1-3 수집 환경 체크:
      항목 6: USB 포트 존재 (/dev/ttyACM0 leader, /dev/ttyACM1 follower)
      항목 7: dialout 그룹 멤버십
      항목 8: v4l2 카메라 (/dev/video* 디바이스)
      항목 9: SO-ARM 포트 응답 (pyserial serial.Serial 임시 open)

    datacollector env_check.py §1 미러 (dgx 경로 맞춤).
    FAIL 시 False 반환 + 안내 메시지 출력 (즉시 종료 X — 사용자가 판단).

    Returns:
        True: 모든 항목 PASS / False: 하나 이상 FAIL
    """
    import grp
    import os

    all_pass = True

    # 항목 6: USB 포트 존재
    print()
    print("  [항목 6] USB 포트 확인")
    leader_port = "/dev/ttyACM0"
    follower_port = "/dev/ttyACM1"
    leader_ok = Path(leader_port).exists()
    follower_ok = Path(follower_port).exists()

    if leader_ok:
        print(f"    PASS  leader  ({leader_port})")
    else:
        print(f"    FAIL  leader  ({leader_port}) 미발견 — SO-ARM leader 연결 확인")
        all_pass = False

    if follower_ok:
        print(f"    PASS  follower ({follower_port})")
    else:
        print(f"    FAIL  follower ({follower_port}) 미발견 — SO-ARM follower 연결 확인")
        all_pass = False

    # 항목 7: dialout 그룹
    print()
    print("  [항목 7] dialout 그룹 멤버십")
    try:
        username = os.environ.get("USER", "") or os.environ.get("LOGNAME", "")
        dialout_gid = grp.getgrnam("dialout").gr_gid
        user_groups = os.getgroups()
        if dialout_gid in user_groups:
            print(f"    PASS  {username} 는 dialout 그룹 멤버")
        else:
            print(f"    FAIL  {username} 가 dialout 그룹 미포함")
            print("          sudo usermod -aG dialout $USER && 재로그인 필요")
            all_pass = False
    except (KeyError, OSError) as e:
        print(f"    WARN  dialout 그룹 확인 실패: {e}")

    # 항목 8: v4l2 카메라
    print()
    print("  [항목 8] v4l2 카메라 확인")
    video_devices = sorted(Path("/dev").glob("video*"))
    if video_devices:
        print(f"    PASS  {len(video_devices)}개 발견: {[str(d) for d in video_devices[:4]]}")
    else:
        print("    FAIL  /dev/video* 디바이스 없음 — 카메라 USB 연결 확인")
        all_pass = False

    # 항목 9: SO-ARM 포트 응답 (follower 포트 임시 open 시도)
    print()
    print("  [항목 9] SO-ARM 포트 응답")
    if follower_ok:
        try:
            import serial  # type: ignore[import-untyped]
            with serial.Serial(follower_port, timeout=0.5):
                pass
            print(f"    PASS  {follower_port} serial open 성공")
        except ImportError:
            print("    SKIP  pyserial 미설치 — 포트 응답 검증 생략")
        except Exception as e:
            print(f"    FAIL  {follower_port} serial open 실패: {e}")
            all_pass = False
    else:
        print(f"    SKIP  {follower_port} 미존재 — 항목 6 FAIL 로 이미 확인됨")

    return all_pass


def flow2_env_check(
    script_dir: Path,
    scenario: str = "smoke",
    mode: str = "train",
) -> bool:
    """flow 2: DGX 환경 체크 단계.

    학습 환경 (preflight 5단계) + 수집 환경 (USB·dialout·v4l2·SO-ARM 4단계) 통합 체크.
    mode 파라미터로 selective check 실행:
      mode="train"   → preflight 5단계만 (기본값)
      mode="collect" → preflight 5단계 + 수집 하드웨어 4단계
      그 외          → preflight 5단계만 (entry.py 사전 점검 용도)

    결정 (TODO-X2 §7): selective check 방식.
      수집 장비 (SO-ARM, 카메라) 는 수집 mode 선택 시에만 필수.
      학습 mode 에서 USB 부재가 preflight FAIL 되면 안 됨.

    Returns:
        True: 환경 체크 통과 / False: FAIL (후속 flow 중단 필요)
    """
    print()
    print("=" * 60)
    if mode == "collect":
        print(" flow 2 — DGX 환경 체크 (학습 + 수집 통합)")
    else:
        print(" flow 2 — DGX 환경 체크 (preflight)")
    print("=" * 60)
    print()
    print(f"  시나리오: {scenario}")
    if mode == "collect":
        print("  mode: collect (수집 환경 체크 추가)")
    print()

    # 학습 환경 체크 (preflight 5단계)
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
        return False

    # 수집 환경 체크 (mode="collect" 일 때만)
    if mode == "collect":
        print()
        print("[flow 2] 수집 환경 하드웨어 체크 (항목 6~9):")
        hw_passed = _check_hardware_collect()
        if hw_passed:
            print()
            print("[flow 2] 수집 환경 체크 PASS.")
        else:
            print()
            print("[flow 2] 수집 환경 체크 FAIL — 위 FAIL 항목을 해결 후 다시 실행하세요.")
            print("         하드웨어 연결 확인 후 CLI 를 재시작하세요.")
            return False

    return True
