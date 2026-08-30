from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_PRD_CANDIDATES = (
    Path("docs") / "prd.md",
    Path("docs") / "PRD.md",
    Path("docs") / "requirements.md",
    Path("PRD.md"),
)

MIN_DOC_BYTES = 80


@dataclass
class SpecKitDetection:
    present: bool
    constitution: Path | None = None
    specs: list[Path] = field(default_factory=list)

    def constitution_rel(self, root: Path) -> str:
        if not self.constitution:
            return ""
        return self.constitution.relative_to(root).as_posix()

    def spec_rels(self, root: Path) -> list[str]:
        return [p.relative_to(root).as_posix() for p in self.specs]


def detect_speckit(root: Path) -> SpecKitDetection:
    """True only when Spec Kit artifacts exist — empty `.specify/` does not count."""
    root = root.resolve()
    specify = root / ".specify"
    constitution = specify / "memory" / "constitution.md"
    specs: list[Path] = []
    specs_root = specify / "specs"
    if specs_root.is_dir():
        specs = sorted(p for p in specs_root.rglob("*.md") if p.is_file())
    present = constitution.is_file() or bool(specs)
    return SpecKitDetection(
        present=present,
        constitution=constitution if constitution.is_file() else None,
        specs=specs,
    )


def existing_prd_candidates(root: Path) -> list[Path]:
    """Project docs that already look like a product PRD (not under `.pm/`)."""
    root = root.resolve()
    found: list[Path] = []
    seen: set[str] = set()
    for rel in REPO_PRD_CANDIDATES:
        p = root / rel
        if not (p.is_file() and p.stat().st_size >= MIN_DOC_BYTES):
            continue
        key = str(p.resolve()).casefold()
        if key in seen:
            continue
        seen.add(key)
        found.append(p)
    return found


def looks_like_existing_project(root: Path) -> bool:
    """Heuristic: has build manifest or business source, not README-only."""
    root = root.resolve()
    markers = (
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "package.json",
        "pyproject.toml",
        "go.mod",
        "Cargo.toml",
        "composer.json",
    )
    if any((root / m).is_file() for m in markers):
        return True
    for name in ("src", "app", "apps", "lib", "cmd", "internal"):
        d = root / name
        if d.is_dir() and any(d.iterdir()):
            return True
    return False


def write_init_metadata(root: Path, detection: SpecKitDetection) -> Path:
    """Idempotently write speckit/prd keys on `.pm/config/project.yaml`."""
    yaml_path = root.resolve() / ".pm" / "config" / "project.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(yaml_path)
    text = yaml_path.read_text(encoding="utf-8")
    present = "true" if detection.present else "false"
    constitution = detection.constitution_rel(root)
    specs = detection.spec_rels(root)
    specs_yaml = "[" + ", ".join(f'"{s}"' for s in specs) + "]"

    if re.search(r"(?m)^speckit:\s*$", text):
        text = re.sub(
            r"(?m)^(\s*present:\s*)(true|false)\s*$",
            rf"\g<1>{present}",
            text,
            count=1,
        )
        if constitution:
            if re.search(r"(?m)^\s*constitution:\s*", text):
                text = re.sub(
                    r"(?m)^(\s*constitution:\s*).*$",
                    rf'\g<1>"{constitution}"',
                    text,
                    count=1,
                )
        if re.search(r"(?m)^\s*specs:\s*", text):
            text = re.sub(
                r"(?m)^(\s*specs:\s*).*$",
                rf"\g<1>{specs_yaml}",
                text,
                count=1,
            )
    else:
        block = (
            "\nspeckit:\n"
            f"  present: {present}\n"
            f'  constitution: "{constitution}"\n'
            f"  specs: {specs_yaml}\n"
        )
        text = text.rstrip() + block

    if not re.search(r"(?m)^prd:\s*$", text):
        prd_status = "imported" if detection.present else "absent"
        prd_source = "speckit" if detection.present else "none"
        # status stays draft-like until Agent fills / user confirms
        if detection.present:
            prd_status = "draft"
        text = text.rstrip() + (
            "\nprd:\n"
            f"  status: {prd_status}\n"
            f"  source: {prd_source}\n"
            '  path: ".pm/prd/prd.md"\n'
        )

    yaml_path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return yaml_path


def read_prd_status(project_root: Path) -> str:
    """Read `prd.status` from `.pm/config/project.yaml`. Empty if missing."""
    cfg = project_root.resolve() / ".pm" / "config" / "project.yaml"
    if not cfg.is_file():
        return ""
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"(?ms)^prd:\s*\n(?:[ \t].*\n)*?[ \t]+status:\s*(\S+)", text)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'")
