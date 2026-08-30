"""Detect core project docs and refresh `.pm/state/doc-index.md` (no body generation)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CORE_DOCS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("DOC-agents", "AGENTS.md or agent.md", ("AGENTS.md", "agent.md")),
    (
        "DOC-prd",
        "prd / product spec",
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


@dataclass
class DocEntry:
    id: str
    expected: str
    status: str  # missing | present
    path: str


def _first_existing(root: Path, rels: tuple[str, ...]) -> Path | None:
    for rel in rels:
        p = root / rel
        if p.is_file():
            return p
    return None


def scan_core_docs(project_root: Path) -> list[DocEntry]:
    root = project_root.resolve()
    entries: list[DocEntry] = []
    for doc_id, expected, rels in CORE_DOCS:
        found = _first_existing(root, rels)
        entries.append(
            DocEntry(
                id=doc_id,
                expected=expected,
                status="present" if found else "missing",
                path=found.relative_to(root).as_posix() if found else "",
            )
        )
    return entries


def render_doc_index(entries: list[DocEntry]) -> str:
    lines = [
        "# Document index",
        "",
        "Core docs (closed set): `AGENTS.md` / `agent.md`, product PRD, design, API, deploy, trouble-shoot.",
        "",
        "| id | expected | status | path |",
        "|----|----------|--------|------|",
    ]
    for e in entries:
        lines.append(f"| {e.id} | {e.expected} | {e.status} | {e.path} |")
    lines += [
        "",
        "Status: `missing` | `present` | `possibly_stale`",
        "",
    ]
    return "\n".join(lines)


def write_doc_index(project_root: Path) -> tuple[Path, list[DocEntry]]:
    """Scan and write `.pm/state/doc-index.md`. Requires `.pm/`."""
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    entries = scan_core_docs(root)
    dest = pm / "state" / "doc-index.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_doc_index(entries), encoding="utf-8")
    return dest, entries


def missing_count(entries: list[DocEntry]) -> int:
    return sum(1 for e in entries if e.status == "missing")
