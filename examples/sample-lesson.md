<!-- EXAMPLE — delete after reading; shows the SHAPE of a good lesson (a near-miss entry with the three-axis front-matter filled). A real one lives at .agent-docs/lessons/<kebab-slug>.md and is APPEND-ONLY. -->

---
id: LP-023
entry_type: near-miss
provenance: llm-reviewed
template-version: 1.0.0
maturity: budding
status: active
severity: high
module: action
type: near-miss
tags: [memory, cache-eviction, rate-limiting, load-testing]
created: 2026-07-01
last-modified: 2026-07-02
last-applied: 2026-07-02
related: [WU-0042, FR-0031, OQ-014]
superseded-by: null
---

# An in-memory keyed limiter/cache without eviction grows unbounded under adversarial key cardinality

## Question

While adding per-IP rate limiting to the redirect endpoint (WU-0042), we keyed one token bucket per
client IP in a plain `map[string]*rate.Limiter`. The unit tests were green and the feature worked in
a normal browser session. Was it safe to ship?

## Claim (the lesson)

**When you key an in-memory structure (limiter, cache, dedup set) by a value an untrusted client
controls, you MUST bound it — an idle-eviction sweep or an LRU cap — because the key count is
adversary-controlled and an unbounded map is a memory-exhaustion (OOM) bug, not a slow leak.** Green
functional tests do not exercise this; only a load test with *realistic key cardinality* does.

## Evidence

- Load run on branch `feature/redirect-rate-limit` @ `9c4f1ab` with ~200,000 randomized source IPs
  grew the `sparrowd` process to **~1.2 GB RSS** before it was stopped short of OOM.
- Root cause: `internal/ratelimit/limiter.go` inserted a bucket per new IP and never removed one.
- Design cost was foreseen but under-weighted in ADR-0007 (§Consequences "the map grows unbounded").
- Remediation tracked + landed as **FR-0031** (the eviction sweeper); re-run at the same cardinality
  held RSS flat. See log.md `## [2026-07-02] lesson | LP-023 filed`.

## Trigger (when this fires)

Watch for it whenever a diff adds a `map[...]` / cache / set whose **key derives from request input**
(client IP, header value, path segment, session token) with no eviction, no TTL, and no size cap.
Grep signal: a package-level or long-lived `map[string]*T` written in a request path, with no
corresponding `delete(` anywhere. `golangci-lint` will not flag it — it is a design gap, not a lint.

## What almost happened

The feature would have passed review on green unit tests and shipped. In production the redirect
endpoint faces the open internet, where unique-IP cardinality is effectively unbounded; a scan or a
botnet would have walked `sparrowd` into OOM and taken down *all* redirects — a full outage caused by
the very anti-abuse feature meant to protect the service.

## What made the save reliable

The load harness (`test/load/redirect_flood_test.go`) used **randomized unique source IPs**, not a
small fixed set. A load test that reused ~10 IPs would have shown flat memory and hidden the bug
completely. The reusable rule: **load tests must model the adversarial input distribution
(high-cardinality keys), not a convenient fixture** — otherwise they green-light the exact shape they
exist to catch.

## Recurrence count

**N = 1** (first occurrence). If an unbounded input-keyed structure recurs (N = 3), promote this from
`budding` to `evergreen` and lift the claim into the Tier-1 lessons MOC as a standing review checklist
item ("any request-keyed map is bounded or it is a bug").
