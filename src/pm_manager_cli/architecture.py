"""Scan a project and write Mermaid architecture / flow diagrams under .pm/architecture/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.vue_detect import has_dep, is_vue_project, vue_hints

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
    ".output",
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


def _yaml_exclude_dirs(project_root: Path) -> set[str]:
    cfg = project_root / ".pm" / "config" / "project.yaml"
    extra: set[str] = set()
    if not cfg.is_file():
        return extra
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return extra
    m = re.search(r"exclude_dirs:\s*\[([^\]]*)\]", text)
    if not m:
        return extra
    return {x.strip() for x in m.group(1).split(",") if x.strip()}


def _file_sig(path: Path) -> str:
    st = path.stat()
    return f"{st.st_mtime_ns}:{st.st_size}"


def _iter_files(root: Path, suffixes: set[str], max_files: int = 400) -> list[Path]:
    out: list[Path] = []
    try:
        iterator = root.rglob("*")
    except OSError:
        return out
    for p in iterator:
        if len(out) >= max_files:
            break
        try:
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if not p.is_file():
                continue
            if p.suffix.lower() in suffixes:
                out.append(p)
        except OSError:
            continue
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
    if is_vue_project(root):
        for label in vue_hints(root).stacks:
            if label not in stacks:
                stacks.append(label)
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


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _scan_controller_files(root: Path) -> list[str]:
    """Return relative paths of route/controller files."""
    found: list[str] = []
    for p in _iter_files(root, {".java", ".kt"}, 300):
        text = _read(p, 40_000)
        if "@RestController" in text or "@Controller" in text:
            found.append(_rel(root, p))
        if len(found) >= 24:
            return found
    for p in _iter_files(root, {".ts", ".js", ".py"}, 200):
        text = _read(p, 30_000)
        if re.search(
            r"@(Get|Post|Put|Delete|Controller)\(|router\.(get|post)|APIRouter|@app\.(get|post)",
            text,
        ):
            found.append(_rel(root, p))
        if len(found) >= 16:
            break
    return found


def _scan_vue_route_files(root: Path) -> list[str]:
    """Page/router files for Vue SPAs. Empty when not a Vue repo."""
    if not is_vue_project(root):
        return []
    found: list[str] = []
    seen: set[str] = set()

    def add(rel: str) -> None:
        if rel in seen:
            return
        if (root / rel).is_file():
            seen.add(rel)
            found.append(rel)

    for rel in (
        "src/router/index.ts",
        "src/router/index.js",
        "src/router.ts",
        "src/router.js",
        "app/router/index.ts",
        "app/router/index.js",
    ):
        add(rel)
    for folder in ("src/pages", "src/views", "pages", "views", "app/pages"):
        d = root / folder
        if not d.is_dir():
            continue
        try:
            for p in sorted(d.rglob("*.vue")):
                add(_rel(root, p))
                if len(found) >= 16:
                    return found
        except OSError:
            continue
    return found


def _scan_controllers(root: Path) -> list[str]:
    return [Path(p).stem for p in _scan_controller_files(root)]


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


def _vue_request_flow_mmd(model: ProjectModel) -> str:
    has_router = has_dep(model.root, "vue-router") or bool(_scan_vue_route_files(model.root))
    has_pinia = has_dep(model.root, "pinia")
    page = "Page / View"
    for folder in ("src/pages", "src/views", "pages", "views"):
        if (model.root / folder).is_dir():
            page = folder.replace("src/", "")
            break
    lines = [
        "flowchart TD",
        f"  %% Request flow heuristic for {model.name} (Vue)",
        "  U([Browser])",
    ]
    if has_router:
        lines.append("  U --> R[Vue Router]")
        lines.append(f'  R --> P["{page}"]')
    else:
        lines.append(f'  U --> P["{page}"]')
    lines.append('  P --> C[Component]')
    if has_pinia:
        lines.append("  P --> S[Pinia Store]")
        lines.append("  S --> A[API client]")
        lines.append("  C --> A")
    else:
        lines.append("  C --> A[API client]")
    return "\n".join(lines) + "\n"


def _request_flow_mmd(model: ProjectModel) -> str:
    """Typical request flowchart."""
    if is_vue_project(model.root):
        return _vue_request_flow_mmd(model)
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
        "# 架构总览",
        "",
        f"> 生成时间: {now} (UTC)，由 `pm arch`  ",
        f"> 项目: **{model.name}**  ",
        f"> 技术栈: {', '.join(model.stacks) if model.stacks else 'unknown'}",
        "",
        "根据仓库布局的启发式图。可用 `/pm-arch` 复核后修订。定位请先读 `map.json` 或运行 `pm map`。",
        "",
        "## 检测摘要",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| 模块 | {', '.join(model.modules) if model.modules else '—'} |",
        f"| Docker 服务 | {', '.join(model.services) if model.services else '—'} |",
        f"| 控制器 | {', '.join(model.controllers[:12]) if model.controllers else '—'} |",
        f"| 外部依赖 | {', '.join(model.externals) if model.externals else '—'} |",
        "",
    ]
    if model.notes:
        lines.append("## 备注")
        lines.append("")
        for n in model.notes:
            lines.append(f"- {n}")
        lines.append("")

    titles = {
        "system-context.mmd": "系统上下文（C4 L1）",
        "service-dependencies.mmd": "服务 / 模块依赖",
        "layer.mmd": "分层架构",
        "request-flow.mmd": "请求流程",
        "deploy-flow.mmd": "部署 / 发布流程",
    }
    for fname, title in titles.items():
        body = diagrams.get(fname, "")
        if not body:
            continue
        lines += [
            f"## {title}",
            "",
            f"源文件: [`{fname}`](./{fname})",
            "",
            "```mermaid",
            body.rstrip(),
            "```",
            "",
        ]
    lines += [
        "## 本目录文件",
        "",
        "- `overview.md` — 本页",
        "- `map.json` — AI 导航地图（先读这个）",
        "- `tree.md` — 带注解目录树",
        "- `system-context.mmd` / `service-dependencies.mmd` / `layer.mmd` / `request-flow.mmd` / `deploy-flow.mmd`",
        "",
        "重新生成: `pm arch` 或 `/pm-arch`。查询: `pm map <关键词>`。",
        "",
    ]
    return "\n".join(lines)


def _vue_layer_mmd(model: ProjectModel) -> str:
    root = model.root
    src = root / "src"

    def dir_label(*candidates: str) -> str | None:
        for name in candidates:
            if (src / name).is_dir():
                return f"src/{name}"
            if (root / name).is_dir():
                return name
        return None

    pages = dir_label("pages", "views")
    components = dir_label("components")
    state = dir_label("composables", "stores")
    api = dir_label("api", "services")
    lines = [
        "flowchart TB",
        f"  %% Layered architecture for {model.name} (Vue)",
        "  subgraph pages [页面]",
        f'    Pages["{pages or "pages / views"}"]',
        "  end",
        "  subgraph components [组件]",
        f'    Components["{components or "components"}"]',
        "  end",
        "  subgraph state [状态 / 组合]",
        f'    State["{state or "composables / stores"}"]',
        "  end",
        "  subgraph api [接口]",
        f'    Api["{api or "api"}"]',
        "  end",
        "  pages --> components",
        "  pages --> state",
        "  components --> api",
        "  state --> api",
    ]
    return "\n".join(lines) + "\n"


def _layer_mmd(model: ProjectModel) -> str:
    if is_vue_project(model.root):
        return _vue_layer_mmd(model)
    ui = [m for m in model.modules if re.search(r"web|ui|front|client|app", m, re.I)]
    data = [e for e in model.externals if e in {"MySQL", "PostgreSQL", "MongoDB", "Database", "Prisma/DB", "Redis"}]
    app = [m for m in model.modules if m not in ui] or [model.name]
    lines = [
        "flowchart TB",
        f"  %% Layered architecture for {model.name}",
        "  subgraph ui [界面]",
    ]
    if ui:
        for n in ui[:6]:
            lines.append(f'    {_safe_id("ui_"+n)}["{n}"]')
    else:
        lines.append('    UI["Client / UI"]')
    lines += ["  end", "  subgraph app [应用]", ]
    for n in app[:8]:
        lines.append(f'    {_safe_id("app_"+n)}["{n}"]')
    lines += ["  end", "  subgraph data [数据]", ]
    if data:
        for e in data[:6]:
            lines.append(f'    {_safe_id("data_"+e)}[("{e}")]')
    else:
        lines.append('    DataUnknown[("数据存储 TBD")]')
    lines += ["  end"]
    others = [e for e in model.externals if e not in data]
    if others:
        lines.append("  subgraph ext [外部]")
        for e in others[:6]:
            lines.append(f'    {_safe_id("ext_"+e)}[("{e}")]')
        lines.append("  end")
    lines.append("  ui --> app")
    lines.append("  app --> data")
    if others:
        lines.append("  app --> ext")
    return "\n".join(lines) + "\n"


def _readme_excerpt(path: Path, limit: int = 160) -> str:
    if not path.is_file():
        return ""
    text = _read(path, 8_000)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip() and not p.lstrip().startswith("#")]
    if not paras:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        paras = lines[:1]
    excerpt = paras[0] if paras else ""
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 1] + "…"
    return excerpt


def _module_path(root: Path, name: str) -> str:
    if (root / name).is_dir():
        return name
    return "."


def _module_responsibility(root: Path, name: str) -> str:
    path = root / name if (root / name).is_dir() else root
    hint = _DIR_HINTS.get(name.lower(), "")
    excerpt = ""
    for readme in ("README.md", "readme.md", "README.zh-CN.md"):
        excerpt = _readme_excerpt(path / readme)
        if excerpt:
            break
    if hint and excerpt:
        return f"{hint}。{excerpt}"
    return hint or excerpt or "信息不足"


def _manifest_key_files(root: Path) -> list[dict[str, str]]:
    roles = [
        ("README.md", "项目说明"),
        ("README.zh-CN.md", "中文说明"),
        ("AGENTS.md", "Agent 说明"),
        ("pyproject.toml", "Python 包清单"),
        ("package.json", "Node 清单"),
        ("go.mod", "Go 模块"),
        ("Cargo.toml", "Rust 清单"),
        ("pom.xml", "Maven 清单"),
        ("Dockerfile", "容器构建"),
        ("docker-compose.yml", "编排"),
        ("src/app.py", "应用入口"),
        ("src/main.py", "应用入口"),
        ("src/__main__.py", "应用入口"),
        ("app.py", "应用入口"),
        ("main.py", "应用入口"),
        ("src/index.ts", "应用入口"),
        ("src/main.ts", "应用入口"),
        ("src/App.vue", "根组件"),
        ("src/app.vue", "根组件"),
        ("App.vue", "根组件"),
        ("index.html", "HTML 入口"),
        ("vite.config.ts", "Vite 配置"),
        ("vite.config.js", "Vite 配置"),
        ("nuxt.config.ts", "Nuxt 配置"),
        ("nuxt.config.js", "Nuxt 配置"),
        ("src/router/index.ts", "页面路由"),
        ("src/router/index.js", "页面路由"),
        ("src/main.rs", "应用入口"),
        ("cmd/main.go", "应用入口"),
    ]
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for rel, role in roles:
        p = root / rel
        if p.is_file() and rel not in seen:
            out.append({"path": rel, "role": role})
            seen.add(rel)
    for rel in _scan_vue_route_files(root):
        if rel not in seen:
            out.append({"path": rel, "role": "页面路由"})
            seen.add(rel)
    for rel in _scan_controller_files(root):
        if rel not in seen:
            out.append({"path": rel, "role": "路由 / 控制器"})
            seen.add(rel)
    return out[:32]


def _capability_entries(root: Path, model: ProjectModel, key_files: list[dict[str, str]]) -> list[dict]:
    cap: list[dict] = []
    marker_files = {
        "Java/Maven": "pom.xml",
        "Java/Gradle": "build.gradle",
        "Node.js": "package.json",
        "Python": "pyproject.toml",
        "Go": "go.mod",
        "Rust": "Cargo.toml",
        "Docker": "Dockerfile",
        "Docker Compose": "docker-compose.yml",
        "Spring Boot": "pom.xml",
        "Vue 3": "package.json",
        "Vue 2": "package.json",
        "Nuxt": "package.json",
        "Vite": "vite.config.ts",
    }
    for stack in model.stacks:
        rel = marker_files.get(stack, "")
        files = [rel] if rel and (root / rel).is_file() else []
        if stack == "Python" and not files and (root / "requirements.txt").is_file():
            files = ["requirements.txt"]
        if stack == "Java/Gradle" and not files:
            for n in ("build.gradle.kts", "settings.gradle"):
                if (root / n).is_file():
                    files = [n]
                    break
        if stack == "Vite" and not files:
            for n in ("vite.config.js", "vite.config.mts", "vite.config.mjs"):
                if (root / n).is_file():
                    files = [n]
                    break
        cap.append({"name": stack, "files": files})
    route_files = [k["path"] for k in key_files if k["role"] == "路由 / 控制器"]
    if route_files:
        cap.append({"name": "HTTP / 路由", "files": route_files[:12]})
    page_files = [k["path"] for k in key_files if k["role"] == "页面路由"]
    if page_files:
        cap.append({"name": "页面路由", "files": page_files[:12]})
    for ext in model.externals:
        cap.append({"name": ext, "files": []})
    return cap


def _git_hotspots(root: Path, limit: int = 8) -> list[str]:
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "log", "--since=90 days ago", "--name-only", "--pretty=format:"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=8,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    counts: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        rel = line.strip().replace("\\", "/")
        if not rel or rel.startswith("."):
            continue
        if any(part in SKIP_DIRS for part in rel.split("/")):
            continue
        if Path(rel).suffix.lower() not in _MAP_SUFFIXES:
            continue
        counts[rel] = counts.get(rel, 0) + 1
    ranked = sorted(counts, key=lambda k: (-counts[k], k))
    return ranked[:limit]


def _hotspot_entries(changed: list[str], git_extra: list[str]) -> list[dict[str, str]]:
    src_ext = {".py", ".java", ".kt", ".ts", ".js", ".go", ".rs"}
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for rel in changed:
        if Path(rel).suffix.lower() not in src_ext:
            continue
        if rel in seen:
            continue
        out.append({"path": rel, "reason": "本轮变更"})
        seen.add(rel)
        if len(out) >= 16:
            return out
    for rel in git_extra:
        if rel in seen:
            continue
        out.append({"path": rel, "reason": "近 90 日频繁修改"})
        seen.add(rel)
        if len(out) >= 16:
            break
    return out


def _build_lookup(modules: list[dict], key_files: list[dict], capabilities: list[dict]) -> dict:
    by_module = {m["name"]: m.get("path") or m["name"] for m in modules}
    by_suffix: dict[str, list[str]] = {}
    for kf in key_files:
        suf = Path(kf["path"]).suffix.lower()
        if not suf:
            continue
        by_suffix.setdefault(suf, []).append(kf["path"])
    for cap in capabilities:
        for f in cap.get("files") or []:
            suf = Path(f).suffix.lower()
            if suf:
                by_suffix.setdefault(suf, []).append(f)
    for suf, paths in list(by_suffix.items()):
        by_suffix[suf] = list(dict.fromkeys(paths))[:20]
    return {"by_module": by_module, "by_suffix": by_suffix}


_COMMENT_PREFIXES = ("#", "//", "/*", "*", "--")
_ENTRY_ROLES = {"应用入口", "路由 / 控制器"}
_BULKY_LINES = 400
_BULKY_BYTES = 64 * 1024


def _file_flags(root: Path, rel: str, *, entry: bool, hotspot: bool) -> tuple[list[str], list[str]]:
    flags: list[str] = []
    reasons: list[str] = []
    if entry:
        flags.append("entry")
        reasons.append("核心入口 / 路由")
    if hotspot:
        flags.append("hotspot")
        reasons.append("本轮或近 90 日高频修改")
    path = root / rel
    if not path.is_file():
        return flags, reasons
    try:
        size = path.stat().st_size
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return flags, reasons
    lines = text.splitlines()
    if size >= _BULKY_BYTES or len(lines) >= _BULKY_LINES:
        flags.append("bulky")
        reasons.append(f"体积 {size} 字节 / {len(lines)} 行")
    sample = lines[:80]
    comments = 0
    codeish = 0
    for line in sample:
        s = line.strip()
        if not s:
            continue
        if s.startswith(_COMMENT_PREFIXES):
            comments += 1
        else:
            codeish += 1
    if codeish >= 12 and comments < 2:
        flags.append("uncommented")
        reasons.append("抽样前 80 行几乎无注释")
    return flags, reasons


def _risk_file_entries(
    root: Path,
    key_files: list[dict[str, str]],
    hotspots: list[dict[str, str]],
) -> list[dict]:
    entry_paths = {
        k["path"]
        for k in key_files
        if k.get("role") in _ENTRY_ROLES or "入口" in str(k.get("role") or "")
    }
    hot_paths = {
        (h.get("path") if isinstance(h, dict) else str(h))
        for h in hotspots
    }
    seen: set[str] = set()
    out: list[dict] = []
    for rel in list(entry_paths) + [p for p in hot_paths if p]:
        rel = str(rel).replace("\\", "/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        flags, reasons = _file_flags(
            root, rel, entry=rel in entry_paths, hotspot=rel in hot_paths
        )
        if not flags:
            continue
        out.append({"path": rel, "flags": flags, "reasons": reasons})
        if len(out) >= 24:
            break
    return out


def build_nav_map(
    root: Path,
    model: ProjectModel,
    hashes: dict[str, str],
    changed: list[str],
    notes: list[str],
) -> dict:
    modules = []
    for name in model.modules:
        modules.append(
            {
                "name": name,
                "path": _module_path(root, name),
                "responsibility": _module_responsibility(root, name),
            }
        )
    key_files = _manifest_key_files(root)
    capabilities = _capability_entries(root, model, key_files)
    hotspots = _hotspot_entries(changed, _git_hotspots(root))
    risk_files = _risk_file_entries(root, key_files, hotspots)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "generated_at": now,
        "project": model.name,
        "stacks": model.stacks,
        "modules": modules,
        "key_files": key_files,
        "capabilities": capabilities,
        "hotspots": hotspots,
        "risk_files": risk_files,
        "lookup": _build_lookup(modules, key_files, capabilities),
        "excludes_applied": sorted(SKIP_DIRS),
        "file_hashes": hashes,
        "changed_paths": changed,
        "notes": notes,
    }


def load_map(project_root: Path) -> dict | None:
    path = project_root.resolve() / ".pm" / "architecture" / "map.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def query_map(data: dict, query: str = "") -> list[dict[str, str]]:
    """Match modules, capabilities, key files, hotspots. Empty query → summary rows."""
    rows: list[dict[str, str]] = []
    q = (query or "").strip().lower()

    def add(kind: str, name: str, detail: str) -> None:
        rows.append({"kind": kind, "name": name, "detail": detail})

    if not q:
        for m in data.get("modules") or []:
            if isinstance(m, dict):
                add("模块", m.get("name", ""), f"{m.get('path', '')} — {m.get('responsibility', '')}")
        for kf in (data.get("key_files") or [])[:12]:
            if isinstance(kf, dict):
                add("入口", kf.get("path", ""), kf.get("role", ""))
            elif isinstance(kf, str):
                add("入口", kf, "")
        for rf in (data.get("risk_files") or [])[:8]:
            if isinstance(rf, dict):
                flags = ",".join(rf.get("flags") or [])
                add("高危", rf.get("path", ""), flags or "信息不足")
        return rows

    for m in data.get("modules") or []:
        if not isinstance(m, dict):
            continue
        blob = " ".join(str(m.get(k, "")) for k in ("name", "path", "responsibility")).lower()
        if q in blob:
            add("模块", m.get("name", ""), f"{m.get('path', '')} — {m.get('responsibility', '')}")
    for cap in data.get("capabilities") or []:
        if isinstance(cap, dict):
            name = str(cap.get("name", ""))
            files = ", ".join(cap.get("files") or [])
            if q in name.lower() or q in files.lower():
                add("能力", name, files or "信息不足")
        elif isinstance(cap, str) and q in cap.lower():
            add("能力", cap, "")
    for kf in data.get("key_files") or []:
        if isinstance(kf, dict):
            path = str(kf.get("path", ""))
            role = str(kf.get("role", ""))
            if q in path.lower() or q in role.lower():
                add("文件", path, role)
        elif isinstance(kf, str) and q in kf.lower():
            add("文件", kf, "")
    for h in data.get("hotspots") or []:
        if isinstance(h, dict):
            path = str(h.get("path", ""))
            if q in path.lower():
                add("热点", path, str(h.get("reason", "")))
        elif isinstance(h, str) and q in h.lower():
            add("热点", h, "")
    for rf in data.get("risk_files") or []:
        if not isinstance(rf, dict):
            continue
        path = str(rf.get("path", ""))
        flags = ",".join(rf.get("flags") or [])
        blob = f"{path} {flags} {' '.join(rf.get('reasons') or [])}".lower()
        if q in blob or q in {"risk", "高危", "危险"}:
            add("高危", path, flags or "信息不足")
    return rows


def _model_from_map(root: Path, data: dict) -> ProjectModel:
    model = ProjectModel(name=str(data.get("project") or root.name), root=root)
    stacks = data.get("stacks")
    if isinstance(stacks, list) and stacks:
        model.stacks = [str(s) for s in stacks]
    else:
        caps = data.get("capabilities") or []
        model.stacks = [
            str(c.get("name") if isinstance(c, dict) else c)
            for c in caps
            if not isinstance(c, dict) or c.get("name")
        ][:8]
    mods = data.get("modules") or []
    model.modules = [
        str(m.get("name") if isinstance(m, dict) else m) for m in mods
    ]
    model.notes = [str(n) for n in (data.get("notes") or [])]
    return model


_MAP_SUFFIXES = {
    ".py",
    ".java",
    ".kt",
    ".ts",
    ".js",
    ".go",
    ".rs",
    ".md",
    ".yml",
    ".yaml",
    ".xml",
    ".json",
    ".kts",
    ".gradle",
    ".vue",
}


_DIR_HINTS = {
    "src": "业务源码",
    "app": "应用入口",
    "apps": "应用集合",
    "lib": "库代码",
    "cmd": "命令入口",
    "docs": "文档",
    "test": "测试",
    "tests": "测试",
    "scripts": "脚本",
    "config": "配置",
    "configs": "配置",
    "deploy": "部署",
    "infra": "基础设施",
    "internal": "内部包",
    "pkg": "包",
    "web": "Web 前端",
    "api": "接口层",
    "server": "服务端",
    "client": "客户端",
    "components": "Vue 组件",
    "views": "页面视图",
    "pages": "页面路由",
    "composables": "组合式函数",
    "stores": "状态仓库",
}

_FILE_HINTS = {
    "readme.md": "项目说明",
    "agents.md": "Agent 说明",
    "pyproject.toml": "Python 包清单",
    "package.json": "Node 清单",
    "go.mod": "Go 模块",
    "cargo.toml": "Rust 清单",
    "pom.xml": "Maven 清单",
    "dockerfile": "容器构建",
    "docker-compose.yml": "编排",
    "docker-compose.yaml": "编排",
    "app.vue": "根组件",
    "vite.config.ts": "Vite 配置",
    "vite.config.js": "Vite 配置",
    "nuxt.config.ts": "Nuxt 配置",
}

_EXT_HINTS = {
    ".py": "Python 源文件",
    ".java": "Java 源文件",
    ".kt": "Kotlin 源文件",
    ".ts": "TypeScript 源文件",
    ".js": "JavaScript 源文件",
    ".go": "Go 源文件",
    ".rs": "Rust 源文件",
    ".md": "Markdown 文档",
    ".yml": "YAML 配置",
    ".yaml": "YAML 配置",
    ".json": "JSON",
    ".xml": "XML",
    ".vue": "Vue 单文件组件",
}


def _entry_hint(name: str, is_dir: bool) -> str:
    key = name.lower()
    if is_dir:
        return _DIR_HINTS.get(key, "")
    return _FILE_HINTS.get(key, "") or _EXT_HINTS.get(Path(name).suffix.lower(), "")


def write_annotated_tree(
    project_root: Path,
    dest: Path,
    *,
    max_entries: int = 400,
    max_depth: int = 4,
) -> Path:
    """Write a skipped-ignore annotated directory tree. Does not walk SKIP_DIRS."""
    root = project_root.resolve()
    lines = [
        "# 带注解目录树",
        "",
        f"项目: `{root.name}`",
        f"生成: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "说明: 已跳过 `node_modules`、构建产物、`.git`、`.pm` 等忽略目录。标注为启发式，供导航。",
        "",
        "```",
        f"{root.name}/",
    ]
    count = 0

    def walk(dir_path: Path, prefix: str, depth: int) -> None:
        nonlocal count
        if count >= max_entries or depth > max_depth:
            return
        try:
            children = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        visible: list[Path] = []
        for child in children:
            if child.name in SKIP_DIRS:
                continue
            visible.append(child)
        for i, child in enumerate(visible):
            if count >= max_entries:
                lines.append(f"{prefix}…")
                return
            last = i == len(visible) - 1
            branch = "└── " if last else "├── "
            child_prefix = prefix + ("    " if last else "│   ")
            try:
                is_dir = child.is_dir()
            except OSError:
                continue
            hint = _entry_hint(child.name, is_dir)
            label = f"{child.name}/" if is_dir else child.name
            suffix = f"  — {hint}" if hint else ""
            lines.append(f"{prefix}{branch}{label}{suffix}")
            count += 1
            if is_dir:
                walk(child, child_prefix, depth + 1)

    walk(root, "", 1)
    lines += ["```", ""]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def _collect_file_hashes(root: Path) -> tuple[dict[str, str], list[str]]:
    """Return (relpath→sig, notes for unreadable files)."""
    hashes: dict[str, str] = {}
    notes: list[str] = []
    for p in _iter_files(root, _MAP_SUFFIXES, max_files=4000):
        try:
            rel = p.relative_to(root).as_posix()
            hashes[rel] = _file_sig(p)
        except OSError as exc:
            notes.append(f"skip unreadable: {p} ({exc})")
    return hashes, notes


def write_architecture(project_root: Path) -> tuple[Path, ProjectModel]:
    """Analyze project and write diagrams under `.pm/architecture/`. Returns (arch_dir, model)."""
    project_root = project_root.resolve()
    pm = project_root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{project_root}）；请先运行 `pm init`")

    extra = _yaml_exclude_dirs(project_root)
    added = extra - SKIP_DIRS
    SKIP_DIRS.update(added)
    try:
        old_hashes: dict[str, str] = {}
        arch = pm / "architecture"
        map_path = arch / "map.json"
        if map_path.is_file():
            try:
                old = json.loads(map_path.read_text(encoding="utf-8"))
                old_hashes = old.get("file_hashes") or {}
            except (OSError, json.JSONDecodeError):
                old_hashes = {}

        hashes, read_notes = _collect_file_hashes(project_root)
        changed = sorted(p for p, sig in hashes.items() if old_hashes.get(p) != sig)
        if old_hashes:
            changed += sorted(p for p in old_hashes if p not in hashes)
            changed = sorted(set(changed))

        arch.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        old_map = None
        if map_path.is_file():
            try:
                loaded = json.loads(map_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and loaded.get("modules"):
                    old_map = loaded
            except (OSError, json.JSONDecodeError):
                old_map = None

        if old_hashes and not changed and old_map:
            notes = list(old_map.get("notes") or [])
            notes.extend(read_notes)
            notes.append("incremental: 0 path(s) changed; reused map")
            old_map["generated_at"] = now
            old_map["file_hashes"] = hashes
            old_map["changed_paths"] = []
            old_map["notes"] = notes
            map_path.write_text(
                json.dumps(old_map, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            model = _model_from_map(project_root, old_map)
            model.notes = notes
            return arch, model

        model = analyze_project(project_root)
        model.notes.extend(read_notes)
        if old_hashes:
            model.notes.append(f"incremental: {len(changed)} path(s) changed")
        else:
            model.notes.append("full scan")

        diagrams = {
            "system-context.mmd": _system_context_mmd(model),
            "service-dependencies.mmd": _service_deps_mmd(model),
            "layer.mmd": _layer_mmd(model),
            "request-flow.mmd": _request_flow_mmd(model),
            "deploy-flow.mmd": _deploy_flow_mmd(model),
        }
        for name, body in diagrams.items():
            (arch / name).write_text(body, encoding="utf-8")
        (arch / "overview.md").write_text(_overview_md(model, diagrams), encoding="utf-8")

        meta = {
            "generated_at": now,
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

        changed_out = changed if old_hashes else sorted(hashes)
        nav_map = build_nav_map(
            project_root, model, hashes, changed_out, model.notes
        )
        map_path.write_text(
            json.dumps(nav_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        write_annotated_tree(project_root, arch / "tree.md")
        return arch, model
    finally:
        SKIP_DIRS.difference_update(added)
