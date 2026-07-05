# Fieldbook Field Guide

A one-page reference for daily use. See `README.md` for what Fieldbook is and how to install;
see `framework-rationale/why-this-system.md` for *why* it is shaped this way. This card assumes
Fieldbook is already installed in your repo (`.agent-docs/` + `.claude/`).

## The session loop

Four skills carry a session from cold start to clean handoff. Say the slash command; Claude runs the skill.

| When | Command | What it does |
|---|---|---|
| **Session start** / "where are we?" | `/orient` | Reads `now/handoff.md`, checks it against git reality, surfaces a ~12-line brief. |
| **Mid-session**, after a chunk lands | `/flush` | Brings `now/{status,work-plan,open-questions}.md` + `log.md` to current reality; keeps working. No archive, no commit. |
| **Before a risky / irreversible op** (migration, wide refactor, destructive fs op) | `/sitrep` | Writes a WRITE-ONCE 10-point checkpoint — the dead-ends and rejected alternatives a summary drops. *(Standard+)* |
| **Session end / pre-compaction / ~80% context** | `/handoff` | Regenerates the cross-session bridge `now/handoff.md`, consumes the latest sitrep, archives the prior. No commit. |

Rule of thumb: `/flush` repairs the *living* state · `/sitrep` freezes an *immutable* record · `/handoff` is
the bridge to the next session. None of them auto-commits — you stay in control of git.

## Which doc type when

Six durable homes. Pick by the *shape* of what you have, not by its topic.

| You have… | Write a… | Lives in | The rule that makes it worth it |
|---|---|---|---|
| A **decision** you're about to make | **ADR** (`ADR-NNNN`) | `decisions/` | Mandatory `## Alternatives Considered`, written BEFORE you act. The dead-ends are the value. |
| A **mistake / near-miss** you don't want to repeat | **lesson** (`LP-NNN`) | `lessons/` | Append-only: the failure + what makes the save reliable. |
| A **durable, non-obvious fact / gotcha** | **memory** | `memories/` | Title it as a *claim*, not a topic. *(Standard+)* |
| An **open question gating progress** | **OQ** (`OQ-NNN`) | `now/open-questions.md` | One source; a resolved OQ cites the ADR/WU that closed it. |
| A **zero-loss snapshot before risk** | **checkpoint** | `checkpoints/` | WRITE-ONCE, all 10 points, via `/sitrep`. Never edited — a new one supersedes it. *(Standard+)* |
| A **fenced work-spec for a sub-agent** | **dispatch-charter** (`FR-NNNN`) | `dispatch-charters/` | One-file-one-owner, hard scope fence, a named wiring proof. *(Full)* |

Quick sort: decision → ADR · regret → lesson · fact → memory · question → OQ · losing the conversation
would lose *reasoning* → checkpoint. Everything else that matters still goes *somewhere* on disk —
a finding that lives only in chat is gone at the next compaction.

## The ID spine at a glance

Every durable artifact is keyed to a typed ID; the prefix encodes the type. Cross-references cite the ID,
never a body excerpt — the ID still resolves after the doc is superseded.

- **WU-NNNN** — work-unit: the spine; one ledgered unit of intended work. Everything else keys back to the WU that spawned it. (`now/work-plan.md`)
- **ADR-NNNN** — decision; stable forever; supersession-not-deletion. (`decisions/`)
- **OQ-NNN** — open question. (`now/open-questions.md`)
- **LP-NNN** — lesson / near-miss. (`lessons/`)
- Full-only: **FR-NNNN** dispatch-charter · **RV-NNN** revisit anchor · **R-NNNN** research investigation · **INC-NNN** incident.

## The golden rules (one screen)

1. **Route, don't browse.** Reach a doc through its directory's `index.md` and the frontmatter breadcrumbs
   (`tags:`, `related:`, `superseded-by:`) — never by enumerating a raw directory listing. Read with intent.
2. **Findings to disk or they don't exist.** A finding / dead-end / rejected alternative that lives only in
   the conversation is DEAD at the next compaction. Write it to its home the moment you have it; a verdict
   carries its on-disk evidence (a `log.md` timestamp, a commit SHA, a command's output).
3. **IMPL → WIRED, not tests-pass.** Code that compiles and passes its tests but is unreachable from a real
   entrypoint is not done. Prove reachability — with `{{CODE_INTEL_TOOL}}`, or the menu, best-tool-first:
   LSP find-references → call-hierarchy → a language call-graph tool → grep-the-callers (the honest floor) →
   a written manual-trace note.
4. **The reviewer is never the builder.** Independent verification is a clean-context checker with no
   authorship stake — and it applies to designs, not just code. A design reviewed only by its author is unreviewed.
5. **Ask before destructive actions.** Deletions outside `now/*`, datastore resets, service restarts that
   discard state, history rewrites, commits, pushes — confirm first.

---

Full discipline: `.claude/rules/standing-rules-core.md` · the schema: `.agent-docs/CONVENTIONS.md` ·
the why: `framework-rationale/why-this-system.md`.
