---
name: kit-upgrade
description: Reconcile an installed Fieldbook copy against a NEWER kit zip. Reads .agent-docs/.kit-manifest.json, 3-way diffs ONLY kit-owned files (skills/hooks/rules/templates/schema — never the colleague's content dirs), and uses sha256-vs-manifest so a file the colleague edited is treated as "theirs" (shows a diff, never overwrites). Bumps the recorded kit-version. Use when the author sends a newer Fieldbook zip, when a new kit's kit-version.txt is ahead of the installed one, or when upgrading/repairing an existing install. Consent-gated; shows a plan before writing.
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
tags: [skill, lifecycle, kit, upgrade, manifest]
---

# /kit-upgrade — reconcile an install against a newer kit

A later Fieldbook zip should merge into an existing install, never clobber it. This skill does a
**3-way reconcile** keyed on the install manifest: for each file the kit owns, it knows what the kit
last wrote (the manifest `sha256`), what is on disk now (possibly the colleague's edit), and what the
new kit ships — and it only ever fast-forwards files the colleague hasn't touched. Everything else it
shows as a diff and lets the human decide. It mutates nothing without an explicit yes.

**Foreground in the main agent** — it needs to read the live tree and present diffs interactively.

## When to invoke

- The author handed over a **newer zip** and the colleague unzipped it somewhere.
- A new kit's `kit-version.txt` is ahead of the `kit-version` recorded in the install manifest.
- Upgrading a profile in place, or repairing an install where a kit-owned file drifted.

## When NOT to invoke

- To ADD a module or bump Minimal→Standard→Full on the SAME kit version — that is a scaffold add-module
  run (`concierge/scaffold-plan.md`), not a version upgrade.
- To UNINSTALL — that is `concierge/uninstall.md`.
- With no newer kit present — there is nothing to reconcile against; run `/kit-doctor` instead.

## Steps

### 1. Read the install manifest (the base for the 3-way merge)

```bash
pwd && git rev-parse --show-toplevel 2>/dev/null      # cwd-check before any reconcile
test -f .agent-docs/.kit-manifest.json && echo "manifest: present" || echo "manifest: MISSING"
```

Load `.agent-docs/.kit-manifest.json`. It gives you `kit-version` (the INSTALLED version), `profile`,
`stack`, and the per-file list — for each kit-managed file: its repo-relative `path`, its `action`
(`create` / `generate` / `copy` / `merge`), whether it is `kit-owned`, the `sha256` the kit last wrote,
and a `backup-path` for merged files. If the manifest is missing, there is no safe base for a 3-way
merge — stop and route to a fresh scaffold instead of guessing.

### 2. Locate the newer kit and confirm the direction

Ask the colleague for the path to the unzipped newer kit (they just unzipped it). Read its
`kit-version.txt`:

```bash
NEWKIT="<path-they-give-you>"      # e.g. the unzipped newer Fieldbook folder
cat "$NEWKIT/kit-version.txt"      # the NEW version
```

Compare to the manifest's installed `kit-version`. If the new version is not actually ahead, say so and
stop (nothing to do, or they pointed at the wrong folder). Confirm the new kit's tree looks intact
(`base/`, `stacks/`, `kit-version.txt` present) before trusting it.

### 3. Classify each kit-owned file — 3-way, sha256-anchored

Walk ONLY the files the manifest marks `kit-owned` (the payload: `.claude/skills/**`, `.claude/hooks/**`,
`.claude/rules/**`, `.agent-docs/CONVENTIONS.md`, `.agent-docs/templates/**`, `.githooks/**`, and the
like). **Never touch the colleague's content** — their `decisions/**` ADRs, `lessons/**`, `memories/**`,
`checkpoints/**`, the prose in `now/*`, or the non-marker parts of `CLAUDE.md`/`settings.json`. Those
are theirs; the manifest does not own them.

For each kit-owned file compute the three hashes:

```bash
sha() { command -v sha256sum >/dev/null 2>&1 && sha256sum "$1" | cut -d' ' -f1 \
        || shasum -a 256 "$1" | cut -d' ' -f1; }     # macOS/BSD fallback
BASE=<manifest sha256 for this path>                 # what the kit last wrote
MINE=$(sha "<path>")                                 # what's on disk now
THEIRS=$(sha "$NEWKIT/<source-path-for-this-file>")  # what the new kit ships
```

Then classify:

| BASE vs MINE | BASE vs THEIRS | Meaning | Action |
|---|---|---|---|
| equal | differ | colleague DIDN'T edit; kit changed it | **Fast-forward** — safe auto-update to THEIRS |
| equal | equal | unchanged both sides | no-op |
| differ | equal | colleague edited; kit DIDN'T change it | **Keep MINE** — no upstream change, don't touch |
| differ | differ | BOTH changed — a real conflict | **Show the diff, human decides** — never auto-overwrite |
| (path absent on disk) | present | a file the new kit adds | **Offer to create** |
| present | (absent in new kit) | kit retired this file | **Offer to remove** (default: keep + flag) |

The load-bearing rule: **`MINE != BASE` means the colleague made it theirs.** A file they edited is
never silently overwritten — you show them what the new kit would change and let them pick. That is the
whole reason the manifest records `sha256`.

**Merged files are special** (`CLAUDE.md`, `.claude/settings.json`): the kit owns only its marked block
/ its hook + permission entries, NOT the whole file. Do not 3-way the whole file — re-merge only the
kit-owned region (the `fieldbook:begin`/`fieldbook:end` marker block in `CLAUDE.md`; the kit's `hooks`
entries + allow-list additions in `settings.json`), preserving everything the colleague added around
it. Back up before re-merging, validate `settings.json` still parses after.

### 4. Present the plan (dry-run FIRST — no writes yet)

Show a compact reconcile plan grouped by action, so the colleague sees exactly what changes before
anything happens:

```
/kit-upgrade  <installed vX> -> <new vY>   (profile: <p> · stack: <s>)
  fast-forward (safe, unedited):   12 files   [list]
  keep yours (you edited these):    2 files   [list — new-kit changes shown on request]
  CONFLICT (both changed):          1 file    [.claude/hooks/pretooluse-safety-gates.sh] -> diff below
  new in vY (offer to add):         3 files   [list]
  retired in vY (offer to remove):  0 files
  re-merge (marker/settings):       CLAUDE.md, .claude/settings.json  (backed up first)
```

For each CONFLICT and each "keep yours" the colleague asks about, show the actual diff
(`diff <disk> <newkit>`). **Wait for an explicit yes** before writing. Nothing is written during the
dry-run.

### 5. Apply (only after consent) + record every action

On yes, apply per the colleague's choices. As with the original install, **record each action to the
manifest as it happens** so an interrupted upgrade is resumable/rollback-able:

- Back up any file before overwriting/re-merging (`<path>.pre-upgrade-<UTC-ts>`), record `backup-path`.
- Fast-forward files: copy from the new kit, update their `sha256` in the manifest.
- Conflict resolutions: apply the colleague's pick; if they kept theirs, leave `sha256` reflecting
  disk and flag it `colleague-owned` so future upgrades keep skipping it.
- Re-merged `CLAUDE.md`/`settings.json`: update only the kit region; re-validate JSON.
- New files: create + add to the manifest. Retired files: remove only on explicit yes.

Then bump the manifest's `kit-version` to the new version and refresh `installed_at`. Copy the new
kit's `kit-version.txt` into the install if the install keeps a local copy.

### 6. Re-verify + report

Re-run the relevant `verify-install.md` checks that the upgrade could have affected — at minimum the
doc lint and (Standard+) a safety-gate dry-fire:

```bash
python3 .claude/hooks/lint-docs.py --root .agent-docs --now "$(date +%Y-%m-%d)"
bash -n .claude/hooks/pretooluse-safety-gates.sh 2>/dev/null && echo "gate syntax OK"
```

Report: `/kit-upgrade <vX> -> <vY>: N fast-forwarded, M kept-yours, K conflicts resolved`. Note any
file left as the colleague's own (so they know it won't track future kits until they re-adopt it), and
recommend they review the diff and commit — **do NOT auto-commit.**

## Anti-patterns

- Do NOT overwrite a file where `MINE != BASE` — that is the colleague's edit; show a diff, let them choose.
- Do NOT 3-way the colleague's content dirs (`decisions/`, `lessons/`, `memories/`, `now/*` prose) — the
  kit doesn't own them.
- Do NOT clobber `CLAUDE.md` or `settings.json` — re-merge only the kit-owned region, backed up first.
- Do NOT apply anything during the dry-run, and do NOT proceed on a conflict without an explicit choice.
- Do NOT auto-commit. The human owns the commit, same as install.

## Design rationale

The manifest's per-file `sha256` is what turns a blind copy into a real 3-way merge: it distinguishes
"the kit wrote this and nobody touched it" (safe to fast-forward) from "the colleague made this theirs"
(hands off). This is the same discipline the install itself runs on — recorded, reversible, consent-gated
— applied to the upgrade path so a newer zip is an *upgrade*, never a *reset*. Uninstall is the inverse
(`concierge/uninstall.md`); the read-only health check is `/kit-doctor`.
