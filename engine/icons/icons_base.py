"""Vice Horizon's original folder icons (from its generate.py: GLYPHS, FOLDERS, folder_svg), vendored.

Original artwork, CC-BY-SA-4.0. Loaded by engine/parts/icons.py with the pack's colours swapped in.
"""
VERSION = ""


def mix(a, b, t):
    """t = share of b (Vice Horizon's rounding)."""
    ra, rb = (tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for c in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))


LAUNCHER_SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512)

GLYPHS = {
    "none": "",
    "home": '<path d="M24 22.5 15.5 29.5V38h6v-5.5h5V38h6v-8.5z" />',
    "documents": '<path d="M18 21h9l4 4v13H18z" opacity=".95"/><path d="M20.5 28.5h8M20.5 31.5h8M20.5 34.5h5.5" stroke="{g2}" stroke-width="1.4" stroke-linecap="round" fill="none"/>',
    "download": '<path d="M22.6 20.5h2.8v8.3h3.6L24 34l-5-5.2h3.6z"/><rect x="17" y="35.5" width="14" height="2.6" rx="1.3"/>',
    "music": '<path d="M28.5 20.5v11.7a3.3 3.3 0 1 1-2-3V24l-6 1.4v9.2a3.3 3.3 0 1 1-2-3V23.2z"/>',
    "pictures": '<circle cx="28.5" cy="24.5" r="2.4"/><path d="M16.5 37 21.5 29.3l3.3 4.2 2.4-2.7L31.5 37z"/>',
    "videos": '<rect x="16" y="22" width="16" height="15" rx="3" opacity=".35"/><path d="M21.5 25.3v8.4l7-4.2z"/>',
    "desktop": '<rect x="16" y="22" width="16" height="11" rx="1.8"/><rect x="21.5" y="34" width="5" height="2"/><rect x="19" y="35.8" width="10" height="1.8" rx=".9"/>',
    "templates": '<rect x="17" y="22" width="6" height="6" rx="1.2"/><rect x="25" y="22" width="6" height="6" rx="1.2"/><rect x="17" y="30" width="6" height="6" rx="1.2"/><rect x="25" y="30" width="6" height="6" rx="1.2" opacity=".55"/>',
    "share": '<circle cx="30" cy="23.5" r="2.6"/><circle cx="18.5" cy="29.5" r="2.6"/><circle cx="30" cy="35" r="2.6"/><path d="M20.8 28.3 27.7 24.7M20.8 30.7l6.9 3.6" stroke="{glyph}" stroke-width="1.8" fill="none"/>',
    "projects": '<path d="M20.5 23.5 15.5 29.5l5 6M27.5 23.5l5 6-5 6" stroke="{glyph}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
}

FOLDERS = {
    # name: (front top, front bottom, back, glyph)
    "folder": ("#F9C8B2", "#EFA1A1", "#C48FBA", "none"),
    "folder-open": ("#F9C8B2", "#EFA1A1", "#C48FBA", "none"),
    "user-home": ("#A79FD4", "#857DB5", "#6C64A3", "home"),
    "folder-home": ("#A79FD4", "#857DB5", "#6C64A3", "home"),
    "folder-documents": ("#D7AACD", "#A77091", "#857DB5", "documents"),
    "folder-download": ("#F4A79A", "#EA5148", "#A77091", "download"),
    "folder-downloads": ("#F4A79A", "#EA5148", "#A77091", "download"),
    "folder-music": ("#F5B3A8", "#EFA1A1", "#C48FBA", "music"),
    "folder-pictures": ("#FAD3C0", "#F2A98F", "#EFA1A1", "pictures"),
    "folder-images": ("#FAD3C0", "#F2A98F", "#EFA1A1", "pictures"),
    "folder-videos": ("#B9A9DA", "#857DB5", "#A77091", "videos"),
    "folder-video": ("#B9A9DA", "#857DB5", "#A77091", "videos"),
    "user-desktop": ("#A79FD4", "#6C64A3", "#A77091", "desktop"),
    "folder-desktop": ("#A79FD4", "#6C64A3", "#A77091", "desktop"),
    "folder-templates": ("#DDB6D5", "#C48FBA", "#A77091", "templates"),
    "folder-publicshare": ("#DDB6D5", "#C48FBA", "#857DB5", "share"),
    "folder-public": ("#DDB6D5", "#C48FBA", "#857DB5", "share"),
    "folder-projects": ("#C3B8E6", "#857DB5", "#C48FBA", "projects"),
    "folder-development": ("#C3B8E6", "#857DB5", "#C48FBA", "projects"),
}


def folder_svg(top, bottom, back, glyph, version=VERSION):
    glyph_col = "#FEFCFC"
    g = GLYPHS[glyph].format(glyph=glyph_col, g2=bottom)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} folder icon - original artwork, CC-BY-SA-4.0 -->
<defs>
<linearGradient id="f" x1="0" y1="14" x2="0" y2="42" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<linearGradient id="b" x1="0" y1="6" x2="0" y2="20" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{mix(back, '#FFFFFF', 0.12)}"/><stop offset="1" stop-color="{back}"/></linearGradient>
</defs>
<path d="M7.5 9.5A2.5 2.5 0 0 1 10 7h9.2a2.5 2.5 0 0 1 1.9.9L23.4 10.5H38a2.5 2.5 0 0 1 2.5 2.5V20h-33z" fill="url(#b)"/>
<rect x="5" y="13.5" width="38" height="28.5" rx="3.2" fill="url(#f)"/>
<rect x="5" y="13.5" width="38" height="1.3" rx=".6" fill="#FFFFFF" opacity=".45"/>
<rect x="5" y="40.6" width="38" height="1.4" rx=".7" fill="#2F1F2B" opacity=".18"/>
<g fill="{glyph_col}" opacity=".93">{g}</g>
</svg>
"""


LAUNCHER_SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512)


