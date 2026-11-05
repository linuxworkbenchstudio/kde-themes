#!/usr/bin/env bash
# shellcheck shell=bash disable=SC2034
# (SC2034: variables here are consumed by the scripts that source this file)
# @@NAME@@ - shared installer library. Sourced by install.sh, uninstall.sh
# and scripts/detect-env.sh. Not meant to be executed directly.
#
# Manifest ($VH_STATE_DIR/manifest.tsv), one record per line, tab-separated:
#   F <component> <sha256>            <path>   file installed by @@NAME@@
#   D <component> -                   <path>   directory created by @@NAME@@
#   B <component> <backup-path>       <path>   pre-existing file (not ours) moved aside
#   L <component> <marker>|<created>|<added-newline>  <path>   line appended to a user config file
#   P <component> <uuid>              -        GNOME Terminal dconf profile
#   S <component> <link-target>       <path>   symlink created by @@NAME@@ (cursor aliases)
#   R <component> <action-id>         -        reversible action (e.g. fastfetch recolour) undone on uninstall

@@NAMES_SH@@

[[ -n "${VH_COMMON_LOADED:-}" ]] && return 0
VH_COMMON_LOADED=1

VH_NAME="@@NAME@@"
VH_DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
VH_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
VH_STATE_DIR="$VH_DATA/@@COMMAND@@"
VH_MANIFEST="$VH_STATE_DIR/manifest.tsv"
VH_SETTINGS="$VH_STATE_DIR/previous-settings.tsv"
VH_BIN="$HOME/.local/bin"
# Cursor themes go to ~/.icons: Plasma's cursor settings (and plasma-apply-cursortheme) only look
# there and in system folders unless XCURSOR_PATH is set; KWin, X11 apps and GNOME read it too.
VH_CURSORS="$HOME/.icons"
VH_BACKUPS="$VH_STATE_DIR/backups"
VH_TS="$(date +%Y%m%d-%H%M%S)"
VH_DRY_RUN="${VH_DRY_RUN:-0}"
VH_ASSUME_YES="${VH_ASSUME_YES:-0}"

# ---------------------------------------------------------------- output
# Colour only on a terminal (NO_COLOR is respected); line-drawing glyphs only in UTF-8 locales,
# plain ASCII otherwise, so logs and piped output stay readable.
VH_UTF8=0
case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in *[Uu][Tt][Ff]-8*|*[Uu][Tt][Ff]8*) VH_UTF8=1 ;; esac
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  VH_COLOR=1
  C_B=$'\e[1m'; C_D=$'\e[2m'; C_R=$'\e[0m'
  C_OK=$'\e[38;2;@@RGB_OK@@m'; C_WARN=$'\e[38;2;@@RGB_WARM@@m'; C_ERR=$'\e[38;2;@@RGB_ERR@@m'
  C_ACC=$'\e[38;2;@@RGB_HIGHLIGHT@@m'; C_VIO=$'\e[38;2;@@RGB_LINK@@m'
  C_PINK=$'\e[38;2;@@RGB_ACCENT@@m'; C_PEACH=$'\e[38;2;@@RGB_WARM@@m'; C_MUTED=$'\e[38;2;@@RGB_MUTED@@m'
else
  VH_COLOR=0
  C_B=""; C_D=""; C_R=""; C_OK=""; C_WARN=""; C_ERR=""; C_ACC=""; C_VIO=""; C_PINK=""; C_PEACH=""; C_MUTED=""
fi
if [[ $VH_UTF8 -eq 1 ]]; then
  G_OK="✓"; G_WARN="!"; G_SKIP="–"; G_RULE="─"; G_BAR="━"; G_SEP="›"; G_DOT="·"
else
  G_OK="+"; G_WARN="!"; G_SKIP="-"; G_RULE="-"; G_BAR="="; G_SEP=">"; G_DOT="-"
fi
VH_W="${COLUMNS:-}"
[[ "$VH_W" =~ ^[0-9]+$ ]] || VH_W="$(tput cols 2>/dev/null || echo 80)"
[[ "$VH_W" =~ ^[0-9]+$ ]] || VH_W=80
(( VH_W > 78 )) && VH_W=78
(( VH_W < 50 )) && VH_W=50
VH_LABEL_W=18

vh_repeat() { local s="" i; for ((i = 0; i < $2; i++)); do s+="$1"; done; printf '%s' "$s"; }

# a rule in the theme's four brand colours, left to right
vh_brand_bar() {
  local w="$1" i t seg f r g b out=""
  if [[ $VH_COLOR -eq 0 ]]; then vh_repeat "$G_BAR" "$w"; return; fi
  local -a R=(@@BAR_R@@) G=(@@BAR_G@@) B=(@@BAR_B@@)
  for ((i = 0; i < w; i++)); do
    t=$(( w > 1 ? i * 300 / (w - 1) : 0 )); seg=$(( t / 100 )); (( seg > 2 )) && seg=2; f=$(( t - seg * 100 ))
    r=$(( R[seg] + (R[seg + 1] - R[seg]) * f / 100 ))
    g=$(( G[seg] + (G[seg + 1] - G[seg]) * f / 100 ))
    b=$(( B[seg] + (B[seg + 1] - B[seg]) * f / 100 ))
    out+=$'\e'"[38;2;${r};${g};${b}m$G_BAR"
  done
  printf '%s%s' "$out" "$C_R"
}

# vh_banner "subtitle"  - the @@NAME@@ header used at the top of each run
vh_banner() {
  local w=$(( VH_W - 4 ))
  printf '\n  %s\n' "$(vh_brand_bar "$w")"
  printf '  %s%s@@SPACED@@%s  %s%s%s\n' "$C_B" "$C_PEACH" "$C_R" "$C_MUTED" "$*" "$C_R"
  printf '  %s\n' "$(vh_brand_bar "$w")"
}

# section heading:  "  Title ──────────"
vh_step() {
  local t="$*" n
  n=$(( VH_W - 5 - ${#t} )); (( n < 3 )) && n=3
  printf '\n  %s%s%s %s%s%s\n' "$C_B$C_PINK" "$t" "$C_R" "$C_MUTED" "$(vh_repeat "$G_RULE" "$n")" "$C_R"
}
vh_sub()  { printf '\n    %s%s%s\n' "$C_B$C_PEACH" "$*" "$C_R"; }   # sub-heading inside a section
# plain messages wrap at the line width; continuation lines line up under the text
vh_wrap() { # prefix-printed-width first-prefix text
  local w=$(( VH_W - $1 )) first="$2" pad line n=0; pad="$(printf '%*s' "$1" '')"
  shift 2
  while IFS= read -r line; do
    if (( n == 0 )); then printf '%s%s\n' "$first" "$line"; else printf '%s%s\n' "$pad" "$line"; fi
    n=$((n + 1))
  done < <(printf '%s\n' "$*" | fold -s -w "$w" | sed 's/ *$//')
}
vh_info() { vh_wrap 4 "    " "$*"; }
vh_ok()   { vh_wrap 6 "    $C_OK$G_OK$C_R " "$*"; }
vh_warn() { vh_wrap 6 "    $C_WARN$G_WARN$C_R " "$*" >&2; }
vh_err()  { printf '%serror:%s %s\n' "$C_ERR" "$C_R" "$*" >&2; }
vh_die()  { vh_err "$*"; exit 1; }
vh_dim()  { local l; while IFS= read -r l; do printf '%s%s%s\n' "$C_D" "$l" "$C_R"; done < <(vh_wrap 4 "    " "$*"); }

# two-column rows for the guidance blocks
vh_row()  { printf '    %s%-*s%s %s\n' "$C_ACC" "$VH_LABEL_W" "$1" "$C_R" "$2"; }               # label text
vh_cmd()  { printf '    %s%-*s%s %s$%s %s%s%s%s\n' "$C_ACC" "$VH_LABEL_W" "$1" "$C_R" "$C_MUTED" "$C_R" \
              "$C_PEACH" "$2" "$C_R" "${3:+   $C_MUTED$3$C_R}"; }                                  # label command [note]
vh_more() { local t="$*" s=" $C_MUTED$G_SEP$C_MUTED "; [[ "$t" == *" >" ]] && t="${t% >} $G_SEP"; printf '    %-*s %s%s%s\n' "$VH_LABEL_W" "" "$C_MUTED" "${t// > /$s}" "$C_R"; }     # continuation line
vh_menu() { local p="$2" s=" $C_MUTED$G_SEP$C_R "; p="${p// > /$s}"; [[ "$p" == *" >" ]] && p="${p% >} $C_MUTED$G_SEP$C_R"; vh_row "$1" "$p"; }
vh_line() { printf '    %s$%s %s%s%s\n' "$C_MUTED" "$C_R" "$C_PEACH" "$*" "$C_R"; }                 # full-width command                 # label "A > B > C"

vh_is_tty() { [[ -t 0 && -t 1 ]]; }

# vh_confirm "question" [default y|n]
vh_confirm() {
  local q="$1" def="${2:-n}" ans prompt
  if [[ "$VH_ASSUME_YES" == 1 ]]; then return 0; fi
  if ! vh_is_tty; then [[ "$def" == y ]]; return; fi
  if [[ "$def" == y ]]; then prompt="[Y/n]"; else prompt="[y/N]"; fi
  read -r -p "    $q $prompt " ans || ans=""
  ans="${ans:-$def}"
  [[ "$ans" =~ ^[Yy]([Ee][Ss])?$ ]]
}

vh_have() { command -v "$1" >/dev/null 2>&1; }

vh_sha256() {
  if [[ -n "${VH_SHA_CACHE[$1]+x}" ]]; then printf '%s\n' "${VH_SHA_CACHE[$1]}"; return 0; fi
  if vh_have sha256sum; then sha256sum -- "$1" | cut -d' ' -f1
  elif vh_have shasum; then shasum -a 256 -- "$1" | cut -d' ' -f1
  else vh_die "neither sha256sum nor shasum is available"; fi
}
# Checksums worked out in bulk (vh_install_tree): path -> sha256. Saves two programs per file.
declare -gA VH_SHA_CACHE=()
vh_sha_into() { # varname path  - like vh_sha256, into a variable, from the cache when it can
  if [[ -n "${VH_SHA_CACHE[$2]+x}" ]]; then printf -v "$1" '%s' "${VH_SHA_CACHE[$2]}"; return 0; fi
  local h; h="$(vh_sha256 "$2")" || return 1
  VH_SHA_CACHE[$2]="$h"; printf -v "$1" '%s' "$h"
}
vh_sha_fill() { # paths... - one sha256sum for all of them (names needing escapes are left to vh_sha256)
  [[ $# -gt 0 ]] && vh_have sha256sum || return 0
  local h p
  while IFS= read -r -d $'\n' line; do
    [[ "$line" == \\* ]] && continue
    h="${line%% *}"; p="${line#*  }"
    VH_SHA_CACHE[$p]="$h"
  done < <(printf '%s\0' "$@" | xargs -0 sha256sum -- 2>/dev/null)
}

# ---------------------------------------------------------------- manifest
declare -gA VH_MF=()      # key "TYPE<TAB>path-or-uuid" -> "component<TAB>field3<TAB>path"
declare -ga VH_MF_ORDER=()

vh_mf_key() { printf '%s\t%s' "$1" "$2"; }

vh_manifest_load() {
  VH_MF=(); VH_MF_ORDER=()
  [[ -f "$VH_MANIFEST" ]] || return 0
  local t c f p key
  while IFS=$'\t' read -r t c f p || [[ -n "$t" ]]; do
    [[ -z "$t" || "$t" == \#* ]] && continue
    case "$t" in F|D|B|L|S) key="$(vh_mf_key "$t" "$p")" ;; P|R) key="$(vh_mf_key "$t" "$f")" ;; *) continue ;; esac
    [[ -n "${VH_MF[$key]+x}" ]] || VH_MF_ORDER+=("$key")
    VH_MF[$key]="$c"$'\t'"$f"$'\t'"$p"
  done < "$VH_MANIFEST"
}

vh_mf_set() { # type component field3 path
  local key
  if [[ "$1" == P || "$1" == R ]]; then key="$(vh_mf_key "$1" "$3")"; else key="$(vh_mf_key "$1" "$4")"; fi
  [[ -n "${VH_MF[$key]+x}" ]] || VH_MF_ORDER+=("$key")
  VH_MF[$key]="$2"$'\t'"$3"$'\t'"$4"
}

vh_mf_get() { # type path-or-uuid -> prints "component<TAB>field3<TAB>path" or fails
  local key; key="$(vh_mf_key "$1" "$2")"
  [[ -n "${VH_MF[$key]+x}" ]] || return 1
  printf '%s' "${VH_MF[$key]}"
}

vh_mf_del() { local key; key="$(vh_mf_key "$1" "$2")"; unset 'VH_MF[$key]'; }

vh_manifest_save() {
  [[ "$VH_DRY_RUN" == 1 ]] && return 0
  local key n=0 tmp
  for key in "${VH_MF_ORDER[@]}"; do [[ -n "${VH_MF[$key]+x}" ]] && n=$((n + 1)); done
  if [[ $n -eq 0 ]]; then rm -f -- "$VH_MANIFEST"; return 0; fi
  mkdir -p -- "$VH_STATE_DIR"
  tmp="$VH_MANIFEST.tmp.$$"
  {
    printf '# @@NAME@@ install manifest - written by install.sh, read by uninstall.sh. Do not edit.\n'
    for key in "${VH_MF_ORDER[@]}"; do
      [[ -n "${VH_MF[$key]+x}" ]] || continue
      printf '%s\t%s\n' "${key%%$'\t'*}" "${VH_MF[$key]}"
    done
  } > "$tmp"
  mv -f -- "$tmp" "$VH_MANIFEST"
}

# ---------------------------------------------------------------- safe file ops
VH_N_NEW=0; VH_N_UPDATED=0; VH_N_SAME=0; VH_N_BACKUP=0; VH_N_FAIL=0

# Only ever write inside the user's own data/config directories.
vh_assert_user_path() {
  local p="$1"
  case "$p" in
    "$VH_DATA"/*|"$VH_CONFIG"/*|"$VH_BIN"/*) ;;
    "$VH_CURSORS"|"$VH_CURSORS"/"$(tw_name cursors Dark)"|"$VH_CURSORS"/"$(tw_name cursors Dark)"/*|"$VH_CURSORS"/"$(tw_name cursors Light)"|"$VH_CURSORS"/"$(tw_name cursors Light)"/*) ;;   # only our own cursor themes in ~/.icons
    *) vh_die "refusing to write outside the user data/config directories: $p" ;;
  esac
  [[ "$p" != *"/../"* && "$p" != *"/.." ]] || vh_die "refusing path with '..': $p"
}

# vh_retire_tree prefix  - remove what an older version installed under prefix (files that are
# unchanged since install, our symlinks, then our now-empty directories); edited files stay.
vh_retire_tree() {
  local prefix="${1%/}" key t f p cur kept=0 dirs=()
  for key in "${!VH_MF[@]}"; do
    t="${key%%$'\t'*}"; p="${key#*$'\t'}"
    [[ "$p" == "$prefix" || "$p" == "$prefix"/* ]] || continue
    IFS=$'\t' read -r _ f _ <<<"${VH_MF[$key]}"
    case "$t" in
      F) if [[ ! -e "$p" ]]; then vh_mf_del F "$p"
         elif [[ -f "$p" && ! -L "$p" ]] && cur="$(vh_sha256 "$p")" && [[ "$cur" == "$f" ]]; then
           [[ "$VH_DRY_RUN" == 1 ]] || { rm -f -- "$p" && vh_mf_del F "$p"; }
         else kept=$((kept + 1)); fi ;;
      S) if [[ -L "$p" && "$(readlink -- "$p")" == "$f" ]] || [[ ! -e "$p" && ! -L "$p" ]]; then
           [[ "$VH_DRY_RUN" == 1 ]] || { rm -f -- "$p"; vh_mf_del S "$p"; }
         else kept=$((kept + 1)); fi ;;
      D) dirs+=("$p") ;;
    esac
  done
  if [[ ${#dirs[@]} -gt 0 && "$VH_DRY_RUN" != 1 ]]; then
    while IFS= read -r p; do
      [[ -d "$p" ]] || { vh_mf_del D "$p"; continue; }
      [[ -z "$(ls -A -- "$p")" ]] && rmdir -- "$p" 2>/dev/null && vh_mf_del D "$p"
    done < <(printf '%s\n' "${dirs[@]}" | awk '{ print length, $0 }' | sort -rn | cut -d' ' -f2-)
  fi
  (( kept == 0 )) || vh_warn "kept $kept edited file(s) in ${prefix/#$HOME/\~} from an older version"
  return 0
}

# Create a directory (and missing parents), recording the ones we created.
vh_mkdir_p() {
  local comp="$1" dir="$2" d missing=()
  [[ -d "$dir" ]] && return 0
  d="$dir"
  while [[ ! -d "$d" && "$d" != / && -n "$d" ]]; do missing=("$d" "${missing[@]}"); d="${d%/*}"; [[ -n "$d" ]] || d=/; done
  for d in "${missing[@]}"; do
    if [[ -e "$d" ]]; then vh_err "$d exists and is not a directory"; return 1; fi
    if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "mkdir $d"; continue; fi
    mkdir -- "$d" || return 1
    vh_mf_set D "$comp" - "$d"
  done
}

vh_backup_file() { # path kind(own|foreign) -> prints backup path
  local src="$1" rel dst
  rel="${src#"$HOME"/}"
  dst="$VH_BACKUPS/$VH_TS/$rel"
  if [[ "$VH_DRY_RUN" == 1 ]]; then printf '%s' "$dst"; return 0; fi
  mkdir -p -- "$(dirname -- "$dst")"
  cp -p -- "$src" "$dst"
  printf '%s' "$dst"
}

# vh_install_file component src dest [mode]
vh_install_file() {
  local comp="$1" src="$2" dest="$3" mode="${4:-644}" new_sha cur_sha kind bk
  vh_assert_user_path "$dest"
  [[ -f "$src" ]] || { vh_err "missing source file: $src"; VH_N_FAIL=$((VH_N_FAIL + 1)); return 1; }
  if [[ -d "$dest" && ! -L "$dest" ]]; then
    vh_err "a directory is in the way, skipping: $dest"; VH_N_FAIL=$((VH_N_FAIL + 1)); return 1
  fi
  vh_mkdir_p "$comp" "${dest%/*}" || { VH_N_FAIL=$((VH_N_FAIL + 1)); return 1; }
  vh_sha_into new_sha "$src"
  if [[ -e "$dest" || -L "$dest" ]]; then
    vh_sha_into cur_sha "$dest" 2>/dev/null || cur_sha=none
    if [[ "$cur_sha" == "$new_sha" && ! -L "$dest" ]]; then
      vh_mf_set F "$comp" "$new_sha" "$dest"
      VH_N_SAME=$((VH_N_SAME + 1))
      return 0
    fi
    local rec rec_sha; kind=foreign
    if rec="$(vh_mf_get F "$dest")"; then kind=own; IFS=$'\t' read -r _ rec_sha _ <<<"$rec"; fi
    if [[ $kind == own && "$cur_sha" == "$rec_sha" ]]; then
      : # our own older version, unchanged since we installed it: just update it (no backup needed)
    else
      bk="$(vh_backup_file "$dest")"
      VH_N_BACKUP=$((VH_N_BACKUP + 1))
      if [[ $kind == foreign ]]; then
        # a file we did not install: restore it on uninstall
        [[ -n "$(vh_mf_get B "$dest" 2>/dev/null)" ]] || vh_mf_set B "$comp" "$bk" "$dest"
        vh_warn "existing file backed up: ${dest/#$HOME/\~} -> ${bk/#$HOME/\~}"
      else
        # ours, but changed since (by you or another tool): keep that copy, one line per install
        VH_N_EDITED=$((${VH_N_EDITED:-0} + 1))
      fi
    fi
    VH_N_UPDATED=$((VH_N_UPDATED + 1))
  else
    VH_N_NEW=$((VH_N_NEW + 1))
  fi
  if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "install $dest"; return 0; fi
  local tmp="$dest.vh-tmp.$$" ok=0
  if [[ -e "$dest" || -L "$dest" ]]; then   # replace in one step, so a crash never leaves half a file
    install -m "$mode" -- "$src" "$tmp" && mv -f -- "$tmp" "$dest" && ok=1
  else
    install -m "$mode" -- "$src" "$dest" && ok=1
  fi
  if [[ $ok -eq 1 ]]; then
    VH_SHA_CACHE[$dest]="$new_sha"
    vh_mf_set F "$comp" "$new_sha" "$dest"
  else
    rm -f -- "$tmp"; vh_err "could not write $dest"; VH_N_FAIL=$((VH_N_FAIL + 1)); return 1
  fi
}

# vh_install_symlink component target linkpath  (target is relative, inside the same directory)
vh_install_symlink() {
  local comp="$1" target="$2" link="$3" bk
  vh_assert_user_path "$link"
  if [[ -L "$link" && "$(readlink -- "$link")" == "$target" ]]; then
    vh_mf_set S "$comp" "$target" "$link"; VH_N_SAME=$((VH_N_SAME + 1)); return 0
  fi
  if [[ -e "$link" || -L "$link" ]]; then
    if [[ -d "$link" && ! -L "$link" ]]; then vh_err "a directory is in the way: $link"; VH_N_FAIL=$((VH_N_FAIL + 1)); return 1; fi
    if [[ "$VH_DRY_RUN" != 1 ]]; then
      if [[ -L "$link" ]]; then rm -f -- "$link"
      else
        bk="$(vh_backup_file "$link")"
        vh_mf_get F "$link" >/dev/null 2>&1 || vh_mf_set B "$comp" "$bk" "$link"
        rm -f -- "$link"
      fi
    fi
    VH_N_UPDATED=$((VH_N_UPDATED + 1))
  else
    VH_N_NEW=$((VH_N_NEW + 1))
  fi
  if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "ln -s $target $link"; return 0; fi
  ln -s -- "$target" "$link" && vh_mf_set S "$comp" "$target" "$link"
}

# vh_install_tree component srcdir destdir
vh_install_tree() { # component src dest [relative path to skip]
  local comp="$1" src="$2" dest="$3" skip="${4:-}" f rel rc=0 files=() have=()
  [[ -d "$src" ]] || { vh_err "missing source directory: $src"; VH_N_FAIL=$((VH_N_FAIL + 1)); return 1; }
  while IFS= read -r -d '' f; do files+=("$f"); done < <(find "$src" -type f -print0 | sort -z)
  # checksums in bulk: every source file, and whatever is already at the destination
  vh_sha_fill "${files[@]}"
  for f in "${files[@]}"; do rel="${f#"$src"/}"; [[ -f "$dest/$rel" && ! -L "$dest/$rel" ]] && have+=("$dest/$rel"); done
  vh_sha_fill "${have[@]}"
  for f in "${files[@]}"; do
    rel="${f#"$src"/}"
    [[ -n "$skip" && "$rel" == "$skip" ]] && continue
    vh_install_file "$comp" "$f" "$dest/$rel" || rc=1
  done
  return $rc
}

# vh_install_rendered component src dest token value  (simple @TOKEN@ substitution)
vh_install_rendered() {
  local comp="$1" src="$2" dest="$3" token="$4" value="$5" tmp rc
  tmp="$(mktemp)"
  local esc="${value//\\/\\\\}"; esc="${esc//&/\\&}"; esc="${esc//|/\\|}"
  sed "s|$token|$esc|g" "$src" > "$tmp"
  vh_install_file "$comp" "$tmp" "$dest"; rc=$?
  rm -f -- "$tmp"
  return $rc
}

# vh_inject_line component file line marker  - append one marked line to a user config file
vh_inject_line() {
  local comp="$1" file="$2" line="$3" marker="$4" created=0 addnl=0
  vh_assert_user_path "$file"
  if [[ -f "$file" ]] && grep -qF -- "$marker" "$file"; then
    # keep an existing record (it knows whether we created the file)
    vh_mf_get L "$file" >/dev/null 2>&1 || vh_mf_set L "$comp" "$marker|0|0" "$file"
    vh_ok "already present in ${file/#$HOME/\~}"
    return 0
  fi
  if [[ "$VH_DRY_RUN" == 1 ]]; then vh_dim "append to $file: $line"; return 0; fi
  vh_mkdir_p "$comp" "$(dirname -- "$file")" || return 1
  if [[ -f "$file" ]]; then
    local bk; bk="$(vh_backup_file "$file")"; vh_dim "backed up ${file/#$HOME/\~} -> ${bk/#$HOME/\~}"
    # make sure we start on a new line
    if [[ -s "$file" && "$(tail -c1 -- "$file" | od -An -c | tr -d ' ')" != '\n' ]]; then
      printf '\n' >> "$file"; addnl=1
    fi
  else
    created=1
  fi
  printf '%s\n' "$line" >> "$file"
  vh_mf_set L "$comp" "$marker|$created|$addnl" "$file"
}

# ---------------------------------------------------------------- environment
VH_OS=""; VH_OS_ID=""; VH_OS_LIKE=""; VH_SESSION=""; VH_SESSION_TYPE=""
VH_PLASMA_VER=""; VH_GNOME_VER=""; VH_GTK3=""; VH_GTK4=""; VH_ADW=""
VH_IS_KDE=0; VH_IS_GNOME=0; VH_HAVE_PLASMA=0; VH_HAVE_GNOME=0

vh_lib_version() { # soname -> version from pkg-config or "present"/""
  local pc="$1" so="$2" v=""
  if vh_have pkg-config; then v="$(pkg-config --modversion "$pc" 2>/dev/null || true)"; fi
  if [[ -z "$v" ]]; then
    if { vh_have ldconfig && ldconfig -p 2>/dev/null | grep -q "$so"; } ||
       compgen -G "/usr/lib*/$so*" >/dev/null || compgen -G "/usr/lib/*/$so*" >/dev/null; then
      v="present"
    fi
  fi
  printf '%s' "$v"
}

vh_gtk4_from_soname() { # libgtk-4.so.1.2004.4 -> 4.20.4 (GTK encodes minor*100 in the file name)
  local f n
  for f in /usr/lib*/libgtk-4.so.1.* /usr/lib/*/libgtk-4.so.1.*; do
    [[ -e "$f" ]] || continue
    n="${f##*/libgtk-4.so.1.}"
    if [[ "$n" =~ ^([0-9]+)\.([0-9]+)$ ]]; then
      printf '4.%d.%s' "$((10#${BASH_REMATCH[1]} / 100))" "${BASH_REMATCH[2]}"; return 0
    fi
  done
  printf 'present'
}

vh_gtk4_minor() { # prints the GTK 4 minor version, or nothing when unknown
  [[ "${VH_GTK4:-}" =~ ^4\.([0-9]+) ]] && printf '%s' "${BASH_REMATCH[1]}"
  return 0
}

vh_detect() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    VH_OS="$(. /etc/os-release && printf '%s' "${PRETTY_NAME:-$NAME}")"
    VH_OS_ID="$(. /etc/os-release && printf '%s' "${ID:-}")"
    VH_OS_LIKE="$(. /etc/os-release && printf '%s' "${ID_LIKE:-}")"
  else
    VH_OS="$(uname -s)"
  fi
  VH_SESSION="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-none}}"
  VH_SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"
  [[ "${VH_SESSION^^}" == *KDE* ]] && VH_IS_KDE=1
  [[ "${VH_SESSION^^}" == *GNOME* ]] && VH_IS_GNOME=1
  if vh_have plasmashell; then
    VH_PLASMA_VER="$(plasmashell --version 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)+' | head -n1 || true)"
    VH_HAVE_PLASMA=1
  elif vh_have plasma-apply-colorscheme; then
    VH_HAVE_PLASMA=1; VH_PLASMA_VER="unknown"
  fi
  if vh_have gnome-shell; then
    VH_GNOME_VER="$(gnome-shell --version 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)*' | head -n1 || true)"
    VH_HAVE_GNOME=1
  fi
  VH_GTK3="$(vh_lib_version gtk+-3.0 libgtk-3.so.0)"
  VH_GTK4="$(vh_lib_version gtk4 libgtk-4.so.1)"
  [[ "$VH_GTK4" == present ]] && VH_GTK4="$(vh_gtk4_from_soname)"
  VH_ADW="$(vh_lib_version libadwaita-1 libadwaita-1.so.0)"
}

VH_UT_UUID="user-theme@gnome-shell-extensions.gcampax.github.com"
# gsettings for User Themes: its schema is global when a distro package installed the extension,
# otherwise it sits in the extension's folder (extensions.gnome.org) and needs --schemadir
vh_ut_gs() {
  local d
  vh_have gsettings || return 1
  if gsettings list-schemas 2>/dev/null | grep -qx org.gnome.shell.extensions.user-theme; then gsettings "$@"; return; fi
  for d in "$VH_DATA/gnome-shell/extensions/$VH_UT_UUID/schemas" "/usr/share/gnome-shell/extensions/$VH_UT_UUID/schemas" \
           "/usr/local/share/gnome-shell/extensions/$VH_UT_UUID/schemas"; do
    [[ -f "$d/gschemas.compiled" ]] && { gsettings --schemadir "$d" "$@"; return; }
  done
  return 1
}

vh_user_theme_enabled() {
  vh_have gnome-extensions || return 1
  gnome-extensions list --enabled 2>/dev/null | grep -q '^user-theme@gnome-shell-extensions'
}

vh_icon_theme_present() { # name
  local d
  for d in "$VH_DATA/icons" "$HOME/.icons" /usr/share/icons /usr/local/share/icons; do
    [[ -f "$d/$1/index.theme" ]] && return 0
  done
  return 1
}

# qdbus has a different name on each distribution: qdbus6 (Arch, openSUSE), qdbus-qt6 (Fedora),
# /usr/lib/qt6/bin/qdbus (Debian/Ubuntu)
vh_qdbus() { local q; for q in qdbus6 qdbus-qt6 /usr/lib/qt6/bin/qdbus /usr/lib64/qt6/bin/qdbus /usr/libexec/qt6/qdbus qdbus; do
  if [[ "$q" == /* ]]; then [[ -x "$q" ]] && { printf '%s' "$q"; return 0; }
  else command -v "$q" >/dev/null 2>&1 && { printf '%s' "$q"; return 0; }; fi
done; return 1; }

# ---- GTK apps on Plasma (Firefox, GIMP, Inkscape ...)
# set one key in the [Settings] group of a GTK settings.ini, leaving every other line as it is
vh_ini_set() { # file key value
  local f="$1" k="$2" v="$3" tmp
  mkdir -p -- "$(dirname -- "$f")" || return 1
  [[ -f "$f" ]] || : > "$f"
  tmp="$(mktemp)"
  awk -v k="$k" -v v="$v" '
    /^[[:space:]]*\[/ { if (ins && !done) { print k "=" v; done = 1 }; ins = ($0 ~ /^[[:space:]]*\[Settings\][[:space:]]*$/) }
    ins && !done && $0 ~ ("^[[:space:]]*" k "[[:space:]]*=") { print k "=" v; done = 1; next }
    { print }
    END { if (!done) { if (!ins) print "[Settings]"; print k "=" v } }' "$f" > "$tmp" &&
    cat -- "$tmp" > "$f"
  local rc=$?; rm -f -- "$tmp"; return $rc
}
# the GTK theme in use: Plasma's GTK settings service (kde-gtk-config) first, then GTK's own file
vh_gtk_now() {
  local q t
  if q="$(vh_qdbus)" && t="$("$q" org.kde.GtkConfig /GtkConfig org.kde.GtkConfig.gtkTheme 2>/dev/null)" && [[ -n "$t" ]]; then
    printf '%s' "$t"; return 0
  fi
  sed -n 's/^[[:space:]]*gtk-theme-name[[:space:]]*=[[:space:]]*//p' "$VH_CONFIG/gtk-3.0/settings.ini" 2>/dev/null | head -n1
}
vh_gtk_default() { if [[ -d /usr/share/themes/Breeze/gtk-3.0 ]]; then printf Breeze; else printf Adwaita; fi; }
# switch GTK apps to a theme. With kde-gtk-config, Plasma does it (and tells running apps);
# without it only the gtk-theme-name line of GTK's own settings files is changed.
vh_gtk_set() { # theme
  local q d
  if q="$(vh_qdbus)" && "$q" org.kde.GtkConfig /GtkConfig org.kde.GtkConfig.setGtkTheme "$1" >/dev/null 2>&1; then
    return 0
  fi
  for d in gtk-3.0 gtk-4.0; do vh_ini_set "$VH_CONFIG/$d/settings.ini" gtk-theme-name "$1" || return 1; done
  if vh_have gsettings && gsettings list-schemas 2>/dev/null | grep -qx org.gnome.desktop.interface; then
    gsettings set org.gnome.desktop.interface gtk-theme "$1" 2>/dev/null || true   # read by Flatpak's settings portal
  fi
  return 0
}
# Plasma's GTK settings module (kde-gtk-config / kde-config-gtk-style)
vh_gtkconfig_present() {
  local f
  for f in /usr/lib/qt6/plugins/kf6/kded/gtkconfig.so /usr/lib64/qt6/plugins/kf6/kded/gtkconfig.so \
           /usr/lib/*/qt6/plugins/kf6/kded/gtkconfig.so; do
    [[ -e "$f" ]] && return 0
  done
  local q; q="$(vh_qdbus)" && "$q" org.kde.GtkConfig /GtkConfig >/dev/null 2>&1
}

# The wallpaper image of the first desktop (Plasma keeps it in its applets file), or nothing
vh_current_wallpaper() {
  local f="$VH_CONFIG/plasma-org.kde.plasma.desktop-appletsrc"
  [[ -f "$f" ]] || return 0
  awk '/^\[Containments\]\[[0-9]+\]\[Wallpaper\]\[org\.kde\.image\]\[General\]$/ {g=1; next}
       /^\[/ {g=0} g && /^Image=/ {sub(/^Image=/, ""); sub(/^file:\/\//, ""); print; exit}' "$f"
}

vh_print_env() {
  local t
  vh_step "Your system"
  vh_row "OS" "${VH_OS:-unknown}"
  vh_row "Session" "$VH_SESSION ($VH_SESSION_TYPE)"
  vh_row "KDE Plasma" "${VH_PLASMA_VER:-not installed}"
  vh_row "Installs into" "${VH_DATA/#$HOME/\~}  and  ${VH_CONFIG/#$HOME/\~}"
  vh_step "Tools it uses"
  for t in plasma-apply-colorscheme plasma-apply-desktoptheme plasma-apply-wallpaperimage plasma-apply-lookandfeel \
           kreadconfig6 kwriteconfig6 konsole kvantummanager; do
    if vh_have "$t"; then vh_ok "$t"; else vh_dim "$G_SKIP $t (not found)"; fi
  done
  if vh_icon_theme_present Papirus; then vh_ok "Papirus icon theme (fills in icons @@NAME@@ doesn't draw)"
  else vh_dim "$G_SKIP Papirus icon theme not found (those icons come from Breeze)"; fi
}
