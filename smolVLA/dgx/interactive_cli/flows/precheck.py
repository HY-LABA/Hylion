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

갱신 (2026-05-03, TODO-D6):
  _run_find_cameras_split(configs_dir, display_mode) 신규 — USB 분리/재연결 기반 카메라 식별.
  기존 _run_find_cameras() 를 teleop_precheck() 호출 위치에서 대체.
  display_mode 인자: "direct" (OpenCV imshow) | "ssh-x11" | "ssh-file" (이미지 파일 저장).

갱신 (2026-05-03, TODO-D7):
  (a) _run_find_cameras_split: 방향 반전 — 모두 연결 상태에서 분리해서 검출
      (lerobot-find-port 패턴 정확히 미러: 분리해서 사라진 것 검출)
  (b) _run_find_port_self: lerobot-find-port subprocess 회피 자체 로직 신규
      (lerobot_find_port.py find_port() L47-L64 핵심 패턴 미러)
  (c) detect_display_mode: ssh-x11 (X11 forwarding) 신규 모드 추가
      display_mode: "direct" | "ssh-x11" | "ssh-file" 3종
  (d) _show_frame: ssh-x11 분기 추가 + cv2.imshow 실패 시 ssh-file 자동 fallback

갱신 (2026-05-04, TODO-D8):
  (e) _get_streamable_video_devices: 신규 — cv2.VideoCapture read 성공 device 만 반환.
      Linux v4l2 가 카메라 1 개당 main stream + metadata 등 multiple device 노출 문제 해결.
      _get_video_devices() 는 backward-compat 보존. _run_find_cameras_split 가 후자 사용.
  (f) _show_frame ssh-file 안내 강화:
      - VSCode remote-ssh 미리보기 안내 명시 (Explorer 클릭 또는 code -r)
      - xdg-open subprocess 결과 보고 (성공/실패 명시)
      - ssh -Y X11 forwarding + libgtk 미설치 안내 추가

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


# ---------------------------------------------------------------------------
# 저장 파일 경로 상수
# ---------------------------------------------------------------------------

_PORTS_FILENAME = "ports.json"
_CAMERAS_FILENAME = "cameras.json"

# 포트 JSON 초기 구조 (orin/config/ports.json 패턴 미러)
_PORTS_DEFAULT: dict = {"follower_port": None, "leader_port": None}

# 카메라 JSON 초기 구조 (dgx 명칭: wrist_left/overview — record.py 기반)
_CAMERAS_DEFAULT: dict = {
    "wrist_left": {"index": None},
    "overview": {"index": None},
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
        # TODO-D8 (f): ssh-file 안내 강화 — VSCode remote-ssh 미리보기 안내 + xdg-open 결과 보고
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

    # baseline: wrist + overview 모두 연결 상태
    # TODO-D8 (e): _get_video_devices() 대신 _get_streamable_video_devices() 사용.
    # v4l2 metadata device 는 cv2 read 실패 → 카메라 후보에서 제외.
    # 주의: cv2 시도로 device 수 × ~1 초 소요 (통상 4 device 미만 → 4 초 이하).
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

        # baseline 재취득 (wrist 재연결 후 상태 — overview 분리 기준선)
        # TODO-D8 (e): streamable device 기준으로 재취득 (metadata device 제외).
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


def _run_calibrate(configs_dir: Path) -> bool:
    """lerobot-calibrate 를 subprocess 로 실행 (대화형).

    run_teleoperate.sh 의 calibrate_follower / calibrate_leader 패턴 참조:
      lerobot-calibrate --robot.type=so101_follower --robot.port=... --robot.id=...
      lerobot-calibrate --teleop.type=so101_leader  --teleop.port=... --teleop.id=...

    포트값은 configs/ports.json 에서 로드. 미설정 시 사용자에게 입력 요청.

    Args:
        configs_dir: configs/ 디렉터리 (ports.json 로드 대상 — D9 fix).

    Returns:
        True: 캘리브 완료 / False: 중단 또는 오류
    """
    print()
    print("[precheck] 캘리브레이션 재실행 — follower → leader 순서로 진행합니다.")
    print()

    # D9 fix: ports.json 로드 (precheck 검출 결과를 default 로)
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

    follower_port = _prompt(
        f"  follower 포트 (Enter={ports_default_follower}, source: {ports_source}): "
    ) or ports_default_follower
    leader_port = _prompt(
        f"  leader 포트  (Enter={ports_default_leader}, source: {ports_source}): "
    ) or ports_default_leader
    follower_id = _prompt(
        "  follower ID  (Enter=my_awesome_follower_arm): "
    ) or "my_awesome_follower_arm"
    leader_id = _prompt(
        "  leader ID   (Enter=my_awesome_leader_arm): "
    ) or "my_awesome_leader_arm"

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

        if result.returncode != 0:
            print(f"[precheck] 경고: {label} 캘리브 비정상 종료 (rc={result.returncode})")
            print()
            cont = _prompt("  계속 진행하겠습니까? [y/N]: ")
            if cont.lower() != "y":
                return False

    print()
    print("[precheck] 캘리브레이션 완료.")
    return True


# ---------------------------------------------------------------------------
# 메인 함수
# ---------------------------------------------------------------------------

def teleop_precheck(script_dir: Path, display_mode: str = "ssh") -> str:
    """teleop 진입 직전 사용자 사전 점검 단계.

    저장된 포트·카메라·캘리브 위치 표시 + 분기.

    호출 위치: mode.py flow3_mode_entry() 수집 분기
      env_check(mode="collect") PASS 후, _run_collect_flow() 직전.

    Args:
        script_dir: dgx/interactive_cli/ 경로 (mode.py 의 script_dir 과 동일).
        display_mode: "direct" (DGX 모니터 OpenCV imshow) | "ssh" (이미지 파일 저장)
                      entry.py detect_display_mode() 결과 전달 (TODO-D6).
                      기본값 "ssh" — 안전한 fallback.

    Returns:
        "proceed" — 기존 설정 진행 (teleop 시작)
        "cancel"  — 취소 (수집 mode 종료)
    """
    configs_dir = _get_configs_dir(script_dir)

    # 1. 저장된 값 읽기
    ports_path = configs_dir / _PORTS_FILENAME
    cameras_path = configs_dir / _CAMERAS_FILENAME
    ports = _load_json_or_default(ports_path, _PORTS_DEFAULT)
    cameras = _load_json_or_default(cameras_path, _CAMERAS_DEFAULT)
    calib_dir = _get_calib_dir()

    # 2. 캘리브 디렉터리 존재 여부 (표시용)
    calib_exists = calib_dir.exists()
    calib_label = str(calib_dir) + (" (존재)" if calib_exists else " (미생성)")

    # 3. 표시
    print()
    print("=" * 60)
    print(" teleop 사전 점검")
    print("=" * 60)
    print()
    print(f"  모터 포트     : {_format_ports(ports)}")
    print(f"  카메라 인덱스 : {_format_cameras(cameras)}")
    print(f"  캘리브 위치   : {calib_label}")
    print()
    print("  ※ 캘리브레이션 값은 웬만하면 변하지 않음.")
    print("    같은 SO-ARM 으로 이어서 작업 시 재사용 가능.")
    print()
    print("어떻게 진행할까요?")
    print()
    print("  (1) 새 학습 데이터 수집 시작 — 포트·카메라 다시 발견 추천")
    print("       USB 분리/재연결 방식으로 포트·카메라 자동 검출")
    print("       (lerobot-find-port 와 같은 패턴 — subprocess 없이 직접 glob)")
    print("       캘리브레이션 재실행 여부는 별도 확인")
    print("  (2) 기존 설정 그대로 진행 (캘리브 재사용)")
    print("  (3) 취소")
    print()

    while True:
        try:
            raw = _prompt("번호 선택 [1~3]: ")
        except KeyboardInterrupt:
            print()
            print("[precheck] 취소됨.")
            return "cancel"

        if raw == "1":
            # 옵션 (1): find-port + find-cameras 재실행 + 캘리브 별도 묻기
            print()
            print("[precheck] 포트·카메라 재발견 시작합니다.")
            print()

            # 자체 포트 검출 (lerobot-find-port subprocess 회피 — TODO-D7 b)
            if not _run_find_port_self(configs_dir):
                print()
                print("[precheck] 포트 발견이 중단되었습니다. 취소합니다.")
                return "cancel"

            # 카메라 식별 (USB 분리/재연결 + 영상 확인 — TODO-D6)
            # _run_find_cameras() 대체: _run_find_cameras_split(display_mode)
            # 차이: lerobot-find-cameras subprocess X, 직접 /dev/video* glob + cv2 capture
            if not _run_find_cameras_split(configs_dir, display_mode):
                print()
                print("[precheck] 카메라 발견이 중단되었습니다. 취소합니다.")
                return "cancel"

            # 캘리브 재실행 별도 묻기
            print()
            print("  캘리브레이션도 재실행할까요?")
            print("  (보통 변하지 않으니 N 권장 — 같은 SO-ARM 이어서 작업 시)")
            print()
            try:
                recalib = _prompt("  캘리브 재실행 [y/N]: ")
            except KeyboardInterrupt:
                recalib = ""

            if recalib.lower() == "y":
                if not _run_calibrate(configs_dir):
                    print()
                    print("[precheck] 캘리브레이션이 중단되었습니다. 취소합니다.")
                    return "cancel"
            else:
                print()
                print("[precheck] 캘리브레이션 재실행 건너뜀.")

            print()
            print("[precheck] 포트·카메라 재발견 완료.")
            print()
            print("  다음 흐름:")
            print("    1. teleop (run_teleoperate.sh) — leader 팔로 follower 조종")
            print("    2. data_kind 선택 → record (에피소드 수집)")
            print("    3. transfer (HF Hub / 로컬)")
            print("    4. 학습 분기 prompt — 바로 fine-tune 진입 가능")
            print()
            return "proceed"

        elif raw == "2":
            print()
            print("[precheck] 기존 설정으로 진행합니다.")
            print()

            # D13 Part A: cameras.json null 검출 → streamable device 자동 fallback
            cameras_data_opt2 = _load_json_or_default(cameras_path, _CAMERAS_DEFAULT)
            wrist_idx_opt2 = cameras_data_opt2.get("wrist_left", {}).get("index")
            overview_idx_opt2 = cameras_data_opt2.get("overview", {}).get("index")

            if wrist_idx_opt2 is None or overview_idx_opt2 is None:
                print("[precheck] cameras.json 미설정 검출 — streamable device 자동 fallback 시도")
                streamable = _get_streamable_video_devices()
                if len(streamable) >= 2:
                    new_cameras = {
                        "wrist_left": {"index": streamable[0]},
                        "overview": {"index": streamable[1]},
                    }
                    if _save_json(cameras_path, new_cameras):
                        print("[precheck] cameras.json 자동 갱신:")
                        print(f"  wrist_left = {streamable[0]} (자동 fallback — 첫 번째 streamable)")
                        print(f"  overview   = {streamable[1]} (자동 fallback — 두 번째 streamable)")
                        print("  ※ 카메라 정합 (wrist vs overview) 확인 필요 — 다르면 옵션 1 으로 다시 식별")
                    else:
                        print("[precheck] cameras.json 자동 갱신 실패 — record 가 hardcoded fallback 사용")
                else:
                    print(
                        f"[precheck] streamable device 부족 ({len(streamable)} 개)"
                        f" — record 가 hardcoded fallback 사용 (메타 device 차단 가능)"
                    )
                print()

            # ports.json 미설정 안내 (자동 fallback 없음 — follower/leader 구분 불가)
            ports_data_opt2 = _load_json_or_default(ports_path, _PORTS_DEFAULT)
            if ports_data_opt2.get("follower_port") is None or ports_data_opt2.get("leader_port") is None:
                print("[precheck] ports.json 미설정 — record 가 hardcoded (ttyACM1, ttyACM0) 사용.")
                print("  포트 정합이 필요하면 옵션 1 으로 재식별 권장.")
                print()

            print("  다음 흐름:")
            print("    1. teleop (run_teleoperate.sh) — leader 팔로 follower 조종")
            print("    2. data_kind 선택 → record (에피소드 수집)")
            print("    3. transfer (HF Hub / 로컬)")
            print("    4. 학습 분기 prompt — 바로 fine-tune 진입 가능")
            print()
            return "proceed"

        elif raw == "3":
            print()
            print("[precheck] 취소됩니다.")
            return "cancel"

        else:
            print("  1, 2, 3 중 하나를 입력하세요.")
