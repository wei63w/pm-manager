---
description: Persist this session's intent, extract change points, refresh the iteration timeline, and list optimization suggestions.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after journal refresh
    send: true
---

## User Input

```text
$ARGUMENTS
```

Accepted: empty | a short session note | `--kind consult|code|fix|docs|refactor` | file paths the user actually named.

## Outline

`/pm-journal` 只管开发记录与意图。用户以中文交互时用中文回复。不监听后台对话；按需落盘。未确认不改业务代码。

1. Require `.pm/`。缺则建议 `/pm-init`。
2. 先读 `.pm/state/session.json`、`timeline.md`、`suggestions.md`、`dialogue.md` 与 `map.json`。**禁止**为找记录做无过滤全库递归。
3. 若用户描述了本轮在做什么、贴了对话、或点名了文件：运行  
   `pm log --kind … --intent "…" --file <用户点名的路径> "脱敏摘录"`  
   不可判断就让 CLI 标 `unresolved`，**禁止编造文件列表**。
4. 运行 **`pm journal`**，刷新并打开：
   - `.pm/state/dialogue.md` 对话落盘
   - `.pm/state/session.json` 本轮意图
   - `.pm/state/changes.md` 变更点
   - `.pm/state/timeline.md` 迭代时间线
   - `.pm/state/suggestions.md` 优化建议
5. 中文汇报：场景（咨询/代码/修复/重构/文档）、目标、变更文件、P0/P1 建议、时间线最近几条。建议只提示，不自动建待办、不改业务树。
6. Closing：`_closing.md` 轻量档。指向已存在的 timeline / suggestions / dialogue。

## Done When

- [ ] 对话已脱敏落盘（或明确无需新笔记）
- [ ] 时间线与建议已刷新
- [ ] 未编造文件；无秘密原文

## Shared Workflow

On-demand only. Map-first. Redact before write. Confirm-before-write for app code. Design baseline: `docs/prd.md` + 宪章。
