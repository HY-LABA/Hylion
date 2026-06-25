"""tui/main.py — Hylion TUI 진입점.

실행:
    cd ~/Hylion
    python3 -m tui.main
"""
from __future__ import annotations

import sys

from rich.console import Console

from tui.stages.stage1_preflight import run as run_stage1
from tui.stages.stage2_verify import run as run_stage2
from tui.stages.stage3_scenario import run as run_stage3

console = Console()


def main() -> None:
    console.rule("[bold]Hylion TUI[/bold]")

    passed = run_stage1()
    if not passed:
        sys.exit(1)

    run_stage2()
    run_stage3()


if __name__ == "__main__":
    main()
