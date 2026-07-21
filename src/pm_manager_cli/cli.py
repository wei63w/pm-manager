from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pm_manager_cli import __version__
from pm_manager_cli.agents import install_agents
from pm_manager_cli.scaffold import ensure_git_exclude, scaffold

app = typer.Typer(
    name="pm",
    help="PM Manager — local .pm project governance for AI coding agents.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _resolve_root(path: Optional[Path]) -> Path:
    return (path or Path.cwd()).resolve()


@app.callback()
def main() -> None:
    """PM Manager CLI."""


@app.command("version")
def version_cmd() -> None:
    """Print CLI version."""
    console.print(f"pm-manager-cli {__version__}")


@app.command("init")
def init_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Target project root (default: current directory)"
    ),
    agent: str = typer.Option(
        "all",
        "--agent",
        "-a",
        help="Install agent adapters: cursor | claude | all | none",
    ),
    scaffold_only: bool = typer.Option(
        False,
        "--scaffold-only",
        help="Only create .pm/ (skip agent skill/command install)",
    ),
) -> None:
    """Create .pm/ workbench and optionally install Cursor/Claude adapters."""
    root = _resolve_root(path)
    if not root.is_dir():
        raise typer.BadParameter(f"Not a directory: {root}")

    console.print(f"[bold]Project:[/bold] {root}")
    pm = scaffold(root)
    exclude_msg = ensure_git_exclude(root)
    console.print(f"[green]OK[/green] Scaffolded {pm}")
    console.print(f"[green]OK[/green] Git exclude: {exclude_msg}")

    chosen = "none" if scaffold_only else agent.lower().strip()
    if chosen not in {"cursor", "claude", "all", "none"}:
        raise typer.BadParameter("--agent must be cursor|claude|all|none")

    if chosen != "none":
        results = install_agents(root, chosen)  # type: ignore[arg-type]
        for name, dest in results.items():
            console.print(f"[green]OK[/green] Installed {name} -> {dest}")

    console.print()
    console.print("[bold]Next (in your AI coding agent):[/bold]")
    console.print("  /pm-init     # detect project, charter discovery, outline")
    console.print("  /pm-status   # today's Top3")


@app.command("install")
def install_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Target project root (default: current directory)"
    ),
    agent: str = typer.Option(
        "all",
        "--agent",
        "-a",
        help="cursor | claude | all",
    ),
) -> None:
    """Install or refresh agent adapters into a project (no scaffold)."""
    root = _resolve_root(path)
    chosen = agent.lower().strip()
    if chosen not in {"cursor", "claude", "all"}:
        raise typer.BadParameter("--agent must be cursor|claude|all")
    results = install_agents(root, chosen)  # type: ignore[arg-type]
    for name, dest in results.items():
        console.print(f"[green]OK[/green] Installed {name} -> {dest}")


@app.command("check")
def check_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Target project root (default: current directory)"
    ),
) -> None:
    """Show whether .pm/ and agent adapters are present."""
    root = _resolve_root(path)
    table = Table(title=f"PM Manager check — {root}")
    table.add_column("Item")
    table.add_column("Status")

    checks = {
        ".pm/": (root / ".pm").is_dir(),
        ".pm/config/project.yaml": (root / ".pm" / "config" / "project.yaml").is_file(),
        "Cursor skill": (root / ".cursor" / "skills" / "pm-manager" / "SKILL.md").is_file(),
        "Claude commands": any(
            (root / ".claude" / "commands").glob("pm-*.md")
        )
        if (root / ".claude" / "commands").is_dir()
        else False,
        "git exclude .pm/": False,
    }
    exclude = root / ".git" / "info" / "exclude"
    if exclude.is_file():
        checks["git exclude .pm/"] = any(
            line.strip() == ".pm/" for line in exclude.read_text(encoding="utf-8").splitlines()
        )

    for item, ok in checks.items():
        table.add_row(item, "[green]ok[/green]" if ok else "[yellow]missing[/yellow]")
    console.print(table)


if __name__ == "__main__":
    app()
