`Read <path-to-fieldbook>/concierge/scaffold-plan.md and be my install concierge.`

☝️ **Already working in your own repo?** Copy the line above into Claude Code. Claude reads this kit and
becomes your install concierge — it interviews you, tailors an install, shows you the plan, and (only on your
yes) writes it into your repo. Nothing is written silently, and every install is reversible.

**Even simpler:** open Claude Code with *this folder* as your working directory. The kit's `CLAUDE.md` loads
automatically and the concierge starts itself — no paste-line needed. (A `CLAUDE.md` in a subdirectory loads
lazily, so the auto-start is only reliable when this folder is your working directory; from your own repo,
use the paste-line.)

## What Fieldbook is

A portable project-memory and working-discipline system for Claude Code — a `.agent-docs/` schema, a small
set of session skills (`/orient` · `/flush` · `/handoff`), and a few safety hooks you install into your own
repo. It gives an agent a durable, version-controlled place to record decisions and carry state across
sessions, so it reads its way back to where you were instead of forgetting at every compaction. See
`README.md` for the full picture and `FIELD-GUIDE.md` for daily use.

## Before you start

- **git** and **bash** (3.2+, so stock macOS works).
- **jq** — recommended; the safety hooks degrade to a harmless no-op without it (you only lose enforcement).
- **python3** — for the doc-schema linter (Standard profile and up); stock Python 3, standard library only, no installs.

## Good to know

- This is a **private ZIP snapshot**, not a live repo — no license, no issue tracker. To update, the author
  hands you a newer zip; your install merges it in rather than clobbering what you have.
- The concierge recommends **Standard** and down-sells to **Minimal** freely — start small, grow later.
- Feedback? Tell the author directly.

<!-- provenance: kit-template · created: 2026-07-03 -->
