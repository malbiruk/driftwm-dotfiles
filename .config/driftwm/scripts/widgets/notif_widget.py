#!/usr/bin/env python3
"""Notification bell widget — shows unread count from swaync. Click to toggle."""

import contextlib
import subprocess
import sys

from common import (
    ICON,
    disable_mouse,
    enable_mouse,
    get_notifications,
    poll_click,
    synchronize_live,
    t,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 20
HEIGHT = 4


def render(height: int) -> Text:
    text = Text()
    top_pad = max((height - 2) // 2, 0)
    text.append("\n" * top_pad)

    count = get_notifications()
    text.append(f"  {ICON['bell']}  ", style="yellow")
    text.append(f"{t('notifications')}\n")
    if count > 0:
        text.append(f"     {count} {t('unread')}\n", style="yellow")
    else:
        text.append(f"     {t('all clear')}\n")

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
                if poll_click(1.0, stdin=stdin) is not None:
                    with contextlib.suppress(OSError):
                        subprocess.Popen(
                            ["swaync-client", "-t"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
