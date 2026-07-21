---
name: pm-manager
description: "Project governance workbench (/pm-*). Use for /pm-init, /pm-status, /pm-next, /pm-done, /pm-fix, /pm-all, /pm-outline, /pm-charter, /pm-export, /pm-arch, project health Top3, pasted logs/stacks, Spec Kit constitution discovery, and local .pm governance. Triggers on project management, governance, what should I do today, help me with this error."
license: MIT
metadata:
  version: "0.0.6"
  author: wei63w
---

# PM Manager

Spec-kit-inspired command pack for **local `.pm/` project governance**.

## When to use

- User says `/pm-init`, `/pm-status`, `/pm-all`, `/pm-fix`, `/pm-done`, `/pm-next`, `/pm-outline`, `/pm-charter`, `/pm-export`, `/pm-arch`
- Natural language: initialize governance, what should I do today, full health check, help me with this error, this todo is done, generate architecture diagram

## How to execute

1. Resolve command name from user message (see routing table in `memory/ROUTING.md`).
2. Read the matching file under `templates/commands/<name>.md` and **follow it exactly**.
3. For `/pm-init`, run `pm init <project-root>` (or `scripts/python/create_pm_scaffold.py`) before filling config.
4. Keep daily UX simple: prefer status Top3; do not dump medium/low unless `--verbose`.
5. Never commit `.pm/`; never print secrets.
6. **Always end with a short Summary + Open these links** (see `templates/commands/_closing.md`). Tell the user to open the overview — do not assume they know `.pm/dashboard/` or `.pm/architecture/` exists.

## Command map

| User command | Template |
|--------------|----------|
| `/pm-init` | `templates/commands/init.md` |
| `/pm-status` | `templates/commands/status.md` |
| `/pm-next` | `templates/commands/next.md` |
| `/pm-done` | `templates/commands/done.md` |
| `/pm-fix` | `templates/commands/fix.md` |
| `/pm-all` | `templates/commands/all.md` |
| `/pm-outline` | `templates/commands/outline.md` |
| `/pm-charter` | `templates/commands/charter.md` |
| `/pm-export` | `templates/commands/export.md` |
| `/pm-arch` | `templates/commands/arch.md` |
| `/pm-discover` | `templates/commands/discover.md` |

## Design baseline

Full contract lives in local `pm-manager-v*.md` (not published in this repo).
