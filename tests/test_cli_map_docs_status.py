import os
import time
from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def _inited_app(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n\nHello.\n", encoding="utf-8")
    assert (
        runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code == 0
    )
    return tmp_path


def test_map_query_hits_key_file(tmp_path: Path) -> None:
    root = _inited_app(tmp_path)
    assert runner.invoke(app, ["arch", str(root)]).exit_code == 0
    result = runner.invoke(app, ["map", "app.py", "--path", str(root)])
    assert result.exit_code == 0, result.output
    assert "app.py" in result.output


def test_map_without_arch_exits_2(tmp_path: Path) -> None:
    root = _inited_app(tmp_path)
    result = runner.invoke(app, ["map", "--path", str(root)])
    assert result.exit_code == 2
    assert "pm arch" in result.output


def test_docs_draft_stays_under_pm(tmp_path: Path) -> None:
    root = _inited_app(tmp_path)
    result = runner.invoke(app, ["docs", str(root), "--draft"])
    assert result.exit_code == 0, result.output
    draft = root / ".pm" / "docs" / "drafts" / "DOC-design.md"
    assert draft.is_file()
    assert "未确认不得写入" in draft.read_text(encoding="utf-8")
    assert not (root / "docs" / "design.md").exists()
    assert not (root / "design.md").exists()


def test_docs_marks_stale_when_source_newer(tmp_path: Path) -> None:
    root = _inited_app(tmp_path)
    docs = root / "docs"
    docs.mkdir()
    design = docs / "design.md"
    design.write_text("# Design\n\nOld.\n", encoding="utf-8")
    assert runner.invoke(app, ["arch", str(root)]).exit_code == 0
    old = time.time() - 3600
    os.utime(design, (old, old))
    app_py = root / "src" / "app.py"
    app_py.write_text("print(2)\n", encoding="utf-8")
    assert runner.invoke(app, ["arch", str(root)]).exit_code == 0
    result = runner.invoke(app, ["docs", str(root)])
    assert result.exit_code == 0, result.output
    index = (root / ".pm" / "state" / "doc-index.md").read_text(encoding="utf-8")
    assert "possibly_stale" in index
    assert "| DOC-design |" in index


def test_status_includes_stack_and_modules(tmp_path: Path) -> None:
    root = _inited_app(tmp_path)
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    assert runner.invoke(app, ["arch", str(root)]).exit_code == 0
    result = runner.invoke(app, ["status", str(root)])
    assert result.exit_code == 0, result.output
    assert "技术栈" in result.output
    assert "模块" in result.output
    assert "缺失核心文档" in result.output
    overview = (root / ".pm" / "state" / "overview.md").read_text(encoding="utf-8")
    assert "现状快照" in overview
    assert (root / ".pm" / "state" / "report.md").is_file()
