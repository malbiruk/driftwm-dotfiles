#!/bin/bash
# Battery notification daemon — thresholds on charge percentage, read via upower over D-Bus.
# Percentage is steadier than upower's time estimate, which is unreliable on Asahi (made-up
# Wh values) and wrong right after unplug. This machine tends to power off near 10%, so
# warnings start at 15% and the ETA counts down to 10% rather than to 0%.

LOW_PERCENT=15
CRITICAL_PERCENT=12
TARGET_PERCENT=10   # effective shutdown point on this machine; ETA counts down to here
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
        pct_int=${pct%.*}
        if [ -n "$pct_int" ]; then
            # ETA to TARGET_PERCENT, assuming linear discharge. TimeToEmpty extrapolates
            # to 0%, so scale it down to the target. Skipped when upower hasn't computed
            # a rate yet (TimeToEmpty=0, common right after unplug).
            eta=""
            if [ -n "$secs" ] && [ "$secs" -gt 0 ] && [ "$pct_int" -gt "$TARGET_PERCENT" ]; then
                target_secs=$(( secs * (pct_int - TARGET_PERCENT) / pct_int ))
                eta=" — ~$((target_secs / 60)) min to ${TARGET_PERCENT}%"
            fi
            if [ "$pct_int" -le "$CRITICAL_PERCENT" ]; then
                check_cooldown critical "$CRITICAL_COOLDOWN" && \
                    notify-send -u critical \
                        --app-name="Battery" \
                        --icon=battery-empty-symbolic \
                        -h "int:value:${pct_int}" \
                        "Critical battery" \
                        "${pct_int}% left${eta} — plug in now"
            elif [ "$pct_int" -le "$LOW_PERCENT" ]; then
                check_cooldown low "$LOW_COOLDOWN" && \
                    notify-send -u normal \
                        --app-name="Battery" \
                        --icon=battery-caution-symbolic \
                        -h "int:value:${pct_int}" \
                        "Low battery" \
                        "${pct_int}% left${eta} — consider charging"
            fi
        fi
    fi
    sleep "$POLL_INTERVAL"
done
