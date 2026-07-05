<!--
Dispatch-charter template per CONVENTIONS-full-addendum §D (dispatch/wave/verifier) + §C (IMPL→WIRED),
core CONVENTIONS.md §4 (WU/FR spine), §7.2 (adversarial separation), §8 (versioned templates).
Instantiate to `.agent-docs/dispatch/YYYY-MM-DD-wNN-<slug>.md` (rename the dir to taste)
and fill in.  YYYY-MM-DD = dispatch date · wNN = zero-padded wave number · <slug> = kebab short id.
Record the `template-version` you scaffolded from (§8) so drift is detectable, not invisible.
Planner authors the PLANNER sections; builder authors BUILDER; the clean-context verifier authors
VERIFIER; operator authors the operator-decision section. Delete this comment block + inline guidance.
-->

---
provenance: llm-draft
status: drafting
template-version: 1.0.0            # §8 — the template revision this charter was scaffolded from
work-unit: WU-NNNN                # §4 spine — the parent work-unit this charter is a leg of
charter-id: FR-NNNN               # the dispatch-charter's typed id (§B spine)
wave: <wave-number>              # wave-plan wave (sequenced by file-overlap)
created: <YYYY-MM-DD>             # LOCAL date (date +%Y-%m-%d), not UTC (§2)
last-modified: <YYYY-MM-DD>
base-commit: <SHA the charter assumes>
model-tier: standard              # cheap | standard | deep — config field, not an inline decision (§B′)
related: [<ADR-NNNN, WU-NNNN, sibling FR-NNNN>]
rollback-handle: null             # builder sets after first commit on the charter branch
operator-eyes-on: false           # true for the first charter of a wave; planner sets
tags: [dispatch, wave-<N>]
---

# FR-NNNN — <one-line claim of what this charter does>

<!-- One paragraph: what this charter is for, why, how it composes with siblings in the wave. -->

## 1. Charter (PLANNER)

### File ownership (one-file-one-owner)
<!-- The EXACT paths this leg OWNS. Wave sequencing keys off file-overlap — two charters in the same
     wave must NOT own the same file. Respect the boundaries in {{WORKSPACE_LAYOUT}}. -->
- `<path/to/module>` — owned by this leg
- ...

### Recalibrated scope (vs the LIVE tree)
<!-- §D: do NOT trust the wave-plan's stale estimate. Survey the live tree FIRST and record reality. -->
- Surveyed via {{CODE_INTEL_TOOL}} (or LSP overview / grep) on <date> @ <SHA>.
- LIVE reality: <what's actually there> across <modules>. (Wave-plan assumed <X>; delta: <why>.)
- Expected diff shape: ~<N> files · touches: <modules>.

### Wiring-proof target (IMPL→WIRED, §C)
<!-- The production entrypoint this work must be reachable FROM. "Done" = production-reachable, not
     test-pass. Name the entrypoint and the reachability check you'll use. -->
- Reachable from: `<production entrypoint>` (a real `main()` / served command / public API surface).
- Reachability proof — first available on this menu: {{CODE_INTEL_TOOL}} call-path → LSP
  find-references → LSP call-hierarchy → language call-graph tool → grep-the-callers (floor) →
  manual-trace note. Record the query + result.
- Record IMPL / WIRED / DEFER in `traceability/` keyed to WU-NNNN.

### Verifier gate (clean-context reviewer, §D / §7.2)
<!-- The reviewer is NEVER the builder. What must a no-authorship-stake verifier independently
     re-derive against the LIVE tree before this charter is certified? -->
- [ ] <claim the verifier confirms — e.g. "new surface is production-reachable, not just compiled">
- [ ] <reachability re-derived INDEPENDENTLY of the builder's assertion>

### Scope
<!-- Concrete actions, priority order. Imperatives. -->
- ...

### Scope-boundaries (stay in lane)
<!-- What is explicitly NOT in scope. An out-of-scope discovery is REPORTED (discoveries[]), not acted
     on; if it BLOCKS the task, HALT and report — never invent a workaround or expand scope. -->
- NOT: ...

### Acceptance criteria
<!-- Deterministic where possible. -->
- [ ] `{{BUILD_CMD}}` clean
- [ ] `{{LINT_CMD}}` clean — warnings are errors; no unjustified lint suppressions
- [ ] `{{FMT_CMD}}` clean
- [ ] `{{TEST_CMD}}` green; **a behavior change OWES a test that fails without it**
- [ ] Hands-on: ran the real touched surface and watched it do the right thing (green tests ≠ ran it)
- [ ] **IMPL→WIRED:** the reachability check proves the new code is reachable from the wiring-proof entrypoint; row recorded in `traceability/`
- [ ] No new `{{PANIC_EQUIVALENT}}` in library code; errors are propagated, not swallowed

### Dependencies
- Charters: <FR-NNNN ids, or "none">
- ADRs that lock substance: <numbers>
- Commits required first: <SHAs or "none">

### Integration-points
<!-- Paths the builder touches AND/OR the verifier must confirm get WIRED. Anchor cross-layer lockstep
     surfaces with REVISIT twin:/claim: markers + a revisit-ledger row in the SAME change (§F). -->
- `<shared types / interface — the dependency root>`
- `<the implementation that must move in lockstep>` — `twin:` REVISIT anchor
- ...

---

## 2. Brief-back (BUILDER → PLANNER)

**My understanding:** <builder restatement>
**Ambiguities / questions:** ...
**Planner response:** <answers or "no ambiguities">
**Planner sign-off:** [ ] brief-back accepted / [ ] re-charter required

---

## 3. State reconnaissance (PLANNER, pre-dispatch)

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

---

## 4. Gate verdicts (AUTOMATED + BUILDER)

- `{{BUILD_CMD}}`: <pass | fail + summary>
- `{{LINT_CMD}}`: <pass | fail + first offending finding>
- `{{FMT_CMD}}`: <pass | fail>
- `{{TEST_CMD}}`: <pass | fail + counts>
- Hands-on run: <surface invoked + observed behavior>
- IMPL→WIRED: <reachability query output · traceability row>
- Custom verifications from the Charter: <results>

---

## 5. Verifier report (VERIFIER — clean-context, never the builder; §D)

### Wiring proof (production-reachability, not test-pass)
- Reachability query (menu, §C): <chain found | EMPTY → IMPL-not-WIRED, reject>
**Verdict:** <WIRED | IMPL-only (reject) | n/a>

### Cross-layer lockstep (twin: surfaces)
- Lockstep surfaces in sync: [ ] yes / [ ] drift
- REVISIT `twin:`/`claim:` ledger rows updated in the same change: [ ] yes / [ ] no

### Per-file analysis (where non-obvious)
- `<path>`: <analysis — evidence cites the query + output, not memory (§7.3)>

### Remediation requests
- [ ] <specific change at specific path with rationale>   OR   ✅ No remediation; charter certified.

---

## 6. Remediation log (if needed)

### Cycle 1 — <date>
**Verifier requested:** ... **Builder response:** ... **Re-verify verdict:** <pass | further | escalate>
<!-- Cap at a small number of cycles before escalating to the operator. -->

---

## 7. Operator decision (when required: wave merge / destructive op / eyes-on)

**Trigger:** <wave-merge | destructive-op | eyes-on>
**Operator notes:** <review notes>
**Decision:** [ ] approved / [ ] rejected / [ ] re-work
**Linked commits:** builder SHA(s): <list> · integration/merge SHA (if worktree-isolated): <SHA or n/a> · `rollback-handle`: <SHA>

---

## Frontmatter `status:` lifecycle

`drafting` → `dispatched` (brief-back accepted) → `in-remediation` → `certified` (gates + verifier pass) → `merged` → `rolled-back`

## Related

- `CONVENTIONS-full-addendum.md` §C (IMPL→WIRED) · §D (dispatch/wave/verifier) · §B′ (model-tier) · §F (revisit-ledger)
- `CONVENTIONS.md` §4 (WU/FR spine) · §7.2 (adversarial separation) · §8 (versioned templates)
- `.claude/rules/standing-rules.md` — the dispatch contract (scope-fence, halt-and-report)
- `now/work-plan.md` — where the parent WU tracks substance
