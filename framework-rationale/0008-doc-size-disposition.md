---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0001-in-repo-context-system, 0005-per-directory-routing-indexes]
tags: [meta, framework, conventions, doc-size, disposition]
---

# ADR-0008 — Doc-size cap recalibration + living-standard disposition

> Framework rationale that ships with the kit. Explains why doc-size limits are
> guidance calibrated to a doc's *kind*, not a single hard line ceiling — and why
> a living enforced standard gets its own home. Included because the same
> tension recurs in any project that writes synthesized research docs.

## Context

A useful synthesis convention is **"one woven genealogy per doc"**: a spine plus
per-track evidence plus preserved dead-ends and walk-backs, folding several dense
source files into ONE mid-tier doc. Such docs are legitimately long — dense
synthesis (many sections, many source citations), not dumps — and each passes a
content-fed audit. Two rule-vs-reality drifts surface once you write enough of
them:

1. **The doc-size cap is mis-calibrated for woven genealogies AND is not lint-
   enforced.** The cap sits in "token-budget guidance," not in the enforced lint
   rules — the lint checks index drift and frontmatter, never line count. So docs
   "exceed" an advisory number that never matched the convention that produced
   them.
2. **There is no disposition category for a living, agent-enforced STANDARD** (as
   opposed to a frozen research-genealogy). An actively-enforced methodology — one
   an agent points to on every recommendation — falls through the gap between
   "reference fact" and "research genealogy."

## Alternatives Considered

- **Keep the tight hard cap; retroactively split the long docs into clusters.**
  Rejected — it fragments coherent genealogies, changes the validated one-doc
  convention, and is significant rework to satisfy a cap that never matched the
  convention and was never enforced. Self-harm.
- **Leave the cap advisory, change nothing.** Rejected — it leaves a documented-
  vs-reality drift that misleads future agents and blocks the "where does the
  standard live" decision. A wrong-but-documented number is worse than a corrected
  one.
- **Make line-count a HARD lint rule at the old numbers.** Rejected — it would
  retro-fail good docs and every future genealogy. The synthesis-not-dump audit is
  the correct quality gate, not a line ceiling.
- **File the living standard under research-genealogy.** Rejected — that
  directory is self-described as frozen genealogy and dead-ends, semantically
  wrong for an actively-enforced standard.
- **Put the full methodology at the reference root under a cap-waiver.** Rejected —
  even under a relaxed cap, a very long root reference doc fights progressive
  disclosure; a standard-vs-evidence split is the better information architecture.

## Decision

1. **Recalibrate the cap by kind.** Woven-genealogy docs get a larger soft/hard
   cap than root reference docs; distilled facts, syntheses, and inventories at
   the reference root stay tight. Over the hard cap ⇒ **split into a subdirectory
   cluster** (index + per-topic docs), never content-drop. The cap stays
   **guidance, not a lint rule** — the real bar is "read with intent, synthesize,
   don't dump," verified by a content-fed audit, not a line ceiling.
2. **No retroactive rework.** Dense, audited genealogies are compliant under the
   recalibrated cap. Fix the rule, not the work — reserved for when the *rule* was
   wrong; where the *work* is wrong, correct the work instead.
3. **Add the "living standard" disposition.** A living, agent-enforced standard →
   the reference root as a **standard-of-record** (`provenance: human`; the
   enforcing agent points to it), distinct from a frozen research-genealogy. When
   such a standard's full body busts the reference cap, **split the standard from
   its evidence** rather than waive the cap.

## Consequences

- The token-budget guidance is calibrated by doc kind; a living-standard
  disposition note is added; the cap is reaffirmed as guidance, not lint-enforced.
- Long-but-dense genealogies are compliant as-is — no rewrites.
- The cap stays unenforced-by-lint; if size drift recurs, a future ADR can add a
  size lint rule.

## Related

- ADR-0001 (the system) · ADR-0005 (progressive disclosure and the index lint)
- `CONVENTIONS.md` (token-budget guidance)
