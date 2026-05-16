#!/usr/bin/env python3
"""dgx/finetune/leftarm_v2/run_train.py — leftarm_v2 학습 래퍼.

config/{base,train}_config.yaml → lerobot-train 명령 구성·실행.
공용 로직(die, expand_path)은 _lib.py. 모든 인자는 yaml 출처 (하드코딩 없음).

사용:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  python run_train.py train --pass 2a              # 2A: 100ep balanced subset
  python run_train.py train --pass 2a --dry-run    # 명령만 출력
  python run_train.py train --pass 2b              # 2B: 200ep 전체 (M1 완성 후)

학습 산출: ~/smolvla/dgx/outputs/<run_name>/  (flat 컨벤션)
결정 근거: dgx/docs/finetune/leftarm_v2/model_config.md
"""
import argparse
import os
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from _lib import die, expand_path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR / "config"
TAG = "[run_train]"


def _load_yaml(path):
    if not path.exists():
        die(f"config 파일 없음: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _expand_episode_ranges(ranges):
    """[[start, end], ...] inclusive → flat list[int]. 중복·역순 검증."""
    out = []
    for r in ranges:
        if not (isinstance(r, list) and len(r) == 2):
            die(f"episode_ranges_inclusive entry 는 [start, end] 쌍, got: {r!r}")
        start, end = r
        if start > end:
            die(f"episode range start > end: {r}")
        out.extend(range(start, end + 1))
    if len(out) != len(set(out)):
        die("episode ranges 가 중복 index 를 생성 — ranges 조정 필요")
    return out


def _format_episodes_arg(episodes):
    """draccus list 인자 형식: [0,1,2,...] (공백 없음)."""
    return "[" + ",".join(str(e) for e in episodes) + "]"


def cmd_train(args, base, train):
    # ── pass 별 dataset subset ──
    if args.pass_name == "2a":
        sub = train.get("dataset_subset_2a") or {}
        ranges = sub.get("episode_ranges_inclusive")
        if not ranges:
            die("train_config.yaml.dataset_subset_2a.episode_ranges_inclusive 미설정")
        episodes = _expand_episode_ranges(ranges)
    elif args.pass_name == "2b":
        episodes = None   # 전체 dataset
    else:
        die(f"--pass 는 2a | 2b (현재: {args.pass_name})")

    # ── 식별·저장위치·계정 (base_config) ──
    hf_repo_id = base["hf_repo_id"]
    dataset_root = expand_path(base["paths"]["dataset_local"], "paths.dataset_local")
    output_root = expand_path(base["paths"]["output_root"], "paths.output_root")
    accounts = base.get("accounts") or {}

    # ── run name + output_dir (flat 컨벤션) ──
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_name = f"leftarm_v2_{args.pass_name}_{ts}"
    output_dir = output_root / run_name

    # ── 필수 train 필드 검증 ──
    required = ("policy_path", "method", "batch_size", "steps",
                "num_workers", "save_freq", "log_freq", "wandb_enable",
                "device", "push_to_hub",
                "dataset_return_uint8", "prefetch_factor", "persistent_workers",
                "dataset_video_backend")
    for k in required:
        if train.get(k) is None:
            die(f"train_config.yaml.{k} 미설정")

    # ── rename_map: dataset 카메라 키 → smolvla 입력 키 (camera1, camera2, ...) ──
    # smolvla 가 observation.images.camera{N} 형태를 기대 — base_config.cameras 순서로 자동 매핑.
    cam_names = list(base["cameras"].keys())
    rename_pairs = [(f"observation.images.{name}", f"observation.images.camera{i+1}")
                    for i, name in enumerate(cam_names)]
    rename_map_str = "{" + ", ".join(f'"{k}":"{v}"' for k, v in rename_pairs) + "}"

    # ── lerobot-train 명령 구성 ──
    b = lambda x: str(x).lower()
    cmd = [
        "lerobot-train",
        f"--policy.path={train['policy_path']}",
        f"--policy.device={train['device']}",
        f"--policy.push_to_hub={b(train['push_to_hub'])}",
        f"--dataset.repo_id={hf_repo_id}",
        f"--dataset.root={dataset_root}",
        f"--batch_size={train['batch_size']}",
        f"--steps={train['steps']}",
        f"--num_workers={train['num_workers']}",
        f"--prefetch_factor={train['prefetch_factor']}",
        f"--persistent_workers={b(train['persistent_workers'])}",
        f"--save_freq={train['save_freq']}",
        f"--log_freq={train['log_freq']}",
        f"--output_dir={output_dir}",
        f"--job_name={run_name}",
        f"--rename_map={rename_map_str}",
        f"--dataset.return_uint8={b(train['dataset_return_uint8'])}",
        f"--dataset.video_backend={train['dataset_video_backend']}",
        f"--wandb.enable={b(train['wandb_enable'])}",
    ]
    if accounts.get("wandb_project"):
        cmd.append(f"--wandb.project={accounts['wandb_project']}")
    if accounts.get("wandb_entity"):
        cmd.append(f"--wandb.entity={accounts['wandb_entity']}")
    if episodes is not None:
        cmd.append(f"--dataset.episodes={_format_episodes_arg(episodes)}")

    # ── PEFT (LoRA) — peft 인자 주면 활성화, 안 주면 full FT ──
    if train["method"] == "lora":
        lora = train.get("lora") or {}
        if "target_modules" not in lora or "r" not in lora:
            die("method=lora 시 train_config.yaml.lora.{target_modules, r} 필요")
        cmd += [
            "--peft.method_type=LORA",
            f"--peft.target_modules={lora['target_modules']}",
            f"--peft.r={lora['r']}",
        ]
    elif train["method"] == "full":
        pass   # peft 인자 없음 = 전체 weight trainable
    else:
        die(f"train_config.yaml.method 는 lora | full (현재: {train['method']!r})")

    # ── 요약 출력 ──
    if episodes is None:
        subset_str = "전체 dataset (2b)"
    else:
        subset_str = (f"{len(episodes)} ep "
                      f"(index {min(episodes)}~{max(episodes)})")
    lora_str = ""
    if train["method"] == "lora":
        lora_str = f" (r={train['lora']['r']}, {train['lora']['target_modules']})"

    print(f"{TAG} pass     : {args.pass_name}")
    print(f"{TAG} dataset  : {hf_repo_id}")
    print(f"{TAG} subset   : {subset_str}")
    print(f"{TAG} base ckpt: {train['policy_path']}")
    print(f"{TAG} method   : {train['method']}{lora_str}")
    print(f"{TAG} steps    : {train['steps']} / batch {train['batch_size']} / save_freq {train['save_freq']}")
    print(f"{TAG} workers  : {train['num_workers']}")
    print(f"{TAG} wandb    : {train['wandb_enable']}  "
          f"({accounts.get('wandb_entity', '?')} / {accounts.get('wandb_project', '?')})")
    print(f"{TAG} output   : {output_dir}")
    print()
    print(f"{TAG} 구성된 명령:")
    print("  " + " \\\n    ".join(shlex.quote(c) for c in cmd))
    print()

    if args.dry_run:
        print(f"{TAG} --dry-run — 실행하지 않음.")
        return

    if not shutil.which("lerobot-train"):
        die("lerobot-train 없음 — venv 활성화 확인: "
            "source ~/smolvla/dgx/.arm_finetune/bin/activate")

    if output_dir.exists():
        die(f"output_dir 이미 존재: {output_dir}\n"
            f"        → lerobot 이 덮어쓰기 거부함. 다른 run 으로 재시도 (timestamp 자동 차별).")

    # HF_USER 주입 (yaml 의 accounts.hf_user — venv 가 자동 export 안 함)
    env = dict(os.environ)
    hf_user = accounts.get("hf_user")
    if hf_user and not env.get("HF_USER"):
        env["HF_USER"] = hf_user

    output_dir.parent.mkdir(parents=True, exist_ok=True)

    print(f"{TAG} lerobot-train 실행...\n")
    subprocess.run(cmd, env=env, check=True)


def main():
    ap = argparse.ArgumentParser(
        description="leftarm_v2 학습 래퍼 (config → lerobot-train)")
    sub = ap.add_subparsers(dest="action", required=True)
    tr = sub.add_parser("train", help="lerobot-train 실행")
    tr.add_argument("--pass", dest="pass_name", required=True,
                    choices=["2a", "2b"],
                    help="2a (100ep balanced subset) | 2b (200ep 전체)")
    tr.add_argument("--dry-run", action="store_true",
                    help="명령만 출력, 실행 안 함")
    args = ap.parse_args()

    base = _load_yaml(CONFIG_DIR / "base_config.yaml")
    train = _load_yaml(CONFIG_DIR / "train_config.yaml")
    if args.action == "train":
        cmd_train(args, base, train)


if __name__ == "__main__":
    main()
