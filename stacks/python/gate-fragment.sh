# ─── Python stack gate fragment ───────────────────────────────────────────────────────
# Spliced into pretooluse-safety-gates.base.sh at the marked STACK-FRAGMENT INSERTION POINT
# (BEFORE the universal rules). NOT a standalone script — it inherits CMD, CSEP, ask(),
# block(), and SAFE_PATHS_EXTRA from the base. Same discipline as the base: anchor a tool
# token to command position via ${CSEP}, use POSIX character classes only ([[:space:]],
# [^[:alnum:]_]) so it behaves identically under GNU and BSD grep, and chain greps with &&
# when two tokens must co-occur in any order on the same line. A tool invoked via `python -m`
# or `sudo` is matched with a plain word boundary (it is not at command position).
#
# Gated surface: the operations that reach OUTSIDE the project virtualenv or are hard to undo
# — publish (index, public), a global / system-wide / user-site install (shared interpreter),
# a virtualenv wipe. Plain in-venv install / run / test / lint stay ungated.

# Extend the recursive-rm safe-path set with regenerable tool caches / coverage output, so
# `rm -rf __pycache__ .pytest_cache` etc. do not prompt. A virtualenv (.venv / .tox / .nox) is
# deliberately NOT here — its wipe stays gated (P3). Preserves any value an earlier fragment set.
SAFE_PATHS_EXTRA="${SAFE_PATHS_EXTRA:+${SAFE_PATHS_EXTRA}|}__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.hypothesis|htmlcov|\.egg-info"

# P1a. twine upload (ask) — the canonical PyPI publish; a released version is public and cannot
#      be re-uploaded. `twine` may be invoked directly or via `python -m twine`, so match a plain
#      word boundary co-occurring with the `upload` subcommand.
echo "$CMD" | grep -qE "(^|[^[:alnum:]_])twine([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])upload([[:space:]]|$)" &&
  ask "Safety gate (python): 'twine upload' publishes to ${PACKAGE_REGISTRY:-the package index} — public and unremovable once live (a version can never be re-uploaded). Confirm the distribution, version, and index with the operator."

# P1b. Tool-native publish subcommand (ask) — uv / poetry / pdm / flit / hatch `publish`.
echo "$CMD" | grep -qE "${CSEP}(uv|poetry|pdm|flit|hatch)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])publish([[:space:]]|$)" &&
  ask "Safety gate (python): publishing to ${PACKAGE_REGISTRY:-the package index} is public and hard to retract. Confirm the package, version, and index before publishing."

# P2. Global / system-wide / user-site install (ask) — a Python installer co-occurring with an
#     escape-the-venv signal: sudo, pip --user / --break-system-packages / --target, uv pip
#     --system, or a global tool install (uv tool / pipx). A plain in-venv `pip install` is NOT
#     gated (no signal token present).
echo "$CMD" | grep -qE "(^|[^[:alnum:]_])(pip|pip3|uv|pipx)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(install|tool)([[:space:]]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])(--user|--break-system-packages|--system|--target|-t)([[:space:]]|=|$)|(^|[^[:alnum:]_])(sudo|pipx)([^[:alnum:]_]|$)|(^|[[:space:]])uv +tool([[:space:]]|$)" &&
  ask "Safety gate (python): a global / system-wide / user-site install (sudo, pip --user/--break-system-packages/--target, uv pip --system, uv tool, pipx) escapes the project virtualenv and mutates a shared interpreter. Confirm with the operator; prefer a project-managed env (uv add / poetry add)."

# P3a. Virtualenv wipe (ask) — a recursive rm of a virtualenv / tox / nox / __pypackages__ dir
#      forces a full reinstall and can break a process bound to it. Fires before the base
#      generic-rm rule for a tailored message.
echo "$CMD" | grep -qE "${CSEP}rm +(-[A-Za-z]*[rR][A-Za-z]*|--recursive)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[^[:alnum:]_])(\.venv|venv|\.virtualenv|virtualenv|\.tox|\.nox|__pypackages__)([^[:alnum:]_]|$)" &&
  ask "Safety gate (python): recursive rm of a virtualenv (.venv / venv / .tox / .nox / ...) forces a full reinstall and can break a running process bound to it. Confirm with the operator."

# P3b. In-place venv wipe via --clear (ask) — `python -m venv --clear`, `virtualenv --clear`, or
#      `uv venv --clear` deletes and recreates the environment in place.
echo "$CMD" | grep -qE "(^|[^[:alnum:]_])(venv|virtualenv)([^[:alnum:]_]|$)" &&
  echo "$CMD" | grep -qE "(^|[[:space:]])--clear([[:space:]]|$)" &&
  ask "Safety gate (python): '--clear' wipes and recreates the virtualenv in place. Confirm with the operator."
# ──────────────────────────────────────────────────────────────────────────────────────
