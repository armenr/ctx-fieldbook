---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0004-operational-hooks, 0005-per-directory-routing-indexes]
tags: [meta, framework, revisit]
---

# ADR-0007 — REVISIT anchor + ledger + revisit-lint

> Framework rationale that ships with the kit (Full profile). Explains why
> "revisit later" intent lives in typed anchors linked to a single ledger with a
> linter, instead of scattered TODO comments.

## Context

`TODO: revisit this later` comments rot and get lost. Worse is **cross-layer
drift**: one fact restated across several layers means you change one site without
seeing its siblings. Every codebase has these surfaces — an interface contract
restated across its producers and consumers; a schema restated across its builder
and its query callers; an invariant restated across a write path and its recovery
or rollback path; a versioned dependency-feature table restated across the code
paths that branch on it. Change one, forget the rest, and the layers silently
disagree.

## Alternatives Considered

- **Plain `TODO` / `FIXME` comments.** Rejected: unstructured, unsearchable *as a
  set*, and they yield no sweep set — you cannot enumerate every site that must
  change together, which is the whole point.
- **A cross-repo scan.** Rejected: such a scan exists only to repair the drift a
  multi-repo split *causes*; a single in-repo store makes it unnecessary. Adding
  the scan would import a problem the architecture already avoids.
- **Typed code-comment anchors linked to a single tracked ledger, enforced by a
  linter.** Chosen.

## Decision

Typed markers in code comments — `REVISIT(RV-NNN <class>): <intent>` — each linked
to a single ledger (`revisit-ledger.md`, with `## Open` / `## Retired` tables).
Classes:

- **`until:`** — interim, lifts at a named event.
- **`retire-at:`** — throwaway, remove at a named point.
- **`twin:`** — a cross-layer lockstep surface (siblings that must change
  together).
- **`claim:`** — one fact restated across layers.

A `revisit-lint` runs as a pre-commit gate: **orphan markers** (a marker in code
with no ledger row) and **dangling open rows** (a row with no marker) both **fail
the commit**. For any staged anchored file, the lint prints its ledger row — the
**sweep set** to consult before changing anchored code. **Same-change rule:** the
marker and its ledger row are created together and resolved together; the row's
site list is the sweep set, so a stale site list is worse than none.

## Consequences

- **+** Parse-able "revisit-this" intent plus a guaranteed sweep set before you
  touch anchored code; the cross-layer drift surfaces get a linter; the `twin:`
  anchors feed the IMPL→WIRED traceability gate.
- **−** The same-change discipline has to be honored, and site lists must be kept
  accurate — an inaccurate sweep set gives false confidence.

## Related

- ADR-0004 (pre-commit enforcement) · ADR-0005 (traceability consumes `twin:`
  anchors)
- `revisit-ledger.md` · standing rules (REVISIT section)
