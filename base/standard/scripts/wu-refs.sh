#!/usr/bin/env bash
# wu-refs.sh — inbound-reference sweep for a work-unit / slice / stage.
#
# Gathers EVERY reference to a work-unit id (and, optionally, a stage token) across
# the context system + code, so that at cycle-start nothing depending on / awaiting /
# referencing it is missed — a forgotten DEFER, a gating OQ, an RV that lifts here, an
# ADR note, a review finding, a dispatch charter parked against it, a code comment.
#
# Companion to the READ-ONLY scope recon: recon looks OUTWARD (what the WU touches);
# this looks INWARD (what references/awaits the WU). The traceability ledger is the
# INTENDED obligation store; this is defense-in-depth against obligations that leaked
# into ADR notes / open-questions / reviews / code comments instead.
#
# It only GATHERS — you TRIAGE each hit:
#   [satisfied] · [do-this-cycle] · [unexpected → investigate] · [stale → remove]
#
# Usage:
#   scripts/wu-refs.sh WU-05
#   scripts/wu-refs.sh WU-05 'stage-2'      # also sweep a stage token
#   scripts/wu-refs.sh U-A4c
#
# Tier-portable: the location groups are a SUPERSET across the minimal/standard/full
# profiles; a group whose dir/file is absent in this repo is skipped silently. Uses
# `git grep --untracked` so NEW/uncommitted files (a just-written ledger, review, ADR)
# are swept; git grep still respects .gitignore.
# NOTE: do not name a bash array `GROUPS` — it is a reserved builtin (supplementary GIDs).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ -z "${1:-}" ]; then
  echo "usage: scripts/wu-refs.sh <WU/unit id> [stage-token]" >&2
  echo "  e.g. scripts/wu-refs.sh WU-05   |   scripts/wu-refs.sh WU-05 'stage-2'" >&2
  exit 2
fi

TOKEN=""
ANY=0

# keep only pathspecs that actually exist (skip magic ':!...' excludes untouched)
_present () {
  local p keep=()
  for p in "$@"; do
    case "$p" in
      :!*|.) keep+=("$p") ;;              # exclude-magic + repo-root always kept
      *) [ -e "$p" ] && keep+=("$p") ;;   # plain path: only if it exists
    esac
  done
  printf '%s\n' "${keep[@]}"
}

group () {  # $1 = label ; $2.. = pathspecs
  local label="$1"; shift
  local -a specs=(); local line out
  while IFS= read -r line; do [ -n "$line" ] && specs+=("$line"); done < <(_present "$@")
  # if only the exclude-magic/root remain (no real doc path), and this is a doc group, skip
  [ ${#specs[@]} -eq 0 ] && return 0
  out="$(git grep -n -i --untracked -e "$TOKEN" -- "${specs[@]}" 2>/dev/null)" || out=""
  if [ -n "$out" ]; then
    printf '── %s ──\n%s\n\n' "$label" "$out"
    ANY=1
  fi
}

sweep () {
  TOKEN="$1"
  ANY=0
  printf '════════ references to: %s ════════\n' "$TOKEN"
  group "traceability (the obligation ledger)"       .agent-docs/traceability
  group "open-questions (gating OQs)"                .agent-docs/now/open-questions.md
  group "revisit-ledger (RV anchors that lift here)" .agent-docs/reference/revisit-ledger.md
  group "decisions / ADRs (parked notes)"            .agent-docs/decisions
  group "reviews (findings deferred here)"           .agent-docs/reviews
  group "work-plan / status"                         .agent-docs/now/work-plan.md .agent-docs/now/status.md
  group "log"                                        .agent-docs/log.md
  group "dispatch-charters"                          .agent-docs/dispatch-charters
  group "incidents"                                  .agent-docs/incidents
  group "code + specs (outside .agent-docs)"         . ':!.agent-docs' ':!scripts/wu-refs.sh'
  [ "$ANY" = 0 ] && echo "(no references found)"
  echo
}

echo "# inbound-reference sweep — TRIAGE each hit:"
echo "#   [satisfied] · [do-this-cycle] · [unexpected → investigate] · [stale → remove]"
echo
sweep "$1"
[ -n "${2:-}" ] && sweep "$2"
exit 0
