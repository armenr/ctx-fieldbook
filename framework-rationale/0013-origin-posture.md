---
provenance: kit-template
status: accepted
created: 2026-07-10
last-modified: 2026-07-10
related: [0001-in-repo-context-system, 0011-marker-convention, 0012-obligations-ledger]
tags: [meta, framework, origin, self-install, dogfood, release-verification]
---

# ADR-0013 — The origin repo runs the kit from a gitignored operator directory, not an installed payload

> Framework rationale that ships with the kit. Ratifies how the repo that AUTHORS
> the kit runs the kit on itself — a scoped self-install whose state root is a
> gitignored operator directory, not the installed payload tree — and why that
> self-install doubles as the release-verification run.
>
> **For adopters this ADR is informational — there is nothing here to install.** It
> documents the AUTHOR's posture (why the origin repo does NOT install its own payload)
> so the source-repo rule ADR-0011 introduced is recorded as a coherent whole; a repo
> installing the kit is by definition not the origin and takes no action on it.

## Context

Every ordinary repo INSTALLS the kit: the payload copies into `.agent-docs/` +
`.claude/`, and a marker-fenced block is spliced into `CLAUDE.md`. The **origin**
repo — the one that authors `base/{minimal,standard,full}/`, the concierge, and the
`framework-rationale/` ADRs — is categorically different: its payload dirs ARE the
product under authorship, not an installed instance of it.

Installing the kit's own payload into the origin would (a) create a *second*,
confusable `.agent-docs/` tree that is half product-source and half live operator
state — indistinguishable to a grep, a lint, or a `wu-refs` sweep — and (b) write a
kit marker block into the origin's own bootstrap `CLAUDE.md`, which the origin
authors as an *installer's entry point*, not as an install target.

Yet the origin's maintainer still needs the kit's working discipline: cold-start
orientation, handoff/compaction survival, the obligations ledger (ADR-0012) for the
multi-party program the origin actually runs. The maintainer must **dogfood the kit
while authoring it** — without polluting the payload tree that ships.

ADR-0011's "source-repo posture" consequence already ruled the *marker* half (the
origin fences nothing it authored; no kit-owned `CLAUDE.md` block; retro-adoption
inventories only the back-ported subset). This ADR generalizes that ruling to the
whole self-install: WHERE origin state lives, WHICH skills the origin runs, and what
is permanently OUT.

## Alternatives Considered

- **A (chosen) — a gitignored operator directory as the state root; repo-local,
  localized lifecycle skills; NO payload `.agent-docs/` and NO kit marker block in
  the origin `CLAUDE.md`.** Defended in Decision.
- **B (the runner-up) — a full self-install** (copy the payload into the origin's
  own `.agent-docs/` + splice the marker block). Superficially the truest dogfood —
  run exactly what a friend runs. Rejected on the deciding axis: it collides the
  product-under-authorship with a live instance (two `.agent-docs/` trees, one
  authored and one operated, indistinguishable to tooling) and writes a kit marker
  into a bootstrap `CLAUDE.md` the origin authors as an INSTALLER. The dogfood value
  — exercising the real lifecycle skills against real state — is preserved without
  the collision by running the same SKILLS against a state root that sits *outside*
  the payload tree.
- **C — no self-install at all** (author the kit, never run it on yourself).
  Rejected: the kit's whole thesis is dogfooding; a kit whose own maintainer does
  not survive compaction with it has produced no evidence its lifecycle works. The
  origin is the highest-signal test bed — it runs a real multi-party program — and
  refusing to run the kit there forfeits exactly that signal.
- **D — state under the payload but gitignored** (e.g. a `live-state/` dir beneath
  `base/…/`). Rejected: still *inside* the payload tree, so `wu-refs`, the lint, and
  the scrub gate all reach it, and a gitignored path under `base/` is one `git add
  -f` or one glob-widening away from shipping operator state into the public payload.
  The state root must be OUTSIDE the payload tree, not merely gitignored within it.

**Deciding axis:** the origin must **dogfood the kit's DISCIPLINE (skills, ledger,
cold-start) without the kit's PAYLOAD (a second `.agent-docs/`, a marker block)
contaminating the product it authors** — which is a gitignored operator directory
plus repo-local skills, not an installed instance.

**Flip-condition:** if the kit ever ships a first-class "author-mode" profile that
formally separates product-source from live-state within one tree, the origin adopts
THAT instead of the hand-kept operator directory.

## Decision

The origin repo runs the kit as a **scoped self-install**:

- **State root = a gitignored operator directory.** A single top-level directory
  (an operator workspace, listed in `.gitignore`) holds the origin maintainer's live
  state — the handoff, the obligations ledger (ADR-0012), the drift/session record,
  the archives. It is operator-only: it never ships, is never linted as payload, and
  is treated by the scrub gate as a forbidden source of leakage into any draft that
  will ship.
- **Repo-local, LOCALIZE-derived lifecycle skills.** The origin's own
  `.claude/skills/` carries `/orient` and `/handoff` (with ADR-0012's sweep + deltas
  wired in) *specialized to the operator-directory paths and the origin's multi-party
  program* — derived from, but not identical to, the payload skills under `base/`.
  These are the origin's operating tools; they are EXCLUDED from the payload tree.
  The `base/` skills remain the shippable canon.
- **No kit marker block in the origin's bootstrap `CLAUDE.md`** (ADR-0011
  source-repo posture). It is the concierge/installer entry point the origin authors,
  treated as never-kit-owned: the fence step is skipped, and retro-adoption
  inventories only the back-ported subset, marking the origin's own inventions
  UPSTREAM.

**IN scope** for the origin self-install: the localized lifecycle skills, the
gitignored operator-directory state root, the obligations ledger for the drift
program, and the standing-rules discipline the maintainer follows.

**Permanently OUT:** any `.agent-docs/` payload tree in the origin (the payload under
`base/` IS the authored product, not a live instance); any kit marker block in the
origin's bootstrap `CLAUDE.md`; any operator state placed inside the payload tree
(it lives in the gitignored operator directory, outside `base/`).

**Self-install as release-verification (P8).** A release is not cut until a P8
end-to-end run proves the payload actually installs and operates — "built ≠ verified"
is the kit's own IMPL→WIRED bar applied to itself. The origin's scoped self-install
is that verification's **highest-fidelity leg for the discipline**: the maintainer
exercises the real `/orient`, `/handoff`, and obligations-ledger skills against real
multi-party state every session, so the lifecycle is continuously verified against
the live payload rather than only at a release gate. It does NOT, however, exercise
the marker / merge / scaffold path — which a source repo deliberately skips — so a
clean-room throwaway-repo install remains required to verify the *install mechanics*.
The two legs are complementary: the origin self-install proves the discipline runs;
the throwaway install proves the mechanics the origin's source-repo posture bypasses.

## Consequences

- **+** The maintainer dogfoods the kit's discipline every session, so the lifecycle
  skills are continuously exercised against the live payload — the strongest possible
  "does our own product work" signal, and it feeds real material back (ADR-0012 is
  itself dogfood-derived).
- **+** No product/state collision: `.agent-docs/` has one meaning in the origin
  (authored payload), operator state sits cleanly outside the payload tree, and there
  is no stray marker block — so grep, lint, and scrub stay unambiguous.
- **+** The source-repo posture (ADR-0011) generalizes from a marker-only footnote to
  a coherent whole-repo rule.
- **−** The origin's lifecycle skills are LOCALIZED, so they can drift from the
  payload canon; they must be re-derived from the `base/` skills whenever those change
  or they rot. A localized skill is a maintenance debt, not a free copy.
- **−** The self-install is not a full-fidelity install (it skips the marker / merge /
  scaffold path by design), so it cannot be the SOLE release verification — a
  clean-room throwaway-repo P8 run is still required.
- **−** An operator directory outside version control means the origin's live state
  is not itself backed up by the repo; its durability is the operator's
  responsibility, not the kit's.

## Related

- ADR-0011 (marker convention — the source-repo posture this generalizes) · ADR-0001
  (the in-repo context system — what a normal install lays down, and what the origin
  deliberately does NOT) · ADR-0012 (the obligations ledger the origin self-install
  dogfoods)
- The concierge install path (what a friend runs) · the ship / release procedure (the
  P8 verify gate) · `standing-rules-core.md` (the discipline the origin follows
  without an installed payload)
</content>
