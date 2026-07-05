# ─── Go stack gate fragment ───────────────────────────────────────────────────────────
# Spliced into pretooluse-safety-gates.base.sh at the marked STACK-FRAGMENT INSERTION POINT
# (BEFORE the universal rules). NOT a standalone script — it inherits CMD, CSEP, ask(),
# block(), and SAFE_PATHS_EXTRA from the base. Same discipline as the base: every rule is
# anchored to command position via ${CSEP}, and uses POSIX character classes only
# ([[:space:]], [^[:alnum:]_]) so it behaves identically under GNU and BSD grep. `bash -n`
# validates it in isolation (syntax only); the undefined helpers resolve at splice time.
#
# Gated surface: the Go operations that reach OUTSIDE the repo, are irreversible, or rewrite
# a dependency manifest non-interactively. Plain build/test/vet/list are safe and stay
# ungated (they are on the allowlist). Go has NO `publish` verb: a module is PUBLISHED by
# pushing a semver VCS tag (git push <remote> vX.Y.Z), which the module proxy + checksum DB
# then cache ~immutably — so that tag-push is the "publish" gate (G4).
#
# No SAFE_PATHS_EXTRA additions: Go has no in-repo throwaway build dir like a target/ —
# binaries land in cwd or $GOBIN and caches live under $GOCACHE / $GOPATH outside the tree.
# `vendor/` is regenerable via `go mod vendor` but is often committed + load-bearing, so it
# is deliberately NOT added to the recursive-rm safe set.

# G1. Global binary install (ask). `go install <pkg>` / `go install <pkg>@<version>` writes an
#     executable into $GOBIN (default $GOPATH/bin) — a global side effect outside the repo; the
#     @version form also builds in module-aware mode IGNORING the local go.mod. Plain build/test
#     are allow-listed; `go install` is not. The bare form still installs the current module's
#     binaries, so match `go install` at command position regardless of arguments.
echo "$CMD" | grep -qE "${CSEP}go +install([^[:alnum:]_]|$)" &&
  ask "Safety gate (Go): 'go install' writes a binary into \$GOBIN/\$GOPATH/bin (global, outside the repo); the pkg@version form ignores the local go.mod. Confirm the target + that a global install is intended."

# G2. Shared-cache wipe (ask). `go clean -modcache` deletes the ENTIRE shared module download cache
#     ($GOPATH/pkg/mod); `-cache` deletes the whole build cache; `-fuzzcache` the fuzz corpus cache.
#     All are machine-wide (not repo-scoped) and slow to rebuild. Chain: `go clean` co-occurring with
#     a cache-wipe flag, in any order.
if echo "$CMD" | grep -qE "${CSEP}go +clean([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])--?(modcache|cache|fuzzcache)([^[:alnum:]_]|$)"; then
  ask "Safety gate (Go): 'go clean -modcache/-cache' wipes the shared module/build cache (machine-wide, not just this repo, slow to rebuild). Confirm with the operator."
fi

# G3. Scripted go.mod requirement rewrite (ask). `go mod edit` with a mutating flag rewrites go.mod
#     NON-interactively (scriptable) — it can add/drop/replace requirements or bump the go/toolchain
#     line WITHOUT the reconciliation that `go mod tidy` / `go get` perform. Bare `go mod edit` and
#     `go mod edit -fmt` / `-print` only reformat or print and are exempt. Chain: `go mod edit` + a
#     rewrite flag, in any order.
if echo "$CMD" | grep -qE "${CSEP}go +mod +edit([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])-(require|droprequire|replace|dropreplace|exclude|dropexclude|retract|dropretract|go|toolchain)([=[:space:]]|$)"; then
  ask "Safety gate (Go): 'go mod edit' with a rewrite flag (-require/-droprequire/-replace/-exclude/-go/-toolchain) edits go.mod non-interactively, bypassing tidy's reconciliation. Prefer 'go get' / 'go mod tidy'; confirm with the operator."
fi

# G4. Module publish = semver VCS tag push (ask). Go has no publish command: pushing a semantic-version
#     tag (vX.Y.Z) makes that version fetchable, and the module proxy + checksum DB cache it ~immutably
#     — you cannot re-point a published version at a different commit. Chain: `git push` co-occurring
#     with an explicit tag push (--tags) OR a vN.N.N ref on the same command.
if echo "$CMD" | grep -qE "${CSEP}git +push([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])--tags([^[:alnum:]_]|$)|(^|[^[:alnum:]_])v[0-9]+\.[0-9]+\.[0-9]+([^[:alnum:]_]|$)"; then
  ask "Safety gate (Go): pushing a semver tag (vX.Y.Z) PUBLISHES that module version to ${PACKAGE_REGISTRY:-the module proxy + checksum DB}, which caches it ~immutably (no take-backs). Confirm the version + remote with the operator."
fi
# ──────────────────────────────────────────────────────────────────────────────────────
