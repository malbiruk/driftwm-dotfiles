#!/bin/bash
# Battery notification daemon — thresholds on minutes-remaining, read via upower over D-Bus.
# upower smooths the energy-rate, so the time estimate is stable even when workload spikes.

LOW_MINUTES=30
CRITICAL_MINUTES=10
LOW_COOLDOWN=600
CRITICAL_COOLDOWN=180
POLL_INTERVAL=120
STATE_DIR="/tmp/driftwm-battery-notify"
BATTERY="/org/freedesktop/UPower/devices/battery_macsmc_battery"

# upower Device.State enum: 1=charging 2=discharging 3=empty 4=full 5=pending-charge 6=pending-discharge
STATE_DISCHARGING=2

mkdir -p "$STATE_DIR"

check_cooldown() {
    local key="$1"
    local cooldown="$2"
    local now=$(date +%s)
    local state_file="$STATE_DIR/$key"
    if [ -f "$state_file" ]; then
        local last=$(cat "$state_file")
        [ $((now - last)) -lt $cooldown ] && return 1
    fi
    echo "$now" > "$state_file"
    return 0
}

# busctl returns "<type> <value>"; strip the type prefix.
prop() {
    busctl get-property org.freedesktop.UPower "$BATTERY" \
        org.freedesktop.UPower.Device "$1" 2>/dev/null | awk '{print $2}'
}

trap 'rm -rf "$STATE_DIR"; exit 0' EXIT INT TERM

while true; do
    state=$(prop State)
    if [ "$state" = "$STATE_DISCHARGING" ]; then
        secs=$(prop TimeToEmpty)
        pct=$(prop Percentage)
        # TimeToEmpty=0 means upower hasn't computed yet (just unplugged); skip.
        if [ -n "$secs" ] && [ "$secs" -gt 0 ]; then
            mins=$((secs / 60))
            pct_int=${pct%.*}
            if [ "$mins" -le "$CRITICAL_MINUTES" ]; then
                check_cooldown critical "$CRITICAL_COOLDOWN" && \
                    notify-send -u critical \
                        --app-name="Battery" \
                        --icon=battery-empty-symbolic \
                        -h "int:value:${pct_int}" \
                        "Critical battery" \
                        "~${mins} min left — plug in now"
            elif [ "$mins" -le "$LOW_MINUTES" ]; then
                check_cooldown low "$LOW_COOLDOWN" && \
                    notify-send -u normal \
                        --app-name="Battery" \
                        --icon=battery-caution-symbolic \
                        -h "int:value:${pct_int}" \
                        "Low battery" \
                        "~${mins} min left — consider charging"
            fi
        fi
    fi
    sleep "$POLL_INTERVAL"
done
