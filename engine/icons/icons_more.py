"""Vice Horizon icon set, second part (original artwork, CC-BY-SA-4.0).

Adds what makes the set complete for KDE Plasma, matching Waypoint's coverage:
  - about 80 folder types (git, cloud, games, locked, ...) and a -symbolic version of every folder
  - the KDE apps (Dolphin, Konsole, Kate, Okular, Discover, ...) and the application-menu categories
  - more drives and devices, and more file types (packages, disc images, databases, e-books, ...)

Every symbol is drawn once in a 24 x 24 box (G24) and placed into a folder, an app tile or a file
page by a transform, so the same symbol looks the same everywhere. The app symbols from
icons_extra.py are reused through "app:<name>". Symbols are generic pictures of what a folder or
app is for: no third-party logos are reproduced (a Git folder shows a branch, an Android folder a
phone, and so on). Imported by generate.py (gen_icons).
"""
import icons_extra as X

SOFT, PLUM = X.SOFT, X.PLUM
ST = 'stroke="{c}" fill="none" stroke-linecap="round" stroke-linejoin="round"'


def _app(name):   # an icons_extra app symbol (drawn in 12..36) moved into the 24 box
    return f'<g transform="translate(-12 -12)">{X.APP_GLYPHS[name]}</g>'


G24 = {
    "star": '<path d="M12 2.2l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17l-5.9 3.3 1.3-6.6L2.5 9.1l6.6-.8z"/>',
    "heart": '<path d="M12 20.5S3 15 3 8.8A4.6 4.6 0 0 1 12 6.6a4.6 4.6 0 0 1 9 2.2c0 6.2-9 11.7-9 11.7z"/>',
    "bookmark": '<path d="M6 2.5h12a1 1 0 0 1 1 1v18l-7-5-7 5v-18a1 1 0 0 1 1-1z"/>',
    "book": '<path d="M2.5 4.5c3.4-1.2 6.6-1 9 1v15c-2.4-1.8-5.6-2.1-9-1z"/><path d="M21.5 4.5c-3.4-1.2-6.6-1-9 1v15c2.4-1.8 5.6-2.1 9-1z" opacity=".7"/>',
    "library": '<rect x="2.5" y="4" width="4.2" height="17" rx="1"/><rect x="8" y="2.5" width="4.2" height="18.5" rx="1" opacity=".8"/>'
               '<path d="M14.2 5.2l3.9-1.1 4.4 15.5-3.9 1.1z" opacity=".65"/>',
    "cloud": '<path d="M7 19.5a5 5 0 0 1-.7-9.96 7 7 0 0 1 13.4 1.1A4.5 4.5 0 0 1 18.5 19.5z"/>',
    "cloud-up": '<path d="M7 19.5a5 5 0 0 1-.7-9.96 7 7 0 0 1 13.4 1.1A4.5 4.5 0 0 1 18.5 19.5z"/>'
                '<path d="M12 17.5v-6M9.2 14l2.8-2.8 2.8 2.8" stroke="{bg}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "cloud-sync": '<path d="M7 19.5a5 5 0 0 1-.7-9.96 7 7 0 0 1 13.4 1.1A4.5 4.5 0 0 1 18.5 19.5z"/>'
                  '<path d="M8.8 14.5a3.3 3.3 0 0 1 5.9-1.6M15.2 14.5a3.3 3.3 0 0 1-5.9 1.6" stroke="{bg}" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
    "lock": f'<path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" {ST} stroke-width="2.4"/><rect x="4.5" y="10" width="15" height="11.5" rx="2.4"/>'
            '<circle cx="12" cy="15" r="1.7" fill="{bg}"/><rect x="11.2" y="15.5" width="1.6" height="3" rx=".8" fill="{bg}"/>',
    "unlock": f'<path d="M8 10.5V7.5a4 4 0 0 1 7.7-1.6" {ST} stroke-width="2.4"/><rect x="4.5" y="10" width="15" height="11.5" rx="2.4"/>'
              '<circle cx="12" cy="15" r="1.7" fill="{bg}"/><rect x="11.2" y="15.5" width="1.6" height="3" rx=".8" fill="{bg}"/>',
    "database": '<ellipse cx="12" cy="5.5" rx="8.5" ry="3.2"/>'
                '<path d="M3.5 8c0 1.8 3.8 3.2 8.5 3.2s8.5-1.4 8.5-3.2v4c0 1.8-3.8 3.2-8.5 3.2S3.5 13.8 3.5 12z" opacity=".85"/>'
                '<path d="M3.5 14.5c0 1.8 3.8 3.2 8.5 3.2s8.5-1.4 8.5-3.2v4c0 1.8-3.8 3.2-8.5 3.2s-8.5-1.4-8.5-3.2z" opacity=".7"/>',
    "chart": '<rect x="3" y="12" width="4.5" height="9" rx="1"/><rect x="9.75" y="5" width="4.5" height="16" rx="1"/>'
             '<rect x="16.5" y="9" width="4.5" height="12" rx="1" opacity=".75"/>',
    "pie": '<path d="M11 3.1A9 9 0 1 0 20.9 13H11z"/><path d="M13 1.5A9.5 9.5 0 0 1 22.5 11H13z" opacity=".7"/>',
    "table": f'<rect x="3" y="4" width="18" height="16" rx="2" {ST} stroke-width="2"/><path d="M3 9.5h18M3 14.8h18M9 4v16M15 4v16" {ST} stroke-width="1.6"/>',
    "gear": X._gear(12, 12, 10, 7.4, 8, 3.1),
    "wrench": '<path d="M15.8 2.6a5.4 5.4 0 0 0-5 7.3L3.3 17.4a2.2 2.2 0 0 0 3.1 3.1l7.5-7.5a5.4 5.4 0 0 0 7.3-5l-3.3 3.3-3-.8-.8-3z"/>',
    "hammer": '<path d="M5.5 3.5h9l2.5 2.5v3h-4.5v-2H8z"/><path d="M11 9h3.5v12a1.75 1.75 0 0 1-3.5 0z" opacity=".85"/>',
    "code": f'<path d="M8 6.5L2.8 12 8 17.5M16 6.5l5.2 5.5-5.2 5.5" {ST} stroke-width="2.6"/><path d="M13.8 4.5l-3.6 15" {ST} stroke-width="2.2" opacity=".75"/>',
    "terminal": f'<path d="M4 6.5l5.5 5.5L4 17.5M12.5 18.5H20" {ST} stroke-width="2.6"/>',
    "braces": f'<path d="M9 3.5c-2.6 0-3 1.6-3 3.6v1.7c0 1.6-.6 2.7-2.3 3.2 1.7.5 2.3 1.6 2.3 3.2v1.7c0 2 .4 3.6 3 3.6'
              f'M15 3.5c2.6 0 3 1.6 3 3.6v1.7c0 1.6.6 2.7 2.3 3.2-1.7.5-2.3 1.6-2.3 3.2v1.7c0 2-.4 3.6-3 3.6" {ST} stroke-width="2.2"/>',
    "branch": f'<path d="M7 6.8v10.4M17 9.8c0 4.4-10 3.4-10 7.4" {ST} stroke-width="2.2"/>'
              '<circle cx="7" cy="4.8" r="2.6"/><circle cx="7" cy="19.2" r="2.6"/><circle cx="17" cy="7.6" r="2.6"/>',
    "box": '<path d="M12 2l9 5v10l-9 5-9-5V7z" opacity=".55"/><path d="M12 12l9-5-9-5-9 5z"/><path d="M12 12v10l-9-5V7z" opacity=".8"/>',
    "containers": '<rect x="3" y="12" width="5.2" height="4.4" rx=".8"/><rect x="9.4" y="12" width="5.2" height="4.4" rx=".8"/>'
                  '<rect x="15.8" y="12" width="5.2" height="4.4" rx=".8"/><rect x="6.2" y="6.6" width="5.2" height="4.4" rx=".8" opacity=".8"/>'
                  '<rect x="12.6" y="6.6" width="5.2" height="4.4" rx=".8" opacity=".8"/><path d="M2 18h20l-1.6 2.6a2 2 0 0 1-1.7.9H5.3a2 2 0 0 1-1.7-.9z" opacity=".65"/>',
    "phone": '<rect x="6.5" y="2" width="11" height="20" rx="2.6"/><rect x="10" y="18.3" width="4" height="1.5" rx=".75" fill="{bg}"/>'
             '<rect x="8.4" y="4.4" width="7.2" height="12" rx=".8" fill="{bg}" opacity=".35"/>',
    "laptop": '<rect x="4" y="4.5" width="16" height="11.5" rx="1.6"/><rect x="6" y="6.5" width="12" height="7.5" rx=".6" fill="{bg}" opacity=".35"/>'
              '<path d="M1.5 17.5h21v1a2 2 0 0 1-2 2h-17a2 2 0 0 1-2-2z" opacity=".85"/>',
    "monitor": '<rect x="2" y="3.5" width="20" height="13" rx="2"/><rect x="4" y="5.5" width="16" height="9" rx=".8" fill="{bg}" opacity=".35"/>'
               '<rect x="10" y="16.5" width="4" height="2.8"/><rect x="7" y="19" width="10" height="2" rx="1"/>',
    "remote": '<rect x="2" y="3.5" width="20" height="13" rx="2"/><rect x="10" y="16.5" width="4" height="2.8"/><rect x="7" y="19" width="10" height="2" rx="1"/>'
              '<path d="M8 12.5l7-6M10.5 6.5H15v4.5" stroke="{bg}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "window": f'<rect x="2.5" y="4" width="19" height="16" rx="2.4" {ST} stroke-width="2"/><path d="M2.5 6.4a2.4 2.4 0 0 1 2.4-2.4h14.2a2.4 2.4 0 0 1 2.4 2.4V9h-19z"/>'
              '<circle cx="5.6" cy="6.5" r=".9" fill="{bg}"/><circle cx="8.4" cy="6.5" r=".9" fill="{bg}"/>',
    "gamepad": '<path d="M7.2 7h9.6a5.2 5.2 0 0 1 5.1 6.2l-.9 4.4a2.4 2.4 0 0 1-4.1 1.1L14.8 16.5H9.2l-2.1 2.2a2.4 2.4 0 0 1-4.1-1.1l-.9-4.4A5.2 5.2 0 0 1 7.2 7z"/>'
               '<path d="M7.8 9.6v4M5.8 11.6h4" stroke="{bg}" stroke-width="1.8" stroke-linecap="round"/>'
               '<circle cx="16" cy="10.4" r="1.15" fill="{bg}"/><circle cx="18" cy="12.6" r="1.15" fill="{bg}"/>',
    "globe": f'<circle cx="12" cy="12" r="9.5" {ST} stroke-width="2"/><ellipse cx="12" cy="12" rx="4.1" ry="9.5" {ST} stroke-width="1.7"/>'
             f'<path d="M3 9h18M3 15h18" {ST} stroke-width="1.7"/>',
    "person": '<circle cx="12" cy="7.5" r="4.5"/><path d="M3.5 21a8.5 8.5 0 0 1 17 0z"/>',
    "people": '<circle cx="9" cy="8" r="3.8"/><path d="M2 20a7 7 0 0 1 14 0z"/><circle cx="16.5" cy="7" r="3" opacity=".7"/><path d="M15.8 12.6A6.5 6.5 0 0 1 22 19h-4.6a8.4 8.4 0 0 0-1.6-6.4z" opacity=".7"/>',
    "exclaim": '<circle cx="12" cy="12" r="10"/><rect x="10.7" y="5.5" width="2.6" height="8.5" rx="1.3" fill="{bg}"/><circle cx="12" cy="17.3" r="1.5" fill="{bg}"/>',
    "warning": '<path d="M10.3 3.3a2 2 0 0 1 3.4 0l8.4 15a2 2 0 0 1-1.7 3H3.6a2 2 0 0 1-1.7-3z"/>'
               '<rect x="10.8" y="8.5" width="2.4" height="6.5" rx="1.2" fill="{bg}"/><circle cx="12" cy="18" r="1.4" fill="{bg}"/>',
    "puzzle": '<path d="M2 6h5a3 3 0 1 1 6 0h5v5a3 3 0 1 0 0 6v5H2v-5a3 3 0 1 1 0-6z"/>',
    "mail": '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M3.6 7.2l8.4 6.4 8.4-6.4" stroke="{bg}" stroke-width="2" fill="none" stroke-linejoin="round"/>',
    "network": f'<path d="M12 6.5L5.5 17M12 6.5L18.5 17M6 18.5h12" {ST} stroke-width="1.9"/>'
               '<circle cx="12" cy="5" r="3"/><circle cx="5" cy="18.5" r="3"/><circle cx="19" cy="18.5" r="3"/>',
    "note": '<path d="M4 3.5h16a.5.5 0 0 1 .5.5v11L15 20.5H4a.5.5 0 0 1-.5-.5V4a.5.5 0 0 1 .5-.5z"/>'
            '<path d="M15 20.5V15.5a.5.5 0 0 1 .5-.5h5" fill="{bg}" opacity=".45"/>'
            '<path d="M7 8h10M7 11.5h7" stroke="{bg}" stroke-width="1.7" stroke-linecap="round"/>',
    "brush": '<path d="M20 2.6a1.7 1.7 0 0 1 2.4 2.4l-9.3 10-3.1-3.1z"/>'
             '<path d="M9.2 13.2l3.1 3.1c-.4 3.4-3.6 6-8.8 4.9 1.8-1.3 1.5-4 2.5-6a3.1 3.1 0 0 1 3.2-2z" opacity=".85"/>',
    "pencil": '<path d="M16 2.8l5.2 5.2L9 20.2 3.2 21.1l.9-5.8z"/><path d="M13.6 5.2l5.2 5.2" stroke="{bg}" stroke-width="1.6"/>',
    "nib": '<path d="M12 2.5l6.5 7.3-2.3 8.7H7.8L5.5 9.8z"/><path d="M12 3v7.4" stroke="{bg}" stroke-width="1.4"/>'
           '<circle cx="12" cy="11.4" r="1.7" fill="{bg}"/><rect x="7.3" y="19.3" width="9.4" height="2.6" rx="1"/>',
    "mic": f'<rect x="8.8" y="2" width="6.4" height="12.4" rx="3.2"/><path d="M5.2 11a6.8 6.8 0 0 0 13.6 0M12 18v3.2M8.5 21.4h7" {ST} stroke-width="2"/>',
    "easel": '<rect x="2.5" y="3" width="19" height="12.5" rx="1.6"/>'
             '<path d="M6 12l3.4-3.4 2.6 2 4.6-4.6" stroke="{bg}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path d="M12 15.5v2.8M7.8 21.5l4.2-3.2 4.2 3.2" {ST} stroke-width="2"/>',
    "printer": '<rect x="6.5" y="2.5" width="11" height="5.5" rx=".8" opacity=".75"/><rect x="2" y="8" width="20" height="9.5" rx="2.2"/>'
               '<rect x="6.5" y="14" width="11" height="7.5" rx=".8" opacity=".9"/><circle cx="18.2" cy="11" r="1" fill="{bg}"/>'
               '<path d="M8.8 17h6.4M8.8 19.3h4.4" stroke="{bg}" stroke-width="1.2" stroke-linecap="round"/>',
    "clock": f'<circle cx="12" cy="12" r="9.5" {ST} stroke-width="2.2"/><path d="M12 6.5V12l3.8 2.5" {ST} stroke-width="2.2"/>',
    "history": f'<path d="M4.2 13A8 8 0 1 0 6 6.6" {ST} stroke-width="2.2"/><path d="M3.3 3.8v4.4h4.4" {ST} stroke-width="2.2"/>'
               f'<path d="M12 8v4.5l3 2" {ST} stroke-width="2"/>',
    "shield": '<path d="M12 2l8.5 3.2v6.2c0 5.2-3.6 9.4-8.5 10.9-4.9-1.5-8.5-5.7-8.5-10.9V5.2z"/>'
              '<path d="M8.2 12.2l2.6 2.6 5-5.2" stroke="{bg}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "sign": f'<path d="M3 15.5c1.8-5 4-8.4 5-7.6 1.2 1-2.2 8.4.2 8.4 1.7 0 2.8-5.2 4.6-5.2 1.3 0 .4 3.8 2.3 3.8 1.3 0 2.1-1.7 5.4-1.7" {ST} stroke-width="2"/>'
            f'<path d="M3 20.5h18" {ST} stroke-width="1.8" opacity=".7"/>',
    "speaker": '<path d="M3.5 9h4l5.5-4.8v15.6L7.5 15h-4a.5.5 0 0 1-.5-.5v-5a.5.5 0 0 1 .5-.5z"/>'
               f'<path d="M16.2 9a4.2 4.2 0 0 1 0 6M18.8 6.4a8 8 0 0 1 0 11.2" {ST} stroke-width="2"/>',
    "zip": '<rect x="4" y="2.5" width="16" height="19" rx="2.4"/>'
           '<path d="M11 4.5h2v2h-2zM11 8.5h2v2h-2zM13 6.5h-2M13 10.5h-2" fill="{bg}"/>'
           '<rect x="10.8" y="4.5" width="2.4" height="2" fill="{bg}"/><rect x="10.8" y="8.5" width="2.4" height="2" fill="{bg}"/>'
           '<rect x="9.8" y="12.5" width="4.4" height="5" rx="1.1" fill="{bg}"/>',
    "hourglass": '<path d="M6 2.5h12v2.2c0 3.2-3.4 5.3-4.4 7.3 1 2 4.4 4.1 4.4 7.3v2.2H6v-2.2c0-3.2 3.4-5.3 4.4-7.3C9.4 10 6 7.9 6 4.7z"/>'
                 '<path d="M8.8 19.2c0-1.8 1.8-3 3.2-3.8 1.4.8 3.2 2 3.2 3.8z" fill="{bg}" opacity=".6"/>',
    "lines": f'<path d="M4 5.5h16M4 10h16M4 14.5h16M4 19h10" {ST} stroke-width="2.2"/>',
    "markdown": f'<rect x="1.8" y="5" width="20.4" height="14" rx="2.4" {ST} stroke-width="1.9"/>'
                f'<path d="M5.2 15.5v-7l2.9 3.4 2.9-3.4v7M16.5 8.5v6.6M14 13l2.5 2.6L19 13" {ST} stroke-width="1.9"/>',
    "bin": '<rect x="4" y="4.5" width="16" height="2.6" rx="1.3"/><rect x="9.5" y="2.5" width="5" height="2.6" rx="1"/>'
           '<path d="M5.5 8h13l-1.2 12a1.8 1.8 0 0 1-1.8 1.6h-7a1.8 1.8 0 0 1-1.8-1.6z"/>'
           '<path d="M10 11v7.5M14 11v7.5" stroke="{bg}" stroke-width="1.6" stroke-linecap="round"/>',
    "image": '<rect x="2" y="4" width="20" height="16" rx="2.6" opacity=".4"/><circle cx="16.5" cy="9" r="2.2"/><path d="M4 18.5l5.2-7.2 3.6 4.5 2.4-2.7 4.8 5.4z"/>',
    "play": '<rect x="2" y="4.5" width="20" height="15" rx="3.4" opacity=".4"/><path d="M9.5 8.3v7.4l6.3-3.7z"/>',
    "film": '<rect x="3" y="3" width="18" height="18" rx="2.4"/><path d="M7.5 3v18M16.5 3v18" stroke="{bg}" stroke-width="1.4"/>'
            '<path d="M4.6 6.5h1.4M4.6 10.5h1.4M4.6 14.5h1.4M4.6 18h1.4M18 6.5h1.4M18 10.5h1.4M18 14.5h1.4M18 18h1.4" stroke="{bg}" stroke-width="1.6"/>'
            '<path d="M10.2 9.2v5.6l4.6-2.8z" fill="{bg}"/>',
    "note-music": _app("music"),
    "venn": f'<circle cx="9" cy="9" r="5.6" {ST} stroke-width="2"/><circle cx="15" cy="9" r="5.6" {ST} stroke-width="2"/><circle cx="12" cy="14.8" r="5.6" {ST} stroke-width="2"/>',
    "bubble": '<path d="M2.5 5a2.5 2.5 0 0 1 2.5-2.5h14A2.5 2.5 0 0 1 21.5 5v9a2.5 2.5 0 0 1-2.5 2.5h-7.4L6 21v-4.5H5A2.5 2.5 0 0 1 2.5 14z"/>'
              '<path d="M7.5 7.5l2 4 2-4M14 7.5h3.5l-3.5 4h3.5" stroke="{bg}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "language": '<path d="M2 4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H8l-3.5 3V12H4a2 2 0 0 1-2-2z"/>'
                '<path d="M11 12.5h9a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-.5V24L16.5 21.5H11a2 2 0 0 1-2-2v-5" opacity=".6"/>'
                '<path d="M6 9.5l2.5-5.5 2.5 5.5M6.9 7.7h3.2" stroke="{bg}" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "flask": '<path d="M9 2.5h6M10 2.5v6.2L4.2 18.6A2 2 0 0 0 6 21.5h12a2 2 0 0 0 1.8-2.9L14 8.7V2.5" stroke="{c}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
             '<path d="M6.4 16h11.2l1.6 2.8a1.2 1.2 0 0 1-1 1.7H5.8a1.2 1.2 0 0 1-1-1.7z"/>',
    "cap": '<path d="M12 4L1.5 9 12 14l10.5-5z"/><path d="M5.5 11.3v4.4c0 1.8 3 3.3 6.5 3.3s6.5-1.5 6.5-3.3v-4.4L12 14.5z" opacity=".8"/>'
           f'<path d="M21 9.5v6" {ST} stroke-width="1.6"/>',
    "drives": '<rect x="2" y="5" width="20" height="14" rx="2.6"/><path d="M2 13h20" stroke="{bg}" stroke-width="1.4" opacity=".7"/>'
              '<circle cx="18" cy="16" r="1.3" fill="{bg}"/><path d="M5 16h7" stroke="{bg}" stroke-width="1.5" stroke-linecap="round"/>',
    "key": '<circle cx="7.5" cy="12" r="5"/><circle cx="7.5" cy="12" r="1.8" fill="{bg}"/><path d="M12 10.6h10v2.8h-2.2v3h-2.8v-3H12z"/>',
    "wallet": '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h13A2.5 2.5 0 0 1 21 7.5V9h-5.5a3 3 0 0 0 0 6H21v1.5a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5z"/>'
              '<rect x="13.5" y="10.5" width="9" height="3" rx="1.5" opacity=".75"/><circle cx="16" cy="12" r=".9" fill="{bg}"/>',
    "info": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="7" r="1.6" fill="{bg}"/><rect x="10.7" y="10" width="2.6" height="8" rx="1.3" fill="{bg}"/>',
    "picker": '<path d="M19.6 2.9a2 2 0 0 1 2.8 2.8l-2.6 2.6.9.9-1.8 1.8-.9-.9-8.1 8.1-3.6.9.9-3.6 8.1-8.1-.9-.9 1.8-1.8.9.9z"/>'
              '<circle cx="4.5" cy="19.5" r="2.4" opacity=".8"/>',
    "font": f'<path d="M4.5 20l6-16h3l6 16M7.2 14h9.6" {ST} stroke-width="2.4"/>',
    "keyboard": '<rect x="1.5" y="5.5" width="21" height="13" rx="2.4"/>'
                + "".join(f'<rect x="{3.7 + c * 3.4:.1f}" y="{8 + r * 3:.1f}" width="2.3" height="2" rx=".5" fill="{{bg}}"/>' for r in range(2) for c in range(5))
                + '<rect x="7" y="14.2" width="10" height="2" rx=".8" fill="{bg}"/>',
    "battery": '<rect x="2" y="7" width="17.5" height="10" rx="2.2" fill="none" stroke="{c}" stroke-width="2"/><rect x="20.2" y="10" width="2" height="4" rx=".8"/>'
               '<rect x="4.3" y="9.3" width="10" height="5.4" rx="1"/>',
    "power": f'<path d="M12 2.8v8.5M6.6 6.2a8 8 0 1 0 10.8 0" {ST} stroke-width="2.6"/>',
    "display": '<rect x="2" y="3.5" width="20" height="13" rx="2"/><rect x="10" y="16.5" width="4" height="2.8"/><rect x="7" y="19" width="10" height="2" rx="1"/>'
               '<path d="M5 13.5l4-4 3 2.5 3.5-4 3.5 5.5z" fill="{bg}" opacity=".5"/>',
    "scanner": '<path d="M3 13h18v5.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M4.5 10.5l14-6 1 2.3-14 6z" opacity=".75"/>'
               '<path d="M6 16.5h8" stroke="{bg}" stroke-width="1.5" stroke-linecap="round"/><circle cx="18" cy="16.5" r="1" fill="{bg}"/>',
    "chat": '<path d="M2.5 5.5A2.5 2.5 0 0 1 5 3h10a2.5 2.5 0 0 1 2.5 2.5V11A2.5 2.5 0 0 1 15 13.5H9l-4 3.5v-3.5A2.5 2.5 0 0 1 2.5 11z"/>'
            '<path d="M19 7.5h.5A2 2 0 0 1 21.5 9.5v6a2 2 0 0 1-2 2H19V21l-3.8-3.5H11a2 2 0 0 1-2-2" opacity=".6"/>',
    "download": f'<path d="M12 3v11.5M7 10l5 5 5-5" {ST} stroke-width="2.6"/><path d="M4 19.5h16" {ST} stroke-width="2.6"/>',
    "clipboard": '<rect x="4.5" y="4" width="15" height="18" rx="2.2"/><rect x="8.5" y="2" width="7" height="4.4" rx="1.2" opacity=".7"/>'
                 '<path d="M8 11h8M8 14.5h8M8 18h5" stroke="{bg}" stroke-width="1.6" stroke-linecap="round"/>',
    "disc": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3.4" fill="{bg}"/><circle cx="12" cy="12" r="1.4"/>'
            '<path d="M6.2 7.6a7 7 0 0 1 4.6-2.5" stroke="{bg}" stroke-width="1.4" stroke-linecap="round" fill="none" opacity=".7"/>',
    "cube3d": '<path d="M12 2l9 5v10l-9 5-9-5V7z" fill="none" stroke="{c}" stroke-width="1.8" stroke-linejoin="round"/>'
              '<path d="M12 12l9-5M12 12L3 7M12 12v10" stroke="{c}" stroke-width="1.6" fill="none"/><path d="M12 12l9-5-9-5-9 5z" opacity=".8"/>',
    "torrent": f'<path d="M12 2.5v13M6.5 10l5.5 5.5 5.5-5.5" {ST} stroke-width="2.6"/><circle cx="5" cy="20" r="1.6"/><circle cx="12" cy="20" r="1.6"/><circle cx="19" cy="20" r="1.6"/>',
    "calendar": _app("calendar"),
    "contacts": _app("contacts"),
    "calculator": _app("calculator"),
    "document": _app("document"),
    "folder": '<path d="M2 6a2 2 0 0 1 2-2h5l2.2 2.4H20a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/>',
    "home": '<path d="M12 3 2.5 11h2.8v9.5h5.2v-6h3v6h5.2V11h2.8z"/>',
    "share": '<circle cx="18" cy="5.5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="18.5" r="3"/>'
             f'<path d="M8.6 10.6l6.8-3.6M8.6 13.4l6.8 3.6" {ST} stroke-width="2"/>',
    "grid4": '<rect x="3" y="3" width="8" height="8" rx="1.6"/><rect x="13" y="3" width="8" height="8" rx="1.6"/>'
             '<rect x="3" y="13" width="8" height="8" rx="1.6"/><rect x="13" y="13" width="8" height="8" rx="1.6" opacity=".55"/>',
    "camera": _app("camera"),
    "web": _app("web"),
}


def place(name, x, y, scale):
    return f'<g transform="translate({x} {y}) scale({scale})">{G24[name]}</g>'


# ---------------------------------------------------------------- folders
# front top, front bottom, back (the colours generate.py's own folders use)
FAM = {
    "peach":  ("#F9C8B2", "#EFA1A1", "#C48FBA"),
    "violet": ("#A79FD4", "#857DB5", "#6C64A3"),
    "mauve":  ("#D7AACD", "#A77091", "#857DB5"),
    "coral":  ("#F4A79A", "#EA5148", "#A77091"),
    "rose":   ("#F5B3A8", "#EFA1A1", "#C48FBA"),
    "sand":   ("#FAD3C0", "#F2A98F", "#EFA1A1"),
    "lilac":  ("#B9A9DA", "#857DB5", "#A77091"),
    "dusk":   ("#DDB6D5", "#C48FBA", "#A77091"),
    "indigo": ("#C3B8E6", "#857DB5", "#C48FBA"),
}

# folder name: (family, symbol)   - the folder types Waypoint covers, and a few more
MORE_FOLDERS = {
    "folder-activities": ("violet", "venn"), "folder-android": ("indigo", "phone"), "folder-appimage": ("sand", "box"),
    "folder-blender": ("coral", "cube3d"), "folder-book": ("mauve", "book"), "folder-bookmark": ("coral", "bookmark"),
    "folder-build": ("lilac", "hammer"), "folder-calculate": ("dusk", "calculator"), "folder-chart": ("violet", "chart"),
    "folder-cloud": ("indigo", "cloud"), "folder-comic": ("rose", "bubble"), "folder-crash": ("coral", "warning"),
    "folder-database": ("lilac", "database"), "folder-deb": ("sand", "box"), "folder-decrypted": ("dusk", "unlock"),
    "folder-design": ("rose", "nib"), "folder-docker": ("indigo", "containers"), "folder-drawing": ("rose", "pencil"),
    "folder-dropbox": ("indigo", "cloud-up"), "folder-encrypted": ("violet", "lock"), "folder-extension": ("mauve", "puzzle"),
    "folder-favorites": ("coral", "star"), "folder-flatpak": ("sand", "box"), "folder-games": ("lilac", "gamepad"),
    "folder-gdrive": ("indigo", "cloud-sync"), "folder-git": ("coral", "branch"), "folder-godot": ("lilac", "gamepad"),
    "folder-html": ("violet", "globe"), "folder_html": ("violet", "globe"), "folder-image": ("sand", "image"),
    "folder-image-people": ("sand", "people"), "folder-important": ("coral", "exclaim"), "folder-java": ("indigo", "braces"),
    "folder-language": ("dusk", "language"), "folder-library": ("mauve", "library"), "folder-locked": ("violet", "lock"),
    "folder-unlocked": ("dusk", "unlock"), "folder-log": ("lilac", "lines"), "folder-mac": ("lilac", "laptop"),
    "folder-mail": ("coral", "mail"), "folder-network": ("indigo", "network"), "folder-notes": ("sand", "note"),
    "folder-onedrive": ("indigo", "cloud"), "folder-owncloud": ("indigo", "cloud-sync"), "folder-paint": ("rose", "brush"),
    "folder-picture": ("sand", "image"), "folder-podcast": ("mauve", "mic"), "folder-presentation": ("coral", "easel"),
    "folder-print": ("lilac", "printer"), "folder-recent": ("violet", "history"), "folder-remote": ("indigo", "remote"),
    "folder-root": ("coral", "shield"), "folder-rpm": ("sand", "box"), "folder-script": ("lilac", "terminal"),
    "folder-sign": ("dusk", "sign"), "folder-snap": ("sand", "box"), "folder-sound": ("rose", "speaker"),
    "folder-table": ("violet", "table"), "folder-tar": ("sand", "zip"), "folder-temp": ("dusk", "hourglass"),
    "folder-text": ("mauve", "lines"), "folder-txt": ("mauve", "lines"), "folder-trash": ("lilac", "bin"),
    "folder-windows": ("indigo", "window"), "folder-vbox": ("lilac", "box"), "folder-steam": ("lilac", "gamepad"),
    "folder-code": ("indigo", "code"), "folder-books": ("mauve", "library"), "folder-wallpaper": ("sand", "image"),
    "folder-screenshots": ("dusk", "camera"), "folder-camera": ("dusk", "camera"), "folder-photos": ("sand", "image"),
    "folder-favorite": ("coral", "heart"), "folder-heart": ("coral", "heart"), "folder-backup": ("violet", "history"),
    "folder-sync": ("indigo", "cloud-sync"), "folder-nextcloud": ("indigo", "cloud"), "folder-kde": ("violet", "gear"),
    "folder-system": ("lilac", "gear"), "folder-config": ("lilac", "gear"), "folder-tools": ("lilac", "wrench"),
    "folder-calendar": ("coral", "calendar"), "folder-contacts": ("violet", "contacts"), "folder-web": ("violet", "globe"),
    "folder-virtual": ("lilac", "monitor"), "folder-vm": ("lilac", "monitor"), "folder-torrent": ("coral", "torrent"),
    "folder-3d": ("coral", "cube3d"), "folder-fonts": ("mauve", "font"), "folder-school": ("violet", "cap"),
}

# the folders generate.py draws itself, with the symbol to use for their -symbolic version
OWN_FOLDER_SYMBOL = {
    "folder": None, "folder-open": None, "user-home": "home", "folder-home": "home", "folder-documents": "document",
    "folder-download": "download", "folder-downloads": "download", "folder-music": "note-music", "folder-pictures": "image",
    "folder-images": "image", "folder-videos": "play", "folder-video": "play", "user-desktop": "monitor",
    "folder-desktop": "monitor", "folder-templates": "grid4", "folder-publicshare": "share", "folder-public": "share",
    "folder-projects": "code", "folder-development": "code",
}


def folder_svg(fam, symbol, folder_body):
    """A folder from generate.py's folder_svg with a G24 symbol on its front."""
    top, bottom, back = FAM[fam]
    svg = folder_body(top, bottom, back, "none")
    g = place(symbol, 15, 20.2, 0.75).replace("{c}", SOFT).replace("{bg}", bottom)
    return svg.replace("</svg>", f'<g fill="{SOFT}" opacity=".93">{g}</g>\n</svg>')


def folder_symbolic(symbol, version, colour):
    """16 px single-colour folder (the symbol cut out), recoloured by Plasma and GTK."""
    cut = ""
    if symbol:
        g = place(symbol, 4.6, 6.6, 0.28).replace("{c}", "#000").replace("{bg}", "#FFF")
        cut = f'<g fill="#000" stroke-width="2.2">{g}</g>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<!-- Vice Horizon {version} symbolic folder - original artwork, CC-BY-SA-4.0 -->
<style type="text/css" id="current-color-scheme">.ColorScheme-Text {{ color:{colour}; }}</style>
<defs><mask id="m"><rect width="16" height="16" fill="#FFF"/>{cut}</mask></defs>
<path class="ColorScheme-Text" style="fill:currentColor" mask="url(#m)" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h3.6l1.5 1.6h5.9A1.5 1.5 0 0 1 15 5.1v7.4a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5z"/>
</svg>
"""


# ---------------------------------------------------------------- apps
# (symbol, tile family from icons_extra.FAM, icon names). "app:" symbols are icons_extra's own.
KDE_APPS = [
    ("app:files", "peach", ["org.kde.dolphin", "dolphin"]),
    ("app:terminal", "night", ["org.kde.konsole", "konsole", "org.kde.yakuake", "yakuake"]),
    ("app:settings", "violet", ["systemsettings", "org.kde.systemsettings", "preferences-desktop-theme-global"]),
    ("app:editor", "mauve", ["org.kde.kate", "kate", "org.kde.kwrite", "kwrite"]),
    ("app:calculator", "dusk", ["org.kde.kcalc", "kcalc", "org.kde.kalk"]),
    ("app:calendar", "coral", ["org.kde.merkuro.calendar", "org.kde.korganizer", "korganizer", "office-calendar"]),
    ("app:clocks", "violet", ["org.kde.kclock"]),
    ("app:weather", "peach", ["org.kde.kweather"]),
    ("app:maps", "coral", ["org.kde.marble", "marble"]),
    ("app:images", "pink", ["org.kde.gwenview", "gwenview"]),
    ("app:videos", "night", ["org.kde.haruna", "haruna", "org.kde.dragonplayer", "multimedia-video-player"]),
    ("app:music", "pink", ["org.kde.elisa", "elisa", "multimedia-audio-player"]),
    ("app:software", "coral", ["org.kde.discover", "plasmadiscover", "system-software-update"]),
    ("app:monitor", "night", ["org.kde.plasma-systemmonitor", "ksysguard", "org.kde.ksysguard"]),
    ("app:disks", "dusk", ["org.kde.partitionmanager", "partitionmanager"]),
    ("app:document", "mauve", ["org.kde.okular", "okular"]),
    ("app:contacts", "violet", ["org.kde.kaddressbook", "kaddressbook", "office-address-book", "system-users", "preferences-system-users"]),
    ("app:screenshot", "dusk", ["org.kde.spectacle", "spectacle"]),
    ("app:web", "violet", ["org.kde.falkon", "falkon", "org.kde.konqueror", "konqueror", "internet-web-browser"]),
    ("app:mail", "coral", ["org.kde.kmail2", "kmail", "internet-mail"]),
    ("app:help", "pink", ["org.kde.khelpcenter", "khelpcenter"]),
    ("app:archive", "peach", ["org.kde.ark", "ark", "utilities-file-archiver"]),
    ("app:logs", "night", ["org.kde.ksystemlog", "ksystemlog", "org.kde.kjournaldbrowser"]),
    ("app:boxes", "dusk", ["virt-manager", "preferences-virtualization"]),
    ("app:camera", "night", ["org.kde.kamoso", "kamoso"]),
    ("info", "violet", ["org.kde.kinfocenter", "kinfocenter", "hwinfo", "preferences-system-info"]),
    ("pie", "coral", ["org.kde.filelight", "filelight"]),
    ("phone", "indigo", ["org.kde.kdeconnect.app", "org.kde.kdeconnect", "kdeconnect", "preferences-kde-connect"]),
    ("wallet", "mauve", ["org.kde.kwalletmanager", "kwalletmanager", "kwalletmanager2", "kwallet"]),
    ("key", "dusk", ["org.kde.keysmith", "password-manager", "dialog-password"]),
    ("note", "peach", ["org.kde.knotes", "knotes"]),
    ("brush", "pink", ["org.kde.kolourpaint", "kolourpaint", "org.kde.krita", "krita", "applications-graphics"]),
    ("film", "night", ["org.kde.kdenlive", "kdenlive"]),
    ("chat", "violet", ["org.kde.neochat", "org.kde.konversation", "konversation", "internet-chat"]),
    ("torrent", "coral", ["org.kde.ktorrent", "ktorrent"]),
    ("remote", "night", ["org.kde.krdc", "krdc", "preferences-desktop-remote-desktop"]),
    ("clipboard", "dusk", ["klipper", "org.kde.klipper"]),
    ("font", "mauve", ["org.kde.kfontview", "kfontview", "preferences-desktop-font"]),
    ("picker", "pink", ["org.kde.kcolorchooser", "kcolorchooser", "preferences-desktop-color"]),
    ("keyboard", "night", ["preferences-desktop-keyboard", "org.kde.kmousetool"]),
    ("network", "indigo", ["preferences-system-network", "preferences-system-network-connection"]),
    ("display", "violet", ["preferences-desktop-display", "preferences-desktop-display-randr"]),
    ("battery", "peach", ["preferences-system-power", "preferences-system-power-management", "org.kde.powerdevil"]),
    ("speaker", "pink", ["preferences-desktop-sound", "org.kde.kmix", "kmix"]),
    ("printer", "lilac", ["printer", "org.kde.print-manager", "preferences-devices-printer"]),
    ("scanner", "lilac", ["org.kde.skanlite", "skanlite", "org.kde.skanpage", "scanner"]),
    ("shield", "coral", ["preferences-security-firewall", "org.kde.plasma.firewall", "security-high"]),
    ("gamepad", "night", ["applications-games", "preferences-desktop-gaming", "org.kde.kpat", "kpat"]),
    ("code", "indigo", ["applications-development", "org.kde.kdevelop", "kdevelop"]),
    ("globe", "violet", ["applications-internet", "preferences-system-network-proxy"]),
    ("play", "pink", ["applications-multimedia"]),
    ("document", "mauve", ["applications-office"]),
    ("flask", "dusk", ["applications-science", "applications-education-science"]),
    ("cap", "violet", ["applications-education", "applications-education-university"]),
    ("gear", "night", ["applications-system", "preferences-other"]),
    ("wrench", "lilac", ["applications-utilities", "applications-accessories", "preferences-desktop"]),
    ("star", "coral", ["applications-other", "bookmarks", "bookmarks-organize"]),
    ("lines", "mauve", ["org.kde.calligrawords", "x-office-document-template"]),
    ("table", "green", ["org.kde.calligrasheets", "x-office-spreadsheet-template"]),
    ("easel", "coral", ["org.kde.calligrastage", "x-office-presentation-template"]),
    ("cube3d", "coral", ["applications-engineering"]),
    ("disc", "peach", ["org.kde.k3b", "k3b"]),
    ("download", "violet", ["org.kde.kget", "kget"]),
    ("book", "mauve", ["org.kde.arianna", "arianna"]),
]


TILE = dict(X.FAM, indigo=("#C3B8E6", "#857DB5"), lilac=("#B9A9DA", "#857DB5"), green=("#A9D8B8", "#3B9564"))


def app_svg(symbol, fam, version):
    top, bottom = TILE[fam]
    if symbol.startswith("app:"):
        return X.app_svg(symbol[4:], fam, version)
    edge = ".16" if fam == "night" else "0"
    g = place(symbol, 12, 12, 1).replace("{c}", SOFT).replace("{bg}", bottom)
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


# ---------------------------------------------------------------- devices
def device_svg(symbol, top, bottom, version):
    g = place(symbol, 6, 6, 1.5).replace("{c}", "url(#t)").replace("{bg}", SOFT)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} device icon - original artwork, CC-BY-SA-4.0 -->
<defs><linearGradient id="t" x1="0" y1="6" x2="0" y2="42" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>
<g fill="url(#t)">{g}</g>
</svg>
"""


MORE_DEVICES = {
    "computer": ("monitor", "#B9B2E3", "#6C64A3"), "video-display": ("display", "#B9B2E3", "#6C64A3"),
    "computer-laptop": ("laptop", "#B9B2E3", "#6C64A3"), "phone": ("phone", "#F4A79A", "#EA5148"),
    "smartphone": ("phone", "#F4A79A", "#EA5148"), "network-workgroup": ("network", "#C3B8E6", "#857DB5"),
    "network-server": ("drives", "#C3B8E6", "#857DB5"), "drive-multidisk": ("drives", "#B9B2E3", "#6C64A3"),
    "input-keyboard": ("keyboard", "#4B4670", "#252239"), "input-gaming": ("gamepad", "#4B4670", "#252239"),
    "printer": ("printer", "#C3B8E6", "#857DB5"), "scanner": ("scanner", "#C3B8E6", "#857DB5"),
    "camera-photo": ("camera", "#4B4670", "#252239"), "audio-speakers": ("speaker", "#F5B3A8", "#E58C8C"),
    "battery": ("battery", "#A9D8B8", "#3B9564"),
}


# ---------------------------------------------------------------- file types
# kind: ((top, bottom), symbol, names)
MORE_FILES = {
    "package": (("#FAD3C0", "#C48FBA"), "box", ["application-x-deb", "application-vnd.debian.binary-package", "application-x-rpm",
                                                 "application-x-redhat-package-manager", "application-vnd.appimage", "application-x-appimage",
                                                 "application-vnd.flatpak", "application-vnd.flatpak.ref", "application-vnd.snap",
                                                 "application-x-xz-pkg", "application-x-zstd-compressed-tar"]),
    "disc": (("#FAD3C0", "#857DB5"), "disc", ["application-x-cd-image", "application-x-iso9660-image", "application-x-raw-disk-image",
                                              "application-x-cue"]),
    "database": (("#C3B8E6", "#6C64A3"), "database", ["application-x-sqlite3", "application-vnd.sqlite3", "application-sql",
                                                       "text-x-sql", "application-x-sql"]),
    "calendar": (("#F4A79A", "#EA5148"), "calendar", ["text-calendar", "text-x-vcalendar"]),
    "contact": (("#B9B2E3", "#6C64A3"), "contacts", ["text-vcard", "text-x-vcard", "text-directory"]),
    "ebook": (("#DDB6D5", "#A77091"), "book", ["application-epub+zip", "application-x-mobipocket-ebook", "application-x-fictionbook+xml"]),
    "markdown": (("#DDB6D5", "#857DB5"), "markdown", ["text-markdown", "text-x-markdown"]),
    "log": (("#4B4670", "#252239"), "lines", ["text-x-log", "text-x-changelog"]),
    "config": (("#C48FBA", "#857DB5"), "gear", ["application-x-desktop", "text-x-ini", "application-toml", "application-x-yaml",
                                                 "application-yaml", "text-x-systemd-unit"]),
    "code": (("#4B4670", "#252239"), "braces", ["application-xml", "text-xml", "text-css", "text-x-java", "application-x-php",
                                                 "text-x-rust", "text-x-go", "text-x-csharp", "text-x-typescript", "application-typescript",
                                                 "text-x-makefile", "text-x-cmake", "application-x-perl", "text-x-lua", "text-x-kotlin"]),
    "model": (("#F4A79A", "#C93B32"), "cube3d", ["model-stl", "model-obj", "application-x-blender", "model-gltf-binary",
                                                  "model-gltf+json", "application-x-3ds", "image-vnd.dxf", "image-vnd.dwg"]),
    "torrent": (("#F4A79A", "#EA5148"), "torrent", ["application-x-bittorrent"]),
    "windows": (("#C3B8E6", "#857DB5"), "window", ["application-x-ms-dos-executable", "application-x-msi", "application-x-msdownload",
                                                    "application-x-ms-shortcut"]),
    "key": (("#DDB6D5", "#857DB5"), "key", ["application-pgp-keys", "application-x-pem-key", "application-x-x509-ca-cert",
                                             "application-pkcs12", "application-pgp-encrypted"]),
    "subtitle": (("#B9A9DA", "#857DB5"), "bubble", ["application-x-subrip", "text-x-ssa", "text-vtt"]),
    "drawing": (("#FAD3C0", "#F2A98F"), "brush", ["image-x-xcf", "application-x-krita", "image-openraster", "image-x-psd",
                                                   "image-vnd.adobe.photoshop"]),
    "html": (("#B9B2E3", "#6C64A3"), "globe", ["application-x-mswinurl", "text-x-uri", "application-x-mozilla-bookmarks"]),
    "font2": (("#DDB6D5", "#857DB5"), "font", ["font-woff", "font-woff2", "application-x-font-otf", "application-x-font-type1"]),
}


def file_svg(top, bottom, symbol, version):
    g = place(symbol, 16, 22.4, 0.667).replace("{c}", SOFT).replace("{bg}", bottom)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<!-- Vice Horizon {version} file-type icon - original artwork, CC-BY-SA-4.0 -->
<defs><linearGradient id="p" x1="0" y1="4" x2="0" y2="44" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>
<path d="M11.5 4.5h17l9 9v28a2 2 0 0 1-2 2h-24a2 2 0 0 1-2-2v-35a2 2 0 0 1 2-2z" fill="url(#p)"/>
<path d="M28.5 4.5v7a2 2 0 0 0 2 2h7z" fill="#FFFFFF" opacity=".45"/>
<rect x="9.5" y="42" width="28" height="1.5" rx=".75" fill="{PLUM}" opacity=".18"/>
<g fill="{SOFT}" opacity=".95">{g}</g>
</svg>
"""


def write_all(write, base, version, folder_body, variant):
    """Everything above into icon theme `base`. Returns {kind: count}."""
    text = SOFT if variant == "dark" else PLUM      # used where the desktop doesn't recolour symbolic icons
    n = {"folders": 0, "symbolic": 0, "apps": 0, "devices": 0, "files": 0}
    for name, (fam, sym) in MORE_FOLDERS.items():
        write(base / "places/scalable" / f"{name}.svg", folder_svg(fam, sym, folder_body)); n["folders"] += 1
    for name, sym in OWN_FOLDER_SYMBOL.items():
        write(base / "places/scalable" / f"{name}-symbolic.svg", folder_symbolic(sym, version, text)); n["symbolic"] += 1
    for name, (fam, sym) in MORE_FOLDERS.items():
        write(base / "places/scalable" / f"{name}-symbolic.svg", folder_symbolic(sym, version, text)); n["symbolic"] += 1
    for sym, fam, names in KDE_APPS:
        svg = app_svg(sym, fam, version)
        for nm in names:
            write(base / "apps/scalable" / f"{nm}.svg", svg); n["apps"] += 1
    for name, (sym, top, bottom) in MORE_DEVICES.items():
        write(base / "devices/scalable" / f"{name}.svg", device_svg(sym, top, bottom, version)); n["devices"] += 1
    for kind, ((top, bottom), sym, names) in MORE_FILES.items():
        svg = file_svg(top, bottom, sym, version)
        for nm in names:
            write(base / "mimetypes/scalable" / f"{nm}.svg", svg); n["files"] += 1
    return n
