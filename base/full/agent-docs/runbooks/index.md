---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, index, routing, runbooks]
related: [CONVENTIONS]
---

# runbooks/ — routing catalog

Operational procedures — **read end-to-end before running them.** UPDATE-IN-PLACE. Schema authority:
`../CONVENTIONS.md` (runbook template).

> **Runbook vs reference vs lesson.** A *runbook* is a HOW-to-run procedure with a blast radius and a
> rollback. A *reference* is a WHAT-IS fact. A *lesson* is a behavioral rule. If it has steps you
> execute against a live system, it's a runbook.

## Entry purpose + naming

- **Purpose:** a repeatable operational procedure (build, migrate, recover) with its safety envelope
  stated up front.
- **Filename:** `runbooks/<kebab-procedure>.md`.
- **Write-discipline:** UPDATE-IN-PLACE.

## Entry SCHEMA (body)

Use when · Prerequisites · Estimated time · **Blast radius** · **Reversibility** · Steps ·
Verification · **Rollback**. Destructive procedures require an operator confirm at run time — the
runbook states this, it does not pre-authorize.

## Runbooks

<!-- EXAMPLE (delete this block on the first real runbook):
- **`example-procedure.md`** — <one-line what it does>.
  - *Open when:* <the situation that calls for this procedure>.
  - *Carry-away:* <the safety envelope + the load-bearing step + how to roll back>.
-->

## Maintenance

UPDATE-IN-PLACE; adding/retiring a runbook updates this index in the same change.
