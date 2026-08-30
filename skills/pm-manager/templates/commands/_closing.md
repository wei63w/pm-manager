## Closing output (required)

Every `/pm-*` reply that writes or refreshes `.pm/` **must** end with a short summary and explicit open links so the user knows where the overview is.

Use this shape (omit rows that were not produced):

```text
## Summary
- <one-line health / what changed>
- <blocking+high open todo count — list them in the body, no 3-item cap>

## Open these (recommended)
- Governance dashboard (browser): `.pm/dashboard/index.html`
- Governance dashboard (IDE): `.pm/dashboard/overview.md`
- Architecture diagrams + map: `.pm/architecture/overview.md` / `.pm/architecture/map.json` / `.pm/architecture/tree.md`
- State / open todos: `.pm/state/overview.md`
- Project PRD (draft or confirmed): `.pm/prd/prd.md`
```

Then say clearly: **Please open the links above for the full overview** (no need to open each module folder).

Do not end only with "done" / "scan complete" without paths.
