---
name: "pm-done"
description: "PM Manager /pm-done"
---

﻿---
description: Close a todo (TODO-xxx), sync completed.md, refresh overview.
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
5. Refresh overview; confirm the item is no longer in the open blocking/high list.


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
9. **Closing:** `templates/commands/_closing.md` **轻量**档（1–2 个已存在链接）。中文摘要。

Design baseline: `docs/prd.md` + 宪章。
