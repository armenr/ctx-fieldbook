---
provenance: kit-template
status: accepted
created: 2026-07-03
tags: [meta, framework, index]
---

# framework-rationale/ — the WHY that ships

The generalized framework ADRs plus the narrative that ties them together. These
teach *why* the context system is shaped the way it is; the **Alternatives
Considered** section of each ADR is the real value — the rejected options and the
reasons are what keep you from re-making an already-made mistake.

**These are read-only reference, not your project's decision log.** Your own
`decisions/` starts empty and is seeded by your real ADR-0001 ("adopted this
context system"). Read these to understand the design; do not treat them as
decisions you made.

## Start here

- **`why-this-system.md`** — the connective narrative: the six load-bearing
  principles (progressive disclosure, findings-to-disk, IMPL→WIRED, adversarial
  separation, ceremony-as-fossil, the three write-disciplines).
  *Open when:* you want the whole system's logic before diving into any one ADR.
  *Carry-away:* internalize the six principles or the folders are just ceremony.

## The framework ADRs

- **`0001-in-repo-context-system.md`** — adopt one in-repo knowledge base fronted
  by a pointer-style `CLAUDE.md`.
  *Open when:* deciding where durable project context should live.
  *Carry-away:* the discipline is the asset; copying the folders without the
  ethos is the failure mode.

- **`0002-session-lifecycle-skills.md`** — `/orient`, `/flush`, `/handoff`, and
  the immutable `/sitrep` checkpoint.
  *Open when:* deciding how state survives session end and compaction.
  *Carry-away:* a naive summary drops the dead-ends that are the actual value —
  the checkpoint tier exists to stop that.

- **`0003-lessons-learned-ledger.md`** — a typed, decay-aware lessons ledger with
  human-gated promotion.
  *Open when:* deciding how recurring failures get captured without noise.
  *Carry-away:* auto-promotion breeds same-model confirmation bias; a human gates
  promotion, and "0 good proposals" beats "3 weak ones."

- **`0004-operational-hooks.md`** — deterministic hooks for the safety-critical +
  lifecycle subset.
  *Open when:* deciding what must be enforced vs left advisory.
  *Carry-away:* rules without enforcement are decorative — hook the subset that
  must never be forgotten, leave the rest advisory.

- **`0005-per-directory-routing-indexes.md`** — per-directory `index.md` catalogs
  plus a presence lint.
  *Open when:* deciding how knowledge is found without browsing raw folders.
  *Carry-away:* route to the one right doc; a numeric read-cap limits volume
  without improving aim.

- **`0006-agentic-dispatch-charters.md`** *(Full profile)* — decompose multi-agent
  work into fenced, file-disjoint dispatch charters with an independent verifier.
  *Open when:* running parallel builders or deterministic fan-out.
  *Carry-away:* the executor never audits its own work; charters must be
  file-disjoint within a wave; the orchestrator is the sole integration point —
  no sub-agent commits.

- **`0007-revisit-anchor-ledger.md`** *(Full profile)* — typed `REVISIT` anchors
  linked to a single ledger, enforced by a lint.
  *Open when:* one fact is restated across layers and you need a sweep set.
  *Carry-away:* a `TODO` yields no sweep set; a typed anchor + ledger row gives you
  every site that must change together.

- **`0008-doc-size-disposition.md`** — calibrate doc-size limits by doc *kind*;
  give a living enforced standard its own home.
  *Open when:* a synthesis doc "exceeds" a cap, or a standard has no clear home.
  *Carry-away:* the real bar is "synthesize, don't dump," verified by audit, not a
  line ceiling; fix the rule when the rule is wrong, the work when the work is.

- **`0009-inbound-reference-sweep.md`** *(Standard profile)* — a grep-sweep at
  cycle start gathers everything that references or awaits the unit being started.
  *Open when:* deciding how parked obligations get found when their cycle starts.
  *Carry-away:* any obligation ledger is only as complete as the discipline that
  fed it; a cheap gather-then-triage sweep catches what leaked, by construction.

- **`0010-reviews-findings-home.md`** *(Standard profile)* — review findings get
  a dedicated `reviews/` ledger with per-finding dispositions + test-obligations.
  *Open when:* deciding where adversarial-review findings live and how they close.
  *Carry-away:* a finding has its own lifecycle — no existing dir models it; the
  test-obligation column turns "write tests against these" into a queryable
  backlog, and a review is done only when every finding is dispositioned.

- **`0011-marker-convention.md`** — one CLAUDE.md marker fence for every
  lifecycle operation: `kit:start (fieldbook <kit-version>)` … `kit:end`.
  *Open when:* touching anything that writes, upgrades, or removes the kit's
  CLAUDE.md block.
  *Carry-away:* match on the `kit:start` prefix across versions, never an exact
  one-version string; foreign marker blocks are preserved byte-verbatim.

- **`0012-obligations-ledger.md`** *(Standard profile)* — a two-direction
  inter-party ledger tracks what an agent OWES and is OWED, each receivable
  carrying a pre-decided **default-if-silent** at a named trigger.
  *Open when:* an agent is blocked waiting on a counterparty (another agent,
  another repo, the operator) and that wait — and the silence rule — must survive
  compaction.
  *Carry-away:* the novel *owed-to-me* direction has no other home; a receivable
  is safe across context loss only if the rule for "they never answered" is
  decided in advance, at a trigger, and written down. The form (standalone file
  vs `now/handoff.md` section) is a DETECTED install fact (`multi_party`), not a
  self-report.

- **`0013-origin-posture.md`** — the repo that AUTHORS the kit runs it from a
  gitignored operator directory, not an installed payload; that self-install
  doubles as release-verification.
  *Open when:* reasoning about how the origin repo dogfoods the kit without
  polluting the payload it ships.
  *Carry-away:* dogfood the DISCIPLINE (skills, ledger, cold-start) without the
  PAYLOAD (a second `.agent-docs/`, a marker block) — for adopters this ADR is
  informational, there is nothing to install.

- **`0014-docs-impact-gate.md`** *(Standard profile)* — a **diff-keyed** doc-refs
  sweep (the twin of the unit-keyed `wu-refs`) feeds a named **docs-impact CLEAR**
  stage that *triages, never blocks*, and a baseline mechanism holds an agent
  accountable only for the doc drift its **own** diffs create or touch.
  *Open when:* deciding how documentation gets reconciled to what a change
  actually altered — without punishing drift the adopter inherited.
  *Carry-away:* gather mechanically, triage by judgment, scoped to what the diff
  touched; file-age is not truth and a blocking gate false-positives on still-true
  claims, so the sweep hands the agent a candidate list and draws the
  accountability line at the change's blast radius.

- **`0015-rewrite-conformance-parity-ledger.md`** *(Full profile, opt-in module
  `rewrite-conformance`)* — a port/rewrite's byte-conformance verdicts get their
  own `parity/` ledger tier, a **sibling** of `traceability/`, never a column in it.
  *Open when:* replacing an existing implementation and needing a durable home for
  the parity verdicts and their sabotage-proven non-vacuity.
  *Carry-away:* **PARITY ≠ WIRED** — byte-conformance against an oracle and
  reachability from a production entrypoint are orthogonal axes; one ledger
  carrying both makes "done" ambiguous and launders a conformance claim as a
  reachability proof, so the module is opt-in (no predecessor ⇒ no oracle ⇒
  nothing to gate).
