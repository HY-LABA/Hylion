"""leftarm_v2 학습 ckpt (BaboGaeguri/leftarm_v2_A2_pc_2026-05-17) Orin HIL 추론.

마일스톤 v2 전용 추론 entry — lerobot/smolvla_base 위에 LoRA adapter 로 fine-tune 된
ckpt 를 로드해 두 task instruction (task1/task2) 추론.

USER_OVERRIDE 2026-05-18 옵션 W 결정에 따라 lerobot-record 폐기 + 신규 작성.
orin/docs/legacy/hil_inference.py 는 사전학습 ckpt 책임 보존 (변경 X).

학습 산출물 (변경 불가 fact):
- HF Hub: BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 — LoRA adapter on smolvla_base
- 로컬 ckpt: ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/
- adapter 파일: adapter_config.json (base_model_name_or_path=lerobot/smolvla_base),
                adapter_model.safetensors
- rename_map: top→camera1, wrist→camera2 (train_config.json 확인)
- task1: "Pick up the blue and yellow doll and place it on the left side of the table"
- task2: "Hand the yellow can to the person"
- n_action_steps=50 (config.json 이미 수정됨, 1 감지 시 경고)

orin/docs/legacy/hil_inference.py / orin/docs/legacy/lego_v1_inference.py 와 차이:
1. ckpt 종류: LoRA adapter (peft) — SmolVLAPolicy.from_pretrained(base) + PeftModel 적용
2. task 선택: --task task1 / task2 CLI 인자 (다중 instruction 분기)
3. rename_map: top→camera1, wrist→camera2 (observation 키 변환 후 policy 입력)
4. n_action_steps default=50 (안전 주석: 실 시연 시 필요 시 낮추기 가능)

LoRA 로드 의존성:
- `peft` 패키지 필요. Orin venv 에 미설치 시 ImportError 와 함께 설치 안내 출력.
- 설치: pip install peft>=0.10.0
- orin/pyproject.toml 에 peft 미등록 (Category B+C — 사용자 동의 후 추가 예정).

rename_map 적용:
- 학습 시: dataset 의 observation.images.top / wrist → camera1 / camera2 으로 매핑
- 추론 시: robot.get_observation() 결과의 'observation.images.top' 키를
           'observation.images.camera1' 로 rename 후 policy 입력

device 매핑 (2026-05-24 udev rule 도입 후):
- /dev/cam_top, /dev/cam_wrist, /dev/so_arm_left, /dev/so_arm_right — orin/config/udev/99-hylion.rules 가 생성
- 인자 default 가 udev path. --follower-port·--cameras override 로 우암 등 전환 가능
- gate-json: 카메라 부가 설정 (rotation/fps/fourcc/flip) 만 cameras.json 에서 로드
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

# ── 상수 ─────────────────────────────────────────────────────────────────────
CKPT_REPO_ID = "BaboGaeguri/leftarm_v2_A2_pc_2026-05-17"
CKPT_LOCAL_DIR = "~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17"
ROBOT_TYPE = "so101_follower"

# 학습 시 rename_map (train_config.json 확인):
#   observation.images.top   → observation.images.camera1
#   observation.images.wrist → observation.images.camera2
# SLOT_MAP: policy 가 기대하는 camera key (학습 분포와 정합)
SLOT_MAP = ["camera1", "camera2"]

# Task instruction (출처: dgx/docs/finetune/leftarm_v2/collection_log.md §task 정의)
# task3: 학습 분포 외 일반화 검증용 (2026-05-24 사용자 추가) — 노란 캔 → 흰색 캔 색 변화
TASK_INSTRUCTIONS = {
    "task1": "Pick up the blue and yellow doll and place it on the left side of the table",
    "task2": "Hand the yellow can to the person",
    "task3": "Hand the white can to the person",
}


# ── 카메라 파싱 유틸 ──────────────────────────────────────────────────────────
def parse_camera_arg(value: str) -> dict[str, int | str]:
    """`--cameras top:0,wrist:1` 또는 `--cameras top:/dev/cam_top,wrist:/dev/cam_wrist` 형식을 파싱.

    udev rule 도입 (2026-05-24) 후 default 는 path 기반. 정수 인덱스도 하위 호환.
    Returns: {camera_name: device_index_or_path} 매핑. 입력 순서 보존 (Python 3.7+).
    """
    pairs: dict[str, int | str] = {}
    for item in value.split(","):
        name, idx = item.split(":", 1)
        idx_s = idx.strip()
        try:
            pairs[name.strip()] = int(idx_s)
        except ValueError:
            pairs[name.strip()] = idx_s
    return pairs


def parse_camera_names(value: str) -> set[str]:
    """`--flip-cameras wrist,top` 형식을 파싱."""
    return {name.strip() for name in value.split(",") if name.strip()}


def flip_observation_cameras(obs: dict, slots: set[str]) -> dict:
    """선택된 slot 의 raw camera observation 을 수직 반전.

    패턴 출처: orin/docs/legacy/hil_inference.py / orin/docs/legacy/lego_v1_inference.py (검증된 구현)
    """
    for slot in slots:
        obs[slot] = obs[slot][::-1, :, :].copy()
    return obs


# ── rename_map 적용 ───────────────────────────────────────────────────────────
def apply_rename_map(obs: dict) -> dict:
    """observation dict 의 camera key 를 학습 분포 에 맞춰 rename.

    학습 rename_map: top→camera1, wrist→camera2
    추론 시: robot.get_observation() 이 'observation.images.top' / 'observation.images.wrist' 반환
    → 이를 policy 가 기대하는 'observation.images.camera1' / 'observation.images.camera2' 로 변환.

    변환 대상 키가 없으면 무시 (orin/docs/legacy/hil_inference.py 의 slot 매핑 방식과 일관).
    """
    rename_pairs = [
        ("observation.images.top", "observation.images.camera1"),
        ("observation.images.wrist", "observation.images.camera2"),
    ]
    for src, dst in rename_pairs:
        if src in obs and dst not in obs:
            obs[dst] = obs.pop(src)
    return obs


# ── cameras.json 부가 설정 로드 ─────────────────────────────────────────────
def load_camera_config(camera_json_path: str) -> dict | None:
    """orin/config/cameras.json 을 로드하여 카메라 부가 설정 (rotation/fps/fourcc/flip) 만 반환.

    2026-05-24 udev rule 도입으로 device path 는 --cameras default (`/dev/cam_top`, `/dev/cam_wrist`) 로 일원화.
    cameras.json 은 부가 파라미터 (rotation/width/height/fps/fourcc/flip) 만 관리.
    """
    p = Path(camera_json_path)
    cameras_path = p if p.suffix == ".json" else p / "cameras.json"

    if not cameras_path.exists():
        return None

    try:
        with open(cameras_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[gate] cameras.json 로드 실패 ({cameras_path}): {e}", file=sys.stderr)
        return None


def apply_camera_config(
    args: argparse.Namespace,
    cameras_data: dict | None,
) -> argparse.Namespace:
    """cameras.json 의 부가 설정으로 카메라 파라미터·flip 을 채운다.

    cameras.json schema (2026-05-24, udev 도입 후):
      {"top":   {"rotation": -90, "width": 480, "height": 640, "fps": 30, "fourcc": "MJPG", "flip": false},
       "wrist": {"rotation":   0, "width": 640, "height": 480, "fps": 30, "fourcc": "MJPG", "flip": false}}
    device path 는 --cameras default 또는 CLI override 로 결정 (cameras.json 에 없음).
    """
    if cameras_data is not None:
        cam_params: dict[str, dict] = {}
        for cam_name in ("top", "wrist"):
            cam_entry = cameras_data.get(cam_name, {})
            rotation = cam_entry.get("rotation", 0)
            width = cam_entry.get("width", 640)
            height = cam_entry.get("height", 480)
            fps = cam_entry.get("fps", 30)
            fourcc = cam_entry.get("fourcc", "MJPG")
            if "rotation" not in cam_entry:
                print(
                    f"[gate] cameras.json.{cam_name}.rotation 미지정 — default rotation=0 적용 "
                    "(rotation 정합을 위해 cameras.json 에 명시 권장)",
                    file=sys.stderr,
                )
            cam_params[cam_name] = {
                "rotation": rotation,
                "width": width,
                "height": height,
                "fps": fps,
                "fourcc": fourcc,
            }
        args._camera_params = cam_params
    else:
        args._camera_params = {}

    # --flip-cameras: cameras.json 의 flip=true 카메라 자동 합산
    if cameras_data is not None and not args.flip_cameras:
        flip_names: set[str] = set()
        for cam_name in ("top", "wrist"):
            if cameras_data.get(cam_name, {}).get("flip", False):
                flip_names.add(cam_name)
        if flip_names:
            args.flip_cameras = flip_names
            print(f"[gate] flip_cameras ← {sorted(flip_names)} (cameras.json)")

    return args


# ── LoRA 로드 헬퍼 ────────────────────────────────────────────────────────────
def load_policy_with_lora(ckpt_dir: str, device: torch.device) -> SmolVLAPolicy:
    """LoRA adapter ckpt 를 로드해 SmolVLAPolicy 를 반환한다.

    패턴 출처: docs/reference/lerobot/src/lerobot/policies/factory.py (line 537-558)
    - PeftConfig.from_pretrained(ckpt_dir) → base_model_name_or_path 읽기
    - SmolVLAPolicy.from_pretrained(base_model) → base policy 로드
    - PeftModel.from_pretrained(policy, ckpt_dir) → adapter 적용

    의존성: peft>=0.10.0 필요.
      미설치 시 ImportError + 설치 안내 출력.
      설치: pip install peft>=0.10.0
      orin/pyproject.toml 에 미등록 (Category B+C 사용자 동의 후 추가 예정).
    """
    try:
        from peft import PeftConfig, PeftModel
    except ImportError as e:
        print(
            "[ERROR] peft 패키지가 설치되어 있지 않습니다.\n"
            "  leftarm_v2_inference.py 는 LoRA adapter 로드를 위해 peft 가 필요합니다.\n"
            "  설치 방법:\n"
            "    source ~/smolvla/orin/.hylion_arm/bin/activate\n"
            "    pip install peft>=0.10.0\n"
            "  (orin/pyproject.toml 에 peft 추가는 Category B+C 사용자 동의 후 처리 예정)",
            file=sys.stderr,
        )
        raise ImportError(f"peft 미설치: {e}") from e

    print(f"[lora] PeftConfig.from_pretrained({ckpt_dir!r})")
    peft_config = PeftConfig.from_pretrained(ckpt_dir)

    base_model_path = peft_config.base_model_name_or_path
    if not base_model_path:
        raise ValueError(
            f"adapter_config.json 에 base_model_name_or_path 가 없습니다 ({ckpt_dir}). "
            "adapter 가 올바르게 저장되었는지 확인하십시오."
        )

    print(f"[lora] base_model_name_or_path = {base_model_path!r}")
    print(f"[lora] SmolVLAPolicy.from_pretrained({base_model_path!r})")

    # base policy 로드 (smolvla_base from HF Hub)
    policy = SmolVLAPolicy.from_pretrained(base_model_path)

    print(f"[lora] PeftModel.from_pretrained (adapter={ckpt_dir!r})")
    # LoRA adapter 적용
    policy = PeftModel.from_pretrained(policy, ckpt_dir, config=peft_config)

    policy = policy.to(device)
    policy.eval()

    print("[lora] LoRA adapter 로드 완료")
    return policy


def main():
    parser = argparse.ArgumentParser(
        description=(
            "leftarm_v2_A2_pc_2026-05-17 LoRA adapter 추론 (Orin + SO-101 follower). "
            "orin/docs/legacy/hil_inference.py (사전학습 ckpt 전용) 와 독립 운용 — USER_OVERRIDE 옵션 W."
        )
    )
    parser.add_argument(
        "--task",
        choices=["task1", "task2", "task3"],
        required=True,
        help=(
            "수행할 task. "
            "task1: 'Pick up the blue and yellow doll and place it on the left side of the table'. "
            "task2: 'Hand the yellow can to the person'. "
            "task3: 'Hand the white can to the person' (학습 분포 외 일반화 검증, 2026-05-24 추가)."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="dry-run: action JSON dump only (follower 미동작) / live: 실 motor 송신.",
    )
    parser.add_argument(
        "--ckpt-dir",
        type=str,
        default=CKPT_LOCAL_DIR,
        help=(
            f"LoRA adapter ckpt 로컬 경로 또는 HF Hub repo_id. "
            f"default: {CKPT_LOCAL_DIR}. "
            "로컬 경로는 ~ 확장 지원."
        ),
    )
    parser.add_argument(
        "--follower-port",
        type=str,
        default="/dev/so_arm_left",
        help=(
            "Follower SO-101 serial port. default: /dev/so_arm_left (udev rule 도입 2026-05-24). "
            "우암으로 전환 시 --follower-port /dev/so_arm_right."
        ),
    )
    parser.add_argument(
        "--follower-id",
        type=str,
        default="leftarm_test_follower",
        help="Follower id for calibration file lookup. default: leftarm_test_follower (DGX 수집 정합 — base_config.yaml robot.id).",
    )
    parser.add_argument(
        "--cameras",
        type=parse_camera_arg,
        default=parse_camera_arg("top:/dev/cam_top,wrist:/dev/cam_wrist"),
        help=(
            "Camera mapping `name:device_path_or_idx,...`. "
            "default: top:/dev/cam_top,wrist:/dev/cam_wrist (udev rule 도입 2026-05-24). "
            "키: top, wrist (학습 rename_map 의 원본 키 — 내부에서 camera1/camera2 로 rename). "
            "정수 인덱스도 하위 호환 (예: top:2,wrist:0)."
        ),
    )
    parser.add_argument(
        "--flip-cameras",
        type=parse_camera_names,
        default=set(),
        help=(
            "수직 반전할 camera 이름 (예: wrist). "
            "--gate-json cameras.json.<name>.flip=true 로도 자동 적용 가능."
        ),
    )
    parser.add_argument(
        "--n-action-steps",
        type=int,
        default=50,
        help=(
            "Action chunk 당 실행 step 수. default=50 (config.json 수정값). "
            "안전 목적으로 낮추려면 5~10 권장."
        ),
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="전체 step 상한. default=50.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="dry-run mode: action history JSON 저장 경로 (필수 — dry-run 시).",
    )
    parser.add_argument(
        "--gate-json",
        type=str,
        default=None,
        help=(
            "orin/config/ 디렉터리 경로 또는 cameras.json 파일 경로. "
            "카메라 부가 설정 (rotation/width/height/fps/fourcc/flip) 을 로드한다. "
            "device path 는 --cameras default 또는 CLI override 로 결정 (udev rule 도입 2026-05-24)."
        ),
    )
    args = parser.parse_args()

    # ── task instruction 결정 ─────────────────────────────────────
    task_instruction = TASK_INSTRUCTIONS[args.task]
    print(f"[task] {args.task}: {task_instruction!r}")

    # ── ckpt 경로 결정 ────────────────────────────────────────────
    ckpt_dir_str = str(Path(args.ckpt_dir).expanduser())
    print(f"[ckpt] {ckpt_dir_str}")

    # ── cameras.json 부가 설정 적용 ───────────────────────────────
    if args.gate_json is not None:
        cameras_data = load_camera_config(args.gate_json)
        args = apply_camera_config(args, cameras_data)
    else:
        args._camera_params = {}

    # ── 필수 인자 최종 검증 ───────────────────────────────────────
    if args.mode == "dry-run" and args.output_json is None:
        parser.error("--output-json 은 dry-run 모드에서 필수입니다.")

    if len(args.cameras) != len(SLOT_MAP):
        parser.error(
            f"--cameras 는 정확히 {len(SLOT_MAP)} 개여야 합니다 (got {len(args.cameras)}). "
            f"예: --cameras top:<idx>,wrist:<idx>"
        )

    unknown_flip = args.flip_cameras - set(args.cameras)
    if unknown_flip:
        parser.error(
            f"--flip-cameras 에 알 수 없는 camera: {sorted(unknown_flip)}. "
            f"알려진 camera: {list(args.cameras)}."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}")

    # ── 1. LoRA adapter + base policy 로드 ───────────────────────
    # 패턴: docs/reference/lerobot/src/lerobot/policies/factory.py line 537-558
    # PeftConfig.from_pretrained → base_model_name_or_path → SmolVLAPolicy.from_pretrained
    # → PeftModel.from_pretrained (adapter 적용)
    policy = load_policy_with_lora(ckpt_dir_str, device)

    # n_action_steps 확인 및 적용
    # config.json 에 n_action_steps=50 이미 수정됨 (prod-test cycle 1 확인)
    # args.n_action_steps 으로 override 가능 (기본 50 — 필요 시 안전 목적으로 낮추기)
    measured_n_action_steps = getattr(policy.config, "n_action_steps", None)
    print(f"[policy.config] n_action_steps 실측값 = {measured_n_action_steps} → {args.n_action_steps} 적용")
    if measured_n_action_steps == 1:
        print("[WARNING] n_action_steps=1 감지 — 50 으로 강제 적용 (prof_train_setting §7-5 trap)", file=sys.stderr)
    policy.config.n_action_steps = args.n_action_steps

    # empty_cameras: ckpt config.json 값을 policy.config 에 강제 적용.
    # LoRA adapter 만 로드 시 base smolvla_base 의 default (=0) 가 들어와 학습 분포 (002+ 분기 = empty_cameras=1)
    # 와 mismatch 발생 → 추론 신뢰도 저하. ckpt config.json 의 값을 ground truth 로 사용.
    measured_empty = getattr(policy.config, "empty_cameras", None)
    ckpt_config_path = Path(ckpt_dir_str) / "config.json"
    ckpt_empty_cameras = None
    if ckpt_config_path.exists():
        with open(ckpt_config_path) as f:
            ckpt_empty_cameras = json.load(f).get("empty_cameras")
    if ckpt_empty_cameras is not None and ckpt_empty_cameras != measured_empty:
        print(
            f"[policy.config] empty_cameras {measured_empty} ≠ ckpt config.json {ckpt_empty_cameras} "
            f"→ 학습 분포 정합 위해 {ckpt_empty_cameras} 강제 적용"
        )
        policy.config.empty_cameras = ckpt_empty_cameras
        measured_empty = ckpt_empty_cameras
    else:
        print(f"[policy.config] empty_cameras = {measured_empty} (ckpt config.json = {ckpt_empty_cameras})")

    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        pretrained_path=ckpt_dir_str,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    # ── 2. Camera + Follower setup ─────────────────────────────────
    # 패턴: orin/docs/legacy/hil_inference.py / orin/docs/legacy/lego_v1_inference.py (검증된 구현)
    # SLOT_MAP: ["camera1", "camera2"] — policy 입력 키
    # cameras: {"top": idx, "wrist": idx} — 사용자 제공 키
    # 순서대로 slot 에 매핑 (top→camera1 slot, wrist→camera2 slot)
    # USB 2.0 hub 대역폭 한계 — fourcc="MJPG" 강제 (orin/docs/legacy/lego_v1_inference.py 패턴)
    # cameras.json 에서 읽은 카메라 파라미터 (rotation 정합 복원 — TODO-03-H 2026-05-18).
    # gate-json 미지정 시 _camera_params 가 빈 dict → default 적용 (rotation=0, 640x480, 30fps, MJPG).
    _cam_params = getattr(args, "_camera_params", {})

    camera_config: dict[str, OpenCVCameraConfig] = {}
    flip_slots: set[str] = set()
    for slot, (name, idx) in zip(SLOT_MAP, args.cameras.items()):
        p = _cam_params.get(name, {})
        rotation = p.get("rotation", 0)          # 수집 정합: top=-90, wrist=0
        width = p.get("width", 640)              # 수집 정합: top=480, wrist=640
        height = p.get("height", 480)            # 수집 정합: top=640, wrist=480
        fps = p.get("fps", 30)
        fourcc = p.get("fourcc", "MJPG")
        camera_config[slot] = OpenCVCameraConfig(
            index_or_path=idx,
            width=width,
            height=height,
            fps=fps,
            fourcc=fourcc,
            rotation=rotation,
        )
        if name in args.flip_cameras:
            flip_slots.add(slot)
        flip_note = ", flip=vertical" if slot in flip_slots else ""
        print(
            f"[camera] {slot} ← {name} (device {idx}, "
            f"{width}x{height} fps={fps} fourcc={fourcc} rotation={rotation}{flip_note})"
        )

    robot_cfg = SO101FollowerConfig(
        port=args.follower_port,
        id=args.follower_id,
        cameras=camera_config,
    )
    robot = SO101Follower(robot_cfg)

    # ── 3. SIGINT 핸들러 — graceful Ctrl+C ──────────────────────
    interrupted = False

    def _sigint_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        print(
            "\n[interrupt] Ctrl+C detected — finishing current step then disconnect.",
            file=sys.stderr,
        )

    signal.signal(signal.SIGINT, _sigint_handler)

    # ── 4. Inference loop ─────────────────────────────────────────
    # 패턴: orin/docs/legacy/hil_inference.py / orin/docs/legacy/lego_v1_inference.py inference loop (검증된 구현)
    # rename_map: observation dict 후처리 — top/wrist → camera1/camera2 rename
    action_history = []
    step_count = 0

    try:
        robot.connect()
        action_features = hw_to_dataset_features(robot.action_features, "action")
        obs_features = hw_to_dataset_features(robot.observation_features, "observation")
        ds_features = {**action_features, **obs_features}

        print(
            f"[loop] mode={args.mode} task={args.task} max_steps={args.max_steps} "
            f"n_action_steps={args.n_action_steps}"
        )
        print(f"[loop] instruction: {task_instruction!r}")

        while step_count < args.max_steps and not interrupted:
            obs = robot.get_observation()

            # flip 적용 (slot 기준 — 카메라가 camera_config 의 slot 키로 반환됨)
            if flip_slots:
                obs = flip_observation_cameras(obs, flip_slots)

            # rename_map 적용: observation.images.top → observation.images.camera1 등
            # robot.get_observation() 이 slot key ('camera1', 'camera2') 로 반환하면
            # 이미 정합 — 이 경우 apply_rename_map 은 no-op.
            # 만약 original camera key ('observation.images.top' 등) 로 반환하면 rename 적용.
            obs = apply_rename_map(obs)

            obs_frame = build_inference_frame(
                observation=obs,
                ds_features=ds_features,
                device=device,
                task=task_instruction,
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

    # ── 5. dry-run JSON dump ──────────────────────────────────────
    if args.mode == "dry-run":
        with open(args.output_json, "w") as f:
            json.dump(
                {
                    "ckpt_dir": ckpt_dir_str,
                    "task": args.task,
                    "task_instruction": task_instruction,
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

    print(f"[done] mode={args.mode} task={args.task} steps={step_count} interrupted={interrupted}")


if __name__ == "__main__":
    main()
