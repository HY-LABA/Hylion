#!/usr/bin/env python3
"""hylion-tui — 노트북에서 SSH로 Jetson + NUC 를 제어하는 3단계 TUI 런처.

3단계 분리:
  Stage 1 · 초기 셋팅       — preflight · CAN up · 관절 캘리브 (사람 손 필요)
  Stage 2 · Cold Start      — NUC 백엔드(make run · rl_controller · bridge) 기동
  Stage 3 · 전체 프로그램 실행 — Jetson coordinator 메인 루프

설계 결정:
  · 이 파일은 노트북에서 돈다. Jetson/NUC 와의 통신은 모두 `ssh` 호출.
  · 장기 실행 프로세스는 양쪽 tmux 세션으로 detach:
      NUC 측      hylion-bridge / hylion-bhl-lowlevel / hylion-bhl-policy
      Jetson 측   hylion-coordinator   ← SSH 끊김에도 살아남음 (배터리 사망 등)
    죽으면 세션이 사라지므로 헬스 체크가 단순해지고, 다른 노트북에서 `--attach`
    한 줄로 끊김 없이 인계 가능 (대화 history 보존).
  · 캘리브는 본질적으로 사용자 인터랙션이 필요하므로 `ssh -t` 로 노트북
    터미널을 일시 인계 → 끝나면 TUI 복귀.

요구사항:
  laptop$ pip install rich
  ~/.ssh/config 에 'jetson' / 'nuc' Host 등록 (NUC 는 ProxyJump=jetson 권장)
  Jetson + NUC 모두에 tmux 설치 (`sudo apt install tmux`).

자세한 사용법: docs/12_hylion_tui_launcher.md
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

try:
    from rich import box
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich.text import Text
except ImportError:
    sys.stderr.write(
        "ERROR: 'rich' 라이브러리가 필요합니다.\n"
        "  → pip install rich\n"
    )
    sys.exit(2)


# ── 설정 (환경변수로 override 가능) ──────────────────────────────────
JETSON_HOST = os.environ.get("HYLION_JETSON_HOST", "jetson")
NUC_HOST = os.environ.get("HYLION_NUC_HOST", "nuc")
JETSON_PROJECT = os.environ.get("HYLION_JETSON_PROJECT", "~/Hylion")
NUC_HYLION_PROJECT = os.environ.get("HYLION_NUC_PROJECT", "~/Hylion")
NUC_BHL_REPO = os.environ.get(
    "HYLION_NUC_BHL_REPO", "~/Berkeley-Humanoid-Lite-Lowlevel"
)
NUC_PYTHON = os.environ.get("HYLION_NUC_PYTHON", "python3")

# NUC 측 tmux 세션 이름
SESSION_BRIDGE = "hylion-bridge"
SESSION_LOWLEVEL = "hylion-bhl-lowlevel"
SESSION_POLICY = "hylion-bhl-policy"
# Jetson 측 tmux 세션 이름 (coordinator) — SSH 끊김에도 살아남도록 tmux 안에서 실행
SESSION_COORDINATOR = "hylion-coordinator"

LOG_BUFFER_MAX = 240
LOG_VISIBLE_LINES = 22
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SSH_CONFIG = os.environ.get(
    "HYLION_SSH_CONFIG",
    str(REPO_ROOT / "ssh_config"),
)


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAIL = "fail"
    SKIP = "skip"
    WAIT_HUMAN = "wait_human"


STATUS_GLYPH: dict[Status, tuple[str, str]] = {
    Status.PENDING: ("·", "dim"),
    Status.RUNNING: ("▶", "cyan"),
    Status.DONE: ("✓", "green"),
    Status.FAIL: ("✗", "red"),
    Status.SKIP: ("⊘", "yellow"),
    Status.WAIT_HUMAN: ("👤", "magenta"),
}


@dataclass
class Step:
    id: str
    title: str
    runner: Callable[["TUI", "Step"], bool]
    status: Status = Status.PENDING
    detail: str = ""


@dataclass
class Stage:
    id: int
    title: str
    subtitle: str
    steps: list[Step] = field(default_factory=list)

    @property
    def summary_status(self) -> Status:
        states = [s.status for s in self.steps]
        if any(s == Status.RUNNING for s in states):
            return Status.RUNNING
        if any(s == Status.FAIL for s in states):
            return Status.FAIL
        if any(s == Status.WAIT_HUMAN for s in states):
            return Status.WAIT_HUMAN
        if states and all(s in {Status.DONE, Status.SKIP} for s in states):
            return Status.DONE
        return Status.PENDING


# ══════════════════════════════════════════════════════════════════
# TUI core
# ══════════════════════════════════════════════════════════════════

class TUI:
    """3단계 진행 패널 + 라이브 로그 패널 + SSH 실행기."""

    def __init__(self, dry_run: bool = False) -> None:
        self.console = Console()
        self.dry_run = dry_run
        self.stages: list[Stage] = []
        self.log_lines: list[Text] = []
        self.current_action: str = "대기 중"
        self.live: Optional[Live] = None
        self.spawned_tmux_sessions: list[tuple[str, str]] = []

    def _ssh_base_args(self) -> list[str]:
        args = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=15",
        ]
        ssh_config = Path(LOCAL_SSH_CONFIG)
        if ssh_config.exists():
            args[1:1] = ["-F", str(ssh_config)]
        return args

    # ── 로그 + 렌더링 ────────────────────────────────────────────
    def log(self, text: str, style: str = "") -> None:
        self.log_lines.append(Text(text, style=style))
        if len(self.log_lines) > LOG_BUFFER_MAX:
            self.log_lines = self.log_lines[-LOG_BUFFER_MAX:]
        self._refresh()

    def set_action(self, text: str) -> None:
        self.current_action = text
        self._refresh()

    def _refresh(self) -> None:
        if self.live is not None:
            self.live.update(self.render())

    def render(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(self._render_stages(), name="stages",
                   size=self._stages_panel_height()),
            Layout(self._render_log(), name="log"),
            Layout(self._render_footer(), name="footer", size=3),
        )
        return layout

    def _stages_panel_height(self) -> int:
        # panel 테두리 2 + 각 stage(헤더 2 + steps + 빈줄 1)
        h = 2
        for st in self.stages:
            h += 2 + len(st.steps) + 1
        return h

    def _render_stages(self) -> Panel:
        body: list[Text] = []
        for stage in self.stages:
            g, c = STATUS_GLYPH[stage.summary_status]
            body.append(Text(f" {g}  Stage {stage.id} · {stage.title}",
                             style=f"bold {c}"))
            body.append(Text(f"        {stage.subtitle}", style="dim"))
            for step in stage.steps:
                sg, sc = STATUS_GLYPH[step.status]
                line = f"        {sg}  {step.title}"
                if step.detail:
                    line += f"   — {step.detail}"
                body.append(Text(line, style=sc))
            body.append(Text(""))
        title = (f"[bold]Hylion Launcher[/]   "
                 f"Jetson=[cyan]{JETSON_HOST}[/]  NUC=[cyan]{NUC_HOST}[/]")
        return Panel(Group(*body), title=title,
                     border_style="blue", box=box.ROUNDED)

    def _render_log(self) -> Panel:
        visible = self.log_lines[-LOG_VISIBLE_LINES:] if self.log_lines else []
        body = Group(*visible) if visible else Text("(로그 없음)", style="dim")
        return Panel(body,
                     title=f"[bold]Live log[/]   진행: {self.current_action}",
                     border_style="grey50", box=box.ROUNDED)

    def _render_footer(self) -> Panel:
        msg = ("단계 사이에 진행 확인 프롬프트가 표시됩니다 · "
               "Ctrl+C 로 중단 · "
               f"DRY-RUN={'ON' if self.dry_run else 'OFF'}")
        return Panel(Text(msg, style="dim"),
                     border_style="grey50", box=box.MINIMAL)

    # ── 인터랙티브 헬퍼 (Live 와 충돌 안 나게 pause/resume) ───────
    def confirm(self, question: str, default: bool = True) -> bool:
        if self.live:
            self.live.stop()
        try:
            return Confirm.ask(f"\n[bold]{question}[/]", default=default)
        finally:
            if self.live:
                self.live.start(refresh=True)

    # ── SSH 실행기 ───────────────────────────────────────────────
    def ssh_capture(self, host: str, command: str,
                    timeout: int = 120) -> tuple[int, str]:
        """비대화형 SSH — stdout 을 라이브 로그로 스트림. (rc, last_tail) 반환."""
        if self.dry_run:
            self.log(f"    [dry-run] ssh {host}: {command[:140]}", "yellow")
            return 0, ""
        self.log(f"    $ ssh {host}: {command[:160]}", "dim")
        cmd = self._ssh_base_args() + [host, command]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.log("    'ssh' 명령을 찾을 수 없음 — OpenSSH 설치 필요",
                     "red")
            return 127, ""

        tail: list[str] = []
        assert proc.stdout is not None
        start = time.time()
        try:
            for raw in proc.stdout:
                line = raw.rstrip()
                tail.append(line)
                if len(tail) > 60:
                    tail = tail[-60:]
                self.log(f"      {line}", "white")
                if time.time() - start > timeout:
                    proc.kill()
                    self.log(f"    ⏱ timeout {timeout}s — kill", "red")
                    return 124, "\n".join(tail)
        except Exception as exc:
            proc.kill()
            self.log(f"    SSH stream 오류: {exc}", "red")
            return 1, "\n".join(tail)
        proc.wait()
        return proc.returncode, "\n".join(tail)

    def ssh_interactive(self, host: str, command: str) -> int:
        """대화형 SSH (-t TTY). Live 일시 정지 후 사용자에게 터미널 인계."""
        if self.dry_run:
            self.log(f"    [dry-run] ssh -t {host}: {command[:140]}", "yellow")
            return 0
        if self.live:
            self.live.stop()
        self.console.print(
            f"\n[bold cyan]→ ssh -t {host}[/]  {command}\n"
            "[dim]   (이 SSH 세션이 끝나면 TUI 로 돌아옵니다)[/]\n"
        )
        try:
            return subprocess.call(self._ssh_base_args() + ["-t", host, command])
        finally:
            if self.live:
                self.live.start(refresh=True)

    def open_local_terminal(self, command: str, title: str = "Hylion") -> bool:
        """Best-effort local terminal launcher for GUI environments.

        Returns True if a terminal emulator was launched successfully.
        """
        if self.dry_run:
            self.log(f"    [dry-run] open terminal: {command[:160]}", "yellow")
            return True

        terminal_commands = [
            ["x-terminal-emulator", "-e", "bash", "-lc", command],
            ["gnome-terminal", "--", "bash", "-lc", command],
            ["konsole", "-e", "bash", "-lc", command],
            ["xfce4-terminal", "--command", f"bash -lc {shlex.quote(command)}"],
            ["xterm", "-e", "bash", "-lc", command],
            ["kitty", "-e", "bash", "-lc", command],
            ["alacritty", "-e", "bash", "-lc", command],
        ]

        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            self.log("    GUI display 환경이 없어 새 터미널을 열 수 없습니다.", "yellow")
            return False

        for cmd in terminal_commands:
            try:
                subprocess.Popen(cmd)
                self.log(f"    새 터미널 실행: {' '.join(cmd[:1])}", "cyan")
                return True
            except FileNotFoundError:
                continue
            except Exception as exc:
                self.log(f"    터미널 실행 실패: {exc}", "yellow")
                continue

        self.log("    지원되는 터미널 에뮬레이터를 찾지 못했습니다.", "yellow")
        return False

    def register_tmux_cleanup(self, host: str, session_name: str) -> None:
        if (host, session_name) not in self.spawned_tmux_sessions:
            self.spawned_tmux_sessions.append((host, session_name))

    def cleanup_spawned_tmux_sessions(self) -> None:
        if self.dry_run:
            return
        for host, session_name in reversed(self.spawned_tmux_sessions):
            try:
                self.ssh_capture(
                    host,
                    f"tmux kill-session -t {session_name} 2>/dev/null; echo killed_{session_name}",
                    timeout=10,
                )
            except Exception as exc:
                self.log(f"    cleanup 실패 ({host}:{session_name}): {exc}", "yellow")
        self.spawned_tmux_sessions.clear()

    # ── step 실행 wrapper ────────────────────────────────────────
    def run_step(self, step: Step) -> bool:
        step.status = Status.RUNNING
        self.set_action(f"Stage step — {step.title}")
        self.log("", "")
        self.log(f"▶ {step.title}", "cyan bold")
        ok = False
        try:
            ok = step.runner(self, step)
        except Exception as exc:
            step.detail = f"예외: {exc}"
            self.log(f"  ✗ 예외: {exc}", "red bold")
            ok = False

        if step.status == Status.SKIP:
            self.log(f"  ⊘ {step.title} — 건너뜀", "yellow")
        elif ok:
            step.status = Status.DONE
            self.log(f"  ✓ {step.title}", "green")
        else:
            step.status = Status.FAIL
            self.log(f"  ✗ {step.title}   {step.detail}", "red")
        return step.status in {Status.DONE, Status.SKIP}


# ══════════════════════════════════════════════════════════════════
# Step runners
# ══════════════════════════════════════════════════════════════════

def step_preflight(tui: TUI, step: Step) -> bool:
    cmd = f"cd {JETSON_PROJECT} && bash scripts/preflight.sh"
    rc, out = tui.ssh_capture(JETSON_HOST, cmd, timeout=60)
    if rc == 0:
        step.detail = "모든 항목 PASS"
        return True
    # preflight 는 WARN 만 있어도 rc=0, FAIL 이면 rc!=0
    # 실패 시 출력에서 [FAIL] 라인들을 발췌해 사용자에게 보여주기 좋게 요약
    fail_lines = [l for l in out.splitlines() if "[FAIL]" in l]
    if fail_lines:
        snippet = " | ".join(fail_lines[-3:])
    else:
        # 없다면 출력의 마지막 몇 줄을 요약
        tail = out.splitlines()[-6:]
        snippet = " | ".join(tail) if tail else "(no output)"
    step.detail = f"preflight FAIL (rc={rc}) — {snippet}"
    return False


def step_can_up(tui: TUI, step: Step) -> bool:
    # NOPASSWD sudo 우선, 안 되면 -t 로 비밀번호 받음.
    cmd_nopw = f"sudo -n bash {NUC_BHL_REPO}/scripts/start_can_transports.sh"
    rc, _ = tui.ssh_capture(NUC_HOST, cmd_nopw, timeout=20)
    if rc == 0:
        step.detail = "CAN up (NOPASSWD sudo)"
        return True
    tui.log("  sudo NOPASSWD 불가 → 인터랙티브 sudo 로 재시도", "yellow")
    cmd = f"sudo bash {NUC_BHL_REPO}/scripts/start_can_transports.sh"
    rc = tui.ssh_interactive(NUC_HOST, cmd)
    if rc != 0:
        step.detail = f"CAN up 실패 (rc={rc})"
        return False
    step.detail = "CAN up (interactive sudo)"
    return True


def step_calibrate(tui: TUI, step: Step) -> bool:
    step.status = Status.WAIT_HUMAN
    tui.log("👤 사람이 로봇 옆에 있어야 합니다.", "magenta bold")
    tui.log("   화면 안내에 따라 12 관절을 손으로 한계까지 돌리세요.",
            "magenta")
    tui.log("   끝나면 calibration.yaml 갱신을 자동 검증합니다.", "magenta")

    # 같은 부팅 안에서 이미 캘리브 했으면 굳이 다시 안 해도 됨.
    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"stat -c '%Y %n' {NUC_BHL_REPO}/calibration.yaml 2>/dev/null "
        f"|| echo MISSING",
        timeout=10,
    )
    boot_rc, boot_out = tui.ssh_capture(
        NUC_HOST, "stat -c '%Y' /proc/1 2>/dev/null", timeout=5
    )
    last_calib_ts = 0
    boot_ts = 0
    try:
        if "MISSING" not in out:
            last_calib_ts = int(out.split()[0])
        boot_ts = int(boot_out.strip())
    except (ValueError, IndexError):
        pass

    if last_calib_ts > boot_ts > 0:
        tui.log(f"  현재 부팅 이후 calibration.yaml 존재 (ts={last_calib_ts})",
                "green")
        if not tui.confirm(
            "이미 캘리브 되어 있습니다. 다시 할까요?", default=False
        ):
            step.status = Status.SKIP
            step.detail = "기존 calibration.yaml 사용"
            return True

    if not tui.confirm(
        "NUC 에 SSH 로 들어가 calibrate_joints.py 를 실행할까요?", default=True
    ):
        step.status = Status.SKIP
        step.detail = "사용자가 건너뜀"
        return True

    cmd = f"cd {NUC_BHL_REPO} && {NUC_PYTHON} scripts/calibrate_joints.py"
    rc = tui.ssh_interactive(NUC_HOST, cmd)
    if rc != 0:
        step.detail = f"calibrate_joints.py exit {rc}"
        return False

    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"test -f {NUC_BHL_REPO}/calibration.yaml "
        f"&& stat -c '%y' {NUC_BHL_REPO}/calibration.yaml",
        timeout=10,
    )
    if rc != 0:
        step.detail = "calibration.yaml 이 갱신되지 않음"
        return False
    step.detail = f"갱신: {out.strip().splitlines()[-1]}"
    return True


def step_daemons(tui: TUI, step: Step) -> bool:
    # Jetson 측 Ollama / MeloTTS 살아있는지 가볍게.
    cmd = (
        "timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/11434' 2>/dev/null "
        "&& echo OLLAMA_OK || echo OLLAMA_FAIL; "
        "timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/8001'  2>/dev/null "
        "&& echo MELO_OK   || echo MELO_FAIL"
    )
    rc, out = tui.ssh_capture(JETSON_HOST, cmd, timeout=15)
    parts = []
    parts.append("Ollama ✓" if "OLLAMA_OK" in out else "Ollama ✗")
    parts.append("MeloTTS ✓" if "MELO_OK" in out else "MeloTTS ✗")
    step.detail = " · ".join(parts)
    if "OLLAMA_FAIL" in out and "MELO_FAIL" in out:
        tui.log("  ⚠ Ollama·MeloTTS 둘 다 없음 — online(Groq) 경로만 사용 가능",
                "yellow")
    return True   # 정보성, FAIL 처리 안 함


def _ensure_tmux(tui: TUI, host: str = NUC_HOST) -> bool:
    rc, out = tui.ssh_capture(host, "command -v tmux || echo MISSING",
                              timeout=10)
    if "MISSING" in out:
        tui.log(
            f"  {host} 에 tmux 가 없습니다. `sudo apt install tmux` 후 재시도.",
            "red bold",
        )
        return False
    return True


def step_bridge(tui: TUI, step: Step) -> bool:
    # 0) Jetson 에서 NUC bridge TCP 가 이미 열려 있으면 통과
    # (NUC SSH 가 막혀 있어도 Stage 2/3 진행 가능)
    rc, out = tui.ssh_capture(
        JETSON_HOST,
        "timeout 3 bash -c 'exec 3<>/dev/tcp/10.42.0.221/9000' 2>/dev/null "
        "&& echo BRIDGE_OK || echo BRIDGE_FAIL",
        timeout=10,
    )
    if "BRIDGE_OK" in out:
        step.detail = "Jetson에서 NUC bridge(10.42.0.221:9000) TCP 확인"
        return True

    # 0-1) NUC 로컬에서 9000 포트가 이미 listen 중이면 bridge 는 살아있는 것
    rc, out = tui.ssh_capture(
        NUC_HOST,
        "ss -tln 2>/dev/null | grep ':9000' | head -1 || true",
        timeout=10,
    )
    if ":9000" in out:
        step.detail = "NUC에서 bridge(:9000) listen 확인"
        return True

    # 1) systemd 우선
    rc, out = tui.ssh_capture(
        NUC_HOST,
        "systemctl is-active hylion-bhl-bridge.service 2>/dev/null || true",
        timeout=10,
    )
    if out.strip().splitlines() and out.strip().splitlines()[-1] == "active":
        step.detail = "systemd: active"
        return True

    if not _ensure_tmux(tui):
        # NUC SSH 실패/미설치 등으로 tmux 확인이 불가해도,
        # Jetson 기준 bridge TCP 가 열려 있으면 운영상 통과로 간주
        rc2, out2 = tui.ssh_capture(
            JETSON_HOST,
            "timeout 3 bash -c 'exec 3<>/dev/tcp/10.42.0.221/9000' 2>/dev/null "
            "&& echo BRIDGE_OK || echo BRIDGE_FAIL",
            timeout=10,
        )
        if "BRIDGE_OK" in out2:
            step.detail = "NUC SSH 불가지만 Jetson에서 bridge TCP 확인"
            return True
        step.detail = "NUC SSH/tmux 확인 실패 + bridge TCP 미확인"
        return False

    # 2) 기존 tmux 세션
    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"tmux has-session -t {SESSION_BRIDGE} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" in out:
        step.detail = f"tmux session '{SESSION_BRIDGE}' 이미 동작 중"
        return True

    # 3) 새로 띄움. bridge.py 는 Hylion repo 에 있음.
    bridge_cmd = (
        f"tmux new -d -s {SESSION_BRIDGE} "
        f"\"cd {NUC_HYLION_PROJECT} && {NUC_PYTHON} -m nuc.bhl.bridge "
        f"2>&1 | tee /tmp/{SESSION_BRIDGE}.log\""
    )
    rc, _ = tui.ssh_capture(NUC_HOST, bridge_cmd, timeout=10)
    time.sleep(1.5)
    rc, out = tui.ssh_capture(
        NUC_HOST, "ss -tln | grep ':9000' | head -1 || true", timeout=10
    )
    if ":9000" not in out:
        # NUC 내부 ss 확인이 실패해도 Jetson 에서 접속 가능하면 성공 처리
        rc2, out2 = tui.ssh_capture(
            JETSON_HOST,
            "timeout 3 bash -c 'exec 3<>/dev/tcp/10.42.0.221/9000' 2>/dev/null "
            "&& echo BRIDGE_OK || echo BRIDGE_FAIL",
            timeout=10,
        )
        if "BRIDGE_OK" in out2:
            step.detail = "NUC 상태 조회 불가하지만 Jetson에서 bridge TCP 확인"
            return True
        step.detail = (
            f"bridge :9000 listen 안 잡힘 (로그: /tmp/{SESSION_BRIDGE}.log)"
        )
        return False
    tui.register_tmux_cleanup(NUC_HOST, SESSION_BRIDGE)
    step.detail = f"tmux '{SESSION_BRIDGE}' 새로 띄움 · :9000 listen 확인"
    return True


def step_lowlevel(tui: TUI, step: Step) -> bool:
    if not _ensure_tmux(tui):
        step.detail = "tmux 미설치"
        return False

    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"tmux has-session -t {SESSION_LOWLEVEL} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" in out:
        step.detail = f"tmux '{SESSION_LOWLEVEL}' 이미 동작 중"
        return True

    cmd = (
        f"tmux new -d -s {SESSION_LOWLEVEL} "
        f"\"cd {NUC_BHL_REPO} && make run 2>&1 "
        f"| tee /tmp/{SESSION_LOWLEVEL}.log\""
    )
    rc, _ = tui.ssh_capture(NUC_HOST, cmd, timeout=10)
    tui.log("  C++ control_loop 기동 대기 (5초)…", "dim")
    time.sleep(5)
    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"tmux has-session -t {SESSION_LOWLEVEL} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" not in out:
        step.detail = (
            f"세션이 5초 내 죽음 (로그: /tmp/{SESSION_LOWLEVEL}.log)"
        )
        return False
    tui.register_tmux_cleanup(NUC_HOST, SESSION_LOWLEVEL)
    step.detail = f"tmux '{SESSION_LOWLEVEL}' 동작 중 (250Hz control loop)"
    return True


def step_policy(tui: TUI, step: Step) -> bool:
    if not _ensure_tmux(tui):
        step.detail = "tmux 미설치"
        return False

    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"tmux has-session -t {SESSION_POLICY} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" in out:
        step.detail = f"tmux '{SESSION_POLICY}' 이미 동작 중"
        return True

    cmd = (
        f"tmux new -d -s {SESSION_POLICY} "
        f"\"cd {NUC_BHL_REPO} && {NUC_PYTHON} "
        f"-m berkeley_humanoid_lite_lowlevel.policy.rl_controller "
        f"2>&1 | tee /tmp/{SESSION_POLICY}.log\""
    )
    rc, _ = tui.ssh_capture(NUC_HOST, cmd, timeout=10)
    tui.log("  ONNX 정책 로드 대기 (3초)…", "dim")
    time.sleep(3)
    rc, out = tui.ssh_capture(
        NUC_HOST,
        f"tmux has-session -t {SESSION_POLICY} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" not in out:
        step.detail = (
            f"정책 프로세스가 3초 내 죽음 (로그: /tmp/{SESSION_POLICY}.log)"
        )
        return False
    tui.register_tmux_cleanup(NUC_HOST, SESSION_POLICY)
    step.detail = f"tmux '{SESSION_POLICY}' 동작 중 (ONNX @25Hz)"
    return True


def step_coordinator(tui: TUI, step: Step) -> bool:
    """coordinator 를 Jetson tmux 세션으로 띄우고 attach.

    SSH 끊김(배터리 dying, wifi 끊김 등) 시에도 coordinator 가 SIGHUP 으로 죽지
    않고 Jetson tmux 안에서 계속 동작. 새 노트북에서 `--attach` 로 끊김 없이
    인계 → 대화 history (최근 4 턴) 도 그대로 보존.
    """
    if not _ensure_tmux(tui, host=JETSON_HOST):
        step.detail = "Jetson 에 tmux 미설치"
        return False

    # 기존 tmux 세션 검사
    rc, out = tui.ssh_capture(
        JETSON_HOST,
        f"tmux has-session -t {SESSION_COORDINATOR} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    already_alive = "ALIVE" in out

    tui.log("", "")
    if already_alive:
        tui.log(
            f"기존 tmux '{SESSION_COORDINATOR}' 가 살아 있습니다. attach 합니다.",
            "cyan bold",
        )
        tui.log("  · history / session 모두 보존된 채로 인계됩니다.", "cyan")
    else:
        tui.log("Jetson tmux 안에 새 coordinator 세션을 띄웁니다.", "cyan bold")
        tui.log(
            "  · SSH 끊겨도 coordinator 는 Jetson 에서 계속 동작 → "
            "다음 노트북에서 `--attach` 로 끊김 없이 인계.",
            "cyan",
        )
    tui.log("  · Ctrl+B → d : detach (coordinator 살려두고 TUI 복귀)", "dim")
    tui.log("  · Ctrl+C    : coordinator 종료 (tmux 세션도 같이 닫힘)", "dim")

    if not tui.confirm(
        "지금 진행할까요?" if already_alive else "coordinator 를 지금 시작할까요?",
        default=True,
    ):
        step.status = Status.SKIP
        step.detail = "사용자가 보류"
        return True

    if not already_alive:
        # 새 세션 띄움 (detached). bash 의 부모를 sshd 가 아닌 tmux 로 만드는 것이
        # 핵심 — SSH 끊김 시 SIGHUP 이 안 옴.
        create_cmd = (
            f"tmux new -d -s {SESSION_COORDINATOR} "
            f"\"cd {JETSON_PROJECT} && bash scripts/run_coordinator.sh "
            f"2>&1 | tee /tmp/{SESSION_COORDINATOR}.log\""
        )
        rc, _ = tui.ssh_capture(JETSON_HOST, create_cmd, timeout=10)
        if rc != 0:
            step.detail = f"tmux new 실패 (rc={rc})"
            return False
        # warm-up 시작 직후 attach 해도 되지만, 세션이 1초 안에 죽는 경우를
        # 잡으려고 잠깐 대기.
        time.sleep(1.0)
        rc, out = tui.ssh_capture(
            JETSON_HOST,
            f"tmux has-session -t {SESSION_COORDINATOR} 2>/dev/null "
            f"&& echo ALIVE || echo DEAD",
            timeout=10,
        )
        if "ALIVE" not in out:
            step.detail = (
                f"tmux 세션이 시작 후 즉시 죽음 "
                f"(로그: /tmp/{SESSION_COORDINATOR}.log)"
            )
            return False
        tui.register_tmux_cleanup(JETSON_HOST, SESSION_COORDINATOR)

    # 새 로컬 터미널에서 coordinator tmux 세션을 attach 하도록 띄움.
    attach_cmd = (
        f"ssh -F {shlex.quote(LOCAL_SSH_CONFIG)} -t {shlex.quote(JETSON_HOST)} "
        f"{shlex.quote(f'tmux attach -d -t {SESSION_COORDINATOR}') }"
    )
    tui.log("", "")
    tui.log("새 터미널에서 coordinator 화면을 엽니다.", "cyan bold")
    tui.log("  새 창이 뜨면 그 안에서 실행 상태/출력값을 보게 됩니다.", "cyan")
    launched = tui.open_local_terminal(attach_cmd, title="Hylion coordinator")
    if not launched:
        tui.log(
            "  새 터미널을 열 수 없어 현재 터미널에서 attach 합니다.",
            "yellow",
        )
        rc = tui.ssh_interactive(JETSON_HOST, f"tmux attach -d -t {SESSION_COORDINATOR}")
        if rc not in (0, 130, 143):
            step.detail = f"coordinator attach 실패 (rc={rc})"
            return False

    step.detail = (
        "coordinator 시작 · 새 터미널에서 실시간 출력 확인 가능. "
        "TUI 종료 시 Jetson tmux 세션도 함께 종료된다."
    )
    return True


# ══════════════════════════════════════════════════════════════════
# Stage 정의
# ══════════════════════════════════════════════════════════════════

def build_stages() -> list[Stage]:
    return [
        Stage(
            1, "초기 셋팅",
            "사람이 로봇 옆에서 손을 대야 하는 단계 (매 부팅 1회)",
            [
                Step("preflight", "Jetson preflight 점검", step_preflight),
                Step("bridge", "NUC: hylion-bhl-bridge", step_bridge),
                Step("can-up", "NUC: CAN 인터페이스 up", step_can_up),
                Step("calibrate",
                     "NUC: 관절 캘리브레이션 (사람 필요)",
                     step_calibrate),
            ],
        ),
        Stage(
            2, "Cold Start",
            "백엔드 데몬 기동 — 노트북에서 원격으로",
            [
                Step("daemons",
                     "Jetson: Ollama / MeloTTS 데몬 점검",
                     step_daemons),
                Step("lowlevel",
                     "NUC: bhl-lowlevel (C++ make run)",
                     step_lowlevel),
                Step("policy",
                     "NUC: bhl-policy (ONNX rl_controller)",
                     step_policy),
            ],
        ),
        Stage(
            3, "전체 프로그램 실행",
            "Jetson coordinator 메인 루프 — Ctrl+C 로 종료",
            [
                Step("coordinator",
                     "Jetson: run_coordinator.sh",
                     step_coordinator),
            ],
        ),
    ]


# ══════════════════════════════════════════════════════════════════
# 보조 명령 (--status / --reset)
# ══════════════════════════════════════════════════════════════════

def cmd_status(dry_run: bool) -> int:
    tui = TUI(dry_run=dry_run)
    tui.console.rule("[bold]Hylion 상태 점검[/]")

    # Jetson 측 coordinator tmux
    rc, out = tui.ssh_capture(
        JETSON_HOST,
        f"tmux ls 2>/dev/null | grep '^{SESSION_COORDINATOR}' "
        f"|| echo '(coordinator tmux 미동작)'",
        timeout=10,
    )
    tui.console.print(f"\n[bold]Jetson tmux 세션 ({SESSION_COORDINATOR})[/]")
    tui.console.print(Text(out))

    # NUC 측 tmux
    rc, out = tui.ssh_capture(
        NUC_HOST,
        "tmux ls 2>/dev/null | grep '^hylion-' || echo '(tmux 세션 없음)'",
        timeout=10,
    )
    tui.console.print("\n[bold]NUC tmux 세션[/]")
    tui.console.print(Text(out or "(없음)"))

    # NUC 포트
    rc, out = tui.ssh_capture(
        NUC_HOST,
        "ss -tln 2>/dev/null | grep -E ':(9000|10000|10001|10011)' "
        "|| echo '(없음)'",
        timeout=10,
    )
    tui.console.print("\n[bold]NUC 포트 리슨[/]")
    tui.console.print(Text(out))

    # Jetson coordinator 프로세스 (tmux 안에 있어도 pgrep 으로 잡힘)
    rc, out = tui.ssh_capture(
        JETSON_HOST,
        "pgrep -af 'jetson.core.coordinator' || echo '(coordinator 미동작)'",
        timeout=10,
    )
    tui.console.print("\n[bold]Jetson coordinator 프로세스[/]")
    tui.console.print(Text(out))
    return 0


def cmd_reset(dry_run: bool) -> int:
    tui = TUI(dry_run=dry_run)
    tui.console.rule("[bold red]Hylion 세션 정리[/]")
    if Confirm.ask(
        "NUC 의 hylion-* tmux 세션 (bridge/lowlevel/policy) 을 모두 종료할까요?",
        default=False,
    ):
        for s in (SESSION_POLICY, SESSION_LOWLEVEL, SESSION_BRIDGE):
            tui.ssh_capture(
                NUC_HOST,
                f"tmux kill-session -t {s} 2>/dev/null; echo killed_{s}",
                timeout=10,
            )
    # coordinator 는 별도로 묻는다 — 운영 중 실수 방지
    if Confirm.ask(
        f"Jetson 의 {SESSION_COORDINATOR} tmux 도 종료할까요? "
        "(coordinator 가 죽고 history 소실됨)",
        default=False,
    ):
        tui.ssh_capture(
            JETSON_HOST,
            f"tmux kill-session -t {SESSION_COORDINATOR} 2>/dev/null; "
            f"echo killed_{SESSION_COORDINATOR}",
            timeout=10,
        )
    tui.console.print("\n[green]완료[/]")
    return 0


def cmd_attach(dry_run: bool) -> int:
    """기존 coordinator tmux 세션에 즉시 attach (다른 노트북에서 인계용).

    Stage 1·2 는 건너뛰고 Stage 3 의 attach 부분만 실행. tmux 세션이 없으면
    안내만 남기고 종료.
    """
    tui = TUI(dry_run=dry_run)
    if dry_run:
        tui.console.print(
            f"[yellow][dry-run][/] ssh -t {JETSON_HOST} "
            f"tmux attach -d -t {SESSION_COORDINATOR}"
        )
        return 0
    rc, out = tui.ssh_capture(
        JETSON_HOST,
        f"tmux has-session -t {SESSION_COORDINATOR} 2>/dev/null "
        f"&& echo ALIVE || echo DEAD",
        timeout=10,
    )
    if "ALIVE" not in out:
        tui.console.print(
            f"[red]Jetson 에 tmux '{SESSION_COORDINATOR}' 세션이 없습니다.[/]\n"
            "처음부터 시작:  [cyan]python3 scripts/hylion-tui.py[/]\n"
            "Stage 3 만:      [cyan]python3 scripts/hylion-tui.py --stage 3[/]"
        )
        return 1
    tui.console.print(
        f"\n[bold cyan]→ ssh -t {JETSON_HOST}[/]  "
        f"tmux attach -d -t {SESSION_COORDINATOR}\n"
        "[dim]   Ctrl+B → d : detach · Ctrl+C : coordinator 종료[/]\n"
    )
    return subprocess.call(
        tui._ssh_base_args() + [
            "-t", JETSON_HOST,
            f"tmux attach -d -t {SESSION_COORDINATOR}",
        ]
    )


# ══════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hylion 통합 런처 — 노트북에서 SSH 로 Jetson+NUC 제어"
    )
    parser.add_argument(
        "--stage", type=int, choices=[1, 2, 3],
        help="특정 단계만 실행 (생략 시 1→2→3 순차)",
    )
    parser.add_argument(
        "--no-confirm", action="store_true",
        help="단계 사이 진행 확인 프롬프트 생략",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 SSH 호출 없이 흐름만 확인",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="현재 NUC tmux 세션 / 포트 / Jetson coordinator 상태 점검만",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="hylion-* tmux 세션 정리 (NUC + Jetson coordinator)",
    )
    parser.add_argument(
        "--attach", action="store_true",
        help="기존 Jetson coordinator tmux 세션에 즉시 attach "
             "(다른 노트북에서 인계할 때)",
    )
    args = parser.parse_args()

    if args.status:
        return cmd_status(args.dry_run)
    if args.reset:
        return cmd_reset(args.dry_run)
    if args.attach:
        return cmd_attach(args.dry_run)

    tui = TUI(dry_run=args.dry_run)
    tui.stages = build_stages()
    stages_to_run = [
        s for s in tui.stages if args.stage is None or s.id == args.stage
    ]

    tui.console.print("\n[bold]Hylion 통합 런처[/]")
    tui.console.print(f"  Jetson host: [cyan]{JETSON_HOST}[/]")
    tui.console.print(f"  NUC host:    [cyan]{NUC_HOST}[/]")
    tui.console.print(f"  Jetson 프로젝트: [dim]{JETSON_PROJECT}[/]")
    tui.console.print(f"  NUC BHL 리포:    [dim]{NUC_BHL_REPO}[/]")
    tui.console.print(f"  NUC Hylion 리포: [dim]{NUC_HYLION_PROJECT}[/]")
    if args.dry_run:
        tui.console.print("  [yellow]DRY-RUN[/] — 실제 SSH 호출 없음")
    tui.console.print("")

    exit_code = 0
    with Live(tui.render(), console=tui.console,
              refresh_per_second=6, screen=False) as live:
        tui.live = live
        try:
            for idx, stage in enumerate(stages_to_run):
                tui.set_action(f"Stage {stage.id}")
                tui.log("", "")
                tui.log(
                    f"━━━ Stage {stage.id}: {stage.title} ━━━", "blue bold"
                )
                tui.log(f"     {stage.subtitle}", "dim")
                for step in stage.steps:
                    proceed = tui.run_step(step)
                    # 실패 시 즉시 종료하지 않고 재시도/건너뜀/중단 옵션 제공
                    while not proceed:
                        tui.log("", "")
                        tui.log(
                            f"❌ '{step.title}' 실패: {step.detail}",
                            "red bold",
                        )
                        # 재시도 요청
                        retry = tui.confirm(f"'{step.title}'을(를) 다시 시도할까요?", default=True)
                        if retry:
                            # 상태 초기화 후 재시도
                            step.status = Status.PENDING
                            step.detail = ""
                            proceed = tui.run_step(step)
                            continue
                        # 재시도를 원치 않으면 건너뛸지 물어봄
                        skip = tui.confirm(f"'{step.title}'을(를) 건너뛰고 다음으로 진행할까요?", default=False)
                        if skip:
                            step.status = Status.SKIP
                            tui.log(f"  ⊘ {step.title} — 건너뜀 (사용자 결정)", "yellow")
                            proceed = True
                            break
                        # 건너뛰지도 않으면 전체 중단
                        tui.log(f"중단: '{step.title}' 실패로 워크플로우를 종료합니다.", "red")
                        time.sleep(1.0)
                        return 1
                if not args.no_confirm and idx < len(stages_to_run) - 1:
                    if not tui.confirm(
                        f"Stage {stage.id} 완료. 다음 단계 진행할까요?",
                        default=True,
                    ):
                        tui.log("사용자가 다음 단계를 보류함.", "yellow")
                        return 0
            tui.log("", "")
            tui.log("✅ 모든 단계 완료", "green bold")
            tui.set_action("완료")
            time.sleep(2.0)
        except KeyboardInterrupt:
            tui.log("\n사용자 인터럽트 (Ctrl+C)", "yellow bold")
            # Ctrl+C 시 TUI가 띄운 tmux 세션은 정리
            tui.cleanup_spawned_tmux_sessions()
            time.sleep(1.0)
            return 130
        finally:
            tui.live = None

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
