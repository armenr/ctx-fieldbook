---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [stacks, routing, meta]
related: [go, generic]
---

# Stacks — per-language overlay packs (routing)

A **stack pack** carries the parts of the discipline that are NOT stack-agnostic scalars — the
language's real gate commands, its safety foot-guns, its permission allowlist, and its code-intel /
reachability tooling. The stack-agnostic payload lives in `base/`; a stack pack overlays it. At
install the concierge **detects the target repo's primary language**, selects ONE pack, and fills the
`{{PLACEHOLDER}}` scalars (build/test/lint/fmt commands, `{{CODE_INTEL_TOOL}}`, …) from the pack + the
interview.

## Selecting a pack

| Detected primary language | Pack | Detected from (examples) |
|---|---|---|
| Rust | `rust/` | `Cargo.toml`, `Cargo.lock` |
| TypeScript / JavaScript | `node-ts/` | `package.json`, `tsconfig.json`, lockfiles |
| Python | `python/` | `pyproject.toml`, `setup.cfg`, `requirements.txt` |
| Go | `go/` | `go.mod`, `go.sum` |
| anything else / mixed / none | `generic/` | interview-filled (no assumed toolchain) |

`generic/` is the **fallback**: when detection is inconclusive, or the language has no dedicated pack,
the concierge fills the same set of files from the interview instead of from a pre-authored pack
(its files carry the `.template.` infix — e.g. `rules.template.md`). Prefer a dedicated pack when one
matches; `generic/` never overrides a real match.

## What every pack contains

| File | Role | Merges into |
|---|---|---|
| `rules.md` | Language discipline: the real gate commands behind the core `{{...}}` scalars, error-handling / unsafe-construct rules, IMPL→WIRED specifics. | the target's context (`.agent-docs/` + rules) |
| `gate-fragment.sh` | Per-stack PreToolUse safety additions (CSEP-anchored, portable bash), spliced into `pretooluse-safety-gates.base.sh` at its STACK-FRAGMENT INSERTION POINT; may extend `SAFE_PATHS_EXTRA`. | assembled `pretooluse-safety-gates.sh` |
| `allowlist.json` | Read-only + safe common-dev permission additions (`permissions.allow`) so safe frequent commands don't prompt. | target `.claude/settings.json` (union) |
| `code-intel.md` | The IMPL→WIRED prover menu specialized to the language's LSP / call-graph / grep-floor tools; what `{{CODE_INTEL_TOOL}}` resolves to. | the target's context |

The concierge unions `allowlist.json`'s `permissions.allow` into `settings.json` and splices
`gate-fragment.sh` into the safety hook; `rules.md` / `code-intel.md` are placed as the language's
context files with their `{{...}}` scalars filled.

## Adding a new stack pack

1. `mkdir stacks/<lang>/` and author the four files, modelling structure on an existing pack.
   `go/` is a good template — it is authored fresh from primary docs and carries no upstream product
   nouns; `rust/` is the sanitized-from-source reference.
2. **rules.md** — map the core `{{BUILD_CMD}}` / `{{TEST_CMD}}` / `{{LINT_CMD}}` / `{{FMT_CMD}}` scalars
   to the language's real commands; add the language-specific correctness disciplines (its
   `{{PANIC_EQUIVALENT}}` analog, its unsafe constructs). **Currency-check every command against
   current-year PRIMARY docs — never training-data memory — and state the sources + date in the file.**
3. **gate-fragment.sh** — add only COMMAND-POSITION-anchored (CSEP), POSIX-portable rules; reuse the
   base's `ask()` / `block()` helpers and `SAFE_PATHS_EXTRA` seam, do not redefine them. `bash -n` it.
   Gate the language's irreversible / global foot-guns: global installs, shared-cache wipes,
   non-interactive dependency-manifest rewrites, and a package-publish.
4. **allowlist.json** — only read-only + safe common-dev commands; never a mutating / publishing /
   global command (those belong in the gate, not the allowlist).
5. **code-intel.md** — specialize the prover menu (LSP references → call hierarchy → a call-graph tool
   → grep floor → manual-trace note) to the language's tooling; state what `{{CODE_INTEL_TOOL}}` resolves to.
6. Add the language's detection signals to the selection table above.
7. The four files must NOT hard-code project facts or metrics — only the `{{PLACEHOLDER}}` scalars carry
   per-project values (the no-free-floating-literals structural rule from the distillation plan §3).

## Related

- `base/*/agent-docs/CONVENTIONS.md` (the schema contract) ·
  `base/standard/claude/rules/standing-rules-core.md` (the universal disciplines a pack specializes) ·
  `base/standard/claude/hooks/pretooluse-safety-gates.base.sh` (the safety hook the gate fragment splices into)
