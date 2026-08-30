---
description: Export desensitized governance summary markdown for sharing or machine switch.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Prefer **`pm export`** from the project root (`--from` / `--to` / `--out`). Default output: `.pm/exports/pm-export-YYYYMMDD.md`.
2. If the CLI is unavailable, build markdown yourself: overview, open blocking/high todos, blocking findings, charter summary, milestones, **and** `.pm/state/audit.jsonl` rows in the requested time window (default: all). Run redaction (`secrets` → `***`) on the body before writing.
3. Exclude `local.yaml`, credentials, raw logs, secret originals. Never include un-redacted secrets.
4. Show the export path and ask the user to open it.


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

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).
