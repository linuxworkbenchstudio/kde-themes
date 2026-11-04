"""python3 -m unittest discover -s tests -t . -v"""
import tempfile
import unittest
from pathlib import Path

from engine.__main__ import build, main
from engine.colour import contrast, mix
from engine.pack import PackError, load

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden"


class Golden(unittest.TestCase):
    """The engine must reproduce what each theme has already released, byte for byte."""

    def check_pack(self, pack_id):
        files = build(load(ROOT / "packs" / pack_id))
        golden = sorted(p for p in (GOLDEN / pack_id).rglob("*") if p.is_file())
        self.assertTrue(golden)
        for g in golden:
            rel = g.relative_to(GOLDEN / pack_id).as_posix()
            with self.subTest(file=rel):
                self.assertIn(rel, files, "the engine does not make this file")
                self.assertEqual(files[rel], g.read_text(encoding="utf-8"))

    def test_waypoint(self):
        self.check_pack("waypoint")


def write_pack(text: str) -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "pack.toml").write_text(text, encoding="utf-8")
    return d


MINIMAL = """
[theme]
id = "test"
name = "Test Theme"
command = "test-theme"
brand = "The Linux Workbench"
version = "0.1.0"
lookandfeel_id = "org.thelinuxworkbench.test"
editions = ["dark"]
parts = ["kde-colors", "konsole"]
[colours]
blue = "#3080F0"
[edition.dark.roles]
window_bg = "#202020"
view_bg = "#1A1A1A"
border = "#404040"
text = "#F0F0F0"
text_muted = "#A0A0A0"
text_disabled = "#606060"
accent = "blue"
selection_bg = "accent"
selection_fg = "#FFFFFF"
negative = "#E04040"
neutral = "#E0A000"
positive = "#40C060"
[edition.dark.terminal]
normal = ["#303030", "negative", "positive", "neutral", "accent", "#A060C0", "#40A0A0", "text_muted"]
bright = ["#505050", "#FF6060", "#60E080", "#FFC040", "#60A0FF", "#C080E0", "#60C0C0", "text"]
"""


REFS = ROOT / "references"


@unittest.skipUnless((REFS / "waypoint" / "reference.json").is_file() and (REFS / "vice-horizon" / "reference.json").is_file(),
                     "references not imported (tools/import_reference.py)")
class AgainstReleases(unittest.TestCase):
    """Every file the engine makes must match the theme's last release (exactly, with the same
    settings, or with settings only added)."""

    def test_both_themes(self):
        from engine.compare import compare
        for pid in ("waypoint", "vice-horizon"):
            with self.subTest(pack=pid):
                r = compare(build(load(ROOT / "packs" / pid)), REFS / pid)
                self.assertEqual(r.different, [])
                self.assertEqual(r.new, [])
                self.assertGreater(len(r.exact) + len(r.same) + len(r.adds), 0)


class Packs(unittest.TestCase):
    def test_minimal_pack_and_names(self):
        p = load(write_pack(MINIMAL))
        ed = p.editions["dark"]
        self.assertEqual(p.file_name("color_scheme", ed), "Test-Theme-Dark")
        self.assertEqual(p.file_name("konsole", ed), "Test-Theme-Dark")
        self.assertEqual(ed.roles["base_bg"], "#1A1A1A")          # optional roles fall back
        self.assertEqual(ed.roles["link"], "#3080F0")
        self.assertEqual(ed.roles["selection_bg"], "#3080F0")      # a role can name an earlier role
        self.assertEqual(ed.kde["settings"]["complementary"], "dark")
        self.assertEqual(ed.kde["groups"]["Window"]["BackgroundNormal"], "#202020")
        files = build(p)
        self.assertEqual(sorted(files), ["color-schemes/Test-Theme-Dark.colors", "konsole/Test-Theme-Dark.colorscheme",
                                         "konsole/Test-Theme-Dark.profile"])
        self.assertIn("Name=Test Theme Dark", files["color-schemes/Test-Theme-Dark.colors"])

    def test_problems_are_reported_together(self):
        bad = (MINIMAL.replace('accent = "blue"', 'accent = "#3080F"')
               .replace('border = "#404040"\n', "")
               .replace("[edition.dark.terminal]", '[edition.dark.kde]\nbuton = "x"\n[edition.dark.kde.View]\nBackgroundNormal = "nonesuch"\n'
                        'Frob = "text"\n[edition.dark.terminal]')
               .replace('"#40A0A0", "text_muted"]', '"#40A0A0"]'))
        with self.assertRaises(PackError) as cm:
            load(write_pack(bad))
        msg = "\n".join(cm.exception.problems)
        for expected in ("accent = '#3080F': not a colour name", "roles] border: missing",
                         "kde] buton: not a KDE colour group", "BackgroundNormal = 'nonesuch': not a role",
                         "kde.View] Frob: not a key", "need 8 colours each (have 7 and 8)"):
            self.assertIn(expected, msg)

    def test_unknown_theme_setting(self):
        with self.assertRaises(PackError) as cm:
            load(write_pack(MINIMAL.replace('brand = "The Linux Workbench"', 'brand = "The Linux Workbench"\ncolour = "red"')))
        self.assertIn("[theme] colour: not a known setting", "\n".join(cm.exception.problems))

    def test_ids_and_parts(self):
        bad = MINIMAL.replace('parts = ["kde-colors", "konsole"]\n', "").replace('lookandfeel_id = "org.thelinuxworkbench.test"',
                              'lookandfeel_id = "Org.Test"\nprevious_ids = ["org.waypoint"]\nparts = ["konsole", "nope"]')
        with self.assertRaises(PackError) as cm:
            load(write_pack(bad))
        msg = "\n".join(cm.exception.problems)
        self.assertIn("lookandfeel_id = 'Org.Test'", msg)
        self.assertIn("parts: 'nope' is not a part", msg)
        p = load(write_pack(MINIMAL.replace('parts = ["kde-colors", "konsole"]', 'parts = ["konsole"]')))
        self.assertEqual(sorted(build(p)), ["konsole/Test-Theme-Dark.colorscheme", "konsole/Test-Theme-Dark.profile"])
        w = load(ROOT / "packs" / "waypoint")
        self.assertEqual((w.brand, w.version, w.lookandfeel_id, w.previous_ids),
                         ("The Linux Workbench", "0.1.0", "org.thelinuxworkbench.waypoint", ["org.waypoint"]))

    def test_every_part_by_default(self):
        p = load(write_pack(MINIMAL.replace('parts = ["kde-colors", "konsole"]\n', "")))
        files = build(p)
        for prefix in ("plasma/desktoptheme/Test-Theme-Dark/", "aurorae/themes/Test-Theme-Dark/", "cursors/Test-Theme-Cursors-Dark/"):
            self.assertTrue(any(f.startswith(prefix) for f in files), prefix)
        self.assertIn("Name=Test Theme Dark", files["aurorae/themes/Test-Theme-Dark/metadata.desktop"])

    def test_cross_edition_reference(self):
        p = load(ROOT / "packs" / "waypoint")
        self.assertEqual(p.editions["light"].terminal["foreground_intense"], p.editions["dark"].roles["base_bg"])

    def test_cli(self):
        out = Path(tempfile.mkdtemp())
        self.assertEqual(main(["build", str(ROOT / "packs" / "waypoint"), "--out", str(out)]), 0)
        self.assertTrue((out / "waypoint" / "konsole" / "WaypointLight.profile").is_file())
        self.assertEqual(main(["build", str(write_pack(MINIMAL.replace('window_bg = "#202020"', 'window_bg = "x"'))), "--out", str(out)]), 1)


class Colours(unittest.TestCase):
    def test_mix_rounds_half_up(self):
        self.assertEqual(mix("#272E37", "#0F1217", 0.55), "#1C2129")   # Waypoint's Color0Faint
        self.assertEqual(mix("#FFFFFF", "#000000", 0.5), "#808080")

    def test_contrast(self):
        self.assertAlmostEqual(contrast("#FFFFFF", "#000000"), 21.0, places=6)
        self.assertAlmostEqual(contrast("#777777", "#777777"), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
