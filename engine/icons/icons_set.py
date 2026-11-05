#!/usr/bin/env python3
"""The Vice Horizon icon set at Waypoint KDE 0.5.0's size, in Vice Horizon's sunset style.

Called by generate.py (gen_icons) after icons_extra / icons_more:
  - folders: about 145 types, each at 32/48/64/96 (full colour) and 16/22/24 (flat sidebar
    versions), plus scalable and -symbolic copies for any size in between
  - apps: about 600 icon names and the app-menu categories. Every app gets a Vice Horizon tile
    with a glyph for what it does - never the app's own logo
  - file types: about 260 names in about 35 families

Glyphs are Vice Horizon's own G24 symbols (icons_more.py) or small monochrome symbols from KDE's
Breeze icon theme (LGPL-3.0-or-later), kept in assets/src/breeze-symbols/ so the build works
offline. Refresh them from a breeze-icons checkout with:

    python3 scripts/dev/icons_set.py --vendor /path/to/breeze-icons
"""
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import icons_extra as X   # noqa: E402
import icons_more as M    # noqa: E402

ROOT = HERE.parent.parent
VENDOR = ROOT / "assets/src/breeze-symbols"
SOFT, PLUM = X.SOFT, X.PLUM
BREEZE_DIRS = ("actions/16", "places/16", "status/16", "devices/16", "mimetypes/16", "apps/16")

# ---------------------------------------------------------------- glyphs
_cache = {}


BG_CLASSES = ("ColorScheme-Background", "ColorScheme-ViewBackground", "ColorScheme-ButtonBackground")


def _light(hexcol):
    h = hexcol.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b > 200


def breeze(name):
    """A Breeze 16 px symbol as (inner SVG, width). Ink becomes currentColor; parts Breeze paints in
    its background colour (cut-outs on two-tone symbols) become the placeholder __BG__; ids prefixed."""
    if name in _cache:
        return _cache[name]
    p = VENDOR / f"{name}.svg"
    if not p.is_file():
        raise SystemExit(f"Breeze symbol '{name}' is not in {VENDOR.relative_to(ROOT)} - run icons_set.py --vendor")
    s = p.read_text(encoding="utf-8")
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>", s, re.S)
    attrs, body = m.group(1), m.group(2)
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)', attrs)
    w = float(vb.group(1)) if vb else float(re.search(r'width="([\d.]+)', attrs).group(1))
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"<style\b.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<(metadata|title|sodipodi:namedview)\b.*?</\1>|<sodipodi:namedview\b[^>]*/>", "", body, flags=re.S)
    body = re.sub(r"<defs\b[^>]*>\s*</defs>|<defs\b[^>]*/>", "", body)
    body = re.sub(r'\s(?:inkscape|sodipodi):[\w-]+="[^"]*"', "", body)

    def tag(mt):
        t = mt.group(0)
        bg = any(c in t for c in BG_CLASSES)
        t = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", lambda c: "__BG__" if _light(c.group(0)) else "currentColor", t)
        if bg:
            t = t.replace("currentColor", "__BG__")
        return re.sub(r'\sclass="ColorScheme-[\w-]+"', "", t)
    body = re.sub(r"<[a-zA-Z][^>]*>", tag, body)
    body = re.sub(r'\bid="([^"]+)"', r'id="bz-\1"', body)
    body = re.sub(r"url\(#([^)]+)\)", r"url(#bz-\1)", body)
    body = re.sub(r'href="#([^"]+)"', r'href="#bz-\1"', body)
    _cache[name] = (body.strip(), w)
    return _cache[name]


def glyph(spec, x, y, size, colour, bg):
    """spec: 'b:<breeze name>' or a G24 symbol name, drawn in a size x size box at (x, y) in
    `colour`; cut-outs are painted `bg` (the colour of whatever is behind the glyph)."""
    if spec.startswith("b:"):
        body, w = breeze(spec[2:])
        return (f'<g transform="translate({x:g} {y:g}) scale({size / w:.4g})" color="{colour}" '
                f'fill="currentColor">{body.replace("__BG__", bg)}</g>')
    g = M.place(spec, x, y, size / 24).replace("{c}", colour).replace("{bg}", bg)
    return f'<g fill="{colour}">{g}</g>'


def glyph_names():
    """Every Breeze symbol the tables below use."""
    specs = [g for g, _ in FOLDER_TYPES.values()] + [g for g, _, _ in APPS] + [g for g, _, _ in CATEGORIES]
    specs += [g for _, g, _ in FILE_FAMILIES.values()]
    return sorted({s[2:] for s in specs if s.startswith("b:")})


def mid(a, b):
    """The colour halfway down a gradient (behind a centred glyph)."""
    ca, cb = (tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for c in (a, b))
    return "#%02X%02X%02X" % tuple((x + y) // 2 for x, y in zip(ca, cb))


def head(version, what, size=48):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n'
            f'<!-- Vice Horizon {version} {what} - original artwork, CC-BY-SA-4.0; glyphs from '
            f'Vice Horizon or KDE Breeze (LGPL-3.0-or-later) -->\n')


# ---------------------------------------------------------------- folders
FAM = dict(M.FAM, green=("#A9D8B8", "#3B9564", "#857DB5"), night=("#6C64A3", "#4B4670", "#302C49"))
# the folders generate.py has always drawn: (front top, front bottom, back) by its own colours
OWN = {
    "folder": ("peach", None), "folder-open": ("peach", None),
    "user-home": ("violet", "home"), "folder-home": ("violet", "home"),
    "folder-documents": ("mauve", "document"), "folder-download": ("coral", "download"),
    "folder-downloads": ("coral", "download"), "folder-music": ("rose", "note-music"),
    "folder-pictures": ("sand", "image"), "folder-images": ("sand", "image"), "folder-videos": ("lilac", "play"),
    "folder-video": ("lilac", "play"), "user-desktop": ("indigo", "monitor"), "folder-desktop": ("indigo", "monitor"),
    "folder-templates": ("dusk", "grid4"), "folder-publicshare": ("violet", "share"), "folder-public": ("violet", "share"),
    "folder-projects": ("indigo", "code"), "folder-development": ("indigo", "code"),
}
NEW_FOLDERS = {
    # projects, drawings / CAD, 3D
    "folder-cad": ("indigo", "b:measure"), "folder-drawings": ("rose", "b:draw-polygon"),
    "folder-blueprints": ("indigo", "b:draw-rectangle"), "folder-models": ("coral", "b:draw-cuboid"),
    "folder-project": ("indigo", "b:project-development"), "folder-work": ("violet", "b:view-time-schedule"),
    "folder-clients": ("violet", "people"), "folder-reports": ("violet", "chart"), "folder-research": ("lilac", "flask"),
    "folder-todo": ("violet", "b:view-pim-tasks"),
    # code, keys, system
    "folder-src": ("indigo", "b:format-text-code"), "folder-repos": ("coral", "b:vcs-branch"),
    "folder-github": ("coral", "b:vcs-branch"), "folder-scripts": ("night", "b:dialog-scripts"),
    "folder-bin": ("night", "b:application-x-executable"), "folder-dotfiles": ("lilac", "b:configure"),
    "folder-ssh": ("night", "terminal"), "folder-keys": ("violet", "key"),
    "folder-certificates": ("violet", "b:security-high"), "folder-private": ("violet", "lock"),
    "folder-databases": ("lilac", "b:server-database"), "folder-backups": ("violet", "b:backup"),
    "folder-archive": ("sand", "b:archive-insert"), "folder-vms": ("lilac", "b:computer"),
    "folder-iso": ("sand", "disc"), "folder-apps": ("violet", "grid4"),
    # money
    "folder-finance": ("green", "b:view-bank"), "folder-money": ("green", "wallet"),
    "folder-invoices": ("green", "b:view-financial-account-savings"), "folder-taxes": ("green", "calculator"),
    # media and personal
    "folder-movies": ("lilac", "film"), "folder-recordings": ("rose", "b:media-record"),
    "folder-podcasts": ("mauve", "b:podcast"), "folder-themes": ("dusk", "b:color-management"),
    "folder-maps": ("green", "b:mark-location"), "folder-family": ("coral", "people"),
}
FOLDER_TYPES = {}
for _n, (_f, _g) in OWN.items():
    FOLDER_TYPES[_n] = (_g or "", _f)
for _n, (_f, _g) in M.MORE_FOLDERS.items():
    FOLDER_TYPES[_n] = (_g, _f)
for _n, (_f, _g) in NEW_FOLDERS.items():
    FOLDER_TYPES[_n] = (_g, _f)

FOLDER_FULL = (32, 48, 64, 96)
FOLDER_SIDEBAR = (16, 22, 24)


def folder_full(fam, spec, size, version):
    """The sunset folder, tuned per size: bolder glyph and fewer details at 32, a soft inner
    shade at 64 and 96."""
    top, bottom, back = FAM[fam]
    shade = '<rect x="5" y="31" width="38" height="11" rx="3.2" fill="#000" opacity=".06"/>' if size >= 64 else ""
    lip = ('<rect x="5" y="13.5" width="38" height="1.3" rx=".6" fill="#FFFFFF" opacity=".45"/>'
           f'<rect x="5" y="40.6" width="38" height="1.4" rx=".7" fill="{PLUM}" opacity=".18"/>') if size > 32 else ""
    g = ""
    if spec:
        gs = 20 if size == 32 else 18
        g = f'<g opacity=".93">{glyph(spec, 24 - gs / 2, 28.4 - gs / 2, gs, SOFT, mid(top, bottom))}</g>'
    return (head(version, f"folder ({size} px)", 48).replace('width="48" height="48"', f'width="{size}" height="{size}"') +
            f'<defs><linearGradient id="f" x1="0" y1="14" x2="0" y2="42" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>\n'
            f'<path d="M7.5 9.5A2.5 2.5 0 0 1 10 7h9.2a2.5 2.5 0 0 1 1.9.9L23.4 10.5H38a2.5 2.5 0 0 1 2.5 2.5V20h-33z" fill="{back}"/>\n'
            f'<rect x="5" y="13.5" width="38" height="28.5" rx="3.2" fill="url(#f)"/>\n{shade}{lip}\n{g}\n</svg>\n')


def folder_sidebar(fam, spec, size, version):
    """Flat folder in the family colour with the glyph cut out - crisp at sidebar sizes."""
    _, bottom, _ = FAM[fam]
    cut = ""
    if spec:
        cut = glyph(spec, 4.5, 6.2, 7, "#000", "#FFF")
    return (head(version, f"sidebar folder ({size} px)", 16).replace('width="16" height="16"', f'width="{size}" height="{size}"') +
            f'<defs><mask id="m"><rect width="16" height="16" fill="#FFF"/>{cut}</mask></defs>\n'
            f'<path fill="{bottom}" mask="url(#m)" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h3.6l1.5 1.6h5.9A1.5 1.5 0 0 1 15 5.1v7.4a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5z"/>\n'
            '</svg>\n')


# ---------------------------------------------------------------- apps
APPS = [
    # (glyph, tile family, "icon names ...") - third-party apps get a tile for what they do, no logo
    ("b:globe", "violet", "firefox org.mozilla.firefox chromium org.chromium.Chromium google-chrome com.google.Chrome "
                          "brave-browser com.brave.Browser org.kde.falkon org.gnome.Epiphany zen-browser "
                          "app.zen_browser.zen web-browser internet-web-browser firefox-esr librewolf vivaldi-stable "
                          "microsoft-edge opera org.kde.konqueror org.kde.angelfish"),
    ("b:mail-message", "coral", "thunderbird org.mozilla.thunderbird org.gnome.Evolution org.gnome.Geary org.kde.kmail2 "
                                "org.kde.kontact internet-mail"),
    ("b:view-conversation-balloon", "indigo", "telegram-desktop org.telegram.desktop discord com.discordapp.Discord vesktop signal-desktop "
                                              "org.signal.Signal element-desktop im.riot.Riot slack com.slack.Slack org.kde.neochat "
                                              "org.kde.konversation org.gnome.Fractal internet-chat pidgin hexchat"),
    ("b:camera-video", "lilac", "zoom us.zoom.Zoom org.gnome.Snapshot org.kde.kamoso org.gnome.Cheese"),
    ("b:phone", "green", "org.kde.kdeconnect.app org.kde.kdeconnect-settings org.gnome.Calls"),
    ("note-music", "pink", "org.kde.elisa rhythmbox org.gnome.Rhythmbox3 strawberry org.strawberrymusicplayer.strawberry "
                           "org.kde.amarok spotify com.spotify.Client org.gnome.Music multimedia-audio-player quodlibet "
                           "clementine"),
    ("b:media-record", "coral", "audacity org.audacityteam.Audacity obs com.obsproject.Studio org.gnome.SoundRecorder "
                                "easyeffects com.github.wwmm.easyeffects pavucontrol org.pulseaudio.pavucontrol ardour lmms"),
    ("b:podcast", "mauve", "org.gnome.Podcasts org.kde.kasts gpodder"),
    ("b:media-playback-start", "mauve", "vlc org.videolan.VLC mpv io.mpv.Mpv celluloid io.github.celluloid_player.Celluloid "
                                        "org.kde.haruna org.kde.dragonplayer org.gnome.Totem org.gnome.Showtime kodi tv.kodi.Kodi "
                                        "freetube io.freetubeapp.FreeTube multimedia-video-player smplayer"),
    ("b:kdenlive-show-video", "dusk", "org.kde.kdenlive kdenlive shotcut org.shotcut.Shotcut openshot org.openshot.OpenShot "
                                      "davinci-resolve resolve handbrake fr.handbrake.ghb"),
    ("b:draw-brush", "peach", "gimp org.gimp.GIMP org.kde.krita krita com.github.PintaProject.Pinta org.kde.kolourpaint "
                              "com.github.xournalpp.xournalpp mypaint"),
    ("b:draw-bezier-curves", "peach", "inkscape org.inkscape.Inkscape scribus net.scribus.Scribus org.kde.karbon penpot"),
    ("b:camera-photo", "dusk", "darktable org.darktable.Darktable rawtherapee com.rawtherapee.RawTherapee org.kde.digikam "
                               "shotwell org.gnome.Shotwell org.kde.showfoto org.kde.spectacle flameshot "
                               "org.flameshot.Flameshot org.gnome.Screenshot accessories-screenshot hugin"),
    ("b:image-x-generic", "peach", "org.kde.gwenview org.gnome.eog org.gnome.Loupe nomacs org.nomacs.ImageLounge "
                                   "org.xfce.ristretto org.gnome.gThumb"),
    ("b:draw-cuboid", "coral", "blender org.blender.Blender freecad org.freecad.FreeCAD openscad org.openscad.OpenSCAD "
                               "prusa-slicer com.prusa3d.PrusaSlicer cura com.ultimaker.cura meshlab net.meshlab.MeshLab "
                               "godot org.godotengine.Godot solvespace"),
    ("b:measure", "indigo", "librecad org.librecad.librecad qcad org.qcad.QCAD kicad org.kicad.KiCad sweethome3d "
                            "com.sweethome3d.Sweethome3d drawio com.jgraph.drawio.desktop fritzing dia"),
    ("b:color-picker", "dusk", "org.kde.kcolorchooser"),
    ("b:font", "mauve", "org.gnome.font-viewer font-manager org.gnome.FontManager org.kde.kfontview"),
    ("b:x-office-document", "violet", "libreoffice-writer org.libreoffice.LibreOffice.writer libreoffice-startcenter "
                                      "org.libreoffice.LibreOffice onlyoffice-desktopeditors org.onlyoffice.desktopeditors "
                                      "wps-office2019-wpsmain org.gnome.TextEditor abiword"),
    ("b:x-office-spreadsheet", "green", "libreoffice-calc org.libreoffice.LibreOffice.calc gnumeric"),
    ("b:x-office-presentation", "coral", "libreoffice-impress org.libreoffice.LibreOffice.impress"),
    ("b:draw-polygon", "peach", "libreoffice-draw org.libreoffice.LibreOffice.draw"),
    ("b:server-database", "lilac", "libreoffice-base org.libreoffice.LibreOffice.base dbeaver io.dbeaver.DBeaverCommunity "
                                   "sqlitebrowser org.sqlitebrowser.sqlitebrowser"),
    ("calculator", "night", "libreoffice-math org.libreoffice.LibreOffice.math org.kde.kcalc org.gnome.Calculator "
                            "qalculate-gtk qalculate-qt org.kde.kalk galculator"),
    ("b:documentinfo", "coral", "org.kde.okular okular org.gnome.Evince org.gnome.Papers org.pwmt.zathura "
                                "com.github.jeromerobert.pdfarranger atril"),
    ("book", "mauve", "calibre com.calibre_ebook.calibre com.github.johnfactotum.Foliate org.kde.arianna"),
    ("b:note", "peach", "obsidian md.obsidian.Obsidian joplin net.cozic.joplin_desktop logseq com.logseq.Logseq "
                        "org.kde.knotes org.kde.marknote zim cherrytree"),
    ("b:view-pim-tasks", "violet", "org.kde.korganizer io.github.mrvladus.List io.github.alainm23.planify org.gnome.Todo"),
    ("b:view-calendar-month", "coral", "org.gnome.Calendar org.kde.merkuro.calendar org.kde.kalendar office-calendar"),
    ("b:view-pim-contacts", "violet", "org.gnome.Contacts org.kde.kaddressbook office-address-book"),
    ("b:feed-subscribe", "coral", "org.kde.akregator io.gitlab.news_flash.NewsFlash liferea"),
    ("b:language-chooser", "dusk", "app.drey.Dialect anki net.ankiweb.Anki"),
    ("b:mark-location", "green", "org.gnome.Maps org.kde.marble qgis org.qgis.qgis org.kde.itinerary"),
    ("cloud", "indigo", "org.gnome.Weather org.kde.kweather"),
    ("b:clock", "dusk", "org.gnome.clocks org.kde.kclock org.kde.ktimer"),
    ("b:chronometer", "dusk", "org.kde.ktimetracker gtimelog"),
    ("b:view-bank", "green", "org.kde.kmymoney gnucash org.gnucash.GnuCash homebank org.kde.skrooge"),
    ("b:format-text-code", "night", "code com.visualstudio.code code-oss codium com.vscodium.codium org.kde.kate org.kde.kwrite "
                                    "org.kde.kdevelop jetbrains-idea com.jetbrains.IntelliJ-IDEA-Community jetbrains-pycharm "
                                    "com.jetbrains.PyCharm-Community android-studio qtcreator org.qt.qtcreator sublime_text zed "
                                    "dev.zed.Zed nvim emacs geany org.gnome.gedit org.gnome.Builder arduino arduino-ide "
                                    "accessories-text-editor applications-development eclipse mousepad"),
    ("b:vcs-branch", "coral", "github-desktop io.github.shiftey.Desktop gitkraken org.gnome.gitg git-cola"),
    ("b:debug-run", "night", "wireshark org.wireshark.Wireshark postman com.getpostman.Postman org.kde.qdbusviewer ghidra"),
    ("containers", "indigo", "docker-desktop podman-desktop io.podman_desktop.PodmanDesktop"),
    ("b:computer", "lilac", "virtualbox org.virtualbox.VirtualBox virt-manager org.virt-manager.virt-manager "
                            "org.gnome.Boxes bottles com.usebottles.bottles lutris net.lutris.Lutris wine"),
    ("remote", "indigo", "org.kde.krdc remmina org.remmina.Remmina rustdesk com.rustdesk.RustDesk anydesk teamviewer "
                         "org.gnome.Connections filezilla"),
    ("terminal", "night", "alacritty org.alacritty.Alacritty kitty wezterm org.wezfurlong.wezterm tilix "
                                      "com.gexperts.Tilix ghostty com.mitchellh.ghostty com.raggesilver.BlackBox guake "
                                      "xfce4-terminal xterm foot terminator"),
    ("b:configure", "violet", "org.gnome.tweaks org.gnome.Extensions com.mattjakeman.ExtensionManager ca.desrt.dconf-editor "
                              "qt6ct kvantummanager org.kde.kinfocenter org.kde.kmenuedit org.bleachbit.BleachBit "
                              "preferences-desktop-theme"),
    ("b:speedometer", "green", "org.kde.plasma-systemmonitor org.kde.ksysguard org.gnome.SystemMonitor net.nokyan.Resources "
                               "io.missioncenter.MissionCenter htop btop org.corectrl.CoreCtrl utilities-system-monitor"),
    ("b:drive-harddisk", "lilac", "org.kde.partitionmanager gparted org.gnome.DiskUtility org.kde.filelight org.gnome.baobab "
                                  "org.kde.isoimagewriter balena-etcher io.gitlab.adhami3310.Impression "
                                  "org.fedoraproject.MediaWriter"),
    ("b:backup", "violet", "timeshift org.kde.kbackup org.gnome.DejaDup com.borgbase.Vorta org.gnome.World.PikaBackup"),
    ("box", "violet", "org.kde.discover plasmadiscover org.gnome.Software pamac-manager "
                      "io.github.flattool.Warehouse com.github.tchx84.Flatseal it.mijorus.gearlever "
                      "system-software-install system-software-update synaptic"),
    ("b:package-x-generic", "peach", "org.kde.ark org.gnome.FileRoller peazip io.github.peazip.PeaZip utilities-file-archiver"),
    ("folder", "peach", "nemo thunar org.xfce.thunar pcmanfm-qt org.kde.krusader doublecmd caja"),
    ("download", "coral", "qbittorrent org.qbittorrent.qBittorrent transmission-gtk transmission-qt "
                          "org.deluge_torrent.deluge org.kde.ktorrent de.haeckerfelix.Fragments motrix"),
    ("b:folder-sync", "indigo", "nextcloud com.nextcloud.desktopclient.nextcloud owncloud dropbox com.dropbox.Client "
                                "syncthing syncthingtray org.localsend.localsend_app"),
    ("b:dialog-password", "violet", "keepassxc org.keepassxc.KeePassXC bitwarden com.bitwarden.desktop org.kde.kwalletmanager5 "
                                    "org.kde.kwalletmanager org.gnome.seahorse.Application org.gnome.World.Secrets "
                                    "com.belmoussaoui.Authenticator org.kde.kleopatra"),
    ("b:security-high", "indigo", "protonvpn com.protonvpn.www mullvad-vpn net.mullvad.MullvadVPN firewall-config gufw "
                                  "org.kde.plasma-vault io.github.mpobaschnig.Vaults org.cryptomator.Cryptomator veracrypt"),
    ("b:help-contents", "violet", "org.kde.khelpcenter org.gnome.Yelp help-browser"),
    ("b:tools-report-bug", "coral", "org.kde.drkonqi"),
    ("b:system-search", "indigo", "org.kde.krunner io.github.cboxdoerfer.FSearch org.xfce.Catfish recoll"),
    ("b:draw-text", "mauve", "org.gnome.Characters org.kde.kcharselect"),
    ("clipboard", "lilac", "org.kde.klipper copyq com.github.hluk.copyq"),
    ("b:input-keyboard", "night", "fcitx5 org.fcitx.Fcitx5 fcitx5-configtool ibus-setup org.freedesktop.Piper"),
    ("b:network-wireless", "indigo", "nm-connection-editor blueman-manager org.kde.bluedevilwizard"),
    ("b:printer", "lilac", "system-config-printer org.kde.print-manager org.gnome.SimpleScan org.kde.skanlite "
                           "org.kde.skanpage"),
    ("star", "dusk", "org.kde.kstars stellarium org.stellarium.Stellarium"),
    ("flask", "lilac", "org.kde.kalzium org.kde.cantor org.kde.labplot octave org.octave.Octave rstudio "
                       "org.spyder_ide.Spyder org.jupyter.JupyterLab org.geogebra.GeoGebra org.kde.kalgebra"),
    ("cap", "violet", "org.kde.kturtle org.kde.ktouch org.kde.kgeography org.kde.parley org.kde.minuet "
                      "org.kde.gcompris"),
    ("gamepad", "lilac", "steam com.valvesoftware.Steam heroic com.heroicgameslauncher.hgl prismlauncher "
                         "org.prismlauncher.PrismLauncher retroarch org.libretro.RetroArch dolphin-emu "
                         "org.DolphinEmu.dolphin-emu pcsx2 net.pcsx2.PCSX2 org.duckstation.DuckStation org.kde.kpat "
                         "org.kde.kmines org.kde.knights org.kde.ksudoku org.kde.kblocks org.gnome.Chess "
                         "org.gnome.Mines org.gnome.Sudoku org.gnome.Mahjongg org.gnome.Aisleriot protonup-qt "
                         "net.davidotek.pupgui2 com.vysp3r.ProtonPlus supertuxkart 0ad wesnoth openttd "
                         "org.luanti.luanti ppsspp rpcs3 mgba"),
]
CATEGORIES = [
    # (glyph, tile family, names) - Kickoff, Kicker and GNOME's app grid use these
    ("grid4", "violet", "applications-all applications-other"),
    ("b:globe", "violet", "applications-internet preferences-system-network-proxy"),
    ("b:media-playback-start", "mauve", "applications-multimedia"),
    ("b:draw-brush", "peach", "applications-graphics"),
    ("b:x-office-document", "violet", "applications-office"),
    ("b:format-text-code", "night", "applications-development applications-engineering-development"),
    ("gamepad", "lilac", "applications-games"),
    ("cap", "violet", "applications-education applications-education-language"),
    ("flask", "lilac", "applications-science applications-education-science applications-education-mathematics"),
    ("b:measure", "indigo", "applications-engineering"),
    ("b:configure", "violet", "applications-system preferences-system-windows preferences-desktop-peripherals"),
    ("wrench", "dusk", "applications-utilities applications-accessories"),
    ("b:speedometer", "green", "applications-monitoring"),
    ("star", "dusk", "applications-education-astronomy applications-astronomy"),
    ("b:mark-location", "green", "applications-geography applications-education-geography"),
    ("person", "coral", "applications-social preferences-desktop-user preferences-desktop-accessibility"),
    ("note-music", "pink", "applications-education-music applications-audio"),
    ("b:language-chooser", "dusk", "applications-education-languages preferences-desktop-locale"),
    ("b:help-contents", "violet", "help-about-app applications-help"),
    ("b:camera-photo", "dusk", "applications-photography"),
    ("b:server-database", "lilac", "applications-database"),
    ("lock", "indigo", "applications-security"),
]

# ---------------------------------------------------------------- file types
# family: ((page top, page bottom), glyph, names)
FILE_FAMILIES = {
    "cad": (("#C3B8E6", "#6C64A3"), "b:measure", ["image-vnd.dxf", "image-vnd.dwg", "image-x-dxf", "image-x-dwg",
                                                   "application-acad", "application-x-autocad", "application-x-qcad",
                                                   "application-x-freecad", "application-x-kicad-project",
                                                   "application-x-kicad-schematic", "application-x-kicad-pcb"]),
    "model3d": (("#F4A79A", "#C93B32"), "b:draw-cuboid", ["model-stl", "model-x.stl-ascii", "model-x.stl-binary",
                                                          "model-obj", "model-3mf", "application-vnd.ms-3mfdocument", "model-step",
                                                          "application-x-step", "model-iges", "model-gltf-binary", "model-gltf+json",
                                                          "model-vrml", "application-x-blender", "application-x-3ds",
                                                          "application-x-fbx", "application-x-openscad", "text-x-gcode"]),
    "font": (("#DDB6D5", "#857DB5"), "b:font", ["font-x-generic", "font-ttf", "font-otf", "font-woff", "font-woff2",
                                                 "font-collection", "application-x-font-ttf", "application-x-font-otf",
                                                 "application-x-font-type1", "application-x-font-pcf"]),
    "ebook": (("#DDB6D5", "#A77091"), "book", ["application-epub+zip", "application-x-mobipocket-ebook",
                                               "application-x-fictionbook+xml", "application-vnd.amazon.ebook",
                                               "application-vnd.comicbook+zip", "application-x-cbz", "application-x-cbr",
                                               "image-vnd.djvu"]),
    "calendar": (("#F4A79A", "#EA5148"), "b:view-calendar-month", ["text-calendar", "text-x-vcalendar"]),
    "contact": (("#B9B2E3", "#6C64A3"), "b:view-pim-contacts", ["text-vcard", "text-x-vcard", "text-directory"]),
    "mail": (("#F4A79A", "#C93B32"), "b:mail-message", ["message-rfc822", "message-news", "application-mbox",
                                                        "application-vnd.ms-outlook"]),
    "database": (("#C3B8E6", "#6C64A3"), "b:server-database", ["application-x-sqlite3", "application-vnd.sqlite3",
                                                               "application-sql", "text-x-sql", "application-x-sql",
                                                               "application-vnd.ms-access", "application-vnd.oasis.opendocument.database"]),
    "package": (("#FAD3C0", "#C48FBA"), "box", ["application-x-deb", "application-vnd.debian.binary-package", "application-x-rpm",
                                                "application-x-redhat-package-manager", "application-x-source-rpm",
                                                "application-vnd.appimage", "application-x-appimage", "application-vnd.flatpak",
                                                "application-vnd.flatpak.ref", "application-vnd.flatpak.repo", "application-vnd.snap",
                                                "application-x-xz-pkg", "application-x-arch-package",
                                                "application-vnd.android.package-archive", "application-x-java-archive"]),
    "cert": (("#DDB6D5", "#857DB5"), "b:security-high", ["application-x-x509-ca-cert", "application-x-x509-user-cert",
                                                          "application-pkix-cert", "application-pkcs7-signature", "application-pkcs12"]),
    "key": (("#DDB6D5", "#6C64A3"), "key", ["application-pgp-keys", "application-pgp-encrypted", "application-pgp-signature",
                                            "application-x-pem-key", "application-x-ssh-key"]),
    "disc": (("#FAD3C0", "#857DB5"), "disc", ["application-x-cd-image", "application-x-iso9660-image", "application-x-raw-disk-image",
                                              "application-x-cue", "application-x-apple-diskimage", "application-x-qemu-disk",
                                              "application-x-vmdk", "application-x-virtualbox-vdi", "application-x-ova"]),
    "torrent": (("#F4A79A", "#EA5148"), "torrent", ["application-x-bittorrent"]),
    "subtitle": (("#B9A9DA", "#857DB5"), "bubble", ["application-x-subrip", "text-x-ssa", "text-vtt", "text-x-microdvd"]),
    "playlist": (("#F5B3A8", "#C48FBA"), "b:media-playlist-append", ["audio-x-mpegurl", "application-vnd.apple.mpegurl",
                                                                     "audio-x-scpls", "application-xspf+xml"]),
    "patch": (("#C48FBA", "#6C64A3"), "b:vcs-commit", ["text-x-patch", "text-x-diff"]),
    "log": (("#4B4670", "#252239"), "lines", ["text-x-log", "text-x-changelog"]),
    "config": (("#C48FBA", "#857DB5"), "b:configure", ["application-x-desktop", "text-x-ini", "application-toml", "application-x-yaml",
                                                       "application-yaml", "text-x-systemd-unit", "text-x-dockerfile",
                                                       "text-x-cmake", "text-x-makefile", "text-x-readme"]),
    "data": (("#B9B2E3", "#6C64A3"), "braces", ["application-json", "application-xml", "text-xml"]),
    "code": (("#4B4670", "#252239"), "b:format-text-code", [
        "text-x-csrc", "text-x-chdr", "text-x-c++src", "text-x-c++hdr", "text-x-csharp", "text-x-java", "text-x-kotlin",
        "text-x-go", "text-x-rust", "text-x-swift", "text-x-dart", "text-x-haskell", "text-x-lua", "text-x-qml",
        "text-css", "text-x-scss", "application-javascript", "application-typescript", "text-x-typescript",
        "application-x-php", "application-x-ruby", "application-x-perl"]),
    "script": (("#4B4670", "#252239"), "b:dialog-scripts", ["text-x-python", "text-x-python3", "text-x-script",
                                                             "application-x-shellscript", "application-x-ipynb+json"]),
    "markdown": (("#DDB6D5", "#857DB5"), "markdown", ["text-markdown", "text-x-markdown", "text-x-rst", "text-x-tex"]),
    "windows": (("#C3B8E6", "#857DB5"), "window", ["application-x-ms-dos-executable", "application-x-msi", "application-x-msdownload",
                                                   "application-x-ms-shortcut"]),
    "web": (("#B9B2E3", "#6C64A3"), "globe", ["application-x-mswinurl", "text-x-uri", "application-x-mozilla-bookmarks"]),
    "drawing": (("#FAD3C0", "#F2A98F"), "brush", ["image-x-xcf", "application-x-krita", "image-openraster", "image-x-psd",
                                                  "image-vnd.adobe.photoshop"]),
    "vector": (("#FAD3C0", "#EFA1A1"), "b:draw-bezier-curves", ["image-svg+xml", "image-svg+xml-compressed", "image-x-eps",
                                                                "application-postscript"]),
    "csv": (("#A9D8B8", "#3B9564"), "table", ["text-csv", "text-tab-separated-values"]),
}
# extra names that take an existing family's icon (copied from its first name)
FAMILY_EXTRAS = {
    "image-x-generic": ["image-avif", "image-heif", "image-jxl", "image-x-icon", "image-x-portable-pixmap", "image-x-tga",
                        "image-x-exr", "image-x-canon-cr2", "image-x-nikon-nef", "image-x-adobe-dng"],
    "audio-x-generic": ["audio-aac", "audio-x-m4a", "audio-x-aiff", "audio-opus", "audio-x-ms-wma", "audio-midi", "audio-x-wavpack"],
    "video-x-generic": ["video-x-msvideo", "video-x-ms-wmv", "video-x-flv", "video-mpeg", "video-mp2t", "video-3gpp", "video-ogg"],
    "package-x-generic": ["application-x-bzip", "application-x-bzip2", "application-x-bzip-compressed-tar", "application-x-lzma",
                          "application-zstd", "application-vnd.rar", "application-x-cpio"],
    "x-office-document": ["application-vnd.oasis.opendocument.text-template", "application-vnd.apple.pages",
                          "application-vnd.wordperfect"],
    "x-office-spreadsheet": ["application-vnd.oasis.opendocument.spreadsheet-template", "application-vnd.apple.numbers",
                             "application-vnd.ms-excel.sheet.macroenabled.12"],
    "x-office-presentation": ["application-vnd.oasis.opendocument.presentation-template", "application-vnd.apple.keynote"],
}


def file_page(top, bottom, spec, version):
    g = glyph(spec, 16, 22.2, 16, SOFT, mid(top, bottom))
    return (head(version, "file-type icon") +
            f'<defs><linearGradient id="p" x1="0" y1="4" x2="0" y2="44" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>\n'
            '<path d="M11.5 4.5h17l9 9v28a2 2 0 0 1-2 2h-24a2 2 0 0 1-2-2v-35a2 2 0 0 1 2-2z" fill="url(#p)"/>\n'
            '<path d="M28.5 4.5v7a2 2 0 0 0 2 2h7z" fill="#FFFFFF" opacity=".45"/>\n'
            f'<rect x="9.5" y="42" width="28" height="1.5" rx=".75" fill="{PLUM}" opacity=".18"/>\n'
            f'<g opacity=".95">{g}</g>\n</svg>\n')


def tile(spec, fam, version):
    top, bottom = M.TILE[fam]
    edge = ".16" if fam == "night" else "0"
    g = glyph(spec, 12, 12, 24, SOFT, mid(top, bottom))
    return (head(version, "app icon") +
            f'<defs><linearGradient id="t" x1="0" y1="4" x2="0" y2="44" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>\n'
            '<clipPath id="c"><rect x="4" y="4" width="40" height="40" rx="10"/></clipPath></defs>\n'
            '<rect x="4" y="4" width="40" height="40" rx="10" fill="url(#t)"/>\n'
            '<g clip-path="url(#c)"><rect x="4" y="4" width="40" height="1.4" fill="#FFFFFF" opacity=".4"/>\n'
            f'<rect x="4" y="42.4" width="40" height="1.6" fill="{PLUM}" opacity=".2"/></g>\n'
            f'<rect x="4.5" y="4.5" width="39" height="39" rx="9.5" fill="none" stroke="#FFFFFF" stroke-opacity="{edge}"/>\n'
            f'<g opacity=".95">{g}</g>\n</svg>\n')


# ---------------------------------------------------------------- writing
def write_all(write, base, version, variant):
    """Write everything into icon theme `base` (relative to ROOT). Names icons_extra / icons_more
    already drew keep their hand-made artwork. Returns {kind: count}."""
    text = SOFT if variant == "dark" else PLUM
    root = ROOT / base
    n = {"folder types": 0, "app names": 0, "categories": 0, "file types": 0}
    for name, (spec, fam) in FOLDER_TYPES.items():
        for size in FOLDER_FULL:
            write(base / f"places/{size}" / f"{name}.svg", folder_full(fam, spec, size, version))
        for size in FOLDER_SIDEBAR:
            write(base / f"places/{size}" / f"{name}.svg", folder_sidebar(fam, spec, size, version))
        if not (root / f"places/scalable/{name}.svg").exists():
            write(base / "places/scalable" / f"{name}.svg", folder_full(fam, spec, 48, version))
        if not (root / f"places/scalable/{name}-symbolic.svg").exists():
            sym = spec if spec and not spec.startswith("b:") else None
            write(base / "places/scalable" / f"{name}-symbolic.svg", M.folder_symbolic(sym, version, text))
        n["folder types"] += 1
    for spec, fam, names in APPS:
        svg = tile(spec, fam, version)
        for nm in names.split():
            if not (root / f"apps/scalable/{nm}.svg").exists():
                write(base / "apps/scalable" / f"{nm}.svg", svg)
    for spec, fam, names in CATEGORIES:
        svg = tile(spec, fam, version)
        for nm in names.split():
            write(base / "categories/scalable" / f"{nm}.svg", svg); n["categories"] += 1
    for fam, ((top, bottom), spec, names) in FILE_FAMILIES.items():
        svg = file_page(top, bottom, spec, version)
        for nm in names:
            write(base / "mimetypes/scalable" / f"{nm}.svg", svg)
    for first, names in FAMILY_EXTRAS.items():
        src = (root / f"mimetypes/scalable/{first}.svg").read_text()
        for nm in names:
            if not (root / f"mimetypes/scalable/{nm}.svg").exists():
                write(base / "mimetypes/scalable" / f"{nm}.svg", src)
    n["app names"] = len(list((root / "apps/scalable").glob("*.svg")))
    n["file types"] = len([p for p in (root / "mimetypes/scalable").glob("*.svg") if p.stem not in ("inode-directory", "folder")])
    return n


def index_dirs():
    """(directory, context, size, type) entries for index.theme, fixed sizes first."""
    d = [(f"places/{s}", "Places", s, "Fixed") for s in FOLDER_SIDEBAR + FOLDER_FULL]
    d.append(("categories/scalable", "Categories", 48, "Scalable"))
    return d


# ---------------------------------------------------------------- vendoring
def vendor(breeze_root):
    breeze_root = Path(breeze_root)
    icons = breeze_root / "icons" if (breeze_root / "icons").is_dir() else breeze_root
    if VENDOR.exists():
        shutil.rmtree(VENDOR)
    VENDOR.mkdir(parents=True)
    missing = []
    for name in glyph_names():
        for d in BREEZE_DIRS:
            p = icons / d / f"{name}.svg"
            if p.exists():
                shutil.copyfile(p.resolve(), VENDOR / f"{name}.svg")
                break
        else:
            missing.append(name)
    commit = ""
    try:
        import subprocess
        commit = subprocess.run(["git", "-C", str(breeze_root), "log", "-1", "--format=%H %cs"],
                                capture_output=True, text=True).stdout.strip()
    except OSError:
        pass
    (VENDOR / "README.md").write_text(
        "# Breeze symbols\n\n"
        "Small monochrome symbols from KDE's Breeze icon theme (https://invent.kde.org/frameworks/breeze-icons),\n"
        "used as glyphs on Vice Horizon's own folder, tile and page artwork. Copyright (C) 2014 Uri Herrera and\n"
        "others, licensed LGPL-3.0-or-later (LICENSES/LGPL-3.0-or-later.txt). They are recoloured when the\n"
        "icons are generated; the files here are unchanged copies.\n\n"
        f"Source: breeze-icons {commit or '(commit unknown)'}, icons/{{actions,places,status,devices,mimetypes,apps}}/16\n"
        f"Refresh: python3 scripts/dev/icons_set.py --vendor /path/to/breeze-icons\n")
    print(f"vendored {len(glyph_names()) - len(missing)} Breeze symbols into {VENDOR.relative_to(ROOT)}")
    if missing:
        sys.exit("not found in Breeze: " + " ".join(missing))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--vendor":
        vendor(sys.argv[2])
    else:
        sys.exit(__doc__)
