"""Gesture replay 공유 프리미티브 — replay_gesture.py(1회성 CLI) 와
gesture_daemon.py(상주 데몬) 가 함께 쓴다.

재생 루프는 의도적으로 `robot.get_observation()` 을 호출하지 않는다: 이 SO-ARM 의
half-duplex 시리얼 버스에서 매 프레임 sync_read(관측) → sync_write(명령) 를
30fps 로 번갈아 하면 write 가 조용히 먹히지 않아 팔이 안 움직인다 (Jetson 실측
2026-05-14). lerobot 의 기본 processor 는 어차피 identity passthrough 라
action dict 를 robot.send_action 에 직접 넘기는 것과 결과가 같다.

torch 는 venv 의 nvidia/cusparselt/lib 에 있는 libcusparseLt.so.0 를 필요로 하고,
그 경로는 torch import *전에* LD_LIBRARY_PATH 에 있어야 한다. `ensure_ld_library_path()`
가 누락 시 그 경로를 얹어 프로세스를 re-exec 한다 — entry point 의 맨 처음에서
(lerobot import 전에) 부를 것.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

DEFAULT_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00"
DEFAULT_ID = "rightarm_test_follower"


def ensure_ld_library_path() -> None:
    """torch import 전에 venv 의 cusparselt lib 를 LD_LIBRARY_PATH 에 보장.

    누락됐으면 환경변수를 채워 self re-exec. 이미 있거나 lib 가 번들돼있지
    않으면 아무것도 안 함. lerobot/torch 를 import 하기 전에 호출해야 한다.

    venv 루트는 sys.prefix 로 잡는다 — venv 의 bin/python 은 시스템
    python 으로의 심링크라 realpath(sys.executable) 는 /usr 로 빠진다.
    """
    venv = sys.prefix
    cusparselt = os.path.join(
        venv, "lib", "python3.10", "site-packages", "nvidia", "cusparselt", "lib"
    )
    if not os.path.isfile(os.path.join(cusparselt, "libcusparseLt.so.0")):
        return  # 이 venv 엔 번들 안 됨 — 손쓸 수 없음
    current = os.environ.get("LD_LIBRARY_PATH", "")
    if cusparselt in current.split(":"):
        return  # 이미 설정됨
    os.environ["LD_LIBRARY_PATH"] = cusparselt + (":" + current if current else "")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def load_episode(gesture_dir: Path) -> tuple[list[str], int, list]:
    """gesture 의 meta/info.json + data parquet 에서 (action_names, fps, actions).

    단일 에피소드 녹화라 chunk/file 0 고정. pyarrow 로 action 컬럼만 읽는다.
    """
    info = json.loads((gesture_dir / "meta" / "info.json").read_text(encoding="utf-8"))
    action_names = info["features"]["action"]["names"]
    fps = int(info["fps"])

    parquet = gesture_dir / "data" / "chunk-000" / "file-000.parquet"
    if not parquet.is_file():
        raise FileNotFoundError(f"parquet 없음: {parquet}")

    import pyarrow.parquet as pq

    actions = pq.read_table(parquet, columns=["action"]).column("action").to_pylist()
    return action_names, fps, actions


def connect_arm(port: str = DEFAULT_PORT, robot_id: str = DEFAULT_ID):
    """SO101 follower 를 build + connect 해서 반환.

    lerobot 의 connect() 는 configure() 의 torque_disabled 컨텍스트를 빠져나오며
    enable_torque 로 끝나므로, 반환 시점에 토크는 ON 상태다. 호출자가 이후
    토크 상태(idle 시 OFF 등)와 disconnect 를 책임진다.
    """
    from lerobot.robots import make_robot_from_config
    from lerobot.robots.so_follower import SO101FollowerConfig

    config = SO101FollowerConfig(port=port, id=robot_id)
    robot = make_robot_from_config(config)
    robot.connect()
    return robot


def replay_episode(robot, action_names: list[str], fps: int, actions: list) -> float:
    """녹화된 action 프레임을 fps 에 맞춰 팔로 스트리밍. elapsed 초 반환.

    토크 상태와 connect/disconnect 는 호출자 소유. 제어 루프 자체가 실패하면
    예외를 올린다 (disconnect 시 cosmetic overload 는 호출자 관심사).
    """
    from lerobot.utils.robot_utils import precise_sleep

    start = time.perf_counter()
    for idx in range(len(actions)):
        frame_t = time.perf_counter()
        action = {name: float(actions[idx][i]) for i, name in enumerate(action_names)}
        robot.send_action(action)
        precise_sleep(max(1.0 / fps - (time.perf_counter() - frame_t), 0.0))
    return time.perf_counter() - start
