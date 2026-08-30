from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app
from pm_manager_cli.review_engine import run_cross_review
from pm_manager_cli.reviews import load_reviews
from pm_manager_cli.rules_lib import add_rule, match_rules, set_rule_enabled

runner = CliRunner()


def _inited(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    assert (
        runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code == 0
    )
    return tmp_path


def test_review_no_diff_does_not_invent(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    result = runner.invoke(app, ["review", "--path", str(root)])
    assert result.exit_code == 0, result.output
    assert "没有可评的变更" in result.output
    rows = load_reviews(root)
    assert rows == []


def test_confirm_qualified_writes_rule(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    reviews = root / ".pm" / "engineering" / "reviews.md"
    reviews.write_text(
        "| id | summary | reasoning | snippet | severity | disposition |\n"
        "| REV-001 | 缺校验 | 未检查空输入会误伤调用方 | `if not x:` | P1 | unset |\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["review", "confirm", "REV-001", "--path", str(root)]
    )
    assert result.exit_code == 0, result.output
    rules = (root / ".pm" / "engineering" / "rules.md").read_text(encoding="utf-8")
    assert "REV-001" in rules
    assert "true" in rules


def test_confirm_unqualified_rejected(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    (root / ".pm" / "engineering" / "reviews.md").write_text(
        "| id | summary | reasoning | snippet | severity | disposition |\n"
        "| REV-001 | 空泛 | — | — | P1 | unset |\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["review", "confirm", "REV-001", "--path", str(root)]
    )
    assert result.exit_code == 1
    assert "推理" in result.output or "片段" in result.output
    rules = (root / ".pm" / "engineering" / "rules.md").read_text(encoding="utf-8")
    assert "REV-001" not in rules


def test_disable_rule_not_matched(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    rule = add_rule(root, "禁止使用 eval 调用", source_finding="REV-009", severity="P0")
    assert match_rules(root, path="src/app.py", blob="eval(user)")
    set_rule_enabled(root, rule.id, False)
    assert match_rules(root, path="src/app.py", blob="eval(user)") == []


def test_checkup_flags_eval(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    (root / "src" / "app.py").write_text("def f(x):\n    return eval(x)\n", encoding="utf-8")
    result = runner.invoke(app, ["checkup", str(root)])
    assert result.exit_code == 0, result.output
    assert "P0" in result.output
    body = (root / ".pm" / "state" / "checkup.md").read_text(encoding="utf-8")
    assert "危险调用" in body or "eval" in body.lower()


def test_annotate_stays_under_pm(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    (root / ".pm" / "engineering" / "reviews.md").write_text(
        "| id | summary | reasoning | snippet | severity | disposition | file | line |\n"
        "| REV-003 | 注释 | 这里缺少边界说明 | `return x` | P2 | unset | src/app.py | 1 |\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app, ["review", "annotate", "REV-003", "--path", str(root)]
    )
    assert result.exit_code == 0, result.output
    dest = root / ".pm" / "reviews" / "annotations" / "REV-003.md"
    assert dest.is_file()
    assert "src/app.py" in dest.read_text(encoding="utf-8")
    assert not (root / "src" / "REV-003.md").exists()


def test_cross_does_not_duplicate_snippet(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    (root / ".pm" / "engineering" / "reviews.md").write_text(
        "| id | summary | reasoning | snippet | severity | disposition | file | line | dimension | cross |\n"
        "| REV-010 | 危险 | 新增 eval 有注入风险 | `return eval(x)` | P0 | unset | src/app.py | 2 | security | unset |\n",
        encoding="utf-8",
    )
    added, dest = run_cross_review(root)
    assert dest.is_file()
    assert all(r.snippet != "return eval(x)" or r.cross != "new" for r in added)
    rows = load_reviews(root)
    assert any(r.id == "REV-010" and r.cross == "agree" for r in rows)
