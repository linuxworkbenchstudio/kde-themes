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

Starting point (4 Nov 2026): Waypoint 6 of 3,867 files (reference: the Waypoint KDE 0.5.0 release
zip); Vice Horizon 0 of 5,865 (1.8.2 source tree; its pack comes in
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
| `[plasma]` | Plasma Style details (corner radius, panel background opacity) |
| `[cursors]` | fill and outline colours |
| `[sddm]` | optional login screen |
| `[store]` | KDE Store texts, screenshots, credits |

## Parts

| # | Part | Waypoint | Vice Horizon | Engine |
|---|---|---|---|---|
| 1 | KDE colour schemes | ✓ | ✓ | **done**, byte-identical to Waypoint 0.2.0 |
| 2 | Konsole colour schemes and profiles | ✓ | ✓ | **done**, byte-identical to Waypoint 0.2.0 |
| 3 | Plasma Style (desktoptheme) | ✓ | ✓ | **done**, from Waypoint templates, recoloured per pack |
| 4 | Global Theme (look-and-feel: defaults, layout, splash, previews) | ✓ | ✓ | **done**: new ids `org.thelinuxworkbench.<theme>.<edition>` |
| 5 | Window decoration (Aurorae) | ✓ | ✓ | **done** |
| 6 | Kvantum (from KvArc/KvArcDark, splitter_width=1, 30 %) | ✓ | ✓ | **done**: one rule set (`[edition.*.kvantum]`) reproduces both generators; defaults from roles |
| 7 | Cursors (recoloured Breeze) | ✓ | ✓ | **done** |
| 8 | Icons: ~145 folder types, ~600 apps, ~260 file types, launcher in hicolor | ✓ | ✓ | **done**: Vice Horizon's generator, colours and style (tile, folder, pages, accent bar) per pack; Waypoint redrawn in its style (choice A, approved) |
| 9 | Wallpapers (Dark/Light) | ✓ | ✓ | **done** (brand part: wallpapers, launcher, splash images, previews, Fastfetch logo from `packs/<pack>/art/`) |
| 10 | GTK 3/4 for GTK apps on Plasma | ✓ | ✓ | **done**: GTK 3.24.52 / 4.16.13 SCSS compiled with Dart Sass 1.78.0 (`tools/get_sass.py`); GTK 4 now ships its images and gtk-dark.css in every theme |
| 11 | Top panel layout (40 px since 5 Nov 2026, was 36; KVitals, centred clock) | ✓ | ✓ | **done**: one script for every theme (Vice Horizon's, with Waypoint's look record); replaces any of the themes' panels |
| 12 | Panel Colorizer: Normal, Transparent, Invisible, Cards, Pills, Fancy × Dark/Light | ✓ | ✓ | **done**: Vice Horizon's look rules, colours per pack; Waypoint moved to them; Cards without a bar, like Pills (5 Nov 2026) |
| 13 | Fastfetch colours and design | ✓ | ✓ | design config **done**; logo with the artwork, recolouring program with the programs |
| 14 | SDDM login screen (optional) | | ✓ | **done**: every theme (helper + README) |
| 15 | The theme command: dark/light, panel, dim, gtk, sync, watch, settings, uninstall | ✓ | ✓ | **done**: Vice Horizon 1.8.2's program as a template (templates/programs/) |
| 16 | Settings app (terminal) with Add-ons and About | ✓ | ✓ (no About yet?) | **done**: Vice Horizon 1.8.2's program as a template (templates/programs/) |
| 17 | Setup (guided installer) | ✓ | ✓ | **done**: Vice Horizon 1.8.2's program as a template (templates/programs/) |
| 18 | Installer and uninstaller: manifest with fingerprints, keeps edited files, restores your look | ✓ | ✓ | **done**: Vice Horizon 1.8.2's program as a template (templates/programs/) |
| 19 | Login sync helper (autostart) | ✓ | ✓ | **done**: Vice Horizon 1.8.2's program as a template (templates/programs/) |
| 20 | Bundled widgets (KVitals, Panel Colorizer) | ✓ | ✓ | **done**: one shared copy (Vice Horizon's) |
| 21 | Licences and credits in each installed part | ✓ | LICENSE only | **done** for every installed folder (single files such as colour schemes share KDE's folders) |
| 22 | Release zip and KDE Store bundle | ✓ | ✓ | **done**: `tools/release.py` |
| 23 | Tests: one suite run against every pack | 167 | 205 | **done**: `tools/test_all.sh [--full]` |

The command, Settings, Setup and installer (15-19) are mostly the same program with the theme's
name in it; in the engine they become templates filled from the pack.

Coverage now (both with 0 different): Vice Horizon 99.5 % of its released files; Waypoint 71.7 %
(the rest is mostly its programs). Waypoint's icons, panel looks and panel script are redrawn on purpose.

### Programs (phase 5, 5 Nov 2026)

Every theme now ships Vice Horizon 1.8.2's programs, filled in from its pack (`tools/port_programs.py`
made the templates once; they are edited by hand since). What changes for **Waypoint**:
- the installer has components (`--with`, `--without`, `--list`), a guided Setup, `--full`, and
  checks the programs the theme needs before asking to install them; Waypoint 0.5's options
  (`--no-gtk`, `--no-fastfetch`, `--skip-addons`, `--activate=later` ...) still work;
- Settings (the terminal app) and the theme command are Vice Horizon's, with Add-ons, About and
  Uninstall; the panel looks, `sync`, `watch` and `gtk` work the same in every theme;
- programs move from `settings/`, `setup/`, `autostart/` into `bin/`.
For every theme:
- `--panel-look` is the option (`--panel-style` still works);
- an install under an old id (Waypoint 0.5 `org.waypoint.*` and its install record, Vice Horizon
  1.8 `org.digitalcohesion.vicehorizon.*`) is found and moved over, with a yes (`--migrate` /
  `--no-migrate`): edition, panel look, Fastfetch and your look from before are kept, the old copy
  goes, files you edited stay;
- the Konsole profile and Fastfetch logo switch over from any of the other themes;
- `tests/run-tests.sh` (Vice Horizon's suite: installs, switches and uninstalls in a throw-away
  home with stand-in KDE tools) runs in every theme's build: Vice Horizon 215, Waypoint 215,
  Natura 209 checks, all passing (5 Nov 2026; again for the 0.1.0 releases). It takes about 40 minutes per theme here.

### Releasing (phase 6, 5 Nov 2026)

    tools/test_all.sh [--full]           engine tests, then every pack: build + static checks
                                         (--full: each pack's whole suite too, in parallel)
    python3 tools/release.py PACK ...    dist/releases/<Name>-<version>/: the zip, store/ (one
                                         package per KDE Store category) and CHECKSUMS.sha256

A release is checked first (static checks and the full suite; `--skip-tests` only for trying it
out) and is reproducible: sorted files, fixed dates (SOURCE_DATE_EPOCH or the build day), the same
input gives the same zip. The zip has no symbolic links (the installer makes the cursor aliases);
the Store's cursor packages keep them. README, LICENSE and LICENSES/ come from templates/docs/ and
templates/licences/, CHANGELOG.md from the pack.

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
2. Licence texts: **kept in each installed part** (Kvantum GPL-3.0, GTK LGPL-2.1, Plasma Style LGPL-2.0).
3. Installer option: **`--panel-look`**; `--panel-style` stays as an alias.
4. Global Theme ids: **`org.thelinuxworkbench.<theme>.<edition>`**.
5. Brand: **The Linux Workbench** for every theme; DigitalCohesion and Desktop Foundry are dropped.
6. **One repository**, `github.com/linuxworkbenchstudio/kde-themes` (public), for the engine and all packs; each theme gets its own page, releases and KDE Store entries (5 Nov 2026).
7. **KDE only** for now.

Natura: all artwork designed here, from the wallpaper Kahlil supplied (Dark and Light).

## Needed to continue

The full source of both themes (generators, dev scripts, assets, tests), not their release zips:
Vice Horizon's latest and Waypoint KDE 0.5.0. The public waypoint-kde repository only has
Waypoint 0.2.0's built files, which is what parts 1 and 2 were checked against.
