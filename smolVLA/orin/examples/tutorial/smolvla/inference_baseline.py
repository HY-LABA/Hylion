"""smolvla_base 사전학습 모델 forward baseline 검증.

03_smolvla_test_on_orin TODO-03 의 책임 — 사전학습 분포에 미러링된 입력으로
1회 forward 가 정상 동작하는지 확인. 카메라 키 / state dim 등은
model.config.input_features 에서 자동 추출하여 사전학습 분포와 일치 보장.

기본 동작 검증만 수행 — latency / VRAM 정량 측정은 measure_latency.py 가 책임.
"""

import numpy as np
import torch

from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.policies import make_pre_post_processors
from lerobot.policies.utils import prepare_observation_for_inference

DEVICE = "cuda"
MODEL_ID = "lerobot/smolvla_base"
TASK = "Pick up the cube and place it in the box."
ROBOT_TYPE = "so100_follower"

print(f"[load] {MODEL_ID}")
policy = SmolVLAPolicy.from_pretrained(MODEL_ID).to(DEVICE)
policy.eval()

print("[input_features]")
for k, v in policy.config.input_features.items():
    print(f"  {k}: {v}")

dummy_obs: dict[str, np.ndarray] = {}
for key, feat in policy.config.input_features.items():
    if "image" in key:
        dummy_obs[key] = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    else:
        dim = len(feat.names) if hasattr(feat, "names") and feat.names else 6
        dummy_obs[key] = np.random.rand(dim).astype(np.float32)

print(f"[dummy_obs keys] {list(dummy_obs.keys())}")

preprocess, postprocess = make_pre_post_processors(
    policy.config,
    pretrained_path=MODEL_ID,
    preprocessor_overrides={"device_processor": {"device": DEVICE}},
)

obs_tensor = prepare_observation_for_inference(
    dummy_obs, device=DEVICE, task=TASK, robot_type=ROBOT_TYPE
)
obs_tensor = preprocess(obs_tensor)

with torch.inference_mode():
    action = policy.select_action(obs_tensor)

action = postprocess(action)

print(f"Action shape: {tuple(action.shape)}")
print(f"Action dtype: {action.dtype}")
print(f"Action min:   {action.min().item():.6f}")
print(f"Action max:   {action.max().item():.6f}")
