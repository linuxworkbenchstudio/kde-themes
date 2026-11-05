#!/bin/sh
# @@NAME@@ colours for Fastfetch - works on any Linux distro, with or without the rest of @@NAME@@.
# Keeps your Fastfetch design (logo, modules, layout); only the colours change to @@NAME@@'s.
#
#   ./install-fastfetch-colours.sh            preview: show what would change (changes nothing)
#   ./install-fastfetch-colours.sh --apply    recolour your Fastfetch config (original kept)
#   ./install-fastfetch-colours.sh --restore  put your original Fastfetch config back
#   ./install-fastfetch-colours.sh --design --apply
#                                             optional: use the @@NAME@@ Fastfetch design instead
#                                             (@@NAME@@ logo + module list); your config is kept
#                                             and comes back with --restore
# Options:  --dark | --light   palette to use (default: follows KDE's colour scheme, else dark)
#           --yes              install missing Fastfetch/Python without asking (uses sudo)
#           --quiet            no diff, just the summary
#
# Needs Fastfetch and Python 3. If either is missing it shows the install command for your
# distro and, with --apply in a terminal, asks before running it (that step uses sudo).
# Everything else happens in your home folder only.
set -eu
SELF=$(readlink -f "$0" 2>/dev/null || echo "$0")
HERE=$(dirname "$SELF")
TOOL="$HERE/@@COMMAND@@-fastfetch.py"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
DEST="$DATA/@@COMMAND@@/fastfetch/@@COMMAND@@-fastfetch.py"

APPLY=0; RESTORE=0; YES=0; DESIGN=0; VARIANT=auto; Q=""
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --restore) RESTORE=1 ;;
    --design) DESIGN=1 ;;
    --dark) VARIANT=dark ;;
    --light) VARIANT=light ;;
    --yes|-y) YES=1 ;;
    --quiet|-q) Q=--quiet ;;
    -h|--help) sed -n '2,20p' "$SELF" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg  (see --help)" >&2; exit 2 ;;
  esac
done
[ -f "$TOOL" ] || TOOL="$DEST"
[ -f "$TOOL" ] || { echo "@@COMMAND@@-fastfetch.py not found next to this script" >&2; exit 1; }

# ---- package manager: the command that installs <package> on this distro ----
pm_cmd() {   # $1 = fastfetch | python
  pkg=$1
  if command -v pacman >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python; echo "sudo pacman -S --needed $pkg"
  elif command -v apt-get >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo apt-get install -y $pkg"
  elif command -v dnf >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo dnf install -y $pkg"
  elif command -v zypper >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo zypper install -y $pkg"
  elif command -v xbps-install >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo xbps-install -Sy $pkg"
  elif command -v apk >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo apk add $pkg"
  elif command -v eopkg >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "sudo eopkg install -y $pkg"
  elif command -v emerge >/dev/null 2>&1; then
    [ "$pkg" = fastfetch ] && pkg=app-misc/fastfetch || pkg=dev-lang/python; echo "sudo emerge --ask $pkg"
  elif command -v nix-env >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "nix-env -iA nixpkgs.$pkg"
  elif command -v brew >/dev/null 2>&1; then
    [ "$pkg" = python ] && pkg=python3; echo "brew install $pkg"
  fi
}

ask() {   # ask "<question>"  -> 0 for yes (only in a terminal; default no)
  [ $YES = 1 ] && return 0
  [ -t 0 ] || return 1
  printf '%s [y/N] ' "$1"; read -r r || return 1
  case "$r" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

need() {   # need <command> <package> <what for>
  command -v "$1" >/dev/null 2>&1 && return 0
  cmd=$(pm_cmd "$2")
  echo "$1 is not installed ($3)."
  if [ -z "$cmd" ]; then
    echo "  Install '$2' with your distro's package manager, then run this again."
    return 1
  fi
  echo "  To install it:  $cmd"
  if [ "$2" = fastfetch ] && command -v apt-get >/dev/null 2>&1; then
    echo "  (Debian 13+ and Ubuntu 25.04+ have it; on older Ubuntu add ppa:zhangsongcui3371/fastfetch first.)"
  fi
  if [ $APPLY = 1 ] && ask "  Run that now?"; then
    sh -c "$cmd" && command -v "$1" >/dev/null 2>&1 && return 0
    echo "  Install did not finish; you can run the command above yourself."
  fi
  return 1
}

echo "@@NAME@@ colours for Fastfetch"
if ! need python3 python "this script needs Python 3"; then
  echo "Nothing was changed."; exit 1
fi
if [ $RESTORE = 1 ]; then
  exec python3 -I "$TOOL" --restore
fi
need fastfetch fastfetch "the system-info tool these colours are for" || \
  echo "  Continuing: the colours are set up now and Fastfetch will use them once it is installed."

FROM=""
if [ $DESIGN = 1 ]; then
  # the optional @@NAME@@ design: config + logo from this folder; the logo path is written for
  # this user's config folder. The recolour step below backs up the current config first.
  [ -f "$HERE/design/config.jsonc" ] && [ -f "$HERE/design/@@COMMAND@@-logo.txt" ] || \
    { echo "design/ files not found next to this script" >&2; exit 1; }
  CONF="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
  TMPD=$(mktemp -d); trap 'rm -rf "$TMPD"' EXIT
  sed "s|~/.config/fastfetch/@@COMMAND@@-logo.txt|$CONF/@@COMMAND@@-logo.txt|" "$HERE/design/config.jsonc" > "$TMPD/config.jsonc"
  FROM="--from $TMPD/config.jsonc"
  echo "@@NAME@@ design: logo -> $CONF/@@COMMAND@@-logo.txt"
  if [ $APPLY = 1 ]; then
    mkdir -p "$CONF"
    if [ -f "$CONF/@@COMMAND@@-logo.txt" ] && ! cmp -s "$HERE/design/@@COMMAND@@-logo.txt" "$CONF/@@COMMAND@@-logo.txt"; then
      cp "$CONF/@@COMMAND@@-logo.txt" "$CONF/@@COMMAND@@-logo.txt.@@COMMAND@@-previous"
    fi
    cp "$HERE/design/@@COMMAND@@-logo.txt" "$CONF/@@COMMAND@@-logo.txt"
  fi
fi

if [ $APPLY = 1 ]; then
  # keep a copy where `@@COMMAND@@ dark|light` can find it, so switching keeps Fastfetch in step
  if [ "$TOOL" != "$DEST" ]; then
    mkdir -p "$(dirname "$DEST")"; cp "$TOOL" "$DEST"; chmod 755 "$DEST"
  fi
  python3 -I "$DEST" --apply --variant "$VARIANT" $Q $FROM
  echo "Run  fastfetch  to see it. Undo:  $0 --restore"
else
  python3 -I "$TOOL" --variant "$VARIANT" $Q $FROM
  echo "Preview only. Add  --apply  to write it."
fi
