---
description: Initialize local .pm governance workbench; detect new vs existing project; discover Spec Kit constitution; optional outline from intent.
handoffs:
  - label: Project status
    agent: pm.status
    prompt: Show project governance status and today's Top3
  - label: Full scan
    agent: pm.all
    prompt: Run full governance scan
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). User input may include: process mode, project intent one-liner, or `skip` charter.

## Outline

You are running `/pm-init` for the **current workspace project root**.

1. **Detect lifecycle**
   - `new`: empty or scaffold-only (README/.git only, no pom/gradle/src business code)
   - `existing`: build files, source tree, or app config present
   - If `.specify/` exists, mark Spec Kit project and prioritize constitution/specs.

2. **Run scaffold** (preferred):
   - CLI: `pm init <root>` (also runs non-interactive `npx skills add wei63w/pm-manager -y` unless `--no-skills-sh` / `--scaffold-only`)
   - PowerShell: `scripts/powershell/create-pm-scaffold.ps1 -ProjectRoot <root>`
   - Or Python: `python scripts/python/create_pm_scaffold.py <root>`
   - If scripts unavailable, create the same directory tree manually from `templates/pm/`.

3. **Ensure git exclude** (not `.gitignore`):
   - Append `.pm/` to `<root>/.git/info/exclude` if git repo and not already present.

4. **Process mode**
   - Ask if missing: `agile` | `kanban` | `waterfall` | `custom` (default agile, iteration `2w`).

5. **Charter discovery** (scan in order from `charter_candidates` in project.yaml template):
   - `.specify/memory/constitution.md` → map into `.pm/charter/charter.md` + dod hints
   - `.specify/specs/**/spec.md` → requirements REQ-xxx
   - `CONSTITUTION.md`, `docs/prd.md`, `docs/requirements.md`, `docs/nfr.md`
   - `README.md` only as last-resort fallback
   - Write `.pm/charter/sources.md`; set `charter.status=draft`, `source=discovered`
   - Do **not** overwrite `approved` charter; only notify if external source changed.

6. **If new and no charter candidates**
   - If user provided intent → run outline generation (same as `/pm-outline`)
   - Else offer: paste intent | `/pm-charter` | `skip` (`charter.status=absent`)

7. **Do NOT deep-scan** all modules (leave to `/pm-discover` or `/pm-all`).

8. Write initial `state/overview.md` and summarize:
   - lifecycle, process.mode, charter status, recommended next: `/pm-status` or `/pm-all`

## Done When

- [ ] `.pm/` tree exists with config/state/charter/outline/inbox/evidence
- [ ] `.git/info/exclude` contains `.pm/` when git is present
- [ ] User told next command clearly


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

9. **Closing (required):** end the user-facing reply with Summary + Open these links per `templates/commands/_closing.md` (dashboard and/or architecture overviews). Ask the user to open them.

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).
