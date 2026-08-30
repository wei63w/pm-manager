"""Build .pm/dashboard aggregate views from module findings and todos."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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

SEVERITY_ORDER = ["blocking", "high", "medium", "low", "suggestion"]
SEVERITY_ALIASES = {
    "blocking": "blocking",
    "阻断": "blocking",
    "block": "blocking",
    "high": "high",
    "高": "high",
    "medium": "medium",
    "中": "medium",
    "low": "low",
    "低": "low",
    "suggestion": "suggestion",
    "建议": "suggestion",
    "info": "suggestion",
}

STATUS_OPEN = {"open", "in_progress", "blocked", "进行中", "开放", "阻塞"}
STATUS_DONE = {"done", "resolved", "wontfix", "cancelled", "已完成", "关闭", "拒绝"}


@dataclass
class Finding:
    id: str
    module: str
    title: str
    severity: str
    status: str
    source_path: str


@dataclass
class Todo:
    id: str
    module: str
    title: str
    priority: str
    status: str
    source_path: str


SEVERITY_WEIGHT = {
    "blocking": 100,
    "high": 40,
    "medium": 10,
    "low": 3,
    "suggestion": 1,
}
HEALTH_PENALTY = {
    "blocking": 25,
    "high": 10,
    "medium": 3,
    "low": 1,
    "suggestion": 0.5,
}


@dataclass
class DashboardStats:
    generated_at: str
    modules_scanned: list[str] = field(default_factory=list)
    findings_by_severity: dict[str, int] = field(default_factory=dict)
    findings_by_module: dict[str, dict[str, int]] = field(default_factory=dict)
    todos_by_status: dict[str, int] = field(default_factory=dict)
    todos_by_module: dict[str, int] = field(default_factory=dict)
    todos_by_priority: dict[str, int] = field(default_factory=dict)
    module_risk: dict[str, int] = field(default_factory=dict)
    open_findings: int = 0
    open_todos: int = 0
    hot_count: int = 0
    health_score: int = 100
    health_label: str = "healthy"


def _norm_severity(raw: str) -> str:
    key = raw.strip().lower()
    return SEVERITY_ALIASES.get(key, key if key in SEVERITY_ORDER else "medium")


def _norm_status(raw: str) -> str:
    key = raw.strip().lower()
    if key in STATUS_DONE or any(k in key for k in ("done", "resolved", "wontfix")):
        return "done"
    if "progress" in key or key in {"in_progress", "进行中"}:
        return "in_progress"
    if "block" in key or key in {"blocked", "阻塞"}:
        return "blocked"
    return "open"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    # utf-8-sig strips BOM so first headings still match ^#
    return path.read_text(encoding="utf-8-sig", errors="replace")


def parse_findings(module: str, path: Path) -> list[Finding]:
    text = _read(path).replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return []
    findings: list[Finding] = []
    matches = list(re.finditer(r"(?m)^#{2,3}\s+(finding-[\w-]+)\s*$", text))
    for idx, m in enumerate(matches):
        fid = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        title = fid
        title_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Title|标题)\*\*\s*[:：]\s*(.+)$", body
        )
        if title_m:
            title = title_m.group(1).strip()
        else:
            for line in body.splitlines():
                s = line.strip()
                if s and not s.startswith("#") and not re.match(r"^[-*]\s*\*\*", s):
                    title = s.lstrip("-* ").strip()
                    break
        sev_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Severity|等级|Level)\*\*\s*[:：]\s*(.+)$", body
        )
        st_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Status|状态)\*\*\s*[:：]\s*(.+)$", body
        )
        severity = _norm_severity(
            sev_m.group(1).split("|")[0].strip() if sev_m else "medium"
        )
        status = _norm_status(st_m.group(1).split("|")[0].strip() if st_m else "open")
        findings.append(
            Finding(
                id=fid,
                module=module,
                title=title,
                severity=severity,
                status=status,
                source_path=str(path.as_posix()),
            )
        )
    return findings


def parse_todos(module: str, path: Path) -> list[Todo]:
    text = _read(path).replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return []
    todos: list[Todo] = []
    matches = list(
        re.finditer(
            r"(?m)^#{2,3}\s+(TODO-[\w-]+)(?:\s+(\[[^\]]+\]))?\s*(.*)$", text
        )
    )
    for idx, m in enumerate(matches):
        tid = m.group(1).strip()
        bracket = (m.group(2) or "").strip()
        heading_rest = (m.group(3) or "").strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        title = heading_rest or tid
        pri = "P2"
        if bracket:
            inner = bracket.strip("[]").strip()
            if re.match(r"(?i)^p[0-3]$", inner):
                pri = inner.upper()
            else:
                sev = _norm_severity(inner)
                pri = {
                    "blocking": "P0",
                    "high": "P1",
                    "medium": "P2",
                    "low": "P3",
                }.get(sev, "P2")
        st_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Status|状态)\*\*\s*[:：]\s*(.+)$", body
        )
        mod_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Module|模块)\*\*\s*[:：]\s*(.+)$", body
        )
        pri_m = re.search(
            r"(?im)^\s*[-*]\s*\*\*(?:Priority|优先级)\*\*\s*[:：]\s*(.+)$", body
        )
        if pri_m:
            p = pri_m.group(1).split("|")[0].strip()
            if re.match(r"(?i)^p[0-3]$", p):
                pri = p.upper()
        status = _norm_status(st_m.group(1).split("|")[0].strip() if st_m else "open")
        mod = mod_m.group(1).strip() if mod_m else module
        todos.append(
            Todo(
                id=tid,
                module=mod,
                title=title,
                priority=pri.upper(),
                status=status,
                source_path=str(path.as_posix()),
            )
        )
    return todos


def collect(pm_root: Path) -> tuple[list[Finding], list[Todo], list[str]]:
    findings: list[Finding] = []
    todos: list[Todo] = []
    scanned: list[str] = []
    for mod in MODULES:
        mod_dir = pm_root / mod
        if not mod_dir.is_dir():
            continue
        scanned.append(mod)
        findings.extend(parse_findings(mod, mod_dir / "findings.md"))
        todos.extend(parse_todos(mod, mod_dir / "todo.md"))
    # authoritative cross-module todos
    state_todos = parse_todos("state", pm_root / "state" / "todo.md")
    # Prefer state todos when same id exists
    by_id = {t.id: t for t in todos}
    for t in state_todos:
        by_id[t.id] = t
    return findings, list(by_id.values()), scanned


def hot_open_todos(pm_root: Path) -> list[Todo]:
    """Open/in_progress todos at blocking (P0) or high (P1). No 3-item cap."""
    _findings, todos, _scanned = collect(pm_root)
    hot = [
        t
        for t in todos
        if t.status in {"open", "in_progress"} and t.priority.upper() in {"P0", "P1"}
    ]
    hot.sort(key=lambda t: (0 if t.priority.upper() == "P0" else 1, t.id))
    return hot


def module_risk_score(sev_counts: dict[str, int], open_todos: int) -> int:
    score = sum(
        sev_counts.get(sev, 0) * SEVERITY_WEIGHT[sev] for sev in SEVERITY_ORDER
    )
    return score + open_todos * 5


def compute_health(
    findings_by_severity: dict[str, int], open_todos: list[Todo]
) -> tuple[int, str]:
    penalty = sum(
        findings_by_severity.get(sev, 0) * HEALTH_PENALTY[sev] for sev in SEVERITY_ORDER
    )
    for t in open_todos:
        pri = t.priority.upper()
        if pri == "P0":
            penalty += 8
        elif pri == "P1":
            penalty += 4
        elif pri == "P2":
            penalty += 1
    score = max(0, min(100, int(round(100 - penalty))))
    if score >= 85:
        label = "healthy"
    elif score >= 65:
        label = "watch"
    elif score >= 40:
        label = "at_risk"
    else:
        label = "critical"
    return score, label


def build_stats(findings: list[Finding], todos: list[Todo], scanned: list[str]) -> DashboardStats:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stats = DashboardStats(generated_at=now, modules_scanned=scanned)
    open_f = [f for f in findings if f.status not in {"done", "resolved", "wontfix"}]
    open_t = [t for t in todos if t.status not in {"done", "cancelled"}]
    stats.open_findings = len(open_f)
    stats.open_todos = len(open_t)
    stats.hot_count = sum(1 for f in open_f if f.severity in {"blocking", "high"})
    for sev in SEVERITY_ORDER:
        stats.findings_by_severity[sev] = sum(1 for f in open_f if f.severity == sev)
    for mod in scanned:
        sev_counts = {
            sev: sum(1 for f in open_f if f.module == mod and f.severity == sev)
            for sev in SEVERITY_ORDER
        }
        stats.findings_by_module[mod] = sev_counts
        t_count = sum(1 for t in open_t if t.module == mod)
        stats.todos_by_module[mod] = t_count
        stats.module_risk[mod] = module_risk_score(sev_counts, t_count)
    for st in ("open", "in_progress", "blocked", "done"):
        stats.todos_by_status[st] = sum(1 for t in todos if t.status == st)
    for pri in ("P0", "P1", "P2", "P3"):
        stats.todos_by_priority[pri] = sum(
            1 for t in open_t if t.priority.upper() == pri
        )
    score, label = compute_health(stats.findings_by_severity, open_t)
    stats.health_score = score
    stats.health_label = label
    return stats


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def _bar(count: int, max_count: int, width: int = 16) -> str:
    if max_count <= 0 or count <= 0:
        return "·" * width if count == 0 else "█" * max(1, min(width, count))
    filled = max(1, int(round(width * count / max_count))) if count else 0
    filled = min(width, filled)
    return "█" * filled + "░" * (width - filled)


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_overview(stats: DashboardStats, findings: list[Finding], todos: list[Todo]) -> str:
    open_f = [f for f in findings if f.status not in {"done", "resolved", "wontfix"}]
    open_t = [t for t in todos if t.status not in {"done", "cancelled"}]
    sev = stats.findings_by_severity
    max_sev = max(sev.values()) if sev else 0
    max_risk = max(stats.module_risk.values()) if stats.module_risk else 0

    lines = [
        "# Governance dashboard",
        "",
        f"> Generated: {stats.generated_at} (UTC)  ",
        f"> Visual UI: open [`index.html`](./index.html) in a browser",
        "",
        "## KPI snapshot",
        "",
        "| Health | Score | Open findings | Hot (B+H) | Open todos | Modules |",
        "|--------|------:|--------------:|----------:|-----------:|--------:|",
        f"| **{stats.health_label}** | **{stats.health_score}/100** | "
        f"{stats.open_findings} | {stats.hot_count} | {stats.open_todos} | "
        f"{len(stats.modules_scanned)} |",
        "",
        "## Severity distribution (open)",
        "",
        "| Severity | Count | Share | Distribution |",
        "|----------|------:|------:|--------------|",
    ]
    total_f = max(stats.open_findings, 1)
    for name in SEVERITY_ORDER:
        c = sev.get(name, 0)
        pct = int(round(100 * c / total_f)) if stats.open_findings else 0
        lines.append(f"| {name} | {c} | {pct}% | `{_bar(c, max_sev)}` |")

    lines += [
        "",
        "## Module risk ranking",
        "",
        "_Risk = blocking×100 + high×40 + medium×10 + low×3 + suggestion×1 + open_todos×5_",
        "",
        "| Rank | Module | Risk | B | H | M | L | S | Todos | Heat |",
        "|-----:|--------|-----:|--:|--:|--:|--:|--:|------:|------|",
    ]
    ranked = sorted(
        stats.modules_scanned,
        key=lambda m: (-stats.module_risk.get(m, 0), m),
    )
    for i, mod in enumerate(ranked, 1):
        c = stats.findings_by_module.get(mod, {})
        risk = stats.module_risk.get(mod, 0)
        lines.append(
            f"| {i} | {mod} | {risk} | {c.get('blocking', 0)} | {c.get('high', 0)} | "
            f"{c.get('medium', 0)} | {c.get('low', 0)} | {c.get('suggestion', 0)} | "
            f"{stats.todos_by_module.get(mod, 0)} | `{_bar(risk, max_risk)}` |"
        )

    lines += [
        "",
        "## Todo priority mix (open)",
        "",
        "| Priority | Count | Distribution |",
        "|----------|------:|--------------|",
    ]
    max_pri = max(stats.todos_by_priority.values()) if stats.todos_by_priority else 0
    for pri in ("P0", "P1", "P2", "P3"):
        c = stats.todos_by_priority.get(pri, 0)
        lines.append(f"| {pri} | {c} | `{_bar(c, max_pri)}` |")

    lines += [
        "",
        "## Hot list (blocking + high)",
        "",
    ]
    hot = [f for f in open_f if f.severity in {"blocking", "high"}]
    hot.sort(key=lambda f: (SEVERITY_ORDER.index(f.severity), f.module, f.id))
    if not hot:
        lines.append("_No blocking/high open findings._")
    else:
        lines.append("| Severity | Module | ID | Title |")
        lines.append("|----------|--------|----|-------|")
        for f in hot[:50]:
            lines.append(
                f"| {f.severity} | {f.module} | {f.id} | {_md_escape(f.title)} |"
            )

    lines += [
        "",
        "## Open todos (priority order)",
        "",
    ]
    pri_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    open_t.sort(key=lambda t: (pri_rank.get(t.priority.upper(), 9), t.module, t.id))
    if not open_t:
        lines.append("_No open todos._")
    else:
        lines.append("| Priority | Status | Module | ID | Title |")
        lines.append("|----------|--------|--------|----|-------|")
        for t in open_t[:50]:
            lines.append(
                f"| {t.priority} | {t.status} | {t.module} | {t.id} | {_md_escape(t.title)} |"
            )

    lines += [
        "",
        "## Files in this folder",
        "",
        "- [`index.html`](./index.html) — visual dashboard (open in browser)",
        "- [`overview.md`](./overview.md) — this page (IDE-friendly tables)",
        "- [`findings.md`](./findings.md) — all open findings",
        "- [`todos.md`](./todos.md) — all open todos",
        "- [`stats.json`](./stats.json) — machine-readable counts",
        "",
        "Regenerate with `pm dashboard` or after `/pm-all`.",
        "",
    ]
    return "\n".join(lines)


def render_findings(findings: list[Finding]) -> str:
    open_f = [f for f in findings if f.status not in {"done", "resolved", "wontfix"}]
    open_f.sort(
        key=lambda f: (
            SEVERITY_ORDER.index(f.severity) if f.severity in SEVERITY_ORDER else 9,
            f.module,
        )
    )
    lines = ["# Aggregated findings (open)", ""]
    if not open_f:
        lines.append("_None._")
        return "\n".join(lines) + "\n"
    for f in open_f:
        lines += [
            f"## {f.id}",
            "",
            f"- **Module**: {f.module}",
            f"- **Severity**: {f.severity}",
            f"- **Status**: {f.status}",
            f"- **Title**: {f.title}",
            f"- **Source**: `{f.source_path}`",
            "",
        ]
    return "\n".join(lines)


def render_todos(todos: list[Todo]) -> str:
    open_t = [t for t in todos if t.status not in {"done", "cancelled"}]
    pri_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    open_t.sort(key=lambda t: (pri_rank.get(t.priority.upper(), 9), t.module, t.id))
    lines = ["# Aggregated todos (open)", ""]
    if not open_t:
        lines.append("_None._")
        return "\n".join(lines) + "\n"
    for t in open_t:
        lines += [
            f"## {t.id}",
            "",
            f"- **Module**: {t.module}",
            f"- **Priority**: {t.priority}",
            f"- **Status**: {t.status}",
            f"- **Title**: {t.title}",
            f"- **Source**: `{t.source_path}`",
            "",
        ]
    return "\n".join(lines)


def render_html(stats: DashboardStats, findings: list[Finding], todos: list[Todo]) -> str:
    open_f = [f for f in findings if f.status not in {"done", "resolved", "wontfix"}]
    open_t = [t for t in todos if t.status not in {"done", "cancelled"}]
    hot = [f for f in open_f if f.severity in {"blocking", "high"}]
    hot.sort(key=lambda f: (SEVERITY_ORDER.index(f.severity), f.module, f.id))
    pri_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    open_t_sorted = sorted(
        open_t, key=lambda t: (pri_rank.get(t.priority.upper(), 9), t.module, t.id)
    )
    ranked = sorted(
        stats.modules_scanned,
        key=lambda m: (-stats.module_risk.get(m, 0), m),
    )
    max_sev = max(stats.findings_by_severity.values()) if stats.findings_by_severity else 1
    max_risk = max(stats.module_risk.values()) if stats.module_risk else 1
    max_pri = max(stats.todos_by_priority.values()) if any(stats.todos_by_priority.values()) else 1

    sev_rows = []
    colors = {
        "blocking": "#b42318",
        "high": "#c4320a",
        "medium": "#b54708",
        "low": "#175cd3",
        "suggestion": "#667085",
    }
    for name in SEVERITY_ORDER:
        c = stats.findings_by_severity.get(name, 0)
        pct = (100 * c / max_sev) if max_sev else 0
        sev_rows.append(
            f'<div class="bar-row"><span class="bar-label">{name}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;'
            f'background:{colors[name]}"></div></div>'
            f'<span class="bar-count">{c}</span></div>'
        )

    risk_rows = []
    for mod in ranked:
        c = stats.findings_by_module.get(mod, {})
        risk = stats.module_risk.get(mod, 0)
        pct = (100 * risk / max_risk) if max_risk else 0
        heat = (
            "heat-crit"
            if risk >= 100
            else "heat-high"
            if risk >= 40
            else "heat-mid"
            if risk > 0
            else "heat-ok"
        )
        risk_rows.append(
            f"<tr class='{heat}'><td>{_html_escape(mod)}</td><td class='num'>{risk}</td>"
            f"<td class='num'>{c.get('blocking', 0)}</td>"
            f"<td class='num'>{c.get('high', 0)}</td>"
            f"<td class='num'>{c.get('medium', 0)}</td>"
            f"<td class='num'>{c.get('low', 0)}</td>"
            f"<td class='num'>{c.get('suggestion', 0)}</td>"
            f"<td class='num'>{stats.todos_by_module.get(mod, 0)}</td>"
            f'<td><div class="mini-track"><div class="mini-fill" style="width:{pct:.1f}%"></div></div></td></tr>'
        )

    pri_rows = []
    for pri in ("P0", "P1", "P2", "P3"):
        c = stats.todos_by_priority.get(pri, 0)
        pct = (100 * c / max_pri) if max_pri else 0
        pri_rows.append(
            f'<div class="bar-row"><span class="bar-label">{pri}</span>'
            f'<div class="bar-track"><div class="bar-fill pri" style="width:{pct:.1f}%"></div></div>'
            f'<span class="bar-count">{c}</span></div>'
        )

    hot_rows = []
    if not hot:
        hot_rows.append('<tr><td colspan="4" class="empty">No blocking/high findings</td></tr>')
    else:
        for f in hot[:40]:
            hot_rows.append(
                f"<tr><td><span class='badge {f.severity}'>{f.severity}</span></td>"
                f"<td>{_html_escape(f.module)}</td>"
                f"<td><code>{_html_escape(f.id)}</code></td>"
                f"<td>{_html_escape(f.title)}</td></tr>"
            )

    todo_rows = []
    if not open_t_sorted:
        todo_rows.append('<tr><td colspan="5" class="empty">No open todos</td></tr>')
    else:
        for t in open_t_sorted[:40]:
            todo_rows.append(
                f"<tr><td><span class='badge pri'>{_html_escape(t.priority)}</span></td>"
                f"<td>{_html_escape(t.status)}</td>"
                f"<td>{_html_escape(t.module)}</td>"
                f"<td><code>{_html_escape(t.id)}</code></td>"
                f"<td>{_html_escape(t.title)}</td></tr>"
            )

    label = stats.health_label
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>PM Governance Dashboard</title>
<style>
:root {{
  --bg: #f4f6f8;
  --panel: #ffffff;
  --ink: #1a2332;
  --muted: #5b6b7c;
  --line: #d8dee6;
  --accent: #0f6e56;
  --accent-soft: #e4f2ed;
  --crit: #b42318;
  --high: #c4320a;
  --mid: #b54708;
  --ok: #0f6e56;
  --shadow: 0 1px 2px rgba(26,35,50,.06), 0 8px 24px rgba(26,35,50,.06);
  --font: "Segoe UI", "Helvetica Neue", sans-serif;
  --mono: ui-monospace, "Cascadia Code", Consolas, monospace;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; font-family: var(--font); color: var(--ink); background:
    radial-gradient(1200px 500px at 10% -10%, #dceee8 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #e8eef5 0%, transparent 50%),
    var(--bg);
  line-height: 1.45;
}}
.wrap {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 64px; }}
header {{ display: flex; flex-wrap: wrap; gap: 16px; justify-content: space-between; align-items: end; margin-bottom: 22px; }}
header h1 {{ margin: 0; font-size: 1.55rem; letter-spacing: -0.02em; }}
header p {{ margin: 4px 0 0; color: var(--muted); font-size: .92rem; }}
.health {{
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 14px 18px; min-width: 160px; box-shadow: var(--shadow); text-align: right;
}}
.health .score {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.03em; }}
.health .label {{ text-transform: uppercase; font-size: .72rem; letter-spacing: .08em; font-weight: 600; }}
.health.healthy .score, .health.healthy .label {{ color: var(--ok); }}
.health.watch .score, .health.watch .label {{ color: var(--mid); }}
.health.at_risk .score, .health.at_risk .label {{ color: var(--high); }}
.health.critical .score, .health.critical .label {{ color: var(--crit); }}
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }}
@media (max-width: 800px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
.kpi {{
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 16px 18px; box-shadow: var(--shadow);
}}
.kpi .n {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em; }}
.kpi .t {{ color: var(--muted); font-size: .82rem; margin-top: 2px; }}
.grid {{ display: grid; grid-template-columns: 1.1fr 1fr; gap: 14px; margin-bottom: 14px; }}
@media (max-width: 860px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.panel {{
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 16px 18px; box-shadow: var(--shadow);
}}
.panel h2 {{ margin: 0 0 12px; font-size: 1rem; }}
.panel .hint {{ color: var(--muted); font-size: .78rem; margin: -6px 0 12px; }}
.bar-row {{ display: grid; grid-template-columns: 88px 1fr 36px; gap: 8px; align-items: center; margin: 7px 0; }}
.bar-label {{ font-size: .82rem; color: var(--muted); }}
.bar-count {{ text-align: right; font-variant-numeric: tabular-nums; font-size: .85rem; }}
.bar-track, .mini-track {{ height: 10px; background: #eef2f6; border-radius: 999px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 999px; }}
.bar-fill.pri {{ background: var(--accent); }}
.mini-fill {{ height: 100%; background: linear-gradient(90deg, #7eb8a4, #0f6e56); }}
table {{ width: 100%; border-collapse: collapse; font-size: .88rem; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
th {{ color: var(--muted); font-weight: 600; font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
td.empty {{ color: var(--muted); text-align: center; padding: 18px; }}
tr.heat-crit td:first-child {{ box-shadow: inset 3px 0 0 var(--crit); }}
tr.heat-high td:first-child {{ box-shadow: inset 3px 0 0 var(--high); }}
tr.heat-mid td:first-child {{ box-shadow: inset 3px 0 0 var(--mid); }}
tr.heat-ok td:first-child {{ box-shadow: inset 3px 0 0 #98a2b3; }}
.badge {{
  display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: .72rem;
  font-weight: 600; text-transform: uppercase; letter-spacing: .03em;
}}
.badge.blocking {{ background: #fee4e2; color: var(--crit); }}
.badge.high {{ background: #ffead5; color: var(--high); }}
.badge.pri {{ background: var(--accent-soft); color: var(--accent); }}
code {{ font-family: var(--mono); font-size: .8rem; }}
.stack {{ display: flex; flex-direction: column; gap: 14px; }}
footer {{ margin-top: 18px; color: var(--muted); font-size: .8rem; }}
footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>PM Governance Dashboard</h1>
      <p>Aggregate of module findings &amp; todos - Generated {_html_escape(stats.generated_at)} UTC</p>
    </div>
    <div class="health {label}">
      <div class="score">{stats.health_score}</div>
      <div class="label">{_html_escape(label)} / 100</div>
    </div>
  </header>

  <section class="kpis">
    <div class="kpi"><div class="n">{stats.open_findings}</div><div class="t">Open findings</div></div>
    <div class="kpi"><div class="n">{stats.hot_count}</div><div class="t">Hot (blocking + high)</div></div>
    <div class="kpi"><div class="n">{stats.open_todos}</div><div class="t">Open todos</div></div>
    <div class="kpi"><div class="n">{len(stats.modules_scanned)}</div><div class="t">Modules scanned</div></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h2>Severity distribution</h2>
      {''.join(sev_rows)}
    </div>
    <div class="panel">
      <h2>Todo priority mix</h2>
      {''.join(pri_rows)}
    </div>
  </section>

  <section class="panel" style="margin-bottom:14px">
    <h2>Module risk ranking</h2>
    <p class="hint">Risk = blocking×100 + high×40 + medium×10 + low×3 + suggestion×1 + open_todos×5</p>
    <table>
      <thead><tr>
        <th>Module</th><th>Risk</th><th>B</th><th>H</th><th>M</th><th>L</th><th>S</th><th>Todos</th><th>Heat</th>
      </tr></thead>
      <tbody>
        {''.join(risk_rows)}
      </tbody>
    </table>
  </section>

  <section class="stack">
    <div class="panel">
      <h2>Hot list</h2>
      <table>
        <thead><tr><th>Severity</th><th>Module</th><th>ID</th><th>Title</th></tr></thead>
        <tbody>{''.join(hot_rows)}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>Open todos</h2>
      <table>
        <thead><tr><th>Priority</th><th>Status</th><th>Module</th><th>ID</th><th>Title</th></tr></thead>
        <tbody>{''.join(todo_rows)}</tbody>
      </table>
    </div>
  </section>

  <footer>
    Also available as Markdown:
    <a href="./overview.md">overview.md</a> ·
    <a href="./findings.md">findings.md</a> ·
    <a href="./todos.md">todos.md</a> ·
    <a href="./stats.json">stats.json</a>
    · Regenerate with <code>pm dashboard</code> or <code>/pm-all</code>
  </footer>
</div>
</body>
</html>
"""


def write_dashboard(project_root: Path) -> Path:
    """Generate `.pm/dashboard/` from module findings/todos. Returns dashboard dir."""
    project_root = project_root.resolve()
    pm = project_root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"Missing .pm/ under {project_root}; run `pm init` first")

    findings, todos, scanned = collect(pm)
    stats = build_stats(findings, todos, scanned)
    out = pm / "dashboard"
    out.mkdir(parents=True, exist_ok=True)

    overview = render_overview(stats, findings, todos)
    (out / "overview.md").write_text(overview, encoding="utf-8")
    (out / "README.md").write_text(overview, encoding="utf-8")
    (out / "index.html").write_text(
        render_html(stats, findings, todos), encoding="utf-8"
    )
    (out / "findings.md").write_text(render_findings(findings), encoding="utf-8")
    (out / "todos.md").write_text(render_todos(todos), encoding="utf-8")
    (out / "stats.json").write_text(
        json.dumps(asdict(stats), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out
