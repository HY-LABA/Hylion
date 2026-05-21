#!/usr/bin/env python3
"""prof_computer/finetune/leftarm_v2/branches/004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180/run_train.py
  — 분기 004 학습 wrapper.

분기 식별: 004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180
  - 매트릭스: A2 (LoRA r=16, target=all-linear)
  - 003 baseline + wrist 180° 회전 단일 변수 변경

vs 003 변경 변수 1개:
  1) wrist camera 학습 시점 180° 회전 적용 (사전학습 분포 정합)

가설 근거:
  - research_wrist_orientation_2026-05-21.md (verdict: NEEDS_INVESTIGATION)
  - VLM (SigLIP) 의 natural image 사전학습 prior 가 *상하반전 입력* 에 약함
  - lerobot 의 Cv2Rotation 파라미터 = 수집 단계 보정 표준 워크플로우 정황

구현 경로 (research 결과 반영):
  - lerobot upstream 의 image_transforms API 는 *카메라별 selective* 미지원
  - custom_train.py 가 LeRobotDataset.__getitem__ 에 monkey-patch 로 wrist 만 180° 회전 적용
  - lerobot upstream 무수정 (옵션 B 보존). lerobot-train 의 모든 흐름 (PEFT, accelerate,
    wandb, ckpt, scheduler) 무변화 재사용 — patch 는 dataset layer 만 변경
  - 본 wrapper 는 003 의 subprocess 패턴을 변형:
    003: `accelerate launch lerobot-train ...`
    004: `accelerate launch custom_train.py ...` (custom_train.py 가 patch 적용 후 lerobot_train.train() 호출)

사용 (분기 디렉터리에서 직접 실행):
  source <prof_computer>/.venv_arm_finetune/bin/activate
  cd <prof_computer>/finetune/leftarm_v2/branches/004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180
  python run_train.py train --pass smoke           # 100 step + 100ep subset 검증
  python run_train.py train --pass full            # 120000 step + 310ep 전체 본 학습 (~16h)
  python run_train.py train --pass full --dry-run  # 명령만 출력
  python run_train.py train --pass 2a              # 비교용 100ep subset

공용 자원 (상위 디렉터리):
  - _lib.py (die, expand_path)
  - config/base_config.yaml (식별·계정·하드웨어)

분기 고유 (본 디렉터리):
  - train_config.yaml (full 본 학습 — 310ep 전체, 120K step)
  - train_config_smoke.yaml (smoke 100 step)
  - custom_train.py (LeRobotDataset monkey-patch + lerobot_train.train() 호출)

학습 산출: ~/prof_computer_runs/<run_name>/  (run_name prefix: leftarm_v2_004_<pass>_<ts>)
비교 대상:
  - 003 (branches/003_a2_310ep_empty1_sched_sync_bf16_b6/) — 본 분기의 baseline (8/8 = 100%)
결정 근거: prof_computer/docs/model_config.md, research_wrist_orientation_2026-05-21.md
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# ── 공용 자원 import (상위 디렉터리의 _lib.py) ──
SCRIPT_DIR = Path(__file__).resolve().parent              # branches/003_a2_310ep_empty1_sched_sync/
LEFTARM_V2_DIR = SCRIPT_DIR.parent.parent                 # prof_computer/finetune/leftarm_v2/
sys.path.insert(0, str(LEFTARM_V2_DIR))
from _lib import die, expand_path                         # noqa: E402

# ── 경로 ──
BRANCH_DIR = SCRIPT_DIR                                   # 본 분기 디렉터리 (train_config.yaml 위치)
SHARED_CONFIG_DIR = LEFTARM_V2_DIR / "config"             # base_config.yaml 위치
TAG = "[004_a2_310ep_empty1_sched_sync_bf16_b6_wrist_rot180]"


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
    # 본 분기는 pass 3 종류:
    #   smoke : 100 step + 100ep subset (빠른 환경 검증)
    #   2a    : 본 학습 step + 100ep subset (001 과 데이터 영역 동일 — 비교용, 거의 사용 X)
    #   full  : 본 학습 step + 310ep 전체 (003 의 핵심 — 데이터 확장 효과 측정)
    if args.pass_name in ("smoke", "2a"):
        sub = train.get("dataset_subset_2a") or {}
        ranges = sub.get("episode_ranges_inclusive")
        if not ranges:
            die("train_config(_smoke).yaml.dataset_subset_2a.episode_ranges_inclusive 미설정")
        episodes = _expand_episode_ranges(ranges)
    elif args.pass_name == "full":
        episodes = None   # 전체 dataset (310ep)
    else:
        die(f"--pass 는 smoke | 2a | full (현재: {args.pass_name})")

    # ── 식별·저장위치·계정 (base_config) ──
    hf_repo_id = base["hf_repo_id"]
    dataset_root = expand_path(base["paths"]["dataset_local"], "paths.dataset_local")
    output_root = expand_path(base["paths"]["output_root"], "paths.output_root")
    accounts = base.get("accounts") or {}

    # ── run name + output_dir — 003 분기 prefix ──
    # 분기명 동적 식별 — 본 wrapper 가 위치한 디렉터리명 = 분기명
    branch_name = SCRIPT_DIR.name   # 예: 003_a2_310ep_empty1_sched_sync_bf16_smoke
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_name = f"leftarm_v2_{branch_name}_{args.pass_name}_{ts}"
    output_dir = output_root / run_name

    # ── 필수 train 필드 검증 ──
    # 004 신규: wrist_rotation_deg 추가
    required = ("policy_path", "method", "batch_size", "steps",
                "num_workers", "save_freq", "log_freq", "wandb_enable",
                "device", "push_to_hub",
                "dataset_return_uint8", "prefetch_factor", "persistent_workers",
                "video_backend", "empty_cameras", "scheduler_decay_steps",
                "wrist_rotation_deg")
    for k in required:
        if train.get(k) is None:
            die(f"train_config.yaml.{k} 미설정")

    # ── 004 분기 sanity check: wrist_rotation_deg 는 180 만 지원 ──
    # (custom_train.py 의 monkey-patch 가 180° 고정. 다른 각도 지원하려면 patch 일반화 필요)
    if train["wrist_rotation_deg"] != 180:
        die(f"본 분기는 wrist_rotation_deg=180 만 지원 (현재: {train['wrist_rotation_deg']}). "
            f"다른 각도 시도 시 custom_train.py 의 _ROTATION_DEG 갱신 + 분기명 변경 필요.")

    # ── rename_map: dataset 카메라 키 → smolvla 입력 키 (camera1, camera2, ...) ──
    cam_names = list(base["cameras"].keys())
    rename_pairs = [(f"observation.images.{name}", f"observation.images.camera{i+1}")
                    for i, name in enumerate(cam_names)]
    rename_map_str = "{" + ", ".join(f'"{k}":"{v}"' for k, v in rename_pairs) + "}"

    # ── lerobot-train 명령 구성 — 003 의 핵심 변수 3개 유지 + 004 신규:
    #   --policy.empty_cameras (002 와 공유)
    #   --policy.scheduler_decay_steps (003 신규)
    #   episodes 인자 (full 시 미전달 = 310ep 전체)
    # ── 004 변경: lerobot-train binary 직접 호출 대신 custom_train.py 경유 ──
    # 이유: custom_train.py 가 LeRobotDataset.__getitem__ 에 wrist 180° rotation patch 적용 후
    #       lerobot.scripts.lerobot_train.train() 호출. lerobot-train CLI 와 동일한 인자 받음
    #       (@parser.wrap() 데코레이터가 sys.argv 파싱).
    # ── accelerate launch 경로 — bf16 mixed precision 활성화 (003 동일) ──
    custom_train_py = str(SCRIPT_DIR / "custom_train.py")
    if not Path(custom_train_py).exists():
        die(f"custom_train.py 없음: {custom_train_py}")

    b = lambda x: str(x).lower()
    cmd = [
        "accelerate", "launch",
        "--mixed_precision=bf16",   # ← 003 동일 — bf16 mixed precision (accelerate autocast)
        "--num_processes=1",
        custom_train_py,            # ← 004 변경 — lerobot-train binary 대신 custom_train.py
        f"--policy.path={train['policy_path']}",
        f"--policy.device={train['device']}",
        f"--policy.push_to_hub={b(train['push_to_hub'])}",
        f"--policy.empty_cameras={train['empty_cameras']}",
        f"--policy.scheduler_decay_steps={train['scheduler_decay_steps']}",
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
        # --policy.use_amp 제거 — accelerate 가 mixed_precision=bf16 로 통제
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

    # ── PEFT (LoRA) — 001 과 동일 ──
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
        pass
    else:
        die(f"train_config.yaml.method 는 lora | full (현재: {train['method']!r})")

    # ── 요약 출력 ──
    if episodes is None:
        subset_str = "전체 dataset (full — 310ep 추정)"
    else:
        subset_str = (f"{len(episodes)} ep "
                      f"(index {min(episodes)}~{max(episodes)})")
    lora_str = ""
    if train["method"] == "lora":
        lora_str = f" (r={train['lora']['r']}, {train['lora']['target_modules']})"

    print(f"{TAG} pass     : {args.pass_name}")
    print(f"{TAG} 분기     : 004 (--policy.empty_cameras={train['empty_cameras']} "
          f"+ --policy.scheduler_decay_steps={train['scheduler_decay_steps']} "
          f"+ wrist_rotation_deg={train['wrist_rotation_deg']}° via custom_train.py monkey-patch)")
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

    # accelerate launch + custom_train.py 의존성 검증
    if not shutil.which("accelerate"):
        die("accelerate 없음 — venv 활성화 확인: "
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

    print(f"{TAG} custom_train.py 실행 (LeRobotDataset wrist patch 적용 후 lerobot train() 호출)...\n")
    subprocess.run(cmd, env=env, check=True)

    # ── 학습 후 wandb system metrics 자동 CSV export ──
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
        description="leftarm_v2 학습 래퍼 — 004 분기 (003 + wrist 180° rotation)")
    sub = ap.add_subparsers(dest="action", required=True)
    tr = sub.add_parser("train", help="custom_train.py 경유 학습 실행")
    tr.add_argument("--pass", dest="pass_name", required=True,
                    choices=["smoke", "2a", "full"],
                    help="smoke (100 step + 100ep subset 환경 검증) | 2a (본 학습 step + 100ep subset 비교용) | full (본 학습 step + 310ep 전체 — 004 핵심)")
    tr.add_argument("--dry-run", action="store_true",
                    help="명령만 출력, 실행 안 함")
    args = ap.parse_args()

    # base_config 는 공용 (상위 디렉터리), train_config 는 분기 고유 (본 디렉터리)
    base = _load_yaml(SHARED_CONFIG_DIR / "base_config.yaml")
    train_yaml = "train_config_smoke.yaml" if args.pass_name == "smoke" else "train_config.yaml"
    train = _load_yaml(BRANCH_DIR / train_yaml)
    if args.action == "train":
        cmd_train(args, base, train)


if __name__ == "__main__":
    main()
