#!/usr/bin/env python3
"""Clock + date widget."""

import subprocess
import sys
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
HEIGHT = 6


def center(line: str) -> str:
    pad = max((WIDTH - len(line)) // 2, 0)
    return " " * pad + line


def render(height: int) -> Text:
    text = Text()
    time.tzset()
    now = datetime.now()  # noqa: DTZ005
    top_pad = max((height - 4) // 2, 0)
    text.append("\n" * top_pad)

    r1, r2 = render_big_time(now.strftime("%H:%M"), colon_on=now.second % 2 == 0)
    text.append(center(r1) + "\n", style="bold")
    text.append(center(r2) + "\n", style="bold")
    text.append("\n")
    date_line = now.strftime("%A · %B %d").lower()
    text.append(center(date_line) + "\n")
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
                click = poll_click(1.0, stdin=stdin)
                if click is not None:
                    subprocess.Popen(
                        ["gnome-clocks"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
