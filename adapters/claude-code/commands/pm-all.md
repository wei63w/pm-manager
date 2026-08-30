---
description: Full technical governance scan; rebuild .pm/dashboard. Default does not wait on draft PRD. Use --compare-baseline only after a confirmed PRD/charter.
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

Flags: `--compare-baseline` | `--skip-charter-gate` (default technical mode) | `--modules=...` | `--path=...` | `--verbose`.

## Outline

Default mode is a **technical debt scan**. Do **not** block on `prd.status=draft`. Unconfirmed PRD/charter must not be used to judge “是否合理”.

1. Gate: `.pm` initialized? else **block** → recommend `/pm-init`.
2. Modes:
   - **Technical (default)**: scan architecture + enabled modules. `--skip-charter-gate` is an alias of this default.
   - **Baseline compare (`--compare-baseline`)**: only if `prd.status=confirmed` **or** `charter.status=approved`. If still draft, **wait** and offer confirm / revise / skip / 继续技术扫描.
3. Run module scans (arch, engineering, env, api, test, release, db, ops, cost) then bugs if log sources/`--path`/paste exist; else skip bugs with recommendation.
   - Architecture step **must** produce diagrams **and** `.pm/architecture/map.json`: run `pm arch` / `/pm-arch`.
   - Module deep-scan internals live in `templates/commands/discover.md` — do **not** tell the user to run `/pm-discover`.
4. Merge findings/todos; write `evidence/scans/pm-all-*.json`.
4b. Qualified reviews: every finding written to `.pm/engineering/reviews.md` MUST include reasoning + cited snippet. Unqualified rows MUST NOT enter `rules.md`. If there is no local diff, say there is nothing to review. Load enabled rules from `.pm/engineering/rules.md`. Only `disposition=confirmed` may become rules. P0/blocking MUST interrupt; P1/P2 stay in the report. Prefer `/pm-review` for a dedicated review pass. Full checkup is **`/pm-checkup` only** — do not run it here by default.
5. **Rebuild the dashboard** (required):
   - Prefer running: `pm dashboard` (from project root)
   - Output: `.pm/dashboard/index.html`、`overview.md`、`findings.md`、`todos.md`、`stats.json`
6. Chat summary (中文): all blocking+high todos (no 3-item cap) unless `--verbose`.
7. Closing: `_closing.md` 完整档；只列已生成文件。
8. Finish with `/pm-status` style Chinese health line.

## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. If `.pm/` metadata is valid, load it; do **not** force a full-repo rescan. Prefer `.pm/architecture/map.json` and the document index before walking the tree.
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`). Never persist raw secrets.
4. Optional charter compare only when `charter.status == approved` **and** the user asked `--compare-baseline` (attach `confidence`). Draft PRD/charter MUST NOT be used as the baseline.
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` with **all** open/in_progress blocking+high todos (no 3-item cap).
7. Append audit to `.pm/state/audit.jsonl`.
8. Never auto-write source/SQL/cloud or land generated docs/rules without explicit user confirmation.
9. **Closing:** `templates/commands/_closing.md`（完整档，只列已有路径）。

Design baseline: `docs/prd.md` + 宪章。
