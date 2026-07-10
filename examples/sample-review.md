<!-- EXAMPLE — delete after reading; shows the SHAPE of a good FILLED review report — every finding, every severity (down to the NIT), carries an explicit disposition + a test-obligation, not just the blockers. A real one lives at .agent-docs/reviews/REV-NNN-<slug>.md and adds a row to reviews/index.md in the SAME change. -->

---
provenance: llm-reviewed           # operator signed the dispositions below → promoted from llm-draft
template-version: 1.0.0
created: 2026-06-30
last-modified: 2026-07-02          # dispositions UPDATE IN PLACE as findings resolve (F1/F2/F6 landed)
# work-unit: WU-0042  — a real front-matter field per §4; commented out ONLY so this isolated gallery
#   example lints without a live now/work-plan.md to resolve against (see ## Related).
related: [ADR-0007, OQ-014, LP-023, FR-0031]   # every id resolves within the fiction
tags: [review, rate-limiting]
---

# REV-001 — Token-bucket rate limiter (Limiter impl + redirect middleware) — WU-0042

- **Review type:** adversarial design + code review (clean-context, diff read against ADR-0007)
- **Reviewer:** fresh-context verifier — NOT the builder who wrote the diff
- **Target:** the WU-0042 limiter diff @ `9c4f1ab` — `internal/ratelimit/limiter.go` + `internal/httpx/middleware.go`
- **Verdict:** **block** → cleared to **pass-with-findings** once F1 + F2 landed (the dispositions below are the living record)

## Findings

### F1 — Per-IP limiter map is unbounded → memory exhaustion under IP cardinality
- **id:** `REV-001-F1`
- **severity:** BLOCKER
- **claim:** `buckets` gains one entry per distinct client IP and never reclaims — a scan or botnet walks `sparrowd` into OOM and takes down ALL redirects (the anti-abuse feature becomes the outage).
- **evidence:** `internal/ratelimit/limiter.go:22` declares `buckets map[string]*rate.Limiter`; `getOrCreate` inserts at :34 and there is no `delete(` anywhere in the package. Reproduced: load run @ `9c4f1ab`, ~200k unique IPs → ~1.2 GB RSS still climbing.
- **disposition:** FIXED → `d4e77c1` (idle-eviction sweeper landed via FR-0031; re-run at the same cardinality held RSS flat)
- **x-ref:** WU-0042 · ADR-0007 (§Consequences accepted this cost) · LP-023 · FR-0031
- **test-obligation:** `test/load/redirect_flood_test.go::TestRedirectFlood_HighCardinality_RSSBounded` — RED on HEAD `9c4f1ab` (RSS unbounded), GREEN after `d4e77c1`

### F2 — Client-IP key trusts `X-Forwarded-For` → the limit is trivially bypassable
- **id:** `REV-001-F2`
- **severity:** BLOCKER
- **claim:** the bucket is keyed on an attacker-controlled header; rotating `X-Forwarded-For` mints a fresh bucket per request → the limit enforces nothing, and every spoofed value is a new map key that amplifies F1.
- **evidence:** `internal/httpx/middleware.go:38` — `ip := r.Header.Get("X-Forwarded-For")`, used verbatim as the bucket key with no trusted-proxy check.
- **disposition:** FIXED → `a2b7f10` (key on the `r.RemoteAddr` host; honor XFF only from a configured trusted-proxy allowlist)
- **x-ref:** WU-0042 · ADR-0007 · LP-023 (spoofing is the worst case of the cardinality that OOMs the map)
- **test-obligation:** `internal/httpx/middleware_test.go::TestRateLimit_KeyIgnoresUntrustedXFF` — RED on HEAD `9c4f1ab` (test did not exist)

### F3 — `getOrCreate` takes the write lock on every request → hot-path contention
- **id:** `REV-001-F3`
- **severity:** MAJOR
- **claim:** the redirect path — Sparrow's hottest — serializes on `mu.Lock()` even for EXISTING buckets (the common case), not just on insert; under concurrency the single mutex is a throughput ceiling on the one endpoint the feature must not slow.
- **evidence:** `internal/ratelimit/limiter.go:34` — `getOrCreate` unconditionally `l.mu.Lock()`s; there is no RLock double-checked fast-path for the cache-hit case.
- **disposition:** DEFER — not a correctness defect; at current single-node QPS the lock sits ~2 orders below saturation (`go test -bench`), and a sharded / RLock fast-path is premature until a profile shows contention. REVISIT trigger: redirect p99 regression or sustained QPS past the measured knee.
- **x-ref:** WU-0042 · ADR-0007
- **test-obligation:** `unbound → backend owner (perf)` — the binding artifact is a contention benchmark with a p99 budget; no perf gate owns it yet (a listed debt, not tribal memory)

### F4 — Limit is per-node, not global → N nodes admit N× the intended rate
- **id:** `REV-001-F4`
- **severity:** MAJOR
- **claim:** on the roadmapped multi-node deploy a client sharded across nodes gets its full quota PER node; effective throughput scales with node count exactly when load is highest — the limiter under-enforces.
- **evidence:** the `map[clientIP]*rate.Limiter` is per-process by construction (`internal/ratelimit/limiter.go:22`); ADR-0007 §Consequences accepted per-node isolation as a known cost.
- **disposition:** TRACKED → OQ-014 (distributed / global limiter; the ADR's `Limiter` interface seam is what keeps this a swap, not a rewrite)
- **x-ref:** WU-0042 · ADR-0007 · OQ-014
- **test-obligation:** DEFERRED — a hermetic single-process fixture cannot fault-inject a second node; see ## Deferred obligations

### F5 — Burst is set equal to the per-second rate → a fresh client fires a full second's quota instantly
- **id:** `REV-001-F5`
- **severity:** MINOR
- **claim:** `rate.NewLimiter(rate.Limit(cfg.RPS), cfg.RPS)` couples burst to steady-state; an idle client can spend `RPS` tokens in the first millisecond, so smoothing only bites after the opening second.
- **evidence:** `internal/ratelimit/limiter.go:41` — the burst argument is `cfg.RPS`, not a separately-tuned `cfg.Burst`.
- **disposition:** WONTFIX — deliberate per ADR-0007: a browser legitimately opens several links from one page render, and the agreed policy admits that fan-out rather than false-throttling real users; a documented tradeoff, not a defect.
- **x-ref:** WU-0042 · ADR-0007
- **test-obligation:** n/a — accepted policy, not a code defect (a WONTFIX-by-design owes no binding test; recorded so the decision is auditable, not silently dropped)

### F6 — 429 response omits `Retry-After` → clients retry-storm instead of backing off
- **id:** `REV-001-F6`
- **severity:** NIT
- **claim:** on deny the middleware writes `429` with no `Retry-After`, so well-behaved clients cannot schedule a polite retry and will hammer the endpoint blind.
- **evidence:** `internal/httpx/middleware.go:47` — `w.WriteHeader(http.StatusTooManyRequests)` with no header set beforehand.
- **disposition:** FIXED → `c3d9e21` (set `Retry-After` to the seconds-until-next-token)
- **x-ref:** WU-0042
- **test-obligation:** `internal/httpx/middleware_test.go::TestRateLimit_429SetsRetryAfter` — RED on HEAD `9c4f1ab`

## Deferred obligations

- **F4 (per-node vs global) → OQ-014.** The single-node hermetic harness structurally cannot exercise
  cross-node under-enforcement — there is no second process to shard one client across. Rather than let
  the untestable half of the guarantee vanish at acceptance, F4 is TRACKED → OQ-014, which references it
  back; the binding cross-node test lands with whatever resolves OQ-014 (a shared-store limiter, or an
  accepted per-node policy).

## Related
- WU: `WU-0042` (parent) · OQ-014 (joined by F4) · ADR-0007 (the design under review) · LP-023 (the
  near-miss F1 confirmed) · FR-0031 (the remediation that FIXED F1).
- log.md: `## [2026-06-30] review | REV-001 — token-bucket limiter · 6 findings (2 BLOCKER→FIXED, 1 DEFER, 1 TRACKED→OQ-014, 1 WONTFIX, 1 NIT→FIXED)`
