"""Parse `.pm/engineering/reviews.md` disposition table."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PENDING = frozenset({"", "unset", "—", "-", "deferred", "later"})
PLACEHOLDER_IDS = frozenset({"", "—", "-", "id"})


@dataclass
class ReviewRow:
    id: str
    summary: str
    reasoning: str
    snippet: str
    severity: str
    disposition: str


def reviews_path(project_root: Path) -> Path:
    return project_root.resolve() / ".pm" / "engineering" / "reviews.md"


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
        rows.append(
            ReviewRow(
                id=rid,
                summary=cells[1],
                reasoning=cells[2],
                snippet=cells[3],
                severity=cells[4],
                disposition=cells[5].lower(),
            )
        )
    return rows


def pending_reviews(project_root: Path) -> list[ReviewRow]:
    path = reviews_path(project_root)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [r for r in parse_reviews(text) if r.disposition in PENDING]


def pending_review_count(project_root: Path) -> int:
    return len(pending_reviews(project_root))
