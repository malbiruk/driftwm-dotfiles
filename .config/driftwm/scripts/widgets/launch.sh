#!/bin/bash
# Launch all driftwm dashboard widgets — one Python daemon serves all 8 via UNIX
# sockets, footclient on each window connects through socat.

DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Single-instance guard: hold a session-long lock so a second invocation (config
# reload, re-run autostart) exits instead of spawning a rival daemon. Two daemons
# both unlink+rebind the 8 socket paths, splitting widgets across them and leaving
# orphaned/duplicate windows. fd 9 stays open (inherited by the background loops
# below) until the session ends, so the lock is held for as long as widgets run.
exec 9>"${RUNTIME}/drift-widgets.lock"
flock -n 9 || exit 0

# Pre-sync once so the daemon's first import doesn't race on .venv/.lock.
uv sync -q --project "$DIR" >/dev/null 2>&1
PY="$DIR/.venv/bin/python"

# Daemon-backed widget: footclient connects to the daemon's UNIX socket via socat.
# We disable ICANON + ECHO so mouse-event bytes pass through unbuffered, but keep
# OPOST on so the PTY still translates Rich's `\n` to CR+LF (otherwise output
# stair-steps down the screen). The while-loop respawns the window if it ever
# exits: a widget that hits an error closes its socket, and without this the
# footclient would vanish for the rest of the session with no restart.
launch() {
    local name="$1" cols="$2" lines="$3" extra="$4"
    (
        while true; do
            # shellcheck disable=SC2086
            footclient --app-id="drift-${name}" \
                --window-size-chars="${cols}x${lines}" \
                ${extra} \
                -- socat -,icanon=0,echo=0 "UNIX-CONNECT:${RUNTIME}/drift-${name}.sock"
            sleep 1
        done
    ) &
}

# Start daemon — it serves all 8 widget sockets. Respawned if it ever dies,
# otherwise every widget would go dark at once.
(
    while true; do
        "$PY" "$DIR/daemon.py"
        sleep 1
    done
) &

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
