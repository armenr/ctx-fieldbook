---
provenance: kit-template
created: 2026-07-03
paths: ["**/*.rs", "**/Cargo.toml", "**/build.rs"]
---

# Rust / Cargo rules

The stack-specific concretion of the universal quality-gate discipline in `standing-rules-core.md`
(§Quality gates). Short on purpose — deep architecture lives in your project's own `reference/`. This
pack is the Rust binding for the generic `{{LINT_CMD}} / {{FMT_CMD}} / {{PANIC_EQUIVALENT}} / {{CODE_INTEL_TOOL}}`
seams: `{{LINT_CMD}}` → `cargo clippy`, `{{FMT_CMD}}` → `cargo fmt`, `{{PANIC_EQUIVALENT}}` → the
panic-family bans below, `{{CODE_INTEL_TOOL}}` → rust-analyzer (see `code-intel.md`).

## Lint & format gates (strict by decision, not preference)

- **`cargo clippy --all-targets --all-features -- -D warnings` must pass — warnings are errors.**
  A clippy warning is a build failure, not a suggestion. `cargo fmt --check` must pass too. The
  pre-commit hook runs both; **never `--no-verify`** to get past a failing gate — investigate it.
- **No `#[allow(...)]` without an explicit, justified, in-comment reason.** A blanket crate-level
  `#![allow(...)]` to dodge a whole lint class is forbidden; suppress the single site with the reason
  (`#[allow(clippy::…)] // why this is correct here`), or fix the finding.

## The panic-family ban in library code ({{PANIC_EQUIVALENT}} for Rust)

- **No `.unwrap()` / `.expect()` / `panic!` / `todo!` / `unimplemented!` / indexing-that-can-panic in
  library code** — i.e. anywhere under a package's `src/**` EXCEPT `src/bin/**`, `tests/`, `benches/`,
  `examples/`, and `#[cfg(test)]` blocks. A library that panics turns a caller's recoverable error into
  a process abort it can't catch. Return a typed error (`Result<T, E>`) and propagate with `?`.
- **Binary entrypoints and tests MAY panic where a failure is genuinely fatal** — but prefer
  `.expect("clear reason")` over a bare `.unwrap()` there, so the abort message names the invariant.
- **`unsafe` requires a `// SAFETY:` comment** stating the invariant upheld. Prefer a safe abstraction;
  `unsafe` is a last resort with its justification on disk, not in your head.

## Error-handling shape

- **Errors are typed, not stringly-typed.** Model failure as an enum (a typed-error derive macro such as
  `thiserror` is the common choice for libraries; a boxed dynamic error such as `anyhow` is acceptable at
  the binary boundary). Propagate with `?`.
- **Never discard a `Result`.** A dropped `Result` is a clippy `#[must_use]` failure and a real bug —
  handle it or propagate it. Don't `let _ = fallible();` to silence the lint without a reason comment.
- **Don't paper over the borrow checker with a needless `.clone()`** to "make it compile." Model
  ownership, or document why the clone is required.

## Dependency discipline

- **Shared dependencies go through `[workspace.dependencies]`** and are referenced as
  `dep = { workspace = true }` in members. Don't pin a divergent version of an already-shared dep in a
  single member's `Cargo.toml`.
- **Currency-check before adding or bumping ANY dependency** (`standing-rules-core.md` §external deps):
  verify the latest stable version + deprecation status of the *exact* API you use against
  current-year primary docs (the registry `{{PACKAGE_REGISTRY}}` + the crate's own docs), not from
  memory. Existing pins were a dated lookup — re-verify before touching them.
- **Respect feature gates.** Keep heavy / platform-specific dependencies behind their own feature flag so
  a lightweight consumer doesn't transitively pull them. Adding a dependency behind a new *default*
  feature is a decision — record it as an ADR.
- **Build-tool preconditions belong in the environment, not routed around.** If a build fails on a
  missing system tool (a code generator, a native `-sys` build dependency), fix the environment — don't
  disable the gate.

## Acceptance for any change here

- **A behavior change OWES a test that fails without it.** `cargo test` green is necessary, not
  sufficient — every behavior carries its falsifier.
- **IMPL → WIRED is the bar, not test-pass.** After it compiles and tests pass, prove the new code is
  reachable from a production entrypoint (a `main()`, a served command, an exported public API a real
  consumer calls) and record IMPL/WIRED/DEFER in `traceability/`. Prove reachability with
  `{{CODE_INTEL_TOOL}}` — for Rust that is rust-analyzer's reference / call-hierarchy tooling, with a
  grep-the-callers floor (see `code-intel.md`). Dead code that clippy's `dead_code` lint flags is a
  wiring failure, not noise.

## Related

- `code-intel.md` (the Rust reachability prover menu) · `standing-rules-core.md` (§Quality gates,
  §IMPL→WIRED) · `../../base/*/agent-docs/CONVENTIONS.md` (the schema contract)
