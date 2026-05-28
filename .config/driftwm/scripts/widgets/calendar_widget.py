#!/usr/bin/env python3
"""Monthly calendar widget with today highlighted."""

import calendar
import sys
from datetime import datetime

from common import ICON, disable_mouse, enable_mouse, poll_click, synchronize_live
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 22
HEIGHT = 11


def render(height: int) -> Text:
    now = datetime.now()  # noqa: DTZ005
    year, month, day = now.year, now.month, now.day

    cal = calendar.monthcalendar(year, month)
    content_lines = 2 + len(cal)  # header + day names + weeks
    top_pad = max((height - content_lines) // 2, 0)

    text = Text()
    text.append("\n" * top_pad)
    header = f"{calendar.month_name[month].lower()} {year}"
    text.append(f" {ICON['calendar']} {header}\n", style="bold")
    day_header = " ".join(calendar.day_abbr[i][:2].lower() for i in range(7))
    text.append(f" {day_header}\n")

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
        with Live(render(height), console=console, refresh_per_second=1) as live:
            synchronize_live(live)
            while True:
                live.update(render(height))
                poll_click(30.0, stdin=stdin)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
