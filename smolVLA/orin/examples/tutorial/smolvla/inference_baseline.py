import torch
from orin.lerobot.policies.smolvla import SmolVLAPolicy
from orin.lerobot.policies.smolvla import make_smolvla_pre_post_processors

# Device
DEVICE = "cuda"

# Model loading
policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")

# Dummy input spec (from current_task.md)
# Camera keys: observation.images.camera1, camera2, camera3
# Image shape: [1, 3, 480, 640] (B=1, C=3, H=480, W=640)
# State key: observation.state, shape: [1, 6]
# Language instruction: "Pick up the cube and place it in the box."

obs = {
    "observation": {
        "images": {
            "camera1": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=DEVICE),
            "camera2": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=DEVICE),
            "camera3": torch.zeros((1, 3, 480, 640), dtype=torch.float32, device=DEVICE),
        },
        "state": torch.zeros((1, 6), dtype=torch.float32, device=DEVICE),
    },
    "language_instruction": ["Pick up the cube and place it in the box."]
}

# Pre/post-processors
pre, post = make_smolvla_pre_post_processors(policy.config)

# Preprocess
obs_proc = pre(obs)

# Inference
with torch.no_grad():
    action = policy.select_action(obs_proc)

# Postprocess
if hasattr(action, "cpu"):
    action = action.cpu()
action = post(action)

print("Action shape:", action.shape)
print("Action dtype:", action.dtype)
print("Action min:", action.min().item())
print("Action max:", action.max().item())
