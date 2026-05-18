"""dgx/finetune/leftarm_v2/_lib.py — run_record.py / run_teleop.py 공용 헬퍼.

config/{base,record}_config.yaml 을 읽어 lerobot CLI 인자를 구성하는 공통 로직.
모든 값은 yaml 출처. 세션 의존값(포트·카메라 인덱스)도 env 가 아니라
base_config.yaml 의 hardware 섹션에서 읽으며, null(미확인) 이면 무조건 에러.
"""
import os
import sys
from pathlib import Path

import yaml


def die(msg):
    print(f"[run] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_configs(config_dir):
    """config/{base,record}_config.yaml 로드 → (base, record)."""
    loaded = {}
    for name in ("base_config.yaml", "record_config.yaml"):
        p = config_dir / name
        if not p.exists():
            die(f"config 파일 없음: {p}")
        with open(p, encoding="utf-8") as f:
            loaded[name] = yaml.safe_load(f)
    return loaded["base_config.yaml"], loaded["record_config.yaml"]


def expand_path(raw, what):
    """yaml 경로의 ${VAR}·~ 확장. 미확장 변수가 남으면 에러."""
    p = os.path.expanduser(os.path.expandvars(str(raw)))
    if "$" in p:
        die(
            f"{what} 경로의 환경변수가 미확장: {raw}\n"
            f"        → HF_HOME 미설정? venv 활성화 확인: "
            f"source ~/smolvla/dgx/.arm_finetune/bin/activate"
        )
    return Path(p)


def get_hardware(hw, key, hint):
    """base_config.yaml 의 hardware 값을 읽음. null(미확인) 이면 무조건 에러.

    포트·카메라 인덱스는 USB enumeration 의존 → 확인되지 않은(null) 값으로
    추측 실행되는 사고를 막기 위해 null 은 항상 에러로 처리한다 (fallback 없음).
    """
    v = hw.get(key)
    if v is None:
        die(
            f"base_config.yaml 의 hardware.{key} 가 null (미확인).\n"
            f"        → {hint}\n"
            f"        확인한 값을 config/base_config.yaml 의 hardware.{key} 에 직접 입력하세요."
        )
    return v


def check_calibration(base):
    """base_config.calibration 의 follower/leader 파일 존재 확인. 없으면 에러."""
    cal = base.get("calibration") or {}
    for role in ("follower", "leader"):
        raw = cal.get(role)
        if not raw:
            die(f"base_config.yaml 의 calibration.{role} 미설정")
        p = expand_path(raw, f"calibration.{role}")
        if not p.exists():
            die(
                f"{role} 캘리브레이션 파일 없음: {p}\n"
                f"        → lerobot-calibrate 또는 dgx/scripts/run_teleoperate.sh 로 "
                f"캘리브레이션 먼저 수행하세요."
            )
    return cal


def build_cameras_arg(cameras_cfg, indices):
    """record_config.cameras (녹화 파라미터) + hardware 인덱스 → draccus --robot.cameras 문자열."""
    parts = []
    for cam_name, params in cameras_cfg.items():
        fields = ["type: opencv", f"index_or_path: {indices[cam_name]}"]
        fields += [f"{k}: {val}" for k, val in params.items()]
        parts.append(f"{cam_name}: {{{', '.join(fields)}}}")
    return "{" + ", ".join(parts) + "}"


def resolve_robot_teleop(base, with_cameras=True):
    """robot/teleop 공통 인자 구성 + 세션값(포트·카메라 인덱스) 해소.

    lerobot-record 와 lerobot-teleoperate 가 공유하는 --robot.* / --teleop.* 인자.
    robot·teleop·cameras 는 base_config.yaml 의 물리 셋업 섹션에서 읽는다 (record/train 공용).
    반환: (args, summary)
      args    — lerobot CLI 인자 리스트 (--robot.type ... --teleop.id)
      summary — 출력용 dict {follower_port, leader_port, cameras}
    """
    hw = base.get("hardware") or {}
    follower_port = get_hardware(
        hw, "follower_port",
        "lerobot-find-port 로 follower 포트 확인 (check_port_and_camera_index.py)")
    leader_port = get_hardware(
        hw, "leader_port",
        "lerobot-find-port 로 leader 포트 확인 (check_port_and_camera_index.py)")
    cam_indices = {}
    if with_cameras:
        for cam_name in base["cameras"]:
            cam_indices[cam_name] = get_hardware(
                hw, f"camera_{cam_name}_index",
                f"v4l2-ctl 로 {cam_name} 카메라 /dev/videoN 확인 (check_port_and_camera_index.py)")

    args = [
        f"--robot.type={base['robot']['type']}",
        f"--robot.port={follower_port}",
        f"--robot.id={base['robot']['id']}",
    ]
    if with_cameras:
        args.append(f"--robot.cameras={build_cameras_arg(base['cameras'], cam_indices)}")
    args += [
        f"--teleop.type={base['teleop']['type']}",
        f"--teleop.port={leader_port}",
        f"--teleop.id={base['teleop']['id']}",
    ]
    return args, {"follower_port": follower_port, "leader_port": leader_port,
                  "cameras": cam_indices}
