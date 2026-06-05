"""Shared helpers for driftwm dashboard widgets."""

import contextlib
import json
import locale as _locale
import os
import re
import select
import subprocess
import sys
import termios
import urllib.request
from collections import deque
from pathlib import Path
from typing import NamedTuple

# ── Locale ──────────────────────────────────────────────────
# Activate the user's locale so strftime / calendar.month_name / day_abbr
# render in the configured language. Safe if the locale isn't installed.
with contextlib.suppress(_locale.Error):
    _locale.setlocale(_locale.LC_ALL, "")


def _detect_lang() -> str:
    """Return 2-letter language code from LC_MESSAGES, defaulting to 'en'."""
    try:
        loc = _locale.getlocale(_locale.LC_MESSAGES)[0]
    except (ValueError, TypeError):
        loc = None
    if not loc:
        for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
            val = os.environ.get(var, "")
            if val and val not in ("C", "POSIX"):
                loc = val
                break
    return (loc or "en")[:2].lower()


LANG = _detect_lang()

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        # generic widget strings
        "offline": "offline",
        "muted": "stumm",
        "notifications": "meldungen",
        "unread": "ungelesen",
        "all clear": "alles ruhig",
        "tmrw": "morgen",
        # stats widget 3-letter labels
        "cpu": "cpu",
        "ram": "ram",
        "bat": "akk",
        "vol": "vol",
        "bri": "hel",
        # canvas widget
        "zoom": "zoom",
        # weather widget single-letter labels (Hoch / Tief)
        "H": "H",
        "L": "T",
        # WMO weather descriptions (must match _WMO_DESC values)
        "Clear": "Klar",
        "Partly cloudy": "Wolkig",
        "Overcast": "Bedeckt",
        "Fog": "Nebel",
        "Drizzle": "Niesel",
        "Rain": "Regen",
        "Snow": "Schnee",
        "Thunderstorm": "Gewitter",
        # power menu
        "Lock": "Sperren",
        "Suspend": "Standby",
        "Log out": "Abmelden",
        "Reboot": "Neustart",
        "Power off": "Ausschalten",
    },
}


def t(s: str) -> str:
    """Translate a string into the active language; fall back to the input."""
    return _TRANSLATIONS.get(LANG, {}).get(s, s)

# ── Block digits (3x2 each) ──────────────────────────────────

DIGITS = {
    "0": ["█▀█", "█▄█"],
    "1": [" ▀█", " ▄█"],
    "2": ["▀▀█", "█▄▄"],
    "3": ["▀▀█", "▄▄█"],
    "4": ["█ █", "▀▀█"],
    "5": ["█▀▀", "▄▄█"],
    "6": ["█▀▀", "█▄█"],
    "7": ["▀▀█", "  █"],
    "8": ["█▀█", "█▀█"],
    "9": ["█▀█", "▄▄█"],
}


def render_big_time(time_str: str, *, colon_on: bool = True) -> tuple[str, str]:
    """Render HH:MM as two rows of block characters."""
    rows: list[list[str]] = [[], []]
    for ch in time_str:
        if ch == ":":
            rows[0].append(" · " if colon_on else "   ")
            rows[1].append(" · " if colon_on else "   ")
        elif ch in DIGITS:
            for i in range(2):
                rows[i].append(DIGITS[ch][i])
    return " ".join(rows[0]), " ".join(rows[1])


# ── Sparkline ────────────────────────────────────────────────

SPARK = " ▁▂▃▄▅▆▇█"


def sparkline(values: deque | list, width: int = 10) -> str:
    """Render a sparkline from recent values (0-100 absolute scale)."""
    recent = list(values)[-width:]
    if not recent:
        return " " * width
    return "".join(
        SPARK[max(min(int(v / 100 * 8), 8), 1 if v > 0.5 else 0)] for v in recent
    )


def progress_bar(pct: float, width: int = 10) -> str:
    """Render a thin horizontal progress bar."""
    pct = max(0.0, min(100.0, pct))
    filled = round(pct / 100 * width)
    return "━" * filled + " " * (width - filled)


# ── Nerd Font icons ─────────────────────────────────────────

ICON = {
    "cpu": "\uf4bc",
    "ram": "\uefc5",
    "bat_charging": "󰂄",
    "bat_full": "󰁹",
    "bat_high": "󰂂",
    "bat_med": "󰂀",
    "bat_low": "󰁾",
    "bat_empty": "󰁺",
    "vol_high": "󰕾",
    "vol_med": "󰖀",
    "vol_low": "󰕿",
    "vol_mute": "󰖁",
    "wifi_4": "󰤨",
    "wifi_3": "󰤥",
    "wifi_2": "󰤢",
    "wifi_1": "󰤟",
    "wifi_off": "󰤮",
    "wifi_none": "󰤭",
    "kbd": "󰌌",
    "pos": "\uf124",
    "zoom": "\uf00e",
    "bell": "\uf0f3",
    "calendar": "\uf073",
    "weather": "\uf0c2",
    "bright_high": "󰃠",
    "bright_med": "󰃟",
    "bright_low": "󰃞",
    "bright_dim": "󰃝",
    "bt_on": "󰂯",
    "bt_off": "󰂲",
    "bt_connected": "󰂱",
    "caffeine": "\uec15",  # nf-md-coffee-steam
}

# ── Weather icons (Unicode, no Nerd Font needed) ────────────

WEATHER_ICON = {
    "clear": chr(0xF0599),  # 󰖙
    "sunny": chr(0xF0599),  # 󰖙
    "partly": chr(0xF0595),  # 󰖕
    "cloudy": chr(0xF0590),  # 󰖐
    "overcast": chr(0xF0590),  # 󰖐
    "rain": chr(0xF0597),  # 󰖗
    "drizzle": chr(0xF0597),  # 󰖗
    "thunder": chr(0xF0593),  # 󰖓
    "snow": chr(0xF0598),  # 󰖘
    "mist": chr(0xF0591),  # 󰖑
    "fog": chr(0xF0591),  # 󰖑
}


def weather_icon(desc: str) -> str:
    desc_lower = desc.lower()
    for key, icon in WEATHER_ICON.items():
        if key in desc_lower:
            return icon
    return chr(0xF0595)  # 󰖕 partly cloudy as default


# ── Data readers ─────────────────────────────────────────────


class CpuTracker:
    """Tracks CPU usage between calls via /proc/stat deltas."""

    def __init__(self) -> None:
        self.prev: tuple[int, int] | None = None

    def read(self) -> float:
        parts = Path("/proc/stat").read_text().split("\n")[0].split()
        idle = int(parts[4]) + int(parts[5])
        total = sum(int(x) for x in parts[1:])
        if self.prev is None:
            self.prev = (idle, total)
            return 0.0
        prev_idle, prev_total = self.prev
        self.prev = (idle, total)
        d_total = total - prev_total
        if d_total == 0:
            return 0.0
        return 100.0 * (1.0 - (idle - prev_idle) / d_total)


cpu_tracker = CpuTracker()


def get_cpu_percent() -> float:
    """CPU usage since last call (delta from /proc/stat)."""
    return cpu_tracker.read()


class MemInfo(NamedTuple):
    ram_used: float  # GB physical RAM in use (MemTotal - MemAvailable)
    ram_total: float  # GB
    pressure: float  # 0-100, distance to OOM, crediting zram compression


def _zram_stats() -> tuple[float, float]:
    """Sum (uncompressed, physical) GB across all zram devices; (0, 0) if none."""
    orig = phys = 0
    for stat in Path("/sys/block").glob("zram*/mm_stat"):
        with contextlib.suppress(OSError, ValueError, IndexError):
            fields = stat.read_text().split()
            orig += int(fields[0])  # orig_data_size
            phys += int(fields[2])  # mem_used_total (compressed + metadata)
    return orig / 1073741824, phys / 1073741824


def get_memory() -> MemInfo:
    """Memory stats plus an OOM-distance score that credits zram compression.

    On a zram-only machine "RAM used %" is alarmingly high while the system is
    still fast, because cold anon pages get compressed into zram (here ~5x) the
    moment RAM tightens. So `pressure` is based on *effective* available memory:
    you can hold ~MemAvailable*ratio more anon data by compressing it, capped by
    the free space left in the zram device. 0 = empty, 100 = effectively OOM.
    """
    info = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        parts = line.split()
        info[parts[0].rstrip(":")] = int(parts[1])  # kB
    total = info["MemTotal"] / 1048576
    avail = info["MemAvailable"] / 1048576
    swap_free = info.get("SwapFree", 0) / 1048576

    orig, phys = _zram_stats()
    ratio = orig / phys if phys > 0.001 else 3.0  # zstd default while idle

    eff_avail = min(avail * ratio, avail + swap_free)
    pressure = max(0.0, min(100.0, (1 - eff_avail / total) * 100)) if total else 0.0
    return MemInfo(total - avail, total, pressure)


def get_battery() -> tuple[int, str, float | None] | None:
    """Returns (percent, status, hours_remaining) or None. Uses sysfs (no subprocess).

    Iterates all power supplies and filters by type=Battery, so this works on
    x86 (BAT0/BAT1) and Apple Silicon under Asahi/ALARM (macsmc-battery) alike.
    Time remaining is computed from energy/power (µWh/µW) or charge/current
    (µAh/µA), whichever the driver exposes.
    """
    for ps in sorted(Path("/sys/class/power_supply").glob("*")):
        try:
            if (ps / "type").read_text().strip() != "Battery":
                continue
            pct = int((ps / "capacity").read_text().strip())
            status = (ps / "status").read_text().strip().lower()
        except (OSError, ValueError):
            continue
        return pct, status, _battery_hours(ps, status)
    return None


def get_battery_time_upower() -> float | None:
    """Smoothed time-to-empty/full (hours) from UPower's DisplayDevice.

    UPower maintains its own moving average of recent energy-rate readings,
    so this avoids the noise of dividing energy_now by an instantaneous
    power_now. Returns None if upower is unavailable or the value is unknown.
    """
    try:
        result = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not (
            stripped.startswith("time to empty") or stripped.startswith("time to full")
        ):
            continue
        parts = stripped.split(":", 1)[1].strip().split()
        if len(parts) < 2:
            continue
        try:
            value = float(parts[0])
        except ValueError:
            continue
        unit = parts[1].lower()
        if unit.startswith("hour"):
            return value
        if unit.startswith("minute"):
            return value / 60
        if unit.startswith("second"):
            return value / 3600
    return None


def _battery_hours(ps: Path, status: str) -> float | None:
    """Compute remaining battery hours from sysfs counters, or None."""
    if status == "full":
        return None
    # Try energy/power (µWh / µW) first, then charge/current (µAh / µA).
    for now_file, rate_file, full_file in (
        ("energy_now", "power_now", "energy_full"),
        ("charge_now", "current_now", "charge_full"),
    ):
        try:
            now = int((ps / now_file).read_text().strip())
            rate = abs(int((ps / rate_file).read_text().strip()))
            if status == "charging":
                full = int((ps / full_file).read_text().strip())
                remaining = full - now
            else:
                remaining = now
        except (OSError, ValueError):
            continue
        if rate == 0:
            continue
        hours = remaining / rate
        # Cap absurd values: when charging is throttled near a user-set cap
        # (e.g. 80%) or the laptop is deeply idle, `current_now` drops to a
        # trickle and the estimate blows up. No real laptop battery legitimately
        # reads > 48h either direction.
        return hours if 0 < hours <= 48 else None
    return None


def battery_icon(pct: int, status: str) -> str:
    if status == "charging":
        return ICON["bat_charging"]
    if pct > 75:
        return ICON["bat_high"]
    if pct > 50:
        return ICON["bat_med"]
    if pct > 25:
        return ICON["bat_low"]
    return ICON["bat_empty"]


def _volume_from_pactl() -> tuple[int, bool] | None:
    """Fallback volume reader via pactl, for when wpctl has no default sink."""
    try:
        vol_out = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        ).stdout
        mute_out = subprocess.run(
            ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"(\d+)%", vol_out)
    if match is None:
        return None
    return int(match.group(1)), "yes" in mute_out.lower()


def get_volume() -> tuple[int, bool]:
    """Returns (percent, is_muted).

    Prefers wpctl's default sink. When WirePlumber has no default node set,
    @DEFAULT_AUDIO_SINK@ resolves to -1 and wpctl prints nothing (still exit 0),
    so fall back to pactl rather than silently reporting a misleading 0%.
    """
    try:
        result = subprocess.run(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        parts = result.stdout.strip().split()
        vol = int(float(parts[1]) * 100)
        muted = "[MUTED]" in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError, ValueError):
        fallback = _volume_from_pactl()
        return fallback if fallback is not None else (0, False)
    else:
        return vol, muted


def volume_icon(pct: int, *, muted: bool) -> str:
    if muted or pct == 0:
        return ICON["vol_mute"]
    if pct > 66:
        return ICON["vol_high"]
    if pct > 33:
        return ICON["vol_med"]
    return ICON["vol_low"]


def get_wifi() -> tuple[str, int] | None:
    """Returns (ssid, signal_percent) or None."""
    try:
        result = subprocess.run(
            [
                "nmcli",
                "-t",
                "-f",
                "ACTIVE,SSID,SIGNAL",
                "dev",
                "wifi",
                "list",
                "--rescan",
                "no",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
        for line in result.stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[0] == "yes":
                return parts[1], int(parts[2])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def wifi_icon(signal: int) -> str:
    if signal >= 75:
        return ICON["wifi_4"]
    if signal >= 50:
        return ICON["wifi_3"]
    if signal >= 25:
        return ICON["wifi_2"]
    return ICON["wifi_1"]


def get_notifications() -> int:
    """Get unread notification count from swaync."""
    try:
        result = subprocess.run(
            ["swaync-client", "-c"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return int(result.stdout.strip())
    except Exception:
        return 0


_WMO_DESC = {
    0: "Clear",
    1: "Partly cloudy",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    61: "Rain",
    63: "Rain",
    65: "Rain",
    71: "Snow",
    73: "Snow",
    75: "Snow",
    77: "Snow",
    80: "Rain",
    81: "Rain",
    82: "Rain",
    85: "Snow",
    86: "Snow",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}

_cached_location: tuple[str, float, float] | None = None


def _geolocate() -> tuple[str, float, float]:
    """IP geolocation via ip-api.com. Cached for the session."""
    global _cached_location  # noqa: PLW0603
    if _cached_location is not None:
        return _cached_location
    with urllib.request.urlopen(
        "http://ip-api.com/json/?fields=city,lat,lon",
        timeout=5,
    ) as resp:
        geo = json.loads(resp.read())
    _cached_location = (geo["city"], geo["lat"], geo["lon"])
    return _cached_location


def get_weather() -> dict | None:
    """Fetch weather from Open-Meteo. Returns dict or None on failure."""
    try:
        city, lat, lon = _geolocate()
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code,relative_humidity_2m,apparent_temperature"
            "&daily=temperature_2m_max,temperature_2m_min,weather_code"
            "&timezone=auto&forecast_days=2"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read())
        cur = data["current"]
        daily = data["daily"]
        code = cur["weather_code"]
        tomorrow_code = (
            daily["weather_code"][1] if len(daily["weather_code"]) > 1 else None
        )
        return {
            "location": city,
            "temp": str(round(cur["temperature_2m"])),
            "feels": str(round(cur["apparent_temperature"])),
            "desc": _WMO_DESC.get(code, "Cloudy"),
            "humidity": str(cur["relative_humidity_2m"]),
            "high": str(round(daily["temperature_2m_max"][0])),
            "low": str(round(daily["temperature_2m_min"][0])),
            "tomorrow_temp": str(
                round(
                    (daily["temperature_2m_max"][1] + daily["temperature_2m_min"][1])
                    / 2,
                ),
            )
            if len(daily["temperature_2m_max"]) > 1
            else "?",
            "tomorrow_desc": _WMO_DESC.get(tomorrow_code, "?")
            if tomorrow_code is not None
            else "?",
        }
    except Exception:
        return None


def read_state_file() -> dict[str, str]:
    """Read driftwm state from $XDG_RUNTIME_DIR/driftwm/state."""
    runtime_dir = Path(environ_get("XDG_RUNTIME_DIR", ""))
    path = runtime_dir / "driftwm" / "state"
    result = {}
    try:
        for line in path.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
    except (FileNotFoundError, PermissionError):
        pass
    return result


def environ_get(key: str, default: str) -> str:
    """Wrapper around os.environ.get for testability."""

    return os.environ.get(key, default)


def get_tuned_profile() -> str:
    """Returns the active tuned profile name, e.g. 'balanced'."""
    try:
        result = subprocess.run(
            ["tuned-adm", "active"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        # Output: "Current active profile: balanced"
        for line in result.stdout.splitlines():
            if ":" in line:
                return line.split(":", 1)[1].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


TUNED_PROFILES = ["powersave", "balanced", "latency-performance"]

TUNED_ICON = {
    "powersave": "\U000f032a",  # 󰌪 nf-md-leaf
    "balanced": "",  # no icon for default mode
    "latency-performance": "\U000f04c5",  # 󰓅 nf-md-speedometer
}


def cycle_tuned_profile() -> None:
    """Cycle to the next tuned profile in TUNED_PROFILES."""
    current = get_tuned_profile()
    try:
        idx = TUNED_PROFILES.index(current)
        next_profile = TUNED_PROFILES[(idx + 1) % len(TUNED_PROFILES)]
    except ValueError:
        next_profile = TUNED_PROFILES[0]
    subprocess.Popen(
        ["tuned-adm", "profile", next_profile],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get_brightness() -> int | None:
    """Returns screen brightness percent or None. Uses sysfs (no subprocess)."""
    for device in sorted(Path("/sys/class/backlight").glob("*")):
        try:
            current = int((device / "brightness").read_text().strip())
            maximum = int((device / "max_brightness").read_text().strip())
            if maximum > 0:
                return current * 100 // maximum
        except (OSError, ValueError):
            continue
    return None


def brightness_icon(pct: int) -> str:
    if pct > 66:
        return ICON["bright_high"]
    if pct > 33:
        return ICON["bright_med"]
    return ICON["bright_low"]


def _bt_battery(mac: str) -> int | None:
    """Query battery percentage for a BT device via bluetoothctl info."""
    try:
        result = subprocess.run(
            ["bluetoothctl", "info", mac],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        for line in result.stdout.splitlines():
            if "Battery Percentage" in line:
                # Format: "	Battery Percentage: 0x42 (66)"
                return int(line.rsplit("(", 1)[1].rstrip(")"))
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError, ValueError):
        pass
    return None


def get_bluetooth() -> str | None:
    """Returns formatted bluetooth status string with icon, or None."""
    try:
        result = subprocess.run(
            ["bluetoothctl", "show"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        powered = any("Powered: yes" in line for line in result.stdout.splitlines())
        if not powered:
            return f"{ICON['bt_off']}  off"

        connected = subprocess.run(
            ["bluetoothctl", "devices", "Connected"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        devices = [
            line.split(" ", 2)[2]
            for line in connected.stdout.strip().splitlines()
            if line.startswith("Device ")
        ]
        if not devices:
            return f"{ICON['bt_on']}  on"
        if len(devices) == 1:
            mac = connected.stdout.strip().splitlines()[0].split(" ", 2)[1]
            bat = _bt_battery(mac)
            name = devices[0][:16]
            if bat is not None:
                return f"{ICON['bt_connected']}  {name} ({bat}%)"
            return f"{ICON['bt_connected']}  {name}"
        return f"{ICON['bt_connected']}  {len(devices)} devices"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


# ── Synchronized output (tear-free Live redraws) ────────────


def synchronize_live(live) -> None:  # type: ignore[no-untyped-def]
    """Wrap Rich Live.refresh() with DEC 2026 BSU/ESU so each frame paints atomically.

    Without this, Rich's "move cursor up → erase → rewrite" sequence is visible
    as a brief see-through flash during updates. Supported by alacritty, kitty,
    foot, wezterm, recent VTE; unsupported terminals ignore the sequences.
    """
    original_refresh = live.refresh
    file = live.console.file

    def refresh() -> None:
        file.write("\033[?2026h")
        try:
            original_refresh()
        finally:
            file.write("\033[?2026l")
            file.flush()

    live.refresh = refresh


# ── Mouse click handling ────────────────────────────────────
# Per-fd termios state — keyed by stdin fd so the daemon (multi-threaded,
# one widget per thread, each with its own socket fd) doesn't trample state.

_orig_termios: dict[int, list] = {}


def enable_mouse(stdin=None, stdout=None) -> None:  # type: ignore[no-untyped-def]
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    fd = stdin.fileno()
    # Sockets aren't ttys — socat sets PTY raw mode on the foot side, so skip termios.
    if os.isatty(fd):
        _orig_termios[fd] = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~(termios.ICANON | termios.ECHO)
        termios.tcsetattr(fd, termios.TCSANOW, new)
    stdout.write("\033[?1000h")
    stdout.flush()


def disable_mouse(stdin=None, stdout=None) -> None:  # type: ignore[no-untyped-def]
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    with contextlib.suppress(Exception):
        stdout.write("\033[?1000l")
        stdout.flush()
    with contextlib.suppress(Exception):
        fd = stdin.fileno()
        if fd in _orig_termios:
            termios.tcsetattr(fd, termios.TCSANOW, _orig_termios.pop(fd))


def poll_click(timeout: float, stdin=None) -> tuple[int, int] | None:  # type: ignore[no-untyped-def]
    """Wait up to timeout seconds for a mouse press. Returns (x, y) 1-based or None."""
    stdin = stdin if stdin is not None else sys.stdin
    fd = stdin.fileno()
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return None
    data = os.read(fd, 64)
    if not data:
        # EOF — terminal disconnected. Signal caller via OSError so the run loop exits.
        raise BrokenPipeError("stdin EOF")
    idx = data.find(b"\033[M")
    if idx < 0 or idx + 5 >= len(data):
        return None
    btn = data[idx + 3] - 32
    if btn & 3 == 3:  # release, not press
        return None
    x = data[idx + 4] - 32
    y = data[idx + 5] - 32
    return x, y


def read_keyboard_layout() -> str:
    """Read keyboard layout from driftwm config."""
    config_dir = Path(environ_get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    config_path = config_dir / "driftwm" / "config.toml"
    try:
        for line in config_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("layout"):
                val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                return val.upper()
    except (FileNotFoundError, PermissionError):
        pass
    return "US"
