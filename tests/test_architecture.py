import json
from pathlib import Path

from pm_manager_cli.architecture import write_architecture
from pm_manager_cli.scaffold import scaffold


def _app_tree(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "info").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "index.js").write_text("module.exports = 1\n", encoding="utf-8")
    scaffold(tmp_path)
    return tmp_path


def test_map_skips_node_modules(tmp_path: Path) -> None:
    root = _app_tree(tmp_path)
    arch, _model = write_architecture(root)
    data = json.loads((arch / "map.json").read_text(encoding="utf-8"))
    joined = " ".join(data.get("file_hashes", {}))
    assert "node_modules" not in joined
    assert any("app.py" in p for p in data["file_hashes"])
    tree = (arch / "tree.md").read_text(encoding="utf-8")
    assert "├── node_modules" not in tree
    assert "└── node_modules" not in tree
    assert "app.py" in tree
    assert "业务源码" in tree


def test_incremental_changed_paths(tmp_path: Path) -> None:
    root = _app_tree(tmp_path)
    write_architecture(root)
    extra = root / "src" / "new.py"
    extra.write_text("x = 1\n", encoding="utf-8")
    arch, model = write_architecture(root)
    data = json.loads((arch / "map.json").read_text(encoding="utf-8"))
    assert any("new.py" in p for p in data["changed_paths"])
    assert len(data["changed_paths"]) < len(data["file_hashes"])
    assert any("incremental" in n for n in model.notes)


def test_unreadable_file_does_not_abort(tmp_path: Path, monkeypatch) -> None:
    root = _app_tree(tmp_path)
    from pm_manager_cli import architecture as arch_mod

    real_sig = arch_mod._file_sig

    def boom(path: Path) -> str:
        if path.name == "app.py":
            raise OSError("simulated")
        return real_sig(path)

    monkeypatch.setattr(arch_mod, "_file_sig", boom)
    arch, model = write_architecture(root)
    assert (arch / "map.json").is_file()
    assert any("unreadable" in n for n in model.notes)
