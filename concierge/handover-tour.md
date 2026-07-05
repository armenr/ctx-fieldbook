---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [concierge, tour, onboarding, handover]
---

# The 10-minute handover tour

Run this immediately after `verify-install.md` comes back green. It is the difference between handing
someone a folder of files and handing them a system they can *use* — you walk them through one full
turn of the session loop on their OWN repo, so the muscle memory is real, not theoretical.

Voice: a colleague showing a friend around something you set up for them. Confident and warm, never a
tutorial drone. Do ONE step, let them see it work, say one sentence about WHY it matters, move on.
Every step that writes to disk shows the plan first and waits for a "yes" — this is also how you teach
the consent discipline the kit itself runs on. Total time ≈ 10 minutes. If they're impatient, the
must-do core is steps 1, 4, and 6; the rest can wait for their first real session.

Open with the frame: *"The whole system is five moves. Let me show you the loop on your actual repo —
by the end you'll have made a real edit, saved state, and written your first decision record. Ready?"*

## Step 1 — `/orient` (≈1 min): see where you are

Have them type `/orient`. It reads `now/handoff.md` + the `now/*` spine and surfaces a ~12-line brief.

- **What they see:** the seeded state — the project one-liner they gave you, an empty-but-valid work
  plan, no open questions yet. On a fresh install it honestly says "this is the seed; no active work
  yet." That's correct.
- **Say why:** *"This is the first thing you (or Claude) run every session. It's how a brand-new
  session reads its way back to exactly where you left off — the cure for Claude forgetting everything
  at each compaction."*

## Step 2 — a tiny real edit (≈1 min): give the state something true

Pick something genuinely true about their repo right now and make one small real change with them — the
point is to have a real "chunk of work" to save in step 3, not a toy. Good options:

- Set the headline in `now/status.md` to what they're actually about to work on, OR
- Fix one real thing in their codebase they mention while you're talking (a typo, a small TODO).

Keep it to a couple of minutes. Don't invent work — use their real next thing. Say: *"Now we've got
something worth recording. Watch how the system captures it."*

## Step 3 — `/flush` (≈1.5 min): update the living state, in place

Have them type `/flush`. It rewrites `now/{status,work-plan,open-questions}.md` + appends to `log.md`
to reflect the edit — and keeps working. Show them the diff:

```bash
git diff --stat .agent-docs/now/ .agent-docs/log.md
```

- **What they see:** `status.md` now describes the real edit; `log.md` gained a `flush | …` line.
  These are UPDATE-IN-PLACE docs — always "now," never a growing history (git holds the history).
- **Say why:** *"`/flush` is the mid-session save. It brings the living state back to reality so you
  can context-switch without losing the thread. No commit, no ceremony — it just keeps `now/` true."*

## Step 4 — `/handoff` (≈2 min): build the cross-session bridge

Have them type `/handoff`. This is the load-bearing one. It regenerates `now/handoff.md` (the curated
cold-start brief), and archives the previous handoff to `.claude/handoffs/<timestamp>-<slug>.md`. Show
both:

```bash
sed -n '1,40p' .agent-docs/now/handoff.md         # the fresh bridge
ls -t .claude/handoffs/ | head -3                  # the archived prior
```

- **What they see:** a structured handoff with an Anti-assumptions section and a Detour-chain — the two
  sections that carry the stuff a naive summary drops. And a timestamped archive copy.
- **Say why:** *"This is what a future session — tomorrow, or after a compaction — reads first via
  `/orient`. `/flush` keeps today true; `/handoff` writes the bridge to next time. The archive means
  you never lose an old one."*
- **Point forward:** *"When you do heavier work, there's also `/sitrep` — a write-once, never-edited
  checkpoint for freezing your reasoning before a risky move. You'll reach for it naturally; it's in
  the field guide."* (Standard+; mention, don't demo.)

## Step 5 — capture their FIRST lesson (≈1.5 min): "what surprised you?"

Ask them directly: **"Setting this up — what surprised you, or what would you tell yourself before
starting?"** Whatever they say is a real, earned lesson. Draft it with them as a proposal — show the
draft, get a yes, then append it to `.agent-docs/now/lessons/proposals.md` (never straight into
`lessons/` — promotion is human-gated, on purpose):

```
- LP-001 (seedling · llm-draft · type: <false-belief|tool-failure|near-miss|…>)
  Trigger: <the situation that surfaced it>
  Claim: <"When X, do Y because Z">
  Evidence: <the moment during setup it came from>
```

- **Say why:** *"That's the lessons ledger. Every regret or surprise that's worth not repeating lands
  here first as a proposal; you promote the ones that recur. You just wrote entry one from your own
  setup — the best possible seed."*
- If nothing genuinely surprised them, don't manufacture one — say *"perfect, we'll catch the first
  one when it happens"* and skip. A forced lesson is worse than none.

## Step 6 — write their real `ADR-0001`: "adopted Fieldbook" (≈2.5 min)

This is the keystone: their first real decision record, which also makes the doc lint *meaningful*
(with a real ADR on disk, the `## Alternatives Considered` rule is now enforcing something). Draft it
WITH them — the value is a genuine alternatives section, so actually ask what else they considered.

Prompt them: *"Before this, what were your other options for keeping project state — and why not
those?"* Common real answers to draw out (use theirs, not these):

- Claude Code's built-in auto-memory — rejected because it isn't git-tracked / auditable / reviewable.
- A single `NOTES.md` or a wiki — rejected because it has no schema, so it rots and nobody trusts it.
- Nothing / status quo — rejected because that's the "Claude forgets and I re-derive everything" pain
  that started this.

Show them the full draft, get an explicit yes, then write these THREE changes together (so the ledger,
the spine, and the index all stay consistent — and the lint stays clean):

1. **`.agent-docs/decisions/0001-adopt-fieldbook.md`** — from `templates/adr-template.md`:
   `provenance: llm-reviewed` (they reviewed it live; accepted ADRs may not be `llm-draft`),
   `status: accepted`, `work-unit: WU-0001`, a real Context paragraph, their genuine
   `## Alternatives Considered`, and Consequences (name a cost, not just wins).
2. **`.agent-docs/now/work-plan.md`** — add the first real work-unit row so `WU-0001` resolves (lint
   rule 15): `| WU-0001 | Adopt Fieldbook for project memory | — | done |`.
3. **`.agent-docs/decisions/index.md`** — add the routing entry for `0001-adopt-fieldbook.md` (lint
   rule 13 — a dir's index must list its docs). One line: *what it holds · Open when · Carry-away.*

Then re-run the lint to show it stays green with real content in it:

```bash
python3 .claude/hooks/lint-docs.py --root .agent-docs --now "$(date +%Y-%m-%d)"
```

- **Say why:** *"That's the pattern for every decision from now on: write down the alternatives BEFORE
  you act — the dead-ends are the value, they're what a summary destroys. And notice the lint now
  actually checks something real: it'd fail if that ADR were missing its alternatives or its index
  entry. You just made the enforcement meaningful."*

## Step 7 — where to go next (≈0.5 min)

Point, don't lecture:

- **`FIELD-GUIDE.md`** — *"the one-pager to keep open: the five-move loop, which doc type goes where,
  the golden rules. This is your daily reference."*
- **`framework-rationale/why-this-system.md`** — *"read this when a rule feels like overhead — it
  explains the six principles the whole thing serves. Every rule is the fossil of a real, expensive
  failure; that doc tells you which."*
- **Re-run me anytime:** *"Open Claude in the kit folder again to grow into another module, bump your
  profile (Minimal → Standard → Full), or run `/kit-doctor` for a health check and `/kit-upgrade` when
  I send a newer zip. Start small; you can always grow later — nothing you did today gets redone."*

Close by handing back control of git, explicitly: *"Everything we wrote is staged in your working tree,
uncommitted — nothing was committed for you. Review the diff and commit it when you're happy:"*

```bash
git status -s
git add .agent-docs .claude .githooks CLAUDE.md
git commit -m "chore: adopt Fieldbook context system (profile: <profile>)"
```

**Do NOT auto-commit for them.** The tour ends the way the whole system runs — the human owns the
commit. That's the last thing they should feel: this system does things *with* their consent, never
behind their back.
