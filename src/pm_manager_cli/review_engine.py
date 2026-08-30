"""Deterministic diff review drafts, cross-check, and annotation stubs."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.guard import (
    _DEF_RE,
    _diff_paths,
    _git_diff,
    is_qualified,
    logic_diff_flags,
    touched_risk_files,
)
from pm_manager_cli.redact import contains_secret_residue, redact
from pm_manager_cli.reviews import (
    ReviewRow,
    append_reviews,
    get_review,
    is_qualified_row,
    latest_unset,
    load_reviews,
    set_disposition,
    write_reviews,
)
from pm_manager_cli.rules_lib import add_rule, match_rules

_EVAL = re.compile(r"\beval\s*\(|\bpickle\.loads\s*\(|shell\s*=\s*True")
_TODO = re.compile(r"\b(TODO|FIXME|XXX)\b")
_STUB = re.compile(r"NotImplementedError|\braise NotImplemented|\bpass\s*$")
_NAME = re.compile(r"^(?:def|class)\s+([a-z])\b")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def collect_diff(root: Path) -> str:
    return (_git_diff(root) + "\n" + _git_diff(root, cached=True)).strip()


def parse_diff_files(blob: str) -> list[dict]:
    """[{path, added: [(line_no, text)], new_defs: []}]"""
    files: list[dict] = []
    current = ""
    added: list[tuple[int, str]] = []
    new_line = 0
    defs: list[str] = []

    def flush() -> None:
        nonlocal current, added, defs
        if current:
            files.append({"path": current, "added": added, "defs": defs})
        added, defs = [], []

    for raw in blob.splitlines():
        if raw.startswith("diff --git "):
            flush()
            parts = raw.split(" b/", 1)
            current = parts[1].strip() if len(parts) == 2 else ""
            new_line = 0
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            text = raw[1:]
            added.append((new_line, text))
            dm = _DEF_RE.match(text)
            if dm:
                defs.append(dm.group(1))
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            pass
        elif not raw.startswith("\\"):
            new_line += 1
    flush()
    return [f for f in files if f["path"] and not str(f["path"]).startswith(".pm/")]


def _finding(
    *,
    summary: str,
    reasoning: str,
    snippet: str,
    severity: str,
    path: str,
    line: str,
    dimension: str,
    cross: str = "unset",
) -> ReviewRow:
    return ReviewRow(
        id="",
        summary=redact(summary)[:80],
        reasoning=redact(reasoning)[:200],
        snippet=redact(snippet)[:80],
        severity=severity,
        disposition="unset",
        file=path,
        line=str(line or "—"),
        dimension=dimension,
        cross=cross,
    )


def heuristic_findings(root: Path, blob: str) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    if not blob.strip():
        return rows
    files = parse_diff_files(blob)
    for item in files:
        path = item["path"]
        added_txt = "\n".join(t for _, t in item["added"])
        if contains_secret_residue(added_txt):
            snip = next((t for _, t in item["added"] if contains_secret_residue(t)), "secret")
            line = next((n for n, t in item["added"] if contains_secret_residue(t)), "")
            rows.append(
                _finding(
                    summary="变更中疑似秘密原文",
                    reasoning="新增行匹配已知密钥/私钥形态，提交前必须脱敏或移出仓库。",
                    snippet=snip.strip()[:80],
                    severity="P0",
                    path=path,
                    line=str(line),
                    dimension="security",
                )
            )
        for n, t in item["added"]:
            if _EVAL.search(t):
                rows.append(
                    _finding(
                        summary="危险调用（eval/pickle/shell）",
                        reasoning="新增行含 eval、pickle.loads 或 shell=True，存在注入或任意代码执行风险。",
                        snippet=t.strip()[:80],
                        severity="P0",
                        path=path,
                        line=str(n),
                        dimension="security",
                    )
                )
                break
        for n, t in item["added"]:
            if _TODO.search(t):
                rows.append(
                    _finding(
                        summary="未收尾标记",
                        reasoning="新增 TODO/FIXME/XXX，完成度未闭合。",
                        snippet=t.strip()[:80],
                        severity="P2",
                        path=path,
                        line=str(n),
                        dimension="complete",
                    )
                )
                break
        for n, t in item["added"]:
            if _STUB.search(t):
                rows.append(
                    _finding(
                        summary="未实现桩",
                        reasoning="新增 NotImplementedError 或空 pass，功能完整性不足。",
                        snippet=t.strip()[:80],
                        severity="P1",
                        path=path,
                        line=str(n),
                        dimension="complete",
                    )
                )
                break
        for n, t in item["added"]:
            m = _NAME.match(t.strip())
            if m:
                rows.append(
                    _finding(
                        summary="命名过短",
                        reasoning=f"新增符号 `{m.group(1)}` 为单字母，可读性差，后续评审难引用。",
                        snippet=t.strip()[:80],
                        severity="P2",
                        path=path,
                        line=str(n),
                        dimension="quality",
                    )
                )
                break
        for rule in match_rules(root, path=path, blob=added_txt):
            snip = item["added"][0][1].strip() if item["added"] else path
            line = item["added"][0][0] if item["added"] else ""
            rows.append(
                _finding(
                    summary=f"命中启用规范 {rule.id}",
                    reasoning=f"启用规则「{rule.text}」与本文件/新增行匹配，需按规范处理。",
                    snippet=snip[:80],
                    severity=rule.severity or "P1",
                    path=path,
                    line=str(line),
                    dimension="quality",
                )
            )
    for flag in logic_diff_flags(root):
        rows.append(
            _finding(
                summary="逻辑丢失或大段删除",
                reasoning=flag["evidence"] + "。须对照旧行为，禁止无证据判定通过。",
                snippet=flag["path"],
                severity="P1",
                path=flag["path"],
                line="—",
                dimension="logic",
            )
        )
    for risk in touched_risk_files(root):
        path = str(risk.get("path") or "")
        flags = ",".join(risk.get("flags") or []) or "高危"
        rows.append(
            _finding(
                summary="本轮改动高危文件",
                reasoning=f"地图将 `{path}` 标为 {flags}，必须加强评审并给出推理与片段。",
                snippet=path,
                severity="P0",
                path=path,
                line="—",
                dimension="security",
            )
        )
    return [r for r in rows if is_qualified_row(r)]


def write_review_draft(root: Path, rows: list[ReviewRow], *, title: str = "评审草稿") -> Path:
    dest = root / ".pm" / "state" / "review-draft.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        f"> 更新: {_now()}",
        "> 仅含带推理与片段的合格行。无 diff 不编造。",
        "",
    ]
    if not rows:
        lines.append("没有可评的变更。")
        lines.append("")
    else:
        for r in rows:
            lines += [
                f"## {r.id or 'REV-?'} [{r.severity}] {r.summary}",
                "",
                f"- 维度: {r.dimension or '—'} · 交叉: {r.cross}",
                f"- 位置: `{r.file}`:{r.line}",
                f"- 推理: {r.reasoning}",
                f"- 片段: `{r.snippet}`",
                "",
            ]
    dest.write_text(redact("\n".join(lines)), encoding="utf-8")
    return dest


def run_review(project_root: Path) -> tuple[list[ReviewRow], Path, bool]:
    """Draft findings from diff. Returns (added rows, draft path, had_diff)."""
    root = project_root.resolve()
    if not (root / ".pm").is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    blob = collect_diff(root)
    if not blob.strip() and not _diff_paths(root):
        dest = write_review_draft(root, [], title="评审草稿")
        return [], dest, False
    findings = heuristic_findings(root, blob)
    added = append_reviews(root, findings)
    dest = write_review_draft(root, added or findings)
    return added, dest, True


def snippet_key(row: ReviewRow) -> str:
    return re.sub(r"\s+", " ", f"{row.file}|{row.snippet}").strip().lower()


def run_cross_review(project_root: Path) -> tuple[list[ReviewRow], Path]:
    """Second pass: security vs quality/complete/docs. No duplicate new snippets."""
    root = project_root.resolve()
    existing = load_reviews(root)
    seen = {snippet_key(r) for r in existing if r.snippet}
    blob = collect_diff(root)
    second: list[ReviewRow] = []
    # Mark existing: unqualified → reject; others with same snippet stay agree
    updated = False
    for row in existing:
        if not is_qualified_row(row) and row.cross != "reject":
            row.cross = "reject"
            updated = True
        elif is_qualified_row(row) and row.cross == "unset":
            row.cross = "agree"
            updated = True
    if updated:
        write_reviews(root, existing)

    files = parse_diff_files(blob)
    for item in files:
        path = item["path"]
        for n, t in item["added"]:
            if _EVAL.search(t) or contains_secret_residue(t):
                cand = _finding(
                    summary="交叉复核：安全风险",
                    reasoning="第二遍安全清单命中危险调用或秘密形态，初评若已覆盖则不应再标 new。",
                    snippet=t.strip()[:80],
                    severity="P0",
                    path=path,
                    line=str(n),
                    dimension="security",
                    cross="new",
                )
                if snippet_key(cand) not in seen:
                    second.append(cand)
                    seen.add(snippet_key(cand))
            if _STUB.search(t) or _TODO.search(t):
                cand = _finding(
                    summary="交叉复核：完成度",
                    reasoning="第二遍完成度清单命中桩或 TODO，与初评质量维分开记录。",
                    snippet=t.strip()[:80],
                    severity="P2",
                    path=path,
                    line=str(n),
                    dimension="complete",
                    cross="new",
                )
                if snippet_key(cand) not in seen:
                    second.append(cand)
                    seen.add(snippet_key(cand))

    added = append_reviews(root, second)
    dest = root / ".pm" / "state" / "cross-review.md"
    lines = [
        "# 交叉复核",
        "",
        f"> 更新: {_now()}",
        "> 第二遍策略：安全 vs 完成度/质量。同一 snippet 不得再标 new。",
        "",
        f"- 新发现: {len(added)}",
        f"- 初评同意/驳回已写回 reviews.md 的 cross 列",
        "",
    ]
    for r in added:
        lines.append(f"- `{r.id}` {r.summary} `{r.snippet}`")
    if not added:
        lines.append("- 无新发现（或与初评片段重复）")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(redact("\n".join(lines) + "\n"), encoding="utf-8")
    return added, dest


def dispose_review(project_root: Path, action: str, rid: str | None) -> ReviewRow:
    root = project_root.resolve()
    act = action.strip().lower()
    aliases = {"later": "later", "deferred": "later", "false_positive": "false_positive"}
    if act not in {"confirm", "false_positive", "later"}:
        raise ValueError("处置必须是 confirm | false_positive | later")
    if not rid:
        latest = latest_unset(root)
        if latest is None:
            raise FileNotFoundError("没有待处置评审")
        rid = latest.id
    row = get_review(root, rid)
    if row is None:
        raise FileNotFoundError(f"没有评审 {rid}")
    if act == "confirm":
        if not is_qualified_row(row):
            raise ValueError(f"{row.id} 缺推理或片段，不能沉淀规范")
        row = set_disposition(root, row.id, "confirmed")
        add_rule(
            root,
            f"{row.summary} — {row.reasoning}",
            source_finding=row.id,
            severity=row.severity or "P2",
        )
        return row
    disp = aliases.get(act, act)
    return set_disposition(root, row.id, disp)


def write_annotation(project_root: Path, rid: str) -> Path:
    root = project_root.resolve()
    row = get_review(root, rid)
    if row is None:
        raise FileNotFoundError(f"没有评审 {rid}")
    dest = root / ".pm" / "reviews" / "annotations" / f"{row.id}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# 回填草稿 {row.id}\n\n"
        f"> 仅存在于 `.pm/reviews/annotations/`。未确认不得写入业务源码。\n\n"
        f"- 文件: `{row.file}`\n"
        f"- 行: {row.line}\n"
        f"- 严重: {row.severity}\n"
        f"- 处置建议: confirm / false_positive / later\n\n"
        f"## 推理\n\n{row.reasoning}\n\n"
        f"## 片段\n\n```\n{row.snippet}\n```\n\n"
        f"## 可粘贴评论\n\n"
        f"{row.summary}（{row.id}）: {row.reasoning}\n"
    )
    dest.write_text(redact(body), encoding="utf-8")
    return dest
