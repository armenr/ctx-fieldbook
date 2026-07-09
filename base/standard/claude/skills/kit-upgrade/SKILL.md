---
name: kit-upgrade
description: Reconcile an installed Fieldbook copy against a NEWER kit zip. Reads .agent-docs/.kit-manifest.json, 3-way diffs ONLY kit-owned files (skills/hooks/rules/templates/schema — never the colleague's content dirs), and uses sha256-vs-manifest so a file the colleague edited is treated as "theirs" (shows a diff, never overwrites). Bumps the recorded kit-version. When the manifest is MISSING but the tree is kit-lineage-shaped (hand-seeded / pre-kit port), emits a retro-adoption plan and backfills the manifest instead of stopping. Use when the author sends a newer Fieldbook zip, when a new kit's kit-version.txt is ahead of the installed one, or when upgrading/repairing an existing install. Consent-gated; shows a plan before writing.
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
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
- A kit-lineage repo has **no manifest** (hand-seeded, or ported before the kit existed) and needs
  adopting into manifest-backed management — the §Retro-adoption branch below.

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
and a `backup` path for merged files. If the manifest is missing, there is no safe base for a 3-way
merge — do NOT guess. Branch on the tree's shape:

- **Kit-lineage-shaped** — `.agent-docs/CONVENTIONS.md` present, a `now/` spine, kit-named skills/hooks
  under `.claude/` → a hand-seeded or pre-kit install. Go to **§Retro-adoption** below: emit an
  ADOPTION PLAN and backfill the manifest instead of stopping.
- **Neither manifest nor kit shape** → not a Fieldbook lineage at all; stop and route to a fresh
  scaffold (`concierge/scaffold-plan.md`).

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
kit-owned region (the `<!-- kit:start (fieldbook <kit-version>) -->` … `<!-- kit:end -->` marker block
in `CLAUDE.md` — match on the `kit:start` prefix, never the full line, since the version stamp inside
the parentheses changes across upgrades (`merge-strategy.md`); the kit's `hooks` entries + allow-list
additions in `settings.json`), preserving everything the colleague added around it. Back up before
re-merging, validate `settings.json` still parses after.

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

- Back up any file before overwriting/re-merging (`<path>.pre-upgrade-<UTC-ts>`), record `backup`
  (the canonical manifest field — `merge-strategy.md` §4).
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

## Retro-adoption — manifest missing, tree kit-shaped

The branch step 1 routes here. A hand-seeded or pre-kit tree has the kit's artifacts but no manifest —
so no `sha256` base, no ownership record, and future upgrades would be blind. Do not upgrade blind and
do not reset: **adopt**. Emit an ADOPTION PLAN, get consent, then backfill the manifest so the tree
becomes a normal manifest-backed install from here on.

### A. Inventory + classify (read-only)

Walk the tree's kit-shaped artifacts (`.claude/skills/**`, `.claude/hooks/**`, `.claude/rules/**`,
`.agent-docs/CONVENTIONS.md`, `.agent-docs/templates/**`, `.githooks/**`, `CLAUDE.md`,
`.claude/settings.json`) and classify each against what the current kit ships, using these classes
(GENERATE bundles scaffold-plan's FILL+RENAME product; the rest map 1:1 onto its write posture) plus
one adoption-only class:

- **COPY-VERBATIM** — on-disk file is byte-identical to what the kit ships → adopt as-is, no write.
- **GENERATE** — a file the kit produces from a template + scalars (`settings.json`, the `CLAUDE.md`
  block, stack rules) → regenerate, diff against disk, route the delta to MERGE or KEEP-LOCAL.
- **MERGE** — both the kit and the tree carry real content (an edited hook, a hand-grown `CLAUDE.md`)
  → marker-block / deep-merge per `merge-strategy.md`, never clobber.
- **SKIP** — the colleague's content (`decisions/**`, `lessons/**`, `now/*` prose) the kit never owned,
  plus kit files outside the chosen profile.
- **KEEP-LOCAL** — a documented local override the colleague wants kept diverged; recorded so future
  upgrades skip it (same standing as a `colleague-owned` conflict resolution in step 5).
- **UPSTREAM** — the tree's surface is AHEAD of the kit (the adopter invented it, or evolved past the
  kit's copy). No write at adoption; the row queues for the kit's next harvest and behaves as
  KEEP-LOCAL until the kit catches up. Adoption is not one-directional — never flatten a source repo
  toward an older kit shape.

**Transform + safety notes** (each earned by a real adoption; skip none):

- **Gate-mechanism translation (do this FIRST).** Detect the tree's actual gate runner — `.githooks`
  + `core.hooksPath`, lefthook, the pre-commit framework, husky, a `just`/`make` target. Kit gate
  CHECKS are mechanism-agnostic; the `.githooks` wiring is just the kit's default carrier. Translate
  each kit check into the local runner (one plan row per check: kit check → local hook entry,
  class MERGE) instead of forcing `core.hooksPath`; kit files that only exist to carry the
  `.githooks` mechanism (`install-hooks.sh`, the fresh-clone hooksPath warning) become SKIP with the
  translation noted.
- **LOCALIZE, never silent-COPY across a namespace.** When a naming override is ruled KEEP-LOCAL
  (ID prefixes, dir names), a kit doc body adopted into that namespace is a MERGE with a
  `localize:` note (kit body + local-name substitution) — a mechanical COPY silently splits the
  namespace across surfaces.
- **`supersedes:` flag.** A row whose adoption REVERSES one of the adopter's own OPEN rulings (an
  open OQ, a proposed ADR) must carry `supersedes: <id>` in its flags; the operator's yes is per-row
  for these, and executing the row writes an explicit supersession entry in the adopter's decision
  record — never a silent override.
- **`lockstep:` flag.** Files forming a producer/consumer pair (e.g. a lint's output format and the
  session-router line that parses it) adopt together or not at all; mark both rows `lockstep:` with
  each other's path.
- **Content, not shape.** Where the kit split a doc (core + rationale, core + addendum) and the tree
  deliberately keeps a monolith, adopt the CONTENT into the local structure (MERGE) — the file split
  is kit packaging, not doctrine; do not require it.
- **Provenance guard.** Adopted kit docs never import the KIT's lifecycle state into local records:
  a kit doc's `status:` (or its upstreamed twin's) does not change the status of the adopter's own
  ADRs/OQs — local decision lifecycle is owned locally.

Present the plan as a per-artifact table — one row per path, with a keep-local column and per-row
secret/machine flags (`secret`: never copy, echo, or diff its contents; `machine`: host-specific
paths/config — regenerate locally, never port):

```
ADOPTION PLAN  (no manifest found; tree is kit-lineage-shaped)
| path                                   | class         | keep-local? | flags   | note                        |
| .claude/hooks/precompact-handoff-*.sh  | COPY-VERBATIM |             |         | identical to kit            |
| .claude/hooks/pretooluse-safety-*.sh   | MERGE         |             |         | local rule added — diff below |
| .claude/settings.json                  | GENERATE      |             | machine | regenerate + union perms    |
| .claude/skills/orient/SKILL.md         | KEEP-LOCAL    | yes         |         | documented local variant    |
| .agent-docs/decisions/**               | SKIP          |             |         | colleague content           |
```

### B. Consent gate, then write via merge-tool

**Nothing is written until the operator says yes to the plan** — and every MERGE row still gets its
own per-file yes on the diff, same contract as install. On consent, apply writes through
`concierge/merge-tool.py` (the kit's write primitive: marker replace-in-place, hook append+dedup,
permission union, refuse-don't-clobber, backups + ledger) — no hand-stitched edits.

### C. Manifest BACKFILL (the final step, always)

Every kept artifact — including untouched COPY-VERBATIM and KEEP-LOCAL rows — gets a manifest row:
its `path`, the `sha256` of what is on disk after adoption, and `action: "adopt"`. Mark
COPY-VERBATIM/GENERATE rows `kit-owned`; mark KEEP-LOCAL rows `colleague-owned` so upgrades keep
skipping them. Stamp `kit-version`, `profile`, and `stack`. From the next run onward the tree takes
the normal 3-way path in steps 1–6.

## Anti-patterns

- Do NOT overwrite a file where `MINE != BASE` — that is the colleague's edit; show a diff, let them choose.
- Do NOT 3-way the colleague's content dirs (`decisions/`, `lessons/`, `memories/`, `now/*` prose) — the
  kit doesn't own them.
- Do NOT clobber `CLAUDE.md` or `settings.json` — re-merge only the kit-owned region, backed up first.
- Do NOT apply anything during the dry-run, and do NOT proceed on a conflict without an explicit choice.
- Do NOT write anything during retro-adoption before the operator's yes, and do NOT backfill a manifest
  row for an artifact that never appeared in the adoption plan.
- Do NOT auto-commit. The human owns the commit, same as install.

## Design rationale

The manifest's per-file `sha256` is what turns a blind copy into a real 3-way merge: it distinguishes
"the kit wrote this and nobody touched it" (safe to fast-forward) from "the colleague made this theirs"
(hands off). This is the same discipline the install itself runs on — recorded, reversible, consent-gated
— applied to the upgrade path so a newer zip is an *upgrade*, never a *reset*. Retro-adoption is the
same idea run in reverse: a manifest-less kit-shaped tree gets classified, consented, and backfilled
into exactly this discipline instead of being reset or upgraded blind. Uninstall is the inverse
(`concierge/uninstall.md`); the read-only health check is `/kit-doctor`.
