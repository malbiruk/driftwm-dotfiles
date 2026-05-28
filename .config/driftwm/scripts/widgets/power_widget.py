#!/usr/bin/env python3
"""Tiny power button widget. Click to open power menu."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text

from common import disable_mouse, enable_mouse, poll_click, synchronize_live

DIR = Path(__file__).resolve().parent
WIDTH = 4
HEIGHT = 1

POWER_ICON = "\U000f0425"  # 󰐥 nf-md-power


def render() -> Text:
    text = Text()
    text.append(f" {POWER_ICON}", style="bold red")
    return text


def open_menu() -> None:
    subprocess.Popen(
        [
            "footclient",
            "--app-id=drift-power-menu",
            "-T",
            " ",
            "--window-size-chars=18x6",
            "-o",
            "pad=8x6",
            "--",
            str(DIR / ".venv" / "bin" / "python"),
            str(DIR / "power_menu.py"),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run(stdin, stdout, width: int, height: int) -> None:  # type: ignore[no-untyped-def]
    console = Console(
        file=stdout,
        width=width,
        highlight=False,
        force_terminal=True,
        color_system="truecolor",
    )
    enable_mouse(stdin=stdin, stdout=stdout)
    try:
        with Live(render(), console=console, refresh_per_second=1) as live:
            synchronize_live(live)
            while True:
                live.update(render())
                click = poll_click(1.0, stdin=stdin)
                if click is not None:
                    open_menu()
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
