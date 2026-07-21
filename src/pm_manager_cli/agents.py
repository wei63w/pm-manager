from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from pm_manager_cli.paths import adapters_root, pack_root

AgentName = Literal["cursor", "claude", "all"]

# skills.sh / `npx skills add` source (override with PM_SKILLS_SOURCE)
DEFAULT_SKILLS_SOURCE = os.environ.get("PM_SKILLS_SOURCE", "wei63w/pm-manager")


def install_cursor(project_root: Path) -> Path:
    """Install full pack into .cursor/skills/pm-manager."""
    project_root = project_root.resolve()
    dest = project_root / ".cursor" / "skills" / "pm-manager"
    src = pack_root()

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    for name in ("SKILL.md", "AGENTS.md", "templates", "memory"):
        s = src / name
        d = dest / name
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Keep a small pointer for debugging
    (dest / ".pm-manager-pack.txt").write_text(str(src), encoding="utf-8")
    return dest


def install_claude(project_root: Path) -> Path:
    """Install slash command markdown into .claude/commands/."""
    project_root = project_root.resolve()
    src = adapters_root() / "claude-code" / "commands"
    if not src.is_dir():
        raise FileNotFoundError(f"Claude adapters missing: {src}")
    dest = project_root / ".claude" / "commands"
    dest.mkdir(parents=True, exist_ok=True)
    for f in src.glob("pm-*.md"):
        shutil.copy2(f, dest / f.name)
    pointer = project_root / ".claude" / "pm-manager-pack.path"
    pointer.write_text(str(pack_root()), encoding="utf-8")
    return dest


def install_agents(project_root: Path, agent: AgentName) -> dict[str, Path]:
    results: dict[str, Path] = {}
    if agent in ("cursor", "all"):
        results["cursor"] = install_cursor(project_root)
    if agent in ("claude", "all"):
        results["claude"] = install_claude(project_root)
    return results


def install_skills_sh(
    project_root: Path,
    source: str = DEFAULT_SKILLS_SOURCE,
    timeout_sec: int = 180,
) -> tuple[bool, str]:
    """Non-interactive `npx skills add <source> -y` for skills.sh indexing + agents.

    Best-effort: missing Node/npx or network errors return (False, reason)
    and must not abort `pm init`.
    """
    project_root = project_root.resolve()
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        return False, "skipped (npx not found; install Node.js to enable skills.sh)"

    cmd = [npx, "--yes", "skills@latest", "add", source, "-y"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout_sec}s running: {' '.join(cmd)}"
    except OSError as exc:
        return False, f"failed to run npx: {exc}"

    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    # Keep message short for CLI
    tail = out[-400:].replace("\r", "") if out else ""
    if proc.returncode != 0:
        detail = tail or f"exit {proc.returncode}"
        return False, f"npx skills add failed: {detail}"
    return True, f"npx skills add {source} -y"
