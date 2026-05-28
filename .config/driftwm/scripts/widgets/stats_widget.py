#!/usr/bin/env python3
"""System stats + connections widget. Click zones dispatch actions."""

import contextlib
import subprocess
import sys
from collections import deque
from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text

from common import (
    ICON,
    battery_icon,
    brightness_icon,
    disable_mouse,
    enable_mouse,
    get_battery,
    get_battery_time_upower,
    get_bluetooth,
    get_brightness,
    get_cpu_percent,
    get_ram,
    get_volume,
    get_wifi,
    poll_click,
    progress_bar,
    sparkline,
    synchronize_live,
    t,
    volume_icon,
    wifi_icon,
)

WIDTH = 36
HEIGHT = 11
PAD = 15
cpu_history: deque[float] = deque(maxlen=10)
ram_history: deque[float] = deque(maxlen=10)

# Slow-poll cache for subprocess-dependent data (volume, SSID, bluetooth)
SLOW_POLL_INTERVAL = 10  # seconds
_slow_state: dict = {"cache": {}, "counter": 0}


def _get_slow_data() -> dict:
    """Return cached slow-poll data, refreshing every SLOW_POLL_INTERVAL seconds."""
    _slow_state["counter"] += 1
    if _slow_state["counter"] >= SLOW_POLL_INTERVAL or not _slow_state["cache"]:
        _slow_state["counter"] = 0
        _slow_state["cache"] = {
            "volume": get_volume(),
            "wifi": get_wifi(),
            "bluetooth": get_bluetooth(),
            "battery_hours": get_battery_time_upower(),
        }
    return _slow_state["cache"]


# Maps terminal row (1-based) → action. Built each render().
# Actions: list[str] = spawn command, str = special action, tuple = bar handler
click_map: dict[int, list[str] | str | tuple | Callable[[], None]] = {}

# Click actions per section
ACTION_CPU = ["gnome-system-monitor"]
ACTION_RAM = ["gnome-system-monitor"]
ACTION_VOL = ["cosmic-settings", "sound"]
ACTION_WIFI = ["cosmic-settings", "wireless"]
ACTION_BT = ["cosmic-settings", "bluetooth"]

# Bar geometry: 3 spaces + icon(2) + 2 spaces + PAD(15) = column 22, width 10
BAR_X_START = 22
BAR_WIDTH = 10


def _bar_pct_from_x(x: int) -> int | None:
    """Convert terminal x coordinate to 0-100 percentage, or None if outside bar."""
    if x < BAR_X_START or x >= BAR_X_START + BAR_WIDTH:
        return None
    return min(round((x - BAR_X_START + 1) / BAR_WIDTH * 100), 100)


def _set_volume(pct: int) -> None:
    current, _ = get_volume()
    delta = pct - current
    if delta == 0:
        return
    subprocess.Popen(
        ["swayosd-client", "--output-volume", f"{delta:+d}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ── Caffeine (swayidle toggle) ─────────────────────────────

IDLE_SH = str(Path("~/.config/driftwm/scripts/idle.sh").expanduser())
INHIBITOR_TAG = "drift-caffeine"


def _is_swayidle_running() -> bool:
    return (
        subprocess.run(
            ["pgrep", "-x", "swayidle"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _inhibitor_running() -> bool:
    return (
        subprocess.run(
            ["pgrep", "-f", f"systemd-inhibit.*--who={INHIBITOR_TAG}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _start_inhibitor() -> None:
    if _inhibitor_running():
        return
    subprocess.Popen(
        [
            "systemd-inhibit",
            "--what=handle-lid-switch",
            "--mode=block",
            f"--who={INHIBITOR_TAG}",
            "--why=caffeine",
            "sleep",
            "infinity",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _stop_inhibitor() -> None:
    subprocess.run(
        ["pkill", "-f", f"systemd-inhibit.*--who={INHIBITOR_TAG}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


_caffeine_on = not _is_swayidle_running()
# Sync inhibitor with caffeine state in case the widget was restarted.
if _caffeine_on:
    _start_inhibitor()
else:
    _stop_inhibitor()


def _toggle_caffeine() -> None:
    global _caffeine_on  # noqa: PLW0603
    if _caffeine_on:
        # Turn off caffeine → restart swayidle, release lid-switch inhibitor.
        subprocess.Popen(
            [IDLE_SH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _stop_inhibitor()
        _caffeine_on = False
    else:
        # Turn on caffeine → kill swayidle, hold lid-switch inhibitor.
        subprocess.run(
            ["killall", "swayidle"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        _start_inhibitor()
        _caffeine_on = True


def _set_brightness(pct: int) -> None:
    subprocess.Popen(
        ["swayosd-client", "--brightness", str(pct)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def load_color(pct: float) -> str:
    if pct < 50:
        return "green"
    if pct < 80:
        return "yellow"
    return "red"


def bat_color(pct: int) -> str:
    if pct > 50:
        return "green"
    if pct > 20:
        return "yellow"
    return "red"


def _render_cpu_ram(text: Text, line: int) -> int:
    cpu = get_cpu_percent()
    cpu_history.append(cpu)
    text.append(f"   {ICON['cpu']}  ", style="cyan")
    info = f"{t('cpu')}  {cpu:3.0f}%"
    text.append(f"{info:<{PAD}}")
    text.append(f"{sparkline(cpu_history)}\n", style=load_color(cpu))
    click_map[line] = ACTION_CPU
    line += 1

    ram_used, ram_total, swap_used = get_ram()
    ram_pct = ram_used / ram_total * 100 if ram_total > 0 else 0
    ram_history.append(ram_pct)
    text.append(f"   {ICON['ram']}  ", style="magenta")
    if swap_used > 0.1:
        info = f"{t('ram')}  {ram_used:.0f}+{swap_used:.0f}/{ram_total:.0f}G"
    else:
        info = f"{t('ram')}  {ram_used:.1f}/{ram_total:.0f}G"
    text.append(f"{info:<{PAD}}")
    text.append(f"{sparkline(ram_history)}\n", style=load_color(ram_pct))
    click_map[line] = ACTION_RAM
    return line + 1


_battery_show_time = False


def _toggle_battery_display() -> None:
    global _battery_show_time  # noqa: PLW0603
    _battery_show_time = not _battery_show_time


def _render_battery(text: Text, line: int, slow: dict) -> int:
    bat = get_battery()
    if not bat:
        return line
    pct, status, hours = bat
    # Prefer UPower's smoothed time-remaining; fall back to instantaneous sysfs value.
    if slow.get("battery_hours") is not None:
        hours = slow["battery_hours"]
    icon = battery_icon(pct, status)
    color = bat_color(pct)
    text.append(f"   {icon}  ", style=color)
    if _battery_show_time and hours is not None:
        label = (
            f"{t('bat')}  {hours * 60:.0f}m"
            if hours < 1
            else f"{t('bat')}  {hours:.1f}h"
        )
    else:
        label = f"{t('bat')}  {pct:3d}%"
    text.append(label)
    remaining = PAD - len(label)
    text.append(f"{'':>{remaining}}")
    text.append(f"{progress_bar(pct)}\n", style=color)
    click_map[line] = _toggle_battery_display
    return line + 1


def _render_volume(text: Text, line: int, slow: dict) -> int:
    vol, muted = slow["volume"]
    vicon = volume_icon(vol, muted=muted)
    if muted:
        text.append(f"   {vicon}  ")
        info = f"{t('vol')}  {t('muted')}"
        text.append(f"{info:<{PAD}}")
        text.append(f"{progress_bar(vol)}\n")
    else:
        text.append(f"   {vicon}  ", style="blue")
        info = f"{t('vol')}  {vol:3d}%"
        text.append(f"{info:<{PAD}}")
        text.append(f"{progress_bar(vol)}\n", style="blue")
    click_map[line] = ("vol_bar", _set_volume, ACTION_VOL)
    return line + 1


def _render_brightness(text: Text, line: int) -> int:
    bri = get_brightness()
    if bri is None:
        return line
    bicon = brightness_icon(bri)
    text.append(f"   {bicon}  ", style="yellow")
    info = f"{t('bri')}  {bri:3d}%"
    if _caffeine_on:
        text.append(info)
        text.append(f"   {ICON['caffeine']}", style="yellow")
        text.append(f"{'':>{PAD - 9 - 4}}")
    else:
        text.append(f"{info:<{PAD}}")
    text.append(f"{progress_bar(bri)}\n", style="yellow")
    click_map[line] = ("bri_bar", _set_brightness, None)
    return line + 1


def _render_connections(text: Text, line: int, slow: dict) -> int:
    wifi = slow["wifi"]
    if wifi:
        ssid, signal = wifi
        wicon = wifi_icon(signal)
        display_ssid = ssid[:14] if len(ssid) > 14 else ssid
        text.append(f"   {wicon}  ", style="cyan")
        text.append(f"{display_ssid} ({signal}%)\n")
    else:
        text.append(f"   {ICON['wifi_off']}  ")
        text.append(f"{t('offline')}\n")
    click_map[line] = ACTION_WIFI
    line += 1

    bt = slow["bluetooth"]
    if bt:
        text.append(f"   {bt}\n", style="blue")
        click_map[line] = ACTION_BT
    return line + 1


def render(height: int) -> Text:
    click_map.clear()
    text = Text()
    top_pad = max((height - 8) // 2, 0)
    text.append("\n" * top_pad)
    line = 1 + top_pad

    slow = _get_slow_data()
    line = _render_cpu_ram(text, line)
    text.append("\n")
    line += 1
    line = _render_battery(text, line, slow)
    line = _render_volume(text, line, slow)
    line = _render_brightness(text, line)
    text.append("\n")
    line += 1
    _render_connections(text, line, slow)

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
                if click is None:
                    continue
                x, y = click
                action = click_map.get(y)
                if callable(action):
                    action()
                elif isinstance(action, tuple):
                    kind, setter, fallback = action
                    pct = _bar_pct_from_x(x)
                    if pct is not None:
                        setter(pct)
                        _slow_state["counter"] = SLOW_POLL_INTERVAL
                    elif kind == "bri_bar":
                        _toggle_caffeine()
                    elif kind == "vol_bar" and x <= 7:
                        subprocess.Popen(
                            ["swayosd-client", "--output-volume", "mute-toggle"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        _slow_state["counter"] = SLOW_POLL_INTERVAL
                    elif fallback:
                        with contextlib.suppress(OSError):
                            subprocess.Popen(
                                fallback,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                elif action:
                    with contextlib.suppress(OSError):
                        subprocess.Popen(
                            action,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    _slow_state["counter"] = SLOW_POLL_INTERVAL
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        disable_mouse(stdin=stdin, stdout=stdout)


if __name__ == "__main__":
    run(sys.stdin.buffer, sys.stdout, WIDTH, HEIGHT)
