---
name: pm-outline
description: >-
  Generate detailed project outline and draft charter from user intent (empty/new projects). Trigger on /pm-outline and related English phrases for this command.
---

# /pm-outline

Follow the workflow below exactly. Scaffold helper: \pm init\ or \scripts/python/create_pm_scaffold.py\.

When resolving pack files, prefer the \pm-manager\ directory that contains this skill's sibling \	emplates/\ (or the project skill pack root).



## User Input

```text
$ARGUMENTS
```

## Outline

1. Require init. Collect intent: goal, users, features, non-goals, stack prefs, timeline, process.mode.
2. Write `.pm/outline/project-outline.md`, `epics.md`, `milestones.md`.
3. Sync draft `.pm/charter/*` (REQ-xxx); set outline/charter status draft, source generated.
4. Do **not** write application source code.
5. Recommend review + `/pm-charter approve` then `/pm-all` or `/pm-status`.


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).

