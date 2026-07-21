"""Scan a project and write Mermaid architecture / flow diagrams under .pm/architecture/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".pm",
    ".svn",
    ".hg",
    "node_modules",
    "target",
    "build",
    "dist",
    "out",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    "coverage",
    "vendor",
    ".next",
    ".nuxt",
    "bin",
    "obj",
}


@dataclass
class ProjectModel:
    name: str
    root: Path
    stacks: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    controllers: list[str] = field(default_factory=list)
    externals: list[str] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _safe_id(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())
    if not s:
        s = "node"
    if s[0].isdigit():
        s = f"n_{s}"
    return s[:48]


def _read(path: Path, limit: int = 200_000) -> str:
    try:
        data = path.read_bytes()[:limit]
        # strip UTF-8 BOM so ^anchors still match first line
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _iter_files(root: Path, suffixes: set[str], max_files: int = 400) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if len(out) >= max_files:
            break
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in suffixes:
            out.append(p)
    return out


def _detect_stacks(root: Path) -> list[str]:
    stacks: list[str] = []
    markers = [
        ("pom.xml", "Java/Maven"),
        ("build.gradle", "Java/Gradle"),
        ("build.gradle.kts", "Java/Gradle"),
        ("settings.gradle", "Java/Gradle"),
        ("settings.gradle.kts", "Java/Gradle"),
        ("package.json", "Node.js"),
        ("go.mod", "Go"),
        ("Cargo.toml", "Rust"),
        ("pyproject.toml", "Python"),
        ("requirements.txt", "Python"),
        ("Gemfile", "Ruby"),
        ("composer.json", "PHP"),
        ("Dockerfile", "Docker"),
        ("docker-compose.yml", "Docker Compose"),
        ("docker-compose.yaml", "Docker Compose"),
        ("Chart.yaml", "Helm"),
    ]
    for name, label in markers:
        if (root / name).is_file():
            stacks.append(label)
    # Spring Boot hint
    for p in _iter_files(root, {".xml", ".gradle", ".kts", ".yml", ".yaml"}, 80):
        text = _read(p, 80_000)
        if "spring-boot" in text.lower() or "springframework" in text.lower():
            if "Spring Boot" not in stacks:
                stacks.append("Spring Boot")
            break
    return stacks


def _maven_modules(root: Path) -> list[str]:
    pom = root / "pom.xml"
    if not pom.is_file():
        return []
    text = _read(pom)
    mods = re.findall(r"<module>\s*([^<]+?)\s*</module>", text)
    return [m.strip().replace("\\", "/").split("/")[-1] for m in mods if m.strip()]


def _gradle_modules(root: Path) -> list[str]:
    for name in ("settings.gradle", "settings.gradle.kts"):
        p = root / name
        if not p.is_file():
            continue
        text = _read(p)
        mods = re.findall(r"""include\s*\(?\s*['"]([^'"]+)['"]""", text)
        cleaned = []
        for m in mods:
            cleaned.append(m.strip(":").split(":")[-1])
        return cleaned
    return []


def _docker_services(root: Path) -> list[str]:
    names: list[str] = []
    for fname in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        p = root / fname
        if not p.is_file():
            continue
        text = _read(p)
        # naive: top-level keys under services:
        in_services = False
        for line in text.splitlines():
            if re.match(r"^services:\s*$", line):
                in_services = True
                continue
            if in_services:
                if re.match(r"^[A-Za-z]", line) and not line.startswith(" "):
                    break
                m = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
                if m:
                    names.append(m.group(1))
    return names


def _yaml_externals(root: Path) -> list[str]:
    found: set[str] = set()
    patterns = [
        (r"redis", "Redis"),
        (r"mysql|mariadb|jdbc:mysql", "MySQL"),
        (r"postgres|jdbc:postgresql", "PostgreSQL"),
        (r"mongodb|mongo", "MongoDB"),
        (r"rabbitmq|amqp", "RabbitMQ"),
        (r"kafka", "Kafka"),
        (r"nacos", "Nacos"),
        (r"eureka", "Eureka"),
        (r"elasticsearch|elastic", "Elasticsearch"),
        (r"minio|s3\.amazonaws|oss\.", "Object Storage"),
        (r"datasource", "Database"),
    ]
    for p in _iter_files(root, {".yml", ".yaml", ".properties", ".env"}, 120):
        if "application" not in p.name.lower() and p.suffix not in {".yml", ".yaml", ".properties"}:
            if p.name not in {".env", "application.properties"}:
                continue
        text = _read(p, 60_000).lower()
        for pat, label in patterns:
            if re.search(pat, text):
                found.add(label)
    return sorted(found)


def _package_json_externals(root: Path) -> list[str]:
    p = root / "package.json"
    if not p.is_file():
        return []
    text = _read(p).lower()
    mapping = [
        ("express", "HTTP API"),
        ("fastify", "HTTP API"),
        ("nestjs", "NestJS"),
        ("next", "Next.js"),
        ("react", "React UI"),
        ("vue", "Vue UI"),
        ("prisma", "Prisma/DB"),
        ("mongoose", "MongoDB"),
        ("ioredis", "Redis"),
        ("amqplib", "RabbitMQ"),
        ("kafkajs", "Kafka"),
    ]
    return [label for key, label in mapping if key in text]


def _scan_controllers(root: Path) -> list[str]:
    names: list[str] = []
    for p in _iter_files(root, {".java", ".kt"}, 300):
        text = _read(p, 40_000)
        if "@RestController" in text or "@Controller" in text:
            names.append(p.stem)
        if len(names) >= 24:
            break
    if names:
        return names
    # Node / Python route hints
    for p in _iter_files(root, {".ts", ".js", ".py"}, 200):
        text = _read(p, 30_000)
        if re.search(r"@(Get|Post|Put|Delete|Controller)\(|router\.(get|post)|APIRouter|@app\.(get|post)", text):
            names.append(p.stem)
        if len(names) >= 16:
            break
    return names


def _feign_clients(root: Path) -> list[str]:
    names: list[str] = []
    for p in _iter_files(root, {".java", ".kt"}, 200):
        text = _read(p, 40_000)
        if "@FeignClient" in text:
            names.append(p.stem)
        if len(names) >= 16:
            break
    return names


def _dir_modules(root: Path) -> list[str]:
    """Fallback: top-level dirs that look like services/apps."""
    mods: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS or child.name.startswith("."):
            continue
        markers = [
            child / "pom.xml",
            child / "build.gradle",
            child / "package.json",
            child / "go.mod",
            child / "src",
            child / "Dockerfile",
        ]
        if any(m.exists() for m in markers):
            mods.append(child.name)
    return mods[:20]


def analyze_project(project_root: Path) -> ProjectModel:
    root = project_root.resolve()
    model = ProjectModel(name=root.name, root=root)
    model.stacks = _detect_stacks(root)
    model.modules = _maven_modules(root) or _gradle_modules(root) or _dir_modules(root)
    model.services = _docker_services(root)
    model.controllers = _scan_controllers(root)
    feign = _feign_clients(root)
    if feign:
        model.notes.append(f"Feign clients: {', '.join(feign[:8])}")
    externals = set(_yaml_externals(root)) | set(_package_json_externals(root))
    infra_alias = {
        "redis": "Redis",
        "mysql": "MySQL",
        "mariadb": "MySQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "rabbit": "RabbitMQ",
        "rabbitmq": "RabbitMQ",
        "kafka": "Kafka",
        "nacos": "Nacos",
        "elasticsearch": "Elasticsearch",
        "es": "Elasticsearch",
    }
    if model.services:
        for s in model.services:
            low = s.lower()
            mapped = None
            for key, label in infra_alias.items():
                if key in low:
                    mapped = label
                    break
            if mapped:
                externals.add(mapped)
    # Drop generic Database if a concrete DB exists
    concrete_db = {"MySQL", "PostgreSQL", "MongoDB", "Prisma/DB"}
    if externals & concrete_db:
        externals.discard("Database")
    model.externals = sorted(externals)
    model.actors = ["User", "Operator"]
    if not model.modules and not model.services:
        model.modules = [model.name]
        model.notes.append("No multi-module layout detected; using project root as single module.")
    if not model.stacks:
        model.stacks = ["Generic"]
        model.notes.append("Stack markers not found; diagrams are structural heuristics.")
    return model


def _system_context_mmd(model: ProjectModel) -> str:
    lines = [
        "flowchart TB",
        f"  %% System context for {model.name}",
    ]
    for actor in model.actors:
        lines.append(f"  {_safe_id(actor)}([{actor}])")
    system = _safe_id(model.name)
    stack_note = ", ".join(model.stacks[:3])
    lines.append(f'  {system}["{model.name}\\n({stack_note})"]')
    for actor in model.actors:
        lines.append(f"  {_safe_id(actor)} --> {system}")
    for ext in model.externals[:12]:
        eid = _safe_id(ext)
        lines.append(f'  {eid}[("{ext}")]')
        lines.append(f"  {system} --> {eid}")
    if not model.externals:
        lines.append('  ExtUnknown[("External systems TBD")]')
        lines.append(f"  {system} -.-> ExtUnknown")
    return "\n".join(lines) + "\n"


def _service_deps_mmd(model: ProjectModel) -> str:
    lines = [
        "flowchart LR",
        f"  %% Service / module dependencies for {model.name}",
    ]
    nodes = model.modules[:] if model.modules else [model.name]
    # Prefer docker app services if present and more descriptive
    app_services = [
        s
        for s in model.services
        if not any(x in s.lower() for x in ("redis", "mysql", "postgres", "mongo", "rabbit", "kafka", "nacos"))
    ]
    if app_services and len(app_services) >= len(nodes):
        nodes = app_services

    for n in nodes[:16]:
        lines.append(f'  {_safe_id(n)}["{n}"]')

    # Wire sequential + hub: first module as gateway-ish if many
    if len(nodes) == 1:
        only = _safe_id(nodes[0])
        for ext in model.externals[:8]:
            lines.append(f'  {_safe_id(ext)}[("{ext}")]')
            lines.append(f"  {only} --> {_safe_id(ext)}")
    else:
        hub = _safe_id(nodes[0])
        for n in nodes[1:]:
            lines.append(f"  {hub} --> {_safe_id(n)}")
        # Also chain neighbors for readability
        for a, b in zip(nodes[1:], nodes[2:]):
            lines.append(f"  {_safe_id(a)} -.-> {_safe_id(b)}")
        for ext in model.externals[:8]:
            lines.append(f'  {_safe_id(ext)}[("{ext}")]')
            lines.append(f"  {_safe_id(nodes[-1])} --> {_safe_id(ext)}")
    return "\n".join(lines) + "\n"


def _request_flow_mmd(model: ProjectModel) -> str:
    """Typical request flowchart."""
    ctrl = model.controllers[0] if model.controllers else "Controller"
    mod = model.modules[0] if model.modules else model.name
    db = next(
        (e for e in model.externals if e in {"MySQL", "PostgreSQL", "MongoDB", "Database", "Prisma/DB"}),
        model.externals[0] if model.externals else "Data store",
    )
    cache = next((e for e in model.externals if e == "Redis"), None)
    lines = [
        "flowchart TD",
        f"  %% Request flow heuristic for {model.name}",
        "  U([Client / User]) --> G[API Gateway / Ingress]",
        f'  G --> C["{ctrl}"]',
        f'  C --> S["{mod} Service"]',
    ]
    if cache:
        lines.append(f'  S --> R["{cache}"]')
        lines.append(f'  S --> D["{db}"]')
        lines.append("  R -.->|miss| D")
    else:
        lines.append(f'  S --> D["{db}"]')
    lines += [
        "  D --> S",
        "  S --> C",
        "  C --> U",
    ]
    if len(model.controllers) > 1:
        lines.append(f"  %% Other controllers: {', '.join(model.controllers[1:6])}")
    return "\n".join(lines) + "\n"


def _deploy_flow_mmd(model: ProjectModel) -> str:
    has_ci = any(
        (model.root / p).exists()
        for p in (
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            "azure-pipelines.yml",
            ".circleci",
        )
    )
    has_docker = (model.root / "Dockerfile").is_file() or "Docker" in model.stacks
    lines = [
        "flowchart LR",
        f"  %% Deploy / release flow for {model.name}",
        "  Dev[Developer] --> VCS[Git]",
    ]
    if has_ci:
        lines.append("  VCS --> CI[CI Pipeline]")
    else:
        lines.append("  VCS --> CI[Build (local/CI TBD)]")
    lines.append("  CI --> Test[Test]")
    if has_docker:
        lines.append("  Test --> Image[Container Image]")
        lines.append("  Image --> Deploy[Deploy]")
    else:
        lines.append("  Test --> Artifact[Build Artifact]")
        lines.append("  Artifact --> Deploy[Deploy]")
    lines.append("  Deploy --> Env[Runtime Env]")
    return "\n".join(lines) + "\n"


def _overview_md(model: ProjectModel, diagrams: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Architecture overview",
        "",
        f"> Generated: {now} (UTC) by `pm arch`  ",
        f"> Project: **{model.name}**  ",
        f"> Stack: {', '.join(model.stacks) if model.stacks else 'unknown'}",
        "",
        "Heuristic diagrams from repository layout. Refine with `/pm-arch` (agent) after review.",
        "",
        "## Detected summary",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Modules | {', '.join(model.modules) if model.modules else '—'} |",
        f"| Docker services | {', '.join(model.services) if model.services else '—'} |",
        f"| Controllers | {', '.join(model.controllers[:12]) if model.controllers else '—'} |",
        f"| Externals | {', '.join(model.externals) if model.externals else '—'} |",
        "",
    ]
    if model.notes:
        lines.append("## Notes")
        lines.append("")
        for n in model.notes:
            lines.append(f"- {n}")
        lines.append("")

    titles = {
        "system-context.mmd": "System context (C4 L1 style)",
        "service-dependencies.mmd": "Service / module dependencies",
        "request-flow.mmd": "Request flowchart",
        "deploy-flow.mmd": "Deploy / release flowchart",
    }
    for fname, title in titles.items():
        body = diagrams.get(fname, "")
        lines += [
            f"## {title}",
            "",
            f"Source: [`{fname}`](./{fname})",
            "",
            "```mermaid",
            body.rstrip(),
            "```",
            "",
        ]
    lines += [
        "## Files",
        "",
        "- `overview.md` — this page",
        "- `system-context.mmd`",
        "- `service-dependencies.mmd`",
        "- `request-flow.mmd`",
        "- `deploy-flow.mmd`",
        "",
        "Regenerate: `pm arch` or `/pm-arch`.",
        "",
    ]
    return "\n".join(lines)


def write_architecture(project_root: Path) -> tuple[Path, ProjectModel]:
    """Analyze project and write diagrams under `.pm/architecture/`. Returns (arch_dir, model)."""
    project_root = project_root.resolve()
    pm = project_root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"Missing .pm/ under {project_root}; run `pm init` first")

    model = analyze_project(project_root)
    arch = pm / "architecture"
    arch.mkdir(parents=True, exist_ok=True)

    diagrams = {
        "system-context.mmd": _system_context_mmd(model),
        "service-dependencies.mmd": _service_deps_mmd(model),
        "request-flow.mmd": _request_flow_mmd(model),
        "deploy-flow.mmd": _deploy_flow_mmd(model),
    }
    for name, body in diagrams.items():
        (arch / name).write_text(body, encoding="utf-8")
    (arch / "overview.md").write_text(_overview_md(model, diagrams), encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": model.name,
        "stacks": model.stacks,
        "modules": model.modules,
        "services": model.services,
        "controllers": model.controllers,
        "externals": model.externals,
        "notes": model.notes,
    }
    (arch / "scan.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return arch, model
