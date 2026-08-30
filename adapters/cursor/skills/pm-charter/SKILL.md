---
description: Create, import, discover, approve, or skip project charter; integrates Spec Kit constitution.
handoffs:
  - label: Re-compare
    agent: pm.all
    prompt: Re-run governance compare after charter change
---

## User Input

```text
$ARGUMENTS
```

Subcommands: `create` | `import <path>` | `discover` | `approve` | `skip`.

## Outline

1. `discover`: rescan `charter_candidates` (Spec Kit constitution first); map into `.pm/charter/`; update `sources.md`.
2. `import`: parse given path into charter files; `source=imported`.
3. `create`: interactive fill from templates.
4. `approve`: `charter.status=approved`. If `.pm/prd/prd.md` is draft, also set `prd.status=confirmed` (same as `/pm-init confirm`).
5. `skip`: `charter.status=absent`. If the user is skipping the generated PRD, set `prd.status=skipped`. Do **not** use skipped/draft charter to judge whether a demand is “reasonable”.
6. Any write → `needs_recompare=true`.
7. Prefer `/pm-init` for first-time Spec Kit detection and PRD draft. This command is the charter lifecycle after that.
8. `approve` is the only path that makes the charter a baseline. Until then, treat charter files as drafts.


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
