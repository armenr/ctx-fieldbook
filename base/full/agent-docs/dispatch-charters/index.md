---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, dispatch, multi-agent]
related: [CONVENTIONS]
---

# dispatch-charters/ — dispatch ledger

Dispatch charters as single-owner work-specs (one-file-one-owner · scope recalibrated against the
LIVE tree · a named wiring-proof target) + the wave-plan ledger. Per the schema contract, **this index
is a ledger TABLE, not prose.** Schema authority: `../CONVENTIONS.md`; ID `FR-NNNN`.

> **The altitude drop.** A **wave-plan** decomposes a work-unit into atomic single-builder charters;
> **waves** group charters so same-wave legs have NO file-overlap. Realize it as a fan-out: emit N
> typed charter objects against the live tree, dispatch in parallel, with a **clean-context verifier
> as a gate stage** — the executor never audits its own work. (The terms *wave-plan* and
> *dispatch-charter* are renameable to your team's vocabulary; see the glossary.)

## The dispatch contract (bake into every charter)

- **Hard scope fence:** the charter names the EXACT files the agent may touch + its single purpose +
  an explicit *do NOT fix/refactor/improve anything outside that, even if it's obviously broken.*
- **Report-all, act-only-in-lane:** any out-of-scope discovery goes to a REQUIRED `discoveries[]` /
  `out_of_scope` return field and is NOT acted on; if the surprise BLOCKS the task, the agent HALTs
  and returns `status: blocked` rather than inventing a workaround.
- **Enforcement:** analysis/review agents are READ-ONLY (or run in an isolated worktree); an
  independent reviewer (verifier ≠ builder) audits the diff for scope-creep before any commit; **no
  agent commits or merges** — the orchestrator is the sole, serial integration point.

## Entry purpose + naming

- **Purpose:** a self-contained, single-owner dispatch charter; the persisted brief is ground truth
  (no reconstruct-from-memory on retry).
- **Filename:** `dispatch-charters/YYYY-MM-DD-<wave>-<slug>.md` (or `FR-NNNN-<slug>.md`).
- **Write-discipline:** APPEND-ONLY. Status lifecycle: `drafting → dispatched → in-remediation →
  certified → merged → rolled-back`.

## Ledger

| FR-id | WU | Wave | Charter one-liner | Status |
|---|---|---|---|---|
<!-- EXAMPLE row (delete on the first real charter):
| `FR-0001-example.md` | WU-0001 | w01 | <single-purpose one-liner; the exact file set + wiring-proof target> | drafting |
-->

## What a charter MUST carry

File ownership (exact paths) · recalibrated scope (size/symbol estimate vs the LIVE tree, not a stale
assumption) · wiring-proof target (the production entrypoint the work must be reachable from,
IMPL→WIRED) · model-tier hint · the verifier-gate claim the clean-context verifier must independently
confirm. Acceptance = production-reachability + the quality gates green
(`{{BUILD_CMD}}` / `{{LINT_CMD}}` / `{{TEST_CMD}}`) + verifier sign-off.

## Maintenance

Dispatching a charter adds a ledger row here in the same change.
