# Optional: SDDM login screen (not installed automatically)

`install.sh` never touches the display manager. SDDM themes live in
`/usr/share/sddm/themes` and its configuration in `/etc/sddm.conf.d`, both
system-wide and root-owned, and a broken greeter can lock you out of a
graphical login. So this component is opt-in, manual and reversible.

@@NAME@@ does not ship its own QML greeter. It restyles the stock
**Breeze** SDDM theme that comes with Plasma 6 by giving it the @@NAME@@
wallpaper. That is the supported customisation point and survives Plasma
updates.

## Option A - System Settings (recommended)

1. Install the KDE components (`./install.sh --desktop kde`) so the wallpaper is present.
2. Open **System Settings -> Colors & Themes -> Login Screen (SDDM)**.
3. Select **Breeze**, click the background button, choose
   `~/.local/share/wallpapers/@@SLUG@@/contents/images_dark/3840x2160.jpg`
   (or `images/` for the Light picture), then **Apply** and authenticate.
4. Optional: the **Apply Plasma Settings...** button copies your fonts, cursor and
   colour scheme to the login screen.

To undo: same page, reset the background or pick another theme.

## Option B - script (needs sudo)

`apply-sddm-background.sh` does the same as Option A from a terminal:

```bash
./sddm/apply-sddm-background.sh --variant dark     # or light
./sddm/apply-sddm-background.sh --restore          # undo
```

What it does, and nothing more:

- copies the chosen wallpaper to `/usr/share/sddm/themes/breeze/@@COMMAND@@-background.jpg`
- backs up an existing `/usr/share/sddm/themes/breeze/theme.conf.user` to
  `theme.conf.user.@@COMMAND@@-backup`, then writes `[General] background=...` and `type=image`
- `--restore` puts the backup back (or removes the file it created) and deletes the copied image

It asks for confirmation, prints every command before running it, and refuses to
run if the Breeze SDDM theme is not installed. It does not change which theme
SDDM uses; select Breeze in System Settings if you use another greeter theme.

Tested: script syntax and dry-run logic only. It has not been run against a live
SDDM install - review it before use.
