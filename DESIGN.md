# The Linux Workbench theme engine: design

One engine, one pack per theme. Waypoint, Vice Horizon and Natura each carry their own copy of the
same machinery (installer, Setup, Settings, the theme command, panel looks, GTK switching, icons,
tests), so every fix has had to be made two or three times and the themes kept drifting apart.
The engine holds the machinery once; a pack holds only what makes a theme itself.

## Layout

```
thelinuxworkbench/
  engine/            the engine (Python 3.11+, standard library only)
    pack.py          reads and checks pack.toml
    colour.py        colour maths (mix, contrast)
    parts/           one module per part of a theme: build(pack) -> {path: text}
  packs/
    waypoint/        pack.toml + art/ (logo, launcher icon, wallpaper, Fastfetch logo)
    vice-horizon/
    natura/
  tests/
    golden/<pack>/   small released files the tests check byte for byte
  tools/
    import_reference.py   copies a theme's last release into references/<pack>/
  references/        (not in the repository) the full released trees, for `engine compare`
```

`python3 -m engine compare packs/<pack>` builds the parts the pack has switched on and checks every
file against the reference: exact, same settings (INI/JSON with the same values in another
order), different (with the first difference), or new. Its coverage figure is the share of the
released theme the engine already makes. Each pack's `parts` list in `[theme]` switches parts on as
they pass.

Starting point (4 Nov 2026): Waypoint 6 of 2,169 files (reference: Waypoint 0.2.0 from GitHub until
the 0.5.0 release zip is imported); Vice Horizon 0 of 5,865 (1.8.2 source tree; its pack comes in
phase 2). New releases from the engine start at **0.1.0** for every theme.

`python3 -m engine build packs/waypoint` writes the theme; `python3 -m engine check packs/waypoint`
checks the pack and prints its palette with contrast ratios.

## The pack

`pack.toml` has a `[theme]` block (name, command, brand, version, file names) and one
`[edition.<id>]` block per edition. Each edition has a small **palette**:

| Name | Meaning |
|---|---|
| `base` | deepest surface: terminal background, inactive title bar (default: `window`) |
| `window`, `raised`, `control` | window background; buttons and alternate rows; buttons if different (default: `raised`) |
| `line` | borders |
| `text`, `muted`, `disabled` | text levels |
| `accent`, `accent_bright`, `on_accent` | selection and focus colour, its lighter version, text on it |
| `link`, `visited` | default to `accent` and `muted` |
| `negative`, `neutral`, `positive` | error, warning, success |

Everything else refers to palette names, to another edition's (`dark.base`), or gives `#RRGGBB`.
`[edition.<id>.kde]` overrides which palette colour fills a KDE colour-scheme slot (defaults in
`pack.py`); `[edition.<id>.terminal]` gives the 8 ANSI colours with their bright versions (faint
versions are 55 % of the colour over the background, which is what Waypoint's hand-made files do).

**File names stay as released.** Waypoint's colour scheme is `Waypoint-Dark` but its Konsole files
are `WaypointDark`; Vice Horizon uses `Vice-Horizon-Dark`. Installed systems and people's own
settings point at these names, so `[theme.names]` keeps each theme's own.

### Still to add to the format (as the parts move over)

| Section | For |
|---|---|
| `[art]` | launcher icon, logo, wallpaper (Dark/Light), Fastfetch logo, splash |
| `[plasma]` | Plasma Style details (corner radius, panel background opacity) |
| `[kvantum]` | window and menu opacity (30 % in both themes now), blur, base theme |
| `[panel]` | default look (Fancy), height (36 px), launcher, widgets; the six looks' tuning |
| `[icons]` | folder colour, tile gradient, glyph colour, accent bar; which glyph sets |
| `[cursors]` | fill and outline colours |
| `[gtk]` | slot overrides for the GTK 3/4 themes |
| `[fastfetch]` | colours and design |
| `[sddm]` | optional login screen |
| `[store]` | KDE Store texts, screenshots, credits |

## Parts

| # | Part | Waypoint | Vice Horizon | Engine |
|---|---|---|---|---|
| 1 | KDE colour schemes | ✓ | ✓ | **done**, byte-identical to Waypoint 0.2.0 |
| 2 | Konsole colour schemes and profiles | ✓ | ✓ | **done**, byte-identical to Waypoint 0.2.0 |
| 3 | Plasma Style (desktoptheme) | ✓ | ✓ | |
| 4 | Global Theme (look-and-feel: defaults, layout, splash, previews) | ✓ | ✓ | |
| 5 | Window decoration (Aurorae) | ✓ | ✓ | |
| 6 | Kvantum (from KvArc/KvArcDark, splitter_width=1, 30 %) | ✓ | ✓ | |
| 7 | Cursors (recoloured Breeze) | ✓ | ✓ | |
| 8 | Icons: ~145 folder types, ~600 apps, ~260 file types, launcher in hicolor | ✓ | ✓ | |
| 9 | Wallpapers (Dark/Light) | ✓ | ✓ | |
| 10 | GTK 3/4 for GTK apps on Plasma | ✓ | ✓ | |
| 11 | Top panel layout (36 px, KVitals, centred clock) | ✓ | ✓ | |
| 12 | Panel Colorizer: Normal, Transparent, Invisible, Cards, Pills, Fancy × Dark/Light | ✓ | ✓ | |
| 13 | Fastfetch colours and design | ✓ | ✓ | |
| 14 | SDDM login screen (optional) | | ✓ | |
| 15 | The theme command: dark/light, panel, dim, gtk, sync, watch, settings, uninstall | ✓ | ✓ | |
| 16 | Settings app (terminal) with Add-ons and About | ✓ | ✓ (no About yet?) | |
| 17 | Setup (guided installer) | ✓ | ✓ | |
| 18 | Installer and uninstaller: manifest with fingerprints, keeps edited files, restores your look | ✓ | ✓ | |
| 19 | Login sync helper (autostart) | ✓ | ✓ | |
| 20 | Bundled widgets (KVitals, Panel Colorizer) | ✓ | ✓ | |
| 21 | Licences and credits in each installed part | ✓ | LICENSE only | |
| 22 | Release zip and KDE Store bundle | ✓ | ✓ | |
| 23 | Tests: one suite run against every pack | 167 | 205 | started |

The command, Settings, Setup and installer (15-19) are mostly the same program with the theme's
name in it; in the engine they become templates filled from the pack.

## How each part moves over

1. Take the part from **Vice Horizon** where it is generated (it already builds the theme from a
   palette file and has the most tests); from Waypoint where Waypoint is ahead.
2. Write the Vice Horizon pack's values for it.
3. **Golden check:** the engine plus the Vice Horizon pack must reproduce Vice Horizon's released
   files, apart from version strings. Waypoint's released files are the second check where they
   were generated the same way; otherwise every colour, file and setting is accounted for and
   checked on a real desktop.
4. Only then does the theme's own copy of that part retire.

Natura is the first pack that never had its own copy: it starts on the engine.

## Decisions (4 Nov 2026)

1. Settings > About with Uninstall: **in every theme.**
2. Licence texts: **open**; proposed: keep them in each installed part, as Waypoint does (parts are
   installed into separate folders, away from LICENSE).
3. Installer option: **`--panel-look`**; `--panel-style` stays as an alias.
4. Global Theme ids: **`org.thelinuxworkbench.<theme>.<edition>`**.
5. Brand: **The Linux Workbench** for every theme; DigitalCohesion and Desktop Foundry are dropped.
6. **One repository** for the engine and all packs (account and public/private still open).
7. **KDE only** for now.

Natura: all artwork designed here, from the wallpaper Kahlil supplied (Dark and Light).

## Needed to continue

The full source of both themes (generators, dev scripts, assets, tests), not their release zips:
Vice Horizon's latest and Waypoint KDE 0.5.0. The public waypoint-kde repository only has
Waypoint 0.2.0's built files, which is what parts 1 and 2 were checked against.
