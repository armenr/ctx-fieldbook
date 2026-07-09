#!/usr/bin/env python3
# merge-tool.py — the kit's mechanical merger for the install concierge.
#
# This is KIT-SIDE tooling. It is NEVER installed into a target repo — it lives in `concierge/`
# and is run by the maintainer/concierge to write into someone else's repo. The LLM concierge stays
# the CONSENT + DIFF layer (it decides, shows the plan, gets the yes); this file is the WRITE
# PRIMITIVE it drives once the friend says yes. It mechanizes the contract spelled out in
# `merge-strategy.md` so install/repair/upgrade are deterministic instead of hand-edited.
#
# The two laws it enforces (merge-strategy.md §5):
#   * NEVER CLOBBER — an existing file is only ever appended-to / unioned-into / marker-merged, never
#     overwritten. Invalid JSON in a target aborts (exit 2) with every file left untouched.
#   * ALWAYS REVERSIBLE — every file it modifies is backed up first, and every action is recorded to
#     an append-only manifest ({action, path, sha256 before/after, backup, ts}) so a run is auditable
#     and undoable.
#
# Portability contract (the maintainer may be on macOS / BSD / WSL):
#   * STOCK Python 3, STDLIB ONLY — no pip installs.
#   * Deterministic — the timestamp is SUPPLIED via --ts (used in the manifest + the default backup
#     dir), never read from a wall clock, so a run is reproducible and testable.
#   * Idempotent — a re-run at the same inputs changes nothing already correct. A transform whose
#     result equals what is already on disk is a SKIP: no write, no backup, no manifest entry. This
#     fixes the field donor's bug of rewriting/reformatting settings.json when nothing changed.
#
# What it can do in one invocation (all consent-gated upstream by the concierge):
#   --block FILE          marker-merge a pre-filled kit block into <target>/CLAUDE.md, wrapped in
#                         `<!-- kit:start (fieldbook <ver>) -->` … `<!-- kit:end -->` (--kit-version
#                         supplies <ver>). A prior kit block of ANY version is replaced in place;
#                         foreign marker blocks (someone else's begin/end pair) are preserved verbatim
#                         and the kit block is appended after them.
#   --hooks-json FILE     union-append an {event: [entries]} fragment into settings.json hooks arrays,
#                         de-duplicated on the exact command string.
#   --allow FILE          union a permission allowlist (JSON array, or {"allow": [...]}) into
#                         settings.json permissions.allow.
#   --set-if-absent K=V   set a top-level settings scalar ONLY if the key is absent (repeatable).
#   --dry-run             print the unified diff of every change and exit 0 without writing.
#
# CLAUDE.md and settings.json are each handled as ONE atomic file op (plan → commit): all planning
# and validation happens before any byte is written, so a parse failure on settings.json can never
# leave a half-written CLAUDE.md behind.
#
# Exit status: 0 on success (including all-skips); 2 on any usage / input / refuse-to-clobber error.
#
# provenance: kit-template · created 2026-07-09 · last-modified 2026-07-09

import argparse
import copy
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

# The kit's CLAUDE.md marker seam. The version stamp inside the parens changes across upgrades, so we
# always FIND a prior block by prefix-regex, never by exact string (merge-strategy.md §1.6).
KIT_END = "<!-- kit:end -->"


def kit_start(version):
    return f"<!-- kit:start (fieldbook {version}) -->"


KIT_BLOCK_RE = re.compile(
    r"<!-- kit:start \(fieldbook [^)]*\) -->.*?<!-- kit:end -->", re.DOTALL
)


def die(msg, code=2):
    """Print an error and exit. Default code 2 == usage / refuse-to-clobber (never a silent 1)."""
    print(f"merge-tool.py: error: {msg}", file=sys.stderr)
    sys.exit(code)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------------------------------
# A planned file operation. Planning is READ-ONLY; nothing here touches disk except reads.
# ---------------------------------------------------------------------------------------------------
class FileOp:
    def __init__(self, path, rel, action, before, after):
        self.path = path        # absolute Path to the target file
        self.rel = rel          # path relative to the target repo (manifest + diff label)
        self.action = action    # "create" | "merge" | "skip"
        self.before = before    # original text, or None if the file is absent
        self.after = after      # text to write, or None on skip


# ---------------------------------------------------------------------------------------------------
# Input loading (the concierge's pre-composed fragments — validated so we fail clean, not mid-write)
# ---------------------------------------------------------------------------------------------------
def read_input_text(path_str, what):
    p = Path(path_str).expanduser()
    if not p.is_file():
        die(f"--{what} file not found: {path_str}")
    return p.read_text(encoding="utf-8")


def read_input_json(path_str, what):
    raw = read_input_text(path_str, what)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"--{what} file is not valid JSON ({e}): {path_str}")


# ---------------------------------------------------------------------------------------------------
# CLAUDE.md marker-block merge
# ---------------------------------------------------------------------------------------------------
def merge_block(text, new_block):
    """Return `text` with the kit block set to `new_block`.

    A prior kit block (any version) is replaced IN PLACE — everything outside it, including foreign
    marker blocks, is left byte-untouched. With no prior kit block the new block is appended at the
    end of the file, which is necessarily AFTER any foreign blocks (merge-strategy.md §1)."""
    m = KIT_BLOCK_RE.search(text)
    if m:
        return text[: m.start()] + new_block + text[m.end():]
    if not text:
        return new_block + "\n"
    prefix = text if text.endswith("\n") else text + "\n"
    return prefix + "\n" + new_block + "\n"


def plan_claude_md(target, args):
    path = target / "CLAUDE.md"
    rel = "CLAUDE.md"
    body = read_input_text(args.block, "block").strip("\n")
    new_block = f"{kit_start(args.kit_version)}\n{body}\n{KIT_END}"
    if path.exists():
        before = path.read_text(encoding="utf-8")
        after = merge_block(before, new_block)
        action = "skip" if after == before else "merge"
        return FileOp(path, rel, action, before, after)
    after = merge_block("", new_block)
    return FileOp(path, rel, "create", None, after)


# ---------------------------------------------------------------------------------------------------
# settings.json deep-merge (union hooks / union allow / set-if-absent scalars)
#
# Each transform mutates `data` ONLY when it actually adds something, so a no-op merge leaves the
# structure identical to the original and the SKIP check (parsed-before == parsed-after) preserves the
# friend's exact formatting instead of reformatting it.
# ---------------------------------------------------------------------------------------------------
def _entry_commands(entry):
    out = set()
    if isinstance(entry, dict):
        for h in entry.get("hooks", []) or []:
            if isinstance(h, dict) and isinstance(h.get("command"), str):
                out.add(h["command"])
    return out


def _collect_commands(entries):
    out = set()
    for e in entries or []:
        out |= _entry_commands(e)
    return out


def apply_hooks(data, fragment, rel):
    if not isinstance(fragment, dict):
        die("--hooks-json must be a JSON object mapping event -> [entries]")
    for event, incoming in fragment.items():
        if not isinstance(incoming, list):
            die(f"--hooks-json event {event!r} must map to a JSON array of entries")
        cur_hooks = data.get("hooks")
        cur_arr = cur_hooks.get(event) if isinstance(cur_hooks, dict) else None
        existing = _collect_commands(cur_arr) if isinstance(cur_arr, list) else set()
        to_add = []
        for entry in incoming:
            cmds = _entry_commands(entry)
            # EXACT-COMMAND dedup: an entry already fully represented is skipped (idempotent re-run).
            if cmds and cmds <= existing:
                continue
            to_add.append(entry)
            existing |= cmds
        if to_add:
            hooks = data.setdefault("hooks", {})
            if not isinstance(hooks, dict):
                die(f"{rel}: 'hooks' is not a JSON object; refusing to merge")
            arr = hooks.setdefault(event, [])
            if not isinstance(arr, list):
                die(f"{rel}: hooks.{event} is not a JSON array; refusing to merge")
            arr.extend(to_add)


def apply_allow(data, incoming, rel):
    if isinstance(incoming, dict):
        incoming = incoming.get("allow", [])
    if not isinstance(incoming, list):
        die('--allow must be a JSON array (or {"allow": [...]})')
    cur_perms = data.get("permissions")
    cur_allow = cur_perms.get("allow") if isinstance(cur_perms, dict) else None
    existing = cur_allow if isinstance(cur_allow, list) else []
    to_add = []
    for rule in incoming:
        if rule not in existing and rule not in to_add:
            to_add.append(rule)
    if to_add:
        perms = data.setdefault("permissions", {})
        if not isinstance(perms, dict):
            die(f"{rel}: 'permissions' is not a JSON object; refusing to merge")
        allow = perms.setdefault("allow", [])
        if not isinstance(allow, list):
            die(f"{rel}: permissions.allow is not a JSON array; refusing to merge")
        allow.extend(to_add)


def _parse_scalar(raw):
    """KEY=VALUE values are parsed as JSON (so false/3/null keep their type), string on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw


def apply_set_if_absent(data, pairs):
    for kv in pairs:
        if "=" not in kv:
            die(f"--set-if-absent expects KEY=VALUE, got {kv!r}")
        key, _, raw = kv.partition("=")
        if not key:
            die(f"--set-if-absent expects a non-empty KEY, got {kv!r}")
        if key not in data:
            data[key] = _parse_scalar(raw)


def plan_settings(target, args):
    path = target / ".claude" / "settings.json"
    rel = ".claude/settings.json"
    if path.exists():
        before_raw = path.read_text(encoding="utf-8")
        try:
            before_data = json.loads(before_raw)
        except json.JSONDecodeError as e:
            # Refuse-don't-clobber: unparseable target → abort, file untouched.
            die(f"{rel} is not valid JSON ({e}); refusing to clobber")
        if not isinstance(before_data, dict):
            die(f"{rel} top-level is not a JSON object; refusing to merge")
    else:
        before_raw = None
        before_data = {}

    after_data = copy.deepcopy(before_data)
    if args.hooks_json:
        apply_hooks(after_data, read_input_json(args.hooks_json, "hooks-json"), rel)
    if args.allow:
        apply_allow(after_data, read_input_json(args.allow, "allow"), rel)
    if args.set_if_absent:
        apply_set_if_absent(after_data, args.set_if_absent)

    # SKIP on semantic equality: preserves the friend's indentation/key-order on a no-op, and only
    # reformats to the kit's canonical 2-space when a real change is being made. `_comment` keys and
    # ${CLAUDE_PROJECT_DIR} strings survive verbatim because we never rewrite entries we don't own.
    if after_data == before_data:
        return FileOp(path, rel, "skip", before_raw, None)
    after_text = json.dumps(after_data, indent=2, ensure_ascii=False) + "\n"
    action = "create" if before_raw is None else "merge"
    return FileOp(path, rel, action, before_raw, after_text)


# ---------------------------------------------------------------------------------------------------
# Output: dry-run diffs, and the commit (backup → write → manifest)
# ---------------------------------------------------------------------------------------------------
def print_diff(op):
    if op.action == "skip":
        print(f"# skip: {op.rel} (no change)")
        return
    label = "new file" if op.action == "create" else "merge"
    print(f"# {label}: {op.rel}")
    before_lines = (op.before or "").splitlines(keepends=True)
    after_lines = (op.after or "").splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_lines, after_lines, fromfile=f"a/{op.rel}", tofile=f"b/{op.rel}"
    )
    wrote = False
    for line in diff:
        sys.stdout.write(line if line.endswith("\n") else line + "\n")
        wrote = True
    if wrote:
        sys.stdout.write("\n")


def resolve_backup_dir(target, args):
    if args.backup_dir:
        d = Path(args.backup_dir).expanduser()
        return d if d.is_absolute() else target / d
    if not args.ts:
        die("--ts is required to build the default backup dir (timestamps are supplied, not generated)")
    return target / ".agent-docs" / ".kit-backups" / args.ts


def rel_to_target(path, target):
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def append_manifest(manifest_path, target, entry):
    p = Path(manifest_path).expanduser()
    if not p.is_absolute():
        p = target / p
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def commit(op, target, args, backup_dir):
    if op.action == "skip":
        print(f"skip: {op.rel} (no change)")
        return

    backup_field = None
    sha_before = None
    if op.action == "merge":
        # Back up the exact on-disk bytes BEFORE writing (always reversible).
        orig = op.path.read_bytes()
        sha_before = sha256_bytes(orig)
        backup_path = backup_dir / op.rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(orig)
        backup_field = rel_to_target(backup_path, target)

    after_bytes = op.after.encode("utf-8")
    op.path.parent.mkdir(parents=True, exist_ok=True)
    op.path.write_bytes(after_bytes)  # write_bytes: the sha we record is exactly what lands on disk
    sha_after = sha256_bytes(after_bytes)
    print(f"{op.action}: {op.rel}")

    if args.manifest:
        if not args.ts:
            die("--ts is required to write a manifest entry (timestamps are supplied, not generated)")
        append_manifest(args.manifest, target, {
            "action": op.action,
            "path": op.rel,
            "sha256_before": sha_before,
            "sha256_after": sha_after,
            "backup": backup_field,
            "ts": args.ts,
        })


# ---------------------------------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(
        prog="merge-tool.py",
        description="Kit-side mechanical merger for the Fieldbook install concierge "
                    "(never installed into targets).",
    )
    ap.add_argument("target", help="path to the target repo to merge into")
    ap.add_argument("--block", metavar="FILE",
                    help="pre-filled CLAUDE.md kit block body; wrapped in versioned kit markers")
    ap.add_argument("--kit-version", metavar="VER",
                    help="kit version stamped into the kit:start marker (required with --block)")
    ap.add_argument("--hooks-json", metavar="FILE",
                    help="{event: [entries]} hooks fragment union-merged into settings.json")
    ap.add_argument("--allow", metavar="FILE",
                    help="permission allowlist (JSON array) unioned into settings.json")
    ap.add_argument("--set-if-absent", metavar="KEY=VALUE", action="append", default=[],
                    help="set a top-level settings scalar only if absent (repeatable)")
    ap.add_argument("--backup-dir", metavar="DIR",
                    help="backup directory (default: <target>/.agent-docs/.kit-backups/<ts>)")
    ap.add_argument("--manifest", metavar="PATH",
                    help="append one JSON action entry per write to this path")
    ap.add_argument("--ts", metavar="STAMP",
                    help="timestamp for the manifest + default backup dir (supplied, not generated)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the unified diff of every change and exit 0 without writing")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        die(f"{target} is not a directory")
    if args.block and not args.kit_version:
        die("--block requires --kit-version (the marker carries the kit version stamp)")
    if not (args.block or args.hooks_json or args.allow or args.set_if_absent):
        die("nothing to merge: pass --block, --hooks-json, --allow, or --set-if-absent")

    # Plan every file op first (read-only). A parse failure here aborts before any write, so an
    # invalid settings.json cannot leave a half-applied CLAUDE.md behind.
    ops = []
    if args.block:
        ops.append(plan_claude_md(target, args))
    if args.hooks_json or args.allow or args.set_if_absent:
        ops.append(plan_settings(target, args))

    if args.dry_run:
        for op in ops:
            print_diff(op)
        return 0

    backup_dir = None
    if any(op.action == "merge" for op in ops):
        backup_dir = resolve_backup_dir(target, args)
    for op in ops:
        commit(op, target, args, backup_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
