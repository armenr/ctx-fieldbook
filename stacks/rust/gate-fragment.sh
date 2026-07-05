# ─── Rust stack gate fragment ─────────────────────────────────────────────────────────
# Spliced into pretooluse-safety-gates.base.sh at the marked STACK-FRAGMENT INSERTION POINT
# (BEFORE the universal rules). NOT a standalone script — it inherits CMD, CSEP, ask(),
# block(), and SAFE_PATHS_EXTRA from the base. Same discipline as the base: every rule is
# anchored to command position via ${CSEP}, and uses POSIX character classes only
# ([[:space:]], [^[:alnum:]_]) so it behaves identically under GNU and BSD grep.
#
# Gated surface: the three cargo operations that reach OUTSIDE the workspace or are
# irreversible — publish (registry, permanent), install (global toolchain mutation),
# update (lockfile churn). Plain build/check/clippy/test/fmt are safe and stay ungated.
# A `(\+[^[:space:]]+ +)?` optional token absorbs a toolchain override (e.g. `cargo +nightly …`).

# Extend the recursive-rm safe-path set with cargo's build / registry-cache / bench-output
# dirs, so `rm -rf target/` (regenerable build output) does not prompt. Preserves any value
# an earlier fragment set.
SAFE_PATHS_EXTRA="${SAFE_PATHS_EXTRA:+${SAFE_PATHS_EXTRA}|}target/|\.cargo/registry|criterion"

# R1. cargo publish (ask) — IRREVERSIBLE: a released version can never be re-uploaded to the
#     registry. Confirm intent before a permanent public release.
echo "$CMD" | grep -qE "${CSEP}cargo +(\+[^[:space:]]+ +)?publish([^[:alnum:]_]|$)" &&
  ask "Safety gate (Rust): 'cargo publish' is IRREVERSIBLE — a released version can never be re-uploaded to ${PACKAGE_REGISTRY:-the package registry}. Confirm the package + version + that a public release is intended."

# R2. cargo install (ask) — mutates the global ~/.cargo/bin toolchain and builds arbitrary
#     upstream packages outside the workspace lock.
echo "$CMD" | grep -qE "${CSEP}cargo +(\+[^[:space:]]+ +)?install([^[:alnum:]_]|$)" &&
  ask "Safety gate (Rust): 'cargo install' mutates the global ~/.cargo/bin toolchain and builds arbitrary upstream packages outside the workspace lock. Confirm the package + that a global install (vs a dev-dependency) is intended."

# R3. cargo update (ask) — rewrites Cargo.lock, pulling new transitive versions (possible breakage).
echo "$CMD" | grep -qE "${CSEP}cargo +(\+[^[:space:]]+ +)?update([^[:alnum:]_]|$)" &&
  ask "Safety gate (Rust): 'cargo update' bumps dependency versions and rewrites Cargo.lock (new transitive versions, possible breakage). Confirm — then re-run the gates (build / clippy / test) after, and currency-check any major bumps."
# ──────────────────────────────────────────────────────────────────────────────────────
