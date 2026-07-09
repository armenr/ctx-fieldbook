---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-09
tags: [concierge, uninstall, reversible, manifest]
---

# Uninstall — clean, reversible removal

Take Fieldbook back out cleanly, restoring the repo to as close as possible to its pre-install shape.
The install recorded every file action to `.agent-docs/.kit-manifest.json` precisely so this is a
mechanical reverse, not a guessing game: kit-created files get deleted, merged files get restored from
their backups, wired settings get unwound. It is fully **consent-gated** — you show the exact removal
plan and wait for a yes — and it keeps a final safety copy so a change of heart is recoverable.

Voice: matter-of-fact and reassuring — *"here's exactly what I'll remove and put back; nothing goes
until you say so, and I'll keep a copy in case you want it back."* Never breezy about deletion.

## 0. Preconditions + a safety net

```bash
pwd && git rev-parse --show-toplevel 2>/dev/null      # cwd-check before any deletion
test -f .agent-docs/.kit-manifest.json && echo "manifest: present" || echo "manifest: MISSING"
```

Before touching anything, take a full snapshot of the context store so an uninstall is itself
reversible (the colleague may have written real ADRs/lessons they'll want back):

```bash
TS=$(date -u +%Y-%m-%d-%H%M%S)
cp -a .agent-docs ".agent-docs.uninstall-backup-$TS"
echo "safety copy -> .agent-docs.uninstall-backup-$TS  (delete it yourself once you're sure)"
```

If the manifest is missing you cannot do a precise reverse — fall back to the manual removal in
§5 and lean harder on the git diff to see what the install added.

## 1. Read the manifest and build the removal plan (dry-run FIRST)

Load `.agent-docs/.kit-manifest.json`. For each recorded file, the `action` determines its reverse:

| Recorded `action` | Reverse |
|---|---|
| `create` / `copy` / `generate` (a kit-authored file) | **delete** it |
| `merge` (existing file the kit spliced into — `CLAUDE.md`, `.claude/settings.json`) | **restore** from its `backup-path`; if no backup, surgically remove only the kit region (§3) |

Sort into a plan and SHOW it before removing anything:

```
/uninstall  Fieldbook <version> (profile: <p> · stack: <s>)
  delete (kit-created):      .claude/skills/**, .claude/hooks/**, .claude/rules/**,
                             .githooks/**, .agent-docs/CONVENTIONS.md, templates/**, ...   (N files)
  restore-from-backup:       CLAUDE.md  <- CLAUDE.md.fieldbook-backup-<ts>
                             .claude/settings.json  <- settings.json.fieldbook-backup-<ts>
  colleague content present: .agent-docs/decisions/** (K real ADRs), lessons/**, memories/**
                             -> KEPT by default (your work). Remove too? (ask explicitly)
  unset:                     git config core.hooksPath
```

**Flag the colleague's own content loudly.** Their real `decisions/`, `lessons/`, `memories/`,
`checkpoints/`, and `now/*` prose are *their work*, not kit files — default to KEEPING them, and ask
separately whether they want a full wipe or a "remove the machinery, keep my notes" removal. Never
delete authored content as a side effect of removing the kit.

**Wait for an explicit yes before any deletion.**

## 2. Reverse the file actions (only after consent)

Work off the manifest, newest-backup-wins, and confirm each restore before deleting its companion:

```bash
# restore merged files from backup (copy-then-verify BEFORE removing the kit version)
cp "CLAUDE.md.pre-fieldbook-<ts>" CLAUDE.md            # if a backup was recorded
python3 -c 'import json;json.load(open(".claude/settings.json"))' 2>/dev/null   # re-validate after restore

# delete kit-created files enumerated in the manifest (NOT colleague content)
#   rm each recorded create/copy/generate path
```

- **Restore before delete**, and verify the restore landed (the pre-install file is back, `settings.json`
  still parses) so you never remove the kit copy and leave nothing.
- Delete only paths the manifest recorded as kit-created. Anything not in the manifest is either the
  colleague's or pre-existing — leave it.
- Remove now-empty kit dirs (`.claude/skills/`, `.claude/hooks/`, `.githooks/`) only if they are empty
  after the file deletions; if the colleague kept content there, leave the dir.

## 3. Unwind the CLAUDE.md marker block (if no backup existed)

If `CLAUDE.md` was merged with NO recorded backup (it existed but the kit only appended its block),
remove exactly the kit-owned region and nothing else — the delimiters the merge step inserted:

```
<!-- kit:start (fieldbook <kit-version>) -->
   ... the spliced Fieldbook constitution / pointer ...
<!-- kit:end -->
```

Match on the `kit:start` prefix, not the full line — the version stamp inside the parentheses changes
across upgrades, so find the block with a regex like `<!-- kit:start \(fieldbook [^)]*\) -->` (or simply
"the line beginning `<!-- kit:start`") rather than an exact-string compare against one version. Delete
only the lines from the `kit:start` line through the matching `<!-- kit:end -->` inclusive, preserving
all of the colleague's own `CLAUDE.md` prose above and below. Marker blocks belonging to OTHER tools
(any `<!-- something:begin/end -->` pair that isn't the kit's `kit:start`/`kit:end`) are not yours —
leave them byte-untouched (`merge-strategy.md` "Foreign marker blocks"). Show the resulting diff and
confirm before saving. (If a backup WAS recorded, prefer restoring it — §2 — over surgery. If the
marker tokens in the actual file differ from the above, defer to what's physically present / what
`concierge/merge-strategy.md` stamped — the manifest's merge record is authoritative.)

## 4. Unset the git-hooks wiring

`core.hooksPath` was set to `.githooks` at install (a per-clone LOCAL setting). Undo it:

```bash
git config --unset core.hooksPath 2>/dev/null && echo "unset core.hooksPath" || echo "core.hooksPath already unset"
```

If the install renamed a pre-existing `.git/hooks/pre-commit` to `*.stale-disabled-<ts>` (the
fresh-clone protection), tell the colleague it's there and let them decide whether to restore it — do
NOT auto-reactivate an old gate. If the `--copy` install mode was used instead, remove
`.git/hooks/pre-commit` and restore any `*.fieldbook-backup-*` backup beside it. (Backup naming
follows `merge-strategy.md`: `<file>.fieldbook-backup-<UTC-timestamp>`; the manifest's recorded
`backup:` path is always authoritative over the naming pattern.)

## 5. Manual fallback (no manifest)

Without a manifest, reconstruct what to remove from the install commit / git status: the kit adds
`.agent-docs/`, `.claude/skills|hooks|rules/`, `.githooks/`, and a `CLAUDE.md` block. Remove the
clearly-kit files, restore `CLAUDE.md`/`settings.json` from git (`git checkout <pre-install-sha> --
CLAUDE.md .claude/settings.json`) if the install was committed, unset `core.hooksPath`, and keep the
`.agent-docs.uninstall-backup-*` snapshot until the colleague confirms.

## 6. Reset the ID counters for a fresh start (OPTIONAL — a different intent)

Sometimes the colleague doesn't want to REMOVE the kit — they want to keep the machinery but wipe the
accumulated content and start the numbering clean (e.g. adopting it on a repo they were experimenting
in). That is a *reset*, not an uninstall; offer it as a distinct, explicitly-consented operation:

- **Empty the append-only ledgers:** clear `decisions/` (back to just `index.md`), `lessons/`,
  `memories/`, `checkpoints/` — so the next `ADR-`/`LP-` starts at `0001`/`001` again. IDs are "never
  reused" *within* a living system; a deliberate reset of a fresh repo is the sanctioned exception —
  record it in `log.md` so the discontinuity is on the record.
- **Reset `now/*` to the seed shape:** overwrite `status.md` / `work-plan.md` / `open-questions.md` /
  `handoff.md` with the empty-but-valid seed content (re-instantiate from `base/*/agent-docs/now/*` or
  from the templates), so `WU-`/`OQ-` numbering restarts at `0001`/`001`.
- **Truncate `log.md`** to a single fresh header line (or archive the old one to
  `archive/YYYY-MM-log.md` first — keep the history if it has any value).
- **Re-run the lint** (`python3 .claude/hooks/lint-docs.py --root .agent-docs --now "$(date +%Y-%m-%d)"`)
  to confirm the reset tree is clean, exactly as at first install.

A reset keeps the manifest and the hooks in place — only the CONTENT is wiped. Make sure the colleague
means "wipe my notes and renumber," not "remove Fieldbook"; they are different requests.

## 7. Report

```
/uninstall complete — Fieldbook <version> removed.
  deleted:   N kit files
  restored:  CLAUDE.md, .claude/settings.json  (from pre-install backups)
  unset:     core.hooksPath
  kept:      your .agent-docs content (K ADRs, lessons) — say the word to remove those too
  safety:    .agent-docs.uninstall-backup-<ts>  (yours to delete when sure)
```

Then: *"Review the diff and commit the removal when you're happy — I didn't commit anything."* Point
out the safety snapshot one more time so they know how to undo the undo.

## Anti-patterns

- Do NOT delete the colleague's authored content (`decisions/`, `lessons/`, `memories/`, `now/*` prose)
  as a side effect — those are theirs; ask separately.
- Do NOT delete before restoring — copy-then-verify the pre-install file is back first.
- Do NOT reactivate a stale `.git/hooks/pre-commit` automatically — surface it, let the colleague choose.
- Do NOT skip the `.agent-docs.uninstall-backup-*` snapshot — it is what makes uninstall itself reversible.
- Do NOT auto-commit the removal. The human owns the commit.
