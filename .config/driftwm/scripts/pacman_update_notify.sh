#!/bin/bash
# Pacman update notifier — checks for available updates via checkupdates(8) and
# fires a notification whose urgency scales with the count. Driven by a systemd
# user timer; runs as a oneshot, exits silently when there's nothing to report.

THRESHOLD_NORMAL=30    # >= this many updates: normal urgency
THRESHOLD_CRITICAL=150 # >= this many updates: critical urgency
MAX_LIST=8            # how many package names to preview in the body

# checkupdates syncs to a private db under /tmp, so it never needs root and
# never leaves the real pacman db in a partial-sync state (which would break
# the next install).
if ! command -v checkupdates >/dev/null; then
    notify-send -u low --app-name="Updates" \
        --icon=software-update-available-symbolic \
        "Update notifier" "checkupdates missing — install pacman-contrib"
    exit 0
fi

updates=$(checkupdates 2>/dev/null)
[ -z "$updates" ] && exit 0

count=$(printf '%s\n' "$updates" | wc -l)

if [ "$count" -ge "$THRESHOLD_CRITICAL" ]; then
    urgency=critical
    icon=software-update-urgent-symbolic
elif [ "$count" -ge "$THRESHOLD_NORMAL" ]; then
    urgency=normal
    icon=software-update-available-symbolic
else
    urgency=low
    icon=software-update-available-symbolic
fi

preview=$(printf '%s\n' "$updates" | head -n "$MAX_LIST" | awk '{print $1}' | paste -sd, -)
if [ "$count" -gt "$MAX_LIST" ]; then
    preview="$preview, +$((count - MAX_LIST)) more"
fi

notify-send -u "$urgency" \
    --app-name="Updates" \
    --icon="$icon" \
    "Pacman: $count updates available" \
    "$preview"
