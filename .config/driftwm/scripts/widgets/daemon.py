#!/usr/bin/env python3
"""Driftwm widget daemon — one process serves all widgets via per-widget UNIX sockets.

footclient on the foot side runs `socat - UNIX-CONNECT:/run/user/$UID/drift-<name>.sock`,
which sets the PTY to raw mode and pipes it to our socket. We spawn a thread per
connection that wraps the socket as text-mode stdout + raw-bytes stdin and runs the
widget's `run(stdin, stdout, width, height)` entry point.
"""

import importlib
import io
import os
import socket
import sys
import threading
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))

RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

# (sock-name, module, console_width, terminal_lines). console_width can exceed
# the foot --window-size-chars value (Rich wraps); height drives top-padding math.
WIDGETS: list[tuple[str, str, int, int]] = [
    ("clock", "clock_widget", 36, 6),
    ("stats", "stats_widget", 36, 11),
    ("canvas", "canvas_widget", 25, 4),
    ("layout", "layout_widget", 7, 4),
    ("calendar", "calendar_widget", 22, 11),
    ("weather", "weather_widget", 22, 6),
    ("notif", "notif_widget", 20, 4),
    ("power", "power_widget", 4, 1),
]


def _handle_connection(conn: socket.socket, module, width: int, height: int) -> None:  # type: ignore[no-untyped-def]
    fd = conn.fileno()
    stdin = os.fdopen(os.dup(fd), "rb", buffering=0)
    stdout = io.TextIOWrapper(
        os.fdopen(os.dup(fd), "wb", buffering=0),
        encoding="utf-8",
        write_through=True,
    )
    try:
        module.run(stdin, stdout, width, height)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    except Exception:
        import traceback

        traceback.print_exc(file=sys.stderr)
    finally:
        for s in (stdin, stdout):
            try:
                s.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass


def _serve(name: str, module_name: str, width: int, height: int) -> None:
    module = importlib.import_module(module_name)
    sock_path = RUNTIME / f"drift-{name}.sock"
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(4)
    while True:
        conn, _ = server.accept()
        threading.Thread(
            target=_handle_connection,
            args=(conn, module, width, height),
            daemon=True,
        ).start()


def main() -> None:
    for name, module_name, width, height in WIDGETS:
        threading.Thread(
            target=_serve,
            args=(name, module_name, width, height),
            daemon=True,
        ).start()
    threading.Event().wait()


if __name__ == "__main__":
    main()
