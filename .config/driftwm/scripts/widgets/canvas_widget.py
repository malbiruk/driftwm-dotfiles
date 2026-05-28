#!/usr/bin/env python3
"""Canvas position widget — shows saved (home-toggle) viewport coords."""

import sys

from common import (
    ICON,
    disable_mouse,
    enable_mouse,
    poll_click,
    read_state_file,
    synchronize_live,
    t,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 25
HEIGHT = 4


def render(height: int) -> Text:
    text = Text()
    top_pad = max((height - 2) // 2, 0)
    text.append("\n" * top_pad)

    state = read_state_file()
    x = state.get("saved_x") or state.get("x", "—")
    y = state.get("saved_y") or state.get("y", "—")
    zoom = state.get("saved_zoom") or state.get("zoom", "—")

    text.append(f"   {ICON['pos']}  ", style="cyan")
    text.append(f"x: {x}  y: {y}\n")
    text.append(f"   {ICON['zoom']}  ", style="yellow")
    text.append(f"{t('zoom')}: {zoom}\n")

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
        with Live(render(height), console=console, refresh_per_second=2) as live:
            synchronize_live(live)
            while True:
                live.update(render(height))
                poll_click(1.0, stdin=stdin)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
