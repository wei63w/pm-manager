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
2. 若已有 `map.json`，先读它。定位文件用 **`pm map <关键词>`**，禁止无过滤全库递归。
3. Run **`pm arch`** from the project root (preferred). This writes:
   - `.pm/architecture/map.json` — 导航地图（modules / key_files / capabilities / hotspots / lookup）
   - `.pm/architecture/tree.md` — 带注解目录树
   - `.pm/architecture/overview.md` — 中文总览 + Mermaid
   - `.pm/architecture/layer.mmd` — 分层架构
   - `.pm/architecture/system-context.mmd` / `service-dependencies.mmd` / `request-flow.mmd` / `deploy-flow.mmd`
   - `.pm/architecture/scan.json`
4. If a valid `map.json` already exists and nothing changed, CLI reuses the map (timestamp only). Skip `node_modules`, build, logs, and `scan.exclude_dirs`.
4. If CLI is unavailable, generate the same files yourself by scanning (still skip ignore dirs; isolate per-file read failures). **If the repo is Vue** (`vue`/`nuxt` in package.json deps): include `.vue` files; draw Browser → Vue Router → Page → Component → API (not API Gateway); layer by pages/views, components, composables/stores, api. Non-Vue repos keep the existing heuristics.
5. Review diagrams: fix wrong edges, rename nodes, add missing externals. Prefer editing the `.mmd` files then refreshing the Mermaid blocks in `overview.md`.
6. Optional charter compare: mark out-of-scope services or missing in-scope capabilities in `architecture/findings.md` (with confidence) **only if charter is approved**.
7. Default: write only under `.pm/architecture/`. If the user asks to land diagrams in the application tree, show the draft and **wait for confirm**.
8. **Closing:** `_closing.md` 完整档；只列已生成的架构文件。中文摘要。

## Done When

- [ ] `map.json` has path-based `key_files` and non-empty module paths; `layer.mmd` exists
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
9. **Closing:** `_closing.md` 完整档。

Design baseline: `docs/prd.md` + 宪章。
