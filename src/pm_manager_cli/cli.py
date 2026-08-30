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
from pm_manager_cli.audit import append_audit
from pm_manager_cli.dashboard import hot_open_todos, write_dashboard
from pm_manager_cli.docs_index import missing_count, scan_core_docs, write_doc_index
from pm_manager_cli.export_audit import write_export
from pm_manager_cli.scaffold import ensure_git_exclude, scaffold
from pm_manager_cli.speckit import (
    detect_speckit,
    existing_prd_candidates,
    looks_like_existing_project,
    read_prd_status,
    write_init_metadata,
)

app = typer.Typer(
    name="pm",
    help="PM Manager — 本地 .pm 项目治理 CLI（确定性引擎；确认与评审走 /pm-*）。",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _resolve_root(path: Optional[Path]) -> Path:
    return (path or Path.cwd()).resolve()


def _require_dir(root: Path) -> None:
    if not root.is_dir():
        raise typer.BadParameter(f"不是目录: {root}")


def _exit_missing_pm(root: Path) -> None:
    console.print(f"[red]错误[/red] 缺少 .pm/（{root}）；请先运行 `pm init`")
    raise typer.Exit(2)


def _print_open_links(title: str, items: list[tuple[str, Path]]) -> None:
    console.print()
    console.print(f"[bold]{title}[/bold]")
    console.print("[dim]建议打开这些总览（不必逐个翻模块目录）。[/dim]")
    for label, p in items:
        resolved = p.resolve()
        console.print(f"  - [cyan]{label}[/cyan]")
        console.print(f"    {resolved}")
        try:
            console.print(f"    {resolved.as_uri()}")
        except ValueError:
            pass


def _audit(
    root: Path,
    command: str,
    input_summary: str = "",
    output_summary: str = "",
) -> None:
    append_audit(
        root,
        command=command,
        input_summary=input_summary,
        output_summary=output_summary,
        actor_or_session="cli",
    )


@app.callback()
def main() -> None:
    """PM Manager CLI。"""


@app.command("version")
def version_cmd() -> None:
    """打印 CLI 版本。"""
    console.print(f"pm-manager-cli {__version__}")


@app.command("init")
def init_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
    agent: str = typer.Option(
        "all",
        "--agent",
        "-a",
        help="安装助手适配器: cursor | claude | all | none",
    ),
    scaffold_only: bool = typer.Option(
        False,
        "--scaffold-only",
        help="只创建 .pm/（不安装助手技能/命令）",
    ),
    skills_sh: bool = typer.Option(
        True,
        "--skills-sh/--no-skills-sh",
        help="同时非交互执行 `npx skills add wei63w/pm-manager -y`",
    ),
) -> None:
    """创建 .pm/ 治理台，并可选安装 Cursor/Claude 适配器。"""
    root = _resolve_root(path)
    _require_dir(root)

    console.print(f"[bold]项目:[/bold] {root}")
    pm = scaffold(root)
    exclude_msg = ensure_git_exclude(root)
    console.print(f"[green]完成[/green] 已搭建 {pm}")
    console.print(f"[green]完成[/green] Git exclude: {exclude_msg}")

    detection = detect_speckit(root)
    write_init_metadata(root, detection)
    if detection.present:
        console.print("[green]完成[/green] 已检测到 Spec Kit")
        if detection.constitution:
            console.print(f"  宪章: {detection.constitution_rel(root)}")
        for rel in detection.spec_rels(root)[:8]:
            console.print(f"  规格: {rel}")
        if len(detection.specs) > 8:
            console.print(f"  … 另有 {len(detection.specs) - 8} 份规格")
    else:
        console.print("[yellow]说明[/yellow] 未使用 Spec Kit")
        docs = existing_prd_candidates(root)
        if docs:
            console.print("  已有产品文档（将作为 PRD 草稿导入）:")
            for p in docs:
                console.print(f"    {p.relative_to(root).as_posix()}")
        elif looks_like_existing_project(root):
            console.print("  已有项目 — 请在助手中运行 /pm-init 分析仓库并起草 PRD")
        else:
            console.print("  空仓/新项目 — 请在助手中运行 /pm-init 并给出一句话意图")

    chosen = "none" if scaffold_only else agent.lower().strip()
    if chosen not in {"cursor", "claude", "all", "none"}:
        raise typer.BadParameter("--agent 必须是 cursor|claude|all|none")

    if chosen != "none":
        results = install_agents(root, chosen)  # type: ignore[arg-type]
        for name, dest in results.items():
            console.print(f"[green]完成[/green] 已安装 {name} -> {dest}")

    if skills_sh and not scaffold_only:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]完成[/green] skills.sh: {msg}")
            if chosen != "none":
                install_agents(root, chosen)  # type: ignore[arg-type]
                console.print("[green]完成[/green] 已用本 CLI 包重新同步适配器")
        else:
            console.print(f"[yellow]警告[/yellow] skills.sh: {msg}")

    _audit(
        root,
        "pm-init",
        input_summary=f"agent={chosen} scaffold_only={scaffold_only}",
        output_summary=f"scaffolded {pm.as_posix()}",
    )

    console.print()
    console.print("[bold]接下来（在 AI 编程助手中）:[/bold]")
    if detection.present:
        console.print("  /pm-init     # 导入 Spec Kit 宪章/规格，然后确认")
    else:
        console.print("  /pm-init     # 根据仓库起草 .pm/prd/prd.md，然后确认")
    console.print("  /pm-status   # 全部未关闭阻断/高优先级待办（确认或跳过 PRD 之后）")


@app.command("install")
def install_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
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
        help="同时非交互执行 `npx skills add wei63w/pm-manager -y`",
    ),
) -> None:
    """安装或刷新项目内助手适配器（不搭脚手架）。"""
    root = _resolve_root(path)
    chosen = agent.lower().strip()
    if chosen not in {"cursor", "claude", "all"}:
        raise typer.BadParameter("--agent 必须是 cursor|claude|all")
    results = install_agents(root, chosen)  # type: ignore[arg-type]
    for name, dest in results.items():
        console.print(f"[green]完成[/green] 已安装 {name} -> {dest}")

    if skills_sh:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]完成[/green] skills.sh: {msg}")
            install_agents(root, chosen)  # type: ignore[arg-type]
            console.print("[green]完成[/green] 已用本 CLI 包重新同步适配器")
        else:
            console.print(f"[yellow]警告[/yellow] skills.sh: {msg}")


@app.command("check")
def check_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """报告 .pm/、适配器与 PRD 资产是否存在（只读）。"""
    root = _resolve_root(path)
    table = Table(title=f"PM Manager 检查 — {root}")
    table.add_column("项")
    table.add_column("状态")

    def _ok(flag: bool) -> str:
        return "[green]有[/green]" if flag else "[yellow]缺[/yellow]"

    checks: dict[str, bool] = {
        ".pm/": (root / ".pm").is_dir(),
        ".pm/config/project.yaml": (root / ".pm" / "config" / "project.yaml").is_file(),
        ".pm/architecture/map.json": (root / ".pm" / "architecture" / "map.json").is_file(),
        ".pm/state/audit.jsonl": (root / ".pm" / "state" / "audit.jsonl").is_file(),
        ".pm/state/doc-index.md": (root / ".pm" / "state" / "doc-index.md").is_file(),
        ".pm/dashboard/index.html": (root / ".pm" / "dashboard" / "index.html").is_file(),
        ".pm/dashboard/overview.md": (root / ".pm" / "dashboard" / "overview.md").is_file(),
        "Cursor 技能": (root / ".cursor" / "skills" / "pm-manager" / "SKILL.md").is_file(),
        "Claude 命令": (
            any((root / ".claude" / "commands").glob("pm-*.md"))
            if (root / ".claude" / "commands").is_dir()
            else False
        ),
        "git exclude .pm/": False,
    }
    exclude = root / ".git" / "info" / "exclude"
    if exclude.is_file():
        checks["git exclude .pm/"] = any(
            line.strip() == ".pm/"
            for line in exclude.read_text(encoding="utf-8").splitlines()
        )

    checks[".pm/prd/prd.md"] = (root / ".pm" / "prd" / "prd.md").is_file()

    for item, ok in checks.items():
        table.add_row(item, _ok(ok))

    detection = detect_speckit(root)
    table.add_row(
        "Spec Kit",
        "[green]在用[/green]" if detection.present else "[dim]未使用[/dim]",
    )
    prd_status = read_prd_status(root)
    table.add_row(
        "prd.status",
        prd_status if prd_status else "[dim]absent[/dim]",
    )
    console.print(table)


@app.command("dashboard")
def dashboard_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """根据模块 findings/todos 重建 .pm/dashboard/。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    out = write_dashboard(root)
    stats_path = out / "stats.json"
    summary = ""
    if stats_path.is_file():
        try:
            data = json.loads(stats_path.read_text(encoding="utf-8"))
            summary = (
                f"健康={data.get('health_label', '?')} "
                f"{data.get('health_score', '?')}/100 | "
                f"未关闭发现={data.get('open_findings', 0)} | "
                f"热点={data.get('hot_count', 0)} | "
                f"未关闭待办={data.get('open_todos', 0)}"
            )
        except (OSError, json.JSONDecodeError, TypeError):
            summary = ""

    console.print(f"[green]完成[/green] 看板已写入 -> {out}")
    if summary:
        console.print(f"  摘要: {summary}")
    _audit(
        root,
        "pm-dashboard",
        output_summary=summary or str(out),
    )
    _print_open_links(
        "请打开这些总览",
        [
            ("治理看板（浏览器）", out / "index.html"),
            ("治理看板（IDE）", out / "overview.md"),
        ],
    )


@app.command("arch")
def arch_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """扫描项目，生成 Mermaid 架构图、map.json 与带注解目录树。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        out, model = write_architecture(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    console.print(f"[green]完成[/green] 架构产物 -> {out}")
    console.print(
        f"  摘要: 技术栈={', '.join(model.stacks) or 'unknown'} | "
        f"模块={len(model.modules)} | "
        f"控制器={len(model.controllers)} | "
        f"外部={len(model.externals)}"
    )
    if model.modules:
        console.print(f"  模块: {', '.join(model.modules[:8])}")
    _audit(
        root,
        "pm-arch",
        output_summary=f"modules={len(model.modules)} map.json+tree.md",
    )
    _print_open_links(
        "请打开这些总览",
        [
            ("架构总览（Mermaid）", out / "overview.md"),
            ("导航地图", out / "map.json"),
            ("带注解目录树", out / "tree.md"),
        ],
    )


@app.command("docs")
def docs_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """检测核心文档是否缺失，并更新 .pm/state/doc-index.md（不生成正文）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    dest, entries = write_doc_index(root)
    missing = [e for e in entries if e.status == "missing"]
    present = [e for e in entries if e.status == "present"]
    console.print(f"[green]完成[/green] 文档索引 -> {dest}")
    console.print(f"  已有 {len(present)} / 缺失 {len(missing)}")
    if missing:
        console.print("  缺失:")
        for e in missing:
            console.print(f"    - {e.id} ({e.expected})")
    for e in present:
        console.print(f"  [dim]有[/dim] {e.id}: {e.path}")
    _audit(
        root,
        "pm-docs",
        output_summary=f"present={len(present)} missing={len(missing)}",
    )


@app.command("status")
def status_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """列出全部未关闭的阻断/高优先级待办（只读，无条数上限）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    todos = hot_open_todos(root / ".pm")
    docs = scan_core_docs(root)
    miss = missing_count(docs)
    prd_status = read_prd_status(root) or "absent"
    console.print(f"[bold]未关闭阻断/高优先级待办[/bold]（{len(todos)}）")
    if not todos:
        console.print("  （无）")
    else:
        for t in todos:
            console.print(f"  - {t.id} [{t.priority}] {t.title}  ({t.status})")
    console.print(f"缺失核心文档: {miss}")
    console.print(f"prd.status: {prd_status}")
    console.print("[dim]叙事与下一步建议请用助手 /pm-status。[/dim]")


@app.command("export")
def export_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
    since: Optional[str] = typer.Option(
        None,
        "--from",
        help="窗口起点（YYYY-MM-DD 或 ISO8601，默认不限）",
    ),
    until: Optional[str] = typer.Option(
        None,
        "--to",
        help="窗口终点（YYYY-MM-DD 或 ISO8601，默认不限）",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="导出 Markdown 路径（默认 .pm/exports/pm-export-YYYYMMDD.md）",
    ),
) -> None:
    """按时间窗导出脱敏后的审计 Markdown。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        dest, n = write_export(root, since=since, until=until, out=out)
    except ValueError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(1) from exc
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    body = dest.read_text(encoding="utf-8") if dest.is_file() else ""
    if "AKIA" in body or "BEGIN PRIVATE KEY" in body:
        console.print("[red]错误[/red] 导出仍含秘密原文，已中止")
        raise typer.Exit(2)
    console.print(f"[green]完成[/green] 已导出 {n} 条 -> {dest}")
    _audit(
        root,
        "pm-export",
        input_summary=f"from={since or ''} to={until or ''}",
        output_summary=str(dest),
    )
    _print_open_links("请打开导出文件", [("审计导出", dest)])


if __name__ == "__main__":
    app()
