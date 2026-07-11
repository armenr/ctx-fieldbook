<!--
Dispatch-charter template per CONVENTIONS-full-addendum §D (dispatch/wave/verifier) + §C (IMPL→WIRED),
core CONVENTIONS.md §4 (WU/FR spine), §7.2 (adversarial separation), §8 (versioned templates).

WHEN TO FILE ONE AT ALL: dispatch persistence is the TOOLING's job — the run journal / workflow log is
the dispatch record (it persists and replays every dispatch prompt), so a charter exists only when a
genuine scoped work-spec adds value, never as prompt replay.

Instantiate to `dispatch-charters/YYYY-MM-DD-wNN-<slug>.md` (or `FR-NNNN-<slug>.md`; see the
dispatch-charters index) and add a ledger row there in the SAME change. YYYY-MM-DD = dispatch date ·
wNN = zero-padded wave number · <slug> = kebab short id. **Part A is the whole charter for most
dispatches** — fill it and stop (target: under 40 lines instantiated). Part B is opt-in for
load-bearing or multi-wave work; delete it otherwise. Record the `template-version` you scaffolded
from (§8) so drift is detectable, not invisible. Planner authors Part A; builder / verifier / operator
author their Part B sections. Delete this comment block + inline guidance.
-->

---
provenance: llm-draft
status: drafting
template-version: 2.1.0            # §8 — the template revision this charter was scaffolded from
work-unit: WU-NNNN                # §4 spine — the parent work-unit this charter is a leg of
charter-id: FR-NNNN               # the dispatch-charter's typed id (§B spine)
wave: <wave-number>              # wave-plan wave (sequenced by file-overlap)
created: <YYYY-MM-DD>             # LOCAL date (date +%Y-%m-%d), not UTC (§2)
last-modified: <YYYY-MM-DD>
base-commit: <SHA the charter assumes>
model-tier: standard              # cheap | standard | deep — config field, not an inline decision (§B′)
risk-tier: standard               # standard | full — full = turn-control / shared-write state / contracts / irreversible surfaces (drives rule 18)
design-rev:                       # pre-G0 multi-lens design-review id (REV-NNN); REQUIRED before status leaves drafting/draft when risk-tier: full — lint rule 18
related: [<ADR-NNNN, WU-NNNN, sibling FR-NNNN>]
rollback-handle: null             # builder sets after first commit on the charter branch
operator-eyes-on: false           # true for the first charter of a wave; planner sets
tags: [dispatch, wave-<N>]
---

# FR-NNNN — <one-line claim of what this charter does>

## Part A — Work-spec (PLANNER · the default; the whole charter for most dispatches)

**Single purpose:** <one sentence. If it needs an AND, it is two charters.>

> **Risk-tier gate (rule 18):** a `risk-tier: full` charter cannot advance past `drafting` without a
> resolvable `design-rev:` (the pre-G0 multi-lens design-review id, `REV-NNN`) — lint rule 18, born from
> a first-operator process miss. Set `risk-tier` in the front-matter; `standard` (the default) is ungated.

### File ownership (one-file-one-owner)
<!-- The EXACT paths this leg OWNS. Wave sequencing keys off file-overlap — two charters in the same
     wave must NOT own the same file. Respect the boundaries in {{WORKSPACE_LAYOUT}}. -->
- `<path/to/module>` — owned by this leg
- NOT: <explicitly out of scope — an out-of-scope discovery is REPORTED (`discoveries[]`), never acted on>

### Recalibrated scope (vs the LIVE tree, §D)
<!-- Do NOT trust the wave-plan's stale estimate. Survey the live tree FIRST and record reality. -->
- Surveyed via {{CODE_INTEL_TOOL}} (or LSP / grep) on <date> @ <SHA>: <live reality — wave-plan
  assumed <X>; delta: <why>>. Expected diff shape: ~<N> files · touches: <modules>.

### Wiring-proof target (IMPL→WIRED, §C)
<!-- "Done" = production-reachable, not test-pass. -->
- Reachable from: `<production entrypoint>` (a real `main()` / served command / public API surface).
- Proof — first available on this menu: {{CODE_INTEL_TOOL}} call-path → LSP find-references →
  LSP call-hierarchy → language call-graph tool → grep-the-callers (floor) → manual-trace note.
  Record the query + result; IMPL / WIRED / DEFER row in `traceability/` keyed to WU-NNNN.

### Acceptance criteria
- [ ] `{{BUILD_CMD}}` · `{{FMT_CMD}}` clean; `{{LINT_CMD}}` clean — warnings are errors; no unjustified suppressions
- [ ] `{{TEST_CMD}}` green; **a behavior change OWES a test that fails without it**
- [ ] Hands-on: ran the real touched surface and watched it do the right thing (green tests ≠ ran it)
- [ ] **IMPL→WIRED** proven per the wiring-proof target; traceability row recorded
- [ ] **Docs-impact swept** for the leg's diff — stale/uncovered rows dispositioned, or a no-impact
      verdict recorded WITH its execution proof (swept range + grammars + exit 0 + canary), or — until
      `scripts/doc-refs.sh` lands — a recorded MANUAL corpus-read verdict ("sweep not installed → read
      surfaces X"). The `docs_impact` return field; N/A only for a read-only leg. framework-rationale/0014.
- [ ] No new `{{PANIC_EQUIVALENT}}` in library code; errors are propagated, not swallowed
- [ ] Verifier (clean-context, NEVER the builder — §7.2/§D) independently re-derives: <the claim to
      confirm against the LIVE tree — e.g. "new surface is production-reachable, not just compiled">

### Dependencies & integration-points
- Requires first: <FR-NNNN / ADR / commit SHAs, or "none">
- Lockstep surfaces: <shared types / interfaces the builder or verifier must confirm get WIRED, or
  "none" — anchor with REVISIT `twin:`/`claim:` markers + a revisit-ledger row in the SAME change (§F)>

**Dispatch contract:** `.claude/rules/standing-rules-core.md` §"Dispatch contract" governs every leg —
scope-fence, report-all/act-only-in-lane, halt-and-report, no agent commits. Never restated here.

---

## Part B — Lifecycle sections (OPT-IN: for load-bearing or multi-wave work; delete otherwise)

<!-- Use Part B when the stakes justify a persisted paper trail beyond the run journal: multi-wave
     work-units, destructive or operator-eyes-on legs, or charters whose verification story must
     survive the session. Planner authors B.2; builder B.1/B.3; verifier B.4; operator B.6. -->

### B.1 Brief-back (BUILDER → PLANNER)

**My understanding:** <builder restatement>
**Ambiguities / questions:** ...
**Planner response:** <answers or "no ambiguities">
**Planner sign-off:** [ ] brief-back accepted / [ ] re-charter required

### B.2 State reconnaissance (PLANNER, pre-dispatch)

```
$ git rev-parse HEAD
<current-SHA>
$ git log -1 --format='%H %s' <owned-path>
<SHA + subject>
$ <live-tree recon — {{CODE_INTEL_TOOL}} overview / LSP / grep — to recalibrate scope (§D)>
<snapshot>
```

**Drift check vs `base-commit`:** [ ] HEAD matches base / [ ] advanced but integration-points unchanged → safe / [ ] integration-points changed → RE-CHARTER
**Verdict:** <safe-to-proceed | re-charter-required | abort>

### B.3 Gate verdicts (AUTOMATED + BUILDER)

- `{{BUILD_CMD}}`: <pass | fail + summary>
- `{{LINT_CMD}}`: <pass | fail + first offending finding>
- `{{FMT_CMD}}`: <pass | fail>
- `{{TEST_CMD}}`: <pass | fail + counts>
- Hands-on run: <surface invoked + observed behavior>
- IMPL→WIRED: <reachability query output · traceability row>
- Custom verifications from Part A: <results>

### B.4 Verifier report (VERIFIER — clean-context, never the builder; §D)

#### Wiring proof (production-reachability, not test-pass)
- Reachability query (menu, §C): <chain found | EMPTY → IMPL-not-WIRED, reject>
**Verdict:** <WIRED | IMPL-only (reject) | n/a>

#### Cross-layer lockstep (twin: surfaces)
- Lockstep surfaces in sync: [ ] yes / [ ] drift
- REVISIT `twin:`/`claim:` ledger rows updated in the same change: [ ] yes / [ ] no

#### Per-file analysis (where non-obvious)
- `<path>`: <analysis — evidence cites the query + output, not memory (§7.3)>

#### Remediation requests
- [ ] <specific change at specific path with rationale>   OR   ✅ No remediation; charter certified.

### B.5 Remediation log (if needed)

#### Cycle 1 — <date>
**Verifier requested:** ... **Builder response:** ... **Re-verify verdict:** <pass | further | escalate>
<!-- Cap at a small number of cycles before escalating to the operator. -->

### B.6 Operator decision (when required: wave merge / destructive op / eyes-on)

**Trigger:** <wave-merge | destructive-op | eyes-on>
**Operator notes:** <review notes>
**Decision:** [ ] approved / [ ] rejected / [ ] re-work
**Linked commits:** builder SHA(s): <list> · integration/merge SHA (if worktree-isolated): <SHA or n/a> · `rollback-handle`: <SHA>

---

## Frontmatter `status:` lifecycle

`drafting` → `dispatched` (brief-back accepted, or dispatch for Part-A-only charters) →
`in-remediation` → `certified` (gates + verifier pass) → `merged` → `rolled-back`

## Related

- `dispatch-charters/index.md` — the ledger (a row per charter, added in the same change) + the
  when-to-file-at-all posture
- `CONVENTIONS-full-addendum.md` §C (IMPL→WIRED) · §D (dispatch/wave/verifier) · §B′ (model-tier) · §F (revisit-ledger)
- `CONVENTIONS.md` §4 (WU/FR spine) · §7.2 (adversarial separation) · §8 (versioned templates)
- `.claude/rules/standing-rules-core.md` — the dispatch contract (scope-fence, halt-and-report)
- `now/work-plan.md` — where the parent WU tracks substance
