#!/usr/bin/env python3
# lint-docs.py — the language-agnostic doc-schema linter for `.agent-docs/`.
#
# This is the ENFORCEMENT the CONVENTIONS.md "Lint rules" section refers to. CONVENTIONS ships those
# rules as a spec; this file makes them real. It implements every rule 1–15 from that section as a
# discrete check with a PASS/FAIL (or WARN) verdict and a `file:line` message. Rule 16 is a kit-local
# advisory (WARN-only, not a CONVENTIONS rule): it nudges `ADR-`-prefixed ADR filenames back toward the
# canonical unprefixed form without failing the run.
#
# Portability contract (the colleague may be on macOS / BSD / WSL):
#   * STOCK Python 3, STDLIB ONLY — no pip installs, no `import yaml`. Front-matter is hand-parsed.
#   * Deterministic — the staleness check reads its "now" from --now, never a wall clock, so a run is
#     reproducible and testable. Without --now the staleness rule is skipped gracefully.
#   * Never hard-fails on a doc it cannot read; degrades to a finding, not a crash.
#
# Exit status: 0 when clean (or warnings only); 1 when any FAIL was reported. Warnings never fail.
#
# CLI: lint-docs.py [--root DIR] [--now YYYY-MM-DD] [--warn-days N] [--fail-days N]
#                   [--extra-id-prefixes S,U,AR,NS]
#
# What gets linted, and the template stance (documented choice):
#   The linter walks every `*.md` under --root. INSTANTIATED docs get the full rule set. Kit-shipped
#   scaffolding — a file whose name ends `.template.md`, OR any file under a `templates/` dir, OR any
#   doc still carrying `provenance: kit-template` — gets a RELAXED pass: structural rules (front-matter
#   present + parseable, required fields, allowed provenance, filename/category shape) still apply, but
#   rules that assume a fully instantiated tree are skipped for it: cross-reference resolution (a seed
#   references not-yet-instantiated sibling names), `now/` staleness, and WU resolution. Rationale: a
#   seed legitimately holds `{{PLACEHOLDER}}` tokens and points at names that only exist post-install;
#   linting those as if instantiated would flag the kit itself. The ADR/checkpoint body rules are keyed
#   on directory + filename shape (`decisions/[ADR-]NNNN-*.md` — the `ADR-` prefix is optional and
#   recognized, `checkpoints/DATE-*.md`), so a template in `templates/` is never mistaken for the real
#   artifact.
#
# Adopt-exemption: docs recorded `action: adopt` in `<root>/.kit-manifest.json` predate the kit and carry
#   no kit front-matter — the schema-class rules (1,2,3,4,5,6,10,12,14) are skipped for them; rule 13
#   (index completeness) still applies so they stay visible. Rule 14 (checkpoint integrity) is exempt for
#   the same write-once reason: a checkpoint authored before the ten-point format cannot be retro-edited to
#   add the points, so an adopted row must exempt it — while a freshly-written checkpoint is never adopted
#   and stays fully checked. Missing/malformed manifest ⇒ no exemptions, no crash.

import argparse
import datetime
import json
import os
import re
import sys

# ---------------------------------------------------------------------------------------------------
# Schema constants (mirror CONVENTIONS.md §2 / §5)
# ---------------------------------------------------------------------------------------------------
ALLOWED_PROVENANCE = {"human", "llm-reviewed", "llm-draft", "llm-autonomous", "kit-template"}
ADR_STATUS = {
    "proposed", "accepted", "pending", "deferred", "rejected", "superseded", "deprecated",
}
REQUIRED_FIELDS = ("provenance", "created", "last-modified")
# Front-matter fields whose values name other docs that must resolve on disk (CONVENTIONS rule 8).
REFERENCE_FIELDS = ("related", "supersedes", "superseded-by", "archived-from")
# Typed ID prefixes that are cross-references, NOT files (they resolve to a ledger row, not a path).
# REV (reviews subsystem — REV-NNN, Standard tier since 0.2.0) is DISTINCT from RV (REVISIT anchors); both
# are listed, ordered longest-first (REV before RV before R) so `REV-001` is matched by REV and never
# swallowed by the shorter RV / R alternatives. The trailing `-` already disambiguates, but longest-first
# keeps that correctness independent of the anchoring detail.
ID_PREFIX_RE = re.compile(r"^(OQ|WU|LP|REV|RV|FR|R|INC)-", re.IGNORECASE)

RULES = {
    1: "front-matter present + parseable",
    2: "required fields populated (provenance, created, last-modified)",
    3: "provenance in the allowed set",
    4: "ADRs have a valid status",
    5: "ADR status:superseded implies non-null superseded-by",
    6: "ADR status:pending implies pending-on; deferred implies deferred-because",
    7: "ADRs contain a non-empty '## Alternatives Considered' section",
    8: "related / supersedes / superseded-by / archived-from references resolve",
    9: "file path matches category (ADR in decisions/, checkpoint in checkpoints/)",
    10: "accepted ADRs are not llm-draft / llm-autonomous",
    11: "date-prefixed filenames match the date format",
    12: "now/ files last-modified within the freshness window (warn-not-fail)",
    13: "index completeness (every populated content dir has a matching index.md)",
    14: "checkpoint integrity (all ten numbered points present)",
    15: "work-unit value resolves to a WU in now/work-plan.md",
    16: "advisory: ADR filenames carry a redundant 'ADR-' prefix; canonical is decisions/NNNN-slug.md "
        "(warn-not-fail)",
}

FAIL = "FAIL"
WARN = "WARN"

# Schema-class rules (front-matter presence + field validity + provenance enum + staleness), PLUS rule 14
# (checkpoint integrity). These are the rules waived for retro-adopted docs (manifest `action: adopt`) —
# a pre-existing flat corpus that predates the kit and carries no kit front-matter. Rule 14 is waived for
# the write-once reason: a checkpoint authored before the ten-point format cannot be retro-edited to pass,
# so an adopted row exempts it — a freshly-written checkpoint is never adopted and stays fully checked.
# Everything else (notably rule 13 index completeness) still applies to them; see load_adopted_paths() and
# the post-filter in main().
SCHEMA_CLASS_RULES = frozenset({1, 2, 3, 4, 5, 6, 10, 12, 14})

# Rule 12 (staleness) is a doc-freshness signal, shipped WARN-only so a stale-but-correct doc never
# hard-fails a commit / CI gate. CONVENTIONS notes a 90d *fail* threshold; --fail-days changes the
# message wording (soft-stale vs hard-stale), not the finding class. A maintainer who wants a hard
# gate can flip this one constant.
STALENESS_FAILS = False


class Finding:
    __slots__ = ("rule", "level", "path", "line", "msg")

    def __init__(self, rule, level, path, line, msg):
        self.rule = rule
        self.level = level
        self.path = path
        self.line = line
        self.msg = msg


# ---------------------------------------------------------------------------------------------------
# Hand-rolled front-matter parser (no PyYAML). A doc's front-matter is the first `---`-delimited
# block, optionally preceded ONLY by blank lines and HTML comment blocks (the templates open with a
# `<!-- guidance -->` block before their front-matter). Supports scalars, inline `[a, b]` lists, and
# simple block lists (`key:` then `- item` lines). Trailing ` # inline comments` are stripped.
# ---------------------------------------------------------------------------------------------------

def _strip_inline_comment(s):
    # A YAML inline comment starts at whitespace + '#'. Strip from the first ' #' or '\t#'.
    for token in (" #", "\t#"):
        idx = s.find(token)
        if idx != -1:
            s = s[:idx]
    return s


def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_scalar(val):
    val = _strip_quotes(val.strip())
    if val == "" or val.lower() in ("null", "~", "none"):
        return None
    return val


def _parse_inline_list(val):
    inner = val.strip()
    inner = inner[1:-1] if inner.startswith("[") else inner
    if inner.endswith("]"):
        inner = inner[:-1]
    inner = inner.strip()
    if not inner:
        return []
    return [_strip_quotes(x) for x in inner.split(",") if x.strip()]


def extract_frontmatter_region(lines):
    """Return (start_idx, end_idx) of the '---' fences, or None. Skips a leading comment block."""
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s == "":
            i += 1
            continue
        if s.startswith("<!--"):
            if "-->" in s:
                i += 1
                continue
            i += 1
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1  # consume the closing '-->' line
            continue
        break
    if i >= n or lines[i].strip() != "---":
        return None  # no opening fence
    start = i
    for j in range(i + 1, n):
        if lines[j].strip() == "---":
            return (start, j)
    return "UNTERMINATED"


def parse_frontmatter(text):
    """Return (fields, field_line, error). fields: {key: scalar|list|None}. field_line: 1-indexed."""
    lines = text.split("\n")
    region = extract_frontmatter_region(lines)
    if region is None:
        return None, None, "no YAML front-matter (expected an opening '---')"
    if region == "UNTERMINATED":
        return None, None, "unterminated front-matter (opening '---' has no closing '---')"
    start, end = region
    fields, field_line = {}, {}
    i = start + 1
    while i < end:
        raw = lines[i]
        line_no = i + 1
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):(.*)$", raw)
        if not m:
            i += 1
            continue
        key = m.group(1)
        val = _strip_inline_comment(m.group(2)).strip()
        if val == "":
            # Possible block list: consecutive '- item' lines.
            items, j = [], i + 1
            while j < end:
                s2 = lines[j].strip()
                if s2.startswith("- "):
                    items.append(_strip_quotes(_strip_inline_comment(s2[2:]).strip()))
                    j += 1
                else:
                    break
            fields[key] = items if items else None
            field_line[key] = line_no
            i = j if items else i + 1
            continue
        if val.startswith("["):
            fields[key] = _parse_inline_list(val)
        else:
            fields[key] = _parse_scalar(val)
        field_line[key] = line_no
        i += 1
    return fields, field_line, None


# ---------------------------------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------------------------------

CHECKPOINT_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-.+\.md$")
# NNNN-kebab (4-digit then dash then non-date). The `ADR-` prefix is OPTIONAL: the canonical authored
# form is the unprefixed `NNNN-slug.md` (CONVENTIONS §5), but a natural adopter choice — carrying the
# `ADR-` in the filename too — is ALSO recognized as an ADR so the ADR-class rules (4-7, 10) actually
# run on it instead of silently no-op'ing. Rule 16 (advisory, WARN) nudges those back toward canonical.
ADR_NAME_RE = re.compile(r"^(?:ADR-)?\d{4}-[a-z0-9].*\.md$")
# Just the prefixed variant, used by the rule-16 convergence advisory.
ADR_PREFIXED_NAME_RE = re.compile(r"^ADR-\d{4}-[a-z0-9].*\.md$")
DATE_PREFIX_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def rel(path, root):
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def is_template(path, fields):
    name = os.path.basename(path)
    if name.endswith(".template.md"):
        return True
    parts = path.replace("\\", "/").split("/")
    if "templates" in parts:
        return True
    if fields and fields.get("provenance") == "kit-template":
        return True
    return False


def is_adr(path):
    name = os.path.basename(path)
    if name == "index.md" or name.endswith(".template.md"):
        return False
    return os.path.basename(os.path.dirname(path)) == "decisions" and bool(ADR_NAME_RE.match(name))


def parent_dir_name(path):
    return os.path.basename(os.path.dirname(path))


def is_checkpoint(path):
    """A checkpoint is classified by DIRECTORY + SHAPE: it must live directly under checkpoints/ AND carry
    the timestamped filename shape (YYYY-MM-DD-HHMMSS-<slug>.md). A date+HHMMSS-named file elsewhere — an
    audits/ artifact that happens to share the shape, say — is NOT a checkpoint and gets no checkpoint-class
    rules (14). index.md and templates are never checkpoints."""
    name = os.path.basename(path)
    if name == "index.md" or name.endswith(".template.md"):
        return False
    return parent_dir_name(path) == "checkpoints" and bool(CHECKPOINT_NAME_RE.match(name))


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


# ---------------------------------------------------------------------------------------------------
# Per-doc checks (rules 1–12, 14, 15)
# ---------------------------------------------------------------------------------------------------

def find_section(body, heading_words):
    """Locate a '## Heading' (case-insensitive prefix). Return (found, non_empty, heading_line_idx)."""
    lines = body.split("\n")
    pat = re.compile(r"^#{2,6}\s+" + re.escape(heading_words), re.IGNORECASE)
    for i, ln in enumerate(lines):
        if pat.match(ln.strip()):
            for j in range(i + 1, len(lines)):
                if re.match(r"^#{1,6}\s", lines[j]):
                    break
                s = lines[j].strip()
                if not s or s.startswith("<!--") or s.startswith("-->"):
                    continue
                return True, True, i
            return True, False, i
    return False, False, -1


def parse_date(s):
    if not isinstance(s, str):
        return None
    try:
        return datetime.datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def scan_content_dirs_for_slug(slug, root):
    """Root-relative dirs (sorted) that contain `<slug>.md`, scanning the managed content dirs only.

    Last-resort rule-8 resolution for a BARE slug (no '/', no '.md', no typed-ID prefix) that names a doc
    living in some content dir other than the referring doc's own dir (or root). One hit resolves; more
    than one is reported as ambiguous by the caller. `managed_dirs` is the same content-dir set rule 13
    indexes (excludes now/, templates/, dot-dirs), so the scan never reaches VCS internals or kit
    scaffolding. (`managed_dirs` is defined further down; Python resolves it at call time.)
    """
    target = slug + ".md"
    hits = []
    for d in managed_dirs(root):
        if os.path.isfile(os.path.join(d, target)):
            hits.append(rel(d, root))
    return sorted(hits)


def resolve_reference(ref, doc_path, root, extra_id_re=None):
    """Resolve a reference token. Returns (resolved, detail).

    `resolved` is True when the token resolves to an existing file (or is a non-file typed ID). `detail`
    is None for the ordinary unresolved case (the caller supplies its generic "does not resolve" message)
    and a short clause (e.g. "ambiguous across N content dirs (...)") when the failure needs a specific
    message.

    `extra_id_re`, when supplied, is a compiled regex of caller-declared LOCAL typed-ID prefixes
    (--extra-id-prefixes); a token matching it is treated as a resolvable non-file ledger id, exactly like
    the canonical OQ-/WU-/… set. This is the upgrade-safe seam for spines the kit deliberately does not
    canonize — a flag in the caller's wiring, not an edit to (or fork of) this linter.
    """
    if not isinstance(ref, str):
        return True, None
    ref = ref.strip()
    if ref == "" or ref.lower() in ("null", "~", "none", "[]"):
        return True, None
    doc_dir = os.path.dirname(doc_path)
    # Path-qualified reference (contains '/', or already carries a .md extension). Try the literal path
    # first, then — for a path-qualified but EXTENSIONLESS ref (e.g. `decisions/0001-foo`) — the same path
    # with `.md` appended; each relative to the doc dir, then the root. This mirrors the bare-stem fallback
    # below so a related-ref written without its extension still resolves.
    if "/" in ref or ref.endswith(".md"):
        cands = [ref] if ref.endswith(".md") else [ref, ref + ".md"]
        for base in (doc_dir, root):
            for c in cands:
                if os.path.isfile(os.path.normpath(os.path.join(base, c))):
                    return True, None
        return False, None
    # ADR-NNNN -> decisions/NNNN-*.md OR decisions/ADR-NNNN-*.md (adopters who keep the prefix on disk).
    m = re.match(r"^ADR-(\d{3,4})$", ref, re.IGNORECASE)
    if m:
        dec = os.path.join(root, "decisions")
        if not os.path.isdir(dec):
            return False, None
        prefix = m.group(1)
        ok = any(
            (fn.startswith(prefix + "-") or fn.startswith("ADR-" + prefix + "-"))
            and fn.endswith(".md")
            for fn in os.listdir(dec)
        )
        return ok, None
    # Other typed IDs (OQ/WU/LP/…) are ledger rows, not files — treat as resolvable. Caller-declared local
    # spines (--extra-id-prefixes) get the same treatment via extra_id_re.
    if ID_PREFIX_RE.match(ref):
        return True, None
    if extra_id_re is not None and extra_id_re.match(ref):
        return True, None
    # Bare stem -> <doc_dir>/<ref>.md or <root>/<ref>.md
    for base in (doc_dir, root):
        if os.path.isfile(os.path.join(base, ref + ".md")):
            return True, None
    # LAST resort — a bare slug that did not resolve in its own dir or root: scan the managed content dirs
    # for `<slug>.md`. A single unambiguous hit resolves; multiple hits keep the FAIL but report the
    # ambiguity so the author can qualify the ref with a path. Kept last so typed ids and path-qualified
    # refs retain their existing semantics.
    hits = scan_content_dirs_for_slug(ref, root)
    if len(hits) == 1:
        return True, None
    if len(hits) > 1:
        return False, ("ambiguous across %d content dirs (%s) — qualify it with a path"
                       % (len(hits), ", ".join(hits)))
    return False, None


def check_document(path, root, findings, now_date, warn_days, fail_days, workplan_wus,
                   extra_id_re=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        findings.append(Finding(1, FAIL, rel(path, root), 1, "cannot read file: %s" % exc))
        return

    fields, field_line, err = parse_frontmatter(text)

    # Rule 1 — front-matter present + parseable.
    if err is not None:
        findings.append(Finding(1, FAIL, rel(path, root), 1, err))
        return  # nothing else is checkable without front-matter
    field_line = field_line or {}
    rpath = rel(path, root)
    body = text.split("---", 2)[-1] if text.count("---") >= 2 else text

    templated = is_template(path, fields)

    # Rule 2 — required fields populated.
    for f in REQUIRED_FIELDS:
        if f not in fields or fields.get(f) in (None, "", []):
            findings.append(Finding(2, FAIL, rpath, field_line.get(f, 1),
                                    "missing/empty required field '%s'" % f))

    # Rule 3 — provenance in allowed set.
    prov = fields.get("provenance")
    if nonempty_str(prov) and prov not in ALLOWED_PROVENANCE:
        findings.append(Finding(3, FAIL, rpath, field_line.get("provenance", 1),
                                "provenance '%s' not in allowed set %s"
                                % (prov, sorted(ALLOWED_PROVENANCE))))

    # Rule 11 — date-prefixed filename matches a real date.
    name = os.path.basename(path)
    dm = DATE_PREFIX_RE.match(name)
    if dm:
        y, mo, d = dm.groups()
        try:
            datetime.date(int(y), int(mo), int(d))
        except ValueError:
            findings.append(Finding(11, FAIL, rpath, 1,
                                    "filename date prefix '%s-%s-%s' is not a valid date"
                                    % (y, mo, d)))
        if parent_dir_name(path) == "checkpoints" and not CHECKPOINT_NAME_RE.match(name):
            findings.append(Finding(11, FAIL, rpath, 1,
                                    "checkpoint filename must match YYYY-MM-DD-HHMMSS-<slug>.md"))

    # Rule 9 — file path matches category (ADR placement). Checkpoints are classified by DIRECTORY + shape,
    # not shape alone: a date+HHMMSS-named file OUTSIDE checkpoints/ (e.g. an audits/ artifact that happens
    # to share the timestamped filename shape) is NOT a checkpoint, so it gets no "misplaced checkpoint"
    # finding — the shape is genuinely ambiguous and cannot distinguish a stray checkpoint from a same-named
    # audit record. The `not CHECKPOINT_NAME_RE.match(name)` guard also stops such a file being misread as
    # an ADR by the NNNN- prefix it incidentally shares. Only ADR placement is actively checked here.
    if ADR_NAME_RE.match(name) and not CHECKPOINT_NAME_RE.match(name) \
            and name != "index.md" and not name.endswith(".template.md"):
        if parent_dir_name(path) != "decisions":
            findings.append(Finding(9, FAIL, rpath, 1,
                                    "ADR-named file (NNNN-*.md) must live in decisions/, not %s/"
                                    % parent_dir_name(path)))

    # ADR-specific rules (4, 5, 6, 7, 10).
    if is_adr(path):
        status = fields.get("status")
        # Rule 4 — valid status.
        if not nonempty_str(status) or status not in ADR_STATUS:
            findings.append(Finding(4, FAIL, rpath, field_line.get("status", 1),
                                    "ADR status '%s' is missing or not one of %s"
                                    % (status, sorted(ADR_STATUS))))
        # Rule 5 — superseded implies superseded-by.
        if status == "superseded" and not nonempty_str(fields.get("superseded-by")):
            findings.append(Finding(5, FAIL, rpath, field_line.get("superseded-by", 1),
                                    "status: superseded requires a non-null superseded-by"))
        # Rule 6 — pending/deferred implications.
        if status == "pending" and not as_list(fields.get("pending-on")):
            findings.append(Finding(6, FAIL, rpath, field_line.get("pending-on", 1),
                                    "status: pending requires a non-empty pending-on"))
        if status == "deferred" and not nonempty_str(fields.get("deferred-because")):
            findings.append(Finding(6, FAIL, rpath, field_line.get("deferred-because", 1),
                                    "status: deferred requires a non-empty deferred-because"))
        # Rule 7 — non-empty '## Alternatives Considered'.
        found, non_empty, hidx = find_section(body, "Alternatives Considered")
        if not found:
            findings.append(Finding(7, FAIL, rpath, 1,
                                    "missing mandatory '## Alternatives Considered' section (§5)"))
        elif not non_empty:
            findings.append(Finding(7, FAIL, rpath, hidx + 1,
                                    "'## Alternatives Considered' section is empty (§5)"))
        # Rule 10 — accepted ADRs are not llm-draft/llm-autonomous.
        if status == "accepted" and prov in ("llm-draft", "llm-autonomous"):
            findings.append(Finding(10, FAIL, rpath, field_line.get("provenance", 1),
                                    "accepted ADR may not be provenance '%s' (need llm-reviewed/human)"
                                    % prov))

    # Rule 14 — checkpoint integrity. Keyed on is_checkpoint (directory + timestamp shape): only a real
    # checkpoint under checkpoints/ is integrity-checked; a timestamp-shaped file elsewhere is not one.
    if is_checkpoint(path):
        present = set()
        for ln in body.split("\n"):
            m = re.match(r"^\s{0,3}(?:[*_]{0,2})?(\d{1,2})\.\s", ln)
            if m:
                num = int(m.group(1))
                if 1 <= num <= 10:
                    present.add(num)
        missing = [n for n in range(1, 11) if n not in present]
        if missing:
            findings.append(Finding(14, FAIL, rpath, 1,
                                    "checkpoint missing required point(s): %s (§6)"
                                    % ", ".join(str(x) for x in missing)))

    # Rules that assume a fully instantiated tree — skip for kit-shipped scaffolding.
    if templated:
        return

    # Rule 8 — reference fields resolve.
    for fld in REFERENCE_FIELDS:
        for ref in as_list(fields.get(fld)):
            resolved, detail = resolve_reference(ref, path, root, extra_id_re)
            if not resolved:
                if detail:
                    msg = "%s reference '%s' is %s" % (fld, ref, detail)
                else:
                    msg = "%s reference '%s' does not resolve to a file" % (fld, ref)
                findings.append(Finding(8, FAIL, rpath, field_line.get(fld, 1), msg))

    # Rule 15 — work-unit resolves to a WU in now/work-plan.md.
    wu = fields.get("work-unit")
    if nonempty_str(wu):
        if workplan_wus is None:
            findings.append(Finding(15, FAIL, rpath, field_line.get("work-unit", 1),
                                    "work-unit '%s' set but now/work-plan.md not found to resolve it"
                                    % wu))
        elif wu not in workplan_wus:
            findings.append(Finding(15, FAIL, rpath, field_line.get("work-unit", 1),
                                    "work-unit '%s' not found in now/work-plan.md" % wu))

    # Rule 12 — now/ staleness (warn-not-fail; requires --now).
    if now_date is not None:
        parts = os.path.dirname(rpath).replace("\\", "/").split("/")
        if "now" in parts:
            lm = parse_date(fields.get("last-modified"))
            if lm is not None:
                age = (now_date - lm).days
                if age > fail_days:
                    lvl = FAIL if STALENESS_FAILS else WARN
                    findings.append(Finding(12, lvl, rpath, field_line.get("last-modified", 1),
                                            "now/ doc is %dd old (> fail window %dd) — refresh"
                                            % (age, fail_days)))
                elif age > warn_days:
                    findings.append(Finding(12, WARN, rpath, field_line.get("last-modified", 1),
                                            "now/ doc is %dd old (> warn window %dd)"
                                            % (age, warn_days)))


# ---------------------------------------------------------------------------------------------------
# Rule 13 — index completeness (folds in lint-agent-docs-indexes.sh, promoted to FAIL: it is THE
# hook-enforced rule per CONVENTIONS). Managed dirs are the one-level (and one-nested) content dirs
# under root, excluding now/ and templates/, that hold >= 1 non-index, non-template .md.
# ---------------------------------------------------------------------------------------------------

# In-dir references count in two forms (mirrors lint-agent-docs-indexes.sh exactly): a bare
# backtick token `file.md`, or a ledger-table markdown link [label](file.md). Targets containing
# '/' are cross-dir references and are skipped by both patterns.
INDEX_TOKEN_RE = re.compile(r"`([^`/]*\.md)`")
INDEX_LINK_RE = re.compile(r"\]\(([^)/]*\.md)\)")
# HTML comment blocks are stripped BEFORE the token scan: an index seed carries an EXAMPLE comment
# whose illustrative `<name>.md` tokens name files that don't exist yet — counting them would flag a
# phantom entry on a fresh install. A commented-out row is not a live index entry.
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def content_docs(dirpath):
    out = []
    try:
        for fn in os.listdir(dirpath):
            if not fn.endswith(".md"):
                continue
            if fn == "index.md" or fn.endswith(".template.md"):
                continue
            if os.path.isfile(os.path.join(dirpath, fn)):
                out.append(fn)
    except OSError:
        pass
    return out


def managed_dirs(root):
    result = []
    try:
        top = sorted(os.listdir(root))
    except OSError:
        return result
    for base in top:
        # Skip dot-prefixed dirs (.git, .kit-backups, ...) — they hold no managed content docs.
        if base.startswith("."):
            continue
        d = os.path.join(root, base)
        if not os.path.isdir(d):
            continue
        if base in ("now", "templates"):
            continue
        if content_docs(d):
            result.append(d)
        try:
            for sub in sorted(os.listdir(d)):
                if sub.startswith("."):
                    continue
                subd = os.path.join(d, sub)
                if os.path.isdir(subd) and content_docs(subd):
                    result.append(subd)
        except OSError:
            pass
    return result


def check_index_completeness(root, findings):
    for d in managed_dirs(root):
        rd = rel(d, root)
        idx = os.path.join(d, "index.md")
        disk = set(content_docs(d))
        if not os.path.isfile(idx):
            findings.append(Finding(13, FAIL, rd, 1,
                                    "populated content dir has no index.md (%d docs)" % len(disk)))
            continue
        try:
            with open(idx, "r", encoding="utf-8", errors="replace") as fh:
                itext = fh.read()
        except OSError as exc:
            findings.append(Finding(13, FAIL, rel(idx, root), 1, "cannot read index.md: %s" % exc))
            continue
        scan = HTML_COMMENT_RE.sub("", itext)  # drop commented-out example rows before counting
        indexed = set(t for t in INDEX_TOKEN_RE.findall(scan) + INDEX_LINK_RE.findall(scan)
                      if t != "index.md")
        unindexed = sorted(disk - indexed)
        phantom = sorted(indexed - disk)
        if unindexed:
            findings.append(Finding(13, FAIL, rel(idx, root), 1,
                                    "unindexed docs (on disk, not in index): %s"
                                    % ", ".join(unindexed)))
        if phantom:
            findings.append(Finding(13, FAIL, rel(idx, root), 1,
                                    "phantom entries (in index, no such file): %s"
                                    % ", ".join(phantom)))


# ---------------------------------------------------------------------------------------------------
# Rule 16 — ADR-prefix convergence advisory (WARN-only, one finding per run). The linter now RECOGNIZES
# `decisions/ADR-NNNN-slug.md` as a full ADR (ADR_NAME_RE) and RESOLVES `ADR-NNNN` references against it
# (resolve_reference), so a prefixed corpus is fully checked and never phantom-fails. This advisory is the
# gentle counter-pressure: the canonical authored form stays the unprefixed `decisions/NNNN-slug.md`
# (CONVENTIONS §5), so ONE warn per run names that form. It never fails a run (mirrors rule 12 staleness)
# — convergence by nudge, not by forced rename.
# ---------------------------------------------------------------------------------------------------

def check_adr_prefix_advisory(root, findings):
    dec = os.path.join(root, "decisions")
    if not os.path.isdir(dec):
        return
    try:
        prefixed = sorted(fn for fn in os.listdir(dec)
                          if ADR_PREFIXED_NAME_RE.match(fn) and not fn.endswith(".template.md"))
    except OSError:
        return
    if not prefixed:
        return
    shown = ", ".join(prefixed[:3]) + (", …" if len(prefixed) > 3 else "")
    canonical = re.sub(r"(?i)^ADR-", "", prefixed[0])
    findings.append(Finding(
        16, WARN, rel(dec, root), 1,
        "%d ADR file(s) carry the redundant 'ADR-' filename prefix (%s); the canonical authored form is "
        "the unprefixed 'decisions/%s' — rename at leisure (ADR rules and references already work either "
        "way)" % (len(prefixed), shown, canonical)))


# ---------------------------------------------------------------------------------------------------
# work-plan WU harvest (for rule 15)
# ---------------------------------------------------------------------------------------------------

WU_RE = re.compile(r"\bWU-\d{3,4}\b")


def load_adopted_paths(root):
    """Root-relative paths (os.sep) for `<root>/.kit-manifest.json` files[] rows with action == 'adopt'.

    Retro-adopted docs predate the kit and carry no kit front-matter; the SCHEMA_CLASS_RULES are dropped
    for them (they stay subject to rule 13 index completeness). Manifest paths are recorded relative to
    the target REPO ROOT (the parent of --root, e.g. `.agent-docs/reference/foo.md`), so they are mapped
    back to root-relative form to match Finding.path. A missing/malformed manifest yields no exemptions
    and never raises.
    """
    manifest = os.path.join(root, ".kit-manifest.json")
    try:
        with open(manifest, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return set()
    if not isinstance(data, dict):
        return set()
    rows = data.get("files")
    if not isinstance(rows, list):
        return set()
    target_root = os.path.dirname(root)
    adopted = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("action") != "adopt":
            continue
        p = row.get("path")
        if not isinstance(p, str) or not p.strip():
            continue
        abs_p = os.path.normpath(os.path.join(target_root, p))
        try:
            adopted.add(os.path.relpath(abs_p, root))
        except ValueError:
            continue
    return adopted


def load_workplan_wus(root):
    for cand in ("now/work-plan.md", "now/work-plan.template.md"):
        p = os.path.join(root, cand)
        if os.path.isfile(p):
            # A live work-plan resolves WUs; the template is a placeholder and resolves nothing real,
            # so only the instantiated work-plan is authoritative for rule 15.
            if cand.endswith(".template.md"):
                return None
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    return set(WU_RE.findall(fh.read()))
            except OSError:
                return None
    return None


# ---------------------------------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------------------------------

def iter_markdown(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune dot-prefixed subdirectories (.git, .kit-backups, ...) so VCS internals and kit backups
        # living under the root are never linted. The root itself (.agent-docs) is always kept — os.walk
        # only exposes CHILD dir names here, so a dot-prefixed root is unaffected.
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Doc-schema linter for .agent-docs/ (CONVENTIONS.md lint rules 1-15).")
    ap.add_argument("--root", default=".agent-docs",
                    help="root of the .agent-docs tree to lint (default: .agent-docs)")
    ap.add_argument("--now", default=None,
                    help="reference date YYYY-MM-DD for the now/ staleness check "
                         "(omit to skip staleness; never reads the wall clock)")
    ap.add_argument("--warn-days", type=int, default=7,
                    help="now/ staleness warn threshold in days (default: 7)")
    ap.add_argument("--fail-days", type=int, default=90,
                    help="now/ staleness hard-stale threshold in days (default: 90)")
    ap.add_argument("--extra-id-prefixes", default=None,
                    help="comma-separated LOCAL typed-ID prefixes (e.g. S,U,AR,NS) to ALSO recognize as "
                         "resolvable non-file ledger ids for rule 8 — for spines the kit does not canonize. "
                         "Upgrade-safe: wire it into the caller, no linter edit / keep-local fork needed.")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.stderr.write("lint-docs: --root '%s' is not a directory\n" % args.root)
        return 2

    now_date = None
    if args.now is not None:
        now_date = parse_date(args.now)
        if now_date is None:
            sys.stderr.write("lint-docs: --now '%s' is not YYYY-MM-DD\n" % args.now)
            return 2

    # Caller-declared LOCAL typed-ID prefixes (--extra-id-prefixes) → one compiled alternation, ordered
    # longest-first so a short prefix never swallows a longer one that shares its stem.
    extra_id_re = None
    if args.extra_id_prefixes:
        prefixes = sorted((p.strip() for p in args.extra_id_prefixes.split(",") if p.strip()),
                          key=len, reverse=True)
        if prefixes:
            extra_id_re = re.compile(r"^(?:%s)-" % "|".join(re.escape(p) for p in prefixes),
                                     re.IGNORECASE)

    findings = []
    workplan_wus = load_workplan_wus(root)

    for path in iter_markdown(root):
        check_document(path, root, findings, now_date, args.warn_days, args.fail_days, workplan_wus,
                       extra_id_re)
    check_index_completeness(root, findings)
    check_adr_prefix_advisory(root, findings)

    # Adopt-exemption: retro-adopted docs (manifest `action: adopt`) predate the kit and carry no kit
    # front-matter, so drop their schema-class findings. Rule 13 (index completeness) is NOT in the
    # schema-class set, so adopted docs remain fully subject to it.
    adopted = load_adopted_paths(root)
    if adopted:
        findings = [f for f in findings
                    if not (f.rule in SCHEMA_CLASS_RULES and f.path in adopted)]

    # Report, grouped by rule.
    n_fail = sum(1 for f in findings if f.level == FAIL)
    n_warn = sum(1 for f in findings if f.level == WARN)
    files_seen = sum(1 for _ in iter_markdown(root))

    if not findings:
        print("lint-docs: clean — %d file(s) checked, all schema rules pass." % files_seen)
        return 0

    for rule in sorted(RULES):
        group = [f for f in findings if f.rule == rule]
        if not group:
            continue
        print("== Rule %d: %s ==" % (rule, RULES[rule]))
        for f in sorted(group, key=lambda x: (x.path, x.line)):
            print("  %-4s %s:%d  %s" % (f.level, f.path, f.line, f.msg))
        print("")

    print("lint-docs: %d FAIL, %d WARN across %d file(s)." % (n_fail, n_warn, files_seen))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
