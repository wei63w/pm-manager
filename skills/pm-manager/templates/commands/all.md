---
description: Orchestrate full governance scan with prerequisite gates; default noise-filtered summary; rebuild .pm/dashboard aggregate.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Summarize after full scan
    send: true
---

## User Input

```text
$ARGUMENTS
```

Flags: `--skip-charter-gate`, `--modules=...`, `--path=...`, `--verbose`.

## Outline

1. Gate: `.pm` initialized? else **block** → recommend `/pm-init`.
2. Gate: `prd.status=draft`? **wait** — ask confirm / revise / skip (`/pm-init`). New project without charter/outline/PRD? **wait** with choices: confirm PRD | outline | charter | skip (`--skip-charter-gate`).
3. Run module scans (arch, engineering, env, api, test, release, db, ops, cost) then bugs if log sources/`--path`/paste exist; else skip bugs with recommendation.
   - Architecture step **must** produce diagrams **and** `.pm/architecture/map.json`: run `pm arch` / `/pm-arch`.
4. Merge findings/todos; write `evidence/scans/pm-all-*.json`.
4b. Qualified reviews: every finding written to `.pm/engineering/reviews.md` MUST include reasoning + cited snippet. Unqualified rows MUST NOT enter `rules.md`. If there is no local diff, say there is nothing to review. Load enabled rules from `.pm/engineering/rules.md`. Only `disposition=confirmed` may become rules. P0/blocking MUST interrupt; P1/P2 stay in the report. Do **not** treat V1.1 checkup/hooks/test-assist/risk badges as required.
5. **Rebuild the dashboard** (required):
   - Prefer running: `pm dashboard` (from project root)
   - Or regenerate `.pm/dashboard/` yourself with the same contents described below
   - Output files:
     - `.pm/dashboard/index.html` — visual KPI / charts / risk tables (open in browser)
     - `.pm/dashboard/overview.md` (and `README.md` mirror) — IDE tables: KPI, bars, module risk ranking, hot list, todos
     - `.pm/dashboard/findings.md` — all open findings across modules
     - `.pm/dashboard/todos.md` — all open todos across modules
     - `.pm/dashboard/stats.json` — machine-readable counts (+ health_score, module_risk)
   - Purpose: one place to review health **without opening each module folder**
6. Chat summary: all blocking+high todos (no 3-item cap) unless `--verbose` (then include medium/low).
7. **Required closing**: follow `templates/commands/_closing.md` — print Summary + **Open these** links (at least `.pm/dashboard/index.html` and `overview.md`; include `.pm/architecture/overview.md` after arch). Explicitly ask the user to open them.
8. Finish with `/pm-status` style health line.


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

Design baseline: local `pm-manager-v*.md` (not published).
