"""interactive_cli flow 6 — lerobot-record draccus 인자 동적 생성 + subprocess 호출.

레퍼런스 직접 인용:

[1] DatasetRecordConfig (lerobot_record.py line 161~211):
    repo_id: str                         — 필수 (예: "myuser/my_dataset")
    single_task: str                     — 필수 (자연어 태스크 설명)
    root: str | Path | None = None       — 로컬 저장 경로 (None → $HF_LEROBOT_HOME/repo_id)
    fps: int = 30                        — 기본 30fps
    episode_time_s: int | float = 60     — 에피소드 당 녹화 시간 (초)
    reset_time_s: int | float = 60       — 에피소드 간 리셋 시간 (초)
    num_episodes: int = 50               — 수집할 에피소드 수
    push_to_hub: bool = True             — HF Hub 자동 업로드 (interactive_cli 에서는 False 권장)
    streaming_encoding: bool = False     — 실시간 인코딩
    encoder_threads: int | None = None   — 인코더 스레드 수
    vcodec: str = "libsvtav1"            — 비디오 코덱

    __post_init__ (line 212~214):
        if self.single_task is None:
            raise ValueError("You need to provide a task as argument in `single_task`.")

[2] RecordConfig (line 217~258):
    robot: RobotConfig                   — 필수 (--robot.type 등)
    dataset: DatasetRecordConfig         — 필수
    teleop: TeleoperatorConfig | None    — 선택
    display_data: bool = False

[3] CLI 예시 (lerobot_record.py line 22~41):
    lerobot-record \\
        --robot.type=so100_follower \\
        --robot.port=/dev/tty.usbmodem58760431541 \\
        --robot.cameras="{laptop: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \\
        --robot.id=black \\
        --dataset.repo_id=<my_username>/<my_dataset_name> \\
        --dataset.num_episodes=2 \\
        --dataset.single_task="Grab the cube" \\
        --dataset.streaming_encoding=true \\
        --dataset.encoder_threads=2 \\
        --display_data=true

[4] 고정 인자 (D1 §4 매핑 표 — run_teleoperate.sh 직접 인용):
    --robot.type=so101_follower      (run_teleoperate.sh line 29)
    --robot.port=/dev/ttyACM1        (run_teleoperate.sh line 19: FOLLOWER_PORT)
    --robot.id=my_awesome_follower_arm  (run_teleoperate.sh line 21: FOLLOWER_ID)
    --teleop.type=so101_leader       (run_teleoperate.sh line 35)
    --teleop.port=/dev/ttyACM0       (run_teleoperate.sh line 20: LEADER_PORT)
    --teleop.id=my_awesome_leader_arm   (run_teleoperate.sh line 22: LEADER_ID)

[5] validation 항목 (D1 §4, push_dataset_hub.sh line 90~94 grep 패턴 재사용):
    1. repo_id 형식: <user>/<name> (push_dataset_hub.sh line 90~94)
    2. num_episodes 양수 정수
    3. data_kind_choice 유효 범위 (1~5)
    4. 카메라 인덱스가 flow 2 env_check 결과와 일치
"""

import os
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# 고정 인자 상수 (D1 §4 매핑 표 + run_teleoperate.sh 직접 인용)
# ---------------------------------------------------------------------------

# run_teleoperate.sh line 19~22
FOLLOWER_PORT = "/dev/ttyACM1"
LEADER_PORT = "/dev/ttyACM0"
FOLLOWER_ID = "my_awesome_follower_arm"
LEADER_ID = "my_awesome_leader_arm"

# run_teleoperate.sh line 27~35 (so101_follower, so101_leader)
ROBOT_TYPE = "so101_follower"
TELEOP_TYPE = "so101_leader"

# D1 §4 결정: interactive_cli 에서 push_to_hub=false (flow 7 에서 별도 처리)
PUSH_TO_HUB = "false"

# D1 §4 결정: streaming_encoding=true + encoder_threads=2 (lerobot_record.py line 33 예시 기반)
STREAMING_ENCODING = "true"
ENCODER_THREADS = "2"

# DatasetRecordConfig.fps 기본값 + 07b §1-2 fps=30 실측
DATASET_FPS = "30"

# D1 §3 매핑 표 — data_kind_choice → single_task
SINGLE_TASK_MAP: dict[int, str] = {
    1: "Pick up the object and place it in the target area.",
    2: "Push the object to the target position.",
    3: "Pick up the block and stack it on top of the other block.",
    4: "Open the drawer.",
    5: "Pick up the object and hand it over.",
}


# ---------------------------------------------------------------------------
# Validation 함수들
# ---------------------------------------------------------------------------

def _validate_repo_id(repo_id: str) -> tuple[bool, str]:
    """repo_id 형식 확인: <user>/<name>.

    push_dataset_hub.sh line 90~94 의 grep 패턴 재사용:
      grep -qE "^[^/]+/[^/]+$"
    """
    pattern = re.compile(r"^[^/]+/[^/]+$")
    if not pattern.match(repo_id):
        return False, (
            f"repo_id 형식 오류: '{repo_id}'\n"
            "  올바른 형식: <hf_username>/<dataset_name> (예: myuser/leftarm_pickplace_v1)"
        )
    return True, f"repo_id OK: {repo_id}"


def _validate_num_episodes(num_episodes: int) -> tuple[bool, str]:
    """num_episodes 양수 정수 확인."""
    if num_episodes <= 0:
        return False, f"num_episodes 는 양수여야 합니다: {num_episodes}"
    return True, f"num_episodes OK: {num_episodes}"


def _validate_data_kind_choice(choice: int) -> tuple[bool, str]:
    """data_kind_choice 유효 범위 (1~5) 확인."""
    if choice not in SINGLE_TASK_MAP:
        return False, (
            f"data_kind_choice 유효 범위 초과: {choice} (유효: 1~5)"
        )
    return True, f"data_kind_choice OK: {choice} ({SINGLE_TASK_MAP[choice]})"


def _validate_camera_indices(
    cam_wrist_left_index: int,
    cam_overview_index: int,
) -> tuple[bool, str]:
    """카메라 인덱스 유효성 확인 (flow 2 env_check 결과 기반).

    flow 2 env_check 가 probe 한 인덱스를 그대로 수신하므로
    음수 인덱스 여부 (OpenCV 오류 시 반환될 수 있는 값) 를 방어적으로 확인.
    D1 §4 validation 4항목: "카메라 인덱스가 flow 2 env_check 결과와 일치"
    — env_check 결과 자체를 전달받으므로, 유효 범위(0 이상) 를 최종 검증.
    """
    if cam_wrist_left_index < 0 or cam_overview_index < 0:
        return False, (
            f"카메라 인덱스 유효 범위 초과 — "
            f"wrist_left={cam_wrist_left_index}, overview={cam_overview_index} (0 이상이어야 함)"
        )
    return True, (
        f"카메라 인덱스 OK (flow 2 env_check): wrist_left={cam_wrist_left_index}, overview={cam_overview_index}"
    )


# ---------------------------------------------------------------------------
# 인자 동적 생성 (D1 §4 build_record_args 패턴 그대로)
# ---------------------------------------------------------------------------

def build_record_args(
    data_kind_choice: int,
    repo_id: str,
    num_episodes: int,
    cam_wrist_left_index: int = 0,
    cam_overview_index: int = 1,
) -> list[str]:
    """lerobot-record 인자 동적 생성.

    D1 §4 build_record_args 패턴 그대로 적용.
    고정 인자 + 사용자 입력 인자 결합.

    Args:
        data_kind_choice: flow 5 에서 선택한 번호 (1~5)
        repo_id: HF Hub ID (예: "myuser/leftarm_pickplace_v1")
        num_episodes: 수집할 에피소드 수
        cam_wrist_left_index: flow 2 env_check 결과 wrist_left 인덱스
        cam_overview_index: flow 2 env_check 결과 overview 인덱스

    Returns:
        lerobot-record 에 전달할 인자 리스트
    """
    # 카메라 인자 (D1 §4 cameras 형식 + fourcc=MJPG 강제)
    # fourcc=MJPG 근거: USB 2.0 hub 단일 사용 시 카메라 2대 동시 capture 가
    # YUYV 640x480x30fps × 2 = 294 Mbps 로 USB 2.0 (480 Mbps) 한계 근접 →
    # 다른 디바이스 (SO-ARM 2대) 와 경합 시 read_failed 발생.
    # MJPG 압축 시 ~10:1 이라 ~30 Mbps × 2 = 60 Mbps 로 여유 충분.
    # OpenCVCameraConfig.fourcc 필드 (configuration_opencv.py:65) 활용.
    cameras_str = (
        f"{{wrist_left: {{type: opencv, index_or_path: {cam_wrist_left_index},"
        f" width: 640, height: 480, fps: 30, fourcc: MJPG}},"
        f" overview: {{type: opencv, index_or_path: {cam_overview_index},"
        f" width: 640, height: 480, fps: 30, fourcc: MJPG}}}}"
    )

    # 로컬 저장 경로 (09_datacollector_setup.md DataCollector 데이터 경로)
    dataset_name = repo_id.split("/")[-1]
    data_root = os.path.expanduser(f"~/smolvla/datacollector/data/{dataset_name}")

    single_task = SINGLE_TASK_MAP[data_kind_choice]

    return [
        "lerobot-record",
        f"--robot.type={ROBOT_TYPE}",
        f"--robot.port={FOLLOWER_PORT}",
        f"--robot.id={FOLLOWER_ID}",
        f"--robot.cameras={cameras_str}",
        f"--teleop.type={TELEOP_TYPE}",
        f"--teleop.port={LEADER_PORT}",
        f"--teleop.id={LEADER_ID}",
        f"--dataset.repo_id={repo_id}",
        f"--dataset.root={data_root}",
        f"--dataset.num_episodes={num_episodes}",
        f"--dataset.single_task={single_task}",
        f"--dataset.push_to_hub={PUSH_TO_HUB}",
        f"--dataset.streaming_encoding={STREAMING_ENCODING}",
        f"--dataset.encoder_threads={ENCODER_THREADS}",
        f"--dataset.fps={DATASET_FPS}",
        "--display_data=false",
    ]


# ---------------------------------------------------------------------------
# 사용자 입력 수집
# ---------------------------------------------------------------------------

def _ask_repo_id() -> str | None:
    """사용자에게 HF repo_id 입력 요청.

    Returns:
        유효한 repo_id 문자열 / None: 종료
    """
    print()
    print("HF Hub repo ID 를 입력하세요.")
    print("  형식: <hf_username>/<dataset_name>")
    print("  예:   myuser/leftarm_pickplace_v1")
    print("  (종료: Ctrl+C)")
    print()

    while True:
        try:
            raw = input("repo_id: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not raw:
            print("  repo_id 를 입력하세요.")
            continue

        ok, msg = _validate_repo_id(raw)
        if ok:
            return raw
        print(f"  [오류] {msg}")


def _ask_num_episodes(default: int) -> int | None:
    """사용자에게 에피소드 수 입력 요청.

    Args:
        default: 권장 에피소드 수 (data_kind 기반)

    Returns:
        유효한 num_episodes / None: 종료
    """
    print()
    print(f"수집할 에피소드 수를 입력하세요. (기본값 Enter → {default})")
    print()

    while True:
        try:
            raw = input(f"num_episodes [{default}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not raw:
            return default

        if not raw.isdigit():
            print("  양수 정수를 입력하세요.")
            continue

        num = int(raw)
        ok, msg = _validate_num_episodes(num)
        if ok:
            return num
        print(f"  [오류] {msg}")


# ---------------------------------------------------------------------------
# flow 6 메인 함수
# ---------------------------------------------------------------------------

def flow6_record(
    data_kind_choice: int,
    single_task: str,
    default_num_episodes: int,
    cam_wrist_left_index: int,
    cam_overview_index: int,
) -> tuple[bool, str, str]:
    """flow 6: lerobot-record subprocess 호출.

    validation 4항목 통과 후 subprocess 실행.

    Args:
        data_kind_choice: flow 5 에서 선택한 번호 (1~5)
        single_task: flow 5 에서 결정된 task instruction
        default_num_episodes: flow 5 기반 권장 에피소드 수
        cam_wrist_left_index: flow 2 env_check 확인 wrist_left 인덱스
        cam_overview_index: flow 2 env_check 확인 overview 인덱스

    Returns:
        (success: bool, local_dataset_path: str, repo_id: str)
        local_dataset_path + repo_id 는 flow 7 transfer.py 에 전달.
    """
    print()
    print("=" * 60)
    print(" flow 6 — 데이터 수집 (lerobot-record)")
    print("=" * 60)
    print()
    print(f"  task: \"{single_task}\"")
    print()

    # validation: data_kind_choice
    ok, msg = _validate_data_kind_choice(data_kind_choice)
    if not ok:
        print(f"[flow 6] ERROR: {msg}", file=sys.stderr)
        return False, "", ""

    # 사용자 입력: repo_id
    repo_id = _ask_repo_id()
    if repo_id is None:
        print("[flow 6] 취소됨.")
        return False, "", ""

    # 사용자 입력: num_episodes
    num_episodes = _ask_num_episodes(default_num_episodes)
    if num_episodes is None:
        print("[flow 6] 취소됨.")
        return False, "", ""

    # validation 4항목 (D1 §4):
    #   1. repo_id 형식 확인 (data_kind_choice early-exit 이후 재확인)
    #   2. num_episodes 양수 정수
    #   3. data_kind_choice 유효 범위 (1~5) — 이미 line 314 에서 early-exit 처리됨;
    #      여기서는 나머지 validation 과 일관된 흐름을 위해 단일 루프로 통합
    #   4. 카메라 인덱스 유효성 (flow 2 env_check 결과 기반)
    validations = [
        _validate_repo_id(repo_id),
        _validate_num_episodes(num_episodes),
        _validate_camera_indices(cam_wrist_left_index, cam_overview_index),
    ]

    for ok, msg in validations:
        if not ok:
            print(f"[flow 6] validation 실패: {msg}", file=sys.stderr)
            return False, "", ""

    # 인자 동적 생성
    cmd_args = build_record_args(
        data_kind_choice=data_kind_choice,
        repo_id=repo_id,
        num_episodes=num_episodes,
        cam_wrist_left_index=cam_wrist_left_index,
        cam_overview_index=cam_overview_index,
    )

    # 로컬 저장 경로 (flow 7 에 전달)
    dataset_name = repo_id.split("/")[-1]
    local_dataset_path = os.path.expanduser(f"~/smolvla/datacollector/data/{dataset_name}")

    print()
    print("[flow 6] lerobot-record 실행 인자:")
    for arg in cmd_args:
        print(f"    {arg}")
    print()
    print(f"[flow 6] 데이터 저장 경로: {local_dataset_path}")
    print()
    print("Enter 를 누르면 lerobot-record 가 시작됩니다.")
    print("(종료하려면 Ctrl+C)")
    print()

    try:
        input()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[flow 6] 취소됨.")
        return False, "", ""

    result = subprocess.run(cmd_args, check=False)

    if result.returncode != 0:
        print()
        print(f"[flow 6] lerobot-record 비정상 종료 (returncode={result.returncode})")
        print("  데이터가 부분 저장되었을 수 있습니다.")
        print(f"  저장 경로: {local_dataset_path}")
        return False, local_dataset_path, repo_id

    print()
    print(f"[flow 6] 데이터 수집 완료. 저장 경로: {local_dataset_path}")
    return True, local_dataset_path, repo_id
