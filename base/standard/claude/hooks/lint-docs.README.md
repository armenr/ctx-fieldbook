---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [hooks, lint, enforcement, schema]
related: [lint-docs]
---

# `lint-docs.py` — the doc-schema linter

This is the **enforcement** that the `.agent-docs/CONVENTIONS.md` *"Lint rules"* section refers to.
CONVENTIONS ships those rules as a spec and is honest that only *index completeness* was ever
hook-enforced; the rest were advisory. `lint-docs.py` makes **all fifteen** real: each is a discrete
check with a `PASS` / `FAIL` (or `WARN`) verdict and a `file:line` message.

Language-agnostic and dependency-free by design: **stock Python 3, standard library only** (no
`pip install`, no `import yaml` — front-matter is hand-parsed). It runs the same on Linux, macOS/BSD,
and WSL. It never reads a wall clock — the staleness check takes its "now" from `--now`, so a run is
deterministic and reproducible in CI.

## Usage

```
lint-docs.py [--root DIR] [--now YYYY-MM-DD] [--warn-days N] [--fail-days N]
```

| Flag | Default | Meaning |
|---|---|---|
| `--root DIR` | `.agent-docs` | Root of the `.agent-docs/` tree to lint. |
| `--now YYYY-MM-DD` | *(unset)* | Reference date for the `now/` staleness rule. **Omit to skip staleness** — the linter never invents a clock. |
| `--warn-days N` | `7` | `now/` age (days) above which a doc warns. |
| `--fail-days N` | `90` | `now/` age (days) above which a doc is "hard-stale" (still a WARN — see rule 12). |

**Exit status:** `0` when clean (or warnings only) · `1` when any `FAIL` was reported · `2` on a usage
error (bad `--root`, bad `--now`). **Warnings never change the exit code.** Output is grouped by rule.

## The fifteen checks (rule → CONVENTIONS mapping)

Every rule maps 1:1 to a numbered entry in the CONVENTIONS *"Lint rules"* section.

| # | Check | Class | CONVENTIONS ref |
|---|---|---|---|
| 1 | Front-matter present + parseable | FAIL | Lint rule 1 · §2 |
| 2 | Required fields populated (`provenance`, `created`, `last-modified`) | FAIL | Lint rule 2 · §2 |
| 3 | `provenance` in the allowed set | FAIL | Lint rule 3 · §2 |
| 4 | ADRs have a valid `status` | FAIL | Lint rule 4 · §2/§5 |
| 5 | `status: superseded` ⇒ non-null `superseded-by` | FAIL | Lint rule 5 · §2/§5 |
| 6 | `status: pending` ⇒ `pending-on`; `deferred` ⇒ `deferred-because` | FAIL | Lint rule 6 · §2 |
| 7 | ADRs contain a non-empty `## Alternatives Considered` | FAIL | Lint rule 7 · §5 |
| 8 | `related` / `supersedes` / `superseded-by` / `archived-from` references resolve | FAIL | Lint rule 8 · §2 |
| 9 | File path matches category (ADR in `decisions/`, checkpoint in `checkpoints/`) | FAIL | Lint rule 9 · §1/§3 |
| 10 | Accepted ADRs are not `llm-draft` / `llm-autonomous` | FAIL | Lint rule 10 · §2 |
| 11 | Date-prefixed filenames match the date format | FAIL | Lint rule 11 · §3 |
| 12 | `now/` files `last-modified` within the freshness window | **WARN** | Lint rule 12 · §1/§2 |
| 13 | **Index completeness** — every populated content dir has a matching `index.md` | FAIL | Lint rule 13 · §7.1 |
| 14 | Checkpoint integrity — all ten numbered points present | FAIL | Lint rule 14 · §6 |
| 15 | `work-unit:` resolves to a WU in `now/work-plan.md` | FAIL | Lint rule 15 · §4 |

### Notes on specific rules

- **Rule 12 ships WARN-only (warn-not-fail by default).** CONVENTIONS describes a 90-day *fail*
  threshold; the linter emits it as a louder warning (`> fail window`) rather than a hard failure, so a
  stale-but-correct doc never blocks a commit or CI gate. `--fail-days` sets where the wording flips
  from "soft" to "hard" stale; it does not change the exit code. A maintainer who wants a hard gate
  flips the single `STALENESS_FAILS` constant at the top of the script. If `--now` is not passed, the
  rule is skipped entirely (no clock is invented).
- **Rule 13 (index completeness) is FAIL here** — it is the one rule the source system already
  enforced by hook, folded in verbatim: for each managed dir it compares the on-disk ``\`file.md\``
  basenames against the `` `file.md` `` backtick tokens in that dir's `index.md`, reporting *missing
  index*, *unindexed* (on disk, not referenced), and *phantom* (referenced, no such file). Cross-dir
  tokens (containing `/`) are ignored — presence-only, by design. Managed dirs are the one-level (and
  one-nested) content dirs under `--root`, **excluding `now/` and `templates/`**.
- **Rule 8 resolution.** A bare id resolves to `<dir>/<id>.md` or `<root>/<id>.md`; a path-like token
  (`../x/y.md`) resolves relative to the doc then to root; `ADR-NNNN` resolves to `decisions/NNNN-*.md`;
  other typed ledger ids (`OQ-`, `WU-`, `LP-`, …) are treated as resolvable non-file references.

## What gets linted — the template stance (documented choice)

The linter walks **every `*.md` under `--root`**. It draws one distinction:

- **Instantiated docs** get the full rule set.
- **Kit-shipped scaffolding gets a relaxed pass.** A doc is treated as scaffolding when its name ends
  `.template.md`, **or** it lives under a `templates/` dir, **or** it still carries
  `provenance: kit-template`. For scaffolding the *structural* rules still apply (front-matter present
  + parseable, required fields, allowed provenance, filename/category shape), but the rules that assume
  a fully instantiated tree are **skipped**: cross-reference resolution (rule 8), `now/` staleness
  (rule 12), and WU resolution (rule 15). Rationale: a seed legitimately holds `{{PLACEHOLDER}}` tokens
  and points at sibling names that only exist once installed — linting those as if instantiated would
  flag the kit against itself. The ADR/checkpoint body rules key off directory + filename shape
  (`decisions/NNNN-*.md`, `checkpoints/DATE-*.md`), so a template in `templates/` is never mistaken
  for the real artifact.

The linter reads its own two `.template.md` neighbours cleanly, including the leading `<!-- guidance -->`
comment block those templates open with and the trailing `# inline comments` on their front-matter
values.

## How it is wired

### Pre-commit (the enforcement point)

Add to the project's pre-commit hook so a schema-violating doc cannot be committed. The path is
relative to the installed `claude/hooks/` location.

```sh
# --- doc-schema lint (only when .agent-docs docs are staged) ---
if command -v python3 >/dev/null 2>&1; then
  if git diff --cached --name-only | grep -q '^\.agent-docs/.*\.md$'; then
    python3 .claude/hooks/lint-docs.py --root .agent-docs || {
      echo "doc-schema lint failed — fix the FAILs above, or see CONVENTIONS.md 'Lint rules'." >&2
      exit 1
    }
  fi
fi
```

`command -v python3` guards a machine without Python 3 — the check degrades to a no-op rather than
hard-failing the commit (the kit's portability contract).

### Optional: SessionStart (advisory freshness nudge)

Wire into a `SessionStart` hook to surface `now/` staleness as a non-blocking nudge at the top of a
session — pass today's date so the deterministic check has a reference point:

```sh
command -v python3 >/dev/null 2>&1 && \
  python3 .claude/hooks/lint-docs.py --root .agent-docs --now "$(date +%Y-%m-%d)" || true
```

Because staleness is WARN-only and the trailing `|| true` swallows a non-zero exit, this never blocks
a session — it just prints what has drifted.

## Self-test

Run it against the kit's own skeleton, and against a throwaway good/bad fixture:

```sh
# The Minimal skeleton — passes clean once its templates are schema-consistent.
python3 lint-docs.py --root ../../agent-docs

# A broken ADR (bad provenance, no Alternatives, dangling related:) fails with three grouped FAILs.
python3 lint-docs.py --root /path/to/fixture/bad   # exit 1
python3 lint-docs.py --root /path/to/fixture/good  # exit 0
```
