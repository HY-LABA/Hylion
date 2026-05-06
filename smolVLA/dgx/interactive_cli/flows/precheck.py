"""interactive_cli — teleop 진입 직전 사전 점검 (사용자 합의 흐름).

TODO-D4 (07_e2e_pilot_and_cleanup, 2026-05-04):
  ANOMALIES 07-#3 ORCHESTRATOR_GAP 후속 — spec 갭 보완.
  수집 mode 의 teleop 진입 직전 *모터 포트·카메라 인덱스·캘리브 위치* 표시 + 분기.

분기 3 종:
  (1) 새 학습 데이터 수집 시작 — find-port + find-cameras 자동 재실행 + 캘리브 별도 묻기
  (2) 기존 설정 그대로 진행 (캘리브 재사용)
  (3) 취소

저장 위치 근거:
  - 모터 포트: dgx/interactive_cli/configs/ports.json
    형식: {"follower_port": <str|null>, "leader_port": <str|null>}
    orin/config/ports.json 패턴 미러 (15_orin_config_policy.md §2).
    초기값 null — 시연장 셋업 후 (1) 선택 시 갱신.
  - 카메라 인덱스: dgx/interactive_cli/configs/cameras.json
    형식: {"wrist_left": {"index": <str path|null>}, "overview": {"index": <str path|null>}}
    예시: {"wrist_left": {"index": "/dev/video2"}, "overview": {"index": "/dev/video4"}}
    _run_find_cameras_split() 이 str path (Linux /dev/video* 경로) 또는 None 을 저장.
    (참고: record.py 는 현재 cameras.json 을 읽지 않고 하드코딩 int 인덱스 사용 — BACKLOG 07-#4)
    dgx 카메라 명칭: record.py flow6_record() 의 cam_wrist_left_index / cam_overview_index 기반.
  - 캘리브 저장 위치: lerobot upstream 표준
    lerobot/src/lerobot/utils/constants.py line 74-75 직접 인용:
      default_calibration_path = HF_LEROBOT_HOME / "calibration"
      HF_LEROBOT_CALIBRATION = Path(os.getenv("HF_LEROBOT_CALIBRATION", default_calibration_path))
    → 기본값: ~/.cache/huggingface/lerobot/calibration/
    환경변수 HF_LEROBOT_CALIBRATION 으로 override 가능.

레퍼런스:
  - lerobot/src/lerobot/utils/constants.py (HF_LEROBOT_CALIBRATION, line 74-75) — 캘리브 위치
  - lerobot/src/lerobot/scripts/lerobot_find_port.py (find_port(), L30-L64):
    find_port() L47: ports_before = find_available_ports()
    find_port() L51: input() — Remove 후 Enter
    find_port() L53-L55: time.sleep(0.5) + ports_after + ports_diff = set(before) - set(after)
    → 본 모듈은 이 패턴을 subprocess 없이 직접 glob 로 구현
  - lerobot/src/lerobot/cameras/opencv/camera_opencv.py (find_cameras, line 286-337):
    Linux: Path("/dev").glob("video*") → targets_to_scan 패턴 직접 인용.
    신규 device 검출: 분리/재연결 glob 비교 방식.
  - lerobot/src/lerobot/cameras/opencv/camera_opencv.py (VideoCapture.read, line 343-348):
    cv2.VideoCapture(target) + ret, frame = videocapture.read() 패턴.
    → _get_streamable_video_devices: 동일 패턴으로 cv2 read 가능한 device 만 필터링.
  - lerobot/src/lerobot/scripts/lerobot_find_cameras.py (save_image, line 130-151):
    PIL Image.fromarray + path.parent.mkdir 패턴 인용 (ssh 모드 저장).
  - orin/config/ports.json, cameras.json — 저장 파일 패턴
  - dgx/interactive_cli/flows/record.py — cam_wrist_left_index / cam_overview_index 명칭 기준
"""

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from flows._back import is_back


# ---------------------------------------------------------------------------
# 저장 파일 경로 상수
# ---------------------------------------------------------------------------

_PORTS_FILENAME = "ports.json"
_CAMERAS_FILENAME = "cameras.json"
_CALIBRATION_FILENAME = "calibration.json"

# 포트 JSON 초기 구조 (orin/config/ports.json 패턴 미러)
_PORTS_DEFAULT: dict = {"follower_port": None, "leader_port": None}

# 카메라 JSON 초기 구조 (dgx 명칭: wrist_left/overview — record.py 기반)
_CAMERAS_DEFAULT: dict = {
    "wrist_left": {"index": None},
    "overview": {"index": None},
}

# 캘리브레이션 JSON 초기 구조 — 첫 calibrate 성공 시 자동 생성
# follower_id / leader_id 는 다음 실행 기본값으로 사용 (so_follower.py 패턴: ID 로 파일 로드)
_CALIBRATION_DEFAULT: dict = {
    "follower_id": None,
    "leader_id": None,
    "follower_type": "so101_follower",
    "leader_type": "so101_leader",
    "calibrated_at": None,
}


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _prompt(message: str) -> str:
    """input() 래퍼 — EOFError·KeyboardInterrupt 보호."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise KeyboardInterrupt


def _get_configs_dir(script_dir: Path) -> Path:
    """dgx/interactive_cli/configs/ 경로 반환.

    script_dir: dgx/interactive_cli/ 경로 (mode.py 기준 상위).
    configs/ 는 script_dir / "configs" 에 위치.
    """
    return script_dir / "configs"


def _load_json_or_default(path: Path, default: dict) -> dict:
    """JSON 파일 로드. 미존재 또는 파싱 실패 시 default 반환."""
    try:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return default.copy()


def _save_json(path: Path, data: dict) -> bool:
    """JSON 파일 저장. 성공 시 True, 실패 시 False."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return True
    except OSError as e:
        print(f"[precheck] 경고: {path.name} 저장 실패: {e}", file=sys.stderr)
        return False


def _get_calib_dir() -> Path:
    """lerobot 표준 캘리브레이션 저장 디렉터리 반환.

    lerobot/src/lerobot/utils/constants.py line 66-75 직접 인용:
      from huggingface_hub.constants import HF_HOME
      default_cache_path = Path(HF_HOME) / "lerobot"
      HF_LEROBOT_HOME = Path(os.getenv("HF_LEROBOT_HOME", default_cache_path)).expanduser()
      default_calibration_path = HF_LEROBOT_HOME / "calibration"
      HF_LEROBOT_CALIBRATION = Path(os.getenv("HF_LEROBOT_CALIBRATION", default_calibration_path)).expanduser()

    환경변수 우선순위:
      HF_LEROBOT_CALIBRATION > HF_LEROBOT_HOME/calibration > ~/.cache/huggingface/lerobot/calibration
    """
    # HF_LEROBOT_CALIBRATION 환경변수 우선
    if "HF_LEROBOT_CALIBRATION" in os.environ:
        return Path(os.environ["HF_LEROBOT_CALIBRATION"]).expanduser()

    # HF_LEROBOT_HOME/calibration
    if "HF_LEROBOT_HOME" in os.environ:
        return Path(os.environ["HF_LEROBOT_HOME"]).expanduser() / "calibration"

    # 기본: HF_HOME/lerobot/calibration
    # HF_HOME 기본값: ~/.cache/huggingface (huggingface_hub.constants.HF_HOME)
    hf_home_default = Path.home() / ".cache" / "huggingface"
    hf_home = Path(os.environ.get("HF_HOME", str(hf_home_default))).expanduser()
    return hf_home / "lerobot" / "calibration"


def _format_ports(ports: dict) -> str:
    """포트 정보 표시용 문자열."""
    follower = ports.get("follower_port")
    leader = ports.get("leader_port")
    if follower is None and leader is None:
        return "(미설정 — lerobot-find-port 실행 필요)"
    return f"follower={follower or '미설정'}  leader={leader or '미설정'}"


def _format_cameras(cameras: dict) -> str:
    """카메라 인덱스 표시용 문자열."""
    wrist_idx = cameras.get("wrist_left", {}).get("index")
    overview_idx = cameras.get("overview", {}).get("index")
    if wrist_idx is None and overview_idx is None:
        return "(미설정 — lerobot-find-cameras 실행 필요)"
    return (
        f"wrist_left={wrist_idx if wrist_idx is not None else '미설정'}  "
        f"overview={overview_idx if overview_idx is not None else '미설정'}"
    )


# ---------------------------------------------------------------------------
# find-port / find-cameras / calibrate 실행 (대화형 subprocess)
# ---------------------------------------------------------------------------

def _run_find_port(configs_dir: Path) -> bool:
    """lerobot-find-port 를 subprocess 로 실행 (대화형).

    lerobot/src/lerobot/scripts/lerobot_find_port.py find_port() 패턴:
      - 사용자에게 USB 케이블 제거/재연결 요청
      - 포트 발견 후 출력
    발견된 포트를 configs_dir/ports.json 에 저장 (사용자가 출력 보고 직접 입력 방식).

    lerobot-find-port 는 leader / follower 2번 실행 필요 (1번에 1포트).
    출력에서 포트 경로 파싱 → ports.json 갱신.

    Returns:
        True: 2회 실행 완료 / False: 중단 또는 오류
    """
    print()
    print("[precheck] lerobot-find-port 실행 (2회 — leader / follower)")
    print("  주의: 각 실행마다 USB 케이블 제거/재연결 지시에 따르세요.")
    print()

    ports: dict = {"follower_port": None, "leader_port": None}

    for arm_label in ("follower", "leader"):
        print(f"  [{arm_label}] lerobot-find-port 실행 중...")
        print(f"  ({arm_label} 팔의 USB 케이블을 분리/재연결하세요 — 프롬프트 지시 따르세요)")
        print()

        try:
            result = subprocess.run(
                ["lerobot-find-port"],
                check=False,
            )
        except FileNotFoundError:
            print(
                "[precheck] 오류: lerobot-find-port 명령을 찾을 수 없습니다.",
                file=sys.stderr,
            )
            print(
                "          venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate",
                file=sys.stderr,
            )
            return False

        if result.returncode != 0:
            print(f"[precheck] 경고: lerobot-find-port 비정상 종료 (rc={result.returncode})")

        print()
        port_val = _prompt(
            f"  발견된 {arm_label} 포트를 입력하세요 (예: /dev/ttyACM0, Enter=건너뜀): "
        )
        if port_val:
            ports[f"{arm_label}_port"] = port_val
        print()

    # ports.json 저장
    ports_path = configs_dir / _PORTS_FILENAME
    if _save_json(ports_path, ports):
        print(f"[precheck] 포트 정보 저장: {ports_path}")
        print(f"  follower={ports['follower_port'] or '(건너뜀)'}  leader={ports['leader_port'] or '(건너뜀)'}")
    return True


def _run_find_port_self(configs_dir: Path) -> bool:
    """모터 포트 식별 — lerobot-find-port 자체 로직 (subprocess 회피).

    lerobot/src/lerobot/scripts/lerobot_find_port.py find_port() L47-L64 패턴 직접 미러:
      L47: ports_before = find_available_ports()
           → glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*') + glob('/dev/tty*') 상위 집합
      L51: input() — "Remove the USB cable ... and press Enter"
      L53: time.sleep(0.5)  # Allow some time for port to be released
      L54: ports_after = find_available_ports()
      L55: ports_diff = list(set(ports_before) - set(ports_after))
      L57-L64: len(ports_diff) == 1 → 발견 / 0 → OSError / >1 → OSError

    본 함수 차이:
      - subprocess 호출 X (lerobot-find-port 설치 불필요, OSError 회피)
      - /dev/ttyACM* + /dev/ttyUSB* 직접 glob (Linux 시리얼 포트 표준 패턴)
      - follower 분리 → 재연결 → leader 분리 → 재연결 순서
      - 분리해서 사라진 것 = 해당 arm 포트 (lerobot-find-port 동일 패턴)
      - 발견 실패 시 수동 입력 fallback (사용자 UX 보호)

    흐름:
        1. baseline = glob /dev/ttyACM* + /dev/ttyUSB*
        2. [follower] "follower 분리 후 Enter" → after = glob → removed = baseline - after
        3. removed 1개 = follower port. 0개 = 재시도 or 수동. >1개 = 수동
        4. "follower 재연결 후 Enter"
        5. [leader] 동일 패턴
        6. ports.json 저장

    Args:
        configs_dir: configs/ 디렉터리 (ports.json 저장 대상)

    Returns:
        True: 완료 (부분 성공 포함) / False: 사용자 취소
    """
    def _get_serial_ports() -> set:
        """현재 연결된 /dev/ttyACM* + /dev/ttyUSB* 목록 (집합)."""
        acm = glob.glob("/dev/ttyACM*")
        usb = glob.glob("/dev/ttyUSB*")
        return set(acm + usb)

    print()
    print("[precheck] 모터 포트 식별 — USB 분리/재연결 방식")
    print()
    print("  lerobot-find-port 와 같은 방식으로 follower / leader 포트를 구분합니다.")
    print("  (lerobot-find-port subprocess 없이 직접 /dev/ttyACM* + /dev/ttyUSB* 감시)")
    print()

    ports: dict = {"follower_port": None, "leader_port": None}

    # baseline: 현재 연결된 시리얼 포트
    baseline = _get_serial_ports()
    print(f"  현재 감지된 시리얼 포트: {sorted(baseline) or '(없음)'}")
    print()

    for arm_label in ("follower", "leader"):
        print(f"  [{arm_label}] 포트 식별")
        print("  ─────────────────────────────────────────────────")
        print(f"  {arm_label} 팔의 USB 케이블을 분리하세요.")
        print("  분리 완료 후 Enter 를 누르세요.")
        print()

        try:
            _prompt(f"  {arm_label} USB 분리 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        # lerobot_find_port.py L53: time.sleep(0.5)
        time.sleep(0.5)

        # lerobot_find_port.py L54-L55: ports_after + ports_diff = set(before) - set(after)
        after_disconnect = _get_serial_ports()
        removed = sorted(baseline - after_disconnect)

        print()
        if len(removed) == 1:
            # lerobot_find_port.py L57: "The port of this MotorsBus is '{port}'"
            detected_port = removed[0]
            print(f"  [검출] {arm_label} 포트: {detected_port}")
            ports[f"{arm_label}_port"] = detected_port
        elif len(removed) == 0:
            # lerobot_find_port.py L61: "Could not detect the port. No difference was found"
            print(f"  [경고] 포트 변화 없음 (분리 전: {sorted(baseline)}, 분리 후: {sorted(after_disconnect)})")
            print("         USB 케이블 분리 상태를 확인하거나 포트를 직접 입력합니다.")
            print()
            raw = _prompt(f"  {arm_label} 포트 직접 입력 (예: /dev/ttyACM1, Enter=건너뜀): ")
            if raw:
                ports[f"{arm_label}_port"] = raw
        else:
            # lerobot_find_port.py L63: "More than one port was found"
            print(f"  [경고] 복수 포트 변화 감지 ({removed}) — 직접 선택합니다.")
            print()
            for i, p in enumerate(removed, 1):
                print(f"    {i}. {p}")
            print()
            raw = _prompt(f"  {arm_label} 포트 번호 또는 직접 입력 (Enter=건너뜀): ")
            if raw.isdigit() and 1 <= int(raw) <= len(removed):
                ports[f"{arm_label}_port"] = removed[int(raw) - 1]
            elif raw:
                ports[f"{arm_label}_port"] = raw

        print()
        print(f"  {arm_label} USB 를 다시 연결하세요.")
        print()
        try:
            _prompt(f"  {arm_label} USB 재연결 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        # baseline 갱신 (재연결 후 상태)
        time.sleep(0.5)
        baseline = _get_serial_ports()
        print(f"  재연결 후 포트: {sorted(baseline) or '(없음)'}")
        print()

    # ports.json 저장
    ports_path = configs_dir / _PORTS_FILENAME
    if _save_json(ports_path, ports):
        print(f"[precheck] 포트 정보 저장: {ports_path}")
        print(f"  follower={ports['follower_port'] or '(건너뜀)'}  leader={ports['leader_port'] or '(건너뜀)'}")
    return True


def _run_find_cameras(configs_dir: Path) -> bool:
    """lerobot-find-cameras opencv 를 subprocess 로 실행 (비대화형).

    lerobot/src/lerobot/scripts/lerobot_find_cameras.py main() 패턴:
      - argparse: camera_type=None|"opencv"|"realsense"
      - opencv: OpenCVCamera.find_cameras() → 인덱스·해상도·fps 출력
    SO-ARM 수집 환경에서는 opencv 카메라 사용 (USB 웹캠).

    발견된 카메라 목록 표시 후 사용자가 wrist_left / overview 인덱스 입력.
    → cameras.json 저장.

    Returns:
        True: 실행 완료 / False: 중단 또는 오류
    """
    print()
    print("[precheck] lerobot-find-cameras opencv 실행 중...")
    print()

    try:
        result = subprocess.run(
            ["lerobot-find-cameras", "opencv"],
            check=False,
        )
    except FileNotFoundError:
        print(
            "[precheck] 오류: lerobot-find-cameras 명령을 찾을 수 없습니다.",
            file=sys.stderr,
        )
        print(
            "          venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate",
            file=sys.stderr,
        )
        return False

    if result.returncode != 0:
        print(f"[precheck] 경고: lerobot-find-cameras 비정상 종료 (rc={result.returncode})")

    print()
    print("  위 출력의 카메라 인덱스(Camera #N 의 id)를 각 역할에 입력하세요.")
    print("  (Enter=건너뜀 — 미입력 시 기본값 유지)")
    print()

    cameras: dict = {
        "wrist_left": {"index": None},
        "overview": {"index": None},
    }

    for cam_label in ("wrist_left", "overview"):
        raw = _prompt(f"  {cam_label} 카메라 인덱스 (정수 Enter=건너뜀): ")
        if raw:
            try:
                cameras[cam_label]["index"] = int(raw)
            except ValueError:
                print(f"  [precheck] '{raw}' 는 정수 아님 — 건너뜀")

    cameras_path = configs_dir / _CAMERAS_FILENAME
    if _save_json(cameras_path, cameras):
        print(f"[precheck] 카메라 정보 저장: {cameras_path}")
        wrist_idx = cameras["wrist_left"]["index"]
        overview_idx = cameras["overview"]["index"]
        print(
            f"  wrist_left={wrist_idx if wrist_idx is not None else '(건너뜀)'}  "
            f"overview={overview_idx if overview_idx is not None else '(건너뜀)'}"
        )
    return True


def _get_video_devices() -> list[str]:
    """현재 연결된 /dev/video* device 목록 반환 (정렬).

    lerobot/src/lerobot/cameras/opencv/camera_opencv.py find_cameras() line 301-303 인용:
      if platform.system() == "Linux":
          possible_paths = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)
          targets_to_scan = [str(p) for p in possible_paths]

    glob.glob 활용 (표준 라이브러리 — cv2 import 불필요).
    주의: Linux v4l2 가 카메라 1 개당 main stream + metadata 등 multiple device 를 노출하므로
          모든 /dev/video* 가 실제 영상 스트림 가능한 것은 아님.
          영상 스트림 가능 device 만 필요하면 _get_streamable_video_devices() 사용.

    Returns:
        정렬된 /dev/video* device 경로 목록 (예: ["/dev/video0", "/dev/video2"])
    """
    return sorted(glob.glob("/dev/video*"))


def _get_streamable_video_devices() -> list[str]:
    """cv2.VideoCapture read 성공 device 만 반환 (스트림 가능 device 필터링).

    TODO-D8 (e): Linux v4l2 는 카메라 1 개당 multiple device 를 노출함.
      예: 카메라 1 개 → /dev/video0 (main stream) + /dev/video1 (metadata).
      metadata device 는 cv2.VideoCapture 로 열거나 프레임을 읽을 수 없으므로
      이를 필터링하여 실제 영상을 읽을 수 있는 device 만 반환.

    lerobot/src/lerobot/cameras/opencv/camera_opencv.py 패턴 인용:
      line 308: camera = cv2.VideoCapture(target)
      line 343-348: ret, frame = self.videocapture.read()
      line 309: if camera.isOpened(): ...

    비용: device 수 × ~1 초 (VideoCapture open + warm-up read 포함).
          통상 4 device × ~1 초 = 4 초 이하. 분리/재연결 기반 검출 전 1 회만 호출.

    Returns:
        영상 스트림 가능 device 경로 목록 (정렬). 실패 device 는 제외.
    """
    all_devs = sorted(glob.glob("/dev/video*"))
    if not all_devs:
        return []

    try:
        import cv2
    except ImportError:
        # cv2 미설치 시 전체 목록 반환 (필터링 불가 — fallback)
        return all_devs

    streamable: list[str] = []
    for dev in all_devs:
        try:
            cap = cv2.VideoCapture(dev)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    streamable.append(dev)
            cap.release()
        except Exception:  # noqa: BLE001
            pass
    return streamable


def _capture_frame_to_file(
    device_path: str,
    label: str,
    output_dir: Path,
) -> str | None:
    """단일 카메라에서 1프레임 capture → jpg 파일 저장 + 경로 반환.

    lerobot/src/lerobot/cameras/opencv/camera_opencv.py 패턴 인용:
      line 308: camera = cv2.VideoCapture(target)
      line 343-348: ret, frame = self.videocapture.read()
      line 309: if camera.isOpened(): ...

    lerobot/src/lerobot/scripts/lerobot_find_cameras.py save_image() line 130-151 패턴 인용:
      path.parent.mkdir(parents=True, exist_ok=True)
      img.save(str(path))

    D4 walkthrough 에서 video2 read failed 발견 → 3회 retry 후 실패 처리.

    Args:
        device_path: OpenCV VideoCapture 에 넘길 device 경로 (예: "/dev/video2")
        label:       카메라 역할 이름 (예: "wrist_left") — 파일명 prefix
        output_dir:  저장 디렉터리

    Returns:
        저장된 파일 경로 문자열 또는 None (실패 시)
    """
    try:
        import cv2
    except ImportError:
        print("[precheck] 경고: cv2 (OpenCV) import 실패 — 영상 capture 건너뜁니다.", file=sys.stderr)
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    out_path = output_dir / f"{label}_{ts}.jpg"

    cap = None
    frame = None
    for attempt in range(3):
        cap = cv2.VideoCapture(device_path)
        if not cap.isOpened():
            cap.release()
            cap = None
            if attempt < 2:
                time.sleep(0.5)
            continue

        # warm-up: 첫 몇 프레임 버림 (카메라 초기화 대기)
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()
        cap = None

        if ret and frame is not None:
            break
        frame = None
        if attempt < 2:
            time.sleep(0.5)

    if frame is None:
        print(
            f"[precheck] 경고: {device_path} 에서 프레임 읽기 실패 (3회 시도) — capture 건너뜁니다.",
            file=sys.stderr,
        )
        return None

    # jpg 저장 (lerobot find_cameras save_image 패턴)
    try:
        encode_ok, buf = cv2.imencode(".jpg", frame)
        if not encode_ok or buf is None:
            print(f"[precheck] 경고: 이미지 인코딩 실패 ({label})", file=sys.stderr)
            return None
        with open(out_path, "wb") as f:
            f.write(buf.tobytes())
        return str(out_path)
    except Exception as e:
        print(f"[precheck] 경고: 이미지 저장 실패 ({label}): {e}", file=sys.stderr)
        return None


def _show_frame(
    device_path: str,
    label: str,
    display_mode: str,
    output_dir: Path,
) -> None:
    """카메라 1프레임 capture 후 display_mode 에 따라 표시.

    display_mode == "direct":
      cv2.imshow 로 DGX 모니터에 표시 (DISPLAY=:0 또는 로컬 DISPLAY).
      2초 후 자동 close.
      cv2.error (X11 connection failed 등) 발생 시 ssh-file 로 자동 fallback.

    display_mode == "ssh-x11":
      SSH X11 forwarding 활성 (DISPLAY=localhost:N).
      cv2.imshow 시도 → cv2.error 발생 시 ssh-file 로 자동 fallback + 안내.
      사용 전제: ssh -Y dgx (또는 ssh -X dgx) 로 접속 필요.

    display_mode == "ssh-file" (또는 "ssh"):
      _capture_frame_to_file 로 jpg 저장 + 경로 출력.
      xdg-open subprocess 시도 (VSCode remote 미리보기 지원 가능).

    Args:
        device_path: 카메라 device 경로
        label: 카메라 역할 이름
        display_mode: "direct" | "ssh-x11" | "ssh-file" (구 "ssh" 도 수용)
        output_dir: ssh-file 모드 저장 디렉터리
    """
    if display_mode in ("direct", "ssh-x11"):
        try:
            import cv2
        except ImportError:
            print("[precheck] 경고: cv2 import 실패 — 영상 표시 건너뜁니다.", file=sys.stderr)
            return

        cap = cv2.VideoCapture(device_path)
        if not cap.isOpened():
            cap.release()
            print(f"[precheck] 경고: {device_path} 열기 실패 — 영상 표시 건너뜁니다.", file=sys.stderr)
            return

        # warm-up
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            print(f"[precheck] 경고: {device_path} 프레임 읽기 실패 — 영상 표시 건너뜁니다.", file=sys.stderr)
            return

        win_name = f"카메라 확인: {label} ({device_path})"
        try:
            cv2.imshow(win_name, frame)
            if display_mode == "ssh-x11":
                print(f"[precheck] SSH X11 영상 표시 중 ({label}) — 2초 후 자동 닫힘.")
            else:
                print(f"[precheck] 영상 표시 중 ({label}) — 2초 후 자동 닫힘. 창을 클릭하면 즉시 닫힙니다.")
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
        except cv2.error as e:
            # X11 연결 실패 (DISPLAY 미설정, X11 forwarding 미작동, libgtk 미설치 등)
            # → ssh-file fallback
            print()
            print(f"[precheck] cv2.imshow 실패 ({e.__class__.__name__}: {e})")
            print("           ssh-file 모드 (이미지 파일 저장) 로 자동 전환합니다.")
            if display_mode == "ssh-x11":
                print("           SSH X11 forwarding 이 작동하지 않습니다.")
                print("           원인 후보:")
                print("             1) ssh -Y dgx 또는 ssh -X dgx 로 재접속 필요")
                print("             2) libgtk2 미설치 — cv2 GUI backend 불가:")
                print("                sudo apt install libgtk2.0-dev pkg-config")
                print("                (설치 후 OpenCV 재빌드 필요할 수 있음)")
            print()
            # fallback: ssh-file
            _show_frame(device_path, label, "ssh-file", output_dir)

    else:  # ssh-file (또는 구 "ssh")
        saved = _capture_frame_to_file(device_path, label, output_dir)
        if saved:
            print(f"[precheck] 영상 저장됨 ({label}): {saved}")
            print()
            print("         -- 영상 확인 방법 --")
            print("         VSCode remote-ssh 사용 중이면:")
            print("           좌측 Explorer 에서 아래 파일 클릭 → 자동 미리보기")
            print(f"           또는 터미널에서: code -r {saved}")
            print("         ssh -Y dgx 사용 중 (X11 forwarding) 이면:")
            print("           ssh-x11 모드 선택 시 cv2.imshow 시도.")
            print("           X11 imshow 실패 시 libgtk2 설치 필요:")
            print("           sudo apt install libgtk2.0-dev pkg-config")
            print("         sftp / scp 로 로컬 전송 후 미리보기도 가능.")
            print()
            # xdg-open 시도 (VSCode remote 환경에서 작동 가능, 실패 시 명시 보고)
            try:
                proc = subprocess.Popen(
                    ["xdg-open", saved],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                # Popen 은 비블로킹 — 즉시 성공/실패 판단 X. poll() 로 짧게 확인.
                time.sleep(0.3)
                rc = proc.poll()
                if rc is None:
                    # 아직 실행 중 (VSCode remote 환경에서 정상 — 비동기 미리보기)
                    print("         (xdg-open 실행됨 — VSCode remote 미리보기 창 확인)")
                elif rc == 0:
                    print("         (xdg-open 성공)")
                else:
                    print(f"         (xdg-open 종료: rc={rc} — 위 수동 확인 방법 사용)")
            except (FileNotFoundError, OSError):
                print("         (xdg-open 미설치 또는 실패 — 위 수동 확인 방법 사용)")
        else:
            print(f"[precheck] 영상 capture 실패 ({label}) — 건너뜁니다.")


def _run_find_cameras_split(configs_dir: Path, display_mode: str) -> bool:
    """카메라 식별 — lerobot-find-port 패턴 미러 (모두 연결 → 분리해서 검출).

    TODO-D7 (a): 방향 반전 — 기존 "연결하면 검출" → "분리해서 사라진 것 검출".
    lerobot-find-port 패턴 정확히 미러:
      lerobot_find_port.py find_port() L47-L55:
        ports_before = find_available_ports()   ← 분리 전 baseline (모두 연결 상태)
        input()                                  ← 분리 후 Enter
        time.sleep(0.5)
        ports_after = find_available_ports()    ← 분리 후 상태
        ports_diff = list(set(ports_before) - set(ports_after))  ← 사라진 것 = 해당 device

    카메라 버전:
      baseline = set(_get_video_devices())       ← wrist + overview 모두 연결 상태
      [wrist 단계]
        "wrist USB 분리 후 Enter"
        after_disconnect = set(_get_video_devices())
        removed = baseline - after_disconnect   ← 사라진 것 = wrist
        "wrist 재연결 후 Enter"
        baseline_restored = set(_get_video_devices())
      [overview 단계] 동일 패턴

    lerobot/src/lerobot/cameras/opencv/camera_opencv.py find_cameras() line 301-303 인용:
      Linux: possible_paths = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)
    본 함수는 _get_streamable_video_devices() 로 cv2 read 가능 device 만 사용.
    (TODO-D8 e: v4l2 metadata device 필터링 — _get_video_devices 의 전체 glob 대비)

    Args:
        configs_dir: configs/ 디렉터리 (cameras.json 저장 대상)
        display_mode: "direct" | "ssh-x11" | "ssh-file" (구 "ssh" 도 수용)

    Returns:
        True: 식별 완료 + cameras.json 저장 / False: 중단 또는 오류
    """
    # 이미지 저장 디렉터리 (interactive_cli/outputs/captured_images/)
    # lerobot/src/lerobot/scripts/lerobot_find_cameras.py --output-dir 기본값 패턴 참조.
    output_dir = configs_dir.parent / "outputs" / "captured_images"

    print()
    print("[precheck] 카메라 식별 — lerobot-find-port 패턴 (분리해서 검출)")
    print()
    print("  wrist + overview 카메라를 모두 연결한 상태에서 시작합니다.")
    print("  각 카메라를 하나씩 분리하여 어떤 device 인지 식별합니다.")
    print("  (lerobot-find-port 와 같은 방식)")
    print()

    # baseline: wrist + overview 모두 연결 상태 (cv2 read 가능 device 만 사용)
    # v4l2 metadata device 는 cv2 read 실패 → 카메라 후보에서 제외
    print("  [사전 스캔] 영상 스트림 가능 device 확인 중 (cv2 시도, 잠시 대기)...")
    baseline = set(_get_streamable_video_devices())
    print(f"  현재 연결된 /dev/video* 기기 (스트림 가능): {sorted(baseline) or '(없음)'}")
    print()

    if not baseline:
        print("[precheck] 경고: /dev/video* 기기 없음 — 카메라 연결 후 다시 시도하세요.")
        print()
        raw_w = _prompt("  wrist 카메라 device 경로 직접 입력 (Enter=건너뜀): ")
        raw_o = _prompt("  overview 카메라 device 경로 직접 입력 (Enter=건너뜀): ")
        wrist_device: str | None = raw_w or None
        overview_device: str | None = raw_o or None
    else:
        # ── wrist 단계 ──────────────────────────────────────────────────────
        print("  [1/2] wrist 카메라 식별 (손목 카메라)")
        print("  ─────────────────────────────────────────────────")
        print("  wrist 카메라 USB 케이블을 분리하세요.")
        print("  분리 완료 후 Enter 를 누르세요.")
        print()

        try:
            _prompt("  wrist USB 분리 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        # lerobot_find_port.py L53: time.sleep(0.5)
        time.sleep(0.5)

        # lerobot_find_port.py L54-L55: ports_after + ports_diff = set(before) - set(after)
        # 분리 후 상태: 전체 glob (metadata device 포함) — baseline(streamable only) 과 비교하면
        # streamable device 중 사라진 것 = 해당 카메라 주 스트림 device.
        after_wrist_disconnect = set(_get_video_devices())
        wrist_removed = sorted(baseline - after_wrist_disconnect)

        print()
        if len(wrist_removed) == 1:
            wrist_device = wrist_removed[0]
            print(f"  [검출] wrist device: {wrist_device}")
        elif len(wrist_removed) == 0:
            print(f"  [경고] 변화 없음 (분리 전: {sorted(baseline)}, 분리 후: {sorted(after_wrist_disconnect)})")
            print("         USB 분리 상태 확인 후 device 경로를 직접 입력합니다.")
            print()
            raw = _prompt("  wrist 카메라 device 경로 (예: /dev/video2, Enter=건너뜀): ")
            wrist_device = raw or None
        else:
            print(f"  [경고] 복수 device 사라짐 ({wrist_removed}) — 직접 선택합니다.")
            print()
            for i, d in enumerate(wrist_removed, 1):
                print(f"    {i}. {d}")
            print()
            raw = _prompt("  wrist device 번호 또는 경로 입력 (Enter=건너뜀): ")
            if raw.isdigit() and 1 <= int(raw) <= len(wrist_removed):
                wrist_device = wrist_removed[int(raw) - 1]
            elif raw:
                wrist_device = raw
            else:
                wrist_device = None

        # wrist 재연결 안내
        print()
        print("  wrist 카메라 USB 를 다시 연결하세요.")
        print()
        try:
            _prompt("  wrist USB 재연결 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        time.sleep(0.5)

        # 재연결 후 영상 확인
        if wrist_device:
            print(f"  wrist device: {wrist_device}")
            print("  영상을 확인하세요:")
            _show_frame(wrist_device, "wrist_left", display_mode, output_dir)
            print()
            try:
                ok = _prompt("  이 카메라가 wrist 카메라가 맞습니까? [Y/n]: ")
            except KeyboardInterrupt:
                print()
                print("[precheck] 취소됨.")
                return False

            if ok.lower() == "n":
                print("  wrist device 를 직접 입력하세요.")
                try:
                    wrist_device = _prompt("  device 경로 (Enter=건너뜀): ") or None
                except KeyboardInterrupt:
                    print()
                    print("[precheck] 취소됨.")
                    return False
        else:
            print("  wrist 카메라 미지정 — cameras.json 에 null 저장.")

        # baseline 재취득 (wrist 재연결 후 상태 — overview 분리 기준선, streamable device 기준)
        time.sleep(0.3)
        baseline_restored = set(_get_streamable_video_devices())
        print(f"\n  재연결 후 기기 목록 (스트림 가능): {sorted(baseline_restored) or '(없음)'}")

        # ── overview 단계 ────────────────────────────────────────────────────
        print()
        print("  [2/2] overview 카메라 식별 (전체뷰 카메라)")
        print("  ─────────────────────────────────────────────────")
        print("  overview 카메라 USB 케이블을 분리하세요.")
        print("  분리 완료 후 Enter 를 누르세요.")
        print()

        try:
            _prompt("  overview USB 분리 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        time.sleep(0.5)

        # 분리 후 상태: 전체 glob (baseline_restored=streamable 기준으로 비교)
        after_overview_disconnect = set(_get_video_devices())
        overview_removed = sorted(baseline_restored - after_overview_disconnect)

        print()
        if len(overview_removed) == 1:
            overview_device = overview_removed[0]
            print(f"  [검출] overview device: {overview_device}")
        elif len(overview_removed) == 0:
            print(f"  [경고] 변화 없음 (분리 전: {sorted(baseline_restored)}, 분리 후: {sorted(after_overview_disconnect)})")
            print()
            raw = _prompt("  overview 카메라 device 경로 (Enter=건너뜀): ")
            overview_device = raw or None
        else:
            print(f"  [경고] 복수 device 사라짐 ({overview_removed}) — 직접 선택합니다.")
            print()
            for i, d in enumerate(overview_removed, 1):
                print(f"    {i}. {d}")
            print()
            raw = _prompt("  overview device 번호 또는 경로 입력 (Enter=건너뜀): ")
            if raw.isdigit() and 1 <= int(raw) <= len(overview_removed):
                overview_device = overview_removed[int(raw) - 1]
            elif raw:
                overview_device = raw
            else:
                overview_device = None

        # overview 재연결 안내
        print()
        print("  overview 카메라 USB 를 다시 연결하세요.")
        print()
        try:
            _prompt("  overview USB 재연결 완료 후 Enter: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return False

        time.sleep(0.5)

        # overview 영상 확인
        if overview_device:
            print(f"  overview device: {overview_device}")
            print("  영상을 확인하세요:")
            _show_frame(overview_device, "overview", display_mode, output_dir)
            print()
            try:
                ok = _prompt("  이 카메라가 overview 카메라가 맞습니까? [Y/n]: ")
            except KeyboardInterrupt:
                print()
                print("[precheck] 취소됨.")
                return False

            if ok.lower() == "n":
                print("  overview device 를 직접 입력하세요.")
                try:
                    overview_device = _prompt("  device 경로 (Enter=건너뜀): ") or None
                except KeyboardInterrupt:
                    print()
                    print("[precheck] 취소됨.")
                    return False
        else:
            print("  overview 카메라 미지정 — cameras.json 에 null 저장.")

    # cameras.json 저장
    # device path 를 index 필드에 저장 (record.py 가 int index 또는 str path 모두 수용)
    cameras: dict = {
        "wrist_left": {"index": wrist_device},
        "overview": {"index": overview_device},
    }
    cameras_path = configs_dir / _CAMERAS_FILENAME
    if _save_json(cameras_path, cameras):
        print()
        print(f"[precheck] 카메라 정보 저장: {cameras_path}")
        print(f"  wrist_left={wrist_device or '(미지정)'}  overview={overview_device or '(미지정)'}")

    return True


def _verify_camera_mapping_live(
    cameras: dict,
    configs_dir: Path,
    display_mode: str,
) -> str:
    """저장된 cameras.json 의 wrist_left/overview 매핑이 실제로 맞는지 라이브 영상 + 사용자 확인.

    display_mode 분기:
      "direct"   — DGX 본체 모니터 (DISPLAY=:1) → ffplay 직접
      "ssh-x11"  — ssh -Y forwarding → ffplay (devPC X11 서버에 표시)
      "ssh-file" — X11 X → cv2 캡처 1장 저장 + xdg-open 안내

    각 슬롯 (wrist_left → overview 순서) 에 대해:
      1. 라이브 표시 (또는 캡처)
      2. 사용자 prompt: "화면의 카메라가 '{slot}' 가 맞습니까? [Y/n/swap]"
         Y / Enter → 다음 슬롯
         n         → "cancel" 반환
         swap      → wrist_left ↔ overview index 교환 + cameras.json 저장 + "swap" 반환

    ffplay 미설치 시 자동 ssh-file fallback.

    Args:
        cameras:     _load_json_or_default(cameras_path, _CAMERAS_DEFAULT) 결과
        configs_dir: cameras.json 저장 디렉터리
        display_mode: "direct" | "ssh-x11" | "ssh-file"

    Returns:
        "ok"     — 전 슬롯 확인 완료
        "swap"   — 사용자 swap 요청 (호출자가 재시도)
        "cancel" — 사용자 취소 또는 device 없음
    """
    cameras_path = configs_dir / _CAMERAS_FILENAME
    output_dir = configs_dir.parent / "outputs" / "captured_images"

    for slot in ("wrist_left", "overview"):
        device = cameras.get(slot, {}).get("index")
        if device is None or not isinstance(device, str):
            print(f"[precheck] {slot} index 없음 — 옵션 (1) 으로 재발견 권장.")
            return "cancel"

        print()
        print(f"[precheck] {slot} 카메라 라이브 표시 ({device})")
        print(f"  display_mode={display_mode}")

        proc = None
        _mode = display_mode  # local copy — fallback 시 변경

        if _mode in ("direct", "ssh-x11"):
            # ffplay 라이브 — direct 는 본체 DISPLAY, ssh-x11 은 X11 forwarding 자동
            cmd = [
                "ffplay", "-f", "v4l2", "-i", device,
                "-window_title", f"{slot} ({device}) — Y=확인 / n=취소 / swap=교환",
                "-loglevel", "error",
                "-fflags", "nobuffer",
            ]
            try:
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL)
                time.sleep(1.0)  # 라이브 시작 대기
            except FileNotFoundError:
                print("[precheck] ffplay 미설치 — ssh-file 모드 fallback")
                _mode = "ssh-file"
                proc = None

        if _mode == "ssh-file" or proc is None:
            # cv2 캡처 1장 저장 + xdg-open
            try:
                saved = _capture_frame_to_file(device, slot, output_dir)
                if saved:
                    print(f"  캡처 저장: {saved}")
                    print("  VSCode remote-ssh Explorer 클릭 또는 xdg-open 으로 확인하세요.")
                    try:
                        subprocess.Popen(
                            ["xdg-open", saved],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        )
                    except FileNotFoundError:
                        pass
                else:
                    print(f"[precheck] {device} 캡처 실패 — 매핑 확인 불가.")
                    return "cancel"
            except Exception as e:  # noqa: BLE001
                print(f"[precheck] cv2 캡처 예외: {e}")
                return "cancel"

        # 사용자 확인 prompt
        try:
            ans = _prompt(f"  화면의 카메라가 '{slot}' 가 맞습니까? [Y/n/swap]: ").lower()
        except KeyboardInterrupt:
            ans = "n"
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                proc = None

        if ans in ("n", "no"):
            print(f"[precheck] {slot} 정합 실패 — 취소합니다.")
            return "cancel"

        if ans == "swap":
            # wrist_left ↔ overview index 교환 + 저장
            cameras["wrist_left"]["index"], cameras["overview"]["index"] = (
                cameras["overview"]["index"],
                cameras["wrist_left"]["index"],
            )
            _save_json(cameras_path, cameras)
            print("[precheck] cameras.json 매핑 교환 저장 완료 — 재검증합니다.")
            return "swap"

        # Y / Enter → 다음
        print(f"[precheck] {slot} 정합 확인.")

    return "ok"


def _run_calibrate(configs_dir: Path, force_new_id: bool = False) -> bool:
    """lerobot-calibrate 를 subprocess 로 실행 (대화형).

    run_teleoperate.sh 의 calibrate_follower / calibrate_leader 패턴 참조:
      lerobot-calibrate --robot.type=so101_follower --robot.port=... --robot.id=...
      lerobot-calibrate --teleop.type=so101_leader  --teleop.port=... --teleop.id=...

    포트값은 configs/ports.json 에서 로드. 미설정 시 사용자에게 입력 요청.

    ⚠️ lerobot-calibrate 동작 주의 (so_follower.py:111-115):
      기존 calibration JSON 있으면 prompt:
        "Press ENTER to use provided calibration file ..., or type 'c' and press ENTER to run calibration:"
      → Enter = 기존 사용 / 'c' + Enter = 재calibration

    force_new_id=True:
      timestamp 기반 신규 ID 자동 생성 — lerobot self.calibration=None 원리 활용.
      lerobot SOFollower.calibrate() 는 ID 와 매핑된 calibration JSON 이 없으면
      self.calibration=None → "Press ENTER ..." prompt 자체 뜨지 않음.
      사용자 'c'+Enter 불필요.

    force_new_id=False:
      calibration.json 의 이전 ID 를 default 로 사용.
      기존 ID 재사용 시 lerobot 이 기존 calibration 로드 → 'c'+Enter 안내 배너 표시.

    완료 후 configs/calibration.json 에 ID·timestamp 저장 → 다음 실행 default.

    Args:
        configs_dir:  configs/ 디렉터리 (ports.json 로드 + calibration.json 저장 대상).
        force_new_id: True 시 timestamp 신규 ID 자동, lerobot prompt 회피.
                      False 시 기존 안내 배너 + ID 입력 (C0b 동작 유지).

    Returns:
        True: 캘리브 완료 / False: 중단 또는 오류
    """
    import datetime

    # ports.json 로드 (precheck 검출 결과를 default 로)
    ports_path = configs_dir / _PORTS_FILENAME
    ports_default_follower = "/dev/ttyACM1"  # hardcoded fallback
    ports_default_leader = "/dev/ttyACM0"
    ports_source = "hardcoded fallback"
    if ports_path.exists():
        try:
            with ports_path.open() as f:
                ports_data = json.load(f)
            if ports_data.get("follower_port"):
                ports_default_follower = ports_data["follower_port"]
                ports_source = "ports.json 검출 결과"
            if ports_data.get("leader_port"):
                ports_default_leader = ports_data["leader_port"]
        except (json.JSONDecodeError, OSError) as e:
            print(f"[precheck] 경고: ports.json 로드 실패 ({e}) — hardcoded fallback 사용")

    calib_path = configs_dir / _CALIBRATION_FILENAME
    calib_data = _load_json_or_default(calib_path, _CALIBRATION_DEFAULT)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if force_new_id:
        # timestamp 새 ID 강제 — lerobot 'c'+Enter prompt 회피
        # 원리: lerobot SOFollower.calibrate() — self.calibration=None 이면 기존 ID prompt 뜨지 않음
        follower_id = f"my_so101_follower_{timestamp}"
        leader_id = f"my_so101_leader_{timestamp}"
        print()
        print("[precheck] timestamp 새 ID 자동 생성:")
        print(f"  follower_id = {follower_id}")
        print(f"  leader_id   = {leader_id}")
        print()
        print("  (lerobot 'c'+Enter prompt 없이 바로 진행됩니다)")
        print()
        print("=" * 60)
        print(" lerobot-calibrate 진행 안내")
        print("=" * 60)
        print()
        print("  ★ 절차 (각 SO-101 마다 1~2분):")
        print("    1. zero pose 안내 — 팔을 zero pose 자세로 두고 Enter")
        print("    2. 각 모터 max range 회전 안내 — 안내 따라 모터 회전 후 Enter")
        print("       - shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, gripper 5개")
        print("       - wrist_roll 자동 처리 (사용자 회전 X — full_turn_motor)")
        print("         (so_follower.py:131-132 — wrist_roll 은 full_turn_motor 로 자동 매핑)")
        print("    3. 완료 시 자동으로 JSON 저장")
        print()
        print("  주의:")
        print("    - 중간 Ctrl+C / ESC 누르면 calibration 중단 → JSON 미생성 → 처음부터 다시")
        print("    - 각 prompt 안내를 차분히 읽고 Enter")
        print()
        print("=" * 60)
        print()
        try:
            go = _prompt("  이해했으면 Enter 로 진행 (b: 취소): ")
        except KeyboardInterrupt:
            return False
        if is_back(go):
            print("[precheck] 캘리브레이션 취소.")
            return False
    else:
        print()
        print("=" * 60)
        print(" lerobot-calibrate 동작 주의")
        print("=" * 60)
        print()
        print("  lerobot-calibrate 가 다음 prompt 를 띄울 수 있습니다")
        print("  (기존 calibration 파일이 있을 때):")
        print()
        print('    "Press ENTER to use provided calibration file ...,')
        print("     or type 'c' and press ENTER to run calibration:")
        print()
        print("  ★ 재calibration 의도이면 반드시 'c' + Enter 입력")
        print("    그냥 Enter 누르면 기존 calibration 그대로 사용됩니다.")
        print()
        print("  ★ 절차 (각 SO-101 마다 1~2분):")
        print("    1. zero pose 안내 — 팔을 zero pose 자세로 두고 Enter")
        print("    2. 각 모터 max range 회전 안내 — 안내 따라 모터 회전 후 Enter")
        print("       - shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, gripper 5개")
        print("       - wrist_roll 자동 처리 (사용자 회전 X — full_turn_motor)")
        print("    3. 완료 시 자동으로 JSON 저장")
        print()
        print("  주의:")
        print("    - 중간 Ctrl+C / ESC 누르면 calibration 중단 → JSON 미생성 → 처음부터 다시")
        print("=" * 60)
        print()
        try:
            go = _prompt("  이해했으면 Enter 로 진행 (b: 취소): ")
        except KeyboardInterrupt:
            return False
        if is_back(go):
            print("[precheck] 캘리브레이션 취소.")
            return False

        follower_id_default = calib_data.get("follower_id") or f"my_so101_follower_{timestamp}"
        leader_id_default = calib_data.get("leader_id") or f"my_so101_leader_{timestamp}"

        follower_id = _prompt(
            f"  follower ID  (Enter={follower_id_default}): "
        ) or follower_id_default
        leader_id = _prompt(
            f"  leader ID   (Enter={leader_id_default}): "
        ) or leader_id_default

    follower_port = _prompt(
        f"  follower 포트 (Enter={ports_default_follower}, source: {ports_source}): "
    ) or ports_default_follower
    leader_port = _prompt(
        f"  leader 포트  (Enter={ports_default_leader}, source: {ports_source}): "
    ) or ports_default_leader

    # JSON 실존 검증용 expected_paths 사전 계산
    # lerobot upstream constants.py L74-75: robots/<robot.name>/<id>.json
    #   so_follower → "so_follower" (robot.name), so_leader → "so_leader" (teleop.name)
    calib_dir = _get_calib_dir()
    expected_paths = {
        "follower": calib_dir / "robots" / "so_follower" / f"{follower_id}.json",
        "leader": calib_dir / "teleoperators" / "so_leader" / f"{leader_id}.json",
    }

    # 각 subprocess 결과 추적 (returncode + JSON 실존)
    calibration_results: dict[str, bool] = {}

    for label, cmd in (
        (
            "follower",
            [
                "lerobot-calibrate",
                "--robot.type=so101_follower",
                f"--robot.port={follower_port}",
                f"--robot.id={follower_id}",
            ],
        ),
        (
            "leader",
            [
                "lerobot-calibrate",
                "--teleop.type=so101_leader",
                f"--teleop.port={leader_port}",
                f"--teleop.id={leader_id}",
            ],
        ),
    ):
        print()
        print(f"[precheck] 캘리브: {label}")
        print(f"  실행: {' '.join(cmd)}")
        print()

        try:
            result = subprocess.run(cmd, check=False)
        except FileNotFoundError:
            print(
                "[precheck] 오류: lerobot-calibrate 명령을 찾을 수 없습니다.",
                file=sys.stderr,
            )
            print(
                "          venv 활성화 확인: source ~/smolvla/dgx/.arm_finetune/bin/activate",
                file=sys.stderr,
            )
            return False

        # subprocess 종료 후 실 JSON 파일 실존 확인
        expected_path = expected_paths[label]
        json_exists = expected_path.is_file()
        rc_ok = result.returncode == 0

        print()
        print(f"[precheck] {label} 결과:")
        print(f"  subprocess returncode: {result.returncode}")
        print(f"  expected JSON: {expected_path}")
        print(f"  JSON 실존: {'예' if json_exists else '아니오'}")

        if rc_ok and json_exists:
            calibration_results[label] = True
            print(f"  → {label} 캘리브 정합 OK")
        else:
            calibration_results[label] = False
            if not json_exists:
                print(f"  {label} JSON 파일 미생성 — calibration 미완료")
                print(
                    "     원인 추정: lerobot-calibrate 가 중간에 종료됐거나"
                    " 모든 모터 절차 미완수"
                )
            print()
            cont = _prompt("  계속 진행하겠습니까? [y/N]: ")
            if cont.lower() != "y":
                print(f"[precheck] {label} 캘리브 실패 — 중단합니다.")
                return False

    # 두 calibration 모두 정합인지 최종 검증
    # 하나라도 False 면 calibration.json 갱신 X (옛 default 보존)
    all_ok = all(calibration_results.values())

    if not all_ok:
        print()
        print("=" * 60)
        print("  Calibration 정합 검증 실패")
        print("=" * 60)
        print()
        for lbl, ok in calibration_results.items():
            status = "OK" if ok else "JSON 미생성 또는 비정상 종료"
            print(f"  {lbl}: {status}")
        print()
        print("  → calibration.json 갱신 안 함 (옛 default 보존)")
        print("  → 다시 calibrate 진행하세요. (precheck → calibrate → a)")
        print()
        return False

    # 두 JSON 모두 실존 확인 후에만 calibration.json 갱신
    calib_data.update({
        "follower_id": follower_id,
        "leader_id": leader_id,
        "follower_type": "so101_follower",
        "leader_type": "so101_leader",
        "calibrated_at": datetime.datetime.now().isoformat(),
    })
    if _save_json(calib_path, calib_data):
        print()
        print("[precheck] calibration.json 저장 완료 — 다음 실행 default 로 사용됩니다.")
        print(f"  follower_id={follower_id}")
        print(f"  leader_id={leader_id}")
        print("  실 JSON 경로:")
        print(f"    {expected_paths['follower']}")
        print(f"    {expected_paths['leader']}")

    print()
    print("[precheck] 캘리브레이션 완료.")
    return True


# ---------------------------------------------------------------------------
# 단계별 [a/b] 분기 헬퍼
# ---------------------------------------------------------------------------

def _step_motor_port(configs_dir: Path, ports: dict) -> str:
    """단계 1: 모터 포트 — (a) 새로 발견 / (b) ports.json 그대로 [Enter default].

    Returns:
        "ok"     — 단계 완료, 다음 단계로
        "cancel" — 사용자 취소 또는 back
    """
    print()
    print("─" * 60)
    print(" 1. 모터 포트")
    print("─" * 60)
    print(f"  현재: {_format_ports(ports)}")
    print()
    print("  (a) 새로 발견 — USB 분리/재연결로 자동 매핑")
    print("  (b) 그대로 사용  [Enter default]")
    print()

    while True:
        try:
            raw = _prompt("  선택 [a/b/Enter=b/back]: ").lower()
        except KeyboardInterrupt:
            return "cancel"

        if is_back(raw):
            return "cancel"

        if raw in ("", "b"):
            print("  [선택] b — ports.json 그대로 사용")
            return "ok"

        if raw == "a":
            print("  [선택] a — USB 분리/재연결로 새로 발견")
            print()
            if _run_find_port_self(configs_dir):
                return "ok"
            else:
                print("[precheck] 포트 발견 중단 — 취소합니다.")
                return "cancel"

        print("  a 또는 b 또는 Enter 또는 back 입력")


def _step_camera_port(configs_dir: Path, cameras: dict, display_mode: str) -> str:
    """단계 2: 카메라 — (a) 새로 발견 / (b) cameras.json 그대로 + 라이브 검증 [Enter default].

    b 선택 시 cameras.json null 체크 → streamable fallback + 라이브 검증.

    Returns:
        "ok"     — 단계 완료
        "cancel" — 사용자 취소, back, 또는 검증 실패
    """
    print()
    print("─" * 60)
    print(" 2. 카메라")
    print("─" * 60)
    print(f"  현재: {_format_cameras(cameras)}")
    print()
    print("  (a) 새로 발견 — USB 분리/재연결로 자동 매핑")
    print("  (b) 그대로 사용 + 라이브 영상 검증  [Enter default]")
    print()

    while True:
        try:
            raw = _prompt("  선택 [a/b/Enter=b/back]: ").lower()
        except KeyboardInterrupt:
            return "cancel"

        if is_back(raw):
            return "cancel"

        if raw in ("", "b"):
            print("  [선택] b — cameras.json 그대로 + 라이브 검증")
            print()

            cameras_path = configs_dir / _CAMERAS_FILENAME

            # cameras null 시 streamable fallback (기존 D13 로직 보존)
            wrist_idx = cameras.get("wrist_left", {}).get("index")
            overview_idx = cameras.get("overview", {}).get("index")
            if wrist_idx is None or overview_idx is None:
                print("[precheck] cameras.json 미설정 — streamable device 자동 fallback")
                streamable = _get_streamable_video_devices()
                if len(streamable) >= 2:
                    cameras["wrist_left"] = {"index": streamable[0]}
                    cameras["overview"] = {"index": streamable[1]}
                    _save_json(cameras_path, cameras)
                    print(f"  자동 매핑: wrist_left={streamable[0]}, overview={streamable[1]}")
                    print()
                else:
                    print(
                        f"[precheck] streamable device 부족 ({len(streamable)} 개)"
                        " — (a) 새로 발견 권장"
                    )
                    return "cancel"

            # 라이브 검증 루프 max 3회 (swap 재시도 포함)
            for attempt in range(3):
                verify_cameras = _load_json_or_default(cameras_path, _CAMERAS_DEFAULT)
                result = _verify_camera_mapping_live(verify_cameras, configs_dir, display_mode)

                if result == "ok":
                    print("[precheck] 카메라 매핑 정합 OK.")
                    return "ok"
                if result == "cancel":
                    print("[precheck] 카메라 매핑 검증 취소.")
                    return "cancel"
                if result == "swap":
                    if attempt < 2:
                        print(f"[precheck] swap 후 재검증 ({attempt + 2}/3 회)")
                        continue
                    else:
                        print("[precheck] swap 반복 한도 도달 — (a) 새로 발견 권장")
                        return "cancel"

            return "cancel"

        if raw == "a":
            print("  [선택] a — USB 분리/재연결로 새로 발견")
            print()
            if _run_find_cameras_split(configs_dir, display_mode):
                return "ok"
            else:
                print("[precheck] 카메라 발견 중단 — 취소합니다.")
                return "cancel"

        print("  a 또는 b 또는 Enter 또는 back 입력")


def _step_calibrate(configs_dir: Path, calib: dict) -> str:
    """단계 3: calibrate — (a) timestamp 새 ID 자동 / (b) calibration.json 그대로 [Enter default].

    (a) 선택 시 force_new_id=True → timestamp ID 강제 → lerobot 'c'+Enter prompt 회피.
    (b) calib 미설정 시 (a) 강제 안내.

    Returns:
        "ok"     — 단계 완료
        "cancel" — 사용자 취소, back
    """
    print()
    print("─" * 60)
    print(" 3. calibrate")
    print("─" * 60)
    fid = calib.get("follower_id") or "(미설정)"
    lid = calib.get("leader_id") or "(미설정)"
    cat = calib.get("calibrated_at") or "(없음)"
    print(f"  현재: follower_id={fid}, leader_id={lid}")
    print(f"        calibrated_at={cat}")
    print()
    print("  (a) 새로 진행 — timestamp 새 ID 자동 (lerobot prompt 회피)")
    print("  (b) 그대로 사용  [Enter default]")
    print()

    while True:
        try:
            raw = _prompt("  선택 [a/b/Enter=b/back]: ").lower()
        except KeyboardInterrupt:
            return "cancel"

        if is_back(raw):
            return "cancel"

        if raw in ("", "b"):
            if calib.get("follower_id") is None or calib.get("leader_id") is None:
                print("  [경고] calibration.json 미설정 — (a) 새로 진행 필요")
                print()
                continue
            print("  [선택] b — calibration.json 그대로 사용")
            return "ok"

        if raw == "a":
            print("  [선택] a — timestamp 새 ID 자동 calibration")
            print()
            if _run_calibrate(configs_dir, force_new_id=True):
                return "ok"
            else:
                print("[precheck] calibration 중단 — 취소합니다.")
                return "cancel"

        print("  a 또는 b 또는 Enter 또는 back 입력")


# ---------------------------------------------------------------------------
# 메인 함수
# ---------------------------------------------------------------------------

def teleop_precheck(script_dir: Path, display_mode: str = "ssh") -> str:
    """teleop 진입 직전 사용자 사전 점검 — 3단계 sequential [a/b] 분기.

    1. 모터 포트: (a) 새로 발견 (USB 분리/재연결) / (b) ports.json 그대로 [Enter]
    2. 카메라:   (a) 새로 발견 (USB 분리/재연결) / (b) cameras.json + 라이브 검증 [Enter]
    3. calibrate: (a) 새로 진행 (timestamp 새 ID 강제) / (b) calibration.json 그대로 [Enter]

    각 단계 b 가 default (Enter). a 선택 시 해당 단계만 새로 진행.

    'c'+Enter 자동 회피: (a) 새 calibrate 시 timestamp 새 ID 강제 → JSON 신규 →
    lerobot-calibrate 의 self.calibration=None → prompt 자체 안 뜸.

    호출 위치: mode.py flow3_mode_entry() 수집 분기
      env_check(mode="collect") PASS 후, _run_collect_flow() 직전.
    시그니처 동일 (mode.py 호출 측 변경 불필요).

    Args:
        script_dir:   dgx/interactive_cli/ 경로 (mode.py 의 script_dir 과 동일).
        display_mode: "direct" | "ssh-x11" | "ssh-file" (구 "ssh" 도 수용).
                      entry.py detect_display_mode() 결과 전달 (TODO-D6).
                      기본값 "ssh" — 안전한 fallback.

    Returns:
        "proceed" — 모든 단계 OK, teleop 시작
        "cancel"  — 어느 단계 취소 또는 back
    """
    configs_dir = _get_configs_dir(script_dir)

    # 현재 저장값 로드 (표시용)
    ports_path = configs_dir / _PORTS_FILENAME
    cameras_path = configs_dir / _CAMERAS_FILENAME
    calib_path = configs_dir / _CALIBRATION_FILENAME

    ports = _load_json_or_default(ports_path, _PORTS_DEFAULT)
    cameras = _load_json_or_default(cameras_path, _CAMERAS_DEFAULT)
    calib = _load_json_or_default(calib_path, _CALIBRATION_DEFAULT)

    print()
    print("=" * 60)
    print(" teleop 사전 점검 — 단계별 진행")
    print("=" * 60)
    print()
    print("  현재 저장값:")
    print(f"    ports.json       : {_format_ports(ports)}")
    print(f"    cameras.json     : {_format_cameras(cameras)}")
    print(
        f"    calibration.json : follower_id={calib.get('follower_id') or '(미설정)'}"
        f", leader_id={calib.get('leader_id') or '(미설정)'}"
    )
    print()
    print("  각 단계에서 b 또는 Enter = 저장값 그대로 사용 (default).")
    print("  a = 해당 단계만 새로 진행.")
    print()

    # ----- 단계 1: 모터 포트 -----
    if _step_motor_port(configs_dir, ports) == "cancel":
        return "cancel"

    # ----- 단계 2: 카메라 -----
    # 단계 1 완료 후 ports.json 최신값 반영 (step 1 에서 저장됐을 수 있음)
    cameras = _load_json_or_default(cameras_path, _CAMERAS_DEFAULT)
    if _step_camera_port(configs_dir, cameras, display_mode) == "cancel":
        return "cancel"

    # ----- 단계 3: calibrate -----
    calib = _load_json_or_default(calib_path, _CALIBRATION_DEFAULT)
    if _step_calibrate(configs_dir, calib) == "cancel":
        return "cancel"

    print()
    print("[precheck] 모든 단계 완료 — teleop 시작합니다.")
    print()
    return "proceed"
