<!--
parity/ routing catalog — the OPT-IN rewrite-conformance tier (Full profile).
Instantiate to `.agent-docs/parity/index.md`. This tier is a SIBLING of
`traceability/`, never a child: PARITY ≠ WIRED
(framework-rationale/0015-rewrite-conformance-parity-ledger.md).
Fill the <angle-bracket> placeholders with your reference/port names and drop
the EXAMPLE blocks once you have real ledger docs. Delete this comment when filled.
-->

---
provenance: kit-template
template-version: 1.0.0
created: <YYYY-MM-DD>
last-modified: <YYYY-MM-DD>
tags: [index, routing, parity, conformance, rewrite]
related: [ledger]
---

# parity/ — routing catalog

The **rewrite-conformance ledger**: does the new implementation behave
**identically** to the reference it replaces? One question, one home. Schema
authority: `../CONVENTIONS.md`.

> **PARITY ≠ WIRED — two orthogonal axes.**
> - **WIRED** (`../traceability/index.md`) asks *"is this code reachable from a
>   production entrypoint?"* — the IMPL→WIRED reachability proof.
> - **PARITY** (here) asks *"does the new implementation produce byte-identical
>   normalized output to the reference on the golden oracle?"* — behavioral
>   conformance.
>
> A case passing PARITY says nothing about whether the code is WIRED; a WIRED
> path says nothing about byte-conformance. Different axes → separate ledgers.
> Mixing parity verdicts into `traceability/` would launder a conformance claim
> as a reachability proof — so this dir is a deliberate sibling, never a child.

## The oracle contract

Conformance is judged against the **golden corpus** — deterministic byte fixtures
recorded off the reference implementation `<reference-name>` by
`scripts/<recorder>`. The runner replays each case against the binary under test
and must match stdout, stderr, exit code, and every file it writes, **after the
closed normalization set** in `<corpus>/README.md`.

- Contract + normalization grammars: `<corpus>/README.md`.
- Reproducibility check: `scripts/<recorder> --check` (re-recording is a
  CONTRACT CHANGE — same scrutiny as editing the frozen-contract spec, not a fix).
- Oracle honesty: the reference `<reference-name>` passes the SAME suite,
  unconditionally, pinned so no env var redirects the oracle onto the port.

## Ledgers

<!-- EXAMPLE (delete on the first real ledger doc):
- ⭐ `ledger.md` — the append-only parity table (date · impl ref · cases
  passed/total · verdict · notes). **Open when:** recording or checking a slice's
  conformance run. **Carry-away:** reference run ORACLE-HONEST <n>/<n>; port
  <name> PASS <n>/<n> at <ref>, sabotage-proven non-vacuous.
- `<slice>-parity-map.md` — the honest residue: every known micro-divergence of
  the port vs the reference, each with a reachability verdict. **Open when:** "is
  this port-vs-reference difference a bug or a recorded carve-out?"
-->

- ⭐ `ledger.md` — the append-only parity table. **Open when:** recording or
  checking a slice's conformance run against the golden corpus. **Carry-away:**
  `<how many cases pass on the reference vs each port ref, and where the sabotage
  proof lives>`.
- `<slice>-parity-map.md` — the divergence residue with reachability verdicts.
  **Open when:** classifying a port-vs-reference difference as carve-out or bug.
  **Carry-away:** `<the divergence classes and which, if any, are reachable>`.

## Maintenance

UPDATE-IN-PLACE (append a row per conformance run). Adding/retiring a ledger doc
updates this index in the same change. Carry-away claims must be traceable to the
source doc. This index and its ledgers are a sibling of `traceability/` — never
fold a parity row into the WIRED ledger.
