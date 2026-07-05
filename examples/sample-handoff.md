<!-- EXAMPLE — delete after reading; shows the SHAPE of a good handoff (the 11-section curated cold-start surface, with Anti-assumptions + Detour-chain populated). A real one lives at .agent-docs/now/handoff.md and is UPDATE-IN-PLACE. -->

---
provenance: llm-reviewed
template-version: 1.0.0
created: 2026-07-01
last-modified: 2026-07-01
# work-unit: WU-0042  — a real field per §4; commented so this isolated example lints without a
#   live now/work-plan.md (the WU is named throughout).
tags: [handoff, now, session-state]
related: [WU-0042, OQ-014, OQ-018, LP-023, FR-0031]
---

# Session handoff — READ FIRST — 2026-07-01

## Project in one paragraph

Sparrow is a small self-hosted URL-shortener HTTP service (Go; `cmd/`, `internal/`, `pkg/` layout).
Active initiative: **WU-0042 — add per-client rate limiting to the redirect endpoint** on branch
`feature/redirect-rate-limit`. The algorithm decision is settled (ADR-0007); the remaining work is the
eviction sweeper (FR-0031) that keeps the limiter's memory bounded.

## Current state summary

The `Limiter` interface + in-memory token bucket are implemented, wired into the redirect middleware,
and unit-tested (committed `9c4f1ab`). `go build ./...` and `go test ./...` are green. The eviction
sweeper is uncommitted WIP — `internal/ratelimit/sweeper.go` has an `Evict()` that compiles but is not
yet called by anything (IMPL, not WIRED). See the checkpoint under §Reading order for the full
zero-loss detail.

| Piece | State | Reachable from |
|---|---|---|
| `Limiter` interface + bucket | done, committed | redirect middleware ✅ |
| middleware wiring | done, committed | `cmd/sparrowd/main.go` ✅ |
| eviction sweeper | IMPL, **not WIRED** | (no caller yet) ⚠️ |
| load harness | exists, gated | not run by `go test ./...` |

## Important context

- Decision rationale lives in **ADR-0007** (token bucket behind a `Limiter` interface) — read it by ID
  rather than re-deriving; the interface seam is deliberate (keeps OQ-014's Redis path a swap).
- **LP-023** is the near-miss that justifies FR-0031 — the unbounded map is a real OOM risk, not
  theoretical.
- Standing rule in force: **IMPL → WIRED is the acceptance bar, not test-pass.** The sweeper is not
  "done" until a path traces from `cmd/sparrowd/main.go` to `Evict()`.

## ⚠️ Anti-assumptions / traps

- **"The `Limiter` interface has no callers in `cmd/` → it's dead."** WRONG. It is reached through the
  middleware chain in `internal/httpx/middleware.go`, not called directly from a `main()`. Prove
  reachability by grepping for the method call `.Allow(`, not the type name `Limiter`.
- **"`go test ./...` is green → the OOM path is covered."** WRONG. The load harness
  `test/load/redirect_flood_test.go` is behind `//go:build load` and is NOT part of `go test ./...`.
  Unit tests each build a single limiter and never exercise the cross-request / high-cardinality path —
  which is exactly how the request-context dead-end (0% rejection) and the unbounded map (LP-023) both
  slipped past green tests.
- **"The sweep interval / idle-TTL are settled."** They are hard-coded (5m / 10m) as a
  keep-moving placeholder — that is an *open question* (OQ-018), not a decision. Do not treat the
  constants as load-bearing.

## Detour-chain

- **MAIN → WU-0042** (rate-limit the redirect endpoint).
  - **Detour A — algorithm choice.** Spawned by: needing a per-client policy. Found: token bucket wins
    over fixed/sliding window; an interface seam keeps the Redis path deferrable. → **RESOLVED**
    (ADR-0007).
  - **Detour B — unbounded memory.** Spawned by: a load run showing RSS climb to ~1.2 GB at ~200k
    unique IPs. Found: the per-IP map has no eviction — a latent OOM. → **RESOLVED as a finding**
    (LP-023), remediation handed to FR-0031.
  - **Detour C — the eviction sweeper.** Spawned by: Detour B. Status: **OPEN / in-flight** — `Evict()`
    written but not wired; sweep-interval question is OQ-018. This is the resume point.

## Immediate next steps

1. Finish `Evict()` in `internal/ratelimit/sweeper.go` (drop buckets whose `lastSeen` is older than
   the TTL, under the map's write lock).
2. Start the sweeper ticker from the middleware constructor, then **prove WIRED**:
   `gopls call-hierarchy` on `Evict` should trace to `cmd/sparrowd/main.go`. Record the IMPL→WIRED
   result in `traceability/`.
3. Add a sweep unit test (insert N buckets → advance the fake clock past the TTL → one sweep → assert
   the map shrank).
4. **Verify-after-the-fact gate (do NOT trust green unit tests here):** re-run the *load* harness with
   the high-cardinality profile —
   `go test -tags load -run TestRedirectFlood ./test/load/ -ip-cardinality=200000` — and confirm RSS
   stays flat. Green `go test ./...` does NOT exercise this.
5. Take OQ-018 to the operator (config vs constants for the sweep interval).

## Recent decisions made

| When | Decision | Rationale / reference |
|---|---|---|
| 2026-06-30 | Token bucket behind a `Limiter` interface | ADR-0007 — avoids boundary bursts + unbounded log; interface defers OQ-014 |
| 2026-07-01 | Hard-code 5m/10m sweep-interval/TTL for now | keep-moving placeholder; real answer is OQ-018 |
| 2026-07-01 | File the unbounded-map risk as a near-miss | LP-023 — load test caught a latent OOM before ship |

## Breadcrumbs / artifacts

- Load run output (the ~1.2 GB RSS observation) was captured to a scratch file **outside** the repo
  and is NOT committed — re-generate it via the step-4 command rather than hunting for it.
- No throwaway spikes or scratch branches left behind; the only uncommitted work is `sweeper.go` in the
  working tree of `feature/redirect-rate-limit`.

## Reading order

1. This handoff.
2. `.agent-docs/checkpoints/2026-07-01-143512-rate-limit-sweeper-wip.md` — the zero-loss sitrep; it
   post-dates nothing but holds the dead-ends (global-limiter, request-context 0%-rejection) at full
   fidelity. The handoff curates; the checkpoint preserves.
3. `ADR-0007` (decision) · `LP-023` (near-miss) · `now/open-questions.md` for OQ-014 / OQ-018.
4. FR-0031 — the sweeper dispatch-charter, for the exact scope/acceptance of the resume work.

## Recent commits

```
9c4f1ab  feat(ratelimit): wire token-bucket Limiter into redirect middleware
3b7e0d2  feat(ratelimit): add Limiter interface + in-memory bucket (ADR-0007)
a1c9f84  test(load): add high-cardinality redirect flood harness (build-tag: load)
5f2ad10  chore: scaffold internal/ratelimit package
```

---

*How to refresh this file:* run `/handoff` at the next checkpoint / before compaction — it rewrites
this in place, archives the prior copy, and folds in the latest `checkpoints/` sitrep.
