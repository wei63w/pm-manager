from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pm_manager_cli import __version__
from pm_manager_cli.agents import (
    AGENT_CHOICES,
    agent_hint,
    install_agents,
    install_skills_sh,
    resolve_agent_spec,
)
from pm_manager_cli.architecture import load_map, query_map, write_architecture
from pm_manager_cli.audit import append_audit
from pm_manager_cli.dashboard import hot_open_todos, write_dashboard
from pm_manager_cli.diagnose import collect_checks, repair_hints
from pm_manager_cli.docs_index import (
    missing_count,
    scan_core_docs,
    stale_count,
    write_doc_drafts,
    write_doc_index,
)
from pm_manager_cli.journal import (
    KIND_LABELS,
    append_dialogue,
    write_journal,
)
from pm_manager_cli.snapshot import write_overview
from pm_manager_cli.checkup import load_checkup, run_checkup
from pm_manager_cli.config_profile import apply_profile
from pm_manager_cli.export_audit import write_export
from pm_manager_cli.guard import run_gate, write_guard
from pm_manager_cli.hooks import hook_status, install_hook, uninstall_hook
from pm_manager_cli.review_engine import (
    dispose_review,
    run_cross_review,
    run_review,
    write_annotation,
)
from pm_manager_cli.rules_lib import (
    add_rule,
    enabled_rules,
    load_rules,
    set_rule_enabled,
)
from pm_manager_cli.redact import contains_secret_residue
from pm_manager_cli.reviews import pending_review_count
from pm_manager_cli.scaffold import ensure_git_exclude, scaffold
from pm_manager_cli.test_assist import write_test_gaps
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


def _refresh_reports(root: Path) -> None:
    try:
        write_journal(root)
    except (OSError, FileNotFoundError):
        pass
    try:
        write_guard(root)
    except (OSError, FileNotFoundError):
        pass
    try:
        write_test_gaps(root)
    except (OSError, FileNotFoundError):
        pass
    try:
        write_overview(root)
    except OSError:
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
        help=f"安装助手适配器: {AGENT_CHOICES}",
    ),
    scaffold_only: bool = typer.Option(
        False,
        "--scaffold-only",
        help="只创建 .pm/（不安装助手技能/命令）",
    ),
    skills_sh: bool = typer.Option(
        False,
        "--skills-sh/--no-skills-sh",
        help="可选：非交互执行 `npx --yes skills@latest add wei63w/pm-manager -y`（默认关闭，不要求 Node）",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        help="配置模板: frontend | backend | service | script | auto（只补缺失键）",
    ),
) -> None:
    """创建 .pm/ 治理台，并可选安装各编程助手适配器。"""
    root = _resolve_root(path)
    _require_dir(root)

    console.print(f"[bold]项目:[/bold] {root}")
    try:
        pm = scaffold(root)
        exclude_msg = ensure_git_exclude(root)
        console.print(f"[green]完成[/green] 已搭建 {pm}")
        console.print(f"[green]完成[/green] Git exclude: {exclude_msg}")

        detection = detect_speckit(root)
        write_init_metadata(root, detection)
        if template:
            dest, added = apply_profile(root, template)
            extra = "、".join(added) if added else "无新键（已有配置未覆盖）"
            console.print(f"[green]完成[/green] 模板 {template} -> {dest}（补上: {extra}）")
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] 安装不完整或模板缺失: {exc}")
        raise typer.Exit(2) from exc
    except ValueError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(1) from exc
    except OSError as exc:
        console.print(f"[red]错误[/red] 无法写入治理台: {exc}")
        raise typer.Exit(1) from exc

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
            console.print("  已有项目 — 下一步只说 /pm-init（分析仓库并起草 PRD）")
        else:
            console.print("  空仓/新项目 — 下一步只说 /pm-init，并给出一句话意图")

    chosen = "none" if scaffold_only else agent.lower().strip()
    try:
        resolve_agent_spec(chosen, allow_none=True)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if chosen != "none":
        try:
            results = install_agents(root, chosen)
        except FileNotFoundError as exc:
            console.print(f"[red]错误[/red] 适配器安装失败: {exc}")
            raise typer.Exit(2) from exc
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        for name, dest in results.items():
            console.print(f"[green]完成[/green] 已安装 {name} -> {dest}")
            hint = agent_hint(name)
            if hint:
                console.print(f"[dim]{name}：{hint}[/dim]")

    if skills_sh and not scaffold_only:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]完成[/green] skills.sh: {msg}")
        else:
            console.print(f"[yellow]警告[/yellow] skills.sh: {msg}（可忽略；项目内适配器已足够）")

    _refresh_reports(root)

    _audit(
        root,
        "pm-init",
        input_summary=f"agent={chosen} scaffold_only={scaffold_only}",
        output_summary=f"scaffolded {pm.as_posix()}",
    )

    console.print()
    console.print("[bold]接下来（在 AI 编程助手中只说这一条）:[/bold]")
    console.print("  /pm-init")
    console.print("[dim]确认或跳过 PRD 后会做技术轻扫；日常再用 /pm-status。[/dim]")


@app.command("install")
def install_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
    agent: str = typer.Option(
        "all",
        "--agent",
        "-a",
        help=f"{AGENT_CHOICES}",
    ),
    skills_sh: bool = typer.Option(
        False,
        "--skills-sh/--no-skills-sh",
        help="可选：非交互执行 `npx --yes skills@latest add wei63w/pm-manager -y`（默认关闭）",
    ),
) -> None:
    """安装或刷新项目内助手适配器（不搭脚手架）。"""
    root = _resolve_root(path)
    _require_dir(root)
    chosen = agent.lower().strip()
    try:
        results = install_agents(root, chosen)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] 适配器安装失败: {exc}")
        raise typer.Exit(2) from exc
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    for name, dest in results.items():
        console.print(f"[green]完成[/green] 已安装 {name} -> {dest}")
        hint = agent_hint(name)
        if hint:
            console.print(f"[dim]{name}：{hint}[/dim]")

    if skills_sh:
        ok, msg = install_skills_sh(root)
        if ok:
            console.print(f"[green]完成[/green] skills.sh: {msg}")
        else:
            console.print(f"[yellow]警告[/yellow] skills.sh: {msg}")


@app.command("check")
def check_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """诊断 .pm/、地图、审计、PRD 与待处置评审（只读）。"""
    root = _resolve_root(path)
    items = collect_checks(root)
    if not (root / ".pm").is_dir():
        console.print("[red]错误[/red] 缺少 .pm/。请先运行 `pm init`，然后在助手中只说 /pm-init。")
        raise typer.Exit(2)

    table = Table(title=f"PM Manager 检查 — {root}")
    table.add_column("项")
    table.add_column("状态")
    table.add_column("说明")
    for item in items:
        status = "[green]正常[/green]" if item.ok else "[yellow]需处理[/yellow]"
        table.add_row(item.name, status, item.detail)
    detection = detect_speckit(root)
    table.add_row(
        "Spec Kit",
        "[green]在用[/green]" if detection.present else "[dim]未使用[/dim]",
        "",
    )
    console.print(table)
    hints = repair_hints(items)
    if hints:
        console.print()
        console.print("[bold]修复建议[/bold]（助手里也可说 /pm-check repair）:")
        for h in hints:
            console.print(f"  - {h}")


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
    try:
        out = write_dashboard(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
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

    _refresh_reports(root)
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
    _refresh_reports(root)
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


@app.command("map")
def map_cmd(
    query: Optional[str] = typer.Argument(
        None, help="关键词（模块 / 能力 / 路径）。省略则打印摘要"
    ),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """查询 .pm/architecture/map.json（只读，先读地图再翻目录）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    data = load_map(root)
    if not data:
        console.print("[red]错误[/red] 还没有导航地图。请先运行 `pm arch`")
        raise typer.Exit(2)
    rows = query_map(data, query or "")
    if not rows:
        console.print(f"[yellow]未命中[/yellow] {query}")
        return
    table = Table(title="导航地图")
    table.add_column("类型")
    table.add_column("名称")
    table.add_column("说明")
    for row in rows:
        table.add_row(row["kind"], row["name"], row["detail"])
    console.print(table)


@app.command("docs")
def docs_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
    draft: bool = typer.Option(
        False,
        "--draft",
        help="为缺失的核心文档在 .pm/docs/drafts/ 写可编辑骨架（不写业务树）",
    ),
) -> None:
    """检测核心文档缺失/过期，并更新 .pm/state/doc-index.md。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    dest, entries = write_doc_index(root)
    missing = [e for e in entries if e.status == "missing"]
    stale = [e for e in entries if e.status == "possibly_stale"]
    present = [e for e in entries if e.status == "present"]
    console.print(f"[green]完成[/green] 文档索引 -> {dest}")
    console.print(
        f"  已有 {len(present)} / 缺失 {len(missing)} / 可能过期 {len(stale)}"
    )
    if missing:
        console.print("  缺失:")
        for e in missing:
            console.print(f"    - {e.id} ({e.expected})")
        console.print("  补齐：自行放到仓库对应路径，或 `pm docs --draft` 后由 /pm-docs 确认落盘")
    if stale:
        console.print("  可能过期（代码变更晚于文档）:")
        for e in stale:
            console.print(f"    - {e.id}: {e.path}")
    for e in present:
        console.print(f"  [dim]有[/dim] {e.id}: {e.path}")
    drafted: list[Path] = []
    if draft:
        drafted = write_doc_drafts(root, missing)
        if drafted:
            console.print("[green]完成[/green] 草稿（仅 .pm/docs/drafts/，未写业务树）:")
            for p in drafted:
                console.print(f"    {p}")
        else:
            console.print("[dim]没有缺失项，未写草稿[/dim]")
    _refresh_reports(root)
    _audit(
        root,
        "pm-docs",
        output_summary=(
            f"present={len(present)} missing={len(missing)} "
            f"stale={len(stale)} drafts={len(drafted)}"
        ),
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
    try:
        report = write_journal(root)
    except (OSError, FileNotFoundError):
        report = None
    try:
        overview = write_overview(root)
    except OSError:
        overview = root / ".pm" / "state" / "overview.md"
    todos = hot_open_todos(root / ".pm")
    docs = scan_core_docs(root)
    miss = missing_count(docs)
    stale = stale_count(docs)
    prd_status = read_prd_status(root) or "absent"
    pending = pending_review_count(root)
    nav = load_map(root) or {}
    stacks = nav.get("stacks") or []
    modules = nav.get("modules") or []
    console.print("[bold]现状快照[/bold]")
    console.print(f"  技术栈: {', '.join(str(s) for s in stacks) if stacks else '尚未扫描（pm arch）'}")
    console.print(f"  模块: {len(modules)}")
    console.print(f"[bold]未关闭阻断/高优先级待办[/bold]（{len(todos)}）")
    if not todos:
        if prd_status == "draft":
            console.print("  （无）向导：PRD 仍是草稿，在助手回复 confirm / revise / skip")
        elif not (root / ".pm" / "architecture" / "map.json").is_file():
            console.print("  （无）向导：还没有导航地图，运行 `pm arch`")
        else:
            console.print("  （无）")
    else:
        for t in todos:
            console.print(f"  - {t.id} [{t.priority}] {t.title}  ({t.status})")
    console.print(f"缺失核心文档: {miss}" + (f"；可能过期: {stale}" if stale else ""))
    console.print(f"prd.status: {prd_status}")
    if pending:
        console.print(f"待处置评审: {pending}（`pm review confirm|false_positive|later`）")
    else:
        console.print("待处置评审: 0")
    exam = load_checkup(root)
    if exam:
        p0n = (exam.get("counts") or {}).get("P0", 0)
        if p0n:
            console.print(f"最近体检 P0: {p0n}（`/pm-checkup` 或 `.pm/state/checkup.md`）")
    if report is not None:
        session = report.session
        kind_zh = KIND_LABELS.get(str(session.get("kind") or ""), "其他")
        console.print("[bold]本轮意图[/bold]")
        console.print(f"  {kind_zh} · {session.get('goal') or '信息不足'}（{session.get('status')}）")
        if session.get("files"):
            console.print("  文件: " + "、".join(str(p) for p in session["files"][:6]))
        top = report.suggestions[:3]
        if top:
            console.print("[bold]优化建议[/bold]")
            for item in top:
                console.print(f"  - [{item['priority']}] {item['title']} → {item['action']}")
    if overview.is_file():
        console.print(f"[dim]完整报告: {overview}（及 .pm/state/report.md）[/dim]")
    console.print("[dim]时间线与变更点：`pm journal` / `/pm-journal`。[/dim]")


@app.command("log")
def log_cmd(
    text: Optional[str] = typer.Argument(
        None, help="本轮对话/意图原文（会脱敏）。省略则只刷新时间线"
    ),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
    kind: Optional[str] = typer.Option(
        None,
        "--kind",
        help="consult | code | fix | docs | refactor | other",
    ),
    intent: Optional[str] = typer.Option(None, "--intent", help="一句话目标（可选）"),
    files: list[str] = typer.Option(
        [],
        "--file",
        help="涉及文件（可重复）。禁止编造；不确定就不要传",
    ),
) -> None:
    """脱敏后追加一条开发对话，并刷新时间线 / 建议。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    note = None
    if text or intent or files or kind:
        note = append_dialogue(
            root,
            text=text or "",
            kind=kind,
            intent=intent,
            files=list(files or []),
        )
        label = KIND_LABELS.get(note.kind, note.kind)
        console.print(f"[green]完成[/green] 已落盘对话 · {label} · {note.status}")
        console.print(f"  意图: {note.intent}")
        if note.files:
            console.print("  文件: " + "、".join(note.files))
        else:
            console.print("  文件: —（未解析，未编造）")
    report = write_journal(root)
    try:
        write_overview(root)
    except OSError:
        pass
    _audit(
        root,
        "pm-log",
        input_summary=(text or intent or "")[:80],
        output_summary=f"kind={note.kind if note else '-'} status={note.status if note else 'refresh'}",
    )
    top = report.suggestions[:3]
    if top:
        console.print("[bold]优化建议[/bold]")
        for item in top:
            console.print(f"  - [{item['priority']}] {item['title']} → {item['action']}")
    _print_open_links(
        "请打开这些记录",
        [
            ("对话记录", report.dialogue_path),
            ("迭代时间线", report.timeline_path),
            ("优化建议", report.suggestions_path),
        ],
    )


@app.command("journal")
def journal_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """刷新并打印本轮意图、变更点、时间线与优化建议。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        report = write_journal(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    try:
        write_overview(root)
    except OSError:
        pass
    session = report.session
    kind_zh = KIND_LABELS.get(str(session.get("kind") or ""), "其他")
    console.print("[bold]本轮意图[/bold]")
    console.print(f"  场景: {kind_zh}（{session.get('status')}）")
    console.print(f"  目标: {session.get('goal') or '信息不足'}")
    files = session.get("files") or []
    console.print("  文件: " + ("、".join(str(p) for p in files[:8]) if files else "—"))
    console.print(f"[bold]变更点[/bold]（{len(report.changes)}）")
    if not report.changes:
        console.print("  （无）")
    else:
        for row in report.changes[:8]:
            console.print(f"  - {row['path']}  [{row['source']}]")
    console.print(f"[bold]优化建议[/bold]（{len(report.suggestions)}）")
    if not report.suggestions:
        console.print("  （无）")
    else:
        for item in report.suggestions:
            console.print(
                f"  - [{item['priority']}] {item['title']} → {item['action']}"
            )
    console.print("[bold]最近迭代[/bold]")
    if not report.timeline:
        console.print("  （无）")
    else:
        for ev in report.timeline[:8]:
            label = KIND_LABELS.get(ev["kind"], ev["kind"])
            if ev["kind"] == "audit":
                label = "审计"
            elif ev["kind"] == "change":
                label = "变更"
            console.print(f"  - {ev['ts']} · {label} · {ev['title']}")
    _audit(
        root,
        "pm-journal",
        output_summary=(
            f"notes={len(report.notes)} changes={len(report.changes)} "
            f"suggestions={len(report.suggestions)}"
        ),
    )
    _print_open_links(
        "请打开这些记录",
        [
            ("迭代时间线", report.timeline_path),
            ("优化建议", report.suggestions_path),
            ("对话记录", report.dialogue_path),
            ("变更点", report.changes_path),
        ],
    )


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
    with_diagrams: bool = typer.Option(
        False,
        "--with-diagrams",
        help="把 .mmd 原文嵌入导出（默认只列架构路径）",
    ),
) -> None:
    """按时间窗导出脱敏后的治理报告（审计、对话、评审、缺口、架构路径）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        dest, n = write_export(
            root, since=since, until=until, out=out, with_diagrams=with_diagrams
        )
    except ValueError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(1) from exc
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    body = dest.read_text(encoding="utf-8") if dest.is_file() else ""
    if contains_secret_residue(body):
        if dest.is_file():
            dest.unlink(missing_ok=True)
        console.print("[red]错误[/red] 导出仍含秘密原文，已删除该文件")
        raise typer.Exit(2)
    console.print(f"[green]完成[/green] 已导出 {n} 条 -> {dest}")
    _audit(
        root,
        "pm-export",
        input_summary=f"from={since or ''} to={until or ''}",
        output_summary=str(dest),
    )
    _print_open_links("请打开导出文件", [("治理导出", dest)])


@app.command("tests")
def tests_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """列出核心源文件的单测缺口（不写业务树测试）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        dest, gaps = write_test_gaps(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    console.print(f"[green]完成[/green] 单测缺口 -> {dest}（{len(gaps)}）")
    for g in gaps[:16]:
        mark = "变更" if g.get("changed") else "核心"
        console.print(f"  - [{mark}] {g['path']} → {g['suggest']}")
    if not gaps:
        console.print("  （未发现缺口）")
    _audit(root, "pm-tests", output_summary=f"gaps={len(gaps)}")
    _print_open_links("请打开", [("单测缺口", dest)])


@app.command("gate")
def gate_cmd(
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """提交前门禁：不合格评审、P0、高危未评。警告不阻断。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        result = run_gate(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    if result.no_diff:
        console.print("[green]门禁通过[/green] 没有可评的变更")
    elif result.failures:
        console.print("[red]门禁未通过[/red]")
        for item in result.failures:
            console.print(f"  - {item}")
    else:
        console.print("[green]门禁通过[/green]")
    if result.warnings and not result.no_diff:
        console.print("[yellow]警告[/yellow]")
        for item in result.warnings:
            console.print(f"  - {item}")
    _audit(
        root,
        "pm-gate",
        output_summary=f"ok={result.ok} fail={len(result.failures)} warn={len(result.warnings)}",
    )
    links = []
    if result.guard_path:
        links.append(("幻觉防御", result.guard_path))
    if result.test_gaps_path:
        links.append(("单测缺口", result.test_gaps_path))
    if links:
        _print_open_links("请打开这些报告", links)
    if not result.ok:
        raise typer.Exit(1)


@app.command("hook")
def hook_cmd(
    action: str = typer.Argument(..., help="install | status | uninstall"),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
    force: bool = typer.Option(False, "--force", help="覆盖已有外来 pre-commit"),
) -> None:
    """可选安装本地 .git/hooks/pre-commit（init 不会自动装）。"""
    root = _resolve_root(path)
    act = action.strip().lower()
    if act not in {"install", "status", "uninstall"}:
        raise typer.BadParameter("action 必须是 install|status|uninstall")
    if act == "status":
        st = hook_status(root)
        labels = {
            "skipped": "不是 git 仓库",
            "absent": "未安装（可选：pm hook install）",
            "installed": "已安装本工具钩子",
            "foreign": "已有外来钩子（覆盖需 --force）",
            "unreadable": "无法读取钩子",
        }
        console.print(f"钩子: {labels.get(st, st)}")
        return
    if act == "uninstall":
        if uninstall_hook(root):
            console.print("[green]完成[/green] 已移除本工具 pre-commit")
        else:
            console.print("[dim]没有本工具安装的钩子[/dim]")
        return
    try:
        dest = install_hook(root, force=force)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    except FileExistsError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[green]完成[/green] 已安装本地钩子 -> {dest}")
    _audit(root, "pm-hook", input_summary=act, output_summary=str(dest))


@app.command("config")
def config_cmd(
    action: str = typer.Argument(..., help="apply"),
    name: str = typer.Argument(
        "auto", help="frontend | backend | service | script | auto"
    ),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
) -> None:
    """套用治理模板，只补缺失键，不覆盖用户已改项。"""
    root = _resolve_root(path)
    if action.strip().lower() != "apply":
        raise typer.BadParameter("目前只支持: pm config apply <template>")
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        dest, added = apply_profile(root, name)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    extra = "、".join(added) if added else "无（已有键未覆盖）"
    console.print(f"[green]完成[/green] 已套用 {name} -> {dest}")
    console.print(f"  补上: {extra}")
    _audit(root, "pm-config", input_summary=f"apply {name}", output_summary=extra)


@app.command("review")
def review_cmd(
    action: Optional[str] = typer.Argument(
        None,
        help="空=出草稿；confirm|false_positive|later|annotate；可加 --cross",
    ),
    target: Optional[str] = typer.Argument(None, help="REV-xxx（省略则处置最新 unset）"),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
    cross: bool = typer.Option(False, "--cross", help="交叉复核（第二遍不同策略）"),
) -> None:
    """Diff 评审草稿、交叉复核、处置与回填（不改业务代码）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    act = (action or "").strip().lower()
    if act in {"confirm", "false_positive", "later", "deferred"}:
        if act == "deferred":
            act = "later"
        try:
            row = dispose_review(root, act, target)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]错误[/red] {exc}")
            raise typer.Exit(1) from exc
        console.print(f"[green]完成[/green] {row.id} → {row.disposition}")
        if act == "confirm":
            console.print("  已沉淀到 .pm/engineering/rules.md")
        _audit(root, "pm-review", input_summary=f"{act} {row.id}", output_summary=row.disposition)
        return
    if act == "annotate":
        rid = target or ""
        if not rid:
            console.print("[red]错误[/red] 请提供 REV-xxx")
            raise typer.Exit(1)
        try:
            dest = write_annotation(root, rid)
        except FileNotFoundError as exc:
            console.print(f"[red]错误[/red] {exc}")
            raise typer.Exit(1) from exc
        console.print(f"[green]完成[/green] 回填草稿（仅 .pm/）-> {dest}")
        _audit(root, "pm-review", input_summary=f"annotate {rid}", output_summary=str(dest))
        _print_open_links("请打开", [("回填草稿", dest)])
        return
    if act and act not in {"cross"}:
        console.print("[red]错误[/red] 未知动作。用 confirm / false_positive / later / annotate 或省略出草稿")
        raise typer.Exit(1)
    try:
        if cross or act == "cross":
            added, dest = run_cross_review(root)
            console.print(f"[green]完成[/green] 交叉复核 新发现 {len(added)} -> {dest}")
            _audit(root, "pm-review", input_summary="cross", output_summary=f"new={len(added)}")
            _print_open_links("请打开", [("交叉复核", dest)])
            return
        added, dest, had = run_review(root)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    if not had:
        console.print("[green]没有可评的变更[/green]")
        _audit(root, "pm-review", output_summary="no-diff")
        return
    console.print(f"[green]完成[/green] 评审草稿 {len(added)} 条 -> {dest}")
    for row in added[:12]:
        mark = "打断" if str(row.severity).upper() == "P0" else row.severity
        console.print(f"  - [{mark}] {row.id} {row.summary}  `{row.file}`")
    p0 = [r for r in added if str(r.severity).upper() == "P0"]
    if p0:
        console.print(f"[red]P0 {len(p0)} 条，必须先处理[/red]")
    _audit(root, "pm-review", output_summary=f"added={len(added)}")
    _print_open_links(
        "请打开",
        [
            ("评审草稿", dest),
            ("评审表", root / ".pm" / "engineering" / "reviews.md"),
        ],
    )


@app.command("rules")
def rules_cmd(
    action: Optional[str] = typer.Argument(None, help="空=列出；enable|disable|add"),
    target: Optional[str] = typer.Argument(None, help="RULE-xxx 或新增规则正文"),
    path: Optional[Path] = typer.Option(
        None, "--path", help="目标项目根目录（默认当前目录）"
    ),
    from_finding: Optional[str] = typer.Option(
        None, "--from", help="来源 REV-xxx"
    ),
) -> None:
    """团队编码规范库（只读写 .pm/engineering/rules.md）。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    act = (action or "").strip().lower()
    if not act:
        rows = load_rules(root)
        console.print(f"[bold]规范库[/bold]（{len(rows)}，启用 {len(enabled_rules(root))}）")
        for r in rows:
            flag = "开" if r.enabled else "关"
            console.print(f"  - {r.id} [{flag}] {r.text}  ({r.source_finding})")
        if not rows:
            console.print("  （空）用 `pm review confirm REV-xxx` 或 `pm rules add \"…\"`")
        return
    if act in {"enable", "disable"}:
        if not target:
            console.print("[red]错误[/red] 需要 RULE-xxx")
            raise typer.Exit(1)
        try:
            rule = set_rule_enabled(root, target, act == "enable")
        except FileNotFoundError as exc:
            console.print(f"[red]错误[/red] {exc}")
            raise typer.Exit(1) from exc
        console.print(f"[green]完成[/green] {rule.id} enabled={rule.enabled}")
        _audit(root, "pm-rules", input_summary=f"{act} {rule.id}")
        return
    if act == "add":
        text = (target or "").strip()
        if not text:
            console.print("[red]错误[/red] 需要规则正文")
            raise typer.Exit(1)
        rule = add_rule(root, text, source_finding=from_finding or "")
        console.print(f"[green]完成[/green] {rule.id} {rule.text}")
        _audit(root, "pm-rules", input_summary=f"add {rule.id}")
        return
    console.print("[red]错误[/red] 未知动作。用 enable / disable / add")
    raise typer.Exit(1)


@app.command("checkup")
def checkup_cmd(
    path: Optional[Path] = typer.Argument(
        None, help="目标项目根目录（默认当前目录）"
    ),
    module: Optional[str] = typer.Option(
        None, "--module", help="只扫某个模块目录名"
    ),
) -> None:
    """按需五维体检（安全/功能/完成度/质量/文档）。无定时器。"""
    root = _resolve_root(path)
    if not (root / ".pm").is_dir():
        _exit_missing_pm(root)
    try:
        report = run_checkup(root, module=module)
    except FileNotFoundError as exc:
        console.print(f"[red]错误[/red] {exc}")
        raise typer.Exit(2) from exc
    counts = report.get("counts") or {}
    console.print(
        f"[green]完成[/green] 体检 P0={counts.get('P0', 0)} "
        f"P1={counts.get('P1', 0)} P2={counts.get('P2', 0)}"
    )
    p0 = [f for f in report.get("findings") or [] if f.get("severity") == "P0"]
    if p0:
        console.print("[red]P0 必须处理[/red]")
        for item in p0[:8]:
            console.print(f"  - [{item['dimension']}] {item['title']}  {item.get('path') or ''}")
    dest = root / ".pm" / "state" / "checkup.md"
    _audit(
        root,
        "pm-checkup",
        input_summary=module or "",
        output_summary=f"P0={counts.get('P0', 0)} P1={counts.get('P1', 0)}",
    )
    _print_open_links("请打开", [("体检报告", dest)])


if __name__ == "__main__":
    app()
