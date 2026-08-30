---
description: Show governance health, iteration progress, and all open blocking/high todos. Primary daily entry.
handoffs:
  - label: Take next task
    agent: pm.next
    prompt: Claim the first blocking or high-priority todo
    send: true
  - label: Full scan
    agent: pm.all
    prompt: Run full governance scan
---

## User Input

```text
$ARGUMENTS
```

Flags: `--full` (deep scan first), `--verbose` (show medium/low), `--focus=iteration`.

## Outline

1. Require `.pm/config/project.yaml` else recommend `/pm-init`.
2. Prefer running **`pm status`** from the project root and use its list as the source of truth for blocking/high todos + missing-doc count. If the CLI is unavailable, parse `state/todo.md` the same way (all open/in_progress blocking/high, **no 3-item cap**).
3. If `--full`, run discover workflow first (read-only modules -> merge).
4. Aggregate open findings counts by severity; list blocking items.
5. Show charter/outline status and `needs_recompare`. Do **not** treat a draft PRD/charter as the baseline.
6. Light iteration progress if `process.iteration` + milestones/REQ exist.
7. Default hide medium/low unless `--verbose` (show counts only). Add a short Chinese health sentence and how to `/pm-done TODO-xxx` on top of the CLI dump.
8. Point the user to **`.pm/dashboard/index.html`** (browser) or **`overview.md`** (IDE) for the cross-module aggregate (if missing, run `pm dashboard` or `/pm-all`).
9. **Required closing**: follow `templates/commands/_closing.md` - always list the Open these links and ask the user to open the dashboard overview.

## Done When

- [ ] All open blocking/high todos listed (no 3-item cap)
- [ ] No secret leakage in output


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
