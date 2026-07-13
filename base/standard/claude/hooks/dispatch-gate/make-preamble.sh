#!/usr/bin/env bash
# make-preamble.sh — regenerate the FIELDBOOK DISPATCH PREAMBLE header hash after editing the primitives.
# provenance: kit-template · created: 2026-07-13 · last-modified: 2026-07-13
#
# The preamble carries a version/hash header the dispatch-conformance gate checks (CW1). After ANY edit to
# the primitives, run this to recompute the canonical body hash and rewrite the header in place. The
# canonicalisation + rewrite live in dispatch-gate.py (ONE source of truth, shared with the live gate), so
# the header and the gate can never compute the hash two different ways.
#
# After a version bump, ALSO update PINNED_PREAMBLES in dispatch-gate.py to the printed hash — the gate's
# self-check (`dispatch-gate.py --self-check`) FAILS LOUD if the pin and the shipped preamble drift.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="${1:-$DIR/preamble.js}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "make-preamble: python3 is required to compute the canonical hash." >&2
  exit 1
fi

python3 "$DIR/dispatch-gate.py" --make-preamble "$FILE"
