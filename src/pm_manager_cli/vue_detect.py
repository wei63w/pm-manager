"""Evidence-based Vue/Nuxt detection from root package.json. Additive only."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_VUE_PACKAGES = ("vue", "nuxt", "nuxt3")
_MAJOR = re.compile(r"(\d+)")


def read_package_json(root: Path) -> dict:
    path = root.resolve() / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}


def package_deps(root: Path) -> dict[str, str]:
    """Merge dependencies / devDependencies / peerDependencies (name → version spec)."""
    data = read_package_json(root)
    out: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(key)
        if not isinstance(block, dict):
            continue
        for name, spec in block.items():
            out[str(name)] = "" if spec is None else str(spec)
    return out


def has_dep(root: Path, name: str) -> bool:
    return name in package_deps(root)


def is_vue_project(root: Path) -> bool:
    deps = package_deps(root)
    return any(pkg in deps for pkg in _VUE_PACKAGES)


def _major(spec: str) -> int | None:
    m = _MAJOR.search(spec or "")
    return int(m.group(1)) if m else None


@dataclass
class VueHints:
    is_vue: bool = False
    runtime: str = ""
    build: str = ""
    stacks: list[str] = field(default_factory=list)


def vue_hints(root: Path) -> VueHints:
    """Fill runtime/build/stack labels only from package.json + config files."""
    root = root.resolve()
    deps = package_deps(root)
    if not any(pkg in deps for pkg in _VUE_PACKAGES):
        return VueHints()

    hints = VueHints(is_vue=True)
    if "nuxt" in deps or "nuxt3" in deps:
        hints.runtime = "nuxt"
        hints.stacks.append("Nuxt")
        nuxt_ver = _major(deps.get("nuxt") or deps.get("nuxt3") or "")
        if nuxt_ver == 2:
            hints.stacks.append("Vue 2")
        else:
            hints.stacks.append("Vue 3")
    else:
        major = _major(deps.get("vue", ""))
        if major == 2:
            hints.runtime = "vue2"
            hints.stacks.append("Vue 2")
        else:
            hints.runtime = "vue3"
            hints.stacks.append("Vue 3")

    vite_cfg = any(
        (root / name).is_file()
        for name in (
            "vite.config.ts",
            "vite.config.js",
            "vite.config.mts",
            "vite.config.mjs",
        )
    )
    vue_cli = (root / "vue.config.js").is_file() or (root / "vue.config.ts").is_file()
    if "nuxt" in deps or "nuxt3" in deps:
        hints.build = "nuxt"
    elif "vite" in deps or vite_cfg:
        hints.build = "vite"
        hints.stacks.append("Vite")
    elif vue_cli:
        hints.build = "vue-cli"

    return hints
