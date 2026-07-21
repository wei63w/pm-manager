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
2. For architecture: run **`pm arch`** (or `/pm-arch`) so `.pm/architecture/` gets real Mermaid diagrams (system context, dependencies, request/deploy flows) — not placeholder stubs.
3. Incremental merge; suppress duplicate evidence hashes.
4. Refresh state overview/todo.
5. Rebuild `.pm/dashboard/` with `pm dashboard` (aggregate findings + todos).
6. Keep chat brief unless `--verbose`.
7. **Required closing**: follow `templates/commands/_closing.md` — Summary + Open links for `.pm/dashboard/index.html`, `.pm/dashboard/overview.md`, and `.pm/architecture/overview.md` (if arch ran). Ask the user to open them.


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
