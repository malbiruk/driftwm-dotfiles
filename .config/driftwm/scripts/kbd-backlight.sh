#!/bin/sh
# Keyboard backlight up/down via UPower (no root needed), with a swayosd OSD.
# Usage: kbd-backlight.sh up|down
DEST=org.freedesktop.UPower
OBJ=/org/freedesktop/UPower/KbdBacklight
IFACE=org.freedesktop.UPower.KbdBacklight
STEP=32

cur=$(busctl --system call "$DEST" "$OBJ" "$IFACE" GetBrightness | awk '{print $2}')
max=$(busctl --system call "$DEST" "$OBJ" "$IFACE" GetMaxBrightness | awk '{print $2}')

case "$1" in
    up)   new=$((cur + STEP)) ;;
    down) new=$((cur - STEP)) ;;
    *)    echo "usage: $0 up|down" >&2; exit 1 ;;
esac

[ "$new" -gt "$max" ] && new="$max"
[ "$new" -lt 0 ] && new=0

busctl --system call "$DEST" "$OBJ" "$IFACE" SetBrightness i "$new"

pct=$(awk -v n="$new" -v m="$max" 'BEGIN { printf "%.2f", n / m }')
swayosd-client --custom-progress "$pct" --custom-icon keyboard-brightness-symbolic 2>/dev/null
