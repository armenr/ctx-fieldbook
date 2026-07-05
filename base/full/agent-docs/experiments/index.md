---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, experiments]
related: [CONVENTIONS]
---

# experiments/ — routing catalog

Spikes and probes with a captured outcome — the throwaway-spike home. A durable finding is **promoted
OUT** of an experiment INTO `reference/` (a WHAT-IS fact), a `memories/` claim, or an ADR; the
experiment itself records the probe and its verdict. Schema authority: `../CONVENTIONS.md`.

> **Experiment vs reference.** An *experiment* is a time-boxed probe whose value is the outcome
> (confirmed / refuted / inconclusive), not the scaffolding. Don't let a spike masquerade as a
> standing fact — capture the outcome, then promote the durable part and let the probe rest.

## Entry purpose + naming

- **Purpose:** a captured spike/probe — the question, what was tried, and the verdict.
- **Filename:** `experiments/YYYY-MM-DD-<slug>.md`.
- **Write-discipline:** APPEND-ONLY (the outcome is written once the probe concludes).

## Entry SCHEMA (body)

Question / hypothesis · What was tried (setup, enough to re-run) · Result (confirmed / refuted /
inconclusive) · **Promoted-to** (the `reference/` doc, `memories/` claim, or ADR the durable finding
moved to — or "nothing durable").

## Experiments

<!-- EXAMPLE (delete this block on the first real experiment):
- `2026-07-03-example-probe.md` — **Open when:** <someone is about to re-ask the question this probe
  already answered>. **Carry-away:** <the verdict in one sentence + where the durable finding was
  promoted, if anywhere>.
-->

## Maintenance

APPEND-ONLY; adding an experiment adds a row here in the same change. When a finding is promoted, add
the `Promoted-to` pointer rather than deleting the experiment.
