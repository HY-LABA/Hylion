"""08_final_e2e fine-tune 모델 (BaboGaeguri/lego_v1) Orin HIL 추론.

본 스크립트는 spec 08_final_e2e 의 첫 정식 fine-tune 산출물 추론용.
hil_inference.py 와 같은 hardware-in-the-loop 패턴 (실 SO-101 follower + 실 카메라 2 대)
이지만, 학습 동기화 항목이 다음과 같이 다르다.

학습 산출물 (변경 불가 fact):
- HF Hub: BaboGaeguri/lego_v1 — lerobot/smolvla_base fine-tune
- 데이터셋: BaboGaeguri/lego_pickplace_20260506 (10 ep, 4464 frame, 15s/ep, 30fps)
- 학습 인자: batch_size=16, num_workers=4, prefetch_factor=2, steps=2000, save_freq=1000
- rename_map: observation.images.overview → observation.images.camera1
              observation.images.wrist    → observation.images.camera2
- 단일 task 문자열: "Grasp a lego block and put it in the bin."
- 최종 loss 0.059 / grad_norm 0.91 (정상 수렴, decision C·D)

Orin 환경 (변경 불가 fact):
- 카메라 매핑 (v4l2 enum, DGX 와 반대):
    overview = /dev/video2 = OpenCV index 2  (YJX-C5 = OV5648)
    wrist    = /dev/video0 = OpenCV index 0  (Innomaker U20CAM-720P)
- SO-101 follower:
    port=/dev/ttyACM1, id=hylion_follower, robot_type=so101_follower
    calibration JSON = $HF_HOME/lerobot/calibration/robots/so_follower/hylion_follower.json
- HF_HOME = /home/laba/smolvla/.hf_cache (export 필요, venv activate 영구화는 BACKLOG)
- venv: ~/smolvla/orin/.hylion_arm
- USB 토폴로지: 두 카메라가 같은 USB 2.0 hub 공유 → MJPG 강제 필수
  (YUYV 시 bandwidth 초과로 read fail — DGX 진단 그대로 적용)

hil_inference.py 와 차이:
1. TASK = "Grasp a lego block and put it in the bin." (cube → lego, box → bin)
2. MODEL_ID = "BaboGaeguri/lego_v1" (lerobot/smolvla_base fine-tune)
3. 사용자 카메라 키: overview / wrist (학습 rename_map 의 실 키와 일관).
   SLOT_MAP 자체는 ["camera1", "camera2"] 보존 (모델 호환).
   gate-json 의 cameras.json 은 top / wrist 키이므로 top → overview alias 처리.
4. follower default: port=/dev/ttyACM1, id=hylion_follower
5. OpenCVCameraConfig 에 fourcc="MJPG" 명시 (USB 2.0 hub 대역폭 한계 정합)

empty_cameras / n_action_steps:
- empty_cameras=1 — 학습 모델 config.json 의 실측값을 시작 시 콘솔 출력해 검증
- n_action_steps=5 (default) — 안전 장치 (chunk_size=50 의 1/10)

모드:
- dry-run: action JSON dump only (실 motor 송신 X)
- live: 실 motor 송신

gate-json:
- orin/config/ports.json + cameras.json 자동 로드 (hil_inference 와 동일 패턴).
  cameras.json 의 top → overview slot 으로 alias 매핑.
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
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.utils.feature_utils import hw_to_dataset_features

MODEL_ID = "BaboGaeguri/lego_v1"
TASK = "Grasp a lego block and put it in the bin."
ROBOT_TYPE = "so101_follower"

# overview, wrist 순서로 camera1, camera2 슬롯에 매핑 (학습 rename_map 결과 정합)
SLOT_MAP = ["camera1", "camera2"]

# gate-json (orin/config/cameras.json) 의 키 → 본 스크립트의 사용자 layer 키
# cameras.json 은 hil_inference 와 공유 자원이라 top/wrist 그대로 두고, 본 스크립트만 alias.
GATE_CAMERA_ALIAS = {"top": "overview"}


def parse_camera_arg(value: str) -> dict[str, int]:
    """`--cameras overview:2,wrist:0` 형식을 파싱.

    Returns: {camera_name: device_index} 매핑. 입력 순서가 보존됨 (Python 3.7+).
    """
    pairs: dict[str, int] = {}
    for item in value.split(","):
        name, idx = item.split(":")
        pairs[name.strip()] = int(idx.strip())
    return pairs


def parse_camera_names(value: str) -> set[str]:
    """`--flip-cameras wrist,overview` 형식을 파싱."""
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
    """
    p = Path(gate_json_path)
    config_dir = p if p.is_dir() else p.parent

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


def _alias_camera_keys(cameras_data: dict) -> dict:
    """gate-json 의 top → overview 등 alias 적용한 사본을 반환."""
    aliased: dict = {}
    for k, v in cameras_data.items():
        aliased[GATE_CAMERA_ALIAS.get(k, k)] = v
    return aliased


def _auto_discover_cameras() -> dict[str, int] | None:
    """OpenCVCamera.find_cameras() 로 시스템에 연결된 카메라를 자동 발견한다.

    발견된 카메라가 정확히 2 대인 경우에만 자동 적용 (overview: 첫 번째, wrist: 두 번째).

    패턴 출처: docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py
    OpenCVCamera.find_cameras() — Linux: /dev/video* glob, others: 0..MAX_OPENCV_INDEX
    """
    try:
        from lerobot.cameras.opencv import OpenCVCamera

        found = OpenCVCamera.find_cameras()
    except Exception as e:
        print(f"[camera] 자동 발견 중 오류: {e}", file=sys.stderr)
        return None

    if len(found) == 0:
        print(
            "[camera] 연결된 카메라를 찾지 못했습니다. lerobot-find-cameras opencv 로 확인하세요.",
            file=sys.stderr,
        )
        return None

    if len(found) != 2:
        print(
            f"[camera] 카메라 {len(found)} 대 발견 — 자동 적용 불가 (정확히 2 대 필요).\n"
            f"[camera] lerobot-find-cameras opencv 결과를 확인하고 "
            f"--cameras overview:<idx>,wrist:<idx> 로 명시하십시오.",
            file=sys.stderr,
        )
        return None

    def _to_idx(v) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            import re

            m = re.search(r"(\d+)$", str(v))
            if m:
                return int(m.group(1))
            raise ValueError(f"카메라 id 를 정수 인덱스로 변환할 수 없음: {v!r}")

    try:
        overview_idx = _to_idx(found[0]["id"])
        wrist_idx = _to_idx(found[1]["id"])
    except Exception as e:
        print(f"[camera] 자동 발견 인덱스 변환 실패: {e}", file=sys.stderr)
        return None

    result = {"overview": overview_idx, "wrist": wrist_idx}
    print(
        f"[camera] 자동 발견 성공 — overview:{overview_idx}, wrist:{wrist_idx} (2대 발견)"
    )
    print(
        "[camera] 인덱스가 올바르지 않으면 lerobot-find-cameras opencv 로 확인 후 "
        "--cameras 로 명시하십시오."
    )
    return result


def apply_gate_config(
    args: argparse.Namespace,
    ports_data: dict | None,
    cameras_data: dict | None,
    parser: argparse.ArgumentParser,
) -> argparse.Namespace:
    """gate config 값으로 미지정 인자를 채운다.

    CLI 에 직접 인자가 지정된 경우 그쪽이 우선 (하위 호환).
    cameras.json 의 top 키는 GATE_CAMERA_ALIAS 따라 overview 로 변환된다.
    """
    # --follower-port: required 이므로 None 일 때만 gate 값 적용
    if args.follower_port is None and ports_data is not None:
        fp = ports_data.get("follower_port")
        if fp:
            args.follower_port = fp
            print(f"[gate] follower_port ← {fp} (ports.json)")
        else:
            print(
                "[gate] ports.json.follower_port = null — --follower-port 는 여전히 필수",
                file=sys.stderr,
            )

    # --cameras: None (미지정) 인 경우 gate 값으로 채움.
    if cameras_data is not None and args.cameras is None:
        aliased = _alias_camera_keys(cameras_data)
        overview_idx = aliased.get("overview", {}).get("index")
        wrist_idx = aliased.get("wrist", {}).get("index")
        if overview_idx is not None and wrist_idx is not None:
            def _to_idx(v):
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return Path(v)

            args.cameras = {
                "overview": _to_idx(overview_idx),
                "wrist": _to_idx(wrist_idx),
            }
            print(
                f"[gate] cameras ← overview:{overview_idx},wrist:{wrist_idx} "
                f"(cameras.json, top→overview alias)"
            )

    # --flip-cameras: 빈 set 인 경우에만 gate 값 적용
    if cameras_data is not None and not args.flip_cameras:
        aliased = _alias_camera_keys(cameras_data)
        flip_names: set[str] = set()
        for cam_name in ("overview", "wrist"):
            if aliased.get(cam_name, {}).get("flip", False):
                flip_names.add(cam_name)
        if flip_names:
            args.flip_cameras = flip_names
            print(f"[gate] flip_cameras ← {sorted(flip_names)} (cameras.json)")

    return args


def main():
    parser = argparse.ArgumentParser(
        description=(
            "BaboGaeguri/lego_v1 fine-tune model HIL inference on Orin + SO-101 follower."
        )
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
        default="/dev/ttyACM1",
        help=(
            "Follower SO-101 serial port. default: /dev/ttyACM1 (Orin 실측). "
            "--gate-json 의 ports.json.follower_port 가 있으면 그 값으로 덮어쓴다 (None 일 때만)."
        ),
    )
    parser.add_argument(
        "--follower-id",
        type=str,
        default="hylion_follower",
        help="Follower id for calibration file lookup. default: hylion_follower (Orin 실측).",
    )
    parser.add_argument(
        "--cameras",
        type=parse_camera_arg,
        default=None,
        help=(
            "Camera mapping `name:device_idx,...` (예: overview:2,wrist:0). "
            "사용자 키는 학습 rename_map 의 실 키 (overview, wrist) 를 따른다. "
            "내부적으로 SLOT_MAP=['camera1','camera2'] 슬롯에 순서대로 매핑됨. "
            "미지정 시 OpenCVCamera.find_cameras() 자동 발견 시도 (발견 수 == 2 일 때만). "
            "사전 발견 명령: lerobot-find-cameras opencv. "
            "--gate-json cameras.json 이 있으면 그 값을 우선 적용 (top→overview alias)."
        ),
    )
    parser.add_argument(
        "--flip-cameras",
        type=parse_camera_names,
        default=set(),
        help=(
            "Comma-separated camera names to vertically flip before inference (예: wrist). "
            "--gate-json 의 cameras.json.<name>.flip=true 로도 자동 적용 가능."
        ),
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
            "CLI 에 직접 인자를 지정한 경우 그쪽이 우선 (하위 호환). "
            "cameras.json 의 top 키는 본 스크립트의 overview 로 alias 된다."
        ),
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help=(
            "HuggingFace Hub repo_id 또는 미지정 시 모듈 상수 MODEL_ID 사용 (BaboGaeguri/lego_v1). "
            "--ckpt-path 와 동시 지정 불가."
        ),
    )
    parser.add_argument(
        "--ckpt-path",
        type=str,
        default=None,
        help=(
            "로컬 pretrained_model 디렉터리 경로 "
            "(예: ~/smolvla/orin/checkpoints/<run>/<step>/pretrained_model). "
            "미지정 시 --model-id 또는 모듈 상수 MODEL_ID 를 사용. --model-id 와 동시 지정 불가."
        ),
    )
    args = parser.parse_args()

    # ── --model-id / --ckpt-path 충돌 검사 ───────────────────────
    if args.model_id is not None and args.ckpt_path is not None:
        parser.error("--model-id 와 --ckpt-path 는 동시에 지정할 수 없습니다.")

    # ── 실제 사용 model 경로 결정 ─────────────────────────────────
    if args.ckpt_path is not None:
        effective_model = str(Path(args.ckpt_path).expanduser())
        print(f"[ckpt] 로컬 경로 사용: {effective_model}")
    elif args.model_id is not None:
        effective_model = args.model_id
        print(f"[ckpt] HF Hub 사용: {effective_model}")
    else:
        effective_model = MODEL_ID
        print(f"[ckpt] 모듈 상수 MODEL_ID 사용: {effective_model}")

    # ── gate-json 자동 인자 채우기 ────────────────────────────────
    if args.gate_json is not None:
        ports_data, cameras_data = load_gate_config(args.gate_json)
        args = apply_gate_config(args, ports_data, cameras_data, parser)

    # ── 카메라 인덱스 결정: CLI > gate-json > 자동 발견 > 기본값 ───
    if args.cameras is None:
        args.cameras = _auto_discover_cameras()

    if args.cameras is None:
        # 자동 발견 실패 — Orin 실측 기본값 (overview:2 = /dev/video2, wrist:0 = /dev/video0)
        print(
            "[camera] 자동 발견 실패 — Orin 실측 기본값(overview:2,wrist:0) 을 사용합니다.\n"
            "[camera] 카메라 인덱스 확인 명령: lerobot-find-cameras opencv\n"
            "[camera] 확인 후 --cameras overview:<idx>,wrist:<idx> 로 명시하십시오.",
            file=sys.stderr,
        )
        args.cameras = parse_camera_arg("overview:2,wrist:0")

    # --follower-port 최종 필수 검증 (gate-json 로딩 후)
    if args.follower_port is None:
        parser.error("--follower-port 는 필수입니다 (또는 --gate-json 으로 ports.json 경로 지정).")

    if args.mode == "dry-run" and args.output_json is None:
        parser.error("--output-json is required in dry-run mode.")

    if len(args.cameras) != len(SLOT_MAP):
        parser.error(
            f"--cameras must have exactly {len(SLOT_MAP)} entries (got {len(args.cameras)}). "
            f"Expected user keys: ['overview', 'wrist'] → SLOT_MAP {SLOT_MAP}."
        )

    unknown_flip_cameras = args.flip_cameras - set(args.cameras)
    if unknown_flip_cameras:
        parser.error(
            f"--flip-cameras contains unknown cameras: {sorted(unknown_flip_cameras)}. "
            f"Known cameras: {list(args.cameras)}."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── 1. Model load ─────────────────────────────────────────
    print(f"[load] {effective_model}")
    policy = SmolVLAPolicy.from_pretrained(effective_model).to(device)
    policy.eval()

    # 학습 모델의 empty_cameras 실측값 출력 (검증 보조)
    measured_empty = getattr(policy.config, "empty_cameras", None)
    print(
        f"[policy.config] empty_cameras 실측값 = {measured_empty} "
        f"(camera2 만 들어가는 환경이라 1 강제 적용 — KeyError 발생 시 실측값 확인)"
    )
    policy.config.empty_cameras = 1
    policy.config.n_action_steps = args.n_action_steps

    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        pretrained_path=effective_model,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    # ── 2. Camera + Follower setup ────────────────────────────
    # USB 2.0 hub 대역폭 한계 — fourcc="MJPG" 강제 (YUYV 시 read fail)
    camera_config: dict[str, OpenCVCameraConfig] = {}
    flip_slots: set[str] = set()
    for slot, (name, idx) in zip(SLOT_MAP, args.cameras.items()):
        camera_config[slot] = OpenCVCameraConfig(
            index_or_path=idx, width=640, height=480, fps=30, fourcc="MJPG"
        )
        if name in args.flip_cameras:
            flip_slots.add(slot)
        flip_note = ", flip=vertical" if slot in flip_slots else ""
        print(f"[camera] {slot} ← {name} (device {idx}, fourcc=MJPG{flip_note})")

    robot_cfg = SO101FollowerConfig(
        port=args.follower_port,
        id=args.follower_id,
        cameras=camera_config,
    )
    robot = SO101Follower(robot_cfg)

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
            f"n_action_steps={args.n_action_steps} task={TASK!r}"
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
                    "model_id": effective_model,
                    "task": TASK,
                    "mode": args.mode,
                    "n_action_steps": args.n_action_steps,
                    "empty_cameras_measured": measured_empty,
                    "total_steps": step_count,
                    "interrupted": interrupted,
                    "actions": action_history,
                },
                f,
                indent=2,
            )
        print(f"[saved] {args.output_json}")

    print(f"[done] mode={args.mode} steps={step_count} interrupted={interrupted}")


if __name__ == "__main__":
    main()
