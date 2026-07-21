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
   - `.pm/architecture/overview.md` — embeds all Mermaid diagrams + detected summary
   - `.pm/architecture/scan.json` — machine-readable scan meta
3. If CLI is unavailable, generate the same files yourself by scanning:
   - Maven/Gradle modules, `docker-compose` services
   - Spring `@RestController` / `@FeignClient`, `application*.yml` externals (DB/MQ/Redis/Nacos)
   - Node/Python route entrypoints when present
4. Review diagrams: fix wrong edges, rename nodes, add missing externals. Prefer editing the `.mmd` files then refreshing the Mermaid blocks in `overview.md`.
5. Optional charter compare: mark out-of-scope services or missing in-scope capabilities in `architecture/findings.md` (with confidence).
6. **Required closing**: short Summary + **Open these** links per `templates/commands/_closing.md`:
   - `.pm/architecture/overview.md` (primary — open this)
   - `.pm/architecture/request-flow.mmd` / `system-context.mmd`
   - Explicitly ask the user to open the architecture overview.

## Done When

- [ ] Four `.mmd` files + `overview.md` exist under `.pm/architecture/`
- [ ] Diagrams reflect this repo (not generic placeholders)
- [ ] No secrets in diagram labels or findings


## Shared Workflow (all /pm-* commands)

Follow this order when the command mutates `.pm/` state:

1. Read `.pm/config/project.yaml` and `.pm/config/local.yaml` (if missing and command is not init → recommend `/pm-init`).
2. On-demand scan using `sources` + `extra_scan_roots` + `--path` + **conversation paste** (highest priority for `/pm-fix`).
3. Desensitize evidence → `.pm/evidence/scans/{command}-{timestamp}.json` (secrets → `***`).
4. Optional charter compare when `charter.status != absent` (attach `confidence`).
5. Incremental merge into module `findings.md` / `todo.md`; sync authoritative `state/todo.md`.
6. Refresh `state/overview.md` (include **Today's Top3**, max 3, blocking+high by default).
7. Output risk summary + recommended next step (≤20 lines). Never auto-write source/SQL/cloud without confirmation.

9. **Closing (required):** end the user-facing reply with Summary + Open these links per `templates/commands/_closing.md` (dashboard and/or architecture overviews). Ask the user to open them.

Design baseline: local `pm-manager-v*.md` (not published).
