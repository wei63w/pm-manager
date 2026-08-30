---
description: Scan project structure and generate Mermaid architecture diagrams + flowcharts under .pm/architecture/.
handoffs:
  - label: Status
    agent: pm.status
    prompt: Summarize after architecture scan
    send: true
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Require `.pm/` initialized; else recommend `/pm-init`.
2. Run **`pm arch`** from the project root (preferred). This writes:
   - `.pm/architecture/system-context.mmd` — system context (C4 L1 style)
   - `.pm/architecture/service-dependencies.mmd` — module/service dependency graph
   - `.pm/architecture/request-flow.mmd` — request flowchart
   - `.pm/architecture/deploy-flow.mmd` — build/deploy flowchart
   - `.pm/architecture/map.json` — structured nav map for later agent reads
   - `.pm/architecture/tree.md` — annotated directory tree (ignore dirs skipped)
   - `.pm/architecture/overview.md` — embeds all Mermaid diagrams + detected summary
   - `.pm/architecture/scan.json` — machine-readable scan meta
3. If a valid `map.json` already exists, prefer incremental (`pm arch` uses mtime/size hashes). Skip `node_modules`, build, logs, and `scan.exclude_dirs`.
4. If CLI is unavailable, generate the same files yourself by scanning (still skip ignore dirs; isolate per-file read failures).
5. Review diagrams: fix wrong edges, rename nodes, add missing externals. Prefer editing the `.mmd` files then refreshing the Mermaid blocks in `overview.md`.
6. Optional charter compare: mark out-of-scope services or missing in-scope capabilities in `architecture/findings.md` (with confidence) **only if charter is approved**.
7. Default: write only under `.pm/architecture/`. If the user asks to land diagrams in the application tree, show the draft and **wait for confirm**.
8. **Required closing**: short Summary + **Open these** links per `templates/commands/_closing.md`:
   - `.pm/architecture/overview.md` (primary — open this)
   - `.pm/architecture/map.json`
   - `.pm/architecture/tree.md`
   - Explicitly ask the user to open the architecture overview.

## Done When

- [ ] Four `.mmd` files + `overview.md` + `map.json` + `tree.md` exist under `.pm/architecture/`
- [ ] Diagrams reflect this repo (not generic placeholders)
- [ ] Ignore dirs were skipped; no secrets in diagram labels or findings


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. If `.pm/` metadata is valid, load it; do **not** force a full-repo rescan. On-demand **incremental** scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`). Prefer `.pm/architecture/map.json` and the document index before walking the tree.
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`). Never persist raw secrets.
4. Optional charter compare only when `charter.status == approved` (attach `confidence`). Draft PRD/charter MUST NOT be used as the baseline.
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` with **all** open/in_progress blocking+high todos (no 3-item cap). Medium/low: counts only unless `--verbose`.
7. Append audit to `.pm/state/audit.jsonl` (command, time, input/output summary; include reasoning when the step was AI-produced).
8. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud or land generated docs/rules without explicit user confirmation.
9. **Closing (required):** end with Summary + Open these links per `templates/commands/_closing.md`. Ask the user to open them.

Design baseline: local `pm-manager-v*.md` (not published).
