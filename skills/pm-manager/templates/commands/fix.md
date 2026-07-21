---
description: Analyze pasted logs/stacks/slow SQL from chat (or --path) into bugs findings and todos.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show Top3 after incident intake
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Prefer **current conversation paste** as evidence; else `--path` / sources / `.pm/inbox/stacks/`.
2. Desensitize; write evidence JSON; optionally copy redacted snippet to inbox.
3. Classify severity (blocking/high/medium/low/suggestion) per design rules.
4. Append `bugs/findings.md` + `state/todo.md` entry with next action.
5. Charter compare for availability/success criteria with confidence.
6. Summarize: severity, owner guess, estimate, suggested `/pm-done` later.

Do **not** modify application code unless user confirms.


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
