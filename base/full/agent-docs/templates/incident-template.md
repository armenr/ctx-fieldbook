<!--
Incident template per CONVENTIONS-full-addendum §A (incidents/) + §B (INC-NNN spine) + core §8.
A post-mortem. APPEND-ONLY; incident genealogy feeds `lessons/` + hardens into rules.
Instantiate to `.agent-docs/incidents/YYYY-MM-DD-<slug>.md`.
Delete this comment block + inline guidance once filled in.
-->

---
provenance: llm-reviewed
template-version: 1.0.0
incident-id: INC-NNN             # §B spine
created: <YYYY-MM-DD>             # LOCAL date (§2)
last-modified: <YYYY-MM-DD>
work-unit: WU-NNNN               # the work-unit this incident occurred under, if any
tags: [incident]
---

# INC-NNN — <what broke, in a sentence>

## When
<!-- Timestamp / window the incident occupied. -->

## Impact
<!-- What was affected and how badly. Blunt, no minimizing. -->

## Detection
<!-- How it was noticed — and how long that took (the detection gap is itself a finding). -->

## Timeline
<!-- Ordered sequence of what happened, with timestamps. -->

## Root cause
<!-- The actual underlying cause, not the surface symptom. Investigate WHY, not just WHAT. -->

## Remediation
<!-- What was done to resolve it, with evidence-on-disk (commits, SHAs, §7.3). -->

## Prevention
<!-- The durable change that stops recurrence — link the lesson (LP-NNN) / rule / ADR it produced. -->
