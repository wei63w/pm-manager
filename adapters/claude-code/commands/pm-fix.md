---
description: Triage pasted logs/stacks into bugs findings and todos. Does not change application code unless the user confirms.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Show status after incident intake
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

**先告诉用户（中文，置顶）：本次只分诊，不改代码。要把修复写进仓库，请你明确确认。**

1. Prefer **current conversation paste** as evidence (first-class; no need to save a file first); else `--path` / sources / `.pm/inbox/stacks/`.
2. Desensitize; write evidence JSON; optionally copy redacted snippet to inbox. Never persist secret originals.
3. Classify severity (blocking/high/medium/low/suggestion).
4. Append `bugs/findings.md` + `state/todo.md` entry with next action.
5. Charter compare for availability/success criteria with confidence **only if charter.status=approved**.
6. Append a desensitized dialogue note to `.pm/state/dialogue.md` (intent + files if parseable; else `unresolved`).
7. Summarize in Chinese: severity, suggested `/pm-next` / later `/pm-done TODO-xxx`. Repeat: 未确认不改业务代码。

Do **not** modify application code unless user confirms.

## Shared Workflow (all /pm-* commands)

1. Read `.pm/config/project.yaml`（缺则建议 `/pm-init`）。
2. Map-first; incremental; conversation paste highest priority.
3. Desensitize evidence. Never persist raw secrets.
4. Draft PRD/charter MUST NOT be used as the baseline.
5. Merge findings/todos; refresh overview (all blocking+high, no 3-item cap).
6. Append audit.
7. Closing: `_closing.md` **轻量**档。

Design baseline: `docs/prd.md` + 宪章。
