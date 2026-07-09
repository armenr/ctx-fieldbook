---
provenance: kit-template
status: accepted
created: 2026-07-09
last-modified: 2026-07-09
related: [0005-per-directory-routing-indexes, 0007-revisit-anchor-ledger]
tags: [meta, framework, sweep, cycle-start, traceability]
---

# ADR-0009 — Inbound-reference sweep at cycle start (`scripts/wu-refs.sh`)

> Framework rationale that ships with the kit (Standard profile). Explains why
> each work cycle opens with a mechanical grep-sweep for everything that
> *references or awaits* the unit being started — gather-then-triage — instead
> of trusting any one obligation ledger to be complete.

## Context

Obligations parked against a *future* work-unit or stage accumulate scattered
across the context system: a `DEFER→` row in the traceability ledger, a gating
`OQ`, a `REVISIT` anchor that lifts at that unit, an ADR note ("the next unit
authors the DTOs"), a review finding, a log "next:" line, a code comment. The
traceability ledger is the *intended* single obligation store — but obligations
demonstrably leak into all those other surfaces, and any ledger is only as
complete as the discipline that fed it. The recon-first rule (standing rules)
covers a unit's *outward* scope — what it touches — but nothing gathers the
*inward* references — what awaits it — so an obligation someone parked against
the unit can silently go unaddressed when its cycle finally starts.

## Alternatives Considered

- **A (chosen) — a grep-sweep script run at cycle start.**
  `scripts/wu-refs.sh <WU> [stage]` gathers every reference across grouped
  locations — traceability, open-questions, revisit-ledger, decisions, reviews,
  dogfood, work-plan/status, log, dispatch-charters, incidents, a catch-all over
  the rest of `.agent-docs/`, and code outside it — then the human/LLM triages
  each hit. Cheap, catch-all, mechanical.
- **B (the runner-up) — a strict obligation REGISTRY + a completeness lint.**
  Every forward obligation MUST be registered in one doc, enforced by a lint.
  Genuinely stronger — a real single source of truth, machine-checkable
  completeness, no triage noise. Rejected because it still depends on discipline
  to *register*: an unregistered obligation is invisible to a lint, whereas the
  grep catches unregistered ones *by construction*; and it is heavier. The two
  compose: the ledger is the intended store, the sweep is the defense-in-depth.
  If the ledger were perfectly disciplined the sweep would be redundant — but it
  isn't, which is exactly the point.
- **C — rely on the traceability ledger alone.** Rejected: obligations
  demonstrably leak; the ledger is only as complete as discipline, and rules
  without enforcement are decorative (ADR-0004).
- **D — ad-hoc manual grep each cycle.** Rejected: not consistent or repeatable;
  a script standardizes the location groups (so none is forgotten) and is
  greppable the same way every time.

**Deciding axis:** *catch-what-leaked, cheaply* — a mechanical defense-in-depth
that assumes omission over a rigorous store that assumes discipline. A cheap
sweep that catches the forgotten obligation beats a strict registry that is only
as good as the person who remembered to register.

**Flip-condition:** if obligations grow numerous enough that grep-triage is
noisy, graduate to Option B (a structured registry + a completeness lint) with
this sweep demoted to the audit that checks the registry.

## Decision

Ship `scripts/wu-refs.sh <WU/unit id> [stage-token]` — `git grep --untracked`
(so *in-flight, uncommitted* files like a just-written ledger or review are
swept; `.gitignore` still respected), grouped by location with a catch-all so no
`.agent-docs` dir is ever silently unswept. Run it at **cycle start as the
inward companion to recon-first** (the standing rules carry the operational
contract). It only GATHERS; the operator/LLM triages each hit: satisfied ·
do-this-cycle · unexpected→investigate · stale→remove.

## Consequences

- **+** Nothing parked against a unit/stage can silently hide at cycle start;
  cheap (one command, read-only); catches obligations in untracked/in-flight
  files a plain `git grep` skips.
- **−** It GATHERS, it does not TRIAGE — every hit must be classified, and some
  are noise to dismiss. And a safety sweep must itself be tested: the original
  shipped with a reserved-shell-variable bug that made it silently report "no
  references" — *the exact silent-under-report failure it exists to prevent* —
  caught only by running it against a unit with known references. A safety tool
  you don't test is worse than none.

## Related

- ADR-0005 (per-directory routing indexes — the surfaces the sweep walks) ·
  ADR-0007 (`REVISIT` anchor + ledger — a sibling "gather the sweep set"
  discipline)
- Standing rules, "Cycle start — scope recon outward, reference sweep inward" (the
  integration point) · `scripts/wu-refs.sh`
