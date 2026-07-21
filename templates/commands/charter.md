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
4. `approve`: `status=approved` (`.pm/charter` becomes source of truth vs external).
5. `skip`: `status=absent`.
6. Any write → `needs_recompare=true`.


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).
