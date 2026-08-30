---
name: "pm-tests"
description: List missing unit-test companions for core/changed sources. Do not write tests into the business tree unless the user confirms.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after test-gap scan
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

`/pm-tests` 只管单测缺口。用户以中文交互时用中文回复。未确认不得把测试文件写入业务树。

1. Require `.pm/`。缺则建议 `/pm-init`。
2. 先读 `.pm/architecture/map.json` 与 `.pm/state/test-gaps.md`（若有）。禁止为找测试做无过滤全库递归。
3. 运行 **`pm tests`**，列出核心源 / 本轮变更缺少的配套测试，以及建议落点。
4. 只报告。若用户要求起草，先给出方案，**停下等确认**后再写测试文件。
5. Closing：`_closing.md` 轻量档。指向 `test-gaps.md`。

## Done When

- [ ] 缺口已列出（或明确没有）
- [ ] 未自动创建业务树测试文件

## Shared Workflow

Map-first. Confirm-before-write for test files. Design baseline: `docs/prd.md` + 宪章。
