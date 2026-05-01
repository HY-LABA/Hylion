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

--gate-json 통합 (TODO-G2):
  check_hardware.sh 가 생성한 orin/config/ports.json 또는 orin/config/ 디렉터리를
  --gate-json 으로 지정하면 미지정 인자 (--follower-port, --cameras, --flip-cameras) 를
  자동으로 채운다.  CLI 에 직접 인자를 지정한 경우 그쪽이 우선 (하위 호환 보장).

  지원 경로 형식:
    --gate-json <dir>          → <dir>/ports.json + <dir>/cameras.json
    --gate-json <ports.json>   → 같은 디렉터리의 cameras.json 도 함께 로드
    --gate-json <cameras.json> → 같은 디렉터리의 ports.json 도 함께 로드
"""

import argparse
import json
import signal
import sys
from pathlib import Path

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


def load_gate_config(gate_json_path: str) -> tuple[dict | None, dict | None]:
    """orin/config/ports.json + cameras.json 을 로드하여 반환.

    --gate-json 인자로 받은 경로가 디렉터리이면 그 안의 ports.json·cameras.json 을
    찾는다. 파일 경로이면 그 파일과 같은 디렉터리에서 나머지 파일을 찾는다.

    Returns:
        (ports_data, cameras_data) — 파일이 없으면 해당 항목은 None.
        ports_data:   {"follower_port": str|None, "leader_port": str|None}
        cameras_data: {"top": {"index": str|None, "flip": bool},
                       "wrist": {"index": str|None, "flip": bool}}
    """
    p = Path(gate_json_path)

    if p.is_dir():
        config_dir = p
    else:
        config_dir = p.parent

    ports_path = config_dir / "ports.json"
    cameras_path = config_dir / "cameras.json"

    ports_data = None
    cameras_data = None

    if ports_path.exists():
        try:
            with open(ports_path) as f:
                ports_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[gate] ports.json 로드 실패 ({ports_path}): {e}", file=sys.stderr)

    if cameras_path.exists():
        try:
            with open(cameras_path) as f:
                cameras_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[gate] cameras.json 로드 실패 ({cameras_path}): {e}", file=sys.stderr)

    return ports_data, cameras_data


def apply_gate_config(
    args: argparse.Namespace,
    ports_data: dict | None,
    cameras_data: dict | None,
    parser: argparse.ArgumentParser,
) -> argparse.Namespace:
    """gate config 값으로 미지정 인자를 채운다.

    CLI 에 직접 인자가 지정된 경우 그쪽이 우선 (하위 호환).
    미지정 인자를 판단하는 기준: argparse 기본값과 일치하는 경우 덮어쓴다.

    채움 규칙:
      ports_data.follower_port  → --follower-port  (기본값 required 이므로 미설정 시 채움)
      cameras_data.top.index + cameras_data.wrist.index → --cameras  (기본값 top:0,wrist:1 이면 덮어씀)
      cameras_data.*.flip==true  → --flip-cameras  (빈 set 이면 gate 값 추가)
    """
    default_cameras = parse_camera_arg("top:0,wrist:1")

    # --follower-port: required 이므로 None 일 때만 gate 값 적용
    if args.follower_port is None and ports_data is not None:
        fp = ports_data.get("follower_port")
        if fp:
            args.follower_port = fp
            print(f"[gate] follower_port ← {fp} (ports.json)")
        else:
            print("[gate] ports.json.follower_port = null — --follower-port 는 여전히 필수", file=sys.stderr)

    # --cameras: 기본값(top:0,wrist:1)과 동일한 경우만 gate 값으로 덮어씀
    # cameras.json 의 index 는 문자열("/dev/video0") 또는 정수일 수 있으므로
    # parse_camera_arg 를 우회하고 직접 dict 구성 (index_or_path 는 int|Path — str 불허)
    if cameras_data is not None and args.cameras == default_cameras:
        top_idx = cameras_data.get("top", {}).get("index")
        wrist_idx = cameras_data.get("wrist", {}).get("index")
        if top_idx is not None and wrist_idx is not None:
            # int 변환 가능하면 int 로, 아니면 Path (e.g., /dev/video0)
            # OpenCVCameraConfig.index_or_path: int | Path — str 불허
            def _to_idx(v):
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return Path(v)

            args.cameras = {"top": _to_idx(top_idx), "wrist": _to_idx(wrist_idx)}
            print(f"[gate] cameras ← top:{top_idx},wrist:{wrist_idx} (cameras.json)")

    # --flip-cameras: 빈 set 인 경우에만 gate 값 적용
    if cameras_data is not None and not args.flip_cameras:
        flip_names: set[str] = set()
        for cam_name in ("top", "wrist"):
            if cameras_data.get(cam_name, {}).get("flip", False):
                flip_names.add(cam_name)
        if flip_names:
            args.flip_cameras = flip_names
            print(f"[gate] flip_cameras ← {sorted(flip_names)} (cameras.json)")

    return args


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
        default=None,
        help=(
            "Follower SO-ARM serial port (e.g., /dev/ttyACM0). "
            "--gate-json 로 ports.json 를 지정하면 자동으로 채워진다."
        ),
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
    parser.add_argument(
        "--gate-json",
        type=str,
        default=None,
        help=(
            "orin/config/ 디렉터리 경로 또는 ports.json 파일 경로. "
            "check_hardware.sh 가 생성한 cache 를 읽어 미지정 인자 "
            "(--follower-port, --cameras, --flip-cameras) 를 자동으로 채운다. "
            "CLI 에 직접 인자를 지정한 경우 그쪽이 우선 (하위 호환)."
        ),
    )
    args = parser.parse_args()

    # ── gate-json 자동 인자 채우기 ────────────────────────────────
    if args.gate_json is not None:
        ports_data, cameras_data = load_gate_config(args.gate_json)
        args = apply_gate_config(args, ports_data, cameras_data, parser)

    # --follower-port 최종 필수 검증 (gate-json 로딩 후)
    if args.follower_port is None:
        parser.error("--follower-port 는 필수입니다 (또는 --gate-json 으로 ports.json 경로 지정).")

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
