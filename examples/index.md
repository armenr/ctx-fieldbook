<!-- EXAMPLE — delete after reading; shows the SHAPE of a good per-dir index (route, don't browse). This one routes the sample gallery; a real per-dir index lives at <dir>/index.md. -->

---
provenance: llm-reviewed
template-version: 1.0.0
created: 2026-07-03
last-modified: 2026-07-11
tags: [index, examples]
related: [sample-adr, sample-checkpoint, sample-lesson, sample-handoff, sample-review, sample-dispatch-charter]
---

# examples/ — index

**These are illustrative, filled-in samples — one per doc type — for a fictional project (Sparrow, a
small self-hosted URL-shortener HTTP service in Go). They exist to show you the SHAPE and feel of each
doc when it is real, using plausible values instead of `{{PLACEHOLDER}}` tokens. They are NOT part of
your `.agent-docs/` and are safe to DELETE once you have read them.** When you author the real thing,
instantiate from `templates/`, not from these — the templates carry the guidance comments and the
`template-version`.

The six samples share one coherent thread (WU-0042: rate-limiting Sparrow's redirect endpoint) so you
can see how the doc types cross-reference each other by ID.

## Recording a decision

- 🔨 `sample-adr.md` — an architecture decision (ADR-0007: token bucket behind a `Limiter` interface).
  **Open when:** you want to see what a *substantive* `## Alternatives Considered` looks like — four
  rejected options, each with the reason that made it lose.
  **Carry-away:** the rejected options ARE the value; the ADR is authored BEFORE the work, not after.

## Capturing state at a boundary

- 🔨 `sample-checkpoint.md` — a 10-point zero-loss sitrep, mid-implementation, with a live pause point.
  **Open when:** you want to see how dead-ends (point 6) and an exact in-flight stop (point 4) are
  preserved — the things a naive summary silently drops.
  **Carry-away:** all ten points are mandatory; point 6 (dead-ends) is the reason the file exists.
- 🔨 `sample-handoff.md` — the 11-section curated cold-start surface, with Anti-assumptions +
  Detour-chain populated.
  **Open when:** you want the shape of a session handoff — especially §Anti-assumptions ("looks like X
  → actually Y") and §Detour-chain (the side-quest map).
  **Carry-away:** the handoff orients and curates; it points AT the checkpoint, which preserves.

## Recording durable knowledge

- 🔨 `sample-lesson.md` — a near-miss lesson (LP-023) with the three-axis front-matter filled.
  **Open when:** you hit a near-miss and want the shape — Question · Claim · Evidence · Trigger · what
  almost happened · what made the save reliable · recurrence count.
  **Carry-away:** the title is the CLAIM ("input-keyed maps must be bounded"), not the topic; the
  three axes are provenance × maturity × severity.

## Recording review findings

- 🔨 `sample-review.md` — a fully-populated adversarial review (REV-001) of the WU-0042 token-bucket
  limiter: six findings spanning every severity (BLOCKER → NIT) and all four dispositions.
  **Open when:** you want the shape of a GOOD *filled* review — how a NIT still earns a disposition, how
  an untestable finding is TRACKED → OQ-014 (with a Deferred-obligations note) instead of dropped, and
  the range the test-obligation column holds (named RED-on-HEAD tests · `unbound → <owner>` · n/a-by-policy).
  **Carry-away:** capture ALL feedback — every severity, never just the blockers — and give each finding
  an EXPLICIT disposition; that discipline is the whole point, the blockers are the easy part.

## Fanning work out to a sub-agent (Full profile)

- 🔨 `sample-dispatch-charter.md` — a fenced single-owner work-spec (FR-0031: the eviction sweeper),
  shown at `status: certified` with the full lifecycle filled in.
  **Open when:** you are decomposing a work-unit into a sub-agent leg and want the shape of a charter —
  one-file-one-owner, a named wiring-proof (IMPL→WIRED) target, and a clean-context verifier gate that
  is NEVER the builder.
  **Carry-away:** "done" is production-reachability proven independently, not test-pass; the scope
  fence + halt-and-report keep the agent in its lane.

<!-- Markers: ⭐ canonical hub · 🔨 actionable · 🧭 proposal awaiting ratification. -->
