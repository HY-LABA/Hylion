"""tui/stages/stage3_scenario.py — Stage 3: 시나리오 실행.

현재는 coordinator 가 이미 실행 중임을 확인하고 tmux 로그를 스트리밍한다.
coordinator 자체가 웨이크워드 → 대화 → standby 루프를 처리하므로
별도 시나리오 제어 없이 자유 대화 모드로 동작한다.

Enter → 종료.
"""
from __future__ import annotations

import os
import select
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
_VENV         = _PROJECT_ROOT / "jetson" / "expression" / ".venv"
_VENV_PY      = _VENV / "bin" / "python"
_CUSPARSELT   = _VENV / "lib" / "python3.10" / "site-packages" / "nvidia" / "cusparselt" / "lib"


def _shell(cmd: str, timeout: int = 5) -> tuple[str, int]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception:
        return "", -1


def _coordinator_pid() -> str | None:
    out, _ = _shell("pgrep -f 'hardcoding_coordinator'")
    pids = [p.strip() for p in out.splitlines()
            if p.strip() and os.path.exists(f"/proc/{p.strip()}")]
    return pids[0] if pids else None


def _ensure_coordinator() -> bool:
    """coordinator 가 tmux 세션으로 실행 중인지 확인, 없으면 기동."""
    _, rc = _shell(f"tmux has-session -t {TMUX_COORDINATOR} 2>/dev/null")
    if rc == 0 and _coordinator_pid():
        console.print(f"  [green]✓[/green] coordinator 실행 중 (tmux '{TMUX_COORDINATOR}')")
        return True

    # 기존 세션 정리 (다른 coordinator 가 올라와 있을 수 있음)
    _shell(f"tmux kill-session -t {TMUX_COORDINATOR} 2>/dev/null")
    console.print("  [yellow]△[/yellow] hardcoding_coordinator 기동 중...")
    coord_env = (
        f"LD_LIBRARY_PATH={_CUSPARSELT}:${{LD_LIBRARY_PATH:-}} "
        f"PYTHONUNBUFFERED=1 "
        f"HYLION_BHL_HOST=10.42.0.221 HYLION_BHL_PORT=9000 "
        f"HYLION_WAKEWORD_DEVICE_KEYWORD=P5HD "
        f"HYLION_WAKEWORD_SAMPLE_RATE=44100 "
        f"HYLION_MIC_SAMPLE_RATE=44100 "
        f"HYLION_WAKEWORD_THRESHOLD=0.3"
    )
    coord_cmd = f"{_VENV_PY} -m jetson.core.hardcoding_coordinator"
    _, rc = _shell(
        f"tmux new-session -d -s {TMUX_COORDINATOR} "
        f"'cd {_PROJECT_ROOT} && {coord_env} {coord_cmd}'",
        timeout=10,
    )
    if rc != 0:
        console.print("  [red]✗[/red] coordinator 기동 실패")
        return False

    for _ in range(15):
        time.sleep(1)
        if _coordinator_pid():
            console.print(f"  [green]✓[/green] coordinator 기동 완료")
            return True

    console.print("  [red]✗[/red] coordinator 기동 타임아웃")
    return False


def run() -> bool:
    console.print("\n[bold]Stage 3 — 시나리오 실행[/bold]")
    console.print("  [dim]coordinator 자유 대화 모드. Enter 를 누르면 종료합니다.[/dim]\n")

    if not _ensure_coordinator():
        return False

    console.print(
        "  [cyan]\"Hey Hylion\" 으로 대화를 시작하세요.[/cyan]"
    )
    console.print("  [dim]웨이크워드 → 대화 → '이제 쉬어' 로 standby 복귀.[/dim]\n")

    log_lines: list[str] = []
    stop = threading.Event()

    def _watch_tmux() -> None:
        while not stop.is_set():
            out, rc = _shell(
                f"tmux capture-pane -p -t {TMUX_COORDINATOR} 2>/dev/null | tail -30",
                timeout=3,
            )
            if rc == 0 and out:
                lines = [l for l in out.splitlines() if l.strip()]
                log_lines.clear()
                log_lines.extend(lines[-20:])
            time.sleep(1)

    threading.Thread(target=_watch_tmux, daemon=True).start()

    def _build_panel() -> Panel:
        log_text = "\n".join(log_lines) if log_lines else "(대기 중...)"
        return Panel(
            Text(log_text, style="dim"),
            title=f"coordinator stdout  [dim](tmux: {TMUX_COORDINATOR})  (Enter = 종료)[/dim]",
            expand=True,
        )

    try:
        with Live(console=console, refresh_per_second=2) as live:
            while True:
                live.update(_build_panel())
                if select.select([sys.stdin], [], [], 0.5)[0]:
                    sys.stdin.readline()
                    break
    finally:
        stop.set()

    _shell(f"tmux kill-session -t {TMUX_COORDINATOR} 2>/dev/null")
    console.print("\n  [dim]Stage 3 종료. coordinator tmux 세션을 종료했습니다.[/dim]")
    return True
