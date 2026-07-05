#!/usr/bin/env bash
# pretooluse-safety-gates.base.sh — UNIVERSAL PreToolUse Bash safety gate (base layer).
# provenance: kit-template · created: 2026-07-03
#
# Reads stdin JSON per the Claude Code hook spec:
#   { "tool_name": "Bash", "tool_input": { "command": "..." } }
# Emits a permissionDecision (ask|deny) on match, or a cwd-safety additionalContext
# on mutative git/fs ops. No match → allow (silent, no output).
#
# This is the STACK-AGNOSTIC base — universal foot-guns only. At install the concierge
# concatenates a per-stack gate fragment (e.g. package-publish, dependency re-lock,
# datastore-wipe) at the marked insertion point to produce the live
# `pretooluse-safety-gates.sh`. The base is also correct STANDALONE.
#
#   `ask`  = reversible-but-consequential  (rm -r, git reset --hard, push to protected)
#   `deny` = unambiguous foot-gun          (force-push to protected, checks-bypass flags)
#
# ── Regex discipline (the reusable crown jewel — DO NOT weaken) ───────────────────────
# 1. Anchor EVERY rule to COMMAND POSITION via CSEP: start-of-line (leading-whitespace
#    tolerant), OR after a shell separator ; && || |, OR inside $( ), optionally after
#    inline VAR=val env assignments. grep segments input on newlines, so per-line command-
#    position anchoring rules out HEREDOC bodies and commit-message text.
# 2. PORTABILITY: POSIX character classes ONLY. Use [[:space:]] not \s, [^[:space:]] not
#    \S, and an explicit ([^[:alnum:]_]|$) tail for a trailing word-boundary. \b \s \w are
#    GNU-grep extensions that silently FAIL on BSD/macOS grep; POSIX word boundaries
#    ([[:<:]] [[:>:]]) are BSD-only. Neither is portable, so boundaries are spelled out.
# 3. Chain greps when two tokens must co-occur in any order.
set -euo pipefail

# jq is required to parse the hook payload. If absent, degrade to allow-through rather
# than failing on EVERY Bash call (never brick the session on a missing tool).
command -v jq >/dev/null 2>&1 || exit 0

CMD=$(jq -r '.tool_input.command // ""')

# Extra rm-safe paths a stack fragment may contribute (default: none). Portable default.
SAFE_PATHS_EXTRA="${SAFE_PATHS_EXTRA:-}"

# OUTPUT SCHEMA: the legacy top-level `decision` field supports only approve/block; `ask`
# is silently dropped there. Use hookSpecificOutput.permissionDecision.
ask() {
  jq -nc --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask",  permissionDecisionReason: $r}}'
  exit 0
}
block() {
  jq -nc --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $r}}'
  exit 0
}

# Command-position anchor (+ optional inline env-var assignments). POSIX-portable.
CSEP='(^[[:space:]]*|[;&|][[:space:]]*|\$\([[:space:]]*)([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+ +)*'

# ─── STACK-FRAGMENT INSERTION POINT ───────────────────────────────────────────────────
# The concierge splices the per-stack gate fragment HERE (BEFORE the universal rules) so
# it can add stack rules and/or extend SAFE_PATHS_EXTRA. Leave untouched when the base
# runs standalone.
# ──────────────────────────────────────────────────────────────────────────────────────

# 1. Git push to a protected branch (block on --force same-line; else ask).
#    Word boundaries spelled out: (^|[^[:alnum:]_])X([^[:alnum:]_]|$).
PROTECTED='(main|master|{{DEFAULT_BRANCH}})'
PUSH_LINES=$(echo "$CMD" | grep -E "${CSEP}git +push([^[:alnum:]_]|$)" | grep -E "(^|[^[:alnum:]_])${PROTECTED}([^[:alnum:]_]|$)" || true)
if [[ -n $PUSH_LINES ]]; then
  if echo "$PUSH_LINES" | grep -qE -- '--force([^[:alnum:]_]|$)|(^|[[:space:]])-f([^[:alnum:]_]|$)'; then
    block "Safety gate: git push --force to a protected branch ${PROTECTED} is BLOCKED — force-push overwrites shared history. Use a feature branch + PR."
  fi
  ask "Safety gate: git push to a protected branch ${PROTECTED}. Confirm with the operator before pushing to shared history."
fi

# 2. Checks-bypass attempts (block). The bypass flag must co-occur with a real git write
#    verb on the SAME line, so a --no-verify mentioned inside a commit-message body (a
#    different line) is exempt.
if echo "$CMD" | grep -qE "${CSEP}git +(.*[^[:alnum:]_])?(commit|push|rebase|merge|cherry-pick|am|tag)(.*[[:space:]])(--no-verify|--no-gpg-sign)([^[:alnum:]_]|$)" ||
  echo "$CMD" | grep -qE "${CSEP}git +.*commit\.gpgsign=false"; then
  block "Safety gate: checks-bypass (--no-verify / --no-gpg-sign / commit.gpgsign=false) is BLOCKED. Investigate the failing pre-commit gate; do not route around it."
fi

# 3. git reset --hard (ask) — destroys uncommitted working-tree changes.
echo "$CMD" | grep -qE "${CSEP}git +reset +--hard([^[:alnum:]_]|$)" &&
  ask "Safety gate: 'git reset --hard' destroys uncommitted changes. Confirm cwd + target with the operator."

# 4. Recursive rm outside safe paths (ask). Matches any short-flag cluster containing r/R
#    (-rf, -fr, -Rf, -rfv, -r) or --recursive. Safe = universal temp/cache/build dirs, plus
#    any stack-specific dirs the fragment added via SAFE_PATHS_EXTRA.
SAFE_PATHS="/tmp/|/private/tmp/|\\.cache|/dist/|/build/|/gen/|coverage${SAFE_PATHS_EXTRA:+|${SAFE_PATHS_EXTRA}}"
if echo "$CMD" | grep -qE "${CSEP}rm +(-[A-Za-z]*[rR][A-Za-z]*|--recursive)([^[:alnum:]_]|$)" &&
  ! echo "$CMD" | grep -qE "$SAFE_PATHS"; then
  ask "Safety gate: recursive rm outside safe paths (${SAFE_PATHS}). Confirm the target with the operator."
fi

# 5. CWD-awareness injection on mutative git / filesystem ops (context-inject, no block).
#    The harness preserves cwd between Bash calls; a prior `cd <subdir>` for a read-only op
#    can silently set the wrong context for a later mutative op (esp. in a multi-package
#    workspace: {{WORKSPACE_LAYOUT}}). Emits cwd+branch+repo-root+tree-shape via
#    additionalContext BEFORE allowing. Ask-gated commands above have already exited.
MUTATIVE_PATTERN='git +(add|clean|commit|rm|mv|reset|merge|rebase|cherry-pick|stash|worktree|revert|restore|push)([^[:alnum:]_]|$)|rm +|mv +'
if echo "$CMD" | grep -qE "${CSEP}(${MUTATIVE_PATTERN})"; then
  set +e
  PWD_NOW=$(pwd 2>/dev/null || echo "<pwd-failed>")
  INTENDED_CWD=""
  if echo "$CMD" | grep -qE '^[[:space:]]*cd[[:space:]]+'; then
    INTENDED_CWD=$(echo "$CMD" | sed -nE 's|^[[:space:]]*cd[[:space:]]+([^&|;]+).*|\1|p' | sed 's/[[:space:]]*$//' | head -1)
    if [ -n "$INTENDED_CWD" ]; then
      INTENDED_CWD=$(eval echo "$INTENDED_CWD" 2>/dev/null || echo "$INTENDED_CWD")
      if [ "${INTENDED_CWD#/}" = "$INTENDED_CWD" ]; then
        INTENDED_CWD="$PWD_NOW/$INTENDED_CWD"
      fi
    fi
  fi
  if [ -n "$INTENDED_CWD" ] && [ -d "$INTENDED_CWD" ]; then
    EFFECTIVE_CWD="$INTENDED_CWD"
    CWD_LABEL="cwd=${INTENDED_CWD} (via cd-chain from shell-cwd=${PWD_NOW})"
  else
    EFFECTIVE_CWD="$PWD_NOW"
    CWD_LABEL="cwd=${PWD_NOW}"
  fi
  BRANCH=$(git -C "$EFFECTIVE_CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "<not-a-git-repo>")
  REPO_ROOT=$(git -C "$EFFECTIVE_CWD" rev-parse --show-toplevel 2>/dev/null || echo "<not-a-git-repo>")
  STATUS_COUNT=$(git -C "$EFFECTIVE_CWD" status -s 2>/dev/null | wc -l | tr -d ' ' || echo "?")
  STATUS_TOP=$(git -C "$EFFECTIVE_CWD" status -s 2>/dev/null | head -3 | tr '\n' ';' | sed 's/;$//' || true)
  CONTEXT_MSG="[cwd-safety] ${CWD_LABEL} | branch=${BRANCH} | repo-root=${REPO_ROOT} | changes=${STATUS_COUNT} | top: ${STATUS_TOP}"
  jq -nc --arg ctx "$CONTEXT_MSG" '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $ctx}}'
  set -e
  exit 0
fi

# No match → allow (no output = no-action per hook spec).
exit 0
