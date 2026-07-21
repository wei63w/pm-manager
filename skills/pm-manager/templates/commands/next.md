---
description: Claim the single next governance todo (marks in_progress).
handoffs:
  - label: Mark done
    agent: pm.done
    prompt: Mark the current todo done
---

## User Input

```text
$ARGUMENTS
```

Optional: `--peek` (do not mark in_progress).

## Outline

1. Require init. Read `state/todo.md`.
2. Pick first Top3-ordered open/in_progress item.
3. Unless `--peek`, set status `in_progress` in state + module mirror.
4. Print task, evidence link, suggested action; remind `/pm-done TODO-id`.


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
