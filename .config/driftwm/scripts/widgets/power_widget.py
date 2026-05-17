#!/usr/bin/env python3
"""Tiny power button widget. Click to open power menu."""

import atexit
import subprocess
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text

from common import disable_mouse, enable_mouse, poll_click, synchronize_live

DIR = Path(__file__).resolve().parent
console = Console(width=4, highlight=False)

POWER_ICON = "\U000f0425"  # 󰐥 nf-md-power


def render() -> Text:
    text = Text()
    text.append(f" {POWER_ICON}", style="bold red")
    return text


def open_menu() -> None:
    subprocess.Popen(
        [
            "alacritty",
            "--class",
            "drift-power-menu",
            "-o",
            "window.dimensions.columns=18",
            "-o",
            "window.dimensions.lines=6",
            "-o",
            "window.padding.x=8",
            "-o",
            "window.padding.y=6",
            # "-o",
            # 'window.decorations="None"',
            "-e",
            "uv",
            "run",
            "--project",
            str(DIR),
            "python",
            str(DIR / "power_menu.py"),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


atexit.register(disable_mouse)
enable_mouse()
try:
    with Live(render(), console=console, refresh_per_second=1) as live:
        synchronize_live(live)
        while True:
            live.update(render())
            click = poll_click(1.0)
            if click is not None:
                open_menu()
finally:
    disable_mouse()
