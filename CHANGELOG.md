# Changelog

All notable changes to the Fieldbook kit. Versions track `kit-version.txt`.

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
