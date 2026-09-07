# driftwm-dotfiles

[driftwm](https://github.com/malbiruk/driftwm) rice (Rose Pine Dawn).

![screenshot](screenshot.png)

## What's included

```
.config/
  driftwm/      WM config, scripts, widgets (Python+uv), wallpaper shader
  waybar/       Taskbar (left) and tray (bottom) bars
  foot/         Terminal, zenburn (widgets keep rose-pine-dawn)
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

# optional: fake rounded screen corners (autostart entry in config.toml)
git clone https://github.com/rezzubs/wayland-rounded-corners ~/.local/share/wayland-rounded-corners
cargo build --release --manifest-path ~/.local/share/wayland-rounded-corners/Cargo.toml
ln -s ~/.local/share/wayland-rounded-corners/target/release/rounded-corners ~/.local/bin/
```

Fonts: `Adwaita Sans` in GTK UI (set in `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`)
and `Monaco Nerd Font` in foot and fuzzel.

## Notes

- **GTK theme**: `rose-pine-dawn-gtk` from AUR. `gtk-4.0/gtk.css` overrides libadwaita color vars so GTK4 apps match the palette without re-theming.
- **Icon theme**: `elementary-pastel` combines [elementary-icon-theme](https://github.com/elementary/icons) with the colorful app icons from [Mignon-pastel](https://www.gnome-look.org/p/1426967).
- **Widgets**: live in `driftwm/scripts/widgets/`, launched by `widgets/launch.sh` from `config.toml`'s autostart.
- **Rounded corners**: `rounded-corners --radius 10` in autostart draws fake rounded screen corners. [wayland-rounded-corners](https://github.com/rezzubs/wayland-rounded-corners) isn't packaged — build it as above, or drop the autostart line.
- **Update notifier**: `driftwm/scripts/pacman_update_notify.sh` fired weekly by the user timer in `systemd/user/`. Uses `checkupdates` from `pacman-contrib`.

## License

MIT. See [LICENSE](LICENSE).
