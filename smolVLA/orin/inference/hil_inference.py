"""smolvla_base 사전학습 모델 hardware-in-the-loop 추론 검증.

03_smolvla_test_on_orin TODO-07 의 책임 — 실 SO-ARM follower 1대 + 카메라 2대
환경에서 사전학습 smolvla_base 가 매 step 실 카메라 프레임 + 실 follower joint
state 를 받아 forward → action chunk 출력 → (모드별로) follower 송신.

본 마일스톤(03)의 책임은 파이프라인 검증 — 사전학습 분포(svla_so100_pickplace
의 lego pick-and-place)와 본 프로젝트 환경/배치/시작 각도가 다르므로 의미 있는
태스크 성공은 기대하지 않음. 그건 04_leftarmVLA 의 책임.

카메라 키 매핑:
- 실 카메라 2대 → smolvla_base 학습 분포의 `camera1` / `camera2` 슬롯
- `camera3` 은 누락 → policy.config.empty_cameras=1 로 더미(mask=0) 처리
- top → camera1, wrist → camera2 (임의 고정 — 03 단계는 정성 검증)

안전 장치:
- (i) SO100Follower 의 기본 토크 한계 의존 (별도 코드 X)
- (iii) n_action_steps=5 (chunk_size=50 의 1/10) — 폭주 시 영향 시간 축소
- 추가: --max-steps 로 전체 실행 step 상한, try/finally 로 follower 깔끔 종료,
  SIGINT 핸들러로 Ctrl+C 시 시리얼 통신 충돌 회피
"""

import argparse
import json
import signal
import sys

import torch

from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.policies import make_pre_post_processors
from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.policies.utils import build_inference_frame, make_robot_action
from lerobot.robots.so_follower import SO100Follower, SO100FollowerConfig
from lerobot.utils.feature_utils import hw_to_dataset_features

MODEL_ID = "lerobot/smolvla_base"
TASK = "Pick up the cube and place it in the box."
ROBOT_TYPE = "so100_follower"

# top, wrist 순서로 camera1, camera2 슬롯에 매핑 (smolvla_base 의 camera3 은 더미)
SLOT_MAP = ["camera1", "camera2"]


def parse_camera_arg(value: str) -> dict[str, int]:
    """`--cameras top:0,wrist:1` 형식을 파싱.

    Returns: {camera_name: device_index} 매핑. 입력 순서가 보존됨 (Python 3.7+).
    """
    pairs: dict[str, int] = {}
    for item in value.split(","):
        name, idx = item.split(":")
        pairs[name.strip()] = int(idx.strip())
    return pairs


def parse_camera_names(value: str) -> set[str]:
    """`--flip-cameras wrist,top` 형식을 파싱."""
    return {name.strip() for name in value.split(",") if name.strip()}


def flip_observation_cameras(obs: dict, slots: set[str]) -> dict:
    """Raw camera observations for selected slots only, flipped vertically."""
    for slot in slots:
        obs[slot] = obs[slot][::-1, :, :].copy()
    return obs


def main():
    parser = argparse.ArgumentParser(
        description="SmolVLA hardware-in-the-loop inference on Orin + SO-ARM follower."
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="dry-run: action JSON dump only / live: send to follower.",
    )
    parser.add_argument(
        "--follower-port",
        type=str,
        required=True,
        help="Follower SO-ARM serial port (e.g., /dev/ttyACM0).",
    )
    parser.add_argument(
        "--follower-id",
        type=str,
        default="follower_so100",
        help="Follower id for calibration file lookup.",
    )
    parser.add_argument(
        "--cameras",
        type=parse_camera_arg,
        default=parse_camera_arg("top:0,wrist:1"),
        help="Camera mapping `name:device_idx,...` (default: top:0,wrist:1).",
    )
    parser.add_argument(
        "--flip-cameras",
        type=parse_camera_names,
        default=set(),
        help="Comma-separated camera names to vertically flip before inference (e.g., wrist).",
    )
    parser.add_argument(
        "--n-action-steps",
        type=int,
        default=5,
        help="Number of action steps per forward chunk (safety: << chunk_size=50).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Total step upper bound across all forward calls.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="dry-run mode: dump action history JSON path.",
    )
    args = parser.parse_args()

    if args.mode == "dry-run" and args.output_json is None:
        parser.error("--output-json is required in dry-run mode.")

    if len(args.cameras) != len(SLOT_MAP):
        parser.error(
            f"--cameras must have exactly {len(SLOT_MAP)} entries (got {len(args.cameras)}). "
            f"Expected slots: {SLOT_MAP}."
        )

    unknown_flip_cameras = args.flip_cameras - set(args.cameras)
    if unknown_flip_cameras:
        parser.error(
            f"--flip-cameras contains unknown cameras: {sorted(unknown_flip_cameras)}. "
            f"Known cameras: {list(args.cameras)}."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── 1. Model load ─────────────────────────────────────────
    print(f"[load] {MODEL_ID}")
    policy = SmolVLAPolicy.from_pretrained(MODEL_ID).to(device)
    policy.eval()

    # camera2 만 들어가는 환경에서 1개 더미 슬롯 자동 처리
    policy.config.empty_cameras = 1
    # 안전 장치 (iii): chunk 짧게 끊기
    policy.config.n_action_steps = args.n_action_steps

    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        pretrained_path=MODEL_ID,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    # ── 2. Camera + Follower setup ────────────────────────────
    camera_config: dict[str, OpenCVCameraConfig] = {}
    flip_slots: set[str] = set()
    for slot, (name, idx) in zip(SLOT_MAP, args.cameras.items()):
        camera_config[slot] = OpenCVCameraConfig(
            index_or_path=idx, width=640, height=480, fps=30
        )
        if name in args.flip_cameras:
            flip_slots.add(slot)
        flip_note = ", flip=vertical" if slot in flip_slots else ""
        print(f"[camera] {slot} ← {name} (device {idx}{flip_note})")

    robot_cfg = SO100FollowerConfig(
        port=args.follower_port,
        id=args.follower_id,
        cameras=camera_config,
    )
    robot = SO100Follower(robot_cfg)

    # ── 3. SIGINT 핸들러 — graceful Ctrl+C ─────────────────────
    interrupted = False

    def _sigint_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        print(
            "\n[interrupt] Ctrl+C detected — finishing current step then disconnect.",
            file=sys.stderr,
        )

    signal.signal(signal.SIGINT, _sigint_handler)

    # ── 4. Inference loop ─────────────────────────────────────
    action_history = []
    step_count = 0

    try:
        robot.connect()
        action_features = hw_to_dataset_features(robot.action_features, "action")
        obs_features = hw_to_dataset_features(robot.observation_features, "observation")
        ds_features = {**action_features, **obs_features}

        print(
            f"[loop] mode={args.mode} max_steps={args.max_steps} "
            f"n_action_steps={args.n_action_steps}"
        )

        while step_count < args.max_steps and not interrupted:
            obs = robot.get_observation()
            if flip_slots:
                obs = flip_observation_cameras(obs, flip_slots)
            obs_frame = build_inference_frame(
                observation=obs,
                ds_features=ds_features,
                device=device,
                task=TASK,
                robot_type=ROBOT_TYPE,
            )
            obs_frame = preprocess(obs_frame)

            with torch.inference_mode():
                action = policy.select_action(obs_frame)
            action = postprocess(action)
            action_dict = make_robot_action(action, ds_features)

            print(f"[step {step_count}] action: {action_dict}")
            action_history.append({"step": step_count, "action": action_dict})

            if args.mode == "live":
                robot.send_action(action_dict)

            step_count += 1
    finally:
        try:
            robot.disconnect()
            print("[robot] disconnected")
        except Exception as e:
            print(f"[robot] disconnect warning: {e}", file=sys.stderr)

    # ── 5. dry-run JSON dump ──────────────────────────────────
    if args.mode == "dry-run":
        with open(args.output_json, "w") as f:
            json.dump(
                {
                    "model_id": MODEL_ID,
                    "mode": args.mode,
                    "n_action_steps": args.n_action_steps,
                    "total_steps": step_count,
                    "interrupted": interrupted,
                    "actions": action_history,
                },
                f,
                indent=2,
            )
        print(f"[saved] {args.output_json}")

    print(
        f"[done] mode={args.mode} steps={step_count} interrupted={interrupted}"
    )


if __name__ == "__main__":
    main()
