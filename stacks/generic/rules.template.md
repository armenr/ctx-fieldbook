---
provenance: kit-template
created: 2026-07-03
---

# {{PRIMARY_LANGUAGE}} quality-gate rules (concierge-filled)

<!--
  This is a TEMPLATE the install concierge fills from the interview when no first-class stack pack
  (rust / node-ts / python / go) matches the target project. It is the stack-specific concretion of
  the universal discipline in standing-rules-core.md (§Quality gates) for whatever language the
  project uses. Fill every {{PLACEHOLDER}}, work through each "Fill:" note, then delete the notes and
  this comment. Set the loaded-when scope by adding a `paths:` front-matter field with your source
  globs (e.g. `paths: ["src/**/*.<ext>"]`).
-->

The stack binding for the generic `{{LINT_CMD}} / {{FMT_CMD}} / {{TEST_CMD}} / {{PANIC_EQUIVALENT}} /
{{CODE_INTEL_TOOL}}` seams. Keep it short; deep architecture lives in your project's `reference/`.

## Lint & format gates (strict by decision, not preference)

- **`{{LINT_CMD}}` must pass — warnings are errors.** A lint finding is a build failure, not a
  suggestion. `{{FMT_CMD}}` (check mode) must pass too. The pre-commit hook runs both; **never bypass a
  failing gate** — investigate it.
  > Fill `{{LINT_CMD}}`: your linter in its strictest mode. Choose the setting that turns warnings into
  > errors and covers all targets/files (the equivalent of a "deny warnings" / "max strict" flag). If
  > your language ships no linter, name the type-checker or compiler-with-warnings-as-errors instead.
  > Fill `{{FMT_CMD}}`: your formatter in check/verify mode (fails on unformatted files, writes nothing).
- **No lint suppression without an explicit, justified, in-comment reason.** A blanket file- or
  project-level suppression to dodge a whole lint class is forbidden; suppress the single site with the
  reason, or fix the finding.

## The crash-on-unexpected ban in library code ({{PANIC_EQUIVALENT}})

- **Do not reach for `{{PANIC_EQUIVALENT}}` in library code** (the reusable, imported-by-others part of
  the codebase, excluding entrypoints/tests). A library that crashes on an unexpected value turns a
  caller's recoverable error into a failure it can't handle. Return a typed error and propagate it.
  > Fill `{{PANIC_EQUIVALENT}}`: the crash-on-unexpected construct(s) your language offers that must not
  > appear in library code — the thing that aborts or throws instead of returning a typed failure.
  > Examples by language: a force-unwrap / assert-or-die on a maybe-absent value; a non-null assertion
  > that silently trusts a nullable; an uncaught throw used for an *expected* (not exceptional)
  > condition; a bare `panic` / `abort` / `os.exit` inside library code. Name the specific tokens so the
  > rule is checkable (e.g. "force-unwrap and panic-family calls").
- **Entrypoints and tests may crash where a failure is genuinely fatal** — but attach a clear reason
  message so the abort names the invariant that was violated.

## Error-handling shape

- **Errors are typed, not stringly-typed.** Model failure as a value the caller can branch on
  (a result/error type, a checked exception hierarchy — whatever your language idiom is), not an opaque
  string.
- **Never silently discard an error result.** Handle it or propagate it; don't swallow it to make the
  code compile or the linter quiet.

## Dependency discipline

- **Currency-check before adding or bumping ANY dependency** (`standing-rules-core.md` §external deps):
  verify the latest stable version + deprecation status of the *exact* API you use against
  current-year primary docs (the registry `{{PACKAGE_REGISTRY}}` + the dependency's own docs), never
  from memory. Pin through the shared manifest; don't pin a divergent version in one package.
- **Build-tool preconditions belong in the environment, not routed around.** If a build fails on a
  missing system tool, fix the environment — don't disable the gate.

## Acceptance for any change here

- **A behavior change OWES a test that fails without it.** `{{TEST_CMD}}` green is necessary, not
  sufficient — every behavior carries its falsifier.
- **IMPL → WIRED is the bar, not test-pass.** After it builds and tests pass, prove the new code is
  reachable from a production entrypoint (a `main`, a served command, an exported API a real consumer
  calls) and record IMPL/WIRED/DEFER in `traceability/`. Prove reachability with `{{CODE_INTEL_TOOL}}`
  (see `code-intel.md`) — editor LSP find-references → call-hierarchy → a call-graph tool →
  grep-the-callers floor → a manual-trace note. Dead code the linter flags is a wiring failure, not noise.

## Related

- `code-intel.md` (the reachability prover menu) · `standing-rules-core.md` (§Quality gates,
  §IMPL→WIRED) · `CONVENTIONS.md` (the schema contract)
