#!/usr/bin/env bash
# revisit-lint — REVISIT-anchor <-> ledger sync + touched-anchor reminders.
#
# A REVISIT anchor is a typed change-intent marker left in a comment where a
# cross-layer surface will need to change again later:
#
#     REVISIT(RV-NNN <class>): <intent>
#
#   classes:  until:<event>     — interim; lifts when <event> happens
#             retire-at:<event> — throwaway; delete at <event>
#             twin:<counterpart>— a surface that must change in lockstep with a
#                                 counterpart in another layer (e.g. a schema and
#                                 the code that (de)serializes it)
#             claim:<fact-id>   — one fact restated across layers; keep in sync
#
# The ledger .agent-docs/reference/revisit-ledger.md is the single source of
# truth (a `## Open` table + a `## Retired` table). Creating an anchor requires
# a matching Open row; resolving one removes the markers and moves the row to
# Retired. This lint keeps the two in sync.
#
# FAILS (exit 1) on:
#   - orphan markers      : an RV-id in code with NO ledger row
#   - dangling open rows  : an Open row whose anchors were all deleted without
#                           retiring the row (move it to §Retired instead)
# INFO (never fails):
#   - staged files that carry anchors -> "you are touching anchored code,
#     consult the row's site list before landing this change"
#
# Docs under .agent-docs/ and .claude/ are sweep-only sites by convention and
# are EXCLUDED from marker scanning (the ledger + design docs mention RV-ids
# natively, which would self-trip the orphan check).
#
# PORTABILITY: bash 3.2+, git, grep, sed, awk, sort. No jq, no GNU-only flags.
#
# THIS MODULE IS OPT-IN and NOT wired by default. To enable it, add this near
# the end of .githooks/pre-commit (before the final `exit "$rc"`):
#     if [ -x scripts/revisit-lint.sh ]; then
#       bash scripts/revisit-lint.sh || rc=1
#     fi
# (adjust the path to wherever you installed this script).

set -u

# ── resolve this script's repo-relative path BEFORE cd (to self-exclude it) ─
self_src="${BASH_SOURCE:-$0}"
self_dir="$(cd -- "$(dirname -- "$self_src")" 2>/dev/null && pwd || true)"
self_abs=""
[ -n "$self_dir" ] && self_abs="$self_dir/$(basename -- "$self_src")"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "revisit-lint: not inside a git repository -> skipped" >&2
  exit 0
fi
cd "$repo_root" || { echo "revisit-lint: cannot cd to repo root -> skipped" >&2; exit 0; }

self_rel=""
case "$self_abs" in
  "$repo_root"/*) self_rel="${self_abs#"$repo_root"/}" ;;
esac

ledger=".agent-docs/reference/revisit-ledger.md"

# ── collect markers (tracked files, minus docs + self) ─────────────────────
# Build the git-grep pathspec (self-exclude only when we resolved a repo-local path).
set -- 'REVISIT(RV-[0-9]' -- . ':(exclude).agent-docs' ':(exclude).claude'
[ -n "$self_rel" ] && set -- "$@" ":(exclude)$self_rel"
all_hits="$(git grep -n "$@" 2>/dev/null || true)"

marker_ids="$(printf '%s\n' "$all_hits" | grep -o 'RV-[0-9]\{3\}' | sort -u || true)"

# ── the ledger (may not exist until the first anchor is created) ────────────
if [ ! -f "$ledger" ]; then
  if [ -z "$marker_ids" ]; then
    # no ledger, no anchors -> module is inert; nothing to check.
    exit 0
  fi
  {
    echo "revisit-lint: x anchors exist in code but the ledger is missing:"
    echo "    $ledger"
    echo "    create it from modules/revisit-ledger/revisit-ledger.template.md and add a row per RV-id."
  } >&2
  exit 1
fi

ledger_ids="$(grep -oE '^\| *RV-[0-9]{3}' "$ledger" | grep -o 'RV-[0-9]\{3\}' | sort -u || true)"
# Open rows only (between '## Open' and '## Retired')
open_ids="$(awk '/^## Open/,/^## Retired/' "$ledger" | grep -oE '^\| *RV-[0-9]{3}' | grep -o 'RV-[0-9]\{3\}' | sort -u || true)"

fail=0

# ── orphan markers (id in code, no ledger row) ─────────────────────────────
while IFS= read -r id; do
  [ -z "$id" ] && continue
  if ! printf '%s\n' "$ledger_ids" | grep -qx "$id"; then
    echo "revisit-lint: x orphan marker $id — found in code, no ledger row:" >&2
    printf '%s\n' "$all_hits" | grep "$id" | sed 's/^/    /' >&2
    fail=1
  fi
done <<EOF
$marker_ids
EOF

# ── dangling open rows (open row, no marker anywhere) ──────────────────────
while IFS= read -r id; do
  [ -z "$id" ] && continue
  if ! printf '%s\n' "$marker_ids" | grep -qx "$id"; then
    echo "revisit-lint: x dangling open row $id — no marker found in the tree" >&2
    echo "   (anchors deleted without retiring the row? move it to §Retired with the landing commit.)" >&2
    fail=1
  fi
done <<EOF
$open_ids
EOF

# ── staged-anchor tripwire (INFO, never fails) ─────────────────────────────
staged="$(git diff --cached --name-only 2>/dev/null || true)"
if [ -n "$staged" ]; then
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    [ -f "$f" ] || continue
    case "$f" in .agent-docs/* | .claude/* | "$self_rel") continue ;; esac
    ids="$(grep -o 'REVISIT(RV-[0-9]\{3\}' "$f" 2>/dev/null | grep -o 'RV-[0-9]\{3\}' | sort -u || true)"
    if [ -n "$ids" ]; then
      one_line="$(printf '%s' "$ids" | tr '\n' ' ' | sed 's/ *$//')"
      echo "revisit-lint: i staged file carries REVISIT anchors: $f [$one_line]" >&2
      while IFS= read -r id; do
        [ -z "$id" ] && continue
        grep -E "^\| *$id " "$ledger" | sed 's/^/      /' >&2 || true
      done <<EOF
$ids
EOF
      echo "      -> consult the row's site list before landing this change ($ledger)" >&2
    fi
  done <<EOF
$staged
EOF
fi

if [ "$fail" -eq 0 ]; then
  echo "revisit-lint: OK markers and ledger in sync"
fi
exit "$fail"
