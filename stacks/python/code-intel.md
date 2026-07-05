---
provenance: kit-template
created: 2026-07-03
paths: ["**/*.py", "**/*.pyi"]
---

# `{{CODE_INTEL_TOOL}}` for Python — the reachability prover

`{{CODE_INTEL_TOOL}}` is the tool you reach for to answer structural questions exactly — "who calls X?",
"what breaks if I change X?", "is X reachable, or is it dead?" — instead of guessing with a text search.
For Python the default resolution is a **Python language server** — `pyright` (`pyright-langserver`,
also `basedpyright`) or `python-lsp-server` (`pylsp`) — driven either through your editor's LSP UI or
through an LSP-aware agent tool. It resolves imports, re-exports, and class hierarchies where a regex
cannot. This file specializes the language-agnostic prover menu in `standing-rules-core.md`
(§IMPL→WIRED) to Python.

## Tool-selection order (structural questions get structural answers)

1. **A Python language server (LSP)** — the default for references, definitions, call hierarchy,
   implementations, and rename. Semantic, not textual: it follows an `import` and an aliased re-export
   that a grep would miss. Python's dynamism (getattr, decorators, dependency injection) means the LSP is
   authoritative for static call sites but cannot see a purely dynamic dispatch — see the floor below.
2. **A dead-code / call-graph tool (OPTIONAL, not required)** — for a wider view than one symbol's
   references: `vulture` (reports unused functions, classes, and imports — a dead-code detector, i.e. the
   wiring-trap alarm), `pydeps` (module import graph), or `code2flow` / `pyan3` for a call graph. Their
   output is a strong lead, not gospel, across dynamic dispatch; `vulture` in particular flags a
   dynamically-referenced symbol as unused, so confirm before deleting.
3. **`grep` / `ripgrep`** — the honest floor, ONLY for literal text (comments, strings, log messages,
   route paths, a symbol referenced by string key) or when no LSP is available. Never use grep as your
   *only* evidence for a "who calls / is this wired" question when the language server can answer it
   semantically.

## The IMPL → WIRED prover menu (in order)

To prove new code is reachable from a production entrypoint (a `[project.scripts]` console-script
`main`, a `python -m <pkg>` `__main__`, a registered route/handler, a public API a real caller imports):

1. **LSP "Find All References"** on the new symbol — does anything import or call it at all?
2. **LSP "Call Hierarchy" → incoming calls**, walked UPWARD — does the chain terminate at an entrypoint
   (a console-script `main`, a `__main__` block, a route registered on the app)? If it dead-ends inside
   your own module with no external importer, it is IMPL-not-WIRED.
3. **A dead-code tool** (menu item 2 above) — `vulture <pkg>` surfaces a function/class nothing
   references, and `pydeps` shows a module nothing imports: the loudest form of the wiring trap.
4. **grep-the-callers floor** — find the definition then its call sites: `rg 'def my_fn\b'` then
   `rg '\bmy_fn\(' -g '*.py'` — when no LSP is running. Note in `traceability/` that the evidence is
   textual (it will miss a call through `getattr` or a re-exported alias).
5. **Manual-trace note** — when even grep can't settle it (a handler wired by string key, a plugin
   discovered by entry-point, a decorator-registered callback), write the hand-traced path into the
   `traceability/` row so the reasoning is on disk, not lost.

## Dead-code as the wiring alarm (and its blind spot)

- **Ruff's pyflakes rules catch unused *within* a module** — `F401` (unused import), `F811`
  (redefinition), `F841` (unused local). A fresh hit on code you just added means you wrote it but never
  used it locally. These fail the `ruff check` gate.
- **Ruff does not see an unused *public* function across the module boundary** — an exported symbol
  nothing imports is invisible to it, exactly the built-but-not-wired case. That gap is what `vulture`
  and the LSP reference walk above exist to close; a clean `ruff check` on an export is not proof of
  wiring. When a real caller is dynamic (an entry-point plugin, a framework auto-discovery), record the
  manual trace rather than trusting either tool's silence.

## Related

- `rules.md` (§Acceptance — IMPL→WIRED) · `standing-rules-core.md` (§IMPL→WIRED prover menu) ·
  `../generic/code-intel.md` (the language-agnostic version)
