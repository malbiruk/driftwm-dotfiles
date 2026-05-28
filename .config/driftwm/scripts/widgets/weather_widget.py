#!/usr/bin/env python3
"""Weather widget — fetches from Open-Meteo, caches for 10 minutes."""

import sys
import time

from common import (
    disable_mouse,
    enable_mouse,
    get_weather,
    poll_click,
    synchronize_live,
    t,
    weather_icon,
)
from rich.console import Console
from rich.live import Live
from rich.text import Text

WIDTH = 22
HEIGHT = 6

REFRESH_INTERVAL = 600  # 10 minutes
RETRY_INTERVAL = 30  # retry quickly when offline

cached_weather: dict | None = None
last_fetch: float = 0


def fetch_if_stale() -> dict | None:
    global cached_weather, last_fetch  # noqa: PLW0603
    now = time.time()
    interval = REFRESH_INTERVAL if cached_weather is not None else RETRY_INTERVAL
    if now - last_fetch > interval:
        last_fetch = now
        result = get_weather()
        if result is not None:
            cached_weather = result
    return cached_weather


def render() -> Text:
    w = fetch_if_stale()

    text = Text()
    text.append("\n")

    if w is None:
        text.append(f"  {t('offline')}\n\n\n")
        return text

    location = w.get("location", "")
    icon = weather_icon(w["desc"])
    if location:
        text.append(f"   {icon} {location.lower()}\n")
    text.append(f"   {w['temp']}°C", style="bold")
    text.append(f" {t(w['desc']).lower()}\n")
    text.append(f"   {t('H')}:{w['high']}°  {t('L')}:{w['low']}°\n")
    text.append(
        f"   {t('tmrw')}: {w['tomorrow_temp']}°C\n",
    )

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
        with Live(render(), console=console, refresh_per_second=1) as live:
            synchronize_live(live)
            while True:
                live.update(render())
                poll_click(60.0, stdin=stdin)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
