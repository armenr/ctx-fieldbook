---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, research]
related: [CONVENTIONS]
---

# research/ — routing catalog

One `research/<R-id>-<slug>/` dir per investigation, each following codified pipeline tiers. The
`<R-id>/synthesis.md` is the **only Tier-2-loaded surface** — callers load it and reference-by-`R-id`;
raw tracks stay in the subdir. Schema authority: `../CONVENTIONS.md`; ID `R-NNNN`.

> **Why this tier exists.** A multi-source investigation whose conclusion feeds a decision needs a
> declared home and an adversarial gate — otherwise the reasoning evaporates and the conclusion is
> untraceable. Currency-check every decision-critical claim against current-year **primary** docs,
> never training data.

## Entry purpose + naming

- **Purpose:** a durable, multi-source, adversarially-verified investigation whose synthesis can feed
  an ADR.
- **Dir naming:** `research/<R-NNNN>-<slug>/`.
- **Write-discipline:** APPEND-ONLY within an `<R-id>`; `<R-id>/synthesis.md` is UPDATE-IN-PLACE until
  sealed.

## Entry SCHEMA — the pipeline tiers (one file per tier)

All tier files live INSIDE the `<R-id>/` subdir (they are never direct children of `research/`, so the
index lint does not read them as in-dir entries):

| File | Tier | Holds |
|---|---|---|
| `<R-id>/00-landscape.md` | broad survey | the initial scan of the problem space |
| `<R-id>/NN-<track>.md` | parallel deep track | one file per track |
| `<R-id>/adversarial.md` | clean-context skeptic | re-checks the tracks' decision-critical claims against PRIMARY sources |
| `<R-id>/synthesis.md` | **Tier-2 surface** | verdict + confidence + evidence-on-disk + residual gaps + decisions influenced |

The verifier is a **clean-context sub-agent** with no authorship stake — the executor never audits its
own research.

## Investigations

<!-- EXAMPLE (delete this block on the first real investigation):
- 🔬 `R-0001-example-topic/` → **`R-0001-example-topic/synthesis.md`** — **Open when:** "<the question
  the investigation answered>". **Carry-away:** <the verdict + confidence + which ADR/decision it
  feeds>. `sealed` / `draft`.
-->

## Maintenance

Add an `R-id` row to this index when an investigation starts; mark it `sealed` in
`<R-id>/synthesis.md` front-matter when complete (same-change rule).
