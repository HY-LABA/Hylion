#!/usr/bin/env python3
"""dgx/finetune/leftarm_v2/run_record.py — leftarm_v2 데이터 수집 래퍼.

config/{base,record}_config.yaml → lerobot-record 명령 구성·실행.
공용 로직은 _lib.py. 모든 인자는 yaml 출처 (하드코딩 없음).

사용:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  # config/base_config.yaml 의 hardware 섹션을 채운 뒤 (check_port_and_camera_index.py 로 확인):
  python run_record.py record --task 1 --episodes 10           # 1차 (dataset 없으면 fresh)
  python run_record.py record --task 1 --episodes 20           # 2차+ (dataset 있으면 자동 resume)
  python run_record.py record --task 2 --episodes 20           # task 2 (캔)
  python run_record.py record --task 1 --episodes 10 --dry-run # 명령만 출력

참고: --episodes 는 "이번 차수에 새로 기록할 개수" (lerobot num_episodes 시맨틱 — 누적 아님).
실 수집 전 셋업 검증은 run_teleop.py (텔레옵) 로.
"""
import argparse
import os
import shlex
import shutil
import subprocess
from pathlib import Path

from _lib import die, load_configs, expand_path, check_calibration, resolve_robot_teleop

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR / "config"
TAG = "[run_record]"


def cmd_record(args, base, record):
    if args.episodes < 1:
        die("--episodes 는 1 이상")

    hf_repo_id = base["hf_repo_id"]
    dataset_root = expand_path(base["paths"]["dataset_local"], "paths.dataset_local")

    # ── task 선택 ──
    tasks = record["tasks"]
    if not (1 <= args.task <= len(tasks)):
        opts_s = " / ".join(f"{i+1}={t['instruction']}" for i, t in enumerate(tasks))
        die(f"--task 는 1~{len(tasks)} (현재: {args.task}).  {opts_s}")
    task = tasks[args.task - 1]
    instruction = task["instruction"]
    target_episodes = task["target_episodes"]   # 수집 목표 (표시용 — 실 수집은 --episodes 차수별)

    # ── 사전 점검: 캘리브레이션 파일 존재 ──
    check_calibration(base)

    # ── robot/teleop/camera 공통 인자 (base_config 물리 셋업, 세션값 = hardware) ──
    rt_args, summary = resolve_robot_teleop(base, with_cameras=True)

    # ── resume 자동 감지 ──
    resume = dataset_root.exists()

    # ── lerobot-record 명령 구성 (모든 인자 yaml 출처) ──
    ds = record["dataset"]
    opts = record["record_opts"]
    b = lambda x: str(x).lower()  # bool → "true"/"false"
    cmd = ["lerobot-record"] + rt_args + [
        f"--dataset.repo_id={hf_repo_id}",
        f"--dataset.single_task={instruction}",
        f"--dataset.num_episodes={args.episodes}",
        f"--dataset.fps={ds['fps']}",
        f"--dataset.episode_time_s={ds['episode_time_s']}",
        f"--dataset.reset_time_s={ds['reset_time_s']}",
        f"--dataset.video={b(ds['video'])}",
        f"--dataset.vcodec={ds['vcodec']}",
        f"--dataset.streaming_encoding={b(ds['streaming_encoding'])}",
        f"--dataset.push_to_hub={b(ds['push_to_hub'])}",
        f"--dataset.private={b(ds['private'])}",
        f"--dataset.tags=[{', '.join(ds['tags'])}]",
        f"--display_data={b(opts['display_data'])}",
        f"--play_sounds={b(opts['play_sounds'])}",
    ]
    if resume:
        cmd += ["--resume=true", f"--dataset.root={dataset_root}"]

    # ── 요약 출력 ──
    print(f"{TAG} dataset  : {hf_repo_id}")
    print(f"{TAG} task {args.task}   : {instruction}")
    print(f"{TAG} episodes : {args.episodes}  (이번 차수 추가분 — 목표 {target_episodes} 중, 누적 아님)")
    print(f"{TAG} mode     : {'RESUME (기존 dataset 발견)' if resume else 'FRESH (신규 생성)'}")
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

    if not shutil.which("lerobot-record"):
        die("lerobot-record 없음 — venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate")

    # HF_USER 주입 (yaml 의 accounts.hf_user — venv 가 자동 export 안 함)
    env = dict(os.environ)
    hf_user = (base.get("accounts") or {}).get("hf_user")
    if hf_user and not env.get("HF_USER"):
        env["HF_USER"] = hf_user

    print(f"{TAG} lerobot-record 실행...\n")
    subprocess.run(cmd, env=env, check=True)


def main():
    ap = argparse.ArgumentParser(
        description="leftarm_v2 데이터 수집 래퍼 (config → lerobot-record)")
    sub = ap.add_subparsers(dest="action", required=True)
    rec = sub.add_parser("record", help="lerobot-record 실행")
    rec.add_argument("--task", type=int, required=True, help="task 번호 (1=인형, 2=캔)")
    rec.add_argument("--episodes", type=int, required=True,
                     help="이번 차수에 새로 기록할 episode 수 (누적 아님)")
    rec.add_argument("--dry-run", action="store_true", help="명령만 출력, 실행 안 함")
    args = ap.parse_args()

    base, record = load_configs(CONFIG_DIR)
    if args.action == "record":
        cmd_record(args, base, record)


if __name__ == "__main__":
    main()
