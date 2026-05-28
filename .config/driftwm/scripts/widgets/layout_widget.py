#!/usr/bin/env python3
"""Keyboard layout widget — shows active XKB layout."""

import sys

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

LAYOUT_SHORT = {
    "English": "EN",
    "Russian": "RU",
    "German": "DE",
    "French": "FR",
    "Spanish": "ES",
    "Ukrainian": "UA",
}

WIDTH = 7
HEIGHT = 4


def _short_layout(name: str) -> str:
    for key, short in LAYOUT_SHORT.items():
        if key in name:
            return short
    return name[:2].upper() if name else "en"


def render(height: int) -> Text:
    text = Text()
    top_pad = max((height - 2) // 2, 0)
    text.append("\n" * top_pad)

    state = read_state_file()
    layout = _short_layout(state.get("layout", "")).lower()

    text.append(f"  {ICON['kbd']}\n", style="magenta")
    text.append(f"  {layout}\n")

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
                poll_click(1.0, stdin=stdin)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
