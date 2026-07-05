---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0001-in-repo-context-system, 0004-operational-hooks]
tags: [meta, framework, indexes]
---

# ADR-0005 — Per-directory routing indexes + completeness lint

> Framework rationale that ships with the kit. Explains why knowledge is reached
> by routing through per-directory indexes rather than browsing raw folders.

## Context

A single flat catalog rots, and agents browse raw directory listings — missing
the one doc they actually want and loading three they don't. A drifting catalog
(docs added or removed without updating it) is worse than none: it silently
misleads. Per-directory indexes are the structural replacement for crude context
caps ("read at most N state files per turn") — the goal is to route to the *one*
right doc, not to cap how many you open blindly.

## Alternatives Considered

- **One root catalog.** Rejected: it rots, does not scale, and offers no per-
  directory routing — every lookup pays to scan the whole thing.
- **Numeric context caps** ("≤ N files per turn"). Rejected as the *primary*
  mechanism: they preserved a good *intent* ("read with intent, synthesize
  immediately") but were a workaround, not an information architecture. A cap
  limits volume without improving aim; a per-directory index discharges the same
  intent structurally by making the *right* doc easy to find.
- **Per-directory routing indexes + a presence lint to keep them honest.** Chosen.

## Decision

Each **populated** content directory carries its own `index.md` routing catalog.
Per entry: **what-it-holds** + **Open when:** (the trigger to reach for it) +
**Carry-away:** (the one fact to retain — and it must be traceable to the source
doc, never approximated from memory). A dispatch-charter index is a ledger
*table*, not prose. The root `index.md` stays **directory-level only** — it names
directories, not documents.

A dependency-free presence lint compares each directory's on-disk `*.md` set
against the backtick tokens in its `index.md` (flagging a missing index, an
unindexed doc, or a phantom row). It runs **warn** at SessionStart, is fixed as a
byproduct at `/flush` (touched directories) and `/handoff` (all), and offers a
`--strict` mode for CI. **Same-change rule:** adding or retiring a doc updates the
directory index in the same change.

## Consequences

- **+** Routable knowledge; no orphan or phantom drift; the lint is cheap (plain
  shell, no heavy dependencies).
- **−** The same-change discipline has to be honored; the lint is presence-only —
  it cannot check that the prose is *fresh*, only that entries exist.

## Related

- ADR-0001 (the system) · ADR-0004 (SessionStart warn injection)
- `CONVENTIONS.md` (index template + lint rules) · `.claude/rules/agent-docs.md`
