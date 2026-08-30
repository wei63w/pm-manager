---
description: Review local git diff with reasoning + snippets; dispose findings (confirm / false_positive / later) into the rules library.
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

Accepted extra words: `confirm REV-xxx` | `false_positive REV-xxx` | `later REV-xxx` | `--path=...` | `--verbose`.

## Outline

`/pm-review` is the **quality loop** users can see. Chinese replies when the user writes Chinese.

### A. New review (no disposition words)

1. Require `.pm/`. Else recommend `/pm-init`.
2. Collect the local diff: `git diff` + `git diff --cached` (and `--path` if given). If there is **no** change, say **没有可评的变更** and stop. Do not invent a pass.
3. Load enabled rules from `.pm/engineering/rules.md`. Prefer `.pm/architecture/map.json` before opening files.
4. Write qualified rows to `.pm/engineering/reviews.md`. Each row MUST have: `id` (`REV-xxx`), `summary`, `reasoning`, `snippet`, `severity` (P0/P1/P2), `disposition` (`unset`). Missing reasoning or snippet = unqualified; do not write it as a finding.
5. P0 / blocking: interrupt in chat. P1/P2 stay in the report.
6. Ask the user to reply with `confirm REV-xxx` / `false_positive REV-xxx` / `later REV-xxx`.
7. Do **not** modify application code. Do **not** copy rows into `rules.md` until `confirm`.

### B. Disposition (same session or later)

- `confirm REV-xxx`: set `disposition=confirmed`. Copy a rule into `.pm/engineering/rules.md` (`enabled: true`, `source_finding=REV-xxx`). Load it on later generate/review.
- `false_positive REV-xxx`: set `disposition=false_positive`. Do not add a rule.
- `later REV-xxx`: set `disposition=deferred`. Keep in the log only.

If the user says `confirm` / `false_positive` / `later` without an id, apply to the **latest unset** row, or list ids and ask.

### C. After write

Refresh overview pending-review count. Append audit (include reasoning). Closing: `_closing.md` 完整档（只列已有路径）。

## Done When

- [ ] No-diff case said 没有可评的变更
- [ ] Every written finding has reasoning + snippet
- [ ] Only `confirmed` rows entered `rules.md`
- [ ] App code unchanged unless the user separately confirmed a fix

## Shared Workflow

Map-first. Redact snippets before persist. Confirm-before-write for app code and official docs. Design baseline: `docs/prd.md` + 宪章。
