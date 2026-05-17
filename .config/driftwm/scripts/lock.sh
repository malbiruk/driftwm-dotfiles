#!/bin/sh
# Rose Pine Dawn themed swaylock with leafy-dawn background.

exec swaylock -f \
    --image "$HOME/Pictures/leafy-dawn.png" \
    --scaling fill \
    --indicator-radius 80 \
    --indicator-thickness 12 \
    --ring-color d7827e \
    --inside-color faf4edff \
    --line-color 00000000 \
    --text-color 575279 \
    --ring-clear-color ea9d34 \
    --inside-clear-color faf4edff \
    --line-clear-color 00000000 \
    --text-clear-color 575279 \
    --ring-ver-color 286983 \
    --inside-ver-color faf4edff \
    --line-ver-color 00000000 \
    --text-ver-color 575279 \
    --ring-wrong-color b4637a \
    --inside-wrong-color faf4edff \
    --line-wrong-color 00000000 \
    --text-wrong-color 575279 \
    --key-hl-color 286983 \
    --bs-hl-color 907aa9 \
    --separator-color 00000000 \
    --indicator-idle-visible \
    --show-failed-attempts \
    --layout-text-color 575279 \
    --layout-bg-color faf4edff \
    --layout-border-color 00000000 \
    --font "Monaco Nerd Font Mono" \
    --font-size 42
