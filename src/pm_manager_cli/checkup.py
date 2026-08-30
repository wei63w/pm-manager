"""On-demand five-dimension project checkup. No cron."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_manager_cli.architecture import SKIP_DIRS, load_map
from pm_manager_cli.docs_index import scan_core_docs
from pm_manager_cli.redact import contains_secret_residue, redact
from pm_manager_cli.rules_lib import match_rules

_SOURCE = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".vue"}
_EVAL = re.compile(r"\beval\s*\(|\bpickle\.loads\s*\(|shell\s*=\s*True")
_TODO = re.compile(r"\b(TODO|FIXME|XXX)\b")
_STUB = re.compile(r"NotImplementedError|\braise NotImplemented")
_MAX_FILES = 80
_MAX_BYTES = 512 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iter_sources(root: Path, module: str | None) -> list[Path]:
    nav = load_map(root) or {}
    wanted: list[Path] = []
    seen: set[str] = set()

    def add(rel: str) -> None:
        rel = rel.replace("\\", "/")
        if not rel or rel in seen or rel.startswith(".pm/"):
            return
        if Path(rel).suffix.lower() not in _SOURCE:
            return
        if any(p in SKIP_DIRS for p in rel.split("/")):
            return
        if module and module not in rel.split("/") and module not in rel:
            return
        path = root / rel
        if path.is_file():
            seen.add(rel)
            wanted.append(path)

    for kf in nav.get("key_files") or []:
        add(kf.get("path") if isinstance(kf, dict) else str(kf))
    for rf in nav.get("risk_files") or []:
        add(rf.get("path") if isinstance(rf, dict) else str(rf))
    for cap in nav.get("capabilities") or []:
        if isinstance(cap, dict):
            for f in cap.get("files") or []:
                add(str(f))
    roots = [root / "src"] if (root / "src").is_dir() else [root]
    if module and (root / module).is_dir():
        roots = [root / module]
    for base in roots:
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            try:
                add(p.relative_to(root).as_posix())
            except ValueError:
                continue
            if len(wanted) >= _MAX_FILES:
                return wanted
    return wanted[:_MAX_FILES]


def run_checkup(project_root: Path, *, module: str | None = None) -> dict[str, Any]:
    root = project_root.resolve()
    if not (root / ".pm").is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    findings: list[dict[str, str]] = []

    def add(dim: str, sev: str, title: str, evidence: str, path: str = "") -> None:
        findings.append(
            {
                "dimension": dim,
                "severity": sev,
                "title": title,
                "evidence": redact(evidence)[:160],
                "path": path,
            }
        )

    nav = load_map(root) or {}
    for cap in nav.get("capabilities") or []:
        if not isinstance(cap, dict):
            continue
        files = [f for f in (cap.get("files") or []) if f]
        if cap.get("name") and not files:
            add("功能", "P2", f"能力「{cap['name']}」无对应文件", "信息不足", "")

    for path in _iter_sources(root, module):
        try:
            if path.stat().st_size > _MAX_BYTES:
                add("质量", "P2", "文件过大未全文扫描", str(path.stat().st_size), path.relative_to(root).as_posix())
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            add("质量", "P2", "单文件读取失败", str(exc), path.name)
            continue
        rel = path.relative_to(root).as_posix()
        if contains_secret_residue(text):
            add("安全", "P0", "疑似秘密原文", "匹配密钥/私钥形态", rel)
        if _EVAL.search(text):
            add("安全", "P0", "危险调用", "eval / pickle.loads / shell=True", rel)
        if _STUB.search(text):
            add("功能", "P1", "未实现逻辑", "NotImplementedError", rel)
        if _TODO.search(text):
            add("完成度", "P2", "TODO/FIXME 未收尾", "标记仍在源码中", rel)
        lines = text.splitlines()
        if len(lines) >= 400:
            add("质量", "P2", "臃肿文件", f"{len(lines)} 行", rel)
        comments = sum(1 for ln in lines[:80] if ln.strip().startswith(("#", "//", "/*", "*")))
        codeish = sum(1 for ln in lines[:80] if ln.strip() and not ln.strip().startswith(("#", "//")))
        if codeish >= 12 and comments < 2:
            add("质量", "P2", "抽样几乎无注释", "前 80 行", rel)
        for rule in match_rules(root, path=rel, blob=text[:3000]):
            sev = rule.severity if str(rule.severity).upper() in {"P0", "P1", "P2"} else "P2"
            add("质量", sev, f"命中规范 {rule.id}", rule.text, rel)

    docs = scan_core_docs(root)
    stale = [e for e in docs if e.status == "possibly_stale"]
    missing = [e for e in docs if e.status == "missing"]
    for e in stale:
        add("文档", "P1", f"{e.id} 可能过期", e.path or e.expected, e.path)
    if missing:
        add("文档", "P2", f"缺失 {len(missing)} 份核心文档", "、".join(x.id for x in missing[:6]), "")

    report = {
        "generated_at": _now(),
        "module": module or "",
        "counts": {
            "P0": sum(1 for f in findings if f["severity"] == "P0"),
            "P1": sum(1 for f in findings if f["severity"] == "P1"),
            "P2": sum(1 for f in findings if f["severity"] == "P2"),
        },
        "findings": findings,
    }
    state = root / ".pm" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "checkup.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# 项目体检",
        "",
        f"> 更新: {report['generated_at']}  模块: {module or '全部（抽样）'}",
        "> 按需扫描，无定时器。P0 打断；P1/P2 只进报告。",
        "",
        f"- P0: {report['counts']['P0']}  P1: {report['counts']['P1']}  P2: {report['counts']['P2']}",
        "",
    ]
    for band in ("P0", "P1", "P2"):
        group = [f for f in findings if f["severity"] == band]
        if not group:
            continue
        lines.append(f"## {band}")
        lines.append("")
        for f in group:
            loc = f"`{f['path']}`" if f["path"] else "—"
            lines.append(f"- [{f['dimension']}] {f['title']} — {loc} — {f['evidence']}")
        lines.append("")
    if not findings:
        lines.append("抽样范围内未发现启发式问题。")
        lines.append("")
    (state / "checkup.md").write_text(redact("\n".join(lines)), encoding="utf-8")
    return report


def load_checkup(project_root: Path) -> dict[str, Any] | None:
    path = project_root.resolve() / ".pm" / "state" / "checkup.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None
