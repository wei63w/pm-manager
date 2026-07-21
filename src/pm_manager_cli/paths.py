from __future__ import annotations

from importlib import resources
from pathlib import Path


def _repo_root() -> Path:
    # src/pm_manager_cli/paths.py → repo root
    return Path(__file__).resolve().parents[2]


def pack_root() -> Path:
    """Return skill pack assets (SKILL.md, templates, memory)."""
    # Installed wheel: pm_manager_cli/pack/...
    try:
        base = resources.files("pm_manager_cli")
        pack = Path(str(base.joinpath("pack")))
        if (pack / "templates").is_dir():
            return pack
    except Exception:
        pass

    # Dev: skills/pm-manager (skills.sh / Agent Skills layout)
    skill = _repo_root() / "skills" / "pm-manager"
    if (skill / "templates").is_dir():
        return skill

    raise FileNotFoundError(
        "PM Manager pack assets not found. Reinstall with: "
        "uv tool install pm-manager-cli --from git+https://github.com/wei63w/pm-manager.git"
    )


def adapters_root() -> Path:
    """Return adapters/ (Cursor + Claude). Kept at repo/pack root, not inside the skill folder."""
    try:
        base = resources.files("pm_manager_cli")
        adapters = Path(str(base.joinpath("pack").joinpath("adapters")))
        if adapters.is_dir():
            return adapters
    except Exception:
        pass

    adapters = _repo_root() / "adapters"
    if adapters.is_dir():
        return adapters

    raise FileNotFoundError(
        "PM Manager adapters not found. Reinstall with: "
        "uv tool install pm-manager-cli --from git+https://github.com/wei63w/pm-manager.git"
    )


def templates_pm() -> Path:
    return pack_root() / "templates" / "pm"
