#!/usr/bin/env python3
"""prof_computer/finetune/leftarm_v2/run_train_camera_empty.py — empty_cameras 검증 분기 wrapper.

run_train.py 의 분리 entry. 단일 변수 (`empty_cameras`) 만 다른 별도 학습 경로:

검증 가설 (2026-05-18):
  - base smolvla 의 config 가 camera1/2/3 3 cam 으로 사전학습됨 (HF Hub config.json 확인)
  - 우리 dataset = top, wrist 2 cam (rename → camera1, camera2)
  - M1.5 학습 시 camera3 슬롯이 `missing_img_keys` 잡혔으나 `empty_cameras=0` 이라
    `_prepare_images()` 의 zero-pad loop 즉시 break → vision encoder 가 2 cam 만 입력 받음
  - = base 3 cam 분포와 *형식 mismatch*
  - empty_cameras=1 로 두면 missing camera3 슬롯을 -1 padded image + mask 0 으로 zero-fill →
    base 의 3 cam 형식 정합 회복

본 분기는 M1.5 와 *단일 변수 (empty_cameras 0→1)* 만 다른 학습:
  - config: train_config_camera_empty.yaml + train_config_camera_empty_smoke.yaml
  - output_dir prefix: `leftarm_v2_camera_empty_2a_pc_<ts>` (M1.5 ckpt 와 식별 분리)
  - run_name 동일 prefix → wandb 에서 검색 분리

사용 (M1.5 와 동일 venv):
  source <prof_computer>/.venv_arm_finetune/bin/activate
  python run_train_camera_empty.py train --pass smoke           # 100 step 검증
  python run_train_camera_empty.py train --pass 2a              # 75000 step 본 학습
  python run_train_camera_empty.py train --pass 2a --dry-run    # 명령만 출력

비교 대상: M1.5 (run_train.py + train_config.yaml, empty_cameras 미명시 = 0)
  - 동일 dataset (100ep balanced), 동일 LoRA (r=16, all-linear), 동일 batch/steps/optimizer
  - 차이: 본 분기만 --policy.empty_cameras=1

결정 근거: prof_computer/docs/model_config.md + 본 사이클 대화 (research_empty_cameras_2026-05-18.md)
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
TAG = "[run_train_camera_empty]"


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
    if args.pass_name in ("2a", "smoke"):
        sub = train.get("dataset_subset_2a") or {}
        ranges = sub.get("episode_ranges_inclusive")
        if not ranges:
            die("train_config(_smoke).yaml.dataset_subset_2a.episode_ranges_inclusive 미설정")
        episodes = _expand_episode_ranges(ranges)
    elif args.pass_name == "2b":
        episodes = None
    else:
        die(f"--pass 는 smoke | 2a | 2b (현재: {args.pass_name})")

    # ── 식별·저장위치·계정 (base_config) ──
    hf_repo_id = base["hf_repo_id"]
    dataset_root = expand_path(base["paths"]["dataset_local"], "paths.dataset_local")
    output_root = expand_path(base["paths"]["output_root"], "paths.output_root")
    accounts = base.get("accounts") or {}

    # ── run name + output_dir — camera_empty 분기 prefix 로 M1.5 와 식별 분리 ──
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_name = f"leftarm_v2_camera_empty_{args.pass_name}_pc_{ts}"
    output_dir = output_root / run_name

    # ── 필수 train 필드 검증 (empty_cameras 추가) ──
    required = ("policy_path", "method", "batch_size", "steps",
                "num_workers", "save_freq", "log_freq", "wandb_enable",
                "device", "push_to_hub",
                "dataset_return_uint8", "prefetch_factor", "persistent_workers",
                "video_backend", "empty_cameras")
    for k in required:
        if train.get(k) is None:
            die(f"train_config_camera_empty.yaml.{k} 미설정")

    # ── rename_map: dataset 카메라 키 → smolvla 입력 키 (camera1, camera2, ...) ──
    cam_names = list(base["cameras"].keys())
    rename_pairs = [(f"observation.images.{name}", f"observation.images.camera{i+1}")
                    for i, name in enumerate(cam_names)]
    rename_map_str = "{" + ", ".join(f'"{k}":"{v}"' for k, v in rename_pairs) + "}"

    # ── lerobot-train 명령 구성 — --policy.empty_cameras 추가가 M1.5 와의 단일 차이 ──
    b = lambda x: str(x).lower()
    cmd = [
        "lerobot-train",
        f"--policy.path={train['policy_path']}",
        f"--policy.device={train['device']}",
        f"--policy.push_to_hub={b(train['push_to_hub'])}",
        f"--policy.empty_cameras={train['empty_cameras']}",   # ← 본 분기의 단일 변수
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
        f"--policy.use_amp={b(train.get('use_amp', False))}",
        f"--dataset.return_uint8={b(train['dataset_return_uint8'])}",
        f"--dataset.video_backend={train['video_backend']}",
        f"--wandb.enable={b(train['wandb_enable'])}",
    ]
    if accounts.get("wandb_project"):
        cmd.append(f"--wandb.project={accounts['wandb_project']}")
    if accounts.get("wandb_entity"):
        cmd.append(f"--wandb.entity={accounts['wandb_entity']}")
    if episodes is not None:
        cmd.append(f"--dataset.episodes={_format_episodes_arg(episodes)}")

    # ── PEFT (LoRA) — M1.5 와 동일 ──
    if train["method"] == "lora":
        lora = train.get("lora") or {}
        if "target_modules" not in lora or "r" not in lora:
            die("method=lora 시 train_config_camera_empty.yaml.lora.{target_modules, r} 필요")
        cmd += [
            "--peft.method_type=LORA",
            f"--peft.target_modules={lora['target_modules']}",
            f"--peft.r={lora['r']}",
        ]
    elif train["method"] == "full":
        pass
    else:
        die(f"train_config_camera_empty.yaml.method 는 lora | full (현재: {train['method']!r})")

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
    print(f"{TAG} 분기     : camera_empty (--policy.empty_cameras={train['empty_cameras']})")
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
            "source <prof_computer>/.venv_arm_finetune/bin/activate")

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

    # ── 학습 후 wandb system metrics 자동 CSV export (run_train.py 와 동일) ──
    if not train.get("wandb_enable", False):
        return
    _export_wandb_metrics(run_name, accounts, output_dir)


def _export_wandb_metrics(run_name, accounts, output_dir):
    """wandb run 의 system metrics + scalar history 를 output_dir/metrics.csv 로 저장."""
    csv_path = output_dir / "metrics.csv"
    try:
        import wandb
        api = wandb.Api()
        entity = accounts.get("wandb_entity")
        project = accounts.get("wandb_project")
        if not (entity and project):
            print(f"{TAG} wandb entity/project 미설정 — metrics export skip")
            return
        runs = api.runs(f"{entity}/{project}", filters={"display_name": run_name})
        run = next(iter(runs), None)
        if run is None:
            print(f"{TAG} wandb run '{run_name}' 미발견 — metrics export skip")
            return
        hist = run.history(samples=10000, pandas=True)
        sys_hist = run.history(stream="events", samples=10000, pandas=True)
        if not hist.empty:
            hist.to_csv(csv_path.with_suffix(".scalar.csv"), index=False)
        if not sys_hist.empty:
            sys_hist.to_csv(csv_path.with_suffix(".system.csv"), index=False)
        print(f"{TAG} wandb metrics → {csv_path.with_suffix('.scalar.csv').name}, "
              f"{csv_path.with_suffix('.system.csv').name}")
    except Exception as e:
        print(f"{TAG} wandb metrics export 실패 (학습엔 영향 X): {e}")


def main():
    ap = argparse.ArgumentParser(
        description="leftarm_v2 학습 래퍼 — empty_cameras 검증 분기 (run_train.py 와 단일 변수 차이)")
    sub = ap.add_subparsers(dest="action", required=True)
    tr = sub.add_parser("train", help="lerobot-train 실행")
    tr.add_argument("--pass", dest="pass_name", required=True,
                    choices=["smoke", "2a", "2b"],
                    help="smoke (100 step 환경 검증) | 2a (100ep balanced subset) | 2b (200ep 전체)")
    tr.add_argument("--dry-run", action="store_true",
                    help="명령만 출력, 실행 안 함")
    args = ap.parse_args()

    base = _load_yaml(CONFIG_DIR / "base_config.yaml")
    # 본 분기 전용 yaml — smoke 와 2a/2b 분리
    train_yaml = ("train_config_camera_empty_smoke.yaml" if args.pass_name == "smoke"
                  else "train_config_camera_empty.yaml")
    train = _load_yaml(CONFIG_DIR / train_yaml)
    if args.action == "train":
        cmd_train(args, base, train)


if __name__ == "__main__":
    main()
