---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0001-in-repo-context-system, 0004-operational-hooks]
tags: [meta, framework, lifecycle, checkpoints]
---

# ADR-0002 — Session lifecycle skills: /orient, /flush, /handoff (+ /sitrep)

> Framework rationale that ships with the kit. Explains why session state is
> bridged by explicit skills rather than left to memory.

## Context

Sessions end, get cleared, or hit context compaction. The curated "where are we +
immediate next action + anti-assumptions" state is lost without an explicit
bridge artifact — the agent's native memory does not reliably carry it forward.
Worse, a *naive summary* silently drops the investigation dead-ends and rejected
alternatives that are the actual value of a session; those are exactly what a
future agent needs to avoid re-deriving a wrong inference.

## Alternatives Considered

- **Rely on native session memory.** Rejected: loses the curated next-action and
  the decision rationale — the things you need *at the start* of the next session.
- **Manual ad-hoc notes.** Rejected: inconsistent and undisciplined; when the
  format is up to the moment, the load-bearing detail is the first thing skipped.
- **A single lighter `/handoff`-only bridge, no separate checkpoint tier.**
  Rejected for the zero-loss case: it under-specifies what must survive, so a
  handoff written in a hurry drops the dead-ends. The fix is to promote a
  10-point zero-loss checkpoint as an explicit anti-naive-summarization contract,
  distinct from the lighter session-end handoff.
- **Four explicit lifecycle skills + a durable bridge artifact + immutable
  checkpoints.** Chosen.

## Decision

- **`/orient`** — read `now/handoff.md` (plus the latest `checkpoints/` sitrep),
  verify staleness against git reality, and surface a short brief.
- **`/flush`** — mid-session checkpoint: rewrite `now/*` and append `log.md`; keep
  working in the same session.
- **`/sitrep`** — write a WRITE-ONCE, immutable 10-point zero-loss checkpoint to
  `checkpoints/YYYY-MM-DD-HHMMSS-<slug>.md`, keyed to the active `WU`. This is the
  anti-naive-summarization artifact: it mandates capturing investigation results
  *including dead-ends* and decisions *with their rejected alternatives*.
- **`/handoff`** — session-end / pre-compaction: update `now/*` and `log.md`, run
  the conversation-residue and workflow-provenance sweeps, capture the required
  anti-assumptions and the detour chain, run the lesson reflection, consume the
  latest checkpoint, then regenerate `now/handoff.md` (archiving the prior).

All four run **FOREGROUND in the main agent**. A sub-agent has zero session
context, so briefing it to capture the state *is* the work — outsourcing is a
wasteful indirection (and sub-agent permissions are narrower). A PreCompact hook
triggers a silent `/handoff` before compaction (ADR-0004).

## Consequences

- **+** Reliable resume. The captured anti-assumptions ("looks like X → actually
  Y") plus the detour chain are the best defense against re-derived wrong
  inferences on the next session.
- **−** A short main-agent writeback pause; the ritual must be honored at
  checkpoints, not skipped under momentum.
- **Never auto-commit** — the operator controls git; the skills update docs, they
  do not commit them.

## Related

- ADR-0004 (PreCompact + SessionStart hooks) · ADR-0003 (lesson reflection at
  `/handoff`)
- `CONVENTIONS.md` (the 10-point checkpoint contract) · `checkpoints/index.md`
- Skills: `orient`, `flush`, `handoff`, `sitrep`
