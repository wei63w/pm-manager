# AGENTS.md — PM Manager

This repository is a **Spec Kit–inspired** skill pack for local project governance (`.pm/`).

## Layout (mirrors Spec Kit ideas)

| Path | Role (like Spec Kit) |
|------|----------------------|
| `templates/commands/*.md` | Slash/skill command prompts (`templates/commands` in Spec Kit) |
| `templates/pm/*` | Artifacts copied into target project `.pm/` |
| `scripts/python\|powershell` | Deterministic scaffold helpers (repo root) |
| `adapters/cursor` | Cursor Agent Skills install (repo root) |
| `adapters/claude-code` | Claude Code slash commands (repo root) |
| `SKILL.md` | Router skill for Cursor / skills hosts |
| Design docs | Local-only `pm-manager-v*.md` (gitignored / not published) |

## Agent rules

1. Prefer daily commands; module deep-dives go through `/pm-all` or `/pm-discover`.
2. Conversation paste is first-class evidence for `/pm-fix`.
3. Discover Spec Kit `.specify/memory/constitution.md` during `/pm-init` / `/pm-charter discover`.
4. `.pm/` is local-only — add to `.git/info/exclude`, never `.gitignore` shared rules.
5. Do not auto-modify application code/SQL/cloud without confirmation.
6. Default noise filter: blocking + high; Top3 only in `/pm-status`.

## Quick test

```bash
pm init /path/to/project
# then in agent: /pm-init  /pm-status
```
