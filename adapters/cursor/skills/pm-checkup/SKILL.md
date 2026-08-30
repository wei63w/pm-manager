---
description: On-demand five-dimension project checkup (security, function, completeness, quality, docs) with P0/P1/P2. No cron.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after checkup
    send: true
---

## User Input

```text
$ARGUMENTS
```

Accepted: empty | `--module <name>`.

## Outline

`/pm-checkup` 是按需全量体检，不是日常口令，也不是 `/pm-all` 默认步骤。用户以中文交互时用中文回复。不启动定时器。未确认不改业务代码。

1. Require `.pm/`。缺则建议 `/pm-init`。
2. 先读 `map.json`、`doc-index.md`、`rules.md`。禁止无过滤全库递归。
3. 运行 **`pm checkup`**（或 `--module`）。打开 `.pm/state/checkup.md`。
4. P0 置顶打断；P1/P2 只汇总。可建议 `/pm-review` 把 P0 收成带推理的评审行。
5. Closing：`_closing.md` 完整档，只链已有 checkup / overview。

## Done When

- [ ] 五维报告已刷新
- [ ] 未把体检绑进日常 status 默认深潜
- [ ] 无秘密原文落盘

## Shared Workflow

Map-first. Redact. Confirm-before-write. Design baseline: `docs/prd.md` + 宪章。
