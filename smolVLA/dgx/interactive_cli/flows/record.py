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
    4. 카메라 인덱스/경로가 cameras.json 검출 결과 또는 hardcoded fallback 과 일치

[6] OpenCVCameraConfig (configuration_opencv.py line 61):
    index_or_path: int | Path
    — 정수 인덱스 (예: 0) 와 str/Path 경로 (예: /dev/video0) 둘 다 지원.
    draccus YAML 인자: index_or_path 필드에 /dev/video0 같은 str 직접 전달 가능.
    근거: camera_opencv.py L158: cv2.VideoCapture(self.index_or_path, self.backend)
    — VideoCapture 는 int/str 모두 수용.

이식 원본:
  docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/record.py

이식 변경 사항 (14_dgx_cli_flow.md §3-4, X2 명세):
  - data_root 경로: ~/smolvla/datacollector/data/{dataset_name}
                 → ~/smolvla/dgx/data/{dataset_name}
    (원본 line 194 + line 367: `~/smolvla/datacollector/data/` → `~/smolvla/dgx/data/`)
  - 기타 모든 상수·함수·로직 그대로 재사용.

D12 변경 사항:
  - _load_configs_for_record(configs_dir) helper 신설 — cameras.json + ports.json 로드.
    precheck.py _run_calibrate() L979~1001 D9 패턴 동일 (JSONDecodeError fallback).
  - build_record_args() 에 cam_wrist_left_index/cam_overview_index 타입을 int|str 로 확장.
  - flow6_record() 에 configs_dir 인자 추가 — cameras.json·ports.json 로드 후 인자 갱신.
  - _validate_camera_indices() 를 int|str 수용으로 확장 (str 은 /dev/videoN 형식 허용).
  - 실행 직전 config 출처 명시 출력 (cameras/ports source 안내).
"""

import json
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
# Config 로드 (D12: cameras.json + ports.json — D9 패턴 동일)
# ---------------------------------------------------------------------------

def _load_configs_for_record(configs_dir: Path) -> "tuple[dict, dict]":
    """cameras.json + ports.json 로드. 미설정 시 빈 dict.

    D9 패턴 (precheck.py _run_calibrate L979~1001) 동일 — JSONDecodeError 시 fallback.

    cameras.json 형식 (D6/D7 저장):
      {"wrist_left": {"index": "/dev/video0"}, "overview": {"index": "/dev/video2"}}

    ports.json 형식 (D7 저장):
      {"follower_port": "/dev/ttyACM1", "leader_port": "/dev/ttyACM0"}

    Args:
        configs_dir: dgx/interactive_cli/configs/ 경로

    Returns:
        (cameras_data, ports_data) — 각 dict, 미존재 또는 파싱 실패 시 빈 dict
    """
    cameras_data: dict = {}
    ports_data: dict = {}
    cameras_path = configs_dir / "cameras.json"
    ports_path = configs_dir / "ports.json"

    for path, target, label in [
        (cameras_path, cameras_data, "cameras"),
        (ports_path, ports_data, "ports"),
    ]:
        if path.exists():
            try:
                with path.open() as f:
                    data = json.load(f)
                target.update(data)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[record] 경고: {label}.json 로드 실패 ({e}) — hardcoded fallback")

    return cameras_data, ports_data


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
    cam_wrist_left_index: "int | str",
    cam_overview_index: "int | str",
) -> "tuple[bool, str]":
    """카메라 인덱스/경로 유효성 확인.

    D1 §4 validation 4항목: "카메라 인덱스가 flow 2 env_check 결과와 일치"

    D12 확장: cameras.json 에서 로드한 str 경로 (/dev/videoN) 도 수용.
    OpenCVCameraConfig.index_or_path: int | Path (configuration_opencv.py L61) 에 맞춰
    — str 경로는 /dev/ 로 시작해야 유효. int 는 0 이상이어야 유효.
    """
    def _check_one(val: "int | str", label: str) -> "tuple[bool, str]":
        if isinstance(val, int):
            if val < 0:
                return False, f"{label}={val} (int 인덱스는 0 이상이어야 함)"
        elif isinstance(val, str):
            if not val.startswith("/dev/"):
                return False, f"{label}='{val}' (str 경로는 /dev/ 로 시작해야 함)"
        else:
            return False, f"{label} 타입 오류 (int 또는 str 경로 필요)"
        return True, ""

    ok_w, msg_w = _check_one(cam_wrist_left_index, "wrist_left")
    if not ok_w:
        return False, f"카메라 인덱스/경로 유효 범위 초과 — {msg_w}"
    ok_o, msg_o = _check_one(cam_overview_index, "overview")
    if not ok_o:
        return False, f"카메라 인덱스/경로 유효 범위 초과 — {msg_o}"

    return True, (
        f"카메라 인덱스/경로 OK: wrist_left={cam_wrist_left_index}, overview={cam_overview_index}"
    )


# ---------------------------------------------------------------------------
# 인자 동적 생성 (D1 §4 build_record_args 패턴 그대로 + data_root 경로 변경)
# ---------------------------------------------------------------------------

def build_record_args(
    data_kind_choice: int,
    repo_id: str,
    num_episodes: int,
    cam_wrist_left_index: "int | str" = 0,
    cam_overview_index: "int | str" = 1,
    single_task: "str | None" = None,
    follower_port: str = FOLLOWER_PORT,
    leader_port: str = LEADER_PORT,
) -> "list[str]":
    """lerobot-record 인자 동적 생성.

    D1 §4 build_record_args 패턴 그대로 적용.
    고정 인자 + 사용자 입력 인자 결합.

    이식 변경: data_root 경로
      원본: ~/smolvla/datacollector/data/{dataset_name}
      dgx:  ~/smolvla/dgx/data/{dataset_name}

    D12 변경:
      - cam_wrist_left_index / cam_overview_index 타입을 int|str 로 확장.
        str 경로 (/dev/videoN) 는 draccus CLI 에서 index_or_path 필드에 직접 전달 가능.
        근거: OpenCVCameraConfig.index_or_path: int | Path (configuration_opencv.py L61).
      - follower_port / leader_port 를 외부에서 주입 가능하도록 인자화.
        기본값은 기존 hardcoded 상수 (ports.json 미설정 시 호환).

    Args:
        data_kind_choice: flow 5 에서 선택한 번호 (1~5)
        repo_id: HF Hub ID (예: "myuser/leftarm_pickplace_v1")
        num_episodes: 수집할 에피소드 수
        cam_wrist_left_index: wrist_left 카메라 인덱스(int) 또는 경로(str, 예: /dev/video0)
        cam_overview_index: overview 카메라 인덱스(int) 또는 경로(str, 예: /dev/video2)
        single_task: G2-a 사용자 확인/커스텀 결과 (None 시 SINGLE_TASK_MAP 기본값 사용)
        follower_port: follower SO-ARM 포트 (ports.json 로드 결과 또는 hardcoded fallback)
        leader_port: leader SO-ARM 포트 (ports.json 로드 결과 또는 hardcoded fallback)

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

    # 로컬 저장 경로 — dgx 경로로 변경 (원본: ~/smolvla/datacollector/data/)
    dataset_name = repo_id.split("/")[-1]
    data_root = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")

    # G2-b: single_task 파라미터 우선 — None 이면 SINGLE_TASK_MAP 기본값 사용
    # (G2-a 에서 사용자 커스텀 결정 시 해당 값 전달됨)
    if single_task is None:
        single_task = SINGLE_TASK_MAP[data_kind_choice]

    return [
        "lerobot-record",
        f"--robot.type={ROBOT_TYPE}",
        f"--robot.port={follower_port}",
        f"--robot.id={FOLLOWER_ID}",
        f"--robot.cameras={cameras_str}",
        f"--teleop.type={TELEOP_TYPE}",
        f"--teleop.port={leader_port}",
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

def _ask_repo_id() -> "str | None":
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


def _ask_num_episodes(default: int) -> "int | None":
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
    cam_wrist_left_index: "int | str" = 0,
    cam_overview_index: "int | str" = 1,
    configs_dir: "Path | None" = None,
) -> "tuple[bool, str, str]":
    """flow 6: lerobot-record subprocess 호출.

    원본 datacollector record.py flow6_record 함수 그대로.
    validation 4항목 통과 후 subprocess 실행.

    이식 변경: data_root 경로 (build_record_args 내부 처리 + local_dataset_path)
      ~/smolvla/datacollector/data/ → ~/smolvla/dgx/data/

    D12 변경:
      - configs_dir 인자 추가 — cameras.json·ports.json 로드.
        None 이면 hardcoded fallback (기존 동작과 동일).
      - 로드 성공 시 cam_wrist_left_index / cam_overview_index / follower_port / leader_port 갱신.
      - 실행 직전 config 출처 명시 출력.

    Args:
        data_kind_choice: flow 5 에서 선택한 번호 (1~5)
        single_task: flow 5 에서 결정된 task instruction
        default_num_episodes: flow 5 기반 권장 에피소드 수
        cam_wrist_left_index: wrist_left 카메라 인덱스(int) 또는 경로(str). configs_dir 전달 시 덮어씀.
        cam_overview_index: overview 카메라 인덱스(int) 또는 경로(str). configs_dir 전달 시 덮어씀.
        configs_dir: dgx/interactive_cli/configs/ 경로. None 이면 hardcoded fallback.

    Returns:
        (success: bool, local_dataset_path: str, repo_id: str)
        local_dataset_path + repo_id 는 flow 7 transfer.py 에 전달.
        repo_id 는 mode.py 의 G-4 학습 전환 dataset_name 인계에도 활용.
    """
    print()
    print("=" * 60)
    print(" flow 6 — 데이터 수집 (lerobot-record)")
    print("=" * 60)
    print()

    # D12: cameras.json + ports.json 로드 (D9 패턴 — precheck.py _run_calibrate 동일)
    follower_port: str = FOLLOWER_PORT
    leader_port: str = LEADER_PORT
    cameras_source = "hardcoded fallback"
    ports_source = "hardcoded fallback"

    if configs_dir is not None:
        cameras_data, ports_data = _load_configs_for_record(configs_dir)

        # cameras.json 에서 wrist_left / overview index 추출
        wrist_idx = cameras_data.get("wrist_left", {}).get("index")
        overview_idx = cameras_data.get("overview", {}).get("index")
        if wrist_idx is not None:
            cam_wrist_left_index = wrist_idx
            cameras_source = "cameras.json 검출 결과"
        if overview_idx is not None:
            cam_overview_index = overview_idx
            cameras_source = "cameras.json 검출 결과"

        # ports.json 에서 follower_port / leader_port 추출
        fp = ports_data.get("follower_port")
        lp = ports_data.get("leader_port")
        if fp:
            follower_port = fp
            ports_source = "ports.json 검출 결과"
        if lp:
            leader_port = lp
            ports_source = "ports.json 검출 결과"

    # config 출처 안내 (D12 §Step 4)
    print("[record] config 출처:")
    if cameras_source == "cameras.json 검출 결과":
        print(
            f"  cameras: wrist_left={cam_wrist_left_index},"
            f" overview={cam_overview_index} ({cameras_source})"
        )
    else:
        print(
            "  cameras: hardcoded (wrist_left:0, overview:1) — cameras.json 미설정"
        )
    if ports_source == "ports.json 검출 결과":
        print(
            f"  ports: follower={follower_port},"
            f" leader={leader_port} ({ports_source})"
        )
    else:
        print(
            "  ports: hardcoded (ttyACM1, ttyACM0) — ports.json 미설정"
        )
    if cameras_source != "cameras.json 검출 결과" or ports_source != "ports.json 검출 결과":
        print(
            "  ⚠ 미설정 항목 — v4l2 메타 device 차단 가능."
            " precheck 옵션 1 (새 학습) 권장."
        )
    print()

    # G2-a: 사용자 task 텍스트 확인 / 커스텀 입력 분기
    # lerobot_record.py DatasetRecordConfig.single_task (line 161~) 직접 인용:
    #   single_task: str — 필수 (모든 frame 에 붙는 자연어 task 설명, VLA instruction 으로 사용)
    print("=" * 60)
    print(" 학습 task 텍스트")
    print("=" * 60)
    print()
    print("  데이터셋의 모든 frame 에 붙는 자연어 task 설명입니다.")
    print("  VLA 모델 학습 시 instruction 으로 사용됩니다.")
    print()
    print(f"  기본 task (data_kind 매핑): \"{single_task}\"")
    print()
    print("  (1) 기본값 사용 (Enter)")
    print("  (2) 커스텀 task 입력")
    print()

    try:
        raw_choice = input("번호 선택 [1~2, Enter=1 기본값]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[flow 6] 취소됨.")
        return False, "", ""

    if raw_choice == "2":
        try:
            custom_task = input(
                "  커스텀 task 입력 (예: 'Pick the red block and place it in the green box'): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 6] 취소됨.")
            return False, "", ""
        if custom_task:
            single_task = custom_task
            print(f"  [info] 커스텀 task 적용: \"{single_task}\"")
        else:
            print(f"  [info] 빈 입력 — 기본값 사용: \"{single_task}\"")
    else:
        print(f"  [info] 기본값 적용: \"{single_task}\"")

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
    #   3. data_kind_choice 유효 범위 (1~5) — 이미 위에서 early-exit 처리됨;
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

    # 인자 동적 생성 (G2-b: 결정된 single_task 전달 — 커스텀 또는 기본값)
    # D12: follower_port / leader_port 는 ports.json 로드 결과 또는 hardcoded fallback
    cmd_args = build_record_args(
        data_kind_choice=data_kind_choice,
        repo_id=repo_id,
        num_episodes=num_episodes,
        cam_wrist_left_index=cam_wrist_left_index,
        cam_overview_index=cam_overview_index,
        single_task=single_task,
        follower_port=follower_port,
        leader_port=leader_port,
    )

    # 로컬 저장 경로 (flow 7 에 전달) — dgx 경로로 변경
    dataset_name = repo_id.split("/")[-1]
    local_dataset_path = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")

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
