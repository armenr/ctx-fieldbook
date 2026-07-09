---
provenance: kit-template
status: accepted
created: 2026-07-09
last-modified: 2026-07-09
related: [0001-in-repo-context-system]
tags: [meta, framework, install, markers, merge]
---

# ADR-0011 — One marker convention: `kit:start (fieldbook <kit-version>)` / `kit:end`

> Framework rationale that ships with the kit. Ratifies the single CLAUDE.md
> marker-block convention every install, upgrade, repair, and uninstall must
> agree on — and records why two conventions briefly coexisted.

## Context

The kit splices its contribution into a colleague's existing `CLAUDE.md` as a
marker-fenced block, and every later lifecycle operation (upgrade replaces the
block body; uninstall deletes exactly the block) must find the same fence the
install wrote. The 0.1.0 payload accidentally shipped **two** conventions —
`kit:start`/`kit:end` in the install/merge path and `fieldbook:begin`/`fieldbook:end`
in the uninstall/upgrade path (plus a third stray variant in a template comment) —
so an uninstall following its own document could not find the block an install
had written. A fleet audit surfaced the schism; this ADR records the ruling that
reconciled it.

## Alternatives Considered

- **A (chosen) — `<!-- kit:start (fieldbook <kit-version>) -->` … `<!-- kit:end -->`.**
  The version stamp rides inside the start marker, so the block self-identifies
  which kit rev wrote it; lifecycle operations match on the `kit:start` prefix
  (regex across versions), never on an exact one-version string. This was the
  convention `merge-strategy.md` — the most detailed statement of the merge
  contract — already specified, and the one `merge-tool.py` implements.
- **B — `fieldbook:begin` / `fieldbook:end`.** Rejected: carried no version
  stamp (upgrades cannot tell which rev wrote the block without consulting the
  manifest), and product-named markers age badly if the kit is ever renamed;
  the generic `kit:` prefix plus a parenthesized product+version stamp keeps
  identification without coupling the seam's grammar to the product name.
- **C — no markers; manifest-recorded byte ranges.** Rejected: offsets rot the
  moment the colleague edits their own file; a textual fence survives
  surrounding edits by construction.

**Deciding axis:** every lifecycle operation must find the same seam, across
versions, in a file the colleague freely edits. **Flip-condition:** if a host
platform ever strips HTML comments from `CLAUDE.md`, the fence grammar must be
revisited — the *one-convention* ruling itself stands regardless of grammar.

## Decision

One convention everywhere: `<!-- kit:start (fieldbook <kit-version>) -->` …
`<!-- kit:end -->`. Matching is by `kit:start` prefix regex across versions.
Foreign marker blocks (any non-kit `begin`/`end` pair) are somebody else's
managed seam: preserved byte-verbatim, never merged into, never removed —
the kit block is inserted after them. The manifest's recorded paths remain
authoritative over any pattern matching.

## Consequences

- `merge-strategy.md`, `scaffold-plan.md`, the install/kit-upgrade skills, and
  `uninstall.md` all state the same fence; `merge-tool.py` is the single
  mechanical implementation.
- Installs written under the retired `fieldbook:begin` variant (none are known
  to exist) would be handled by kit-upgrade's retro-adoption branch, which
  classifies unrecognized-but-kit-shaped blocks for operator adjudication
  rather than pattern-matching them blind.
