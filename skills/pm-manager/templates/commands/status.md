---
description: Show governance health, wizard next step, all open blocking/high todos, and pending review count. Primary daily entry.
handoffs:
  - label: Take next task
    agent: pm.next
    prompt: Claim the first blocking or high-priority todo
    send: true
---

## User Input

```text
$ARGUMENTS
```

Flags: `--verbose` (show medium/low). `--full` is deprecated: do **not** deep-scan here; tell the user to run `/pm-all` if they want a full technical scan.

## Outline

`/pm-status` is a **health view**. Prefer not mutating module findings. You may refresh `overview.md` counts if stale.

1. Require `.pm/config/project.yaml` else recommend `/pm-init`.
2. Prefer **`pm status`** from the project root as the source of truth for blocking/high todos + missing-doc count + pending reviews. If the CLI is unavailable, parse `state/todo.md` and `.pm/engineering/reviews.md` the same way (**no 3-item cap**).
3. Do **not** run discover / `/pm-discover`. Deep scan is `/pm-all`.
4. Aggregate open findings counts by severity; list blocking items.
5. Show charter/outline/`prd.status`. Do **not** treat a draft PRD/charter as the baseline.
6. If `reviews.md` has rows with `disposition` unset / empty / `deferred`, print: `有 N 条待处置评审，回复 /pm-review 后用 confirm / false_positive / later。`
7. Default hide medium/low unless `--verbose`. Add a short **Chinese** health sentence and how to `/pm-done TODO-xxx`.
8. Empty / first-hour: follow the **wizard** in `.pm/state/overview.md` (confirm PRD / 轻扫 / `/pm-arch` / `/pm-all`). Do not say “没有待办” as if the tool is empty when the wizard still has a step.
9. Point to `.pm/dashboard/index.html` **only if it exists**; else say 看板尚未生成，发布前再跑 `/pm-all` 或 `pm dashboard`.
10. Closing: `_closing.md` **轻量**档（1–2 个已存在链接）。

## Done When

- [ ] All open blocking/high todos listed (no 3-item cap)
- [ ] Pending reviews mentioned when N > 0
- [ ] No secret leakage in output
- [ ] Chinese health sentence when the user writes Chinese

## Shared Workflow

Read-only preferred. If you refresh overview, still: map-first, redact, no auto-write of app code, graded closing.

Design baseline: `docs/prd.md` + 宪章。
