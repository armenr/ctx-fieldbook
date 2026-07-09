---
provenance: kit-template
status: accepted
created: 2026-07-09
last-modified: 2026-07-09
related: [0001-in-repo-context-system, 0003-lessons-learned-ledger]
tags: [meta, framework, reviews, findings, disposition]
---

# ADR-0010 — Reviews get their own home (`reviews/` + `REV-NNN`)

> Framework rationale that ships with the kit (Standard profile). Explains why
> review findings are a first-class filing-cabinet category with a typed ID and
> a per-finding disposition + test-obligation — and why every existing home for
> them is the wrong one.

## Context

An adversarial review pass — a red-team of a design, a fresh-context verifier
run, a security audit — produces the highest-value knowledge the system
generates: enumerated, severity-ranked, adversarially-verified defects. Without
a home of their own, those findings dissolve into log prose ("15 findings"
becomes one sentence), where individual findings are unaddressable and
effectively lost — a direct violation of the standing rules' "findings to disk
or they don't exist" and "every finding gets a durable home AND an explicit
disposition." The forcing constraint: a finding is a *distinct artifact type*
with its own lifecycle (`open → dispositioned → fixed | deferred | wontfix`)
and its own join needs — a finding cites the ADR it amends, the `OQ-` it
becomes, the work-unit it hits, and the **named test that binds it**; those
cite back. None of the existing dirs model that axis.

## Alternatives Considered

- **Status quo — narrate findings in `log.md`.** Rejected: lossy by
  construction. Prose has no stable per-finding ID, no disposition field, no
  test-obligation column; a two-dozen-finding review becomes one sentence,
  unrecoverable at the granularity a test needs.
- **Fold into `checkpoints/`.** Rejected: checkpoints are WRITE-ONLY zero-loss
  sitreps keyed to a session moment, never edited after write (CONVENTIONS §6).
  A findings ledger must *evolve* as each finding is fixed or deferred —
  mutable disposition tracking is the opposite of write-once. A checkpoint can
  *reference* a review; it can't *be* one.
- **Fold into `traceability/`.** Rejected: traceability is a different axis —
  IMPL→WIRED production-reachability per unit. A finding is not a wiring-state
  row; conflating "is this code reachable" with "did the review find a defect
  here" muddies both ledgers.
- **Fold into `decisions/` (ADRs).** Rejected: a review is *evidence that
  feeds* decisions, not a decision. Findings are inputs; an ADR amendment is
  the ruling. Review → recommends → ADR amendment is the correct direction;
  making the review an ADR inverts it — and the two have different lifecycles
  (a finding closes; an accepted ADR stands until superseded).
- **Fold into `research/`.** Rejected: research is *external* multi-source
  investigation → synthesis, currency-checked against primary docs. A review is
  an *internal* adversarial audit of YOUR artifacts against YOUR spec.
  Different provenance, evidence model, and lifecycle.
- **A dedicated `reviews/` dir + `REV-NNN` typed ID (with per-finding
  `REV-NNN-FNN` sub-IDs).** Chosen — it models the finding's own lifecycle and
  join needs, and slots beside the other join-key dirs the ID spine already
  anticipates.

**Deciding axis:** the finding's *lifecycle* — mutable per-finding dispositions
that close one by one. Every rejected home is either immutable (checkpoints),
tracks a different axis (traceability), has a different lifecycle (decisions),
or has different provenance (research); only a dedicated ledger fits.

**Flip-condition:** if a project genuinely never runs independent review passes
(no adversarial separation to feed it), the dir is dead weight — drop it rather
than carry an empty ceremony.

## Decision

Add `reviews/` as a managed content dir with its own `index.md`. Each review
pass is one `REV-NNN` report from the review template, keyed to the work-unit
it examines. Every finding gets a stable `REV-NNN-FNN` sub-ID, a severity, an
explicit disposition (the disposition contract the standing rules already
mandate — reference, don't restate), an x-ref to the ADR/OQ/unit it touches,
and a **test-obligation**: the named test that binds it, or `unbound → <owner>`.
The test-obligation column is what turns "these findings are worth writing
tests against" from an intention into a queryable backlog — each `unbound` row
is a listed debt with an owner, not tribal memory. Write-discipline:
APPEND-ONLY for new reports; a report's finding *dispositions* update in place
as findings resolve — the report is the living ledger for its findings until
all are closed. A review is not "done" at report-write; it is done when every
finding carries a terminal disposition with on-disk evidence.

## Consequences

- **+** No finding is ever silently dropped: the standing rules' full-
  disposition contract gets a dir it can mechanically point at, and the test
  backlog becomes queryable.
- **+** Reviews compose with the existing ID spine: `REV-` joins the work-unit,
  cites `ADR-`/`OQ-`, and a fixed finding carries its commit SHA as evidence.
- **−** One more managed dir whose index must be updated in the same change,
  and the bidirectional x-ref discipline (a deferred finding updates the `OQ-`
  it cites; a test names the finding it binds) has to be honored or the joins
  rot.

## Related

- ADR-0001 (the context system and its filing-cabinet categories) · ADR-0003
  (the lessons ledger — the precedent for a typed ledger with a disposition
  lifecycle)
- Standing rules, "Findings, decisions & review feedback to disk" (the
  disposition contract) · `CONVENTIONS.md` §4 (the typed-ID spine) · the review
  template · `reviews/index.md`
