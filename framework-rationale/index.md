---
provenance: kit-template
status: accepted
created: 2026-07-03
tags: [meta, framework, index]
---

# framework-rationale/ — the WHY that ships

The generalized framework ADRs plus the narrative that ties them together. These
teach *why* the context system is shaped the way it is; the **Alternatives
Considered** section of each ADR is the real value — the rejected options and the
reasons are what keep you from re-making an already-made mistake.

**These are read-only reference, not your project's decision log.** Your own
`decisions/` starts empty and is seeded by your real ADR-0001 ("adopted this
context system"). Read these to understand the design; do not treat them as
decisions you made.

## Start here

- **`why-this-system.md`** — the connective narrative: the six load-bearing
  principles (progressive disclosure, findings-to-disk, IMPL→WIRED, adversarial
  separation, ceremony-as-fossil, the three write-disciplines).
  *Open when:* you want the whole system's logic before diving into any one ADR.
  *Carry-away:* internalize the six principles or the folders are just ceremony.

## The framework ADRs

- **`0001-in-repo-context-system.md`** — adopt one in-repo knowledge base fronted
  by a pointer-style `CLAUDE.md`.
  *Open when:* deciding where durable project context should live.
  *Carry-away:* the discipline is the asset; copying the folders without the
  ethos is the failure mode.

- **`0002-session-lifecycle-skills.md`** — `/orient`, `/flush`, `/handoff`, and
  the immutable `/sitrep` checkpoint.
  *Open when:* deciding how state survives session end and compaction.
  *Carry-away:* a naive summary drops the dead-ends that are the actual value —
  the checkpoint tier exists to stop that.

- **`0003-lessons-learned-ledger.md`** — a typed, decay-aware lessons ledger with
  human-gated promotion.
  *Open when:* deciding how recurring failures get captured without noise.
  *Carry-away:* auto-promotion breeds same-model confirmation bias; a human gates
  promotion, and "0 good proposals" beats "3 weak ones."

- **`0004-operational-hooks.md`** — deterministic hooks for the safety-critical +
  lifecycle subset.
  *Open when:* deciding what must be enforced vs left advisory.
  *Carry-away:* rules without enforcement are decorative — hook the subset that
  must never be forgotten, leave the rest advisory.

- **`0005-per-directory-routing-indexes.md`** — per-directory `index.md` catalogs
  plus a presence lint.
  *Open when:* deciding how knowledge is found without browsing raw folders.
  *Carry-away:* route to the one right doc; a numeric read-cap limits volume
  without improving aim.

- **`0006-agentic-dispatch-charters.md`** *(Full profile)* — decompose multi-agent
  work into fenced, file-disjoint dispatch charters with an independent verifier.
  *Open when:* running parallel builders or deterministic fan-out.
  *Carry-away:* the executor never audits its own work; charters must be
  file-disjoint within a wave.

- **`0007-revisit-anchor-ledger.md`** *(Full profile)* — typed `REVISIT` anchors
  linked to a single ledger, enforced by a lint.
  *Open when:* one fact is restated across layers and you need a sweep set.
  *Carry-away:* a `TODO` yields no sweep set; a typed anchor + ledger row gives you
  every site that must change together.

- **`0008-doc-size-disposition.md`** — calibrate doc-size limits by doc *kind*;
  give a living enforced standard its own home.
  *Open when:* a synthesis doc "exceeds" a cap, or a standard has no clear home.
  *Carry-away:* the real bar is "synthesize, don't dump," verified by audit, not a
  line ceiling; fix the rule when the rule is wrong, the work when the work is.
