---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [module, revisit, cross-layer, opt-in]
related: [revisit-ledger.template, revisit-lint]
---

# Module: revisit-ledger (Full-profile, OPT-IN)

**Not wired by default.** Enable this only if your codebase has **cross-layer
surfaces that must change together** — places in different layers that are
silently coupled, where changing one and forgetting the other is a recurring
bug class. Examples:

- an on-disk / wire **schema** and the code that (de)serializes it,
- a **grammar / IDL** and the generated types + the hand-written code around them,
- a public **contract / interface** and every implementation of it,
- one **fact** (a limit, a magic constant, an enum's variants) restated in more
  than one file.

If your code has none of these, skip this module — it adds ceremony for no gain.

## What it gives you

A **typed change-intent marker** you drop in a comment at the coupled site:

```
REVISIT(RV-NNN <class>): <one-line intent>
```

and a **ledger** (`.agent-docs/reference/revisit-ledger.md`) whose row for each
`RV-NNN` lists the *complete set of sites that move together* — the **sweep
set**. Before you change anchored code, you read the row and change every site
it names, together. The discipline turns an invisible coupling into a visible,
greppable, lint-checked one.

The four classes (full grammar in `revisit-ledger.template.md`):

| Class | Use for |
|---|---|
| `until:<event>` | interim code that lifts when some event happens |
| `retire-at:<event>` | throwaway scaffolding to delete at some event |
| `twin:<counterpart>` | one end of a lockstep cross-layer surface |
| `claim:<fact-id>` | one fact restated across layers; keep the copies in sync |

## The same-change rule

- **Create** an anchored surface ⇒ add the marker(s) **and** an `## Open` ledger
  row, in the same change.
- **Resolve** it ⇒ remove the marker(s) **and** move the row to `## Retired`
  with the landing commit, in the same change.

`revisit-lint.sh` enforces the invariant both ways:

- **orphan marker** (an `RV-id` in code with no ledger row) → **fails** the commit;
- **dangling open row** (an Open row whose anchors were all deleted) → **fails**;
- **staged file carries anchors** → prints an INFO reminder with the row's sweep
  set (never fails) so you consult it before landing the change.

## Install (opt-in)

1. Copy the ledger template into place and clear the seeded comments as you add
   real rows:

   ```sh
   mkdir -p .agent-docs/reference
   cp modules/revisit-ledger/revisit-ledger.template.md \
      .agent-docs/reference/revisit-ledger.md
   ```

2. Install the lint script wherever you keep repo scripts, e.g.:

   ```sh
   mkdir -p scripts
   cp modules/revisit-ledger/revisit-lint.sh scripts/revisit-lint.sh
   chmod +x scripts/revisit-lint.sh
   ```

3. **Wire it into the pre-commit gate** (this is the opt-in step — the base
   `.githooks/pre-commit` does NOT call it). Add this just before the final
   `exit "$rc"` in `.githooks/pre-commit`:

   ```sh
   # revisit-lint (opt-in module): REVISIT anchor <-> ledger sync.
   if [ -x scripts/revisit-lint.sh ]; then
     echo "pre-commit: revisit-lint (marker<->ledger sync)"
     bash scripts/revisit-lint.sh || rc=1
   fi
   ```

   (adjust the path if you installed the script elsewhere.)

4. Add a row to the ledger's `index.md` sibling if your `reference/` dir has one,
   so the index-completeness lint stays clean.

The lint is **grep-based and offline**, so it is cheap to run on every commit.
It is a no-op (exit 0) until you have both a ledger and at least one anchor —
enabling the module before you have any cross-layer surfaces costs nothing.

## Undo

Remove the wiring block from `.githooks/pre-commit`, delete
`scripts/revisit-lint.sh`, and (if you never adopted anchors) delete
`.agent-docs/reference/revisit-ledger.md`. No other state is kept.
