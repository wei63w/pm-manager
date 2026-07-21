**📋 PM Manager**  
*Know what to fix next — with any AI coding agent.*

An open source skill pack for **local project governance** — init a `.pm/` workbench, keep a daily Top3, triage pasted logs, and run release-ready health scans. Inspired by [Spec Kit](https://github.com/github/spec-kit)’s command-template + multi-agent adapter model. Works alongside Spec Kit: Spec Kit drives *what to build*; PM Manager drives *project health and what’s next*.



---



## Table of Contents

- [What is PM Manager?](#-what-is-pm-manager)
- [Get Started](#-get-started)
- [CLI Reference](#-cli-reference)
- [Supported AI Coding Agents](#-supported-ai-coding-agents)
- [Available Slash Commands](#-available-slash-commands)
- [How it relates to Spec Kit](#-how-it-relates-to-spec-kit)
- [Core Philosophy](#-core-philosophy)
- [Daily Workflow](#-daily-workflow)
- [Repository Layout](#-repository-layout)
- [Prerequisites](#-prerequisites)
- [Support](#-support)
- [License](#-license)



## What is PM Manager?

Most AI coding sessions jump straight into code. **PM Manager flips the day-to-day loop**: keep a local, auditable `.pm/` board for health, todos, incidents, and release gates — then let the agent recommend **at most three things to do today**.

It is **not** a cloud PM suite and **not** a replacement for Jira/Linear. It is a **developer-side governance workbench** that lives in your repo’s local `.pm/` directory (git-excluded), driven by slash commands / skills the same way Spec Kit drives `/speckit.`*.

## Get Started



### 1. Install the CLI (cross-platform)

Requires **[uv](https://docs.astral.sh/uv/)** and **Python 3.11+**.

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



### 2. Bootstrap a project

In your **application** repository (not required to keep this pack checked out):

```bash
cd /path/to/your-app

# Create .pm/ + install Cursor & Claude adapters (default)
pm init

# Cursor only
pm init --agent cursor

# Claude Code only
pm init --agent claude

# Scaffold .pm/ only (no agent files)
pm init --scaffold-only
```

Refresh adapters without re-scaffolding:

```bash
pm install --agent all
pm check
```

> Windows / macOS / Linux all use the same commands. Legacy PowerShell helpers under `scripts/powershell/` still work, but `pm init` **is preferred**.



### 3. Initialize governance in your agent

Open Cursor / Claude Code in the project and run:

```text
/pm-init
```

- Detects **new vs existing** projects  
- Discovers Spec Kit `.specify/memory/constitution.md` (and other charter candidates) when present  
- For empty projects, accepts a one-line intent to generate an outline  
- Complements the filesystem scaffold from `pm init` (agent fills charter/overview)



### 4. Check today's Top3

```text
/pm-status
```

You’ll get a short health line and **up to three** actionable todos. Claim one with `/pm-next`, close it with `/pm-done TODO-001`.

### 5. Triage an incident

Paste a stack trace or log into the chat:

```text
/pm-fix
```

Conversation paste is a first-class evidence source (no need to save a file first).

### 6. Pre-release full scan

```text
/pm-all
```

Runs gated full governance with a **noise-filtered** summary (blocking + high by default). Use `--verbose` for the long list.

## CLI Reference


| Command                                  | Description                            |
| ---------------------------------------- | -------------------------------------- |
| `pm version`                             | Print CLI version                      |
| `pm init [path]`                         | Create `.pm/` + install agent adapters |
| `pm init --agent cursor|claude|all|none` | Choose which adapters to install       |
| `pm init --scaffold-only`                | Only create `.pm/`                     |
| `pm install --agent …`                   | Refresh adapters without scaffolding   |
| `pm check [path]`                        | Show whether `.pm/` and adapters exist |


`pm-manager` is an alias of `pm`.

## Supported AI Coding Agents


| Agent                 | Install path                                                                               | How you invoke                                            |
| --------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| **Cursor**            | `.cursor/skills/pm-manager` (+ optional per-command skills under `adapters/cursor/skills`) | `/pm-init`, `/pm-status`, … or natural language ("what should I do today") |
| **Claude Code**       | `.claude/commands/pm-*.md`                                                                 | `/pm-init`, `/pm-status`, …                               |
| **Other skill hosts** | Use root `SKILL.md` as a router into `templates/commands/`                                 | Follow host skill conventions                             |


Natural-language routing (when slash commands are unavailable) is documented in `[memory/ROUTING.md](./memory/ROUTING.md)`.

## Available Slash Commands



### Daily commands (remember these)


| Command      | Agent skill | Description                                               |
| ------------ | ----------- | --------------------------------------------------------- |
| `/pm-init`   | `pm-init`   | Create `.pm/`, detect lifecycle, discover charter sources |
| `/pm-status` | `pm-status` | Health summary + **Today's Top3** (primary daily entry)        |
| `/pm-next`   | `pm-next`   | Claim the next todo (`in_progress`)                       |
| `/pm-done`   | `pm-done`   | Close `TODO-xxx`, refresh overview                        |
| `/pm-fix`    | `pm-fix`    | Parse pasted logs/stacks into bugs + todos                |
| `/pm-all`    | `pm-all`    | Full gated scan with quiet summary                        |




### Planning & export


| Command       | Agent skill  | Description                                              |
| ------------- | ------------ | -------------------------------------------------------- |
| `/pm-outline` | `pm-outline` | Generate outline + draft charter from intent             |
| `/pm-charter` | `pm-charter` | create / import / discover / approve / skip charter      |
| `/pm-export`  | `pm-export`  | Desensitized markdown summary for share / machine switch |




### Internal (usually via `/pm-all`)


| Command        | Agent skill   | Description                   |
| -------------- | ------------- | ----------------------------- |
| `/pm-discover` | `pm-discover` | Deep-scan all enabled modules |


Command prompts live in `[templates/commands/](./templates/commands/)` with Spec Kit–style frontmatter and `handoffs`.

## How it relates to Spec Kit


| Spec Kit                         | PM Manager                                 |
| -------------------------------- | ------------------------------------------ |
| `.specify/`                      | `.pm/` (local, not committed)              |
| `/speckit.constitution`          | `/pm-charter` + auto-discover constitution |
| Spec → plan → tasks → implement  | Status → Top3 → done / fix / all           |
| Spec-driven **feature** delivery | Governance-driven **project health**       |


They can run in the **same repo**. PM Manager will read Spec Kit artifacts when present; it does not replace Spec-Driven Development.

## Core Philosophy

- **Simple daily UX** — few entry commands; Top3 over long finding dumps  
- **Local & auditable** — evidence and todos stay in `.pm/` with redaction  
- **On-demand scans** — no background daemons; paste / `--path` / registered sources  
- **Safe defaults** — report first; never auto-write app code/SQL/cloud without confirmation  
- **Charter-aware (optional)** — without a charter you get technical debt scans; with one you get scoped “unreasonable” checks **with confidence**



## Daily Workflow


| Moment                   | Command                   |
| ------------------------ | ------------------------- |
| First time in a repo     | `/pm-init`                |
| Morning / “what now?”    | `/pm-status` → `/pm-next` |
| Finished a todo          | `/pm-done TODO-xxx`       |
| Production / local error | paste + `/pm-fix`         |
| Before release           | `/pm-all`                 |
| Hand-off / laptop switch | `/pm-export`              |


```text
/pm-init → /pm-status → /pm-done
         ↘ /pm-fix (incidents)
         ↘ /pm-all  (release gate)
```



## Repository Layout

```text
pm-manager/
  pyproject.toml           # uv/pip package (pm / pm-manager entrypoints)
  src/pm_manager_cli/      # Cross-platform CLI
  SKILL.md                 # Router skill
  AGENTS.md                # Agent-oriented notes
  templates/commands/      # Slash/skill command prompts
  templates/pm/            # Files copied into target .pm/
  scripts/python/          # Thin wrappers (prefer `pm init`)
  scripts/powershell/      # Legacy Windows helpers
  adapters/cursor/         # Cursor skill variants
  adapters/claude-code/    # Claude Code command files
  memory/ROUTING.md        # NL → command map
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