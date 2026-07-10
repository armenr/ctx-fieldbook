---
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-10
tags: [concierge, merge, never-clobber, manifest, rollback]
related: [scaffold-plan, interview, profiles]
---

# Merge strategy — never clobber, always reversible

The install writes into someone else's repo. The first law is **never destroy work that's already
there**, and the second is **every change is reversible**. This file is how the concierge honors both:
the collision handling for the three files that are likely to already exist (`CLAUDE.md`,
`.claude/settings.json`, name-colliding skills/hooks), plus the `.kit-manifest.json` ledger that makes
an interrupted install resumable, a re-run idempotent, and an uninstall clean.

**The universal rule (from `scaffold-plan.md`):** for every dest file — **absent → CREATE** ·
**present + identical after transform → SKIP** · **present + different → MERGE**. A MERGE never writes
without a backup, a shown diff, and a per-file explicit yes. One blanket Q6 "go" authorizes the CREATEs;
each clobbering MERGE is surfaced and confirmed on its own.

---

> **Mechanical executor.** The write steps in §1–§2 are implemented by `concierge/merge-tool.py`
> (python3 stdlib, kit-side only — never installed into the target). The concierge stays the
> consent layer: compute the plan, show the diff (`--dry-run`), get the explicit yes, THEN invoke
> the tool as the write primitive. Backups land under `<target>/.kit-backups/<ts>/` at the repo
> ROOT — deliberately OUTSIDE `.agent-docs/`, so a backed-up `.md` is never re-linted by the kit's
> own doc linter. Manifest sink is dual: pointed at the structured `.kit-manifest.json` (a JSON
> object carrying a `files[]` array) the tool read-modify-writes a canonical §4 row into `files[]`
> (a row for the same path is replaced, never duplicated); pointed at a plain `.jsonl` log it
> appends a per-action evidence line (`action · path · sha256-before/after · backup · ts`). It never
> appends raw JSONL onto a structured manifest — that hybrid is unparseable.

## 1 · Existing `CLAUDE.md` → backup + marker block + diff + yes

The constitution goes in the target's project-root `CLAUDE.md`. If one already exists (the friend has
their own instructions), we ADD to it, never overwrite it.

1. **Back up** verbatim → `<target>/CLAUDE.md.fieldbook-backup-<UTC-timestamp>`. Record the backup path
   in the manifest entry.
2. **Marker-block the kit content.** Wrap everything the kit contributes in:
   ```
   <!-- kit:start (fieldbook <kit-version>) -->
   ...the composed/filled constitution...
   <!-- kit:end -->
   ```
   The markers are the seam an upgrade/uninstall edits — the kit only ever touches text BETWEEN its own
   markers; the friend's content outside them is never read or rewritten.
3. **Placement.** Append the block at the end (least disruptive) unless the friend's file is empty/only a
   title, in which case top-of-file reads better — offer the choice in one line.
4. **Idempotency.** If a `<!-- kit:start … -->` block already exists (a prior install/upgrade), do NOT
   add a second — **replace the existing block's body in place** (diff the old block body vs the new,
   show it, get yes). Content outside the markers is left byte-untouched.
5. **Diff + yes.** Show the unified diff of what lands between the markers; get an explicit yes before
   writing. On no → adjust or skip the CLAUDE.md step (the rest of the install can still proceed; note
   the constitution as un-wired in the manifest).
6. **Version matching.** The `kit:start` line carries the kit version, which changes across upgrades —
   so any operation that must FIND the kit's block (idempotency check, upgrade, uninstall) matches on
   the `kit:start` prefix, e.g. `<!-- kit:start \([^)]*\) -->`, never on an exact one-version string.
   A leak-gated public fork MAY instead stamp the sanctioned nameless variant
   `<!-- kit:start (<kit-version>) -->` (label dropped, version kept — ADR-0011); the label is optional
   and matching is prefix-only, so named and nameless blocks are found and replaced interchangeably.
   When rewriting the block, stamp the current `kit-version.txt` value into the new start marker.

### Foreign marker blocks

Other tools use the same trick: the friend's `CLAUDE.md` may already contain marker pairs that are not
ours (any `<!-- something:begin -->` / `<!-- something:end -->` or similarly-fenced region whose tokens
aren't the kit's own `kit:start`/`kit:end`). Those blocks are somebody else's managed seam:

- **Preserve byte-verbatim.** Never merge into, reflow, or edit inside a foreign block.
- **Never count as kit-owned.** They don't enter the manifest, and uninstall never removes them —
  uninstall strips only the kit's own `kit:start`…`kit:end` region.
- **Insert after.** When appending the kit block (§1 step 3), place it AFTER any existing foreign
  blocks, not between a foreign pair or above one.
- **The same seam discipline, inverted, is how kit docs host LOCAL content:** a kit doc may ship a
  deliberately-unfilled fork slot for the adopter's own idiom (e.g. work-discipline's "Your gate
  idiom" section) — the adopter re-voices inside the slot, and upgrades preserve the filled slot the
  way installs preserve foreign blocks.
- **Read-to-classify (obligations-form detection, ADR-0012 — an EXTENSION, not a loosening).** The
  installer MAY *read* a foreign block's body to classify the repo's coordination posture: a foreign
  block whose body reads as an **agent-comms protocol** (a message room, monitor/watch-arming lines,
  named agents + their reply discipline) is the strongest signal for the obligations-ledger form
  decision (`multi_party` — `interview.md` Q1 detection; `scaffold-plan.md` then ships
  `now/obligations.md` as a standalone file vs a `## Obligations` handoff section). This is READ-ONLY
  classification and changes none of the preservation rules above — never merge into, reflow, or edit
  inside a foreign block; it still never enters the manifest and uninstall never touches it. Classifying
  is looking, not editing.

---

## 2 · Existing `.claude/settings.json` → deep-merge (never overwrite)

settings.json is JSON the friend may already hook/permission. Overwriting it would silently drop their
config, so we **deep-merge** and validate.

1. **Parse both** — the existing target settings.json and the kit-built one (`scaffold-plan.md` Phase 4).
   If the target file is invalid JSON, do NOT proceed on it: back it up, report the parse error, and ask
   whether to replace-from-backup or hand-fix — never write a merge on top of unparseable JSON.
2. **Back up** → `<target>/.claude/settings.json.fieldbook-backup-<UTC-timestamp>`.
3. **Merge rules (append/union, never replace a scalar the friend set):**
   - `hooks.<Event>[]` — **append** the kit's hook entries to any existing array for that event; do not
     drop the friend's hooks. Dedup on the exact `command` string (a re-run adds nothing new).
   - `permissions.allow[]` / `permissions.deny[]` — **union** (set-union, dedup). The kit only adds to
     `allow`; it never adds to `deny` and never removes a friend's entry.
   - `autoMemoryEnabled` and other top-level scalars — the kit sets `autoMemoryEnabled: false` **only if
     the key is absent**; if the friend has set it, leave their value and note the kit's rationale (the
     comment in the template) rather than overriding a deliberate choice.
   - Any key the kit doesn't own → left exactly as the friend had it.
4. **Validate** the merged JSON parses before writing. **Diff + yes.** Then write.
5. **Manifest** records `action: merge`, the backup path, and the post-merge `sha256`.

---

## 3 · Skill / hook name collisions → namespace or ask

Skills install bare-name (`.claude/skills/orient/`, …) so `/orient` muscle memory transfers. That means
a name collision with the friend's own skill/hook is possible.

- **Identical content** (same skill the kit already installed, e.g. a prior run) → SKIP silently
  (idempotent).
- **Different content, same name** (the friend has their own `orient` skill, or a hook filename clash) →
  do NOT overwrite. Surface it and offer, in one line:
  1. **Keep theirs** (skip the kit's — note it in the manifest as `skipped: name-collision`), or
  2. **Install kit's under a suffix** — `orient-fieldbook` / `pretooluse-safety-gates-fieldbook.sh` —
     and, for a hook, wire the suffixed name into settings.json instead. The friend's stays the default;
     the kit's is available explicitly.
- Default recommendation: keep theirs for a *skill* (their muscle memory), suffix-install for a *hook*
  (so the kit's enforcement still runs) — but ASK; never silently pick.
- The pre-commit dispatcher is a special case: if the friend already has `.githooks/pre-commit`, MERGE
  per §1's marker approach where feasible, else `install-hooks.sh --copy` with the backup it already
  performs (it backs up an existing `.git/hooks/pre-commit`).

---

## 4 · The manifest — idempotency + rollback ledger

`<target>/.agent-docs/.kit-manifest.json` is the single source of truth for what the install did. It is
written **as operations happen** (not at the end), so a crash mid-install leaves an accurate partial
record.

### Schema
```json
{
  "kit_version": "<from kit-version.txt>",
  "kit_ref": "<IMMUTABLE ref of the kit tree installed from — commit SHA or version tag, NEVER a branch name>",
  "kit_commit": "<when kit_ref is a TAG, the tag's resolved commit SHA frozen alongside — tags can move, SHAs can't; verification compares against THIS (field-contributed pattern, first v0.4.0 adoption)>",
  "multi_party": "<JSON boolean true|false — the obligations-ledger form decision (ADR-0012), recorded at install/ratification; never a string>",
  "profile": "minimal|standard|full",
  "stack": "rust|node-ts|python|go|generic",
  "created": "<UTC timestamp>",
  "completed": "<UTC timestamp | null while in-flight>",
  "status": "in-progress|complete",
  "tokens": { "PROJECT_NAME": "...", "BUILD_CMD": "...", "...": "..." },
  "modules": ["research-pipeline", "revisit-ledger", "recurrence-guard", "agents-starter"],
  "files": [
    {
      "path": "<dest, relative to target>",
      "action": "create|merge|skip|adopt",
      "source": "<kit source, relative to kit root | null for adopted non-kit-origin files>",
      "sha256": "<sha256 of the installed file>",
      "backup": "<backup path | null>",
      "keep-local": "<true ONLY on documented local-override rows; omit otherwise>"
    }
  ],
  "git": { "hooksPath_set": true, "hooksPath_prev": "<prior value | null>" }
}
```

**This block is the CANONICAL manifest row schema** — scaffold-plan, kit-upgrade (including its
retro-adoption backfill), kit-doctor, and uninstall all read/write THIS shape; the field is `backup`
(never `backup-path`), and `adopt` is the action for retro-adopted files.

**Pin fields.** The header `kit_ref` is the ratified BASELINE pin for every row. A row may carry its
own `kit-ref` override ONLY when it diverges from the baseline (a security-expedited single-file
delta, an incremental adoption) — mirroring the `keep-local` only-on-override pattern. Pins are
immutable refs; the pin protocol itself lives in the kit-upgrade skill (§Pin protocol).

### The five modes (all read the manifest first)

- **install** — no manifest (or `status` absent) → fresh install; write the header, execute
  `scaffold-plan.md`, append entries, write the footer.
- **repair** — manifest present, same `kit_version` + `profile` → re-verify each `files[]` entry's
  on-disk `sha256`. Missing file → re-create from source. Drifted file (friend edited it) → LEAVE it
  (their edit wins) and report the drift; do not silently revert. This is the idempotent re-run.
- **upgrade** — manifest present, `kit_version` older than this kit → copy the delta payload
  (`profiles.md` §5 additive upgrade), MERGE any file whose kit-source changed (marker-block / deep-merge
  per §1–2), bump `kit_version` in the manifest. Never rewrite a friend-drifted file without a diff+yes.
- **add-module / grow-profile** — manifest present, friend opts into a higher profile or a module →
  install only the new payload; record the new entries + updated `profile`/`modules`.
- **uninstall** — walk `files[]` in REVERSE order: for `action: create` → delete the installed file if
  its on-disk `sha256` still matches (unmodified since install); if it drifted, ask before deleting. For
  `action: merge` → restore from the recorded `backup` (or, for a CLAUDE.md/settings marker/merge, strip
  the kit block / un-union the kit entries and restore the backup). Unset `core.hooksPath` if
  `git.hooksPath_set` and restore `git.hooksPath_prev`. Remove the manifest last.

### Resume (interrupted install)
On restart with `status: in-progress`, the concierge reads `files[]`, treats every recorded entry as
already-done (verifying `sha256`), and continues `scaffold-plan.md` from the first operation NOT in the
ledger. No completed step is redone; no half-written step is trusted (verify its `sha256`; if it doesn't
match a clean transform, redo it).

---

## 5 · Invariants (the two laws, spelled out)

- **Never clobber.** No existing file is overwritten without: a timestamped backup recorded in the
  manifest, a shown diff, and a per-file explicit yes. CLAUDE.md and settings.json are always
  merge-if-present; skills/hooks are keep-or-suffix-on-collision.
- **Always reversible.** Every mutation (file create, file merge, the one git-config change) has a
  manifest entry with the undo material (backup path, or prior git value). An uninstall or a rollback of
  an interrupted install is a deterministic replay of the ledger in reverse.
- **Idempotent.** A re-run at the same version/profile changes nothing that is already correct
  (`sha256`-verified) and only repairs what's missing — it never duplicates a marker block, a hook array
  entry, or an allowlist permission.
- **Consent-gated.** The manifest header + every backup + every diff exist so the friend can see and undo
  anything. Modeling this discipline IS part of what the kit teaches.

## Related

- `scaffold-plan.md` — the ordered operations this file adjudicates the collisions for ·
  `interview.md` (Q6 shows the diffs) · `profiles.md` §5 (the additive upgrade path uses `upgrade` mode).
