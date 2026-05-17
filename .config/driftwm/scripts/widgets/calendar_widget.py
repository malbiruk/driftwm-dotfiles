#!/usr/bin/env python3
"""Monthly calendar widget with today highlighted."""

import atexit
import calendar
import os
from datetime import datetime

from common import ICON, disable_mouse, enable_mouse, poll_click, synchronize_live
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console(width=22, highlight=False)


def render() -> Text:
    now = datetime.now()  # noqa: DTZ005
    year, month, day = now.year, now.month, now.day

    cal = calendar.monthcalendar(year, month)
    content_lines = 2 + len(cal)  # header + day names + weeks

    try:
        term_h = os.get_terminal_size().lines
    except OSError:
        term_h = 11
    top_pad = max((term_h - content_lines) // 2, 0)

    text = Text()
    text.append("\n" * top_pad)
    header = f"{calendar.month_name[month].lower()} {year}"
    text.append(f" {ICON['calendar']} {header}\n", style="bold")
    text.append(" mo tu we th fr sa su\n")

    for week in cal:
        line = Text(" ")
        for d in week:
            if d == 0:
                line.append("   ")
            elif d == day:
                line.append(f"{d:2d}", style="bold reverse")
                line.append(" ")
            else:
                line.append(f"{d:2d} ")
        line.append("\n")
        text.append(line)

    return text


atexit.register(disable_mouse)
enable_mouse()
try:
    with Live(render(), console=console, refresh_per_second=1) as live:
        synchronize_live(live)
        while True:
            live.update(render())
            poll_click(30.0)
finally:
    disable_mouse()
