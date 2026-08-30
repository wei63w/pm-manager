"""Apply governance profile overlays. Only fill missing keys; never clobber user values."""

from __future__ import annotations

import re
from pathlib import Path

from pm_manager_cli.paths import templates_pm
from pm_manager_cli.speckit import infer_project_type

PROFILES = ("frontend", "backend", "service", "script", "auto")

_TYPE_TO_PROFILE = {
    "node": "frontend",
    "java": "backend",
    "python": "backend",
    "go": "backend",
    "rust": "backend",
    "php": "backend",
}


def resolve_profile_name(root: Path, name: str) -> str:
    raw = (name or "auto").strip().lower()
    if raw == "auto":
        return _TYPE_TO_PROFILE.get(infer_project_type(root), "script")
    if raw not in {"frontend", "backend", "service", "script"}:
        raise ValueError(f"未知模板: {name}（frontend|backend|service|script|auto）")
    return raw


def profile_path(name: str) -> Path:
    return templates_pm() / "profiles" / f"{name}.yaml"


def _top_level_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current = ""
    buf: list[str] = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^[A-Za-z_][\w-]*:", line) and not line.startswith(" "):
            if current:
                blocks[current] = "".join(buf)
            current = line.split(":", 1)[0]
            buf = [line]
        elif current:
            buf.append(line)
    if current:
        blocks[current] = "".join(buf)
    return blocks


def _has_top_key(text: str, key: str) -> bool:
    return bool(re.search(rf"(?m)^{re.escape(key)}:", text))


def apply_profile(project_root: Path, name: str) -> tuple[Path, list[str]]:
    """Append missing top-level keys from a profile. Returns (yaml_path, added_keys)."""
    root = project_root.resolve()
    dest = root / ".pm" / "config" / "project.yaml"
    if not dest.is_file():
        raise FileNotFoundError(f"缺少 .pm/config/project.yaml（{root}）；请先运行 `pm init`")
    resolved = resolve_profile_name(root, name)
    src = profile_path(resolved)
    if not src.is_file():
        raise FileNotFoundError(f"缺少模板 {src}")
    existing = dest.read_text(encoding="utf-8")
    profile = src.read_text(encoding="utf-8")
    added: list[str] = []
    extra = ""
    for key, block in _top_level_blocks(profile).items():
        if key in {"#"}:
            continue
        if _has_top_key(existing, key):
            continue
        extra += "\n" + block.rstrip() + "\n"
        added.append(key)
    if extra:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        dest.write_text(existing + extra, encoding="utf-8")
    return dest, added


def read_required_doc_ids(project_root: Path) -> list[str] | None:
    cfg = project_root.resolve() / ".pm" / "config" / "project.yaml"
    if not cfg.is_file():
        return None
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"(?ms)^docs:\s*\n(?:[ \t].*\n)*?[ \t]+required:\s*\[([^\]]*)\]", text)
    if not m:
        return None
    ids = [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()]
    return ids or None


def read_gate_on_commit(project_root: Path) -> bool:
    cfg = project_root.resolve() / ".pm" / "config" / "project.yaml"
    if not cfg.is_file():
        return False
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(re.search(r"(?m)^\s*gate_on_commit:\s*true\s*$", text))
