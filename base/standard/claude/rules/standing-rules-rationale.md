---
provenance: kit-template
created: 2026-07-03
---

# Standing rules — rationale (load on demand)

The companion to `standing-rules-core.md`. Each entry states the generalized failure mode the rule
prevents — the *why* behind the imperative. Read this when a rule feels like ceremony, when you're
tempted to skip one, or when onboarding someone to the discipline. The core file stays terse so it can
be always-on; the cost of the "why" is paid here, on demand.

## cwd-check before mutative git / filesystem ops

The shell's working directory persists between tool calls. A scoped read-only command earlier in the
session (`cd` into a package to run a build or read a file) silently relocates you, and the next mutative
command — a `git add`, an `rm`, a redirect — resolves its paths against that moved cwd, not the root you
think you're in. In a multi-package workspace the classic casualty is a lost worktree: files created in
the wrong package, a commit staged from the wrong tree, or a delete that lands somewhere unexpected.
The four-line check is cheap; the recovery from a mis-rooted mutation is not.

## Ask before destructive actions

Destructive operations are irreversible or expensive to reverse: dropping a datastore, resetting state,
rewriting history, force-pushing, deleting outside the scratch area. Automation that performs these
without a confirmation gate eventually performs one you didn't intend — the cost asymmetry (a one-line
confirm vs. an unrecoverable loss) is the entire justification. Confirm first, always.

## Scope for completeness, not MVP

The recurring, expensive trap is the built-but-not-wired surface: a feature implemented and tested but
never reachable from a real entrypoint, or a path half-finished because "MVP" quietly became the ceiling.
It reads as done — the code exists, the tests are green — but the production path is dead. Building to a
finished, wired state (or writing the deferral down with its reason) is what prevents a backlog of
plausible-looking work that never actually runs.

## The gates must pass; never bypass them

Bypassing a gate (`--no-verify`, silencing a lint, skipping a test) trades a visible failure now for an
invisible one later. The gate encodes a class of defect someone already paid to discover; routing around
it re-admits that class. A strict linter with warnings-as-errors is a deliberate choice, not pedantry:
the alternative is a slow accumulation of "harmless" warnings until the signal is gone and a real defect
hides in the noise. Investigate the failing gate; the failure is information.

## A behavior change owes a test

Tests-passing is not the same as done. A behavior with no test that would fail without it is a behavior
with no guardrail against silent regression — the next refactor can quietly break it and every gate stays
green. The falsifier is what makes the behavior real; without it, "it works" is an unverified claim that
decays the moment someone else touches the code.

## IMPL → WIRED is the acceptance bar

This is the single most expensive recurring failure: code that compiles and passes its unit tests but is
never called from any production entrypoint. It survives review because every local signal is green. It
is only caught when someone asks "does anything actually reach this?" — often much later, after more work
has been built on top of the dead branch. Proving reachability from a real `main()` / served command (via
a code-intel query, an LSP reference search, a call-hierarchy, or the honest grep-the-callers floor) at
acceptance time is what closes the gap. Dead code a linter flags is this failure surfacing, not noise.

## Hands-on acceptance for runtime-facing changes

"Green tests" and "I ran it and watched it work" are different claims. Hermetic tests exercise the code
under assumptions the test author chose; they cannot see an integration seam that was never wired, a
config that only exists in the fixture, or a behavior that's correct in isolation and wrong in the real
loop. For anything runtime-facing, actually running it is the only evidence that the assumptions hold.

## Findings, decisions, and review feedback to disk

Conversation is volatile; it is deleted at compaction and lost at session end. A finding, a rejected
alternative, a dead-end investigation, or a review nit that lives only in the transcript is gone the
moment the context window rolls — and its absence is invisible, so the same dead-end gets re-explored and
the same nit re-discovered. Writing it to its durable home (an ADR, a memory claim, a checkpoint, an OQ)
the moment you have it is what makes the work cumulative instead of amnesiac. The corollary on review
feedback is sharper: an independent verifier routinely finds real defects that an in-workflow pass called
CLEAN, so "CLEAN except a few nits" that drops the nits is discarding exactly the signal that mattered.

## Decision-rationale-with-alternatives, before acting

An ADR written after the fact is a justification, not a decision record — the alternatives get
reverse-engineered to flatter the choice already made. Written *before* acting, the rejected options and
the reasons they lost are the actual value: they stop the team from re-litigating settled questions and
they make a later reversal legible ("we knew about X; here's why it lost; here's what changed"). A
decision doc with an empty Alternatives field is a decision that was never really made.

## Adversarial separation — the reviewer is never the builder

An author cannot reliably review their own work; they share its blind spots and have a stake in its
correctness. Self-review is the failure mode that lets a whole class of defect ship because the one person
who could catch it is the one person motivated not to look. An independent reviewer with no authorship
stake, re-deriving the claim against the live tree, is the control. This applies to designs as much as
code — a design reviewed only by its author is unreviewed, and design defects are the most expensive to
discover late.

## The dispatch contract

A dispatched agent with a fuzzy scope will freelance: fix something adjacent that looked broken, refactor
beyond its lane, or invent a workaround to get unblocked — and those unsanctioned changes land silently,
sometimes colliding with a track no one was watching. The contract (a hard file-scope fence, report-all /
act-only-in-lane, halt-and-report on a blocker, and no agent committing or merging) confines each agent's
authority to exactly its purpose and routes every surprise back to a single serial integration point where
a human can adjudicate it. The residual risk — an agent misjudging in-scope necessity, or failing to notice
something worth reporting — is why the orchestrator reads every diff firsthand and never trusts a
self-report of "done": reproduce the claim against the live tree before acting on it.

## Context lifecycle

Context windows are finite and compaction is lossy. Without deliberate checkpoints, a long session's
hard-won state — the detour map, the dead-ends, the in-flight pause point — is silently summarized away,
and the next session (or the same one after compaction) restarts half-blind. The lifecycle rituals
(`/orient` to load, `/flush` to keep `now/*` honest, `/handoff` before compaction, a write-once checkpoint
at any zero-loss boundary) exist because a naive summary drops exactly the reasoning that was expensive to
produce. Proposing `/handoff` at ~80% usage beats discovering the loss after it happens.

## Currency-check external dependencies

Training data has a cutoff; the ecosystem does not. A version number, an API signature, a deprecation
status, or a "recommended replacement" recalled from memory is a snapshot that may be stale or was never
accurate. Infrastructure and dependency choices built on a stale recollection fail in ways that are hard
to diagnose because the reasoning looked sound. Verifying the exact API you're about to use against
current-year primary docs — not an aggregator, not memory — is the difference between a decision and a guess.

## Never commit secrets, credentials, or regulated / user data

A secret committed to a tracked file is compromised the instant it's pushed and stays in history after
it's "removed" — the only real remediation is rotation. Regulated or user data in a fixture, a log line, or
a checkpoint is a leak with legal weight, and derived artifacts (embeddings, caches, traces) can leak the
content they were derived from. Referencing a path or a store key instead of pasting the value is the
cheap habit that avoids the unrecoverable mistake. Detail in `sensitive-data.md`.
