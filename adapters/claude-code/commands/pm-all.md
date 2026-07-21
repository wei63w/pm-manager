---
description: Orchestrate full governance scan with prerequisite gates; default noise-filtered summary; rebuild .pm/dashboard aggregate.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Summarize after full scan
    send: true
---

## User Input

```text
$ARGUMENTS
```

Flags: `--skip-charter-gate`, `--modules=...`, `--path=...`, `--verbose`.

## Outline

1. Gate: `.pm` initialized? else **block** → recommend `/pm-init`.
2. Gate: new project without charter/outline? **wait** with choices: outline | charter | skip (`--skip-charter-gate`).
3. Run module scans (arch, engineering, env, api, test, release, db, ops, cost) then bugs if log sources/`--path`/paste exist; else skip bugs with recommendation.
   - Architecture step **must** produce diagrams: run `pm arch` / `/pm-arch` → `.pm/architecture/*.mmd` + `overview.md`.
4. Merge findings/todos; write `evidence/scans/pm-all-*.json`.
5. **Rebuild the dashboard** (required):
   - Prefer running: `pm dashboard` (from project root)
   - Or regenerate `.pm/dashboard/` yourself with the same contents described below
   - Output files:
     - `.pm/dashboard/index.html` — visual KPI / charts / risk tables (open in browser)
     - `.pm/dashboard/overview.md` (and `README.md` mirror) — IDE tables: KPI, bars, module risk ranking, hot list, todos
     - `.pm/dashboard/findings.md` — all open findings across modules
     - `.pm/dashboard/todos.md` — all open todos across modules
     - `.pm/dashboard/stats.json` — machine-readable counts (+ health_score, module_risk)
   - Purpose: one place to review health **without opening each module folder**
6. Chat summary: blocking+high + Top3 only unless `--verbose`.
7. **Required closing**: follow `templates/commands/_closing.md` — print Summary + **Open these** links (at least `.pm/dashboard/index.html` and `overview.md`; include `.pm/architecture/overview.md` after arch). Explicitly ask the user to open them.
8. Finish with `/pm-status` style health line.


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. After multi-module updates (`/pm-all`, `/pm-discover`), rebuild `.pm/dashboard/` via `pm dashboard`.
8. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

9. **Closing (required):** end the user-facing reply with Summary + Open these links per `templates/commands/_closing.md` (dashboard and/or architecture overviews). Ask the user to open them.

Design baseline: local `pm-manager-v*.md` (not published).
