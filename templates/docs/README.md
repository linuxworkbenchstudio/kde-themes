# @@NAME@@ for KDE Plasma 6 — @@VERSION@@

@@TAGLINE@@
By @@BRAND@@.

## What you get
- **Global Themes** @@NAME@@ Dark and @@NAME@@ Light, with the @@NAME@@ splash screen
- **Plasma Styles** (panels, popups, widgets) with flat task buttons
- **Colour schemes**, Dark and Light
- **Window decorations** (Aurorae) with rounded top corners and a coloured focus border
- **Kvantum app style**: translucent windows and menus (30 % see-through) with blur
- **GTK theme** for GTK apps on Plasma (Firefox, GIMP, Inkscape …), Dark and Light, switched with
  the rest; a GTK theme you picked yourself is left alone
- **Icons**: about 145 folder types (with small sidebar versions), tiles for about 600 apps and the
  app-menu categories, about 260 file types, drives and devices — a generic picture of what each
  app does, never the app's own logo; everything else comes from Papirus or Breeze
- **Cursors**: Breeze cursors recoloured for Dark and Light
- **Wallpaper** "@@NAME@@", Dark and Light (Plasma shows the one that matches the theme)
- **Konsole** colour schemes and profiles
- **Top panel** (40 px): launcher, task manager, centred clock, KVitals system stats and system
  tray, with six looks via the Panel Colorizer widget — Normal, Transparent, Invisible, Cards,
  Pills and Fancy (the default), each in Dark and Light
- **Fastfetch colours**: recolours your own Fastfetch setup, keeping its layout and logo; or the
  optional @@NAME@@ Fastfetch layout, with your distro's logo in @@NAME@@ colours
- **@@NAME@@ Settings**: every setting in one full-screen terminal app (`@@COMMAND@@ settings`, or
  "@@NAME@@ Settings" in the app menu), with Add-ons, About and Uninstall
- **`@@COMMAND@@`**: one command to switch everything between Dark and Light
- **SDDM login screen** (optional, by hand): see `sddm/README.md`

## Install
    cd @@FOLDER@@
    ./install.sh

That starts **@@NAME@@ Setup**, a guided installer in the terminal (needs Python 3). Nothing
changes until you press Install on its Review screen. It shows what your choices need (Kvantum,
qdbus, the KVitals and Panel Colorizer widgets, Fastfetch …) and installs a missing program only if
you say so. Everything goes into your home folder; nothing outside it is touched.

Without the guide:

    ./install.sh --text                        the same as plain questions
    ./install.sh --full                        everything in one go
    ./install.sh --variant both --activate=dark --yes
    ./install.sh --panel --panel-look Pills    build the top panel with the Pills look
    ./install.sh --help                        every option

An earlier version under its old name (Waypoint 0.5 `org.waypoint.*`, Vice Horizon 1.8
`org.digitalcohesion.vicehorizon.*`) is found and, with your yes, moved over: your choices stay,
the old copy goes, files you edited are kept.

## Use
    @@COMMAND@@ dark | light          switch everything
    @@COMMAND@@ panel --apply         build the top panel (your panels are backed up first)
    @@COMMAND@@ panel --look Cards    change its look
    @@COMMAND@@ gtk on | off          GTK apps: @@NAME@@ or your own theme
    @@COMMAND@@ settings              @@NAME@@ Settings
    @@COMMAND@@ uninstall             remove @@NAME@@

Picking @@NAME@@ Dark or Light in System Settings also switches Kvantum, Konsole and Fastfetch
(the login sync helper), unless you turned that off.

## Uninstall
    @@COMMAND@@ uninstall          (or ./uninstall.sh in this folder)

It removes exactly what the installer put in, keeps any file you changed, and puts your look from
before @@NAME@@ back.

## Requirements
KDE Plasma 6. Optional: Kvantum (the app style), Panel Colorizer and KVitals (the top panel; both
are bundled and installed for your user if you want), Fastfetch, Papirus icons, Python 3 (Setup,
Settings, Fastfetch colours).

## Credits and licences
See LICENSE (which part is under which licence) and LICENSES/. Built with the theme engine of
@@BRAND@@ (one engine for all its themes). Thanks to KDE (Breeze, Breeze icons and cursors), the
GTK project, Tsu Jan (Kvantum, KvArc), Luis Bocanegra (Panel Colorizer) and Yassine Amjad (KVitals).
