"""Time-window audit export with redaction."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.audit import read_audit
from pm_manager_cli.redact import redact


def parse_bound(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        dt = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt
    iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError(f"无法解析时间: {raw}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _row_ts(row: dict) -> datetime | None:
    raw = str(row.get("ts") or "").strip()
    if not raw:
        return None
    try:
        return parse_bound(raw)
    except ValueError:
        return None


def filter_audit_rows(
    rows: list[dict],
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        ts = _row_ts(row)
        if ts is None:
            out.append(row)
            continue
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        out.append(row)
    return out


def render_export(
    rows: list[dict],
    *,
    since_label: str,
    until_label: str,
    generated_at: str,
) -> str:
    lines = [
        "# 治理审计导出",
        "",
        f"- 窗口: {since_label or '开始'} → {until_label or '现在'}",
        f"- 生成: {generated_at}",
        f"- 条数: {len(rows)}",
        "",
        "| 时间 | 命令 | 输入摘要 | 输出摘要 |",
        "|------|------|----------|----------|",
    ]
    if not rows:
        lines.append("| — | — | （窗口内无记录） | — |")
    else:
        for row in rows:
            ts = str(row.get("ts") or "").replace("|", " ")
            cmd = str(row.get("command") or "").replace("|", " ")
            inn = str(row.get("input_summary") or "").replace("|", " ")
            out = str(row.get("output_summary") or "").replace("|", " ")
            lines.append(f"| {ts} | {cmd} | {inn} | {out} |")
    lines.append("")
    return redact("\n".join(lines))


def default_export_path(project_root: Path, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d")
    return project_root.resolve() / ".pm" / "exports" / f"pm-export-{stamp}.md"


def write_export(
    project_root: Path,
    *,
    since: str | None = None,
    until: str | None = None,
    out: Path | None = None,
) -> tuple[Path, int]:
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    since_dt = parse_bound(since)
    until_dt = parse_bound(until, end_of_day=True)
    rows = filter_audit_rows(read_audit(root), since=since_dt, until=until_dt)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = render_export(
        rows,
        since_label=since or "",
        until_label=until or "",
        generated_at=generated,
    )
    dest = out if out is not None else default_export_path(root)
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    return dest, len(rows)
