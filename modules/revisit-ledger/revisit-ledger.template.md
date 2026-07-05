---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, revisit, cross-layer, ledger]
related: [index, CONVENTIONS]
---

# REVISIT ledger — cross-layer change-intent anchors

Single source of truth for every `REVISIT(RV-NNN <class>)` anchor in the tree.
An anchor marks a spot that will need to change again later — usually because it
is one end of a **cross-layer surface** (two or more places that must move in
lockstep). The ledger row is the map of ALL the sites that move together: the
**sweep set**. Consult a row before changing any code it anchors.

Install this file at `.agent-docs/reference/revisit-ledger.md`. `revisit-lint.sh`
keeps it in sync with the anchors in code (orphan markers and dangling rows
fail; touching an anchored file prints a reminder).

> Seeded empty below — the lint passes on an empty ledger with no anchors. Add
> your first row the same change you add your first anchor.

## The marker grammar

In a code comment, at the site that must be revisited:

```
REVISIT(RV-001 twin:on-disk-schema): bump this validator when the schema adds a field
```

Classes:

| Class | Meaning | Resolves when |
|---|---|---|
| `until:<event>` | interim code that stays until `<event>` happens | `<event>` occurs → remove marker + retire row |
| `retire-at:<event>` | throwaway scaffolding to delete at `<event>` | `<event>` occurs → delete code + retire row |
| `twin:<counterpart>` | one end of a surface that must change in lockstep with `<counterpart>` in another layer | the twin surfaces are unified / one side is removed |
| `claim:<fact-id>` | one fact restated across several layers; keep the copies consistent | the fact is single-sourced |

## Same-change rule

- Creating an anchored surface ⇒ add the marker(s) **and** an `## Open` row, in
  the same change.
- Resolving it ⇒ remove the marker(s) **and** move the row to `## Retired` with
  the landing commit — in the same change.

The row's **Sites** column is the sweep set: the exhaustive list of places that
change together. A wrong or incomplete sweep set is worse than none.

---

## Open

| RV-id | Class | Intent | Sites (the sweep set) | Opened |
|---|---|---|---|---|
| <!-- RV-001 | twin:example | one-line intent | path/a.ext:120 · path/b.ext:44 | YYYY-MM-DD --> |

## Retired

| RV-id | Class | Intent | Resolved by | Retired |
|---|---|---|---|---|
| <!-- RV-000 | until:example | one-line intent | commit <sha> / ADR-NNNN | YYYY-MM-DD --> |
