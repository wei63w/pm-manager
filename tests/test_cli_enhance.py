from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def _inited(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    assert (
        runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code == 0
    )
    return tmp_path


def test_tests_lists_gap_and_does_not_write_tests(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    assert runner.invoke(app, ["arch", str(root)]).exit_code == 0
    result = runner.invoke(app, ["tests", str(root)])
    assert result.exit_code == 0, result.output
    assert "app.py" in result.output
    gaps = (root / ".pm" / "state" / "test-gaps.md").read_text(encoding="utf-8")
    assert "src/app.py" in gaps
    assert not (root / "tests").exists()
    assert not list(root.glob("**/test_app.py"))


def test_export_includes_bundle_sections(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    runner.invoke(app, ["arch", str(root)])
    dest = tmp_path / "out.md"
    result = runner.invoke(app, ["export", str(root), "--out", str(dest)])
    assert result.exit_code == 0, result.output
    body = dest.read_text(encoding="utf-8")
    assert "## 评审" in body
    assert "## 单测缺口" in body
    assert "## 幻觉防御" in body
    assert "## 架构产物" in body
    assert "map.json" in body


def test_hook_install_and_refuses_foreign(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    result = runner.invoke(app, ["hook", "install", "--path", str(root)])
    assert result.exit_code == 0, result.output
    hook = root / ".git" / "hooks" / "pre-commit"
    assert hook.is_file()
    assert "PM-MANAGER-HOOK" in hook.read_text(encoding="utf-8")
    hook.write_text("#!/bin/sh\necho foreign\n", encoding="utf-8")
    blocked = runner.invoke(app, ["hook", "install", "--path", str(root)])
    assert blocked.exit_code == 1
    assert "外来" in blocked.output
    assert "foreign" in hook.read_text(encoding="utf-8")


def test_config_apply_fills_missing_not_name(tmp_path: Path) -> None:
    root = _inited(tmp_path)
    cfg = root / ".pm" / "config" / "project.yaml"
    cfg.write_text("version: \"2.0\"\nproject:\n  name: keep-me\n", encoding="utf-8")
    result = runner.invoke(
        app, ["config", "apply", "frontend", "--path", str(root)]
    )
    assert result.exit_code == 0, result.output
    text = cfg.read_text(encoding="utf-8")
    assert "name: keep-me" in text
    assert "docs:" in text
    assert "DOC-agents" in text
    assert "profile: frontend" in text
