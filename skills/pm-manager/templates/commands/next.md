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
2. Pick the first open/in_progress item ordered by blocking>high, then P0>P1 (no 3-item cap).
3. Unless `--peek`, set status `in_progress` in state + module mirror.
4. Print task, evidence link, suggested action; remind `/pm-done TODO-id`.


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
9. **Closing:** `templates/commands/_closing.md` **轻量**档。中文摘要。

Design baseline: `docs/prd.md` + 宪章。
