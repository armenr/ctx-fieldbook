<!--
Research-synthesis template per CONVENTIONS-full-addendum §E (research pipeline tiers) + §8.
`synthesis.md` is the ONLY Tier-2-loaded surface of a research investigation — the tiers that feed it
(00-landscape.md → NN-<track>.md → adversarial.md) stay in the `research/<R-id>-<slug>/` subdir and
are NOT loaded wholesale; callers load THIS file and reference by R-id.
Instantiate to `.agent-docs/research/<R-id>-<slug>/synthesis.md`. UPDATE-IN-PLACE until sealed.
Currency-check every decision-critical claim against CURRENT-YEAR PRIMARY docs, never training data.
Delete this comment block + inline guidance once filled in.
-->

---
provenance: llm-draft
status: draft                     # draft → sealed (once the investigation is closed)
template-version: 1.0.0
created: <YYYY-MM-DD>             # LOCAL date (§2)
last-modified: <YYYY-MM-DD>
work-unit: WU-NNNN
sources: [00-landscape.md, NN-<track>.md, adversarial.md]   # the tiers this synthesis derives FROM
tags: [research]
---

# R-NNNN — <the research question> · synthesis

## Verdict
<!-- The answer, with an explicit confidence level. Lead with it. -->

## Evidence (on-disk, primary-source)
<!-- Each decision-critical claim → its PRIMARY source (current-year) → the adversarial re-check
     result. The adversarial tier is a clean-context skeptic who refuted-or-confirmed each claim (§E). -->
- claim → primary source (current-year) → adversarial re-check result

## Residual gaps / what we did NOT resolve
<!-- Name the open edges honestly — an unresolved gap surfaced beats a false-complete. -->

## Decisions influenced
<!-- ADR-NNNN if this fed a decision. Reference by ID, don't restate the decision. -->
