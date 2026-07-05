# ─── Node / TypeScript stack gate fragment ────────────────────────────────────────────
# Spliced into pretooluse-safety-gates.base.sh at the marked STACK-FRAGMENT INSERTION POINT
# (BEFORE the universal rules). NOT a standalone script — it inherits CMD, CSEP, ask(),
# block(), and SAFE_PATHS_EXTRA from the base. Same discipline as the base: every rule is
# anchored to command position via ${CSEP}, and uses POSIX character classes only
# ([[:space:]], [^[:alnum:]_]) so it behaves identically under GNU and BSD grep. Two greps
# are chained with && when two tokens must co-occur in any order on the same line.
#
# Gated surface: the package-manager operations that reach OUTSIDE the project or drift the
# committed dependency graph — publish (registry, public), global install (shared toolchain),
# a node_modules wipe, a forced lockfile re-resolve. Plain local install / run / build / test
# are safe and stay ungated. Covers npm / pnpm / yarn / bun.

# Extend the recursive-rm safe-path set with regenerable framework build/cache output, so
# `rm -rf .next` / `.turbo` etc. do not prompt. node_modules is deliberately NOT here — its
# wipe stays gated (N3). Preserves any value an earlier fragment set.
SAFE_PATHS_EXTRA="${SAFE_PATHS_EXTRA:+${SAFE_PATHS_EXTRA}|}\.next|\.nuxt|\.svelte-kit|\.turbo|\.parcel-cache|\.astro|\.vite"

# N1. Publish to a package registry (ask) — a released version is public and hard to fully
#     retract (unpublish is time-boxed / blocked for established packages). Manager at command
#     position co-occurring with a standalone `publish` token.
echo "$CMD" | grep -qE "${CSEP}(npm|pnpm|yarn|bun)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])publish([[:space:]]|$)" &&
  ask "Safety gate (node-ts): publishing to ${PACKAGE_REGISTRY:-the package registry} is public and hard to fully retract. Confirm the package, version, and registry — and that a real release is intended — before publishing."

# N2. Global / system-wide install (ask) — a manager install verb (install|i|add) co-occurring
#     with a global marker (-g / --global / --location=global / yarn's `global` subcommand).
#     A plain local install (no global marker) is NOT gated.
echo "$CMD" | grep -qE "${CSEP}(npm|pnpm|yarn|bun)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(install|i|add)([[:space:]]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(-g|--global|--location=global)([[:space:]]|=|$)|(^|[[:space:]])global([[:space:]]|$)" &&
  ask "Safety gate (node-ts): a global install mutates a shared toolchain outside the project. Prefer a project-local devDependency; confirm with the operator if a global install is really intended."

# N3. Recursive rm of node_modules (ask) — fires before the base generic-rm rule to give a
#     tailored message. Any recursive rm touching a node_modules dir forces a full reinstall
#     and can break a running dev server.
echo "$CMD" | grep -qE "${CSEP}rm +(-[A-Za-z]*[rR][A-Za-z]*|--recursive)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])node_modules([^[:alnum:]_]|$)" &&
  ask "Safety gate (node-ts): recursive rm of node_modules forces a full reinstall and can break a running dev server. Confirm with the operator (usually a clean 'npm ci' / 'pnpm install --frozen-lockfile' is what you want)."

# N4a. Forced dependency re-resolve (ask) — an install/update with --force / -f can re-resolve
#      and overwrite the committed lockfile, drifting the whole dependency graph.
echo "$CMD" | grep -qE "${CSEP}(npm|pnpm|yarn|bun)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(install|i|add|update|up|upgrade)([[:space:]]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(--force|-f)([[:space:]]|$)" &&
  ask "Safety gate (node-ts): a forced install/update can re-resolve and overwrite the lockfile. Confirm — an unintended lockfile rewrite drifts every dependency version away from the committed lock."

# N4b. Deleting a lockfile (ask) — discards the exact resolved graph; the next install
#      re-resolves to possibly-different versions. A non-recursive rm the base rule won't catch.
echo "$CMD" | grep -qE "${CSEP}rm +" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])(package-lock\.json|npm-shrinkwrap\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|bun\.lock)([^[:alnum:]_]|$)" &&
  ask "Safety gate (node-ts): deleting a lockfile discards the exact resolved dependency graph (the next install re-resolves to possibly-different versions). Confirm with the operator."
# ──────────────────────────────────────────────────────────────────────────────────────
