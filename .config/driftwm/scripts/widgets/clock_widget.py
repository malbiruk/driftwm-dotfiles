#!/usr/bin/env python3
"""Clock + date widget."""

import atexit
import os
import subprocess
import time
from datetime import datetime

from common import (
    disable_mouse,
    enable_mouse,
    poll_click,
    render_big_time,
    synchronize_live,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 36
console = Console(width=WIDTH, highlight=False)


def center(line: str) -> str:
    pad = max((WIDTH - len(line)) // 2, 0)
    return " " * pad + line


def render() -> Text:
    text = Text()
    time.tzset()
    now = datetime.now()  # noqa: DTZ005
    try:
        term_h = os.get_terminal_size().lines
    except OSError:
        term_h = 6
    top_pad = max((term_h - 4) // 2, 0)
    text.append("\n" * top_pad)

    r1, r2 = render_big_time(now.strftime("%H:%M"), colon_on=now.second % 2 == 0)
    text.append(center(r1) + "\n", style="bold")
    text.append(center(r2) + "\n", style="bold")
    text.append("\n")
    date_line = now.strftime("%A · %B %d").lower()
    text.append(center(date_line) + "\n")
    return text


atexit.register(disable_mouse)
enable_mouse()
try:
    with Live(render(), console=console, refresh_per_second=1) as live:
        synchronize_live(live)
        while True:
            live.update(render())
            click = poll_click(1.0)
            if click is not None:
                subprocess.Popen(
                    ["gnome-clocks"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
finally:
    disable_mouse()
