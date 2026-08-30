"""Time-window audit export with redaction."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.audit import read_audit
from pm_manager_cli.journal import KIND_LABELS, load_notes
from pm_manager_cli.redact import contains_secret_residue, redact
from pm_manager_cli.reviews import load_reviews


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


def render_journal_export(notes: list, *, since_label: str, until_label: str) -> str:
    lines = [
        "## 开发记录",
        "",
        f"- 窗口: {since_label or '开始'} → {until_label or '现在'}",
        f"- 对话条数: {len(notes)}",
        "",
        "| 时间 | 场景 | 意图 | 文件 | 状态 |",
        "|------|------|------|------|------|",
    ]
    if not notes:
        lines.append("| — | — | （窗口内无对话） | — | — |")
    else:
        for note in notes:
            ts = str(getattr(note, "ts", "") or "").replace("|", " ")
            kind = KIND_LABELS.get(getattr(note, "kind", ""), getattr(note, "kind", ""))
            intent = str(getattr(note, "intent", "") or "").replace("|", " ")
            files = "、".join(getattr(note, "files", []) or []) or "—"
            status = str(getattr(note, "status", "") or "")
            lines.append(f"| {ts} | {kind} | {intent} | {files.replace('|', ' ')} | {status} |")
    lines.append("")
    return redact("\n".join(lines))


def _clip_md(path: Path, *, limit: int = 40) -> list[str]:
    if not path.is_file():
        return ["（无）"]
    try:
        rows = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ["（无法读取）"]
    return rows[:limit] + (["…"] if len(rows) > limit else [])


def render_bundle_export(project_root: Path, *, with_diagrams: bool = False) -> str:
    root = project_root.resolve()
    pm = root / ".pm"
    lines = [
        "## 现状快照",
        "",
    ]
    overview = pm / "state" / "overview.md"
    if overview.is_file():
        for line in overview.read_text(encoding="utf-8").splitlines():
            if line.startswith("## ") and "现状快照" not in line and line != "## 现状快照":
                if lines[-1] != "":
                    lines.append("")
                break
            if line.startswith("# "):
                continue
            lines.append(line)
    else:
        lines.append("（还没有 overview.md）")
        lines.append("")

    lines += ["## 评审", ""]
    rows = load_reviews(root)
    lines += [
        "| id | summary | reasoning | snippet | severity | disposition |",
        "|----|---------|-----------|---------|----------|-------------|",
    ]
    if not rows:
        lines.append("| — | （无评审行） | — | — | — | — |")
    else:
        for r in rows[:40]:
            lines.append(
                f"| {r.id} | {r.summary.replace('|', ' ')} | "
                f"{r.reasoning.replace('|', ' ')[:80]} | "
                f"{r.snippet.replace('|', ' ')[:60]} | {r.severity} | {r.disposition} |"
            )
    lines.append("")

    lines += ["## 单测缺口", ""]
    gap = pm / "state" / "test-gaps.md"
    if gap.is_file():
        lines.extend(_clip_md(gap, limit=30))
    else:
        lines.append("（还没有 test-gaps.md，运行 `pm tests`）")
    lines.append("")

    lines += ["## 幻觉防御", ""]
    guard = pm / "state" / "guard.md"
    if guard.is_file():
        lines.extend(_clip_md(guard, limit=30))
    else:
        lines.append("（还没有 guard.md，运行 `pm gate`）")
    lines.append("")

    lines += ["## 项目体检", ""]
    exam = pm / "state" / "checkup.md"
    if exam.is_file():
        lines.extend(_clip_md(exam, limit=36))
    else:
        lines.append("（还没有 checkup.md，运行 `pm checkup`）")
    lines.append("")

    lines += ["## 架构产物", ""]
    arch = pm / "architecture"
    if arch.is_dir():
        for p in sorted(arch.glob("*")):
            if p.suffix.lower() in {".md", ".mmd", ".json"} or p.name == "map.json":
                lines.append(f"- `{p.relative_to(root).as_posix()}`")
                if with_diagrams and p.suffix.lower() == ".mmd":
                    try:
                        body = p.read_text(encoding="utf-8")
                    except OSError:
                        body = ""
                    if body.strip():
                        lines.append("")
                        lines.append("```mermaid")
                        lines.append(body.strip())
                        lines.append("```")
                        lines.append("")
    else:
        lines.append("- （还没有 .pm/architecture/）")
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
    with_diagrams: bool = False,
) -> tuple[Path, int]:
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    since_dt = parse_bound(since)
    until_dt = parse_bound(until, end_of_day=True)
    rows = filter_audit_rows(read_audit(root), since=since_dt, until=until_dt)
    kept_notes = [
        n
        for n in load_notes(root)
        if _row_ts(n.as_dict()) is None
        or (
            (since_dt is None or _row_ts(n.as_dict()) >= since_dt)
            and (until_dt is None or _row_ts(n.as_dict()) <= until_dt)
        )
    ]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        from pm_manager_cli.guard import write_guard

        write_guard(root)
    except (OSError, FileNotFoundError):
        pass
    try:
        from pm_manager_cli.test_assist import write_test_gaps

        write_test_gaps(root)
    except (OSError, FileNotFoundError):
        pass
    body = (
        render_export(
            rows,
            since_label=since or "",
            until_label=until or "",
            generated_at=generated,
        )
        + render_journal_export(
            kept_notes,
            since_label=since or "",
            until_label=until or "",
        )
        + render_bundle_export(root, with_diagrams=with_diagrams)
    )
    dest = out if out is not None else default_export_path(root)
    dest = dest.resolve()
    if contains_secret_residue(body):
        if dest.is_file():
            dest.unlink(missing_ok=True)
        raise ValueError("导出仍含秘密原文，已中止（未写入文件）")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    if dest.is_file() and contains_secret_residue(dest.read_text(encoding="utf-8")):
        dest.unlink(missing_ok=True)
        raise ValueError("导出仍含秘密原文，已删除该文件")
    return dest, len(rows)
