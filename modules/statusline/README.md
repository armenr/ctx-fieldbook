---
provenance: kit-template
created: 2026-07-05
last-modified: 2026-07-05
tags: [module, statusline, optional]
---

# Statusline module (opt-in)

A single-line, information-dense Claude Code status line. Reads the authoritative JSON Claude Code pipes
to it — no cost guessing, no cap estimation — and renders, left to right:

```
📁 repo ⎇ branch │ 🤖 Model 1M │ 📦 AC on │ 🧠 ctx 20% 200K/1M │ ⏳ 5h 12% ↻ 3h 40m │ 📅 7d 8% ↻ 5d 2h │ 📧 <account-email>
```

- **📁 repo ⎇ branch** — the project dir name + current git branch (or short SHA if detached).
- **🤖 Model + context label** — active model, with its context window (`200K` / `1M`).
- **📦 AC** — auto-compact on/off (reads `autoCompactEnabled` from settings; green on / red off).
- **🧠 ctx** — context used: percentage **and** absolute tokens (`20% 200K/1M`), color-graded
  (green <50% → yellow <75% → orange <90% → red).
- **⏳ 5h / 📅 7d** — your rate-limit usage for each window, with a `↻` countdown to reset.
- **📧 email** — the Claude account email, read at runtime from *your own* `~/.claude.json`.

**Dependencies:** `python3` only (standard library — no `pip install`, no `jq`). It's the same `python3`
the doc-schema linter already needs, so a Standard+ install has it. Degrades gracefully: missing fields
render as `—`, and it caches the last-seen rate limits under `~/.cache/` as a fallback.

---

## Install

Pick ONE scope. **A statusline is a per-user preference**, so **global** is the usual choice (one
statusline across every project). **Project-scoped** keeps it inside this repo and, because
`.claude/settings.json` **overrides** `~/.claude/settings.json`, wins over any global one you already have.

> Mechanics that drive the two forms (verified against the Claude Code docs): in a `statusLine.command`,
> **`~` is the only expansion that is guaranteed** — `$CLAUDE_PROJECT_DIR` is documented for *hooks*, not
> statuslines — and the command's working directory is **undefined**, so a *relative* path is unreliable.
> That's why global uses `~` and project-scoped uses an **absolute** path.

### Global (recommended — same statusline everywhere)

1. Copy the script to your home config:
   ```
   cp modules/statusline/statusline.py ~/.claude/statusline.py
   ```
2. Add this to **`~/.claude/settings.json`** (merge into the top-level object; don't clobber existing keys):
   ```json
   {
     "statusLine": { "type": "command", "command": "python3 ~/.claude/statusline.py", "padding": 0 }
   }
   ```

### Project-scoped (this repo only; overrides a global statusline)

1. Copy the script into the repo:
   ```
   cp modules/statusline/statusline.py <project>/.claude/statusline.py
   ```
2. Add this to **`<project>/.claude/settings.json`**, using the repo's **absolute** path
   (the concierge fills this in for you; substitute your real path if installing by hand):
   ```json
   {
     "statusLine": { "type": "command", "command": "python3 /abs/path/to/<project>/.claude/statusline.py", "padding": 0 }
   }
   ```
   > Absolute because the statusline command's cwd isn't guaranteed. If you move the repo, update this
   > path (or re-run the concierge).

---

## Verify

Open a new Claude Code session — the line should render at the bottom. To test the script directly:

```
echo '{"model":{"display_name":"Sonnet"},"workspace":{"project_dir":"'"$PWD"'"}}' | python3 ~/.claude/statusline.py
```

You should see a rendered line (with `—` for fields the fake input omits). If it's blank, confirm the
command path is absolute or `~`-based (not relative) and that `python3` is on PATH.

## Notes

- **Rate limits (⏳/📅)** need a Claude Pro/Max plan and appear only *after the first API response* in a
  session — until then they show `—`. Not a bug.
- **Version:** the context-token fields stabilized at Claude Code v2.1.132; on much older builds the ctx
  segment may read differently. The script tolerates absent fields either way.
- **Privacy:** the `📧` segment shows *your* account email (read from your own `~/.claude.json`, never
  baked into the script). If you'd rather not have it on screen during screenshares, delete the
  `email` / `email_seg` block near the end of `statusline.py` — the rest is unaffected.
