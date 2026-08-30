from __future__ import annotations

import shutil
from pathlib import Path

from pm_manager_cli.paths import templates_pm

MODULES = [
    "bugs",
    "architecture",
    "engineering",
    "environments",
    "integration",
    "testing",
    "release",
    "database",
    "operations",
    "cost",
]


def ensure_git_exclude(project_root: Path) -> str:
    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        return "skipped (not a git repo)"
    exclude = git_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    line = ".pm/"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if any(x.strip() == line for x in existing.splitlines()):
        return "already present"
    with exclude.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n# PM governance workbench (local only)\n.pm/\n")
    return f"appended to {exclude}"


def _copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists() or not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def scaffold(project_root: Path) -> Path:
    """Create .pm/ tree from bundled templates. Idempotent for existing files."""
    project_root = project_root.resolve()
    tpl = templates_pm()
    if not tpl.is_dir():
        raise FileNotFoundError(f"templates/pm missing at {tpl}")

    pm = project_root / ".pm"
    (pm / "config").mkdir(parents=True, exist_ok=True)
    (pm / "state").mkdir(parents=True, exist_ok=True)
    (pm / "charter").mkdir(parents=True, exist_ok=True)
    (pm / "outline").mkdir(parents=True, exist_ok=True)
    (pm / "prd").mkdir(parents=True, exist_ok=True)
    (pm / "inbox" / "stacks").mkdir(parents=True, exist_ok=True)
    (pm / "evidence" / "scans").mkdir(parents=True, exist_ok=True)
    (pm / "bugs" / "incidents").mkdir(parents=True, exist_ok=True)

    for src_name, dst in [
        ("project.yaml", pm / "config" / "project.yaml"),
        ("local.yaml", pm / "config" / "local.yaml"),
        ("overview.md", pm / "state" / "overview.md"),
        ("todo.md", pm / "state" / "todo.md"),
        ("completed.md", pm / "state" / "completed.md"),
    ]:
        _copy_if_missing(tpl / src_name, dst)

    for name in ("charter.md", "requirements.md", "nfr.md", "dod.md", "sources.md"):
        _copy_if_missing(tpl / "charter" / name, pm / "charter" / name)

    for name in ("project-outline.md", "epics.md", "milestones.md"):
        _copy_if_missing(tpl / "outline" / name, pm / "outline" / name)

    _copy_if_missing(tpl / "prd" / "prd.md", pm / "prd" / "prd.md")

    for mod in MODULES:
        d = pm / mod
        d.mkdir(parents=True, exist_ok=True)
        for name in ("checklist.md", "findings.md", "todo.md", "completed.md"):
            _copy_if_missing(tpl / "module" / name, d / name)

    arch = pm / "architecture"
    arch.mkdir(parents=True, exist_ok=True)
    overview = arch / "overview.md"
    if not overview.exists():
        overview.write_text(
            "# Architecture overview\n\n_Run `pm arch` or `/pm-arch` to generate Mermaid diagrams from this project._\n",
            encoding="utf-8",
        )
    for stub in (
        "system-context.mmd",
        "service-dependencies.mmd",
        "request-flow.mmd",
        "deploy-flow.mmd",
    ):
        p = arch / stub
        if not p.exists():
            p.write_text(
                f"flowchart LR\n  %% Placeholder — regenerate with: pm arch\n  A[Project] --> B[Dependency]\n",
                encoding="utf-8",
            )

    (pm / "evidence" / "scans" / ".gitkeep").write_text("", encoding="utf-8")
    (pm / "dashboard").mkdir(parents=True, exist_ok=True)
    (pm / "engineering").mkdir(parents=True, exist_ok=True)
    _copy_if_missing(tpl / "engineering" / "reviews.md", pm / "engineering" / "reviews.md")
    _copy_if_missing(tpl / "engineering" / "rules.md", pm / "engineering" / "rules.md")
    doc_index = pm / "state" / "doc-index.md"
    if not doc_index.exists():
        src_idx = tpl / "doc-index.md"
        if src_idx.is_file():
            _copy_if_missing(src_idx, doc_index)
        else:
            doc_index.write_text(
                "# Document index\n\n_Fill via `/pm-init` core-doc check._\n",
                encoding="utf-8",
            )
    audit = pm / "state" / "audit.jsonl"
    if not audit.exists():
        audit.write_text("", encoding="utf-8")
    dialogue = pm / "state" / "dialogue.md"
    if not dialogue.exists():
        dialogue.write_text("# Dialogue notes\n\n", encoding="utf-8")
    # Never modify a shared .gitignore — local exclude only (constitution I).
    ensure_git_exclude(project_root)

    # Initial empty dashboard aggregate
    try:
        from pm_manager_cli.dashboard import write_dashboard

        write_dashboard(project_root)
    except Exception:
        stub = pm / "dashboard" / "overview.md"
        if not stub.exists():
            stub.write_text(
                "# Governance dashboard\n\n_Run `pm dashboard` or `/pm-all` to populate._\n",
                encoding="utf-8",
            )
    return pm
