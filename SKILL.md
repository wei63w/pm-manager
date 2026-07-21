---
name: pm-manager
description: >-
  Project governance workbench (/pm-*). Use for /pm-init, /pm-status, /pm-next,
  /pm-done, /pm-fix, /pm-all, /pm-outline, /pm-charter, /pm-export, project
  health Top3, pasted logs/stacks, Spec Kit constitution discovery, and local
  .pm governance. Triggers on 项目管理、治理、今日做什么、帮我看报错.
---

# PM Manager

Spec-kit-inspired command pack for **local `.pm/` project governance**.

## When to use

- User says `/pm-init`, `/pm-status`, `/pm-all`, `/pm-fix`, `/pm-done`, `/pm-next`, `/pm-outline`, `/pm-charter`, `/pm-export`
- Natural language: 初始化治理、今天做什么、全面检查、帮我看这个报错、这个待办做完了

## How to execute

1. Resolve command name from user message (see routing table in `../pm-manager-v2.md` or `memory/ROUTING.md`).
2. Read the matching file under `templates/commands/<name>.md` and **follow it exactly**.
3. For `/pm-init`, run `scripts/python/create_pm_scaffold.py <project-root>` (or PowerShell twin) before filling config.
4. Keep daily UX simple: prefer status Top3; do not dump medium/low unless `--verbose`.
5. Never commit `.pm/`; never print secrets.

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
| `/pm-discover` | `templates/commands/discover.md` |

## Design baseline

Full contract lives in local `pm-manager-v*.md` (not published in this repo).
