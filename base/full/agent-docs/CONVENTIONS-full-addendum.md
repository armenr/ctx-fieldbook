---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [meta, schema, conventions, full-profile]
related: [CONVENTIONS, index, glossary]
---

# CONVENTIONS — Full-profile addendum

The **Full profile** additions to the core schema contract. This doc **references** the core
`CONVENTIONS.md` by section number; it does not restate it. Read the core first — everything there
(progressive disclosure §0, front-matter §2, the WU/ADR/OQ/LP spine §4, the decision policy §5, the
10-point checkpoint contract §6, per-dir index routing §7.1) still holds. This addendum adds the
modules a project turns on once it starts fanning work out to sub-agents and needs
production-reachability proof: **dispatch-charters / wave-plans, the research pipeline, the IMPL→WIRED
traceability ledger, the revisit-ledger, and incidents / experiments / runbooks.**

---

## A. Taxonomy additions (extends core §1)

Same write-discipline legend as core §1. Caps are GUIDANCE (core §Token-budget), not lint-enforced.

| Dir | Holds | Write-discipline | Caps · notes |
|---|---|---|---|
| `research/` | One `research/<R-id>/` dir per investigation, with codified pipeline tiers: `00-landscape.md → NN-<track>.md → adversarial.md → synthesis.md` (§B) | APPEND-ONLY within an `<R-id>`; `synthesis.md` UPDATE-IN-PLACE until sealed | `synthesis.md` is the only Tier-2 surface; raw tracks stay in the subdir. |
| `dispatch-charters/` *(name renameable to taste)* | Dispatch-charters as sub-agent / workflow-step specs (one-file-one-owner, recalibrated-scope vs the live tree, wiring-proof target); the parent **wave-plan** | APPEND-ONLY | Ledger TABLE in `dispatch-charters/index.md` (§D). |
| `traceability/` | The **IMPL→WIRED ledger** (§C) — production-reachability proof, not test-pass. One row per work-unit. | UPDATE-IN-PLACE (per work-unit rows) | One ledger; row = work-unit. Keep the discipline, not a monolith. |
| `runbooks/` | Operational procedures; read end-to-end before running | UPDATE-IN-PLACE | up to 300 lines, hard 500. |
| `incidents/` | Post-mortems, date-prefixed; incident genealogy feeds `lessons/` + rules | APPEND-ONLY | `YYYY-MM-DD-<slug>.md`. |
| `experiments/` | Spikes/probes with captured outcome (the throwaway-spike home; promote durable findings to `reference/`) | APPEND-ONLY | `YYYY-MM-DD-<slug>.md`. |
| `dogfood/` *(optional)* | Self-audit findings — where the project runs its own quality tooling ({{CODE_INTEL_TOOL}}, linters, analyzers) against its own code — plus a triage **INDEX** (§E) | APPEND-ONLY (findings) + UPDATE-IN-PLACE (the triage index) | Findings date-prefixed; index is the routing surface. |

Deeper nesting is allowed for the mandated cases only: `research/<R-id>/`, plus the core's
`now/lessons/` and `lessons/archive/`. **No new top-level category without an ADR** (core §1).

**Naming additions (extends core §3):**
- **Research:** `research/<R-id>-<slug>/` dir; files `00-landscape.md`, `NN-<track>.md`,
  `adversarial.md`, `synthesis.md`.
- **Dispatch-charters:** `dispatch-charters/YYYY-MM-DD-wNN-<slug>.md` (`wNN` = zero-padded wave number).
- **Incidents / experiments:** `YYYY-MM-DD-<slug>.md`.

---

## B. ID spine additions (extends core §4)

The prefix still encodes the artifact's type; the ID is still the join key; cross-references still
cite the ID, not a body excerpt (core §0.5).

| Prefix | Type | Format | Lives in | Lifecycle |
|---|---|---|---|---|
| `FR-NNNN` | **Dispatch-charter** — a scoped sub-agent / workflow-step spec under a wave-plan | `FR-NNNN` | `dispatch-charters/` | drafted → dispatched → verified |
| `RV-NNN` | **Revisit anchor** — a typed change-intent marker in code (`REVISIT(RV-NNN <class>): <intent>`), classes `until:` · `retire-at:` · `twin:` · `claim:` | `RV-NNN` | code comments ↔ `reference/revisit-ledger.md` | live → retired (markers removed, ledger row moved) |
| `R-NNNN` | **Research investigation** — the pipeline dir id | `R-NNNN` | `research/` | landscape → tracks → adversarial → synthesis → sealed |
| `INC-NNN` | **Incident** | `INC-NNN` | `incidents/` | open → remediated → prevention-linked |

**Reconciliation (extends core §4):**
- **One WU keys a fan-out.** When a `WU` decomposes into a dispatch fan-out, each leg is an `FR-NNNN`
  carrying `work-unit: WU-NNNN`. The verifier stage (§D) and the checkpoint (core §6) both key back to
  the same `WU`.
- `RV-NNN` (a code-anchored change-intent marker) and `OQ-NNN` (an unresolved question) are
  **orthogonal** to `ADR-NNNN` (a settled decision): a resolved `OQ` cites the `ADR` that closed it;
  an `ADR` may spawn `RV` anchors for its lockstep surfaces. Different *phases* of one idea, not
  competing namespaces.
- IDs are **never reused**; retired IDs stay resolvable (supersession-not-deletion, core §5).

---

## B′. Model-tiering field (extends core §7.3 evidence-on-disk)

Sub-agent / dispatch-stage specs carry a **model-tier hint** (`cheap | standard | deep`): cheap work
(mechanical edits) → cheaper model, cross-cutting design → deeper model. It is a **config field, not
an inline decision** — declared in the charter front-matter, not argued in prose each time.

---

## C. IMPL→WIRED traceability (`traceability/`)

The #1 recurring, expensive failure this ledger exists to catch: **code that compiles and passes
tests but is never reachable from a production entrypoint — the built-but-not-wired trap.**
**Verification is by production-reachability, not test-pass.**

The `traceability/` ledger carries one row per work-unit with an explicit **`IMPL` / `WIRED` /
`DEFER`** state. `WIRED` requires a *traced path* from a production entrypoint (a real `main()`, a
served command, a public API surface) to the new code. `DEFER` is a legitimate, written-down state
(with a reason) — a half-wired surface silently left as "done" is not.

**Prove reachability with the best tool the project has — a menu, floor first-acceptable:**
1. `{{CODE_INTEL_TOOL}}` reachability / call-path query, if the project ships one.
2. Else an **LSP find-references** on the new symbol.
3. Else an **LSP call-hierarchy** from the production entrypoint down.
4. Else a **language call-graph tool** (whatever {{PRIMARY_LANGUAGE}} offers).
5. Else **grep-the-callers** as an explicit floor (record the query + result).
6. Else a **manual-trace note** in the row, naming the entrypoint and the hop chain by hand.

Cross-layer lockstep surfaces are anchored with **REVISIT `twin:`** markers (§F). This is a
**mandatory gate stage at phase boundaries**, not an afterthought. **IMPL → WIRED is the acceptance
bar, not test-pass** — a unit of work is done only when a path traces from a real entrypoint to the
new code, and that state is recorded in the ledger keyed to its `WU`.

---

## D. Dispatch-charters, wave-plans, and the verifier gate (extends core §7.2)

Core §7.2 states the discipline: **the reviewer is never the builder; it applies to designs, not
just code.** The Full profile realizes it operationally.

**Dispatch-charter (`FR-NNNN`).** A `WU` is decomposed into **one-file-one-owner** charters, each
recalibrating the parent plan's stale scope assumptions against the **live tree** (survey first, then
charter) and naming its **wiring-proof target** (the production entrypoint the work must be reachable
from, §C). Two charters in the same wave must not own the same file.

**Wave-plan.** The parent decomposition. Legs are sequenced into **waves by file-overlap** so
parallel legs touch disjoint files; the orchestrator verifies file-disjointness *before* launching a
parallel wave.

**Verifier gate stage.** Independent verification is a **clean-context reviewer with no authorship
stake, run as a gate stage** before the design/code proceeds: it re-derives the claim (especially
**production-reachability**, §C) against the live tree, independently of the builder's assertion. The
executor never audits its own work. Reviews are keyed to the `WU`/`FR` they gate. **This applies to
DESIGNS too** — `design → adversarial-review` BEFORE implementation, not only after.

**Dispatch persistence is the tooling's job.** The durable **principle** is: the persisted brief is
ground truth — never reconstruct a prompt from memory on retry. Let the dispatch tooling persist and
replay charters verbatim; do not hand-persist prompts as a manual file step.

See `templates/dispatch-charter-template.md` for the full charter scaffold (charter → brief-back →
state-recon → gate verdicts → verifier report → remediation log → operator decision).

---

## E. Research pipeline tiers (`research/<R-id>/`)

Every investigation follows codified tiers, one file per tier:
`00-landscape.md` (broad survey) → `NN-<track>.md` (parallel deep tracks, one file each) →
`adversarial.md` (a **clean-context skeptic re-checks the tracks' decision-critical claims against
PRIMARY sources**) → `synthesis.md` (the only Tier-2-loaded surface; reconciles tracks, records
confidence + residual gaps). Raw tracks stay in the subdir (Tier-3-ish); callers load `synthesis.md`
and reference-by-`R-id`. **Currency-check every decision-critical claim against current-year primary
docs, never training data.** See `templates/research-synthesis-template.md`.

### Dogfood triage INDEX (`dogfood/`, optional)

Where the project runs its own quality tooling against its own code, findings are append-only,
date-prefixed; the **triage INDEX** (`dogfood/index.md`) is the routing surface — it triages each
finding (severity · status · owning WU/ADR) so the corpus stays a navigable backlog, not a dumping
ground. Findings that harden into rules feed `lessons/` + `incidents/`.

---

## F. The revisit-ledger (`reference/revisit-ledger.md`)

**Typed change-intent markers in code comments:** `REVISIT(RV-NNN <class>): <intent>`, classes:
- **`until:`** — interim; lifts at a named event.
- **`retire-at:`** — throwaway; delete at a named point.
- **`twin:`** — a cross-layer lockstep surface (two places that must move together — e.g. a schema
  ↔ its parser ↔ its consumers, or an interface ↔ its implementations).
- **`claim:`** — one fact restated across layers.

**Same-change rule:** creating such a surface ⇒ marker + a row in `reference/revisit-ledger.md`,
together; resolving ⇒ remove the markers + move the row to a §Retired section with the landing
commit. The row's site list is the **SWEEP SET** — consult it before changing anchored code. Orphan
markers (no ledger row) and dangling rows (no marker) are lint failures.

---

## G. log.md op-vocabulary additions (extends core §log.md)

Beyond the core op set, the Full profile logs: `dispatch` (charter sent) · `research` (R-id tier
completed) · `incident` · `dogfood` (self-audit finding).

## Related

- `CONVENTIONS.md` — the core schema contract (normative; this addendum only extends it)
- `templates/index.md` — the Full-profile scaffolds (dispatch-charter, research-synthesis, runbook,
  incident, experiment)
- `.claude/rules/standing-rules.md` — the operational rules (orchestration, dispatch contract,
  adversarial separation) that reference this schema
