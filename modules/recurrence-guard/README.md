---
provenance: kit-template
created: 2026-07-10
last-modified: 2026-07-10
template-version: 1.0.0
tags: [module, recurrence-guard, enforcement, opt-in]
related: [recurrence-guard.template, standing-rules-core]
---

# Module: recurrence-guard (opt-in)

**Not wired by default.** Enable this only when you have **closed a bug class in
an ADR** — a decision of the form "we will never again write X" — and want that
decision to be *enforced*, not merely remembered. If you have no such decided-and-
banned idiom yet, skip this module; it adds ceremony for no gain until you do.

## The recipe

When an ADR (`decisions/NNNN-...`) closes a bug class, a prose rule is not enough:
it relies on every future author (and every future agent) **remembering** the
rule, which is exactly the failure mode enforcement exists to remove. This module
ships that decision as a **commit-blocking grep-guard**: a small script that
**fails the commit** (exit 1) if the banned idiom reappears at a guarded source
site. The rule then physically cannot lapse — a regression trips the gate in the
same commit that introduces it.

One guard locks **one** bug class:

> one closed bug class = one ADR = one `scripts/<bug-class>-guard.sh`.

You author the guard the same change you accept the ADR, and cite the ADR from the
guard's `FIX_HINT` so a blocked commit finds the rationale.

## The determinism-split doctrine

Not every discipline belongs in a guard. Before you write one, **split the
discipline on the determinism line**:

- The **deterministic** part — "this exact idiom must never appear here" — is what
  a grep-guard can decide mechanically. It goes in the hook, so it cannot be
  skipped.
- The **judgment** part — "is this design actually right?" — a grep cannot decide.
  It stays with a human / an independent reviewer; do **not** fake it with a
  brittle pattern that will false-fire or, worse, silently pass.

Advisory codification (a standing rule, a runbook line) is **necessary but not
sufficient**: it documents the rule but does not enforce it, so it lapses silently
the first time attention is elsewhere. Reach for the guard **proactively** for the
deterministic residue. This module is only for that residue — the kit's home for
the underlying "enforcement > advisory" principle and the non-vacuity bar
("break the guard, watch the control fail for the right reason, restore — a guard
you have never seen fail is not yet a guard") is `rules/standing-rules-core.md`;
this README does not restate it.

## Two hardening techniques

A grep-guard has two silent-failure modes. A guard that has quietly stopped
guarding is worse than none, because the ADR still *reads* as enforced. The
template defends both:

1. **Positive-control sentinel — fail LOUD when a rename strips every matchable
   token.** The banned idiom is spelled out of some symbol / API (`SENTINEL`). If
   that token is renamed, every banned pattern would match nothing *forever* and
   the guard would pass on a tree that no longer even contains the thing it
   guards. So the guard asserts the sentinel exists in the scanned surface
   **before** scanning, and fails loud when it is gone — forcing you to update the
   patterns in the same commit as the rename.

2. **Loud fail-open when the analysis engine is absent.** The portable floor is
   pure grep, which needs nothing. But if you opt into the heavier in-file
   test-block stripping (`STRIP_TEST_BLOCKS=1`), that needs `python3`. If the
   engine is requested but missing, the guard neither blocks every commit (a false
   block) nor silently scans test code as if it were production (a false pass) — it
   **warns loudly and skips (fail-open)**, so the missing dependency is visible and
   gets fixed, rather than the guard degrading into a lie.

## Two honest caveats

- **The drain-down allowlist is kit-designed, not field-proven.** The `is_exempt`
  hook doubles as a way to adopt a guard on a tree that *already* has violations
  you cannot fix in one commit: list the existing sites, block all *new* ones from
  day one, and delete each exemption as you fix it (drain it down to empty). This
  adoption workflow is a kit design, not something the field donors exercised —
  they adopted onto clean trees with empty allowlists. Treat it as a reasonable
  pattern, not a proven one, and prefer a clean adoption when you can.

- **Cross-stack in-file test-block exclusion is unproven beyond one stack.** The
  `STRIP_TEST_BLOCKS` mechanism (blank an inline test module before scanning, so an
  idiom that is legal in test code does not trip the guard) was proven in exactly
  one language's brace-delimited test blocks. Its brace-depth tracker is not known
  to be correct for other stacks' test-block shapes. The **portable floor** is
  therefore **path-exclusion**: keep whole test *directories* out of
  `enumerate_scope()`. Reach for in-file stripping only when a stack genuinely
  interleaves test and production code in one file, and validate it there.

## Install (opt-in)

1. Copy the template to one guard per bug class and make it executable:

   ```sh
   mkdir -p scripts
   cp modules/recurrence-guard/recurrence-guard.template.sh scripts/<bug-class>-guard.sh
   chmod +x scripts/<bug-class>-guard.sh
   ```

2. Open the copy and fill its `CONFIG` block: `BANNED` (the forbidden idiom(s), one
   per line), `SENTINEL` (the positive-control token), `FIX_HINT` (the remediation,
   citing the ADR), `enumerate_scope` (your source files, with test directories
   path-excluded), and — only if you truly need it — `STRIP_TEST_BLOCKS` +
   `TEST_BLOCK_OPEN_RE`. Until `BANNED` is non-empty the guard is an inert no-op, so
   a half-configured copy is safe.

3. **Wire it into the pre-commit gate** (this is the opt-in step — the base
   `.githooks/pre-commit` does NOT call it). Add this just before the final
   `exit "$rc"` in `.githooks/pre-commit`, one block per guard:

   ```sh
   # recurrence-guard (opt-in module): <bug-class> ADR-NNNN regression lock.
   if [ -x scripts/<bug-class>-guard.sh ]; then
     echo "pre-commit: <bug-class>-guard (ADR-NNNN regression lock)"
     bash scripts/<bug-class>-guard.sh || rc=1
   fi
   ```

   (adjust the path if you installed the script elsewhere.) This is the same
   registration form the revisit-ledger module documents.

The guard is **grep-based and offline**, so it is cheap to run on every commit,
and it is a no-op (exit 0) until you configure `BANNED` — copying it before the
idiom is decided costs nothing.

## Verify

The `[ROOT]` argument points the guard at a throwaway fixture tree, so you can
prove it actually blocks before you trust it. Author these three checks the same
change as the guard (this is the "watch the control fail for the right reason"
discipline `standing-rules-core.md` requires of any guard):

```sh
# a) POSITIVE CONTROL fires on an empty tree (sentinel absent) -> non-zero exit.
mkdir -p /tmp/fix-empty && bash scripts/<bug-class>-guard.sh /tmp/fix-empty; echo $?

# b) DETECTOR fires when the banned idiom is planted (include the sentinel token,
#    or the positive control trips first) -> non-zero exit, names the file + fix.
mkdir -p /tmp/fix-bad/src
printf '<a line containing your banned idiom AND the sentinel token>\n' > /tmp/fix-bad/src/f.<ext>
bash scripts/<bug-class>-guard.sh /tmp/fix-bad; echo $?

# c) CLEAN tree (sentinel present, idiom absent) -> "OK", zero exit.
mkdir -p /tmp/fix-ok/src
printf '<a line with the sentinel token but the CORRECT construct>\n' > /tmp/fix-ok/src/f.<ext>
bash scripts/<bug-class>-guard.sh /tmp/fix-ok; echo $?
```

A guard whose detector you have never watched fire is not yet a guard.

## Undo

Remove the guard's block from `.githooks/pre-commit` and delete
`scripts/<bug-class>-guard.sh`. The guard keeps no other state.
