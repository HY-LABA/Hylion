"""tui/stages/stage2_verify.py — Stage 2: 하드웨어 검증 + 대화 검증."""
from __future__ import annotations

import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tui.stages.config import ORIN_PROJECT, TMUX_COORDINATOR

console = Console()

_PROJECT_ROOT = Path(os.path.expanduser(ORIN_PROJECT))
_SESSION_LOG_DIR = _PROJECT_ROOT / "data" / "sessions"

# expression venv (coordinator, STT/TTS)
_VENV       = _PROJECT_ROOT / "jetson" / "expression" / ".venv"
_VENV_PY    = _VENV / "bin" / "python"
_CUSPARSELT = _VENV / "lib" / "python3.10" / "site-packages" / "nvidia" / "cusparselt" / "lib"

# arm venv (gesture daemon)
_ARM_VENV       = Path.home() / "smolvla" / "orin" / ".hylion_arm"
_ARM_VENV_PY    = _ARM_VENV / "bin" / "python"
_ARM_CUSPARSELT = _ARM_VENV / "lib" / "python3.10" / "site-packages" / "nvidia" / "cusparselt" / "lib"
_GESTURE_DAEMON = _PROJECT_ROOT / "jetson" / "arm" / "gestures" / "gesture_daemon.py"
_GESTURE_SOCK   = "/tmp/hylion_gesture.sock"

_HW_ITEMS = ["마이크", "스피커", "팔", "서보"]

_CONV_LABELS = {
    "웨이크워드": "Hey Hylion 감지",
    "STT":       "음성 인식 완료",
    "LLM":       "응답 생성 완료",
    "TTS":       "음성 출력 완료",
}


def _run(cmd: str, timeout: int = 5) -> tuple[str, int]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception:
        return "", -1


def _coordinator_pid() -> str | None:
    out, _ = _run("pgrep -f 'jetson.core.coordinator'")
    pids = [p.strip() for p in out.splitlines()
            if p.strip() and os.path.exists(f"/proc/{p.strip()}")]
    return pids[0] if pids else None


def _kill_coordinator() -> None:
    pid = _coordinator_pid()
    if pid:
        _run(f"kill {pid}")
        time.sleep(1.5)
    _run(f"tmux kill-session -t {TMUX_COORDINATOR} 2>/dev/null")


def _start_coordinator_tmux() -> bool:
    _, rc = _run(f"tmux has-session -t {TMUX_COORDINATOR} 2>/dev/null")
    if rc == 0:
        console.print(f"  [green]✓[/green] tmux '{TMUX_COORDINATOR}' 세션 이미 실행 중")
        return True

    coord_env = (
        f"LD_LIBRARY_PATH={_CUSPARSELT}:${{LD_LIBRARY_PATH:-}} "
        f"PYTHONUNBUFFERED=1 "
        f"HYLION_BHL_HOST=10.42.0.221 HYLION_BHL_PORT=9000 "
        f"HYLION_WAKEWORD_DEVICE_KEYWORD=P5HD "
        f"HYLION_WAKEWORD_SAMPLE_RATE=44100 "
        f"HYLION_MIC_SAMPLE_RATE=44100"
    )
    coord_cmd = f"{_VENV_PY} -m jetson.core.coordinator --preferred-keyword P5HD"
    tmux_cmd = (
        f"tmux new-session -d -s {TMUX_COORDINATOR} "
        f"'cd {_PROJECT_ROOT} && {coord_env} {coord_cmd}'"
    )
    _, rc = _run(tmux_cmd, timeout=10)
    if rc != 0:
        console.print("  [red]✗[/red] tmux 세션 시작 실패")
        return False

    for _ in range(15):
        time.sleep(1)
        if _coordinator_pid():
            console.print(f"  [green]✓[/green] coordinator → tmux '{TMUX_COORDINATOR}' 시작됨")
            return True

    console.print("  [red]✗[/red] coordinator 시작 타임아웃")
    return False


# ── gesture daemon 선기동 ─────────────────────────────────────────────────────

def _ping_gesture_sock() -> bool:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(_GESTURE_SOCK)
            s.sendall(b"ping\n")
            return s.recv(64).decode().strip() == "pong"
    except Exception:
        return False


def _start_gesture_daemon_bg() -> subprocess.Popen | None:
    if not _ARM_VENV_PY.is_file():
        console.print("  [yellow]△[/yellow] .hylion_arm venv 없음 → 팔 테스트 건너뜀")
        return None
    if not _GESTURE_DAEMON.is_file():
        console.print("  [yellow]△[/yellow] gesture_daemon.py 없음 → 팔 테스트 건너뜀")
        return None

    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    if (_ARM_CUSPARSELT / "libcusparseLt.so.0").is_file():
        env["LD_LIBRARY_PATH"] = f"{_ARM_CUSPARSELT}:{env.get('LD_LIBRARY_PATH', '')}"
    env["HYLION_GESTURE_SOCK"] = _GESTURE_SOCK
    env["ORIN_GESTURES_ROOT"] = str(_PROJECT_ROOT / "jetson" / "arm" / "data")

    try:
        return subprocess.Popen(
            [str(_ARM_VENV_PY), str(_GESTURE_DAEMON)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        console.print(f"  [red]✗[/red] gesture daemon 기동 실패: {e}")
        return None


def _wait_gesture_ready(timeout: int = 60) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _ping_gesture_sock():
            return True
        time.sleep(1)
    return False


# ── Stage 2A: 하드웨어 순차 검증 ─────────────────────────────────────────────

def _run_hardware_tests() -> tuple[bool, bool]:
    """하드웨어 검증 실행.

    Returns:
        (ok, user_skipped) — user_skipped=True 이면 Enter로 조기 종료.
    """
    console.print("\n[bold]Stage 2A — 하드웨어 순차 검증[/bold]")
    console.print("  [dim]Enter 를 누르면 이 단계를 건너뜁니다.[/dim]\n")

    pid = _coordinator_pid()
    if pid:
        console.print(f"  [yellow]△[/yellow] coordinator (pid={pid}) 종료")
        _kill_coordinator()

    if _ping_gesture_sock():
        console.print("  [green]✓[/green] gesture daemon 소켓 이미 응답 중 → 재사용")
    else:
        console.print("  [dim]gesture daemon 기동 중... (torch 로딩 ~10-20s)[/dim]")
        gesture_proc = _start_gesture_daemon_bg()
        if gesture_proc:
            if _wait_gesture_ready(timeout=60):
                console.print("  [green]✓[/green] gesture daemon 준비됨")
            else:
                console.print("  [yellow]△[/yellow] gesture daemon 타임아웃 — 팔 테스트 제한될 수 있음")

    hw_status: dict[str, str] = {k: "대기" for k in _HW_ITEMS}
    log_lines: list[str] = []

    def _parse_hw_log(line: str) -> None:
        l = line.strip()
        for item in _HW_ITEMS:
            if f"[{item}]" in l:
                if "PASS" in l or "확인됨" in l or "완료" in l:
                    hw_status[item] = "✓"
                elif "✗" in l or "건너뜀" in l or "실패" in l or "WARN" in l:
                    hw_status[item] = "✗"
                elif "테스트 시작" in l or "시작" in l:
                    hw_status[item] = "실행 중"

    def _build_hw_panel() -> Table:
        grid = Table.grid(padding=(0, 0))
        tbl = Table(box=None, show_header=False, padding=(0, 1))
        tbl.add_column(width=8)
        tbl.add_column(width=8)
        _S = {"✓": "green", "✗": "red", "실행 중": "cyan", "대기": "dim"}
        for name, st in hw_status.items():
            tbl.add_row(Text(st, style=_S.get(st, "dim")),
                        Text(name, style="bold" if st != "대기" else "dim"))
        grid.add_row(Panel(tbl, title="하드웨어 검증  [dim](Enter = 건너뜀)[/dim]", expand=True))
        log_text = "\n".join(log_lines[-10:]) if log_lines else "(대기 중...)"
        grid.add_row(Panel(Text(log_text, style="dim"), title="test_coordinator stdout", expand=True))
        return grid

    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["LD_LIBRARY_PATH"] = f"{_CUSPARSELT}:{env.get('LD_LIBRARY_PATH', '')}"
    env["HYLION_GESTURE_SOCK"] = _GESTURE_SOCK

    try:
        proc = subprocess.Popen(
            [str(_VENV_PY), "-m", "jetson.core.test_coordinator"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(_PROJECT_ROOT),
            env=env,
        )
    except Exception as e:
        console.print(f"  [red]✗[/red] test_coordinator 실행 실패: {e}")
        return False, False

    # stdout 읽기는 별도 스레드 — 메인 루프에서 Enter 감지 가능하게
    skip_event = threading.Event()

    def _read_stdout() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_lines.append(line)
                if len(log_lines) > 200:
                    log_lines.pop(0)
                _parse_hw_log(line)
            if skip_event.is_set():
                break

    stdout_thread = threading.Thread(target=_read_stdout, daemon=True)
    stdout_thread.start()

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while proc.poll() is None and not skip_event.is_set():
                live.update(_build_hw_panel())
                if select.select([sys.stdin], [], [], 0.3)[0]:
                    sys.stdin.readline()
                    skip_event.set()
                    proc.terminate()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        return False, False
    finally:
        stdout_thread.join(timeout=2)
        proc.wait()

    if skip_event.is_set():
        console.print("  [yellow]△[/yellow] Stage 2A 건너뜀")
        return True, True

    rc = proc.returncode
    if rc != 0:
        console.print(f"  [yellow]△[/yellow] test_coordinator 종료 코드={rc} (계속 진행)")
    else:
        console.print("  [green]✓[/green] 하드웨어 검증 완료")
    return True, False


# ── Stage 2B: 대화 검증 ───────────────────────────────────────────────────────

def _latest_session_file() -> Path | None:
    if not _SESSION_LOG_DIR.exists():
        return None
    files = sorted(_SESSION_LOG_DIR.glob("sess-live-*.jsonl"),
                   key=lambda f: f.stat().st_mtime)
    return files[-1] if files else None


def _build_conv_panel(components: dict[str, bool], log_lines: list[str]) -> Table:
    grid = Table.grid(padding=(0, 0))
    tbl = Table(box=None, show_header=False, padding=(0, 1))
    tbl.add_column(width=3)
    tbl.add_column(width=12)
    tbl.add_column()
    for name, done in components.items():
        icon = ("✓", "green") if done else ("○", "dim")
        tbl.add_row(Text(icon[0], style=icon[1]),
                    Text(name, style="bold" if done else "dim"),
                    Text(_CONV_LABELS[name], style=icon[1]))
    grid.add_row(Panel(tbl, title="컴포넌트 확인  [dim](Enter = 건너뜀)[/dim]", expand=True))
    log_text = "\n".join(log_lines) if log_lines else "(로그 대기 중...)"
    grid.add_row(Panel(Text(log_text, style="dim"), title="coordinator stdout", expand=True))
    return grid


def _run_conversation_verify() -> bool:
    console.print("\n[bold]Stage 2B — 대화 검증[/bold]")
    console.print("  [dim]Enter 를 누르면 이 단계를 건너뜁니다.[/dim]\n")
    console.print("  coordinator를 tmux 세션으로 준비합니다...\n")

    if not _start_coordinator_tmux():
        return False

    console.print("\n  [cyan]\"Hey Hylion\" 을 말한 뒤 명령(예: 손 흔들어)을 해보세요.[/cyan]\n")

    components: dict[str, bool] = {k: False for k in _CONV_LABELS}
    log_lines: list[str] = []
    stop = threading.Event()

    def _watch_jsonl() -> None:
        session_file: Path | None = None
        last_pos = 0
        while not stop.is_set():
            new_file = _latest_session_file()
            if new_file != session_file:
                session_file = new_file
                last_pos = 0
            if session_file and session_file.exists():
                size = session_file.stat().st_size
                if size > last_pos:
                    with session_file.open(encoding="utf-8") as f:
                        f.seek(last_pos)
                        data = f.read()
                    last_pos = size
                    for line in data.splitlines():
                        if not line.strip():
                            continue
                        try:
                            evt = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        kind = evt.get("event", "")
                        if kind == "wake_activation":
                            components["웨이크워드"] = True
                        elif kind == "turn":
                            if evt.get("user_text"):
                                components["STT"] = True
                            if evt.get("assistant_text"):
                                components["LLM"] = True
            time.sleep(0.4)

    def _watch_tmux() -> None:
        while not stop.is_set():
            out, rc = _run(
                f"tmux capture-pane -p -t {TMUX_COORDINATOR} 2>/dev/null | tail -20",
                timeout=3,
            )
            if rc == 0 and out:
                lines = [l for l in out.splitlines() if l.strip()]
                log_lines.clear()
                log_lines.extend(lines[-12:])
                if any("[Speaker]" in l and "done" in l for l in lines):
                    components["TTS"] = True
            time.sleep(1)

    threading.Thread(target=_watch_jsonl, daemon=True).start()
    threading.Thread(target=_watch_tmux, daemon=True).start()

    try:
        with Live(console=console, refresh_per_second=2) as live:
            while True:
                live.update(_build_conv_panel(components, log_lines))
                if select.select([sys.stdin], [], [], 0.3)[0]:
                    sys.stdin.readline()
                    break
    finally:
        stop.set()

    passed = sum(v for v in components.values())
    total  = len(components)
    unverified = [k for k, v in components.items() if not v]

    if passed == total:
        console.print(Panel(
            Text(f"모든 컴포넌트 확인 ({passed}/{total}) — Stage 3 진행", style="bold green"),
            style="green",
        ))
    else:
        console.print(Panel(
            Text(f"{passed}/{total} 확인됨" +
                 (f"  미확인: {', '.join(unverified)}" if unverified else ""),
                 style="yellow"),
            style="yellow",
        ))
    return True


# ── 진입점 ────────────────────────────────────────────────────────────────────

def run() -> bool:
    """Stage 2 전체 실행: 2A(하드웨어) → 2B(대화).

    어느 단계에서든 Enter 를 누르면 나머지 Stage 2 를 건너뛰고
    coordinator 만 준비한 뒤 Stage 3 로 진행한다.
    """
    ok, hw_skipped = _run_hardware_tests()
    if not ok:
        return False

    if hw_skipped:
        console.print("\n  [dim]Stage 2 건너뜀 — coordinator 준비 후 Stage 3 진행[/dim]")
        _start_coordinator_tmux()
        return True

    return _run_conversation_verify()
