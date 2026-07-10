---
provenance: kit-template
status: accepted
created: 2026-07-10
last-modified: 2026-07-10
related: [0005-per-directory-routing-indexes, 0007-revisit-anchor-ledger, 0008-doc-size-disposition, 0009-inbound-reference-sweep, 0010-reviews-findings-home, 0013-origin-posture]
tags: [meta, framework, obligations, ledger, multi-party, default-if-silent, detection, degradation]
---

# ADR-0012 — A two-direction inter-party ledger tracks what an agent OWES and is OWED

> Framework rationale that ships with the kit. Explains why the kit adds an
> inter-party debt ledger — and why the novel *owed-to-me* direction, carrying a
> pre-decided **default-if-silent** at a named trigger, is the one surface no existing
> home provides.

## Context

The kit already tracks what an agent **owes**: a `DEFER→` row parks deferred work; an
`OQ-` with a `home:` parks an open question; the reviews test-obligation column
(ADR-0010) parks a finding that owes a named test (`unbound → <owner>`). Every one is
an *outbound* debt the agent carries forward.

Nothing tracks the other direction — what an agent is **waiting to receive** from a
counterparty (another agent, another repo, the operator) — nor what to do when that
counterparty stays silent. In multi-party work this is the #1 compaction casualty.
"I'm blocked until repo-b sends the schema doc" lives only in the conversation and dies
at the next compaction; the next session re-derives it from scratch or, worse, stalls
indefinitely on a promise nobody wrote down. Two gaps sit underneath:

1. **Direction.** Every existing surface is agent-outbound. The inbound direction (what
   is owed *to* me) has no home at all.
2. **Silence.** A receivable is safe across context loss only if the rule for "the
   counterparty never answered" is decided *in advance*, at a *named trigger*, and
   written down. Otherwise every re-orient re-litigates chase-vs-wait-vs-proceed — and
   a blocked agent with no pre-decided fallback waits forever.

Terminology caution (reconciled below): "obligation" already names FORWARD WORK parked
against a unit — the `traceability/` ledger is its store (ADR-0009). This ADR adds the
*distinct* **inter-party debt** (owed to / by a counterparty). Two stores, one sweep.

Field datum from dogfooding this in a live **multi-party** program: in one session the
ledger mutated ~7 times (promises made / received / settled) while the handoff
regenerated 0 times. Obligations move on their **own clock**, mid-session — *in
multi-party work*. That scoping is load-bearing: the datum argues for a
mid-session-writable file **where multi-party work happens**, not for a tier line (the
form decision below). The owed-TO direction + default-if-silent has no direct kit
precedent (only a loose accounts-receivable analog); that novelty is a risk the
flip-conditions hedge.

## Alternatives Considered

- **A (chosen) — a standalone `now/obligations.md` as the MULTI-PARTY form, plus a
  lighter `## Obligations` handoff SECTION for single-party / Minimal installs.** Two
  tables, a tripwires block, a settled line; update-in-place on the obligation's own
  clock. The file is instantiated where the workload is multi-party (the recommendation
  leans toward the file at Full; detection + the empty-ceremony DOWN-flip still govern —
  never automatic — and it is opt-in at Standard on a cross-party signal); otherwise the
  section. Defended in Decision.
- **B (runner-up) — a handoff SECTION only, every install.** Attractive: zero new
  always-read surface. Rejected as the SOLE mechanism *for multi-party work* —
  obligations mutate mid-session (the ~7-vs-0 datum), and a section that regenerates
  only at `/handoff` loses every intra-session mutation (a receivable settled *between*
  handoffs vanishes). So the section is **kept** as the default for single / low-party
  installs and rejected only as the multi-party carrier — which is why A ships **both**.
- **B′ (near-tie against A) — the standalone file at FULL only; Standard takes the same
  section as Minimal.** Honestly cleaner against the recommendation tree (`profiles.md`
  up-sells multi-agent work to Full, down-sells solo to Minimal) and needs no
  cross-party probe at Standard. Rejected as *primary* because it denies the file to a
  legitimate multi-party STANDARD install — cross-repo / operator coordination that
  `profiles.md` does NOT up-sell to Full (no sub-agent dispatch). **Kept as the
  pre-approved fallback** if the Standard cross-party probe proves too heavy to wire.
- **C — fold into `now/open-questions.md`.** Rejected: an `OQ-` is an undecided FORK;
  an obligation is a *settled* debt (known who-owes-whom + a silence rule). An OQ has no
  counterparty, direction, trigger, or default-if-silent; folding bloats the OQ schema
  or drops them. (The non-overlap rule, as a rejected merge.)
- **D — a tracker OUTSIDE the doc system.** Rejected: the kit's thesis is
  findings-to-disk-in-repo. An off-repo tracker is invisible to `wu-refs`, dies with the
  machine or the chat window, and is not greppable by the sweep meant to catch leaks.
- **E — per-counterparty files** under `obligations/`. Rejected at this scale:
  obligations are read as a SET at cold-start; sharding fragments the one sweep and
  scales the always-read surface with the party count. One two-table ledger is right
  until a project carries dozens of live rows (the up-flip).

**Deciding axis:** the surface must be **updatable on the obligation's own
(mid-session) clock AND readable as one set at cold-start** — a standalone `now/` file
*earns* that only where the workload is multi-party; below that the handoff section is
adequate. The form follows the **workload**, not the tier line.

**Flip-conditions (two, symmetric):**
- **UP:** if live obligations outgrow one legible file (dozens of rows, many parties),
  graduate to per-counterparty files under `obligations/` + index + completeness lint
  (the registry graduation ADR-0009 reserves for its own sweep).
- **DOWN (the empty-ceremony guard, mirroring ADR-0010's reviews flip):** if an install
  has no live cross-party counterparty (single-agent, single-repo, synchronous), do NOT
  instantiate the standalone file — carry the section and grow into the file when the
  first cross-party wait appears. An empty two-table always-read ledger is carried
  ceremony, not discipline.

## Decision

Add `now/obligations.md` as the **multi-party form** of the inter-party debt ledger
(the recommendation leans toward the file at Full; detection + the empty-ceremony
DOWN-flip govern — never automatic — opt-in at Standard on a cross-party signal).
Single-party / Minimal installs carry the same content as an `## Obligations` handoff
SECTION — lighter *presentation*, same *safety floor*. (`now/obligations.template.md`,
this package, is the single schema authority for both forms.)

- **OWED TO ME (receivables — the novel direction).** Columns: *Counterparty · What ·
  Class · **Trigger/by-when** · **Default-if-silent** · Source.*
  - **Trigger/by-when** — REQUIRED, parseable (a stage / event / date): the point at
    which silence becomes actionable. A receivable with no trigger can never "come due,"
    so it rots unstruck — `/orient` computes *overdue* against this cell.
  - **Default-if-silent** — REQUIRED, the pre-decided rule *at* the trigger:
    **chase-once** (one ping, then a recorded fallback) · **apply-default** (proceed on
    a fallback, no chase) · **never-chase-never-peek** (silence is a specific recorded
    disposition; for fenced / operator-keyed rows — do not pursue or inspect).
  - **Gate safety (hard constraint).** `apply-default` is **forbidden** on a HARD row
    whose counterparty is the operator, OR whose deliverable is an *authorization*
    (approval / sign-off / release / deploy / merge). Those rows MUST use `chase-once`
    or `never-chase-never-peek`; `apply-default` may auto-proceed only past a SOFT,
    non-gating wait. `/orient` fires the recorded default *mechanically* at cold-start,
    so a self-authored "silence = proceed" across an approval gate is exactly the
    ask-first line the standing rules mark CRITICAL.
- **OWED BY ME (debts).** Columns: *Counterparty · What · Class · Due/trigger · Source.*
  A debt I control has no silence problem — its risk is a *missed trigger*, so column 4
  is the due-point, not a silence rule. Silence is the counterparty's failure mode; a
  missed trigger is mine.
- **Class (direction-aware).** HARD gates forward work / SOFT does not — but the
  *subject* inverts: owed-to-me HARD = gates **my** work (I am blocked); owed-by-me HARD
  = gates the **counterparty's** work (blocked on my delivery).
- **Source** (both): the *promise's* provenance — a message id / commit SHA / doc ref.
  Distinct from the document's front-matter `provenance:` field.
- **Rows are UN-IDed** — deliberately outside the CONVENTIONS §4 durable-artifact ID
  spine, by reasoned exemption. An obligation points OUTWARD (cites `OQ-`/`WU-`/`REV-`/`DEFER`
  ids) and is short-lived (struck on settlement, then folded away); nothing durable needs
  to cite an obligation *back*. The reverse join is sweep-mediated (`wu-refs`) + the `/orient`
  dangling-pointer check, not a stored back-pointer — a recorded, weaker guarantee taken
  to keep a Tier-1 surface lean.
- **TRIPWIRES** — watched conditions that flip a decision but that **no counterparty
  owes**. **POINT-ONLY:** a tripwire CITES the `RV-`/`DEFER`/`WU-` id whose
  flip-condition it watches; it never restates that trigger's action. They co-locate
  here because they surface at the same cold-start read as the receivables (`/orient`
  reads one ledger). At Full a tripwire graduates to a typed `RV` anchor +
  revisit-ledger row (ADR-0007); at Standard the tripwire is the lightweight doc-level
  stand-in.
- **Settled-row hygiene.** A settled row is struck *in place* with a settlement stamp
  (date + Source), kept for ONE cycle so `/orient` surfaces "settled while away," then
  **journaled to `log.md`** (folded into the `/handoff` log entry) and **pruned** from
  `now/obligations.md`. This is the carve-out to "never delete silently": the row is
  *preserved in the journal*, not vanished — so the Tier-1 ledger stays bounded while the
  audit trail is intact.

**Non-overlap rule (the second load-bearing decision).** An obligation row may **POINT
at** an `OQ-` / `DEFER` / review-finding / `WU-` by id; it must **never DUPLICATE** one.
Obligations are inter-party debts; OQs are open questions, DEFER rows are deferred work,
review findings are defects with dispositions. An owed-TO row "repo-b owes the schema
doc" *cites* `OQ-014` — the OQ states the fork, the obligation states the counterparty
and the silence rule. Honored by **discipline, not lint**: table-cell ids sit outside
lint rule 8's front-matter resolution, so nothing mechanically checks the join — the
same discipline-only cost ADR-0010's bidirectional x-refs carry. (`--extra-id-prefixes`
in `lint-docs.py` is the future enforcement seam.)

**Position against each prior-art surface** (compose, never compete):

- **vs `OQ-` homes** — an OQ's `home:` says WHERE an answer files; the obligation says
  WHO owes it and what happens on silence.
- **vs `DEFER` rows / flip-conditions** — a DEFER parks *my* work behind a *self*-trigger;
  an owed-BY row is a promise to a *named counterparty*. Self-deferral ≠ inter-party debt.
- **vs the reviews test-obligation column** (ADR-0010) — that column already carries a
  cross-party owner (`unbound → <owner>`), so the split is NOT "cross-party ⇒
  obligations." Boundary: reviews stays the home for the test-binding AND the owner
  identity; an owed-TO row adds ONLY the *default-if-silent*, citing `REV-NNN-FNN`, and
  never re-records the owner.
- **vs `REVISIT` anchors** (ADR-0007, Full / module) — RV anchors are typed *code-comment*
  markers on a revisit-ledger; a tripwire is a *doc-level* watched flip-condition where RV
  anchors aren't installed. A tripwire POINTS at an RV row where one exists and graduates
  to it at Full. Bridge, not rival; neither restates the other's action.
- **vs `wu-refs`' inbound sweep** (ADR-0009 — the sharpest analog). `wu-refs` **gathers**
  what awaits a *unit* (pull, unit-scoped); the ledger **records** what awaits an *agent*
  across parties (push, agent-scoped). They COMPOSE as 0009 frames it. Terminology
  reconciles here: `traceability/` is the intended store for FORWARD-WORK obligations
  parked against a unit; `now/obligations.md` is the intended store for INTER-PARTY debt.
  `wu-refs`' catch-all sweeps BOTH, so an obligation citing a `WU-` can't hide at that
  unit's cycle start.

**Lint & indexing integration** (honest about what is and isn't checked):

- The file carries `now/` front-matter → passes rules 1–3; `last-modified` is
  staleness-checked (rule 12) *file-level* like the rest of `now/`. File-level: a single
  rotting *row* is invisible to rule 12 — the `Trigger/by-when` column + `/orient`'s
  overdue surfacing are the per-row net.
- `now/` is **excluded** from rule-13 index-completeness (`managed_dirs` skips `now/`),
  so the `now/index.md` routing row (ADR-0005) is lint-safe where the file is absent —
  the way `now/index.md` already lists `handoff.md` before it exists.
- The REQUIRED-field safety invariant (every owed-to-me row has a non-empty `Trigger` AND
  a `Default-if-silent` from the canonical set) is covered by **no shipped rule**. It
  should get a rule-17-class stdlib table scan of `now/obligations.md` (skipping the
  fictional rows the template fences between `<!-- example:start -->` / `<!-- example:end -->`
  markers), warn-or-fail like rule 12; until added it is discipline + `/orient`'s overdue
  surfacing. (`lint-docs.py` ships verbatim, so this is a linter change the maintainer lands.)
- Same-change wiring the maintainer lands with this ADR **in this same release**: the
  `now/index.md` routing row; a CONVENTIONS §1 `now/` note ("multi-party installs also
  carry `obligations.md`; single-party / Minimal carry it as a `handoff.md` section")
  mirroring `reviews/`; the `profiles.md` payload-map row; the `framework-rationale/index.md`
  rows. **Concierge wiring (per *Detection & degradation*, below):** the obligations FORM
  is selected by a **manifest install-decision** — the header field `"multi_party": true|false`
  recorded beside `kit_ref` in `.agent-docs/.kit-manifest.json` at install / ratification —
  **not** a `{{…}}` substitution token: `parameters.md`'s closed set stays **twelve**,
  unchanged. The concierge DOCS read and write that field the way they already carry the
  profile choice and module toggles (read at scaffold time, never spliced into a doc body):
  the interview gains the detect-then-confirm question; `scaffold-plan.md` reads the field to
  instantiate `now/obligations.md` OR seed the handoff `## Obligations` section;
  `merge-strategy.md`'s foreign-marker-block recognition is **extended** (read-to-classify
  only) as detection signal (a). All of this ships together — the field is not banked for a
  later release.

## Detection & degradation

The FORM (standalone file vs handoff section, per the Alternatives) turns on one install-time
fact: **is this a multi-party COORDINATION workload** — cross-repo, multi-agent, or
operator-in-the-loop work where a receivable crosses a party boundary? An agent-to-agent
**comms layer** (a message room, a shared inbox, a monitor-armed agent protocol) is the
STRONGEST signal of that workload — but **not the only one**: a repo can coordinate across
parties with no comms tooling at all, and the gate is the *workload*, not the *tooling*. That
fact is **DETECTED, then confirmed** — never left to self-declaration, per the concierge's
detect-then-confirm contract. Three signals, strongest first:

- **(a) A foreign marker block in the target `CLAUDE.md`** whose body reads as an agent-comms
  protocol — a message room, monitor/watch-arming instructions, named agents and their reply
  discipline. This is an **extension of `merge-strategy`'s foreign-block handling**: the merge
  already recognizes such a block as *somebody else's managed seam* (a
  `<!-- x:begin -->…<!-- x:end -->` region whose tokens aren't the kit's own
  `kit:start`/`kit:end`; preserved byte-verbatim, never kit-owned). Detection **reuses that
  shipped concept** — a foreign block describing agent coordination is the strongest tell a
  comms layer is already wired here — reading it **to CLASSIFY only**; it NEVER edits inside a
  foreign block (that rule still holds).
- **(b) An agent-room CLI or config surfaced during read-only detection** — a coordination
  tool or its state/log file present in the tree. The interview's existing surface-scan
  (Q1 detection) is where a hit registers.
- **(c) The interview's coordination question** — *"Do other agents or repos coordinate with
  this one — a message room, a shared inbox, an agent-to-agent protocol, or a cross-repo
  hand-off?"* Unlike a mere tiebreaker, a **yes here sets `multi_party` true on its own**,
  even with no comms tooling present (no (a) or (b) hit): the coordination *workload* is the
  gate, and tooling is merely its strongest tell. Detect-then-confirm runs both ways — the
  operator can also overrule a detected-yes down to false.

The confirmed result is recorded as the **manifest install-decision field `multi_party`**
(`"multi_party": true|false`, beside `kit_ref` in `.agent-docs/.kit-manifest.json`): true →
instantiate `now/obligations.md` (the file form); false → carry the `## Obligations` handoff
section. This is the mechanical realization of the "cross-party signal" the Alternatives'
opt-in-at-Standard rule and the DOWN flip-condition name — the signal is now a detected,
confirmed, recorded install fact, not a self-report, and **not** a `{{…}}` parameter (the
twelve stay twelve).

**Why the ledger exists even when `multi_party` is false.** A comms layer does NOT create
receivables — it only concentrates them among *agents*. A solo repo with no comms layer still
waits on real counterparties every day: a PR reviewer, an upstream fix, a vendor ticket, an
operator ruling. And **operator silence is the single most common silence a solo repo faces** —
the operator steps away mid-decision and the next session must know whether to chase, to
proceed on a recorded default, or to hold. That is *exactly* what default-if-silent
pre-decides, so the ledger **earns its keep most** where there is no comms layer to keep waits
visible. What a comms layer changes is therefore never the **schema** — both forms are
**schema-equivalent**: the same columns, the required `Trigger/by-when`, the required
`Default-if-silent`, and the gate-safety rule (the section is a lighter *presentation* of the
same fields — a bullet list rather than a table — not a lighter *schema*). Only two things
differ:

1. **VOLUME.** Agents generate receivables far faster than operator/external counterparties do
   (the ~7-mutations field datum is a *multi-party* datum). High volume is what a standalone
   always-read file buys over a handoff section; low volume is what the section serves without
   carried ceremony — so the file GATE rides on `multi_party`, and the schema does not.
2. **SWEEP MECHANICS** — *where* `/orient` and `/handoff` look for landings and settlements:
   - **`multi_party` true:** `/orient`'s landed / came-due check **scans the repo's agent-comms
     log** (tool-generic — whatever coordination log the layer writes) for traffic since the
     last handoff, and `Source` cells cite **message ids** from that log.
   - **`multi_party` false:** `/orient` **prompts the operator** ("anything land while I was
     away?") and checks each row's **named sources** — a commit now on disk, a PR / issue state,
     a dated conversation note. There is no comms log to scan; the row's own `Source` cell is
     the pointer.
   Both are the SAME sweep asking the SAME question ("what moved?"); they differ only in the
   surface read. **Safety is invariant across the two** — the materiality gate, the required
   trigger + default-if-silent, the `apply-default`-across-a-gate prohibition, and
   snapshot-before-mutate all hold identically. A lower-ceremony form never relaxes a safety
   constraint.

**Later acquisition (the upgrade path).** A repo installs single-party, then takes on
cross-party coordination (or wires a comms layer) later. At the next `kit-upgrade` the
concierge re-detects (signals a–c), flips `multi_party` true, and **promotes the handoff
`## Obligations` section into a standalone `now/obligations.md`** — content *moved*, never
re-authored: existing rows migrate verbatim, the section is removed from `handoff.md`, and the
promotion is recorded in `.agent-docs/.kit-manifest.json` so the step is **idempotent** (a
re-run sees the file already present and no-ops). The reverse — the DOWN flip — retires an
*empty* file back to the section when a repo loses its comms layer and the ledger holds no
live cross-party rows. `kit-upgrade` owns both flips (section→file promotion, field-preserving
row migration; and file→section retirement when empty-ceremony fires). **Both directions are
content-preserving** (ADR-0008's living-standard disposition: content is split, moved, or
journaled — never dropped); an upgrade that lost a row, or a downgrade that discarded a live
one, is a defect, not a degradation. No skill re-fork is needed across either flip: the shipped
`/handoff` and `/orient` bodies **branch on the runtime fact** — *if `now/obligations.md`
exists*, they read the file; *otherwise* they read the handoff's `## Obligations` section — so
they follow whichever surface the flip produced without reading any recorded flag.

## Consequences

- **+** The inbound direction has a home: a receivable, its trigger, and its
  default-if-silent survive compaction, so a blocked-on-counterparty wait no longer dies
  in conversation or stalls forever.
- **+** Composes with existing surfaces — swept by ADR-0009's catch-all, points at
  ADR-0010's `REV-` findings, bridges to ADR-0007's RV anchors, references DEFER/OQ
  without duplicating them.
- **+** The canonical defaults make silence a pre-decided auditable call; the gate-safety
  constraint keeps `apply-default` from ever auto-crossing an approval / deploy gate at
  cold-start.
- **−** A mid-session in-place mutation must survive compaction: the `/handoff` sweep
  snapshots `obligations.md` alongside the handoff archive and writes each owed-to-me row
  **atomically** (never one missing its `Trigger` or `Default-if-silent`), so a
  compaction mid-write can't leave a trusted half-row.
- **−** The reverse join is sweep-mediated, not stored — weaker than ADR-0010's
  bidirectional x-ref, accepted to keep the surface un-IDed and lean; the `/orient`
  dangling-pointer check (a cited `OQ-`/`REV-` now resolved → flag the row) recovers the
  common split-brain case.
- **−** default-if-silent is only as safe as the recorded rule; the column forces the
  *decision*, not the follow-through (`/orient`'s overdue surfacing is that net). Rows
  also clear a **materiality gate** at sweep time (named deliverable + identified
  counterparty + trigger), or conversational hedges become phantom rows — a phantom HARD
  row is worse than a missed SOFT one; an ambiguous-strength row files SOFT, never HARD.
- **−** One more Tier-1 surface on a multi-party install (mitigated: settled rows prune
  to `log.md`, so it stays bounded); the section variant accepts lower fidelity
  (handoff-cadence capture) as the single / low-party trade. "Start small, grow later"
  holds: a single-party install grows into the file at its first cross-party wait.
- **+** The multi-party form is DETECTED (a foreign agent-comms block in `CLAUDE.md` / room
  tooling in the tree / a confirmed interview answer), never self-declared, so the
  file-vs-section choice is a recorded install fact (the manifest `multi_party` field) an
  upgrade can re-evaluate — and a repo that later gains a comms layer promotes section→file
  content-preserving at the next `kit-upgrade` (manifest-recorded, idempotent). Absent a
  comms layer the ledger still ships: operator and external counterparties are real
  receivables, and operator silence is the most common silence, so default-if-silent pays
  there most.
- **−** Detection can misread — a dormant comms block, or a friend who under-reports
  coordination, yields the section where the file was warranted (or the reverse). Mitigated on
  both ends: the interview's detect-then-confirm settles the ambiguous read at install, and the
  content-preserving section↔file flip means a wrong call is re-flippable at any `kit-upgrade`,
  never a trapped state.

## Related

- ADR-0009 (inbound-reference sweep — the ledger is the inter-party-debt store its sweep
  also defends) · ADR-0010 (reviews test-obligation — the intra-artifact debt this points
  at) · ADR-0007 (REVISIT anchor — the Full-tier home a tripwire bridges to) · ADR-0005
  (per-directory indexes — the routing row + the rule-13 `now/` exemption) · ADR-0008
  (doc-size / living-standard disposition — the content-preserving rule the section↔file
  upgrade & downgrade obey) · ADR-0013 (origin posture — the self-install that dogfoods this
  ledger)
- `standing-rules-core.md` §"Findings, decisions & review feedback to disk" + §"Context
  lifecycle" · `now/obligations.md` + `now/obligations.template.md` · the `/handoff`
  + `/orient` skill deltas · `scripts/wu-refs.sh` (the catch-all that sweeps it)
</content>
</invoke>
