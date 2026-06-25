"""tui/stages/stage1_preflight.py — Stage 1: 사전 점검."""
from __future__ import annotations

from rich.console import Console

from tui.stages.utils.checks import GROUPS
from tui.ui.panels import render_group, render_summary

console = Console()


def run() -> bool:
    """전체 점검 실행. 모두 통과하면 True 반환."""
    console.print("\n[bold]Stage 1 — 사전 점검[/bold]\n")

    all_passed = True
    for group_name, check_fns in GROUPS:
        results = [fn() for fn in check_fns]
        render_group(group_name, results)
        if any(r.failed for r in results):
            all_passed = False

    render_summary(all_passed)
    return all_passed
