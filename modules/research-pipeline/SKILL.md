---
name: research-pipeline
description: Run a tiered, adversarially-gated research investigation under .agent-docs/research/<R-id>-<slug>/. Codified tiers — 00-landscape → NN-<track> deep-dives → MANDATORY adversarial gate (a clean-context skeptic re-checks decision-critical claims against PRIMARY sources BEFORE synthesis) → synthesis.md (the only Tier-2-loaded surface). Use for any multi-source investigation whose conclusion will feed a decision (an ADR, a build choice, a dependency adoption). Currency-check every decision-critical claim against current-year primary docs, never training data.
provenance: kit-template
created: 2026-07-03
last-modified: 2026-07-03
---

# /research-pipeline — tiered, adversarially-gated investigation

> **OPTIONAL Full-profile module — not wired by default.** This skill assumes the Full-profile
> `research/` directory and the `R-NNNN` id spine (`CONVENTIONS-full-addendum.md` §E). Enable it only if
> you run multi-source investigations whose conclusions feed durable decisions. To install: copy this
> file to `.claude/skills/research-pipeline/SKILL.md`, ensure `.agent-docs/research/` and its `index.md`
> exist, and copy `templates/research-synthesis-template.md` into your `templates/`. If you never do
> decision-gating research, skip the module — it adds ceremony for no gain.

Run a research investigation as a disciplined pipeline that produces ONE durable, cited,
confidence-scored `synthesis.md` — and bakes in the disciplines that make research trustworthy:
**decision-critical claims are re-checked against primary sources by a clean-context skeptic BEFORE
synthesis**, and **findings go to disk or they don't exist** (a conclusion only in conversation is dead
at compaction).

Output lives under `research/<R-id>-<slug>/`, keyed to a work-unit (`WU-NNNN`) and an investigation id
(`R-NNNN`).

## When to invoke

- A conclusion will **feed a decision** — an ADR, a dependency/library adoption, a storage or
  architecture choice, a build-portability call. Research that gates a decision must be adversarially
  checked.
- A question needs **multiple sources reconciled** — a competitive landscape, a version-matrix
  validation, a library/ecosystem evaluation, an external-pattern survey.
- **Currency matters** — "latest stable," EOL/deprecation status, a recommended replacement. Verify
  against the current year's primary docs, never training data.

## When NOT to invoke

- A single-fact lookup answerable from one primary doc — just look it up and cite it (a `memories/`
  claim or a `log.md` line is enough).
- A pure code-comprehension question about THIS repo — that is code-intelligence territory
  (`{{CODE_INTEL_TOOL}}` / LSP / a code-intel sub-agent), not external research.
- When the answer does not gate anything durable — the pipeline's overhead (the adversarial gate) is
  justified by decision-stakes.

## The tiers (codified — one file per tier)

```
research/<R-id>-<slug>/
  00-landscape.md      ← broad survey: the question decomposed, the candidate space, the tracks to drill
  NN-<track>.md        ← parallel deep tracks, ONE file each (01-…, 02-…); the raw per-track findings
  adversarial.md       ← MANDATORY GATE: a clean-context skeptic re-checks decision-critical claims vs PRIMARY sources
  synthesis.md         ← the ONLY Tier-2-loaded surface: verdict + confidence + residual gaps + decisions influenced
```

`synthesis.md` is the surface callers load and reference by `R-id`. The raw tracks stay in the subdir
(Tier-3-ish): discoverable, not bulk-loaded.

## Steps

### 0. Allocate the R-id and scaffold the dir

```bash
pwd && git rev-parse --abbrev-ref HEAD            # cwd-check
ls .agent-docs/research/                          # find the next R-NNNN (sequential, never reused)
mkdir -p ".agent-docs/research/R-NNNN-<slug>"
```

Pick the next `R-NNNN`. Identify the work-unit this research serves (`WU-NNNN` from
`now/work-plan.md`); every tier file carries `work-unit:` in front-matter. Append a
`research | R-NNNN opened — <question>` line to `log.md`.

### 1. Tier 0 — landscape (`00-landscape.md`)

A broad survey that DECOMPOSES the question and names the tracks:

- **The question**, stated precisely, and what decision it gates (cite the WU / the prospective ADR).
- **Decomposition** — the sub-questions; the candidate space (the options / tools / versions in play).
- **The tracks** — the N parallel deep-dives, one per `NN-<track>.md`. Make them independent so they
  can fan out.
- **Decision-critical claims to watch** — flag upfront the claims whose truth gates the decision; these
  are exactly what the adversarial gate will re-check.

Front-matter `tags: [research, landscape]`, `work-unit: WU-NNNN`, `provenance: llm-draft`.

### 2. Tier NN — track deep-dives (`NN-<track>.md`, one file each)

Each track drills one sub-question. **Fan these out in parallel** — they are independent (parallel-first;
sequential only with a real dependency justification). Dispatch each track to the cheapest capable
executor:

- **In-repo / code-intelligence tracks** → `{{CODE_INTEL_TOOL}}` directly (or a code-intelligence
  sub-agent for structural reasoning); LSP fallback; grep only for raw text.
- **External / web tracks** → a web-research sub-agent (or your web-search / deep-research skill, if you
  have one) — competitive landscape, library docs, ecosystem state. Cite current-year primary docs.
- **Language / library-ecosystem evaluation tracks** → a language-expert sub-agent for trade-off
  judgement, grounded in current-year primary docs (`{{PACKAGE_REGISTRY}}` release pages, official docs).

In each `NN-<track>.md`: the finding, **the primary source it came from (URL / doc + current-year
date)**, and a confidence tag. Capture the raw evidence on disk — a quote, a version string, a
manifest / lockfile excerpt, a build-log excerpt, a code-intel query output. *(Findings-to-disk: the
raw evidence is the proof; a summary is not.)* Front-matter `tags: [research, track]`, `work-unit:`.

### 3. Tier — the MANDATORY adversarial gate (`adversarial.md`)

**This stage runs BEFORE synthesis and is non-skippable.** It realizes the adversarial-review discipline
(`CONVENTIONS.md` §7.2): **the reviewer is never the author of the tracks.** Dispatch a **clean-context
verifier sub-agent** that has NOT seen the track reasoning. Hand it ONLY:

- the list of **decision-critical claims** from `00-landscape.md`, and
- the instruction to **independently re-derive each against PRIMARY current-year sources** — not to
  confirm the tracks, but to try to break them.

The verifier writes `adversarial.md`: per decision-critical claim — `confirmed` / `refuted` /
`qualified` / `unresolved`, the primary source it checked against, and what (if anything) the tracks got
wrong, stale, or over-claimed. A claim the verifier cannot independently confirm against a primary
source is downgraded — it does NOT reach `synthesis.md` as settled. Front-matter
`provenance: llm-autonomous` (a clean-context agent's output), `tags: [research, adversarial]`,
`work-unit:`.

> If you skip this gate, you have not run the pipeline — you have written an unaudited literature
> review. The gate is the thing the conclusion's trustworthiness rests on (it kills the failure where
> the author audits their own work).

### 4. Tier — synthesis (`synthesis.md`)

ONLY after the adversarial gate. Reconcile the tracks **as corrected by `adversarial.md`**. Use
`templates/research-synthesis-template.md`:

- **Verdict** — the answer, with an explicit **confidence level** (and what would raise it).
- **Evidence (on-disk, primary-source)** — each load-bearing claim → its primary source (current-year)
  → its adversarial re-check result. Refuted / qualified claims are stated as such, not silently
  dropped.
- **Residual gaps / what we did NOT resolve** — the honest boundary of the investigation.
- **Decisions influenced** — the ADR(s) / WU this feeds; if it should spawn an ADR, name it
  (`→ ADR-NNNN`).

`synthesis.md` is `status: draft` until the operator seals it (`status: sealed`); it is the only tier
callers load. Reference it by `R-id`, not by quoting its body (progressive disclosure, §0).

### 5. Index + journal

- **Update `research/index.md`** (route, don't browse; §7.1) in the SAME change: entry = what the
  investigation holds · *Open when:* · *Carry-away:* (the one-line verdict — traceable to `synthesis.md`,
  never approximated). The index-completeness lint fails on an unindexed research dir.
- **Append to `log.md`**: `## [YYYY-MM-DD] research | R-NNNN <tier> complete — <one line>` per tier
  landed (landscape / tracks / adversarial / synthesis).

### 6. Report

- "/research-pipeline R-NNNN: <verdict> (confidence: <level>) → `research/R-NNNN-<slug>/synthesis.md`"
- One line on the adversarial gate result (claims confirmed / refuted / qualified).
- If it feeds a decision: "Queue ADR-NNNN from this synthesis."

**DO NOT auto-commit.**

## Parallelization

The track tier is parallel-first (independent deep-dives fan out; sequential only with an explicit
dependency). The pipeline tiers themselves are SEQUENTIAL by dependency:
landscape → tracks → **adversarial gate** → synthesis. The gate gates on purpose — synthesis must not
begin before the skeptic has run.

## Anti-patterns

- Do NOT write `synthesis.md` before `adversarial.md` exists — the gate is mandatory.
- Do NOT let a track author also write the adversarial review — clean-context separation is the point
  (`CONVENTIONS.md` §7.2).
- Do NOT cite training-data recall for a decision-critical claim — verify against current-year PRIMARY
  docs.
- Do NOT bulk-load raw tracks into a decision — load `synthesis.md`, reference by `R-id` (progressive
  disclosure).
- Do NOT drop refuted / qualified claims silently — record them; the dead-ends are evidence.
- Do NOT include secrets, credentials, or regulated / user data — reference paths.

## Design rationale

Pipeline tiers + adversarial gate: `CONVENTIONS-full-addendum.md` §E. The clean-context separation
(§7.2) exists because the author of a research track shares its blind spots and has a stake in its
conclusion — an independent skeptic re-deriving each decision-critical claim against a primary source is
the only control that catches a stale or over-claimed finding before it hardens into a decision.
Currency-check-against-primary is the same discipline applied to the ecosystem: training data has a
cutoff, the ecosystem does not. Related: `templates/research-synthesis-template.md`, and `/debrief`
(which verifies a dispatch OUTCOME, where this gate verifies a CLAIM).
