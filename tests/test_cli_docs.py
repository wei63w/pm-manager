from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def _inited(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    result = runner.invoke(
        app, ["init", str(tmp_path), "--scaffold-only", "--no-skills-sh"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path


def test_docs_marks_design_missing(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    result = runner.invoke(app, ["docs", str(root)])
    assert result.exit_code == 0, result.output
    index = (root / ".pm" / "state" / "doc-index.md").read_text(encoding="utf-8")
    assert "DOC-design" in index
    assert "| DOC-design | design.md | missing |" in index


def test_docs_marks_design_present(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "design.md").write_text("# Design\n\nHello.\n", encoding="utf-8")
    result = runner.invoke(app, ["docs", str(root)])
    assert result.exit_code == 0, result.output
    index = (root / ".pm" / "state" / "doc-index.md").read_text(encoding="utf-8")
    assert "| DOC-design | design.md | present | docs/design.md |" in index


def test_docs_without_pm_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["docs", str(tmp_path)])
    assert result.exit_code == 2
