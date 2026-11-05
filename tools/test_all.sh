#!/usr/bin/env bash
# Every check, for every pack:
#   tools/test_all.sh           engine tests (incl. both released themes reproduced), then per pack:
#                               build + static checks (programs parse, JSON/SVG read)
#   tools/test_all.sh --full    the same, plus each pack's full test suite (install, switch and
#                               uninstall in a throw-away home; about 40 minutes per pack, run in parallel)
set -uo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
FULL=0; [[ "${1:-}" == --full ]] && FULL=1
fail=0
echo "== engine tests"; python3 -m unittest -q 2>&1 | tail -3 || fail=1
python3 -m unittest -q >/dev/null 2>&1 || fail=1
OUT="$(mktemp -d)"; trap 'rm -rf -- "$OUT"' EXIT
packs=(); for p in packs/*/pack.toml; do packs+=("$(basename "$(dirname "$p")")"); done
for p in "${packs[@]}"; do
  echo "== $p"
  python3 -m engine build "packs/$p" --out "$OUT" >/dev/null || { echo "  build FAILED"; fail=1; continue; }
  bash "$OUT/$p/tests/validate.sh" | tail -1 || fail=1
done
if [[ $FULL -eq 1 ]]; then
  for p in "${packs[@]}"; do ( cd "$OUT/$p" && bash tests/run-tests.sh --no-static > "$OUT/$p.log" 2>&1 ) & done
  wait
  for p in "${packs[@]}"; do
    s="$(sed 's/\x1b\[[0-9;]*m//g' "$OUT/$p.log" | grep -E '[0-9]+ passed, [0-9]+ failed' | tail -1)"
    echo "== $p suite: ${s:-no summary}"
    [[ "$s" == *" 0 failed"* ]] || { fail=1; sed 's/\x1b\[[0-9;]*m//g' "$OUT/$p.log" | grep '^  FAIL'; }
  done
fi
[[ $fail -eq 0 ]] && echo "all passed" || { echo "FAILED"; exit 1; }
