<!--
The parity map — the HONEST RESIDUE of a rewrite: every place the new
implementation is NOT byte-identical to the reference, each with a reachability
verdict. Instantiate to `.agent-docs/parity/<slice>-parity-map.md`, one per slice
that produces residue. The golden corpus + the differential falsifier layer prove
everything OUTSIDE this list; a row here is acceptable ONLY while its
"reachable from a real producer?" answer stays NO. When a row becomes reachable,
it becomes a bug with a test obligation. Delete this comment when filled.
-->

---
provenance: kit-template
template-version: 1.0.0
created: <YYYY-MM-DD>
last-modified: <YYYY-MM-DD>
work-unit: WU-NNNN
tags: [parity, divergences, rewrite]
related: [ledger, <FR-NNNN>]
---

# `<slice>` parity map — known micro-divergences (`<port-name>` vs `<reference-name>`)

The honest residue of `<FR-NNNN>`: every place the port's behavior is NOT
byte-identical to the reference, each with its reachability verdict. The golden
oracle and the differential falsifier layer prove everything OUTSIDE this list. A
divergence here is acceptable ONLY while its "reachable from a real producer?"
answer stays **no** — if a row becomes reachable, it becomes a bug.

**Real producers** (the closed set that can reach the port in production): `<list
them — e.g. the two service binaries which emit only canonical records, the
clients, hand-typed input>`. A divergence no member of this set can trigger is a
carve-out, not a defect.

## Chartered scope divergences (deliberate, DEFER-tracked)

Surfaces you deliberately did not port in this slice. Each carries a DEFER row in
`../traceability/ledger.md` and a pointer to the slice that lands it.

<!-- EXAMPLE (Sparrow):
- **`GET /admin` dashboard is not ported** (chartered to the TUI slice). The Go
  `sparrowd` returns 501 with `not implemented in this build`; `sparrow-ref`
  still serves the admin surface in production. DEFER → admin slice
  (traceability ledger row).
- **`-h/--help` BODIES are content-parity, not byte-parity**: the reference's
  flag-formatter alignment is not cloned. The usage LINES and every error line
  ARE byte-parity (differential-tested). No golden case invokes `-h`.
-->

## Input-acceptance micro-divergences (unreachable from real producers)

Inputs the reference and port handle differently, that no real producer can emit.
State, per row, *why* it is unreachable.

<!-- EXAMPLE (Sparrow):
- **Non-canonical percent-encoding in a stored short code** (`%2F` vs `/`): the
  reference's parser folds it, the port preserves the literal. No writer emits
  it — codes are minted from the base62 alphabet only.
- **Cursor/offset above int64 in a stored counter file**: the reference's
  bignum parse takes the past-EOF reset; the port overflows to the
  unreadable-counter warning. Net effect identical (both reset, exit 0) — only
  the warning CLASS differs. Unreachable: a >2^63 offset means a >9-exabyte data
  file; real writers only store offsets ≤ file size.
-->

## Environment- / language-shaped divergences (contract carve-outs)

Bytes outside the frozen surface by nature — per-language error prose, signal
behavior, TTY-only wrap. The contracted SHAPE (prefix/suffix, streams, exit
codes) is differential-tested per binary; the interior prose is carved out.

<!-- EXAMPLE (Sparrow):
- **Runtime error text inside a 500 body**: `sparrow-ref` emits an interpreter
  traceback above the contracted `internal error` line; `sparrowd` emits a Go
  error string. Same carve-out class — the exit code + the final contracted line
  are byte-parity; the trace above it is explicitly outside the contract.
- **SIGINT outside long-poll**: the reference exits 130; the un-handled port dies
  by signal (shells report 130; process state differs). No golden case covers
  signals.
-->

## Wiring residue (record DEFER rows in traceability/, not here)

Symbols that are IMPL-but-not-yet-WIRED after this slice belong in the
`traceability/` ledger as DEFER rows — NOT in this map. This section is a pointer,
not a second home: PARITY ≠ WIRED. Name the traceability rows here only as a
cross-reference so a reader of the parity map can find the wiring story.
