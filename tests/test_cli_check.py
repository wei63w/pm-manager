from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def test_check_without_pm_exits_2_and_prompts_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 2
    assert "pm init" in result.output
    assert "缺" not in result.output or "缺少 .pm/" in result.output


def test_check_after_init_lists_prd_and_map(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    assert (
        runner.invoke(
            app, ["init", str(tmp_path), "--scaffold-only"]
        ).exit_code
        == 0
    )
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "prd.status" in result.output
    assert "map.json" in result.output
