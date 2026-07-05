---
provenance: kit-template
status: accepted
created: 2026-07-03
related: [0001-in-repo-context-system]
tags: [meta, framework, narrative]
---

# Why this system is shaped the way it is

The eight framework ADRs each argue one decision. This is the connective
tissue — the handful of load-bearing principles that the whole system exists to
serve. If you internalize these six, the folders and skills will make sense; if
you skip them and copy the structure, you will get the ceremony without the
payoff.

## 1 · Progressive disclosure — route, don't browse

The knowledge base is not a pile you scan; it is a graph you *route* through. You
reach a document via its directory's `index.md` and the frontmatter breadcrumbs
(`tags:`, `related:`, `superseded-by:`, `archived-from:`) — never by enumerating
raw directory listings. This is the load-bearing information-architecture
principle. A flat catalog rots and an agent that browses loads three wrong docs
for every right one. The per-directory index (ADR-0005) exists so you can find
the *one* doc that answers the question and synthesize immediately, instead of
paying to read everything nearby. Read with intent.

## 2 · Findings to disk — or they don't exist

Knowledge that lives only in the conversation is DEAD at the next compaction. A
finding, a dead-end, a rejected alternative, a verification result — if you have
it and it matters, it goes to disk *the moment you have it*, in the place it
belongs: a decision → an ADR; a gotcha → a lesson; an investigation result → a
checkpoint or a research track. A verdict carries its evidence with it (a
`log.md` timestamp, a commit SHA, a command's output). This is why the system has
so many typed homes for writing things down: the alternative is re-deriving the
same expensive conclusion next week, having forgotten you already reached it.

## 3 · IMPL → WIRED — tests-pass is not done

The most expensive recurring trap is code that compiles and passes its tests but
is never reachable from a production entrypoint — built, green, and dead. A unit
of work is not done when its tests are green; it is done when a path traces from a
real entrypoint to the new code. **Prove reachability**, don't assume it. The
proof is a menu, best-tool-first: an LSP find-references, then a call-hierarchy,
then a language call-graph tool (`{{CODE_INTEL_TOOL}}` if you have one), then the
honest floor — grep the callers — and, failing all of those, a written manual-
trace note. Record the IMPL / WIRED / DEFER state; a dead-code warning is a wiring
failure, not noise.

## 4 · Adversarial separation — the reviewer is never the builder

An executor auditing its own work is not review; it is the same mind grading its
own exam. Independent verification means a *clean-context* checker that re-derives
the claim against the live tree with no authorship stake — and it applies to
designs, not just code. A design reviewed only by its author is unreviewed. This
is why the dispatch framework (ADR-0006) makes the verifier a separate gate stage
and why non-trivial designs get an adversarial pass *before* implementation, not
only after. The failure it prevents: a builder's self-review passing work that an
independent pass immediately fails.

## 5 · Ceremony as fossil — trust it before you trim it

Every discipline in this system is the fossil of a real, expensive failure. The
rules can look like bureaucracy from the outside — verify cwd before mutative
commands, write the alternative down before you act, never bypass the gate — but
each earned its place by being the thing that was skipped the day something broke.
When you are tempted to cut a rule because it feels like overhead, assume it is
load-bearing until you can name the failure it was guarding against and argue that
failure cannot recur here. Trim from evidence, not from impatience. (And when a
rule genuinely no longer fits — ADR-0008 — recalibrate it deliberately and write
down why; do not just ignore it.)

## 6 · Write-disciplines — three kinds of document, three ways to write

Not every doc is written the same way, and mixing the modes corrupts the record:

- **Update-in-place (living state).** `now/{status,work-plan,open-questions}.md`
  are rewritten to reflect current reality every session. They are always "now,"
  never a history.
- **Append-only (growing ledgers).** `log.md`, the `decisions/` ADRs, and the
  `lessons/` ledger grow by *adding*. An ADR is never edited to change its
  conclusion — it is superseded by a new one (`status: superseded` +
  `superseded-by:`). History is preserved, not overwritten.
- **Write-once / immutable (checkpoints).** A `checkpoints/` sitrep is never
  edited after it is written. New information is a NEW checkpoint that references
  the prior one. Immutability is what makes a checkpoint a trustworthy record of
  what you knew at that moment — including the dead-ends a later summary would
  quietly drop.

Keep the modes straight and the record stays honest. Blur them — edit a
checkpoint, rewrite a lesson, let `now/` accumulate history — and you lose exactly
the signal the system was built to preserve.

## Where to go next

- The eight framework ADRs (`0001`–`0008`) — the full argument for each decision,
  with the alternatives that were rejected.
- `CONVENTIONS.md` — the schema contract these principles are encoded into.
