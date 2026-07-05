---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, incidents]
related: [CONVENTIONS]
---

# incidents/ — routing catalog

Post-mortems, date-prefixed. Incident genealogy feeds `lessons/` + the rules. APPEND-ONLY. Schema
authority: `../CONVENTIONS.md` (incident template); ID `INC-NNN`.

> **Incident → lesson → rule genealogy.** Every durable guardrail traces back to a dated,
> recurrence-counted incident (e.g. a lost-worktree footgun → the cwd-check-before-mutation rule). An
> incident is where a guardrail earns its existence — "rules without enforcement are decorative."

## Entry purpose + naming

- **Purpose:** a post-mortem capturing root cause + prevention, so the failure becomes a guardrail
  rather than a recurrence.
- **Filename:** `incidents/YYYY-MM-DD-<slug>.md`.
- **Write-discipline:** APPEND-ONLY.

## Entry SCHEMA (body)

When · Impact · Detection · Timeline · Root cause · Remediation · **Prevention** (the link to the
`lessons/` entry or the hook/rule that now blocks recurrence — with a recurrence count if the pattern
repeats).

## Incidents

<!-- EXAMPLE (delete this block on the first real incident):
- `2026-07-03-example-slug.md` — **Open when:** <the failure class recurs / you're wiring a guardrail
  against it>. **Carry-away:** <root cause in one sentence + the guardrail that now prevents it>.
-->

## Maintenance

APPEND-ONLY; adding an incident adds a row here in the same change.
