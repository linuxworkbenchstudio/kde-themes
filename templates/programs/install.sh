#!/usr/bin/env bash
# @@NAME@@ - installer for KDE Plasma 6, Dark and Light editions (per-user, no root).
# Run ./install.sh in a terminal for @@NAME@@ Setup (guided); ./install.sh --help for options.
set -euo pipefail

VH_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$VH_ROOT/lib/common.sh"
VH_VERSION="$(cat "$VH_ROOT/VERSION" 2>/dev/null || echo unknown)"

# ------------------------------------------------------------------ components
ALL_COMPONENTS=(kde-colors kde-plasma kde-aurorae kde-kvantum kde-gtk kde-cursors kde-konsole kde-lookandfeel kde-wallpaper
                kde-widgets kde-panel kde-command icons fastfetch)
KDE_DEFAULT=(kde-colors kde-plasma kde-aurorae kde-kvantum kde-gtk kde-cursors kde-konsole kde-lookandfeel kde-wallpaper
             kde-panel kde-command icons)
OPTIONAL=(fastfetch)

declare -A DESC=(
  [kde-colors]="KDE colour schemes (System Settings > Colors)"
  [kde-plasma]="Plasma style: panel, launcher, menus, notifications, tooltips"
  [kde-aurorae]="Window decoration (Aurorae): rounded corners, focus border, @@NAME@@ close button"
  [kde-kvantum]="Kvantum widget style for Qt apps, translucent (needs Kvantum installed)"
  [kde-gtk]="GTK apps on Plasma (Firefox, GIMP, Inkscape...): GTK 3/4 theme, follows Dark/Light"
  [kde-cursors]="Cursor themes (Breeze cursors recoloured)"
  [kde-konsole]="Konsole colour scheme + profile"
  [kde-lookandfeel]="Plasma Global Theme: colours, style, decoration, icons, cursors, wallpaper, splash"
  [kde-wallpaper]="Plasma wallpaper package (switches dark/light automatically)"
  [kde-widgets]="Panel widgets KVitals + Panel Colorizer (bundled copies, for your user; only missing ones)"
  [kde-panel]="Top panel (KVitals stats, styled by Panel Colorizer) + presets; built only when you ask"
  [kde-command]="'@@COMMAND@@' command + @@NAME@@ Settings app + login sync helper"
  [icons]="@@NAME@@ icons: folders, apps, drives, file types + the launcher; inherits Papirus/Breeze"
  [fastfetch]="OPTIONAL: recolour your Fastfetch config (original kept; --fastfetch-design for the logo)"
)
declare -A DEPS=([kde-lookandfeel]="kde-colors kde-plasma kde-aurorae kde-cursors icons kde-wallpaper"
                [kde-panel]="icons kde-command")
declare -A PER_VARIANT=([kde-colors]=1 [kde-plasma]=1 [kde-aurorae]=1 [kde-kvantum]=1 [kde-gtk]=1 [kde-cursors]=1 [kde-konsole]=1
                        [kde-lookandfeel]=1 [icons]=1)
LNF_PREFIX="@@LNF@@"
OLD_LNF_PREFIXES=(@@OLD_LNF@@)   # earlier ids of this theme: moved over (ask first), see migrate_old

Title() { case "$1" in dark) echo Dark ;; light) echo Light ;; esac; }

# ------------------------------------------------------------------ usage
usage() {
  cat <<EOF
${C_B}@@NAME@@ ${VH_VERSION}${C_R} - KDE Plasma 6 theme installer (Dark and Light editions)

Usage:
  ./install.sh                         @@NAME@@ Setup: a guided installer in the terminal
  ./install.sh --text                  the same as plain questions (no full-screen screens)
  ./install.sh [options]               install with the options below, no guide

Choose what to install:
  -v, --variant dark|light|both    edition(s) to install (default: both)
  -c, --components LIST            exact comma-separated component list (see --list)
  -w, --with LIST                  add optional components (fastfetch)
      --without LIST               drop components from the selection (e.g. kde-gtk: leave GTK apps alone)
  (GNOME is not part of this release yet.)

Extras:
      --panel                      build the @@NAME@@ top panel now (your panels are backed up)
      --no-panel                   don't build it and don't ask
      --kvitals                    install the KVitals stats widget if missing (AUR with yay/paru,
                                   otherwise the copy bundled with @@NAME@@, for your user)
      --panel-colorizer            install Panel Colorizer if missing, the same way - it
                                   styles the panel; without the flag the installer checks and asks
      --panel-look NAME            panel look: Normal, Transparent, Invisible, Cards, Pills, Fancy
                                   (default) or Standard (no Panel Colorizer); --panel-style also works.
                                   Older names work: Base = Transparent, Islands = Pills, Plain = Normal
      --widgets LIST               install the bundled copies now: kvitals, panel-colorizer (or all)
      --plain-panel                build the panel without Panel Colorizer
      --only-panel                 make it the only panel on the main screen (removes Plasma's
                                   default bottom panel; backed up, @@COMMAND@@ panel --restore)
      --migrate / --no-migrate     an earlier @@NAME@@ under its old ids: move it over without asking /
                                   leave it as it is (asked otherwise)
      --no-autosync                don't add the login helper that keeps Kvantum/Konsole/Fastfetch in step
      --fastfetch                  recolour your Fastfetch config (same as --with fastfetch)
      --fastfetch-design           use the @@NAME@@ Fastfetch design (its logo) instead

Full setup:
      --full                       everything in one go: install missing programs, build the top
                                   panel, recolour Fastfetch and switch the theme on

Programs the theme uses (Kvantum, qdbus, KVitals, Panel Colorizer, Fastfetch, Papirus...):
                                   checked before installing; missing ones are listed with the
                                   exact command and installed only if you agree
      --install-deps               install missing programs without asking (uses sudo / your AUR helper)
      --no-deps                    don't offer to install missing programs
      --deps-report                list what the chosen parts need, one per line, and stop

Behaviour:
      --activate[=dark|light]      switch @@NAME@@ on afterwards (default edition: the first installed)
      --no-activate                never switch it on (default when not interactive)
  -y, --yes                        do not ask questions (non-interactive)
  -n, --dry-run                    show what would happen, change nothing
      --log FILE                   also write everything shown to FILE
      --allow-root                 permit running as root (installs into root's own home)

Information:
  -l, --list                       list components, targets and install status
      --detect                     print the detected desktop and tools
  -V, --version                    print version
  -h, --help                       this help

Examples:
  ./install.sh --variant both --activate=dark --yes
  ./install.sh --full
  ./install.sh --components kde-colors,icons --variant light
  ./install.sh --panel --kvitals --panel-colorizer

Everything installs under \$XDG_DATA_HOME (${VH_DATA/#$HOME/\~}), \$XDG_CONFIG_HOME, ~/.icons and
~/.local/bin; nothing outside your home directory is touched (programs only with your consent).
Existing files are backed up before being replaced. Remove with ./uninstall.sh.
EOF
}

# ------------------------------------------------------------------ targets
targets_for() { # component variant -> human-readable target(s)
  local c="$1" v="${2:-dark}" T; T="$(Title "$v")"
  case "$c" in
    kde-colors) echo "$VH_DATA/color-schemes/$(tw_name color_scheme "$T").colors" ;;
    kde-plasma) echo "$VH_DATA/plasma/desktoptheme/$(tw_name plasma_style "$T")/" ;;
    kde-aurorae) echo "$VH_DATA/aurorae/themes/$(tw_name aurorae "$T")/" ;;
    kde-kvantum) echo "$VH_CONFIG/Kvantum/$(tw_name kvantum "$T")/" ;;
    kde-gtk) echo "$VH_DATA/themes/$(tw_name gtk "$T")/{gtk-3.0,gtk-4.0}/" ;;
    kde-cursors) echo "$VH_CURSORS/$(tw_name cursors "$T")/" ;;
    kde-widgets) echo "$VH_DATA/plasma/plasmoids/{org.kde.plasma.kvitals,luisbocanegra.panel.colorizer}/" ;;
    kde-panel) echo "$VH_STATE_DIR/panel/ + $VH_CONFIG/panel-colorizer/presets/@@NAME@@*/" ;;
    kde-command) echo "$VH_BIN/@@COMMAND@@{,-settings} + autostart + app-menu entry" ;;
    fastfetch) echo "$VH_STATE_DIR/fastfetch/ + colours in your ~/.config/fastfetch/config.jsonc" ;;
    kde-konsole) echo "$VH_DATA/konsole/$(tw_name konsole "$T").{colorscheme,profile}" ;;
    kde-lookandfeel) echo "$VH_DATA/plasma/look-and-feel/$LNF_PREFIX.$v/" ;;
    kde-wallpaper) echo "$VH_DATA/wallpapers/@@SLUG@@/" ;;
    icons) echo "$VH_DATA/icons/$(tw_name icons "$T")/ + logo in $VH_DATA/icons/hicolor/" ;;
  esac
}

component_installed() { # component -> 0 if manifest has entries for it
  local key
  for key in "${VH_MF_ORDER[@]}"; do
    [[ -n "${VH_MF[$key]+x}" ]] || continue
    [[ "${VH_MF[$key]%%$'\t'*}" == "$1" ]] && return 0
  done
  return 1
}

list_components() {
  vh_manifest_load
  printf '%s%-17s %-10s %s%s\n' "$C_B" "COMPONENT" "STATUS" "DESCRIPTION" "$C_R"
  local c st
  for c in "${ALL_COMPONENTS[@]}"; do
    if component_installed "$c"; then st="${C_OK}installed${C_R}"; else st="-        "; fi
    printf '%-17s %s  %s\n' "$c" "$st" "${DESC[$c]}"
    printf '%-17s            %s%s%s\n' "" "$C_D" "$(targets_for "$c" dark | sed "s|$HOME|~|g")" "$C_R"
  done
  echo
  printf 'Defaults: %s\n' "${KDE_DEFAULT[*]}"
  printf 'Optional (opt-in): %s\n' "${OPTIONAL[*]}"
  printf 'SDDM login screen: manual only - see sddm/README.md\n'
}

# ------------------------------------------------------------------ component installers
inst_kde_colors() { local T; T="$(Title "$1")"
  vh_install_file kde-colors "$VH_ROOT/color-schemes/$(tw_name color_scheme "$T").colors" "$VH_DATA/color-schemes/$(tw_name color_scheme "$T").colors"; }
inst_kde_plasma() { local T; T="$(Title "$1")"
  vh_install_tree kde-plasma "$VH_ROOT/plasma/desktoptheme/$(tw_name plasma_style "$T")" "$VH_DATA/plasma/desktoptheme/$(tw_name plasma_style "$T")"; }
inst_kde_aurorae() { local T; T="$(Title "$1")"
  vh_install_tree kde-aurorae "$VH_ROOT/aurorae/themes/$(tw_name aurorae "$T")" "$VH_DATA/aurorae/themes/$(tw_name aurorae "$T")"; }
inst_kde_cursors() {
  local T src dst a b rc=0; T="$(Title "$1")"
  src="$VH_ROOT/cursors/$(tw_name cursors "$T")"; dst="$VH_CURSORS/$(tw_name cursors "$T")"
  # 1.3.1 and older put the cursors in ~/.local/share/icons, where Plasma's cursor settings don't look
  vh_retire_tree "$VH_DATA/icons/$(tw_name cursors "$T")"
  vh_install_tree kde-cursors "$src" "$dst" || rc=1
  while read -r a b; do
    [[ -z "$a" || "$a" == \#* ]] && continue
    vh_install_symlink kde-cursors "$b" "$dst/cursors/$a" || rc=1
  done < "$src/aliases.txt"
  return $rc; }
inst_kde_panel() {
  local d rc=0
  # 1.7 and earlier: "@@NAME@@" (now Transparent) and "@@NAME@@ Islands" (now Pills)
  for d in "@@NAME@@" "@@NAME@@ Light" "@@NAME@@ Islands" "@@NAME@@ Islands Light"; do
    vh_retire_tree "$VH_CONFIG/panel-colorizer/presets/$d"
  done
  vh_install_file kde-panel "$VH_ROOT/panel/@@COMMAND@@-panel.js" "$VH_STATE_DIR/panel/@@COMMAND@@-panel.js" || rc=1
  for d in "$VH_ROOT"/panel-colorizer/*/; do
    d="${d%/}"
    vh_install_tree kde-panel "$d" "$VH_CONFIG/panel-colorizer/presets/$(basename -- "$d")" || rc=1
  done
  # copies of the bundled widgets, so @@NAME@@ Settings > Add-ons can add them later
  vh_install_tree kde-panel "$VH_ROOT/widgets" "$VH_STATE_DIR/widgets" || rc=1
  return $rc; }
inst_kde_widgets() {
  local w id src dst rc=0 seen=" "
  for w in "${WIDGETS_WANT[@]}"; do
    [[ "$seen" == *" $w "* ]] && continue; seen+="$w "
    case "$w" in kvitals) id=org.kde.plasma.kvitals ;; panel-colorizer) id=luisbocanegra.panel.colorizer ;; esac
    if [[ -d "/usr/share/plasma/plasmoids/$id" ]]; then vh_dim "$id: your system already has it"; continue; fi
    src="$VH_ROOT/widgets/$id"; dst="$VH_DATA/plasma/plasmoids/$id"
    vh_install_tree kde-widgets "$src" "$dst" README.md || rc=1
    # helper scripts inside the widget must stay runnable
    [[ "$VH_DRY_RUN" == 1 ]] || find "$dst" -path '*/tools/*' \( -name '*.sh' -o -name '*.py' \) -exec chmod 755 {} + 2>/dev/null || true
  done
  return $rc; }
inst_kde_command() {
  vh_install_file kde-command "$VH_ROOT/bin/@@COMMAND@@" "$VH_BIN/@@COMMAND@@" 755 || return 1
  # a copy of the uninstaller, so `@@COMMAND@@ uninstall` works after the download is gone
  vh_install_file kde-command "$VH_ROOT/uninstall.sh" "$VH_STATE_DIR/uninstaller/uninstall.sh" 755
  vh_install_file kde-command "$VH_ROOT/lib/common.sh" "$VH_STATE_DIR/uninstaller/lib/common.sh"
  vh_install_file kde-command "$VH_ROOT/VERSION" "$VH_STATE_DIR/uninstaller/VERSION"
  vh_install_file kde-command "$VH_ROOT/bin/@@COMMAND@@-settings" "$VH_BIN/@@COMMAND@@-settings" 755
  vh_install_file kde-command "$VH_ROOT/bin/@@COMMAND@@-settings.desktop" "$VH_DATA/applications/@@COMMAND@@-settings.desktop"
  if [[ $NO_AUTOSYNC -eq 0 ]]; then
    vh_install_file kde-command "$VH_ROOT/bin/@@COMMAND@@-sync.desktop" "$VH_CONFIG/autostart/@@COMMAND@@-sync.desktop"
  fi
  path_note; }
path_note() {
  [[ -n "${PATH_NOTED:-}" ]] && return 0; PATH_NOTED=1
  case ":$PATH:" in *":$VH_BIN:"*) return 0 ;; esac
  vh_warn "${VH_BIN/#$HOME/\~} is not on your PATH yet - add it once:"
  case "$(basename -- "${SHELL:-}")" in
    fish) vh_more "fish_add_path ~/.local/bin      (works straight away)" ;;
    zsh)  vh_more "echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
          vh_more "then open a new terminal" ;;
    *)    vh_more "echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
          vh_more "then open a new terminal" ;;
  esac
  vh_more "or run it as ~/.local/bin/@@COMMAND@@"; }
inst_fastfetch() {
  local dir="$VH_STATE_DIR/fastfetch" variant="$1" from=() tmp
  vh_install_file fastfetch "$VH_ROOT/fastfetch/@@COMMAND@@-fastfetch.py" "$dir/@@COMMAND@@-fastfetch.py" 755 || return 1
  vh_install_file fastfetch "$VH_ROOT/fastfetch/install-fastfetch-colours.sh" "$dir/install-fastfetch-colours.sh" 755
  vh_install_tree fastfetch "$VH_ROOT/fastfetch/design" "$dir/design"
  vh_have python3 || { vh_warn "python3 not found - Fastfetch colours not applied (files are in ${dir/#$HOME/\~})"; return 1; }
  # the logo sits next to your config (also used when another theme's design is switched over)
  vh_install_file fastfetch "$VH_ROOT/fastfetch/design/@@COMMAND@@-logo.txt" "$VH_CONFIG/fastfetch/@@COMMAND@@-logo.txt" || return 1
  if [[ $FF_DESIGN -eq 1 ]]; then
    tmp="$(mktemp)"
    sed "s|~/.config/fastfetch/@@COMMAND@@-logo.txt|$VH_CONFIG/fastfetch/@@COMMAND@@-logo.txt|" "$VH_ROOT/fastfetch/design/config.jsonc" > "$tmp"
    from=(--from "$tmp")
  fi
  if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "recolour Fastfetch config ($variant${from:+, @@NAME@@ design})"; return 0; fi
  if python3 -I "$dir/@@COMMAND@@-fastfetch.py" --apply --quiet --variant "$variant" "${from[@]}"; then
    vh_mf_set R fastfetch fastfetch -
  else
    vh_warn "Fastfetch recolour failed - run ${dir/#$HOME/\~}/install-fastfetch-colours.sh --apply later"
  fi
  [[ -n "${tmp:-}" ]] && rm -f -- "$tmp"
  return 0; }
inst_kde_kvantum() { local T; T="$(Title "$1")"
  vh_install_tree kde-kvantum "$VH_ROOT/Kvantum/$(tw_name kvantum "$T")" "$VH_CONFIG/Kvantum/$(tw_name kvantum "$T")" || return 1
  if ! vh_have kvantummanager; then
    if [[ -z "${KV_WARNED:-}" ]]; then
      vh_warn "Kvantum is not installed - the files are in place for when it is"
      if vh_have pacman; then vh_more "install: sudo pacman -S kvantum"
      elif vh_have dnf; then vh_more "install: sudo dnf install kvantum"
      elif vh_have apt; then vh_more "install: sudo apt install qt6-style-kvantum"
      else vh_more "install your distribution's 'kvantum' package"; fi
    fi
    KV_WARNED=1
  fi; }
inst_kde_gtk() { local T base="" b; T="$(Title "$1")"
  vh_install_tree kde-gtk "$VH_ROOT/gtk/$(tw_name gtk "$T")" "$VH_DATA/themes/$(tw_name gtk "$T")" || return 1
  # GTK 2 apps: lean on the system's Breeze GTK 2 theme when there is one
  for b in "Breeze-$T" Breeze; do
    [[ -f "/usr/share/themes/$b/gtk-2.0/gtkrc" ]] && { base="/usr/share/themes/$b/gtk-2.0/gtkrc"; break; }
  done
  [[ -z "$base" ]] || vh_install_rendered kde-gtk "$VH_ROOT/gtk/gtk-2.0.gtkrc.in" "$VH_DATA/themes/$(tw_name gtk "$T")/gtk-2.0/gtkrc" '@BASE@' "$base"; }
inst_kde_konsole() { local T; T="$(Title "$1")"
  vh_install_file kde-konsole "$VH_ROOT/konsole/$(tw_name konsole "$T").colorscheme" "$VH_DATA/konsole/$(tw_name konsole "$T").colorscheme"
  vh_install_file kde-konsole "$VH_ROOT/konsole/$(tw_name konsole "$T").profile" "$VH_DATA/konsole/$(tw_name konsole "$T").profile"; }
inst_kde_lookandfeel() {
  vh_install_tree kde-lookandfeel "$VH_ROOT/look-and-feel/$LNF_PREFIX.$1" "$VH_DATA/plasma/look-and-feel/$LNF_PREFIX.$1"; }
inst_kde_wallpaper() {
  vh_install_tree kde-wallpaper "$VH_ROOT/wallpapers/@@SLUG@@" "$VH_DATA/wallpapers/@@SLUG@@"; }
inst_icons() { local T src inh="" t; T="$(Title "$1")"; src="$VH_ROOT/icons/$(tw_name icons "$T")"
  # before 1.4.7 the launcher icon was also in the icon theme, where it would hide hicolor's new one
  vh_retire_tree "$VH_DATA/icons/$(tw_name icons "$T")/apps/scalable/@@COMMAND@@-launcher.svg"
  vh_install_tree icons "$src" "$VH_DATA/icons/$(tw_name icons "$T")" index.theme || return 1
  # inherit only the icon themes this system has (KDE warns about every missing one); hicolor always
  for t in $(sed -n 's/^Inherits=//p' "$src/index.theme" | tr ',' ' '); do
    { [[ "$t" == hicolor ]] || vh_icon_theme_present "$t"; } && inh="${inh:+$inh,}$t"
  done
  vh_install_rendered icons "$src/index.theme" "$VH_DATA/icons/$(tw_name icons "$T")/index.theme" '^Inherits=.*$' "Inherits=${inh:-hicolor}" || return 1
  # the logo also goes into hicolor (only our files), so the launcher shows with any icon theme
  vh_install_tree icons "$VH_ROOT/hicolor" "$VH_DATA/icons/hicolor"; }
# ------------------------------------------------------------------ activation
record_setting() { # tool target key value  (first value wins: the state from before @@NAME@@)
  [[ "$VH_DRY_RUN" == 1 ]] && return 0
  tw_mine "$4" && return 0   # already ours: nothing to go back to
  mkdir -p -- "$VH_STATE_DIR"
  if [[ -f "$VH_SETTINGS" ]] && awk -F'\t' -v a="$1" -v b="$2" -v c="$3" '$1==a&&$2==b&&$3==c{f=1}END{exit !f}' "$VH_SETTINGS"; then
    return 0
  fi
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$VH_SETTINGS"
}

run_cmd() { vh_dim "\$ $*"; [[ "$VH_DRY_RUN" == 1 ]] || "$@"; }

plasma_changeicons() {
  local p
  for p in plasma-changeicons /usr/lib/plasma-changeicons /usr/libexec/plasma-changeicons \
           /usr/lib/x86_64-linux-gnu/libexec/plasma-changeicons /usr/lib64/libexec/plasma-changeicons \
           /usr/lib/libexec/plasma-changeicons; do
    if [[ "$p" == /* && -x "$p" ]] || { [[ "$p" != /* ]] && vh_have "$p"; }; then printf '%s' "$p"; return 0; fi
  done
  return 1
}

activate_kde() {
  local v="$1" T prev ic; T="$(Title "$v")"
  vh_step "Activating @@NAME@@ $T on KDE Plasma"
  if vh_have kreadconfig6; then
    # the Global Theme and wallpaper first: on uninstall they go back first, then the single settings
    prev="$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage 2>/dev/null || true)"; record_setting kde lookandfeel - "${prev:-org.kde.breeze.desktop}"
    prev="$(vh_current_wallpaper)"; [[ -n "$prev" ]] && record_setting kde wallpaper - "$prev"
    prev="$(kreadconfig6 --file kdeglobals --group General --key ColorScheme 2>/dev/null || true)"; record_setting kde colorscheme - "${prev:-BreezeLight}"
    prev="$(kreadconfig6 --file plasmarc --group Theme --key name 2>/dev/null || true)"; record_setting kde desktoptheme - "${prev:-default}"
    prev="$(kreadconfig6 --file kdeglobals --group Icons --key Theme 2>/dev/null || true)"; record_setting kde icons - "${prev:-breeze}"
  fi
  if component_selected kde-colors && vh_have plasma-apply-colorscheme; then run_cmd plasma-apply-colorscheme "$(tw_name color_scheme "$T")" || vh_warn "colour scheme not applied"; fi
  if component_selected kde-plasma && vh_have plasma-apply-desktoptheme; then run_cmd plasma-apply-desktoptheme "$(tw_name plasma_style "$T")" || vh_warn "Plasma style not applied"; fi
  if component_selected icons; then
    if ic="$(plasma_changeicons)"; then run_cmd "$ic" "$(tw_name icons "$T")" || vh_warn "icons not applied"
    else vh_warn "plasma-changeicons not found: choose @@NAME@@ $T in System Settings > Icons"; fi
  fi
  if component_selected kde-kvantum; then
    if vh_have kvantummanager; then
      prev="$(sed -n 's/^theme=//p' "$VH_CONFIG/Kvantum/kvantum.kvconfig" 2>/dev/null | head -n1 || true)"
      record_setting kde kvantum - "${prev:-}"
      run_cmd kvantummanager --set "$(tw_name kvantum "$T")" || vh_warn "Kvantum theme not applied"
      if vh_have kwriteconfig6; then
        prev="$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle 2>/dev/null || true)"
        record_setting kde widgetstyle - "${prev:-Breeze}"
        run_cmd kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum
        vh_info "Qt apps pick up the Kvantum style when they restart."
      else
        vh_warn "kwriteconfig6 not found: choose 'kvantum' in System Settings > Application Style"
      fi
    else
      vh_warn "Kvantum not installed - Kvantum style not applied"
    fi
  fi
  if component_selected kde-gtk; then
    prev="$(vh_gtk_now)"; record_setting kde gtk - "${prev:-$(vh_gtk_default)}"
    vh_dim "\$ GTK apps: $(tw_name gtk "$T")"
    if [[ "$VH_DRY_RUN" != 1 ]]; then
      rm -f -- "$VH_STATE_DIR/gtk-off"
      vh_gtk_set "$(tw_name gtk "$T")" || vh_warn "GTK theme not applied - choose @@NAME@@ $T in System Settings > Application Style > GNOME/GTK"
    fi
  fi
  if component_selected kde-aurorae && vh_have kwriteconfig6; then
    prev="$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key library 2>/dev/null || true)|$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme 2>/dev/null || true)"
    [[ "$prev" == "|" ]] && prev="org.kde.breeze|Breeze"
    record_setting kde decoration - "$prev"
    run_cmd kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
    run_cmd kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "__aurorae__svg__$(tw_name aurorae "$T")"
    local q; q="$(vh_qdbus)" && { run_cmd "$q" org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true; }
  fi
  if component_selected kde-cursors && vh_have plasma-apply-cursortheme; then
    prev="$(kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme 2>/dev/null || true)"
    record_setting kde cursor - "${prev:-breeze_cursors}"
    if ! run_cmd plasma-apply-cursortheme "$(tw_name cursors "$T")"; then
      # fall back to the setting the Global Theme writes; KWin reads it at the next login
      run_cmd kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$(tw_name cursors "$T")" &&
        vh_warn "cursor theme set for the next login (Plasma could not switch it live)" ||
        vh_warn "cursor theme not applied"
    fi
  fi
  if component_selected kde-lookandfeel && vh_have kwriteconfig6; then
    prev="$(kreadconfig6 --file ksplashrc --group KSplash --key Theme 2>/dev/null || true)"
    record_setting kde splash - "${prev:-org.kde.breeze.desktop}"
    run_cmd kwriteconfig6 --file ksplashrc --group KSplash --key Engine KSplashQML
    run_cmd kwriteconfig6 --file ksplashrc --group KSplash --key Theme "$LNF_PREFIX.$v"
  fi
  if component_selected kde-wallpaper && vh_have plasma-apply-wallpaperimage; then
    run_cmd plasma-apply-wallpaperimage "$VH_DATA/wallpapers/@@SLUG@@" ||
      run_cmd plasma-apply-wallpaperimage "$VH_DATA/wallpapers/@@SLUG@@/contents/images$([[ $v == dark ]] && echo _dark)/3840x2160.jpg" ||
      vh_warn "wallpaper not applied"
  fi
  component_selected kde-command || vh_info "Konsole: Settings > Manage Profiles > '@@NAME@@ $T' > Set as Default (not changed automatically)."
}

# ------------------------------------------------------------------ an earlier install, under its old ids
# Waypoint 0.5.0 and older (org.waypoint.*, its install-manifest.tsv) and Vice Horizon 1.8 and older
# (org.digitalcohesion.vicehorizon.*): their Global Themes would sit next to the new ones and keep
# your desktop on the old copy. Found ones are moved over - only with your yes (--yes counts):
# your choices carry over, your desktop moves to the new id, the old copy goes (files you edited stay).
OLD_MANIFEST="$VH_STATE_DIR/install-manifest.tsv"
old_found() {
  local p e
  [[ -f "$OLD_MANIFEST" ]] && return 0
  for p in "${OLD_LNF_PREFIXES[@]}"; do for e in dark light; do
    [[ -d "$VH_DATA/plasma/look-and-feel/$p.$e" ]] && return 0
  done; done
  return 1
}
migrate_old() {
  [[ "$MIGRATE" == 0 ]] && return 0
  old_found || return 0
  local cur p e found="" look ff
  for p in "${OLD_LNF_PREFIXES[@]}"; do for e in dark light; do
    [[ -d "$VH_DATA/plasma/look-and-feel/$p.$e" ]] && found+="${found:+, }$p.$e"
  done; done
  [[ -f "$OLD_MANIFEST" ]] && found+="${found:+, }its install record"
  vh_step "An earlier @@NAME@@ is installed"
  vh_row "Found" "$found"
  vh_info "Moving it over keeps your choices (edition, panel look, Fastfetch, sync), switches your"
  vh_info "desktop to the new @@NAME@@ and removes the old copy. Files you edited are kept."
  if [[ "$MIGRATE" != 1 ]] && ! { [[ "$VH_ASSUME_YES" == 1 ]] || { can_ask && vh_confirm "Move it over?" y; }; }; then
    vh_dim "$G_SKIP left as it is - the new @@NAME@@ installs next to it"; return 0
  fi
  # 1. your choices
  cur="$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage 2>/dev/null || true)"
  for p in "${OLD_LNF_PREFIXES[@]}"; do
    case "$cur" in "$p.dark"|"$p.light") [[ -z "$ACTIVATE" ]] && ACTIVATE=1; [[ -z "$AV_WANT" ]] && AV_WANT="${cur##*.}" ;; esac
  done
  look="$(sed -n 's/^\(waypointLook\|@@KEY@@Look\|@@KEY@@Style\)=//p' "$VH_CONFIG/plasma-org.kde.plasma.desktop-appletsrc" 2>/dev/null | head -n1)"
  look="${look#@@NAME@@ }"; look="${look% Light}"
  [[ -n "$look" && "$PANEL_STYLE_SET" != 1 ]] && PANEL_STYLE="$look"
  for ff in "$VH_CONFIG/fastfetch/config.jsonc.@@COMMAND@@-original" "$VH_CONFIG/fastfetch/config.json5.@@COMMAND@@-original"; do
    [[ -f "$ff" ]] && { select_add fastfetch; break; }
  done
  # 2. your look from before the old version (so uninstall still puts it back)
  if [[ -f "$OLD_MANIFEST" ]]; then
    awk -F'\t' '$1=="setting" {print $2"\t"$3"\t"$4"\t"$5}' "$OLD_MANIFEST" | while IFS=$'\t' read -r f g k v; do
      [[ "$v" == "<unset>" ]] && v=""
      case "$f|$g|$k" in
        kdeglobals\|KDE\|LookAndFeelPackage) record_setting kde lookandfeel - "$v" ;;
        kdeglobals\|General\|ColorScheme) record_setting kde colorscheme - "$v" ;;
        plasmarc\|Theme\|name) record_setting kde desktoptheme - "$v" ;;
        kdeglobals\|Icons\|Theme) record_setting kde icons - "$v" ;;
        kcminputrc\|Mouse\|cursorTheme) record_setting kde cursor - "$v" ;;
        kdeglobals\|KDE\|widgetStyle) record_setting kde widgetstyle - "$v" ;;
        ksplashrc\|KSplash\|Theme) record_setting kde splash - "$v" ;;
        *kvantum.kvconfig\|General\|theme) record_setting kde kvantum - "$v" ;;
      esac
    done
  fi
  # 3. the old copy: the Global Themes under the old ids, and (Waypoint 0.5) every file its install
  #    record lists with its fingerprint - removed when unchanged, kept when you edited it
  for p in "${OLD_LNF_PREFIXES[@]}"; do for e in dark light; do
    [[ -d "$VH_DATA/plasma/look-and-feel/$p.$e" ]] || continue
    vh_retire_tree "$VH_DATA/plasma/look-and-feel/$p.$e"   # recorded by this installer (Vice Horizon 1.8)
  done; done
  if [[ -f "$OLD_MANIFEST" ]] && vh_have python3; then
    if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "would remove the old copy's unchanged files"
    else python3 -I - "$OLD_MANIFEST" "$HOME" <<'PY' || vh_warn "the old copy could not be removed completely - see $OLD_MANIFEST"
import hashlib, os, sys, shutil
manifest, home = sys.argv[1], sys.argv[2]
items, sums = [], {}
for line in open(manifest, encoding="utf-8"):
    parts = line.rstrip("\n").split("\t")
    if parts[0] == "file" and len(parts) > 1:
        items.append(parts[1])
    elif parts[0] == "sum" and len(parts) > 2:
        sums[parts[1]] = parts[2]
def sha(f):
    if os.path.islink(f):
        return "link:" + os.readlink(f)
    with open(f, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()
kept = 0
for p in items:
    if not p.startswith(home + "/") or not os.path.lexists(p):
        continue
    files = [p] if (not os.path.isdir(p) or os.path.islink(p)) else [
        os.path.join(d, f) for d, ds, fs in os.walk(p) for f in fs + [x for x in ds if os.path.islink(os.path.join(d, x))]]
    for f in files:
        if f in sums and sha(f) == sums[f]:
            os.remove(f)
        elif f in sums:
            kept += 1
    for d, ds, fs in sorted(os.walk(p, topdown=False)) if os.path.isdir(p) and not os.path.islink(p) else []:
        try:
            os.rmdir(d)
        except OSError:
            pass
print(f"old copy removed ({kept} file(s) you edited kept)")
PY
      mv -f -- "$OLD_MANIFEST" "$OLD_MANIFEST.moved-$(date +%Y%m%d%H%M%S)"
    fi
  fi
  vh_ok "moved over - your desktop switches to the new @@NAME@@ at the end"
  [[ -z "$ACTIVATE" ]] && ACTIVATE=1
  return 0
}

# ------------------------------------------------------------------ selection helpers
declare -A SELECTED=()
component_selected() { [[ -n "${SELECTED[$1]+x}" ]]; }
select_add() { local c; for c in "$@"; do [[ -n "$c" ]] && SELECTED[$c]=1; done; }
select_del() { local c; for c in "$@"; do unset 'SELECTED[$c]'; done; }
valid_component() { local c; for c in "${ALL_COMPONENTS[@]}"; do [[ "$c" == "$1" ]] && return 0; done; return 1; }
split_list() { tr ',' ' ' <<<"$1"; }

resolve_deps() {
  local changed=1 c d
  while [[ $changed -eq 1 ]]; do
    changed=0
    for c in "${!SELECTED[@]}"; do
      for d in ${DEPS[$c]:-}; do
        if ! component_selected "$d"; then SELECTED[$d]=1; changed=1; vh_dim "$c needs $d - added"; fi
      done
    done
  done
}

# ------------------------------------------------------------------ interactive menu
interactive_menu() {
  local choice opt
  vh_banner "$VH_VERSION $G_DOT KDE Plasma 6 $G_DOT Dark + Light"
  vh_print_env
  cat <<EOF

  ${C_B}${C_PINK}What would you like to do?${C_R}
   1) Install @@NAME@@ (Dark + Light) and switch on ${C_B}Dark${C_R}
   2) Install @@NAME@@ (Dark + Light) and switch on ${C_B}Light${C_R}
   3) Install @@NAME@@ (Dark + Light), switch it on later
   4) Choose individual components
   l) List components   q) Quit
EOF
  read -r -p "  Choice: " choice || choice=q
  case "$choice" in
    1) DESKTOP=kde; VARIANT=both; ACTIVATE=1; AV_WANT=dark ;;
    2) DESKTOP=kde; VARIANT=both; ACTIVATE=1; AV_WANT=light ;;
    3) DESKTOP=kde; VARIANT=both; ACTIVATE=0 ;;
    4) DESKTOP=custom
       echo; local i=1; for opt in "${ALL_COMPONENTS[@]}"; do printf '   %2d) %-16s %s\n' "$i" "$opt" "${DESC[$opt]}"; i=$((i + 1)); done
       read -r -p "  Component numbers (space separated): " choice || choice=""
       for opt in $choice; do
         [[ "$opt" =~ ^[0-9]+$ && $opt -ge 1 && $opt -le ${#ALL_COMPONENTS[@]} ]] && COMPONENTS+=("${ALL_COMPONENTS[$((opt - 1))]}")
       done
       [[ ${#COMPONENTS[@]} -gt 0 ]] || vh_die "no components chosen"
       read -r -p "  Edition - (d)ark, (l)ight or (b)oth [b]: " choice || choice=b
       case "${choice:-b}" in d*) VARIANT=dark ;; l*) VARIANT=light ;; *) VARIANT=both ;; esac ;;
    l|L) list_components; exit 0 ;;
    *) echo "  Nothing installed."; exit 0 ;;
  esac
}

# ------------------------------------------------------------------ main
DESKTOP=""; VARIANT=""; COMPONENTS=(); WITH=(); WITHOUT=(); ACTIVATE=""; ALLOW_ROOT=0; INTERACTIVE=0; WANT_DEPS=""; FULL=""
WIDGETS_WANT=(); AV_WANT=""; TEXT=0; DEPS_REPORT=0; LOG_FILE=""; NARGS=0; WANT_PANEL=""; WANT_KVITALS=0; WANT_PC=0; NO_AUTOSYNC=0; FF_DESIGN=0; PANEL_STYLE="Fancy"; PLAIN_PANEL=0; ONLY_PANEL=0
MIGRATE=""; PANEL_STYLE_SET=0

while [[ $# -gt 0 ]]; do
  case "$1" in --allow-root|--text|--log|--log=*) ;; *) NARGS=$((NARGS + 1)) ;; esac   # what counts as "told what to do"
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -V|--version) echo "@@NAME@@ $VH_VERSION"; exit 0 ;;
    -l|--list) list_components; exit 0 ;;
    --detect) vh_detect; vh_print_env; exit 0 ;;
    -d|--desktop) DESKTOP="${2:-}"; shift ;;
    --desktop=*) DESKTOP="${1#*=}" ;;
    -v|--variant) VARIANT="${2:-}"; shift ;;
    --variant=*) VARIANT="${1#*=}" ;;
    -c|--components) read -r -a COMPONENTS <<<"$(split_list "${2:-}")"; shift ;;
    --components=*) read -r -a COMPONENTS <<<"$(split_list "${1#*=}")" ;;
    -w|--with) read -r -a _w <<<"$(split_list "${2:-}")"; WITH+=("${_w[@]}"); shift ;;
    --with=*) read -r -a _w <<<"$(split_list "${1#*=}")"; WITH+=("${_w[@]}") ;;
    --without) read -r -a _w <<<"$(split_list "${2:-}")"; WITHOUT+=("${_w[@]}"); shift ;;
    --without=*) read -r -a _w <<<"$(split_list "${1#*=}")"; WITHOUT+=("${_w[@]}") ;;
    --panel) WANT_PANEL=1 ;;
    --no-panel) WANT_PANEL=0 ;;
    --kvitals) WANT_KVITALS=1 ;;
    --widgets) read -r -a _w <<<"$(split_list "${2:-}")"; WIDGETS_WANT+=("${_w[@]}"); shift ;;
    --widgets=*) read -r -a _w <<<"$(split_list "${1#*=}")"; WIDGETS_WANT+=("${_w[@]}") ;;
    --panel-colorizer) WANT_PC=1 ;;
    --panel-look|--panel-style) PANEL_STYLE="${2:-}"; PANEL_STYLE_SET=1; shift ;;
    --panel-look=*|--panel-style=*) PANEL_STYLE="${1#*=}"; PANEL_STYLE_SET=1 ;;
    --migrate) MIGRATE=1 ;;
    --no-migrate) MIGRATE=0 ;;
    # Waypoint 0.5's options, still understood
    --no-gtk) WITHOUT+=(kde-gtk) ;;
    --no-fastfetch) WITHOUT+=(fastfetch) ;;
    --skip-addons) WANT_DEPS=0 ;;
    --no-dim|--wallpaper=*|--manual|--preview|--keep-other-panels|--no-color|--no-colour) ;;
    --plain-panel) PLAIN_PANEL=1 ;;
    --only-panel) ONLY_PANEL=1 ;;
    --no-autosync) NO_AUTOSYNC=1 ;;
    --fastfetch) WITH+=(fastfetch) ;;
    --fastfetch-design) WITH+=(fastfetch); FF_DESIGN=1 ;;
    --full) FULL=1 ;;
    --install-deps) WANT_DEPS=1 ;;
    --no-deps) WANT_DEPS=0 ;;
    --activate) ACTIVATE=1 ;;
    --activate=later) ACTIVATE=0 ;;
    --activate=*) ACTIVATE=1; AV_WANT="${1#*=}" ;;
    --text) TEXT=1 ;;
    --deps-report) DEPS_REPORT=1 ;;
    --log) LOG_FILE="${2:-}"; shift ;;
    --log=*) LOG_FILE="${1#*=}" ;;
    --no-activate) ACTIVATE=0 ;;
    -y|--yes) VH_ASSUME_YES=1 ;;
    -n|--dry-run) VH_DRY_RUN=1 ;;
    --allow-root) ALLOW_ROOT=1 ;;
    *) vh_err "unknown option: $1"; echo "Run ./install.sh --help for usage." >&2; exit 2 ;;
  esac
  shift
done

if [[ $EUID -eq 0 && $ALLOW_ROOT -ne 1 ]]; then
  vh_die "do not run the installer as root - it installs per user. (Use --allow-root to install into root's own home.)"
fi
[[ -n "${HOME:-}" && -d "$HOME" ]] || vh_die "HOME is not set to an existing directory"

if [[ -n "$LOG_FILE" ]]; then   # keep a copy of everything shown (Setup reads it back)
  exec > >(tee -a -- "$LOG_FILE") 2>&1
fi
case "$DESKTOP" in ""|kde|custom) ;;
  gnome|both) vh_die "GNOME is not part of this release yet - @@NAME@@ ${VH_VERSION} is for KDE Plasma 6" ;;
  *) vh_die "--desktop must be kde (got '$DESKTOP')" ;; esac
if [[ $NARGS -eq 0 || $TEXT -eq 1 ]] && [[ -z "$DESKTOP" && ${#COMPONENTS[@]} -eq 0 ]]; then
  if vh_is_tty && [[ "$VH_ASSUME_YES" != 1 ]]; then
    # the guided installer, unless asked for plain questions (or it can't run here)
    if [[ $TEXT -eq 0 ]] && vh_have python3 && python3 -c 'import curses' 2>/dev/null; then
      exec python3 -I "$VH_ROOT/bin/@@COMMAND@@-setup" "$VH_ROOT"
    fi
    INTERACTIVE=1
    vh_detect
    interactive_menu
  else
    usage >&2; exit 2
  fi
fi
[[ -z "$DESKTOP" && ${#COMPONENTS[@]} -eq 0 ]] && DESKTOP=kde

[[ -z "$VARIANT" ]] && VARIANT=both
case "$VARIANT" in dark|light|both) ;; *) vh_die "--variant must be dark, light or both (got '$VARIANT')" ;; esac
case "$(tr '[:upper:]' '[:lower:]' <<<"$PANEL_STYLE")" in   # the six looks; names of 1.7 and earlier still work
  normal|plain) PANEL_STYLE=Normal ;; transparent|base) PANEL_STYLE=Transparent ;; invisible) PANEL_STYLE=Invisible ;;
  cards) PANEL_STYLE=Cards ;; pills|islands) PANEL_STYLE=Pills ;; fancy) PANEL_STYLE=Fancy ;;
  standard) PANEL_STYLE=Fancy; PLAIN_PANEL=1 ;;
  *) vh_die "--panel-style must be Normal, Transparent, Invisible, Cards, Pills, Fancy or Standard (got '$PANEL_STYLE')" ;; esac
case "$AV_WANT" in ""|dark|light) ;; *) vh_die "--activate= takes dark or light (got '$AV_WANT')" ;; esac
_ww=(); for _w in "${WIDGETS_WANT[@]}"; do case "$_w" in
  kvitals|panel-colorizer) _ww+=("$_w") ;; all) _ww+=(kvitals panel-colorizer) ;;
  *) vh_die "--widgets takes kvitals, panel-colorizer or all (got '$_w')" ;; esac; done; WIDGETS_WANT=("${_ww[@]}")
case "$DESKTOP" in kde) select_add "${KDE_DEFAULT[@]}" ;; ""|custom) ;; esac
if [[ ${#COMPONENTS[@]} -gt 0 ]]; then SELECTED=(); select_add "${COMPONENTS[@]}"; fi
select_add "${WITH[@]}"
select_del "${WITHOUT[@]}"
[[ ${#WIDGETS_WANT[@]} -gt 0 ]] && select_add kde-widgets
for c in "${!SELECTED[@]}"; do valid_component "$c" || vh_die "unknown component '$c' (see --list)"; done
resolve_deps
[[ ${#SELECTED[@]} -gt 0 ]] || vh_die "nothing selected"

# ---- requirements helpers
can_ask() { [[ "$VH_ASSUME_YES" != 1 ]] && { [[ $INTERACTIVE -eq 1 ]] || vh_is_tty; }; }
widget_installed() { local d; for d in /usr/share/plasma/plasmoids "$VH_DATA/plasma/plasmoids"; do [[ -d "$d/$1" ]] && return 0; done; return 1; }
PM=""; for _p in pacman dnf zypper apt; do vh_have "$_p" && { PM="$_p"; break; }; done
AUR=""; for _p in paru yay; do vh_have "$_p" && { AUR="$_p"; break; }; done
REQ_PKGS=(); REQ_OPT=(); REQ_AUR=(); REQ_MANUAL=(); REQ_N=0; REPORT=()
pm_install_cmd() { case "$PM" in pacman) echo "sudo pacman -S --needed" ;; dnf) echo "sudo dnf install" ;;
  zypper) echo "sudo zypper install" ;; apt) echo "sudo apt install" ;; esac; }
pkg_for() { case "$PM" in pacman) echo "$1" ;; dnf) echo "$2" ;; zypper) echo "$3" ;; apt) echo "$4" ;; esac; }
req_ok()   { REPORT+=("$1"$'\t'ok$'\t'"$2"$'\t'-); [[ $DEPS_REPORT -eq 1 ]] || printf '    %s%s%s %-20s %s%s%s\n' "$C_OK" "$G_OK" "$C_R" "$1" "$C_MUTED" "$2" "$C_R"; }
req_miss() { [[ $DEPS_REPORT -eq 1 ]] || printf '    %s%s%s %-20s %s\n' "$C_WARN" "$G_WARN" "$C_R" "$1" "missing - $2"; REQ_N=$((REQ_N + 1)); }
req_opt()  { [[ $DEPS_REPORT -eq 1 ]] || printf '    %s%s%s %-20s %s%s%s\n' "$C_MUTED" "$G_SKIP" "$C_R" "$1" "$C_MUTED" "optional - $2" "$C_R"; }
# need LABEL WHY TEST-COMMAND arch fedora suse debian [optional]
need() {
  local label="$1" why="$2" test="$3" pkg cmd; pkg="$(pkg_for "$4" "$5" "$6" "$7")"
  if eval "$test"; then req_ok "$label" "$why"; return 0; fi
  if [[ -n "$pkg" ]]; then cmd="$(pm_install_cmd) $pkg"; else cmd="manual: install $label with your package manager"; fi
  if [[ "${8:-}" == optional ]]; then
    req_opt "$label" "$why"; [[ -n "$pkg" ]] && REQ_OPT+=("$pkg"); REPORT+=("$label"$'\t'optional$'\t'"$why"$'\t'"$cmd")
  else
    req_miss "$label" "$why"; REPORT+=("$label"$'\t'missing$'\t'"$why"$'\t'"$cmd")
    [[ -n "$pkg" ]] && REQ_PKGS+=("$pkg") || REQ_MANUAL+=("$label: install it with your package manager")
  fi
}
widget_wanted() { local w; for w in "${WIDGETS_WANT[@]}"; do [[ "$w" == "$1" ]] && return 0; done; return 1; }
REQ_BUNDLED=()
need_widget() { # LABEL WHY plasmoid-id aur-package key
  local cmd
  if widget_installed "$3"; then req_ok "$1" "$2"; return 0; fi
  if widget_wanted "$5"; then   # asked for already (--widgets): the bundled copy goes in with the theme
    REPORT+=("$1"$'\t'ok$'\t'"$2"$'\t'-)
    [[ $DEPS_REPORT -eq 1 ]] || printf '    %s%s%s %-20s %s%s%s\n' "$C_OK" "$G_OK" "$C_R" "$1" "$C_MUTED" "bundled copy is installed with the theme" "$C_R"
    return 0
  fi
  req_miss "$1" "$2"
  if [[ -n "$AUR" ]]; then REQ_AUR+=("$4"); cmd="$AUR -S --needed $4"
  else REQ_BUNDLED+=("$5"); cmd="bundled:$5"; fi
  REPORT+=("$1"$'\t'missing$'\t'"$2"$'\t'"$cmd")
}
ask_full() {
  [[ -z "$FULL" && -z "$WANT_DEPS" && -z "$WANT_PANEL" && -z "$ACTIVATE" ]] && can_ask || return 0
  echo
  vh_info "${C_B}Full setup${C_R} installs the missing programs (your password is asked once), builds"
  vh_info "the top panel, recolours Fastfetch and switches the theme on - no more questions after this."
  if vh_confirm "Do the full setup?" y; then FULL=1; else FULL=0; vh_dim "ok - you'll be asked step by step"; fi
}
apply_full() {
  [[ "$FULL" == 1 ]] || return 0
  [[ -n "$WANT_DEPS" ]] || WANT_DEPS=1
  component_selected kde-panel && [[ -z "$WANT_PANEL" ]] && WANT_PANEL=1 && ONLY_PANEL=1
  [[ -n "$ACTIVATE" ]] || ACTIVATE=1
  [[ -n "$DESKTOP" && "$DESKTOP" != custom ]] && select_add fastfetch
  return 0
}
ask_fastfetch() { # your layout and logo stay; uninstall restores them
  component_selected fastfetch && return 0
  [[ "$FULL" == 1 ]] && return 0
  vh_have fastfetch && [[ -n "$DESKTOP" && "$DESKTOP" != custom ]] && can_ask || return 0
  echo
  if vh_confirm "Recolour Fastfetch to match @@NAME@@? (keeps your layout and logo; uninstall restores it)" y; then
    select_add fastfetch
    vh_confirm "  Use the @@NAME@@ Fastfetch design with its logo instead?" n && FF_DESIGN=1
  fi
  return 0
}
check_requirements() {
  local c
  [[ $DEPS_REPORT -eq 1 ]] || vh_step "What it needs"
  [[ -n "$PM" && $DEPS_REPORT -eq 0 ]] && vh_dim "package manager: $PM${AUR:+   AUR helper: $AUR}"
  if component_selected kde-kvantum; then
    need "Kvantum" "the @@NAME@@ app style for Qt apps" "vh_have kvantummanager" kvantum kvantum kvantum-qt6 qt6-style-kvantum
  fi
  if component_selected kde-gtk; then
    need "Plasma GTK settings" "switches GTK apps live (else only GTK's settings file)" "vh_gtkconfig_present" kde-gtk-config kde-gtk-config kde-gtk-config6 kde-config-gtk-style optional
  fi
  if component_selected kde-panel || component_selected kde-command; then
    need "qdbus" "builds the panel, used by @@COMMAND@@" "vh_qdbus >/dev/null" qt6-tools qt6-qttools qt6-tools-qdbus qt6-tools-dev-tools
  fi
  if component_selected kde-command && [[ $NO_AUTOSYNC -eq 0 ]]; then
    need "dbus-monitor" "the login sync helper" "vh_have dbus-monitor" dbus dbus-tools dbus-1-tools dbus-bin
  fi
  if component_selected kde-panel; then
    need_widget "KVitals" "CPU, RAM, GPU and network stats on the panel" org.kde.plasma.kvitals plasma6-applets-kvitals-git kvitals
    [[ $PLAIN_PANEL -eq 1 ]] || need_widget "Panel Colorizer" "gives the top panel its @@NAME@@ look" luisbocanegra.panel.colorizer plasma6-applets-panel-colorizer panel-colorizer
  fi
  if component_selected fastfetch; then
    need "Python 3" "recolours Fastfetch" "vh_have python3" python python3 python3 python3
    need "Fastfetch" "system info in the terminal" "vh_have fastfetch" fastfetch fastfetch fastfetch fastfetch optional
  fi
  if component_selected icons; then
    need "Papirus icons" "fills in app icons @@NAME@@ doesn't draw" "vh_icon_theme_present Papirus" papirus-icon-theme papirus-icon-theme papirus-icon-theme papirus-icon-theme optional
  fi
  if [[ $DEPS_REPORT -eq 1 ]]; then
    printf 'PM\t%s\nAUR\t%s\n' "${PM:--}" "${AUR:--}"
    for c in "${REPORT[@]}"; do printf 'ITEM\t%s\n' "$c"; done
    return 0
  fi
  (( REQ_N > 0 || ${#REQ_OPT[@]} > 0 )) || { vh_ok "everything it needs is installed"; return 0; }
  local cmds=() do_main=0 do_opt=0 aur_only=0
  # --kvitals / --panel-colorizer are a yes for those widgets only
  [[ -z "$WANT_DEPS" && ${#REQ_AUR[@]} -gt 0 ]] && [[ $WANT_KVITALS -eq 1 || $WANT_PC -eq 1 ]] && aur_only=1
  [[ ${#REQ_PKGS[@]} -gt 0 ]] && cmds+=("$(pm_install_cmd) ${REQ_PKGS[*]}")
  [[ ${#REQ_AUR[@]} -gt 0 ]] && cmds+=("$AUR -S --needed ${REQ_AUR[*]}")
  if [[ ${#cmds[@]} -gt 0 ]]; then
    vh_sub "To install what's missing"
    for c in "${cmds[@]}"; do vh_line "$c"; done
  fi
  for c in "${REQ_MANUAL[@]}"; do vh_warn "$c"; done
  if [[ ${#REQ_BUNDLED[@]} -gt 0 ]]; then
    vh_sub "Bundled with @@NAME@@ (installed for your user, no password)"
    vh_row "$(printf '%s ' "${REQ_BUNDLED[@]}")" ""
    local take=0 w
    if [[ "$WANT_DEPS" == 1 ]]; then take=1
    elif [[ "$WANT_DEPS" != 0 ]] && can_ask && vh_confirm "Install the bundled widgets?" y; then take=1; fi
    for w in "${REQ_BUNDLED[@]}"; do
      if [[ $take -eq 1 ]] || { [[ $w == kvitals && $WANT_KVITALS -eq 1 ]]; } || { [[ $w == panel-colorizer && $WANT_PC -eq 1 ]]; }; then
        WIDGETS_WANT+=("$w"); select_add kde-widgets
      fi
    done
    component_selected kde-widgets && vh_ok "they go in with the theme"
  fi
  if [[ ${#cmds[@]} -gt 0 ]]; then
    if [[ "$WANT_DEPS" == 1 ]]; then do_main=1
    elif [[ "$WANT_DEPS" != 0 ]] && can_ask && vh_confirm "Install the missing programs now? (asks for your password)" y; then do_main=1
    elif [[ $aur_only -eq 1 ]]; then REQ_PKGS=(); do_main=1; fi
  fi
  if [[ ${#REQ_OPT[@]} -gt 0 && -n "$PM" ]]; then
    vh_sub "Recommended"
    vh_line "$(pm_install_cmd) ${REQ_OPT[*]}"
    if [[ "$WANT_DEPS" == 1 ]]; then do_opt=1
    elif [[ "$WANT_DEPS" != 0 ]] && can_ask && vh_confirm "Install the recommended extras too?" y; then do_opt=1; fi
  fi
  (( do_main + do_opt > 0 )) || { [[ ${#cmds[@]} -gt 0 ]] && vh_dim "$G_SKIP nothing installed - the theme still installs; add the programs any time"; return 0; }
  run_req() { if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "would run: $*"; return 0; fi
    # never stops the installer: a failed extra is reported and the theme still installs
    vh_info "running: $*"; "$@" || vh_warn "that didn't finish - the theme still installs; run it again later"; return 0; }
  local pmc; read -r -a pmc <<<"$(pm_install_cmd)"
  if (( do_main )); then
    [[ ${#REQ_PKGS[@]} -gt 0 ]] && run_req "${pmc[@]}" "${REQ_PKGS[@]}"
    if [[ ${#REQ_AUR[@]} -gt 0 ]]; then
      run_req "$AUR" -S --needed "${REQ_AUR[@]}"
      vh_more "saw 404 errors? run: sudo pacman -Syu, then try again"
    fi
  fi
  (( do_opt )) && run_req "${pmc[@]}" "${REQ_OPT[@]}"
  hash -r
  return 0
}

if [[ $VARIANT == both ]]; then VARIANTS=(dark light); else VARIANTS=("$VARIANT"); fi
[[ $INTERACTIVE -eq 1 ]] || vh_detect
if [[ $DEPS_REPORT -eq 1 ]]; then check_requirements; exit 0; fi

# ---- summary + confirmation
[[ $INTERACTIVE -eq 1 ]] || vh_banner "$VH_VERSION $G_DOT KDE Plasma 6 installer$([[ "$VH_DRY_RUN" == 1 ]] && echo " $G_DOT dry run")"
ask_full
apply_full
ask_fastfetch
vh_step "Install plan$([[ "$VH_DRY_RUN" == 1 ]] && echo ' (dry run - nothing is written)')"
vh_row "Edition" "$(for v in "${VARIANTS[@]}"; do printf '%s ' "$(Title "$v")"; done)"
plan_w=$(( VH_W - 5 - VH_LABEL_W ))
for c in "${ALL_COMPONENTS[@]}"; do
  component_selected "$c" || continue
  d="${DESC[$c]}"; (( ${#d} > plan_w )) && { if [[ $VH_UTF8 -eq 1 ]]; then d="${d:0:$((plan_w - 1))}…"; else d="${d:0:$((plan_w - 3))}..."; fi; }
  vh_row "$c" "${C_MUTED}${d}${C_R}"
done
if component_selected kde-plasma && [[ "$VH_PLASMA_VER" =~ ^([0-9]+) ]] && [[ ${BASH_REMATCH[1]} -lt 6 ]]; then
  vh_warn "Plasma $VH_PLASMA_VER detected - the Plasma components target Plasma 6."
fi
# with the full setup the plan is shown for information only - you already said yes
if [[ "$FULL" != 1 ]] && can_ask && ! vh_confirm "Proceed?" y; then echo "  Cancelled."; exit 0; fi

# ---- what the chosen parts need: check, list, and install only with consent
check_requirements

# ---- install
vh_manifest_load
trap 'vh_manifest_save' EXIT
migrate_old
declare -A RESULT=()
for c in "${ALL_COMPONENTS[@]}"; do
  component_selected "$c" || continue
  fn="inst_${c//-/_}"
  [[ -n "${_vh_installing:-}" ]] || { vh_step "Installing"; _vh_installing=1; }
  ok=1
  if [[ -n "${PER_VARIANT[$c]:-}" ]]; then
    for v in "${VARIANTS[@]}"; do "$fn" "$v" || ok=0; done
  else
    "$fn" "${AV_WANT:-${VARIANTS[0]}}" || ok=0   # e.g. Fastfetch colours: the edition being switched on
  fi
  if [[ $ok -eq 1 ]]; then RESULT[$c]=installed; vh_ok "$c"; else RESULT[$c]=failed; vh_warn "$c finished with problems"; fi
done
vh_manifest_save

# ---- report
vh_step "Summary"
n_ok=0; n_bad=0
for c in "${ALL_COMPONENTS[@]}"; do
  component_selected "$c" || continue
  if [[ ${RESULT[$c]} == installed ]]; then n_ok=$((n_ok + 1)); else n_bad=$((n_bad + 1)); vh_warn "$c - FAILED (see messages above)"; fi
done
vh_row "Components" "$n_ok installed$([[ $n_bad -gt 0 ]] && echo ", $n_bad failed")"
vh_row "Files" "$VH_N_NEW new, $VH_N_UPDATED replaced, $VH_N_SAME unchanged, $VH_N_BACKUP backed up, $VH_N_FAIL failed"
[[ $VH_N_BACKUP -gt 0 && "$VH_DRY_RUN" != 1 ]] && vh_row "Backups" "${VH_BACKUPS/#$HOME/\~}/$VH_TS/"
[[ ${VH_N_EDITED:-0} -gt 0 ]] && vh_more "${VH_N_EDITED} of them were @@NAME@@ files changed since the last install - your copies are in the backup"
[[ "$VH_DRY_RUN" == 1 ]] || vh_row "Install record" "${VH_MANIFEST/#$HOME/\~}"

# ---- KDE extras: top panel, sync helper
if component_selected kde-panel; then
  vh_step "Top panel"
  widget_installed org.kde.plasma.kvitals && vh_ok "KVitals installed" || vh_dim "$G_SKIP KVitals not installed - the panel will have no stats"
  if [[ $PLAIN_PANEL -eq 0 ]]; then
    widget_installed luisbocanegra.panel.colorizer && vh_ok "Panel Colorizer installed" ||
      vh_warn "Panel Colorizer not installed - the panel is built plain until it is"
  fi
  if [[ $PLAIN_PANEL -eq 1 ]]; then panel_args=(--plain); else panel_args=(--look "$PANEL_STYLE"); fi
  [[ $ONLY_PANEL -eq 1 ]] && panel_args+=(--only)
  if [[ -z "$WANT_PANEL" ]]; then
    if can_ask && [[ $VH_IS_KDE -eq 1 ]] && vh_confirm "Set up the @@NAME@@ top panel now? (replaces your current top panel; it is backed up first)" y; then WANT_PANEL=1; else WANT_PANEL=0; fi
  fi
  if [[ "$WANT_PANEL" == 1 ]]; then
    if [[ $VH_IS_KDE -eq 1 && "$VH_DRY_RUN" != 1 ]]; then
      "$VH_BIN/@@COMMAND@@" panel --apply "${panel_args[@]}" || vh_warn "panel step failed - run: @@COMMAND@@ panel --apply ${panel_args[*]}"
    else
      vh_dim "$G_SKIP not in a running Plasma session - build it later:"
      vh_more "@@COMMAND@@ panel --apply ${panel_args[*]}"
    fi
  else
    vh_dim "$G_SKIP panel not changed"
    vh_more "build it any time: @@COMMAND@@ panel --apply"
    vh_more "undo:              @@COMMAND@@ panel --restore"
  fi
fi
if component_selected kde-command && [[ $VH_IS_KDE -eq 1 ]] && [[ $NO_AUTOSYNC -eq 0 && "$VH_DRY_RUN" != 1 ]] &&
   [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] && vh_have dbus-monitor; then
  ( nohup "$VH_BIN/@@COMMAND@@" watch >/dev/null 2>&1 & )   # now; at login via autostart
fi
if [[ "$VH_DRY_RUN" != 1 ]] && component_selected kde-plasma; then
  rm -f -- "$HOME/.cache/plasma_theme_$(tw_name plasma_style Dark).kcache" "$HOME/.cache/plasma_theme_$(tw_name plasma_style Light).kcache" 2>/dev/null || true   # only @@NAME@@'s own cache
fi
if [[ "$VH_DRY_RUN" != 1 ]] && component_selected icons; then
  # Plasma caches icons it has drawn; without this, icons replaced by a newer @@NAME@@ (like the
  # launcher) can keep showing the old picture until the cache expires. It is rebuilt on its own.
  rm -f -- "$HOME/.cache/icon-cache.kcache" 2>/dev/null || true
fi

# ---- activation
can_kde=0; [[ $VH_IS_KDE -eq 1 ]] && vh_have plasma-apply-colorscheme && can_kde=1
want_kde=0
for c in kde-colors kde-plasma kde-aurorae kde-cursors icons kde-wallpaper; do component_selected "$c" && want_kde=1; done
AV="${AV_WANT:-${VARIANTS[0]}}"
if [[ -n "$AV_WANT" ]] && ! printf '%s\n' "${VARIANTS[@]}" | grep -qx "$AV_WANT"; then
  vh_die "--activate=$AV_WANT: that edition is not being installed"
fi
if [[ -z "$ACTIVATE" ]]; then
  if [[ $INTERACTIVE -eq 1 ]] || { vh_is_tty && [[ "$VH_ASSUME_YES" != 1 ]]; }; then
    if [[ $can_kde -eq 1 && $want_kde -eq 1 ]]; then
      echo
      if vh_confirm "Switch @@NAME@@ $(Title "$AV") on now? (your current settings are recorded for uninstall)" n; then ACTIVATE=1; else ACTIVATE=0; fi
    fi
  else
    ACTIVATE=0
  fi
fi
if [[ "$ACTIVATE" == 1 && $want_kde -eq 1 ]]; then
  if [[ $can_kde -eq 1 ]]; then
    activate_kde "$AV"
    # then the same switch `@@COMMAND@@ dark|light` does: Kvantum, Konsole, Fastfetch, the panel's look, dimming
    if [[ "$VH_DRY_RUN" != 1 && -x "$VH_BIN/@@COMMAND@@" ]] && component_selected kde-command; then
      "$VH_BIN/@@COMMAND@@" "$AV" || vh_warn "@@COMMAND@@ $AV finished with problems - run it again"
    fi
  else
    vh_warn "not in a KDE Plasma session with plasma-apply-* tools - switching on skipped"
    vh_more "log in to Plasma and run: @@COMMAND@@ $AV"
  fi
fi

# ---- how to turn it on (or what else there is, after activation)
T="$(Title "$AV")"; OTHER=light; [[ "$AV" == light ]] && OTHER=dark
if [[ "$ACTIVATE" == 1 ]]; then vh_step "You're set - good to know"; else vh_step "How to turn it on"; fi
if [[ $want_kde -eq 1 ]]; then
  if component_selected kde-command; then
    vh_cmd "Everything" "@@COMMAND@@ $AV" "or: @@COMMAND@@ $OTHER"
    vh_more "the whole look + Kvantum, Konsole and Fastfetch"
  fi
  if component_selected kde-panel; then
    vh_cmd "Top panel" "@@COMMAND@@ panel --apply"
    vh_more "looks: --look Normal $G_DOT Transparent $G_DOT Invisible $G_DOT Cards $G_DOT Pills $G_DOT Fancy"
    vh_more "undo:  @@COMMAND@@ panel --restore"
  fi
  vh_menu "Global Theme" "System Settings > Colors & Themes >"
  vh_menu "" "Global Theme > @@NAME@@ $T"
  vh_sub "One piece at a time (optional)"
  vh_row "System Settings" "Colors, Plasma Style, Window Decorations, Icons,"
  vh_more "Cursors, Splash Screen and Wallpaper each list it"
  vh_cmd "Colours + style" "plasma-apply-colorscheme $(tw_name color_scheme "$T")"
  vh_cmd "" "plasma-apply-desktoptheme $(tw_name plasma_style "$T")"
  vh_cmd "Global Theme" "plasma-apply-lookandfeel -a \\"
  vh_more "  $LNF_PREFIX.$AV"
  if component_selected kde-konsole; then
    vh_menu "Konsole" "Settings > Manage Profiles >"
    vh_menu "" "@@NAME@@ $T > Set as Default"
  fi
  if component_selected kde-kvantum; then
    vh_cmd "Kvantum" "kvantummanager --set $(tw_name kvantum "$T")"
    vh_more "then Application Style > kvantum"
    vh_more "(after the Global Theme - it resets the style)"
  fi
  if component_selected kde-gtk; then
    vh_menu "GTK apps" "System Settings > Colors & Themes >"
    vh_menu "" "Application Style > GNOME/GTK > @@NAME@@ $T"
    vh_more "or: @@COMMAND@@ gtk on  (off: back to your own)"
  fi
fi
if component_selected kde-command; then
  vh_sub "Settings app"
  vh_cmd "Everything above" "@@COMMAND@@ settings" "or: @@NAME@@ Settings in the app menu"
fi
vh_step "Undo"
vh_cmd "Remove everything" "./uninstall.sh"
vh_more "restores your backups and previous settings"
echo
