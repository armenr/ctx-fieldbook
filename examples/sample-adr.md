<!-- EXAMPLE — delete after reading; shows the SHAPE of a good ADR (an architecture decision whose value is the substantive Alternatives Considered section). A real ADR lives at .agent-docs/decisions/NNNN-kebab-claim.md. -->

---
provenance: llm-reviewed
status: accepted
template-version: 1.0.0
created: 2026-06-29
last-modified: 2026-06-30
# work-unit: WU-0042  — a real front-matter field per §4; commented out ONLY so this isolated
#   gallery example lints without a live now/work-plan.md to resolve against (see ## Related).
supersedes: []
superseded-by: null
related: [WU-0042, OQ-014, LP-023, FR-0031]
tags: [rate-limiting, http, redirect, decision]
---

# ADR-0007 — Rate-limit the redirect path with an in-memory per-IP token bucket behind a Limiter interface

## Context

The public redirect endpoint `GET /r/{code}` is Sparrow's hottest path — every shortened link
resolves through it. Over the last week two scraper bots walked the code space at ~400 req/s each,
inflating our datastore read load and skewing click analytics. We need per-client rate limiting on
that one endpoint. Two constraints shape the choice: (1) Sparrow ships **single-node** today, so we
must not take on new infrastructure to solve a single-node problem; (2) a multi-node deploy is on the
roadmap (OQ-014), so whatever we build must not paint us into a per-process corner we cannot escape.

## Alternatives Considered

- **Fixed-window counter** (N requests per rolling 60s bucket) — *rejected.* Cheapest to implement,
  but it admits boundary bursts: a client can spend its full quota in the last 100ms of one window
  and again in the first 100ms of the next, sailing through at ~2x the intended rate exactly when a
  scraper is hammering us. The failure mode is worst precisely in the case we are defending against.
- **Sliding-window log** (retain a timestamp per request per client) — *rejected.* Accurate, but it
  stores one entry per request per client. Under a scraper flood the memory footprint grows with
  request volume — an unbounded-memory shape in the exact adversarial scenario. Trades the bug we
  have for a worse one.
- **Off-the-shelf throttling middleware** (a third-party HTTP throttling package) — *rejected.* Pulls
  a dependency and its transitive graph in exchange for ~80 lines of logic we can own outright, and
  couples our rate policy to the package's storage assumptions (many assume a shared store), which
  fights constraint (1). Not worth the supply-chain surface for logic this small.
- **Redis-backed counters first** — *rejected for now, deferred behind the interface.* This is the
  correct answer for a *global* limit across multiple nodes, but it adds an operational dependency and
  a network hop on the hottest path to solve a problem we do not yet have. Building it now would be
  speculative (YAGNI) infra. Recorded as OQ-014 so the future need is not lost; the interface below
  is what keeps that door open.

## Prior art / reference

Token-bucket is the standard rate-limiting algorithm and is implemented in the standard extended
library `golang.org/x/time/rate` (`rate.Limiter`), which gives us burst + steady-state in one type.
We wrap one `*rate.Limiter` per client rather than reimplementing the algorithm. No novel shape here —
the only original decision is the *interface seam*, called out as a consequence below.

## Decision

Rate-limit `GET /r/{code}` with an **in-memory `map[clientIP]*rate.Limiter`**, one token bucket per
client IP, reached through a small **`Limiter` interface** (`Allow(clientIP string) bool`). The
concrete in-memory type implements the interface; the redirect middleware depends only on the
interface. A future distributed (Redis-backed) implementation can be dropped in without touching the
handler or the middleware — the seam is the whole point of choosing an interface over a concrete type.

## Consequences

- **Good:** no new infrastructure; pure-Go and unit-testable with a fake clock; the interface seam
  makes the Redis path (OQ-014) a swap, not a rewrite; per-node isolation means one abuser cannot
  starve a shared store.
- **Sizing policy (deliberate):** burst == steady-state RPS — one page render legitimately fans out
  several redirects at once; the bucket admits that fan-out while the refill rate holds the average.
- **Bad / costs:** the map grows **unbounded** — a new key per unique client IP, never reclaimed —
  which is a latent memory-exhaustion bug under high IP cardinality (surfaced as the near-miss LP-023
  and remediated by the sweeper in FR-0031; this ADR is not "done" until that lands). Limits are
  **per-node, not global**, so effective throughput scales with node count until OQ-014 is resolved.

## Related

- **WU-0042** — "Add per-client rate limiting to the redirect endpoint" (the parent work-unit).
- **OQ-014** — "Do we need a distributed (global) limiter before the multi-node deploy?" (open; this
  ADR's interface seam is what keeps that deferrable).
- **LP-023** — the near-miss the unbounded-map consequence produced.
- **FR-0031** — the dispatch-charter that implements the eviction sweeper this ADR's cost demands.
- log.md: `## [2026-06-30] decision | ADR-0007 accepted — token-bucket limiter behind an interface`.
