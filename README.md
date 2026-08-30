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
- [Vue frontend projects](#vue-frontend-projects)
- [CLI Reference](#cli-reference)
- [Supported AI Coding Agents](#supported-ai-coding-agents)
- [Available Slash Commands](#available-slash-commands)
- [How it relates to Spec Kit](#how-it-relates-to-spec-kit)
- [Core Philosophy](#core-philosophy)
- [Daily Workflow](#daily-workflow)
- [Generated `.pm/` layout](#generated-pm-layout)
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

# Create .pm/ + install mainstream assistant adapters (default; no Node.js)
# Optional skills.sh index: pm init --skills-sh
pm init

# One host
pm init --agent cursor
pm init --agent claude

# Combine hosts, or write every registered host
pm init --agent cursor,codex,copilot
pm init --agent full

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

### Vue frontend projects

If the app's `package.json` lists `vue` or `nuxt`, `pm init` keeps the usual Python path and **also** seeds frontend defaults (no SQL/ops modules, Vue/Vite stack labels). `.vue` files join the architecture map; request-flow diagrams use Vue Router instead of an API gateway.

Without Python, scaffold only:

```bash
npx @wei63w/pm-manager init
```

Then open the same repo in Cursor and run `/pm-init`. Architecture maps, reviews, and the HTML dashboard still use `pm arch` / `pm review` / `pm dashboard` when the Python CLI is installed.

### 4. Initialize governance in your agent

Open the same project folder in your coding agent. In Cursor, start a **new** Agent chat and type `/pm`. Then run:

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
| `pm init --agent all\|full\|cursor\|claude\|…` | Choose adapters (`all` = mainstream; `full` = every registered host; comma-separated OK) |
| `pm init --scaffold-only` | Only create `.pm/` |
| `pm init --skills-sh` | Also run `npx --yes skills@latest add wei63w/pm-manager -y` (needs Node) |
| `pm install --agent …` | Refresh adapters without scaffolding |
| `pm check [path]` | Diagnose `.pm/`, map, audit, `prd.status`, pending reviews |
| `pm docs [path]` | Detect missing/stale core docs; `--draft` writes `.pm/docs/drafts/` only |
| `pm map [query]` | Query `map.json` (modules / capabilities / paths) |
| `pm status [path]` | Snapshot + todos + session intent + top suggestions |
| `pm log [text]` | Redact + classify one dialogue note (`--kind` / `--intent` / `--file`) |
| `pm journal [path]` | Refresh timeline, change points, session intent, suggestions |
| `pm dashboard [path]` | Rebuild `.pm/dashboard/` from module findings/todos |
| `pm arch [path]` | Scan → Mermaid, `map.json`, `layer.mmd`, annotated `tree.md` |
| `pm tests [path]` | List missing unit-test companions (does not write tests) |
| `pm review` | Diff draft + `--cross` + `confirm|false_positive|later` + `annotate` |
| `pm rules` | List / enable / disable / add coding rules |
| `pm checkup` | On-demand five-dimension checkup (not a cron) |
| `pm gate --path` | Pre-commit gate: secrets, syntax, rules, P0, high-risk |
| `pm hook install\|status\|uninstall` | Optional local `.git/hooks/pre-commit` (not installed by `pm init`) |
| `pm config apply <template>` | Fill missing keys from frontend/backend/service/script/auto |
| `pm export [path]` | Bundle: audit, journal, snapshot, reviews, gaps, guard, arch paths |

`pm-manager` is an alias of `pm`.

## Supported AI Coding Agents

Command prompts are generated at install time from one source: `skills/pm-manager/templates/commands/`. `pm init` (default `--agent all`) writes the **mainstream** hosts below. Use `--agent full` for the rest of the registry, or `--agent cursor,gemini` to pick.

| Agent | `--agent` | Install path | How you invoke |
|-------|-----------|--------------|----------------|
| **Cursor** | `cursor` | `.cursor/skills/pm-*` | New Agent chat, type `/pm` |
| **Claude Code** | `claude` | `.claude/skills/pm-*` + `.claude/commands/pm-*.md` | `/pm-init` |
| **Codex / Zed** | `codex` | `.agents/skills/pm-*` | skill `pm-init` / `$pm-init` |
| **GitHub Copilot** | `copilot` | `.github/skills/pm-*` | Copilot Chat skill `pm-init` |
| **Windsurf** | `windsurf` | `.windsurf/workflows/pm-*.md` | `/pm-init` |
| **Gemini CLI** | `gemini` | `.gemini/commands/pm-*.toml` | `/pm-init` |
| **Qwen Code** | `qwen` | `.qwen/commands/pm-*.md` | `/pm-init` |
| **opencode** | `opencode` | `.opencode/commands/pm-*.md` | `/pm-init` |
| **Kilo Code** | `kilocode` | `.kilo/commands/pm-*.md` | `/pm-init` |
| **Trae** | `trae` | `.trae/skills/pm-*` | `/pm-init` |
| **Auggie** | `auggie` | `.augment/commands/pm-*.md` | `/pm-init` |
| **Cline** | `cline` | `.clinerules/workflows/pm-*.md` | `/pm-init` |

Also registered (use `--agent <key>` or `--agent full`): `grok`, `droid`, `lingma`, `kimi`, `zcode`, `command-code`, `qoder`, `alquimia`, `devin`, `codebuddy`, `junie`, `shai`, `omp`, `firebender`, `tabnine`, `kiro`, `pi`.

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
| `/pm-review` | `pm-review` | Diff review + cross-check + dispose into rules |
| `/pm-checkup` | `pm-checkup` | On-demand checkup (P0/P1/P2); not part of daily status |
| `/pm-check` | `pm-check` | Diagnose / repair `.pm/` without overwriting confirmed files |
| `/pm-arch` | `pm-arch` | Generate architecture + map + annotated tree |
| `/pm-docs` | `pm-docs` | Missing/stale docs; draft under `.pm/` until confirm |
| `/pm-journal` | `pm-journal` | Session intent, timeline, change points, suggestions |
| `/pm-tests` | `pm-tests` | Missing unit-test companions; confirm before writing tests |

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

After a scan, open **`.pm/dashboard/index.html`** in a browser (or `overview.md` in the IDE). The full folder map is below.

## Generated `.pm/` layout

`pm init` / `/pm-init` creates a **git-excluded** `.pm/` workbench in the **target** repo (written to `.git/info/exclude`, never to a shared `.gitignore`). Later `/pm-*` / `pm` commands fill more folders. Nothing here is meant to be committed.

```text
.pm/
  config/            # project + machine-local settings
  state/             # live board: status, todos, journal, indexes
  prd/               # product draft (confirm before using as baseline)
  charter/           # goals, REQs, NFR, DoD
  outline/           # epics / milestones
  architecture/      # map.json, Mermaid, annotated tree (+ scan module)
  dashboard/         # HTML/MD health board
  engineering/       # reviews + rules library (+ scan module)
  evidence/scans/    # redacted scan JSON
  inbox/stacks/      # optional stack dumps for /pm-fix
  bugs/              # incident findings (+ incidents/)
  environments/      # scan module
  integration/       # scan module
  testing/           # scan module
  release/           # scan module
  database/          # scan module (often off for Vue frontend)
  operations/        # scan module (often off for Vue frontend)
  cost/              # scan module (often off for Vue frontend)
  docs/              # on demand — doc drafts until you confirm
  reviews/           # on demand — annotate backfill only
  exports/           # on demand — shareable summaries
```

Vue / Nuxt projects keep the same tree; `pm init` may turn off `database` / `operations` / `cost` in `config/project.yaml` so those modules stay empty.

### Core folders (created at init)

| Folder | Purpose |
|--------|---------|
| `config/` | `project.yaml` (stack, lifecycle, PRD/charter status, which modules are on, scan excludes) and `local.yaml` (machine paths / credential *refs* — never raw secrets). |
| `state/` | Living board. Starts with `overview.md`, `todo.md`, `completed.md`, `doc-index.md`, `audit.jsonl`, `dialogue.md`. Later commands add `report.md`, journal (`session.json`, `timeline.md`, `changes.md`, `suggestions.md`), `checkup.md`, `test-gaps.md`, `guard.md`, `review-draft.md`. **`todo.md` is the authority** for `/pm-status` / `/pm-next` / `/pm-done`. |
| `prd/` | `.pm/prd/prd.md` — drafted by `/pm-init`. Stays `draft` until you **confirm**; unconfirmed PRDs must not be used as an acceptance baseline. |
| `charter/` | `charter.md` (goals / scope), `requirements.md` (`REQ-xxx`), `nfr.md`, `dod.md`, `sources.md`. Filled from Spec Kit, a confirmed PRD, or `/pm-charter` / `/pm-outline`. `charter.status=approved` is optional; only then may scans compare “is this unreasonable?”. |
| `outline/` | `project-outline.md`, `epics.md`, `milestones.md` from `/pm-outline`. |
| `architecture/` | After `/pm-arch` / `pm arch`: `map.json` (navigation map — agents read this first), Mermaid (`system-context.mmd`, `layer.mmd`, `request-flow.mmd`, …), annotated `tree.md`, `overview.md`, `scan.json`. Also a scan module (checklist / findings / todos). |
| `dashboard/` | Rebuilt by `/pm-all` or `pm dashboard`: `index.html` (browser), `overview.md` / `README.md` (IDE), `findings.md`, `todos.md`, `stats.json` (counts, `health_score`, module risk). |
| `engineering/` | `reviews.md` (disposition table: confirm / false_positive / later) and `rules.md` (only **confirmed** findings become enabled rules). Also a scan module. |
| `evidence/scans/` | Per-command JSON after desensitization (`{command}-{timestamp}.json`). Raw secrets must never land here. |
| `inbox/stacks/` | Optional drop zone for stack traces / logs when you are not pasting into chat. `/pm-fix` prefers the current conversation paste first. |
| `bugs/` | Incident module: `/pm-fix` appends `findings.md` + todos. `bugs/incidents/` holds structured incident notes. |

Each **scan module** (`bugs`, `architecture`, `engineering`, `environments`, `integration`, `testing`, `release`, `database`, `operations`, `cost`) starts with the same four files: `checklist.md`, `findings.md`, `todo.md`, `completed.md`. Module todos roll up into `state/todo.md`; dashboard aggregates the open ones.

| Module | Tracks |
|--------|--------|
| `bugs/` | Production / local incidents from `/pm-fix` |
| `architecture/` | Map / diagram / structure health |
| `engineering/` | Code-quality / review follow-ups |
| `environments/` | Env, config, deploy-target drift |
| `integration/` | Third-party, CI, service boundaries |
| `testing/` | Test gaps and quality findings (`/pm-tests` also writes `state/test-gaps.md`) |
| `release/` | Release-gate leftovers |
| `database/` | Schema / SQL / migration findings |
| `operations/` | Runtime / ops findings |
| `cost/` | Cost / resource findings |

### Folders created later (on demand)

| Folder | Created by | Purpose |
|--------|------------|---------|
| `docs/drafts/` | `pm docs --draft` / `/pm-docs` | Editable `DOC-*.md` skeletons for missing core docs. **Confirm** before copying to `.pm/docs/` or a path you name (`docs/*.md`). Unconfirmed drafts must not land in the business tree. |
| `reviews/annotations/` | `pm review annotate` / `/pm-review` | Backfill notes only. Does not patch application code. Confirmed rows go to `engineering/rules.md`. |
| `exports/` | `pm export` / `/pm-export` | Desensitized Markdown bundle (default `pm-export-YYYYMMDD.md`) for hand-off or switching machines. |

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
  packages/npx-cli/              # Optional Node init (`npx @wei63w/pm-manager init`)
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
