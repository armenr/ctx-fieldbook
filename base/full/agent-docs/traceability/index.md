---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, traceability, wiring]
related: [CONVENTIONS]
---

# traceability/ — routing catalog

The **IMPL→WIRED ledger**: verification by **production-reachability, not test-pass**. One row per
work-unit with an explicit `IMPL` / `WIRED` / `DEFER` state; `WIRED` requires a traced path from a
production entrypoint (the real `main()` / served command / request handler). Schema authority:
`../CONVENTIONS.md`.

> **Why this tier exists — a recurring, expensive trap.** *Code that compiles and passes tests but is
> never reachable from a production entrypoint* — the built-but-not-wired trap. Tests-green ≠ done; a
> unit of work is done when a path traces from a real entrypoint to the new code. Keep the discipline;
> hold the ledger to a table, not a monolith.

## The wiring proof (the reachability-prover MENU)

Prove reachability with the best tool your stack offers, in this order of preference — the point is an
*evidence-on-disk* trace, not any one product:

1. **{{CODE_INTEL_TOOL}}** reachability/dead-code query, if the project has one.
2. **LSP find-references** on the symbol, walked up to an entrypoint.
3. **LSP / editor call-hierarchy** (incoming calls) to the same end.
4. A **language call-graph tool** (whatever the ecosystem provides).
5. The **grep-the-callers floor** — grep every call site and read the chain by hand.
6. A **manual-trace note** — when none of the above apply, write the traced path explicitly and cite
   the files.

Cross-layer lockstep surfaces are anchored with `twin:` REVISIT markers (see `reference/`).

## Entry purpose + naming

- **Purpose:** prove each work-unit is reachable from production, not merely test-green.
- **Form:** ONE ledger doc with a table; row = work-unit, keyed by `WU-NNNN`.
- **Write-discipline:** UPDATE-IN-PLACE (per work-unit rows).

## Entry SCHEMA — the ledger row

| Column | Meaning |
|---|---|
| `WU` | the work-unit this row tracks (`WU-NNNN`) |
| State | `IMPL` (built) · `WIRED` (reachable from an entrypoint, proof attached) · `DEFER` (intentionally not yet wired, with reason) |
| Entrypoint | the production entrypoint the WIRED path traces from |
| Proof | the reachability evidence (which prover from the menu, + its output) — evidence-on-disk |
| REVISIT | linked `RV-NNN` `twin:` anchors for cross-layer surfaces, if any |

## Gate semantics

This is a **mandatory gate at phase boundaries**, not an afterthought. A `WU` may not be marked done
while its row is still `IMPL` with no `WIRED`/`DEFER` resolution.

## Ledgers

<!-- EXAMPLE (delete this block on the first real ledger doc):
- ⭐ `wiring-ledger.md` — the per-work-unit IMPL→WIRED table. **Open when:** checking whether a WU is
  actually reachable from production, or before marking a WU done. **Carry-away:** <how many WUs are
  WIRED vs IMPL-only vs DEFER, and where the proofs live>.
-->

## Maintenance

UPDATE-IN-PLACE — rows added/advanced as work-units progress; this index points at the ledger docs.
Adding/retiring a ledger doc updates this index in the same change.
