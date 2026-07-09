---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
paths: ["**/*.py", "**/*.pyi", "**/pyproject.toml", "**/ruff.toml", "**/.ruff.toml", "**/mypy.ini", "**/setup.cfg", "**/tox.ini"]
---

# Python rules

The stack-specific concretion of the universal quality-gate discipline in `standing-rules-core.md`
(§Quality gates). Short on purpose — deep architecture lives in your project's own `reference/`. This
pack is the Python binding for the generic `{{BUILD_CMD}} / {{TEST_CMD}} / {{LINT_CMD}} / {{FMT_CMD}} /
{{PANIC_EQUIVALENT}} / {{CODE_INTEL_TOOL}}` seams: `{{LINT_CMD}}` → `ruff check`, `{{FMT_CMD}}` →
`ruff format --check`, `{{TEST_CMD}}` → `pytest`, the type-check gate → `mypy` (or `pyright`),
`{{PANIC_EQUIVALENT}}` → the swallowed-exception / bare-`except` trap below, `{{CODE_INTEL_TOOL}}` → the
Python language server (see `code-intel.md`). Commands verified against current-year primary docs (Ruff,
mypy, pyright, pytest, uv) — currency-check again before pinning versions.

## Lint & format & type gates (strict by decision, not preference)

- **Versions-check first — the gate FAILS on toolchain drift.** Before any other stage runs, verify
  the active toolchain matches the pins: `python --version` against `requires-python` /
  `.python-version`, and `ruff --version` / `mypy --version` (or `pyright --version`) against the
  lockfile's resolved versions. A mismatch is a gate FAILURE, not a note — a lint or type-check run
  that goes green under a toolchain the pins don't describe is vacuously green, not passing.
- **`ruff check` must pass with zero findings.** Ruff is the linter (it subsumes flake8, isort,
  pyupgrade, and much of pylint). Configure it in `pyproject.toml` under `[tool.ruff.lint]`; select a
  broad rule set (at least `E,F,W,I,B,UP,SIM,RUF` — pycodestyle, pyflakes, isort, bugbear, pyupgrade,
  simplify, Ruff-native) and treat every finding as an error. `ruff check --fix` applies the
  auto-fixable ones. Don't blanket-`# noqa` a line; use `# noqa: <CODE>  # why this is correct here`, or
  fix the finding.
- **`ruff format --check` must pass.** `ruff format` is the formatter (Black-compatible); `--check` is
  the non-writing CI mode that exits non-zero on unformatted files. `ruff format` (no flag) fixes them.
- **A type checker must pass on a typed codebase.** `mypy` (or `pyright`, or Astral's emerging `ty`) runs
  in strict mode — in `pyproject.toml` set `[tool.mypy] strict = true` (or pyright's
  `"typeCheckingMode": "strict"`). New code is fully annotated; **`Any` is a hole in the type system** —
  prefer a precise type or a `Protocol`; an `Any` or a `# type: ignore` needs an explicit, justified,
  in-comment reason (`# type: ignore[code]  # why`) or it must be fixed.
- The pre-commit hook runs lint + format; **never `--no-verify`** to get past a failing gate —
  investigate it.

## The swallowed-exception trap ({{PANIC_EQUIVALENT}} for Python)

Python's analog of an uncaught fatal is an **unhandled exception escaping the library boundary** — and
the way it turns silent-and-dangerous is a **bare or over-broad `except` that swallows it**.

- **No bare `except:` and no blanket `except Exception:` that swallows.** Catch the *specific* exception
  you can handle (`except KeyError:`), do something real with it, and re-raise or wrap the rest. A bare
  `except:` also catches `KeyboardInterrupt`/`SystemExit` and hides real bugs (Ruff `E722`/`BLE001` flag
  this). When you re-wrap, preserve the chain: `raise MyError(...) from exc`.
- **Never `except ...: pass`** to silence a failure. That converts a caller's recoverable, diagnosable
  error into a silent wrong-answer. If a failure is genuinely ignorable, log it and say why in a comment.
- **Library code raises typed, caller-recoverable exceptions — it does not `sys.exit()` or `os._exit()`.**
  A library that exits the process turns a caller's recoverable failure into an abort it can't catch.
  Raise a domain-specific `Exception` subclass; let the entrypoint decide the exit code.
- **No `assert` for runtime validation in shipped code** — `assert` is stripped under `python -O`. Use it
  for internal invariants only; validate real inputs with an explicit `raise`.

## Typing & structure

- **New code is type-annotated at the boundary** — public functions, dataclass fields, return types.
  Prefer `dataclasses` / `Protocol` / `TypedDict` over untyped dicts for structured data. Modern syntax
  (`list[str]`, `X | None`) over the deprecated `typing.List` / `Optional[X]` (Ruff `UP` enforces this).
- **Mutable default arguments are a bug** (`def f(x=[])` — Ruff `B006`). Use `None` + a body default.
- **Don't reach for a global interpreter state hack** to make something importable; model the dependency.

## Dependency & environment discipline

- **One project environment, locked and committed.** Prefer a project manager that produces a committed
  lockfile — `uv` (`uv.lock`, via `uv sync`), Poetry (`poetry.lock`), or PDM. Dependencies and their
  constraints live in `pyproject.toml` under `[project.dependencies]` / `[dependency-groups]`, never as
  an un-pinned ad-hoc `pip install`. A reproducible install is `uv sync --frozen` (or
  `poetry install`).
- **Install into the project virtualenv, never the system interpreter.** The safety gate asks on a
  global / system-wide / user-site install (`sudo pip`, `pip --user` / `--break-system-packages`,
  `uv pip --system`, `uv tool` / `pipx`) precisely because those escape the project env and mutate a
  shared Python. Prefer `uv add` / `uv run` (or `poetry add` / `poetry run`) so the command runs in the
  locked project env.
- **Currency-check before adding or bumping ANY dependency** (`standing-rules-core.md` §external deps):
  verify the latest stable version + deprecation status of the *exact* API you use against current-year
  primary docs (the index `{{PACKAGE_REGISTRY}}` + the package's own docs), not from memory.

## Acceptance for any change here

- **A behavior change OWES a test that fails without it.** A green `pytest` run (`{{TEST_CMD}}`) is
  necessary, not sufficient — every behavior carries its falsifier.
- **IMPL → WIRED is the bar, not test-pass.** After it lints, type-checks, and tests pass, prove the new
  code is reachable from a production entrypoint (a `[project.scripts]` console-script `main`, a
  `python -m <pkg>` `__main__`, a registered route/handler, an imported public API a real caller uses)
  and record IMPL/WIRED/DEFER in `traceability/`. Prove reachability with `{{CODE_INTEL_TOOL}}` — for
  Python that is the language server's references / call-hierarchy, with an optional dead-code /
  call-graph tool and a grep-the-callers floor (see `code-intel.md`). An unimported module or unused
  public function is a wiring failure, not noise.

## Related

- `code-intel.md` (the Python reachability prover menu) · `standing-rules-core.md` (§Quality gates,
  §IMPL→WIRED) · `../../base/*/agent-docs/CONVENTIONS.md` (the schema contract)
