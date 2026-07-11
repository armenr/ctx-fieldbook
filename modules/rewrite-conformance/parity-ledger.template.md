<!--
The parity ledger — one row per conformance run of the rewrite-conformance gate.
Instantiate to `.agent-docs/parity/ledger.md`. Append-only; UPDATE-IN-PLACE.
The FIRST row is always the REFERENCE run that proves the harness itself is
honest (oracle honesty) — a port row may only be trusted after it exists.
Parity results live HERE, never in `traceability/` — PARITY ≠ WIRED
(framework-rationale/0015-rewrite-conformance-parity-ledger.md).
Replace the EXAMPLE block with your real reference row before the first port run.
Delete this comment when filled.
-->

---
provenance: kit-template
template-version: 1.0.0
created: <YYYY-MM-DD>
last-modified: <YYYY-MM-DD>
tags: [parity, conformance, rewrite, ledger]
related: [index]
---

# parity ledger — `<port-name>` conformance vs the `<reference-name>` reference

## Purpose

Track the new implementation's **behavioral conformance** against the reference
it replaces. One row per conformance run: how many golden cases the binary
reproduces byte-identically (after the closed normalization set), and the
resulting verdict. This ledger is a **sibling of `../traceability/`** — never a
section of it (PARITY ≠ WIRED).

## The oracle contract

Parity is decided by the **golden corpus** — deterministic byte fixtures recorded
off the reference by `scripts/<recorder>`. The runner replays each case's inputs
against the binary under test and must produce byte-identical **normalized**
output: stdout, stderr, exit code, and every file written. The contract,
invariants, and the normalization grammars (the only permitted divergence) live
in `<corpus>/README.md`. Re-recording is a **CONTRACT CHANGE**, not a fix.

## Row schema

| Column | Meaning |
|---|---|
| `date` | LOCAL date of the run |
| `impl ref` | which binary + at which commit — the reference on the first row, then each port slice |
| `cases` | golden cases `passed/total` for this run |
| `verdict` | `ORACLE-HONEST` (reference proving the harness) · `PASS` · `FAIL` (+cases) · `BLOCKED` (gate could not run) |
| `notes` | the acceptance rule this row satisfies, the non-vacuity/sabotage proof, and a pointer to the divergence map |

**Write-discipline:** APPEND a row per conformance run; never rewrite history. The
first row is the reference run (oracle honesty). A `FAIL` row stays — it is the
record that the gate bit.

## Ledger

<!-- EXAMPLE (delete this block once your real reference row lands):
Scenario: Sparrow's shorten/redirect service is being reimplemented — the legacy
`sparrow-ref` is frozen as the conformance oracle, and the Go `sparrowd` must
reproduce its HTTP responses byte-for-byte. Golden corpus = 18 recorded
request→response transcripts; normalizers = `<CODE>` (base62 short code), `<TS>`
(RFC3339 created-at), `<ROOT>` (temp data dir), value-discriminating against the
seed sentinels (`code-000…` ids, year-1970 timestamps).

| date | impl ref | cases | verdict | notes |
|---|---|---|---|---|
| 1970-01-01 | `sparrow-ref` (reference) | 18/18 | ORACLE-HONEST | AR-2: the harness proven against the reference before judging any port; non-vacuity BOTH ways — corrupting the `<CODE>` normalizer to eat seeds → reference goes RED on 6 cases; loosening the `<TS>` grammar to match seeds → RED on 4. Suite green only under the exact closed set (`TestNormalizationIsClosed`). |
| 1970-01-01 | `sparrowd` @ a1b2c3d | 18/18 | PASS | AR-1: same runner loop as the reference (oracle pinned — env cannot redirect it); AR-3: non-vacuity proven by 3 port sabotages (base62-alphabet swap → `create` case RED; drop the 404 body → `resolve-miss` RED; off-by-one Location header → `redirect` RED; all restored green). Differential layer byte-diffs both binaries on ~30 corpus-uncovered inputs — 1 real divergence found + fixed. Residue: `w01-parity-map.md`. |
-->

| date | impl ref | cases | verdict | notes |
|---|---|---|---|---|

_First row = the reference run that proves the harness itself (oracle honesty).
Port rows land per slice; parity is never recorded as WIRED._
