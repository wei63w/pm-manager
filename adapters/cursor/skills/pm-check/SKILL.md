---
name: "pm-check"
description: Diagnose .pm/ health (missing files, broken audit, stale map, unconfirmed PRD) and repair or increment without overwriting confirmed content.
---

## User Input

```text
$ARGUMENTS
```

Accepted: `repair` | empty (diagnose only).

## Outline

`/pm-check` is the recovery command. Prefer **`pm check`** from the project root and explain the table in Chinese.

1. If `.pm/` is missing: **block** → 请先 `/pm-init` 或 `pm init`。Do not treat as a new empty project silently.
2. Read `pm check` output. Also inspect:
   - `project.yaml` / `prd.status`（draft → 提醒 confirm / skip，不自动当基线）
   - `.pm/state/audit.jsonl` 是否可逐行 JSON 解析
   - `.pm/architecture/map.json` 是否存在、是否能解析
   - `.pm/engineering/reviews.md` 待处置条数
   - 核心文档索引是否过期（`pm docs` 只更新索引）
3. If the user said `repair` (or agrees after you list issues):
   - Re-run `pm init --scaffold-only --no-skills-sh` to **fill missing skeleton only** (CLI is copy-if-missing).
   - Never overwrite user-edited or `prd.status=confirmed` / `charter.status=approved` content.
   - Rebuild map with `pm arch` if missing or unreadable.
   - Rebuild dashboard with `pm dashboard` if missing.
   - If `audit.jsonl` is corrupt: keep a `.bak` of the readable prefix if possible; do not silently truncate confirmed reviews/todos.
4. Tell the user what was repaired vs what needs a human confirm.
5. Closing: `_closing.md` **轻量**档。

## Done When

- [ ] Missing `.pm/` directed to `/pm-init`
- [ ] Diagnosis listed in Chinese
- [ ] Repair path did not overwrite confirmed baselines

## Shared Workflow

Map-first. Redact. No auto-write of app code. Design baseline: `docs/prd.md` + 宪章。
