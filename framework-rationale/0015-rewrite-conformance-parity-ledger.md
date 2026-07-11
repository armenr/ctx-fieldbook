---
provenance: kit-template
status: accepted
created: 2026-07-11
last-modified: 2026-07-11
supersedes: []
superseded-by: null
related: [0010-reviews-findings-home, 0001-in-repo-context-system]
tags: [meta, framework, rewrite, conformance, parity, traceability, opt-in]
---

# ADR-0015 — Rewrite-conformance parity is a separate opt-in ledger (PARITY ≠ WIRED)

> Framework rationale that ships with the kit (Full profile, opt-in module
> `rewrite-conformance`). Explains why a port/rewrite's byte-conformance results
> get their own ledger tier — a **sibling** of `traceability/`, never a column in
> it — and why the module is gated on applicability rather than shipped by default.

## Context

When a project **replaces an existing implementation** — a port to a new
language, a rewrite of a legacy service — "done" acquires a second meaning that
the standard gates do not capture. The work discipline already gates *production
reachability* (`traceability/`, IMPL→WIRED) and already carries the
**oracle-honesty rule** for a conformance suite (`reference/work-discipline.md`:
one suite both the reference and the new implementation must pass, sabotage-proven
non-vacuous). What it does not give the port is a **durable home for the parity
verdicts themselves** — the per-run record of how many golden cases the new
binary reproduces byte-identically, and the sabotage evidence that the harness is
non-vacuous.

The tempting move is to record those verdicts in `traceability/`, since both are
"is this work-unit done?" ledgers. A field port in the fleet ran the full gate
end-to-end — froze its predecessor's wire behavior as a golden corpus, proved the
harness honest by passing the reference first and sabotaging it both directions,
and filed its first parity row **deliberately as PARITY-not-WIRED** — and the
placement question is what this ADR settles.

## Alternatives Considered

- **A (chosen) — a separate opt-in ledger tier, sibling of `traceability/`.** The
  `rewrite-conformance` module ships `parity/` (index + append-only ledger +
  divergence map) plus the golden-corpus discipline. Parity verdicts live there
  and nowhere else.
- **B (the runner-up) — reuse `traceability/`: add a `PARITY` state or a `kind:`
  column to the WIRED ledger.** Genuinely strong: one ledger, no new tier, and a
  work-unit's reachability proof and its conformance proof sit on the same row
  where a reader finds both at once. Rejected on the deciding axis — it conflates
  two orthogonal axes. A `WIRED` row answers *"reachable from production?"*; a
  parity row answers *"byte-identical to the reference?"*. A case can be one
  without the other (a WIRED path with a conformance bug; a passing golden case in
  dead code). Merging them makes "done" ambiguous and **launders a conformance
  claim as a reachability proof** — the reader of a green row cannot tell which
  guarantee it carries. The axes compose better as neighbors than as one column.
- **C — prose-only in `work-discipline.md`, no ledger.** Rejected: the *rules*
  (oracle honesty, sabotage non-vacuity, freeze-fixtures-not-prose) do belong
  there and already ship — this ADR references, does not restate them. But a
  discipline with no per-run ledger loses the record: which slice passed how many
  cases, and the sabotage proof, dissolve into log prose — the same "findings to
  disk or they don't exist" failure the reviews tier (ADR-0010) exists to prevent.
- **D — ship it as a core Full tier, like `traceability/`.** Rejected on
  applicability: only a project with a **predecessor to conform to** has an
  oracle. A greenfield install would carry an empty `parity/` tier with nothing to
  gate — dead ceremony. Gating it as an opt-in module (like `revisit-ledger`,
  `recurrence-guard`) attaches the cost only where the rewrite shape is present.
- **E — DEFER; keep the 7-line placeholder.** Rejected: the defer's own recorded
  flip condition fired — a field port ran the discipline through to a certified,
  triple-gated Wave-1 parity ledger with sabotage-proven non-vacuity — which
  pre-authorized the harvest at n=1 ("its real parity ledger becomes the kit
  exemplar").

**Deciding axis:** *axis-orthogonality* — PARITY (byte-conformance against an
oracle) and WIRED (reachability from a production entrypoint) answer different
questions, so a single ledger that carries both makes "done" ambiguous and lets
one proof masquerade as the other. Keep the axes on separate ledgers; let them
cross-reference, never merge.

**Flip-condition:** if a second adopter shows the two ledgers genuinely share a
key and lifecycle — or a non-port conformance need appears (two live
implementations kept in lockstep with no predecessor/successor relation) — revisit
merging into one tier with an explicit axis column. Separately, if a class of
rewrites produces output that is non-deterministic by nature (normalization cannot
close), the module needs a property-based-oracle variant rather than golden
byte-fixtures.

## Prior art / reference

Distilled from one field port that practiced the gate end-to-end (n=1 as a
*practiced* gate; the harvest was pre-authorized at n=1 by the defer's flip
condition). The reachability sibling it defers to is the shipped `traceability/`
tier (ADR-0001 filing-cabinet categories); the oracle-honesty and
bootstrap-canary rules it builds on ship in `reference/work-discipline.md`. The
"findings to disk" precedent for insisting on a durable ledger over prose is
ADR-0010 (reviews).

## Decision

Ship `rewrite-conformance` as a **Full-profile opt-in module**. It provides the
`parity/` ledger tier (index, append-only ledger, divergence map) and codifies
four rules: (1) the golden corpus IS the contract — freeze executable byte
fixtures, not prose, and re-recording is a contract-change event; (2)
normalization is a closed, value-discriminating set proven closed both ways; (3)
oracle honesty via a swap-in binary seam with the reference passing first
(reference-not-restate to the work-discipline rule); (4) **PARITY ≠ WIRED** —
parity verdicts live in the sibling ledger, never in `traceability/`. Divergence
is recorded honestly in a parity map with a reachability verdict per row; a
divergence that becomes reachable becomes a bug. The module is **not** wired by
default — greenfield projects skip it.

## Consequences

- **+** A port has a durable, auditable home for conformance verdicts and their
  sabotage proof, distinct from the reachability ledger; "done" stays
  unambiguous because each ledger carries exactly one axis.
- **+** The discipline composes with the existing loop: the corpus + harness are
  the bootstrap unit's deliverable, the parity gate runs inside G1 conformance
  falsifiers, and no new hook or default-tier cost is added.
- **−** One more opt-in tier and a placement invariant a reviewer must respect
  (parity never in `traceability/`) — worth stating once in a project ADR at
  install. And the golden-corpus discipline is only as honest as its
  normalization set: an over-loose normalizer silently widens the contract, so
  the closed-both-ways proof is not optional.
- **−** Applicability is narrow by construction; the module is dead weight if
  enabled without a predecessor to conform to — hence opt-in, not core.

## Related

- ADR-0010 (reviews — the "durable ledger over prose" precedent) · ADR-0001 (the
  filing-cabinet categories `parity/` slots beside `traceability/`).
- `reference/work-discipline.md` — §oracle-honesty, §bootstrap-canary,
  §scale-down-floor (the loop this gate runs inside) · the module
  `rewrite-conformance/README.md` · `traceability/` (the WIRED sibling).
