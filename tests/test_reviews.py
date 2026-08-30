from pathlib import Path

from pm_manager_cli.guard import qualify_reviews
from pm_manager_cli.reviews import parse_reviews, pending_review_count


def test_parse_skips_placeholder() -> None:
    text = """
| id | summary | reasoning | snippet | severity | disposition |
|----|---------|-----------|---------|----------|-------------|
| — | — | — | — | P0/P1/P2 | unset / confirmed |
| REV-001 | 缺校验 | 未检查空输入 | `if x:` | P1 | unset |
| REV-002 | 已确认 | 推理 | `return` | P2 | confirmed |
"""
    rows = parse_reviews(text)
    assert [r.id for r in rows] == ["REV-001", "REV-002"]


def test_pending_review_count(tmp_path: Path) -> None:
    dest = tmp_path / ".pm" / "engineering"
    dest.mkdir(parents=True)
    (dest / "reviews.md").write_text(
        "| id | summary | reasoning | snippet | severity | disposition |\n"
        "| REV-001 | a | r | s | P1 | unset |\n"
        "| REV-002 | b | r | s | P2 | deferred |\n"
        "| REV-003 | c | r | s | P2 | confirmed |\n",
        encoding="utf-8",
    )
    assert pending_review_count(tmp_path) == 2


def test_qualify_reviews_rejects_missing_reasoning(tmp_path: Path) -> None:
    dest = tmp_path / ".pm" / "engineering"
    dest.mkdir(parents=True)
    (dest / "reviews.md").write_text(
        "| id | summary | reasoning | snippet | severity | disposition |\n"
        "| REV-001 | 空泛 | — | — | P1 | unset |\n"
        "| REV-002 | 合格 | 未校验空输入会误伤 | `if not x:` | P2 | unset |\n",
        encoding="utf-8",
    )
    bad = qualify_reviews(tmp_path)
    assert [r["id"] for r in bad] == ["REV-001"]
