---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0002-session-lifecycle-skills, 0005-per-directory-routing-indexes]
tags: [meta, framework]
---

# ADR-0001 — Adopt an in-repo context system with a pointer-style entrypoint

> This is framework rationale that ships with the kit — the WHY behind the
> system's shape. It is not a decision in *your* project's log; your own
> `decisions/` starts empty, seeded by your real ADR-0001 ("adopted this context
> system"). Read this to understand the design; keep it as reference.

## Context

A project needs durable, structured, provenance-tracked context that survives
across sessions and across context compaction, plus a token-bounded entrypoint
the agent reads first. An unbounded `CLAUDE.md` rots: it grows without limit,
its signal-to-noise falls, and nothing records *why* a rule exists. The agent's
native session memory is good for background knowledge, but it does not capture
curated next-actions, handoff state, or decision rationale — the things that must
be true at the *start* of the next session.

## Alternatives Considered

- **A single growing `CLAUDE.md`.** Rejected: unbounded, low-signal, no
  provenance — every fact carries equal weight and no trace of when or why it was
  added, so the file becomes a junk drawer nobody trusts.
- **Native session memory only.** Rejected: it captures background well, but not
  the decisions, handoffs, and lessons that must persist as *curated, re-readable*
  artifacts. State that lives only in the model's memory dies at compaction.
- **A two-tier split** — a separate "strategy" store and a separate "execution"
  store, kept in sync by hand. Rejected: the hand-sync human relay is a single
  point of failure, and the split breeds vestigial stubs and dangling cross-store
  references. The durable part — separating strategy from execution *with
  independent verification* — is worth keeping, so it is preserved as a
  clean-context verifier stage (ADR-0006); only the two-store mechanism is dropped.
- **One unified in-repo knowledge base + a pointer entrypoint.** Chosen.

## Decision

Adopt ONE unified `.agent-docs/` knowledge base (a taxonomy plus a
`CONVENTIONS.md` schema contract) living inside the repo, fronted by a
**pointer-style `CLAUDE.md`** (kept small; the substance lives in `.agent-docs/`,
`.claude/rules/`, and skills) and an `AGENTS.md` cross-tool shim so other agents
find the same entrypoint.

The framework is a *carrier*. Its value is not the empty folders — it is the
disciplines back-ported into it: the wave-plan → dispatch-charter altitude drop
(ADR-0006), the IMPL→WIRED gate, adversarial separation of duties, decision-
rationale-with-alternatives, zero-loss checkpoints, findings-to-disk, and an
append-only lessons ledger read before action. The schema, templates, lint, and
lifecycle skills transfer intact; the stack-specific pieces (`{{BUILD_CMD}}` /
`{{TEST_CMD}}` / `{{LINT_CMD}}` gates, `{{CODE_INTEL_TOOL}}` as the code-analysis
tool) are filled per project.

## Consequences

- **+** Durable, structured memory; lint-enforced freshness; provenance trust
  signals (`llm-draft` → `llm-reviewed` → `human`); a bounded entrypoint that
  stays readable.
- **−** Maintenance overhead: keeping `now/*` and `log.md` current as a byproduct
  of work, per-directory index discipline, honoring the lifecycle ritual.
- **The discipline *is* the asset.** Copying the folders without the ethos — the
  structure with none of the practice — is the failure mode. The system only pays
  off if the disciplines it carries are actually practiced.

## Related

- ADR-0002 (handoff lifecycle) · ADR-0003 (lessons) · ADR-0004 (hooks) ·
  ADR-0005 (indexes) · ADR-0006 (dispatch charters) · ADR-0007 (REVISIT)
- `CONVENTIONS.md` (the schema contract) · `why-this-system.md` (the narrative)
