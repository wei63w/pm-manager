"""Assemble `.pm/state/overview.md` (and report.md) from map + docs + todos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.architecture import load_map
from pm_manager_cli.dashboard import collect, hot_open_todos, module_risk_score
from pm_manager_cli.docs_index import scan_core_docs
from pm_manager_cli.journal import KIND_LABELS, load_session
from pm_manager_cli.reviews import pending_review_count
from pm_manager_cli.speckit import read_prd_status


def _read_yaml_field(root: Path, key: str) -> str:
    cfg = root / ".pm" / "config" / "project.yaml"
    if not cfg.is_file():
        return ""
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return ""
    import re

    m = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(\S+)", text)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'")


def _wizard_steps(
    root: Path,
    *,
    prd_status: str,
    has_map: bool,
    has_dash: bool,
    todo_n: int,
    review_n: int,
) -> list[str]:
    steps: list[str] = []
    if not (root / ".pm").is_dir():
        return ["还没有治理台 → 运行 `/pm-init`"]
    if prd_status == "draft":
        steps.append("PRD 仍是草稿 → 回复 `confirm` / `revise: …` / `skip`（跳过仍可做技术扫描）")
    if not has_map:
        steps.append("还没有导航地图 → 运行 `pm arch` 或 `/pm-arch`")
    if not has_dash:
        steps.append("看板尚未生成 → 运行 `/pm-all` 或 `pm dashboard`（默认技术扫描）")
    if todo_n:
        steps.append(f"有 {todo_n} 条未关闭阻断/高优先级待办 → `/pm-status` 或 `/pm-next`")
    if review_n:
        steps.append(f"有 {review_n} 条待处置评审 → `/pm-review`")
    if not steps:
        steps.append("治理台可用。日常 `/pm-status`；贴报错 `/pm-fix`；发布前 `/pm-all`。")
    return steps


def write_overview(project_root: Path) -> Path:
    """Refresh `.pm/state/overview.md` and `report.md`. Requires `.pm/`."""
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")

    nav = load_map(root) or {}
    docs = scan_core_docs(root)
    missing = [e for e in docs if e.status == "missing"]
    stale = [e for e in docs if e.status == "possibly_stale"]
    prd_status = read_prd_status(root) or "absent"
    pending = pending_review_count(root)

    todos = hot_open_todos(pm)
    findings, all_todos, scanned = collect(pm)
    risk: dict[str, int] = {}
    for mod in scanned:
        sev = {}
        for f in findings:
            if f.module == mod and f.status not in {"done", "resolved", "wontfix"}:
                sev[f.severity] = sev.get(f.severity, 0) + 1
        t_count = sum(
            1
            for t in all_todos
            if t.module == mod and t.status not in {"done", "cancelled"}
        )
        risk[mod] = module_risk_score(
            {
                "blocking": sev.get("blocking", 0),
                "high": sev.get("high", 0),
                "medium": sev.get("medium", 0),
                "low": sev.get("low", 0),
                "suggestion": sev.get("suggestion", 0),
            },
            t_count,
        )
    ranked = sorted(risk, key=lambda m: (-risk[m], m))

    stacks = nav.get("stacks") or []
    modules = nav.get("modules") or []
    key_files = nav.get("key_files") or []
    has_map = bool(nav)
    has_dash = (pm / "dashboard" / "index.html").is_file()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lifecycle = _read_yaml_field(root, "lifecycle") or "unknown"
    process = _read_yaml_field(root, "mode") or "agile"
    cfg = pm / "config" / "project.yaml"
    charter_status = "absent"
    outline_status = "absent"
    if cfg.is_file():
        text = cfg.read_text(encoding="utf-8")
        import re

        cm = re.search(r"(?ms)^charter:\s*\n(?:[ \t].*\n)*?[ \t]+status:\s*(\S+)", text)
        om = re.search(r"(?ms)^outline:\s*\n(?:[ \t].*\n)*?[ \t]+status:\s*(\S+)", text)
        if cm:
            charter_status = cm.group(1).strip().strip("\"'")
        if om:
            outline_status = om.group(1).strip().strip("\"'")

    wizard = _wizard_steps(
        root,
        prd_status=prd_status,
        has_map=has_map,
        has_dash=has_dash,
        todo_n=len(todos),
        review_n=pending,
    )

    def _mod_name(m: object) -> str:
        if isinstance(m, dict):
            return str(m.get("name") or "")
        return str(m)

    def _kf_line(k: object) -> str:
        if isinstance(k, dict):
            return f"`{k.get('path', '')}`（{k.get('role', '')}）"
        return f"`{k}`"

    stack_s = ", ".join(str(s) for s in stacks) if stacks else "尚未扫描（运行 `pm arch`）"
    mod_s = ", ".join(_mod_name(m) for m in modules if _mod_name(m)) or "—"
    entries = [_kf_line(k) for k in key_files[:8]] or ["—"]

    health_rows = ["| 模块 | 状态 | 阻断 | 高 | 中 | 低 | 上次扫描 |", "|------|------|------|----|----|----|----------|"]
    if not scanned:
        health_rows.append("| — | 未扫描 | 0 | 0 | 0 | 0 | — |")
    else:
        for mod in scanned:
            sev = {"blocking": 0, "high": 0, "medium": 0, "low": 0}
            for f in findings:
                if f.module == mod and f.status not in {"done", "resolved", "wontfix"}:
                    if f.severity in sev:
                        sev[f.severity] += 1
            health_rows.append(
                f"| {mod} | 已扫描 | {sev['blocking']} | {sev['high']} | "
                f"{sev['medium']} | {sev['low']} | {now} |"
            )

    todo_lines = []
    if todos:
        for t in todos:
            todo_lines.append(f"- `{t.id}` [{t.priority}] {t.title}（{t.status}）")
    else:
        todo_lines.append("- （还没有阻断/高优先级待办）")

    session = load_session(root)
    session_kind = KIND_LABELS.get(str(session.get("kind") or ""), str(session.get("kind") or "其他"))
    session_files = session.get("files") or []
    session_file_s = "、".join(f"`{p}`" for p in session_files[:8]) if session_files else "—"
    sug_path = pm / "state" / "suggestions.md"
    sug_lines: list[str] = []
    if sug_path.is_file():
        for line in sug_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- `SUG-"):
                sug_lines.append(line)
            if len(sug_lines) >= 5:
                break
    if not sug_lines:
        sug_lines = ["- 运行 `pm journal` 刷新建议"]

    miss_lines = [f"- `{e.id}` {e.expected}" for e in missing] or ["- 无"]
    stale_lines = [f"- `{e.id}` `{e.path}`" for e in stale] or ["- 无"]
    if ranked:
        risk_lines = [f"- `{m}` 风险分 {risk[m]}" for m in ranked[:8] if risk[m] > 0]
        if not risk_lines:
            risk_lines = ["- 已扫描模块暂无计分风险"]
    else:
        risk_lines = ["- 未扫描（运行 `/pm-all` 或 `pm dashboard`）"]

    body = "\n".join(
        [
            "# 项目治理总览",
            "",
            f"> 更新时间: {now} | 触发: cli-snapshot",
            f"> 生命周期: {lifecycle} | 过程: {process} | 宪章: {charter_status} | "
            f"提纲: {outline_status} | PRD: {prd_status}",
            "",
            "## 现状快照",
            "",
            f"- 技术栈: {stack_s}",
            f"- 模块（{len(modules) if modules else 0}）: {mod_s}",
            "- 核心入口: " + "；".join(entries),
            f"- 缺失核心文档: {len(missing)}",
            f"- 可能过期文档: {len(stale)}",
            f"- 待处置评审: {pending}",
            "",
            "## 本轮意图",
            "",
            f"- 场景: {session_kind}（{session.get('status', 'unresolved')}）",
            f"- 目标: {session.get('goal') or '信息不足'}",
            f"- 变更文件: {session_file_s}",
            f"- 对话条数: {session.get('note_count', 0)}",
            "",
            "## 优化建议（前 5）",
            "",
            *sug_lines,
            "",
            "## 健康",
            "",
            *health_rows,
            "",
            "## 向导（有哪条做哪条）",
            "",
            *[f"{i}. {s}" for i, s in enumerate(wizard, 1)],
            "",
            "## 缺失资产",
            "",
            *miss_lines,
            "",
            "## 可能过期",
            "",
            *stale_lines,
            "",
            "## 风险模块",
            "",
            *risk_lines,
            "",
            "## 未关闭的阻断 / 高优先级待办",
            "",
            *todo_lines,
            "",
            "## 建议下一步",
            "",
            "1. 先完成上面的向导",
            "2. 日常：`/pm-status` → `/pm-next` → `/pm-done`",
            "3. 贴报错：`/pm-fix`（只分诊，不改代码）",
            "4. 定位文件：先 `pm map` / 读 `.pm/architecture/map.json`",
            "5. 复盘本轮：`pm journal` / `/pm-journal`（时间线 + 变更点 + 建议）",
            "",
        ]
    )
    dest = pm / "state" / "overview.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    (pm / "state" / "report.md").write_text(body, encoding="utf-8")
    return dest


def print_status_lines(project_root: Path) -> list[str]:
    """Short Chinese snapshot lines for `pm status`."""
    root = project_root.resolve()
    nav = load_map(root) or {}
    docs = scan_core_docs(root)
    stacks = nav.get("stacks") or []
    modules = nav.get("modules") or []
    prd = read_prd_status(root) or "absent"
    pending = pending_review_count(root)
    todos = hot_open_todos(root / ".pm")
    miss = sum(1 for e in docs if e.status == "missing")
    stale = sum(1 for e in docs if e.status == "possibly_stale")
    stack_s = ", ".join(str(s) for s in stacks) if stacks else "尚未扫描"
    nmod = len(modules) if modules else 0
    return [
        f"技术栈: {stack_s}",
        f"模块: {nmod}",
        f"缺失核心文档: {miss}" + (f"；可能过期: {stale}" if stale else ""),
        f"prd.status: {prd}",
        f"未关闭阻断/高优先级待办（{len(todos)}）",
        f"待处置评审: {pending}",
    ]
