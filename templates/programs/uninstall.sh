#!/usr/bin/env bash
# @@NAME@@ - uninstaller. Removes only what install.sh recorded in its manifest.
# Run ./uninstall.sh --help for usage.
set -euo pipefail

VH_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$VH_ROOT/lib/common.sh"
VH_VERSION="$(cat "$VH_ROOT/VERSION" 2>/dev/null || echo unknown)"

usage() {
  cat <<EOF
${C_B}@@NAME@@ ${VH_VERSION}${C_R} - uninstaller

Usage: ./uninstall.sh [options]      (or, once installed: @@COMMAND@@ uninstall [options])

Removes the files listed in the install manifest
(${VH_MANIFEST/#$HOME/\~}) and nothing else.

Options:
  -c, --components LIST    remove only these components (comma-separated; default: all)
  -y, --yes                no questions: keep modified files, restore recorded settings
  -f, --force              also remove files you modified after installing
                           (a copy is kept in the backups folder first)
      --restore-settings   restore desktop settings recorded at activation (default: ask)
      --keep-settings      leave current desktop settings alone
      --purge-backups      delete ${VH_BACKUPS/#$HOME/\~} afterwards
  -n, --dry-run            show what would happen, change nothing
  -h, --help               this help

Switching back by hand:
  KDE:   System Settings > Colors & Themes > Global Theme > Breeze
         (or: plasma-apply-lookandfeel -a org.kde.breeze.desktop)
  GNOME: gsettings reset org.gnome.desktop.interface gtk-theme
         gsettings reset org.gnome.desktop.interface icon-theme
         gsettings reset org.gnome.shell.extensions.user-theme name
EOF
}

ONLY=(); FORCE=0; RESTORE=""; PURGE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -c|--components) read -r -a ONLY <<<"$(tr ',' ' ' <<<"${2:-}")"; shift ;;
    --components=*) read -r -a ONLY <<<"$(tr ',' ' ' <<<"${1#*=}")" ;;
    -y|--yes) VH_ASSUME_YES=1 ;;
    -f|--force) FORCE=1 ;;
    --restore-settings) RESTORE=1 ;;
    --keep-settings) RESTORE=0 ;;
    --purge-backups) PURGE=1 ;;
    -n|--dry-run) VH_DRY_RUN=1 ;;
    *) vh_err "unknown option: $1"; echo "Run ./uninstall.sh --help for usage." >&2; exit 2 ;;
  esac
  shift
done

wanted() { # component
  [[ ${#ONLY[@]} -eq 0 ]] && return 0
  local c; for c in "${ONLY[@]}"; do [[ "$c" == "$1" ]] && return 0; done; return 1
}

vh_manifest_load
if [[ ${#VH_MF_ORDER[@]} -eq 0 ]]; then
  vh_step "@@NAME@@ is not installed for this user (no manifest at ${VH_MANIFEST/#$HOME/\~})."
  [[ -f "$VH_SETTINGS" ]] || exit 0
fi

# ---- plan
declare -a FILES=() DIRS=() BACKS=() LINES=() PROFS=() LINKS=() ACTIONS=()
declare -A COMPS=()
for key in "${VH_MF_ORDER[@]}"; do
  [[ -n "${VH_MF[$key]+x}" ]] || continue
  t="${key%%$'\t'*}"; id="${key#*$'\t'}"
  IFS=$'\t' read -r comp _ _ <<<"${VH_MF[$key]}"
  wanted "$comp" || continue
  COMPS[$comp]=1
  case "$t" in F) FILES+=("$id") ;; D) DIRS+=("$id") ;; B) BACKS+=("$id") ;; L) LINES+=("$id") ;; P) PROFS+=("$id") ;;
               S) LINKS+=("$id") ;; R) ACTIONS+=("$id") ;; esac
done

vh_banner "$VH_VERSION $G_DOT uninstall$([[ "$VH_DRY_RUN" == 1 ]] && echo " $G_DOT dry run")"
vh_step "Removing"
vh_info "${#FILES[@]} files, ${#LINKS[@]} links, ${#DIRS[@]} directories, ${#LINES[@]} config lines, ${#PROFS[@]} terminal profiles, ${#ACTIONS[@]} actions to undo, ${#BACKS[@]} originals to restore"
[[ ${#ONLY[@]} -gt 0 ]] && vh_info "components: ${ONLY[*]}"
if vh_is_tty && [[ "$VH_ASSUME_YES" != 1 ]] && ! vh_confirm "Continue?" y; then echo "  Cancelled."; exit 0; fi

trap 'vh_manifest_save' EXIT
removed=0; kept=0; n_missing=0; restored=0
declare -a KEPT=() PROBLEMS=()

# ---- settings recorded at activation (do first, while the themes still exist)
restore_settings() {
  [[ -f "$VH_SETTINGS" ]] || return 0
  vh_step "Restoring desktop settings recorded at activation"
  local tool target key value ic rest=()
  while IFS=$'\t' read -r tool target key value; do
    [[ -z "$tool" ]] && continue
    case "$tool" in
      gsettings)
        if vh_have gsettings && gsettings get "$target" "$key" >/dev/null 2>&1; then
          vh_dim "\$ gsettings set $target $key $value"
          if [[ "$VH_DRY_RUN" == 1 ]] || gsettings set "$target" "$key" "$value"; then continue; fi
        fi ;;
      usertheme)
        if vh_ut_gs get org.gnome.shell.extensions.user-theme name >/dev/null 2>&1; then
          vh_dim "\$ gsettings set org.gnome.shell.extensions.user-theme name $value"
          if [[ "$VH_DRY_RUN" == 1 ]] || vh_ut_gs set org.gnome.shell.extensions.user-theme name "$value"; then continue; fi
        fi ;;
      dconf)
        if vh_have dconf; then
          if [[ -z "$value" ]]; then vh_dim "\$ dconf reset $target"
            if [[ "$VH_DRY_RUN" == 1 ]] || dconf reset "$target"; then continue; fi
          else vh_dim "\$ dconf write $target $value"
            if [[ "$VH_DRY_RUN" == 1 ]] || dconf write "$target" "$value"; then continue; fi
          fi
        fi ;;
      kde)
        case "$target" in
          lookandfeel) if vh_have plasma-apply-lookandfeel; then vh_dim "\$ plasma-apply-lookandfeel -a $value"
                         if [[ "$VH_DRY_RUN" == 1 ]] || plasma-apply-lookandfeel -a "$value" >/dev/null 2>&1; then continue; fi; fi ;;
          wallpaper) if vh_have plasma-apply-wallpaperimage && [[ -e "$value" ]]; then vh_dim "\$ plasma-apply-wallpaperimage $value"
                       if [[ "$VH_DRY_RUN" == 1 ]] || plasma-apply-wallpaperimage "$value" >/dev/null 2>&1; then continue; fi; fi ;;
          colorscheme) if vh_have plasma-apply-colorscheme; then vh_dim "\$ plasma-apply-colorscheme $value"
                         if [[ "$VH_DRY_RUN" == 1 ]] || plasma-apply-colorscheme "$value" >/dev/null; then continue; fi; fi ;;
          desktoptheme) if vh_have plasma-apply-desktoptheme; then vh_dim "\$ plasma-apply-desktoptheme $value"
                          if [[ "$VH_DRY_RUN" == 1 ]] || plasma-apply-desktoptheme "$value" >/dev/null; then continue; fi; fi ;;
          kvantum) if vh_have kvantummanager; then vh_dim "\$ kvantummanager --set ${value:-Default}"
                     if [[ "$VH_DRY_RUN" == 1 ]] || kvantummanager --set "${value:-Default}" >/dev/null 2>&1; then continue; fi; fi ;;
          widgetstyle) if vh_have kwriteconfig6; then vh_dim "\$ kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle $value"
                         if [[ "$VH_DRY_RUN" == 1 ]] || kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle "$value"; then continue; fi; fi ;;
          decoration) if vh_have kwriteconfig6; then vh_dim "\$ kwriteconfig6 kwinrc org.kde.kdecoration2 -> $value"
                        if [[ "$VH_DRY_RUN" == 1 ]] || { kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library "${value%%|*}" &&
                             kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme "${value#*|}"; }; then
                          ic="$(vh_qdbus)" && { "$ic" org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true; }
                          continue
                        fi; fi ;;
          cursor) if vh_have plasma-apply-cursortheme; then vh_dim "\$ plasma-apply-cursortheme $value"
                    if [[ "$VH_DRY_RUN" == 1 ]] || plasma-apply-cursortheme "$value" >/dev/null 2>&1; then continue; fi; fi ;;
          splash) if vh_have kwriteconfig6; then vh_dim "\$ kwriteconfig6 --file ksplashrc --group KSplash --key Theme $value"
                    if [[ "$VH_DRY_RUN" == 1 ]] || kwriteconfig6 --file ksplashrc --group KSplash --key Theme "$value"; then continue; fi; fi ;;
          gtk) vh_dim "\$ GTK apps: $value"
               if [[ "$VH_DRY_RUN" == 1 ]] || vh_gtk_set "$value"; then continue; fi ;;
          icons) for ic in plasma-changeicons /usr/lib/plasma-changeicons /usr/libexec/plasma-changeicons \
                           /usr/lib/x86_64-linux-gnu/libexec/plasma-changeicons /usr/lib64/libexec/plasma-changeicons; do
                   if vh_have "$ic" || [[ -x "$ic" ]]; then vh_dim "\$ $ic $value"
                     if [[ "$VH_DRY_RUN" == 1 ]] || "$ic" "$value" >/dev/null; then continue 2; fi; fi
                 done ;;
        esac ;;
    esac
    rest+=("$tool"$'\t'"$target"$'\t'"$key"$'\t'"$value")
    PROBLEMS+=("could not restore $tool $target $key -> $value (do it by hand)")
  done < "$VH_SETTINGS"
  [[ "$VH_DRY_RUN" == 1 ]] && return 0
  if [[ ${#rest[@]} -eq 0 ]]; then rm -f -- "$VH_SETTINGS"; else printf '%s\n' "${rest[@]}" > "$VH_SETTINGS"; fi
  vh_ok "settings restored"
}

if [[ -f "$VH_SETTINGS" && ${#ONLY[@]} -eq 0 ]]; then
  if [[ -z "$RESTORE" ]]; then
    vh_step "Desktop settings"
    vh_info "@@NAME@@ was applied by the installer; your earlier settings were recorded:"
    while IFS=$'\t' read -r a b c d; do vh_dim "$a $b $c = $d"; done < "$VH_SETTINGS"
    if vh_confirm "Restore them?" y; then RESTORE=1; else RESTORE=0; fi
  fi
  [[ "$RESTORE" == 1 ]] && restore_settings
fi
# GTK apps must not be left on a theme that is about to disappear (e.g. picked by hand in System Settings)
if [[ -n "${COMPS[kde-gtk]+x}" ]]; then
  case "$(vh_gtk_now)" in
    "$(tw_name gtk Dark)"|"$(tw_name gtk Light)")
      g="$( [[ -f "$VH_SETTINGS" ]] && awk -F'\t' '$1=="kde" && $2=="gtk" {print $4; exit}' "$VH_SETTINGS" )"
      g="${g:-$(vh_gtk_default)}"
      vh_dim "\$ GTK apps: $g"
      [[ "$VH_DRY_RUN" == 1 ]] || vh_gtk_set "$g" || PROBLEMS+=("GTK apps still use @@NAME@@ - pick another theme in System Settings > Application Style > GNOME/GTK") ;;
  esac
  [[ "$VH_DRY_RUN" == 1 ]] || rm -f -- "$VH_STATE_DIR/gtk-off"
fi

# ---- reversible actions (before their tools are removed)
for act in "${ACTIONS[@]}"; do
  case "$act" in
    topbar)
      for f in "$VH_DATA/themes/$(tw_name gtk Dark)/gnome-shell/topbar.css" "$VH_DATA/themes/$(tw_name gtk Light)/gnome-shell/topbar.css" "$VH_STATE_DIR/topbar-style"; do
        [[ -e "$f" ]] || continue
        if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "rm $f"; else rm -f -- "$f"; fi
      done
      [[ "$VH_DRY_RUN" == 1 ]] || vh_mf_del R topbar ;;
    fastfetch)
      tool="$VH_STATE_DIR/fastfetch/@@COMMAND@@-fastfetch.py"
      vh_step "Fastfetch: putting your original config back"
      if [[ -f "$tool" ]] && vh_have python3; then
        if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "python3 $tool --restore"
        elif python3 -I "$tool" --restore; then vh_mf_del R fastfetch
        else PROBLEMS+=("Fastfetch restore failed - your original is next to the config as *.@@COMMAND@@-original"); fi
      else
        PROBLEMS+=("Fastfetch: tool or python3 missing - restore by hand from ~/.config/fastfetch/*.@@COMMAND@@-original")
      fi ;;
  esac
done

# ---- KDE extras: the login helper and the top panel
if [[ -n "${COMPS[kde-command]+x}${COMPS[gnome-command]+x}" && "$VH_DRY_RUN" != 1 ]]; then
  pkill -f "$VH_BIN/@@COMMAND@@ watch" 2>/dev/null || true
fi
if [[ -n "${COMPS[kde-panel]+x}" && -d "$VH_STATE_DIR/panel-backups" ]]; then
  vh_step "Top panel"
  if [[ -x "$VH_BIN/@@COMMAND@@" ]] && vh_is_tty && [[ "$VH_ASSUME_YES" != 1 ]] &&
     vh_confirm "Put back the panels you had before '@@COMMAND@@ panel --apply'?" n; then
    [[ "$VH_DRY_RUN" == 1 ]] || "$VH_BIN/@@COMMAND@@" panel --restore || PROBLEMS+=("panel restore failed")
  else
    vh_info "Panel backups stay in ${VH_STATE_DIR/#$HOME/\~}/panel-backups/ (the panel keeps working; its launcher"
    vh_info "icon falls back to the default). To restore by hand: copy the files back into ~/.config and log out/in."
  fi
fi

# ---- GNOME Terminal profiles
for uuid in "${PROFS[@]}"; do
  if vh_have dconf && vh_have gsettings; then
    vh_dim "remove GNOME Terminal profile $uuid"
    if [[ "$VH_DRY_RUN" != 1 ]]; then
      list="$(gsettings get org.gnome.Terminal.ProfilesList list 2>/dev/null || true)"
      if [[ "$list" == *"$uuid"* ]]; then
        new="$(sed -e "s/, '$uuid'//; s/'$uuid', //; s/'$uuid'//" <<<"$list")"
        [[ "$new" == "[]" ]] && new="@as []"
        gsettings set org.gnome.Terminal.ProfilesList list "$new" || PROBLEMS+=("could not update GNOME Terminal profile list")
        def="$(gsettings get org.gnome.Terminal.ProfilesList default 2>/dev/null || true)"
        [[ "$def" == "'$uuid'" ]] && gsettings reset org.gnome.Terminal.ProfilesList default
      fi
      dconf reset -f "/org/gnome/terminal/legacy/profiles:/:$uuid/" || PROBLEMS+=("could not reset dconf profile $uuid")
      vh_mf_del P "$uuid"
    fi
  else
    PROBLEMS+=("dconf/gsettings not available - GNOME Terminal profile $uuid left in place")
  fi
done

# ---- injected config lines
for file in "${LINES[@]}"; do
  rec="$(vh_mf_get L "$file")"
  IFS=$'\t' read -r _ f3 _ <<<"$rec"
  IFS='|' read -r marker created addnl <<<"$f3"
  if [[ ! -f "$file" ]]; then vh_mf_del L "$file"; continue; fi
  vh_dim "remove @@NAME@@ line from ${file/#$HOME/\~}"
  if [[ "$VH_DRY_RUN" != 1 ]]; then
    tmp="$file.vh-tmp.$$"
    grep -vF -- "$marker" "$file" > "$tmp" || true
    if [[ "$created" == 1 ]] && ! grep -q '[^[:space:]]' "$tmp"; then
      rm -f -- "$tmp" "$file"
    else
      if [[ "${addnl:-0}" == 1 && -s "$tmp" ]]; then
        # we added a newline before our line: take it away again (byte-exact restore)
        head -c -1 -- "$tmp" > "$file"
      else
        cat -- "$tmp" > "$file"                # keep the original file's inode and mode
      fi
      rm -f -- "$tmp"
    fi
    vh_mf_del L "$file"
  fi
done

# ---- files
for file in "${FILES[@]}"; do
  rec="$(vh_mf_get F "$file")"
  IFS=$'\t' read -r comp sha _ <<<"$rec"
  if [[ ! -e "$file" && ! -L "$file" ]]; then
    n_missing=$((n_missing + 1)); vh_mf_del F "$file"; continue
  fi
  if [[ -L "$file" || ! -f "$file" ]]; then
    KEPT+=("$file (no longer a regular file)"); kept=$((kept + 1)); continue
  fi
  cur="$(vh_sha256 "$file")"
  if [[ "$cur" != "$sha" ]]; then
    if [[ $FORCE -eq 1 ]] || { vh_is_tty && [[ "$VH_ASSUME_YES" != 1 ]] && vh_confirm "Modified since install: ${file/#$HOME/\~} - remove anyway (a copy is kept)?" n; }; then
      bk="$(vh_backup_file "$file")"; vh_dim "modified file saved to ${bk/#$HOME/\~}"
    else
      KEPT+=("$file (modified after install)"); kept=$((kept + 1)); continue
    fi
  fi
  if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "rm $file"; removed=$((removed + 1)); continue; fi
  if rm -f -- "$file"; then removed=$((removed + 1)); vh_mf_del F "$file"
  else PROBLEMS+=("could not remove $file"); fi
done

# ---- symlinks (cursor aliases): only if still pointing where we pointed them
for link in "${LINKS[@]}"; do
  rec="$(vh_mf_get S "$link")"
  IFS=$'\t' read -r _ target _ <<<"$rec"
  if [[ -L "$link" && "$(readlink -- "$link")" == "$target" ]]; then
    if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "rm $link"; removed=$((removed + 1)); continue; fi
    rm -f -- "$link" && { removed=$((removed + 1)); vh_mf_del S "$link"; }
  elif [[ ! -e "$link" && ! -L "$link" ]]; then
    vh_mf_del S "$link"
  else
    KEPT+=("$link (changed after install)"); kept=$((kept + 1))
  fi
done

# ---- restore originals that the installer moved aside
for file in "${BACKS[@]}"; do
  rec="$(vh_mf_get B "$file")"
  IFS=$'\t' read -r _ bk _ <<<"$rec"
  if [[ -e "$file" ]]; then
    PROBLEMS+=("original of ${file/#$HOME/\~} not restored - path still occupied (backup: ${bk/#$HOME/\~})"); continue
  fi
  if [[ ! -f "$bk" ]]; then PROBLEMS+=("backup missing for ${file/#$HOME/\~}: $bk"); vh_mf_del B "$file"; continue; fi
  vh_dim "restore ${file/#$HOME/\~}"
  if [[ "$VH_DRY_RUN" != 1 ]]; then
    mkdir -p -- "$(dirname -- "$file")"
    if cp -p -- "$bk" "$file"; then restored=$((restored + 1)); vh_mf_del B "$file"; fi
  else
    restored=$((restored + 1))
  fi
done

# ---- directories we created (deepest first, only if empty - never recursive)
if [[ ${#DIRS[@]} -gt 0 ]]; then
  while IFS= read -r d; do
    [[ -d "$d" ]] || { vh_mf_del D "$d"; continue; }
    if [[ -z "$(ls -A -- "$d")" ]]; then
      if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "rmdir $d"
      elif rmdir -- "$d" 2>/dev/null; then vh_mf_del D "$d"; fi
    else
      [[ "$VH_DRY_RUN" == 1 ]] || vh_mf_del D "$d"   # holds other files now: leave it, forget it
    fi
  done < <(printf '%s\n' "${DIRS[@]}" | awk '{ print length, $0 }' | sort -rn | cut -d' ' -f2-)
fi

vh_manifest_save
trap - EXIT

# ---- state directory housekeeping
if [[ "$VH_DRY_RUN" != 1 ]]; then
  if [[ $PURGE -eq 1 && -d "$VH_BACKUPS" && "$VH_BACKUPS" == */@@COMMAND@@/backups ]]; then
    rm -rf -- "$VH_BACKUPS"; vh_ok "backups deleted"
  fi
  rmdir -- "$VH_STATE_DIR/libadwaita" 2>/dev/null || true
  [[ -f "$VH_MANIFEST" || -f "$VH_SETTINGS" || -d "$VH_BACKUPS" ]] || rmdir -- "$VH_STATE_DIR" 2>/dev/null || true
fi

# ---- report
vh_step "Summary"
vh_row "Files" "removed $removed, restored $restored originals, kept $kept, already missing $n_missing"
for k in "${KEPT[@]}"; do vh_warn "kept: ${k/#$HOME/\~}"; done
for p in "${PROBLEMS[@]}"; do vh_warn "$p"; done
[[ $kept -gt 0 ]] && vh_more "re-run with --force to remove modified files (a copy is saved first)"
[[ -d "$VH_BACKUPS" ]] && vh_row "Backups" "${VH_BACKUPS/#$HOME/\~}  (delete with --purge-backups)"
vh_row "Still selected?" "switch back to Breeze (KDE) or Adwaita (GNOME) - see --help"
echo
exit 0
