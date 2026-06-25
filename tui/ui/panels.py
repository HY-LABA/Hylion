"""tui/ui/panels.py — rich 공통 UI 컴포넌트."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tui.stages.config import CheckResult, Status

console = Console()

# ── 상태별 색상·아이콘 ────────────────────────────────────────────────────────
_STYLE: dict[Status, tuple[str, str]] = {
    Status.OK:   ("green",  "✓"),
    Status.WARN: ("yellow", "△"),
    Status.FAIL: ("red",    "✗"),
}


def _status_text(status: Status) -> Text:
    style, icon = _STYLE[status]
    return Text(f"{icon} {status.value}", style=style)


def render_group(group_name: str, results: list[CheckResult]) -> None:
    """그룹 이름 + 점검 결과 테이블 출력."""
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column(width=10)   # 상태
    table.add_column(width=20)   # 항목명
    table.add_column()           # 메시지 + hint

    for r in results:
        style, icon = _STYLE[r.status]
        msg = Text(r.message)
        if r.hint:
            msg.append(f"\n→ {r.hint}", style="dim")
        table.add_row(
            Text(f"{icon} {r.status.value}", style=style),
            Text(r.name, style="bold"),
            msg,
        )

    # 그룹 전체 상태 결정
    if any(r.failed for r in results):
        group_status = Status.FAIL
    elif any(r.status == Status.WARN for r in results):
        group_status = Status.WARN
    else:
        group_status = Status.OK

    style, icon = _STYLE[group_status]
    title = Text(f"{icon} {group_name}", style=f"bold {style}")
    console.print(Panel(table, title=title, title_align="left"))


def render_summary(passed: bool) -> None:
    """전체 점검 결과 요약 출력."""
    if passed:
        console.print(Panel(
            Text("모든 점검 통과 — Stage 2 진행 가능", style="bold green"),
            style="green",
        ))
    else:
        console.print(Panel(
            Text("점검 실패 항목 있음 — 위 FAIL 항목 해결 후 재실행", style="bold red"),
            style="red",
        ))
