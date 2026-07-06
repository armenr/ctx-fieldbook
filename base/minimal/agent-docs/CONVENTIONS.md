---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, schema, conventions]
related: [index, glossary, CONVENTIONS-full-addendum]
---

# CONVENTIONS.md — the schema contract

THE schema contract for `.agent-docs/` in the **{{PROJECT_NAME}}** repo ({{PROJECT_ONE_LINER}}).
This is the operating manual every session, sub-agent, and hook conforms to. Per-dir `index.md`
files route; THIS file is normative.

> This is the **Minimal / Standard** core. The Full profile adds the dispatch-charter / wave-plan
> system, the research pipeline, the IMPL→WIRED traceability ledger, the revisit-ledger, and
> incidents/experiments/runbooks — see `CONVENTIONS-full-addendum.md`, which references (never
> restates) the sections here.

---

## 0. First-class principle — PROGRESSIVE DISCLOSURE

**Progressive disclosure is the load-bearing principle of this system.** Context is finite and
expensive; the schema's entire job is to let an agent reach exactly the fact it needs at the moment
it needs it — and nothing else. It replaces crude context caps (a numeric "N files/turn" ceiling)
with a real information architecture. The *intent* of those caps ("read with intent, synthesize
immediately") is kept and discharged structurally, not by a line count.

Its mechanisms, each enforced by a concrete schema rule below:

1. **Pointers-not-content.** `CLAUDE.md` and root catalogs hold pointers; substance lives in the
   owning doc. No doc duplicates another's content — it references by ID/path.
2. **Per-dir index routing — route, don't browse.** Every populated content dir has an `index.md`
   routing catalog (§7.1): *what each doc holds · when to open it · the one carry-away fact*. Agents
   route through the index; they do **not** enumerate raw directory listings (§1, §7.1).
3. **Front-matter as the breadcrumb layer.** `tags:` / `related:` / `sources:` / `superseded-by:` /
   `archived-from:` form a navigable graph between docs without reading their bodies (§2).
4. **Tiered loading.** Tier-1 surfaces (`now/`, the lessons MOC, this file, per-dir indexes) are
   small and auto/early-loaded. Tier-2 (`reference/`, `decisions/`) is on-demand by ID. Tier-3
   (`archive/`, `_archive` snapshots) is never loaded wholesale — only reached by an explicit
   `archived-from:` breadcrumb (§2, §7.3).
5. **Reference-by-ID.** Every durable artifact carries a typed work-unit ID (§4). Cross-references
   cite the ID, not a body excerpt — the ID resolves to the current doc even after supersession.
6. **The `archived-from:` breadcrumb.** Archived material keeps a single back-pointer to its
   `_archive` snapshot so it is *discoverable* without being *resident*. The snapshot is never
   bulk-loaded (§2, §7.3).

Every rule in this document either implements one of these mechanisms or protects a durable
discipline. Where the two conflict, progressive disclosure governs *how much is loaded*; the durable
disciplines govern *what must never be lost*.

---

## 1. The taxonomy

ONE `.agent-docs/` store. One level of nesting under `.agent-docs/` is the norm; deeper nesting only
where a dir's template mandates it (`now/lessons/`, `lessons/archive/`).

**Write-discipline legend:**
- **UPDATE-IN-PLACE** — the doc is rewritten to reflect current reality; history lives in git.
- **APPEND-ONLY** — new entries are added; existing entries are never edited away (supersede, don't
  delete). Genealogy is the value.
- **WRITE-ONLY** — created once, timestamped, never edited after creation (immutable artifact).

| Dir | Holds | Write-discipline | Caps (GUIDANCE, not lint-enforced — see §Token-budget) |
|---|---|---|---|
| `now/` | Fleeting working state: `status.md` · `work-plan.md` (active board + backlog + completed) · `open-questions.md` (OQ-NNN single source; inline-RESOLVED threading) · `handoff.md` · `lessons/{MOC.md,proposals.md}` | UPDATE-IN-PLACE | 50–150 lines/file, hard 250. Drift >7d = lint warn, >90d = lint fail. |
| `decisions/` | ADRs (`ADR-NNNN`) — why we chose what; mandatory **Alternatives Considered** field | APPEND-ONLY (new ADRs) + status-UPDATE-IN-PLACE (existing ADRs change `status:`, never move) | 50–150 lines, hard 250. Stable IDs forever; supersession-not-deletion. |
| `checkpoints/` | WRITE-ONLY timestamped **10-point zero-loss sitreps** (§6). The anti-naive-summarization tier. | WRITE-ONLY | One file per checkpoint, `YYYY-MM-DD-HHMMSS-<slug>.md`. Never edited; addendum = a NEW checkpoint referencing the prior. |
| `lessons/` | Typed append-only ledger of lessons / near-misses (`LP-NNN`); `lessons/archive/` for superseded; a **quarantine** sub-section for model/harness-bound lessons | APPEND-ONLY (`status:` may change to `superseded`/`deprecated`) | Atomic entries; superseded → `lessons/archive/`. Read before action. |
| `reference/` | Stable facts: architecture, syntheses, inventories, a validated-version matrix, **living agent-enforced standards** (standard-of-record, `provenance: human`) | UPDATE-IN-PLACE (rare) | up to 200, hard 400. |
| `memories/` | Non-obvious gotchas/findings, titled as claims (not topics) | UPDATE-IN-PLACE (rare) | 30–100 lines, hard 200. |
| `templates/` | Versioned referenceable scaffolding templates (§8) — the canonical source new docs instantiate from | UPDATE-IN-PLACE (versioned) | n/a; each carries a `template-version`. |
| `archive/` | Retired non-ADR docs, banner-stamped, immutable (Tier-3) | WRITE-ONLY (on archive move) | Never loaded wholesale; reached via `archived-from:`. |
| `CONVENTIONS.md` · `glossary.md` · `charter.md` · `log.md` · root `index.md` | This schema · jargon · mission · append-only journal · directory-level catalog | `log.md` APPEND-ONLY; rest UPDATE-IN-PLACE | `log.md`/root `index.md` unbounded; the rest 100–400 lines. |
| `<dir>/index.md` | Per-dir routing catalog (§7.1) | UPDATE-IN-PLACE (same change as any doc add/retire in the dir) | ~150 lines, keep routable. |

**Full profile adds** `research/`, dispatch-charters (`dispatch/`), `traceability/`,
`runbooks/`, `incidents/`, `experiments/` — see the addendum. **No new top-level category without an
ADR justifying it.** `_archive` snapshots (whole-corpus ejections) live OUTSIDE `.agent-docs/` and
are referenced only by `archived-from:` (§7.3).

---

## 2. Front-matter schema

Every doc starts with YAML front-matter. Fields:

```yaml
---
provenance: human | llm-draft | llm-reviewed | llm-autonomous   # REQUIRED — trust signal
created: YYYY-MM-DD                                             # REQUIRED — LOCAL date (date +%Y-%m-%d)
last-modified: YYYY-MM-DD                                       # REQUIRED — LOCAL date
status: <see §5 / below>                                        # REQUIRED for ADRs; optional elsewhere
tags: [tag, ...]                                                # the breadcrumb / filter layer
related: [doc-id, ...]                                          # the breadcrumb graph (encouraged)
sources: [path, ...]                                            # raw originals a synthesized doc derived FROM
supersedes: [doc-id, ...]                                       # doc(s) this OVERRIDES (they become obsolete)
superseded-by: doc-id | null                                    # back-pointer (set when this doc is overridden)
amended-by: [doc-id, ...]                                       # doc(s) that AMEND sections without overriding the whole
archived-from: <path-to-_archive-snapshot> | null              # Tier-3 breadcrumb (§7.3) — never bulk-loaded
work-unit: <typed-id>                                           # the keying work-unit ID (§4), where applicable
---
```

Kit-shipped scaffolding (this file, the templates) carries `provenance: kit-template`; the user
bumps an instantiated doc to its own provenance (`llm-draft` on creation, up from there).

**Date timezone.** `created`/`last-modified` are **LOCAL dates** (`date +%Y-%m-%d`, not `date -u`).
UTC produces future-dated front-matter west of UTC and breaks staleness checks. UTC is reserved for
machine-sortable filenames (`checkpoints/`, handoff archives: `date -u +%Y-%m-%d-%H%M%S`).

**Relationship fields — four distinct semantics (all may coexist):**
- **`supersedes:`** — "this OVERRIDES X; X is now obsolete." X gets `status: superseded` +
  `superseded-by:` back-pointer. Whole-doc replacement.
- **`amended-by:`** — "Z modifies SECTIONS of this without overriding the whole." This doc stays
  authoritative; each amended section gets a banner `> **Amended YYYY-MM-DD by [ADR-NNNN]:** …`.
- **`sources:`** — "DERIVED FROM Y; Y is preserved as raw material and may still be partially true."
  The synthesis relationship.
- **`archived-from:`** — "this doc/dir is a curated extract of snapshot S; S is the immutable
  Tier-3 original." The progressive-disclosure breadcrumb (§7.3).

**`provenance:` values.** `human` (highest trust) · `llm-reviewed` (LLM drafted, operator signed
off) · `llm-draft` (not yet reviewed — treat as draft) · `llm-autonomous` (unsupervised — flag for
review). **Rule:** ADRs at `status: accepted` may NOT be `llm-draft`/`llm-autonomous` —
`llm-reviewed` or `human` minimum.

**`status:` for ADRs** — `proposed` · `accepted` · `pending` (stub; needs `pending-on: [...]`) ·
`deferred` (stub; needs `deferred-because: "..."`) · `rejected` · `superseded` (needs
`superseded-by:`) · `deprecated`. **For non-ADRs (optional):** `active` (default) · `draft` ·
`deprecated`. **STALE state is front-matter, not body text** — absorbed into `status:` +
`last-modified` + the lint staleness check.

---

## 3. Naming

- All filenames **kebab-case**.
- **ADRs:** `decisions/NNNN-kebab-claim-as-title.md` (zero-padded 4-digit, sequential).
- **Memories:** `memories/kebab-claim-as-title.md` — title is the claim/finding, not the topic.
  Good: `payload-cap-forces-fallback-encoder.md`. Bad: `journal-notes.md`.
- **Checkpoints:** `checkpoints/YYYY-MM-DD-HHMMSS-<slug>.md` (UTC, machine-sortable).
- **Lessons:** `lessons/<kebab-slug-of-claim>.md`, keyed `LP-NNN`.
- **Archive:** `archive/YYYY-MM-original-title.md` on move-in.
- **Indexes:** exactly one `<dir>/index.md` per populated content dir.

---

## 4. The typed WORK-UNIT ID spine

Every durable artifact is keyed to a typed work-unit ID; the **prefix encodes the artifact's type**.
The ID is the join key across `decisions/`, `checkpoints/`, reviews, and (Full profile) dispatch and
traceability — cross-references cite the ID, not a body excerpt (progressive-disclosure §0.5).

| Prefix | Type | Format | Lives in | Lifecycle |
|---|---|---|---|---|
| `WU-NNNN` | **Work-unit** — the spine. One ledgered unit of intended work. Decisions, reviews, checkpoints, and traceability rows all reference the WU that spawned them. | `WU-NNNN` | `now/work-plan.md` (board), keyed everywhere | active → done; never reused |
| `ADR-NNNN` | **Decision** — an architecture decision record | `ADR-NNNN` | `decisions/` | proposed → accepted/rejected → superseded/deprecated |
| `OQ-NNN` | **Open question** — single source, reference-by-number, inline-RESOLVED threading | `OQ-NNN` | `now/open-questions.md` | open → RESOLVED (resolution cites the ADR/WU that closed it) |
| `LP-NNN` | **Lesson / near-miss** — a typed entry in the append-only lessons ledger | `LP-NNN` | `lessons/` | seedling → budding → evergreen; active → superseded |

**Full profile adds** `FR-NNNN` (dispatch-charter), `RV-NNN` (revisit anchor), `R-NNNN` (research
investigation), `INC-NNN` (incident) — defined in the addendum.

**Reconciliation rules:**
- **`ADR-NNNN` is canonical for decisions.** `OQ-NNN` (an unresolved question) is **orthogonal** to
  `ADR-NNNN` (a settled decision): a resolved `OQ` cites the `ADR` that closed it. They are different
  *phases* of the same idea, not competing namespaces.
- IDs are **never reused**; retired IDs stay resolvable (supersession-not-deletion, §5).

---

## 5. Decision policy

- **`ADR-NNNN` is the canonical decision ID.** Sequential, zero-padded 4-digit, stable forever.
- **Supersession, not deletion.** A superseded ADR keeps its file and ID; it gains
  `status: superseded` + `superseded-by:`; the successor gains `supersedes:`. Genealogy is queryable
  without a database (the chain IS the record). Log: `## [DATE] supersede | ADR-A → ADR-B`.
- **Mandatory `## Alternatives Considered` field — written BEFORE acting.** Every ADR records the
  rejected options and *why* they were rejected — the superseded-but-instructive rationale. The
  dead-ends ARE the value; a summarizer that drops them destroys the WHY. An ADR without this field
  is lint-incomplete. The rationale-with-alternatives is authored *before* the work, not
  reverse-engineered after.
- **Capture the load-bearing rationale, not just the verdict.** Beyond "options + why rejected," the
  ADR names **(a) the deciding axis** the choice turned on, **(b) an honest steelman of the runner-up**
  (never a strawman), and **(c) the flip-condition** — the goal / evidence / constraint that would
  reverse it (the pre-written trigger for a future reversal). Rule of thumb: *if the conversation that
  produced the decision was more insightful than the ADR, the ADR is not done.*

**ADR body shape:** Context (what forced it) → Alternatives Considered (options + why rejected /
superseded-but-instructive + **the deciding axis + a runner-up steelman + the flip-condition**) → Prior
art / reference (cite the backing source, or flag a novel shape as a risk) → Decision (one paragraph) →
Consequences (good and bad) → Related (ADRs, memories, the WU + log entry where decided). See
`templates/adr-template.md`.

---

## 6. The 10-point zero-loss sitrep contract (`checkpoints/`) — CANONICAL

*(This section is the single source of truth for the checkpoint contract; the checkpoint template and
the Full-profile docs reference it, they do not restate it.)*

A checkpoint is **WRITE-ONLY**: a timestamped, immutable sitrep at
`checkpoints/YYYY-MM-DD-HHMMSS-<slug>.md`, keyed to the active `WU`. Its purpose is
**anti-naive-summarization** — it preserves what a lossy summary would silently drop. Every
checkpoint MUST contain all ten points:

1. **Mission / objective** — the MAIN objective and the active `WU` (+ the side-quest / detour
   stack: what spawned each nested detour → what it found → resolved/open).
2. **Current state** — what is true right now (branch, working-tree shape, what builds/runs).
3. **Work completed this segment** — concrete deliverables, each tied to its `WU`.
4. **In-flight / interrupted** — exactly where execution was when paused; the next concrete action.
5. **Decisions made — WITH rejected alternatives.** Not just what was chosen; what was rejected and
   why (mirrors the ADR Alternatives field; mandatory).
6. **Investigation results — INCLUDING dead-ends.** Paths explored that did NOT pan out, with the
   reason. *(The single most anti-summarization clause — dead-ends are the thing a summary deletes.)*
7. **Open questions / blockers** — `OQ-NNN` references; what is undecided or blocking, and on whom.
8. **Files / artifacts touched** — paths, with one-line why; the wiring/reachability status of each.
9. **Next actions** — the ordered queue to resume from, precise enough to act on cold.
10. **Addendum check** — an explicit "what would be LOST if this checkpoint were the only surviving
    record?" pass: re-read points 1–9, name anything still living only in conversation, and add it.
    *(Findings-to-disk-or-they-don't-exist: a finding only in conversation is DEAD at compaction.)*

**Immutability + addenda.** A checkpoint is never edited after write. New information ⇒ a NEW
checkpoint that references the prior by filename. Handoff consumes the latest checkpoint; orientation
reads it to reconstruct cold-start state.

---

## 7. Formalized conventions

### 7.1 Per-dir index routing (route, don't browse)

Each populated content dir has exactly one `index.md` routing catalog. Entry =
**what the doc holds · *Open when:* (the situation that makes it the right doc) · *Carry-away:* (the
one fact to retain even if you don't open it)**. Grouped by question/job, not alphabet. Markers:
⭐ canonical hub · 🔨 actionable · 🧭 proposal awaiting ratification. **Maintenance rule
(hook-enforced): adding/retiring any doc updates that dir's index in the SAME change.**
**Carry-away claims must be traceable to the source doc** — a wrong carry-away is worse than none.
Root `index.md` is directory-level only. See `templates/index-template.md`.

### 7.2 Adversarial separation of duties (review applies to designs, not just code)

**The reviewer is never the builder; the executor never audits its own work.** Independent
verification is a clean-context reviewer with no authorship stake who re-derives the claim against
the live tree. **This applies to DESIGNS, not just code** — a design reviewed only by its author is
unreviewed. Pattern: `design → adversarial-review` BEFORE implementation, not only after. The Full
profile realizes this as a verifier gate stage keyed to the WU (see the addendum).

### 7.3 Evidence-on-disk · the `_archive` breadcrumb

- **Evidence-on-disk behind every verdict.** A claim/verdict cites its evidence (a `log.md`
  timestamp, a git SHA, a tool query output, a `{{TEST_CMD}}` result, an ADR). Verdicts without
  on-disk evidence are not durable. *(Findings only in conversation are DEAD at compaction.)*
- **The `archived-from:` breadcrumb.** Whole-corpus ejections are referenced ONLY by an
  `archived-from:` front-matter pointer on the curated extract. The snapshot is Tier-3: discoverable,
  never bulk-loaded. STALE/archival state is front-matter (`status` + banner on archive move), never
  free-text in the body.

---

## 8. Scaffolding-as-versioned-template

The scaffolding (this taxonomy, the per-dir index shape, the ADR/checkpoint/lesson/memory templates)
is a **versioned, referenceable template, not a hand-copied fork** — hand-copied scaffolding drifts
silently across repos. Canonical templates live in `templates/` and each carries a
`template-version`. An instantiated doc records which template version it was scaffolded from; updates
to a template are versioned, and instances are migrated deliberately — never by silent copy-paste.
This makes drift detectable (version mismatch) instead of invisible. **Canonical fill-in scaffolds
live in `templates/` — see `templates/index.md`; do not inline-duplicate them here.**

---

## log.md format

Append-only. Grep-parseable:

```
## [YYYY-MM-DD] op | short summary

Optional body — one or two lines of context. Reference the WU.
```

**Op vocabulary (core):** `ingest` (new doc) · `decision` (ADR status change) · `memory` (new
gotcha) · `work` (commands run / code changed) · `checkpoint` (sitrep written) · `lesson` (lessons
ledger entry) · `supersede` (doc → archive w/ named successor) · `lint`. The Full profile adds
`dispatch` · `research` · `incident` · `dogfood`.

---

## Lint rules (index completeness = hook-enforced; the rest ADVISORY — not yet implemented)

> **Honesty note.** The only rule a shipped hook actually enforces today is **index completeness**
> (below). The remaining rules are the SPEC for a doc-schema linter that does not exist yet; track its
> implementation as an OQ. Until it lands, treat them as manual discipline, not a guarantee.

1. Front-matter present + YAML-parseable. *(ADVISORY)*
2. Required fields populated (`provenance`, `created`, `last-modified`). *(ADVISORY)*
3. `provenance` in the allowed set. *(ADVISORY)*
4. ADRs have a valid `status`. *(ADVISORY)*
5. ADRs `status: superseded` ⇒ non-null `superseded-by`. *(ADVISORY)*
6. ADRs `status: pending` ⇒ non-empty `pending-on:`; `status: deferred` ⇒ non-empty `deferred-because:`. *(ADVISORY)*
7. ADRs MUST contain a non-empty `## Alternatives Considered` section (§5). *(ADVISORY)*
8. `related:` / `supersedes:` / `superseded-by:` / `archived-from:` references resolve. *(ADVISORY)*
9. File path matches category (ADR in `decisions/`, checkpoint in `checkpoints/`, etc.). *(ADVISORY)*
10. ADRs `status: accepted` are not `llm-draft`/`llm-autonomous`. *(ADVISORY)*
11. Date-prefixed filenames (checkpoints/incidents/experiments) match the date format. *(ADVISORY)*
12. `now/` files `last-modified` within 7d (warn at 7, fail at 90). *(ADVISORY)*
13. **Index completeness (HOOK-ENFORCED):** every populated content dir has an `index.md`; its
    `` `file.md` `` references match the on-disk set (no unindexed, no phantom).
14. **Checkpoint integrity:** files in `checkpoints/` contain all ten numbered §6 points. *(ADVISORY)*
15. **WU resolution:** a `work-unit:` value resolves to a known WU in `now/work-plan.md`. *(ADVISORY)*

A Tier-2 substantive review (a clean-context reviewer, §7.2) checks beyond schema.

---

## Token-budget guidance

**Caps are GUIDANCE, not lint-enforced** — the hook checks index drift + front-matter, NOT line
count. The real bar is *"read with intent, synthesize, don't dump."*

| Type | Target | Hard cap |
|---|---|---|
| Memory | 30–100 | 200 |
| ADR | 50–150 | 250 |
| Checkpoint | 60–150 | 250 |
| Reference (distilled facts) | up to 200 | 400 |
| now/* | 50–150 each | 250 |
| CONVENTIONS/glossary/charter | 100–400 | — |
| root index.md / log.md | unbounded | — |
| per-dir `<dir>/index.md` | ~150 | — |

> Over a **hard cap** ⇒ split into a subdir cluster, **never content-drop**. An actively
> agent-enforced standard → `reference/` as a **standard-of-record** (`provenance: human`), distinct
> from frozen research/genealogy; if its full body busts the reference cap, split standard from
> evidence rather than waive the cap.

---

## What NOT to do

- Don't auto-generate docs without `provenance: llm-draft`.
- Don't duplicate another doc's content — reference by ID (progressive disclosure §0.1).
- Don't browse raw directory listings — route via `index.md` (§7.1).
- Don't pad to look thorough — compression > completeness.
- Don't store secrets, credentials, or regulated / user data in any git-tracked doc — reference paths.
- Don't deep-nest (one level under `.agent-docs/`, except the mandated `now/lessons/`,
  `lessons/archive/`).
- Don't bulk-load `_archive` snapshots — follow the `archived-from:` breadcrumb (§7.3).
- Don't drop dead-ends / rejected alternatives from ADRs or checkpoints — they ARE the value.
- Don't add a top-level category without an ADR.
- Don't hand-copy scaffolding — instantiate from the versioned template (§8).

## Related

- `CONVENTIONS-full-addendum.md` — the Full-profile additions (dispatch, research, traceability, …)
- `index.md` — directory-level catalog · `log.md` — operational journal · `glossary.md` — jargon
- `charter.md` — long-term goal · `templates/index.md` — the versioned scaffolds
- `.claude/rules/standing-rules.md` — the operational rules that reference this schema
