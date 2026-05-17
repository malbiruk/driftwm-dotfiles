#!/usr/bin/env python3
"""Canvas position widget — shows saved (home-toggle) viewport coords."""

import atexit
import os

from common import (
    ICON,
    disable_mouse,
    enable_mouse,
    poll_click,
    read_state_file,
    synchronize_live,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 25
console = Console(width=WIDTH, highlight=False)


def render() -> Text:
    text = Text()
    try:
        term_h = os.get_terminal_size().lines
    except OSError:
        term_h = 4
    top_pad = max((term_h - 2) // 2, 0)
    text.append("\n" * top_pad)

    state = read_state_file()
    x = state.get("saved_x") or state.get("x", "—")
    y = state.get("saved_y") or state.get("y", "—")
    zoom = state.get("saved_zoom") or state.get("zoom", "—")

    text.append(f"   {ICON['pos']}  ", style="cyan")
    text.append(f"x: {x}  y: {y}\n")
    text.append(f"   {ICON['zoom']}  ", style="yellow")
    text.append(f"zoom: {zoom}\n")

    return text


atexit.register(disable_mouse)
enable_mouse()
try:
    with Live(render(), console=console, refresh_per_second=2) as live:
        synchronize_live(live)
        while True:
            live.update(render())
            poll_click(1.0)
finally:
    disable_mouse()
