#!/usr/bin/env bash
# Canonical swayidle invocation. Sourced from config.toml autostart and
# stats_widget.py caffeine toggle so both stay in sync.

DIM_BRIGHTNESS=5

LOCK=~/.config/driftwm/scripts/lock.sh

exec swayidle -w \
    timeout 120 "brightnessctl -s set ${DIM_BRIGHTNESS}%" \
        resume 'brightnessctl -r' \
    timeout 240 "$LOCK" \
    timeout 245 'wlopm --off "*"' \
        resume 'wlopm --on "*"' \
    timeout 545 'systemctl suspend' \
    before-sleep "$LOCK"
