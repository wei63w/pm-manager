---
description: Analyze pasted logs/stacks/slow SQL from chat (or --path) into bugs findings and todos.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after incident intake
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Prefer **current conversation paste** as evidence (first-class; no need to save a file first); else `--path` / sources / `.pm/inbox/stacks/`.
2. Desensitize; write evidence JSON; optionally copy redacted snippet to inbox. Never persist secret originals.
3. Classify severity (blocking/high/medium/low/suggestion) per design rules.
4. Append `bugs/findings.md` + `state/todo.md` entry with next action.
5. Charter compare for availability/success criteria with confidence **only if charter.status=approved**.
6. Append a desensitized dialogue note to `.pm/state/dialogue.md` (intent + files if parseable; else `unresolved`).
7. Summarize: severity, owner guess, estimate, suggested `/pm-done` later.

Do **not** modify application code unless user confirms.


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
