---
provenance: kit-template
created: 2026-07-09
last-modified: 2026-07-09
tags: [reference, work-discipline, standard-of-record, gates, full-profile]
related: [CONVENTIONS, CONVENTIONS-full-addendum, standing-rules-core, dispatch-charter-template]
---

# Work discipline — the gated delivery loop

The standard-of-record for how a unit of work goes from a raw directive to a merged, wired, verified
change. It is ONE loop; ceremony scales with risk tier, but **the ratchet is non-negotiable at every
tier**. Most of the ratchet is already normative in `.claude/rules/standing-rules-core.md` — this doc
never restates those rules, it sequences them into gates and points back ("core §X" below means that
file's section; a second divergent statement of a rule is worse than none). Roles are the charter
template's authorship roles — **planner · builder · verifier · operator** — and every dispatched
agent runs under the dispatch contract (core §Dispatch contract).

## The loop

```
INTAKE      raw directive → a structured, approved work-unit spec: WU-NNNN + acceptance rules +
            negative spec (the must-not-reproduce list, seeded from lessons/ + incidents/) + open questions
  ▸ G0      the operator approves the normalized spec (a concrete object, not prose); open questions
            answered or explicitly deferred first
DECOMPOSE   spec → waves (a wave = one topological layer of the DAG — addendum §D). Parallelize
            FILE-DISJOINT legs; SERIALIZE the shared surface (interface / schema / registry / twin:
            anchor), one owner per wave. Can't PROVE disjoint ⇒ serial. [recon-first + the
            inbound-reference sweep run BEFORE any build is authored, ownership sets verified
            disjoint pre-launch — core §Cycle start owns both rules]
per wave:
  FIXTURES  author the adversarial test matrix BEFORE any implementation
    ▸ G1    every acceptance rule + negative-spec item → a NAMED test: (a) a RED-on-HEAD falsifier
            (fails on the unmodified tree for the RIGHT reason, on a bug-exposing shape); (b) a
            NON-VACUOUS negative control. REJECT if "a test that goes RED→GREEN" is the whole story.
  IMPLEMENT fan out atomic legs; read-only drafters, exactly ONE mutating builder per charter
            (one-file-one-owner, addendum §D)
  INTEGRATE the orchestrator merges serially, reconciles the shared surface, builds once
    ▸ G2    gates green REPRODUCED FIRSTHAND ({{BUILD_CMD}} · {{LINT_CMD}} · {{FMT_CMD}} · {{TEST_CMD}})
            + the diff FENCED to the named scope + IMPL→WIRED (reachable from a real entrypoint,
            PROVEN via {{CODE_INTEL_TOOL}}, not merely compiled)
  DOCS      a docs pass reconciles docs to the wave diff via the doc-refs sweep
            (gather-then-triage; self-skips only when the sweep reports zero changed referents)
    ▸ G2-docs docs-impact CLEAR — doc-refs sweep run, every row triaged per core §Cycle start,
            stale/uncovered dispositioned; an ADR stub if a decision surfaced
  REVIEW    adversarial reviewer(s), clean context, reviewer ≠ builder
    ▸ G3    every claim "NOT proven" until source shows it; the DAMAGING direction audited; EVERY
            finding dispositioned in reviews/ — no silent drops
ACCEPT      full unit suite → map results to acceptance rules → unit report + traceability row
    ▸ G4    HANDS-ON: the real binary / service / loop run on real inputs and observed doing the
            right thing (green tests ≠ ran it) + an INDEPENDENT fresh-context verifier (≠ builder,
            ≠ in-workflow reviewer) re-derives the risky invariants + operator sign-off → MERGE
            (the operator owns the irreversible step)
```

**The four named gates:** design-first (G0 + an ADR-with-alternatives before acting, CONVENTIONS §5) ·
IMPL→WIRED (G2 — the acceptance bar, not test-pass) · adversarial review (G3 — reviewer ≠ builder,
clean context) · hands-on acceptance (G4 — real run + independent verifier).

**Structural invariants.** A work-unit decomposes as a DAG, not a flat list. Tests and docs distribute
INTO each wave as its definition-of-done — never a trailing "write the tests" / "write the docs" leg.
Every acceptance rule and negative-spec item is pre-bound to a named test id, so ACCEPT is a mechanical
`rule → test-result` join, not a judgment call. (A future structured-spec module may formalize the spec
object; its mapping is fixed in advance: the spec is the WU, its units are FR charters.)

## One definition of done — gates ↔ the charter lifecycle

Full installs run this loop THROUGH the dispatch-charter system (addendum §D). The gates and the
charter `status:` lifecycle are one machine, not two competing definitions of done:

| Gate passed | WU / `FR-NNNN` charter state | Recorded where |
|---|---|---|
| G0 | WU active; decomposition may start | the WU row in `now/work-plan.md` + the approved spec |
| (DECOMPOSE) | charters `drafting` → `dispatched` (brief-back accepted; Part-A-only: on dispatch) | `dispatch-charters/` ledger row |
| G1 | fixtures named in the charter's acceptance criteria | the charter + the named tests on disk |
| G2 / G2-docs | gate verdicts recorded; wiring proven | charter §Gate verdicts (Part-A-only: the run journal) · `traceability/` row · an ADR stub in `decisions/` if a decision surfaced |
| G3 | findings dispositioned; `in-remediation` until clean → `certified` | `reviews/` (`REV-NNN`) + charter §Verifier report |
| G4 | operator sign-off → `merged`; the WU closes | charter §Operator decision · WU row → done · traceability WIRED (or explicit DEFER) |

**"Done" is defined exactly once: G4 passed ⇔ the charter reaches `certified → merged` ⇔ the WU's
`traceability/` row reads WIRED (or a written-down DEFER).** Dispatch persistence is the tooling's job
(addendum §D) — file an FR charter when a genuine scoped work-spec adds value; for work that never
fans out, the gates still run and are recorded against the WU itself.

## The ratchet (pointers — the normative text lives in standing-rules-core.md)

Non-negotiable at EVERY tier. Each line is a pointer to the rule that owns it — never re-derive or
re-word these here:

- **RED-on-HEAD falsifier per behavior change** → core §Quality gates ("a behavior change OWES a test").
- **IMPL→WIRED as the acceptance bar, not test-pass** → core §Quality gates + addendum §C.
- **Reviewer ≠ builder — for designs too** → core §Adversarial separation of duties.
- **EVERY finding dispositioned (FIXED / DEFER / WONTFIX / TRACKED→OQ)** → core §Findings;
  dispositions land in `reviews/`.
- **Firsthand gate reproduction — never trust a sub-agent's self-report** → core §Dispatch contract.
- **Hands-on acceptance for anything runtime-facing** → core §Quality gates.

## Risk-tier dial

Ceremony scales with surface risk; declare the tier in the spec so the loop self-selects instead of
re-arguing it per run. `full` (default for anything destructive, auth-adjacent, data-layer, migration,
shared-surface, or customer-path work): all gates, the adversarial design review iterated to
convergence, the fresh-context G4 verifier, operator gates on interior waves. `light` (a mechanical,
reversible, well-fenced change): the ratchet above still holds in full; the heavy gates drop. The
operator owns where the threshold sits — that is where they spend or save.

## Gate contracts (checklists — adopt as-is; re-voice only in the fork slot below)

### G1 — FIXTURES (before a line of implementation)

- [ ] Every falsifier is RED-on-HEAD for the RIGHT reason — fails on the UNMODIFIED tree because the
      defect is real, not green-by-construction.
- [ ] Each falsifier uses a BUG-EXPOSING fixture shape, not the happy shape that hides it. State the
      shape existing tests missed and why.
- [ ] Every fix carries a NON-VACUOUS negative control, PROVEN non-vacuous: temporarily break the
      fix's guard → the control FAILS → restore.
- [ ] Every acceptance rule maps to a named test id.
- [ ] Every negative-spec item (must-not-reproduce, ledger-referenced) maps to a named test id.
- REJECT if: "we added a test that goes RED→GREEN" is the whole justification. Necessary, not sufficient.

### G2 — INTEGRATE (reproduced by the orchestrator, never asserted by an agent)

- [ ] `{{BUILD_CMD}}` → clean.
- [ ] `{{LINT_CMD}}` → clean (warnings are errors — core §Quality gates).
- [ ] `{{FMT_CMD}}` → clean.
- [ ] `{{TEST_CMD}}` → 0 failed; read the summary line + exit code firsthand.
- [ ] The stack pack's additional gates where defined (a race / concurrency mode, a vet pass, …) —
      see the installed stack `rules.md`.
- [ ] Diff FENCED to the charter's named file scope — no stray files, no out-of-lane edits.
- [ ] IMPL→WIRED: new code REACHABLE from a real entrypoint, PROVEN via `{{CODE_INTEL_TOOL}}`
      (fallback menu: addendum §C) — not merely compiled; row recorded in `traceability/`.
- REJECT if: any lint warning, any dead new code, any scope creep.

### G2-docs — DOCS-IMPACT CLEAR (at the G2→G3 boundary; self-skips only on a zero-referent sweep)

The DOCS pass reconciles the human-doc corpus to the wave diff. Its mechanical half
is the `doc-refs` sweep (the diff-keyed twin of the unit-keyed `wu-refs`, framework-rationale/0014):
it GATHERS candidate claims and pre-tags the fenced lanes — you TRIAGE. It TRIAGES,
never blocks. The five-state triage vocabulary and the two fenced lanes are owned by
core §"Cycle start" (the docs-impact-sweep rule) — this gate does not restate them.

- [ ] Ran `scripts/doc-refs.sh <wave-diff-range>` to gather every human-doc claim
      about the wave's changed referents (degrades to a manual corpus read until the
      sweep is installed — `doc-refs-contract.md`). **Self-skip is earned only by a
      zero-referent sweep** (exit 0, empty over the enabled grammars with the canary
      firing) — never a self-declared "no doc-impact."
- [ ] Every gathered row TRIAGED per core §"Cycle start" (the five states), minus
      the sweep-fenced **baseline** / **retirement** lanes (`baseline-mechanism.md`).
- [ ] Each **stale** row → a doc fix (a `log.md` entry) OR a new `OQ-NNN` / a
      dispositioned `reviews/` finding (`doc-refs-contract.md` §"where a stale row
      files"); each **uncovered** row → coverage added OR a recorded no-impact.
- [ ] The **license-join** check (`doc-refs-contract.md`) resolved where the diff
      touched a license field — small ≠ safe.
- [ ] A decision surfaced → an `ADR-NNNN` stub filed in `decisions/`.
- [ ] An **unverifiable-locally** (cross-repo) claim → a manual / owed-to-me check
      (framework-rationale/0012), never silently passed.
- REJECT if: a public API / CLI flag / config key / protocol behavior changed with a
  **stale** or **uncovered** row left un-triaged and no recorded no-impact verdict.

### G3 — REVIEW (adversarial; reviewer ≠ builder, clean context)

- [ ] The reviewer defaults every claim to "NOT proven" until source shows it.
- [ ] Audited: green-by-construction? scope fence respected? the DAMAGING direction specifically?
      negative-spec compliance?
- [ ] EVERY finding (BLOCKER→NIT) dispositioned in `reviews/` (`REV-NNN`) per core §Findings —
      FIXED / DEFER+reason / WONTFIX+reason / TRACKED→OQ. No silent drops.
- REJECT if: a finding has no durable home, or a damaging path is unaudited.

### G4 — ACCEPT (before merge)

- [ ] Hands-on: the REAL binary / service / loop was run on real inputs and observed doing the right
      thing — not just "tests green."
- [ ] Full unit suite (unit + integration) green, reproduced firsthand.
- [ ] The acceptance-rule → test-result map is complete (every rule has a passing named test).
- [ ] [full tier] An INDEPENDENT verifier (fresh context, ≠ builder, ≠ in-workflow reviewer)
      re-derived the risky invariants and cleared it.
- [ ] Operator sign-off — the operator owns the merge / push and any irreversible step.

## The don't-trust ladder (six rungs; each is a scar)

1. **Don't trust a sub-agent's self-report.** "Gates pass" gets reproduced firsthand (core §Dispatch
   contract).
2. **Don't trust the IDE / language server.** The compiler and test runner are the only oracles —
   when `{{CODE_INTEL_TOOL}}` and `{{BUILD_CMD}}` disagree, the build wins. Always.
3. **Don't trust a relayed finding.** Reproduce the bug firsthand against the live tree; the imagined
   mechanism differs from the real one, and the mechanism dictates the fix.
4. **The reviewer is never the builder — and one review isn't enough.** After in-workflow review, an
   independent fresh-context verifier runs before merge (G4).
5. **Don't trust an "accepted" design on a load-bearing surface.** Such surfaces get design →
   adversarial design review → build, iterated to convergence. The dead-ends are the value.
6. **"Tests green" ≠ "done."** Done = green AND IMPL→WIRED AND hands-on. Green without a falsifier
   proves nothing.

## Safety-by-construction (structure the damaging direction out)

The strongest control is not "review harder" — it is sequencing so the irreversible / damaging
capability (a destructive migration, a real outbound send, a delete / teardown path, an authz-bypass
surface) is introduced **LAST**, behind a guard proven empirically, so earlier waves cannot harm even
if flawed. Build the non-destructive surface against a safe double first and prove it; introduce each
destructive capability in a later wave behind an explicit guard + a named negative-spec test asserting
the guard holds. Until then the capability is *structurally absent*, not merely untested.

**The bootstrap-canary rule.** The first work-unit of a fresh effort cannot be gated by tools that do
not exist yet — so its own G2 is *"the gates now EXIST and are green on a trivial canary."* Its
deliverable IS the gate machinery (lint config, CI, test doubles, the conformance harness). It earns
the full adversarial design review: a bug in the factory is a bug in every later unit.

**The oracle-honesty rule.** A test double that encodes wrong semantics means every later wave passes
against a lie, and no gate G1–G4 catches it — the oracle itself is wrong. The fix: **ONE conformance
suite that BOTH the reference oracle (the fake, or the predecessor implementation in a port) AND the
real implementation must pass**, shipped as a first-class deliverable of the bootstrap unit, not a
byproduct of a later wave. Prove the suite non-vacuous with deliberately-wrong sabotage fakes: a
double that violates the contract MUST fail the suite; if it passes, the suite tests nothing.

## Gate commands — a pattern, bound by your stack pack

The loop names gates by PURPOSE; the concrete commands are the installed scalars, and the
per-language concretion lives in your stack pack — this table is the pattern, the pack is the binding:

| Purpose | Command |
|---|---|
| Build / compile | `{{BUILD_CMD}}` |
| Lint (warnings are errors) | `{{LINT_CMD}}` |
| Format | `{{FMT_CMD}}` |
| Tests | `{{TEST_CMD}}` |
| IMPL→WIRED proof | `{{CODE_INTEL_TOOL}}` (fallback menu: addendum §C) |
| Stack-specific gates (concurrency modes, integration doubles, …) | the installed stack `rules.md` + `code-intel.md` |

An empty scalar means the repo declared no such step — that gate self-skips (the pre-commit
dispatcher handles this); never fabricate a command to fill a cell.

## The scale-down floor

The loop scales DOWN as legitimately as it scales up. For a small project or a port, the whole intake
may be exactly: **a work-unit spec (WU-NNNN + acceptance rules + a negative spec seeded from the
predecessor's scar list) + ONE design ADR with a real Alternatives Considered + a contract review of
the highest-leverage frozen surface (run BEFORE any dependent work builds against it) + the G1
conformance falsifiers.** No fleet-scale ceremony. The ratchet still holds in full; add waves,
charters, and the heavy gates only when the surface grows to need them.

## Your gate idiom (deliberately unfilled)

The kit ships §Gate contracts in its own vocabulary — adopt it verbatim to start. When your team has
its own gate vocabulary, re-voice §Gate contracts HERE, keeping the underlying contracts intact:
RED-on-HEAD + non-vacuous control @ G1 · firsthand gates + IMPL→WIRED @ G2 · reviewer ≠ builder +
full disposition @ G3 · hands-on + independent verifier + operator sign-off @ G4. **The wording is
yours; the ratchet is not.**

<!-- Re-voiced gate contracts go here. -->

## Related

- `.claude/rules/standing-rules-core.md` — the normative ratchet rules this loop sequences (never
  restated here)
- `CONVENTIONS-full-addendum.md` §C (IMPL→WIRED) · §D (dispatch-charters, wave-plans, verifier gate)
- `CONVENTIONS.md` §4 (WU spine) · §5 (decision policy) · §7.2 (adversarial separation)
- `templates/dispatch-charter-template.md` — the `FR-NNNN` scaffold the lifecycle table keys to
- `reviews/index.md` — where G3 dispositions land (`REV-NNN`)
- `doc-refs-contract.md` · `baseline-mechanism.md` — the docs-impact CLEAR stage the G2-docs gate
  above invokes: the diff-keyed sweep contract + its brownfield baseline mechanism
- the installed stack pack (`rules.md` · `code-intel.md`) — the concrete gate bindings
