from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.cli import app

runner = CliRunner()


def test_export_redacts_secrets_and_filters_window(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    assert (
        runner.invoke(
            app, ["init", str(tmp_path), "--scaffold-only", "--no-skills-sh"]
        ).exit_code
        == 0
    )
    audit = tmp_path / ".pm" / "state" / "audit.jsonl"
    audit.write_text(
        "\n".join(
            [
                '{"ts":"2026-01-01T12:00:00Z","command":"pm-init","input_summary":"early","output_summary":"ok"}',
                '{"ts":"2026-08-15T12:00:00Z","command":"pm-fix","input_summary":"key=AKIAIOSFODNN7EXAMPLE leftover","output_summary":"-----BEGIN PRIVATE KEY-----\\nMIIHide\\n-----END PRIVATE KEY-----"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    dest = tmp_path / "out.md"
    result = runner.invoke(
        app,
        [
            "export",
            str(tmp_path),
            "--from",
            "2026-08-01",
            "--to",
            "2026-08-31",
            "--out",
            str(dest),
        ],
    )
    assert result.exit_code == 0, result.output
    body = dest.read_text(encoding="utf-8")
    assert "AKIAIOSFODNN7EXAMPLE" not in body
    assert "BEGIN PRIVATE KEY" not in body
    assert "***" in body
    assert "pm-fix" in body
    assert "pm-init" not in body
    assert "leftover" in body


def test_export_aborts_and_deletes_when_residue_forced(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    assert (
        runner.invoke(
            app, ["init", str(tmp_path), "--scaffold-only"]
        ).exit_code
        == 0
    )
    dest = tmp_path / "leaky.md"
    dest.write_text("pre-existing\n", encoding="utf-8")

    def _leaky(*_args, **_kwargs):
        dest.write_text("key=AKIAIOSFODNN7EXAMPLE leftover\n", encoding="utf-8")
        return dest, 1

    monkeypatch.setattr("pm_manager_cli.cli.write_export", _leaky)
    result = runner.invoke(app, ["export", str(tmp_path), "--out", str(dest)])
    assert result.exit_code == 2, result.output
    assert "秘密" in result.output
    assert not dest.exists()


def test_export_without_pm_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, ["export", str(tmp_path)])
    assert result.exit_code == 2


def test_init_and_arch_append_audit(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    init = runner.invoke(
        app, ["init", str(tmp_path), "--scaffold-only", "--no-skills-sh"]
    )
    assert init.exit_code == 0, init.output
    audit = tmp_path / ".pm" / "state" / "audit.jsonl"
    text = audit.read_text(encoding="utf-8")
    assert "pm-init" in text
    arch = runner.invoke(app, ["arch", str(tmp_path)])
    assert arch.exit_code == 0, arch.output
    text2 = audit.read_text(encoding="utf-8")
    assert "pm-arch" in text2
    assert text2.count("\n") > text.count("\n")
