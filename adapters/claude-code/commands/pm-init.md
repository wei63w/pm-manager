---
description: Initialize local .pm governance; detect Spec Kit; if absent, analyze the repo and draft a PRD for user confirmation; after confirm/skip run a technical light scan.
handoffs:
  - label: Project status
    agent: pm.status
    prompt: Show project governance status
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Accepted extra words: `confirm` | `approve` | `revise: <notes>` | `skip` | a one-line project intent.

## Outline

You are running `/pm-init` for the **current workspace project root**.

User-facing replies must be **Chinese** when the user writes Chinese. Command names stay `/pm-*`.

### 1. Scaffold

Preferred: `pm init <root>` (creates `.pm/`, git exclude, adapters). CLI no longer runs skills.sh unless `--skills-sh`.

Fallbacks: `npx @wei63w/pm-manager init`, `scripts/powershell/create-pm-scaffold.ps1`, `python scripts/python/create_pm_scaffold.py`, or copy `templates/pm/` by hand.

Do **not** overwrite user-edited files under `.pm/`. Never overwrite `prd.status=confirmed` or `charter.status=approved`.

### 2. Lifecycle and type

- `new`: empty or scaffold-only (README / `.git` only, no business source).
- `existing`: build files, `src` / `app` / `lib`, or app config present.

If `project.type` is `unknown` / empty, infer from manifests (`package.json` with vue/nuxt deps → vue, other `package.json` → node, `pyproject.toml` → python, `go.mod` → go, `pom.xml` / `build.gradle` → java, `Cargo.toml` → rust). Do not invent a stack. Write `project.lifecycle` and `project.type` on `.pm/config/project.yaml`. If type is `vue` and fields still match scaffold defaults, apply Vue frontend seeds (`modules.database/operations/cost: false`, Vite/Vue runtime on `stack`, extra scan excludes).

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
5. **Stop** and ask the user to **confirm** / **revise** / **skip** (Chinese prompt).
6. Do not run a module deep-scan yet.

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
- **If Vue** (`package.json` deps contain `vue` or `nuxt`): also `vite.config.*` / `nuxt.config.*` and `src/components` / `views` / `pages` / `router` / `stores` / `composables`. In 「当前产品（据仓库观察）」cite framework, router, store, and build tool with paths. Never invent.

Then write a complete draft to `.pm/prd/prd.md`:

- Problem, users, goals, not-goals
- Current product **as observed** (cite paths)
- REQ table (only evidenced behavior)
- Success + open questions
- Status line: `draft`, `source=generated`

Rules:

- Unknown → write `信息不足`. Never invent users, revenue, or roadmap.
- Do not write the repo's `docs/prd.md` unless the user explicitly asks.
- Set `prd.status=draft` on `project.yaml`. Sync a short draft into `.pm/charter/` (still draft).

**Stop.** Show a short PRD summary (≤ 20 lines) and wait:

```text
PRD 草稿：`.pm/prd/prd.md`

请回复其一：
- confirm — 把这份说明当作治理基线
- revise: <要改什么>
- skip — 本次不要 PRD 基线（仍可做技术扫描）
```

If this repo is Vue, add one extra line: 纯前端可先 `skip`，仍做技术轻扫。

#### D. No Spec Kit — new / empty repo

- If the user already gave a one-line intent → fill `.pm/prd/prd.md` from that intent, then ask confirm.
- Else ask **one** question: the project intent. Do not ask a long intake form.

### 5. Confirm / revise / skip (same session or later `/pm-init confirm`)

- **confirm**: `prd.status=confirmed`. Sync goals / scope / REQs into `.pm/charter/`. `charter.status=draft`. Tell the user they can later `/pm-charter approve` if they want charter-gated compare — **not required** for technical scans.
- **revise: …**: edit `.pm/prd/prd.md`, keep `draft`, ask confirm again.
- **skip**: `prd.status=skipped`. Do not pretend a baseline exists.

Never overwrite `prd.status=confirmed` or `charter.status=approved` on a later init — only notify if sources changed.

### 6. Process mode

If still unset: default `agile`, iteration `2w`. Ask only if the user did not give a mode.

### 7. After confirm or skip — technical light scan (required)

Do **not** wait for `/pm-all` or `/pm-discover`. Immediately:

1. Prefer `pm docs` to refresh `.pm/state/doc-index.md` (AGENTS.md/agent.md, PRD, design, API, deploy, trouble-shoot). If CLI unavailable, update the index yourself.
2. Prefer `pm arch` to write `.pm/architecture/map.json` + Mermaid + `tree.md`. Incremental if a map already exists.
3. Rebuild overview with the **wizard** empty-state (missing PRD / missing map / missing dashboard / next command). Do not write “没有待办，去跑 /pm-all”.
4. If core docs are missing, ask: 用户自备 **或** AI 起草。AI 草稿可编辑，未确认不得覆盖正式路径。
5. Optional: `pm dashboard` so `.pm/dashboard/` exists after first init.

Do **not** run a full module deep-scan here. Deep scan is `/pm-all` (default technical, no PRD gate).

### 8. Overview + dialogue

Refresh `state/overview.md` with: lifecycle, type, Spec Kit yes/no, `prd.status`, wizard next step (`confirm` or `/pm-status`).

Prefer **`pm log --kind consult --intent "…"`** (or the user's one-line intent) so the CLI redacts and refreshes `.pm/state/dialogue.md` + timeline. If CLI is unavailable, append the same fields yourself. Unclear → `unresolved`; never invent file lists. Then `pm journal` is optional.

If `.pm/` metadata is already valid, **do not** force a full-repo rescan; load assets and only incrementally refresh.

If metadata looks corrupt, tell the user and run `/pm-check` repair or increment — do not silently treat as empty.

## Done When

- [ ] `.pm/` tree exists (config / state / charter / prd / outline)
- [ ] `.git/info/exclude` contains `.pm/` when git is present
- [ ] Spec Kit detection recorded
- [ ] If no Spec Kit: draft PRD written **or** user was asked for intent **or** user skipped
- [ ] User was asked to confirm before treating the PRD as baseline
- [ ] After confirm/skip: doc index + architecture map refreshed (or explicitly failed with a next step)

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
9. **Closing:** follow `templates/commands/_closing.md` (graded; only existing paths).

Design baseline: `docs/prd.md` + 宪章（中文优先）。
