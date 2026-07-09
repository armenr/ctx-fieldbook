---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-10
---

# `{{CODE_INTEL_TOOL}}` — the language-agnostic reachability prover

`{{CODE_INTEL_TOOL}}` is whatever tool your project reaches for to answer structural questions exactly —
"who calls X?", "what breaks if I change X?", "is X reachable, or is it dead?" — instead of guessing with
a text search. This file is the stack-neutral version of the IMPL→WIRED prover menu in
`standing-rules-core.md` (§IMPL→WIRED); a first-class stack pack (e.g. `../rust/code-intel.md`)
specializes it to a concrete language server.

Set `{{CODE_INTEL_TOOL}}` to the best structural tool your language + editor offer. In descending order of
what most projects have: a language server (LSP) exposing references and call hierarchy → a dedicated
call-graph / dependency-graph tool → structured search → plain `grep`. Prefer semantic over textual
whenever the semantic tool can answer.

## Tool-selection order (structural questions get structural answers)

1. **A language server (LSP)** — the default for references, definitions, call hierarchy, and rename.
   Semantic and exact: it resolves through modules, types, and generics where a regex can't. Most editors
   expose it; LSP-aware agent tools can drive it headless.
2. **A call-graph / module-dependency tool** for your language — for a wider view than one symbol's
   references. Whole-program call graphs are usually partial (dynamic dispatch, reflection, callbacks), so
   treat the output as a strong lead, not gospel.
3. **`grep` / `ripgrep`** — the honest floor, ONLY for literal text (comments, strings, log messages) or
   when no LSP is available. Never make grep your *only* evidence for a "who calls / is this wired"
   question when a language server can answer it semantically.

## The IMPL → WIRED prover menu (in order)

To prove new code is reachable from a production entrypoint (a `main`, an exported/served symbol, a
public API a real consumer calls):

1. **LSP "Find All References"** on the new symbol — does anything call it at all?
2. **LSP "Call Hierarchy" → incoming calls**, walked UPWARD — does the chain terminate at an entrypoint?
   If it dead-ends inside your own module with no external caller, it is IMPL-not-WIRED.
3. **A call-graph tool** (menu item 2 above) when the reference walk is ambiguous across a dynamic-dispatch
   or callback boundary.
4. **grep-the-callers floor** — a word-bounded search for the symbol name across your source globs — when
   no LSP is running. Note in `traceability/` that the evidence is textual, not semantic.
5. **Manual-trace note** — when even grep can't settle it (reflection, generated call sites, a plugin
   registry), write the hand-traced path into the `traceability/` row so the reasoning is on disk.

## Dead-code as the wiring alarm

- **Your linter's / compiler's dead-code or unused-symbol warning is the built-in wiring-trap detector.**
  A fresh unreachable-symbol warning on code you just added means you wrote it but never wired it — that
  is a wiring failure, not noise.
- **Beware the public-API blind spot:** many toolchains do NOT flag an unreachable *exported* symbol
  (they assume an external consumer might call it). So for a new public API, the linter's silence is not
  proof of wiring — use the reference / call-hierarchy walk above to confirm a real caller exists.

## Reachability baseline

With no code-intel tool installed, the baseline is the **grep-floor call-chase**, run deterministically:
from each production entrypoint (a `main`, a served handler, an exported API a real consumer calls) grep the
symbols it calls, then grep the callers of your new symbol, and chase the chain by hand until it either
reaches an entrypoint (WIRED) or dead-ends (IMPL-not-WIRED). It is reproducible but purely textual — it
misses dynamic dispatch, reflection, and re-exported aliases, and its cost grows with call depth. **Honest
note: this is a floor, not an oracle.** A real reachability tool — a language server's call hierarchy, or a
dead-code detector like the ones the first-class packs name (`deadcode`, `knip`, `vulture`, rustc
`dead_code`) — should replace it the moment one exists for the stack. Record the hand-traced chain in
`traceability/` so the textual evidence is on disk, not lost.

> **Currency:** the named exemplar tools (`deadcode`, `knip`, `vulture`, rustc `dead_code`) checked against
> PRIMARY docs on 2026-07-10; see each stack pack's `code-intel.md`. Re-verify before adopting.

## Related

- `standing-rules-core.md` (§IMPL→WIRED prover menu) · `rules.template.md` (§Acceptance) ·
  `../rust/code-intel.md` (a concrete specialization)
