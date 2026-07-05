<!-- EXAMPLE — delete after reading; shows the SHAPE of a good dispatch-charter (a fenced, single-owner sub-agent work-spec with a named wiring-proof target and a clean-context verifier gate). A real one lives at .agent-docs/dispatch-charters/YYYY-MM-DD-<wave>-<slug>.md. -->

---
provenance: llm-reviewed
status: certified
template-version: 1.0.0
# work-unit: WU-0042  — the parent work-unit (a real front-matter field per §4; commented so this
#   isolated example lints without a live now/work-plan.md).
charter-id: FR-0031
wave: 3
created: 2026-07-02
last-modified: 2026-07-02
base-commit: 9c4f1ab
model-tier: standard
related: [WU-0042, LP-023, OQ-018]
rollback-handle: 9c4f1ab
operator-eyes-on: false
tags: [dispatch, wave-3, ratelimit]
---

# FR-0031 — Implement the limiter-map eviction sweeper so per-IP buckets are reclaimed

This charter closes the memory-safety gap ADR-0007 accepted and LP-023 flagged: the per-IP token-bucket
map grows unbounded. It adds a background sweeper that evicts idle buckets, and — the acceptance bar —
proves the sweeper is actually reachable from the daemon entrypoint (IMPL → WIRED), not merely written.
It is a single-owner leg of WU-0042's wave 3; no sibling charter touches the `internal/ratelimit`
package this wave, so file ownership is disjoint by construction.

## 1. Charter (PLANNER)

### File ownership (one-file-one-owner)

- `internal/ratelimit/sweeper.go` — **NEW**, owned by this leg (the sweeper goroutine + ticker).
- `internal/ratelimit/limiter.go` — owned by this leg this wave (add `lastSeen` bookkeeping + an
  `Evict(olderThan)` method to the in-memory bucket store).
- `internal/ratelimit/sweeper_test.go` — **NEW**, owned by this leg (unit test).

No other leg in wave 3 owns any `internal/ratelimit/*` file; verified disjoint against the wave-plan
before dispatch.

### Recalibrated scope (vs the LIVE tree)

- Surveyed via `gopls` (symbol overview) + grep on 2026-07-02 @ `9c4f1ab`.
- LIVE reality: `bucketLimiter` in `limiter.go` holds `mu sync.RWMutex` + `buckets map[string]*rate.Limiter`
  and already takes the write lock in `getOrCreate`. There is **no** `lastSeen` field yet — the sweeper
  needs one, so this leg adds it (the wave-plan assumed a timestamp already existed; delta: it does not).
- Expected diff shape: ~3 files · touches only `internal/ratelimit/`. ~90 net new lines.

### Wiring-proof target (IMPL → WIRED)

- **Reachable from:** `cmd/sparrowd/main.go` → `httpx.NewRouter(...)` → the rate-limit middleware
  constructor, which must START the sweeper goroutine. "Done" = a live daemon reclaims idle buckets,
  not "`Evict()` compiles."
- **Reachability proof — first available on this menu:** `gopls` call-hierarchy / references →
  LSP find-references → a language call-graph tool → grep-the-callers (the honest floor) →
  manual-trace note. Use the highest available; record the query + its output.
- Record IMPL / WIRED / DEFER in `traceability/` keyed to WU-0042.

### Verifier gate (clean-context reviewer — NEVER the builder)

- [ ] The sweeper goroutine is **started from a production entrypoint** — re-derive the call path
      `cmd/sparrowd/main.go → … → sweeper start` INDEPENDENTLY of the builder's claim; an empty path =
      IMPL-not-WIRED = reject.
- [ ] Eviction takes the map's **write lock** (no data race with `getOrCreate`); confirm against the
      live source, not the PR description.
- [ ] A behavior test exists that FAILS without the sweep (map does not shrink) and passes with it.

### Scope

1. Add `lastSeen time.Time` to each bucket entry; stamp it on every `Allow`.
2. Add `Evict(olderThan time.Duration)` to the in-memory store — under the write lock, delete buckets
   whose `lastSeen` is older than `olderThan`.
3. Add `sweeper.go`: a goroutine that `time.Ticker`s every sweep interval and calls `Evict(idleTTL)`,
   with a `context.Context` for clean shutdown.
4. Start the sweeper from the middleware constructor and return a stop func the daemon defers.

### Scope-boundaries (stay in lane)

- **NOT** the distributed/global limiter (that is OQ-014 — a different WU; do not start it).
- **NOT** making the interval/TTL configurable — that is OQ-018, operator-owned; hard-code the agreed
  5m sweep / 10m idle-TTL constants and REPORT the config question in `discoveries[]`, do not act on it.
- **NOT** refactoring `limiter.go` beyond the two additions above, even if something nearby looks
  improvable. Report it; do not touch it. If an out-of-scope issue BLOCKS the task, HALT and report —
  do not improvise a workaround or widen scope to get unblocked.

### Acceptance criteria

- [ ] `go build ./...` clean
- [ ] `golangci-lint run` clean — warnings are errors; no unjustified lint suppressions
- [ ] `gofmt -l .` clean (no files listed)
- [ ] `go test ./...` green; **a behavior change OWES a test that fails without it** — the sweep test
      must fail on the pre-sweeper tree
- [ ] Hands-on: ran `sparrowd` locally, drove traffic from several IPs, waited past the TTL, and
      watched the bucket count drop (green tests ≠ ran it)
- [ ] **IMPL → WIRED:** `gopls` call-hierarchy proves `Evict` is reachable from `cmd/sparrowd/main.go`;
      row recorded in `traceability/`
- [ ] No new `panic()` in library code; the sweeper propagates shutdown via context, it does not panic

### Dependencies

- Charters: none (disjoint from the rest of wave 3).
- ADRs that lock substance: ADR-0007 (the interface + the unbounded-map cost this remediates).
- Commits required first: `9c4f1ab` (the Limiter is already landed — this builds on it).

### Integration-points

- `internal/ratelimit/limiter.go` — the shared store type; the dependency root both this leg's sweeper
  and the existing middleware read/write. Anchor the store's locking rule with a REVISIT
  `claim:` note if the "every mutator holds `mu`" invariant is restated across the sweeper + the store.
- `internal/httpx/middleware.go` — the constructor that must START the sweeper and hand its stop-func to
  the daemon; the WIRED path passes through here.

---

## 2. Brief-back (BUILDER → PLANNER)

**My understanding:** add idle-eviction to the in-memory limiter store (new `lastSeen` + `Evict`), run
it from a background sweeper started by the middleware and stopped by the daemon, and PROVE the sweeper
is reachable from `cmd/sparrowd/main.go` — not just that it compiles. Constants (5m/10m) hard-coded;
config question reported, not built.
**Ambiguities / questions:** should the stop-func be returned from the constructor or registered on a
lifecycle manager? — the daemon has no lifecycle manager yet, so a returned stop-func the `main()`
defers is simplest.
**Planner response:** returned stop-func is correct; do not introduce a lifecycle manager this leg.
**Planner sign-off:** [x] brief-back accepted / [ ] re-charter required

---

## 3. State reconnaissance (PLANNER, pre-dispatch)

```
$ git rev-parse HEAD
9c4f1ab3e2...
$ git log -1 --format='%H %s' internal/ratelimit/limiter.go
9c4f1ab feat(ratelimit): wire token-bucket Limiter into redirect middleware
$ gopls references internal/ratelimit/limiter.go:#bucketLimiter.Allow
  internal/httpx/middleware.go:41  (sole caller — the redirect chain)
```

**Drift check vs `base-commit`:** [x] HEAD matches base / [ ] advanced, integration-points unchanged /
[ ] integration-points changed → RE-CHARTER
**Verdict:** safe-to-proceed

---

## 4. Gate verdicts (AUTOMATED + BUILDER)

- `go build ./...`: pass
- `golangci-lint run`: pass (0 findings)
- `gofmt -l .`: pass (no files listed)
- `go test ./...`: pass — 41 tests, +1 new (`TestSweeperEvictsIdleBuckets`)
- Hands-on run: started `sparrowd`, drove ~50 distinct source IPs, bucket count peaked at 50, dropped
  to 0 within one sweep after the idle-TTL elapsed — observed via a debug `/metrics` count.
- IMPL → WIRED: `gopls call-hierarchy` on `Evict` → `startSweeper` → `NewRateLimitMiddleware` →
  `httpx.NewRouter` → `cmd/sparrowd/main.go:run`. Chain non-empty → WIRED. Row added to
  `traceability/` keyed to WU-0042.
- Custom verifications: re-ran the LP-023 load profile (200k unique IPs) — RSS held at ~140 MB flat
  (pre-sweeper: ~1.2 GB climbing).

---

## 5. Verifier report (VERIFIER — clean-context, never the builder)

### Wiring proof (production-reachability, not test-pass)

- Reachability query (independent re-derivation): `gopls call-hierarchy` on `sweeper.Evict` traced to
  `cmd/sparrowd/main.go:run` without consulting the builder's note. Chain confirmed.
**Verdict:** WIRED

### Cross-layer lockstep

- Locking-rule invariant ("every mutator of `buckets` holds `mu`") holds for both `getOrCreate` and
  the new `Evict`: [x] yes / [ ] drift
- REVISIT `claim:` ledger row for the lock invariant updated in the same change: [x] yes / [ ] no

### Per-file analysis (where non-obvious)

- `internal/ratelimit/sweeper.go`: eviction runs under `mu.Lock()`; the ticker goroutine exits on
  `ctx.Done()` — no leaked goroutine. Evidence: read the source + ran `go test -race ./internal/ratelimit/`,
  clean.
- `internal/ratelimit/limiter.go`: `lastSeen` stamped inside the existing `Allow` critical section — no
  new lock ordering introduced.

### Remediation requests

- ✅ No remediation; charter certified.

---

## 6. Remediation log (if needed)

*(none — certified on the first pass)*

---

## 7. Operator decision (when required)

**Trigger:** none — `operator-eyes-on: false`, not a wave-merge boundary, no destructive op. Merged by
the orchestrator on green gates + verifier certification.
**Operator notes:** n/a
**Decision:** [x] approved / [ ] rejected / [ ] re-work
**Linked commits:** builder SHA: `d4e77c1` · integration/merge SHA: `d4e77c1` (no worktree isolation
this leg) · `rollback-handle`: `9c4f1ab`

---

## Frontmatter `status:` lifecycle

`drafting` → `dispatched` → `in-remediation` → **`certified`** → `merged` → `rolled-back`
(this charter is at `certified`, merged as `d4e77c1`).

## Related

- WU-0042 (parent work-unit) · ADR-0007 (the decision that accepted the cost this closes) ·
  LP-023 (the near-miss that justified it) · OQ-018 (the config question this leg reported, not built).
- The dispatch contract (scope-fence, halt-and-report) governs this charter's builder.
