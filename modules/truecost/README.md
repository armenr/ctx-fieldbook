---
provenance: kit-template
created: 2026-07-14
last-modified: 2026-07-14
tags: [module, truecost, estimation, opt-in]
related: [truecost, test_truecost, clients.example]
---

# truecost

**Stop guessing how long Claude Code takes. You already have the receipts.**

Every Claude Code session writes a JSONL transcript to `~/.claude/projects/<slug>/`.
Those transcripts are timestamped, per turn, with exact token usage. That means the
ground truth of how long your work actually took is already sitting on your disk. You
just never read it.

`truecost` reads it.

The headline number is **TIME**: active hours in Claude Code, per project, per task,
with idle stripped out. Once you can measure how long the last thing took, you can
forecast the next one from your own history instead of from a feeling. Token spend is
reported too. Client billing is there if you want it, and completely optional.

---

## What it measures

| Number | What it actually is |
|---|---|
| **active time** | Idle-thresholded working time. Any gap longer than 15 minutes means you left the desk and is not counted. This is the number to trust. |
| **work blocks** | A burst of work separated from the next by a >15 min idle gap. One block is roughly one task. |
| **tokens by model** | Exact token counts per turn, priced at public API rates, split by model. Subagent (sidechain) turns burn real tokens and are counted. |
| **reference-class forecast** | What did work *like this* really take, according to your own past blocks. p50 and p80, with the prompts that started them. |
| **calibration** | Your measured forecasting bias, split by phase. How wrong you are, as a multiplier. |

Subagent turns count for **tokens** but not for **active time**. Agents working in
parallel while you make coffee is not you working. Folding machine wall-clock into
your hours is the fastest way to invent numbers.

## What it CANNOT see

This is the honest limit of the whole tool, and it is not a small one.

**truecost only sees Claude Code.** Client calls, browser testing, deploys, design
work, reading the brief, arguing about scope, thinking in the shower: none of that is
in any transcript. **Your real delivery hours are always higher than what this
reports.** Add them by hand (`--offline N`). Never hand someone the tool's number and
call it the total.

---

## Install

```bash
mkdir -p ~/.claude/skills/truecost
cp -R truecost/ ~/.claude/skills/truecost/
```

(The trailing slashes matter. They copy the *contents* in, so re-running this to
upgrade overwrites the skill in place instead of nesting a copy inside it.)

That is the whole install. It is a **user-level skill**, so it is live in every repo
immediately. There is nothing to activate, nothing to register, no config file to
touch.

From then on you can just ask Claude, in any repo:

> "how long did the checkout work take?"
> "how long will this migration take?"
> "what should I quote for this?"

Or run the script yourself:

```bash
T=~/.claude/skills/truecost/truecost.py
python3 $T --all
```

### Requirements

- Python 3.8 or newer. Standard library only, no `pip install`, no dependencies.
- Claude Code, with some history. The tool measures your transcripts, so the more you
  have used Claude Code, the more it can tell you.

---

## Quickstart: value in 60 seconds

```bash
T=~/.claude/skills/truecost/truecost.py

python3 $T --all                    # every repo you have ever worked in, ranked by active hours
python3 $T myrepo                   # one project: active time + tokens by model
python3 $T myrepo --tasks           # that project split into work blocks, with the prompt that started each
python3 $T --estimate "add stripe checkout"    # what did work like this ACTUALLY take?
```

Matching is word overlap over your own past prompts. If the work went by another
name back then, pool several phrasings in one query and each block still counts
once: `--estimate "add stripe checkout | payment gateway | checkout integration"`.

Nothing above needs a profile, a config file, or a single answered question. It works
the moment you copy the folder in.

---

## Day one: "No comparable found" is the tool working

`--estimate` is a **reference-class forecaster over your own transcript history**. It
does not know anything about software in general. It only knows what *you* have
already done.

So on a fresh install, with little history, it will say:

```
  No comparable found. You are estimating BLIND.
  Say so out loud rather than inventing a number.
```

**That is correct behavior, not a bug.** The tool is refusing to make something up,
which is exactly the failure mode it exists to prevent. It gets better every week you
use Claude Code, because every session you run is another data point in your own
reference class. Give it a month of real work and it will have plenty to say.

---

## The unit that matters

This tool reports **ACTIVE CLAUDE CODE HOURS**. Not human hours. Not wall-clock. If
you estimate in the wrong unit, no amount of careful thinking will save you.

A real, measured miss:

> A feature was estimated at **15 to 20 hours**. A grounding pass surfaced more scope
> than expected, so the estimate was revised **UPWARD to 30 to 40 hours** out of alarm.
> The measured actual was **~2.5 hours**. A ~12x miss.

That was a **unit error, not a judgment error.** The estimate was in HUMAN hours, for
work that agents do in parallel. And nothing recorded the miss, so it taught nobody
anything. Both of those are what this tool fixes.

### Four rules

1. **Never estimate before a grounding pass.** Pre-recon, the honest answer is "I do
   not know until I have read the code." Not a range. Not a guess with a caveat.
   `--predict --phase pre-recon` will warn you, and the warning is the point.

2. **Estimate in active Claude Code hours.** State operator hours (calls, QA, review,
   deploys) as a **separate line**. Never blend them. Agent fan-out means the coding
   number is far smaller than it feels, and the operator number is usually the one
   that actually blocks a deadline.

3. **Anchor to a measured comparable.** Run `--estimate "<the work>"` before you open
   your mouth, pooling 2-3 phrasings with `|` so vocabulary drift cannot hide your own
   history from you. It gives you the p50 and p80 of past work that looked like this,
   with the prompts, so you can name your comparable out loud instead of vibing.

4. **Never revise an estimate upward out of alarm.** Discovering complexity is not
   evidence about duration. Re-run `--estimate` against the newly understood scope and
   revise on **that**. If you are inflating because the problem feels scary, you are
   not estimating, you are flinching.

### A block is a TASK, not a PROJECT

`--estimate` reports the distribution of **work blocks**, and one block is roughly one
task. A whole feature is many blocks.

So the method is: **decompose the work into the blocks you expect, then multiply by the
p50** (use p80 if it is on a money path, where review rounds are real). Do not read a
p50 of 0.35 h and conclude "the whole feature takes 20 minutes."

### Close the loop, or you learn nothing

An estimate you never settle is a guess you get to repeat forever.

```bash
python3 $T --predict "widget import job" --hours 1.5 --phase post-recon --repo myrepo
#   ... do the work ...
python3 $T --settle e1234567890 --actual 1.2      # --predict prints the id
python3 $T --calibration
```

`--calibration` prints your measured multiplier, **split by phase**, because pre-recon
and post-recon estimates fail differently and by different magnitudes. Apply the
correction for the matching phase. Do not re-derive it by feel. Re-deriving it by feel
is the original bug.

---

## Two metrics that will lie to you

truecost computes neither of these. You will meet them elsewhere, and they are
seductive, so it is worth knowing why they are junk.

**1. A "read-and-type gap" is not attention time.** Count only the capped gap in front
of each typed prompt and the total is bounded by `prompt count x idle cap`, so it
structurally cannot exceed a few hours no matter how long the project really took.
Measured against a project that truly took about a month, that method read roughly a
fifth of the real hours, and then turned the undercount into a realized hourly rate
five times higher than reality. Nobody questions a number that flatters them, which is
exactly the danger. Never price on it.

**2. Session span is not work time.** Claude Code sessions stay open for days. Single
"sessions" of 100+ hours are routine, and one really did span **215 hours**. That is a
terminal left running, not a human working.

Active time (main-thread only, gaps over 15 minutes dropped entirely) is the number
that survives contact with reality. It is the only one this tool leads with.

---

## Token spend

Every assistant turn is priced at public API rates, per model, including cache reads
and cache writes. Two things to keep straight:

**On a subscription, marginal token cost is not cash.** But the subscription itself is
a real fixed overhead, shared across every project you touched that month. So:

- Do **not** tell a client "the tokens cost $1,200." They did not. No cash left your
  account when that inference ran.
- Do **not** say "tokens are free." They are **prepaid**.

The honest move is to allocate the subscription by inference share:
`months x subscription price x (this project's token value / all token value that month)`.
That is usually a small number, and it is a real one.

**Normalize currency before comparing anything.** Every price in this tool is USD, and
so is nearly every market comp you will read. If you bill in another currency and
compare a local figure to a USD figure, you will be wrong by tens of percent in
whichever direction hurts most. Set your FX rate in `--setup` and keep it fresh.

---

## If you bill clients (optional)

Everything above works with **zero configuration**. This part does not, and it is
deliberately opt-in.

```bash
python3 $T --setup          # short questionnaire, writes your profile
python3 $T myrepo --quote   # measured hours -> an invoice
python3 $T --clients        # every client rolled up, against what they actually pay
```

`--setup` asks only what you actually know:

1. Your currency.
2. Your **target take-home per hour worked**. There is no default. You have to say it.
3. Your monthly tool and subscription spend, in USD.
4. Your default markup (`0` = break-even, the family rate).
5. Your utilization. The tool will offer to **measure** it from your history, or take a
   number from you. Whichever you choose, every report labels it **MEASURED** or
   **ASSUMED**, so you always know which one you are standing on.
6. Your FX rate to USD, if your currency is not USD. It records the date and warns you
   when it goes stale.

**`--quote` and `--clients` will refuse to run without a profile.** They exit with an
error telling you to run `--setup`. They will never quietly fall back to a default wage
or a default rate card, because shipping you somebody else's economics as a default is
worse than shipping nothing at all.

If you cannot run the questionnaire (CI, a container, a fresh machine), there is a
validated non-interactive path: `python3 $T --setup --from-json profile.json`, or pipe
it in with `--from-json -`. It checks every value before it writes, which hand-writing
the file does not.

Per-run overrides exist for the profile values you set once:

| Override | What it does |
|---|---|
| `--offline N` | Hours worked outside Claude Code. **Always set this.** It is the only way the untracked half of your work reaches the invoice. |
| `--wage N` | A different take-home target for this quote, in your **profile's** currency. |
| `--markup N` | A different markup. `0` is the break-even floor. |
| `--currency XXX` | Present the quote in another currency. **Display only: it does not move the fee.** The price is computed in USD and converted for the reader. |
| `--fx N` | The rate taking `--currency` into USD, for a one-off quote in a currency you do not normally bill in. Without it, an unknown currency is refused rather than guessed. |

### The cost model

```
  the wage you want per hour WORKED
    / your utilization              you work more hours than you can invoice
    = wage per BILLABLE hour
  + your fixed monthly stack
    / billable hours per month      usually under 5% of cost. Tools never matter.
  + marginal tokens                 prepaid on a subscription
  ---------------------------------------------------------------
  = BREAK-EVEN per hour
  + markup                          profit, overrun, rework, bad debt
  = YOUR RATE
```

Worked example with **entirely made-up placeholder numbers**:

```
  wage target                 80 /h worked
    / utilization             70%            -> 114.29 / billable h
  + stack                    250 /mo
    / billable hours         100 /mo         ->   2.50 / h
  ------------------------------------------------------------
  = BREAK-EVEN                              -> 116.79 / h
  + markup                    30%           -> 151.82 / h
```

The only two levers that meaningfully move a quote are your **wage target** and your
**utilization**. The stack is a rounding error. `--markup 0` is the break-even floor:
you still clear your wage target, you just take no profit. Never go below it, because
below break-even you are paying money to work.

### The single most important thing in this README

**YOUR OWN HOURS ARE NOT A COST.**

If you are a solo operator there is no payroll. Your labour does not leave your bank
account. So multiplying your hours by your rate and calling it "cost to deliver" is
**wrong**, and it manufactures fake losses out of thin air.

An early version of this tool did exactly that. It valued a project's measured hours at
the rate card, called that a "cost", set it against the fee, and concluded a
comfortably profitable project had **lost money**. It had not. Revenue was real, cash
out was approximately zero, and the profit was the fee.

Your rate is your **price**, not your **cost**. Your hours are a **take-home rate** and
a **capacity limit**. So the right question is never "did this project lose money" (it
almost never did). The right question is:

> **"Is that a good return on N hours of a finite life, given what else I could have
> done with them?"**

That question only bites when you are capacity constrained. If nothing else was queued
for those hours, the fee is pure profit.

### Two traps worth naming

**Recurring costs are the invisible leak.** Hosting, deploy platforms, transactional
email: if a client's infrastructure sits on **your** card, it is an annuity running the
wrong way. The project fee is paid once. The subscriptions behind it are paid every
month, forever. Put client infrastructure on the **client's** card, in the client's
name. This also stops you being a single point of failure on their production stack.

**Watch for a scope that grew to fit a price.** If a quote has ballooned, check whether
the deliverables inflated to justify the number, rather than the number following the
work. It is a very easy thing to do to yourself by accident.

---

## Client mapping

`--clients` needs to know which repos belong to which client, because one client often
spans several repos and you will undercount them if you look at one at a time.

Copy `clients.example.json` to `~/.claude/truecost/clients.json` and edit it. The
example file documents every field it uses: `repos`, `retainer` or `billed`,
`currency`, `fx_to_usd` (needed whenever a client pays in a currency that is neither
USD nor your own), `markup` (per client, `0` = the family rate), `offline_h`, and the
`internal` list of repos that are real hours but earn nothing.

Two projects in different directories that happen to share a name (say
`~/clients/acme/web` and `~/clients/globex/web`) are **never** summed into one row.
They are reported separately as `acme/web` and `globex/web`, and that is the name to
put in `repos`. Silently merging two clients' hours is how the wrong one gets
invoiced.

---

## Where your data lives

```
~/.claude/truecost/profile.json      your wage, utilization, stack, markup, FX
~/.claude/truecost/clients.json      your client -> repo mapping
~/.claude/truecost/estimates.jsonl   your prediction ledger
```

These are created on demand, **outside** the skill folder, so you can overwrite the
skill on update without losing anything. Override the location with the `TRUECOST_HOME`
environment variable if you want them somewhere else.

## Privacy

The tool reads your **local** Claude Code transcripts and writes to your **local** data
directory. It makes **no network calls of any kind**. It is standard library Python
with no dependencies, so there is nothing else in the process that could. Your profile,
your clients, and your estimates never leave your machine.

The skill folder ships with a `.gitignore` that ignores `profile.json`,
`clients.json`, and `estimates.jsonl` defensively, in case you ever end up running the
tool from inside a repo.

## Limitations, honestly

- **It only sees Claude Code.** Real hours are always higher. This is the big one.
- **Prices go stale.** The `PRICES` table in `truecost.py` is a hand-maintained list of
  public API rates. Update it as models change.
- **`--estimate` matches on words, not meaning.** It scores the overlap between your
  query and the prompts that opened past work blocks. Query it the way you actually
  write prompts and it does well. Query it in vocabulary you never use and it will find
  nothing.
- **A fresh install knows nothing.** No history, no forecast. See the day-one note
  above.
- **Utilization is only as good as its source.** If you told the tool a number instead
  of measuring one, every report will say ASSUMED. Believe it.
- **Unknown models are priced at the most expensive tier in the table.** The fallback
  is derived from `PRICES`, not hardcoded, so it stays true as you add models. The
  tool would rather overstate your spend than quietly understate it.
- **A "session" that never ends is not a project.** Time is only ever counted inside
  15-minute gaps. Everything longer is discarded, so nights, weekends and the months
  between two visits to a repo contribute exactly zero.

## Tests

`test_truecost.py` is a self-contained, stdlib-only regression suite. Run it from the
skill folder (or anywhere):

```
python3 test_truecost.py
```

It runs entirely against synthetic transcripts in temp directories, never reads your
real `~/.claude` data, and leaves nothing behind, not even a `__pycache__`. It pins
the behaviours an edit is most likely to break: the idle rule (a multi-day gap must
contribute ZERO active time, the phantom-hours bug that once inflated measured hours
by ~28%), work-block splitting, the `PRICES` table multipliers and unknown-model
fallback, repo-name disambiguation, estimate pooling, the no-profile gate, quote
arithmetic against hand-computed fees, profile validation, and the prediction ledger
round trip. Run it after any edit to `truecost.py`, especially the `PRICES` table.
