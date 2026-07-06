---
provenance: kit-template
created: 2026-07-03
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
- **A behavior change OWES a test that would fail without it.** Tests-pass ≠ done; every behavior carries its falsifier.
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
- **Decision-rationale-with-alternatives, written BEFORE acting — capture the load-bearing WHY, not the
  verdict.** A non-trivial choice gets an ADR with a non-empty `## Alternatives Considered` field authored
  *before* the work, not reverse-engineered after — the rejected options + why are the value. "Chose X over
  Y" is NOT enough: record **(a) the deciding axis** the choice actually turned on, **(b) an honest steelman
  of the runner-up** (why the rejected front-runner is genuinely good — never a strawman), and **(c) the
  flip-condition** — what would reverse it (a different goal, new evidence, a changed constraint; e.g. "for a
  product rather than a reference architecture, we'd have chosen the other"). If the conversation that
  produced the decision was richer than the ADR, the ADR is INCOMPLETE. An ADR without the field is
  lint-incomplete.
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

## Dispatch contract — scope-fence + halt-and-report, never freelance

Every dispatched agent (Agent tool or Workflow worker) operates under this contract; bake it into the
prompt + the return schema, every time.
- **Hard scope fence (stay in lane).** The prompt names the EXACT files the agent may touch + its single
  purpose + an explicit *do NOT fix / refactor / improve anything outside that, even if it's obviously broken*.
- **Posture = report-all, act-only-in-lane.** Full judgment INSIDE the scoped task; any out-of-scope
  discovery, ambiguity, or temptation is recorded to a REQUIRED `discoveries[]` / `out_of_scope` field and
  NOT acted on. If the unexpected thing BLOCKS the task, the agent returns `status: blocked` and stops — it
  never invents a workaround or expands scope to get unblocked.
- **No agent commits or merges.** The orchestrator is the sole, serial integration point; it reads every
  diff firsthand and an independent reviewer audits for scope-creep BEFORE any commit. Discoveries are the
  operator's to adjudicate.
- **Don't trust an agent's self-report** that it wrote/verified something — `ls`/grep the live artifact
  yourself; reproduce a relayed bug/finding firsthand against the live tree before filing or acting on it.

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
