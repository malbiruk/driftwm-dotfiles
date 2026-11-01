#!/usr/bin/env bash
# Caffeine: "on" replaces idle.sh with a swayidle that only locks before sleep, and blocks
# lid-switch suspend; "off" restarts idle.sh.
# Both run as their own systemd user units so restarting a caller (tide-island) can't kill them.
# Usage: caffeine.sh on|off|toggle|status   (status prints "on" or "off")

DIR="$(cd "$(dirname "$0")" && pwd)"
TAG=drift-caffeine

is_on() { pgrep -f "systemd-inhibit.*--who=$TAG" >/dev/null; }

on() {
    is_on && return
    killall -q swayidle
    systemd-run --user --quiet --collect --unit="$TAG" \
        systemd-inhibit --what=handle-lid-switch --mode=block \
        --who="$TAG" --why=caffeine swayidle -w before-sleep "$DIR/lock.sh"
}

off() {
    systemctl --user stop "$TAG" 2>/dev/null
    pkill -f "systemd-inhibit.*--who=$TAG"
    pgrep -x swayidle >/dev/null && return
    systemd-run --user --quiet --collect --unit=drift-swayidle "$DIR/idle.sh"
}

case "${1:-}" in
    on) on ;;
    off) off ;;
    toggle) if is_on; then off; else on; fi ;;
    status) if is_on; then echo on; else echo off; fi ;;
    *) echo "usage: $0 on|off|toggle|status" >&2; exit 1 ;;
esac
