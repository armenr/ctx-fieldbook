# Changelog

All notable changes to the Fieldbook kit. Versions track `kit-version.txt`.

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
