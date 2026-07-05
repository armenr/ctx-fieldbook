<!-- EXAMPLE — delete after reading; shows the SHAPE of a good checkpoint (a 10-point zero-loss sitrep). A real one lives at .agent-docs/checkpoints/YYYY-MM-DD-HHMMSS-<slug>.md, is WRITE-ONCE, and is never edited after write. -->

---
provenance: llm-autonomous
template-version: 1.0.0
created: 2026-07-01
last-modified: 2026-07-01
# work-unit: WU-0042  — a real field per §4; commented so this isolated example lints without a
#   live now/work-plan.md (named in point 1).
tags: [checkpoint]
---

# Checkpoint 2026-07-01-143512 — rate-limit-sweeper-wip

<!-- All ten points are MANDATORY (CONVENTIONS §6). Point 6 (dead-ends) is the one a naive summary deletes — it is why this file exists. -->

1. **Mission / objective** — MAIN: ship per-client rate limiting on `GET /r/{code}` (active
   **WU-0042**). Detour stack: (A) *which algorithm?* → settled as ADR-0007 (token bucket behind a
   `Limiter` interface) — **resolved**; (B) *the map grows forever* → discovered in the load test,
   filed as near-miss LP-023 — **resolved as a finding**; (C) *build the eviction sweeper* → in
   progress under FR-0031 — **OPEN, this is where I am**.

2. **Current state** — branch `feature/redirect-rate-limit` (4 commits ahead of `main`). `go build
   ./...` clean; `go test ./...` green (unit tests only — see point 6). Working tree is dirty:
   uncommitted WIP in `internal/ratelimit/sweeper.go` (a half-written eviction loop). Nothing is
   committed for the sweeper yet.

3. **Work completed this segment** (all WU-0042) — the `Limiter` interface + the in-memory
   `bucketLimiter` (token bucket per IP) in `internal/ratelimit/limiter.go`; wired it into the
   redirect chain via `internal/httpx/middleware.go`; unit tests for allow/deny + burst behaviour
   with a fake clock. Committed at `9c4f1ab`.

4. **In-flight / interrupted** — writing `sweeper.go`: a background goroutine that periodically walks
   the limiter map and evicts buckets idle past a TTL. **Exact pause point:** `Evict()` compiles but
   is not yet called by anything, and I stopped mid-decision on the sweep interval (see OQ-018). **Next
   concrete action:** finish `Evict()` (drop buckets whose `lastSeen` is older than the TTL under the
   map's write lock), then start the ticker from the middleware constructor so it is actually WIRED.

5. **Decisions made — with rejected alternatives** — (a) token bucket over fixed-window (boundary
   bursts admit ~2x rate) and over sliding-window-log (unbounded memory under flood) — per ADR-0007;
   (b) a `Limiter` *interface*, not the concrete type, so the Redis path (OQ-014) is a swap not a
   rewrite — rejected "just use the concrete type, add the interface later" because retrofitting a
   seam after callers exist is more churn than adding it now.

6. **Investigation results — including dead-ends** —
   - **DEAD-END 1:** a single *global* `rate.Limiter` for the whole endpoint. Rejected: wrong
     granularity — one abuser consumes the shared bucket and every legitimate client gets throttled.
   - **DEAD-END 2:** stashing each client's limiter in the *request context*. Looked clean; was
     silently a no-op — the context is per-request, so a fresh bucket was created and discarded every
     request and *nothing was ever rate-limited*. Caught only because the load test showed **0%
     rejection** under a flood that should have been ~80% rejected. Unit tests were green throughout —
     they each build one limiter and never exercise the cross-request path.
   - **FINDING (→ LP-023):** the working per-IP map has no eviction. A load run with ~200k randomized
     source IPs grew the process to ~1.2 GB before I stopped it — a latent OOM. This is what spawned
     detour (C) / FR-0031.

7. **Open questions / blockers** — **OQ-014** (distributed/global limiter before multi-node — not
   blocking this WU, the interface defers it); **OQ-018** ("should the sweep interval + idle-TTL be
   config, or hard-coded constants?" — mildly blocking point 4: I hard-coded 5m/10m to keep moving
   and noted the question).

8. **Files / artifacts touched** —
   - `internal/ratelimit/limiter.go` — the interface + in-memory bucket. **WIRED** (called from the
     middleware; verified with `gopls references` on `Allow`).
   - `internal/ratelimit/sweeper.go` — the eviction loop. **IMPL, NOT WIRED** — `Evict()` has no
     caller yet; this is the gap FR-0031 closes.
   - `internal/httpx/middleware.go` — inserts the limiter into the redirect chain. **WIRED** (reached
     from `cmd/sparrowd/main.go` → router setup).
   - `test/load/redirect_flood_test.go` — the load harness (build tag `//go:build load`); **NOT** run
     by `go test ./...`.

9. **Next actions** (ordered, resume-cold) — (1) finish `Evict()` under the write lock; (2) start the
   sweeper ticker from the middleware constructor and prove reachability from `cmd/sparrowd/main.go`
   with `gopls call-hierarchy`; (3) add a unit test that inserts N buckets, advances the fake clock
   past the TTL, runs one sweep, asserts the map shrank; (4) re-run `test/load/redirect_flood_test.go`
   with the 200k-unique-IP profile and confirm RSS stays flat; (5) resolve OQ-018 with the operator.

10. **Addendum check** — re-reading 1–9, what lives ONLY in this conversation and would be lost:
    (i) the *reason* DEAD-END 2 produced 0% rejection (per-request context lifetime) — captured in
    point 6 now; (ii) the exact OOM trigger — **~200k unique IPs → ~1.2 GB RSS** — the number that
    makes LP-023's severity concrete; captured in point 6; (iii) that `go test ./...` does **not**
    cover the OOM path because the load harness is behind a build tag — captured in points 2/8. Nothing
    else outstanding.
