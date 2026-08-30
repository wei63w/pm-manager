"""Copy skills/pm-manager/templates/commands/*.md into Cursor/Claude adapters."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "skills" / "pm-manager" / "templates" / "commands"
CURSOR = ROOT / "adapters" / "cursor" / "skills"
CLAUDE = ROOT / "adapters" / "claude-code" / "commands"


def _with_cursor_name(body: str, skill_name: str) -> str:
    """Cursor slash menu uses SKILL.md `name:` (Spec Kit style)."""
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            fm = body[4:end].lstrip("\n")
            rest = body[end + 4 :]
            lines = [ln for ln in fm.splitlines() if not ln.startswith("name:")]
            fm = f'name: "{skill_name}"\n' + ("\n".join(lines) + "\n" if lines else "")
            return f"---\n{fm}---{rest}"
    return f'---\nname: "{skill_name}"\ndescription: "PM Manager /{skill_name}"\n---\n\n{body}'


def main() -> None:
    for path in sorted(SRC.glob("*.md")):
        if path.name.startswith("_"):
            continue
        name = path.stem
        body = path.read_text(encoding="utf-8")
        dest_c = CURSOR / f"pm-{name}" / "SKILL.md"
        dest_c.parent.mkdir(parents=True, exist_ok=True)
        dest_c.write_text(_with_cursor_name(body, f"pm-{name}"), encoding="utf-8")
        dest_l = CLAUDE / f"pm-{name}.md"
        dest_l.parent.mkdir(parents=True, exist_ok=True)
        dest_l.write_text(body, encoding="utf-8")
        print(f"synced pm-{name}")


if __name__ == "__main__":
    main()
