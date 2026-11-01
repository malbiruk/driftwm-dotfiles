#!/usr/bin/env bash
# Canonical swayidle invocation. Sourced from config.toml autostart and
# caffeine.sh so both stay in sync.

DIM_BRIGHTNESS=5

LOCK=~/.config/driftwm/scripts/lock.sh

exec swayidle -w \
    timeout 300 "brightnessctl -s set ${DIM_BRIGHTNESS}%" \
        resume 'brightnessctl -r' \
    timeout 1800 'systemctl suspend' \
    before-sleep "$LOCK"
