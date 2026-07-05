#!/usr/bin/env bash
# lint-agent-docs-indexes.sh — index-completeness lint (CONVENTIONS "index completeness" rule).
#
# The FAST, index-only check used by the SessionStart router (warn mode) and the pre-commit
# gate (--strict). The full doc-schema linter (lint-docs.py) folds this same check in as one of
# its rules; this script is the cheap standalone surface so a session start does not pay for the
# whole schema pass.
#
# Check: for each managed dir (populated content dirs under .agent-docs/), compare the on-disk
# *.md basename set (excluding index.md) against `file.md` backtick tokens in that dir's index.md:
#   - missing index.md (populated managed dir without one)
#   - unindexed files (on disk, not referenced)
#   - phantom entries (referenced bare token, no such file in dir)
#
# Token contract (per the CONVENTIONS index template): in-dir files are referenced as `file.md`
# (bare backtick token); cross-dir references use relative paths (`../dir/file.md`) and are
# ignored here (tokens containing '/' are skipped). Presence-only by design.
#
# Modes: default = warn (always exit 0; one line per drifting dir, silent when clean).
#        --strict = exit 1 if any drift (CI / gate use).
# Deps: bash 3.2+, find, sort, comm, grep, sed. No jq, no GNU-isms.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOCS="$REPO_ROOT/.agent-docs"
STRICT=0
[ "${1:-}" = "--strict" ] && STRICT=1

# No .agent-docs/ yet (e.g. a fresh clone before install) → nothing to lint.
[ -d "$DOCS" ] || exit 0

# Managed dirs: structurally derived — top-level dirs with >=1 non-index .md,
# except now/ + templates/ (fleeting/scaffold, permanently out of scope);
# plus populated nested content dirs one level down.
managed_dirs() {
  for d in "$DOCS"/*/; do
    [ -d "$d" ] || continue
    base="$(basename "$d")"
    case "$base" in now | templates) continue ;; esac
    n=$(find "$d" -maxdepth 1 -name '*.md' ! -name 'index.md' | wc -l | tr -d ' ')
    [ "$n" -gt 0 ] && echo "$d"
    for sub in "$d"*/; do
      [ -d "$sub" ] || continue
      sn=$(find "$sub" -maxdepth 1 -name '*.md' ! -name 'index.md' | wc -l | tr -d ' ')
      [ "$sn" -gt 0 ] && echo "$sub"
    done
  done
}

DRIFT=0
for dir in $(managed_dirs); do
  rel="${dir#"$DOCS"/}"
  rel="${rel%/}"
  idx="$dir/index.md"
  if [ ! -f "$idx" ]; then
    echo "index drift: ${rel}/ — MISSING index.md ($(find "$dir" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ') docs)"
    DRIFT=1
    continue
  fi
  disk=$(find "$dir" -maxdepth 1 -name '*.md' ! -name 'index.md' -exec basename {} \; | sort -u)
  indexed=$(grep -o '`[^`/]*\.md`' "$idx" 2>/dev/null | sed 's/`//g' | grep -v '^index\.md$' | sort -u)
  unindexed=$(comm -23 <(echo "$disk") <(echo "$indexed") | grep -c . || true)
  phantom=$(comm -13 <(echo "$disk") <(echo "$indexed") | grep -c . || true)
  if [ "$unindexed" -gt 0 ] || [ "$phantom" -gt 0 ]; then
    u_list=$(comm -23 <(echo "$disk") <(echo "$indexed") | head -3 | tr '\n' ' ')
    p_list=$(comm -13 <(echo "$disk") <(echo "$indexed") | head -3 | tr '\n' ' ')
    msg="index drift: ${rel}/ —"
    [ "$unindexed" -gt 0 ] && msg="$msg ${unindexed} unindexed (${u_list% })"
    [ "$phantom" -gt 0 ] && msg="$msg ${phantom} phantom (${p_list% })"
    echo "$msg"
    DRIFT=1
  fi
done

[ "$STRICT" -eq 1 ] && exit "$DRIFT"
exit 0
