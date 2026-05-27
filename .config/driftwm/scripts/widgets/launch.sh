#!/bin/bash
# Launch all driftwm dashboard widgets as foot terminals.
# Each gets its own app_id for window rule matching.

DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"

# Pre-sync once so parallel widget launches don't race on .venv/.lock.
# Then call the venv's python directly — `uv run` keeps a supervisor process
# alive per widget (~26 MB each = ~200 MB wasted across 8 widgets).
uv sync -q --project "$DIR" >/dev/null 2>&1
PY="$DIR/.venv/bin/python"

launch() {
    local name="$1" cols="$2" lines="$3" script="$4"
    footclient --app-id="drift-${name}" \
        --window-size-chars="${cols}x${lines}" \
        -- "$PY" "$DIR/${script}" &
}

launch clock       34 6  clock_widget.py
launch stats       34 11 stats_widget.py
launch canvas      26 4  canvas_widget.py
launch layout      7 4  layout_widget.py
launch calendar    22 11  calendar_widget.py
launch weather     22 6  weather_widget.py
launch notif       22 4  notif_widget.py

# Power button — custom padding to match tray waybar height (28px)
footclient --app-id="drift-power" \
    --window-size-chars="3x1" \
    -o pad=5x3 \
    -- "$PY" "$DIR/power_widget.py" &

wait
