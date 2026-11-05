#!/usr/bin/env bash
# @@NAME@@ Setup - the guided, full-screen installer (the same as running ./install.sh in a
# terminal). Nothing changes until you press Install on its Review screen.
# (Prefer flags? Use ./install.sh directly - see ./install.sh --help.)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null 2>&1 || { echo "Setup needs python3 - or run ./install.sh (no python needed)." >&2; exit 1; }
exec python3 -I "$HERE/bin/@@COMMAND@@-setup" "$HERE" "$@"
