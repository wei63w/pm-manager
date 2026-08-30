"""Detect core project docs and refresh `.pm/state/doc-index.md` (optional drafts)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CORE_DOCS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("DOC-agents", "AGENTS.md 或 agent.md", ("AGENTS.md", "agent.md")),
    (
        "DOC-prd",
        "prd / 产品说明",
        ("docs/prd.md", "docs/PRD.md", "PRD.md", "docs/requirements.md"),
    ),
    ("DOC-design", "design.md", ("docs/design.md", "design.md")),
    ("DOC-api", "api.md", ("docs/api.md", "api.md")),
    ("DOC-deploy", "deploy.md", ("docs/deploy.md", "deploy.md")),
    (
        "DOC-trouble",
        "trouble-shoot.md",
        ("docs/trouble-shoot.md", "docs/troubleshoot.md", "trouble-shoot.md"),
    ),
)

_SOURCE_SUFFIXES = {".py", ".java", ".kt", ".ts", ".js", ".go", ".rs", ".vue"}

DRAFT_HINTS = {
    "DOC-agents": "给编码助手的仓库说明：能改什么、先读哪些文件。",
    "DOC-prd": "产品要解决的问题、用户、目标与非目标。未确认不当基线。",
    "DOC-design": "模块如何协作、关键数据流与约束。",
    "DOC-api": "对外接口、鉴权与错误约定。",
    "DOC-deploy": "如何构建、配置与发布。",
    "DOC-trouble": "常见故障、日志位置与排查步骤。",
}


@dataclass
class DocEntry:
    id: str
    expected: str
    status: str  # missing | present | possibly_stale | extra
    path: str
    kind: str = "core"  # core | extra


@dataclass
class DocIndex:
    generated_at: str
    core: list[DocEntry] = field(default_factory=list)
    extra: list[DocEntry] = field(default_factory=list)


def _first_existing(root: Path, rels: tuple[str, ...]) -> Path | None:
    for rel in rels:
        p = root / rel
        if p.is_file():
            return p
    return None


def _source_changed_mtimes(project_root: Path) -> list[float]:
    """mtime of business source files listed in map.json changed_paths."""
    map_path = project_root / ".pm" / "architecture" / "map.json"
    if not map_path.is_file():
        return []
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    times: list[float] = []
    for rel in data.get("changed_paths") or []:
        if not isinstance(rel, str):
            continue
        if Path(rel).suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        p = project_root / rel
        if p.is_file():
            try:
                times.append(p.stat().st_mtime)
            except OSError:
                continue
    return times


def _is_stale(doc: Path, source_mtimes: list[float]) -> bool:
    if not source_mtimes:
        return False
    try:
        return doc.stat().st_mtime < max(source_mtimes)
    except OSError:
        return False


def _extra_docs(root: Path, claimed: set[str]) -> list[DocEntry]:
    extras: list[DocEntry] = []
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return extras
    for p in sorted(docs_dir.rglob("*.md")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel in claimed:
            continue
        extras.append(
            DocEntry(
                id=f"EXTRA-{len(extras)+1:03d}",
                expected=p.name,
                status="present",
                path=rel,
                kind="extra",
            )
        )
        if len(extras) >= 40:
            break
    return extras


def _core_table(project_root: Path) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    try:
        from pm_manager_cli.config_profile import read_required_doc_ids

        wanted = read_required_doc_ids(project_root)
    except Exception:
        wanted = None
    if not wanted:
        return CORE_DOCS
    allowed = {row[0] for row in CORE_DOCS}
    picked = [row for row in CORE_DOCS if row[0] in wanted and row[0] in allowed]
    return tuple(picked) or CORE_DOCS


def scan_core_docs(project_root: Path) -> list[DocEntry]:
    root = project_root.resolve()
    source_mtimes = _source_changed_mtimes(root)
    entries: list[DocEntry] = []
    for doc_id, expected, rels in _core_table(root):
        found = _first_existing(root, rels)
        if not found:
            entries.append(
                DocEntry(id=doc_id, expected=expected, status="missing", path="")
            )
            continue
        status = "possibly_stale" if _is_stale(found, source_mtimes) else "present"
        entries.append(
            DocEntry(
                id=doc_id,
                expected=expected,
                status=status,
                path=found.relative_to(root).as_posix(),
            )
        )
    return entries


def scan_doc_index(project_root: Path) -> DocIndex:
    root = project_root.resolve()
    core = scan_core_docs(root)
    claimed = {e.path for e in core if e.path}
    extra = _extra_docs(root, claimed)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return DocIndex(generated_at=now, core=core, extra=extra)


def render_doc_index(index: DocIndex | list[DocEntry]) -> str:
    if isinstance(index, list):
        index = DocIndex(generated_at="", core=index, extra=[])
    lines = [
        "# 文档索引",
        "",
        f"> 生成: {index.generated_at or '—'}",
        "",
        "核心说明（封闭集合）：`AGENTS.md` / `agent.md`、产品 PRD、设计、接口、部署、排障。",
        "",
        "| id | expected | status | path |",
        "|----|----------|--------|------|",
    ]
    for e in index.core:
        lines.append(f"| {e.id} | {e.expected} | {e.status} | {e.path} |")
    lines += [
        "",
        "状态: `missing` | `present` | `possibly_stale`",
        "",
        "缺失时：用户自备，或 `pm docs --draft` 在 `.pm/docs/drafts/` 起草（确认后才写入正式路径）。",
        "",
    ]
    if index.extra:
        lines += [
            "## 其他文档（只索引，不算核心缺失）",
            "",
            "| id | path |",
            "|----|------|",
        ]
        for e in index.extra:
            lines.append(f"| {e.id} | {e.path} |")
        lines.append("")
    return "\n".join(lines)


def write_doc_index(project_root: Path) -> tuple[Path, list[DocEntry]]:
    """Scan and write `.pm/state/doc-index.md` + `.json`. Requires `.pm/`."""
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    index = scan_doc_index(root)
    dest = pm / "state" / "doc-index.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_doc_index(index), encoding="utf-8")
    payload = {
        "generated_at": index.generated_at,
        "core": [asdict(e) for e in index.core],
        "extra": [asdict(e) for e in index.extra],
    }
    (pm / "state" / "doc-index.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return dest, index.core


def write_doc_drafts(project_root: Path, entries: list[DocEntry] | None = None) -> list[Path]:
    """Write editable skeletons under `.pm/docs/drafts/` for missing core docs only."""
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    targets = entries if entries is not None else scan_core_docs(root)
    dest_dir = pm / "docs" / "drafts"
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for e in targets:
        if e.status != "missing":
            continue
        path = dest_dir / f"{e.id}.md"
        hint = DRAFT_HINTS.get(e.id, e.expected)
        body = (
            f"# {e.id} 草稿 — {e.expected}\n\n"
            f"> 生成: {now}  \n"
            f"> 仅存在于 `.pm/docs/drafts/`。未确认不得写入仓库正式文档。\n\n"
            f"## 用途\n\n{hint}\n\n"
            "## 观察到的入口\n\n"
            "_根据 `pm map` / README 填写路径。信息不足则保持本句。_\n\n"
            "## 待补\n\n"
            "- \n"
        )
        path.write_text(body, encoding="utf-8")
        written.append(path)
    return written


def missing_count(entries: list[DocEntry]) -> int:
    return sum(1 for e in entries if e.status == "missing")


def stale_count(entries: list[DocEntry]) -> int:
    return sum(1 for e in entries if e.status == "possibly_stale")
