---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0002-session-lifecycle-skills, 0005-per-directory-routing-indexes, 0007-revisit-anchor-ledger]
tags: [meta, framework, hooks]
---

# ADR-0004 — Operational hooks (deterministic enforcement)

> Framework rationale that ships with the kit. Explains why a subset of the
> discipline is enforced by hooks rather than left advisory.

## Context

Some discipline must be deterministic, not advisory — safety gates on destructive
commands, state routing at session start, a handoff before compaction. Advisory
rules written in `CLAUDE.md` are honored inconsistently: under momentum, the rule
that "should" have blocked an action is the one that gets skipped. The principle
this enforces is that **rules without enforcement are decorative** — where a rule
can be made a blocking mechanism instead of prohibition text, it should be.

## Alternatives Considered

- **Advisory rules only.** Rejected: bypassed under momentum — the exact failure
  that motivates having any enforcement at all. But advisory framing is *kept* for
  the non-safety-critical majority; hooks are scoped only to the subset that must
  never be forgotten. Enforcing everything would be as brittle as enforcing
  nothing.
- **Hooks for the safety-critical + lifecycle subset, advisory rules for the
  rest.** Chosen.

## Decision

Wire four hooks (registered in `.claude/settings.json`, scripts under
`.claude/hooks/`):

- **SessionStart `state-router`** — classify `now/handoff.md` staleness (fresh /
  stale-warn → suggest `/orient` / stale-block → suggest `/handoff`); point at the
  lessons MOC, the latest `checkpoints/` sitrep, and any per-directory index
  drift. Context-inject only — it never fails the session.
- **PreCompact `handoff-trigger`** — a `systemMessage` prompting a silent
  `/handoff` before compaction. Never `decision: block` — blocking here is a
  foot-gun.
- **PreToolUse `safety-gates`** (matcher: shell commands) — `ask` / `deny` via the
  structured permission-decision schema, anchored to command position. Typical
  surface: **ask** on publish/install to `{{PACKAGE_REGISTRY}}`, dependency-bump
  or re-lock, store-destructive operations (dropping a database or store, wiping
  local state), data-erasure/purge against a live store, and push to
  `{{DEFAULT_BRANCH}}`; **deny** on `--force` push to `{{DEFAULT_BRANCH}}` and on
  bypass flags that skip the commit-time gates. Plus cwd-safety context-injection
  on mutative git/filesystem operations (a real foot-gun in a
  `{{WORKSPACE_LAYOUT}}` where a previous scoped `cd` may have moved you out of the
  workspace root).
- **SubagentStart `prefix`** — inject the multi-agent prompt prefix (including
  "verify cwd before mutative ops"); inject the full standing rules for sub-agents
  that skip `CLAUDE.md`.

## Consequences

- **+** Deterministic safety and state routing; the safety-critical subset cannot
  be forgotten under momentum.
- **−** The PreToolUse command list needs maintenance as the project's tooling
  evolves; hooks run on every matching call, so they are kept cheap.
- Hooks **complement, not replace**, the advisory standing rules and the
  commit-time gates (`{{BUILD_CMD}}` / `{{LINT_CMD}}` / `{{TEST_CMD}}` plus the
  doc-schema and REVISIT lints).

## Related

- ADR-0002 (handoff lifecycle) · ADR-0005 (index-lint at SessionStart) ·
  ADR-0007 (revisit-lint at pre-commit)
- `.claude/hooks/*` · `.claude/settings.json`
