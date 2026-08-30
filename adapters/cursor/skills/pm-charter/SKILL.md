---
name: "pm-charter"
description: Create, import, discover, approve, or skip project charter. No-arg form is an interactive wizard.
handoffs:
  - label: Re-compare
    agent: pm.all
    prompt: Re-run technical scan after charter change
---

## User Input

```text
$ARGUMENTS
```

Subcommands: `create` | `import <path>` | `discover` | `approve` | `skip`.

## Outline

If `$ARGUMENTS` is empty, **do not guess a subcommand**. Show this Chinese wizard and wait:

```text
宪章还没选定动作。请回复其一：
- create — 按模板起草宪章（仍是草稿，须再 approve）
- import <路径> — 从已有文件导入
- discover — 扫描 charter_candidates（优先 Spec Kit）
- approve — 把宪章升为基线（若 PRD 仍是草稿，同时 confirm）
- skip — 不要宪章基线；技术扫描仍可用
```

Then:

1. `discover`: rescan `charter_candidates` (Spec Kit constitution first); map into `.pm/charter/`; update `sources.md`.
2. `import`: parse given path into charter files; `source=imported`.
3. `create`: interactive fill from templates.
4. `approve`: `charter.status=approved`. If `.pm/prd/prd.md` is draft, also set `prd.status=confirmed` (same as `/pm-init confirm`).
5. `skip`: `charter.status=absent`. If the user is skipping the generated PRD, set `prd.status=skipped`. Do **not** use skipped/draft charter to judge whether a demand is “reasonable”.
6. Any write → `needs_recompare=true`.
7. Prefer `/pm-init` for first-time Spec Kit detection and PRD draft. This command is the charter lifecycle after that.
8. `approve` is the only path that makes the charter a baseline. Technical `/pm-all` does **not** require approve.

## Shared Workflow (all /pm-* commands)

1. Read config; map-first; redact; confirm before landing generated docs.
2. Append audit. Closing: `_closing.md` 完整档（只列已有路径）。

Design baseline: `docs/prd.md` + 宪章。
