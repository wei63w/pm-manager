from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def _inited(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    assert (
        runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code == 0
    )
    return tmp_path


def test_log_writes_dialogue_under_pm_only(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    result = runner.invoke(
        app,
        [
            "log",
            "修一下 src/app.py 的登录超时 password=supersecret",
            "--path",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "bug修复" in result.output
    jsonl = (root / ".pm" / "state" / "dialogue.jsonl").read_text(encoding="utf-8")
    md = (root / ".pm" / "state" / "dialogue.md").read_text(encoding="utf-8")
    assert "src/app.py" in jsonl
    assert "supersecret" not in jsonl
    assert "supersecret" not in md
    assert (root / ".pm" / "state" / "timeline.md").is_file()
    assert (root / ".pm" / "state" / "suggestions.md").is_file()
    assert not (root / "dialogue.md").exists()


def test_journal_lists_intent_and_suggestions(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    assert (
        runner.invoke(
            app, ["log", "修一下 src/app.py", "--path", str(root)]
        ).exit_code
        == 0
    )
    result = runner.invoke(app, ["journal", str(root)])
    assert result.exit_code == 0, result.output
    assert "本轮意图" in result.output
    assert "优化建议" in result.output
    assert "变更点" in result.output
    session = (root / ".pm" / "state" / "session.json").read_text(encoding="utf-8")
    assert "src/app.py" in session
    assert "开发迭代时间线" in (
        root / ".pm" / "state" / "timeline.md"
    ).read_text(encoding="utf-8")


def test_status_includes_session_after_log(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    runner.invoke(app, ["log", "补一下文档 design.md", "--path", str(root)])
    result = runner.invoke(app, ["status", str(root)])
    assert result.exit_code == 0, result.output
    assert "本轮意图" in result.output
    assert "优化建议" in result.output
    overview = (root / ".pm" / "state" / "overview.md").read_text(encoding="utf-8")
    assert "本轮意图" in overview


def test_export_includes_journal_section(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    runner.invoke(app, ["log", "修一下 src/app.py", "--path", str(root)])
    dest = tmp_path / "out.md"
    result = runner.invoke(app, ["export", str(root), "--out", str(dest)])
    assert result.exit_code == 0, result.output
    body = dest.read_text(encoding="utf-8")
    assert "## 开发记录" in body
    assert "src/app.py" in body
