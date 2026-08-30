---
name: "pm-discover"
description: "PM Manager /pm-discover"
---

﻿---
description: Internal module deep-scan used by /pm-all. Do not recommend this command to users.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after discover
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

**Internal only.** If the user typed `/pm-discover`, say：深潜已并入 `/pm-all`（默认技术扫描），请改用 `/pm-all`。然后执行与 `/pm-all` 相同的技术扫描。

1. Require init. For each enabled module, perform on-demand technical scan. Charter compare only when `charter.status=approved` **and** `--compare-baseline`.
2. For architecture: run **`pm arch`** so `.pm/architecture/` gets Mermaid + `map.json`.
3. Incremental merge; suppress duplicate evidence hashes.
4. Reviews: require reasoning + snippet; no local diff → say nothing to review. Load `engineering/rules.md`. P0 interrupts. Dedicated pass: `/pm-review`.
5. Refresh state overview/todo (all blocking+high, no 3-item cap).
6. Rebuild `.pm/dashboard/` with `pm dashboard`.
7. Keep chat brief unless `--verbose`. Do not treat V1.1 checkup/hooks/test-assist as required.
8. Closing: `_closing.md` 完整档。

## Shared Workflow

Same as `/pm-all`. Map-first. Redact. No auto-write of app code.

Design baseline: `docs/prd.md` + 宪章。
