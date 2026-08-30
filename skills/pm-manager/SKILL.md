---
name: pm-manager
description: "Project governance workbench (/pm-*). Daily: /pm-init, /pm-status, /pm-next, /pm-done, /pm-fix; release: /pm-all; journal: /pm-journal; review diffs: /pm-review; diagnose: /pm-check. Triggers on what should I do today, help me with this error, initialize governance, review this change, session intent, timeline."
license: MIT
metadata:
  version: "0.0.9"
  author: wei63w
---

# PM Manager

Spec-kit-inspired command pack for **local `.pm/` project governance**.

## When to use

- User says `/pm-init`, `/pm-status`, `/pm-next`, `/pm-done`, `/pm-fix`, `/pm-all`, `/pm-review`, `/pm-checkup`, `/pm-check`, `/pm-docs`, `/pm-journal`, `/pm-tests`, `/pm-outline`, `/pm-charter`, `/pm-export`, `/pm-arch`
- Natural language: initialize governance, what should I do today, full health check, help me with this error, this todo is done, review this diff, repair .pm
- Do **not** send users to `/pm-discover` (internal to `/pm-all`)

## How to execute

1. Resolve command name from user message (see routing table in `memory/ROUTING.md`).
2. Read the matching file under `templates/commands/<name>.md` and **follow it exactly**.
3. For `/pm-init`, run `pm init <project-root>` (or `scripts/python/create_pm_scaffold.py`) before filling config. Then detect Spec Kit; if absent, draft `.pm/prd/prd.md` and **wait for user confirm**. After confirm or skip, run the **technical light scan** (docs + arch) in `init.md` §7.
4. Keep daily UX simple: `/pm-status` lists all open blocking+high todos (do **not** cap at 3); mention pending reviews; do not dump medium/low unless `--verbose`.
5. Never commit `.pm/`; never print secrets.
6. **Closing:** `templates/commands/_closing.md` — graded; only existing paths. Chinese when the user writes Chinese.

## Command map

| User command | Template | Audience |
|--------------|----------|----------|
| `/pm-init` | `templates/commands/init.md` | daily |
| `/pm-status` | `templates/commands/status.md` | daily |
| `/pm-next` | `templates/commands/next.md` | daily |
| `/pm-done` | `templates/commands/done.md` | daily |
| `/pm-fix` | `templates/commands/fix.md` | daily |
| `/pm-all` | `templates/commands/all.md` | release |
| `/pm-review` | `templates/commands/review.md` | quality |
| `/pm-checkup` | `templates/commands/checkup.md` | quality |
| `/pm-check` | `templates/commands/check.md` | recovery |
| `/pm-outline` | `templates/commands/outline.md` | planning |
| `/pm-charter` | `templates/commands/charter.md` | planning |
| `/pm-export` | `templates/commands/export.md` | export |
| `/pm-arch` | `templates/commands/arch.md` | maps |
| `/pm-docs` | `templates/commands/docs.md` | docs |
| `/pm-journal` | `templates/commands/journal.md` | journal |
| `/pm-tests` | `templates/commands/tests.md` | quality |
| `/pm-discover` | `templates/commands/discover.md` | internal |

## Design baseline

Governing text: pack `docs/prd.md` + 宪章（中文优先）。
