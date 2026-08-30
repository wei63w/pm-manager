"""Optional local git pre-commit hook. Never installed by pm init."""

from __future__ import annotations

from pathlib import Path

MARKER = "PM-MANAGER-HOOK"


def hook_path(project_root: Path) -> Path:
    return project_root.resolve() / ".git" / "hooks" / "pre-commit"


def hook_script(project_root: Path) -> str:
    root = project_root.resolve().as_posix()
    return (
        "#!/bin/sh\n"
        f"# {MARKER} — local only; uninstall with: pm hook uninstall\n"
        f'pm gate --path "{root}"\n'
    )


def hook_status(project_root: Path) -> str:
    path = hook_path(project_root)
    if not (project_root.resolve() / ".git").is_dir():
        return "skipped"
    if not path.is_file():
        return "absent"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unreadable"
    if MARKER in text:
        return "installed"
    return "foreign"


def install_hook(project_root: Path, *, force: bool = False) -> Path:
    root = project_root.resolve()
    git = root / ".git"
    if not git.is_dir():
        raise FileNotFoundError(f"不是 git 仓库: {root}")
    dest = hook_path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    status = hook_status(root)
    if status == "foreign" and not force:
        raise FileExistsError("已有外来 pre-commit，拒绝覆盖。确认后加 --force")
    dest.write_text(hook_script(root), encoding="utf-8", newline="\n")
    try:
        dest.chmod(dest.stat().st_mode | 0o111)
    except OSError:
        pass
    return dest


def uninstall_hook(project_root: Path) -> bool:
    dest = hook_path(project_root)
    status = hook_status(project_root)
    if status != "installed":
        return False
    dest.unlink(missing_ok=True)
    return True
