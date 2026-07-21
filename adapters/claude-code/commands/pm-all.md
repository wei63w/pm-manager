---
description: Orchestrate full governance scan with prerequisite gates; default noise-filtered summary.
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
2. Gate: new project without charter/outline? **wait** with choices: outline | charter | skip (`--skip-charter-gate`).
3. Run module scans (arch, engineering, env, api, test, release, db, ops, cost) then bugs if log sources/`--path`/paste exist; else skip bugs with recommendation.
4. Merge findings/todos; write `evidence/scans/pm-all-*.json`.
5. Chat summary: blocking+high + Top3 only unless `--verbose`.
6. Finish with `/pm-status` style health line.


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **今日 Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

Design baseline: repo root `pm-manager-v2.md` (or packaged copy under `memory/`).
