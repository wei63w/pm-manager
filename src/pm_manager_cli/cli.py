from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pm_manager_cli import __version__
from pm_manager_cli.agents import install_agents, install_skills_sh
from pm_manager_cli.architecture import write_architecture
from pm_manager_cli.dashboard import write_dashboard
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


def _print_open_links(title: str, items: list[tuple[str, Path]]) -> None:
    """Print a short summary footer so users know which overviews to open."""
    console.print()
    console.print(f"[bold]{title}[/bold]")
    console.print(
        "[dim]Suggested: open these overviews (no need to browse each module).[/dim]"
    )
    for label, p in items:
        resolved = p.resolve()
        console.print(f"  - [cyan]{label}[/cyan]")
        console.print(f"    {resolved}")
        try:
            console.print(f"    {resolved.as_uri()}")
        except ValueError:
            pass


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
    skills_sh: bool = typer.Option(
        True,
        "--skills-sh/--no-skills-sh",
        help="Also run non-interactive `npx skills add wei63w/pm-manager -y`",
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

    # skills.sh telemetry + multi-agent install (best-effort, non-interactive)
    if skills_sh and not scaffold_only:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]OK[/green] skills.sh: {msg}")
            # Re-apply bundled adapters so this CLI pack version wins over clone
            if chosen != "none":
                install_agents(root, chosen)  # type: ignore[arg-type]
                console.print(
                    "[green]OK[/green] Re-synced local adapters from this CLI pack"
                )
        else:
            console.print(f"[yellow]WARN[/yellow] skills.sh: {msg}")

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
    skills_sh: bool = typer.Option(
        True,
        "--skills-sh/--no-skills-sh",
        help="Also run non-interactive `npx skills add wei63w/pm-manager -y`",
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

    if skills_sh:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]OK[/green] skills.sh: {msg}")
            install_agents(root, chosen)  # type: ignore[arg-type]
            console.print(
                "[green]OK[/green] Re-synced local adapters from this CLI pack"
            )
        else:
            console.print(f"[yellow]WARN[/yellow] skills.sh: {msg}")


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
        ".pm/dashboard/index.html": (root / ".pm" / "dashboard" / "index.html").is_file(),
        ".pm/dashboard/overview.md": (root / ".pm" / "dashboard" / "overview.md").is_file(),
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


@app.command("dashboard")
def dashboard_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Target project root (default: current directory)"
    ),
) -> None:
    """Rebuild .pm/dashboard from module findings and todos."""
    root = _resolve_root(path)
    out = write_dashboard(root)
    # Quick stats for the terminal summary
    stats_path = out / "stats.json"
    summary = ""
    if stats_path.is_file():
        try:
            data = json.loads(stats_path.read_text(encoding="utf-8"))
            summary = (
                f"health={data.get('health_label', '?')} "
                f"{data.get('health_score', '?')}/100 | "
                f"open findings={data.get('open_findings', 0)} | "
                f"hot={data.get('hot_count', 0)} | "
                f"open todos={data.get('open_todos', 0)}"
            )
        except (OSError, json.JSONDecodeError, TypeError):
            summary = ""

    console.print(f"[green]OK[/green] Dashboard written -> {out}")
    if summary:
        console.print(f"  Summary: {summary}")
    _print_open_links(
        "Open these overviews",
        [
            ("Governance dashboard (browser)", out / "index.html"),
            ("Governance dashboard (IDE)", out / "overview.md"),
        ],
    )


@app.command("arch")
def arch_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="Target project root (default: current directory)"
    ),
) -> None:
    """Scan project and generate Mermaid architecture / flow diagrams."""
    root = _resolve_root(path)
    out, model = write_architecture(root)
    console.print(f"[green]OK[/green] Architecture diagrams -> {out}")
    console.print(
        f"  Summary: stack={', '.join(model.stacks) or 'unknown'} | "
        f"modules={len(model.modules)} | "
        f"controllers={len(model.controllers)} | "
        f"externals={len(model.externals)}"
    )
    if model.modules:
        console.print(f"  Modules: {', '.join(model.modules[:8])}")
    _print_open_links(
        "Open these overviews",
        [
            ("Architecture overview (Mermaid)", out / "overview.md"),
            ("System context", out / "system-context.mmd"),
            ("Request flowchart", out / "request-flow.mmd"),
        ],
    )


if __name__ == "__main__":
    app()
