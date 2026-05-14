"""interactive_cli flow 2 — DataCollector 환경 체크.

5단계 체크 (04 G1 check_hardware.sh 패턴 미러 + datacollector 맞춤):
  1. venv 활성화 확인 (.hylion_collector)
  2. USB 포트 존재 확인 (/dev/ttyACM0, /dev/ttyACM1)
  3. 카메라 인덱스 확인 (OpenCV index probe)
  4. lerobot import 확인
  5. 데이터 저장 경로 확인 (~/smolvla/datacollector/data/)

레퍼런스:
  - orin/tests/check_hardware.sh step_venv (line 152~173): venv 체크 패턴
  - orin/tests/check_hardware.sh step_soarm_port (line 220~328): USB 포트 스캔 패턴
  - orin/tests/check_hardware.sh step_cameras (line 336~486): OpenCV 카메라 probe 패턴
  - datacollector/scripts/run_teleoperate.sh line 19~20: 기본 포트 상수
    FOLLOWER_PORT="/dev/ttyACM1", LEADER_PORT="/dev/ttyACM0"
"""

import os
import sys
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 체크 결과 컨테이너
# ---------------------------------------------------------------------------

class EnvCheckResult(NamedTuple):
    """flow 2 전체 체크 결과.

    record.py 가 cam_wrist_left_index / cam_overview_index 로 사용.
    """
    ok: bool
    cam_wrist_left_index: int   # wrist_left 카메라 인덱스 (기본 0)
    cam_overview_index: int     # overview 카메라 인덱스 (기본 1)


# ---------------------------------------------------------------------------
# 체크 단계 함수
# ---------------------------------------------------------------------------

def _check_venv() -> tuple[bool, str]:
    """Step 1: .hylion_collector venv 활성화 확인.

    check_hardware.sh step_venv (line 152~173) 패턴 미러.
    VIRTUAL_ENV 환경변수 또는 sys.prefix 로 판단.
    """
    virtual_env = os.environ.get("VIRTUAL_ENV", "")
    if "hylion_collector" in virtual_env:
        return True, f"venv OK: {virtual_env}"

    # sys.prefix 로 이중 확인
    prefix = sys.prefix
    if "hylion_collector" in prefix:
        return True, f"venv OK (sys.prefix): {prefix}"

    if virtual_env:
        return False, (
            f"다른 venv 활성 중: {virtual_env}\n"
            "  해결: source ~/smolvla/datacollector/.hylion_collector/bin/activate"
        )
    return False, (
        "venv 비활성 상태\n"
        "  해결: source ~/smolvla/datacollector/.hylion_collector/bin/activate"
    )


def _check_usb_ports() -> tuple[bool, str]:
    """Step 2: USB 포트 존재 확인.

    run_teleoperate.sh line 19~20 기준:
      FOLLOWER_PORT="/dev/ttyACM1"
      LEADER_PORT="/dev/ttyACM0"

    check_hardware.sh step_soarm_port (line 220~328) 의 ttyACM* 스캔 패턴 미러.
    """
    follower_port = Path("/dev/ttyACM1")
    leader_port = Path("/dev/ttyACM0")

    missing = []
    if not follower_port.exists():
        missing.append(f"{follower_port} (follower)")
    if not leader_port.exists():
        missing.append(f"{leader_port} (leader)")

    if missing:
        detail = "미발견: " + ", ".join(missing)
        detail += "\n  해결: SO-ARM USB 연결 확인 후 lerobot-find-port 재확인"
        # /dev/ttyACM* 전체 목록 출력 (진단용)
        available = sorted(Path("/dev").glob("ttyACM*"))
        if available:
            detail += f"\n  현재 /dev/ttyACM*: {[str(p) for p in available]}"
        else:
            detail += "\n  현재 /dev/ttyACM*: 없음"
        return False, detail

    return True, f"포트 OK: follower={follower_port}, leader={leader_port}"


def _check_cameras() -> tuple[bool, str, int, int]:
    """Step 3: 카메라 인덱스 확인 (OpenCV index probe).

    check_hardware.sh step_cameras (line 336~486) 의 OpenCV probe 패턴 미러.
    lerobot-find-cameras 사용 시 lerobot import 필요 → 먼저 OpenCV 직접 probe.

    DataCollector 노트북의 일반적 패턴:
      - /dev/video0·1: 노트북 내장 카메라 (UVC capture/metadata 페어)
      - /dev/video2·3, /dev/video4·5, ...: 외부 USB 웹캠
    → 외부 카메라 (인덱스 ≥ 2) 를 우선 매핑하여 노트북 내장이 wrist 로 잡히는 오류 회피.

    Returns:
        (ok, detail, wrist_left_index, overview_index)
        외부 카메라 2대 이상 → 첫 외부 = wrist_left, 둘째 외부 = overview
        외부 1대 + 내장 → 외부 = wrist_left, 내장 = overview (경고)
        모두 내장 또는 외부 1대만 → 동일 인덱스 사용 (경고)
        미발견 → 실패
    """
    try:
        import cv2
    except ImportError:
        return False, "opencv-python 미설치 (pip install opencv-python)", 0, 1

    found_indices = []
    for idx in range(10):  # /dev/video0~9 탐색 (외부 USB 카메라 포함)
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            found_indices.append(idx)
            cap.release()

    if len(found_indices) == 0:
        return (
            False,
            "카메라 미발견 (인덱스 0~9 탐색)\n"
            "  해결: 카메라 USB 연결 확인",
            0, 1,
        )

    # 외부 카메라 (idx ≥ 2) 우선 — 내장 카메라 (video0·1) 회피
    external = [i for i in found_indices if i >= 2]
    internal = [i for i in found_indices if i < 2]

    if len(external) >= 2:
        wrist_idx, overview_idx = external[0], external[1]
        detail = (
            f"외부 카메라 {len(external)}대 발견 ({external}), 내장 {len(internal)}대 ({internal}) — "
            f"wrist_left={wrist_idx}, overview={overview_idx}"
        )
        return True, detail, wrist_idx, overview_idx

    if len(external) == 1 and len(internal) >= 1:
        wrist_idx, overview_idx = external[0], internal[0]
        return (
            True,
            f"외부 카메라 1대 + 내장 1대 — wrist_left={wrist_idx} (외부), overview={overview_idx} (내장, 권장: 외부 2대)",
            wrist_idx, overview_idx,
        )

    # fallback — 가능한 인덱스 그대로
    if len(found_indices) >= 2:
        wrist_idx, overview_idx = found_indices[0], found_indices[1]
        return (
            True,
            f"카메라 {len(found_indices)}대 ({found_indices}) — wrist_left={wrist_idx}, overview={overview_idx} (외부 카메라 권장)",
            wrist_idx, overview_idx,
        )

    wrist_idx = found_indices[0]
    return (
        True,
        f"카메라 1대만 발견 (index={wrist_idx}) — wrist_left·overview 동일 사용 (권장: 외부 2대)",
        wrist_idx, wrist_idx,
    )


def _check_lerobot_import() -> tuple[bool, str]:
    """Step 4: lerobot import 확인.

    check_hardware.sh step_cameras (line 342~363) ImportError 패턴 미러.
    """
    try:
        import lerobot  # noqa: F401
        from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: F401
        import lerobot as _lr
        version = getattr(_lr, "__version__", "unknown")
        return True, f"lerobot OK (version={version})"
    except ImportError as e:
        return False, (
            f"lerobot import 실패: {e}\n"
            "  해결: source ~/smolvla/datacollector/.hylion_collector/bin/activate"
            " && pip install -e datacollector/"
        )


def _check_data_dir() -> tuple[bool, str]:
    """Step 5: 데이터 저장 경로 확인.

    경로: ~/smolvla/datacollector/data/
    존재하지 않으면 자동 생성 시도.
    """
    data_dir = Path(os.path.expanduser("~/smolvla/datacollector/data"))

    if not data_dir.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            return True, f"데이터 저장 경로 생성: {data_dir}"
        except OSError as e:
            return False, (
                f"데이터 저장 경로 생성 실패: {data_dir}\n"
                f"  오류: {e}\n"
                "  해결: 디스크 공간·권한 확인"
            )

    # 쓰기 가능 확인
    if not os.access(data_dir, os.W_OK):
        return False, (
            f"데이터 저장 경로 쓰기 불가: {data_dir}\n"
            f"  해결: chmod u+w {data_dir}"
        )

    return True, f"데이터 저장 경로 OK: {data_dir}"


def _check_motor_ids() -> tuple[bool, str]:
    """Step 6: SO-ARM follower·leader 모터 ID 1~6 등록 여부 확인.

    feetech-servo-sdk (`scservo_sdk`) 로 각 ttyACM 포트에서 ID 1~6 ping.
    `lerobot-setup-motors` 가 모터 1~6 을 굽지 않으면 default ID (보통 1) 만 응답.
    6개 모두 응답하면 setup_motors 완료로 판정.

    실패 시 안내: `lerobot-setup-motors --robot.type=so101_follower --robot.port=...`

    상수 출처: record.py FOLLOWER_PORT/LEADER_PORT (run_teleoperate.sh line 19~20).
    """
    try:
        from scservo_sdk import PortHandler, PacketHandler
    except ImportError:
        return False, "scservo_sdk import 실패 — feetech extras 미설치"

    # record.py 와 동일한 포트 (현재 cycle 에서 import 순환 방지로 자체 정의)
    FOLLOWER_PORT = "/dev/ttyACM1"
    LEADER_PORT = "/dev/ttyACM0"
    BAUDRATE = 1_000_000  # Feetech STS3215 default

    results: dict[str, tuple[bool, str]] = {}
    for label, port in [("follower", FOLLOWER_PORT), ("leader", LEADER_PORT)]:
        if not Path(port).exists():
            results[label] = (False, f"{port}: 포트 없음 (SO-ARM USB 연결·전원 확인)")
            continue
        port_handler = PortHandler(port)
        packet_handler = PacketHandler(0)  # SCS protocol version
        try:
            if not port_handler.openPort():
                results[label] = (False, f"{port}: 포트 열기 실패")
                continue
            if not port_handler.setBaudRate(BAUDRATE):
                port_handler.closePort()
                results[label] = (False, f"{port}: baudrate {BAUDRATE} 설정 실패")
                continue
            ids_responding: list[int] = []
            for motor_id in range(1, 7):
                _, comm_result, error = packet_handler.ping(port_handler, motor_id)
                if comm_result == 0 and error == 0:
                    ids_responding.append(motor_id)
        finally:
            port_handler.closePort()

        if ids_responding == list(range(1, 7)):
            results[label] = (True, f"{port}: ID 1~6 모두 응답 (setup_motors OK)")
        else:
            missing = [i for i in range(1, 7) if i not in ids_responding]
            results[label] = (
                False,
                f"{port}: 응답 ID={ids_responding}, 누락={missing} — "
                f"`lerobot-setup-motors --robot.type=so101_{label} --robot.port={port} "
                f"--robot.id=...` 필요",
            )

    all_ok = all(ok for ok, _ in results.values())
    detail = " | ".join(f"{label} → {d}" for label, (_, d) in results.items())
    return all_ok, detail


def _check_calibration() -> tuple[bool, str]:
    """Step 7: SO-ARM follower·leader calibration JSON 파일 존재 확인.

    lerobot 의 calibration 경로:
      HF_LEROBOT_CALIBRATION = HF_LEROBOT_HOME / "calibration"
      HF_LEROBOT_HOME       = HF_HOME / "lerobot"  (default)
      HF_HOME               = ~/.cache/huggingface  (setup_env.sh §4 설정)

    파일 경로 (lerobot/robots/robot.py:50, teleoperators/teleoperator.py:50 인용):
      Robot:        {calibration_root}/robots/{robot.name}/{robot.id}.json
      Teleoperator: {calibration_root}/teleoperators/{teleop.name}/{teleop.id}.json

    record.py 의 ROBOT_TYPE / TELEOP_TYPE / FOLLOWER_ID / LEADER_ID 상수 활용.
    실패 시 안내: `lerobot-calibrate --robot.type=so101_follower ...`
    """
    # record.py 와 동일한 ID·type (자체 정의 — 순환 import 방지)
    ROBOT_TYPE = "so101_follower"
    TELEOP_TYPE = "so101_leader"
    FOLLOWER_ID = "my_awesome_follower_arm"
    LEADER_ID = "my_awesome_leader_arm"

    hf_home = Path(os.path.expanduser(os.environ.get("HF_HOME", "~/.cache/huggingface")))
    calibration_root = hf_home / "lerobot" / "calibration"

    follower_path = calibration_root / "robots" / ROBOT_TYPE / f"{FOLLOWER_ID}.json"
    leader_path = calibration_root / "teleoperators" / TELEOP_TYPE / f"{LEADER_ID}.json"

    follower_ok = follower_path.is_file()
    leader_ok = leader_path.is_file()

    if follower_ok and leader_ok:
        return True, (
            f"follower·leader calibration JSON 모두 존재 — "
            f"follower={follower_path.name}, leader={leader_path.name} "
            f"(아래 {calibration_root.relative_to(Path.home()) if calibration_root.is_relative_to(Path.home()) else calibration_root})"
        )

    missing = []
    if not follower_ok:
        missing.append(
            f"follower 누락: {follower_path} — "
            f"`lerobot-calibrate --robot.type={ROBOT_TYPE} --robot.port=/dev/ttyACM1 "
            f"--robot.id={FOLLOWER_ID}`"
        )
    if not leader_ok:
        missing.append(
            f"leader 누락: {leader_path} — "
            f"`lerobot-calibrate --teleop.type={TELEOP_TYPE} --teleop.port=/dev/ttyACM0 "
            f"--teleop.id={LEADER_ID}`"
        )
    return False, " | ".join(missing)


# ---------------------------------------------------------------------------
# flow 2 메인 함수
# ---------------------------------------------------------------------------

def flow2_env_check() -> EnvCheckResult:
    """flow 2: DataCollector 환경 체크.

    7개 체크 항목 순차 실행 (D1 §1 스펙 순서 + 사용자 요청 §6·§7):
      1. venv (.hylion_collector)
      2. USB 포트 (/dev/ttyACM0, /dev/ttyACM1)
      3. 카메라 인덱스 (OpenCV probe)
      4. lerobot import
      5. 데이터 저장 경로 (~/smolvla/datacollector/data/)
      6. SO-ARM 모터 ID 1~6 등록 (setup_motors 완료 확인) — 사용자 요청 추가
      7. Calibration JSON 파일 존재 (follower + leader) — 사용자 요청 추가

    실패 항목 출력 + 해결 방법 안내.
    모두 통과 시 EnvCheckResult(ok=True, ...) 반환.
    하나 이상 실패 시 EnvCheckResult(ok=False, ...) 반환.

    Returns:
        EnvCheckResult: ok 여부 + 카메라 인덱스 (record.py 로 전달)
    """
    print()
    print("=" * 60)
    print(" flow 2 — 환경 체크 (DataCollector)")
    print("=" * 60)

    all_ok = True
    cam_wrist_left_index = 0
    cam_overview_index = 1

    # Step 1: venv
    print()
    print("  [venv (.hylion_collector)]")
    try:
        ok, detail = _check_venv()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    # Step 2: USB 포트
    print()
    print("  [USB 포트 (/dev/ttyACM0, /dev/ttyACM1)]")
    try:
        ok, detail = _check_usb_ports()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    # Step 3: 카메라 인덱스 (D1 §1 순서: USB 다음, lerobot 이전)
    print()
    print("  [카메라 인덱스 (wrist_left, overview)]")
    try:
        cam_ok, cam_detail, wrist_idx, overview_idx = _check_cameras()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        cam_ok, cam_detail, wrist_idx, overview_idx = False, f"예외 발생: {e}", 0, 1
    print(f"  {'[PASS]' if cam_ok else '[FAIL]'} {cam_detail}")
    if not cam_ok:
        all_ok = False
    else:
        cam_wrist_left_index = wrist_idx
        cam_overview_index = overview_idx

    # Step 4: lerobot import
    print()
    print("  [lerobot import]")
    try:
        ok, detail = _check_lerobot_import()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    # Step 5: 데이터 저장 경로
    print()
    print("  [데이터 저장 경로 (~/smolvla/datacollector/data/)]")
    try:
        ok, detail = _check_data_dir()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    # Step 6: SO-ARM 모터 ID 1~6 등록 여부 (사용자 요청 추가)
    print()
    print("  [SO-ARM 모터 ID 1~6 등록 (lerobot-setup-motors 완료 확인)]")
    try:
        ok, detail = _check_motor_ids()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    # Step 7: Calibration JSON 파일 존재 (사용자 요청 추가)
    print()
    print("  [Calibration JSON (follower + leader, lerobot-calibrate 완료 확인)]")
    try:
        ok, detail = _check_calibration()
    except (EOFError, KeyboardInterrupt):
        print("\n[flow 2] 중단됨.")
        return EnvCheckResult(ok=False, cam_wrist_left_index=0, cam_overview_index=1)
    except Exception as e:
        ok, detail = False, f"예외 발생: {e}"
    print(f"  {'[PASS]' if ok else '[FAIL]'} {detail}")
    if not ok:
        all_ok = False

    print()
    if all_ok:
        print("[flow 2] 모든 환경 체크 통과. flow 3 으로 진행합니다.")
    else:
        print("[flow 2] 환경 체크 실패. 위 [FAIL] 항목을 해결 후 다시 실행하세요.")

    return EnvCheckResult(
        ok=all_ok,
        cam_wrist_left_index=cam_wrist_left_index,
        cam_overview_index=cam_overview_index,
    )
