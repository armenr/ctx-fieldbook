---
provenance: kit-template
created: 2026-07-11
last-modified: 2026-07-11
tags: [module, rewrite, conformance, parity, oracle, opt-in]
related: [parity-index.template, parity-ledger.template, parity-map.template]
---

# Module: rewrite-conformance (Full-profile, OPT-IN)

**Not wired by default.** Enable this only when you are **replacing an existing
implementation with a new one and require behavioral parity** — a port to a new
language, a rewrite of a legacy service, a second implementation that must agree
with the first byte-for-byte on the wire. It presumes the `traceability/` tier
(Full) — the parity ledger is that tier's **sibling**, never a row in it (see
PARITY ≠ WIRED below).

If you are building something new with no predecessor to conform to, **skip this
module** — there is no oracle, so there is nothing to gate. It is dead ceremony
for greenfield work.

## What it gives you

A **parity ledger tier** (`.agent-docs/parity/`) — a home for one question and
only one: *does the new implementation behave identically to the reference?*
It ships three instantiable docs and one discipline:

- `parity/index.md` — the routing catalog for the tier (from `parity-index.template.md`).
- `parity/ledger.md` — the append-only conformance ledger: one row per run
  (`date · impl ref · cases passed/total · verdict · notes`), whose **first row
  is the reference run that proves the harness itself** (from `parity-ledger.template.md`).
- `parity/<slice>-parity-map.md` — the **honest residue**: every place the new
  implementation is NOT identical to the reference, each with a reachability
  verdict (from `parity-map.template.md`).

The discipline these encode is the **rewrite-conformance gate**, and it stands on
four load-bearing rules.

## Rule 1 — the golden corpus IS the contract (freeze fixtures, not prose)

Freeze the reference's behavior as **executable byte fixtures** — recorded
transcripts of the reference implementation's observable output (stdout, stderr,
exit code, and any files it writes), captured by a recorder script and stored on
disk. The fixtures + the normalization rules (Rule 2) ARE the contract's only
authority. Do NOT freeze a prose spec instead: prose-reviewed designs pass
mechanism-false, and only executable fixtures make the review falsifiable
(cite a case at an offset) and the gate mechanical.

Re-recording the fixtures is a **CONTRACT-CHANGE event** — it demands the same
scrutiny as editing the frozen-contract section of your design doc, never a
routine fix. When you find a contract bug during the port, fix it in the
**reference first**, re-record, then port — never let the port define the
contract.

## Rule 2 — normalization is a closed, value-discriminating set

Two correct runs of the reference differ only in non-deterministic bytes — a
timestamp, a generated id, a temp path, a timing-dependent message. Those are
the **only** permitted divergences, and each is pinned as an **exact anchored
grammar** in the corpus README, applied in a fixed order before comparison.
Everything else — field order, separators, warning text, exit codes — is
contract, byte for byte.

The normalizers must be **value-discriminating**: they normalize *live* values
but must NOT match the *seed sentinels* your fixtures use for deterministic
inputs (seed a timestamp outside the live grammar, seed ids that are not
id-shaped), so seeded values anchor literally and live values normalize in the
same file. Prove closure **both ways** — live sentinels normalize, seed
sentinels survive — as a named test. A fifth, looser normalizer that "just makes
it pass" is a hole in the contract; adding one is a contract change, not a fix.

## Rule 3 — oracle honesty (one suite, both implementations)

This is the rule the work discipline already names — see
`reference/work-discipline.md` § *The oracle-honesty rule* (do not restate it
here). The concrete shape for a rewrite:

- **One** conformance suite, driven by a **swap-in binary seam** — the runner
  replays each golden case against *whatever binary it is pointed at* (subprocess,
  never linked), and diffs normalized output against the fixture.
- The **reference implementation must pass the suite first**, unconditionally, in
  the same run — pinned so no environment variable can redirect the oracle onto
  the thing under test. If the reference does not pass its own golden corpus, the
  corpus is a lie and every later parity claim is worthless.
- Prove the suite **non-vacuous by sabotage, in BOTH directions**, and record it:
  a deliberately-corrupted **normalizer/oracle** must make the reference run go
  RED (proves the harness can fail), and a deliberately-corrupted **port** must
  go RED on a specific case for the right reason (proves the harness catches a
  real defect). A suite that passes a wrong double tests nothing.

## Rule 4 — PARITY ≠ WIRED (why this is a separate ledger)

PARITY and WIRED are **orthogonal verification axes** and must never be conflated:

- **WIRED** (`traceability/`) asks *"is this code reachable from a production
  entrypoint?"* — the IMPL→WIRED reachability proof.
- **PARITY** (`parity/`) asks *"does the new implementation produce output
  identical to the reference on the golden oracle?"* — behavioral conformance.

A case passing PARITY says nothing about whether the code is WIRED; a WIRED path
says nothing about byte-conformance. Recording parity verdicts in `traceability/`
would **launder a conformance claim as a reachability proof** — so parity results
live in their own sibling ledger, and neither ledger ever borrows the other's
column. This is the whole reason the module ships a new tier instead of a new
`kind:` column on the traceability ledger (the kit's
framework-rationale/0015-rewrite-conformance-parity-ledger.md).

## The parity map — divergence is allowed, silently is not

No two implementations are ever *perfectly* identical. The parity map is where
you record the residue honestly, each row carrying a **reachability verdict**. A
divergence is acceptable **only while it is unreachable from a real producer** —
the moment a real caller can reach it, it is a bug, not a carve-out. Three
recurring classes:

| Class | Meaning | Example |
|---|---|---|
| chartered scope | a surface you deliberately did not port yet | an interactive/TTY mode deferred to a later slice |
| unreachable-input edge | inputs the reference accepts/rejects differently, that no real producer can emit | a malformed record only hand-corruption could write |
| per-language / per-env text | environment- or language-shaped bytes outside the frozen surface | an interpreter traceback above a contracted error line |

Each row names *why* it is unreachable. When that reason stops being true, the
row becomes a defect with a test obligation.

## Install (opt-in)

1. Create the tier and instantiate the three docs:

   ```sh
   mkdir -p .agent-docs/parity
   cp modules/rewrite-conformance/parity-index.template.md  .agent-docs/parity/index.md
   cp modules/rewrite-conformance/parity-ledger.template.md .agent-docs/parity/ledger.md
   # per slice/wave, when you have residue to record:
   cp modules/rewrite-conformance/parity-map.template.md    .agent-docs/parity/<slice>-parity-map.md
   ```

   Clear the seeded `EXAMPLE` blocks as you add real rows.

2. Build the corpus + harness as the **bootstrap unit's deliverable** (work
   discipline § *The bootstrap-canary rule*): a recorder script, the golden
   fixtures, the normalization README (Rule 2), and the swap-in runner — with the
   reference passing (Rule 3) and the sabotage proof recorded — BEFORE any port
   code exists. The parity gate then runs inside your existing G1 conformance
   falsifiers; it adds no new hook.

3. Wire the ledger into the routing spine: add a `parity/` row to your
   `.agent-docs/index.md` so the index-completeness lint stays clean, and record
   the PARITY-column-only ledger row for the reference run as acceptance evidence
   for the bootstrap unit.

4. Record the placement ruling once in a project ADR: *parity records live in the
   sibling ledger, never `traceability/` — PARITY ≠ WIRED*. This is the one
   invariant a reviewer will otherwise re-litigate.

## Undo

Delete `.agent-docs/parity/` and its `index.md` row. The corpus and harness are
your own test assets — keep or remove them on their own merits; no other kit
state is kept.

## Related

- `reference/work-discipline.md` — §*oracle-honesty*, §*bootstrap-canary*,
  §*safety-by-construction*, §*the scale-down floor* (the loop this gate runs inside).
- `traceability/` — the WIRED sibling this tier is deliberately NOT part of.
- `framework-rationale/0015-rewrite-conformance-parity-ledger.md` — why the kit
  ships a separate tier rather than a traceability column.
