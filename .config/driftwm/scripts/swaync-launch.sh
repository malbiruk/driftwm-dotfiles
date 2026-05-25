#!/usr/bin/env bash
# Generate ~/.config/swaync/config.json from the template, substituting the
# 4 user-facing strings based on $LANG, then exec swaync.

set -euo pipefail

TEMPLATE="${XDG_CONFIG_HOME:-$HOME/.config}/swaync/config.template.json"
OUT="${XDG_CONFIG_HOME:-$HOME/.config}/swaync/config.json"

case "${LANG%%_*}" in
    de)
        T_TITLE="Meldungen"
        T_CLEAR="Löschen"
        T_DND="Nicht stören"
        T_EMPTY="Keine Meldungen"
        ;;
    *)
        T_TITLE="Notifications"
        T_CLEAR="Clear"
        T_DND="Do Not Disturb"
        T_EMPTY="No notifications"
        ;;
esac

sed -e "s|__T_TITLE__|${T_TITLE}|g" \
    -e "s|__T_CLEAR__|${T_CLEAR}|g" \
    -e "s|__T_DND__|${T_DND}|g" \
    -e "s|__T_EMPTY__|${T_EMPTY}|g" \
    "$TEMPLATE" > "$OUT"

exec swaync
