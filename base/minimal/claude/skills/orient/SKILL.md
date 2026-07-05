---
name: orient
description: Read .agent-docs/now/handoff.md and surface current session state. Use at session start, after time away, or when reorienting ("where are we?"). Verifies the handoff isn't stale against git reality and runs a quick state-file health sweep (the folded-in /status check).
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [skill, lifecycle, orient]
---

# /orient — Surface current session state from handoff

Single-entry session orientation: read the curated bridge, verify it against reality, and surface a ~12-line brief. Folds in the `/status` quick-health sweep so there is ONE orientation skill, not two.

## 1. Read the handoff

Read `.agent-docs/now/handoff.md`.

If missing:
- Note that the agent context system may not be set up here, or the handoff was never regenerated
- Recommend running `/handoff` to create one

## 2. Check staleness vs reality

- `last-modified` field. If > 24h old, flag prominently.
- `git status -s` and `git log --oneline -3` — verify git state matches the handoff's claims.
- If the session touched runtime-facing code (the app, a service, a CLI), a quick check that the claimed state holds (e.g. the last `{{BUILD_CMD}}` / `{{TEST_CMD}}` baseline the handoff cites is still current).
- If any contradiction exists, surface it BEFORE acting on the handoff's "immediate next action."

## 3. Read supporting docs (in this order)

- `.agent-docs/now/status.md`
- `.agent-docs/now/work-plan.md`
- `.agent-docs/now/open-questions.md`

## 3.5 Quick state-file health sweep (the folded-in /status check)

A fast, no-deep-analysis health pass over the durable state surfaces — flag drift, don't fix it (fixes are `/flush`/`/handoff`'s job):

- **`now/*` currency** — `last-modified` on `status.md` / `work-plan.md` / `open-questions.md`. CONVENTIONS.md lint rule 12 warns at 7d, fails at 90d (the doc linter reports staleness as a warning where installed); flag anything stale.
- **Latest checkpoint** — newest file in `.agent-docs/checkpoints/`; if a `/sitrep` is more recent than `handoff.md`, the forensic state is ahead of the bridge — read it (it holds the dead-ends + in-flight pause point the handoff may have summarized away).
- **Open work-units / blockers** — count active `WU-NNNN` in `now/work-plan.md` and open `OQ-NNN` in `now/open-questions.md`.
- **Index lint** — if the doc linter hook is installed (Standard profile) and it is cheap, note whether `python3 .claude/hooks/lint-docs.py --root .agent-docs` is clean; do NOT fix here.

## 4. Surface to user (concise — ~12 lines)

- **TL;DR**: 1-2 sentences pulled from `status.md`
- **Immediate Next Action**: verbatim from `handoff.md`
- **Active open questions** that gate forward motion (typically 1-3 `OQ-NNN` from `open-questions.md`)
- **Active work-unit(s)**: the `WU-NNNN` in flight
- **Staleness / health flags** if any (from §2 + §3.5) — incl. "a `/sitrep` post-dates the handoff" if so
- **Recent commits**: 3-5 lines from `git log --oneline`

End with: "Ready to proceed with the immediate next action, or refresh state first via `/handoff` or `/flush`?"

## When to invoke

- First action in a new session (manual or via SessionStart hook injection)
- After significant time away from the project
- When the user asks "where are we?"
- After context compaction (if the SessionStart hook didn't auto-orient)

## When NOT to invoke

- Mid-operation. If you're working, you already know where you are.
- Repeatedly within the same session. Read once, work from memory.

## Design rationale

The session-lifecycle contract lives in `standing-rules-core.md` (§Context lifecycle) and `CONVENTIONS.md` (§6 — the checkpoint contract `/sitrep` writes and `/handoff` consumes). Orientation is one skill, not two: the standalone quick-health `/status` check is folded into §3.5 above.
