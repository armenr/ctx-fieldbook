# Fieldbook

Fieldbook is a portable **project-memory and working-discipline system for Claude Code** — a schema, a
set of session skills, and a handful of safety hooks you drop into your own repo. It gives an agent a
durable, version-controlled place to record decisions, carry state across sessions, and prove that work is
actually wired up — not just green on tests.

**The problem it solves.** Claude Code forgets. Every compaction and every fresh session drops whatever
lived only in the conversation — the decision you made and *why*, the dead-end you already ruled out, the
fact that a change compiles but is never reached. Fieldbook moves that knowledge onto disk, next to the
code, under a schema the agent maintains as a byproduct of working. Next session it reads its way back to
exactly where you were.

## What it is, concretely

A `.agent-docs/` tree (living state, decisions, lessons, checkpoints) plus a `.claude/` payload (skills,
hooks, rules) that together give an agent:

- a **cold-start loop** — `/orient` at the top of a session, `/flush` mid-session, `/handoff` at the end;
- a **schema** (`CONVENTIONS.md`) that says where every kind of note goes and how it is written;
- **disciplines** it holds to — findings-to-disk, decisions-with-alternatives, IMPL→WIRED, reviewer-never-builder.

## Install profiles

Adoption is the point, so the payload is split into three additive profiles — each copies on top of the one below it:

- **Minimal** (~6 core artifacts) — the `now/` state spine, the `/orient` · `/flush` · `/handoff` loop, the
  schema, the ADR habit, and the SessionStart / PreCompact hooks. Roughly 80% of the daily payoff at a fraction of the ceremony.
- **Standard** (recommended) — adds checkpoints and the `/sitrep` skill, a lessons system, memories, the
  doc-schema linter and the PreToolUse safety-gate hook, and the IMPL→WIRED discipline.
- **Full** — adds the traceability ledger, the research pipeline, dispatch-charters, revisit anchors, and
  incidents / experiments / runbooks.

Start at Standard; grow into Full only when you feel the need.

**Optional add-on — the statusline.** A python-only Claude Code status line (repo + branch, model +
context window, auto-compact state, context %/tokens, 5h/7d rate-limit usage, account email). Available at
any profile, global or project-scoped — the concierge offers it, or install it by hand per
`modules/statusline/README.md`.

**Optional add-on: truecost.** Measures what work in Claude Code *actually* took, read from the session
transcripts Claude Code already writes to your disk: active hours per project and per task with idle
stripped out, token spend by model, and a forecast for the next job drawn from your own measured history
rather than a feeling. Optional client billing on top. Python-only, stdlib-only, no network calls.
Available at any profile, installed globally (`~/.claude/skills/truecost/`) so it works in every repo, not
just this one. The concierge offers it, or install it by hand per `modules/truecost/README.md`.

## How to install

The intended path: **open Claude Code with this folder as your working directory**, and it becomes an
*install concierge* — it reads your repo, asks about six questions, recommends a profile, and generates a
tailored install (shown as a plan and consented to before anything is written). *The concierge lands in a
later build phase; today this folder ships the payload, the schema, the hooks, and the safety
infrastructure — the base you install by hand or with Claude's help until the concierge arrives.*

Working from your own repo instead of this folder? Paste this to Claude:

> `Read <path-to-fieldbook>/concierge/scaffold-plan.md and be my install concierge.`

(A `CLAUDE.md` in a subdirectory loads lazily, so the open-in-this-folder auto-trigger is only reliable when
this folder is your working directory. From your own repo, the paste-line is the trigger.)

## Prerequisites

- **git** and **bash** (bash 3.2+, so stock macOS works).
- **jq** — recommended; the hooks degrade to a no-op without it, so nothing breaks — you only lose the enforcement.
- **python3** — for the doc-schema linter (Standard+); stock Python 3, standard library only, no installs.

## What it writes into your repo

Always shown as a plan and consented to first — nothing is written silently:

- a **`.agent-docs/`** tree (the memory store + the schema);
- a **`.claude/`** payload — `skills/`, `hooks/`, `rules/`, and the merged `settings.json` hook wiring;
- optionally a **`CLAUDE.md`** section, spliced into a marked, backed-up block — never clobbering an existing file.

Every file action is recorded so an install is reversible and re-runnable.

## Distribution

Fieldbook is handed to you as a **ZIP snapshot**, not a live repo. To update, the author re-shares a newer
zip — versioning survives it (`kit-version.txt` + the install manifest), so a later zip merges into your
existing install rather than clobbering it. Feedback? Tell the author directly.

## Read next

- **`FIELD-GUIDE.md`** — the daily-usage one-pager: the session loop, which doc type when, the ID spine, the golden rules.
- **`framework-rationale/why-this-system.md`** — the six load-bearing principles behind the folders and skills.
