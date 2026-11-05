"""Vice Horizon app, device and file-type icons (original artwork, CC-BY-SA-4.0).

Drawn from the palette in the same language as the folder icons: soft vertical gradients,
Soft White symbols, a light top edge and a faint plum base line. Each icon is a generic
symbol for what the app does - no third-party logos are reproduced.
Imported by generate.py (gen_icons).
"""
import math

SOFT = "#FEFCFC"
PLUM = "#2F1F2B"

# tile gradients (top, bottom)
FAM = {
    "coral":  ("#F4A79A", "#EA5148"),
    "peach":  ("#FAD3C0", "#F2A98F"),
    "pink":   ("#F5B3A8", "#E58C8C"),
    "mauve":  ("#DDB6D5", "#A77091"),
    "violet": ("#B9B2E3", "#6C64A3"),
    "night":  ("#4B4670", "#252239"),
    "dusk":   ("#C48FBA", "#857DB5"),
}


def _gear(cx=24, cy=24, r_out=11.5, r_in=8.6, teeth=8, hole=3.6):
    pts = []
    for i in range(teeth * 4):
        a = (i / (teeth * 4)) * 2 * math.pi - math.pi / 2
        r = r_out if (i % 4) in (1, 2) else r_in
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return (f'<path fill-rule="evenodd" d="M{" L".join(pts)} Z M{cx + hole},{cy} '
            f'a{hole},{hole} 0 1 0 {-2 * hole},0 a{hole},{hole} 0 1 0 {2 * hole},0 Z"/>')


S = 'stroke="{c}" fill="none" stroke-linecap="round" stroke-linejoin="round"'

APP_GLYPHS = {
    "files": '<path d="M13 17.5a2 2 0 0 1 2-2h6l2.2 2.4H33a2 2 0 0 1 2 2V31a2 2 0 0 1-2 2H15a2 2 0 0 1-2-2z"/>',
    "terminal": f'<path d="M14 18l6 6-6 6" {S} stroke-width="3"/><path d="M23 31h11" {S} stroke-width="3"/>',
    "settings": _gear(),
    "editor": f'<path d="M15 17h12M15 22h9M15 27h6" {S} stroke-width="2.4"/>'
              '<path d="M24.5 33.5l1-4.5 8.5-8.5 3.5 3.5-8.5 8.5z"/>',
    "calculator": '<rect x="15" y="12" width="18" height="24" rx="3" opacity=".35"/>'
                  '<rect x="17.5" y="14.5" width="13" height="5" rx="1.2"/>'
                  + "".join(f'<rect x="{17.5 + c * 4.6:.1f}" y="{22 + r * 4.4:.1f}" width="3.4" height="3.2" rx=".8"/>'
                            for r in range(3) for c in range(3)),
    "calendar": '<rect x="13" y="15" width="22" height="20" rx="3" opacity=".35"/>'
                '<path d="M13 18a3 3 0 0 1 3-3h16a3 3 0 0 1 3 3v3H13z"/>'
                '<rect x="17" y="12" width="2.4" height="6" rx="1.2"/><rect x="28.6" y="12" width="2.4" height="6" rx="1.2"/>'
                + "".join(f'<rect x="{16.5 + c * 5:.1f}" y="{24 + r * 4.6:.1f}" width="3.2" height="3" rx=".7"/>'
                          for r in range(2) for c in range(3)),
    "clocks": f'<circle cx="24" cy="24" r="11" {S} stroke-width="2.6"/><path d="M24 17v7.5l5 3" {S} stroke-width="2.6"/>',
    "weather": '<circle cx="20" cy="20" r="5.5" opacity=".8"/>'
               '<path d="M18 34a5 5 0 0 1 .6-9.97 7 7 0 0 1 13.2 2.2A4 4 0 0 1 31 34z"/>',
    "maps": '<path d="M24 36s-9-9.2-9-15a9 9 0 0 1 18 0c0 5.8-9 15-9 15z"/><circle cx="24" cy="21" r="3.4" fill="{bg}"/>',
    "images": '<rect x="12" y="14" width="24" height="20" rx="3" opacity=".35"/><circle cx="29" cy="20.5" r="2.6"/>'
              '<path d="M14.5 32l6.5-9 4.5 5.6 3-3.4 5 6.8z"/>',
    "videos": '<rect x="12" y="15" width="24" height="18" rx="4" opacity=".35"/><path d="M21 19.5v9l7.5-4.5z"/>',
    "music": '<path d="M30 13v14.5a3.8 3.8 0 1 1-2.4-3.5V18l-8 1.8v10.7a3.8 3.8 0 1 1-2.4-3.5V16.2z"/>',
    "software": '<path d="M14 19h20l-1.6 15.2a2 2 0 0 1-2 1.8H17.6a2 2 0 0 1-2-1.8z"/>'
                f'<path d="M19.5 22v-4a4.5 4.5 0 0 1 9 0v4" {S} stroke-width="2.4"/>',
    "monitor": f'<path d="M12 25h5l3-7 4.5 13 3.5-9 2 3h6" {S} stroke-width="2.8"/>',
    "disks": '<ellipse cx="24" cy="17" rx="10" ry="3.6"/><path d="M14 17v13c0 2 4.5 3.6 10 3.6S34 32 34 30V17'
             'c0 2-4.5 3.6-10 3.6S14 19 14 17z" opacity=".75"/>',
    "document": '<path d="M16 12h11l6 6v17a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 15 35V13a1 1 0 0 1 1-1z"/>'
                '<path d="M27 12v6h6" fill="{bg}" opacity=".35"/>'
                '<path d="M19 24h10M19 28h10M19 32h6" stroke="{bg}" stroke-width="1.8" stroke-linecap="round"/>',
    "contacts": '<circle cx="24" cy="19" r="5.5"/><path d="M13.5 35a10.5 10.5 0 0 1 21 0z"/>',
    "screenshot": f'<path d="M13 19v-4.5a1.5 1.5 0 0 1 1.5-1.5H19M29 13h4.5a1.5 1.5 0 0 1 1.5 1.5V19M35 29v4.5'
                  f'a1.5 1.5 0 0 1-1.5 1.5H29M19 35h-4.5a1.5 1.5 0 0 1-1.5-1.5V29" {S} stroke-width="2.6"/>'
                  '<circle cx="24" cy="24" r="4.2"/>',
    "web": f'<circle cx="24" cy="24" r="11" {S} stroke-width="2.4"/><ellipse cx="24" cy="24" rx="4.8" ry="11" {S} stroke-width="2"/>'
           f'<path d="M13.5 20.5h21M13.5 27.5h21" {S} stroke-width="2"/>',
    "mail": '<rect x="12" y="16" width="24" height="17" rx="3" opacity=".9"/>'
            '<path d="M13.5 18l10.5 8 10.5-8" stroke="{bg}" stroke-width="2.2" fill="none" stroke-linejoin="round"/>',
    "help": f'<circle cx="24" cy="24" r="11" {S} stroke-width="5"/>'
            '<path d="M16.2 16.2l3.6 3.6M31.8 16.2l-3.6 3.6M16.2 31.8l3.6-3.6M31.8 31.8l-3.6-3.6" stroke="{bg}" stroke-width="2.8"/>',
    "extensions": '<path d="M14 20h5a3 3 0 1 1 6 0h5v5a3 3 0 1 0 0 6v5H14v-5a3 3 0 1 1 0-6z"/>',
    "archive": '<rect x="13" y="15" width="22" height="20" rx="2.5" opacity=".9"/><rect x="12" y="13" width="24" height="5" rx="1.5"/>'
               '<rect x="21" y="21" width="6" height="3.5" rx="1" fill="{bg}"/>',
    "logs": f'<path d="M15 16h18M15 21h18M15 26h12M15 31h15" {S} stroke-width="2.6"/>',
    "boxes": '<path d="M24 12l10.5 6v12L24 36l-10.5-6V18z" opacity=".55"/><path d="M24 24l10.5-6L24 12l-10.5 6z"/>'
             '<path d="M24 24v12l-10.5-6V18z" opacity=".8"/>',
    "camera": '<path d="M13 19a2.5 2.5 0 0 1 2.5-2.5H19l1.8-2.5h6.4l1.8 2.5h3.5A2.5 2.5 0 0 1 35 19v12a2.5 2.5 0 0 1-2.5 2.5h-17'
              'A2.5 2.5 0 0 1 13 31z"/><circle cx="24" cy="25" r="5" fill="{bg}"/><circle cx="24" cy="25" r="3"/>',
}

# glyph, family, icon names
APPS = [
    ("files", "peach", ["org.gnome.Nautilus", "system-file-manager"]),
    ("terminal", "night", ["org.gnome.Ptyxis", "org.gnome.Console", "org.gnome.Terminal", "utilities-terminal"]),
    ("settings", "violet", ["org.gnome.Settings", "preferences-system", "preferences-desktop"]),
    ("editor", "mauve", ["org.gnome.TextEditor", "accessories-text-editor", "org.gnome.gedit"]),
    ("calculator", "dusk", ["org.gnome.Calculator", "accessories-calculator"]),
    ("calendar", "coral", ["org.gnome.Calendar"]),
    ("clocks", "violet", ["org.gnome.clocks"]),
    ("weather", "peach", ["org.gnome.Weather"]),
    ("maps", "coral", ["org.gnome.Maps"]),
    ("images", "pink", ["org.gnome.Loupe", "org.gnome.eog", "image-viewer"]),
    ("videos", "night", ["org.gnome.Showtime", "org.gnome.Totem"]),
    ("music", "pink", ["org.gnome.Music", "org.gnome.Decibels"]),
    ("software", "coral", ["org.gnome.Software", "system-software-install"]),
    ("monitor", "night", ["org.gnome.SystemMonitor", "utilities-system-monitor"]),
    ("disks", "dusk", ["org.gnome.DiskUtility"]),
    ("document", "mauve", ["org.gnome.Papers", "org.gnome.Evince"]),
    ("contacts", "violet", ["org.gnome.Contacts"]),
    ("screenshot", "dusk", ["org.gnome.Screenshot", "applets-screenshooter"]),
    ("web", "violet", ["org.gnome.Epiphany", "web-browser"]),
    ("mail", "coral", ["org.gnome.Geary"]),
    ("help", "pink", ["org.gnome.Yelp", "help-browser"]),
    ("extensions", "mauve", ["org.gnome.Extensions"]),
    ("archive", "peach", ["org.gnome.FileRoller"]),
    ("logs", "night", ["org.gnome.Logs"]),
    ("boxes", "dusk", ["org.gnome.Boxes"]),
    ("camera", "night", ["org.gnome.Snapshot"]),
]


def app_svg(glyph, fam, version):
    top, bottom = FAM[fam]
    edge = ".16" if fam == "night" else "0"
    g = APP_GLYPHS[glyph].format(c=SOFT, bg=bottom)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} app icon - original artwork, CC-BY-SA-4.0 -->
<defs><linearGradient id="t" x1="0" y1="4" x2="0" y2="44" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<clipPath id="c"><rect x="4" y="4" width="40" height="40" rx="10"/></clipPath></defs>
<rect x="4" y="4" width="40" height="40" rx="10" fill="url(#t)"/>
<g clip-path="url(#c)"><rect x="4" y="4" width="40" height="1.4" fill="#FFFFFF" opacity=".4"/>
<rect x="4" y="42.4" width="40" height="1.6" fill="{PLUM}" opacity=".2"/></g>
<rect x="4.5" y="4.5" width="39" height="39" rx="9.5" fill="none" stroke="#FFFFFF" stroke-opacity="{edge}"/>
<g fill="{SOFT}" opacity=".95">{g}</g>
</svg>
"""


# ---- devices and the bin -------------------------------------------------------
def _obj(body, version, kind):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} {kind} icon - original artwork, CC-BY-SA-4.0 -->
{body}
</svg>
"""


def trash_svg(full, version):
    paper = ('<path d="M16.5 14.5l4-5 5 3 4-4 3.5 6z" fill="#FEFCFC" opacity=".95"/>'
             '<path d="M20.5 9.5l5 3" stroke="#C48FBA" stroke-width="1.2"/>') if full else ""
    return _obj(f"""<defs><linearGradient id="t" x1="0" y1="14" x2="0" y2="42" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#B9B2E3"/><stop offset="1" stop-color="#6C64A3"/></linearGradient></defs>
{paper}
<rect x="10" y="12" width="28" height="4.6" rx="2.3" fill="#C48FBA"/>
<rect x="20" y="9" width="8" height="4" rx="1.5" fill="#C48FBA"/>
<path d="M12.5 17h23l-2 23.2a2.5 2.5 0 0 1-2.5 2.3H17a2.5 2.5 0 0 1-2.5-2.3z" fill="url(#t)"/>
<path d="M19.5 21.5v16M24 21.5v16M28.5 21.5v16" stroke="#FEFCFC" stroke-width="2" stroke-linecap="round" opacity=".75"/>""",
                version, "bin")


def drive_svg(kind, version):
    if kind == "harddisk":
        body = """<defs><linearGradient id="t" x1="0" y1="14" x2="0" y2="38" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#B9B2E3"/><stop offset="1" stop-color="#6C64A3"/></linearGradient></defs>
<rect x="6" y="14" width="36" height="22" rx="4" fill="url(#t)"/>
<rect x="6" y="28" width="36" height="8" rx="3" fill="#252239" opacity=".35"/>
<circle cx="35" cy="32" r="1.8" fill="#F9C8B2"/><path d="M11 32h14" stroke="#FEFCFC" stroke-width="1.6" stroke-linecap="round" opacity=".7"/>"""
    elif kind == "removable":
        body = """<defs><linearGradient id="t" x1="0" y1="10" x2="0" y2="40" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#F4A79A"/><stop offset="1" stop-color="#EA5148"/></linearGradient></defs>
<rect x="18" y="6" width="12" height="9" rx="1.5" fill="#CEC9EA"/><rect x="21" y="9" width="2" height="2.5" fill="#6C64A3"/><rect x="25" y="9" width="2" height="2.5" fill="#6C64A3"/>
<rect x="14" y="14" width="20" height="28" rx="4" fill="url(#t)"/>
<circle cx="24" cy="34" r="2" fill="#FEFCFC" opacity=".85"/>"""
    else:  # optical
        body = """<defs><linearGradient id="t" x1="0" y1="8" x2="0" y2="40" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#FAD3C0"/><stop offset=".5" stop-color="#EFA1A1"/><stop offset="1" stop-color="#857DB5"/></linearGradient></defs>
<circle cx="24" cy="24" r="17" fill="url(#t)"/><circle cx="24" cy="24" r="5.5" fill="#FEFCFC"/><circle cx="24" cy="24" r="2.4" fill="#857DB5"/>
<path d="M14 15a13 13 0 0 1 9-4.5" stroke="#FEFCFC" stroke-width="1.6" stroke-linecap="round" fill="none" opacity=".7"/>"""
    return _obj(body, version, "drive")


DEVICES = {
    "user-trash": ("places", lambda v: trash_svg(False, v)),
    "user-trash-full": ("places", lambda v: trash_svg(True, v)),
    "drive-harddisk": ("devices", lambda v: drive_svg("harddisk", v)),
    "drive-harddisk-solidstate": ("devices", lambda v: drive_svg("harddisk", v)),
    "drive-removable-media": ("devices", lambda v: drive_svg("removable", v)),
    "drive-removable-media-usb": ("devices", lambda v: drive_svg("removable", v)),
    "media-removable": ("devices", lambda v: drive_svg("removable", v)),
    "drive-optical": ("devices", lambda v: drive_svg("optical", v)),
    "media-optical": ("devices", lambda v: drive_svg("optical", v)),
}

# ---- file types -----------------------------------------------------------------
FILE_GLYPHS = {
    "text": f'<path d="M17 25h14M17 29h14M17 33h9" {S} stroke-width="2"/>',
    "script": f'<path d="M19 26l-3.5 3.5L19 33M29 26l3.5 3.5L29 33M25.5 25l-3 9" {S} stroke-width="2"/>',
    "html": f'<circle cx="24" cy="29.5" r="6" {S} stroke-width="1.8"/><path d="M18 29.5h12M24 23.5c-2.5 3.5-2.5 8.5 0 12M24 23.5c2.5 3.5 2.5 8.5 0 12" {S} stroke-width="1.5"/>',
    "pdf": '<path d="M16 27h16v8H16z" opacity=".25"/><path d="M18.5 33v-4.5h2a1.3 1.3 0 0 1 0 2.6h-2M23.5 33v-4.5h1.5a2 2 0 0 1 0 4.5zM28.5 33v-4.5h3M28.5 30.8h2.4" stroke="{c}" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "image": '<circle cx="28.5" cy="25.5" r="2"/><path d="M16 35l5-7 3.5 4.3 2.5-2.8 5 5.5z"/>',
    "audio": '<path d="M29 22v9.5a2.8 2.8 0 1 1-1.8-2.6V25l-6 1.4v7.1a2.8 2.8 0 1 1-1.8-2.6v-7.2z"/>',
    "video": '<path d="M21 24.5v10l8-5z"/>',
    "archive": '<path d="M22.5 21h3v2h-3zM22.5 25h3v2h-3zM22.5 29h3v2h-3z"/><rect x="21.5" y="32" width="5" height="4" rx="1"/>',
    "document": f'<path d="M17 24h14M17 28h14M17 32h14M17 36h8" {S} stroke-width="1.8"/>',
    "spreadsheet": f'<rect x="16.5" y="23.5" width="15" height="12" rx="1" {S} stroke-width="1.6"/><path d="M16.5 27.5h15M16.5 31.5h15M21.5 23.5v12M26.5 23.5v12" {S} stroke-width="1.4"/>',
    "presentation": '<rect x="16" y="23" width="16" height="10" rx="1.5" opacity=".35"/><path d="M19 30.5l3-3 2.5 2 4-4"/><rect x="23" y="33" width="2" height="3"/>',
    "executable": _gear(24, 29.5, 6.5, 4.8, 6, 2).replace("<path", "<path"),
    "font": f'<path d="M18 35l6-13 6 13M20.3 30.5h7.4" {S} stroke-width="2.2"/>',
}

FILES = {
    # family colour (top, bottom), names
    "text": (("#DDB6D5", "#A77091"), ["text-x-generic", "text-plain"]),
    "script": (("#4B4670", "#252239"), ["text-x-script", "application-x-shellscript", "text-x-python", "text-x-python3",
                                        "application-javascript", "text-x-csrc", "text-x-c++src", "application-json"]),
    "html": (("#B9B2E3", "#6C64A3"), ["text-html", "application-xhtml+xml"]),
    "pdf": (("#F4A79A", "#EA5148"), ["application-pdf"]),
    "image": (("#FAD3C0", "#F2A98F"), ["image-x-generic", "image-png", "image-jpeg", "image-gif", "image-webp",
                                       "image-svg+xml", "image-bmp", "image-tiff"]),
    "audio": (("#F5B3A8", "#E58C8C"), ["audio-x-generic", "audio-mpeg", "audio-flac", "audio-x-wav", "audio-ogg",
                                       "audio-x-vorbis+ogg", "audio-mp4"]),
    "video": (("#B9A9DA", "#857DB5"), ["video-x-generic", "video-mp4", "video-x-matroska", "video-webm", "video-quicktime"]),
    "archive": (("#FAD3C0", "#C48FBA"), ["package-x-generic", "application-zip", "application-x-tar",
                                         "application-x-compressed-tar", "application-x-7z-compressed", "application-x-xz",
                                         "application-x-xz-compressed-tar", "application-x-rar", "application-gzip"]),
    "document": (("#B9B2E3", "#857DB5"), ["x-office-document", "application-vnd.oasis.opendocument.text",
                                          "application-vnd.openxmlformats-officedocument.wordprocessingml.document",
                                          "application-msword", "application-rtf"]),
    "spreadsheet": (("#A9D8B8", "#3B9564"), ["x-office-spreadsheet", "application-vnd.oasis.opendocument.spreadsheet",
                                             "application-vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                             "application-vnd.ms-excel", "text-csv"]),
    "presentation": (("#F9C8B2", "#EA5148"), ["x-office-presentation", "application-vnd.oasis.opendocument.presentation",
                                              "application-vnd.openxmlformats-officedocument.presentationml.presentation",
                                              "application-vnd.ms-powerpoint"]),
    "executable": (("#C48FBA", "#857DB5"), ["application-x-executable", "application-x-sharedlib", "application-x-object"]),
    "font": (("#DDB6D5", "#857DB5"), ["font-x-generic", "font-ttf", "font-otf", "application-x-font-ttf"]),
}


def file_svg(kind, version):
    (top, bottom), _ = FILES[kind]
    g = FILE_GLYPHS[kind].format(c=SOFT)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} file-type icon - original artwork, CC-BY-SA-4.0 -->
<defs><linearGradient id="p" x1="0" y1="4" x2="0" y2="44" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>
<path d="M11.5 4.5h17l9 9v28a2 2 0 0 1-2 2h-24a2 2 0 0 1-2-2v-35a2 2 0 0 1 2-2z" fill="url(#p)"/>
<path d="M28.5 4.5v7a2 2 0 0 0 2 2h7z" fill="#FFFFFF" opacity=".45"/>
<rect x="9.5" y="42" width="28" height="1.5" rx=".75" fill="{PLUM}" opacity=".18"/>
<g fill="{SOFT}" opacity=".95">{g}</g>
</svg>
"""


def write_all(write, base, version):
    """Write every app, device and file-type icon into icon theme `base`."""
    n = 0
    for glyph, fam, names in APPS:
        svg = app_svg(glyph, fam, version)
        for nm in names:
            write(base / "apps/scalable" / f"{nm}.svg", svg); n += 1
    for nm, (ctx, fn) in DEVICES.items():
        write(base / f"{ctx}/scalable" / f"{nm}.svg", fn(version)); n += 1
    for kind, (_, names) in FILES.items():
        svg = file_svg(kind, version)
        for nm in names:
            write(base / "mimetypes/scalable" / f"{nm}.svg", svg); n += 1
    return n
