import argparse
import json
import time
import torch
import psutil
import numpy as np
from orin.lerobot.policies.smolvla import SmolVLAPolicy
from orin.lerobot.policies.smolvla import make_smolvla_pre_post_processors

# Device
DEVICE = "cuda"

# Dummy input spec (from inference_baseline.py)
def make_dummy_obs(device):
    return {
        "observation": {
            "images": {
                "camera1": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=device),
                "camera2": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=device),
                "camera3": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=device),
            },
            "state": torch.zeros((1, 6), dtype=torch.float32, device=device),
        },
        "language_instruction": ["Pick up the cube and place it in the box."]
    }

def main():
    parser = argparse.ArgumentParser(description="Measure SmolVLA inference latency and RAM usage.")
    parser.add_argument("--num-steps", type=int, default=10, help="Number of steps to measure.")
    parser.add_argument("--warmup", type=int, default=10, help="Number of warmup steps.")
    parser.add_argument("--repeats", type=int, default=50, help="Number of repeats for statistics.")
    parser.add_argument("--output-json", type=str, required=True, help="Path to output JSON file.")
    args = parser.parse_args()

    # Model loading
    policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")
    pre, post = make_smolvla_pre_post_processors(policy.config)

    obs = make_dummy_obs(DEVICE)
    obs_proc = pre(obs)

    # Warmup
    for _ in range(args.warmup):
        with torch.no_grad():
            _ = policy.select_action(obs_proc)
            torch.cuda.synchronize()

    # Latency and RAM measurement
    latencies = []
    process = psutil.Process()
    ram_peaks = []
    for _ in range(args.repeats):
        step_latencies = []
        ram_peak = 0
        for _ in range(args.num_steps):
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.no_grad():
                _ = policy.select_action(obs_proc)
                torch.cuda.synchronize()
            end = time.perf_counter()
            step_latencies.append(end - start)
            ram_now = process.memory_info().rss
            if ram_now > ram_peak:
                ram_peak = ram_now
        latencies.extend(step_latencies)
        ram_peaks.append(ram_peak)

    latencies_np = np.array(latencies)
    p50 = float(np.percentile(latencies_np, 50))
    p95 = float(np.percentile(latencies_np, 95))
    ram_peak = int(max(ram_peaks))

    result = {
        "num_steps": args.num_steps,
        "warmup": args.warmup,
        "repeats": args.repeats,
        "latency_p50": p50,
        "latency_p95": p95,
        "ram_peak": ram_peak,
        "latencies": latencies_np.tolist(),
    }

    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Latency p50: {p50:.6f} s, p95: {p95:.6f} s, RAM peak: {ram_peak/1024/1024:.2f} MB")

if __name__ == "__main__":
    main()
