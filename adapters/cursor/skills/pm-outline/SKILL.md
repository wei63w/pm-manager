---
description: Generate detailed project outline and draft charter from user intent (empty/new projects).
handoffs:
  - label: Approve charter
    agent: pm.charter
    prompt: Approve the generated charter
  - label: Full scan
    agent: pm.all
    prompt: Run full scan after outline
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Require init. Collect intent: goal, users, features, non-goals, stack prefs, timeline, process.mode.
2. Write `.pm/outline/project-outline.md`, `epics.md`, `milestones.md`.
3. Sync draft `.pm/charter/*` (REQ-xxx); set outline/charter status draft, source generated.
4. Do **not** write application source code.
5. Do **not** treat the outline/charter as acceptance criteria until `/pm-charter approve` (or `/pm-init confirm` for PRD).
6. Recommend `/pm-init confirm` or `/pm-charter` 向导；技术扫描用 `/pm-all`（不必先 approve）。


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
9. **Closing:** `_closing.md` 完整档（只列已有路径）。

Design baseline: `docs/prd.md` + 宪章。
