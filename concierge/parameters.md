---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [concierge, parameters, placeholders]
related: [interview, scaffold-plan, profiles]
---

# Parameters — the `{{PLACEHOLDER}}` registry

The **complete, closed** set of scalars the concierge fills. There are exactly **twelve**. Everything
else in the kit is either structural (ships identically to every repo) or lives in a stack pack. If a
value isn't one of these twelve, it is NOT a concierge scalar — do not invent new tokens.

**Substitution discipline (load-bearing — get this wrong and you corrupt the kit's own guards):**
- Substitute **only these twelve exact token strings**, matched literally (`{{PROJECT_NAME}}`, …).
  **Never** run a blanket `\{\{.*\}\}` replace. Two non-scalar `{{…}}` forms MUST survive untouched:
  - `{{PLACEHOLDER}}` — a literal example token inside `lint-docs.py`'s comments and the generic
    stack template. It is documentation, not a fill site.
  - a bare `{{` / `}}` — the pre-commit dispatcher greps for `*'{{'*'}}'*` to detect an *unwired* gate
    and skip it gracefully. Blindly substituting would defeat that guard.
- `${CLAUDE_PROJECT_DIR}` and `$1`/`$NOW`/`$CMD`-style shell vars are **runtime** variables, not kit
  tokens — leave them.
- An **empty** value is legitimate for the gate commands (a repo with no build/lint/format step). Leave
  the token's value empty rather than fabricating a command — the pre-commit gate and the allowlist both
  treat an empty/unwired command as a graceful skip. Never guess a command to avoid an empty cell.

---

## The twelve

### 1 · `{{PROJECT_NAME}}`
- **What:** the human name of the target project. Lands in `CONVENTIONS.md`, `charter.md`, the `now/*`
  seeds, `index.md`, and the SubagentStart prefix.
- **Detect:** basename of the target repo root (from interview Q1). Cross-check a `name` field in the
  manifest (`package.json` `.name`, `Cargo.toml` `[package].name`, `pyproject.toml` `[project].name`,
  `go.mod` module last segment) and prefer it if it's cleaner than the dir name.
- **Fallback question:** Q3 confirms the auto-derived name ("Project name I'll use is `<x>` — good?").

### 2 · `{{PROJECT_ONE_LINER}}`
- **What:** one sentence on what the project is. Seeds `charter.md`, `CONVENTIONS.md`, `now/status.md`,
  `now/handoff.md`.
- **Detect:** manifest `description` field, or the first non-title sentence of the repo `README`.
- **Fallback question:** Q3 asks for it directly (the one thing detection genuinely can't infer). Trim a
  paragraph to the thesis and show the trim.

### 3 · `{{PRIMARY_LANGUAGE}}`
- **What:** the project's primary language / the stack pack name. Used in the debrief skill and the
  Full addendum; also selects the `stacks/<lang>/` pack.
- **Detect:** manifest file present → `rust` (`Cargo.toml`) · `node-ts` (`package.json`/`tsconfig.json`)
  · `python` (`pyproject.toml`/`setup.cfg`/`requirements.txt`) · `go` (`go.mod`) · else `generic`.
  On a tie (multiple manifests), pick the root/larger tree and name the tie in Q2.
- **Fallback question:** Q2 confirm table — the language row is editable; correcting it re-selects the
  pack and re-derives the gate defaults.

### 4 · `{{BUILD_CMD}}`
- **What:** the build / compile command. Lands in `now/*` seeds, the lifecycle skills, `standing-rules-core.md`.
- **Detect (order):** the project's own scripts first — `package.json` `.scripts.build`; a `Makefile` /
  `justfile` / `Taskfile.yml` `build` target; a CI workflow's build step — **then** the stack pack's
  default (each `stacks/<lang>/rules.md` maps `{{BUILD_CMD}}` to the language's real command).
- **Fallback question:** Q2 confirm row. If none exists, leave empty (honest; the gate skips).

### 5 · `{{TEST_CMD}}`
- **What:** the test command. Same sinks as build; also referenced by `/orient` + `/flush`.
- **Detect (order):** `.scripts.test`; Make/just/Task `test` target; CI test step; else the pack default.
- **Fallback question:** Q2 confirm row. No tests detected is itself a **down-sell-to-Minimal signal**
  (`profiles.md` §4).

### 6 · `{{LINT_CMD}}`
- **What:** the lint / static-analysis command. Sinks: `now/*`, skills, `standing-rules-core.md`, and the
  **pre-commit code gate** (`.githooks/pre-commit` runs it on staged code).
- **Detect (order):** `.scripts.lint`; a linter config in the repo mapped to its runner
  (per the stack pack); Make/just target; CI lint step; else the pack default.
- **Fallback question:** Q2 confirm row. Empty → the pre-commit lint gate self-skips (graceful).

### 7 · `{{FMT_CMD}}`
- **What:** the formatter command. Sinks: `now/*`, skills, and the **pre-commit format gate**.
- **Detect (order):** `.scripts.format`/`.scripts.fmt`; the pack's formatter default; a formatter config
  in the repo.
- **Fallback question:** Q2 confirm row. Empty → format gate self-skips.

### 8 · `{{CODE_INTEL_TOOL}}`
- **What:** the reachability / code-intel tool that answers "who calls X? is X wired?" — the IMPL→WIRED
  prover. The kit's single most-used token (appears across rules, skills, code-intel guidance). It is the
  *generalized* name for what the source system had as a bespoke tool.
- **Detect:** from the stack pack's `code-intel.md` default — e.g. the language server for the detected
  language (each pack states what it resolves to). There is no per-repo detection beyond the language;
  the pack owns this.
- **Fallback question:** none needed if a pack matched; for `generic`, Q2/Q5 may ask "what do you use to
  answer 'who calls this?' (a language server, a call-graph tool, or grep-as-floor)?" — default to the
  language-server-or-grep floor described in `stacks/generic/code-intel.md`.

### 9 · `{{DEFAULT_BRANCH}}`
- **What:** the protected default branch. Lands in the safety-gate hook's `PROTECTED` pattern and the
  `now/*` seeds.
- **Detect (order):** `git symbolic-ref --quiet refs/remotes/origin/HEAD` (strip `origin/`) →
  `git rev-parse --abbrev-ref HEAD` → `main`.
- **Fallback question:** Q2 confirm row. (The hook already protects `main|master` unconditionally; this
  adds the repo's actual default if it differs.)

### 10 · `{{WORKSPACE_LAYOUT}}`
- **What:** a short description of the repo's package layout, used in the cwd-safety guidance
  (`standing-rules-core.md`, the safety-gate hook comment, the dispatch-charter template) so the
  cwd-before-mutation warning names the real foot-gun.
- **Detect:** single-package vs multi-package. Signals: a workspace declaration in the manifest
  (`[workspace]` members, `workspaces` array, `go.work`, multiple nested manifests) → list the member
  dirs (e.g. `multi-package: api/ web/ shared/`); otherwise `single-package`.
- **Fallback question:** Q2 confirm row (workspace layout). If unsure, `single-package` is the safe
  default (the guidance still reads correctly).

### 11 · `{{PACKAGE_REGISTRY}}`
- **What:** the package registry the project publishes to (used in the safety gate's publish-warning and
  the stack `rules.md`). Names what a publish is irreversible *to*.
- **Detect:** from the stack pack default (the language's canonical public registry) unless the manifest
  names a private/custom registry (`publishConfig.registry`, a `[registries]`/index entry, a module
  proxy). Prefer the manifest's explicit registry when present.
- **Fallback question:** none usually — the pack default is fine. The gate reads
  `${PACKAGE_REGISTRY:-the package registry}`, so an unset value degrades to a generic phrase, never a
  broken message.

### 12 · `{{PANIC_EQUIVALENT}}`
- **What:** the language's "crash / abort instead of returning a typed error" construct — the thing the
  "don't reach for X in library code" discipline names (`standing-rules-core.md`, the stack `rules.md`,
  the dispatch-charter template).
- **Detect:** from the stack pack (each language's `rules.md` supplies its analog — the unchecked-abort
  / uncaught-throw construct appropriate to that language).
- **Fallback question:** none if a pack matched; for `generic`, Q5 may ask "what's the 'crash instead of
  handling it' construct you want flagged in library code?" — else leave the pack/generic default.

---

## Detection cheatsheet (read-only, per language)

| Token | rust | node-ts | python | go | generic |
|---|---|---|---|---|---|
| `{{PRIMARY_LANGUAGE}}` | rust | node-ts | python | go | generic |
| gate cmds (build/test/lint/fmt) | pack `rules.md` defaults | `package.json` scripts → pack | `pyproject`/Make → pack | pack defaults | interview |
| `{{CODE_INTEL_TOOL}}` | pack `code-intel.md` | pack | pack | pack (`gopls`) | interview / grep floor |
| `{{PACKAGE_REGISTRY}}` | pack default / manifest | manifest `publishConfig` / pack | manifest / pack | module proxy / pack | interview |
| `{{PANIC_EQUIVALENT}}` | pack | pack | pack | pack | interview |

The gate commands always let the **project's own scripts win** over the pack default — a `package.json`
`test` script is the truth; the pack default is the fallback when the repo declares nothing.

## Related

- `interview.md` (Q2/Q3/Q5 collect these) · `profiles.md` (which payload files consume which token) ·
  `scaffold-plan.md` (the fill pass) · `../stacks/index.md` (where the per-language defaults live).
