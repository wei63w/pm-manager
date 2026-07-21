---
name: pm-discover
description: >-
  Deep-scan all enabled governance modules and refresh state (internal; used by pm-all / status --full). Trigger on /pm-discover and related English phrases for this command.
---

# /pm-discover

Follow the workflow below exactly. Scaffold helper: `pm init` or `scripts/python/create_pm_scaffold.py`.

When resolving pack files, prefer the `pm-manager` directory that contains this skill's sibling `templates/` (or the project skill pack root).



## User Input

```text
$ARGUMENTS
```

## Outline

1. Require init. For each enabled module, perform on-demand technical scan + optional charter compare.
2. Incremental merge; suppress duplicate evidence hashes.
3. Refresh state overview/todo.
4. Keep chat brief unless `--verbose`.


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

