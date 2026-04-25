"""Sim-to-sim: Run Hylion v6 IsaacLab policy in MuJoCo.

학습 환경 (IsaacLab/PhysX) 에서 훈련된 RSL-RL policy를
MuJoCo에서 그대로 실행하는 sim-to-sim validation 스크립트.

필요 파일:
  - checkpoints/biped/stage_d5_hylion_v6/best.pt  (or --ckpt_path로 지정)
  - sim/isaaclab/robot/hylion_v6.urdf              (MuJoCo가 URDF 로드)

obs 구성 (45-dim, IsaacLab env_cfg.py와 동일 순서):
  [0:3]   velocity_commands  (lin_vel_x, lin_vel_y, ang_vel_z)
  [3:6]   base_ang_vel
  [6:9]   projected_gravity
  [9:21]  joint_pos_rel  (12 leg joints, default offset 제거)
  [21:33] joint_vel_rel  (12 leg joints)
  [33:45] last_action    (12)

action (12-dim):
  JointPositionActionCfg(scale=0.25, use_default_offset=True)
  → target_pos = default_pos + action * 0.25

Physics:
  sim_dt = 1/200 Hz, decimation = 8  →  control_freq = 25 Hz
"""

import argparse
import os
import sys
import numpy as np

# ─────────────────────────────────────────────
# 의존 패키지: mujoco, torch, rsl_rl
# pip install mujoco torch rsl-rl-lib
# ─────────────────────────────────────────────

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DEFAULT_CKPT = os.path.join(REPO_ROOT, "checkpoints/biped/stage_d5_hylion_v6/best.pt")
DEFAULT_URDF = os.path.join(REPO_ROOT, "sim/isaaclab/robot/hylion_v6.urdf")

# IsaacLab env_cfg.py에서 정의된 다리 joint 순서 (preserve_order=True)
LEG_JOINTS = [
    "leg_left_hip_roll_joint",
    "leg_left_hip_yaw_joint",
    "leg_left_hip_pitch_joint",
    "leg_left_knee_pitch_joint",
    "leg_left_ankle_pitch_joint",
    "leg_left_ankle_roll_joint",
    "leg_right_hip_roll_joint",
    "leg_right_hip_yaw_joint",
    "leg_right_hip_pitch_joint",
    "leg_right_knee_pitch_joint",
    "leg_right_ankle_pitch_joint",
    "leg_right_ankle_roll_joint",
]

# robot_cfg.py InitialStateCfg 기준 default joint positions (use_default_offset=True)
DEFAULT_JOINT_POS = np.array([
    0.0,   # leg_left_hip_roll_joint
    0.0,   # leg_left_hip_yaw_joint
    -0.2,  # leg_left_hip_pitch_joint
    0.4,   # leg_left_knee_pitch_joint
    -0.3,  # leg_left_ankle_pitch_joint
    0.0,   # leg_left_ankle_roll_joint
    0.0,   # leg_right_hip_roll_joint
    0.0,   # leg_right_hip_yaw_joint
    -0.2,  # leg_right_hip_pitch_joint
    0.4,   # leg_right_knee_pitch_joint
    -0.3,  # leg_right_ankle_pitch_joint
    0.0,   # leg_right_ankle_roll_joint
], dtype=np.float32)

ACTION_SCALE = 0.25   # JointPositionActionCfg scale
CONTROL_HZ   = 25     # decimation=8, physics=200Hz
SIM_DT       = 1.0 / 200.0
N_SUBSTEPS   = 8      # decimation


def build_mujoco_model(urdf_path: str):
    """URDF → MuJoCo model 변환 후 로드."""
    try:
        import mujoco
    except ImportError:
        raise ImportError("mujoco 패키지가 없습니다. pip install mujoco")

    model = mujoco.MjModel.from_xml_path(urdf_path)
    data  = mujoco.MjData(model)
    return model, data


def get_joint_indices(model, joint_names: list[str]) -> list[int]:
    """joint 이름 → MuJoCo qpos 인덱스 리스트 반환."""
    import mujoco
    indices = []
    for name in joint_names:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid < 0:
            raise ValueError(f"Joint '{name}' not found in MuJoCo model.")
        indices.append(model.jnt_qposadr[jid])
    return indices


def get_joint_vel_indices(model, joint_names: list[str]) -> list[int]:
    """joint 이름 → MuJoCo qvel 인덱스 리스트 반환."""
    import mujoco
    indices = []
    for name in joint_names:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid < 0:
            raise ValueError(f"Joint '{name}' not found in MuJoCo model.")
        indices.append(model.jnt_dofadr[jid])
    return indices


def load_policy(ckpt_path: str, obs_dim: int = 45, act_dim: int = 12, device: str = "cpu"):
    """RSL-RL checkpoint에서 actor network만 추출."""
    try:
        import torch
    except ImportError:
        raise ImportError("torch 패키지가 없습니다. pip install torch")

    ckpt = torch.load(ckpt_path, map_location=device)

    # RSL-RL checkpoint 구조: {"model_state_dict": {...}} 또는 직접 state_dict
    if "model_state_dict" in ckpt:
        state = ckpt["model_state_dict"]
    elif "actor_critic" in ckpt:
        state = ckpt["actor_critic"]
    else:
        state = ckpt

    # actor MLP: actor_hidden_dims=[256, 128, 128], activation=elu
    import torch.nn as nn

    class ActorMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(obs_dim, 256), nn.ELU(),
                nn.Linear(256, 128),    nn.ELU(),
                nn.Linear(128, 128),    nn.ELU(),
                nn.Linear(128, act_dim),
            )

        def forward(self, x):
            return self.net(x)

    # RSL-RL ActorCritic weight 키 패턴:
    #   actor.0.weight, actor.0.bias, actor.2.weight, ...
    actor_state = {}
    for k, v in state.items():
        if k.startswith("actor."):
            # "actor.0.weight" → "net.0.weight"
            new_key = "net." + k[len("actor."):]
            actor_state[new_key] = v

    model = ActorMLP().to(device)
    missing, unexpected = model.load_state_dict(actor_state, strict=False)
    if missing:
        print(f"[WARN] Missing keys in actor: {missing[:5]}")
    return model


def projected_gravity_vec(quat_wxyz: np.ndarray) -> np.ndarray:
    """quaternion (w,x,y,z) → base frame에서의 gravity unit vector."""
    w, x, y, z = quat_wxyz
    # world gravity = (0, 0, -1)
    # R^T @ g  (body←world rotation)
    gx = -2.0 * (x * z - w * y)
    gy = -2.0 * (y * z + w * x)
    gz = -(1.0 - 2.0 * (x * x + y * y))
    return np.array([gx, gy, gz], dtype=np.float32)


def run(args):
    import mujoco
    import mujoco.viewer
    import torch

    # ── 모델 로드 ──
    print(f"[SIM2SIM] Loading MuJoCo model: {args.urdf}")
    model, data = build_mujoco_model(args.urdf)
    model.opt.timestep = SIM_DT

    qpos_ids = get_joint_indices(model, LEG_JOINTS)
    qvel_ids = get_joint_vel_indices(model, LEG_JOINTS)

    # actuator index (LEG_JOINTS 순서)
    act_ids = []
    for name in LEG_JOINTS:
        aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
        if aid < 0:
            # fallback: actuator 이름 = joint 이름 + "_actuator"
            aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name + "_actuator")
        act_ids.append(aid)

    # ── 초기 자세 ──
    mujoco.mj_resetData(model, data)
    for i, qi in enumerate(qpos_ids):
        data.qpos[qi] = DEFAULT_JOINT_POS[i]
    data.qpos[2] = 0.95   # base height (약 0.95m)
    mujoco.mj_forward(model, data)

    # ── policy 로드 ──
    print(f"[SIM2SIM] Loading policy: {args.ckpt}")
    device = args.device
    policy = load_policy(args.ckpt, obs_dim=45, act_dim=12, device=device)
    policy.eval()

    # ── 명령 ──
    cmd = np.array([args.vx, args.vy, args.wz], dtype=np.float32)
    print(f"[SIM2SIM] Command: vx={args.vx} vy={args.vy} wz={args.wz}")
    print(f"[SIM2SIM] Control Hz: {CONTROL_HZ}, substeps: {N_SUBSTEPS}")

    last_action = np.zeros(12, dtype=np.float32)
    total_steps = int(args.duration * CONTROL_HZ)

    def get_obs() -> np.ndarray:
        # [0:3]  velocity_commands
        o_cmd = cmd.copy()
        # [3:6]  base_ang_vel (body frame)
        o_angvel = data.sensor("imu_gyro").data.astype(np.float32) if "imu_gyro" in [model.sensor(i).name for i in range(model.nsensor)] else data.qvel[3:6].astype(np.float32)
        # [6:9]  projected_gravity
        quat = data.qpos[3:7].astype(np.float32)          # (x,y,z,w) MuJoCo 순서
        quat_wxyz = np.array([quat[3], quat[0], quat[1], quat[2]])
        o_grav = projected_gravity_vec(quat_wxyz)
        # [9:21] joint_pos_rel
        o_qpos = np.array([data.qpos[qi] for qi in qpos_ids], dtype=np.float32) - DEFAULT_JOINT_POS
        # [21:33] joint_vel_rel
        o_qvel = np.array([data.qvel[vi] for vi in qvel_ids], dtype=np.float32)
        # [33:45] last_action
        o_act  = last_action.copy()

        obs = np.concatenate([o_cmd, o_angvel, o_grav, o_qpos, o_qvel, o_act])
        return obs.astype(np.float32)

    # ── 실행 ──
    print(f"[SIM2SIM] Running {total_steps} steps ({args.duration}s) ...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        for step in range(total_steps):
            obs_np = get_obs()
            obs_t  = torch.tensor(obs_np, dtype=torch.float32, device=device).unsqueeze(0)

            with torch.inference_mode():
                action_t = policy(obs_t)
            action_np = action_t.squeeze(0).cpu().numpy()
            # NaN/Inf 방어
            action_np = np.nan_to_num(action_np, nan=0.0, posinf=10.0, neginf=-10.0)
            last_action[:] = action_np

            # target position = default + action * scale
            target_pos = DEFAULT_JOINT_POS + action_np * ACTION_SCALE

            # actuator ctrl 설정 후 N_SUBSTEPS 시뮬레이션
            for vi, aid in enumerate(act_ids):
                if aid >= 0:
                    data.ctrl[aid] = target_pos[vi]
            for _ in range(N_SUBSTEPS):
                mujoco.mj_step(model, data)

            viewer.sync()

            # 넘어짐 감지: base height < 0.3m
            base_z = data.qpos[2]
            if base_z < 0.3:
                print(f"[SIM2SIM] FALL detected at step {step} (base_z={base_z:.3f})")
                break

        print(f"[SIM2SIM] Done. Survived {step+1}/{total_steps} steps.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hylion v6 sim-to-sim (IsaacLab → MuJoCo)")
    parser.add_argument("--ckpt",     type=str, default=DEFAULT_CKPT,  help="best.pt 경로")
    parser.add_argument("--urdf",     type=str, default=DEFAULT_URDF,  help="hylion_v6.urdf 경로")
    parser.add_argument("--vx",       type=float, default=0.3,         help="lin_vel_x 명령 (m/s)")
    parser.add_argument("--vy",       type=float, default=0.0,         help="lin_vel_y 명령 (m/s)")
    parser.add_argument("--wz",       type=float, default=0.0,         help="ang_vel_z 명령 (rad/s)")
    parser.add_argument("--duration", type=float, default=10.0,        help="시뮬레이션 시간 (s)")
    parser.add_argument("--device",   type=str,   default="cpu",       help="torch device")
    args = parser.parse_args()

    if not os.path.isfile(args.ckpt):
        print(f"[ERROR] Checkpoint not found: {args.ckpt}")
        sys.exit(1)
    if not os.path.isfile(args.urdf):
        print(f"[ERROR] URDF not found: {args.urdf}")
        sys.exit(1)

    run(args)
