---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [concierge, scaffold, deterministic, install]
related: [interview, profiles, parameters, merge-strategy]
---

# Scaffold plan — the deterministic install

Given `{answers, profile, stack, target, existing-file-map}` from the interview, this is the **exact,
ordered** set of file operations. It is deterministic: the same inputs produce the same operations. The
concierge shows this as the Q6 dry-run plan, then — on an explicit yes — executes it top to bottom,
recording each action to the manifest **as it happens** (`merge-strategy.md`). All *source* paths are
relative to this kit folder; all *dest* paths are under `<target>` (the repo from Q1).

**Inputs.**
- `profile` ∈ `{minimal, standard, full}`
- `stack` ∈ `{rust, node-ts, python, go, generic}`
- `tokens` = the twelve filled scalars (`parameters.md`)
- `q5` = project-specific gate rules + opted modules
- `existing` = which of `CLAUDE.md` / `.claude/settings.json` / `.claude/**` / `.agent-docs/` / `.githooks/` already exist

**Three transform primitives (used throughout):**
1. **COPY-VERBATIM** — byte-for-byte (a file with no tokens: `lint-docs.py`, `install-hooks.sh`,
   `hooks/README.md`, most `index.md` and `templates/*`). A no-op fill leaves it identical.
2. **FILL** — substitute the twelve exact token strings (`parameters.md` §substitution-discipline:
   literal match only, never a blanket `{{…}}` regex; preserve `{{PLACEHOLDER}}` and bare `{{`/`}}`).
3. **RENAME** — a source ending `.template.md` / `.template.json` / `.template.<ext>` (or the generic
   `X.template.Y` infix) drops the `.template` on install: `charter.template.md → charter.md`,
   `now/status.template.md → now/status.md`, `settings.json.template → settings.json`,
   `stacks/generic/rules.template.md → rules.md`, `allowlist.template.json → allowlist.json`.

**Write posture.** For every dest, first consult `existing`: **absent → CREATE**; **present + identical
after transform → SKIP** (idempotent re-run); **present + different → MERGE** (never clobber — route to
`merge-strategy.md`, back up + marked block / deep-merge + diff + explicit yes). CLAUDE.md and
settings.json are the always-merge-if-present cases.

---

## Phase 0 — Preconditions + manifest init

0.1 Re-verify `<target>` is a git work tree (`git -C <target> rev-parse --show-toplevel`). Not a repo →
    warn: hooks + branch gates assume git; offer to proceed docs-only or stop.
0.2 Compute the full operation list (Phases 1–7 below) WITHOUT writing — this is the Q6 dry-run.
0.3 On the Q6 yes: create/open `<target>/.agent-docs/.kit-manifest.json` and write the header
    (`kit-version` from `<kit>/kit-version.txt`, `profile`, `stack`, `created` timestamp, `tokens`
    resolved). If a manifest already exists, this is a repair/upgrade run — reconcile against it
    (`merge-strategy.md` §idempotency) instead of starting fresh.
    *(The manifest lives inside `.agent-docs/`, so Phase 1 must create that dir first; in practice
    write a bare `.agent-docs/` + the manifest header at 0.3, then populate in Phase 1.)*

Every subsequent operation appends a manifest entry the moment it completes:
`{ "path": "<dest rel to target>", "action": "create|merge|skip", "sha256": "<of installed file>",
"backup": "<backup path or null>", "source": "<kit source rel path>" }`.

---

## Phase 1 — `.agent-docs/` (the context store)

Copy the profile's `.agent-docs/` payload (additively — `profiles.md` §1–3 is the source→dest map).

1.1 **Minimal payload** (`base/minimal/agent-docs/`): FILL+RENAME the `now/*.template.md`,
    `now/lessons/*.template.md`, `charter.template.md`; FILL `CONVENTIONS.md`, `index.md`, `glossary.md`,
    `log.md`; COPY-VERBATIM `decisions/index.md`, `lessons/index.md`, `now/index.md`, `templates/*`.
    - **Root `index.md` row-prune:** the root catalog ships all rows (minimal/standard/full). Delete the
      rows for dirs this profile does NOT install (`index.md` says to, to "keep the catalog honest"):
      Minimal keeps `now/ decisions/ lessons/`; Standard also keeps `reference/ checkpoints/ memories/`;
      Full keeps everything. Prune before writing.
1.2 **Standard payload** (`base/standard/agent-docs/`, if profile ≥ standard): COPY-VERBATIM
    `checkpoints/index.md`, `memories/index.md`, and `reference/index.md` (all ship as seed stubs —
    the root catalog routes to `reference/` at Standard, so its index must be present for rule 13).
1.3 **Full payload** (`base/full/agent-docs/`, if profile == full): FILL `CONVENTIONS-full-addendum.md`;
    COPY-VERBATIM the six Full dir `index.md` files (`traceability/ dispatch-charters/ research/
    runbooks/ incidents/ experiments/`); FILL the Full `templates/*` (`dispatch-charter-template.md` etc.)
    into `templates/`; **merge** the Full `templates/index.md` catalog INTO the already-installed Minimal
    `templates/index.md` (append the Full section — do not overwrite the Minimal catalog).

**Determinism note:** within a phase, process dirs in sorted order and files in sorted order, so the
dry-run plan and the manifest are stable across runs.

---

## Phase 2 — `.claude/` rules, skills, hooks (non-assembled)

2.1 **Rules** — Minimal: COPY `rules/agent-docs.md`, `rules/sensitive-data.md`. Standard+: FILL
    `rules/standing-rules-core.md` (`{{WORKSPACE_LAYOUT}}`, `{{PANIC_EQUIVALENT}}`, gate cmds,
    `{{CODE_INTEL_TOOL}}`), COPY `rules/standing-rules-rationale.md`.
2.1b **Scripts** — Standard+: COPY-VERBATIM `base/standard/scripts/wu-refs.sh` → `scripts/wu-refs.sh`
    (`chmod +x`) — the cycle-start inbound-reference sweep the standing-rule invokes (`git grep`-only, no
    tokens to FILL). Minimal: skip (the sweep pairs with the Standard+ orchestration discipline).
2.2 **Skills** — bare-name dirs under `.claude/skills/` (never namespaced, so `/orient` muscle memory
    transfers; distillation decision on skills). Minimal: FILL `skills/{orient,flush,handoff}/SKILL.md`.
    Standard+: FILL `skills/{sitrep,debrief,distill-lessons}/SKILL.md`. Full + opted:
    `skills/research-pipeline/SKILL.md` (from `modules/research-pipeline/`).
2.3 **Hooks (non-assembled)** — Minimal: COPY `hooks/sessionstart-state-router.sh`,
    `hooks/precompact-handoff-trigger.sh`. Standard+: COPY `hooks/lint-docs.py`,
    `hooks/lint-docs.README.md`, `hooks/lint-agent-docs-indexes.sh` (the fast index-lint the router +
    pre-commit probe), `hooks/install-hooks.sh`, `hooks/README.md`; FILL
    `hooks/subagentstart-prefix.sh` (`{{PROJECT_NAME}}`). Full + opted revisit-ledger: COPY
    `hooks/revisit-lint.sh` (from `modules/revisit-ledger/`).
2.4 `chmod +x` every installed `.sh` (portable chmod; ignore failures — `install-hooks.sh` re-chmods).
2.5 **Statusline (opted, any profile — from `modules/statusline/`).** By chosen scope:
    - **project:** COPY `modules/statusline/statusline.py` → `<target>/.claude/statusline.py`; record for
      the Phase-4 `statusLine` block (absolute-path form).
    - **global:** this is a **`~/.claude` write** — confirm the distinct yes from Q5 first, then COPY to
      `~/.claude/statusline.py` and deep-merge a `statusLine` block into `~/.claude/settings.json`
      (`python3 ~/.claude/statusline.py`), backing up that file per `merge-strategy.md`. Record both in
      the manifest so uninstall can reverse the global write too.
    - Exact settings blocks + mechanics: `modules/statusline/README.md`.

---

## Phase 3 — Assemble the PreToolUse safety gate (Standard+ only)

Minimal installs **no** safety-gate hook (skip this phase). Standard+ produces
`<target>/.claude/hooks/pretooluse-safety-gates.sh` by assembly:

3.1 Read the base `base/standard/claude/hooks/pretooluse-safety-gates.base.sh`.
3.2 Read the selected `stacks/<stack>/gate-fragment.sh` (for `generic`, the fragment is a commented
    scaffold — uncomment/synthesize the Q5 project rules into it, following its in-file discipline:
    CSEP-anchored, POSIX classes, `ask`/`block` helpers, `SAFE_PATHS_EXTRA` seam).
3.3 **Splice** the fragment into the base at the marked block:
    ```
    # ─── STACK-FRAGMENT INSERTION POINT ───...
    ```
    Insert the fragment's body BETWEEN that comment block and the first universal rule (rule 1 / the
    `PROTECTED=` line), so the fragment can extend `SAFE_PATHS_EXTRA` and add rules before the universal
    set — exactly as the base's comment and each fragment's header specify. Do NOT duplicate the base's
    `set -euo pipefail`, `jq` guard, `CMD=`, `ask()`, `block()`, or `CSEP=` — the fragment inherits them.
3.4 Append any Q5 project-specific `ask`/`block` rules (if not already folded into the generic fragment).
3.5 FILL `{{DEFAULT_BRANCH}}` (the base's `PROTECTED=` pattern), `{{PACKAGE_REGISTRY}}`,
    `{{WORKSPACE_LAYOUT}}` in the assembled file.
3.6 `bash -n <target>/.claude/hooks/pretooluse-safety-gates.sh` — the assembled hook MUST parse. If it
    fails, do NOT install it (a broken PreToolUse hook could gate every Bash call); report the splice
    error and fall back to the base standalone (which is correct on its own) + record the fragment as
    a deferred manual step.
3.7 `chmod +x`.

---

## Phase 4 — `.claude/settings.json` (build + prune + union)

Build from `base/minimal/claude/settings.json.template` (it ships under minimal but references
Standard-only hooks, so it MUST be pruned per profile):

4.1 FILL the template's `{{BUILD_CMD}}`/`{{TEST_CMD}}`/`{{LINT_CMD}}`/`{{FMT_CMD}}` permission entries.
    Drop any allow-entry whose command is empty (no such gate) so no `Bash(:*)` garbage lands.
4.2 **Prune the `hooks` block to installed hooks only.** Remove any hook entry whose target script was
    not installed by this profile:
    - Minimal: keep `SessionStart` + `PreCompact`; **remove** `SubagentStart` and `PreToolUse`
      (those scripts are Standard payload — leaving them would point at absent scripts).
    - Standard+: keep all four.
4.3 **Union the stack allowlist.** Read `stacks/<stack>/allowlist.json` (`generic` →
    `allowlist.template.json`, FILL its gate-cmd entries first) and merge its `permissions.allow` array
    into the settings `permissions.allow` (dedup; preserve the base read-only set). Never add a mutating/
    publishing/global command to allow — those stay gated (they are deliberately absent from every pack
    allowlist).
4.4 The settings entries referencing `lint-agent-docs-indexes.sh` are valid at Standard+ (the script is
    installed in Phase 2.3). At Minimal (no index-lint script), drop those entries so nothing points at an
    absent script.
4.4b **Statusline `statusLine` block (only if opted PROJECT scope in Q5/Phase 2.5).** Add to the target
    `settings.json` top level, using the repo's ABSOLUTE path (cwd is undefined for statuslines; `~` and
    `$CLAUDE_PROJECT_DIR` are not reliable there):
    `"statusLine": { "type": "command", "command": "python3 <target-abs>/.claude/statusline.py", "padding": 0 }`.
    Global scope does NOT touch the target settings.json — it edits `~/.claude/settings.json` in Phase 2.5.
4.5 **Validate JSON** (parse the result) before writing. If `<target>/.claude/settings.json` already
    exists → this is a **deep-merge**, not a write: `merge-strategy.md` §settings-json (append hooks
    arrays, union `permissions.allow`, back up, re-validate, diff + yes).

---

## Phase 5 — The project-root constitution (`<target>/CLAUDE.md`)

The constitution is **written into the target's project-root `CLAUDE.md`** (a plugin cannot carry it;
a subdirectory CLAUDE.md loads lazily — only the project-root file is reliably always-on).

5.1 Source: the kit's target-constitution template **`base/minimal/CLAUDE.md.template`** (used by all
    profiles — a pointer constitution routes to `.agent-docs/`, which is what varies by profile, so the
    template does not). Instantiate it, filling the scalars from `parameters.md`: `{{PROJECT_NAME}}`,
    `{{PROJECT_ONE_LINER}}`, the gate recipe (`{{BUILD_CMD}}`/`{{TEST_CMD}}`/`{{LINT_CMD}}`/`{{FMT_CMD}}`),
    `{{CODE_INTEL_TOOL}}`, `{{DEFAULT_BRANCH}}`. Strip the leading HTML comment block on instantiation.
    Do NOT ship the kit's OWN root `CLAUDE.md` (the concierge bootstrap) to the target — it is the
    installer, not the constitution.
5.2 If `<target>/CLAUDE.md` **exists** → NEVER clobber. `merge-strategy.md` §claude-md: back up + wrap
    the kit content in `<!-- kit:start -->` / `<!-- kit:end -->` markers + append/insert + diff +
    explicit yes.
5.3 If absent → CREATE it (consented at Q6). FILL tokens.

---

## Phase 6 — Git pre-commit gate + hook wiring (Standard+)

6.1 FILL `base/standard/githooks/pre-commit` (`{{LINT_CMD}}`, `{{FMT_CMD}}`) → `<target>/.githooks/pre-commit`;
    `chmod +x`. If `<target>/.githooks/pre-commit` exists → MERGE (`merge-strategy.md`).
6.2 **Wire the hooks so they actually fire** (the fresh-clone-inertness fix — a tracked `.githooks/` is
    inert until `core.hooksPath` points at it). Run `bash <target>/.claude/hooks/install-hooks.sh`
    (default `core.hooksPath` mode): it sets `core.hooksPath=.githooks`, disables a stale
    `.git/hooks/pre-commit`, and self-verifies. This is a **consented, per-clone LOCAL git-config change**
    — surface it in the Q6 plan (it mutates git config, not a file). If the target already uses
    `core.hooksPath` for something else, use `--copy` mode (documented in `install-hooks.sh`).
6.3 Claude Code hooks (settings.json) need no separate wiring — they activate when settings.json is
    present. Confirm the four (or two, at Minimal) reference installed scripts (Phase 4.2 guaranteed it).

---

## Phase 7 — Finalize manifest + hand to verify

7.1 Write the manifest footer: `completed` timestamp, final `profile`/`stack`/`kit-version`, the module
    opt-ins, and a `status: complete`. The manifest is now the idempotency + rollback ledger
    (`merge-strategy.md`).
7.2 Hand to **`verify-install.md`** (sibling deliverable) for the smoke test + guided tour. Minimum if
    that file is absent from this build: `/orient` cold on the seeded `now/`; run
    `python3 <target>/.claude/hooks/lint-docs.py --root <target>/.agent-docs --now <today>` (Standard+)
    and confirm clean on the fresh skeleton; parse settings.json; dry-fire the safety gate on a sample
    destructive command; run the detected `{{BUILD_CMD}}`/`{{TEST_CMD}}` once to reality-check the baked
    gates; confirm `core.hooksPath`.

---

## Ordered operation summary (the deterministic spine)

```
0  preconditions + manifest header
1  .agent-docs/  (minimal → [standard] → [full], additive; root index.md row-prune; reference/ stub)
2  .claude/ rules + skills(bare-name) + non-assembled hooks (+ chmod)
3  assemble pretooluse-safety-gates.sh  (base + stack fragment + Q5 rules; bash -n)   [Standard+]
4  .claude/settings.json  (fill → prune hooks to profile → union stack allowlist → validate JSON)
5  <target>/CLAUDE.md constitution  (create, or never-clobber merge)
6  .githooks/pre-commit (fill) + install-hooks.sh wiring (core.hooksPath)             [Standard+]
7  manifest footer → verify-install.md
```

Every step: consult `existing` → CREATE / SKIP / MERGE; append the manifest entry on completion; on any
MERGE, stop and get the per-file explicit yes before touching the existing file.

---

## Enforcement gaps — RESOLVED in the P7 reconcile pass (2026-07-03)

The three gaps this plan originally flagged were closed after the P5/P6 build:

- **`lint-agent-docs-indexes.sh` now ships** at `base/standard/claude/hooks/lint-agent-docs-indexes.sh`
  — the fast, index-only check (warn by default, `--strict` for the pre-commit gate) that the router,
  settings allowlist, and pre-commit dispatcher probe. It no-ops cleanly if `.agent-docs/` doesn't exist
  yet. (The comprehensive `lint-docs.py` still folds the same check in as rule 13 for the full pass.)
  NOTE: it is a **Standard** payload — a Minimal-only install has no index probe target, which is fine
  (Minimal is WARN-only by design; the guarded `[[ -x ]]` probes degrade to no-op).
- **`reference/index.md` now ships** at `base/standard/agent-docs/reference/index.md` (a seed stub), so
  the root catalog's Standard route to `reference/` resolves and rule 13 stays clean without a Phase-1.2
  synthesized stub.
- **The target-`CLAUDE.md` constitution template now ships** at `base/minimal/CLAUDE.md.template`
  (Phase 5.1) — the concierge instantiates it rather than composing the constitution ad-hoc.

## Related

- `interview.md` (produces the inputs) · `profiles.md` (source→dest payload map) · `parameters.md`
  (the fill values) · `merge-strategy.md` (CREATE/SKIP/MERGE + the manifest ledger + rollback).
