#!/bin/bash
# Launch all driftwm dashboard widgets — one Python daemon serves all 8 via UNIX
# sockets, footclient on each window connects through socat.

DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Pre-sync once so the daemon's first import doesn't race on .venv/.lock.
uv sync -q --project "$DIR" >/dev/null 2>&1
PY="$DIR/.venv/bin/python"

# Daemon-backed widget: footclient connects to the daemon's UNIX socket via socat.
# We disable ICANON + ECHO so mouse-event bytes pass through unbuffered, but keep
# OPOST on so the PTY still translates Rich's `\n` to CR+LF (otherwise output
# stair-steps down the screen).
launch() {
    local name="$1" cols="$2" lines="$3" extra="$4"
    # shellcheck disable=SC2086
    footclient --app-id="drift-${name}" \
        --window-size-chars="${cols}x${lines}" \
        ${extra} \
        -- socat -,icanon=0,echo=0 "UNIX-CONNECT:${RUNTIME}/drift-${name}.sock" &
}

# Start daemon — it serves all 8 widget sockets.
"$PY" "$DIR/daemon.py" &

# Wait for every socket to appear (avoids socat-connect race).
for name in clock stats canvas layout calendar weather notif power; do
    for _ in $(seq 1 50); do
        [ -S "${RUNTIME}/drift-${name}.sock" ] && break
        sleep 0.05
    done
done

launch clock     34 6
launch stats     34 11
launch canvas    26 4
launch layout    7  4
launch calendar  22 11
launch weather   22 6
launch notif     22 4

# Power button — custom padding to match tray waybar height (28px).
launch power     3  1  "-o pad=5x3"

wait
