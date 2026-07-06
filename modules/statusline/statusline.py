#!/usr/bin/env python3
"""Statusline using Claude Code's authoritative rate_limits + context_window fields.

Matches what `/usage` shows. No cost estimation, no cap guessing — reads the
truth straight from the JSON Claude Code pipes to stdin.
"""
import sys, os, json, time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache"
RATE_CACHE = CACHE_DIR / "claude-rate-limits.json"   # fallback for sessions before first API response
CTX_CACHE  = CACHE_DIR / "claude-context.json"

# === helpers ===
def write_json(path, val):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(val))
    except Exception:
        pass

# === main render ===
stdin_data = json.loads(sys.stdin.read())

# --- model + context window size ---
model = stdin_data.get("model") or {}
model_name = model.get("display_name") or model.get("id") or "Claude"
for suffix in (" (1M context)", " (1M)", " (200K)"):
    if model_name.endswith(suffix):
        model_name = model_name[: -len(suffix)]
model_id = (model.get("id") or "").lower()
ctx_block_in = stdin_data.get("context_window") or {}
ctx_window = ctx_block_in.get("context_window_size") or (1_000_000 if "1m" in model_id else 200_000)
ctx_label = "1M" if ctx_window >= 1_000_000 else f"{ctx_window // 1000}K"

# --- context %: use stdin authoritatively, cache it for fallback ---
if ctx_block_in:
    ctx_used_pct = ctx_block_in.get("used_percentage")
    write_json(CTX_CACHE, {"used": ctx_used_pct})
else:
    try: ctx_used_pct = json.loads(CTX_CACHE.read_text()).get("used")
    except Exception: ctx_used_pct = None

# --- rate limits: use stdin authoritatively, cache for fallback ---
rl = stdin_data.get("rate_limits") or {}
if rl:
    write_json(RATE_CACHE, rl)
else:
    try: rl = json.loads(RATE_CACHE.read_text())
    except Exception: rl = {}
five_h  = rl.get("five_hour") or {}
seven_d = rl.get("seven_day") or {}

# === ANSI styling ===
R = "\x1b[0m"; DIM = "\x1b[2m"; BOLD = "\x1b[1m"
GREEN = "\x1b[38;5;82m"; YELLOW = "\x1b[38;5;220m"; ORANGE = "\x1b[38;5;208m"
RED   = "\x1b[38;5;196m"; CYAN = "\x1b[38;5;81m"; PURPLE = "\x1b[38;5;141m"; GREY = "\x1b[38;5;244m"
SEP = f"{GREY}│{R}"

def color_for(pct):
    if pct is None: return GREY
    if pct < 50:    return GREEN
    if pct < 75:    return YELLOW
    if pct < 90:    return ORANGE
    return RED

def fmt_remaining(secs):
    if secs <= 0: return "reset"
    days, rem = divmod(int(secs), 86400)
    h, rem    = divmod(rem, 3600)
    m         = rem // 60
    if days > 0: return f"{days}d {h}h"
    if h > 0:    return f"{h}h {m}m"
    return f"{m}m"

def fmt_tokens(n):
    """Format a token count with K/M units + sensible rounding.
    1_000_000 -> "1M", 1_500_000 -> "1.5M", 200_000 -> "200K",
    47_300 -> "47K" (rounded to nearest K), 234 -> "234"."""
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        m = n / 1_000_000
        return f"{int(m)}M" if m == int(m) else f"{m:.1f}M"
    if n >= 1_000:
        return f"{round(n / 1000)}K"
    return str(n)

def field(icon, label, pct_used, label_color, reset_ts=None):
    if pct_used is None:
        return f"{label_color}{icon} {label}{R} {DIM}—{R}"
    pct_used = float(pct_used)
    c = color_for(pct_used)
    s = f"{label_color}{icon} {label}{R} {c}{pct_used:.0f}%{R}"
    if reset_ts:
        rs = fmt_remaining(reset_ts - time.time())
        if rs:
            s += f" {DIM}↻{R} {label_color}{rs}{R}"
    return s

def ctx_field(pct_used, total_tokens):
    """ctx segment shows used % AND absolute token count (e.g. 20% 200K/1M),
    both rendered in the same threshold color so they tell a consistent story."""
    if pct_used is None:
        return f"{CYAN}🧠 ctx{R} {DIM}—{R}"
    pct = float(pct_used)
    c = color_for(pct)
    used_tokens = int(total_tokens * pct / 100)
    return (f"{CYAN}🧠 ctx{R} {c}{pct:.0f}%{R} "
            f"{c}{fmt_tokens(used_tokens)}/{fmt_tokens(total_tokens)}{R}")

# === auto-compact ===
def truthy(v): return str(v).strip().lower() in ("1", "true", "yes", "on")
ac_enabled = True
if truthy(os.environ.get("DISABLE_AUTO_COMPACT", "")):
    ac_enabled = False
else:
    paths = [Path.home() / ".claude" / "settings.json"]
    proj = (stdin_data.get("workspace") or {}).get("project_dir")
    if proj:
        paths.append(Path(proj) / ".claude" / "settings.json")
        paths.append(Path(proj) / ".claude" / "settings.local.json")
    for p in paths:
        try:
            if p.exists():
                cfg = json.loads(p.read_text())
                if "autoCompactEnabled" in cfg:
                    ac_enabled = bool(cfg["autoCompactEnabled"])
        except Exception:
            pass

# === repo + branch ===
project_dir = (stdin_data.get("workspace") or {}).get("project_dir") or ""
repo_name = Path(project_dir).name if project_dir else ""
branch = None
if project_dir:
    head = Path(project_dir) / ".git" / "HEAD"
    try:
        line = head.read_text().strip()
        if line.startswith("ref: refs/heads/"):
            branch = line[len("ref: refs/heads/"):]
        else:
            branch = line[:7]  # detached HEAD → short SHA
    except Exception:
        pass

# === assemble ===
ac_color = GREEN if ac_enabled else RED
ac_label = "on" if ac_enabled else "off"

repo_label = repo_name or "—"
branch_text = f" {DIM}⎇{R} {GREEN}{branch}{R}" if branch else ""
repo_seg = f"{BOLD}📁 {repo_label}{R}{branch_text}"

# --- active account email (from ~/.claude.json oauthAccount.emailAddress) ---
email = None
try:
    cj = json.loads((Path.home() / ".claude.json").read_text())
    email = (cj.get("oauthAccount") or {}).get("emailAddress")
except Exception:
    email = None
email_seg = f" {SEP} {CYAN}📧{R} {DIM}{email}{R}" if email else ""

print(
    f"{repo_seg} {SEP} "
    f"{BOLD}🤖 {model_name}{R} {DIM}{ctx_label}{R} {SEP} "
    f"{PURPLE}📦 AC{R} {ac_color}{ac_label}{R} {SEP} "
    f"{ctx_field(ctx_used_pct, ctx_window)} {SEP} "
    f"{field('⏳', '5h', five_h.get('used_percentage'), PURPLE, five_h.get('resets_at'))} {SEP} "
    f"{field('📅', '7d', seven_d.get('used_percentage'), YELLOW, seven_d.get('resets_at'))}"
    f"{email_seg}"
)
