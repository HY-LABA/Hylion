# BHL(Berkeley Humanoid Lite) 레퍼런스 코드 작동 흐름

> **대상 코드**
> - [nuc/bhl/Berkeley-Humanoid-Lite-main/](../nuc/bhl/Berkeley-Humanoid-Lite-main/) — Isaac Lab 학습 + MuJoCo 시뮬 + 자산 정의
> - [nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/](../nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/) — 실제 로봇 저수준 제어(C++/Python, CAN, IMU)
>
> **주의:** 이 코드는 Hylion 런타임에서 직접 사용하지 않는 **레퍼런스/원본 논문 구현**입니다. 우리는 학습 산출물(ONNX 정책 + yaml 설정)만 차용하고, 명령 입력 경로(조이스틱 → UDP)만 Jetson 코디네이터의 NDJSON 명령으로 대체합니다 ([nuc/bhl/bridge.py](../nuc/bhl/bridge.py)).

---

## 0. 한눈에 보는 두 단계

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ① TRAINING (오프라인, GPU 서버)                                          │
│  ─────────────────────────────────────────────────                       │
│  Isaac Lab (4096 envs) + RSL-RL PPO                                      │
│         ▼                                                                │
│  학습 산출물:                                                            │
│    • policy.onnx       (Actor 네트워크, MLP 256-128-128, ELU)            │
│    • policy.pt         (TorchScript 백업)                                │
│    • policy_*.yaml     (deploy config: joint 순서/kp·kd/스케일/포트…)    │
│    • env.yaml/.pkl     (재현용 환경 설정)                                │
└──────────────────────────────────────────────────────────────────────────┘
                              │  (체크포인트와 yaml만 복사)
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ② OPERATION (온라인, NUC/로봇)                                          │
│  ─────────────────────────────────────────────────                       │
│  MuJoCo sim2sim    ─OR─    실제 로봇 (C++ control_loop + Python policy)  │
│         ▼                                                                │
│  obs(45) → ONNX → action(12) → PD제어(20·2 kp/kd) → 모터/시뮬            │
└──────────────────────────────────────────────────────────────────────────┘
```

핵심 아이디어:

- 학습은 **속도 명령 추종(velocity tracking)** locomotion 정책을 만든다.
- 학습이 끝나면 **정책 자체(ONNX)** 와 **배포용 메타데이터(yaml)** 가 떨어진다.
- 배포(MuJoCo / 실제 로봇) 쪽은 이 두 파일만 있으면 동일한 추론 코드([rl_controller.py](../nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/rl_controller.py))로 돌릴 수 있다.

---

## 1. TRAINING 파이프라인 (Isaac Lab + RSL-RL)

### 1.1 디렉터리 지도

```
Berkeley-Humanoid-Lite-main/
├── scripts/rsl_rl/
│   ├── train.py            ← 학습 진입점 (PPO)
│   ├── play.py             ← 학습된 정책 재생 + ONNX/PT/YAML 익스포트
│   └── cli_args.py
├── source/berkeley_humanoid_lite/
│   └── berkeley_humanoid_lite/tasks/locomotion/velocity/
│       ├── velocity_env_cfg.py   ← Scene/Sim 공통 베이스
│       ├── config/
│       │   ├── biped/env_cfg.py     ← biped(다리 12관절) 환경
│       │   │   └── agents/rsl_rl_ppo_cfg.py
│       │   └── humanoid/env_cfg.py  ← 전신 22관절 환경
│       └── mdp/
│           ├── rewards.py        ← 보상 함수 정의
│           ├── events.py         ← 도메인 랜덤화/리셋
│           ├── terminations.py
│           └── curriculums.py
└── source/berkeley_humanoid_lite_assets/   ← URDF/MJCF/USD
```

### 1.2 학습 루프 구조도

```
            ┌────────────────── Isaac Sim (PhysX, GPU) ──────────────────┐
            │   4096개 환경 병렬, 200 Hz physics, decimation=8           │
            │                                                             │
            │   ┌── Scene ──┐  ┌── Events (랜덤화) ──┐                    │
            │   │ Robot URDF │  │ • mass / friction   │                    │
            │   │ Plane      │  │ • actuator gain     │                    │
            │   │ ContactSnsr│  │ • init joint offset │                    │
            │   └────────────┘  │ • 외력 펄스         │                    │
            │                   └─────────────────────┘                    │
            │                                                             │
            │   ┌───── ManagerBasedRLEnv ──────┐                          │
            │   │ ObservationsCfg (policy obs)  │                          │
            │   │   velocity_commands  3        │                          │
            │   │   base_ang_vel       3        │                          │
            │   │   projected_gravity  3        │                          │
            │   │   joint_pos          12       │                          │
            │   │   joint_vel          12       │                          │
            │   │   last_action        12       │                          │
            │   │                      = 45     │                          │
            │   │                              │                          │
            │   │ ActionsCfg                    │                          │
            │   │   JointPositionAction(12, ×0.25)                        │
            │   │                              │                          │
            │   │ RewardsCfg                    │                          │
            │   │   +track_lin_vel_xy_exp      │                          │
            │   │   +track_ang_vel_z_exp       │                          │
            │   │   +feet_air_time_biped       │                          │
            │   │   -lin_vel_z, -ang_vel_xy    │                          │
            │   │   -flat_orientation          │                          │
            │   │   -action_rate, -torques     │                          │
            │   │   -dof_acc, -dof_pos_limits  │                          │
            │   │   -feet_slide                │                          │
            │   │   -undesired_contacts        │                          │
            │   │   -joint_deviation_hip/ankle │                          │
            │   │   -termination_penalty       │                          │
            │   └──────────────────────────────┘                          │
            └──────────────────────────────────────────────────────────────┘
                        ▲ obs(45)                      │ action(12)
                        │                              ▼
            ┌───────────────────── RSL-RL OnPolicyRunner ──────────────────┐
            │  PPO (rsl_rl_ppo_cfg.py)                                     │
            │   actor  : MLP [256,128,128] ELU  → mean+std                 │
            │   critic : MLP [256,128,128] ELU  → V(s)                     │
            │   24 steps/env, 5 epochs, 4 minibatch                        │
            │   clip 0.2, KL 0.01 adaptive, entropy 0.008                  │
            │   max_iterations = 6000 (biped)                              │
            └──────────────────────────────────────────────────────────────┘
                        │
                        ▼  (logs/rsl_rl/biped/<timestamp>/model_*.pt)
```

`train.py`는 ① argparse → AppLauncher(Isaac Sim 실행), ② `gym.make` 로 환경 생성, ③ `RslRlVecEnvWrapper` → `OnPolicyRunner.learn(...)` 를 호출하는 표준 RSL-RL 흐름입니다 ([scripts/rsl_rl/train.py:88-158](../nuc/bhl/Berkeley-Humanoid-Lite-main/scripts/rsl_rl/train.py#L88-L158)).

### 1.3 학습 산출물 (가장 중요한 부분)

`play.py`는 두 가지 일을 동시에 합니다 — 학습된 정책을 시뮬에서 재생하면서, **배포에 필요한 모든 파일을 한 번에 추출**합니다.

```
play.py 실행:

  로드: logs/rsl_rl/<exp>/<run>/model_<iter>.pt   (PPO 체크포인트)
        │
        ├──▶ export_policy_as_jit  ─▶  .../exported/policy.pt   (TorchScript)
        │
        ├──▶ export_policy_as_onnx ─▶  .../exported/policy.onnx (ONNX, deploy용)
        │
        └──▶ deploy_config (yaml)  ─▶  configs/policy_latest.yaml
              {
                policy_checkpoint_path,
                control_dt = 0.004     # 250 Hz 저수준 PD
                policy_dt  = sim.dt × decimation   (biped ≈ 0.04 → 25 Hz)
                physics_dt = 0.0005    # 2 kHz
                num_joints, joints[12],
                joint_kp[12]=20, joint_kd[12]=2,
                effort_limits[12]=6.0,
                default_joint_positions[12]   ← URDF init_state 에서 추출
                num_observations=45, history_length=0,
                num_actions=12, action_scale=0.25,
                action_indices[12]            ← 관절 이름 매칭 결과
                command_velocity[3],
                ip_*  / port_*                ← UDP 기본 포트
              }
```

체크포인트 디렉터리(`Berkeley-Humanoid-Lite-main/checkpoints/`)에 이미 들어있는 사전 학습 산출물은 다음과 같습니다.

| 파일                              | 설명                                  | 짝꿍 yaml                       |
| --------------------------------- | ------------------------------------- | ------------------------------- |
| `policy_biped_25hz_a.onnx`        | 다리 12관절, 25 Hz, 표준 게인         | `configs/policy_biped_25hz_a.yaml` |
| `policy_biped_25hz_b.onnx`        | 다리 12관절, 25 Hz, 다른 보상/세팅    | `configs/policy_biped_25hz_b.yaml` |
| `policy_biped_50hz.onnx`          | 다리 12관절, 50 Hz                    | `configs/policy_biped_50hz.yaml`   |
| `policy_humanoid.onnx`            | 전신 22관절                           | `configs/policy_humanoid.yaml`     |
| `policy_humanoid_legs.onnx`       | 전신 모델에서 다리 부분만 사용        | `configs/policy_humanoid_legs.yaml`|
| `policy_video.onnx`               | 데모 영상용                           | `configs/policy_video.yaml`        |

> **핵심 인사이트**: 배포 코드는 **ONNX + yaml 한 쌍** 만 있으면 다른 일은 알 필요가 없습니다. yaml이 obs/action 차원, 관절 인덱스, PD 게인까지 모두 담고 있기 때문에 같은 `RlController` 가 모델만 갈아끼우면 작동합니다.

---

## 2. OPERATION 파이프라인

운영 모드는 **(A) MuJoCo sim2sim**, **(B) 실제 로봇 sim2real** 두 가지인데, 정책 추론 부분(`RlController`)은 **완전히 동일한 코드**를 공유합니다. 차이는 obs를 어디서 받고, action을 어디로 보내느냐 뿐입니다.

### 2.1 공통 추론 코어: `RlController.update()`

`rl_controller.py:144` 이하가 매 정책 스텝(25 Hz / 50 Hz)마다 하는 일:

```
robot_observations (35 floats from low-level)
   │
   ├─ [0:4]   base_quat            (IMU)
   ├─ [4:7]   base_ang_vel         (IMU, rad/s)
   ├─ [7:19]  joint_pos[12]        - default_joint_positions   ← 학습 obs는 "default 대비 상대값"
   ├─ [19:31] joint_vel[12]
   ├─ [31]    mode                 (사용 안 함, 디버그)
   └─ [32:35] command_velocity     (vx, vy, wz)
   │
   ▼ 가공
   projected_gravity = quat_rotate_inverse(base_quat, [0,0,-1])
   │
   ▼ obs(45) 조립 (학습 환경과 같은 순서!)
   [command_velocity(3), base_ang_vel(3), projected_gravity(3),
    joint_pos(12), joint_vel(12), prev_actions(12)]
   │
   ▼ ONNX 추론
   raw_action(12) ← OnnxPolicy.forward(obs)
   │
   ▼ 후처리
   prev_actions   = clip(raw_action)
   target_joint   = raw_action × action_scale(0.25) + default_joint_positions
   │
   ▼ return target_joint(12)
```

> **순서 일치가 생명**: 학습 시 `ObservationsCfg.PolicyCfg` 에 정의된 순서(velocity_commands → base_ang_vel → projected_gravity → joint_pos → joint_vel → last_action)와 `RlController` 의 `np.concatenate(...)` 순서가 100% 같아야 한다. 누가 하나라도 어긋나면 로봇이 그냥 쓰러진다.

### 2.2 (A) MuJoCo sim2sim — `play_mujoco.py`

```
┌──────────────────────────── 단일 프로세스 ────────────────────────────┐
│                                                                       │
│  Cfg.from_arguments()  ─ configs/policy_biped_25hz_a.yaml             │
│        │                                                              │
│        ▼                                                              │
│  MujocoSimulator(cfg)                                                 │
│    • bhl_biped_scene.xml 로드 (또는 num_joints==22면 bhl_scene.xml)   │
│    • physics_substeps = policy_dt / physics_dt (≈ 40)                 │
│    • Se2Gamepad() 스레드 시작  → command_velocity 입력                │
│        │                                                              │
│        ▼ reset() → obs(35) 형식으로 가공                              │
│                                                                       │
│  RlController(cfg).load_policy()  → ONNX 세션 준비                    │
│                                                                       │
│  while True:                                                          │
│    actions = controller.update(obs)              ← 25 Hz              │
│    obs     = simulator.step(actions)             ← 내부에서 40번 PD   │
└───────────────────────────────────────────────────────────────────────┘
```

`MujocoSimulator.step()` 내부에서 매 physics tick(2 kHz)마다:

```
output_torque = kp(20) × (target_pos - q) + kd(2) × (-dq)
output_torque = clip(output_torque, ±effort_limit(6 Nm))
mj_data.ctrl[:] = output_torque   →  mujoco.mj_step()
```

즉 학습 환경의 actuator(stiffness/damping) 모델을 그대로 MuJoCo에서 재현하여 sim2sim consistency를 확보합니다.

### 2.3 (B) 실제 로봇 sim2real — 두 프로세스가 UDP로 분리됨

원본 논문 구현은 **C++ 저수준 컨트롤러**와 **Python 정책 컨트롤러**가 독립 프로세스로 돌고 둘 사이를 UDP로 잇습니다.

```
┌────────────────────────── 정책 컴퓨터 (Python) ──────────────────────┐
│                                                                       │
│  scripts/run_locomotion.py  (Lowlevel 저장소)                         │
│   ├─ Cfg.from_arguments()                                             │
│   ├─ RlController + ONNX 로드                                         │
│   ├─ Humanoid() ← 잠깐, 이 스크립트는 직접 CAN을 잡는 변형판          │
│   └─ rate = 25 Hz                                                     │
│                                                                       │
│     ※ 또는 "정책만" 분리한 변형이 있을 때:                            │
│        UDP recv obs ─▶ controller.update ─▶ UDP send acs              │
└───────────────────────────────────────────────────────────────────────┘
                         ▲                       │
              UDP :10000 │ obs(35)               │ acs(12)  UDP :10001
                         │                       ▼
┌──────────────────── 로봇 저수준 컴퓨터 (C++ `main`) ─────────────────┐
│                                                                       │
│  real_humanoid.cpp / .h  + main.cpp                                   │
│                                                                       │
│  RealHumanoid::run() 가 다음 5개 스레드를 띄움:                       │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │ loop_imu        500 Hz   IMU 시리얼 읽기                        │ │
│   │ loop_udp_recv   500 Hz   정책에서 온 acs 수신                   │ │
│   │ loop_joystick    20 Hz   UDP :10011 조이스틱 입력 + 모드 전환   │ │
│   │ loop_keyboard    20 Hz   r/t/q 키로 상태 전환 (디버그)          │ │
│   │ loop_control    250 Hz   ★ 메인 제어 루프                       │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   control_loop() 매 tick:                                             │
│     1) 상태머신 step (아래 §2.4)                                      │
│     2) update_joints():  CAN(PDO2)로 6쌍 관절 동시 write/read         │
│     3) lowlevel_states 채우기                                         │
│           [base_quat 4, base_ang_vel 3, q 12, dq 12,                  │
│            mode 1, vel_cmd 3]  = 35 floats                            │
│     4) policy_dt 마다 UDP sendto(:10000) 로 obs 전송                  │
│                              + sendto(:10002) 로 시각화 사본          │
│                                                                       │
│   하드웨어: 4개 CAN bus(원래) → 다리만 쓰면 can0/can1 두 개          │
│            12개 MotorController (Recoil 액추에이터)                  │
│            HiPNUC IMU (시리얼)                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.4 저수준 상태 머신

```
              ┌───────────┐
   start ───▶ │  IDLE     │  motor mode=DAMPING, target=measured
              └─────┬─────┘
                    │  joystick: command_mode=2 (LB+A)
                    ▼
              ┌───────────┐
              │ RL_INIT   │  100~200 step 동안 measured → rl_init_pose 보간
              │           │  motor mode=POSITION (kp/kd 적용)
              └─────┬─────┘
                    │  init_percentage==1.0 && command_mode=3 (RB+A)
                    ▼
              ┌───────────┐
              │RL_RUNNING │  UDP로 받은 acs(12)를 position_target 에 그대로
              │           │  CAN write_position 으로 PD 추종
              └─────┬─────┘
                    │  command_mode=1 (B/Stick)  또는 SIGINT
                    ▼
              ┌───────────┐
              │  IDLE     │  motor mode=DAMPING (수동 안전 정지)
              └───────────┘

   * rl_init_pose = [0,0,-0.2, 0.4, -0.3,0, 0,0,-0.2, 0.4, -0.3,0]
     (default_joint_positions 와 같음 = 학습 obs의 "0" 기준점)
```

이 상태 머신은 C++(`real_humanoid.cpp:64`)과 Python(`robot/humanoid.py:235`)에 동일 로직으로 두 번 구현되어 있습니다(언어 선택 가능).

### 2.5 캘리브레이션 사이드 경로

부팅 시마다 한 번 필요:

```
scripts/calibrate_joints.py
   사용자가 각 관절을 기계적 한계까지 수동으로 움직임
        │
        ▼
   각 관절의 영점 offset 측정
        │
        ▼
   calibration.yaml  ← position_offsets[12]
```

이후 `Humanoid()` / `RealHumanoid()` 생성자가 항상 `calibration.yaml` 을 읽어 `position_offsets`, `joint_axis_directions` 로 측정값과 명령값을 보정합니다(`humanoid.py:114`, `real_humanoid.cpp:36`).

---

## 3. 학습 산출물 ↔ 운영 단계 매핑

이게 본 문서의 핵심입니다. **학습에서 나온 뭐가, 운영에서 어디로 들어가서, 어떻게 쓰이느냐**.

| 학습 산출물                     | 어디서 만들어지나                                  | 운영에서 들어가는 위치                                            | 운영에서 하는 역할                                                                 |
| ------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `policy.onnx`                  | `play.py` → `export_policy_as_onnx`                | `OnnxPolicy(checkpoint_path)` 세션 ([rl_controller.py:49](../nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/rl_controller.py#L49)) | 매 정책 스텝(25/50 Hz)마다 obs(45) → action(12) 추론                              |
| `policy.pt` (TorchScript)      | 동상                                               | `TorchPolicy(checkpoint_path)`                                    | ONNX 대안. `.pt` 확장자 자동 인식 ([rl_controller.py:132](../nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/berkeley_humanoid_lite_lowlevel/policy/rl_controller.py#L132))             |
| `joints[12]` 이름 리스트       | `env_cfg.scene.robot.init_state.joint_pos.keys()`  | yaml로 저장 → `Cfg.joints` 로 로드                                | 실제 로봇 측 관절 등록 순서와 1:1 매칭하기 위한 정답                                |
| `default_joint_positions[12]`  | `env_cfg.scene.robot.init_state.joint_pos.values()`| 두 곳:<br>① obs 만들 때 `q_obs = q_measured - default`<br>② action 후처리: `target = a·scale + default` | 학습은 "기본 자세 대비 상대각" 으로 진행되므로 운영에서도 동일 좌표계로 변환     |
| `action_scale` (=0.25)         | `ActionsCfg.joint_pos.scale`                       | `policy_actions_scaled = clipped × scale + default`               | 정책 출력을 실제 joint 각도(rad) 변화량으로 환산                                   |
| `action_indices[12]`           | yaml로 dump (학습 시 관절 이름 → 인덱스 매핑)      | MuJoCo: `target_pos[action_indices] = actions` ([mujoco.py:191](../nuc/bhl/Berkeley-Humanoid-Lite-main/source/berkeley_humanoid_lite/berkeley_humanoid_lite/environments/mujoco.py#L191)) | 학습 행동 차원과 시뮬/실기 자유도 순서가 다를 때 재배열                            |
| `joint_kp[12]`, `joint_kd[12]` | `ActuatorCfg.stiffness/damping` → yaml             | • MuJoCo: `_apply_actions()` PD 계산 ([mujoco.py:195](../nuc/bhl/Berkeley-Humanoid-Lite-main/source/berkeley_humanoid_lite/berkeley_humanoid_lite/environments/mujoco.py#L195))<br>• 실기 C++: `MotorController::write_position_kp/kd()` ([real_humanoid.cpp:511](../nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/csrc/real_humanoid.cpp#L511)) | 학습 시 가정한 액추에이터 모델을 그대로 모터/시뮬에 주입                          |
| `effort_limits[12]` (=6 Nm)    | `ActuatorCfg.effort_limit`                         | • MuJoCo: torque clip<br>• 실기 C++: `write_torque_limit()`        | 모터 토크 상한 → 학습과 동일한 한계 조건 적용                                     |
| `policy_dt`, `control_dt`      | `env_cfg.sim.dt × decimation`, 고정값(0.004)        | • Python rate limiter (`run_locomotion.py:23`)<br>• C++ `loop_control` 분주율(`real_humanoid.cpp:182`) | 정책 추론 속도(25 Hz) vs 저수준 PD/통신 속도(250 Hz) 분리                          |
| `num_observations`(=45), `history_length`(=0) | obs term 합산              | `RlController.__init__` 의 obs 버퍼 크기 결정                     | history_length>0이면 이전 obs를 슬라이딩 윈도로 누적 → 같은 ONNX가 그대로 받음    |
| `command_velocity[3]`          | yaml 기본값(0,0,0)                                 | 운영 중에는 **조이스틱/UDP**가 매 스텝 덮어씀                     | 학습 시 보았던 명령 분포와 같은 입력 채널 제공                                    |
| `init_noise_std`, 네트워크 크기 | PPO cfg                                            | (운영에서 직접 안 씀)                                              | ONNX 그래프에 이미 가중치로 박혀 있음                                              |
| `env.yaml/.pkl`                | `dump_yaml/dump_pickle` (train.py)                  | (재학습/재현용)                                                   | 운영 자체에는 불필요, 추후 재학습 시 환경 복원                                    |

### 매핑을 시각화

```
TRAINING                                OPERATION
========                                =========
ObservationsCfg.PolicyCfg ──────────▶  rl_controller.update() concat 순서
                                       │
                                       └─ 학습/배포 obs 순서 100% 일치 보장

ActionsCfg.joint_pos.scale ─────────▶  policy_actions × scale
                          ╲
                           ╲──────▶  yaml: action_scale

init_state.joint_pos ──────────────▶  yaml: default_joint_positions
   (URDF 기본 자세)                    │
                                       ├─ obs: q - default
                                       ├─ action: a*scale + default
                                       └─ STATE_RL_INIT 목표 자세

ActuatorCfg.stiffness/damping ─────▶  yaml: joint_kp/kd
                                       │
                                       ├─ MuJoCo PD 게인
                                       └─ 실기 모터 write_position_kp/kd

ActuatorCfg.effort_limit ──────────▶  yaml: effort_limits
                                       │
                                       ├─ MuJoCo torque clip
                                       └─ 실기 write_torque_limit

PPO Actor (256-128-128) ───────────▶  policy.onnx
                                       │
                                       └─ OnnxPolicy.forward(obs[1,45]) → [1,12]

학습 명령 분포(UniformVelocityCommandCfg)─▶  실제 조이스틱(Se2Gamepad / UDP joystick)
   lin_vel_x ∈ [-0.5, 0.5]                   command_velocity 슬롯에 주입
   lin_vel_y ∈ [-0.25, 0.25]
   ang_vel_z ∈ [-1.0, 1.0]
```

---

## 4. 데이터 시간선 한 장 요약

```
[학습 단계]                                                      한 번만
─────────────────────────────────────────────────────────────────────────
GPU 서버 |  Isaac Lab × PPO × 6000 iter   ≈  여러 시간/하루 단위
         |
         |        ▼
         |  logs/.../model_<N>.pt   ── play.py ──▶
         |        ├── checkpoints/policy_*.onnx          ┐
         |        └── configs/policy_*.yaml              ┘  배포 패키지
─────────────────────────────────────────────────────────────────────────


[운영 단계]                                                  매 부팅마다
─────────────────────────────────────────────────────────────────────────
NUC  |  scripts/start_can_transports.sh   (CAN 인터페이스 up)
     |  calibrate_joints.py               (1회, calibration.yaml 생성)
     |
     |  make run   →  RealHumanoid (C++)        ┐
     |                  • 5개 스레드            │
     |                  • 250 Hz control loop   │
     |                                          │  UDP 10000/10001
     |  python run_locomotion.py                │
     |                  • RlController          │
     |                  • 25 Hz 추론            │
     |                                          ▼
     |        ┌─── 매 25 Hz tick ────────────────────────┐
     |        │ obs ← IMU + joint + joystick             │
     |        │ obs ── ONNX ──▶ action                   │
     |        │ action ── ×scale + default ──▶ target    │
     |        │ target ── CAN PDO2 ──▶ motors            │
     |        └──────────────────────────────────────────┘
─────────────────────────────────────────────────────────────────────────
```

---

## 5. Hylion에서 이 코드를 어떻게 활용하는가 (참조)

우리 런타임은 위 그림에서 다음 부분만 빌려옵니다.

- **학습 산출물 그대로 사용**: ONNX(`policy_biped_*.onnx`) + yaml(관절 순서/kp·kd/스케일) → 그대로 NUC에 배치.
- **명령 입력 경로 교체**:
  원본은 `Se2Gamepad` / UDP joystick → C++ `joystick_loop` → `lowlevel_states[32:35]` 로 들어감.
  Hylion은 **Jetson 코디네이터 → TCP/NDJSON → [nuc/bhl/bridge.py](../nuc/bhl/bridge.py) → UDP** 로 같은 슬롯에 주입합니다(상세는 [09_project_flow_overview.md](09_project_flow_overview.md)).
- **저수준 제어 루프는 BHL 원본을 그대로 사용**: 즉 학습된 정책 추론(25 Hz)·CAN PD(250 Hz)·IMU(500 Hz)는 검증된 BHL 스택에 위임하고, 우리는 그 위에 "음성·LLM 기반 의도 → 속도 명령"을 얹는 구조.

이 분리 덕분에 우리가 정책을 새로 학습할 일이 있으면, **이 문서 §1만 다시 돌리고 §2 운영부는 ONNX/yaml만 교체**하면 끝납니다.
