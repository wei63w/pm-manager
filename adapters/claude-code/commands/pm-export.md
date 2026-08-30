---
description: Export desensitized governance summary markdown for sharing or machine switch.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Prefer **`pm export`** from the project root (`--from` / `--to` / `--out`，可选 `--with-diagrams`)。Default output: `.pm/exports/pm-export-YYYYMMDD.md`。
2. The file must include: audit window, dialogue notes, snapshot excerpt, reviews table, test-gaps, guard, and architecture **paths** (embed `.mmd` only with `--with-diagrams`). If the CLI is unavailable, assemble the same sections and **redact before writing**. If residue remains (`AKIA…`, `BEGIN PRIVATE KEY`), delete the file and fail.
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
9. **Closing:** `_closing.md` 完整档（只列已写出的导出文件）。

Design baseline: `docs/prd.md` + 宪章。
