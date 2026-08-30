---
name: "pm-docs"
description: Detect missing/stale core docs; dual-mode fill (user upload or AI draft under .pm/docs/drafts). Confirm before writing official paths.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after doc index
    send: true
---

## User Input

```text
$ARGUMENTS
```

Accepted: empty | `--draft` | `confirm DOC-xxx [path]` | `upload`（用户自备）.

## Outline

`/pm-docs` 只管文档索引与补齐。用户以中文交互时用中文回复。正式文档未经确认不得写入业务树。

1. Require `.pm/`。缺则建议 `/pm-init`。
2. 先读 `.pm/architecture/map.json` 与现有 `.pm/state/doc-index.md`（若有）。**禁止**为找文档做无过滤全库递归。
3. 运行 **`pm docs`**（刷新索引 + `.pm/state/doc-index.json`）。列出缺失与 `possibly_stale`。
4. 双模式（对每条缺失）：
   - **自备 / upload**：告诉用户把文件放到索引 `expected` 路径，再跑一次 `pm docs`。
   - **起草**：运行 `pm docs --draft`，只写 `.pm/docs/drafts/DOC-*.md`。按地图 / README / 注释填草稿，保持可编辑。**停下等确认**。
5. `confirm DOC-xxx [path]`：仅在用户明确指定正式路径后，把草稿复制过去。默认建议 `.pm/docs/` 或用户点名的 `docs/*.md`。未指定路径则继续只留在 drafts。
6. 过期文档：只提示代码变更可能新于文档，默认不自动改正文。
7. Closing：`_closing.md` 轻量档。指向 `doc-index.md` 与已有草稿。

## Done When

- [ ] 索引已更新（中文）
- [ ] 草稿未写入业务树，除非用户确认了路径
- [ ] 无秘密落盘

## Shared Workflow

Map-first. Redact. Confirm-before-write for official docs. Design baseline: `docs/prd.md` + 宪章。
