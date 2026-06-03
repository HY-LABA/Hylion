"""tui/core/config.py — TUI 전역 설정.

환경변수로 override 가능. 모든 모듈이 이 파일에서 설정을 가져온다.
"""
from __future__ import annotations

import os

ORIN_PROJECT = os.environ.get("HYLION_ORIN_PROJECT", "~/Hylion")

# ── Orin 경로 (ORIN_PROJECT 기준, checks.py 에서 사용) ───────────────────────
ORIN_VENV_EXPR    = f"{ORIN_PROJECT}/jetson/expression/.venv"
ORIN_VENV_ARM     = "~/smolvla/orin/.hylion_arm"
ORIN_GESTURE_DATA = f"{ORIN_PROJECT}/jetson/arm/data"
ORIN_SCENARIOS    = f"{ORIN_PROJECT}/tui/scenarios"

# ── udev 심볼릭 링크 (Stage 1 점검) ──────────────────────────────────────────
UDEV_SYMLINKS = [
    "/dev/so_arm_left",
    "/dev/so_arm_right",
]

# ── 웨이크워드 모델 경로 (Orin) ───────────────────────────────────────────────
WAKEWORD_MODEL    = f"{ORIN_PROJECT}/checkpoints/wakeword/Hey_Hyleon.tflite"

# ── 마이크 키워드 ─────────────────────────────────────────────────────────────
MIC_KEYWORD        = os.environ.get("HYLION_WAKEWORD_DEVICE_KEYWORD", "P5HD")

# ── 입 서보 ───────────────────────────────────────────────────────────────────
MOUTH_SERVO_PIN    = int(os.environ.get("HYLION_MOUTH_SERVO_PIN", "7"))

# ── 스피커 ────────────────────────────────────────────────────────────────────
SPEAKER_SINK_KEYWORD = os.environ.get("HYLION_SPEAKER_SINK_KEYWORD", "usb")

# ── tmux 세션 이름 ────────────────────────────────────────────────────────────
TMUX_COORDINATOR  = "hylion-coordinator"

# ── Stage 1 점검 SSH 타임아웃 (초) ───────────────────────────────────────────


# ── 공통 타입 ─────────────────────────────────────────────────────────────────
from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    OK   = "OK"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    hint: str = ""

    @property
    def ok(self) -> bool:
        return self.status == Status.OK

    @property
    def failed(self) -> bool:
        return self.status == Status.FAIL
