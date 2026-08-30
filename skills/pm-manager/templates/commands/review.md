---
description: Review local git diff with reasoning + snippets; cross-check; dispose findings into the rules library.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after review dispositions
    send: true
---

## User Input

```text
$ARGUMENTS
```

Accepted extra words: `confirm REV-xxx` | `false_positive REV-xxx` | `later REV-xxx` | `annotate REV-xxx` | `--cross` | `--path=...` | `--verbose`.

## Outline

`/pm-review` 是可见的质量闭环。用户以中文交互时用中文回复。未确认不改业务代码。

### A. New review (no disposition words)

1. Require `.pm/`。缺则建议 `/pm-init`。
2. 先跑 **`pm gate --path <root>`** 与 **`pm review --path <root>`**。读 `.pm/state/review-draft.md`、`guard.md`。无 diff 则说 **没有可评的变更** 并停止，不许编造通过。
3. 地图优先。加载 `.pm/engineering/rules.md` 启用规则。对照旧/新行为。碰到 `risk_files` 必须打断并单独成行。
4. 只润色或补**合格**行（`summary` + `reasoning` + `snippet` + `severity` + `file`/`line`）。缺推理或片段禁止落盘。
5. 建议再跑 **`pm review --cross`**，对照 `.pm/state/cross-review.md` 用另一套检查单（安全 vs 完成度/文档），禁止复制初评空话、禁止同一 snippet 再标 new。
6. P0 打断。P1/P2 进报告。单测缺口只警告。
7. 请用户回复 `confirm REV-xxx` / `false_positive REV-xxx` / `later REV-xxx`。回填用 `pm review annotate REV-xxx`（只写 `.pm/reviews/annotations/`）。

### B. Disposition

- `confirm` → `pm review confirm REV-xxx`（或最新 unset）。仅合格行可进 `rules.md`。
- `false_positive` → 不进规范。
- `later` → 待优化，留在表里。

### C. After write

刷新总览待处置数。追加审计（含推理）。Closing：`_closing.md` 完整档。

## Done When

- [ ] 无 diff 时说了没有可评的变更
- [ ] 每条落盘发现有推理 + 片段
- [ ] 仅 confirmed 进入 rules.md
- [ ] 回填未写入业务树
- [ ] 业务代码未改，除非用户另确认修复

## Shared Workflow

Map-first. Redact snippets. Confirm-before-write. Design baseline: `docs/prd.md` + 宪章。
