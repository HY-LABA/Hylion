#!/usr/bin/env python3
"""dgx/finetune/leftarm_v2/run_teleop.py — leftarm_v2 텔레옵 (셋업 검증).

config/{base,record}_config.yaml → lerobot-teleoperate 명령 구성·실행.
record 전에 캘리브레이션·포트·카메라·모터 정합을 텔레오퍼레이션으로 검증하는 용도.
데이터를 저장하지 않음 (--dataset.* 없음). 공용 로직은 _lib.py.

사용:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  # config/base_config.yaml 의 hardware 섹션을 채운 뒤 (check_port_and_camera_index.py 로 확인):
  python run_teleop.py                  # 카메라 포함 — 영상 + 모터 정합 검증 (display_data)
  python run_teleop.py --no-cameras     # 모터만 — 빠른 모터·통신 점검 (카메라 인자 제외)
  python run_teleop.py --dry-run        # 명령만 출력, 실행 안 함

종료: Ctrl-C. leader 팔을 움직여 follower 가 따라오는지, 화면(display_data)으로 카메라
영상이 record_config 의 회전/해상도대로 나오는지 확인.
"""
import argparse
import shlex
import shutil
import subprocess
from pathlib import Path

from _lib import die, load_configs, check_calibration, resolve_robot_teleop

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR / "config"
TAG = "[run_teleop]"


def cmd_teleop(args, base, record):
    # ── 사전 점검: 캘리브레이션 파일 존재 ──
    check_calibration(base)

    # ── robot/teleop(/camera) 공통 인자 (base_config 물리 셋업, 세션값 = hardware) ──
    with_cameras = not args.no_cameras
    rt_args, summary = resolve_robot_teleop(base, with_cameras=with_cameras)

    # ── lerobot-teleoperate 명령 구성 ──
    opts = record["record_opts"]
    b = lambda x: str(x).lower()
    cmd = ["lerobot-teleoperate"] + rt_args + [
        f"--display_data={b(opts['display_data'])}",
    ]

    # ── 요약 출력 ──
    print(f"{TAG} mode     : 셋업 검증 텔레옵 (데이터 저장 X)")
    print(f"{TAG} cameras  : {'포함' if with_cameras else '제외 (--no-cameras)'}")
    print(f"{TAG} follower : {summary['follower_port']}  [config hardware.follower_port]")
    print(f"{TAG} leader   : {summary['leader_port']}  [config hardware.leader_port]")
    for c, idx in summary["cameras"].items():
        print(f"{TAG} cam {c:<6}: {idx}  [config hardware.camera_{c}_index]")
    print()
    print(f"{TAG} 구성된 명령:")
    print("  " + " \\\n    ".join(shlex.quote(c) for c in cmd))
    print()

    if args.dry_run:
        print(f"{TAG} --dry-run — 실행하지 않음.")
        return

    if not shutil.which("lerobot-teleoperate"):
        die("lerobot-teleoperate 없음 — venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate")

    print(f"{TAG} lerobot-teleoperate 실행... (Ctrl-C 로 종료)\n")
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(
        description="leftarm_v2 텔레옵 — 셋업 검증 (config → lerobot-teleoperate)")
    ap.add_argument("--no-cameras", action="store_true",
                    help="카메라 인자 제외 (모터만 — 빠른 점검)")
    ap.add_argument("--dry-run", action="store_true", help="명령만 출력, 실행 안 함")
    args = ap.parse_args()

    base, record = load_configs(CONFIG_DIR)
    cmd_teleop(args, base, record)


if __name__ == "__main__":
    main()
