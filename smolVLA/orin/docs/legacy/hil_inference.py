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
- (i) SO101Follower 의 기본 토크 한계 의존 (별도 코드 X)
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

카메라 인덱스 사전 발견 (03 BACKLOG #15):
  Linux 에서 카메라 인덱스가 재부팅·USB 재연결마다 달라질 수 있다.
  실행 전 반드시 아래 명령으로 인덱스를 확인하고 --cameras 에 명시할 것:

    lerobot-find-cameras opencv

  --cameras 를 생략하거나 --gate-json 을 미지정하면 자동 발견을 시도하며
  (OpenCVCamera.find_cameras()), 발견된 카메라가 정확히 2 대일 때만 자동 적용
  (top: 첫 번째, wrist: 두 번째). 발견 수가 0 이거나 3 대 이상이면 수동 지정 필수.

wrist 카메라 플립 (03 BACKLOG #16):
  wrist 카메라를 거꾸로 장착한 경우 --flip-cameras wrist 를 추가한다.
  사전학습 분포(svla_so100_pickplace)의 wrist 카메라 방향과 일치 여부는
  08_leftarmVLA 진입 시 확인 예정 (03 BACKLOG #11).
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

MODEL_ID = "lerobot/smolvla_base"
TASK = "Pick up the cube and place it in the box."
ROBOT_TYPE = "so101_follower"

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


def _auto_discover_cameras() -> dict[str, int] | None:
    """OpenCVCamera.find_cameras() 로 시스템에 연결된 카메라를 자동 발견한다.

    발견된 카메라가 정확히 2 대인 경우에만 자동 적용.
    반환: {camera_name: device_index} 또는 자동 적용 불가 시 None.

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
        print("[camera] 연결된 카메라를 찾지 못했습니다. lerobot-find-cameras opencv 로 확인하세요.", file=sys.stderr)
        return None

    if len(found) != 2:
        print(
            f"[camera] 카메라 {len(found)} 대 발견 — 자동 적용 불가 (정확히 2 대 필요).\n"
            f"[camera] lerobot-find-cameras opencv 결과를 확인하고 --cameras top:<idx>,wrist:<idx> 로 명시하십시오.",
            file=sys.stderr,
        )
        return None

    # 발견 수 == 2: 첫 번째 → top, 두 번째 → wrist
    # find_cameras() 의 각 항목은 {'id': str|int, ...} 형식
    # id 는 Linux 에서 str('/dev/video0'), 다른 OS 에서 int
    def _to_idx(v) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            # '/dev/video2' → 2 (끝 숫자만 추출)
            import re
            m = re.search(r"(\d+)$", str(v))
            if m:
                return int(m.group(1))
            raise ValueError(f"카메라 id 를 정수 인덱스로 변환할 수 없음: {v!r}")

    try:
        top_idx = _to_idx(found[0]["id"])
        wrist_idx = _to_idx(found[1]["id"])
    except Exception as e:
        print(f"[camera] 자동 발견 인덱스 변환 실패: {e}", file=sys.stderr)
        return None

    result = {"top": top_idx, "wrist": wrist_idx}
    print(f"[camera] 자동 발견 성공 — top:{top_idx}, wrist:{wrist_idx} (2대 발견)")
    print("[camera] 인덱스가 올바르지 않으면 lerobot-find-cameras opencv 로 확인 후 --cameras 로 명시하십시오.")
    return result


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
      cameras_data.top.index + cameras_data.wrist.index → --cameras  (None 또는 기본값일 때 덮어씀)
      cameras_data.*.flip==true  → --flip-cameras  (빈 set 이면 gate 값 추가)
    """
    # --follower-port: required 이므로 None 일 때만 gate 값 적용
    if args.follower_port is None and ports_data is not None:
        fp = ports_data.get("follower_port")
        if fp:
            args.follower_port = fp
            print(f"[gate] follower_port ← {fp} (ports.json)")
        else:
            print("[gate] ports.json.follower_port = null — --follower-port 는 여전히 필수", file=sys.stderr)

    # --cameras: None (미지정) 인 경우 gate 값으로 채움.
    # cameras.json 의 index 는 문자열("/dev/video0") 또는 정수일 수 있으므로
    # parse_camera_arg 를 우회하고 직접 dict 구성 (index_or_path 는 int|Path — str 불허)
    if cameras_data is not None and args.cameras is None:
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
        default=None,
        help=(
            "Camera mapping `name:device_idx,...` (예: top:2,wrist:0). "
            "미지정 시 OpenCVCamera.find_cameras() 로 자동 발견 시도 "
            "(발견 수 == 2 일 때만 자동 적용 — top: 첫 번째, wrist: 두 번째). "
            "사전 발견 명령: lerobot-find-cameras opencv. "
            "--gate-json 지정 시 cameras.json 에서 인덱스를 읽어 채움 (이쪽이 우선)."
        ),
    )
    parser.add_argument(
        "--flip-cameras",
        type=parse_camera_names,
        default=set(),
        help=(
            "Comma-separated camera names to vertically flip before inference (e.g., wrist). "
            "wrist 카메라를 거꾸로 장착한 경우 `--flip-cameras wrist` 를 추가한다. "
            "--gate-json 의 cameras.json.wrist.flip=true 로도 자동 적용 가능."
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
            "CLI 에 직접 인자를 지정한 경우 그쪽이 우선 (하위 호환)."
        ),
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help=(
            "HuggingFace Hub repo_id (예: lerobot/smolvla_base, <username>/<repo>). "
            "미지정 시 모듈 상수 MODEL_ID 를 사용 (하위 호환). "
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
            "미지정 시 --model-id 또는 모듈 상수 MODEL_ID 를 사용 (하위 호환). "
            "--model-id 와 동시 지정 불가."
        ),
    )
    args = parser.parse_args()

    # ── --model-id / --ckpt-path 충돌 검사 ───────────────────────
    if args.model_id is not None and args.ckpt_path is not None:
        parser.error("--model-id 와 --ckpt-path 는 동시에 지정할 수 없습니다.")

    # ── 실제 사용 model 경로 결정 ─────────────────────────────────
    # 우선순위: --ckpt-path > --model-id > 모듈 상수 MODEL_ID
    if args.ckpt_path is not None:
        effective_model = str(Path(args.ckpt_path).expanduser())
        print(f"[ckpt] 로컬 경로 사용: {effective_model}")
    elif args.model_id is not None:
        effective_model = args.model_id
        print(f"[ckpt] HF Hub 사용: {effective_model}")
    else:
        effective_model = MODEL_ID  # 하드코드 기본값 (하위 호환)

    # ── gate-json 자동 인자 채우기 ────────────────────────────────
    if args.gate_json is not None:
        ports_data, cameras_data = load_gate_config(args.gate_json)
        args = apply_gate_config(args, ports_data, cameras_data, parser)

    # ── 카메라 인덱스 자동 발견 fallback (03 BACKLOG #15) ──────────
    # 우선순위: --cameras CLI 직접 지정 > --gate-json cameras.json > 자동 발견 > 기본값
    if args.cameras is None:
        args.cameras = _auto_discover_cameras()

    # ── 자동 발견 실패 시 기본값 적용 + 사전 발견 안내 ───────────────
    if args.cameras is None:
        print(
            "[camera] 자동 발견 실패 — 기본값(top:0,wrist:1) 을 사용합니다.\n"
            "[camera] 카메라 인덱스 확인 명령: lerobot-find-cameras opencv\n"
            "[camera] 확인 후 --cameras top:<idx>,wrist:<idx> 로 명시하십시오.",
            file=sys.stderr,
        )
        args.cameras = parse_camera_arg("top:0,wrist:1")

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
    print(f"[load] {effective_model}")
    policy = SmolVLAPolicy.from_pretrained(effective_model).to(device)
    policy.eval()

    # camera2 만 들어가는 환경에서 1개 더미 슬롯 자동 처리
    policy.config.empty_cameras = 1
    # 안전 장치 (iii): chunk 짧게 끊기
    policy.config.n_action_steps = args.n_action_steps

    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        pretrained_path=effective_model,
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
                    "model_id": effective_model,
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
