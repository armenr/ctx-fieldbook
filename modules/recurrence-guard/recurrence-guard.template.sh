#!/usr/bin/env bash
# recurrence-guard (TEMPLATE) — a commit-blocking grep-guard that locks a closed
# bug class shut.  recurrence-guard template-version: 1.0.0
#
# ── THE RECIPE ──────────────────────────────────────────────────────────────
# When an ADR (decisions/NNNN-...) closes a bug class — "we will never again
# write X" — a prose rule relies on everyone REMEMBERING not to write X, which is
# the failure mode enforcement exists to remove. This template turns that decided
# rule into a DETERMINISTIC gate: it FAILS the commit (exit 1) if the banned idiom
# reappears at a guarded source site, so the rule physically cannot lapse.
# One guard = one closed bug class = one ADR.
#
# ── COPY, DON'T EDIT IN PLACE ───────────────────────────────────────────────
# For each bug class you lock, COPY this file to
#     scripts/<bug-class>-guard.sh
# fill the CONFIG block, and register it in .githooks/pre-commit (see README).
# This template ships INERT: with an empty BANNED set it is a no-op (exit 0), so a
# copy is safe to commit before you have finished configuring it.
#
# ── USAGE ───────────────────────────────────────────────────────────────────
#     scripts/<bug-class>-guard.sh [ROOT]
# ROOT defaults to the repository root. Pass ROOT to point the guard at a
# throwaway FIXTURE tree for self-testing (README "Verify"): an empty fixture
# exercises the positive control; a fixture that plants the banned idiom (plus the
# sentinel token) exercises the detector.
#
# ── PORTABILITY ─────────────────────────────────────────────────────────────
# bash 3.2+, POSIX find / grep / sed. No jq, no GNU-only flags. python3 is needed
# ONLY if you opt into in-file test-block stripping (STRIP_TEST_BLOCKS=1); without
# it the guard uses the portable path-exclusion floor.
#
# OPT-IN: not wired by default. Register it in .githooks/pre-commit (see README).

set -u

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG — fill this in when you adopt the guard. Empty BANNED == inert no-op.
# ══════════════════════════════════════════════════════════════════════════════

# 1 · BANNED — the idiom(s) whose reappearance you forbid, ONE PER LINE. Matched
#     as FIXED strings (grep -F) unless MATCH_MODE=regex. Ships EMPTY (inert). Keep
#     the examples in this COMMENT so the guard stays inert until you fill BANNED:
#         parseConfig(path).unwrapOrDefault()
#         parseConfig(path).orNull()
BANNED='
'

# 2 · MATCH_MODE — how BANNED lines are read: "fixed" (grep -F, safest — a literal
#     idiom) or "regex" (grep -E — when the idiom varies). Default fixed.
MATCH_MODE="fixed"

# 3 · SENTINEL — the POSITIVE CONTROL. A token that MUST still exist in the scanned
#     surface for the BANNED idiom to be spellable AT ALL — usually the symbol / API
#     the idiom is built from (e.g. "parseConfig"). If a rename retires it, every
#     BANNED pattern would match nothing FOREVER and the guard would silently
#     protect nothing. So the guard asserts the sentinel first and FAILS LOUD when
#     it is gone, forcing you to update the patterns in the SAME commit as the
#     rename. Leave empty ONLY while BANNED is empty; set it when you adopt.
SENTINEL=''

# 4 · FIX_HINT — the one line printed when the guard fires. Name the RIGHT
#     construct, not just "don't do that" (a good failure message teaches the fix).
#     EXAMPLE: "return the config-load error instead of swallowing it to a default (ADR-NNNN)".
FIX_HINT='<name the correct construct here — see the ADR this guard enforces>'

# 5 · GUARD_ID — short label for messages, e.g. the ADR / OQ id this guard locks
#     (ADR-NNNN / OQ-NNN). Cosmetic; helps a blocked commit find the rationale.
GUARD_ID="recurrence-guard"

# 6 · STRIP_TEST_BLOCKS — opt-in in-file test-block stripping. Set to 1 ONLY if the
#     banned idiom is legitimately allowed inside test code that lives in the SAME
#     file as production code (an inline test module). Needs python3 + a per-stack
#     TEST_BLOCK_OPEN_RE. The PORTABLE FLOOR is 0: exclude whole test DIRECTORIES in
#     enumerate_scope() instead (README caveat). Default 0.
STRIP_TEST_BLOCKS=0
# The line pattern that OPENS an in-file test block (used only when =1). Per-stack;
# there is NO portable default — you MUST set this if you enable stripping.
TEST_BLOCK_OPEN_RE=''

# 7 · enumerate_scope — which files the guard scans, emitted NUL-delimited. Edit the
#     find-expression for YOUR tree: name your source extension(s) and EXCLUDE
#     generated / vendored / test paths. Whole-directory PATH-EXCLUSION is the
#     PORTABLE FLOOR for keeping test code out of scope. The example scans '*.EXT'
#     (a deliberate placeholder that matches nothing) — replace it, or the guard
#     scans an empty surface and the positive control will tell you so.
enumerate_scope() {
  find "$ROOT" -type f -name '*.EXT' \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/target/*' \
    ! -path '*/dist/*' \
    ! -path '*/build/*' \
    ! -path '*/vendor/*' \
    ! -path '*/tests/*' \
    ! -path '*/test/*' \
    -print0 2>/dev/null
}

# 8 · is_exempt — the EXEMPTION HOOK (a "drain-down allowlist"). Return 0 to EXEMPT
#     a file. Two honest uses: (a) a documented, genuinely-correct production site
#     where the idiom is intended; (b) DRAIN-DOWN — when you first adopt this guard
#     on a tree that ALREADY has violations you cannot fix in one commit, list them
#     here and delete each line as you fix it, so the guard blocks NEW violations
#     from day one. Key exemptions on file CONTENT or a stable path SUFFIX, never a
#     line number (drift-proof). Ships EMPTY.
is_exempt() {
  # case "$1" in
  #   */path/to/documented-exception.ext) return 0 ;;
  # esac
  return 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ENGINE — you should not need to edit below here.
# ══════════════════════════════════════════════════════════════════════════════

# ── resolve this script's own path BEFORE anything, to self-exclude it (the
#    template carries the example idiom in a comment) ─────────────────────────
self_src="${BASH_SOURCE:-$0}"
self_dir="$(cd -- "$(dirname -- "$self_src")" 2>/dev/null && pwd || true)"
self_abs=""
[ -n "$self_dir" ] && self_abs="$self_dir/$(basename -- "$self_src")"

# ── ROOT: explicit arg -> fixture / explicit mode (no git needed, e.g. self-test).
#    No arg -> resolve the repo root via git; DEGRADE TO A NO-OP outside a git repo
#    (a guard must never error just because it ran in a non-repo context) ───────
if [ "$#" -ge 1 ]; then
  ROOT="$1"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -z "$ROOT" ]; then
    echo "$GUARD_ID: not inside a git repository -> skipped" >&2
    exit 0
  fi
fi

# ── INERT until adopted: an empty BANNED set means the guard is unconfigured ──
banned_trim="$(printf '%s' "$BANNED" | tr -d '[:space:]')"
if [ -z "$banned_trim" ]; then
  echo "$GUARD_ID: no banned patterns configured -> inert (exit 0)"
  exit 0
fi

# ── grep flavour ────────────────────────────────────────────────────────────
case "$MATCH_MODE" in
  regex) MATCH_FLAG="-E" ;;
  *)     MATCH_FLAG="-F" ;;
esac

# ── POSITIVE CONTROL: fail LOUD if the sentinel token is gone from the scanned
#    surface (a rename would leave the guard matching nothing forever) ─────────
if [ -n "$SENTINEL" ]; then
  sentinel_found=0
  while IFS= read -r -d '' f; do
    [ -f "$f" ] || continue
    if grep -q -F -- "$SENTINEL" "$f" 2>/dev/null; then
      sentinel_found=1
      break
    fi
  done < <(enumerate_scope)
  if [ "$sentinel_found" -eq 0 ]; then
    {
      echo "$GUARD_ID: POSITIVE CONTROL FAILED - sentinel '$SENTINEL' not found in the"
      echo "  scanned surface (check SENTINEL and enumerate_scope)."
      echo "  The banned idiom is built from a token that no longer exists (a rename?),"
      echo "  so this guard now matches NOTHING and silently protects nothing."
      echo "  Update BANNED + SENTINEL to the new spelling in the SAME commit as the rename."
    } >&2
    exit 1
  fi
fi

# ── ANALYSIS-ENGINE FAIL-OPEN: in-file test-block stripping needs python3. If it
#    was requested but the engine is absent, do NOT block every commit and do NOT
#    silently scan test code — warn LOUD and skip (fail-open) so the missing
#    dependency is visible, never a false block nor a false pass ───────────────
strip_enabled=0
if [ "$STRIP_TEST_BLOCKS" = "1" ]; then
  if command -v python3 >/dev/null 2>&1 && [ -n "$TEST_BLOCK_OPEN_RE" ]; then
    strip_enabled=1
  else
    {
      echo "$GUARD_ID: WARNING in-file test-block stripping requested but its engine is"
      echo "  unavailable (need python3 + TEST_BLOCK_OPEN_RE) -> guard SKIPPED (fail-open)."
      echo "  Install python3 / set TEST_BLOCK_OPEN_RE, or drop STRIP_TEST_BLOCKS and use"
      echo "  path-exclusion in enumerate_scope() to keep the guard active."
    } >&2
    echo "$GUARD_ID: SKIPPED (test-block-stripping engine unavailable)"
    exit 0
  fi
fi

# ── optional in-file test-block stripper (position-preserving blank) ─────────
strip_test_blocks() {
  # $1 = file path. Prints the file with in-file test blocks blanked out, so a
  # banned idiom that is legal in test code does not trip the guard. Brace-depth
  # tracker from the first '{' after a TEST_BLOCK_OPEN_RE line to its matching
  # close — the same mechanism a per-stack guard uses for its test blocks.
  python3 - "$1" "$TEST_BLOCK_OPEN_RE" <<'PY'
import sys, re
path = sys.argv[1]
open_re = re.compile(sys.argv[2])
with open(path, encoding='utf-8', errors='replace') as fh:
    lines = fh.readlines()
out = []
i = 0
n = len(lines)
while i < n:
    if open_re.search(lines[i]):
        j = i
        depth = 0
        started = False
        while j < n:
            depth += lines[j].count('{') - lines[j].count('}')
            if '{' in lines[j]:
                started = True
            out.append('\n')  # blank the line but keep the line count
            j += 1
            if started and depth <= 0:
                break
        i = j
        continue
    out.append(lines[i])
    i += 1
sys.stdout.write(''.join(out))
PY
}

# ── scan ────────────────────────────────────────────────────────────────────
violations=0
while IFS= read -r -d '' file; do
  [ -f "$file" ] || continue
  if [ -n "$self_abs" ]; then
    case "$file" in
      "$self_abs") continue ;;
    esac
  fi
  is_exempt "$file" && continue

  if [ "$strip_enabled" = "1" ]; then
    if ! text="$(strip_test_blocks "$file")"; then
      echo "$GUARD_ID: ERROR test-block stripper crashed on $file" >&2
      exit 1
    fi
  else
    text="$(cat "$file")"
  fi

  while IFS= read -r pat; do
    [ -z "$pat" ] && continue
    if printf '%s\n' "$text" | grep -q $MATCH_FLAG -- "$pat" 2>/dev/null; then
      echo "$GUARD_ID: BANNED idiom '$pat' at $file"
      violations=$((violations + 1))
    fi
  done <<EOF
$BANNED
EOF
done < <(enumerate_scope)

if [ "$violations" -gt 0 ]; then
  {
    echo "$GUARD_ID: FAILED ($violations violation(s))."
    echo "  $FIX_HINT"
  } >&2
  exit 1
fi

echo "$GUARD_ID: OK (no banned idioms at guarded sites)"
exit 0
