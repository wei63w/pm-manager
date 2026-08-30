"""Parse and write `.pm/engineering/reviews.md` disposition table."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PENDING = frozenset({"", "unset", "—", "-", "deferred", "later"})
PLACEHOLDER_IDS = frozenset({"", "—", "-", "id"})
_EMPTY = frozenset({"", "—", "-", "待补", "n/a", "none", "tbd"})

_TABLE_HEADER = (
    "| id | summary | reasoning | snippet | severity | disposition "
    "| file | line | dimension | cross |"
)
_TABLE_SEP = (
    "|----|---------|-----------|---------|----------|-------------|"
    "------|------|-----------|-------|"
)


@dataclass
class ReviewRow:
    id: str
    summary: str
    reasoning: str
    snippet: str
    severity: str
    disposition: str
    file: str = ""
    line: str = ""
    dimension: str = ""
    cross: str = "unset"


def reviews_path(project_root: Path) -> Path:
    return project_root.resolve() / ".pm" / "engineering" / "reviews.md"


def is_qualified_row(row: ReviewRow) -> bool:
    reasoning = (row.reasoning or "").strip()
    snippet = (row.snippet or "").strip()
    if reasoning.lower() in _EMPTY or snippet.lower() in _EMPTY:
        return False
    return len(reasoning) >= 4 and len(snippet) >= 2


def parse_reviews(text: str) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 6:
            continue
        rid = cells[0]
        if rid.lower() in {"id"} or set(rid) <= {"-", ":"}:
            continue
        if rid in PLACEHOLDER_IDS:
            continue
        extra = cells[6:] + [""] * 4
        rows.append(
            ReviewRow(
                id=rid,
                summary=cells[1],
                reasoning=cells[2],
                snippet=cells[3],
                severity=cells[4],
                disposition=cells[5].lower(),
                file=extra[0],
                line=extra[1],
                dimension=extra[2],
                cross=(extra[3] or "unset").lower(),
            )
        )
    return rows


def load_reviews(project_root: Path) -> list[ReviewRow]:
    path = reviews_path(project_root)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return parse_reviews(text)


def pending_reviews(project_root: Path) -> list[ReviewRow]:
    return [r for r in load_reviews(project_root) if r.disposition in PENDING]


def pending_review_count(project_root: Path) -> int:
    return len(pending_reviews(project_root))


def next_review_id(rows: list[ReviewRow]) -> str:
    n = 0
    for row in rows:
        m = re.fullmatch(r"REV-(\d+)", row.id, flags=re.I)
        if m:
            n = max(n, int(m.group(1)))
    return f"REV-{n + 1:03d}"


def _esc(text: str) -> str:
    return (text or "").replace("|", " ").replace("\n", " ").strip()


def render_reviews(rows: list[ReviewRow]) -> str:
    lines = [
        "# 评审记录",
        "",
        "每条**合格**发现必须包含：摘要、推理、引用片段、严重级别。",
        "缺推理或片段 = 不合格，不得写入规范库。",
        "",
        _TABLE_HEADER,
        _TABLE_SEP,
    ]
    if not rows:
        lines.append("| — | — | — | — | P0/P1/P2 | unset | — | — | — | unset |")
    else:
        for r in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _esc(r.id),
                        _esc(r.summary),
                        _esc(r.reasoning),
                        _esc(r.snippet)[:120],
                        _esc(r.severity) or "P2",
                        _esc(r.disposition) or "unset",
                        _esc(r.file) or "—",
                        _esc(r.line) or "—",
                        _esc(r.dimension) or "—",
                        _esc(r.cross) or "unset",
                    ]
                )
                + " |"
            )
    lines += [
        "",
        "处置：",
        "",
        "- `confirmed` → 写入 `rules.md`（enabled）",
        "- `false_positive` → 后续评审不再当约束",
        "- `deferred` / `later` → 只留在本表",
        "- 空 / `unset` → 待处置；`/pm-status` 应提示条数",
        "",
    ]
    return "\n".join(lines)


def write_reviews(project_root: Path, rows: list[ReviewRow]) -> Path:
    dest = reviews_path(project_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_reviews(rows), encoding="utf-8")
    return dest


def append_reviews(project_root: Path, new_rows: list[ReviewRow]) -> list[ReviewRow]:
    rows = load_reviews(project_root)
    existing_snip = {(r.file, r.snippet) for r in rows}
    added: list[ReviewRow] = []
    for row in new_rows:
        key = (row.file, row.snippet)
        if key in existing_snip and row.snippet:
            continue
        if not row.id or row.id in PLACEHOLDER_IDS:
            row.id = next_review_id(rows + added)
        rows.append(row)
        added.append(row)
        existing_snip.add(key)
    write_reviews(project_root, rows)
    return added


def get_review(project_root: Path, rid: str) -> ReviewRow | None:
    want = (rid or "").strip().upper()
    for row in load_reviews(project_root):
        if row.id.upper() == want:
            return row
    return None


def latest_unset(project_root: Path) -> ReviewRow | None:
    pending = pending_reviews(project_root)
    return pending[-1] if pending else None


def set_disposition(project_root: Path, rid: str, disposition: str) -> ReviewRow:
    rows = load_reviews(project_root)
    want = (rid or "").strip().upper()
    found: ReviewRow | None = None
    for row in rows:
        if row.id.upper() == want:
            row.disposition = disposition
            found = row
            break
    if found is None:
        raise FileNotFoundError(f"没有评审 {rid}")
    write_reviews(project_root, rows)
    return found
