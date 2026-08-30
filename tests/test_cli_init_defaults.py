from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def test_init_default_type_unknown_then_infer_python(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    result = runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"])
    assert result.exit_code == 0, result.output
    assert "/pm-init" in result.output
    text = (tmp_path / ".pm" / "config" / "project.yaml").read_text(encoding="utf-8")
    assert "type: python" in text
    assert "lifecycle: existing" in text
    assert "java-spring-boot" not in text


def test_init_empty_repo_stays_unknown_new(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    result = runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"])
    assert result.exit_code == 0, result.output
    text = (tmp_path / ".pm" / "config" / "project.yaml").read_text(encoding="utf-8")
    assert "type: unknown" in text
    assert "lifecycle: new" in text


def test_status_mentions_pending_reviews(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    assert (
        runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code
        == 0
    )
    reviews = tmp_path / ".pm" / "engineering" / "reviews.md"
    reviews.write_text(
        "| id | summary | reasoning | snippet | severity | disposition |\n"
        "| REV-001 | x | why | `code` | P1 | unset |\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["status", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "待处置评审: 1" in result.output
