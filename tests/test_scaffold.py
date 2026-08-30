from pathlib import Path

from pm_manager_cli.scaffold import ensure_git_exclude, scaffold


def test_exclude_appended_in_git_repo(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    msg = ensure_git_exclude(tmp_path)
    exclude = tmp_path / ".git" / "info" / "exclude"
    text = exclude.read_text(encoding="utf-8")
    assert ".pm/" in text
    assert "appended" in msg or "already present" in msg
    assert ensure_git_exclude(tmp_path) == "already present"


def test_exclude_skipped_without_git(tmp_path: Path) -> None:
    assert ensure_git_exclude(tmp_path) == "skipped (not a git repo)"


def test_scaffold_does_not_touch_gitignore(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("keep-me\n", encoding="utf-8")
    scaffold(tmp_path)
    assert gitignore.read_text(encoding="utf-8") == "keep-me\n"
    yaml_text = (tmp_path / ".pm" / "config" / "project.yaml").read_text(encoding="utf-8")
    assert (tmp_path / ".pm" / "config" / "project.yaml").is_file()
    assert "type: unknown" in yaml_text
    assert "java-spring-boot" not in yaml_text


def test_second_scaffold_does_not_overwrite_user_files(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    scaffold(tmp_path)
    cfg = tmp_path / ".pm" / "config" / "project.yaml"
    cfg.write_text("# user-edited\n", encoding="utf-8")
    scaffold(tmp_path)
    assert cfg.read_text(encoding="utf-8") == "# user-edited\n"


def test_existing_project_yaml_not_reset(tmp_path: Path) -> None:
    pm = tmp_path / ".pm" / "config"
    pm.mkdir(parents=True)
    (pm / "project.yaml").write_text("version: kept\n", encoding="utf-8")
    scaffold(tmp_path)
    assert (pm / "project.yaml").read_text(encoding="utf-8") == "version: kept\n"
