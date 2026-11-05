#!/usr/bin/env bash
# @@NAME@@ static checks: every program parses, every JSON, SVG and INI file reads.
set -uo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
n=0; bad=0
chk() { n=$((n + 1)); if ! "$@" >/dev/null 2>&1; then bad=$((bad + 1)); echo "FAIL: $*"; fi; }
for f in "$ROOT"/install.sh "$ROOT"/uninstall.sh "$ROOT"/setup.sh "$ROOT"/lib/common.sh "$ROOT"/bin/@@COMMAND@@ \
         "$ROOT"/fastfetch/install-fastfetch-colours.sh "$ROOT"/sddm/apply-sddm-background.sh; do chk bash -n "$f"; done
for f in "$ROOT"/bin/@@COMMAND@@-settings "$ROOT"/bin/@@COMMAND@@-setup "$ROOT"/fastfetch/@@COMMAND@@-fastfetch.py; do
  chk python3 -I -c 'import ast, sys; ast.parse(open(sys.argv[1]).read())' "$f"; done
out="$(python3 -I - "$ROOT" <<'PY'
import json, sys, xml.etree.ElementTree as ET, gzip
from pathlib import Path
root = Path(sys.argv[1]); n = bad = 0
for p in root.rglob("*"):
    if not p.is_file() or "tests" in p.parts:
        continue
    try:
        if p.suffix == ".json":
            n += 1; json.loads(p.read_text())
        elif p.suffix == ".svg":
            n += 1; ET.parse(p)
        elif p.suffix == ".svgz":
            n += 1; ET.fromstring(gzip.decompress(p.read_bytes()))
    except Exception as e:      # noqa: BLE001
        bad += 1; print(f"FAIL: {p.relative_to(root)}: {e}")
print(f"{n} {bad}")
PY
)"
echo "$out" | grep '^FAIL' || true
read -r jn jb <<<"$(echo "$out" | tail -n1)"; n=$((n + jn)); bad=$((bad + jb))
echo "$n checks, $bad failed"
[[ $bad -eq 0 ]]
