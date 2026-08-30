import json
import shutil
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from pm_manager_cli.architecture import write_architecture
from pm_manager_cli.checkup import run_checkup
from pm_manager_cli.cli import app
from pm_manager_cli.review_engine import heuristic_findings
from pm_manager_cli.speckit import infer_project_type
from pm_manager_cli.test_assist import find_test_gaps, suggested_test_path

runner = CliRunner()
NPX = Path(__file__).resolve().parents[1] / "packages" / "npx-cli" / "bin" / "pm-manager.mjs"


def _vue_tree(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    pkg = {
        "name": "demo-vue",
        "dependencies": {
            "vue": "^3.4.21",
            "vue-router": "^4.3.0",
            "pinia": "^2.1.7",
        },
        "devDependencies": {
            "vite": "^5.2.0",
            "vitest": "^1.5.0",
        },
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    (tmp_path / "vite.config.ts").write_text("export default {}\n", encoding="utf-8")
    (tmp_path / "index.html").write_text("<div id='app'></div>\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.vue").write_text("<template><div /></template>\n", encoding="utf-8")
    (src / "main.ts").write_text("createApp(App).mount('#app')\n", encoding="utf-8")
    (src / "router").mkdir()
    (src / "router" / "index.ts").write_text("export const router = {}\n", encoding="utf-8")
    (src / "views").mkdir()
    (src / "views" / "Home.vue").write_text("<template>home</template>\n", encoding="utf-8")
    return tmp_path


def test_empty_package_json_still_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    assert infer_project_type(tmp_path) == "node"


def test_react_package_json_is_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^18.0.0"}}),
        encoding="utf-8",
    )
    assert infer_project_type(tmp_path) == "node"


def test_vue_deps_infer_type_vue(tmp_path: Path) -> None:
    _vue_tree(tmp_path)
    assert infer_project_type(tmp_path) == "vue"


def test_non_vue_arch_keeps_gateway(tmp_path: Path) -> None:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(tmp_path), "--scaffold-only"]).exit_code == 0
    arch, _ = write_architecture(tmp_path)
    flow = (arch / "request-flow.mmd").read_text(encoding="utf-8")
    assert "API Gateway" in flow
    assert "Vue Router" not in flow


def test_vue_init_seeds_frontend_defaults(tmp_path: Path) -> None:
    root = _vue_tree(tmp_path)
    result = runner.invoke(app, ["init", str(root), "--scaffold-only"])
    assert result.exit_code == 0, result.output
    text = (root / ".pm" / "config" / "project.yaml").read_text(encoding="utf-8")
    assert "type: vue" in text
    assert "runtime: vue3" in text
    assert "build: vite" in text
    assert "database: false" in text
    assert "operations: false" in text
    assert "cost: false" in text
    assert "DOC-trouble" not in text
    assert ".nuxt" in text
    assert "profile: frontend" in text


def test_vue_arch_map_and_request_flow(tmp_path: Path) -> None:
    root = _vue_tree(tmp_path)
    assert runner.invoke(app, ["init", str(root), "--scaffold-only"]).exit_code == 0
    arch, model = write_architecture(root)
    data = json.loads((arch / "map.json").read_text(encoding="utf-8"))
    hashes = " ".join(data.get("file_hashes", {}))
    assert "App.vue" in hashes
    assert "Home.vue" in hashes
    flow = (arch / "request-flow.mmd").read_text(encoding="utf-8")
    assert "API Gateway" not in flow
    assert "Vue Router" in flow
    assert any("Vue 3" in s or s == "Vue 3" for s in model.stacks)
    layer = (arch / "layer.mmd").read_text(encoding="utf-8")
    assert "components" in layer.lower() or "页面" in layer
    roles = [k.get("role") for k in data.get("key_files") or [] if isinstance(k, dict)]
    assert "页面路由" in roles


def test_vue_checkup_and_test_assist_see_sfc(tmp_path: Path) -> None:
    root = _vue_tree(tmp_path)
    assert runner.invoke(app, ["init", str(root), "--scaffold-only"]).exit_code == 0
    write_architecture(root)
    run_checkup(root)
    from pm_manager_cli.test_assist import write_test_gaps

    gaps = find_test_gaps(root)
    paths = [str(g["path"]) for g in gaps]
    assert any(p.endswith(".vue") for p in paths)
    assert suggested_test_path("src/App.vue").endswith("App.spec.ts")
    write_test_gaps(root)
    report = (root / ".pm" / "state" / "test-gaps.md").read_text(encoding="utf-8")
    assert "Vitest" in report


def test_vue_review_heuristics(tmp_path: Path) -> None:
    blob = """diff --git a/src/App.vue b/src/App.vue
--- a/src/App.vue
+++ b/src/App.vue
@@ -1,3 +1,5 @@
 <template>
-  <div />
+  <div v-html="raw"></div>
+  <li v-for="item in items">{{ item }}</li>
 </template>
"""
    rows = heuristic_findings(tmp_path, blob)
    summaries = [r.summary for r in rows]
    assert any("v-html" in s for s in summaries)
    assert any("key" in s for s in summaries)


def test_npx_init_seeds_vue(tmp_path: Path) -> None:
    if shutil.which("node") is None:
        return
    root = _vue_tree(tmp_path)
    proc = subprocess.run(
        ["node", str(NPX), "init", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (root / ".pm" / "config" / "project.yaml").read_text(encoding="utf-8")
    assert "type: vue" in text
    assert "database: false" in text
    assert "operations: false" in text
    assert "cost: false" in text
    assert "runtime: vue3" in text
    assert "profile: frontend" in text
