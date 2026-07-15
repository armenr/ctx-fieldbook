---
name: truecost
description: Measure how long work in Claude Code ACTUALLY took, from your own session transcripts, and forecast or SCHEDULE the next one from measured history instead of vibes. Use BEFORE GIVING ANY TIME ESTIMATE OR DEADLINE, when someone asks "how long will this take" or "can we ship by <date>", when you want to know how many hours a past project really consumed, when tracking progress mid-build, and (optionally, after `--setup`) when pricing billable work or checking whether an engagement made money. Triggers "how long will X take", "how many hours did X take", "can we do X by <date>", "is that enough time", "what % are we through", "how much time have I spent on X", "what did this cost", "what should I quote", "am I underpricing".
provenance: kit-template
created: 2026-07-14
last-modified: 2026-07-14
---

# /truecost: measure what work actually took, then forecast from that

> **OPTIONAL any-profile module, not wired by default.** Available at Minimal, Standard and
> Full. Installs **globally** (`~/.claude/skills/truecost/`), never into a repo, because it reads
> the transcripts of *every* project. Precondition: some Claude Code history to read. A fresh
> machine has nothing to measure, and the skill will say so rather than invent a number. If you
> never need to answer "how long will this take", skip the module: it adds a skill you will not use.

Every time estimate you have ever been given was a guess. This one is measured.

Claude Code writes a JSONL transcript for every session under
`~/.claude/projects/<slug>/`. Those transcripts are ground truth: timestamped
human prompts, timestamped assistant turns, exact token usage per turn. How long
the work took is recoverable from them. **Do not estimate what you can measure.**

It measures the past AND forecasts the next one. Scheduling and pricing are the
same problem: both die the moment somebody invents a number.

## When to invoke

- **BEFORE giving any time estimate or deadline.** "How long will this take?", "can we ship by
  Friday?", "is that enough time?" This is the headline case, and it is the one people skip.
- Mid-build progress: "what percent are we through?", "how many hours has this eaten?"
- After the fact: "how long did X actually take?", "what did this project cost?"
- Pricing billable work, if you invoice: "what should I quote?", "am I underpricing?", "did this
  engagement make money?" Needs a profile (`--setup`); everything else does not.
- Whenever anyone, including you, starts estimating operator hours without measuring them.

## When NOT to invoke

- **There is no Claude Code history for the work in question.** A forecast with no comparable is a
  guess with a tool's authority on it. Say "no comparable found", say why, and give a range you
  label ESTIMATED. Do not run the tool and quote its silence as a number.
- **The work is mostly outside Claude Code.** Design, meetings, manual QA, deploys and thinking are
  in no transcript. If those dominate, the tool's hours are a fraction of the truth and must not be
  handed over as the total. Add them by hand (`--offline N`) and label them added.
- **Someone wants a number to justify a price already chosen.** That is not measurement.
- Wall-clock questions about subagents. Agents running in parallel while you make coffee is not
  you working, and the tool deliberately refuses to count it.

## Run it

```bash
T=~/.claude/skills/truecost/truecost.py

# ---- MEASURE (the past). Zero config. Works the moment you install it. ----
python3 $T <repo> [<repo>...]     # per-project: active time + tokens by exact model
python3 $T --all                  # portfolio: every repo, active hours, inference spend
python3 $T <repo> --tasks         # per-work-block: time, cost, model, the actual prompt
python3 $T --live                 # LIVE tracker for the session running right now

# ---- FORECAST (the next one). Also zero config. ----
python3 $T --estimate "<the work | other phrasing>"   # what did work LIKE THIS really take?
python3 $T --predict "<task>" --hours N --phase pre-recon|post-recon --repo <r>
python3 $T --settle <id> --actual <h>          # settle it against reality
python3 $T --calibration                       # your MEASURED forecasting bias

# ---- BILLING (optional). Requires a profile. See the last section. ----
python3 $T --setup                # one-time questionnaire, writes your profile
python3 $T <repo> --quote --offline 6   # measured hours -> invoice. ALWAYS set --offline:
                                        # calls, QA, deploys, review are in no transcript.
python3 $T --clients              # client rollup vs what they actually pay
```

Quote overrides, all optional, all one-off: `--offline N`, `--wage N`, `--markup N`
(`0` = break-even), `--currency XXX` (presentation only, it does not move the fee),
`--fx N` (the rate taking `--currency` into USD, when you are quoting in a currency
you do not normally bill in).

Nothing to activate. The skill is user-level, so it is already live in every repo.
Just ask, anywhere: *"how long will this take?"*, *"how many hours has X eaten?"*,
*"can we ship by Friday?"*

**Where your data lives:** `~/.claude/truecost/` (profile, clients, prediction
ledger). Never inside the skill directory, so upgrading the skill cannot clobber
your numbers. Override the location with `TRUECOST_HOME` if you want it somewhere
else.

## STOP. BEFORE YOU GIVE ANY TIME ESTIMATE, READ THIS

**A feature build was estimated at "15-20 h". Recon surfaced more scope than
expected, so the estimate was revised UPWARD to "30-40 h". The measured actual was
~2.5 hours. A ~12x miss, in the direction of alarm.**

That miss was a **UNIT ERROR, not a judgment error.** The estimate was in HUMAN
hours, for work that agents do in parallel. The only unit this tool reports, and
the only unit that means anything here, is **ACTIVE CLAUDE CODE HOURS**.

Four rules. Every one of them exists because it was broken that day.

1. **NEVER estimate before a grounding pass.** Pre-recon, the honest answer is
   *"unbounded until I have read the code."* Not a range. Not a guess with a
   caveat. `--predict --phase pre-recon` will warn you, and the warning is the
   point.

2. **Estimate in ACTIVE CLAUDE CODE HOURS.** State operator hours (calls, QA,
   manual testing, client review, deploys) as a SEPARATE line. Never blend the
   two. Agent fan-out means the coding number is far smaller than it feels, and
   the operator number is usually the one that actually blocks the deadline.

3. **Anchor to a MEASURED comparable, never to a feeling.** Run
   `--estimate "<the work>"` first. It returns the real distribution (p50, p80) of
   your past blocks that looked like this, with their prompts, so you can name
   your comparable out loud: *"like the import-pipeline work last month, measured
   at 7.5 h."*

   **Query it 2-3 ways, not once.** Matching is word overlap, so "add Stripe
   checkout", "payment gateway" and "checkout integration" each reach a different
   slice of history even though they are the same work. You, the model reading
   this, are the semantic layer: rephrase the task in the words its past
   incarnations would have used (the library name, the generic term, the verb the
   user actually types) and pool them in ONE call, separated by pipes:

   ```bash
   python3 $T --estimate "add stripe checkout | payment gateway | checkout integration"
   ```

   Each block scores as its best phrasing and is counted once, so the pooled
   distribution is safe to anchor on. Check the printed `confidence:` line before
   treating the anchor as solid.

4. **NEVER revise an estimate upward out of alarm.** Discovering complexity is not
   evidence about duration. Re-run `--estimate` against the newly understood scope
   and revise on THAT. If you catch yourself inflating a number because the
   problem suddenly feels scary, you are not estimating, you are flinching.

### A block is a TASK, not a PROJECT

`--estimate` reports the distribution of **work blocks**: bursts of work split by
an idle gap over 15 minutes. One block is roughly one task. A feature is N blocks:
a mid-sized one might be ~15 blocks spread across two days.

So the method is: **decompose the work into the blocks you expect, then multiply
by the p50.** Use the p80 if the work is on a money path, where adversarial review
rounds are real and they are not free. Do NOT read a p50 of 0.35 h as "the whole
feature takes 20 minutes."

### Close the loop, or you learn nothing

An estimate you never settle is a guess you get to repeat forever.

```bash
python3 $T --predict "widget import job" --hours 1.5 --phase post-recon --repo myrepo
#   ... do the work ...
python3 $T --settle e1234567890 --actual 1.2
python3 $T --calibration     # -> "post-recon (n=6) median ratio 0.31 -> you OVER by 3.2x"
```

`--predict` prints the id to settle with. Below three settled estimates in a phase,
`--calibration` shows the rows but refuses to prescribe a multiplier: two data
points is an anecdote, and prescribing off an anecdote is the same guessing this
tool exists to stop.

`--calibration` prints your **measured multiplier, split by phase**, because
pre-recon and post-recon estimates fail differently and by different magnitudes.
**Apply the correction for the matching phase. Do not re-derive it by feel.**
Re-deriving it by feel is the original bug.

## Day one: "No comparable found" is the tool WORKING

`--estimate` is a reference-class forecaster over **your own** transcript history.
On a fresh install, with little history, it will often say:

```
  No comparable found. You are estimating BLIND.
  Say so out loud rather than inventing a number.
```

**That is not a bug. That is the tool refusing to lie to you.** It is telling you
the truth about your evidence, which is that you have none yet for this kind of
work. Say exactly that to whoever asked, instead of manufacturing a range.

The tool gets sharper every week you keep using Claude Code, because your reference
class grows. Everything else (active time, work blocks, token spend, `--live`)
works from the first session.

## What it reports, and what each number means

| Metric | Meaning |
|---|---|
| **time in Claude Code** | Idle-thresholded active time across main-thread events: gaps under 15 min are work, gaps over 15 min contribute nothing at all. **This is the number to trust.** |
| **work blocks** | The bursts that time is made of, split by those idle gaps. One block is roughly one task. |
| **token cost** | API-equivalent value of the inference consumed. On a subscription this is not marginal cash. See the token section. |

That is the whole list. If you want anything else, derive it and say that you did.

### Two metrics OTHER tools report, and both of them lie

This tool does not compute either of these. That is deliberate, and it is worth
knowing why, because you will meet them elsewhere and they are seductive.

**A "read-and-type gap" is not attention time.** Count only the capped gap in front
of each typed prompt and the total is bounded by `prompt count x cap`, so it
structurally cannot exceed a few hours no matter how long the project really took.
Measured against a project that truly took about a month, that method read roughly
a fifth of the real hours, and it turned that undercount into a realized hourly
rate five times higher than the truth. The fake number looked great, which is why
nobody questioned it. Do not price on it. Do not schedule on it.

**Session span is not work time either.** Claude Code sessions stay open for days:
single "sessions" of 100+ hours are routine, and one really did span 215 hours.
That is a terminal left running overnight, not a human working.

### The honest limit of the whole tool

**It only sees Claude Code.** Client calls, browser testing, deploys, design,
reading the brief, the thinking you do in the shower: none of it is in any
transcript. **Real delivery hours are ALWAYS higher than what this reports.** Add
them by hand, label them as added, and never present the tool's number as the
total.

### Sanity-check it against a project you remember

Before you trust this on anything that matters, spend five minutes calibrating it
against your own memory:

1. Pick two projects whose real duration you actually remember, one short and one
   long.
2. Run `python3 $T <repo>` on each and read the **time in Claude Code** line.
3. Ask yourself out loud what you would have told a friend that project took.

You are looking for agreement in the right units, not agreement to the hour. A repo
that reads 12 h and that you remember as "a couple of long afternoons" is the tool
telling the truth. So is a repo that reads 40 h and that you remember as "most of a
quarter, on and off", because calendar time is not hands-on-keyboard time and an
intermittent project is mostly gaps. What you are checking is that the tool is
**not off by an order of magnitude**, and that the difference between measured
Claude Code hours and your lived experience is explained by work the transcripts
cannot see (rule above), not by a broken measurement.

If a number feels absurd, run `--tasks` on that repo. The block list, with the
actual prompt that started each block, will usually show you why in about ten
seconds.

## Token spend

`truecost.py <repo>` prices every assistant turn against the public API rate card,
per exact model, including cache reads and cache writes. Subagent (sidechain) turns
burn real tokens, so they are counted for spend, but they are **not** counted as
active time. The machine working in parallel is not you working.

**On a subscription, marginal token cost is not cash. But the subscription IS.**
If you are on a Claude Max or Pro plan, the tokens are prepaid. The API-equivalent
figure the tool prints is a *value*, not an invoice line.

- Do NOT tell a client "the tokens cost $1,200." They did not. Nothing left your
  bank account when that inference ran.
- Do NOT say "tokens are free." They are not. They are **prepaid**.

The right treatment: your subscription is a real fixed overhead shared across every
project you touched that month. Allocate it by inference share:

```
months x (subscription $/mo) x (this project's API-equiv $ / total API-equiv $ that month)
```

On a month of real work that lands in the tens of dollars, not the hundreds. Real,
and small. Tools are almost never the reason a project is unprofitable.

---

# BILLING (optional)

**If you never bill anyone for this work, you can stop reading here.** Everything
above works with zero configuration and no numbers about your business.

Billing needs to know things only you know: what you want to earn, what your tools
cost you, what markup you take. So it requires a one-time profile.

```bash
python3 $T --setup       # writes ~/.claude/truecost/profile.json
```

`--quote` and `--clients` **will not run without it**, and they will not fall back
to some default rate card. A shipped default wage would be somebody else's
business asserted as yours, which is exactly the bug this fork exists to kill.

`--setup` asks six things: your currency, your target take-home per hour **worked**
(no default, you have to say it), your monthly tool spend in USD, your default
markup (0 = break-even / family rate), your utilization (it can MEASURE this from
your transcripts, or you can state it, and every report labels which it used as
**MEASURED** or **ASSUMED**), and an FX rate if you do not bill in USD. Re-run
`--setup` any time to update it.

Utilization is the sneakiest number in the whole model. If your report says
`ASSUMED`, treat every rate it derives as provisional until you measure it.

## THE BIG ONE: your own hours are not a cost

If you are a solo operator there is **no payroll**. Your labour does not leave the
bank account. So **multiplying your hours by your rate and calling it "cost to
deliver" is wrong**, and it manufactures fake losses out of thin air.

An earlier version of this very skill did exactly that. It took the measured hours,
valued them at the rate card, called that a "cost", set it against the fee, and
concluded that a project which had banked essentially its entire fee as profit had
**lost money**. It had not. Revenue in, near-zero cash out, profit is the fee. The
rate is your **price**, not your **cost**. Feeding it in on both sides of the
ledger is what invented the loss.

The only real cash costs on a project are:

- third-party invoices (translators, reviewers, contractors, licences)
- fixed overhead (subscriptions, hosting), which is not per-project
- tokens, which are prepaid on a subscription

Everything else is **profit against your time**.

**So your hours are not a cost line. They are a TAKE-HOME RATE and a CAPACITY
limit:**

> fee, minus real cash out, minus this project's share of overhead, divided by
> total hours = what an hour of your life actually earned.

The right question is never *"did this lose money"* (it almost never does). It is:

> **"is that a good return on N hours of a finite life, given the alternatives?"**

That only bites when you are capacity-constrained. If nothing else was queued for
those hours, the fee is pure profit and the "hourly rate" is a comparison, not a
verdict.

## Normalize the currency before you compare anything

Every cost in this tool, every subscription price, and every market comp another
model quotes at you is in **USD**. If you bill in another currency, a fee that
looks big in your head can be materially smaller in USD, and you will overstate
your own rate by exactly the FX gap.

Set the rate in `--setup`, and the tool records the date you set it and warns you
when it goes stale. Before you use any figure anybody hands you, ask which currency
it is in. The corollary is a real lever: quoting a US client in USD is a genuine
uplift on a mental price you formed in a weaker currency.

## The cost model

```
  wage you want per hour WORKED                    from your profile
    / utilization                                  MEASURED or ASSUMED, always labelled
    = wage per BILLABLE hour                       (you work >1 h for every hour you can invoice)
  + fixed stack per month / billable hours per month
  + marginal tokens                                $0 on a subscription (prepaid)
  ---------------------------------------------------------------
  = BREAK-EVEN per billable hour
  + markup                                         profit, fixed-fee overrun, rework, bad debt
  = YOUR RATE
```

Worked example. **These numbers are placeholders. They are not a recommendation
and they are nobody's real economics. Yours come from `--setup`.**

```
  wage target              75/h worked
    / utilization          70%   (ASSUMED)      -> 107.14 per billable hour
  + stack $300/mo / 120 billable h/mo           ->   2.50 per billable hour
  + marginal tokens                             ->   0.00
  ---------------------------------------------------------------
  = BREAK-EVEN                                     109.64 /h
  + 30% markup                                     142.53 /h  <- your rate
```

Look at the shape of that. **The cost is your time. Everything else is a rounding
error** (the tool stack there is under 3% of break-even). The only two levers that
actually move a quote are your **wage target** and your **utilization**.

**Family rate = `--markup 0` = break-even.** You still clear your wage target, you
just take no profit. **Never go below it.** Under break-even you are paying money
for the privilege of working.

## How to price the next project

1. **Measure a comparable past project.** Do not skip this to save five minutes.
2. **Scale the hours** to the new scope, then **add the out-of-Claude-Code work the
   tool cannot see** (calls, QA, deploys, coordination). Budget +30% to +50%.
3. **Convert the price into a take-home rate, not a margin.** `fee / total hours` is
   what an hour of your life earned. Compare that to what you want it to be worth.
   Do NOT compute "profit over cost of labour". See the section above.
4. **Sanity-check three ways, and only trust convergence:**
   - *Cash floor*: real third-party invoices only. Usually small. It is a floor, not
     a target.
   - *Market comp*: what an agency would charge for the same brief. Keep it in the
     proposal as the **comparison**, never as the price.
   - *Value*: what ONE good outcome is worth to the client. If a single new customer
     is worth more to them than the entire build costs, the fee follows the outcome,
     not the hours.
5. **Price where the three converge.** The fee is set by what the outcome is worth,
   not by the hours you happened to spend. A site that takes a business from no
   inbound leads to a steady stream of them is not priced by the hours it took to
   build.

## Recurring costs are the invisible leak

Hosting, deploy platforms, transactional email. If they sit on **your** card, they
are an annuity running the wrong way. A one-off project fee is paid once. The
subscriptions behind it are paid **every month, forever**, and they compound
against a fee that never repeats.

Put every client's infrastructure on the **client's** card, in the client's name.
This is also why you must never be the single point of failure on somebody else's
production stack.

## `clients.json`: a client is not a repo

`--clients` rolls a client up across **all** the repos you work in for them. One
client can easily span three. Without the mapping you undercount every multi-repo
client and their effective rate looks better than it is.

Copy `clients.example.json` to `~/.claude/truecost/clients.json` and edit it. Keep
it current: add every new client, and set `offline_h` for the work the transcripts
cannot see. A client whose `offline_h` is 0 is a client whose hours are wrong.

## Anti-patterns

The rules that keep this honest. Every one of them is a way to turn a measurement back into a
guess while keeping the authority of the tool.

- Do **NOT** present an estimate as a measurement. If you did not run the tool, say ESTIMATED,
  out loud.
- Do **NOT** fold agent wall-clock into attention time. It is nearly free, and it inflates your
  hours.
- Do **NOT** quote token cost to a client as an expense if you are on a subscription. It is
  prepaid, not marginal cash. It is also not free. Both statements are wrong.
- Do **NOT** hand over the tool's hours as the total. The transcripts only cover work done in
  Claude Code. Hand-written code, calls, deploys and client meetings are not in them. Add those
  separately (`--offline N`) and label them as added.
- Do **NOT** let scope grow to fit a price. If a quote has ballooned, check whether the
  deliverables inflated to justify the number rather than the number following the work. That is
  how a modest job becomes a proposal nobody can defend line by line.
- Do **NOT** report utilization without labelling it MEASURED or ASSUMED. An assumed utilization
  is a guess wearing a lab coat.
- Do **NOT** trust a retainer client's verdict without a sanity check. Retainer months are the
  span of your transcripts, which is a proxy for tenure, not tenure (see the README's limitations).
- Do **NOT** auto-commit. The tool reads; you decide what to do about what it says.
- Do **NOT** include secrets, credentials, or regulated / user data in anything you write out of
  this skill. A wage, a client name and a rate are sensitive: they live in `~/.claude/truecost/`,
  outside the repo, and they belong in no commit, no report and no channel. Reference paths.

## Design rationale

**Do not estimate what you can measure.** The transcripts already exist, they are timestamped per
turn, and they carry exact token counts. Every hour argued about in a planning meeting is sitting
on disk, unread. The whole skill is a refusal to guess in the presence of evidence.

**Active time, not wall-clock.** A gap longer than 15 minutes means you left the desk and counts as
zero, not as fifteen minutes. Capping instead of dropping would bill every night, every weekend and
every gap between two projects, which is exactly how a tool starts inventing hours and then
invoicing them. Subagent turns burn real tokens and are counted for spend, but never for time.

**Fail loud, never flatter.** An unknown model is priced at the ceiling of the table and says so.
A bad `--wage` is refused rather than quoted. A missing profile is a hard stop, not a fallback to
somebody else's rate card. The one failure this tool cannot survive is a wrong number stated
calmly, because a wrong number that looks right gets invoiced.

**The honest limit is part of the product.** truecost sees Claude Code and nothing else, so the
real delivery hours are ALWAYS higher than what it reports. The README says so, the reports say
so, and this skill says so. A measurement tool that hides its blind spot is worse than no tool,
because it is believed.

Related: `modules/truecost/README.md` (the full model, the limitations, the client mapping).
