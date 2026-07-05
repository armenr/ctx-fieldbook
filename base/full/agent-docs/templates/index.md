---
provenance: kit-template
template-version: 1.0.0
created: 2026-07-03
last-modified: 2026-07-03
tags: [index, templates, full-profile]
related: [CONVENTIONS-full-addendum]
---

# templates/ (Full profile) — index

The **Full-profile** scaffolds — the ones a project turns on once it fans work out to sub-agents and
needs production-reachability proof. These are ADDITIONS to the Minimal-profile templates (ADR,
checkpoint, handoff, memory, lesson, index); see the Minimal `templates/index.md` for those. Each
carries a `template-version` (CONVENTIONS.md §8). **Instantiate from the template — never hand-copy.**

## Fanning work out to sub-agents

- 🔨 `dispatch-charter-template.md` — a scoped, one-file-one-owner sub-agent / workflow-step spec (`dispatch/`, `FR-NNNN`).
  **Open when:** decomposing a WU into a parallel wave; before dispatching any builder.
  **Carry-away:** one-file-one-owner + a named wiring-proof target + a clean-context verifier gate (reviewer ≠ builder). (Addendum §D)

## Proving investigations

- 🔨 `research-synthesis-template.md` — the sealed synthesis of a tiered investigation (`research/<R-id>/synthesis.md`).
  **Open when:** an investigation's conclusion will feed a decision.
  **Carry-away:** synthesis is the only Tier-2 surface; every decision-critical claim is currency-checked against current-year PRIMARY docs. (Addendum §E)

## Operations & failure

- 🔨 `runbook-template.md` — an operational procedure (`runbooks/`).
  **Open when:** a repeatable, blast-radius-bearing procedure needs a read-before-run script.
  **Carry-away:** state blast radius + reversibility + rollback up front.
- 🔨 `incident-template.md` — a post-mortem (`incidents/`, `INC-NNN`).
  **Open when:** something broke and the root cause + prevention must be captured.
  **Carry-away:** root cause, not symptom; link the prevention (lesson / rule / ADR).
- 🔨 `experiment-template.md` — a throwaway spike with a captured outcome (`experiments/`).
  **Open when:** probing an unknown before committing to a design.
  **Carry-away:** the spike is scratch — PROMOTE durable findings to `reference/`.
