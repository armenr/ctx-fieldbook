---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
tags: [meta, index, routing, reference]
related: [CONVENTIONS]
---

# reference/ — routing catalog

Stable **WHAT-IS** facts: architecture notes, inventories, syntheses, validated-version matrices, and
**standards of record** (living, agent-enforced standards). Tier-2 — loaded on demand. UPDATE-IN-PLACE
(rare — these are durable facts, not fleeting state). Schema authority: `../CONVENTIONS.md`.

> **reference/ vs research/ vs decisions/.** `reference/` holds the DISTILLED fact ("this is how the
> auth layer is shaped"). `research/` (Full profile) holds the woven investigation genealogy that
> produced a fact. `decisions/` holds WHY a fork was chosen (an ADR). A fact with no live decision and
> no open investigation belongs here.

## Entry purpose + naming

- **Purpose:** capture a stable, reusable fact so it is not re-derived from scratch each session.
- **Filename:** `reference/<kebab-topic>.md` — a kebab-case topic name (for example an architecture
  overview, or a validated-versions matrix).
- **Write-discipline:** UPDATE-IN-PLACE (rare). A standard-of-record carries `provenance: human`.

## Entry SCHEMA (body)

What-it-is (the fact, stated plainly) · Scope / where it applies · Evidence or source (so it can be
re-verified) · Last-verified (facts drift — date the check) · See also.

## Reference docs

- 🔨 `work-discipline.md` *(Full profile)* — the gated-delivery standard-of-record: INTAKE→G0→DECOMPOSE→per-wave G1/G2/G2-docs/G3→G4, the risk-tier dial, and the scale-down floor.
  **Open when:** starting a work unit, or unsure which gate a piece of work must clear next.
  **Carry-away:** the gate table maps 1:1 onto the dispatch-charter lifecycle — one definition of "done".

<!-- EXAMPLE (delete this block on the first real project-authored reference doc):
- `architecture-overview.md` — **Open when:** you need the big-picture shape before changing a
  subsystem. **Carry-away:** <the one-sentence fact this doc anchors>. (Verified <date>.)
-->

## Maintenance

UPDATE-IN-PLACE; adding/retiring a reference doc updates this index in the same change. Carry-away
claims must be traceable to the source doc — never approximate from memory.
