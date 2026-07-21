---
description: Show governance health, iteration progress, and today's Top3 actionable todos. Primary daily entry.
handoffs:
  - label: Take next task
    agent: pm.next
    prompt: Claim the first Top3 todo
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
2. If `--full`, run discover workflow first (read-only modules -> merge).
3. Aggregate open findings counts by severity; list blocking items.
4. Build **Today's Top3** from `state/todo.md` (open/in_progress), order: blocking>high, P0>P1, iteration-related first. Suppress resolved/wontfix/done and low-confidence charter findings.
5. Show charter/outline status and `needs_recompare`.
6. Light iteration progress if `process.iteration` + milestones/REQ exist.
7. Default hide medium/low unless `--verbose` (show counts only).
8. Point the user to **`.pm/dashboard/index.html`** (browser) or **`overview.md`** (IDE) for the cross-module aggregate (if missing, run `pm dashboard` or `/pm-all`).
9. End with one health sentence + how to `/pm-done TODO-xxx`.
10. **Required closing**: follow `templates/commands/_closing.md` - always list the Open these links and ask the user to open the dashboard overview.

## Done When

- [ ] Top3 <= 3 items with clear next actions
- [ ] No secret leakage in output


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init ??recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence ??`.pm/evidence/scans/{command}-{timestamp}.json` (secrets ??`***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (??0 lines). Never auto-write source/SQL/cloud without confirmation.

9. **Closing (required):** end the user-facing reply with Summary + Open these links per `templates/commands/_closing.md` (dashboard and/or architecture overviews). Ask the user to open them.

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).
