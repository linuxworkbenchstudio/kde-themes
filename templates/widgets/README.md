# Bundled panel widgets

The theme's top panel uses two community Plasma widgets. Copies are bundled here, unchanged,
so the installer can add them for your user on any distribution, offline and without a password:

| Widget | Plasma ID | Version | Source (commit) | Licence |
|---|---|---|---|---|
| KVitals - Yassine Amjad | `org.kde.plasma.kvitals` | 3.3.0 | https://github.com/yassine20011/kvitals (7ecaf373f736701b233e1a6481a132f934e5906d) | GPL-3.0 |
| Panel Colorizer - Luis Bocanegra | `luisbocanegra.panel.colorizer` | 8.0.0 | https://github.com/luisbocanegra/plasma-panel-colorizer (d0b1d4cab773f05cdcda2c1b2970093a5c367b54) | GPL-3.0 |

They are installed to `~/.local/share/plasma/plasmoids/<id>/` only when a widget is missing and you
choose Install (Setup) or pass `--widgets` / `--install-deps`; uninstall removes them again. A copy
from your distribution or the AUR is always preferred when you have one.

Panel Colorizer's optional C++ plugin (used only for its custom blur background) is not bundled;
everything the theme's panel looks use works without it. Translations are not bundled (English).
They are shared by every The Linux Workbench theme (templates/widgets/ in the theme engine).
