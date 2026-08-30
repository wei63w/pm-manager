from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def _todo_block(n: int, pri: str, status: str = "open") -> str:
    return (
        f"## TODO-{n:03d} [{pri}] item {n}\n\n"
        f"- **Status**: {status}\n"
        f"- **Priority**: {pri}\n\n"
    )


def test_status_lists_all_blocking_not_medium(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    assert (
        runner.invoke(
            app, ["init", str(tmp_path), "--scaffold-only", "--no-skills-sh"]
        ).exit_code
        == 0
    )
    body = "# Todos\n\n"
    for i in range(1, 11):
        body += _todo_block(i, "P0")
    body += _todo_block(99, "P2")
    (tmp_path / ".pm" / "state" / "todo.md").write_text(body, encoding="utf-8")
    result = runner.invoke(app, ["status", str(tmp_path)])
    assert result.exit_code == 0, result.output
    for i in range(1, 11):
        assert f"TODO-{i:03d}" in result.output
    assert "TODO-099" not in result.output
    assert "（10）" in result.output or "(10)" in result.output


def test_status_without_pm_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["status", str(tmp_path)])
    assert result.exit_code == 2
