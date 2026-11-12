#!/usr/bin/env bash
# shellcheck disable=SC2034  # variables are read inside eval'd test expressions
# @@NAME@@ test suite: static validation + install/uninstall round trips in a
# throw-away HOME, with stubbed desktop tools (plasma-apply-*, gsettings, dconf...).
# Never touches your real home directory or desktop settings.
#   ./tests/run-tests.sh            all tests
#   ./tests/run-tests.sh --no-static   skip tests/validate.sh
@@NAMES_SH@@
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/@@COMMAND@@-tests.XXXXXX")"
trap 'rm -rf -- "$TMP"' EXIT
PASS=0; FAIL=0
EXTRA=(); [[ $EUID -eq 0 ]] && EXTRA=(--allow-root)   # CI containers often run as root

ok()   { PASS=$((PASS + 1)); printf '  \e[32mok\e[0m   %s\n' "$*"; }
bad()  { FAIL=$((FAIL + 1)); printf '  \e[31mFAIL\e[0m %s\n' "$*"; }
t()    { if eval "$2"; then ok "$1"; else bad "$1"; fi; }
section() { printf '\n\e[1m%s\e[0m\n' "$*"; }

new_home() {
  H="$TMP/home-$1"; rm -rf -- "$H"; mkdir -p "$H"
  D="$H/.local/share"; C="$H/.config"
  export STUB_STATE="$H/.stub"; mkdir -p "$STUB_STATE"
}
run_inst()   { HOME="$H" XDG_DATA_HOME="" XDG_CONFIG_HOME="" DBUS_SESSION_BUS_ADDRESS="" "$ROOT/install.sh" "${EXTRA[@]}" "$@" </dev/null >"$TMP/out" 2>&1; }
run_uninst() { HOME="$H" XDG_DATA_HOME="" XDG_CONFIG_HOME="" DBUS_SESSION_BUS_ADDRESS="" "$ROOT/uninstall.sh" "$@" </dev/null >"$TMP/out" 2>&1; }
run_vh()     { HOME="$H" XDG_DATA_HOME="" XDG_CONFIG_HOME="" "$H/.local/bin/@@COMMAND@@" "$@" </dev/null >"$TMP/out" 2>&1; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
vh_files() { find "$H" -path "$D/@@COMMAND@@/backups" -prune -o \( @@FIND_OURS@@ \) -print | grep -v "^$D/@@COMMAND@@$" ; }

# ---------------------------------------------------------------- stubs
STUBS="$TMP/stubs"; mkdir -p "$STUBS"
cat > "$STUBS/gsettings" <<'EOF'
#!/usr/bin/env bash
db="$STUB_STATE/gsettings.db"; touch "$db"; echo "gsettings $*" >> "$STUB_STATE/calls.log"
if [[ "$1" == --schemadir ]]; then echo "schemadir $2" >> "$STUB_STATE/calls.log"; shift 2; fi
defaults() { case "$1 $2" in
  "org.gnome.desktop.interface gtk-theme") echo "'Adwaita'";; "org.gnome.desktop.interface icon-theme") echo "'Adwaita'";;
  "org.gnome.desktop.interface color-scheme") echo "'default'";;
  "org.gnome.desktop.background picture-uri"|"org.gnome.desktop.background picture-uri-dark") echo "'file:///usr/share/backgrounds/default.jpg'";;
  "org.gnome.shell.extensions.user-theme name") echo "''";;
  "org.gnome.Terminal.ProfilesList list") echo "['b1dcc9dd-5262-4d8d-a863-c897e6d979b9']";;
  "org.gnome.Terminal.ProfilesList default") echo "'b1dcc9dd-5262-4d8d-a863-c897e6d979b9'";;
  *) return 1;; esac; }
case "$1" in
  list-schemas) printf '%s\n' org.gnome.desktop.interface org.gnome.desktop.background org.gnome.Terminal.ProfilesList
                [[ -n "${STUB_NO_UT:-}" ]] || echo org.gnome.shell.extensions.user-theme ;;
  get) v="$(grep -F "$2|$3|" "$db" | tail -n1 | cut -d'|' -f3-)"; [[ -n "$v" ]] && echo "$v" || defaults "$2" "$3" ;;
  set) v="$4"; [[ "$v" != \'* && "$v" != \[* && "$v" != @* ]] && v="'$v'"; grep -vF "$2|$3|" "$db" > "$db.t"; echo "$2|$3|$v" >> "$db.t"; mv "$db.t" "$db" ;;
  reset) grep -vF "$2|$3|" "$db" > "$db.t"; mv "$db.t" "$db" ;;
esac
EOF
cat > "$STUBS/dconf" <<'EOF'
#!/usr/bin/env bash
echo "dconf $*" >> "$STUB_STATE/calls.log"
case "$1" in load) cat > "$STUB_STATE/dconf-$(echo "$2" | tr '/:' '__')";; reset) rm -f "$STUB_STATE/dconf-$(echo "$3" | tr '/:' '__')";; esac
EOF
for c in plasma-apply-colorscheme plasma-apply-desktoptheme plasma-apply-wallpaperimage plasma-changeicons kvantummanager kwriteconfig6 \
         plasma-apply-cursortheme plasma-apply-lookandfeel yay sudo; do
  printf '#!/usr/bin/env bash\necho "%s $*" >> "$STUB_STATE/calls.log"\n' "$c" > "$STUBS/$c"
done
cat > "$STUBS/kreadconfig6" <<'EOF'
#!/usr/bin/env bash
case "$*" in *ColorScheme*) echo "${STUB_CS:-BreezeDark}";; *LookAndFeelPackage*) echo "${STUB_LNF:-org.fedoraproject.fedora.desktop}";; *plasmarc*) echo default;; *"--group Icons"*) echo breeze-dark;;
  *DefaultProfile*) echo "${STUB_KP:-}";; *widgetStyle*) echo "${STUB_STYLE:-Breeze}";; *cursorTheme*) echo breeze_cursors;;
  *kdecoration2*library*) echo org.kde.breeze;; *kdecoration2*theme*) echo Breeze;; *ksplashrc*) echo org.kde.breeze.desktop;; esac
EOF
cat > "$STUBS/gnome-extensions" <<'EOF'
#!/usr/bin/env bash
echo "gnome-extensions $*" >> "$STUB_STATE/calls.log"
case "$1" in
  info) [[ "$2" == user-theme@* || -e "$STUB_STATE/ext-$2" ]] ;;
  list) [[ -n "${STUB_UT_OFF:-}" && ! -e "$STUB_STATE/ext-on-user-theme@gnome-shell-extensions.gcampax.github.com" ]] || echo "user-theme@gnome-shell-extensions.gcampax.github.com"
        for f in "$STUB_STATE"/ext-on-*; do [[ -e "$f" ]] && echo "${f##*/ext-on-}"; done; true ;;
  enable) touch "$STUB_STATE/ext-on-$2" ;;
esac
EOF
cat > "$STUBS/qdbus6" <<'EOF'
#!/usr/bin/env bash
printf 'qdbus6 %s\n' "$*" >> "$STUB_STATE/calls.log"
case "$*" in *org.kde.GtkConfig*)     # Plasma's GTK settings service; STUB_NO_GTKCONFIG: not installed
  [[ -n "${STUB_NO_GTKCONFIG:-}" ]] && exit 1
  case "$*" in *setGtkTheme*) echo "${@: -1}" > "$STUB_STATE/gtk" ;; *gtkTheme*) cat "$STUB_STATE/gtk" 2>/dev/null || echo Breeze ;; esac
  exit 0 ;; esac
case "$*" in *knownWidgetTypes.indexOf*) echo false;; *"print(f);"*) echo "${STUB_PANEL_LOOK:-@@NAME@@ Fancy}";; esac
EOF
cat > "$STUBS/systemctl" <<'EOF'
#!/usr/bin/env bash
echo "systemctl $*" >> "$STUB_STATE/calls.log"
case "$*" in *is-active*) exit 1;; esac
EOF
chmod +x "$STUBS"/*

# ================================================================ static
if [[ "${1:-}" != --no-static ]]; then
  section "Static validation"
  if "$ROOT/tests/validate.sh" > "$TMP/val" 2>&1; then ok "tests/validate.sh ($(grep -o '[0-9]* checks' "$TMP/val"))"
  else bad "tests/validate.sh"; cat "$TMP/val"; fi
fi

# ================================================================ CLI
section "Command line"
new_home cli
t "--help exits 0"            'run_inst --help'
t "--list exits 0"            'run_inst --list && grep -q kde-colors "$TMP/out"'
t "--version prints version"  'run_inst --version && grep -q "$(cat "$ROOT/VERSION")" "$TMP/out"'
t "unknown option exits 2"    'run_inst --bogus; [[ $? -eq 2 ]]'
t "bad variant rejected"      '! run_inst --desktop kde --variant blue'
t "bad component rejected"    '! run_inst --components nope'
t "no args + no tty -> usage, exit 2" 'run_inst; [[ $? -eq 2 ]]'
t "GNOME is refused (not in this release)" '! run_inst --desktop gnome --yes && grep -q "GNOME is not part of this release" "$TMP/out"'
t "--deps-report lists one item per line" 'run_inst --deps-report && grep -q "^ITEM	Kvantum	" "$TMP/out" && grep -q "^ITEM	KVitals	" "$TMP/out"'
t "  writes nothing"            '[[ -z "$(find "$H" -mindepth 1 -not -path "$H/.stub*" | head -n1)" ]]'
t "--activate=blue rejected"    '! run_inst --activate=blue --yes'
t "uninstall --help exits 0"  'run_uninst --help'
if [[ $EUID -eq 0 ]]; then
  t "root refused without --allow-root" '! HOME="$H" "$ROOT/install.sh" --desktop kde --yes </dev/null >/dev/null 2>&1'
fi
t "uninstall with nothing installed is a no-op" 'run_uninst --yes && grep -q "not installed" "$TMP/out"'

# ================================================================ dry run
section "Dry run"
new_home dry
t "dry run succeeds"          'run_inst --variant both --dry-run --yes'
t "dry run writes nothing"    '[[ -z "$(find "$H" -mindepth 1 -not -path "$H/.stub*" | head -n1)" ]]'

# ================================================================ full round trip
section "Install KDE Dark + Light"
new_home full
mkdir -p "$D/color-schemes" "$C/gtk-4.0" "$D/themes/SomeOtherTheme/gtk-3.0"
printf '[General]\nName=Mine\n' > "$D/color-schemes/@@N:color_scheme:Dark@@.colors"      # pre-existing, not ours
printf '[General]\nName=Other\n' > "$D/color-schemes/Other.colors"                 # unrelated
printf '/* my own tweaks */\nwindow { padding: 1px; }' > "$C/gtk-4.0/gtk.css"      # no trailing newline on purpose
echo "other" > "$D/themes/SomeOtherTheme/gtk-3.0/gtk.css"
orig_foreign="$(sha "$D/color-schemes/@@N:color_scheme:Dark@@.colors")"
orig_other="$(sha "$D/color-schemes/Other.colors")"
orig_gtk4="$(sha "$C/gtk-4.0/gtk.css")"
orig_theme="$(sha "$D/themes/SomeOtherTheme/gtk-3.0/gtk.css")"

t "install succeeds"            'run_inst --variant both --yes'
t "summary reports 0 failed"    'grep -q " 0 failed" "$TMP/out"'
t "icon theme inherits only themes that exist" '! grep -q "^Inherits=.*Papirus" "$D/icons/@@N:icons:Dark@@/index.theme" && grep -q "^Inherits=.*hicolor" "$D/icons/@@N:icons:Dark@@/index.theme"'
t "manifest written"            '[[ -s "$D/@@COMMAND@@/manifest.tsv" ]]'
for f in color-schemes/@@N:color_scheme:Light@@.colors plasma/desktoptheme/@@N:plasma_style:Dark@@/metadata.json \
         plasma/desktoptheme/@@N:plasma_style:Light@@/dialogs/background.svgz konsole/@@N:konsole:Dark@@.profile \
         plasma/look-and-feel/@@LNF@@.dark/contents/defaults wallpapers/@@SLUG@@/metadata.json \
         icons/@@N:icons:Dark@@/index.theme icons/@@N:icons:Light@@/places/scalable/folder.svg \
         ../../.config/Kvantum/@@N:kvantum:Dark@@/@@N:kvantum:Dark@@.kvconfig ../../.config/Kvantum/@@N:kvantum:Light@@/@@N:kvantum:Light@@.svg \
         icons/@@N:icons:Dark@@/places/scalable/folder-git.svg icons/@@N:icons:Light@@/apps/scalable/org.kde.dolphin.svg; do
  t "installed $f" "[[ -f \"\$D/$f\" ]]"
done
t "Aurorae decoration installed" '[[ -f "$D/aurorae/themes/@@N:aurorae:Dark@@/decoration.svg" && -f "$D/aurorae/themes/@@N:aurorae:Light@@/@@N:aurorae:Light@@rc" ]]'
first_alias="$(grep -v '^#' "$ROOT/cursors/@@N:cursors:Dark@@/aliases.txt" | head -n1)"
t "cursor theme + alias symlinks in ~/.icons"  '[[ -f "$H/.icons/@@N:cursors:Dark@@/cursors/default" && -L "$H/.icons/@@N:cursors:Dark@@/cursors/${first_alias%% *}" && -e "$H/.icons/@@N:cursors:Dark@@/cursors/${first_alias%% *}" && ! -e "$D/icons/@@N:cursors:Dark@@" ]]'
t "folder MIME-type icon (Dolphin file view)" '[[ -f "$D/icons/@@N:icons:Light@@/mimetypes/scalable/inode-directory.svg" ]] && grep -q "mimetypes/scalable" "$D/icons/@@N:icons:Light@@/index.theme"'
t "logo in hicolor"             '[[ ( -f "$D/icons/hicolor/scalable/apps/@@COMMAND@@-launcher.svg" || -f "$D/icons/hicolor/256x256/apps/@@COMMAND@@-launcher.png" ) && -f "$D/icons/hicolor/256x256/apps/@@COMMAND@@.png" ]]'
t "launcher in hicolor and in the theme at fixed sizes" '[[ -f "$D/icons/hicolor/22x22/apps/@@COMMAND@@-launcher.png" && -f "$D/icons/@@N:icons:Dark@@/apps/22/@@COMMAND@@-launcher.png" && -f "$D/icons/@@N:icons:Light@@/apps/16/@@COMMAND@@-launcher.png" && ! -e "$D/icons/@@N:icons:Dark@@/apps/scalable/@@COMMAND@@-launcher.svg" ]]'
t "panel script + presets"      '[[ -f "$D/@@COMMAND@@/panel/@@COMMAND@@-panel.js" && -f "$C/panel-colorizer/presets/@@NAME@@ Fancy/settings.json" ]]'
t "@@COMMAND@@ command executable" '[[ -x "$H/.local/bin/@@COMMAND@@" && -f "$C/autostart/@@COMMAND@@-sync.desktop" ]]'
t "every manifest file exists with recorded sha" \
  'awk -F"\t" "\$1==\"F\"{print \$3\"  \"\$4}" "$D/@@COMMAND@@/manifest.tsv" | sha256sum -c --quiet -'
t "no GNOME parts installed"    '[[ ! -e "$D/themes/@@N:gtk:Dark@@/gnome-shell" && ! -e "$D/gnome-background-properties" && ! -e "$D/org.gnome.Ptyxis" ]]'
t "foreign file was backed up"  'grep -q "^B	" "$D/@@COMMAND@@/manifest.tsv" && [[ -n "$(find "$D/@@COMMAND@@/backups" -name @@N:color_scheme:Dark@@.colors)" ]]'
t "unrelated colour scheme untouched" '[[ "$(sha "$D/color-schemes/Other.colors")" == "$orig_other" ]]'
t "unrelated GTK theme untouched"     '[[ "$(sha "$D/themes/SomeOtherTheme/gtk-3.0/gtk.css")" == "$orig_theme" ]]'
t "gtk.css untouched"           '[[ "$(sha "$C/gtk-4.0/gtk.css")" == "$orig_gtk4" ]]'

section "Repeat install (idempotent)"
nb="$(find "$D/@@COMMAND@@/backups" -type f | wc -l)"
lines="$(grep -c . "$D/@@COMMAND@@/manifest.tsv")"
t "second install succeeds"     'run_inst --variant both --yes'
t "nothing new or replaced"     'grep -q "0 new, 0 replaced" "$TMP/out"'
t "no extra backups"            '[[ "$(find "$D/@@COMMAND@@/backups" -type f | wc -l)" -eq "$nb" ]]'
t "manifest size stable"        '[[ "$(grep -c . "$D/@@COMMAND@@/manifest.tsv")" -eq "$lines" ]]'

section "Partial uninstall"
t "uninstall --components kde-aurorae" 'run_uninst --components kde-aurorae --yes'
t "decorations removed"         '[[ ! -e "$D/aurorae/themes/@@N:aurorae:Dark@@" && ! -e "$D/aurorae" ]]'
t "other components still there" '[[ -f "$D/color-schemes/@@N:color_scheme:Light@@.colors" && -f "$D/plasma/desktoptheme/@@N:plasma_style:Dark@@/metadata.json" ]]'

section "Uninstall keeps user-modified files"
MOD="$D/plasma/desktoptheme/@@N:plasma_style:Dark@@/metadata.json"; USER_FILE="$D/plasma/desktoptheme/@@N:plasma_style:Dark@@/my-extra.svg"
echo " " >> "$MOD"
echo "user-added" > "$USER_FILE"
t "uninstall --yes succeeds"    'run_uninst --yes'
t "modified file kept"          '[[ -f "$MOD" ]] && grep -q "kept:" "$TMP/out"'
t "user-added file kept"        '[[ -f "$USER_FILE" ]]'
t "other files removed"         '[[ ! -e "$D/plasma/desktoptheme/@@N:plasma_style:Light@@" && ! -e "$D/color-schemes/@@N:color_scheme:Light@@.colors" ]]'
t "foreign original restored"   '[[ "$(sha "$D/color-schemes/@@N:color_scheme:Dark@@.colors")" == "$orig_foreign" ]]'
t "gtk.css still untouched"     '[[ "$(sha "$C/gtk-4.0/gtk.css")" == "$orig_gtk4" ]]'
t "unrelated files still untouched" '[[ "$(sha "$D/color-schemes/Other.colors")" == "$orig_other" && "$(sha "$D/themes/SomeOtherTheme/gtk-3.0/gtk.css")" == "$orig_theme" ]]'
t "manifest still lists kept file" 'grep -q "desktoptheme/@@N:plasma_style:Dark@@/metadata.json" "$D/@@COMMAND@@/manifest.tsv"'

section "Forced uninstall"
t "uninstall --force succeeds"  'run_uninst --yes --force --purge-backups'
t "modified file removed"       '[[ ! -e "$MOD" ]]'
t "user-added file still kept"  '[[ -f "$USER_FILE" ]]'
t "manifest gone"               '[[ ! -e "$D/@@COMMAND@@/manifest.tsv" ]]'
rm -f "$USER_FILE"
run_uninst --yes >/dev/null 2>&1
t "only the user's own files remain" '[[ -z "$(find "$H" -path "$H/.stub" -prune -o -type f -print | grep -v -e "/color-schemes/@@N:color_scheme:Dark@@.colors$" -e "/color-schemes/Other.colors$" -e "/gtk-4.0/gtk.css$" -e "SomeOtherTheme")" ]]'
t "second uninstall is harmless" 'run_uninst --yes'

# ================================================================ activation with stubbed tools
section "Activation + settings restore (stubbed Plasma tools)"
new_home act
export PATH="$STUBS:$PATH"
t "KDE install --activate=light" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --activate=light --yes'
t "colour scheme applied"       'grep -q "plasma-apply-colorscheme @@N:color_scheme:Light@@" "$STUB_STATE/calls.log"'
t "plasma style applied"        'grep -q "plasma-apply-desktoptheme @@N:plasma_style:Light@@" "$STUB_STATE/calls.log"'
t "icons applied"               'grep -q "plasma-changeicons @@N:icons:Light@@" "$STUB_STATE/calls.log"'
t "kvantum theme applied"        'grep -q "kvantummanager --set @@N:kvantum:Light@@" "$STUB_STATE/calls.log" && grep -q "kwriteconfig6 .*widgetStyle kvantum" "$STUB_STATE/calls.log"'
t "wallpaper applied"           'grep -q "plasma-apply-wallpaperimage .*wallpapers/@@SLUG@@" "$STUB_STATE/calls.log"'
t "Aurorae decoration applied"  'grep -q "kwriteconfig6 .*kdecoration2 --key theme __aurorae__svg__@@N:aurorae:Light@@" "$STUB_STATE/calls.log"'
t "cursors applied"             'grep -q "plasma-apply-cursortheme @@N:cursors:Light@@" "$STUB_STATE/calls.log"'
t "splash applied"              'grep -q "kwriteconfig6 --file ksplashrc .*@@LNF@@.light" "$STUB_STATE/calls.log"'
t "panel left alone without --panel" '! grep -q "org.kde.plasma.kickoff" "$STUB_STATE/calls.log"'
t "previous KDE settings recorded" 'grep -q "colorscheme	-	BreezeDark" "$D/@@COMMAND@@/previous-settings.tsv"'
t "re-activation keeps original values" 'XDG_CURRENT_DESKTOP=KDE STUB_CS=@@N:color_scheme:Light@@ run_inst --variant dark --activate --yes && [[ $(grep -c "colorscheme" "$D/@@COMMAND@@/previous-settings.tsv") -eq 1 ]]'
: > "$STUB_STATE/calls.log"
t "uninstall restores settings" 'run_uninst --yes'
t "Kvantum + widget style restored" 'grep -q "kvantummanager --set Default" "$STUB_STATE/calls.log" && grep -q "widgetStyle Breeze" "$STUB_STATE/calls.log"'
t "decoration, cursor, splash restored" 'grep -q "kdecoration2 --key theme Breeze" "$STUB_STATE/calls.log" && grep -q "plasma-apply-cursortheme breeze_cursors" "$STUB_STATE/calls.log" && grep -q "ksplashrc --group KSplash --key Theme org.kde.breeze.desktop" "$STUB_STATE/calls.log"'
t "KDE colour scheme restored"  'grep -q "plasma-apply-colorscheme BreezeDark" "$STUB_STATE/calls.log"'
t "settings file cleared"       '[[ ! -e "$D/@@COMMAND@@/previous-settings.tsv" ]]'
t "no @@NAME@@ files left"  '[[ -z "$(vh_files)" ]]'

# ================================================================ @@COMMAND@@ command + top panel
section "@@COMMAND@@ command, top panel, KVitals (stubbed Plasma)"
new_home cmd
t "KDE install --panel --kvitals --panel-colorizer" 'XDG_CURRENT_DESKTOP=KDE run_inst --desktop kde --variant both --panel --kvitals --panel-colorizer --yes'
t "KVitals requested from the AUR" 'grep -q "yay -S --needed plasma6-applets-kvitals-git" "$STUB_STATE/calls.log"'
t "Panel Colorizer requested from the AUR" 'grep -q "yay -S --needed .*plasma6-applets-panel-colorizer" "$STUB_STATE/calls.log"'
t "panel built via plasmashell"   'grep -q "evaluateScript" "$STUB_STATE/calls.log" && grep -q @@KEY@@Panel "$STUB_STATE/calls.log"'
t "panel styled by Panel Colorizer by default" 'grep -q "var @@PREFIX@@_FANCY = {" "$STUB_STATE/calls.log" && grep -q "@@PREFIX@@_STYLE_NAME = \"@@NAME@@ Fancy\"" "$STUB_STATE/calls.log"'
t "missing Panel Colorizer is reported" 'grep -q "Panel Colorizer .*missing" "$TMP/out" && grep -q "Panel Colorizer not installed" "$TMP/out"'
t "panel backup taken"            '[[ -d "$D/@@COMMAND@@/panel-backups" ]]'
mkdir -p "$C"; echo "original-panels" > "$C/plasma-org.kde.plasma.desktop-appletsrc"
t "panel preview"                 'run_vh panel && grep -q "36 px top panel" "$TMP/out"'
: > "$STUB_STATE/calls.log"
t "panel --apply --fancy"         'run_vh panel --apply --fancy && grep -q "var @@PREFIX@@_FANCY = {" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "panel --apply --style Islands (old name) builds Pills" 'run_vh panel --apply --style Islands && grep -q "@@PREFIX@@_STYLE_NAME = \"@@NAME@@ Pills\"" "$STUB_STATE/calls.log" && grep -q "\"@@KEY@@\":{\"islands\":true}" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "panel --apply --only removes the other panels" 'run_vh panel --apply --only && grep -q "@@PREFIX@@_ONLY = true" "$STUB_STATE/calls.log" && grep -q "Other panels" "$TMP/out"'
: > "$STUB_STATE/calls.log"
t "  without --only they stay"    'run_vh panel --apply && ! grep -q "var @@PREFIX@@_ONLY = true" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "panel --apply --plain"         'run_vh panel --apply --plain && grep -q evaluateScript "$STUB_STATE/calls.log" && ! grep -q "var @@PREFIX@@_FANCY =" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "Light edition gets the see-through white preset" 'STUB_CS=@@N:color_scheme:Light@@ run_vh panel --apply && grep -q "@@NAME@@ Fancy Light" "$STUB_STATE/calls.log" && grep -q "\"custom\":\"@@PANEL_LIGHT@@\"" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "panel --restyle light"         'run_vh panel --restyle light && grep -q "@@KEY@@Style" "$STUB_STATE/calls.log" && grep -q "\"custom\":\"@@PANEL_LIGHT@@\"" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "@@COMMAND@@ light restyles the panel" 'run_vh light && grep -q "@@KEY@@Style" "$STUB_STATE/calls.log" && grep -q "\"custom\":\"@@PANEL_LIGHT@@\"" "$STUB_STATE/calls.log"'
t "bad panel style exits 2"       'run_vh panel --apply --style Neon; [[ $? -eq 2 ]]'
t "installer rejects bad --panel-style" '! run_inst --desktop kde --panel-style Neon --yes'
t "panel --restore"               'run_vh panel --restore && grep -q original-panels "$C/plasma-org.kde.plasma.desktop-appletsrc" && grep -q "systemctl --user start plasma-plasmashell" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "@@COMMAND@@ dark"             'run_vh dark'
t "  applies the Global Theme"    'grep -q "plasma-apply-lookandfeel --apply @@LNF@@.dark" "$STUB_STATE/calls.log"'
t "  sets Kvantum + style"        'grep -q "kvantummanager --set @@N:kvantum:Dark@@" "$STUB_STATE/calls.log" && grep -q "widgetStyle kvantum" "$STUB_STATE/calls.log"'
t "  sets Konsole profile"        'grep -q "DefaultProfile @@N:konsole:Dark@@.profile" "$STUB_STATE/calls.log"'
t "  dims inactive windows (20)"  'grep -q "Effect-diminactive --key Strength 20" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "sync follows Light scheme"     'STUB_CS=@@N:color_scheme:Light@@ STUB_STYLE=kvantum run_vh sync && grep -q "DefaultProfile @@N:konsole:Light@@.profile" "$STUB_STATE/calls.log" && grep -q "kvantummanager --set @@N:kvantum:Light@@" "$STUB_STATE/calls.log"'
: > "$STUB_STATE/calls.log"
t "sync ignores other schemes"    'STUB_CS=BreezeDark run_vh sync && [[ ! -s "$STUB_STATE/calls.log" ]]'
t "sync keeps a user's own Konsole profile" 'STUB_CS=@@N:color_scheme:Dark@@ STUB_KP=Mine.profile run_vh sync && ! grep -q DefaultProfile "$STUB_STATE/calls.log"'
t "sync replaces another theme's Konsole profile" 'STUB_CS=@@N:color_scheme:Light@@ STUB_KP=@@SIBLING_PROFILE@@ run_vh sync && grep -q "DefaultProfile @@N:konsole:Light@@.profile" "$STUB_STATE/calls.log"'
t "dim 35"                        'run_vh dim 35 && grep -q "Strength 35" "$STUB_STATE/calls.log"'
t "bad subcommand exits 2"        'run_vh nonsense; [[ $? -eq 2 ]]'
t "uninstall keeps panel backups" 'run_uninst --yes && [[ -d "$D/@@COMMAND@@/panel-backups" ]] && grep -q "Panel backups stay" "$TMP/out"'
t "command + helper removed"      '[[ ! -e "$H/.local/bin/@@COMMAND@@" && ! -e "$C/autostart/@@COMMAND@@-sync.desktop" ]]'
t "cursor symlinks removed"       '[[ ! -e "$H/.icons/@@N:cursors:Dark@@" && ! -e "$H/.icons" ]]'

# ================================================================ Fastfetch
section "Six panel looks (Normal, Transparent, Invisible, Cards, Pills, Fancy)"
new_home looks
t "all six, each with a Light twin, installed" 'run_inst --components kde-panel,kde-command --variant dark --yes && [[ $(ls "$C/panel-colorizer/presets" | grep -c "^@@NAME@@") -eq 12 ]] && for l in Normal Transparent Invisible Cards Pills Fancy; do [[ -f "$C/panel-colorizer/presets/@@NAME@@ $l Light/settings.json" ]] || exit 1; done'
t "  no Light look uses the Complementary colours" '! grep -l Complementary "$C"/panel-colorizer/presets/*Light/settings.json'
for pair in "Base:Transparent" "Plain:Normal" "Invisible:Invisible" "normal:Normal" "Cards:Cards"; do
  t "panel --apply --look ${pair%%:*} -> ${pair##*:}" "run_vh panel --apply --look ${pair%%:*} && grep -q '@@PREFIX@@_STYLE_NAME = \"@@NAME@@ ${pair##*:}\"' \"\$STUB_STATE/calls.log\""
done
t "panel --look Pills changes the panel you have" 'run_vh panel --look Pills && grep -q "writeConfig(.globalSettings." "$STUB_STATE/calls.log" && grep -q "@@KEY@@Style., .@@NAME@@ Pills." "$STUB_STATE/calls.log" && grep -q "var ISL = !!(S.@@KEY@@" "$STUB_STATE/calls.log"'
t "  Light edition: the Light twin" 'STUB_CS=@@N:color_scheme:Light@@ run_vh panel --look Transparent && grep -q "@@NAME@@ Transparent Light" "$STUB_STATE/calls.log"'
t "a look stored by 1.7 (Islands) becomes Pills on a switch" 'STUB_PANEL_LOOK="@@NAME@@ Islands" run_vh panel --restyle light && grep -q "@@NAME@@ Pills Light" "$STUB_STATE/calls.log"'
t "  and the old base look becomes Transparent" 'STUB_PANEL_LOOK="@@NAME@@" run_vh panel --restyle dark && grep -q "@@KEY@@Style., .@@NAME@@ Transparent." "$STUB_STATE/calls.log"'
t "unknown look exits 2" 'run_vh panel --look Neon; [[ $? -eq 2 ]]'
t "installer: --panel-style Plain means Normal" 'run_inst --components kde-panel,kde-command --variant dark --panel --panel-style Plain --yes && grep -q "panel --apply --look Normal" "$TMP/out"'
t "installer: --panel-look Standard builds without Panel Colorizer" 'run_inst --components kde-panel,kde-command --variant dark --panel --panel-look Standard --yes && grep -q "panel --apply --plain" "$TMP/out"'
new_home oldlooks
pcp="$C/panel-colorizer/presets"; mkdir -p "$pcp/@@NAME@@ Islands" "$pcp/@@NAME@@" "$pcp/My Look" "$D/@@COMMAND@@"
cp "$ROOT/panel-colorizer/@@NAME@@ Pills/settings.json" "$pcp/@@NAME@@ Islands/settings.json"
cp "$ROOT/panel-colorizer/@@NAME@@ Transparent/settings.json" "$pcp/@@NAME@@/settings.json"
echo '{"mine":1}' > "$pcp/My Look/settings.json"
{ printf 'F\tkde-panel\t%s\t%s\n' "$(sha "$pcp/@@NAME@@ Islands/settings.json")" "$pcp/@@NAME@@ Islands/settings.json"
  printf 'F\tkde-panel\t%s\t%s\n' "$(sha "$pcp/@@NAME@@/settings.json")" "$pcp/@@NAME@@/settings.json"
  printf 'D\tkde-panel\t-\t%s\n' "$pcp/@@NAME@@ Islands" "$pcp/@@NAME@@"; } > "$D/@@COMMAND@@/manifest.tsv"
echo '{"edited":1}' > "$pcp/@@NAME@@/settings.json"   # you changed this one after installing
t "1.7 preset folders: ours go, edited and your own stay" 'run_inst --components kde-panel --variant dark --yes && [[ ! -e "$pcp/@@NAME@@ Islands" && -f "$pcp/@@NAME@@/settings.json" && -f "$pcp/My Look/settings.json" && -f "$pcp/@@NAME@@ Pills/settings.json" ]]'

section "Icons: about 145 folder types, 600 apps, 260 file types"
new_home icons
t "installed: folder sizes 16-96, apps, categories, file types" 'run_inst --components icons --variant dark --yes && I="$D/icons/@@N:icons:Dark@@" && for f in places/16/folder-git places/22/folder-cad places/24/folder-ssh places/32/folder-keys places/48/folder-finance places/64/folder-3d places/96/folder-vms apps/scalable/firefox apps/scalable/org.mozilla.firefox apps/scalable/freecad categories/scalable/applications-graphics mimetypes/scalable/image-vnd.dwg mimetypes/scalable/model-3mf mimetypes/scalable/application-x-bittorrent; do [[ -f "$I/$f.svg" ]] || exit 1; done'
t "  counts: about 145 folder types, 600 apps, 260 file types" 'I="$D/icons/@@N:icons:Dark@@"; f=$(ls "$I/places/48" | wc -l); a=$(ls "$I/apps/scalable" | wc -l); m=$(ls "$I/mimetypes/scalable" | wc -l); (( f >= 140 && f <= 160 && a >= 570 && a <= 680 && m >= 240 && m <= 290 ))'
t "  every installed SVG parses" 'python3 -I -c "import sys,pathlib,xml.etree.ElementTree as E; [E.parse(p) for p in pathlib.Path(sys.argv[1]).rglob(\"*.svg\")]" "$D/icons/@@N:icons:Dark@@"'
t "  no app is drawn with its own logo: every app icon is a @@NAME@@ tile" '! grep -L "@@NAME@@ .* app icon" "$D/icons/@@N:icons:Dark@@/apps/scalable/"*.svg | grep -v "@@COMMAND@@" | grep -q .'
t "  uninstall removes them" 'run_uninst --yes && [[ ! -e "$D/icons/@@N:icons:Dark@@" ]]'
echo "changed" > "$C/plasma-org.kde.plasma.desktop-appletsrc"

section "1.6: switch check, Global Theme + wallpaper restore, uninstall command, widget command"
new_home v16
mkdir -p "$C"; printf '[Containments][1][Wallpaper][org.kde.image][General]\nImage=file:///usr/share/wallpapers/Next/contents/images/1920x1080.png\n' > "$C/plasma-org.kde.plasma.desktop-appletsrc"
t "install --activate records Global Theme + wallpaper" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --activate=dark --yes && grep -q "^kde	lookandfeel	-	" "$D/@@COMMAND@@/previous-settings.tsv" && grep -q "^kde	wallpaper	-	/usr/share/wallpapers/Next/contents/images/1920x1080.png$" "$D/@@COMMAND@@/previous-settings.tsv"'
: > "$STUB_STATE/calls.log"
t "@@COMMAND@@ dark re-sets what the Global Theme skipped" 'run_vh dark && grep -q "plasma-apply-colorscheme @@N:color_scheme:Dark@@" "$STUB_STATE/calls.log" && grep -q "set directly" "$TMP/out"'
t "@@COMMAND@@ widget installs a bundled copy (recorded)" 'run_vh widget kvitals && [[ -f "$D/plasma/plasmoids/org.kde.plasma.kvitals/metadata.json" ]] && grep -q "plasmoids/org.kde.plasma.kvitals/metadata.json" "$D/@@COMMAND@@/manifest.tsv"'
: > "$STUB_STATE/calls.log"
t "@@COMMAND@@ uninstall --yes works from the kept copy" 'run_vh uninstall --yes && [[ ! -e "$H/.local/bin/@@COMMAND@@" && ! -e "$D/plasma/plasmoids/org.kde.plasma.kvitals" ]]'
t "  your Global Theme put back"   'grep -q "plasma-apply-lookandfeel -a org.fedoraproject.fedora.desktop" "$STUB_STATE/calls.log"'
new_home v16b
t "a switch without the installer records your look too" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --no-activate --yes && run_vh light && grep -q "^kde	colorscheme	-	BreezeDark$" "$D/@@COMMAND@@/previous-settings.tsv" && run_uninst --yes'

section "Fastfetch colours (opt-in)"
new_home ff
mkdir -p "$C/fastfetch"
cat > "$C/fastfetch/config.jsonc" <<'JSON'
// my own fastfetch config
{
  "logo": "arch",
  "display": { "separator": " -> " },
  "modules": ["title", {"type": "os", "keyColor": "31"}, "cpu"]
}
JSON
orig_ff="$(sha "$C/fastfetch/config.jsonc")"
t "not touched by a default KDE install" 'run_inst --desktop kde --variant dark --yes && [[ "$(sha "$C/fastfetch/config.jsonc")" == "$orig_ff" ]]'
t "--activate=light recolours Fastfetch for Light" 'run_inst --components fastfetch --variant both --activate=light --yes && grep -q "38;2;@@FF_LIGHT_ACCENT@@" "$C/fastfetch/config.jsonc" && run_uninst --yes'
t "--fastfetch recolours"         'run_inst --components fastfetch --variant dark --yes && grep -q "38;2;@@RGB_ACCENT@@" "$C/fastfetch/config.jsonc"'
t "  keeps comments and layout"   'grep -q "my own fastfetch config" "$C/fastfetch/config.jsonc" && grep -qF "\" -> \"" "$C/fastfetch/config.jsonc"'
t "  original kept"               '[[ "$(sha "$C/fastfetch/config.jsonc.@@COMMAND@@-original")" == "$orig_ff" ]]'
t "uninstall restores the original" 'run_uninst --yes && [[ "$(sha "$C/fastfetch/config.jsonc")" == "$orig_ff" ]]'
new_home ffw
mkdir -p "$C/fastfetch"
cat > "$C/fastfetch/config.jsonc" <<'JSON'
{
  "logo": {
    "type": "file",
    "source": "~/.config/fastfetch/@@SIBLING_COMMAND@@-logo.txt",
    "color": { "1": "38;2;214;154;80", "2": "39" }
  },
  "modules": ["title", "os"]
}
JSON
orig_ffw="$(sha "$C/fastfetch/config.jsonc")"
t "an older theme design's logo becomes the distro logo" 'run_inst --components fastfetch --variant light --yes && ! grep -q -- "-logo.txt" "$C/fastfetch/config.jsonc" && grep -q "38;2;@@FF_LIGHT_ACCENT@@" "$C/fastfetch/config.jsonc" && grep -q "\"modules\"" "$C/fastfetch/config.jsonc"'
t "  uninstall brings that design back" 'run_uninst --yes && [[ "$(sha "$C/fastfetch/config.jsonc")" == "$orig_ffw" ]]'
new_home ffd
t "--fastfetch-design (no config yet)" 'run_inst --components icons --fastfetch-design --variant light --yes'
t "  layout has no logo file, in @@NAME@@ colours" '! grep -q -- "-logo.txt" "$C/fastfetch/config.jsonc" && ! grep -q "\"source\"" "$C/fastfetch/config.jsonc" && grep -q "38;2;@@FF_LIGHT_ACCENT@@" "$C/fastfetch/config.jsonc" && [[ ! -e "$C/fastfetch/@@COMMAND@@-logo.txt" ]]'
t "  uninstall moves it aside"         'run_uninst --yes && [[ ! -e "$C/fastfetch/config.jsonc" ]]'

section "Missing programs: listed, installed only with consent"
new_home deps
t "--yes lists what's missing but installs nothing" 'XDG_CURRENT_DESKTOP=KDE run_inst --desktop kde --variant dark --yes && grep -q "What it needs" "$TMP/out" && grep -q "KVitals .*missing" "$TMP/out" && ! grep -q "running:" "$TMP/out" && ! grep -q "^yay" "$STUB_STATE/calls.log" 2>/dev/null'
t "  shows the exact install command"  'grep -q "sudo $(for p in pacman dnf zypper apt; do command -v $p >/dev/null && { echo $p; break; }; done)" "$TMP/out"'
new_home deps2
t "--install-deps --dry-run would install them" 'XDG_CURRENT_DESKTOP=KDE run_inst --desktop kde --variant dark --install-deps --dry-run && grep -q "would run: sudo" "$TMP/out" && grep -q "would run: yay -S --needed plasma6-applets-kvitals-git" "$TMP/out"'
t "--no-deps asks nothing and installs nothing" 'XDG_CURRENT_DESKTOP=KDE run_inst --desktop kde --variant dark --no-deps --dry-run && ! grep -q "would run:" "$TMP/out"'

new_home cachy
NOAUR="$TMP/noaur"; rm -rf "$NOAUR"; cp -a "$STUBS" "$NOAUR"; rm -f "$NOAUR/yay" "$NOAUR/paru"
printf '#!/usr/bin/env bash\necho "pacman $*" >> "$STUB_STATE/calls.log"\n[[ "$1" == -Si && "$2" == paru ]]\n' > "$NOAUR/pacman"; chmod +x "$NOAUR/pacman"
t "No AUR helper (Fedora, CachyOS...): the bundled widgets are offered" 'PATH="$NOAUR:${PATH//$STUBS:/}" XDG_CURRENT_DESKTOP=KDE run_inst --variant dark --install-deps --dry-run && grep -q "Bundled with @@NAME@@" "$TMP/out" && grep -q "they go in with the theme" "$TMP/out" && ! grep -q "paru" "$TMP/out"'
t "  --deps-report says bundled"  'PATH="$NOAUR:${PATH//$STUBS:/}" run_inst --deps-report && grep -q "^ITEM	KVitals	missing	.*	bundled:kvitals$" "$TMP/out" && grep -q "bundled:panel-colorizer$" "$TMP/out"'
new_home widgets
t "--widgets all installs both for your user" 'PATH="$NOAUR:${PATH//$STUBS:/}" run_inst --components kde-panel --widgets all --variant dark --yes && [[ -f "$D/plasma/plasmoids/org.kde.plasma.kvitals/metadata.json" && -f "$D/plasma/plasmoids/luisbocanegra.panel.colorizer/metadata.json" && -x "$D/plasma/plasmoids/luisbocanegra.panel.colorizer/contents/ui/tools/list_presets.sh" ]]'
t "  then they count as installed" 'PATH="$NOAUR:${PATH//$STUBS:/}" run_inst --deps-report && grep -q "^ITEM	KVitals	ok" "$TMP/out" && grep -q "^ITEM	Panel Colorizer	ok" "$TMP/out"'
t "  uninstall removes them"       'run_uninst --yes && [[ ! -e "$D/plasma/plasmoids/org.kde.plasma.kvitals" && ! -e "$D/plasma/plasmoids/luisbocanegra.panel.colorizer" ]]'
t "--widgets rejects unknown names" '! run_inst --widgets neon --yes'
QD="$TMP/qdfedora"; mkdir -p "$QD"; printf '#!/bin/sh\nexit 0\n' > "$QD/qdbus-qt6"; chmod +x "$QD/qdbus-qt6"
t "qdbus found under the Fedora name qdbus-qt6" '[[ "$(PATH="$QD:/usr/bin:/bin" bash -c ". $ROOT/lib/common.sh; vh_qdbus")" == qdbus-qt6 ]]'
t "  and by the @@COMMAND@@ command" 'grep -q "qdbus-qt6" "$ROOT/bin/@@COMMAND@@"'

new_home full
t "--full: programs, panel, Fastfetch and apply in one go" 'XDG_CURRENT_DESKTOP=KDE run_inst --desktop kde --variant dark --full --dry-run && grep -q "would run:" "$TMP/out" && grep -q "fastfetch" "$TMP/out" && grep -q "plasma-apply-colorscheme @@N:color_scheme:Dark@@" "$TMP/out"'
t "Full setup is offered first in a terminal" 'grep -q "ask_full$" "$ROOT/install.sh" && grep -q "Do the full setup?" "$ROOT/install.sh"'

section "An earlier install under its old id is moved over (asks first)"
if [[ -n "@@OLD_LNF_FIRST@@" ]]; then
  new_home migrate
  old="$D/plasma/look-and-feel/@@OLD_LNF_FIRST@@.dark"; mkdir -p "$old/contents" "$D/@@COMMAND@@"
  echo '{"KPlugin":{"Id":"@@OLD_LNF_FIRST@@.dark"}}' > "$old/metadata.json"; echo "[kdeglobals][General]" > "$old/contents/defaults"
  echo "mine" > "$old/contents/my-note.txt"                       # a file you added: stays
  { printf 'file\t%s\n' "$old"
    printf 'sum\t%s\t%s\n' "$old/metadata.json" "$(sha "$old/metadata.json")" "$old/contents/defaults" "$(sha "$old/contents/defaults")"
    printf 'setting\tkdeglobals\tKDE\tLookAndFeelPackage\torg.kde.breeze.desktop\n'; } > "$D/@@COMMAND@@/install-manifest.tsv"
  t "--no-migrate leaves it alone" 'XDG_CURRENT_DESKTOP=KDE run_inst --components kde-colors --variant dark --no-migrate --yes && [[ -f "$old/metadata.json" && -f "$D/@@COMMAND@@/install-manifest.tsv" ]]'
  t "with a yes it is moved over" 'XDG_CURRENT_DESKTOP=KDE STUB_LNF=@@OLD_LNF_FIRST@@.dark run_inst --variant both --yes && grep -q "An earlier @@NAME@@ is installed" "$TMP/out"'
  t "  the old Global Theme is gone, your own file stays" '[[ ! -e "$old/metadata.json" && ! -e "$old/contents/defaults" && -f "$old/contents/my-note.txt" ]]'
  t "  the old install record is put aside" '[[ ! -e "$D/@@COMMAND@@/install-manifest.tsv" ]] && ls "$D/@@COMMAND@@"/install-manifest.tsv.moved-* >/dev/null'
  t "  your look from before is kept for uninstall" 'grep -q "^kde	lookandfeel	-	org.kde.breeze.desktop$" "$D/@@COMMAND@@/previous-settings.tsv"'
  t "  the Dark edition you had is switched on" 'grep -q "plasma-apply-colorscheme @@N:color_scheme:Dark@@" "$STUB_STATE/calls.log"'
  t "  the new Global Theme is installed" '[[ -f "$D/plasma/look-and-feel/@@LNF@@.dark/metadata.json" ]]'
  run_uninst --yes
else
  ok "(no earlier ids for @@NAME@@)"
fi

section "Cursors move from ~/.local/share/icons (1.3.1 and older) to ~/.icons"
new_home curmove
old="$D/icons/@@N:cursors:Dark@@"; mkdir -p "$old/cursors" "$D/@@COMMAND@@"
cp "$ROOT/cursors/@@N:cursors:Dark@@/index.theme" "$old/index.theme"; ln -s default "$old/cursors/arrow"
printf 'F\tkde-cursors\t%s\t%s\nS\tkde-cursors\tdefault\t%s\nD\tkde-cursors\t-\t%s\nD\tkde-cursors\t-\t%s\n' \
  "$(sha "$old/index.theme")" "$old/index.theme" "$old/cursors/arrow" "$old" "$old/cursors" > "$D/@@COMMAND@@/manifest.tsv"
t "reinstall moves the cursors"       'run_inst --components kde-cursors --variant dark --yes && [[ ! -e "$old" && -f "$H/.icons/@@N:cursors:Dark@@/index.theme" ]]'
t "  old records gone from the manifest" '! grep -q "$old" "$D/@@COMMAND@@/manifest.tsv"'
t "  uninstall leaves nothing"        'run_uninst --yes && [[ ! -e "$H/.icons" ]]'

section "Launcher icon leaves the icon theme (1.4.6 and older) for hicolor"
new_home launcher
ol="$D/icons/@@N:icons:Dark@@/apps/scalable/@@COMMAND@@-launcher.svg"; mkdir -p "$(dirname "$ol")" "$D/@@COMMAND@@"
printf '<svg xmlns="http://www.w3.org/2000/svg"/>\n' > "$ol"
{ printf 'F\ticons\t%s\t%s\n' "$(sha "$ol")" "$ol"   # as 1.4.6 recorded it, with the folders it made
  for d in "$D/icons" "$D/icons/@@N:icons:Dark@@" "$D/icons/@@N:icons:Dark@@/apps" "$D/icons/@@N:icons:Dark@@/apps/scalable"; do
    printf 'D\ticons\t-\t%s\n' "$d"; done; } > "$D/@@COMMAND@@/manifest.tsv"
t "reinstall removes the old theme copy" 'run_inst --components icons --variant dark --yes && [[ ! -e "$ol" && -f "$D/icons/hicolor/22x22/apps/@@COMMAND@@-launcher.png" ]]'
t "  uninstall leaves nothing"          'run_uninst --yes && [[ ! -e "$D/icons/@@N:icons:Dark@@" && ! -e "$D/icons/hicolor/22x22/apps/@@COMMAND@@-launcher.png" ]]'

section "GTK apps on Plasma (Firefox, GIMP, Inkscape ...)"
new_home gtk
gtk_is() { [[ "$(cat "$STUB_STATE/gtk" 2>/dev/null)" == "$1" ]]; }
t "GTK 3/4 theme installed for both editions" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --no-activate --yes && ( for T in Dark Light; do [[ -f "$D/themes/$(tw_name gtk "$T")/gtk-3.0/gtk.css" && -f "$D/themes/$(tw_name gtk "$T")/gtk-4.0/gtk.css" && -f "$D/themes/$(tw_name gtk "$T")/gtk-3.0/assets/check-symbolic.svg" && ! -e "$D/themes/$(tw_name gtk "$T")/gnome-shell" ]] || exit 1; done )'
t "  not switched on without --activate" '! grep -q setGtkTheme "$STUB_STATE/calls.log"'
echo Mine-GTK > "$STUB_STATE/gtk"
t "--activate records your GTK theme, then switches" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --activate=dark --yes && grep -q "^kde	gtk	-	Mine-GTK$" "$D/@@COMMAND@@/previous-settings.tsv" && gtk_is @@N:gtk:Dark@@'
t "sync follows Light while @@NAME@@ is the GTK theme" 'STUB_CS=@@N:color_scheme:Light@@ run_vh sync && gtk_is @@N:gtk:Light@@'
t "  but leaves a GTK theme of your own alone" 'echo Other-GTK > "$STUB_STATE/gtk"; STUB_CS=@@N:color_scheme:Dark@@ run_vh sync && gtk_is Other-GTK'
t "@@COMMAND@@ gtk off: yours again, and dark|light leave it" 'echo @@N:gtk:Dark@@ > "$STUB_STATE/gtk"; run_vh gtk off && gtk_is Mine-GTK && run_vh dark && gtk_is Mine-GTK'
t "@@COMMAND@@ gtk on: back to @@NAME@@" 'run_vh gtk on && gtk_is @@N:gtk:Dark@@ && [[ ! -e "$D/@@COMMAND@@/gtk-off" ]]'
t "uninstall puts your GTK theme back" 'run_uninst --yes && gtk_is Mine-GTK && [[ ! -e "$D/themes/@@N:gtk:Dark@@" && ! -e "$D/@@COMMAND@@/gtk-off" ]]'
new_home gtkini
mkdir -p "$C/gtk-3.0"; printf '[Settings]\ngtk-font-name=Noto Sans,  10\ngtk-theme-name=Mine-GTK\n' > "$C/gtk-3.0/settings.ini"
t "No Plasma GTK settings: only the theme line of GTK's settings.ini changes" 'STUB_NO_GTKCONFIG=1 XDG_CURRENT_DESKTOP=KDE run_inst --variant both --activate=light --yes && grep -qx "gtk-theme-name=@@SLUG@@-Light" "$C/gtk-3.0/settings.ini" && grep -qx "gtk-font-name=Noto Sans,  10" "$C/gtk-3.0/settings.ini" && grep -qx "gtk-theme-name=@@SLUG@@-Light" "$C/gtk-4.0/settings.ini" && grep -q "^kde	gtk	-	Mine-GTK$" "$D/@@COMMAND@@/previous-settings.tsv"'
t "  uninstall puts it back" 'STUB_NO_GTKCONFIG=1 run_uninst --yes && grep -qx "gtk-theme-name=Mine-GTK" "$C/gtk-3.0/settings.ini" && grep -qx "gtk-font-name=Noto Sans,  10" "$C/gtk-3.0/settings.ini"'
new_home gtkno
t "--without kde-gtk leaves GTK apps alone" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant dark --without kde-gtk --activate=dark --yes && [[ ! -e "$D/themes" ]] && ! grep -q setGtkTheme "$STUB_STATE/calls.log"'
t "Setup: GTK apps Leave alone" '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-gtk-off)" == *"--without kde-gtk"* ]]'

section "@@NAME@@ Settings + Setup (driven through a pseudo-terminal)"
t "Setup with the defaults"         '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-defaults)" == *"COMMAND: --variant both --yes --no-deps --panel --panel-style Fancy"*"--activate=dark"* ]]'
t "Setup: Light, Pills, design, sync off, dim off" 'o="$(python3 "$ROOT/tests/tui-test.py" setup-choices)"; [[ "$o" == *"--panel --panel-style Pills --only-panel --fastfetch-design --no-autosync --activate=light"* && "$o" == *"THEN: dim off"* ]]'
t "Setup: a panel look by name (Invisible)" '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-look)" == *"--panel-style Invisible"* ]]'
t "Setup: Standard = no Panel Colorizer" 'o="$(python3 "$ROOT/tests/tui-test.py" setup-addons)"; [[ "$o" == *"--plain-panel"* && "$o" != *panel-colorizer* ]]'
t "Setup: narrow terminal shows the look as N of 7" '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-narrow)" == NARROW-OK ]]'
t "Setup: Later + keep my panel"    '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-later)" == *"--no-panel"*"--no-activate"* ]]'
t "Setup: add-ons come from install.sh" 'o="$(python3 "$ROOT/tests/tui-test.py" setup-addons)"; [[ "$o" == *"ADDONS: "*"yay -S --needed plasma6-applets-kvitals-git"* && "$o" != *panel-colorizer* ]]'
t "Setup: q changes nothing"        '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-quit)" == NOTHING ]]'
new_home setuprun
t "Setup installs for real (stubbed Plasma)" 'HOME="$H" python3 "$ROOT/tests/tui-test.py" setup-install > "$TMP/out" 2>&1; grep -q "INSTALLED" "$TMP/out" && [[ -f "$D/color-schemes/@@N:color_scheme:Dark@@.colors" && -f "$D/color-schemes/@@N:color_scheme:Light@@.colors" ]]'
t "  and keeps a log in your home"  'ls "$H"/@@COMMAND@@-install-*.log >/dev/null 2>&1 && grep -q "plasma-apply-colorscheme @@N:color_scheme:Dark@@" "$H"/@@COMMAND@@-install-*.log'
t "  uninstall afterwards"          'run_uninst --yes && [[ ! -e "$D/color-schemes/@@N:color_scheme:Dark@@.colors" ]]'
t "80 x 24: Setup Add-ons with every add-on listed fits (rows, Continue, help, keys apart)" '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-addons-80)" == ADDONS80-OK ]]'
t "80 x 24: Settings Add-ons shows every row, the full reason below" '[[ "$(python3 "$ROOT/tests/tui-test.py" settings-addons-80)" == SADDONS80-OK ]]'
t "80 x 24: Setup step names fit" '[[ "$(python3 "$ROOT/tests/tui-test.py" setup-steps-80)" == STEPS80-OK ]]'
t "80 x 24: Settings opens and quits cleanly" '[[ "$(python3 "$ROOT/tests/tui-test.py" settings-quit-80)" == SQUIT80-OK ]]'
t "Settings: Status page opens"     '[[ "$(python3 "$ROOT/tests/tui-test.py" settings-status)" == STATUS-OK ]]'
t "Settings: Add-ons page opens"    '[[ "$(python3 "$ROOT/tests/tui-test.py" settings-addons)" == ADDONS-OK ]]'
new_home about
echo Mine-GTK > "$STUB_STATE/gtk"
tui() { HOME="$H" XDG_DATA_HOME="" XDG_CONFIG_HOME="" python3 "$ROOT/tests/tui-test.py" "$@"; }
t "About page (80 x 24): version, edition, GTK theme, installed, Uninstall row" 'XDG_CURRENT_DESKTOP=KDE run_inst --variant both --activate=dark --yes && gtk_is @@N:gtk:Dark@@ && [[ "$(tui settings-about-80)" == ABOUT80-OK ]]'
t "  Uninstall > No changes nothing" '[[ "$(tui settings-uninstall-no)" == NO-OK ]] && [[ -f "$D/@@COMMAND@@/manifest.tsv" && -x "$H/.local/bin/@@COMMAND@@-settings" ]] && gtk_is @@N:gtk:Dark@@'
t "  Uninstall > Yes: removes @@NAME@@, closes with the message" '[[ "$(tui settings-uninstall)" == UNINSTALLED-OK ]] && [[ ! -e "$D/@@COMMAND@@/manifest.tsv" && ! -e "$H/.local/bin/@@COMMAND@@-settings" && ! -e "$D/color-schemes/@@N:color_scheme:Dark@@.colors" ]]'
t "  ...and puts the previous look and GTK theme back" 'grep -q "plasma-apply-lookandfeel -a org.fedoraproject.fedora.desktop" "$STUB_STATE/calls.log" && gtk_is Mine-GTK'
new_home settingsapp
t "Settings app + menu entry installed" 'run_inst --components kde-command --variant dark --yes && [[ -x "$H/.local/bin/@@COMMAND@@-settings" && -f "$D/applications/@@COMMAND@@-settings.desktop" ]]'
t "  removed on uninstall"          'run_uninst --yes && [[ ! -e "$H/.local/bin/@@COMMAND@@-settings" && ! -e "$D/applications/@@COMMAND@@-settings.desktop" ]]'

printf '\n\e[1m%d passed, %d failed\e[0m\n' "$PASS" "$FAIL"
[[ $FAIL -eq 0 ]]
