---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0002-session-lifecycle-skills, 0005-per-directory-routing-indexes]
tags: [meta, framework, lessons]
---

# ADR-0003 — Typed lessons-learned ledger

> Framework rationale that ships with the kit. Explains why lessons are a typed,
> decay-aware, human-gated ledger rather than freeform notes.

## Context

Failure patterns and near-misses recur. Without a typed, deduped, decay-aware
ledger they are re-learned from scratch each time — the same expensive mistake,
paid for again. But the opposite failure is just as real: without a promotion
gate, a lessons store fills with low-signal noise until nobody reads it, and an
always-loaded surface of stale "lessons" is worse than none.

## Alternatives Considered

- **Freeform notes / memories only.** Rejected: no typing, no decay, no bounded
  surface — the store grows without discrimination and the signal drowns.
- **An LLM that auto-promotes lessons.** Rejected: it produces noise *and*
  same-model confirmation bias — the model rates its own inferences as insightful.
  This is exactly why promotion is human-gated with a two-step gradient (see
  Decision): the model critiques, then proposes, but a human accepts.
- **A typed ledger with a bounded auto-loaded surface + human-gated promotion + a
  quarantine for era-bound lessons.** Chosen.

## Decision

Atomic entries at `lessons/<id>.md` (`LP-NNN`), each with three-axis frontmatter
(`provenance × maturity × severity`) plus an `entry_type: lesson | near-miss`
discriminator (schema in `CONVENTIONS.md`). A **Tier-1 MOC** (a bounded map-of-
content, capped small) is auto-loaded by the SessionStart hook — this is the only
lessons surface loaded by default.

`/distill-lessons` proposes candidates (`provenance: llm-draft`,
`maturity: seedling`) into a proposals file. **Promotion is always human-gated at
`/handoff`**, using a two-step gradient (critique-only → propose-only) to mitigate
same-model mode-collapse. Maturity ripens `seedling → budding → evergreen`; entries
whose `last-applied` exceeds a decay window are pruned to `lessons/archive/`.

A **quarantine** sub-section (`status: quarantined`) holds lessons that are true
only of a specific model or harness era — kept for genealogy, never auto-loaded
into the Tier-1 MOC; the quarantine screen is human-gated.

## Consequences

- **+** A high-signal, bounded, decay-pruned surface; lessons are typed and
  evidence-linked (claim / trigger / mitigation), so a future agent can act on
  them.
- **−** Requires discipline at the gate — "0 high-quality proposals accepted" must
  beat "3 weak ones," or the surface rots.
- Lessons ≠ runbooks (procedures) ≠ ADRs (decisions). Keep the three distinct so
  each stays readable for its purpose.

## Related

- ADR-0002 (the `/handoff` promotion gate) · ADR-0004 (SessionStart MOC injection)
- Skill: `distill-lessons` · `lessons/MOC.md`, `lessons/proposals.md`
