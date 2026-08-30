**English** | [简体中文](./README.zh-CN.md)

**📋 PM Manager**  
*Know what to fix next — with any AI coding agent.*

[![Release](https://img.shields.io/github/v/release/wei63w/pm-manager?logo=github&label=release)](https://github.com/wei63w/pm-manager/releases/latest)
[![Version](https://img.shields.io/badge/version-alpha-orange)](https://github.com/wei63w/pm-manager)
[![Downloads](https://img.shields.io/github/downloads/wei63w/pm-manager/total?label=downloads&color=brightgreen)](https://github.com/wei63w/pm-manager/releases)
[![Commit activity](https://img.shields.io/github/commit-activity/m/wei63w/pm-manager)](https://github.com/wei63w/pm-manager/commits/main)
[![License](https://img.shields.io/github/license/wei63w/pm-manager)](https://github.com/wei63w/pm-manager/blob/main/LICENSE)
[![skills.sh](https://skills.sh/b/wei63w/pm-manager)](https://skills.sh/wei63w/pm-manager)

An open source skill pack for **local project governance** — init a `.pm/` workbench, see today's open todos, triage pasted logs, and run release-ready health scans. Inspired by [Spec Kit](https://github.com/github/spec-kit)’s command-template + multi-agent adapter model. Works alongside Spec Kit: Spec Kit drives *what to build*; PM Manager drives *project health and what’s next*.

---

## Table of Contents

- [What is PM Manager?](#what-is-pm-manager)
- [Get Started](#get-started)
- [CLI Reference](#cli-reference)
- [Supported AI Coding Agents](#supported-ai-coding-agents)
- [Available Slash Commands](#available-slash-commands)
- [How it relates to Spec Kit](#how-it-relates-to-spec-kit)
- [Core Philosophy](#core-philosophy)
- [Daily Workflow](#daily-workflow)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Support](#support)
- [License](#license)

## What is PM Manager?

Most AI coding sessions jump straight into code. **PM Manager flips the day-to-day loop**: keep a local, auditable `.pm/` board for health, todos, incidents, and release gates — then let the agent show **today’s open blocking and high-priority work**.

It is **not** a cloud PM suite and **not** a replacement for Jira/Linear. It is a **developer-side governance workbench** that lives in your repo’s local `.pm/` directory (git-excluded), driven by slash commands / skills the same way Spec Kit drives `/speckit.*`.

## Get Started

### 1. Install the Agent Skill (skills.sh)

```bash
npx skills@latest add wei63w/pm-manager
```

Or copy `skills/pm-manager` into your tool’s skills directory:

| Tool | Path |
|------|------|
| Cursor | `~/.cursor/skills/pm-manager/` |
| Claude Code | `~/.claude/skills/pm-manager/` |
| Codex | `~/.agents/skills/pm-manager/` |

### 2. Install the CLI (optional, cross-platform)

Requires **[uv](https://docs.astral.sh/uv/)** and **Python 3.11+**. The CLI scaffolds `.pm/` and installs per-agent adapters.

```bash
# From GitHub (recommended)
uv tool install pm-manager-cli --from git+https://github.com/wei63w/pm-manager.git

# Or from a local checkout
uv tool install --editable .
```

Verify:

```bash
pm version
# or
pm-manager version
```

Upgrade later:

```bash
uv tool upgrade pm-manager-cli
# or reinstall from git
uv tool install pm-manager-cli --force --from git+https://github.com/wei63w/pm-manager.git
```

### 3. Bootstrap a project

In your **application** repository (not required to keep this pack checked out):

```bash
cd /path/to/your-app

# Create .pm/ + install Cursor & Claude adapters (default; no Node.js)
# Optional skills.sh index: pm init --skills-sh
pm init

# Cursor only
pm init --agent cursor

# Claude Code only
pm init --agent claude

# Scaffold .pm/ only (no agent files, no skills.sh)
pm init --scaffold-only

# Also index via skills.sh (needs Node.js / npx)
pm init --skills-sh
```

Refresh adapters without re-scaffolding:

```bash
pm install --agent all
pm check
```

> Windows / macOS / Linux all use the same commands. Legacy PowerShell helpers under `scripts/powershell/` still work, but `pm init` **is preferred**.

### 4. Initialize governance in your agent

Open Cursor / Claude Code in the project and run:

```text
/pm-init
```

- Detects **new vs existing** projects
- Checks whether the repo already uses **Spec Kit** (`.specify/memory/constitution.md` or `.specify/specs/**/*.md`)
- If Spec Kit is present: imports constitution/specs and asks you to confirm
- If Spec Kit is **not** present: analyzes the repo (or a one-line intent on an empty repo) and drafts `.pm/prd/prd.md` for **your confirmation**
- Complements the filesystem scaffold from `pm init` (agent fills the PRD / charter)
- After you **confirm or skip**, runs a **technical light scan** (doc index + architecture map) — you do not need `/pm-all` first

### 5. Check today's status

```text
/pm-status
```

You’ll get a short health line and the open blocking/high todos (or run `pm status` without an agent). Claim one with `/pm-next`, close it with `/pm-done TODO-001`.

### 6. Triage an incident

Paste a stack trace or log into the chat:

```text
/pm-fix
```

Conversation paste is a first-class evidence source (no need to save a file first). This command **triages only** — it does not change application code unless you confirm.

### 7. Pre-release full scan

```text
/pm-all
```

Runs a **technical** full scan with a **noise-filtered** summary (blocking + high by default). A draft PRD does **not** block. Use `--compare-baseline` only after a confirmed PRD/charter. Use `--verbose` for the long list.

After the scan, open **`.pm/dashboard/index.html`** in a browser for the visual dashboard (KPI, charts, module risk). Or read **`overview.md`** in the IDE. Rebuild anytime with `pm dashboard`.

## CLI Reference

| Command | Description |
|---------|-------------|
| `pm version` | Print CLI version |
| `pm init [path]` | Create `.pm/` + install agent adapters (Node/skills.sh off by default) |
| `pm init --agent cursor\|claude\|all\|none` | Choose which adapters to install |
| `pm init --scaffold-only` | Only create `.pm/` |
| `pm init --skills-sh` | Also run `npx --yes skills@latest add wei63w/pm-manager -y` (needs Node) |
| `pm install --agent …` | Refresh adapters without scaffolding |
| `pm check [path]` | Diagnose `.pm/`, map, audit, `prd.status`, pending reviews |
| `pm docs [path]` | Detect missing core docs; update `.pm/state/doc-index.md` (does not generate bodies) |
| `pm status [path]` | List all open blocking/high todos (read-only, no 3-item cap) |
| `pm dashboard [path]` | Rebuild `.pm/dashboard/` from module findings/todos |
| `pm arch [path]` | Scan → Mermaid, `map.json`, annotated `tree.md` |
| `pm export [path]` | Time-window desensitized audit Markdown (`--from` / `--to` / `--out`) |

`pm-manager` is an alias of `pm`.

## Supported AI Coding Agents

| Agent | Install path | How you invoke |
|-------|--------------|----------------|
| **Cursor** | `.cursor/skills/pm-manager` (+ optional per-command skills under `adapters/cursor/skills`) | `/pm-init`, `/pm-status`, … or natural language ("what should I do today") |
| **Claude Code** | `.claude/commands/pm-*.md` | `/pm-init`, `/pm-status`, … |
| **Other skill hosts** | Use `skills/pm-manager/SKILL.md` as a router into `templates/commands/` | Follow host skill conventions |

Natural-language routing (when slash commands are unavailable) is documented in [`skills/pm-manager/memory/ROUTING.md`](./skills/pm-manager/memory/ROUTING.md).

## Available Slash Commands

### Daily commands (remember these)

| Command | Agent skill | Description |
|---------|-------------|-------------|
| `/pm-init` | `pm-init` | Scaffold + draft PRD; after confirm/skip run a technical light scan |
| `/pm-status` | `pm-status` | Health + wizard + all open blocking/high todos + pending reviews |
| `/pm-next` | `pm-next` | Claim the next todo (`in_progress`) |
| `/pm-done` | `pm-done` | Close `TODO-xxx`, refresh overview |
| `/pm-fix` | `pm-fix` | Triage pasted logs into todos (**does not change app code**) |

### Release / quality / recovery

| Command | Agent skill | Description |
|---------|-------------|-------------|
| `/pm-all` | `pm-all` | Full **technical** scan + dashboard (draft PRD does not block) |
| `/pm-review` | `pm-review` | Diff review with reasoning + `confirm` / `false_positive` / `later` |
| `/pm-check` | `pm-check` | Diagnose / repair `.pm/` without overwriting confirmed files |
| `/pm-arch` | `pm-arch` | Generate architecture + map + annotated tree |

### Planning & export

| Command | Agent skill | Description |
|---------|-------------|-------------|
| `/pm-outline` | `pm-outline` | Generate outline + draft charter from intent |
| `/pm-charter` | `pm-charter` | Wizard if no args: create / import / discover / approve / skip |
| `/pm-export` | `pm-export` | Desensitized markdown summary for share / machine switch |

`/pm-discover` is internal (used by `/pm-all`). Do not send users there.

Command prompts live in [`skills/pm-manager/templates/commands/`](./skills/pm-manager/templates/commands/) with Spec Kit–style frontmatter and `handoffs`.

## How it relates to Spec Kit

| Spec Kit | PM Manager |
|----------|------------|
| `.specify/` | `.pm/` (local, not committed) |
| `/speckit.constitution` | `/pm-charter` + auto-discover constitution |
| Spec → plan → tasks → implement | Status → next → done / fix / all |
| Spec-driven **feature** delivery | Governance-driven **project health** |

They can run in the **same repo**. PM Manager will read Spec Kit artifacts when present; it does not replace Spec-Driven Development.

## Core Philosophy

Governing text is Chinese-first in [`.specify/memory/constitution.md`](./.specify/memory/constitution.md) (v1.1.1). This README is English by default; [简体中文](./README.zh-CN.md) is the Chinese edition. In short:

- **Local-first durable assets** — maps, indexes, reviews, and logs live in `.pm/` (git-excluded); they survive sessions and stay auditable
- **Confirm before write** — report first; never auto-write app code/SQL/cloud or land generated docs without confirmation
- **Map-first collaboration** — agents read the navigation map and doc index before walking the tree
- **Evidence-backed quality loop** — review verdicts carry a reasoning chain; confirmed issues deposit into the rules library
- **Daily status is not capped at three** — `/pm-status` lists open blocking/high todos (no Top3 cap); paste is first-class evidence for `/pm-fix`
- **Chinese-first docs** — constitution, specs, plans, tasks, and PRDs are written in Chinese; CLI/command names stay English
- **On-demand scans** — no background daemons; paste / `--path` / registered sources
- **Charter-aware (optional)** — without a charter you get technical debt scans; with one you get scoped “unreasonable” checks **with confidence**

## Daily Workflow

| Moment | Command |
|--------|---------|
| First time in a repo | `/pm-init` (confirm or skip, then light scan) |
| Morning / “what now?” | `/pm-status` → `/pm-next` |
| Finished a todo | `/pm-done TODO-xxx` |
| Production / local error | paste + `/pm-fix` (triage only) |
| Local diff quality | `/pm-review` |
| `.pm/` looks broken | `/pm-check` |
| Before release | `/pm-all` → `.pm/dashboard/` |
| Need architecture diagrams | `/pm-arch` or `pm arch` |
| Hand-off / laptop switch | `/pm-export` |

```text
/pm-init → /pm-status → /pm-done
         ↘ /pm-fix (incidents)
         ↘ /pm-all  → .pm/dashboard/  (release gate + overview)
```

### Target `.pm/dashboard/` (after `/pm-all` or `pm dashboard`)

```text
.pm/dashboard/
  index.html    # visual dashboard — open in a browser
  overview.md   # IDE tables: KPI, bars, module risk ranking, hot/todos
  findings.md   # aggregated open findings
  todos.md      # aggregated open todos
  stats.json    # counts + health_score + module_risk
  README.md     # same as overview.md (entry alias)
```

## Repository Layout

```text
pm-manager/
  pyproject.toml                 # uv/pip package (pm / pm-manager entrypoints)
  src/pm_manager_cli/            # Cross-platform CLI (incl. pm dashboard)
  skills/pm-manager/             # Installable Agent Skill (skills.sh)
    SKILL.md                     # Router skill
    AGENTS.md                    # Agent-oriented notes
    templates/commands/          # Slash/skill command prompts
    templates/pm/                # Files copied into target .pm/
    memory/ROUTING.md            # NL → command map
  scripts/python/                # Thin wrappers (prefer `pm init`)
  scripts/powershell/            # Legacy Windows helpers
  adapters/cursor/               # Cursor skill variants
  adapters/claude-code/          # Claude Code command files
  skills.sh.json                 # skills.sh groupings
```

## Prerequisites

- **Windows / macOS / Linux**
- [uv](https://docs.astral.sh/uv/) (recommended) for `uv tool install`
- **Python 3.11+**
- **Git** (so exclude rules can be written)
- An AI coding agent that supports skills or project slash commands (Cursor or Claude Code recommended)
- Optional: [Spec Kit](https://github.com/github/spec-kit) if you already use constitution/specs

## Support

Questions and bugs: open a [GitHub issue](https://github.com/wei63w/pm-manager/issues/new).

## License

This project is licensed under the [MIT License](./LICENSE).
