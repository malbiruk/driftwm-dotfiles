# driftwm-dotfiles

[driftwm](https://github.com/malbiruk/driftwm) rice (Rose Pine Dawn).

![screenshot](screenshot.png)

## What's included

```
.config/
  driftwm/      WM config, scripts, widgets (Python+uv), wallpaper shader
  waybar/       Taskbar (left) and tray (bottom) bars
  foot/         Terminal with rose-pine-dawn colors
  fuzzel/       Launcher
  swaync/       Notification daemon styling
  swayosd/      OSD styling (volume/brightness)
  fastfetch/    Fastfetch
  gtk-3.0/      GTK theme + icon theme + cursor settings
  gtk-4.0/      Same, plus libadwaita color overrides (rose-pine-dawn)
.local/share/icons/elementary-pastel/   Custom icon theme (elementary + Mignon-pastel apps)
.config/systemd/user/                   Weekly pacman update notifier (user timer)
```

## Install

```bash
paru -S driftwm waybar fuzzel swaync swayosd foot socat fastfetch \
        rose-pine-gtk-theme elementary-icon-theme uv pacman-contrib

git clone https://github.com/malbiruk/driftwm-dotfiles
cd driftwm-dotfiles
cp -r --backup=numbered .config .local ~/   # repo mirrors $HOME; existing files kept as *.~1~

systemctl --user enable --now foot-server.socket    # widgets + mod+return use footclient
cd ~/.config/driftwm/scripts/widgets && uv sync     # widget deps

systemctl --user enable --now pacman-update-notify.timer   # optional: weekly update notifier
```

Fonts: `Adwaita Sans` in GTK UI (set in `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`)
and `Monaco Nerd Font` in foot and fuzzel.

## Notes

- **GTK theme**: `rose-pine-dawn-gtk` from AUR. `gtk-4.0/gtk.css` overrides libadwaita color vars so GTK4 apps match the palette without re-theming.
- **Icon theme**: `elementary-pastel` combines [elementary-icon-theme](https://github.com/elementary/icons) with the colorful app icons from [Mignon-pastel](https://www.gnome-look.org/p/1426967).
- **Widgets**: live in `driftwm/scripts/widgets/`, launched by `widgets/launch.sh` from `config.toml`'s autostart.
- **Immersive maximize**: `driftwm/scripts/immersive_maximize.py` follows the compositor's IPC
  event stream and promotes a maximized window to real fullscreen, dropping the snap gap,
  decorations and wallpaper. Reads the window's `mode` from the IPC state (needs a driftwm that
  reports it), so `fit-window`, the titlebar button and `center-nearest` onto an already-fit
  window all count, while `fill-window` correctly doesn't. `mod+f` drops back to a windowed
  maximize; `mod+m` restores the original size.
- **Update notifier**: `driftwm/scripts/pacman_update_notify.sh` fired weekly by the user timer in `systemd/user/`. Uses `checkupdates` from `pacman-contrib`.

## License

MIT. See [LICENSE](LICENSE).
