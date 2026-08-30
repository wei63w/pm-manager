---
description: Deep-scan all enabled governance modules and refresh state (internal; used by pm-all / status --full).
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after discover
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Require init. For each enabled module, perform on-demand technical scan + optional charter compare.
2. For architecture: run **`pm arch`** (or `/pm-arch`) so `.pm/architecture/` gets Mermaid + `map.json`.
3. Incremental merge; suppress duplicate evidence hashes.
4. Reviews: require reasoning + snippet; no local diff → say nothing to review. Load `engineering/rules.md`. P0 interrupts.
5. Refresh state overview/todo (all blocking+high, no 3-item cap).
6. Rebuild `.pm/dashboard/` with `pm dashboard` (aggregate findings + todos).
7. Keep chat brief unless `--verbose`. Do not treat V1.1 checkup/hooks/test-assist as required.
8. **Required closing**: follow `templates/commands/_closing.md` — Summary + Open links for `.pm/dashboard/index.html`, `.pm/dashboard/overview.md`, and `.pm/architecture/overview.md` (if arch ran). Ask the user to open them.


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
