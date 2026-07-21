from __future__ import annotations

from importlib import resources
from pathlib import Path


def pack_root() -> Path:
    """Return the bundled pack directory (installed) or repo pack (editable/dev)."""
    # Installed wheel: pm_manager_cli/pack/...
    try:
        base = resources.files("pm_manager_cli")
        pack = Path(str(base.joinpath("pack")))
        if (pack / "templates").is_dir():
            return pack
    except Exception:
        pass

    # Dev: repo root (…/pm-manager) when running from source
    here = Path(__file__).resolve()
    repo = here.parents[2]
    if (repo / "templates").is_dir():
        return repo

    raise FileNotFoundError(
        "PM Manager pack assets not found. Reinstall with: "
        "uv tool install pm-manager-cli --from git+https://github.com/wei63w/pm-manager.git"
    )


def templates_pm() -> Path:
    return pack_root() / "templates" / "pm"


def adapters_root() -> Path:
    return pack_root() / "adapters"
