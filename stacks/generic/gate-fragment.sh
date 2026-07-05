# ─── Generic stack gate fragment (concierge-filled) ───────────────────────────────────
# Spliced into pretooluse-safety-gates.base.sh at the marked STACK-FRAGMENT INSERTION POINT
# (BEFORE the universal rules) when no first-class stack pack matches the project. NOT a
# standalone script — it inherits CMD, CSEP, ask(), block(), and SAFE_PATHS_EXTRA from the
# base. By default it adds NOTHING (the universal base is already correct on its own); the
# concierge fills in the project's stack-specific foot-guns from the interview.
#
# Discipline to copy from the base when you add a rule:
#   * Anchor the command to command position with ${CSEP} (so a match inside a HEREDOC body
#     or a commit message doesn't fire).
#   * POSIX character classes ONLY — [[:space:]] not \s, ([^[:alnum:]_]|$) for a trailing
#     word boundary — so it behaves the same under GNU and BSD grep.
#   * `ask "..."` for reversible-but-consequential; `block "..."` for an unambiguous foot-gun.
#
# ── EXAMPLE (commented — fill from the interview, then uncomment) ──────────────────────
# Ask before your package manager's publish command (releasing to a registry is usually
# irreversible) and its global-install command (mutates a shared, outside-the-project
# toolchain). Replace <pkg-mgr> and <publish-subcommand> with the real tokens the interview
# captured for this project (e.g. the tool named by {{PACKAGE_REGISTRY}}'s client):
#
#   echo "$CMD" | grep -qE "${CSEP}<pkg-mgr> +<publish-subcommand>([^[:alnum:]_]|$)" &&
#     ask "Safety gate: publishing to ${PACKAGE_REGISTRY:-the package registry} is typically irreversible. Confirm the package + version + that a public release is intended."
#
#   echo "$CMD" | grep -qE "${CSEP}<pkg-mgr> +<global-install-subcommand>([^[:alnum:]_]|$)" &&
#     ask "Safety gate: a global install mutates a shared toolchain outside this project. Confirm it is intended (vs a project-local dev dependency)."
#
# To make a recursive rm of your build-output dir stop prompting, extend the safe-path set
# instead of adding a rule (preserve any earlier value):
#   SAFE_PATHS_EXTRA="${SAFE_PATHS_EXTRA:+${SAFE_PATHS_EXTRA}|}<your-build-output-dir>/"
# ──────────────────────────────────────────────────────────────────────────────────────
