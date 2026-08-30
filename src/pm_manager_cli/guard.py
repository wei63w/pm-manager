"""Hallucination guard: qualify reviews, cheap logic-loss flags, commit gate."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_manager_cli.architecture import load_map
from pm_manager_cli.dashboard import hot_open_todos
from pm_manager_cli.redact import contains_secret_residue, redact
from pm_manager_cli.reviews import ReviewRow, is_qualified_row, load_reviews
from pm_manager_cli.rules_lib import match_rules

_EMPTY = frozenset({"", "—", "-", "待补", "n/a", "none", "tbd"})
_DEF_RE = re.compile(
    r"^\s*(?:async\s+def|def|function|class|func|fn|export\s+(?:async\s+)?function|"
    r"export\s+class|export\s+const|export\s+function)\s+(\w+)",
    re.IGNORECASE,
)
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_qualified(row: ReviewRow) -> bool:
    return is_qualified_row(row)


def qualify_reviews(project_root: Path) -> list[dict[str, str]]:
    """Return unqualified review rows (missing reasoning or snippet)."""
    bad: list[dict[str, str]] = []
    for row in load_reviews(project_root):
        if is_qualified(row):
            continue
        missing = []
        if (row.reasoning or "").strip().lower() in _EMPTY or len((row.reasoning or "").strip()) < 4:
            missing.append("reasoning")
        if (row.snippet or "").strip().lower() in _EMPTY or len((row.snippet or "").strip()) < 2:
            missing.append("snippet")
        bad.append(
            {
                "id": row.id,
                "summary": row.summary,
                "missing": "+".join(missing) or "reasoning/snippet",
            }
        )
    return bad


def _git_diff(root: Path, cached: bool = False) -> str:
    cmd = ["git", "-C", str(root), "diff"]
    if cached:
        cmd.append("--cached")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=8,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def _diff_paths(root: Path) -> list[str]:
    cmd = ["git", "-C", str(root), "diff", "--name-only", "HEAD"]
    cached = ["git", "-C", str(root), "diff", "--cached", "--name-only"]
    found: list[str] = []
    for args in (cmd, cached):
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            rel = line.strip().replace("\\", "/")
            if rel and rel not in found and not rel.startswith(".pm/"):
                found.append(rel)
    return found[:40]


def logic_diff_flags(project_root: Path) -> list[dict[str, str]]:
    """Heuristic: deleted defs without matching adds, or large delete hunks."""
    root = project_root.resolve()
    blob = _git_diff(root) + "\n" + _git_diff(root, cached=True)
    if not blob.strip():
        return []
    flags: list[dict[str, str]] = []
    current = ""
    removed: list[str] = []
    added: list[str] = []
    minus = 0
    plus = 0

    def flush() -> None:
        nonlocal removed, added, minus, plus
        if not current:
            removed, added, minus, plus = [], [], 0, 0
            return
        lost = [n for n in removed if n not in added]
        if lost:
            flags.append(
                {
                    "path": current,
                    "risk": "logic_loss",
                    "evidence": "删除了 " + "、".join(lost[:6]) + "，未见对应新增",
                }
            )
        if minus >= 12 and plus <= max(2, minus // 4):
            flags.append(
                {
                    "path": current,
                    "risk": "large_delete",
                    "evidence": f"删除 {minus} 行 / 新增 {plus} 行",
                }
            )
        removed, added, minus, plus = [], [], 0, 0

    for raw in blob.splitlines():
        if raw.startswith("+++ b/") or raw.startswith("--- a/"):
            continue
        if raw.startswith("diff --git "):
            flush()
            parts = raw.split(" b/", 1)
            current = parts[1].strip() if len(parts) == 2 else ""
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            plus += 1
            m = _DEF_RE.match(raw[1:])
            if m:
                added.append(m.group(1))
        elif raw.startswith("-") and not raw.startswith("---"):
            minus += 1
            m = _DEF_RE.match(raw[1:])
            if m:
                removed.append(m.group(1))
    flush()
    return flags[:20]


def risk_files_from_map(project_root: Path) -> list[dict[str, Any]]:
    nav = load_map(project_root) or {}
    rows = nav.get("risk_files") or []
    out: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict) and item.get("path"):
            out.append(item)
        elif isinstance(item, str):
            out.append({"path": item, "flags": [], "reasons": []})
    return out


def touched_risk_files(project_root: Path) -> list[dict[str, Any]]:
    changed = set(_diff_paths(project_root))
    hits: list[dict[str, Any]] = []
    for item in risk_files_from_map(project_root):
        path = str(item.get("path") or "").replace("\\", "/")
        if path and path in changed:
            hits.append(item)
    return hits


def write_guard(project_root: Path) -> Path:
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    bad = qualify_reviews(root)
    flags = logic_diff_flags(root)
    risks = touched_risk_files(root)
    lines = [
        "# 幻觉防御",
        "",
        f"> 更新: {_now()}",
        "> 缺推理/片段的评审不合格。逻辑丢失只做 diff 启发式，写不清标信息不足。",
        "",
        "## 不合格评审",
        "",
    ]
    if not bad:
        lines.append("- 无")
    else:
        for row in bad:
            lines.append(f"- `{row['id']}` {row['summary']}（缺 {row['missing']}）")
    lines += ["", "## 逻辑丢失嫌疑", ""]
    if not flags:
        lines.append("- 无（或没有可解析的 diff）")
    else:
        for flag in flags:
            lines.append(f"- `{flag['path']}` {flag['risk']}：{flag['evidence']}")
    lines += ["", "## 本轮碰到的高危文件", ""]
    if not risks:
        lines.append("- 无")
    else:
        for item in risks:
            flags_s = ",".join(item.get("flags") or []) or "—"
            reasons = "；".join(item.get("reasons") or []) or "信息不足"
            lines.append(f"- `{item['path']}` [{flags_s}] {reasons}")
    lines.append("")
    dest = pm / "state" / "guard.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(redact("\n".join(lines)), encoding="utf-8")
    return dest


@dataclass
class GateResult:
    ok: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    guard_path: Path | None = None
    test_gaps_path: Path | None = None
    no_diff: bool = False


def _review_mentions(path: str, rows: list[ReviewRow]) -> bool:
    needle = path.lower()
    name = Path(path).name.lower()
    for row in rows:
        blob = f"{row.summary} {row.snippet} {row.reasoning}".lower()
        if needle in blob or name in blob:
            return True
    return False


def run_gate(project_root: Path) -> GateResult:
    """Read-only pre-commit checks. Fail on P0 / unqualified reviews / unreviewed risk files."""
    from pm_manager_cli.docs_index import scan_core_docs
    from pm_manager_cli.test_assist import write_test_gaps

    root = project_root.resolve()
    if not (root / ".pm").is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    guard_path = write_guard(root)
    try:
        gaps_path, gaps = write_test_gaps(root)
    except OSError:
        gaps_path, gaps = None, []

    failures: list[str] = []
    warnings: list[str] = []
    changed = _diff_paths(root)
    blob = _git_diff(root) + "\n" + _git_diff(root, cached=True)
    no_diff = not changed and not blob.strip()
    if no_diff:
        return GateResult(
            ok=True,
            failures=[],
            warnings=["没有可评的变更"],
            guard_path=guard_path,
            test_gaps_path=gaps_path,
            no_diff=True,
        )

    bad = qualify_reviews(root)
    if bad:
        failures.append(f"{len(bad)} 条评审缺推理或片段")
    todos = hot_open_todos(root / ".pm")
    p0 = [t for t in todos if str(t.priority).lower() in {"p0", "blocking", "阻断"}]
    if p0:
        failures.append(f"{len(p0)} 条未关闭阻断/P0 待办")
    reviews = load_reviews(root)
    for item in touched_risk_files(root):
        path = str(item.get("path") or "")
        if path and not _review_mentions(path, reviews):
            failures.append(f"高危文件 `{path}` 在本次变更中，尚无带推理的评审提及")
    changed_gaps = [g for g in gaps if g.get("changed")]
    if changed_gaps:
        warnings.append(f"{len(changed_gaps)} 个变更文件未见配套测试")
    flags = logic_diff_flags(root)
    if flags:
        warnings.append(f"{len(flags)} 处逻辑丢失/大段删除嫌疑")

    if contains_secret_residue(blob):
        failures.append("本次 diff 含秘密原文形态")

    source_changed = False
    for rel in changed:
        path = root / rel
        if rel.endswith(".py") and path.is_file():
            try:
                import ast

                ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError as exc:
                failures.append(f"语法错误 `{rel}`: {exc.msg}")
            except OSError:
                warnings.append(f"无法读取 `{rel}` 做语法检查")
        elif path.is_file() and path.suffix.lower() in {".ts", ".js", ".go", ".rs", ".java"}:
            warnings.append(f"`{rel}` 未做语法解析（非 Python）")
        if path.suffix.lower() in {".py", ".ts", ".js", ".go", ".rs", ".java"}:
            source_changed = True
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if contains_secret_residue(text):
                failures.append(f"`{rel}` 含秘密原文形态")
            for m in re.finditer(r"^\s*(?:def|class)\s+([a-z])\b", text, re.M):
                warnings.append(f"`{rel}` 命名过短: {m.group(1)}")
                break
            for rule in match_rules(root, path=rel, blob=text[:4000]):
                msg = f"命中启用规范 {rule.id}"
                if str(rule.severity).upper() == "P0":
                    failures.append(msg)
                else:
                    warnings.append(msg)

    if source_changed:
        try:
            stale = [e for e in scan_core_docs(root) if e.status == "possibly_stale"]
        except Exception:
            stale = []
        if stale:
            warnings.append(
                "核心文档可能过期: " + "、".join(e.id for e in stale[:4])
            )

    return GateResult(
        ok=not failures,
        failures=failures,
        warnings=warnings,
        guard_path=guard_path,
        test_gaps_path=gaps_path,
        no_diff=False,
    )
