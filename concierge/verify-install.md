---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [concierge, verify, smoke-test, install]
---

# Post-install verification — the smoke test

You (the concierge) run this the moment scaffolding finishes, BEFORE the guided tour. It proves the
install is *live*, not just *written* — the single most common install failure is files-on-disk that
are silently inert (hooks not wired, a stale seed the lint trips on, a gate command that doesn't
actually run here). Run every check, then show the colleague a short pass/fail report. Nothing here
mutates the tree; the only writes are optional fixes, and each of those is consent-gated.

Voice: report like a colleague who just set the thing up and is double-checking it in front of you —
"let me make sure this actually works before I hand it over." One clause of WHY per check, no lecture.

## 0. Preconditions

Confirm you are in the target repo and the install completed:

```bash
pwd
git rev-parse --show-toplevel 2>/dev/null || echo "(not a git repo)"
test -f .agent-docs/.kit-manifest.json && echo "manifest: present" || echo "manifest: MISSING — install did not complete"
```

Read `.agent-docs/.kit-manifest.json` — it records `kit-version`, `profile`, `stack`, and a per-file
list (`action` · `sha256` · `backup-path`). It is the ground truth for what was installed; the checks
below are keyed to the `profile` it names (Minimal skips the safety-gate + doc-linter checks). If the
manifest is missing, the install was interrupted — resume the scaffold (`concierge/scaffold-plan.md`)
before verifying.

## 1. Platform preflight (degrade-gracefully — never brick)

The colleague may be on Linux, macOS/BSD, or WSL. Probe each tool and REPORT; a missing optional tool
downgrades a feature, it does not fail the install (every hook is written to no-op without `jq`).

```bash
for t in bash git jq python3 stat sha256sum; do
  if command -v "$t" >/dev/null 2>&1; then echo "OK   $t -> $(command -v "$t")"; else echo "MISS $t"; fi
done
```

Report each result with its consequence, so the colleague knows exactly what they lose:

- **`bash`, `git`** — required. If either is missing, stop and say so; the kit can't operate.
- **`jq`** — the four Claude Code hooks parse their JSON payload with it; **missing `jq` ⇒ every hook
  degrades to a silent no-op** (guarded by `command -v jq || exit 0`). Nothing breaks, but you get no
  enforcement. Recommend installing it.
- **`python3`** — runs the doc-schema linter (`.claude/hooks/lint-docs.py`, Standard+). Missing ⇒ the
  doc lint is skipped; index-completeness enforcement is lost until installed. Stock Python 3 is
  enough (stdlib only, no `pip`).
- **`stat`** — the SessionStart router uses GNU `stat -c %Y` with a BSD `stat -f %m` fallback, so
  either flavor works; only report if BOTH forms fail.
- **`sha256sum`** — used for manifest verification; on macOS/BSD it is often `shasum -a 256` instead.
  If `sha256sum` is missing, note the `shasum -a 256` substitute for `/kit-doctor` and `/kit-upgrade`.

## 2. Doc-schema lint on the seeded tree (expect CLEAN)

The seeds shipped as `*.template.md` and the scaffold instantiated them to their real names
(`status.template.md` → `status.md`, etc.), filling the `{{PLACEHOLDER}}` scalars. A clean lint proves
that instantiation was complete — no dangling `.template.md` left behind, and every `index.md` lists
exactly the files now on disk (rule 13, the one hook-enforced rule).

```bash
python3 .claude/hooks/lint-docs.py --root .agent-docs --now "$(date +%Y-%m-%d)"
```

Expected: `lint-docs: clean — N file(s) checked, all schema rules pass.` (exit 0). Passing `--now`
today means the freshly-written `now/*` docs are 0 days old, so the staleness rule (12, warn-only)
stays quiet.

If it is NOT clean, the finding IS the signal — read it and fix the instantiation, don't wave it
through:

- **Rule 13 "unindexed / phantom"** — a seed was renamed but its `index.md` still lists the old
  `.template.md` name, or a dir has docs but no `index.md`. Fix the index entry to match disk.
- **Rule 1/2/3** — a `{{PLACEHOLDER}}` leaked into a required front-matter field, or a seed kept
  `provenance: kit-template` where it should have been bumped. Fix the field.
- **Rule 15 "work-unit not found"** — a seeded doc references a `WU-NNNN` that isn't in
  `now/work-plan.md`. Either add the WU row or clear the stray reference.

Re-run until clean. A clean lint here is what makes the ADR lint meaningful once the tour writes
`ADR-0001` (see `handover-tour.md`). If `python3` is absent (§1), skip this check and say so.

## 3. `settings.json` parses + is wired

The hook wiring is worthless if the JSON is malformed (Claude Code silently ignores an unparseable
`settings.json`). Validate it, then confirm the four hook events are present:

```bash
python3 -c 'import json,sys; json.load(open(".claude/settings.json")); print("settings.json: valid JSON")' \
  || echo "settings.json: INVALID — the merge produced malformed JSON, fix before proceeding"
for ev in SessionStart PreCompact SubagentStart PreToolUse; do
  grep -q "\"$ev\"" .claude/settings.json && echo "hook wired: $ev" || echo "hook MISSING: $ev"
done
```

If the file was deep-merged into a pre-existing `settings.json`, also confirm the colleague's own
prior `permissions`/`hooks` survived the union (spot-check one entry they had before). A missing event
on Standard+ means the merge dropped it — re-run the merge step (`concierge/merge-strategy.md`).

## 4. Git hooks are actually active (the fresh-clone-inert trap)

Tracked hooks under `.githooks/` do NOTHING until git is pointed at them — this is git's design, and
it is the #1 silent failure: the rules promise a pre-commit gate that is inert on every fresh clone.
Wire it and verify it fires:

```bash
bash .claude/hooks/install-hooks.sh          # sets core.hooksPath=.githooks (idempotent, reversible)
git config --get core.hooksPath              # expect: .githooks
```

`install-hooks.sh` self-verifies and prints `OK verified core.hooksPath=.githooks`. If instead you see
it empty, the wiring did not take — surface it loudly; the SessionStart router will also warn
`core.hooksPath != .githooks` on the next session start until it is set. (The script also renames any
stale `.git/hooks/pre-commit` so a later `--unset` can't resurrect an old divergent gate.)

## 5. The PreToolUse safety gate dry-fires (Standard+ only)

Skip if the manifest `profile` is Minimal (the safety-gate hook ships at Standard+). Otherwise, feed
the assembled gate a sample destructive command on stdin and confirm it intervenes — this proves the
base + stack fragment assembled into a working `pretooluse-safety-gates.sh`:

```bash
GATE=.claude/hooks/pretooluse-safety-gates.sh
bash -n "$GATE" && echo "gate: syntax OK"

# should DENY — force-push to a protected branch is an unambiguous foot-gun
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
  | bash "$GATE"

# should be SILENT (allow) — a benign read-only command
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
  | bash "$GATE"
```

Expected: the first emits JSON containing `"permissionDecision":"deny"`; the second emits nothing at
all (no output = allow, per the hook spec). If the stack fragment added a rule (e.g. a package-publish
or datastore-wipe gate for the detected stack), dry-fire one of those too from the stack pack's
`gate-fragment.sh` header comment. A syntax error here means the assembly spliced the fragment wrong —
re-assemble; do not hand-edit the merged file.

## 6. `/orient` runs cold

The behavioural proof that skills load and the state spine parses. Run `/orient` yourself against the
freshly-seeded state (do NOT pre-read the files — the point is to exercise the cold path a real session
takes):

- It must resolve the `orient` skill by bare name (proves `.claude/skills/` installed project-scoped,
  so the colleague's `/orient` muscle memory transfers).
- It reads `now/handoff.md` and the `now/*` spine and surfaces a ~12-line brief with no parse errors
  (proves the seeds are valid instantiated docs, not raw templates).
- On a fresh seed it will honestly report "no active work-units yet / handoff is the seed" — that is
  correct, not a failure. The tour (`handover-tour.md`) is what fills in the first real state.

If `/orient` can't find the skill, the skills didn't install to `.claude/skills/<name>/SKILL.md` (or
landed namespaced) — re-check the scaffold's skill-copy step.

## 7. Reality-check the baked-in gates

The `{{BUILD_CMD}}` / `{{TEST_CMD}}` / `{{LINT_CMD}}` values were DETECTED from the repo's manifests/CI
and baked into `settings.json`, `now/status.md`, and the pre-commit gate. Detection can be wrong (a
monorepo script, a task-runner alias). Run each ONCE to confirm it actually works here, so the rules
don't promise a gate that errors:

```bash
{{BUILD_CMD}}    # expect: completes (or a known-preexisting failure the colleague confirms)
{{TEST_CMD}}     # expect: runs the suite
{{LINT_CMD}}     # expect: runs the linter
```

You are reality-checking the COMMAND resolves and runs, not that the colleague's code is green. If a
command is unrecognized or wrong, offer to correct it — and note it touches three places
(`settings.json` allow-list, the `now/status.md`/`work-plan.md` gate lines, and `.githooks/pre-commit`
via the `{{LINT_CMD}}`/`{{FMT_CMD}}` placeholders); fix all, then re-run. If the repo has no build/test
toolchain yet (a docs-only or greenfield repo), that's fine — record "no gates wired yet" and move on.

## 8. Report card

Show a compact table — pass / warn / fail per check, with the one-line remedy for anything not green:

```
Fieldbook install — verification (<profile> · <stack> · kit <version>)
  1 platform preflight ...... OK (jq, python3 present)   [or: WARN jq missing -> hooks no-op]
  2 doc-schema lint ......... OK clean
  3 settings.json ........... OK valid + 4 hooks wired
  4 git hooks active ........ OK core.hooksPath=.githooks
  5 safety gate dry-fire .... OK deny on force-push, silent on git status   [Minimal: n/a]
  6 /orient cold ............ OK skill loaded, now/* parsed
  7 baked gates ............. OK {{BUILD_CMD}} / {{TEST_CMD}} / {{LINT_CMD}} run
```

- All green → "Verified. Ready for the 10-minute tour whenever you are (`handover-tour.md`)."
- Any WARN (a degraded-but-safe tool gap) → name it + the one-line fix, then proceed; warnings don't block.
- Any FAIL → stop, explain what's inert and why it matters, offer the specific fix, and re-verify after.
  Do not start the tour on a failed install — a colleague's first impression is a working system.

**Do NOT auto-commit** the seeded install; the colleague reviews and commits it themselves (the tour
ends by pointing at that). Verification is read-only plus the one consented `install-hooks.sh` wiring.
