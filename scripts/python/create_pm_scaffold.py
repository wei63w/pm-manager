#!/usr/bin/env python3
"""Create .pm/ governance scaffold in a project (spec-kit style helper)."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = PACK_ROOT / "templates" / "pm"

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


def ensure_exclude(project_root: Path) -> None:
    git_dir = project_root / ".git"
    if not git_dir.is_dir():
        print("skip exclude: not a git repo")
        return
    exclude = git_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    line = ".pm/"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if line in existing.splitlines() or any(
        x.strip() == line for x in existing.splitlines()
    ):
        print("exclude already has .pm/")
        return
    with exclude.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n# PM governance workbench (local only)\n.pm/\n")
    print(f"appended .pm/ to {exclude}")


def copy_module(dst: Path) -> None:
    for name in ("checklist.md", "findings.md", "todo.md", "completed.md"):
        src = TEMPLATES / "module" / name
        if src.exists():
            shutil.copy2(src, dst / name)


def scaffold(project_root: Path) -> None:
    pm = project_root / ".pm"
    (pm / "config").mkdir(parents=True, exist_ok=True)
    (pm / "state").mkdir(parents=True, exist_ok=True)
    (pm / "charter").mkdir(parents=True, exist_ok=True)
    (pm / "outline").mkdir(parents=True, exist_ok=True)
    (pm / "inbox" / "stacks").mkdir(parents=True, exist_ok=True)
    (pm / "evidence" / "scans").mkdir(parents=True, exist_ok=True)
    (pm / "bugs" / "incidents").mkdir(parents=True, exist_ok=True)

    pairs = [
        ("project.yaml", pm / "config" / "project.yaml"),
        ("local.yaml", pm / "config" / "local.yaml"),
        ("overview.md", pm / "state" / "overview.md"),
        ("todo.md", pm / "state" / "todo.md"),
        ("completed.md", pm / "state" / "completed.md"),
    ]
    for src_name, dst in pairs:
        src = TEMPLATES / src_name
        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)

    for name in ("charter.md", "requirements.md", "nfr.md", "dod.md", "sources.md"):
        dst = pm / "charter" / name
        src = TEMPLATES / "charter" / name
        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)

    for name in ("project-outline.md", "epics.md", "milestones.md"):
        dst = pm / "outline" / name
        src = TEMPLATES / "outline" / name
        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)

    for mod in MODULES:
        d = pm / mod
        d.mkdir(parents=True, exist_ok=True)
        if not (d / "checklist.md").exists():
            copy_module(d)

    (pm / "architecture").mkdir(parents=True, exist_ok=True)
    for stub in ("overview.md", "system-context.mmd", "service-dependencies.mmd"):
        p = pm / "architecture" / stub
        if not p.exists():
            if stub.endswith(".mmd"):
                p.write_text("flowchart LR\n  A[System] --> B[Dependency]\n", encoding="utf-8")
            else:
                p.write_text("# Architecture overview\n\n(待 /pm-arch 或 /pm-discover 生成)\n", encoding="utf-8")

    keep = pm / "evidence" / "scans" / ".gitkeep"
    keep.write_text("", encoding="utf-8")

    ensure_exclude(project_root)
    print(f"scaffolded {pm}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create .pm governance scaffold")
    parser.add_argument("project_root", nargs="?", default=".", help="Target project root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if not TEMPLATES.is_dir():
        raise SystemExit(f"templates not found: {TEMPLATES}")
    scaffold(root)


if __name__ == "__main__":
    main()
