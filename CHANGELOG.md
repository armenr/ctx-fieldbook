# Changelog

All notable changes to the Fieldbook kit. Versions track `kit-version.txt`.

## 0.6.1 — 2026-07-14 (the convergence-findings batch)

Seven field-nominated riders from the v0.6.0 convergence round — every one credited to the
field repo that found it, every fix red/green-proven before ship.

- **Entry-detector two-half fix** (2 sightings): the index-completeness check lived in TWO
  engines with complementary halves of the same bug — the shell lint stripped no HTML
  comments and anchored no rows; the python rule 13 stripped comments but matched bare
  backtick filenames in prose. Both engines now strip comment spans in a pre-pass AND
  anchor entry detection on the leading list-marker/table-row shape; real phantoms (an
  entry row pointing at a missing file) still fail. Proven against the kit's own shipped
  index, which the old shell lint falsely blocked.
- **Configurable gate protocol token**: `DISPATCH_GATE_TOKEN` env (or the top-of-file
  default constant) now governs the dispatch marker, degrade marker, and the derived
  `<TOKEN>_GATE_CWD` var — leak-gated public adopters configure instead of hand-forking.
  Default byte-identical; the preamble body hash is token-independent; self-test passes
  under the default and an overridden token.
- **Interrupt triage** (new standing-rules section): inbound mail is a doorbell, not a
  detour — four rungs: answer-inline / dispatch-and-return / ask-don't-block-and-file /
  file-durable; unsure → file plus the one-line ask. Work-unit INTAKE miniaturized for
  interrupts. Plus the **one-voice fence** now defined in the dispatch contract (a
  dispatched agent never speaks on a shared channel under the repo's name).
- **Review doctrine — independent panels can share a blind spot**: ladder rung 4 extended
  (a green N-lens review is a distinct confidence layer, never a substitute for the
  orchestrator's firsthand read of the load-bearing diff); adversarial-separation gains
  failure-mode-diverse lenses, boundary-probing a converged mechanism model, and the
  dead-field tell (a write-only field is a symptom — trace before deleting).
- **Upgrade/merge guidance**: manifest source-field drift — the profile-keyed overlay rule
  is the AUTHORITY over a row's recorded source tier, and the upgrade corrects the record
  on discovery; diverged grafts MUST collapse to pointer form (faithful grafts may choose);
  settings hook blocks are wired by targeted text insert, never a whole-file json
  round-trip (a 135-line reformat was measured where 3 lines suffice).

## 0.6.0 — 2026-07-13 (the fail-loud era)

The **fail-loud dispatch contract** becomes both doctrine and mechanism. Born from a fleet
operator directive after a real incident (a fan-out silently dropped half its legs and the
synthesis LOOKED complete), designed spec-first with a three-lens adversarial review (1 BLOCKER
+ 10 MAJORs, all dispositioned) and grounded by a firsthand three-probe hook spike before any
enforcement code was written.

- **`reference/fail-loud-dispatch-contract.md`** — the contract (R1–R6), the single normative
  home: completeness asserted at every phase boundary; the silent-drop idioms banned
  (`.filter(Boolean)`-and-continue on dependent paths, early-return partials, vacuous
  `every()` verdicts); two sanctioned shortfall paths (halt-and-repair via resume ·
  declared-degraded with a failure manifest); COMPLETED ≠ COMPLETE in both directions;
  launch pre-flight; lower-bound honesty. `standing-rules-core` carries a two-sentence
  pointer, never a restatement.
- **`hooks/dispatch-gate/`** (Standard+): a PreToolUse gate over BOTH dispatch surfaces —
  sub-agent dispatches and dynamic workflows — via two matcher blocks with deliberately
  DISTINCT commands (the settings-merge dedup is matcher-blind; identical commands would
  silently drop a surface). Graded model-pin check (WARN undeclared / FAIL declared — never
  a brownfield retro-block); canonicalised hash check on the paste-in **fail-loud preamble**
  (`assertComplete` · a self-consistent `manifestDiff` whose `{expected, received, missing}`
  triple agrees with its coverage verdict on BOTH paths · `vacuityGuard` — an empty verifier
  set resolves UNVERIFIED, never confirmed · an auto-asserting `fanout`); the declaration
  lane in RETURN-LOCUS form (the gate confirms the sanctioned call in return position and
  reads the returned coverage field — it never greps a file body for verdict words); a
  hardened, audited escape hatch (no blanket scope, enumerated check-ids, resolvable
  artifact reference, append-only audit log); fail-OPEN-with-loud-WARN on any unknown
  payload shape (the dispatch tool's hook payload is upstream-undocumented — a gate that
  did not run must never look like a gate that passed); red/green fixtures + a
  known-positive self-test that MUST fire.
- **`scripts/doc-refs.sh` ships** — the docs-impact gate's mechanical gatherer (spec-first
  since 0.5.0, contract unchanged): five-state triage rows, fenced baseline/retirement
  lanes, canary-backed emptiness, loud internal-failure semantics (a tool error can never
  read as "no drift"), plus its known-positive fixture test. The CLEAR stage upgrades from
  recorded-manual-read to canary-backed proof.
- **Lint:** rule 18 gains filename-keyed charter detection (an `FR-NNNN` charter file can no
  longer early-return the detector — the silent-vacuity hole); NEW rule 19 enforces the
  baseline seal (sealed drift-inventory entries cannot be edited or laundered; not
  adopt-exempt, rule-17 class).
- **Field-nominated riders** (v0.5.0 convergence, credited generically): the overlay-resolution
  upgrade rule (a multi-tier file 3-ways against the highest tier ≤ the installed profile);
  the template-vs-instance line (amendments never auto-propagate; hand-apply is sanctioned);
  adopter-resolvable `related:` refs on the two docs-impact reference docs; the
  SOURCE-FIDELITY install rule (installs extract from the pinned ref, never a working tree);
  research-tier wording (runs at Standard too, both index copies, harmonized).

## 0.5.0 — 2026-07-11 (the docs-impact era)

The **docs-impact gate** (framework-rationale/0014) — the work discipline learns to ask
*"which documents did my change just falsify?"* — plus the **rewrite-conformance module**
(framework-rationale/0015) and the batch of field-nominated fixes from the v0.4.1 convergence.
Designed from a 4-repo field survey; 25 adversarial design findings + 4 build-verify findings
all applied.

- **docs-impact CLEAR** (spec-first): the `doc-refs` sweep contract — the diff-keyed twin of
  the unit-keyed `wu-refs` — ships at `reference/doc-refs-contract.md`; the gate wires into
  work-discipline (G2-docs generalized; self-skip only on a proven zero-referent sweep),
  the always-on cycle-start discipline (the ONE normative home of the five-state triage
  vocabulary: still-true · stale · uncovered · provenance/record-fact · unverifiable-locally),
  the dispatch return schema (`docs_impact`, proof-carrying — a bare "none" is as incomplete
  as a proofless falsifier claim), and an ADVISORY third pre-commit lane (routed, never
  touches rc). `reference/baseline-mechanism.md` makes brownfield-vs-cold-start first-class:
  new debt loud, inherited debt inventoried once and fenced, sealed against laundering.
  **The `scripts/doc-refs.sh` build is a chartered follow-up** — every invocation degrades to
  a no-op-with-notice until it lands.
- **`modules/rewrite-conformance/`** (opt-in, Full): the parity-ledger discipline harvested
  from the fleet's first certified rewrite — PARITY ≠ WIRED as a durable sibling tier of
  traceability/, golden-corpus oracle contract, three templates. Zero field code.
- **Lint rule 18** (FAIL): a `risk-tier: full` dispatch charter cannot advance past drafting
  without a resolvable `design-rev: REV-NNN` — a witness review is one lens, not the station
  (born from a first-operator process miss). Charter template → 2.1.0 with the carrier fields.
- **Rule 17 emphasis fix:** markdown-bold canonical values no longer false-FAIL (first-install
  finding; the prefix-matching lesson, third application).
- **Obligations ledger amendments** (framework-rationale/0012, dated): the session-boundary
  fast path (rows are for debts that OUTLIVE a session; same-session debts may take a journal
  line — gate-safety rows always required) and the public-repo gitignored-ledger variant.
- **Fixes:** kit-rationale citations path-qualified in adopter-facing text (the ADR-id
  collision class); the rule-17 adopt-exemption rationale erratum (rule 17 was never
  adopt-exempt — the instruction stands on schema-rule grounds; credited to the second field
  install); reference/index.md made overlay-correct (Full ships its own copy — retires the
  standalone-tier lint artifact); charter lifecycle vocabulary reconciled to "drafting";
  kit-upgrade gains the manifest kit_version consistency check; four leaked build-artifact
  XML tags swept from payload (incl. one shipped since v0.4.0 — the sweep is now a standing
  ship check).

## 0.4.1 — 2026-07-11 (the fleet-convergence standard)

Cut by operator directive as the version the entire fleet converges to. Doc-only deltas over the
P8-verified v0.4.0 machinery — first-field-adoption findings (the obligations surface's first
real install, same evening as the v0.4.0 tag): four doc clarifications + one field-contributed
manifest hardening:

- **Adopt-row self-exemption trap closed** (the headline): an instantiated `now/obligations.md`
  enters the manifest as `action: "create"`, NEVER `"adopt"` — an adopt-row is schema-exempt and
  would switch off lint rule 17 for the very file it guards. Stated in scaffold-plan §1.2b and
  kit-upgrade's promotion step.
- **`kit_commit` manifest field** (field-contributed): when `kit_ref` is a TAG, freeze the tag's
  resolved SHA alongside — tags can move, SHAs can't; verification compares against the SHA.
- **`multi_party` value schema stated:** JSON boolean, never a string.
- **Settled lifecycle disambiguated:** settling = strike + move to `## Settled` in one edit; the
  Settled entry is deliberately a compact audit stub (column fidelity lives in the journal).

## 0.4.0 — 2026-07-11 (first verified release)

Cut as the kit's first release to clear its own built-AND-verified bar: every surface below
passed the P8 end-to-end exercise (install → byte-identical uninstall; single-party install →
comms-gained → form promotion; adversarially audited) before this tag.

The **obligations ledger** (ADR-0012) — the first kit surface tracking what an agent is
**owed**, not just what it owes — plus the origin-posture rationale (ADR-0013) and two
field-evidenced linter fixes.

- **`examples/sample-review.md`** joins the gallery (seventh sample, same Sparrow WU-0042
  thread): a fully-populated REV-001 modeling the capture-ALL discipline — six findings across
  every severity (the NIT gets a disposition too), all four dispositions with reasons, every
  test-obligation form, and a verdict lifecycle updated in place. Adversarially verified for
  schema fidelity and fiction coherence before landing.

- **Inter-party debt ledger** (`framework-rationale/0012`): two directions (owed-by / owed-to),
  direction-aware HARD/SOFT class, per-row promise `Source`, and the two novel fields — a
  required, parseable **Trigger/by-when** and a required **default-if-silent** on every
  receivable ({chase-once, apply-default, never-chase-never-peek}). Gate-safety hard
  constraint: `apply-default` is forbidden on any HARD row whose counterparty is the operator
  or whose deliverable is an authorization. Rows point at `OQ-`/`WU-`/`REV-`/DEFER ids, never
  duplicate them; settled rows journal to `log.md` then prune.
- **Form follows workload, detected at install:** multi-party coordination ⇒ standalone
  `now/obligations.md` (template ships in the Standard overlay); single-party ⇒ a compact
  `## Obligations` handoff section. Detection = foreign agent-comms marker block
  (read-to-classify extension of the foreign-block rules) · agent-room CLI/config · the
  interview's coordination question — detect-then-confirm both ways, recorded as a
  `multi_party` manifest install-decision beside `kit_ref` (the twelve scalars stay twelve).
  `kit-upgrade` owns both form flips (section→file promotion; empty-ceremony retirement).
- **Skills wired:** `/handoff` sweeps the ledger (snapshot-before-mutate, atomic rows,
  materiality gate — hedges never become rows, ambiguous strength files SOFT); `/orient`
  surfaces landed / came-due / overdue + dangling-pointer and no-trigger rot checks; `/flush`
  updates the file mid-session. All branches key on the runtime fact (does
  `now/obligations.md` exist), never a scaffold token.
- **Origin posture** (`framework-rationale/0013`, informational): how the kit's own origin
  repo runs the discipline from a gitignored operator directory without contaminating the
  authored payload; the origin self-install doubles as the release-verification discipline leg.
- **lint-docs rule 17** (FAIL): every owed-to-me row carries a non-empty Trigger and a
  canonical default-if-silent; example-marker rows skipped (prefix-matched markers — the
  ADR-0011 lesson applied to its own new rule after a planted-violation proof caught the
  exact-literal variant); absent file = silent pass; malformed table = one WARN, never a crash.
- **Linter gaps from the field** (second adopter A/B evidence, verified firsthand in code):
  rule-8 bare-slug resolution now reaches `now/` (scoped via `include_now` so rule-13 index
  completeness is unchanged; ambiguity-FAIL remains the collision guard) and rule-9 no longer
  ADR-classifies calendar-dated `YYYY-MM-DD-slug.md` artifacts outside `decisions/`. Both
  proven by planted violations, both directions.
- **SessionStart snippet hardened:** a crashed linter now emits a fallback advisory line
  instead of silently emptying the nudge under `|| true` (the silent-vacuity class, again).
- **P8 release-verification fixes** (first full end-to-end concierge exercise — two throwaway
  repos, install → uninstall byte-identical reversal + single-party install → comms-gained →
  section→file promotion, adversarially audited): stray `</content>` tag removed from the
  obligations template's last line; scaffold-plan gains the missing stack-pack placement step
  (2.1a — `stacks/<lang>/{rules,code-intel}.md` → `.claude/rules/<lang>-*`, previously dropped
  by a doc-literal install); handoff template now ships the `## Obligations` single-party stub
  (kills the hand-authoring variance); example rows RETAINED at install (rule 17 skips them;
  the adopter deletes on first real use); stale `backup-path` field name corrected to the
  canonical `backup` in uninstall.md + the install skill; `.kit-backups/` residue surfaced in
  uninstall; duplicate review-template index-row instruction corrected (the row already ships);
  go pack's `{{LINT_CMD}}` un-compounded (`golangci-lint run` subsumes `go vet`); promotion's
  section-removal warned about the section-at-EOF silent no-op (found by the field-preservation
  re-proof, which now passes from committed artifacts: every field carried, both directions,
  idempotent re-run, live pre-commit gate green throughout).

## 0.3.2-dev — 2026-07-10

Post-harvest cherry-pick batch: the smalls nominated by the 0.3.x UPSTREAM sweep, plus a stale-label
fix its deliberations exposed. Doctrine only — no mechanism, no new surfaces.

- **"Never answer from absence"** doctrine line in `standing-rules-core.md` (§Adversarial separation
  of duties): an empty scoped retrieval is evidence about the query, not the world — widen and
  retrieve before concluding absence.
- **ID-prefix rename crosswalk rule** in kit-upgrade's retro-adoption branch: retired IDs stay
  resolvable via a crosswalk table in the renaming ADR, never silently deleted; an accepted ADR
  outranks an open question at reconciliation (pairs with the existing `supersedes:` flag).
- **Fork-slot cross-ref** in `merge-strategy.md` §Foreign marker blocks: the seam discipline
  inverted — kit docs may ship deliberately-unfilled local-idiom slots (work-discipline's "Your
  gate idiom"); the filled slot is preserved the way installs preserve foreign blocks.
- **CONVENTIONS lint-rules section made tier-true** (header + honesty note claimed the schema linter
  was "not yet implemented" — text predating `lint-docs.py`): ADVISORY at Minimal, enforced at
  Standard+ (FAIL except rule 12 WARN-then-FAIL; kit-local rule-16 advisory WARN-only).
  Adopt-exemption unchanged.

## 0.3.1-dev — 2026-07-10

Field-hardening pass from the first retro-adoption shakedown (public-fork + source-repo cases) and
the first pre-existing-corpus adopter:

- **Nameless marker variant (ADR-0011 amended).** Leak-gated public repos may write
  `<!-- kit:start (<kit-version>) -->` (label dropped, version kept). Matching everywhere is by the
  `kit:start (` prefix with the label OPTIONAL; `merge-tool.py --marker-label` writes it (empty
  label = nameless). Cross-form replace-in-place proven by test.
- **Source-repo posture** in kit-upgrade's retro-adoption: an origin repo classifies only the
  back-ported subset, marks its inventions UPSTREAM, fences nothing it authored; leak-gated repos
  may gitignore the manifest via a local ADR. Plus the git-mv stage-before-commit note.
- **Manifest adopt-exemption** in `lint-docs.py`: files carried in `.kit-manifest.json` with
  `action: "adopt"` (a pre-existing corpus adopted in place) are exempt from the schema-class rules
  (front-matter presence/validity, provenance, staleness) but remain subject to rule-13 index
  completeness. Malformed/absent manifest = no exemptions, no crash.

## 0.3.0-dev — 2026-07-10

Wave-3 pass: shipped the gate-runner **agents-starter** crew and the **recurrence-guard** enforcement
module (both opt-in, never default), plus the deterministic reachability oracle the crew cites. No
field-install bytes ship — the six agent skeletons, the guard template, and the reachability fragments
are all de-hosted, generalized mechanism.

- **New Full-tier opt-in module — `agents-starter`.** Six token-filled sub-agent templates →
  `<target>/.claude/agents/`, one per leg of the dispatch-charter lifecycle: **`tactical-planner`**
  (decompose a `WU-NNNN` into file-disjoint waves + author each charter's Part-A work-spec),
  **`recon-verifier`** (read-only scope recon → the unit's complete file-ownership set),
  **`quality-engineer`** (the RED-on-HEAD falsifier matrix + proven-non-vacuous negative controls),
  **`docs-sync`** (reconcile docs to the wave diff, self-skip on no-impact), **`integration-auditor`**
  (IMPL→WIRED reachability proof — the built-but-not-wired trap), and **`completion-agent`**
  (fresh-context close-out verifier). Every template **points at `standing-rules-core.md` for the
  dispatch contract and never restates it** (the #1 silent-drift risk); carries a mandatory degradation
  guard (referenced artifact missing / operator-waived → flag the operator, never invent a tracked file);
  pins a `cheap | standard | deep` model tier per the model-pinning rule; and files findings into the
  existing spine sinks (a `traceability/` row + the charter's verifier report). `recon-verifier` /
  `integration-auditor` / `completion-agent` are read-only by construction. Offer-gated: only when the
  dispatch-charter module + the `traceability/` ledger are installed. The module wires no hook and no
  `settings.json` block — Claude Code discovers agents by reading `.claude/agents/`.
- **Roster exclusions (v1).** Three agents from the same field lineage are deliberately left out:
  `requirements-analyst` and `plan-reviewer` (anchored to intake/review maturity that is not yet a
  load-bearing default — shipping their prompts would smuggle an unadopted pipeline in through the back
  door of a role definition), and `security-engineer` (its substance is the ~100%-host-specific
  per-project attack surface — a HOST-fill-only body would be an empty shell). Each flips in on a named
  condition: the intake/review home lands as default payload; the owner commits a red-team findings home.
- **New Standard+ opt-in module — `recurrence-guard`.** A freshly-authored commit-blocking grep-guard
  skeleton (`template.sh`) mirroring revisit-ledger. When a decision closes a bug class, one
  `scripts/<bug-class>-guard.sh` **fails the commit** if the banned idiom reappears — the rule is
  enforced, not merely remembered. Ships the determinism-split doctrine (deterministic residue → hook,
  judgment → reviewer), a positive-control sentinel (fails LOUD when a rename strips every matchable
  token), and loud fail-open when the analysis engine is absent. One guard per bug class; inert until
  `BANNED` is filled; zero lines of the field scripts ship.
- **Stack reachability fragments.** Every `stacks/<lang>/code-intel.md` gains a named
  **`## Reachability baseline`** section — the deterministic dead/unreachable-code oracle the agent
  templates cite for the IMPL→WIRED check: `deadcode` (go), `knip` (node-ts), `vulture` (python), the
  rustc/clippy `dead_code` gate + `cargo-udeps`/`cargo-machete` (rust), and the honest grep-floor
  call-chase (generic). Each carries a degradation fallback (tool absent → grep-floor, record textual
  evidence in `traceability/`, never invent an analysis-backed verdict) and a currency note dated
  2026-07-10.
- **Concierge + manifest wiring.** `profiles.md`, `interview.md` (Q5), and `scaffold-plan.md` gain the
  offer + copy steps for both modules — agents-starter → `.claude/agents/` with `<!-- HOST: … -->` blocks
  resolved post-install; recurrence-guard → `scripts/` + a per-bug-class pre-commit registration.
  `ship-manifest.md` flips `agents-starter` to **built** and adds the `recurrence-guard` row.
- **Deferred to 0.3.x — the UPSTREAM-class harvest sweep.** The fleet's ahead-of-kit field surfaces (a
  red-team review tier, an events/measurement firewall, populated `reviews/` exemplars, and the other
  UPSTREAM queues) remain **pending the fleet's completion reports**: each surface is still adjudicated
  kit-side against its existing flip-condition before harvest, never flattened. Scoped for a later 0.3.x
  cut.

## 0.2.0-dev — 2026-07-09

Fleet-reconciliation pass: upstreamed the Wave-1 field inventions, fixed 7 defects in the shipped
kit, and ratified four owner rulings. Every upstream was de-hosted — no field-install bytes ship,
only the generalized mechanism.

- **Wave-1 upstreams** (each distilled from the field-install lineage, generalized): index-ledger
  markdown-link matcher unioned into both index linters + CONVENTIONS rule 13; sep-of-duties residue
  folded into `framework-rationale/0006` (rejected military-operations-order vocabulary + the
  maker-checker/prior-art section); cycle-start inbound-reference-sweep rationale (new
  `framework-rationale/0009`) + the `wu-refs.sh` `dogfood/` group and a trailing catch-all;
  standing-rules **memory-locality** (durable knowledge in repo-local `.agent-docs/`) and
  **model-pinning on every dispatch**; claim-level **veracity markers** in CONVENTIONS §2 + the ADR
  proposed→accepted gate; orient/handoff gain live git state, TRUST-THE-CODE staleness precedence,
  work/doc commit-separation guidance, and `$ARGUMENTS` notes; **wave-probe discipline** (recon-first
  rule, non-builder-READ-ONLY + worktree-isolation dispatch clauses, a 4-row failure-mode table, and
  full-addendum §D wave-decomposition sentences).
- **New Standard payload** — the typed **review-report ledger**: `reviews/index.md` seed +
  `templates/review-template.md`, the `REV-NNN` spine (3-digit, monotonic), per-finding disposition +
  the test-obligation column; rationale `framework-rationale/0010`. ID spine adds `REV`.
- **New Full payload** — `reference/work-discipline.md`, the gated-delivery standard-of-record
  (INTAKE→G0→…→G4 mapped onto the FR-charter lifecycle; reference-not-restate over standing-rules).
- **7 defect fixes** — canonical marker convention (below); dangling scope-recon reference (the
  recon-first rule now exists); `wu-refs.sh` group asymmetry (`dogfood/` + catch-all so no
  `.agent-docs/` subtree is silently unswept); `lessons/index` `kebab-slug-of-claim`; `eval` removed
  from the safety hook's cwd rule (case-limited expansion — command substitution is never executed);
  hook-cwd assumption documented + self-checked against `CLAUDE_PROJECT_DIR`; `framework-rationale/0006`
  restored to the mandatory ADR-section shape.
- **Marker-convention ruling** — `<!-- kit:start (fieldbook <ver>) -->` … `<!-- kit:end -->` is
  canonical across install / upgrade / uninstall / merge; blocks are matched by `kit:start` prefix
  regex (never an exact-version string), and foreign (non-kit) marker blocks are preserved verbatim,
  never merged into, never claimed.
- **Charter slim** — `dispatch-charter-template.md` v2.0.0: **Part A** (work-spec) is the whole
  charter for most dispatches; **Part B** (lifecycle sections) is opt-in for load-bearing / multi-wave
  work. The run journal / workflow log is the dispatch record; a charter exists only when a scoped
  work-spec adds value.
- **New concierge machinery** — `concierge/merge-tool.py`, the kit-side mechanical write primitive
  (marker replace-in-place, hook append + exact-command dedup, permission union, per-write backups +
  JSONL manifest ledger, byte-idempotent SKIP, refuse-don't-clobber) + its `maintainer/tests/`
  suite; a `kit-upgrade` **retro-adoption** branch (adoption plan + manifest backfill for
  manifest-less kit-lineage repos); and a `kit-doctor` **hook-registration check**
  (script-present-but-never-registered is a FAIL).

## 0.1.0-dev — 2026-07-03

- P0+P1: scrub gate, ship-manifest, stack-agnostic base extraction.
- P2–P6: portable hooks + stdlib doc-schema linter, lifecycle skills, stack packs
  (rust/node-ts/python/go/generic), framework rationale, sanitized examples, and the
  install concierge (interview → scaffold → merge → verify → tour).
- Statusline module (`modules/statusline/`): opt-in, python-only status line (repo/branch,
  model + context, auto-compact, ctx %/tokens, 5h/7d rate limits, account email); concierge
  offers it at any profile, global or project scope. Instructions in the module README.
