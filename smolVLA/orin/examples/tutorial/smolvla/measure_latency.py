"""smolvla_base Orin latency / RAM(UMA) peak 측정.

03_smolvla_test_on_orin TODO-04 의 책임 — warmup N회 + 측정 N회 forward 로
latency 분포(p50/p95) + RAM peak 측정. num_steps∈{10, 5} 두 설정 비교.

inference_baseline.py 와 입력 미러링 로직을 공유 — model.config.input_features
에서 카메라/상태 키 자동 추출.
"""

import argparse
import json
import time

import numpy as np
import psutil
import torch

from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.policies import make_pre_post_processors
from lerobot.policies.utils import prepare_observation_for_inference

DEVICE = "cuda"
MODEL_ID = "lerobot/smolvla_base"
TASK = "Pick up the cube and place it in the box."
ROBOT_TYPE = "so100_follower"


def make_dummy_obs(input_features):
    obs = {}
    for key, feat in input_features.items():
        if "image" in key:
            obs[key] = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        else:
            dim = len(feat.names) if hasattr(feat, "names") and feat.names else 6
            obs[key] = np.random.rand(dim).astype(np.float32)
    return obs


def main():
    parser = argparse.ArgumentParser(
        description="Measure SmolVLA inference latency and RAM(UMA) peak."
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=10,
        help="Flow matching num_steps (override policy.config.num_steps).",
    )
    parser.add_argument(
        "--warmup", type=int, default=10, help="Number of warmup forward calls."
    )
    parser.add_argument(
        "--repeats", type=int, default=50, help="Number of measured forward calls."
    )
    parser.add_argument(
        "--output-json", type=str, required=True, help="Path to output JSON file."
    )
    args = parser.parse_args()

    print(f"[load] {MODEL_ID}")
    policy = SmolVLAPolicy.from_pretrained(MODEL_ID).to(DEVICE)
    policy.eval()
    policy.config.num_steps = args.num_steps

    preprocess, _ = make_pre_post_processors(
        policy.config,
        pretrained_path=MODEL_ID,
        preprocessor_overrides={"device_processor": {"device": DEVICE}},
    )

    dummy_obs = make_dummy_obs(policy.config.input_features)
    obs_tensor = prepare_observation_for_inference(
        dummy_obs, device=DEVICE, task=TASK, robot_type=ROBOT_TYPE
    )
    obs_tensor = preprocess(obs_tensor)

    print(f"[warmup] {args.warmup} forward calls")
    for _ in range(args.warmup):
        with torch.inference_mode():
            _ = policy.select_action(obs_tensor)
        torch.cuda.synchronize()

    print(f"[measure] {args.repeats} forward calls (num_steps={args.num_steps})")
    process = psutil.Process()
    latencies = []
    ram_peak = 0
    for _ in range(args.repeats):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.inference_mode():
            _ = policy.select_action(obs_tensor)
        torch.cuda.synchronize()
        latencies.append(time.perf_counter() - t0)
        ram_now = process.memory_info().rss
        if ram_now > ram_peak:
            ram_peak = ram_now

    arr = np.asarray(latencies)
    p50 = float(np.percentile(arr, 50))
    p95 = float(np.percentile(arr, 95))

    result = {
        "model_id": MODEL_ID,
        "num_steps": args.num_steps,
        "warmup": args.warmup,
        "repeats": args.repeats,
        "latency_p50_s": p50,
        "latency_p95_s": p95,
        "ram_peak_bytes": int(ram_peak),
        "latencies_s": arr.tolist(),
    }
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

    print(
        f"latency p50: {p50*1000:.2f} ms | p95: {p95*1000:.2f} ms | "
        f"RAM peak: {ram_peak/1024/1024:.2f} MiB"
    )
    print(f"saved: {args.output_json}")


if __name__ == "__main__":
    main()
