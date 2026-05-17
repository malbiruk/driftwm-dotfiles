#!/usr/bin/env python3
"""Power menu TUI for driftwm. Navigate with arrows/jk/mouse, Enter/click to select, q/Esc to close."""

import os
import select
import signal
import subprocess
import sys
import termios
import tty

ITEMS = [
    ("\U000f033e", "Lock", "lock"),  # 󰌾
    ("\U000f04b2", "Suspend", "suspend"),  # 󰒲
    ("\U000f0343", "Log out", "logout"),  # 󰍃
    ("\U000f0709", "Reboot", "reboot"),  # 󰜉
    ("\U000f0425", "Power off", "poweroff"),  # 󰐥
]

RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
REVERSE = "\033[7m"
RESET = "\033[0m"

top_pad = 0


def draw(selected: int) -> None:
    global top_pad  # noqa: PLW0603
    sys.stdout.write("\033[H\033[2J\033[?25l")
    try:
        term_h = os.get_terminal_size().lines
    except OSError:
        term_h = 9
    top_pad = max((term_h - len(ITEMS)) // 2, 0)
    sys.stdout.write("\n" * top_pad)

    for i, (icon, label, _) in enumerate(ITEMS):
        if i == selected:
            sys.stdout.write(f"  {BOLD}{RED}{REVERSE} {icon}  {label:<10}{RESET}\n")
        else:
            sys.stdout.write(f"   {DIM}{icon}  {label}{RESET}\n")

    sys.stdout.flush()


def item_from_y(y: int) -> int | None:
    """Convert 1-based terminal row to item index, or None if outside."""
    idx = y - 1 - top_pad
    if 0 <= idx < len(ITEMS):
        return idx
    return None


def _parse_mouse(data: bytes) -> tuple[str, int | None]:
    idx = data.find(b"\033[M")
    if idx < 0 or idx + 5 >= len(data):
        return ("none", None)
    btn = data[idx + 3] - 32
    y = data[idx + 5] - 32
    item = item_from_y(y)
    if btn & 0x20:  # motion (bit 5 set)
        return ("hover", item)
    if btn & 3 != 3:  # press (not release)
        return ("click", item)
    return ("none", None)


_KEY_MAP = {
    b"\x1b[A": "up",
    b"k": "up",
    b"\x1b[B": "down",
    b"j": "down",
    b"\r": "enter",
    b"\n": "enter",
    b"q": "quit",
    b"\x1b": "quit",
}


def read_input() -> tuple[str, int | None]:
    """Read keyboard or mouse input. Returns (event_type, item_index_or_None)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ready, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not ready:
            return ("none", None)
        data = os.read(fd, 64)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

    if b"\033[M" in data:
        return _parse_mouse(data)
    return (_KEY_MAP.get(data, "none"), None)


_DEVNULL = subprocess.DEVNULL
# Delay lets the terminal close first so swaylock gets clean keyboard focus
_LOCK_CMD = "sleep 0.3 && swaylock -f -c 000000 -k -l"


def _spawn_shell(cmd: str) -> None:
    """Spawn a shell command fully detached from the terminal."""
    subprocess.Popen(
        ["bash", "-c", cmd],
        stdin=_DEVNULL,
        stdout=_DEVNULL,
        stderr=_DEVNULL,
        start_new_session=True,
    )


def execute(action: str) -> None:
    cleanup()
    if action == "lock":
        _spawn_shell(_LOCK_CMD)
    elif action == "suspend":
        subprocess.run(["systemctl", "suspend"], check=False)
    elif action == "logout":
        subprocess.run(["pkill", "-x", "driftwm"], check=False)
    elif action == "reboot":
        subprocess.run(["systemctl", "reboot"], check=False)
    elif action == "poweroff":
        subprocess.run(["systemctl", "poweroff"], check=False)


_orig_termios: list | None = None


def setup() -> None:
    global _orig_termios  # noqa: PLW0603
    fd = sys.stdin.fileno()
    _orig_termios = termios.tcgetattr(fd)
    # Enable any-event mouse tracking (clicks + hover)
    sys.stdout.write("\033[?1003h")
    sys.stdout.flush()


def cleanup() -> None:
    sys.stdout.write("\033[?1003l\033[?25h\033[H\033[2J")
    sys.stdout.flush()
    if _orig_termios is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, _orig_termios)


def main() -> None:
    setup()
    selected = 0
    draw(selected)
    try:
        while True:
            event, item = read_input()
            if event == "hover" and item is not None and item != selected:
                selected = item
                draw(selected)
            elif event == "click" and item is not None:
                _, _, action = ITEMS[item]
                execute(action)
                return
            elif event == "up":
                selected = (selected - 1) % len(ITEMS)
                draw(selected)
            elif event == "down":
                selected = (selected + 1) % len(ITEMS)
                draw(selected)
            elif event == "enter":
                _, _, action = ITEMS[selected]
                execute(action)
                return
            elif event == "quit":
                cleanup()
                return
    except Exception:
        cleanup()
        raise


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: (cleanup(), sys.exit(0)))
    main()
