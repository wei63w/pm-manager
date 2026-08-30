from pathlib import Path

import pytest

from pm_manager_cli.agents import (
    CORE_KEYS,
    REGISTRY,
    install_agents,
    install_cursor,
    installed_agent_keys,
    resolve_agent_spec,
)


def test_install_cursor_writes_slash_skills(tmp_path: Path) -> None:
    dest = install_cursor(tmp_path)
    assert dest == tmp_path / ".cursor" / "skills"
    pack = dest / "pm-manager" / "SKILL.md"
    assert pack.is_file()
    init_skill = dest / "pm-init" / "SKILL.md"
    assert init_skill.is_file()
    text = init_skill.read_text(encoding="utf-8")
    assert 'name: "pm-init"' in text
    assert "sibling `pm-manager` skill" in text
    status = dest / "pm-status" / "SKILL.md"
    assert status.is_file()
    assert 'name: "pm-status"' in status.read_text(encoding="utf-8")


def test_install_cursor_refreshes_existing_skills(tmp_path: Path) -> None:
    skills = tmp_path / ".cursor" / "skills"
    stale = skills / "pm-init"
    stale.mkdir(parents=True)
    (stale / "SKILL.md").write_text("# stale\n", encoding="utf-8")
    install_cursor(tmp_path)
    text = (skills / "pm-init" / "SKILL.md").read_text(encoding="utf-8")
    assert 'name: "pm-init"' in text
    assert "# stale" not in text


def test_install_claude_writes_skills_and_commands(tmp_path: Path) -> None:
    results = install_agents(tmp_path, "claude")
    assert (results["claude"] / "pm-init" / "SKILL.md").is_file()
    cmd = tmp_path / ".claude" / "commands" / "pm-init.md"
    assert cmd.is_file()
    assert 'name: "pm-init"' in cmd.read_text(encoding="utf-8")


def test_install_gemini_writes_toml(tmp_path: Path) -> None:
    results = install_agents(tmp_path, "gemini")
    toml = results["gemini"] / "pm-init.toml"
    assert toml.is_file()
    text = toml.read_text(encoding="utf-8")
    assert "description =" in text
    assert 'name = "pm-init"' in text
    assert "prompt = " in text


def test_install_all_writes_core_hosts(tmp_path: Path) -> None:
    results = install_agents(tmp_path, "all")
    assert set(results) == set(CORE_KEYS)
    assert (tmp_path / ".cursor" / "skills" / "pm-init" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "skills" / "pm-init" / "SKILL.md").is_file()
    assert (tmp_path / ".github" / "skills" / "pm-init" / "SKILL.md").is_file()
    assert (tmp_path / ".windsurf" / "workflows" / "pm-init.md").is_file()
    assert (tmp_path / ".gemini" / "commands" / "pm-init.toml").is_file()
    assert "cursor" in installed_agent_keys(tmp_path)
    assert "gemini" in installed_agent_keys(tmp_path)


def test_comma_and_alias_resolution() -> None:
    assert resolve_agent_spec("cursor,claude") == ["cursor", "claude"]
    assert resolve_agent_spec("cursor-agent") == ["cursor"]
    assert resolve_agent_spec("zed") == ["codex"]
    assert resolve_agent_spec("none") == []
    with pytest.raises(ValueError):
        resolve_agent_spec("not-a-tool")


def test_full_covers_registry() -> None:
    assert set(resolve_agent_spec("full")) == set(REGISTRY)
