---
provenance: kit-template
created: 2026-07-10
last-modified: 2026-07-10
tags: [module, agents, dispatch, opt-in, full-profile]
related: [standing-rules-core, dispatch-charter-template, work-discipline]
---

# Module: agents-starter (Full-profile, OPT-IN)

**Never a default payload.** This module ships **six sub-agent templates** into
`<target>/.claude/agents/` — the read-only / authoring crew of the
**work-discipline delivery loop** (`reference/work-discipline.md`: intake →
decompose → fixtures → build → integrate → docs → review → accept), one keyed to
each verifying or authoring leg around the single fenced builder. The concierge
offers it **at the interview only**, and **only when the dispatch-charter module
and the `traceability/` ledger are already installed** — the crew run that loop
*against the charter spine*, so without the charter template and the wiring ledger
to report into they point at nothing. It is a Full-tier opt-in; a Minimal or
Standard install never sees it, and no profile installs it by default.

If your project does not fan work out to sub-agents under the charter loop, skip
this module — six role prompts with nothing to run against is ceremony for no gain.

## The roster

Each template is a fenced, single-purpose sub-agent keyed to one leg of the
delivery loop `reference/work-discipline.md` sequences (intake → decompose →
fixtures → build → integrate → docs → review → accept); these six are its crew.
Every one runs under the **dispatch contract** in `standing-rules-core.md` —
scope-fence, report-all/act-only-in-lane, halt-and-report, no agent commits —
which the templates **point at, never restate**. Each also **pins a default model
tier** (`cheap | standard | deep`) in its front-matter per the contract's
model-pinning rule (`standing-rules-core.md` §"Dispatch contract": default the
standard tier, escalate to `deep` only where it demonstrably adds value, and
*mechanical stages MAY drop lower*). The four adversarial-verify / wiring /
planning legs — `tactical-planner`, `recon-verifier`, `quality-engineer`,
`integration-auditor` — run `deep`; `docs-sync` runs `standard`;
`completion-agent`, the fast mechanical gate-reproduction leg, runs `cheap`.

| Agent | Role | When it runs in the charter lifecycle |
|---|---|---|
| `tactical-planner` | Decomposes a `WU-NNNN` work-unit into file-disjoint waves and authors each charter's Part-A work-spec — single purpose, one-file-one-owner fence, wiring-proof target. | At decompose, before any build is authored; drives charters `drafting → dispatched`. |
| `recon-verifier` | Independent clean-context integration verifier at the **merge gate**: with fresh context and no build stake, re-derives the risky invariants — IMPL→WIRED reachability, blast radius, cross-boundary effects — against the LIVE tree and returns a **VERIFIED / FLAGGED** verdict; its report lands in the charter's verifier report. Read-only; advances no ledger. | Runs AFTER the completion gate reports CLEAR, before merge — the orchestrator advances the `traceability/` row on the pair. |
| `quality-engineer` | Authors the adversarial test matrix: a **RED-on-HEAD** falsifier plus a **proven-non-vacuous** negative control for each behavior change, each bound to a named acceptance rule. | Fixtures stage, before a line of implementation. |
| `docs-sync` | Reconciles docs to the wave diff — public surface, decision stubs, routing-index rows; self-skips when the diff has no doc-impact. | After integrate, at the review boundary. |
| `integration-auditor` | System-wiring verification: proves new code is production-reachable (**IMPL→WIRED**), not merely test-green — multi-path reachability + a registration-vs-implementation diff that catches the built-but-not-wired trap. Read-only; reports, never fixes. | At the wave / phase gate, before the unit is called done. |
| `completion-agent` | Firsthand gate-reproduction leg: reruns the build / lint / format / test gates itself, reads the fenced diff, proves IMPL→WIRED, and returns a **CLEAR / BLOCKED** verdict — trusts no builder self-report, advances no ledger. Fast/mechanical (`model: cheap`). | Runs FIRST at wave close, before the independent verifier — the orchestrator advances the `traceability/` row on the completion+verify pair. |

No `builder` template ships. The one mutating agent per track is dispatched
ad-hoc from its charter's Part-A fence, not from a standing role prompt — these
six are the read-only / authoring crew around it. `recon-verifier`,
`integration-auditor`, and `completion-agent` are **read-only by construction**
(their `tools` line omits Write/Edit); do not add mutation tools to them when you
fill the template — that is the dispatch contract's non-builder rule made
concrete, not an oversight.

Findings and verdicts land in the spine's existing sinks — a `traceability/`
IMPL/WIRED/DEFER row keyed to the `WU-NNNN`, and the charter's verifier report
(Part B.4 in the shipped template, its wiring-proof subsection); `reviews/` is an
optional sink where an agent files review-style findings, and reachability-query
output is evidence-on-disk cited in the row or a `checkpoints/` entry. The
templates land findings in those sinks — directly where they own the surface, or
via their return for the orchestrator to file; never in a private notebook.

## Not in this roster (and why)

Three agents from the same field lineage are deliberately **left out of v1** —
including them would ship an empty gesture or smuggle in an unshipped subsystem:

- **`requirements-analyst`** and **`plan-reviewer`** — both anchor to intake- and
  review-loop maturity that is still stabilizing as default payload. Shipping their
  prompts now would smuggle that pipeline into every install through the back door
  of a role definition — the prompt would assert a process the target repo has not
  adopted. They flip in when the intake spec object and the review home are
  load-bearing defaults, not before.
- **`security-engineer`** — its load-bearing content is the **per-project attack
  surface**, which is ~100% host-specific. A template body reduced to HOST-fill
  blocks would be an empty shell: the ceremony of an agent with none of the
  substance that makes one useful. It flips in only when the owner commits a
  red-team findings home for its output to land in; until then the kit's own spine
  already carries the portable security doctrine, and a hollow template is worse
  than its absence.

## Install (opt-in)

The concierge does this for you in add-module mode; the by-hand steps mirror each
template's own `INSTALL` header:

1. **Copy the six templates**, dropping the `.template` suffix, into the target's
   agents dir:

   ```sh
   mkdir -p <target>/.claude/agents
   for t in modules/agents-starter/agents/*.template.md; do
     cp "$t" "<target>/.claude/agents/$(basename "$t" .template.md).md"
   done
   ```

   (This `README.md` stays behind — reference only, never copied to the target.)

2. **Fill each copied template's blanks.** Two kinds, then delete the leading
   `INSTALL` comment:
   - the **twelve concierge scalars** (`{{PROJECT_NAME}}`, `{{BUILD_CMD}}`,
     `{{TEST_CMD}}`, `{{CODE_INTEL_TOOL}}`, `{{PRIMARY_LANGUAGE}}`,
     `{{PANIC_EQUIVALENT}}`, …) — the concierge fills these automatically; by hand,
     substitute the twelve exact tokens (`concierge/parameters.md`) and nothing else.
   - the **`<!-- HOST: … -->` blocks** — structured per-project content that is not
     a scalar. Each block states what it wants and carries one generic example;
     write your repo's real prose in its place, then delete the block. For instance:

     ```
     <!-- HOST: list THIS project's parallel production paths (how a capability can reach
          production). One generic example: an HTTP-handler path vs a background-worker path
          vs a CLI path — the same feature may be dispatched on one and silently absent on
          another. Replace with your real paths. -->
     ```

   Each template records the `template-version` it was scaffolded from, so drift
   between your filled copy and a later kit revision stays detectable, not invisible.

3. **Wire nothing.** Claude Code discovers agents by reading `.claude/agents/` —
   dropping the filled files in is the whole installation. There is no
   `settings.json` block and no hook to register. (Contrast the revisit-ledger
   module, which *does* wire a pre-commit gate; this one deliberately does not.)

## Degradation is the contract

Every template carries a **degradation guard**, and it is a correctness property,
not politeness. When a referenced artifact is absent or the operator has waived
that scaffolding — no `traceability/` ledger, no `dispatch-charters/` dir, no
`reviews/` home — the agent **flags the operator and continues within its
read-only, report-all lane. It never fabricates a tracked file to satisfy a
pointer.** A wiring auditor that invents a `traceability/` row to tick its own
checklist has corrupted the ledger it exists to protect; a planner that writes a
phantom charter into a dir the repo waived has manufactured state no one asked
for. Missing-or-waived → the agent's returned report *is* the record, flag the
operator, do not invent the file. That guard is standing behavior in every one of
the six, not per-install courtesy.

## Undo

The templates are inert files. To remove the module, delete the six from
`<target>/.claude/agents/`:

```sh
rm <target>/.claude/agents/{tactical-planner,recon-verifier,quality-engineer,docs-sync,integration-auditor,completion-agent}.md
```

Nothing else was written — no hook, no `settings.json` edit, no ledger row.
Removal is complete; the rest of the install is untouched.

## Drift warning — keep the pointer

The templates deliberately **point at `standing-rules-core.md` for the dispatch
contract** (scope-fence, halt-and-report, reviewer-≠-builder, findings-to-disk)
and at `reference/work-discipline.md` for the gate sequencing, instead of
restating either. **If you fork a template — re-voice its wording for your team —
keep that pointer intact.** The moment you inline the contract text instead of
pointing at it, your copy silently diverges from the rules the next time they are
revised, and you are running a stale dispatch contract with no signal that it
drifted. The pointer *is* the anti-drift mechanism; severing it is the single
largest silent-drift risk this module carries.

## Related

- `.claude/rules/standing-rules-core.md` — the dispatch contract the templates
  point at (never restated in an agent body)
- `reference/work-discipline.md` — the gated delivery loop these six crew; Full
  profile
- `templates/dispatch-charter-template.md` — the `FR-NNNN` scaffold whose
  lifecycle roles (planner · builder · verifier · operator) the roster fills
- `concierge/parameters.md` — the twelve scalars the templates consume
