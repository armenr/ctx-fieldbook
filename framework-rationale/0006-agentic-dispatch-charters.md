---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0001-in-repo-context-system, 0002-session-lifecycle-skills]
tags: [meta, framework, dispatch, multi-agent]
---

# ADR-0006 — Dispatch-charter agentic dispatch framework

> Framework rationale that ships with the kit (Full profile). Explains why
> multi-agent work is decomposed into fenced, file-disjoint dispatch charters with
> an independent verifier. Renamed terms: a *dispatch charter* is the atomic
> single-builder work-spec; a *wave-plan* is the parent operation it decomposes.

## Context

Multi-agent work — parallel builders, deterministic fan-out — needs structured
decomposition, file-overlap-safe sequencing, and adversarial review. Ad-hoc
fan-out collides on shared files and ships hallucinated plans. The two disciplines
that pay for themselves here: the wave-plan → dispatch-charter *altitude drop*
(decomposing a stale high-level plan into charters recalibrated against the live
tree), and the constraint that **the executor never audits its own work** — a
reviewer with an authorship stake is not a reviewer, and self-review passing work
that an independent pass immediately fails is a recurring, expensive failure.

## Alternatives Considered

- **Ad-hoc parallel dispatch.** Rejected: file collisions, no review, no handling
  of drift between the plan and the live tree — the parallel agents clobber each
  other and ship plans built on stale assumptions.
- **A two-tier human relay** — a strategy layer compiles wave-plans, a human
  copy-pastes them to executors, and state is synced by hand. Rejected: the human
  bridge is the system's single point of failure and does not survive a different
  harness. The durable *role contract* (strategy / execution separation with
  independent verification) is kept; the copy-paste mechanism is dropped.
- **One orchestrator + schema'd sub-agents + dynamic workflows, with the verifier
  realized as a clean-context gate stage.** Chosen.

## Decision

- **Wave-plan → dispatch-charters:** decompose a parent operation into atomic,
  self-contained, single-builder charters (`FR-NNNN`, from a charter template),
  each recalibrated against the LIVE tree rather than the parent plan's stale
  line/symbol assumptions.
- **Waves:** group charters so same-wave charters have **no file overlap**;
  serialize any touches to shared surfaces — an interface contract restated across
  its producers and consumers, a schema restated across its builder and its query
  callers, an invariant restated across a write path and its recovery path, or any
  `twin:` / `claim:` REVISIT site (ADR-0007). The orchestrator VERIFIES file-
  disjointness before launching a parallel wave.
- **Before dispatch:** state reconnaissance (drift vs the base commit).
  **After a builder returns:** brief-back verification (catch charter
  hallucination). **Before the operator commits:** adversarial plan-review —
  applied to *designs*, not just code (a design reviewed only by its author is
  unreviewed).
- Realized as **one orchestrator dispatching schema'd sub-agents + dynamic
  workflows**; the **clean-context verifier is a workflow gate stage** with no
  authorship stake. The persisted charter is ground truth — no copy-paste relay,
  and a retry replays the persisted charter verbatim rather than reconstructing it
  from memory.

## Consequences

- **+** Safe parallelism; hallucination and file collisions caught before
  dispatch; durable on-disk charters; the verifier has no stake in the work it
  audits.
- **−** Real ceremony — worth it for multi-step multi-agent work, overkill for a
  single edit. Reach for it when the work is genuinely parallel, not by default.

## Related

- ADR-0002 (the orchestrator drives from `now/work-plan.md`) · ADR-0005 (the
  charter index is a ledger table) · ADR-0007 (`twin:` anchors mark the shared
  surfaces to serialize)
- Charter template · dispatch-charter index
