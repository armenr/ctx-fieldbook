---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-10
paths: ["**/*.rs"]
---

# `{{CODE_INTEL_TOOL}}` for Rust — the reachability prover

`{{CODE_INTEL_TOOL}}` is the tool you reach for to answer structural questions exactly — "who calls X?",
"what breaks if I change X?", "is X reachable, or is it dead?" — instead of guessing with a text search.
For Rust the default resolution is **rust-analyzer**, the Rust language server, driven either through your
editor's LSP UI or through an LSP-aware agent tool. This file specializes the language-agnostic prover
menu in `standing-rules-core.md` (§IMPL→WIRED) to Rust.

## Tool-selection order (structural questions get structural answers)

1. **rust-analyzer (LSP)** — the default for references, definitions, call hierarchy, implementations,
   and rename. Semantic and exact: it resolves through modules, traits, and generics where a regex can't.
2. **A Rust call-graph / module tool** — for a wider view than a single symbol's references (e.g.
   `cargo-modules` for the module + item dependency tree; `cargo-call-stack` for a call graph where your
   target supports it). Whole-program call graphs in Rust are partial by nature (trait objects, function
   pointers), so treat the output as a strong lead, not gospel.
3. **`grep` / `ripgrep`** — the honest floor, ONLY for literal text (comments, strings, log messages,
   feature names) or when no LSP is available. Never use grep as your *only* evidence for a "who calls /
   is this wired" question when rust-analyzer can answer it semantically.

## The IMPL → WIRED prover menu (in order)

To prove new code is reachable from a production entrypoint (a `main()`, a `#[no_mangle]` / exported
symbol, a bin target, or a public API a real consumer calls):

1. **rust-analyzer "Find All References"** on the new item — does anything call it at all?
2. **rust-analyzer "Call Hierarchy" → incoming calls**, walked UPWARD — does the chain terminate at an
   entrypoint (`fn main`, a `pub` API surface an external caller uses, a registered command handler)? If
   it dead-ends inside your own module with no external caller, it is IMPL-not-WIRED.
3. **A call-graph tool** (menu item 2 above) when the reference walk is ambiguous across a trait boundary.
4. **grep-the-callers floor** — `rg '\bmy_fn\b' -g '*.rs'` — when no LSP is running. Note in
   `traceability/` that the evidence is textual, not semantic.
5. **Manual-trace note** — when even grep can't settle it (dynamic dispatch, a macro-generated call
   site), write the hand-traced path into the `traceability/` row so the reasoning is on disk, not lost.

## Dead-code as the wiring alarm

- **clippy / rustc's `dead_code` lint is the built-in wiring-trap detector** for private items: an
  unreachable `fn`, `struct`, or field fires a warning, which under `-D warnings` is a build failure. A
  fresh `dead_code` hit on code you just added means you wrote it but never wired it.
- **`dead_code` does NOT flag unreachable `pub` items** — the compiler assumes an external consumer might
  call them. So for a new *public* API, the compiler's silence is not proof of wiring; use the
  rust-analyzer reference / call-hierarchy walk above to confirm a real caller exists.

## Reachability baseline

The deterministic oracle is built into the toolchain: **rustc / clippy's `dead_code` lint**, promoted to a
gate with `-D warnings` (or `#![deny(dead_code)]`), fails the build on any unreachable private item every
compile — reproducible, no extra tool. A fresh `dead_code` hit on code you just added is IMPL-not-WIRED (the
`pub`-item blind spot from the section above still applies — confirm a new public API with the rust-analyzer
reference walk). For the dependency axis, **`cargo-udeps`** (`cargo +nightly udeps`, compiler-accurate,
nightly-only) and the faster text-based **`cargo-machete`** report crates declared in `Cargo.toml` but never
used. If nightly / udeps is unavailable, the `dead_code` gate plus the grep-floor call-chase are the floor;
record in `traceability/` that the residual evidence is textual.

> **Currency:** `cargo-udeps` / `cargo-machete` checked against PRIMARY docs on 2026-07-10
> (crates.io/crates/cargo-udeps, crates.io/crates/cargo-machete). Re-verify before adopting.

## Related

- `rules.md` (§Acceptance — IMPL→WIRED) · `standing-rules-core.md` (§IMPL→WIRED prover menu) ·
  `../generic/code-intel.md` (the language-agnostic version)
