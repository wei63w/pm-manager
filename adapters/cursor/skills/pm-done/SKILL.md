---
description: Close a todo (TODO-xxx), sync completed.md, refresh overview Top3.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Refresh status after closing todo
    send: true
---

## User Input

```text
$ARGUMENTS
```

Usage: `TODO-001` | `TODO-001 --note "..."` | `TODO-001 --start` (only in_progress).

## Outline

1. Parse TODO id. Require it exists in `state/todo.md`.
2. `--start` → `in_progress` only.
3. Else → `done`, append to `state/completed.md` and module `completed.md`, remove/mark done in state todo.
4. If linked finding has no other open todos → `resolved`.
5. Refresh overview; confirm item left Top3.


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
