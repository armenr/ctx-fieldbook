#!/usr/bin/env python3
"""
truecost - measure how long Claude Code ACTUALLY takes, from its own transcripts,
then forecast the next one from your own measured history instead of guessing.

  TIME (zero config)
    truecost.py <repo> [<repo>...]     per-project: active time + tokens by model
    truecost.py --all                  portfolio across every repo
    truecost.py <repo> --tasks         per-work-block breakdown
    truecost.py --live                 live tracker for the session running NOW
    truecost.py --estimate "<query>"   reference-class forecast from past blocks
    truecost.py --predict "<task>" --hours N --phase pre-recon|post-recon --repo <r>
    truecost.py --settle <id> --actual <h>
    truecost.py --calibration          your MEASURED forecasting bias

  BILLING (opt-in, needs a profile)
    truecost.py --setup                one-time questionnaire, writes profile.json
    truecost.py --setup --from-json F  same thing, non-interactive and validated
    truecost.py <repo> --quote         measured hours -> invoice
    truecost.py --clients              client rollup vs what they actually pay

Time is ACTIVE time only. A gap longer than IDLE_CAP (15 min) means you left the
desk, and it is not counted. Session span is NOT work time: Claude Code sessions
stay open for days, and a single "session" can span 200+ hours of wall clock.

The transcripts only see Claude Code. Calls, QA, deploys, design and thinking away
from the keyboard are in no transcript. Real hours are ALWAYS higher than what this
reports. Add them with --offline, and never present this number as the total.

Your data (profile, clients, estimate ledger) lives in $TRUECOST_HOME, default
~/.claude/truecost/. It is never written inside the skill directory: an update
overwrites the skill, and your numbers have to survive that.

Stdlib only. Python 3.8+.
"""
import json, sys, glob, os, re, time, argparse
from datetime import datetime
from collections import defaultdict

# --- pricing, USD per 1M tokens. PUBLIC list prices, safe to ship. -------------
# cache write 5m = 1.25x in | cache write 1h = 2x in | cache read = 0.1x in
# KEEP THIS UPDATED. Models ship and prices move; a stale table quietly misprices
# every report. An unrecognised model falls back to DEFAULT_PRICE, which is at
# least as expensive as every row in the table, per component: it deliberately
# overstates rather than flatters.
PRICES = {
    "claude-fable-5":    (10.00, 50.00),
    "claude-opus-4-8":   ( 5.00, 25.00),
    "claude-opus-4-7":   ( 5.00, 25.00),
    "claude-opus-4-5":   ( 5.00, 25.00),
    "claude-opus-4-1":   (15.00, 75.00),
    "claude-sonnet-5":   ( 3.00, 15.00),
    "claude-sonnet-4-6": ( 3.00, 15.00),
    "claude-sonnet-4-5": ( 3.00, 15.00),
    "claude-haiku-4-5":  ( 1.00,  5.00),
}
# Unknown model: price it at the ceiling of the table, COMPONENTWISE. Derived, not
# a literal, so it stays true when you add a pricier model. Never understate
# someone's spend.
#
# It must be componentwise, not max(PRICES.values()): that is a LEXICOGRAPHIC max
# over (in, out) tuples, so the input price alone picks the winner and the output
# price rides along as a tiebreak. Today every row happens to be exactly 5x
# out/in, so the two agree and nothing is wrong. Add one row with a cheap input
# and a dear output, say (8.00, 100.00), and the lexicographic max still returns
# (15.00, 75.00): the fallback would then UNDERSTATE output, the dominant term in
# most turns, while warn_unpriced() cheerfully prints "overstated, never
# flattered". The pair below is at least as expensive as every row, per component,
# which is the promise actually being made. It may correspond to no single row.
def _ceiling(prices):
    return (max(p[0] for p in prices.values()),
            max(p[1] for p in prices.values()))


DEFAULT_PRICE = _ceiling(PRICES)
# Bump this whenever you touch PRICES. It is printed with every cost so the reader
# can judge staleness; the tool works offline and cannot check prices for you.
PRICES_AS_OF = "2026-07-14"
IDLE_CAP = 900.0                # 15 min. Beyond this you left the desk.

HOME = os.path.expanduser("~")
# Claude Code's config dir is relocatable via CLAUDE_CONFIG_DIR. Honour it. Hard-
# coding ~/.claude means a relocated user reads ZERO transcripts and is told, with
# a straight face, that they have no history. A tool that reports nothing must be
# sure it is because there is nothing, not because it looked in the wrong place.
CLAUDE_DIR = os.path.expanduser(
    os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME, ".claude"))
BASE = os.path.join(CLAUDE_DIR, "projects")


# ============================================================ DATA DIR
# Everything the USER owns lives here, never next to the script. TRUECOST_HOME
# makes it overridable, which is also what makes this tool testable.
def data_dir():
    d = os.environ.get("TRUECOST_HOME") or os.path.join(CLAUDE_DIR, "truecost")
    return os.path.expanduser(d)


def data_path(name):
    return os.path.join(data_dir(), name)


def ensure_dir():
    os.makedirs(data_dir(), exist_ok=True)


PROFILE_NAME = "profile.json"
CLIENTS_NAME = "clients.json"
LEDGER_NAME  = "estimates.jsonl"


# ============================================================ ENGINE
_UNPRICED = set()   # model ids that fell through to DEFAULT_PRICE, for the footer


# What may legally trail a price-table key in a real transcript id: a dated
# snapshot ("-20251001"), a context-window tag ("[1m]"), or both. Anything else is
# a DIFFERENT model, not a variant of this one.
_SUFFIX = re.compile(r"^(-\d{8})?(\[[^\]]*\])?$")


def _match_key(model):
    """The PRICES key this model id resolves to, or None if the table has no row.

    Prefix matching needs a BOUNDARY. A bare startswith() lets a future id lexically
    extend an existing key and silently inherit the wrong price: "claude-opus-4-10"
    starts with "claude-opus-4-1", so it would bill at the 4-1 rate AND never reach
    _UNPRICED, because a prefix hit suppresses the warning. That is the same
    quiet-mispricing failure the DEFAULT_PRICE ceiling exists to prevent, except on
    a live path rather than a latent one. So: exact key, or key + a recognised
    suffix. Longest key wins among the survivors.
    """
    m = model or ""
    if m in PRICES:
        return m
    hits = [k for k in PRICES if m.startswith(k) and _SUFFIX.match(m[len(k):])]
    return max(hits, key=len) if hits else None


def _canon(model):
    """The id to GROUP by: the price-table key when there is one, else the raw id.

    totals() must key on this, not on the raw string. Otherwise one model split
    across a dated and an undated id ("claude-opus-4-8" and
    "claude-opus-4-8-20260115") lands as two rows in the per-model table, each with
    a fraction of the turns. The grand total stays right, which is exactly why it
    goes unnoticed.
    """
    return _match_key(model) or (model or "?")


def _rate(model):
    """Exact key first, then longest bounded prefix: transcripts carry dated ids."""
    m = model or ""
    k = _match_key(m)
    if k:
        return PRICES[k]
    if m and m != "?":
        _UNPRICED.add(m)
    return DEFAULT_PRICE


def warn_unpriced():
    """A stale price table must misprice LOUDLY, not quietly."""
    if _UNPRICED:
        print(f"\n  NOT IN THE PRICE TABLE: {', '.join(sorted(_UNPRICED))}.")
        print("  Priced at the table ceiling (overstated, never flattered).")
        print("  Update PRICES at the top of truecost.py with the current list price.")


def _tok(d, k):
    """A token count, treating a present-but-null field as zero.

    `u.get(k, 0)` returns None when the key IS there and holds JSON null, which is
    legal in a transcript and multiplies into a TypeError that takes down the whole
    report. One null field in one turn should not cost you the run.
    """
    return (d.get(k) or 0) if d else 0


def price(u, model):
    pin, pout = _rate(model)
    cc = u.get("cache_creation") or {}
    w5 = _tok(cc, "ephemeral_5m_input_tokens")
    w1 = _tok(cc, "ephemeral_1h_input_tokens")
    if not (w5 or w1):
        w5 = _tok(u, "cache_creation_input_tokens")   # assume 5m: cheaper, never inflates
    return (_tok(u, "input_tokens") * pin / 1e6
            + _tok(u, "cache_read_input_tokens") * pin * .10 / 1e6
            + w5 * pin * 1.25 / 1e6
            + w1 * pin * 2.00 / 1e6
            + _tok(u, "output_tokens") * pout / 1e6)


def load(files):
    """Every timestamped event, with each assistant turn priced by its exact model."""
    ev = []
    for fn in files:
        try:
            lines = open(fn, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = e.get("timestamp")
            if not t:
                continue
            try:
                ts = datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
            except ValueError:
                continue
            typ = e.get("type")
            if typ == "assistant":
                msg = e.get("message") or {}
                m, u = msg.get("model", "?"), msg.get("usage")
                # Sidechain (subagent) turns still burn real tokens: count them.
                # They do NOT count as active time: they run while you wait.
                ev.append(dict(ts=ts, kind="a", model=m, usage=u,
                               cost=price(u, m) if u else 0.0,
                               side=bool(e.get("isSidechain"))))
            elif typ == "user":
                c = (e.get("message") or {}).get("content")
                txt = c if isinstance(c, str) else (
                    " ".join(b.get("text", "") for b in c
                             if isinstance(b, dict) and b.get("type") == "text")
                    if isinstance(c, list) else "")
                ev.append(dict(ts=ts, kind="u", cost=0.0,
                               side=bool(e.get("isSidechain")),
                               typed=e.get("promptSource") in
                                     ("typed", "queued", "suggestion_accepted"),
                               text=" ".join(txt.split())[:90]))
    ev.sort(key=lambda x: x["ts"])
    return ev


def active_seconds(ev):
    """Idle-thresholded active time over main-thread events. Idle is never billed.

    A gap SHORTER than IDLE_CAP is work: you were at the desk, reading or waiting.
    A gap LONGER than IDLE_CAP is not work, and it contributes ZERO. Not the cap.
    Capping it instead of dropping it would bill 15 minutes for every night, every
    weekend and every gap between two projects, which is how a tool ends up
    inventing hours and then invoicing them.
    """
    m = [e for e in ev if not e["side"]]
    gaps = (m[i]["ts"] - m[i - 1]["ts"] for i in range(1, len(m)))
    return sum(g for g in gaps if 0 < g <= IDLE_CAP)


def totals(ev):
    bm = defaultdict(lambda: dict(cost=0.0, out=0, cr=0, cw=0, inp=0, turns=0))
    for e in ev:
        if e["kind"] != "a" or not e["usage"]:
            continue
        # Group by the CANONICAL id, so a dated and an undated form of the same
        # model do not split into two rows that each tell half the truth.
        u, d = e["usage"], bm[_canon(e["model"])]
        d["cost"] += e["cost"]; d["turns"] += 1
        d["inp"] += _tok(u, "input_tokens")
        d["out"] += _tok(u, "output_tokens")
        d["cr"]  += _tok(u, "cache_read_input_tokens")
        cc = u.get("cache_creation") or {}
        d["cw"] += ((_tok(cc, "ephemeral_5m_input_tokens")
                     + _tok(cc, "ephemeral_1h_input_tokens"))
                    or _tok(u, "cache_creation_input_tokens"))
    return bm


def blocks(ev):
    """A work block = a burst of work split by an idle gap. One block ~ one task."""
    m = [e for e in ev if not e["side"]]
    if not m:
        return []
    out, cur = [], [m[0]]
    for i in range(1, len(m)):
        if m[i]["ts"] - m[i - 1]["ts"] > IDLE_CAP:
            out.append(cur); cur = []
        cur.append(m[i])
    out.append(cur)
    side = [e for e in ev if e["side"] and e["kind"] == "a"]
    return [b + [s for s in side if b[0]["ts"] <= s["ts"] <= b[-1]["ts"]] for b in out]


def num(x):
    """Never print a positive divisor as '0': it reads like a bug in your own quote."""
    return f"{x:,.1f}" if 0 < abs(x) < 10 else f"{x:,.0f}"


def fmt_h(s):
    mins = int(round(s / 60.0))          # round, do not truncate: 6600s is 1h 50m
    h, m = divmod(mins, 60)
    return f"{h}h {m:02d}m" if h else f"{mins}m"


# ============================================================ REPO NAMING
# A dir under ~/.claude/projects is the project's cwd with every "/" replaced by
# "-". That encoding is LOSSY: a repo called "my-cool-app" is indistinguishable
# from a path .../my/cool/app. So do not try to parse the slug. In order:
#   1. read the cwd straight out of the transcript (authoritative, layout-free)
#   2. failing that, resolve the slug against the real filesystem, with backtracking
#   3. failing that, strip the home prefix and show what is left
# This works for ~/code, ~/src, ~/work, /opt/whatever. No layout is assumed.
def _peek_cwd(files, max_lines=60):
    for fn in files[:3]:
        try:
            with open(fn, encoding="utf-8", errors="ignore") as fh:
                for i, ln in enumerate(fh):
                    if i >= max_lines:
                        break
                    try:
                        e = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    c = e.get("cwd")
                    if isinstance(c, str) and c.startswith("/"):
                        return c
        except OSError:
            continue
    return None


def _decode_slug(slug):
    """Greedy longest-segment-first walk of the real filesystem, with backtracking."""
    toks = [t for t in slug.split("-") if t]
    if not toks or len(toks) > 16:      # bound the search, it is only a fallback
        return None

    def walk(root, ts):
        if not ts:
            return []
        for i in range(len(ts), 0, -1):
            seg = "-".join(ts[:i])
            p = os.path.join(root, seg)
            if os.path.isdir(p):
                rest = walk(p, ts[i:])
                if rest is not None:
                    return [seg] + rest
        return None

    return walk("/", toks)


def project_cwd(d, files):
    """The working directory a transcript dir belongs to, or None if unrecoverable."""
    cwd = _peek_cwd(files)
    if not cwd:
        segs = _decode_slug(os.path.basename(d))
        cwd = "/" + "/".join(segs) if segs else None
    if not cwd:
        return None
    return os.path.normpath(cwd) or "/"


def _fallback_name(d):
    """The dir is gone and the transcript carried no cwd. Show the slug, but never
    the home prefix and never a username."""
    s = os.path.basename(d)
    hs = HOME.rstrip("/").replace("/", "-")
    if s == hs:
        return "(home)"
    if s.startswith(hs + "-"):
        return s[len(hs) + 1:] or "(home)"
    m = re.match(r"^-(?:Users|home|root)-[^-]+-?(.*)$", s)
    return (m.group(1) if m else s.lstrip("-")) or "(home)"


def _name_at(cwd, depth):
    """Display name for a cwd: its last `depth` path segments."""
    if cwd == "/":
        return "(root)"
    if cwd == HOME.rstrip("/"):
        return "(home)"
    segs = [s for s in cwd.split("/") if s]
    return "/".join(segs[-depth:]) if segs else "(root)"


_MAP = None
_AMBIG = []


def repo_map():
    """display name -> [transcripts].

    Keyed on the project's real working directory, NOT on its basename. Two dirs
    with the SAME cwd (one repo, opened by different paths) merge. Two DIFFERENT
    cwds that happen to share a basename (~/clients/acme/web and
    ~/clients/globex/web) must NOT merge: silently summing two clients' hours into
    one row is how you invoice the wrong one. They are disambiguated instead, as
    acme/web and globex/web.
    """
    global _MAP, _AMBIG
    if _MAP is not None:
        return _MAP
    byc, orphan = {}, {}
    for d in sorted(glob.glob(os.path.join(BASE, "*"))):
        if not os.path.isdir(d):
            continue
        fs = sorted(glob.glob(os.path.join(d, "*.jsonl")))
        if not fs:
            continue
        cwd = project_cwd(d, fs)
        (byc.setdefault(cwd, []) if cwd else
         orphan.setdefault(_fallback_name(d), [])).extend(fs)

    # Name each cwd by its basename, then lengthen only the names that collide.
    depth = {c: 1 for c in byc}
    names = {}
    for _ in range(8):
        names = {c: _name_at(c, depth[c]) for c in byc}
        clash = defaultdict(list)
        for c, n in names.items():
            clash[n].append(c)
        dupes = [cs for n, cs in clash.items() if len(cs) > 1]
        if not dupes:
            break
        for cs in dupes:
            for c in cs:
                depth[c] += 1
    _AMBIG = sorted(n for c, n in names.items() if depth[c] > 1)

    m = {}
    for c, fs in byc.items():
        m.setdefault(names[c], []).extend(fs)
    for n, fs in orphan.items():
        m.setdefault(n, []).extend(fs)
    _MAP = m
    return _MAP


def ambiguous():
    repo_map()
    return list(_AMBIG)


def repos(names, everything=False, quiet=False):
    m = repo_map()
    if everything:
        return dict(m)
    out = {}
    for n in names:
        q = str(n).strip().rstrip("/")
        ql, base = q.lower(), (os.path.basename(q) or q).lower()
        hit = ([k for k in m if k.lower() == ql]
               or [k for k in m if k.lower() == base or k.lower().endswith("/" + base)]
               or [k for k in m if base in k.lower()])
        if len(hit) > 1 and not quiet:
            # Reported separately, never summed. An ambiguous name must not become
            # one invoice.
            print(f"  note: \"{q}\" matches {len(hit)} DIFFERENT working directories:"
                  f" {', '.join(sorted(hit))}")
            print("  they are reported separately. Name one exactly to pick it.")
        for k in hit:
            out[k] = m[k]
    return out


# ============================================================ PROFILE
# The billing layer runs on YOUR numbers or it does not run. There are no shipped
# defaults for wage, utilization, stack or FX: a default rate card is somebody
# else's business asserted as if it were yours.
REQUIRED = ("currency", "wage", "utilization", "billable_h_month", "stack_usd_mo", "markup")


def profile_errors(p):
    """Presence is not enough: a hand-written 0 divides by zero three functions later."""
    if not isinstance(p, dict):
        return ["profile.json is not a JSON object."]
    e = [f"missing: {k}" for k in REQUIRED if p.get(k) is None]
    if e:
        return e

    def num(k):
        try:
            return float(p[k])
        except (TypeError, ValueError):
            return None
    checks = (("wage", lambda v: v > 0, "wage must be > 0"),
              ("utilization", lambda v: 0 < v <= 1, "utilization must be > 0 and <= 1"),
              ("billable_h_month", lambda v: v > 0, "billable_h_month must be > 0"),
              ("stack_usd_mo", lambda v: v >= 0, "stack_usd_mo must be >= 0"),
              ("markup", lambda v: v >= 0, "markup must be >= 0"))
    for k, ok, msg in checks:
        v = num(k)
        if v is None or not ok(v):
            e.append(f"{msg} (got {p.get(k)!r})")
    if str(p.get("currency") or "").upper() != "USD":
        try:
            fx = float(p.get("fx_to_usd") or 0)
        except (TypeError, ValueError):
            fx = 0
        if fx <= 0:
            e.append("currency is not USD, so fx_to_usd must be set and > 0")
    return e


def load_profile(loud=True):
    try:
        with open(data_path(PROFILE_NAME), encoding="utf-8") as f:
            p = json.load(f)
    except OSError:
        return None
    except json.JSONDecodeError:
        print(f"  profile.json at {data_path(PROFILE_NAME)} is not valid JSON.")
        print("  fix it, or re-run: truecost.py --setup")
        return None
    errs = profile_errors(p)
    if errs:
        if loud:
            print(f"\n  profile.json at {data_path(PROFILE_NAME)} is not usable:")
            for x in errs:
                print(f"    - {x}")
            print("  fix it, or re-run: truecost.py --setup")
        return None
    return p


def quote_input_errors(p, wage, markup, offline, fx):
    """The predicates the PROFILE has to pass, applied to the EFFECTIVE values.

    A one-off override is an input like any other. profile_errors() already enforces
    wage > 0 and markup >= 0 on the stored profile, but the overrides used to walk
    straight past it: `--wage 0` did not crash, it printed a confident invoice for
    nothing, and `--markup -1` quietly billed below cost. A wrong number stated
    calmly is this tool's cardinal sin. The check was already written; it was simply
    never pointed at the overrides.
    """
    eff = dict(p)
    if wage is not None:
        eff["wage"] = wage
    if markup is not None:
        eff["markup"] = markup
    errs = profile_errors(eff)
    if offline is not None and offline < 0:
        errs.append(f"--offline must be >= 0 (got {offline!r})")
    if fx is not None and fx <= 0:
        errs.append(f"--fx must be > 0 (got {fx!r})")
    return errs


def refuse_bad_quote_inputs(p, wage, markup, offline, fx):
    """Fail BEFORE any work is printed. A half-report then a refusal reads as a
    partial success, and the whole point is that nothing plausible-looking escapes.
    """
    errs = quote_input_errors(p, wage, markup, offline, fx)
    if not errs:
        return
    print("\n  refusing to quote: these numbers are not usable.")
    for x in errs:
        print(f"    - {x}")
    print("\n  A quote built on a bad input is worse than no quote: it is wrong,")
    print("  and it looks right. Fix the flag, or re-run: truecost.py --setup\n")
    sys.exit(2)


def require_profile(cmd):
    p = load_profile()
    if p:
        return p
    print(f"\n  {cmd} needs YOUR numbers, and there is no profile yet.")
    print(f"  expected: {data_path(PROFILE_NAME)}")
    print("\n  run:  truecost.py --setup")
    print("\n  It will NOT fall back to a default wage, utilization or stack.")
    print("  Shipping someone else's rate card as your default is how bad quotes")
    print("  get made. The time and token layers work fine without a profile.\n")
    sys.exit(2)


def src(p, key, default="ASSUMED"):
    """Provenance of a profile number: MEASURED, STATED or ASSUMED. Never hide it."""
    return p.get(key + "_src", default)


def profile_fx(p):
    """Multiplier taking the PROFILE's currency into USD. Validated > 0 on load."""
    return 1.0 if (p.get("currency") or "USD").upper() == "USD" else float(p["fx_to_usd"])


def fx_to_usd(p, currency, override=None):
    """Multiplier taking `currency` into USD. None means we honestly do not know."""
    if override:
        return float(override)
    if (currency or "USD").upper() == "USD":
        return 1.0
    if (currency or "").upper() == (p.get("currency") or "").upper():
        return float(p.get("fx_to_usd") or 0) or None
    return None


def fx_age_days(p):
    try:
        return (datetime.now() - datetime.strptime(p.get("fx_set_on", ""), "%Y-%m-%d")).days
    except (ValueError, TypeError):
        return None


def fx_line(p, currency, fx, override=False, tail=""):
    if (currency or "USD").upper() == "USD":
        return None
    if override:
        return f"  fx  1 {currency} = {fx:.4f} USD   OVERRIDE (--fx){tail}"
    age = fx_age_days(p)
    stale = "  <- STALE, re-check it" if age is not None and age > 45 else ""
    when = f"STATED {p.get('fx_set_on', '?')}" + (f" ({age}d old)" if age is not None else "")
    return f"  fx  1 {currency} = {fx:.4f} USD   {when}{stale}{tail}"


# ============================================================ SETUP
def _in(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  setup aborted. Nothing written.\n")
        sys.exit(1)


def ask_str(q, default=None):
    tail = f" [{default}]" if default not in (None, "") else ""
    while True:
        v = _in(f"  {q}{tail}: ")
        if v:
            return v
        if default not in (None, ""):
            return default
        print("      needs an answer. There is no sane default for this one.")


def ask_num(q, default=None, lo=None, hi=None):
    while True:
        raw = ask_str(q, None if default is None else f"{default:g}")
        try:
            x = float(str(raw).replace(",", "").replace("$", "").replace("%", "").strip())
        except ValueError:
            print("      numbers only.")
            continue
        if lo is not None and x < lo:
            print(f"      must be at least {lo:g}.")
            continue
        if hi is not None and x > hi:
            print(f"      must be at most {hi:g}.")
            continue
        return x


def ask_yn(q, default=False):
    while True:
        v = _in(f"  {q} [{'Y/n' if default else 'y/N'}]: ").lower()
        if not v:
            return default
        if v in ("y", "yes"):
            return True
        if v in ("n", "no"):
            return False
        print("      y or n.")


def measure_activity(window_days):
    """Active Claude Code hours per repo over a recent window. Measured, not guessed."""
    cut = time.time() - window_days * 86400
    out = {}
    for n, f in repo_map().items():
        ev = [e for e in load(f) if e["ts"] >= cut]
        if not ev:
            continue
        h = active_seconds(ev) / 3600
        if h >= 0.25:
            out[n] = h
    return dict(sorted(out.items(), key=lambda x: -x[1]))


def suggested_billable(rows):
    """Pre-fill the billable list from clients.json, if there is one.

    Repos mapped to a client are billable. Repos on the `internal` list are not:
    they are the real hours that earn nothing, which is exactly what drags
    utilization below 100%. This only pre-fills a default. You can overtype it.
    """
    cfg = load_clients()
    cl = cfg.get("clients") or {}
    internal = (cfg.get("internal") or {}).get("repos") or []
    if not cl and not internal:
        return None
    billable = set()
    for c in cl.values():
        billable |= set(repos(c.get("repos") or [], quiet=True))
    off = set(repos(internal, quiet=True))
    return [i for i, (n, _) in enumerate(rows, 1) if n in billable and n not in off]


def write_profile(prof):
    ensure_dir()
    path = data_path(PROFILE_NAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prof, f, indent=2)
    try:
        os.chmod(path, 0o600)   # your economics are nobody else's business
    except OSError:
        pass
    return path


def setup_from_json(source):
    """Non-interactive profile, VALIDATED. For CI, containers, a new machine.

    The alternative was telling people to hand-write profile.json, which is the one
    path with no validation at all: a stray 0 in utilization used to divide by zero
    inside the invoice.
    """
    try:
        raw = sys.stdin.read() if source == "-" else \
            open(os.path.expanduser(source), encoding="utf-8").read()
        p = json.loads(raw)
    except (OSError, json.JSONDecodeError) as ex:
        print(f"  --from-json could not read {source}: {ex}")
        sys.exit(2)
    errs = profile_errors(p)
    if errs:
        print("  that profile is not usable:")
        for x in errs:
            print(f"    - {x}")
        print(f"  needs: {', '.join(REQUIRED)}"
              " (+ fx_to_usd if currency is not USD). Nothing written.")
        sys.exit(2)
    p.setdefault("version", 1)
    p["currency"] = str(p["currency"]).upper()
    for k in ("wage", "utilization", "billable_h_month", "markup"):
        p.setdefault(k + "_src", "STATED")
    p.setdefault("fx_set_on", datetime.now().strftime("%Y-%m-%d"))
    p["updated_at"] = datetime.now().isoformat(timespec="seconds")
    p.setdefault("created_at", p["updated_at"])
    print(f"\n  profile written: {write_profile(p)}")
    print("  every number in it came from you, and every report will say so.\n")


def r_setup():
    if not sys.stdin.isatty():
        print("  --setup is interactive and stdin is not a terminal.")
        print("  Non-interactive:  truecost.py --setup --from-json profile.json")
        print("                    cat profile.json | truecost.py --setup --from-json -")
        print(f"  It validates before it writes. Target: {data_path(PROFILE_NAME)}")
        sys.exit(2)
    old = load_profile(loud=False) or {}
    print(f"\n{'=' * 74}\n  truecost --setup   (billing layer only. The time layer needs none"
          f" of this.)\n{'=' * 74}")
    print("  Nothing here is shipped with a default. These are YOUR numbers.")
    print(f"  Written to: {data_path(PROFILE_NAME)}\n")

    # 1. currency
    cur = ask_str("1. currency you think and bill in (USD / CAD / EUR / GBP / other)",
                  old.get("currency", "USD")).upper()
    if cur == "OTHER":
        cur = ask_str("   3-letter code").upper()
    cur = re.sub(r"[^A-Z]", "", cur)[:3] or "USD"

    # 2. wage. No default, deliberately: the number has to come out of your mouth.
    print(f"\n2. Target TAKE-HOME per hour WORKED, in {cur}.")
    print("   Not your billed rate. What you want an hour of your life to earn,")
    print("   before markup and before covering idle time.")
    wage = ask_num(f"   {cur} per hour worked", None, lo=0.01)

    # 3. stack
    print("\n3. Monthly tool + subscription spend, in USD.")
    print("   Common ones: Claude Max 20x 200, Max 5x 100, Pro 20, plus whatever")
    print("   else you pay for monthly. It is usually under 5% of your cost, so a")
    print("   round number is fine.")
    items = dict(old.get("stack_items") or {})
    if ask_yn("   itemize it?", default=False):
        items = {}
        print("      name then amount. Blank name when done.")
        while True:
            n = _in("      tool name (blank = done): ")
            if not n:
                break
            items[n] = ask_num(f"      {n} USD/month", 0, lo=0)
        stack = sum(items.values())
        print(f"      -> ${stack:,.0f}/mo")
    else:
        items = {}
        stack = ask_num("   total USD per month", old.get("stack_usd_mo", 200), lo=0)

    # 4. markup
    print("\n4. Default markup on break-even, as a percent.")
    print("   It buys profit, fixed-fee overrun, rework and bad debt. 0 = the")
    print("   family rate: you clear your wage target and take no profit.")
    mk_default = round(float(old.get("markup", 0.30)) * 100)
    mk_raw = _in(f"  percent [{mk_default:g}, ASSUMED if you just hit enter]: ")
    if mk_raw:
        try:
            markup = max(0.0, float(mk_raw.replace("%", "").strip())) / 100.0
            markup_src = "STATED"
        except ValueError:
            markup, markup_src = mk_default / 100.0, "ASSUMED"
            print("      not a number. Using the assumed default.")
    else:
        markup, markup_src = mk_default / 100.0, "ASSUMED"

    # 5. utilization. Measure it or assume it, but SAY WHICH.
    print("\n5. Utilization: the share of the hours you work that you can actually")
    print("   invoice. It is the second-biggest lever on your rate after wage.")
    util = old.get("utilization")
    util_src = old.get("utilization_src", "ASSUMED")
    bh = old.get("billable_h_month")
    bh_src = old.get("billable_h_month_src", "ASSUMED")
    win = int(old.get("utilization_window_days") or 90)
    measured = False
    if ask_yn("   measure it from your Claude Code transcripts?", default=True):
        win = int(ask_num("   window, in days", 90, lo=7, hi=730))
        print("\n   reading transcripts...")
        act = measure_activity(win)
        if not act:
            print("   No activity in that window. Falling back to an ASSUMED value.")
        else:
            rows = list(act.items())[:25]
            hint = suggested_billable(rows)
            for i, (n, h) in enumerate(rows, 1):
                tag = "  <- client" if hint and i in hint else ""
                print(f"     {i:>3}. {n[:34]:<36}{h:>7.1f} h{tag}")
            print("\n   Which of these are BILLABLE (client) work?")
            if hint:
                print(f"   clients.json says: {', '.join(map(str, hint))}."
                      "  Enter accepts that, or type your own.")
            sel = _in("   numbers, comma separated (or 'none'): ").lower()
            picked = set()
            if not sel and hint:
                picked = {i - 1 for i in hint}
            elif sel and sel != "none":
                for tok in re.split(r"[,\s]+", sel):
                    if tok.isdigit() and 1 <= int(tok) <= len(rows):
                        picked.add(int(tok) - 1)
            billable = sum(h for i, (_, h) in enumerate(rows) if i in picked)
            total = sum(act.values())
            if total > 0 and billable > 0:
                util, util_src, measured = billable / total, "MEASURED", True
                months = max(win / 30.44, 0.5)
                bh, bh_src = billable / months, "MEASURED"
                print(f"\n   MEASURED: {billable:.1f} billable h / {total:.1f} total h"
                      f" = {util * 100:.0f}% utilization, over {win}d")
                print(f"   MEASURED: {bh:.1f} billable h/month")
                print("   Honest caveat: this measures Claude Code time ONLY. Calls, QA and")
                print("   admin are in no transcript, so your real utilization is lower.")
            else:
                print("   Nothing marked billable. Falling back to an ASSUMED value.")
    if not measured:
        keep = (util is not None and util_src == "MEASURED"
                and ask_yn(f"   keep the {util * 100:.0f}% you MEASURED before"
                           f" ({bh:.0f} billable h/mo)?", default=True))
        if not keep:
            print("\n   No measurement. Give an honest guess. It will be labelled ASSUMED,")
            print("   and it will stay labelled ASSUMED everywhere it is used.")
            util = ask_num("   percent of worked hours you can invoice",
                           round(float(util or 0.75) * 100), lo=1, hi=100) / 100.0
            util_src = "ASSUMED"
            bh = ask_num("   billable hours you invoice in a typical month", bh or 100, lo=1)
            bh_src = "ASSUMED"

    # 6. FX, only if it matters.
    fx = 1.0
    fx_on = datetime.now().strftime("%Y-%m-%d")
    if cur != "USD":
        print(f"\n6. FX. Token prices, most market comps and most competitor quotes are")
        print(f"   in USD. Compare nothing until it is in one currency.")
        fx = ask_num(f"   1 {cur} = how many USD?", old.get("fx_to_usd") or None, lo=0.000001)
        print(f"   Stored as STATED on {fx_on}. This tool will nag you when it goes stale.")

    prof = dict(
        version=1, currency=cur,
        wage=wage, wage_src="STATED",
        stack_usd_mo=stack, stack_items=items, stack_usd_mo_src="STATED",
        markup=markup, markup_src=markup_src,
        utilization=util, utilization_src=util_src, utilization_window_days=win,
        billable_h_month=bh, billable_h_month_src=bh_src,
        fx_to_usd=fx, fx_set_on=fx_on, fx_src="STATED",
        updated_at=datetime.now().isoformat(timespec="seconds"),
        created_at=old.get("created_at") or datetime.now().isoformat(timespec="seconds"),
    )
    path = write_profile(prof)

    be = wage * fx / util + stack / bh
    print(f"\n{'=' * 74}\n  saved: {path}\n{'=' * 74}")
    print(f"  {'wage':<15}{cur + ' ' + format(wage, ',.0f') + '/h worked':<28}STATED")
    print(f"  {'utilization':<15}{format(util * 100, '.0f') + '%':<28}{util_src}")
    print(f"  {'stack':<15}{'$' + format(stack, ',.0f') + '/mo':<28}STATED")
    print(f"  {'billable h/mo':<15}{num(bh) + ' h':<28}{bh_src}")
    if cur != "USD":
        print(f"  {'fx':<15}{'1 ' + cur + ' = ' + format(fx, '.4f') + ' USD':<28}STATED {fx_on}")
    print(f"  {'markup':<15}{format(markup * 100, '.0f') + '%':<28}{markup_src}")
    print(f"\n  -> break-even ${be:,.2f}/h USD, your rate ${be * (1 + markup):,.2f}/h USD"
          f" ({cur} {be * (1 + markup) / fx:,.0f}/h)")
    print("\n  Re-run --setup any time to update. Now try:  truecost.py <repo> --quote\n")


# ============================================================ CLIENTS
def load_clients():
    try:
        with open(data_path(CLIENTS_NAME), encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}
    except json.JSONDecodeError:
        print(f"  clients.json at {data_path(CLIENTS_NAME)} is not valid JSON. Ignoring it.")
        return {}


def client_files(cfg):
    f = []
    for v in repos(cfg.get("repos", [])).values():
        f += v
    return f


def r_clients(p):
    """Every client, rolled up across repos, against what they actually pay."""
    cfg = load_clients()
    cl = cfg.get("clients") or {}
    if not cl:
        print(f"\n  no clients.json at {data_path(CLIENTS_NAME)}")
        print("  copy clients.example.json there and map each client to its repos.")
        print("  A client can span several repos. Without the map you undercount them.\n")
        return
    pcur = (p["currency"] or "USD").upper()
    pfx = profile_fx(p)
    util, bh, stack = p["utilization"], p["billable_h_month"], p["stack_usd_mo"]
    oh = stack / bh                                  # stack, per billable hour, USD
    wage_usd = p["wage"] * pfx                       # the CONFIGURED wage. Never a literal.
    be_usd = wage_usd / util + oh                    # break-even, USD per billable hour

    print(f"\n{'=' * 106}\n  CLIENTS  (rolled up across repos)\n{'=' * 106}")
    print(f"  {'client':<14}{'repos':>6}{'hours':>8}{'revenue':>14}{'eff rate':>12}"
          f"{'break-even':>12}{'target':>12}{'verdict':>16}")
    unknown_fx = set()
    for name, c in cl.items():
        ev = load(client_files(c))
        if not ev:
            continue
        h = active_seconds(ev) / 3600
        if h < 0.5:
            continue
        h += c.get("offline_h", 0) or 0
        cur = (c.get("currency") or pcur).upper()
        # FX is per CLIENT, because the client pays in the client's currency. The
        # profile rate only helps when the profile is in that same currency.
        fx = c.get("fx_to_usd") or (1.0 if cur == "USD" else (pfx if cur == pcur else None))
        if fx is None:
            unknown_fx.add(cur)
            fx = 1.0
        be_local = be_usd / fx
        # Per-client markup, falling back to the profile default. markup 0 is the
        # family rate: break-even IS the target, and clearing it is healthy.
        mk = c.get("markup")
        mk = p["markup"] if mk is None else float(mk)
        tgt_local = be_local * (1 + mk)

        if c.get("retainer"):
            months = (ev[-1]["ts"] - ev[0]["ts"]) / 86400 / 30.44
            rev = c["retainer"] * max(months, 1.0)
            rate = rev / h
            label = f"{cur} {c['retainer']:,.0f}/mo"
        elif c.get("billed"):
            rev, rate = c["billed"], c["billed"] / h
            label = f"{cur} {c['billed']:,.0f}"
        else:
            rev = rate = 0
            label = "UNBILLED"

        if rate == 0:
            v = "NOT YET BILLED"
        elif rate < be_local * 0.5:
            v = "!! BLEEDING !!"
        elif rate < be_local:
            v = "! below cost !"
        elif rate < tgt_local:
            v = "thin"
        else:
            v = "healthy"
        print(f"  {name[:13]:<14}{len(c.get('repos', [])):>6}{h:>8.1f}{label:>14}"
              f"{cur + ' ' + format(rate, ',.0f') if rate else '-':>12}"
              f"{cur + ' ' + format(be_local, ',.0f'):>12}"
              f"{cur + ' ' + format(tgt_local, ',.0f'):>12}{v:>16}")

    print(f"\n  break-even = wage {pcur} {p['wage']:,.0f}/h [{src(p, 'wage', 'STATED')}]"
          f" / {util * 100:.0f}% utilization [{src(p, 'utilization')}]"
          f" + ${num(stack)}/mo stack over {num(bh)} h/mo [{src(p, 'billable_h_month')}]")
    print(f"  target = break-even + markup (the client's own markup if it sets one,"
          f" else your {p['markup'] * 100:.0f}%).")
    if unknown_fx:
        print(f"  NO FX RATE for {', '.join(sorted(unknown_fx))}: treated as 1.0 = USD."
              f" Set fx_to_usd on those clients.")
    print("  hours EXCLUDE everything outside Claude Code. Set offline_h in clients.json.")
    print("  eff rate is TAKE-HOME per hour, not margin. Your own hours are not a cost.")

    # A repo the map does not claim SILENTLY vanishes from this report, and a
    # vanished repo is a client you forgot to bill. Make the gap loud.
    claimed = set()
    for c in cl.values():
        claimed |= set(repos(c.get("repos", []) or [], quiet=True))
    internal = cfg.get("internal") or {}
    irepos = internal.get("repos", []) if isinstance(internal, dict) else list(internal)
    claimed |= set(repos(irepos or [], quiet=True))
    stray = []
    for n, f in repos([], everything=True).items():
        if n in claimed:
            continue
        h = active_seconds(load(f)) / 3600
        if h >= 2.0:
            stray.append((h, n))
    if stray:
        stray.sort(reverse=True)
        shown = ", ".join(f"{n} ({h:.0f}h)" for h, n in stray[:8])
        more = f" and {len(stray) - 8} more" if len(stray) > 8 else ""
        print(f"\n  UNASSIGNED (2+ h, in no client and not internal): {shown}{more}.")
        print("  File each one in clients.json, as a client or as internal. A repo")
        print("  nobody claims is work nobody invoices.")
    print()


# ============================================================ REPORTS
def r_project(name, ev):
    sec, bm = active_seconds(ev), totals(ev)
    cost = sum(d["cost"] for d in bm.values())
    typed = sum(1 for e in ev if e["kind"] == "u" and e.get("typed") and not e["side"])
    print(f"\n{'=' * 78}\n  {name}\n{'=' * 78}")
    print(f"  ACTIVE TIME (idle >15m excluded)  {fmt_h(sec):>12}  = {sec / 3600:.1f} h")
    print(f"  work blocks {len(blocks(ev))}  |  typed prompts {typed}")
    print(f"\n  {'model':<20}{'turns':>7}{'output':>10}{'cache rd':>11}{'cost':>11}")
    for m, d in sorted(bm.items(), key=lambda x: -x[1]["cost"]):
        print(f"  {m:<20}{d['turns']:>7,}{d['out'] / 1e6:>9.2f}M{d['cr'] / 1e6:>10.1f}M"
              f"{'$' + format(d['cost'], ',.2f'):>11}")
    print(f"  {'':<48}{'TOTAL':>10}{'$' + format(cost, ',.2f'):>11}")
    print(f"  API-equivalent value, at list prices as of {PRICES_AS_OF}. On a")
    print("  subscription this is PREPAID, not marginal cash: do not bill it to a")
    print("  client, and do not call it free.")
    warn_unpriced()
    return sec, cost


def r_tasks(name, ev):
    bl = blocks(ev)
    print(f"\n{'=' * 94}\n  {name}: {len(bl)} work blocks  (a block = a burst of work, "
          f"split by >15m idle)\n{'=' * 94}")
    print(f"  {'started':<16}{'active':>8}{'cost':>9}  {'models':<24}task")
    ts_ = tc = 0
    for b in bl:
        sec = active_seconds([e for e in b if not e["side"]])
        c = sum(e["cost"] for e in b if e["kind"] == "a")
        if sec < 60 and c < 0.05:
            continue
        ms = sorted({e["model"].replace("claude-", "") for e in b
                     if e["kind"] == "a" and e["model"] != "?"})
        lab = next((e["text"] for e in b if e["kind"] == "u" and e.get("typed")
                    and e.get("text")), "(no typed prompt)")
        print(f"  {datetime.fromtimestamp(b[0]['ts']).strftime('%d %b %H:%M'):<16}"
              f"{fmt_h(sec):>8}{'$' + format(c, ',.0f'):>9}  "
              f"{','.join(ms)[:23]:<24}{lab[:42]}")
        ts_ += sec; tc += c
    print(f"  {'-' * 92}\n  {'TOTAL':<16}{fmt_h(ts_):>8}{'$' + format(tc, ',.0f'):>9}")
    hidden = active_seconds(ev) - ts_
    hidden_c = sum(e["cost"] for e in ev if e["kind"] == "a") - tc
    if hidden > 60 or hidden_c > 1:
        print(f"  (+ {fmt_h(hidden)} and ${hidden_c:,.0f} in blocks too small to list"
              f" or in subagents that ran between blocks. The project totals are"
              f" {fmt_h(active_seconds(ev))} and"
              f" ${sum(e['cost'] for e in ev if e['kind'] == 'a'):,.0f}.)")
    print("  One block is one TASK, not one project. A feature is N blocks.\n")


def r_all():
    rows = []
    for n, f in repos([], everything=True).items():
        ev = load(f)
        if not ev:
            continue
        s = active_seconds(ev)
        if s < 1200:
            continue
        rows.append((n, s / 3600, sum(e["cost"] for e in ev if e["kind"] == "a")))
    rows.sort(key=lambda r: -r[1])
    print(f"\n{'=' * 70}\n  PORTFOLIO: every repo, all time\n{'=' * 70}")
    if not rows:
        print("  No repo has 20+ minutes of active time yet. Nothing to show.\n")
        return
    th, tc = sum(r[1] for r in rows), sum(r[2] for r in rows)
    print(f"  {'repo':<30}{'active h':>10}{'inference':>12}{'$/h':>8}")
    for n, h, c in rows:
        print(f"  {n[:29]:<30}{h:>10.1f}{'$' + format(c, ',.0f'):>12}"
              f"{'$' + format(c / h, ',.0f') if h else '-':>8}")
    print(f"  {'-' * 68}\n  {'TOTAL':<30}{th:>10.1f}{'$' + format(tc, ',.0f'):>12}"
          f"{'$' + format(tc / th, ',.0f') if th else '-':>8}")
    p = load_profile(loud=False)
    if p:
        print(f"\n  {len(rows)} repos. Utilization on file: {p['utilization'] * 100:.0f}%"
              f" [{src(p, 'utilization')}].")
    else:
        print(f"\n  {len(rows)} repos. Active Claude Code time only: your real hours are higher.")
    amb = ambiguous()
    if amb:
        print(f"  {len(amb)} projects share a directory name with another and are shown"
              f" with their parent: {', '.join(amb)}.")
    warn_unpriced()
    print()


def live_dir(cwd):
    """The transcript dir for THIS cwd, found the same way every other read is.

    Never derive the dir name from the path. `cwd.replace("/", "-")` assumes the
    slug encodes nothing but the separator, and it does: Claude Code folds "." and
    "_" to "-" as well. So the guess misses for any repo whose path carries one,
    r_live prints "no transcripts", exits 0, and looks exactly like an honest empty
    history. Every other command in this file already resolves the dir by reading
    the cwd recorded INSIDE the transcript (see the REPO NAMING note), which is
    correct under any slug rule the tool does not control. Do the same here.
    """
    for d in sorted(glob.glob(os.path.join(BASE, "*"))):
        if not os.path.isdir(d):
            continue
        fs = sorted(glob.glob(os.path.join(d, "*.jsonl")))
        if fs and _peek_cwd(fs) == cwd:
            return d
    return None


def r_live(poll=5.0):
    """Watch the session running right now. Idle time is never counted."""
    cwd = os.getcwd()
    d = live_dir(cwd)
    if not d:
        print(f"no transcripts for {cwd}")
        return
    print(f"LIVE  {os.path.basename(cwd)}   idle >15m not counted   ctrl-c to stop\n")
    try:
        while True:
            fs = glob.glob(os.path.join(d, "*.jsonl"))
            if fs:
                ev = load([max(fs, key=os.path.getmtime)])
                if ev:
                    sec, bm = active_seconds(ev), totals(ev)
                    cost = sum(x["cost"] for x in bm.values())
                    idle = time.time() - ev[-1]["ts"]
                    mix = "  ".join(
                        f"{m.replace('claude-', '')} ${v['cost']:,.0f}"
                        for m, v in sorted(bm.items(), key=lambda x: -x[1]["cost"])[:3])
                    st = "IDLE  " if idle > IDLE_CAP else "ACTIVE"
                    sys.stdout.write(f"\r  [{st}] active {fmt_h(sec):>7} | "
                                     f"${cost:8,.2f} | {mix} | last {idle:4.0f}s ago   ")
                    sys.stdout.flush()
            time.sleep(poll)
    except KeyboardInterrupt:
        print("\n")


def r_quote(name, sec, offline, p, wage, currency, markup, fx_override):
    """Measured hours -> invoice. Every input is YOURS, and every input is labelled.

    Currency discipline: the fee is computed in USD and only PRESENTED in another
    currency. --currency changes the display, never the price. Re-reading a CAD
    wage as if it were USD would silently move the fee by the whole FX gap, and it
    would move it DOWN for anyone whose currency is stronger than the dollar.
    --wage, like the profile wage it overrides, is in the PROFILE's currency.
    """
    pcur = (p["currency"] or "USD").upper()
    cur = (currency or pcur).upper()          # DISPLAY currency only
    wage_src = "OVERRIDE" if wage is not None else src(p, "wage", "STATED")
    mk_src = "OVERRIDE" if markup is not None else src(p, "markup")
    wage = p["wage"] if wage is None else wage       # denominated in pcur
    markup = p["markup"] if markup is None else markup
    util, bh, stack = p["utilization"], p["billable_h_month"], p["stack_usd_mo"]

    # pcur -> USD. What the wage is actually worth. --fx refreshes it only when it
    # IS a rate for the profile currency; against a third currency it is a display
    # rate and must not touch the wage. A USD profile needs no rate at all, and a
    # USD-to-USD "rate" other than 1.0 would silently rescale the wage: ignore it.
    same = fx_override and cur == pcur and pcur != "USD"
    pfx = float(fx_override) if same else profile_fx(p)
    dfx = fx_to_usd(p, cur, fx_override)      # display currency -> USD
    if dfx is None:
        print(f"\n  No FX rate for {cur}. Your profile is in {pcur}.")
        print("  Pass --fx <rate to USD>, or re-run --setup. Guessing it would be a lie.\n")
        sys.exit(2)

    h = sec / 3600 + offline
    wage_usd = wage * pfx
    wpb = wage_usd / util                   # wage grossed up for the hours you cannot bill
    oh = stack / bh                         # the stack, per billable hour. Always small.
    be = wpb + oh
    rate = be * (1 + markup)
    fee = rate * h

    print(f"\n{'=' * 74}\n  INVOICE: {name}\n{'=' * 74}")
    print(f"  measured in Claude Code  {sec / 3600:8.1f} h   MEASURED")
    print(f"  + outside it (--offline) {offline:8.1f} h   STATED"
          + ("   <- ZERO. Calls? Deploys? Review? QA?" if not offline else ""))
    print(f"  = BILLABLE               {h:8.1f} h\n")
    print(f"  {'wage ' + pcur + ' ' + format(wage, ',.0f') + '/h worked':<34}"
          f"[{wage_src}]")
    pl = fx_line(p, pcur, pfx, override=bool(same),
                 tail=f"   -> ${wage_usd:,.2f}/h worked")
    if pl:
        print(pl)
    print(f"  {'÷ utilization ' + format(util * 100, '.0f') + '%':<34}"
          f"{'[' + src(p, 'utilization') + ']':<12}-> ${wpb:,.2f}/billable h")
    print(f"  {'+ stack $' + num(stack) + '/mo ÷ ' + num(bh) + ' h/mo':<34}"
          f"{'[' + src(p, 'billable_h_month') + ']':<12}-> ${oh:,.2f}/h")
    print(f"  {'= BREAK-EVEN':<34}{'':<12}   ${be:,.2f}/h"
          + ("   <- family rate floor" if not markup else ""))
    print(f"  {'+ markup ' + format(markup * 100, '.0f') + '%':<34}"
          f"{'[' + mk_src + ']':<12}-> ${rate:,.2f}/h  ({cur} {rate / dfx:,.0f}/h)")
    if cur != pcur:
        dl = fx_line(p, cur, dfx, override=bool(fx_override), tail="   display only")
        if dl:
            print(dl)
    print(f"\n    >>>  ${fee:,.0f} USD   ({cur} {fee / dfx:,.0f})  <<<\n")
    print("  Your own hours are NOT a cost: there is no payroll, so nothing leaves the")
    print("  bank. This is a PRICE. The hours are a take-home rate and a capacity limit.")
    print("  Never set the fee against a 'cost of labour' and conclude you lost money.\n")


# =====================================================================
#  FORECASTING  --  the part that stops you guessing
#
#  Two instruments:
#    --estimate  reference-class forecasting. What did work LIKE THIS
#                actually take? Answered from YOUR transcripts, not from a feeling.
#    --predict / --settle / --calibration
#                the loop that makes the bias MEASURABLE. Log a prediction,
#                settle it against reality, learn your personal multiplier.
#
#  Why this exists. A build was estimated at "15-20 h", then revised UPWARD to
#  "30-40 h" out of alarm when a recon pass surfaced more scope. The measured
#  actual was ~2.5 h. A ~12x miss.
#
#  The miss was a UNIT ERROR, not a judgment error: the estimate was in HUMAN
#  hours for work that agents do in parallel. The measurable unit, the only one
#  this tool reports, is ACTIVE CLAUDE CODE HOURS. Nothing forced that unit,
#  nothing forced an anchor to a measured comparable, and nothing recorded the
#  miss, so the miss taught nobody anything. That is what these commands fix.
#
#  DAY ONE: --estimate reads YOUR history. On a fresh install it will say "No
#  comparable found. You are estimating BLIND." That is the tool working, not the
#  tool broken. It gets better the more you use Claude Code.
# =====================================================================
STOP = set("""a an the and or of to in on for with at by from is are was were be been it
this that these those we you i our your my as if then than so but not no do does did how
what when where which who why can could should would will shall may might must have has had
please just make made get got need needs want use used using new all any some more most""".split())


def _terms(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if len(w) > 2 and w not in STOP}


def all_blocks():
    """Every work block in every repo, with its opening prompt. The reference class."""
    out = []
    for n, f in repos([], everything=True).items():
        ev = load(f)
        if not ev:
            continue
        for b in blocks(ev):
            sec = active_seconds([e for e in b if not e["side"]])
            c = sum(e["cost"] for e in b if e["kind"] == "a")
            if sec < 120 and c < 0.50:
                continue                      # noise, not a task
            lab = next((e["text"] for e in b if e["kind"] == "u" and e.get("typed")
                        and e.get("text")), "")
            out.append(dict(repo=n, ts=b[0]["ts"], sec=sec, cost=c, prompt=lab or "(untyped)"))
    return out


def _pct(xs, q):
    """Linear-interpolated percentile. Nearest-rank rounds UP at the midpoint, so on
    an even sample the 'median' of [0.5x, 3.0x] came out as 3.0x and --calibration
    then told you to triple every estimate on the strength of one miss."""
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = q * (len(xs) - 1)
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def r_estimate(query, n_show=8):
    """Reference-class forecast. Past blocks LIKE this one, and what they REALLY took.

    The query can be several phrasings of the SAME work, separated by "|". Matching
    is word overlap, so "stripe checkout", "payment gateway" and "checkout
    integration" each reach a different slice of history; the pipe pools them into
    ONE reference class. A block scores as its BEST phrasing and is counted once."""
    probes = [t for t in (_terms(p) for p in query.split("|")) if t]
    if not probes:
        print("  --estimate needs words to match on.")
        return
    scored = []
    for b in all_blocks():
        t = _terms(b["prompt"])
        if not t:
            continue
        s = max(len(q & t) / len(q) for q in probes)
        if s:
            scored.append((s, b))
    scored.sort(key=lambda x: (-x[0], -x[1]["sec"]))
    hits = [b for s, b in scored if s > 0]

    print(f"\n{'=' * 78}\n  REFERENCE CLASS: work that looked like \"{query}\"\n{'=' * 78}")
    if len(probes) > 1:
        print(f"  pooled from {len(probes)} phrasings, each block counted once\n")
    if not hits:
        print("  No comparable found. You are estimating BLIND.")
        print("  Say so out loud rather than inventing a number.")
        print("\n  Before declaring blind, try other words for the same work, pooled in")
        print("  one query: --estimate \"stripe checkout | payment gateway | billing\".")
        print("  Each phrasing reaches a different slice of your history.")
        print("\n  This is normal on a fresh install: the forecaster reads YOUR OWN")
        print("  transcript history, so it has nothing to go on until you have some.")
        print("  It is not broken. It gets sharper every week you use Claude Code.\n")
        return

    hrs = [b["sec"] / 3600 for b in hits]
    print(f"  n = {len(hits)} comparable blocks\n")
    print(f"    p50   {_pct(hrs, .50):6.2f} h   <- use THIS as the anchor")
    print(f"    p80   {_pct(hrs, .80):6.2f} h   <- use THIS if the work is on a money path")
    print(f"    max   {max(hrs):6.2f} h")
    print(f"    mean  {sum(hrs) / len(hrs):6.2f} h\n")
    # Confidence is a labelled verdict, never a percentage. A "91% confident"
    # number would itself be an invented number, the exact disease this treats.
    p50 = _pct(hrs, .50)
    spread = _pct(hrs, .80) / p50 if p50 else 0.0
    match = sum(s for s, _ in scored) / len(scored)
    if len(hits) < 3:
        conf = "LOW (n < 3). A hint, not an anchor. Say the sample is tiny."
    elif spread > 3:
        conf = (f"LOW: comparables disagree (p80 is {spread:.1f}x the p50). "
                "Split the task and estimate the pieces.")
    elif match < 0.5:
        conf = ("MEDIUM: matches are loose (under half your words hit). "
                + ("Read the listed prompts before trusting the anchor."
                   if len(probes) > 1 else
                   "Pool 2-3 phrasings: --estimate \"one phrasing | another\"."))
    else:
        conf = f"SOLID: {len(hits)} comparables, agreeing with each other."
    print(f"    confidence: {conf}\n")
    print(f"  {'when':<14}{'repo':<22}{'actual':>8}{'cost':>8}  the task")
    for b in hits[:n_show]:
        print(f"  {datetime.fromtimestamp(b['ts']).strftime('%d %b %H:%M'):<14}"
              f"{b['repo'][:21]:<22}{fmt_h(b['sec']):>8}"
              f"{'$' + format(b['cost'], ',.0f'):>8}  {b['prompt'][:38]}")
    print("\n  WARNING: these are ACTIVE CLAUDE CODE HOURS. Not human hours, not")
    print("  wall-clock. Agent fan-out makes them far smaller than the work feels.")
    print("  Quote in this unit. Add operator hours (calls, QA, review) separately.")
    print("\n  A block is a TASK, not a PROJECT. Decompose the job into the blocks you")
    print("  expect, then multiply by p50 (p80 on a money path). Do not read a p50 of")
    print("  0.35 h as 'the whole feature takes 20 minutes'.\n")


def _ledger():
    path = data_path(LEDGER_NAME)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def r_predict(task, hours, repo, phase):
    """Log a prediction BEFORE doing the work. Unsettled predictions are the point."""
    # Collision-safe. int(time.time()) alone gives two predictions logged in the
    # same second the SAME id, which silently corrupts the ledger: --settle then
    # updates whichever it finds first. A calibration tool that quietly
    # mis-records is worse than no calibration tool.
    existing = {r.get("id") for r in _ledger()}
    base = int(time.time())
    eid, n = f"e{base}", 0
    while eid in existing:
        n += 1
        eid = f"e{base}-{n}"
    rec = dict(id=eid, task=task, predicted_h=hours, repo=repo, phase=phase,
               made_at=datetime.now().isoformat(timespec="seconds"),
               actual_h=None, ratio=None)
    ensure_dir()
    with open(data_path(LEDGER_NAME), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(f"\n  logged {eid}: {hours} h  ({phase})  {task}")
    if phase == "pre-recon":
        print("  WARNING: PRE-RECON. Historically the least reliable kind of estimate")
        print("  there is. Label it provisional to the client. Re-predict after grounding.")
    print(f"  settle it later:  truecost.py --settle {eid} --actual <measured h>\n")


def r_settle(eid, actual):
    recs = _ledger()
    hit = next((r for r in recs if r.get("id") == eid), None)
    if not hit:
        print(f"  no such estimate: {eid}   (ledger: {data_path(LEDGER_NAME)})")
        sys.exit(1)
    hit["actual_h"] = actual
    hit["ratio"] = round(actual / hit["predicted_h"], 3) if hit.get("predicted_h") else None
    hit["settled_at"] = datetime.now().isoformat(timespec="seconds")
    ensure_dir()
    with open(data_path(LEDGER_NAME), "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    r_ = hit["ratio"]
    verdict = ("OVER-estimated by " + f"{1 / r_:.1f}x") if r_ and r_ < 1 else \
              ("UNDER-estimated by " + f"{r_:.1f}x") if r_ and r_ > 1 else "spot on"
    print(f"\n  {eid}: predicted {hit['predicted_h']} h, actual {actual} h  ->  {verdict}\n")


def r_calibration():
    """Your measured forecasting bias. The whole reason the ledger exists."""
    recs = [r for r in _ledger() if r.get("ratio")]
    print(f"\n{'=' * 78}\n  CALIBRATION: how wrong are your estimates, really?\n{'=' * 78}")
    if not recs:
        print("  Nothing settled yet. An unsettled ledger teaches you nothing.")
        print("  --predict before the work, --settle after it. That is the loop.\n")
        return
    for phase in ("pre-recon", "post-recon"):
        rs = [r for r in recs if r.get("phase") == phase]
        if not rs:
            continue
        ratios = sorted(r["ratio"] for r in rs)
        med = _pct(ratios, .50)
        direction = f"OVER by {1 / med:.1f}x" if med < 1 else f"UNDER by {med:.1f}x"
        print(f"\n  {phase}  (n={len(rs)})   median ratio {med:.2f}  ->  you {direction}")
        if len(rs) >= 3:
            print(f"    CORRECTION: multiply your gut number by {med:.2f}")
        else:
            # Two settled estimates is an anecdote. Prescribing a multiplier off it
            # is exactly the guessing this tool exists to stop.
            print(f"    n < 3. Too thin to prescribe a multiplier: read the rows, do not")
            print(f"    apply {med:.2f} to anything yet. Settle a few more.")
        for r in rs:
            print(f"      {r['predicted_h']:>5} h -> {r['actual_h']:>5} h  "
                  f"({r['ratio']:.2f}x)  {str(r.get('task', ''))[:40]}")
    print("\n  Apply the correction for the matching phase. Do not re-derive it by feel:")
    print("  re-deriving it by feel is the original bug.\n")


# ============================================================ CLI
def main(argv=None):
    p = argparse.ArgumentParser(
        prog="truecost.py",
        description="Measure how long Claude Code actually takes, and forecast the "
                    "next one from your own measured history.",
        epilog="Billing (--quote, --clients) needs a profile: run --setup first. "
               "The time and token layers need nothing.")
    p.add_argument("projects", nargs="*", help="repo name(s), or a path to one")
    p.add_argument("--all", action="store_true", help="portfolio across every repo")
    p.add_argument("--tasks", action="store_true", help="per-work-block breakdown")
    p.add_argument("--live", action="store_true", help="track the session running now")
    p.add_argument("--setup", action="store_true",
                   help="interactive profile. Unlocks --quote and --clients.")
    p.add_argument("--from-json", metavar="FILE", default=None,
                   help="with --setup: write the profile from a JSON file ('-' = stdin), "
                        "validated. For CI, containers and new machines.")
    p.add_argument("--quote", action="store_true",
                   help="measured hours -> invoice. NEEDS a profile.")
    p.add_argument("--clients", action="store_true",
                   help="every client vs what they pay. NEEDS a profile + clients.json.")
    p.add_argument("--offline", type=float, default=0.0,
                   help="hours worked OUTSIDE Claude Code. Always set this.")
    # These are OVERRIDES of your profile, not defaults. There are no defaults:
    # a shipped rate card is somebody else's business asserted as if it were yours.
    p.add_argument("--wage", type=float, default=None,
                   help="override the profile wage, in the PROFILE's currency")
    p.add_argument("--currency", default=None,
                   help="present the quote in this currency. Display only: it does not "
                        "move the fee. Needs --fx if it is not your profile currency.")
    p.add_argument("--markup", type=float, default=None,
                   help="override the profile markup. 0 = break-even / family rate.")
    p.add_argument("--fx", type=float, default=None,
                   help="rate taking --currency into USD. Overrides the profile FX.")
    # forecasting
    p.add_argument("--estimate", metavar="QUERY",
                   help="reference-class forecast: what did work LIKE THIS actually take?")
    p.add_argument("--predict", metavar="TASK", help="log a prediction BEFORE doing the work")
    p.add_argument("--hours", type=float, help="the predicted ACTIVE CLAUDE CODE hours")
    p.add_argument("--phase", choices=["pre-recon", "post-recon"], default="post-recon",
                   help="pre-recon estimates are historically the worst. Label them.")
    p.add_argument("--repo", default="", help="repo the prediction is about")
    p.add_argument("--settle", metavar="ID", help="settle a prediction against measured reality")
    p.add_argument("--actual", type=float, help="the measured active hours, for --settle")
    p.add_argument("--calibration", action="store_true", help="your measured forecasting bias")
    a = p.parse_args(argv)

    # A report that needs a repo and did not get one used to fall through to the
    # help text and exit 0, which in a script is indistinguishable from success.
    if (a.quote or a.tasks) and not a.projects:
        p.error("--quote and --tasks need a repo: truecost.py <repo> --quote")
    if a.from_json and not a.setup:
        p.error("--from-json goes with --setup: truecost.py --setup --from-json <file>")

    if a.setup:
        setup_from_json(a.from_json) if a.from_json else r_setup()
    elif a.estimate:
        r_estimate(a.estimate)
    elif a.predict:
        if a.hours is None:
            p.error("--predict needs --hours (in ACTIVE CLAUDE CODE hours)")
        r_predict(a.predict, a.hours, a.repo, a.phase)
    elif a.settle:
        if a.actual is None:
            p.error("--settle needs --actual")
        r_settle(a.settle, a.actual)
    elif a.calibration:
        r_calibration()
    elif a.live:
        r_live()
    elif a.clients:
        r_clients(require_profile("--clients"))
    elif a.all:
        r_all()
    elif a.projects:
        prof = require_profile("--quote") if a.quote else None
        if prof:
            refuse_bad_quote_inputs(prof, a.wage, a.markup, a.offline, a.fx)
        found = repos(a.projects)
        if not found:
            print(f"  no transcripts for: {', '.join(a.projects)}")
            print("  run  truecost.py --all  to see the repo names it knows about.")
            sys.exit(1)
        for n, f in found.items():
            ev = load(f)
            if not ev:
                print(f"  {n}: no sessions")
                continue
            sec = active_seconds(ev)
            if a.tasks:
                r_tasks(n, ev)          # --tasks and --quote compose: blocks, then invoice
            else:
                r_project(n, ev)
            if a.quote:
                r_quote(n, sec, a.offline, prof, a.wage, a.currency, a.markup, a.fx)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
