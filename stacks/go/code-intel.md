---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-10
paths: ["**/*.go"]
---

# `{{CODE_INTEL_TOOL}}` for Go — the reachability prover

`{{CODE_INTEL_TOOL}}` is the tool you reach for to answer structural questions exactly — "who calls X?",
"what breaks if I change X?", "is X reachable, or is it dead?" — instead of guessing with a text search.
For Go the default resolution is **gopls**, the official Go language server
(golang.org/x/tools/gopls), driven either through your editor's LSP UI or through an LSP-aware agent
tool. This file specializes the language-agnostic prover menu in `standing-rules-core.md`
(§IMPL→WIRED) to Go.

> **Currency:** checked against PRIMARY docs on 2026-07-03 (go.dev, pkg.go.dev/golang.org/x/tools/gopls,
> pkg.go.dev/golang.org/x/tools/cmd/callgraph). Re-verify before adopting.

## Tool-selection order (structural questions get structural answers)

1. **gopls (LSP)** — the default for references, definitions, call hierarchy, and implementations.
   Semantic and exact: it resolves through packages, interfaces, and embedding where a regex cannot.
   Run it at the module root (the directory holding `go.mod`) so it indexes every package.
2. **The toolchain's package graph** — `go list` answers *package*-level reachability without an editor:
   `go list -deps ./path/to/main-pkg` prints an entrypoint's full dependency closure; `go list -json ./...`
   emits the machine-readable import graph. Fast, but package-level only — it does not prove a *symbol*
   is called (step 4 does that).
3. **A whole-program static call graph** — `callgraph` from golang.org/x/tools/cmd/callgraph
   (`callgraph -algo=rta -format=graphviz ./...`; algorithms: `static`, `cha`, `rta`, `vta`) emits the
   call graph rooted at a `main` package. Its predecessor `guru` is **deprecated / superseded by gopls**
   — do not reach for guru; use gopls (step 1) or `callgraph`. Call graphs are partial by nature
   (interface dispatch, reflection, `func` values), so treat the output as a strong lead, not gospel.
4. **`grep` / `ripgrep`** — the honest floor, ONLY for literal text (comments, strings, log messages,
   build tags) or when no LSP is available. Never use grep as your *only* evidence for a "who calls / is
   this wired" question when gopls can answer it semantically.

## The IMPL → WIRED prover menu (in order)

To prove new code is reachable from a production entrypoint (a `main` package's `main()`, an `init()`,
a registered `http.Handler`, a registered CLI command, or a public API a real consumer calls):

1. **gopls "Find All References"** (LSP `textDocument/references`) on the new symbol — does anything call
   it at all? Zero references from non-test code ⇒ IMPL-not-WIRED.
2. **gopls "Call Hierarchy" → incoming calls** (LSP `callHierarchy/incomingCalls`), walked UPWARD — does
   the chain terminate at an entrypoint edge (a `main()`, an `init()`, a handler / command registration)?
   If it dead-ends inside your own package with no external caller, it is IMPL-not-WIRED.
3. **`go list -deps` on the entrypoint package** (step 2 above) to confirm the package is even in the
   binary's dependency closure, then **`callgraph`** when the reference walk is ambiguous across an
   interface boundary.
4. **grep-the-callers floor** — `grep -rn 'FuncName(' --include='*.go' .` — when no LSP is available.
   Text-only (misses interface-dispatched and same-name-different-package calls); note in
   `traceability/` that the evidence is textual, not semantic.
5. **Manual-trace note** — when even grep can't settle it (reflection, interface dispatch, code
   generation, a plugin / DI registry), hand-trace the path and WRITE the trace into the `traceability/`
   row or the checkpoint's evidence, so the reasoning is on disk, not lost.

## Dead-code as the wiring alarm

- **The `unused` linter (default-on in `golangci-lint`) and staticcheck `U1000`** flag unreachable
  package-level declarations. A fresh hit on code you just added means you wrote it but never wired it —
  resolve the wiring, do not silence the lint.
- **The compiler only rejects unused *locals* and *imports*** — an unused *exported* / package-level
  function or type compiles clean, so the compiler's silence is NOT proof of wiring. Use the gopls
  reference / call-hierarchy walk above to confirm a real caller exists.

## Reachability baseline

The deterministic oracle the IMPL→WIRED proof cites is **`deadcode`** (golang.org/x/tools/cmd/deadcode):
via Rapid Type Analysis it builds the whole-program call graph rooted at every `main` (add `-test` for test
binaries) and prints every function unreachable from those entrypoints — one reproducible, scriptable run:
`deadcode ./...`. A symbol you just added that it lists is IMPL-not-WIRED; `-whylive=pkg.Func` prints the
live call path when it *is* wired. RTA is conservative (interface / reflection / `func`-value calls may
over-report reachability, and `//go:linkname` is unmodelled), so a *listed* symbol is a strong dead verdict
but an *absent* one still wants the call-hierarchy walk above to name the caller. If `deadcode` is
unavailable, fall back to the grep-floor call-chase and record in `traceability/` that the evidence is
textual, not analysis-backed.

> **Currency:** `deadcode` checked against PRIMARY docs on 2026-07-10
> (pkg.go.dev/golang.org/x/tools/cmd/deadcode, v0.48.0). Re-verify before adopting.

## Related

- `rules.md` (§Acceptance — IMPL→WIRED) · `standing-rules-core.md` (§IMPL→WIRED prover menu) ·
  `../generic/code-intel.md` (the language-agnostic version)
