---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
---

# Standing operational rules — core (always-on)

These disciplines persist across every session. Framing here is advisory; the safety-critical subset is
meant to be hook-enforced. Every rule is the fossil of a recurring, expensive failure — keep the wording.
The generalized failure-mode behind each lives in `standing-rules-rationale.md` (load on demand).

## 🛑 CRITICAL — cwd-check before any mutative git / filesystem op

**ALWAYS verify `pwd` + branch + working-tree shape BEFORE any mutative git or filesystem command.**
The harness preserves cwd between shell calls — a previous `cd` into a subdir for a scoped read-only
command may have moved you out of the workspace root, and mutative commands resolve paths relative to
cwd. In a multi-package workspace (`{{WORKSPACE_LAYOUT}}`) that is a live foot-gun.

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --show-toplevel    # which repo am I actually in
git status -s | head -3          # working-tree shape
```

If cwd ≠ expected repo + branch, `cd` to the correct absolute path first, verify again, then proceed.
Applies to sub-agents too — every dispatch prompt involving git/fs mutation carries this constraint.

## Behavior & momentum

- **Ask before destructive actions.** File deletions outside `now/*`, dropping/resetting a datastore,
  service restarts that discard state, history rewrites, commits, pushes — confirm first.
- **Brief responses, momentum, less process.** Default to forward motion; don't narrate options you won't pursue.
- **Surface gaps loudly; be pessimistic about ambiguity.** An honest open-question (`OQ-NNN`) beats a
  polished plan with hidden assumptions. Lock scope before bulk work.
- **Scope for completeness, NOT MVP.** Build to a finished, wired state, not a demo — finish the
  production path or write the deferral down (a `DEFER` row) with the reason. An MVP-default leaves a
  half-wired surface.
- **Keep a continuous detour map (the side-quest stack).** Track the MAIN objective and each nested
  side-quest so you can always climb one level back up; long sessions lose the original objective without it.

## Quality gates & change discipline

- **The gates must pass; never bypass them.** `{{BUILD_CMD}}` · `{{LINT_CMD}}` · `{{TEST_CMD}}` ·
  `{{FMT_CMD}}`. The pre-commit hook runs the linter + formatter; **never `--no-verify`** — investigate
  the failing gate, don't route around it.
- **Lint is strict by decision, not preference.** Warnings are errors. Don't silence a lint without an
  explicit, justified, in-comment reason; in library code don't reach for `{{PANIC_EQUIVALENT}}` — return
  a typed error. No needless work to "make it compile."
- **A behavior change OWES a test that would fail without it.** Tests-pass ≠ done; every behavior carries
  its falsifier. And a fix's guard must be proven **NON-VACUOUS**: break the guard deliberately, watch the
  control fail for the right reason, restore. A guard you have never seen fail is not yet a guard.
- **IMPL → WIRED is the acceptance bar, not test-pass.** The most expensive recurring trap is code that
  compiles and passes tests but is never reachable from a production entrypoint. A unit of work is done
  only when a path traces from a real entrypoint (a `main()`, a served command) to the new code. **Prove
  reachability** — with the code-intel tool (`{{CODE_INTEL_TOOL}}`) or, in order, the fallback menu:
  LSP find-references → call-hierarchy → a language call-graph tool → grep-the-callers (the honest floor)
  → a manual-trace note — and record the IMPL/WIRED/DEFER state in `traceability/`. Dead code the linter
  flags is a wiring failure, not noise.
- **Hands-on acceptance for anything runtime-facing.** "Green tests" ≠ "I ran it and saw it work." Actually
  run the real loop / command and watch it do the right thing. Hermetic-green is necessary, not sufficient.

## Findings, decisions & review feedback to disk

- **Findings to disk or they don't exist.** A finding, dead-end, or rejected alternative that lives only
  in conversation is DEAD at compaction. Write it where it belongs the moment you have it — a decision →
  an ADR (`decisions/`); a gotcha → a `memories/` claim; an investigation result → a checkpoint or
  `research/` track. Verdicts carry on-disk evidence (a `log.md` timestamp, a commit SHA, a command output).
- **All durable knowledge lives IN-REPO — never in a harness- or user-local memory store.** Every durable
  claim (a gotcha, an operator preference, a project fact, a ruling) goes into the version-controlled
  `.agent-docs` system — `memories/` for claims, `lessons/` for patterns, ADRs for decisions, this file for
  rules. Any harness-level or machine-local memory store holds ONLY a redirect pointer to this rule:
  knowledge parked there is invisible to the repo, to other tools and operators, and dies with the machine.
  Same locality for sub-agents — **never route a dispatched agent to memory tools**; equip search/read +
  code-intel only, and durable findings travel back through the return schema to be filed here.
- **Decision-rationale-with-alternatives, written BEFORE acting — capture the load-bearing WHY, not the
  verdict.** A non-trivial choice gets an ADR with a non-empty `## Alternatives Considered` field authored
  *before* the work, not reverse-engineered after — the rejected options + why are the value. "Chose X over
  Y" is NOT enough: record **(a) the deciding axis** the choice actually turned on, **(b) an honest steelman
  of the runner-up** (why the rejected front-runner is genuinely good — never a strawman), and **(c) the
  flip-condition** — what would reverse it (a different goal, new evidence, a changed constraint; e.g. "for a
  product rather than a reference architecture, we'd have chosen the other"). If the conversation that
  produced the decision was richer than the ADR, the ADR is INCOMPLETE. An ADR without the field is
  lint-incomplete.
- **Consult the decision record before reopening ANY settled decision — and bring genuinely new
  information.** The flip-condition is the pre-written trigger for a reversal; re-litigating a settled call
  without new evidence, a changed goal, or a changed constraint burns the record's whole value.
- **Capture ALL review feedback — every severity, never just the blockers.** When ANY review pass returns
  findings, EVERY finding gets a durable home AND an explicit disposition: `FIXED` · `DEFER` (+reason) ·
  `WONTFIX` (+reason) · `TRACKED` (→ a new `OQ-`). Minors and nits included. "CLEAN except a few nits" is
  NOT license to drop the nits — an independent verifier routinely catches majors an in-workflow pass
  passed CLEAN; silently dropping non-blockers loses exactly that signal.
- **Efficiency/savings claims carry a MEASURED[n]/ESTIMATED[lo…hi] label — never a bare %.** Vendor
  headline figures are ESTIMATED-until-reproduced-on-our-workload; measure the trace, not the feeling.

## Adversarial separation of duties

- **The reviewer is never the builder.** The executor never audits its own work. Independent verification
  is a clean-context verifier sub-agent that re-derives the claim against the live tree with no authorship stake.
- **This applies to DESIGNS, not just code.** Pattern: `design → split → adversarial-review` BEFORE
  implementation. A design reviewed only by its author is unreviewed.
- **A capped or budget-limited audit run yields a LOWER BOUND, not a completed floor.** If the run stopped
  on a cap (time, tokens, item count) rather than exhaustion, report "found ≥ N" — never "found all N".
- **0/N findings refuted is a smell, not a triumph — check the refuter before celebrating.** A perfectly
  clean adversarial pass is more often a broken or misaimed checker than a perfect artifact: confirm the
  refuter actually ran, against the right tree, and could have failed.
- **Never answer from absence.** An empty search / lookup / retrieval result is evidence about the
  QUERY, not the world: scope the query to the question, and when the scoped result comes back empty,
  WIDEN and retrieve before concluding "does not exist" — "not found" and "absent" are different
  claims, and only the widened pass earns the second.

## Cycle start — scope recon outward, reference sweep inward

- **Recon-first per work-unit — a READ-ONLY scope recon before authoring any build.** Before a work-unit's /
  stage's build is authored, run a read-only scope recon (one parallelizable recon per unit, under the
  dispatch contract) that recalibrates the unit's stale line/scope assumptions against the LIVE tree AND
  returns its COMPLETE file-ownership set. The orchestrator VERIFIES cross-unit file-disjointness from
  those sets BEFORE any parallel launch — a collision caught at recon costs one read; caught mid-build it
  costs a track. **Treat any durable backlog as a DRAFT**: its claims (line numbers, finding completeness,
  multi-site counts) are re-verified at point of use, never trusted — the backlog is a map, not the territory.
- **Inbound-reference sweep at cycle start (the inward companion to scope-recon).** Before authoring a
  work-unit's / stage's build, scope-recon looks OUTWARD (what the WU touches); ALSO look INWARD — run
  `scripts/wu-refs.sh <WU/unit id> [stage]` to gather everything that references / awaits it across the
  whole tree (a forgotten `DEFER→`, a gating `OQ`, an `RV` that lifts here, an ADR note, a review finding,
  a dispatch charter, a code comment), and TRIAGE each: satisfied · do-this-cycle · unexpected→investigate ·
  stale→remove. The `traceability/` ledger is the *intended* obligation store; the sweep is the
  defense-in-depth that catches whatever leaked into the other surfaces (`git grep --untracked`, so
  in-flight uncommitted files are swept). Cheap (one command, read-only), and it fails LOUD not silent — a
  sweep that silently under-reports is worse than none, so **test your safety tools** (the original shipped
  with a reserved-bash-variable bug that returned "no references" against a WU with dozens of real hits).

## Dispatch contract — scope-fence + halt-and-report, never freelance

Every dispatched agent (Agent tool or Workflow worker) operates under this contract; bake it into the
prompt + the return schema, every time.
- **Hard scope fence (stay in lane).** The prompt names the EXACT files the agent may touch + its single
  purpose + an explicit *do NOT fix / refactor / improve anything outside that, even if it's obviously broken*.
- **Posture = report-all, act-only-in-lane.** Full judgment INSIDE the scoped task; any out-of-scope
  discovery, ambiguity, or temptation is recorded to a REQUIRED `discoveries[]` / `out_of_scope` field and
  NOT acted on. If the unexpected thing BLOCKS the task, the agent returns `status: blocked` and stops — it
  never invents a workaround or expands scope to get unblocked.
- **Non-builder agents are READ-ONLY.** Recon, fixture, review, and verify agents never mutate the tree;
  only ONE fenced build agent per track mutates.
- **Parallel tracks run in isolated worktrees over pre-verified disjoint file ownership** — the ownership
  sets come from the recon-first pass and the orchestrator verifies disjointness BEFORE launch, so tracks
  cannot clobber each other mid-flight.
- **No agent commits or merges.** The orchestrator is the sole, serial integration point; it reads every
  diff firsthand and an independent reviewer audits for scope-creep BEFORE any commit. Discoveries are the
  operator's to adjudicate.
- **Pin the model tier on every dispatch — never silent-inherit the session model into fan-out.** A
  dispatch that omits an explicit tier is a defect to fix, not run. Default to the standard/workhorse tier;
  escalate to the deep tier ONLY where it demonstrably adds value (the hardest adversarial-verify / judge /
  design stages) and with the justification stated; cheap mechanical stages may drop lower. (The
  dispatch-charter template's `model-tier` hint is the per-charter home for this call.)
- **Returns are structured and REQUIRE the honesty fields.** Every dispatch return carries: proof the
  falsifier ran RED on the unmodified HEAD (for the right reason) · the guard's non-vacuous negative
  control (broke it, watched the control fail, restored) · the IMPL→WIRED reachability proof · the
  `discoveries[]` field (present even when empty) · a per-finding disposition for anything it reviewed.
  A return missing these is incomplete, not done.
- **Don't trust an agent's self-report** that it wrote/verified something — `ls`/grep the live artifact
  yourself; reproduce a relayed bug/finding firsthand against the live tree before filing or acting on it.

### Fan-out failure modes — apply the mitigation on sight

Each row is a recurrence-counted failure with a standing response. Don't re-derive the mitigation — the
IF is the trigger to watch for, the THEN is the standing answer.

| IF | THEN |
|---|---|
| Parallel heavy agents hit repeated **server-side rate-limit waves** | **SERIALIZE the heavy stage** (one at a time); keep lighter stages pipelined; resuming banks already-cached successes. Never hammer fresh parallel re-dispatches into an active wave; back off if a resume makes zero new progress. |
| Multiple **heavy LOCAL builds** would run at once (distinct from the wave above — this is one machine's finite cores/disk) | **SERIALIZE the heavy build phases**; give each parallel-track worktree its own build/output dir; keep **at most 2 concurrent heavy streams** — three or more thrash and starve each other. |
| Draft agents **write docs to disk AND return a placeholder/summary** in structured output (disk ≠ return → phantom or clobbered docs) | Use **RETURN-ONLY** draft prompts (no file tools); reconcile disk-vs-return **per-doc**; list-verify every claimed path; recover any placeholder'd doc from the agent's transcript. |
| Agents **transiently error mid-run** | **RESUME the interrupted run** (replay what already succeeded, re-run only the failed legs) — do NOT re-dispatch fresh. |

## Context lifecycle

- `/orient` at session start, `/flush` mid-session, `/handoff` at session end / pre-compaction. Write a
  write-once 10-point checkpoint at any zero-loss boundary — it preserves the dead-ends + rejected
  alternatives a naive summary deletes.
- Update `now/*` + `log.md` as a byproduct of work, not a separate task.
- At ~80% context usage, proactively propose `/handoff` before continuing.

## Commits, external deps & data safety

- **Conventional commits**, HEREDOC for multiline messages; **don't push without an explicit go** (a branch
  may accumulate many local commits before the push gate).
- **Currency-check before pulling in / touching ANY external artifact** (packages, base images, CLI tools,
  CI actions): verify the latest stable version + deprecation status of the *exact* API used against
  **current-year primary docs**, never training data. Search the current year for versions and framework state.
- **Never commit secrets, credentials, or regulated / user data** to any tracked file (docs, code, configs,
  fixtures). Reference paths / store keys, never literal values. Detail in `sensitive-data.md`.
