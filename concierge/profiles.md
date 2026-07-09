---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
tags: [concierge, profiles, payload-map]
related: [interview, scaffold-plan, parameters, merge-strategy]
---

# Profiles — payload map, recommendation tree, upgrade path

Three additive profiles. Each is a **superset of the one below it** — Standard is Minimal + the
`standard/` payload; Full is Standard + the `full/` payload + opted-in modules. This file is the
authoritative map from a chosen profile to the **exact on-disk kit paths** the concierge copies. All
paths are relative to this kit folder. The scaffold *order* + fill/rename/assemble rules live in
`scaffold-plan.md`; this file is the WHAT, that file is the HOW.

> **Physical split = clean additivity.** The payload dirs (`base/minimal/`, `base/standard/`,
> `base/full/`) are disjoint and copy on top of each other. Upgrading a profile later re-runs the
> concierge in add-module mode and copies only the newer tier's payload — nothing already installed is
> rewritten (`merge-strategy.md`).

---

## 1 · Minimal — the payload

The `now/` state spine + the cold-start loop + the schema + the ADR habit. Source: **`base/minimal/`**
(everything under it) plus the selected stack pack.

### `.agent-docs/` (from `base/minimal/agent-docs/`)
| Kit source | Installs to `<target>/.agent-docs/` | Note |
|---|---|---|
| `CONVENTIONS.md` | `CONVENTIONS.md` | token-fill (`{{PROJECT_NAME}}`, `{{PROJECT_ONE_LINER}}`) |
| `index.md` | `index.md` | root catalog; token-fill; prune Full-only rows for this profile |
| `glossary.md` | `glossary.md` | token-fill |
| `log.md` | `log.md` | seeded append-only journal |
| `charter.template.md` | `charter.md` | fill + drop `.template` |
| `now/status.template.md` | `now/status.md` | fill + drop `.template` (seeded valid) |
| `now/work-plan.template.md` | `now/work-plan.md` | fill + drop `.template` |
| `now/open-questions.template.md` | `now/open-questions.md` | fill + drop `.template` |
| `now/handoff.template.md` | `now/handoff.md` | fill + drop `.template` (seeds a cold `/orient`) |
| `now/index.md` | `now/index.md` | verbatim-ish (token-fill if any) |
| `now/lessons/MOC.template.md` | `now/lessons/MOC.md` | fill + drop `.template` |
| `now/lessons/proposals.template.md` | `now/lessons/proposals.md` | fill + drop `.template` |
| `decisions/index.md` | `decisions/index.md` | verbatim |
| `lessons/index.md` | `lessons/index.md` | verbatim |
| `templates/*` | `templates/*` | verbatim (adr, checkpoint, handoff, lesson, memory, index, index-template) |

### `.claude/` (from `base/minimal/claude/`)
| Kit source | Installs to `<target>/.claude/` |
|---|---|
| `rules/agent-docs.md` | `rules/agent-docs.md` |
| `rules/sensitive-data.md` | `rules/sensitive-data.md` |
| `hooks/sessionstart-state-router.sh` | `hooks/sessionstart-state-router.sh` |
| `hooks/precompact-handoff-trigger.sh` | `hooks/precompact-handoff-trigger.sh` |
| `skills/orient/SKILL.md` | `skills/orient/SKILL.md` |
| `skills/flush/SKILL.md` | `skills/flush/SKILL.md` |
| `skills/handoff/SKILL.md` | `skills/handoff/SKILL.md` |
| `settings.json.template` | `settings.json` | fill + drop `.template` + **prune** to installed hooks (`scaffold-plan.md` §settings) |

### Stack pack (Minimal takes only what it uses)
- `rules.md` + `code-intel.md` from the selected `stacks/<lang>/` → placed as the target's language
  context (`scaffold-plan.md` decides final location); token-fill.
- `allowlist.json` → unioned into `settings.json`.
- **Gate fragment is NOT spliced at Minimal** — the PreToolUse safety-gate hook is a Standard payload
  (`pretooluse-safety-gates.base.sh` lives under `base/standard/`). Minimal ships no safety-gate hook.

### Enforcement at Minimal
- SessionStart + PreCompact hooks (state routing + handoff nudge).
- Index-completeness lint runs **WARN-mode** via the SessionStart router *if* a Minimal index-lint
  script is present (see `scaffold-plan.md` §enforcement-gap: the router probes
  `.claude/hooks/lint-agent-docs-indexes.sh`; the full doc-schema linter arrives at Standard).
- ID spine: `WU` · `ADR` · `OQ`.

---

## 2 · Standard — adds (recommended default)

Everything in Minimal **plus** the `base/standard/` payload + the assembled safety gate.

### `.agent-docs/` (from `base/standard/agent-docs/`)
| Kit source | Installs to | Note |
|---|---|---|
| `checkpoints/index.md` | `checkpoints/index.md` | verbatim |
| `memories/index.md` | `memories/index.md` | verbatim |
| `reference/index.md` | `reference/index.md` | seed stub; root `index.md` routes to `reference/` at Standard |
| `reviews/index.md` | `reviews/index.md` | verbatim — the typed `REV-NNN` review-report ledger seed (0.2.0); root `index.md` routes to `reviews/` at Standard |
| `templates/review-template.md` | `templates/review-template.md` | verbatim — one `REV-NNN` report per review pass; **its `templates/index.md` catalog row must ship** (see scaffold-plan §1.2 note) |

### `.claude/` (from `base/standard/claude/`)
| Kit source | Installs to | Note |
|---|---|---|
| `rules/standing-rules-core.md` | `rules/standing-rules-core.md` | token-fill (`{{WORKSPACE_LAYOUT}}`, `{{PANIC_EQUIVALENT}}`, gate cmds, `{{CODE_INTEL_TOOL}}`) |
| `rules/standing-rules-rationale.md` | `rules/standing-rules-rationale.md` | on-demand rationale |
| `hooks/lint-docs.py` | `hooks/lint-docs.py` | **verbatim** (no tokens; stdlib-only linter) |
| `hooks/lint-docs.README.md` | `hooks/lint-docs.README.md` | verbatim |
| `hooks/install-hooks.sh` | `hooks/install-hooks.sh` | verbatim (wires `core.hooksPath`) |
| `hooks/subagentstart-prefix.sh` | `hooks/subagentstart-prefix.sh` | token-fill (`{{PROJECT_NAME}}`) |
| `hooks/README.md` | `hooks/README.md` | verbatim |
| `hooks/pretooluse-safety-gates.base.sh` | (not copied directly) | **base for assembly** → see below |
| `skills/sitrep/SKILL.md` | `skills/sitrep/SKILL.md` | token-fill |
| `skills/debrief/SKILL.md` | `skills/debrief/SKILL.md` | token-fill (`{{PRIMARY_LANGUAGE}}`, `{{CODE_INTEL_TOOL}}`) |
| `skills/distill-lessons/SKILL.md` | `skills/distill-lessons/SKILL.md` | token-fill |

### The assembled safety-gate hook (Standard+ only)
- Base: `base/standard/claude/hooks/pretooluse-safety-gates.base.sh`.
- Splice: the selected `stacks/<lang>/gate-fragment.sh` at the base's **STACK-FRAGMENT INSERTION POINT**
  marker, plus any project-specific `ask`/`block` rules captured in interview Q5.
- Fill `{{DEFAULT_BRANCH}}`, `{{PACKAGE_REGISTRY}}`, `{{WORKSPACE_LAYOUT}}`.
- Output → `<target>/.claude/hooks/pretooluse-safety-gates.sh`. (Full procedure: `scaffold-plan.md`
  §assemble-safety-gate.)

### The git pre-commit gate (Standard+)
| Kit source | Installs to | Note |
|---|---|---|
| `base/standard/githooks/pre-commit` | `<target>/.githooks/pre-commit` | token-fill (`{{LINT_CMD}}`, `{{FMT_CMD}}`) |
| — | wire via `install-hooks.sh` | sets `core.hooksPath=.githooks`; disables a stale `.git/hooks/pre-commit` |

### Enforcement at Standard
- Everything from Minimal **plus** the PreToolUse safety gate, the doc-schema linter (`lint-docs.py`,
  blocking opt-in via pre-commit), the SubagentStart prefix, and the path-aware pre-commit dispatcher.
- The typed review-report ledger (`reviews/`, `REV-NNN` + per-finding disposition + test-obligation) —
  the durable home the findings-to-disk standing rule mandates.
- ID spine adds `LP` (lessons) · `REV` (reviews).

---

## 3 · Full — adds

Everything in Standard **plus** the `base/full/` payload + opted-in modules.

### `.agent-docs/` (from `base/full/agent-docs/`)
| Kit source | Installs to | Note |
|---|---|---|
| `CONVENTIONS-full-addendum.md` | `CONVENTIONS-full-addendum.md` | token-fill; references (never restates) the core |
| `reference/work-discipline.md` | `reference/work-discipline.md` | token-fill (gate cmds + `{{CODE_INTEL_TOOL}}`); the gated-delivery standard-of-record (0.2.0) — a Full addition to the Standard `reference/` dir |
| `traceability/index.md` | `traceability/index.md` | the IMPL→WIRED ledger surface |
| `dispatch-charters/index.md` | `dispatch-charters/index.md` | dispatch-charter / wave-plan ledger |
| `research/index.md` | `research/index.md` | pipeline dir routing |
| `runbooks/index.md` | `runbooks/index.md` | |
| `incidents/index.md` | `incidents/index.md` | |
| `experiments/index.md` | `experiments/index.md` | |
| `templates/dispatch-charter-template.md` | `templates/dispatch-charter-template.md` | token-fill (gate cmds, `{{WORKSPACE_LAYOUT}}`, `{{PANIC_EQUIVALENT}}`, `{{CODE_INTEL_TOOL}}`); **v2.0.0 compact shape** — Part A (work-spec) is the whole charter for most dispatches, Part B (lifecycle sections) is opt-in for load-bearing / multi-wave work |
| `templates/research-synthesis-template.md` | `templates/research-synthesis-template.md` | |
| `templates/runbook-template.md` | `templates/runbook-template.md` | |
| `templates/incident-template.md` | `templates/incident-template.md` | |
| `templates/experiment-template.md` | `templates/experiment-template.md` | |
| `templates/index.md` | merge into `templates/index.md` | the Full templates extend the Minimal `templates/index.md` catalog |

> The root `.agent-docs/index.md` Full rows (traceability/dispatch-charters/research/runbooks/
> incidents/experiments) are UN-pruned at Full — keep them; prune them for Minimal/Standard.

### Modules (opt-in, from interview Q5)
| Module | Kit source | Installs to |
|---|---|---|
| research pipeline | `modules/research-pipeline/SKILL.md` | `<target>/.claude/skills/research-pipeline/SKILL.md` |
| revisit-ledger | `modules/revisit-ledger/revisit-ledger.template.md` | `<target>/.agent-docs/reference/revisit-ledger.md` (fill + drop `.template`) |
| revisit-ledger | `modules/revisit-ledger/revisit-lint.sh` | `<target>/.claude/hooks/revisit-lint.sh` |
| revisit-ledger | `modules/revisit-ledger/README.md` | reference only (not copied to target) |
| statusline (ANY profile) | `modules/statusline/statusline.py` | **global:** `~/.claude/statusline.py` · **project:** `<target>/.claude/statusline.py` (+ a `statusLine` block in the chosen `settings.json` — see the module README) |

> The statusline is available at **any** profile (it's a per-user quality-of-life add-on, not tied to
> Full) and is the one module whose **global** form writes to `~/.claude` — the concierge asks scope
> (global/project) and gets a distinct yes for a global write.

> `agents-starter` / `native-lite` appear in the distillation plan as Full-tier opt-in modules. Offer
> them ONLY if their directory exists under `modules/` in this kit build; otherwise they are not part of
> this build and the concierge does not mention them.

### Enforcement at Full
- The full gate set + the traceability ledger + (if opted) the revisit-lint pre-commit check.
- The gated-delivery standard-of-record (`reference/work-discipline.md`) — maps the gate loop onto the
  FR-charter lifecycle so a Full install has one definition of "done".
- ID spine adds `FR` (dispatch-charter) · `RV` (revisit) · `R` (research) · `INC` (incident).

---

## 4 · Recommendation decision tree

Canonical logic (the interview restates the friendly framing; this is the rule):

```
start: Standard
│
├─ low-ceremony signal?  → down-sell to Minimal
│    ANY of: solo repo (git shortlog -sn shows one author)
│          · no CI config (.github/workflows, .gitlab-ci.yml, etc. absent)
│          · no test command detected
│          · scripts / prototype / docs-only repo
│          · friend says "keep it light / basics only / minimal process"
│
├─ explicit heavy signal? → up-sell to Full
│    ANY of: already runs sub-agent / multi-agent dispatch
│          · asks for reachability tracking / a traceability ledger
│          · asks for a research / investigation workflow
│          · says "give me everything / the full thing"
│
└─ else: hold Standard (the default)
```

Rules:
- **Standard is the floor recommendation** — it carries the safety gate and the IMPL→WIRED discipline,
  which are what pay for themselves.
- **Down-sell freely, up-sell only on an explicit ask.** Never push Full unprompted; it buries the
  differentiator under ceremony (distillation decision #3).
- Always close with **"start small, grow later"** — the upgrade is additive and re-runnable, so a
  Minimal pick is never a wrong pick.
- The friend's stated choice **overrides** the recommendation. Recommend, don't gate.

---

## 5 · Additive upgrade path

Upgrading is **copy the next tier's payload on top; rewrite nothing**.

- **Minimal → Standard.** Re-run the concierge (add-module / upgrade mode). It copies `base/standard/`,
  assembles the safety gate (base + the already-selected stack fragment), installs `lint-docs.py`, wires
  the pre-commit via `install-hooks.sh`, and creates the Standard `.agent-docs/` dirs
  (`checkpoints/`, `memories/`, `reference/`). Existing Minimal files are SKIPPED if unchanged, MERGED
  if the friend edited them (`merge-strategy.md`), never clobbered. The manifest records the new
  `kit-version` + profile.
- **Standard → Full.** Same shape: copy `base/full/`, merge the Full rows back into the root
  `.agent-docs/index.md` and the `templates/index.md` catalog, install opted modules.
- **Idempotency.** A re-run at the SAME profile is a repair: it re-verifies every manifest entry's
  `sha256`, restores anything missing, and no-ops anything already correct. This is the same code path
  as upgrade — the manifest is the diff (`merge-strategy.md` §idempotency).

## Related

- `interview.md` — where the profile is chosen · `parameters.md` — the tokens each payload file needs ·
  `scaffold-plan.md` — the ordered file operations + fill/rename/assemble rules ·
  `merge-strategy.md` — never-clobber merge + the manifest ledger · `../stacks/index.md` — stack packs.
