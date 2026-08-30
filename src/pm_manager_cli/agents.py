from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pm_manager_cli.paths import adapters_root, pack_root

# skills.sh / `npx skills add` source (override with PM_SKILLS_SOURCE)
DEFAULT_SKILLS_SOURCE = os.environ.get("PM_SKILLS_SOURCE", "wei63w/pm-manager")

Kind = Literal["skills", "commands", "toml"]

_PACK_POINTER = (
    "When this skill refers to `templates/` or `memory/`, "
    "read them from the sibling `pm-manager` skill in this same skills directory.\n"
)


@dataclass(frozen=True)
class AgentTarget:
    key: str
    kind: Kind
    rel_dir: str
    hint: str
    extra_commands_dir: str | None = None


# Paths follow Spec Kit / each host's documented layout.
REGISTRY: dict[str, AgentTarget] = {
    "cursor": AgentTarget(
        "cursor",
        "skills",
        ".cursor/skills",
        "新开 Agent 对话，输入 /pm",
    ),
    "claude": AgentTarget(
        "claude",
        "skills",
        ".claude/skills",
        "输入 /pm-init（Skills + slash commands）",
        extra_commands_dir=".claude/commands",
    ),
    "codex": AgentTarget(
        "codex",
        "skills",
        ".agents/skills",
        "Codex / Zed：技能 pm-init（或 $pm-init）",
    ),
    "copilot": AgentTarget(
        "copilot",
        "skills",
        ".github/skills",
        "Copilot Chat 调用 pm-init 技能",
    ),
    "windsurf": AgentTarget(
        "windsurf", "commands", ".windsurf/workflows", "Windsurf：/pm-init"
    ),
    "gemini": AgentTarget("gemini", "toml", ".gemini/commands", "Gemini CLI：/pm-init"),
    "qwen": AgentTarget("qwen", "commands", ".qwen/commands", "Qwen Code：/pm-init"),
    "opencode": AgentTarget(
        "opencode", "commands", ".opencode/commands", "opencode：/pm-init"
    ),
    "kilocode": AgentTarget(
        "kilocode", "commands", ".kilo/commands", "Kilo Code：/pm-init"
    ),
    "trae": AgentTarget("trae", "skills", ".trae/skills", "Trae：/pm-init"),
    "auggie": AgentTarget(
        "auggie", "commands", ".augment/commands", "Auggie：/pm-init"
    ),
    "cline": AgentTarget(
        "cline", "commands", ".clinerules/workflows", "Cline：/pm-init"
    ),
    "grok": AgentTarget("grok", "skills", ".grok/skills", "Grok：/pm-init"),
    "droid": AgentTarget("droid", "skills", ".factory/skills", "Factory Droid：/pm-init"),
    "lingma": AgentTarget("lingma", "skills", ".lingma/skills", "Lingma：/pm-init"),
    "kimi": AgentTarget("kimi", "skills", ".kimi-code/skills", "Kimi Code：/pm-init"),
    "zcode": AgentTarget("zcode", "skills", ".zcode/skills", "ZCode：$pm-init"),
    "command-code": AgentTarget(
        "command-code", "skills", ".commandcode/skills", "Command Code：$pm-init"
    ),
    "qoder": AgentTarget("qoder", "skills", ".qoder/skills", "Qoder：/pm-init"),
    "alquimia": AgentTarget(
        "alquimia", "skills", ".alquimia/skills", "Alquimia：/pm-init"
    ),
    "devin": AgentTarget("devin", "skills", ".devin/skills", "Devin：/pm-init"),
    "codebuddy": AgentTarget(
        "codebuddy", "commands", ".codebuddy/commands", "CodeBuddy：/pm-init"
    ),
    "junie": AgentTarget("junie", "commands", ".junie/commands", "Junie：/pm-init"),
    "shai": AgentTarget("shai", "commands", ".shai/commands", "SHAI：/pm-init"),
    "omp": AgentTarget("omp", "commands", ".omp/commands", "Oh My Pi：/pm-init"),
    "firebender": AgentTarget(
        "firebender", "commands", ".firebender/commands", "Firebender：/pm-init"
    ),
    "tabnine": AgentTarget(
        "tabnine", "commands", ".tabnine/agent/commands", "Tabnine：/pm-init"
    ),
    "kiro": AgentTarget("kiro", "commands", ".kiro/prompts", "Kiro：/pm-init"),
    "pi": AgentTarget("pi", "commands", ".pi/prompts", "Pi：/pm-init"),
}

ALIASES: dict[str, str] = {
    "cursor-agent": "cursor",
    "github": "copilot",
    "agents": "codex",
    "zed": "codex",
    "kilo": "kilocode",
    "kiro-cli": "kiro",
    "qodercli": "qoder",
}

# Default `all`: mainstream hosts. `full` writes every registry entry.
CORE_KEYS: tuple[str, ...] = (
    "cursor",
    "claude",
    "codex",
    "copilot",
    "windsurf",
    "gemini",
    "qwen",
    "opencode",
    "kilocode",
    "trae",
    "auggie",
    "cline",
)

AGENT_CHOICES = (
    "all | full | none | "
    + " | ".join(REGISTRY)
    + "（可逗号组合，如 cursor,claude）"
)


def known_agent_keys() -> list[str]:
    return list(REGISTRY)


def resolve_agent_spec(spec: str, *, allow_none: bool = True) -> list[str]:
    """Return canonical agent keys. Empty list means install nothing."""
    raw = spec.lower().strip()
    if not raw:
        raise ValueError("empty --agent")
    if raw == "none":
        if not allow_none:
            raise ValueError("--agent 不能是 none")
        return []
    if raw == "all":
        return list(CORE_KEYS)
    if raw == "full":
        return list(REGISTRY)
    keys: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        key = ALIASES.get(token, token)
        if key not in REGISTRY:
            raise ValueError(f"未知助手 {token!r}。可选: {AGENT_CHOICES}")
        if key not in seen:
            seen.add(key)
            keys.append(key)
    if not keys:
        raise ValueError("empty --agent")
    return keys


def _with_skill_name(text: str, name: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[4:end].lstrip("\n")
            body = text[end + 4 :]
            lines = [ln for ln in fm.splitlines() if not ln.startswith("name:")]
            fm = f'name: "{name}"\n' + ("\n".join(lines) + "\n" if lines else "")
            return f"---\n{fm}---{body}"
    return f'---\nname: "{name}"\ndescription: "PM Manager /{name}"\n---\n\n{text}'


def _ensure_pack_pointer(skill_md: Path) -> None:
    text = skill_md.read_text(encoding="utf-8")
    if _PACK_POINTER.strip() in text:
        return
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            head = text[: end + 4]
            body = text[end + 4 :].lstrip("\n")
            skill_md.write_text(f"{head}\n\n{_PACK_POINTER}\n{body}", encoding="utf-8")
            return
    skill_md.write_text(f"{_PACK_POINTER}\n{text}", encoding="utf-8")


def _description_from_md(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[4:end].splitlines():
                if line.startswith("description:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return "PM Manager command"


def _iter_commands() -> list[tuple[str, str]]:
    src = pack_root() / "templates" / "commands"
    if not src.is_dir():
        adapter = adapters_root() / "claude-code" / "commands"
        if adapter.is_dir():
            items: list[tuple[str, str]] = []
            for path in sorted(adapter.glob("pm-*.md")):
                items.append((path.stem, path.read_text(encoding="utf-8-sig")))
            return items
        raise FileNotFoundError(f"command templates missing: {src}")
    items = []
    for path in sorted(src.glob("*.md")):
        if path.name.startswith("_"):
            continue
        items.append((f"pm-{path.stem}", path.read_text(encoding="utf-8-sig")))
    return items


def _write_pack(skills_dir: Path) -> Path:
    dest_pack = skills_dir / "pm-manager"
    src = pack_root()
    if dest_pack.exists():
        shutil.rmtree(dest_pack)
    dest_pack.mkdir(parents=True, exist_ok=True)
    for name in ("SKILL.md", "AGENTS.md", "templates", "memory"):
        s = src / name
        d = dest_pack / name
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    (dest_pack / ".pm-manager-pack.txt").write_text(str(src), encoding="utf-8")
    return dest_pack


def _replace_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _install_skills(project_root: Path, rel_dir: str) -> Path:
    skills_dir = project_root / Path(rel_dir)
    skills_dir.mkdir(parents=True, exist_ok=True)
    _write_pack(skills_dir)
    for name, body in _iter_commands():
        dest_skill = skills_dir / name
        _replace_dir(dest_skill)
        dest_md = dest_skill / "SKILL.md"
        dest_md.write_text(_with_skill_name(body, name), encoding="utf-8")
        _ensure_pack_pointer(dest_md)
    return skills_dir


def _install_commands(project_root: Path, rel_dir: str) -> Path:
    dest = project_root / Path(rel_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for name, body in _iter_commands():
        (dest / f"{name}.md").write_text(
            _with_skill_name(body, name), encoding="utf-8"
        )
    pointer = dest / "pm-manager-pack.path"
    pointer.write_text(str(pack_root()), encoding="utf-8")
    return dest


def _to_toml(name: str, body: str) -> str:
    desc = _description_from_md(body)
    prompt = body
    if '"""' in prompt:
        prompt = prompt.replace('"""', "'''")
    return (
        f'description = {desc!r}\n'
        f'name = "{name}"\n\n'
        f'prompt = """\n{prompt.rstrip()}\n"""\n'
    )


def _install_toml(project_root: Path, rel_dir: str) -> Path:
    dest = project_root / Path(rel_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for name, body in _iter_commands():
        (dest / f"{name}.toml").write_text(_to_toml(name, body), encoding="utf-8")
    return dest


def install_target(project_root: Path, target: AgentTarget) -> Path:
    project_root = project_root.resolve()
    if target.kind == "skills":
        dest = _install_skills(project_root, target.rel_dir)
        if target.extra_commands_dir:
            _install_commands(project_root, target.extra_commands_dir)
        return dest
    if target.kind == "commands":
        return _install_commands(project_root, target.rel_dir)
    if target.kind == "toml":
        return _install_toml(project_root, target.rel_dir)
    raise ValueError(f"unknown agent kind: {target.kind}")


def install_cursor(project_root: Path) -> Path:
    """Install Cursor skills so `/pm-*` appears in the slash menu."""
    return install_target(project_root, REGISTRY["cursor"])


def install_claude(project_root: Path) -> Path:
    """Install Claude Code skills plus legacy `.claude/commands/`."""
    return install_target(project_root, REGISTRY["claude"])


def install_agents(project_root: Path, agent: str) -> dict[str, Path]:
    keys = resolve_agent_spec(agent, allow_none=False)
    results: dict[str, Path] = {}
    for key in keys:
        results[key] = install_target(project_root, REGISTRY[key])
    return results


def installed_agent_keys(project_root: Path) -> list[str]:
    """Which registry agents look present under project_root."""
    root = project_root.resolve()
    found: list[str] = []
    for key, target in REGISTRY.items():
        base = root / Path(target.rel_dir)
        ok = False
        if target.kind == "skills":
            ok = (base / "pm-init" / "SKILL.md").is_file()
        elif target.kind == "commands":
            ok = (base / "pm-init.md").is_file()
        elif target.kind == "toml":
            ok = (base / "pm-init.toml").is_file()
        if ok:
            found.append(key)
    return found


def agent_hint(key: str) -> str:
    target = REGISTRY.get(key)
    return target.hint if target else ""


def install_skills_sh(
    project_root: Path,
    source: str = DEFAULT_SKILLS_SOURCE,
    timeout_sec: int = 180,
) -> tuple[bool, str]:
    """Non-interactive `npx skills add <source> -y` for skills.sh indexing + agents.

    Best-effort: missing Node/npx or network errors return (False, reason)
    and must not abort `pm init`.
    """
    project_root = project_root.resolve()
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        return False, "skipped (npx not found; install Node.js to enable skills.sh)"

    cmd = [npx, "--yes", "skills@latest", "add", source, "-y"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout_sec}s running: {' '.join(cmd)}"
    except OSError as exc:
        return False, f"failed to run npx: {exc}"

    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    tail = out[-400:].replace("\r", "") if out else ""
    if proc.returncode != 0:
        detail = tail or f"exit {proc.returncode}"
        return False, f"npx skills add failed: {detail}"
    return True, f"npx skills add {source} -y"
