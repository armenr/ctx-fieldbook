---
provenance: kit-template
status: accepted
created: 2026-07-11
last-modified: 2026-07-11
related: [0007-revisit-anchor-ledger, 0008-doc-size-disposition, 0009-inbound-reference-sweep, 0010-reviews-findings-home, 0012-obligations-ledger]
tags: [meta, framework, docs-impact, sweep, gate, brownfield, drift]
---

# ADR-0014 — A diff-keyed docs-impact sweep + a triage gate reconciles docs to what changed, without punishing inherited drift

> Framework rationale that ships with the kit (Standard profile). Explains why the
> work cycle gains a **diff-keyed** doc-refs sweep — the twin of the **unit-keyed**
> `wu-refs` sweep — feeding a named **docs-impact CLEAR** stage that
> *triages, never blocks*; and why **brownfield-vs-cold-start** is a first-class
> axis, handled by a baseline mechanism that holds an agent accountable only for
> the doc drift its own diffs create or touch.
>
> **Terminology (the kit uses inbound/outbound on more than one axis).** `wu-refs`'s
> recon looks OUTWARD at what a change touches while its sweep looks INWARD at what
> awaits a unit (`wu-refs.sh`); ADR-0012's "outbound" is what an agent OWES. To avoid
> a third clashing axis, this ADR's load-bearing distinction is **diff-keyed vs
> unit-keyed**. Where "outbound" appears it is a reading-aid only — the
> diff→downstream-docs blast radius (a change out to the docs that may now misdescribe
> it) — never a claim that doc-refs reverses `wu-refs`'s reference direction:
> mechanically both gather references pointing AT a key; the difference is the KEY and
> the CORPUS.
>
> **Spec-first:** this package is the ratified *contract* (`doc-refs-contract.md`,
> `gate-deltas.md`, `baseline-mechanism.md`); the `scripts/doc-refs.sh` build is a
> later unit gated on this design — the kit's own G0 discipline (design-with-
> alternatives before acting) applied to itself.

## Context

The kit already sweeps one direction. `wu-refs` (ADR-0009) runs at cycle start and
gathers everything that **references or awaits** the unit being started — the
*inbound* obligations, keyed on a unit id. And a Full install already runs a docs
pass at the G2→G3 boundary (`reference/work-discipline.md`, the **G2-docs** step):
"public API / CLI / config / protocol changes documented; self-skips on no
doc-impact."

But nothing mechanically answers the *outbound* question the owner named directly:
**is there any correlation between the SHIT THAT CHANGED and the DOCUMENTATION IN
THE REPO?** G2-docs asks the agent to *judge* doc-impact but hands it no
mechanical list of candidate claims — so a docs pass by eye misses the claim
scattered three directories away in a README, a design doc, or a source
doc-comment. Three independent field repos named this the same way: *the missing
half is the MECHANICAL list — these changed things now have doc-claims about them
that are unverified.* Two structural gaps sit underneath:

1. **Key.** The shipped sweep is unit-keyed (what awaits this unit). The diff-keyed
   question — *given a diff, what documentation does the change's blast radius touch,
   and which of those claims did it just falsify* (the owner's "outbound" question) —
   has no mechanical gatherer at all.
2. **Brownfield.** Adopters walk into repos where drift **already exists** (a
   README a lifecycle-stage stale, a normative doc settled-wrong-in-place, a
   test-count claim off by 2×) — or a mostly cold start. A gate that holds an agent
   accountable for **inherited** drift on its very first diff is a false-positive
   machine; a gate that ignores drift the agent's **own** diff creates is useless.
   The accountability line has to be drawn at *what the diff touches*.

There is also a structural hole underneath the pre-commit dispatcher
(`base/standard/githooks/pre-commit`): it classifies each staged file as
`.agent-docs`-markdown **or** code, and the human-doc surface — README, design
docs, generated-doc *source comments*, CLI-help text — falls through **both
lanes**: neither-doc-nor-code, fully ungated. A field datum makes the split-brain
precise: one repo's `.agent-docs` tracked reality *same-day* under byproduct
discipline while its human docs froze at last hand-edit — the drift is scoped
exactly to what the gate never covered.

**Field grounding (four archetypes).** The design is calibrated against four real
corpora, generalized here:

- **A mature-`.agent-docs` service** (thin human surface: README + generated API
  docs + CLI help). A docs-sync agent already runs at G2-docs, diff-driven and
  judgment-based — it wants only the mechanical candidate list. Referenceability:
  `file:line`, exported symbols, CLI flags, config keys. Constraint: generated API
  docs are produced *from* source comments → gate the source, never the output;
  vendored `file:line` citations are FROZEN (re-verify on version bump); "the ADR
  decided X" is a *record-fact*, not a reality-claim, even if code differs.
- **A brownfield normative-contract corpus with no `.agent-docs`** (install
  waiver). Self-amending docs (a §1.1 that amends §3/§5 lower in the same file;
  spec text corrected only by a deltas block in a *different* file), append-only
  dual-signed ledgers, cross-repo claims that are the most load-bearing yet
  locally unverifiable, a superseded doc kept *deliberately* as provenance, and a
  spike cited in five places all scheduled to go stale at one known milestone.
  Constraints: normative/append-only surfaces are FLAG-only; claim extraction must
  resolve amendments before judging; the sweep must run STANDALONE.
- **A doc-comment-dense workspace** where the referenceability profile *inverts*
  the first archetype (~55% runnable commands, ~25% routes/client methods, ~15%
  symbols, ~5% paths) — a path-only sweep misses most claims, so matchers must be
  PLUGGABLE. Its most load-bearing doc (a nine-line README whose license table
  omits the most legally-encumbered component) is its most drifted — *weight by
  load-bearing-ness, not size*. In-code status comments ("not yet wired" on code
  that IS wired) nearly misled a dead-code deletion — first-class claims that
  drift *both* directions.
- **A small flat-corpus tool** that named the neither-doc-nor-code hole outright,
  carries a two-register voice rule (gate CLAIMS, never prose style), and
  volunteers as pilot.

## Alternatives Considered

- **A (chosen) — a diff-scoped outbound doc-refs SWEEP (the `wu-refs` twin) +
  a named docs-impact CLEAR gate at Standard+ that TRIAGES, never blocks + a
  baseline mechanism fencing inherited drift.** Defended in Decision.
- **B (the runner-up) — a BLOCKING doc-freshness gate.** Genuinely strong: a
  blocked commit *cannot* ship drift, and it depends on no follow-through. Rejected
  on the deciding axis: doc-impact is a *judgment* call — still-true vs stale needs
  reading the claim against the changed code — so a blocking gate blocks on
  still-true claims, i.e. a false-positive machine; and it would gate *prose* where
  the field's two-register voice rule is load-bearing ("when clarity and voice
  conflict, voice loses" — gate CLAIMS, never style). Same contract as `wu-refs`:
  the sweep gathers mechanically; judgment stays with the agent/operator. **Kept**
  as the per-grammar *graduation* target (see the flip-condition) once a claim
  class's false-positive rate is provably near-zero.
- **C — a docs-freshness LINT keyed on file-age / mtime.** Rejected: file-age ≠
  truth. This is *already* what lint rule 12 is (now/ staleness, warn-only), and
  the field disproved it as a drift signal — a 2,117-line reference fully accurate
  next to a nine-line README badly wrong; a doc's mtime says nothing about whether
  its *claims* hold. The sweep reads claims-vs-code and weights by load-bearing-
  ness, never a timestamp.
- **D — an ALWAYS-FULL-CORPUS sweep** (re-triage every doc every cycle) instead of
  diff-scoped. Rejected: unbounded triage noise (a 35-doc corpus, a ~100%
  doc-comment-density workspace) — every cycle re-judges claims nothing touched.
  Worse, it erases the brownfield accountability line: full-corpus cannot tell
  drift THIS diff created from drift inherited, so it drowns an adopter on day one.
  Diff-scoping is what makes the gate cheap AND makes "accountable only for what you
  touched" mechanical. Full-corpus survives in exactly one place: the *one-shot*
  adoption baseline inventory (run once, never per-cycle — `baseline-mechanism.md`).
- **E — JUDGMENT-ONLY, no mechanical sweep** (keep G2-docs as-is, merely rename
  it). Rejected: this is the status quo the field rejected — "the missing half is
  the MECHANICAL list." An agent eyeballing a corpus misses the scattered claim;
  the whole value is the mechanical gather *feeding* the judgment, exactly as
  `wu-refs` is to recon-first.
- **F — the docs-architecture MODULE** (a managed `docs/` tree with per-surface
  claim schemas) shipped now. **HELD, not rejected.** Three field repos say
  keep-local / defer / hard-NO — no `docs/` tree and YAGNI; it would restructure
  frozen normative surfaces; mandating per-component READMEs where in-source
  doc-comments ARE the ecosystem convention is wrong. One repo volunteers as pilot.
  A 3-to-1 split is a *hold*, not a ship: this ADR records the module as deferred
  with its flip-condition and nothing more.

**Deciding axis:** *gather-mechanically, triage-by-judgment, scoped to what the
diff touched.* A cheap diff-scoped sweep that hands the agent the candidate claims
and draws the accountability line at the change's blast radius beats a blocking
lint that either false-positives on judgment calls or holds agents accountable for
drift they inherited.

**Flip-condition (two):**
- **Per-grammar graduation:** if a *specific* claim grammar's false-positive rate
  proves near-zero — the sweep can mechanically decide still-true vs stale for that
  class (e.g. a license-table join, an env-var name) — that grammar's lane
  graduates from advisory to blocking (Option B, for that lane only).
- **The held module:** if adopter demand for a managed `docs/` tree crosses a
  real pilot threshold (more than one committed volunteer, or the uncovered-lane
  repeatedly wants a home a flat corpus can't give), the held module (F) ships as
  its own ADR.

## Decision

Ship four things; the script is spec-first (contract now, build later).

1. **`scripts/doc-refs.sh <diff-range | --staged | --files …>` — the DIFF-KEYED
   twin of `wu-refs.sh`.** `wu-refs` is unit-keyed (what *awaits* this unit);
   `doc-refs` is diff-keyed (what documentation about the changed things the diff's
   blast radius may have *falsified*). Both gather references pointing at a key and
   hand them to triage; the difference is the KEY and the CORPUS, not a reversed
   direction. It derives the changed referents via
   pluggable claim-grammar plugins, greps the **human-doc corpus** (README,
   generated-doc *source* comments, CLI-help sources, design/normative docs — NOT
   restricted to `.agent-docs`), and emits a triage worksheet. It only GATHERS and
   *pre-tags the mechanically-determinable lanes*; the agent triages the judgment
   states. Runs STANDALONE (no `.agent-docs` required). Flag-only — NEVER
   auto-edits. Full CLI + output contract: `doc-refs-contract.md`.

2. **Generalize G2-docs into a named `docs-impact CLEAR` stage at Standard+.**
   The stage's mechanical half is the sweep above; its Standard home is the
   always-on cycle-start discipline (`standing-rules-core.md`, where the unit-keyed
   sweep already lives — the *single* normative statement of the five-state
   vocabulary; `work-discipline.md`'s G2-docs and this ADR POINT there, never restate
   it), and its Full formalization is the generalized G2-docs gate contract in
   `work-discipline.md`. It is wired into the **dispatch return schema** — a
   `docs_impact` field beside `discoveries[]`, but **PROOF-CARRYING, not a passive
   present-even-empty observation**: a `none` verdict is valid only WITH its execution
   proof (swept range + enabled grammars + exit 0 + the canary firing, or a recorded
   manual-read verdict until the script lands). A bare "none" is a rubber-stamp
   exactly as a proofless falsifier claim is — the governing precedent is
   standing-rules' "0/N findings refuted is a smell … confirm the refuter actually
   ran" and ADR-0012's materiality gate. And the stage **self-skips only on a
   zero-referent sweep** (exit 0, empty over the enabled grammars) — NEVER on a
   self-declared "no doc-impact," which would be the circular skip the sweep exists to
   close. Also wired into an **optional pre-commit ADVISORY third lane** (routed to
   fire only when something outside `.agent-docs` is staged) covering the
   neither-doc-nor-code human-doc surface. The gate **TRIAGES, never blocks** — the
   same contract as `wu-refs`. Exact edits: `gate-deltas.md`.

3. **The baseline mechanism makes brownfield-vs-cold-start first-class.** At
   adoption, pre-existing drift is inventoried ONCE into a parked backlog with its
   own home; thereafter the gate holds agents accountable ONLY for drift their own
   diffs create or *touch*. New debt loud, inherited debt acknowledged-and-fenced —
   the **adopt-exemption pattern's next application** (CONVENTIONS adopt-exemption /
   manifest `action: adopt`). Full design, incl. the retirement lane and
   scheduled-drift registration: `baseline-mechanism.md`.

4. **The docs-architecture module is HELD** — deferred with the flip-condition
   above, recorded here and nowhere expanded.

**Triage vocabulary (five states + two lanes)** — from the field, two repos
independently. The states map onto the **shipped closed veracity set** (CONVENTIONS
§2); the sweep introduces NO new marker, and the only *active* agent call is
still-true vs stale (the rest are pre-tagged):

- **still-true** — the claim holds against the change (→ veracity `[code-verified]`,
  citing the evidence).
- **stale** — the change contradicts the claim (→ `[contradicted-by-code]`; files as
  a doc fix, else a new `OQ-`, else a `reviews/` finding — `doc-refs-contract.md`
  §"where a stale row files").
- **uncovered** — a changed referent with an *expected-but-absent* doc claim (a new
  CLI flag with no help text; a new route in no README) — mechanically detectable
  via a grammar's coverage-expectation. (No claim exists, so no veracity marker.)
- **provenance / record-fact** — the doc/section deliberately records frozen
  history ("the ADR decided X"; a superseded doc kept as provenance). A record-fact
  carries **no reality-claim marker at all** (CONVENTIONS §2: "faithful capture
  suffices") — code differing is NOT drift; without this state every historical
  record is a false positive.
- **unverifiable-locally** — the claim's referent lives outside the repo (a sibling
  repo, an external service); it cannot be checked from here → `[claimed-unverified]`
  (asserted, not locally checkable) + a manual / owed-to-me check, and is *the most
  load-bearing precisely because it can't be mechanically settled*.

Two **lanes** fence rows OUT of accountability entirely:

- **retirement** — a doc/tree marked queued-for-deletion: surfaced, never owed a
  fix (do not force-fix a doc about to be excised).
- **baseline** — a claim in the adoption-time inherited-drift inventory whose
  referent this diff did not touch (`baseline-mechanism.md`).

**Design invariants baked in:**

- **Reads the colleague's human docs by default** (reading is not colonizing), with
  **per-surface opt-out**; **flag-only, never auto-edit** — hard-enforced on
  normative / append-only / frozen surfaces. (Archetype A preferred per-surface
  *opt-in* or nothing; that was **consciously resolved to read-by-default +
  declared exclusions** — an A-type adopter declares its generated/frozen surfaces
  once, rather than opting each doc in — so the resolution is a decision on record,
  not an oversight.)
- **Claim grammars are PLUGGABLE:** a core engine + per-repo matcher sets. A grammar
  is an EXTRACTOR + MATCHER + COVERAGE-EXPECTATION (+ an optional **RESOLVER** that
  computes the effective claim before judging — the §/amendment grammar needs one, or
  it flags "unresolved" rather than emitting a false stale). The four archetype
  grammars — *paths/symbols · commands/routes · §/amendment-ids · env-vars/flags/
  wire-shapes* — plus the wired **license-join** check are the initial library,
  enabled to match a repo's referenceability profile (a path-only sweep on a
  command-dense repo misses most of it). Because coverage-expectation only sees
  *within* an enabled grammar, a **coverage audit** (adoption + periodic re-audit)
  flags referent shapes no enabled grammar extracts — so an evolving repo's emergent
  claim classes don't fall silently outside the sweep's vision.
- **Claim-target indirection:** generated artifacts chase their SOURCE (the
  doc-comment, the schema file) — but *which* surfaces are generated is a **declared
  fact** (`generated: <glob> from <source>` in `.docrefs.config`), not a mechanical
  guess; **vendored citations are FROZEN** (re-verify on a dependency version bump,
  not per-diff). **In-code doc-comments about wiring / status are first-class claims**
  (they drift both directions).
- **Weight by load-bearing-ness:** the **license-join** check (manifest license
  fields ↔ README/LICENSE table) is a *wired first-class check* with its own
  extractor/matcher/coverage, not merely a weight; small ≠ safe. Honest trigger: it
  is caught once at the adoption inventory and per-diff only when the diff touches a
  license field / lockfile / packaging — diff-scoped like everything else, sorting
  HIGH when in scope.
- **Scheduled drift is pre-registrable.** Where an obligations ledger exists it
  POINTS at ADR-0012's tripwire watching the milestone (cite, don't duplicate — the
  non-overlap rule); **standalone** (no ledger to point at) it self-carries a bare
  event token inline, which is not a duplication (nothing else owns the trigger).
  Firing: `/orient` overdue-against-`expires-at` where `.agent-docs` exists, else the
  sweep flags expired-still-fenced rows on every run (`baseline-mechanism.md` §4).
- **Fail LOUD + a known-positive test + a per-repo canary** — inherited from the
  `wu-refs` scar (it shipped with a reserved-variable bug that returned "no
  references" silently, the exact silent-under-report failure it exists to prevent).
  The fixture test proves the engine; the per-repo canary (a real corpus claim the
  grammar set MUST find every run) proves the grammar set is not mis-scoped for THIS
  repo — a "(no claims)" result is trusted only if the canary fired. A safety tool
  you don't test is worse than none.

**Position against each adjacent shipped surface (compose, never compete):**

- **vs `wu-refs` / ADR-0009 — the unit-keyed twin.** `wu-refs` gathers what awaits a
  UNIT (unit-keyed); `doc-refs` gathers, from a DIFF, the docs about the changed
  things it may have falsified (diff-keyed). Same gather-then-triage contract, same
  fail-loud scar; the distinction is the KEY (diff vs unit) and the CORPUS (human-doc
  corpus vs obligation stores), NOT a reversed reference-direction (both grep for
  references pointing at their key). The twinning is at the CONTRACT/POSTURE level,
  not the build: `wu-refs` is a ~112-line one-token git-grep, whereas `doc-refs`
  needs a per-grammar claim-extraction engine (diff-hunk extractors, amendment
  resolution, generated→source indirection, coverage-expectation) — see Consequences.
- **vs G2-docs — the seed being generalized.** G2-docs is the Full-tier *judgment*
  step; this generalizes it to a named Standard+ stage with a *mechanical gatherer*
  underneath.
- **vs lint rule 12 (now/ staleness) — file-age ≠ truth.** Rule 12 reads `mtime`,
  warn-only, `.agent-docs`-only. `doc-refs` reads claims-vs-code, corpus-wide,
  diff-scoped, and never reads a timestamp.
- **vs `/orient` trust-the-code.** `/orient`'s trust-the-code covers `now/*` (docs
  stale vs the tree → trust the tree). `doc-refs` extends the *same principle* —
  code is ground truth, docs are the map — OUTWARD to the whole human-doc corpus,
  at cycle time rather than only cold-start.
- **vs the reviews test-obligation ledger (ADR-0010).** A doc-drift row is NOT a
  review-pass finding with a binding test, so it does not default into `reviews/`'s
  `REV-NNN-FNN` model: a stale claim files as a doc fix, else a new `OQ-` (the
  doc-debt lane G2-docs already names), else — when the docs pass IS a review pass —
  a `REV-NNN-FNN` whose test-obligation reads `n/a (doc-claim) → unbound → <owner>`.
  The sweep *feeds* those homes; it does not replace them.
- **vs the obligations ledger (ADR-0012).** Scheduled drift cites the obligations
  tripwire that watches the milestone — POINT, don't DUPLICATE (0012's non-overlap
  rule).
- **vs the pre-commit dispatcher — the third-lane delta.** The dispatcher's two
  lanes leave human docs neither-doc-nor-code; the advisory third lane covers
  exactly that hole, and only that hole.
- **vs rule 13 / `managed_dirs`.** Rule 13 indexes `.agent-docs` content dirs;
  `doc-refs` reaches the human-doc corpus rule 13 never sees. Orthogonal — neither
  subsumes the other.

## Consequences

- **+** The diff→docs direction gets a mechanical gatherer; G2-docs' judgment step
  finally gets its missing candidate list; the neither-doc-nor-code hole is covered
  advisory-ly; brownfield adopters are not drowned in inherited-drift false
  positives.
- **+** Composes across the whole system — swept adjacent to `wu-refs`, feeds the
  doc-debt / `reviews/` homes, cites obligations tripwires, reuses `/orient`'s
  overdue machinery, extends trust-the-code, honors the living-standard
  content-preserving rule (ADR-0008) for graduated baseline rows, and introduces NO
  new veracity marker (maps onto CONVENTIONS §2's closed set).
- **+** STANDALONE operation means the install-waiver repo (no `.agent-docs`) still
  gets the sweep — the corpus + the diff + an optional config are all it needs; the
  scheduled-drift firing net degrades to a sweep-side expired-row flag where
  `/orient` is absent.
- **−** It GATHERS and pre-tags; the still-true / stale call stays judgment — some
  rows are noise to dismiss on a still-true. The same cost `wu-refs` carries, by
  construction (the load is only two live choices; the rest are pre-tagged).
- **−** Pluggable grammars mean a repo that enables the wrong grammar set misses
  claims. The archetypes are a *library*, not a guarantee; the coverage audit +
  per-repo canary are the nets that keep the grammar set honest against the repo's
  actual referencing style rather than freezing it at install.
- **−** Flag-only means a flagged-stale claim can still be ignored — the gate forces
  the LOOK, not the fix (the doc-debt / `reviews/` disposition is that net).
- **−** A safety sweep must itself be tested; shipping without the known-positive
  fixture test AND the per-repo canary reintroduces exactly the silent-under-report
  failure that scarred the twin — the canary is what catches a per-repo grammar
  mis-scope a fixture test cannot.
- **− The twinning is CONTRACT/POSTURE-level, not build-cost — the load-bearing risk
  this spec-first ratification is deciding on.** The runtime is cheap (read-only,
  diff-scoped); the BUILD is materially heavier than the ~112-line one-token `wu-refs`
  grep — a per-grammar claim-extraction engine (diff-hunk extractors, amendment
  RESOLVER, generated→source indirection, coverage audit), likely per-language. The
  maintainer should ratify expecting an engine, not a grep.
- **− Ceremony-before-capability asymmetry (named, eyes-open).** This package lands
  the full DISCIPLINE cost now (the proof-carrying `docs_impact` field, the charter
  criterion, the G2-docs / cycle-start rewrites, the baseline inventory + seal, the
  vocabulary) while the mechanical gather — the script — is a later build. The
  interim is honest, not vaporware-pointing: the CLEAR stage and the `docs_impact`
  field run on a **recorded MANUAL corpus read** ("sweep not installed → read
  surfaces X → verdict"), self-upgrading to canary-backed proof when the script
  lands. The discipline (including the neither-lane advisory coverage) is worth
  landing before the tool — but the maintainer chooses this asymmetry knowingly;
  the runner-up was to defer the field + criterion to the same unit as the script
  (Alt E's judgment-only interim), rejected here to close the neither-lane hole now.
- **−** The held module means repos wanting a managed `docs/` tree get nothing yet
  — acknowledged and flip-conditioned, not silently dropped.

## Related

- ADR-0009 (inbound-reference sweep — the unit-keyed twin this mirrors, diff-keyed) ·
  ADR-0007 (REVISIT anchor / tripwire — the Full home a scheduled-drift entry
  bridges to) · ADR-0010 (reviews home — where a stale finding may land) · ADR-0012
  (obligations tripwires + `/orient` overdue machinery — scheduled-drift cites and
  reuses, never duplicates) · ADR-0008
  (living-standard content-preserving disposition — the rule graduated baseline
  rows obey)
- `doc-refs-contract.md` (the sweep spec) · `gate-deltas.md` (the exact wiring
  edits) · `baseline-mechanism.md` (the brownfield design) · `scripts/wu-refs.sh`
  (the twin) · `reference/work-discipline.md` §G2-docs (the seed) · the pre-commit
  dispatcher (the third-lane host) · `standing-rules-core.md` §"Cycle start" (the
  Standard home of both sweeps)
