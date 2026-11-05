#!/usr/bin/env bash
# @@NAME@@ - optional SDDM (Breeze greeter) background. Requires sudo.
# Never run automatically by install.sh. See README.md next to this script.
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$HERE/../../.." && pwd)"
THEME_DIR="${SDDM_BREEZE_DIR:-/usr/share/sddm/themes/breeze}"
CONF="$THEME_DIR/theme.conf.user"
BACKUP="$CONF.@@COMMAND@@-backup"
MARK="$THEME_DIR/.@@COMMAND@@-created-conf"
IMG="$THEME_DIR/@@COMMAND@@-background.jpg"
variant=dark
action=apply
dry=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [--variant dark|light] [--restore] [--dry-run]

Sets the @@NAME@@ wallpaper as the background of the Breeze SDDM theme.
  --variant dark|light   wallpaper to use (default: dark)
  --restore              undo a previous apply
  --dry-run              print the commands without running them
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --variant) variant="${2:-}"; shift 2 ;;
    --restore) action=restore; shift ;;
    --dry-run|-n) dry=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ "$variant" == dark || "$variant" == light ]] || { echo "--variant must be dark or light" >&2; exit 2; }

run() {
  printf '  + %s\n' "$*"
  [[ $dry -eq 1 ]] || sudo "$@"
}

if [[ ! -f "$THEME_DIR/Main.qml" && ! -f "$THEME_DIR/metadata.desktop" ]]; then
  echo "Breeze SDDM theme not found at $THEME_DIR - nothing to do." >&2
  exit 1
fi

if [[ $action == apply ]]; then
  src="$ROOT/assets/wallpapers/@@COMMAND@@-$variant.jpg"
  [[ -f "$src" ]] || { echo "Wallpaper not found: $src" >&2; exit 1; }
  echo "This will (with sudo):"
  echo "  - copy $src to $IMG"
  [[ -f "$CONF" && ! -f "$BACKUP" ]] && echo "  - back up $CONF to $BACKUP"
  echo "  - write background=$IMG and type=image to $CONF"
  if [[ $dry -eq 0 ]]; then
    read -r -p "Continue? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
  fi
  run install -m 644 "$src" "$IMG"
  if [[ -f "$CONF" && ! -f "$BACKUP" && ! -f "$MARK" ]]; then
    run cp -p "$CONF" "$BACKUP"
  elif [[ ! -f "$CONF" ]]; then
    run touch "$MARK"
  fi
  tmp="$(mktemp)"
  printf '[General]\nbackground=%s\ntype=image\n' "$IMG" > "$tmp"
  run install -m 644 "$tmp" "$CONF"
  rm -f "$tmp"
  echo "Done. Log out to see the login screen, or preview with: sddm-greeter-qt6 --test-mode --theme $THEME_DIR"
else
  echo "Restoring the Breeze SDDM background (with sudo)."
  if [[ $dry -eq 0 ]]; then
    read -r -p "Continue? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
  fi
  if [[ -f "$BACKUP" ]]; then
    run mv -f "$BACKUP" "$CONF"
  elif [[ -f "$MARK" ]]; then
    run rm -f "$CONF" "$MARK"
  else
    echo "No @@NAME@@ backup found; leaving $CONF untouched."
  fi
  [[ -f "$IMG" ]] && run rm -f "$IMG"
  echo "Restored."
fi
