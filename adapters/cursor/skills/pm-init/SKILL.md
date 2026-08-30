---
description: Initialize local .pm governance; detect Spec Kit; if absent, analyze the repo and draft a PRD for user confirmation.
handoffs:
  - label: Project status
    agent: pm.status
    prompt: Show project governance status
  - label: Full scan
    agent: pm.all
    prompt: Run full governance scan
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Accepted extra words: `confirm` | `approve` | `revise: <notes>` | `skip` | a one-line project intent.

## Outline

You are running `/pm-init` for the **current workspace project root**.

### 1. Scaffold

Preferred: `pm init <root>` (creates `.pm/`, git exclude, adapters).

Fallbacks: `scripts/powershell/create-pm-scaffold.ps1`, `python scripts/python/create_pm_scaffold.py`, or copy `templates/pm/` by hand.

Do **not** overwrite user-edited files under `.pm/`.

### 2. Lifecycle

- `new`: empty or scaffold-only (README / `.git` only, no business source).
- `existing`: build files, `src` / `app` / `lib`, or app config present.

Write `project.lifecycle` on `.pm/config/project.yaml` if still empty.

### 3. Detect Spec Kit (required)

Treat the repo as **using Spec Kit** only if either exists:

- `.specify/memory/constitution.md`
- at least one `.md` under `.specify/specs/`

An empty `.specify/` directory does **not** count.

Write `speckit.present` / `constitution` / `specs` on `project.yaml`.

### 4. Branch

#### A. Spec Kit is present

1. Map constitution → `.pm/charter/charter.md` + DoD hints.
2. Map `.specify/specs/**/*.md` → `.pm/charter/requirements.md` (`REQ-xxx`).
3. Write `.pm/charter/sources.md`. Set `charter.status=draft`, `source=discovered`, `prd.source=speckit`, `prd.status=draft`.
4. **Do not** invent a competing PRD that disagrees with Spec Kit.
5. **Stop** and ask the user to **confirm** / **revise** / **skip**.
6. Do not run a module deep-scan.

#### B. No Spec Kit — repo already has a real product doc

If `docs/prd.md`, `docs/requirements.md`, or `PRD.md` exists and is substantial (not a stub):

1. Import into `.pm/prd/prd.md` (`source=imported`, `status=draft`).
2. Summarize in chat (problem / goals / REQ count). Do not rewrite from scratch.
3. **Stop** and ask **confirm** / **revise** / **skip**.

#### C. No Spec Kit — existing project

Analyze **only** these (no `/pm-all`, no module-by-module deep review):

- README (and short docs titles under `docs/`)
- Manifests: `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`, compose files
- Top two directory levels of `src` / `app` / `apps` / `lib` / `cmd` (skip `node_modules`, `target`, `.git`, `dist`, `build`)

Then write a complete draft to `.pm/prd/prd.md`:

- Problem, users, goals, not-goals
- Current product **as observed** (cite paths)
- REQ table (only evidenced behavior)
- Success + open questions
- Status line: `draft`, `source=generated`

Rules:

- Unknown → write `Information missing`. Never invent users, revenue, or roadmap.
- Do not write the repo's `docs/prd.md` unless the user explicitly asks.
- Set `prd.status=draft` on `project.yaml`. Sync a short draft into `.pm/charter/` (still draft).

**Stop.** Show a short PRD summary (≤ 20 lines) and wait:

```text
Draft PRD: `.pm/prd/prd.md`

Reply with one of:
- confirm — use this as the governance baseline
- revise: <what to change>
- skip — no PRD baseline this time
```

#### D. No Spec Kit — new / empty repo

- If the user already gave a one-line intent → same as `/pm-outline`, plus fill `.pm/prd/prd.md`, then ask confirm.
- Else ask **one** question: the project intent. Do not ask a long intake form.

### 5. Confirm / revise / skip (same session or later `/pm-init confirm`)

- **confirm**: `prd.status=confirmed`. Sync goals / scope / REQs into `.pm/charter/`. `charter.status=draft`. Tell the user they can `/pm-charter approve` when ready.
- **revise: …**: edit `.pm/prd/prd.md`, keep `draft`, ask confirm again.
- **skip**: `prd.status=skipped`. Do not pretend a baseline exists.

Never overwrite `prd.status=confirmed` or `charter.status=approved` on a later init — only notify if sources changed.

### 6. Process mode

If still unset: default `agile`, iteration `2w`. Ask only if the user did not give a mode.

### 7. Do not deep-scan

Leave module scans to `/pm-discover` or `/pm-all` **after** the user confirms or skips the PRD.

### 8. Overview

Refresh `state/overview.md` with: lifecycle, Spec Kit yes/no, `prd.status`, recommended next (`confirm` or `/pm-status`).

### 9. Core docs + dialogue

After baseline branch (A/B/C/D), prefer **`pm docs`** to refresh `.pm/state/doc-index.md` for the closed set: AGENTS.md/agent.md, PRD, design, API, deploy, trouble-shoot. If the CLI is unavailable, update the index yourself. If missing, ask: user upload/manual **or** AI draft. AI drafts MUST remain editable and MUST NOT overwrite the official path until the user confirms.

Append a short desensitized dialogue note to `.pm/state/dialogue.md` (kind + intent files if parseable; else `unresolved` — never invent file lists).

If `.pm/` metadata is already valid, **do not** force a full-repo rescan; load assets and only incrementally refresh.

If metadata looks corrupt, tell the user and repair or increment — do not silently treat as empty.

## Done When

- [ ] `.pm/` tree exists (config / state / charter / prd / outline)
- [ ] `.git/info/exclude` contains `.pm/` when git is present
- [ ] Spec Kit detection recorded
- [ ] If no Spec Kit: draft PRD written **or** user was asked for intent **or** user skipped
- [ ] User was asked to confirm before treating the PRD as baseline

## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. If `.pm/` metadata is valid, load it; do **not** force a full-repo rescan. On-demand **incremental** scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`). Prefer `.pm/architecture/map.json` and the document index before walking the tree.
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`). Never persist raw secrets.
4. Optional charter compare only when `charter.status == approved` (attach `confidence`). Draft PRD/charter MUST NOT be used as the baseline.
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` with **all** open/in_progress blocking+high todos (no 3-item cap). Medium/low: counts only unless `--verbose`.
7. Append audit to `.pm/state/audit.jsonl` (command, time, input/output summary; include reasoning when the step was AI-produced).
8. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud or land generated docs/rules without explicit user confirmation.
9. **Closing (required):** end with Summary + Open these links per `templates/commands/_closing.md`. Ask the user to open them.

Design baseline: `docs/prd.md` + `docs/design.md` in this pack (not unpublished `pm-manager-v*.md`).
