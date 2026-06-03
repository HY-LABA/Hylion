#!/usr/bin/env python
"""1회성 gesture 재생 CLI — Hylion (lerobot.datasets 미의존).

`lerobot-replay` CLI 는 `from lerobot.datasets import LeRobotDataset` 를 하지만,
Jetson 의 lerobot 0.5.2 는 smolVLA inference 전용으로 추려진 curated subset 이라
`datasets` 모듈 자체가 없다. 이 스크립트는 녹화 parquet 의 `action` 컬럼을
pyarrow 로 직접 읽어 재생한다 (재생 로직은 gesture_replay_core 공유).

수동 테스트 / play_gesture.sh 가 호출하는 1회성 경로. 상주 재생은 gesture_daemon.py.

Exit code:
  0  재생 성공 (disconnect overload 'cosmetic' 포함)
  1  재생 실패 (제어 루프 자체 실패)
  2  인자 / 데이터 오류
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# torch import 전에 LD_LIBRARY_PATH 보장 (필요 시 self re-exec).
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from gesture_replay_core import (  # noqa: E402
    DEFAULT_ID,
    DEFAULT_PORT,
    connect_arm,
    ensure_ld_library_path,
    load_episode,
    replay_episode,
)

ensure_ld_library_path()

DEFAULT_ROOT = Path.home() / "Hylion" / "jetson" / "arm" / "data"


def main() -> int:
    ap = argparse.ArgumentParser(description="Hylion gesture 1회성 재생 (lerobot.datasets 미의존)")
    ap.add_argument("--gesture", required=True, help="gesture 이름 (gestures/<name>/)")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="gesture 데이터 루트")
    ap.add_argument("--port", default=DEFAULT_PORT, help="follower 시리얼 by-id 경로")
    ap.add_argument("--id", dest="robot_id", default=DEFAULT_ID, help="robot.id = 캘리브 파일명")
    args = ap.parse_args()

    gesture_dir = Path(args.root).expanduser() / args.gesture
    if not (gesture_dir / "meta" / "info.json").is_file():
        print(f"[replay_gesture] ERROR: gesture 데이터 없음: {gesture_dir}", file=sys.stderr)
        return 2

    try:
        action_names, fps, actions = load_episode(gesture_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"[replay_gesture] ERROR: 에피소드 로드 실패: {exc!r}", file=sys.stderr)
        return 2

    num_frames = len(actions)
    print(f"[replay_gesture] {args.gesture}: frames={num_frames}, fps={fps}, motors={action_names}")

    from lerobot.utils.utils import init_logging

    init_logging()
    robot = connect_arm(args.port, args.robot_id)
    print("Replaying episode")  # play_gesture.sh 의 cosmetic 패턴 매칭용 마커

    replay_error: Exception | None = None
    elapsed = 0.0
    try:
        elapsed = replay_episode(robot, action_names, fps, actions)
    except Exception as exc:  # noqa: BLE001
        replay_error = exc

    # disconnect 는 따로: 재생 정상 완료 후 disable_torque 단계의 overload 는
    # 'cosmetic' (trajectory 는 이미 끝남) — 실패로 치지 않는다.
    disconnect_error: Exception | None = None
    try:
        robot.disconnect()
    except Exception as exc:  # noqa: BLE001
        disconnect_error = exc

    if replay_error is not None:
        print(f"[replay_gesture] ERROR: 재생 루프 실패: {replay_error!r}", file=sys.stderr)
        print(f"[replay_gesture] {args.gesture}: frames={num_frames}, elapsed={elapsed:.1f}s, rc=1")
        return 1

    if disconnect_error is not None:
        print(
            f"[replay_gesture] WARN: disconnect overload (cosmetic) — "
            f"재생은 정상 완료: {disconnect_error!r}",
            file=sys.stderr,
        )

    print(f"[replay_gesture] {args.gesture}: frames={num_frames}, elapsed={elapsed:.1f}s, rc=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
