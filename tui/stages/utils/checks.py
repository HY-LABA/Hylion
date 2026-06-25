"""tui/core/checks.py — Stage 1 개별 점검 함수 모음.

각 함수는 CheckResult를 반환한다.
모든 점검은 Orin 로컬에서 직접 실행된다.
"""
from __future__ import annotations

import os
import subprocess
from typing import Callable
from tui.stages.config import Status, CheckResult

from tui.stages.config import (
    MIC_KEYWORD,
    MOUTH_SERVO_PIN,
    ORIN_GESTURE_DATA,
    ORIN_VENV_EXPR,
    ORIN_VENV_ARM,
    ORIN_PROJECT,
    SPEAKER_SINK_KEYWORD,
    UDEV_SYMLINKS,
    WAKEWORD_MODEL,
    TMUX_COORDINATOR,
)



def _run(cmd: str, timeout: int = 5) -> tuple[str, int]:
    """로컬 shell 명령 실행. (stdout, returncode) 반환."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception:
        return "", -1


# ── 프로세스 ──────────────────────────────────────────────────────────────────

def check_no_duplicate_coordinator() -> CheckResult:
    out, _ = _run(f"tmux has-session -t {TMUX_COORDINATOR} 2>/dev/null && echo yes || echo no")
    if out == "yes":
        return CheckResult("중복 실행", Status.WARN,
                           f"tmux '{TMUX_COORDINATOR}' 세션 실행 중",
                           f"종료: tmux kill-session -t {TMUX_COORDINATOR}")
    # /proc/<pid> 존재 여부로 실제 살아있는 프로세스만 감지
    out2, _ = _run("pgrep -f 'jetson.core.coordinator'")
    pids = [p for p in out2.splitlines() if os.path.exists(f"/proc/{p.strip()}")]
    if pids:
        return CheckResult("중복 실행", Status.WARN,
                           f"coordinator.py 실행 중 (pid={pids[0]})",
                           f"종료: kill {pids[0]}")
    return CheckResult("중복 실행", Status.OK, "없음")


# ── 하드웨어 ──────────────────────────────────────────────────────────────────

def check_udev_symlinks() -> CheckResult:
    missing = [link for link in UDEV_SYMLINKS if not os.path.exists(link)]
    if not missing:
        return CheckResult("팔", Status.OK,
                           ", ".join(os.path.basename(l) for l in UDEV_SYMLINKS))
    if len(missing) == len(UDEV_SYMLINKS):
        return CheckResult("팔", Status.FAIL, "모든 링크 없음",
                           "udev rules 확인: /etc/udev/rules.d/99-hylion.rules")
    return CheckResult("팔", Status.WARN,
                       f"없음: {', '.join(os.path.basename(l) for l in missing)}")


def check_audio() -> CheckResult:
    """마이크 + 스피커 동시 점검."""
    mic_out, _ = _run(f"arecord -l 2>/dev/null | grep -i '{MIC_KEYWORD}'")
    spk_out, _ = _run(f"pactl list short sinks 2>/dev/null | grep -i '{SPEAKER_SINK_KEYWORD}'")

    mic_ok  = bool(mic_out)
    spk_ok  = bool(spk_out)

    if mic_ok and spk_ok:
        return CheckResult("오디오", Status.OK,
                           f"마이크({MIC_KEYWORD}) + 스피커({SPEAKER_SINK_KEYWORD}) 감지됨")
    if not mic_ok and not spk_ok:
        return CheckResult("오디오", Status.FAIL,
                           "마이크·스피커 모두 없음",
                           "USB 마이크/스피커 연결 확인.")
    if not mic_ok:
        return CheckResult("오디오", Status.FAIL,
                           f"마이크 '{MIC_KEYWORD}' 없음",
                           "USB 마이크 연결 후 'arecord -l' 확인.")
    return CheckResult("오디오", Status.WARN,
                       f"스피커 '{SPEAKER_SINK_KEYWORD}' sink 없음",
                       "USB 스피커 연결 후: pactl load-module module-alsa-sink device=hw:3,0")


def check_servo() -> CheckResult:
    """입 서보 GPIO 접근 가능 여부."""
    out, rc = _run("python3 -c 'import Jetson.GPIO' 2>/dev/null && echo ok || echo fail")
    if out == "ok":
        return CheckResult(f"서보 (GPIO {MOUTH_SERVO_PIN})", Status.OK, "Jetson.GPIO 사용 가능")
    return CheckResult(f"서보 (GPIO {MOUTH_SERVO_PIN})", Status.WARN,
                       "Jetson.GPIO import 실패 — 입 서보 비활성",
                       "웨이크워드 가상환경 에 Jetson.GPIO 설치 필요.")


# ── 소프트웨어 ────────────────────────────────────────────────────────────────

def check_wakeword_model() -> CheckResult:
    path = os.path.expanduser(WAKEWORD_MODEL)
    if os.path.isfile(path):
        return CheckResult("웨이크워드 모델 ", Status.OK, os.path.basename(path))
    return CheckResult("웨이크워드 모델 ", Status.FAIL,
                       f"없음: {WAKEWORD_MODEL}",
                       "checkpoints/wakeword/ 에 Hey_Hyleon.tflite 필요.")


def check_expression_venv() -> CheckResult:
    """wakeword·STT 실행에 항상 필요한 venv."""
    path = os.path.expanduser(f"{ORIN_VENV_EXPR}/bin/python")
    if os.path.isfile(path):
        return CheckResult("웨이크워드 가상환경 ", Status.OK, "wakeword·STT 준비됨")
    return CheckResult("웨이크워드 가상환경 ", Status.FAIL,
                       "venv 없음 — wakeword 동작 불가",
                       f"{ORIN_VENV_EXPR} 구축 필요.")


def check_arm_venv() -> CheckResult:
    """gesture(팔 동작) 실행용 venv."""
    path = os.path.expanduser(f"{ORIN_VENV_ARM}/bin/python")
    if os.path.isfile(path):
        return CheckResult("팔 가상환경  ", Status.OK, "gesture 준비됨")
    return CheckResult("팔 가상환경  ", Status.WARN,
                       "venv 없음 — gesture 비활성",
                       f"{ORIN_VENV_ARM} 구축 필요.")


def check_gesture_data() -> CheckResult:
    data_path = os.path.expanduser(ORIN_GESTURE_DATA)
    if not os.path.isdir(data_path):
        return CheckResult("gesture 데이터", Status.WARN, "데이터 폴더 없음",
                           "fetch_hf_gesture.py 로 데이터 추가 가능.")
    gestures = [d for d in os.listdir(data_path)
                if os.path.isfile(os.path.join(data_path, d, "meta", "info.json"))]
    if gestures:
        return CheckResult("gesture 데이터", Status.OK,
                           f"{len(gestures)}개: {', '.join(gestures)}")
    return CheckResult("gesture 데이터", Status.WARN, "데이터 없음",
                       "fetch_hf_gesture.py 로 데이터 추가 가능.")


# ── 네트워크 / API ────────────────────────────────────────────────────────────

def check_network() -> CheckResult:
    _, groq_rc  = _run("timeout 3 bash -c 'exec 3<>/dev/tcp/api.groq.com/443'", timeout=6)
    _, clova_rc = _run("timeout 3 bash -c 'exec 3<>/dev/tcp/naveropenapi.apigw.ntruss.com/443'", timeout=6)

    groq_ok  = groq_rc  == 0
    clova_ok = clova_rc == 0

    if groq_ok and clova_ok:
        return CheckResult("인터넷", Status.OK, "Groq + Clova 도달 가능")
    if not groq_ok and not clova_ok:
        return CheckResult("인터넷", Status.FAIL, "연결 없음",
                           "WiFi 연결 확인. Groq(LLM/STT)·Clova(TTS) 모두 불가.")
    if not groq_ok:
        return CheckResult("인터넷", Status.FAIL, "Groq 연결 불가",
                           "LLM·STT 불가. WiFi 또는 Groq 서비스 확인.")
    return CheckResult("인터넷", Status.WARN, "Clova 연결 불가 — TTS 불가",
                       "naveropenapi.apigw.ntruss.com 접근 확인.")


def check_api_keys() -> CheckResult:
    """GROQ_API_KEY + Clova TTS 키 동시 점검."""
    env_path = os.path.expanduser(f"{ORIN_PROJECT}/.env")
    env_vars: dict[str, str] = {}
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    env_vars[k.strip()] = v.strip()

    groq_ok  = bool(env_vars.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY"))
    clova_ok = bool(env_vars.get("Naver_Clova_Speech_Client_ID") and
                    env_vars.get("Naver_Clova_Speech_Client_Secret"))

    if groq_ok and clova_ok:
        return CheckResult("API 키", Status.OK, "Groq + Clova 설정됨")
    if groq_ok:
        return CheckResult("API 키", Status.WARN,
                           "Groq OK / Clova 미설정 — TTS 불가",
                           f"{ORIN_PROJECT}/.env 에 Naver_Clova_Speech_Client_* 추가 필요.")
    if clova_ok:
        return CheckResult("API 키", Status.WARN,
                           "Clova OK / Groq 미설정 — LLM·STT 불가",
                           f"{ORIN_PROJECT}/.env 에 GROQ_API_KEY 추가 필요.")
    return CheckResult("API 키", Status.FAIL, "Groq·Clova 모두 미설정",
                       f"{ORIN_PROJECT}/.env 에 두 키 모두 추가 필요.")


# ── 전체 점검 목록 ────────────────────────────────────────────────────────────

ALL_CHECKS: list[Callable[[], CheckResult]] = [
    check_no_duplicate_coordinator,
    check_udev_symlinks,
    check_audio,
    check_servo,
    check_wakeword_model,
    check_expression_venv,
    check_arm_venv,
    check_gesture_data,
    check_network,
    check_api_keys,
]


# ── 그룹 정의 ─────────────────────────────────────────────────────────────────

GROUPS: list[tuple[str, list[Callable[[], CheckResult]]]] = [
    ("프로세스", [
        check_no_duplicate_coordinator,
    ]),
    ("하드웨어", [
        check_udev_symlinks,
        check_audio,
        check_servo,
    ]),
    ("소프트웨어", [
        check_wakeword_model,
        check_expression_venv,
        check_arm_venv,
        check_gesture_data,
    ]),
    ("네트워크/API", [
        check_network,
        check_api_keys,
    ]),
]


def run_groups() -> bool:
    """그룹별 점검 실행 및 출력. FAIL 이 하나라도 있으면 False 반환."""
    STATUS_ICON = {Status.OK: "OK  ", Status.WARN: "WARN", Status.FAIL: "FAIL"}
    all_passed = True

    for group_name, checks in GROUPS:
        print(f"\n[ {group_name} ]")
        results = [fn() for fn in checks]

        for r in results:
            icon = STATUS_ICON[r.status]
            print(f"  [{icon}] {r.name}: {r.message}")
            if r.hint:
                print(f"         → {r.hint}")

        if any(r.failed for r in results):
            print(f"  ✗ {group_name} FAIL")
            all_passed = False
        elif any(r.status == Status.WARN for r in results):
            print(f"  △ {group_name} WARN")
        else:
            print(f"  ✓ {group_name} OK")

    return all_passed


if __name__ == "__main__":
    import sys
    ok = run_groups()
    sys.exit(0 if ok else 1)
