# The Linux Workbench themes

One engine for The Linux Workbench's KDE Plasma 6 and COSMIC themes (Waypoint, Vice Horizon and Natura out now; Vacation, Vintage Trail and Core coming): each
theme is a pack of colours, names and artwork, and the engine makes every file from it. A fix or a
new feature in the engine reaches every theme at once. `DESIGN.md` has the plan and the decisions.

```
python3 -m engine check packs/waypoint             # check a pack: palette, contrast, ids, parts
python3 -m engine build packs/waypoint --out dist  # write the theme's files
python3 -m engine compare packs/waypoint           # how much of the released theme the engine reproduces
python3 -m unittest discover -s tests -t . -v      # tests
python3 tools/build_site.py                         # the website, into site/ (needs Pillow)
```

Python 3.11 or newer, nothing to install.

## References

`compare` checks the engine against each theme's last release, kept in `references/<pack>/`
(not in the repository: tens of megabytes of icons). Fill it with:

```
python3 tools/import_reference.py vice-horizon Vice-Horizon-source.zip     # 1.8.2 source tree
python3 tools/import_reference.py waypoint     Waypoint-KDE-0.5.0.zip      # the release zip
```

## Status

Parts made by the engine: KDE colour schemes, Konsole colour schemes and profiles (Waypoint:
identical to the release). The other parts move over one at a time; see `DESIGN.md`.
