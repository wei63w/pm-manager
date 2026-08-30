from pathlib import Path

from pm_manager_cli.speckit import (
    detect_speckit,
    existing_prd_candidates,
    infer_project_type,
    looks_like_existing_project,
    write_init_metadata,
)


def test_empty_repo_is_not_speckit(tmp_path: Path) -> None:
    assert detect_speckit(tmp_path).present is False


def test_empty_specify_dir_is_not_speckit(tmp_path: Path) -> None:
    (tmp_path / ".specify").mkdir()
    assert detect_speckit(tmp_path).present is False


def test_constitution_counts_as_speckit(tmp_path: Path) -> None:
    path = tmp_path / ".specify" / "memory" / "constitution.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Constitution\n", encoding="utf-8")
    det = detect_speckit(tmp_path)
    assert det.present is True
    assert det.constitution_rel(tmp_path) == ".specify/memory/constitution.md"


def test_specs_count_as_speckit(tmp_path: Path) -> None:
    spec = tmp_path / ".specify" / "specs" / "001-foo" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# Spec\n", encoding="utf-8")
    det = detect_speckit(tmp_path)
    assert det.present is True
    assert det.spec_rels(tmp_path) == [".specify/specs/001-foo/spec.md"]


def test_existing_prd_ignores_tiny_stub(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "prd.md").write_text("todo\n", encoding="utf-8")
    assert existing_prd_candidates(tmp_path) == []


def test_existing_prd_finds_substantial_doc(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "prd.md").write_text("# PRD\n" + ("x" * 80), encoding="utf-8")
    found = existing_prd_candidates(tmp_path)
    assert len(found) == 1
    assert found[0].name.lower() == "prd.md"


def test_infer_project_type(tmp_path: Path) -> None:
    assert infer_project_type(tmp_path) == "unknown"
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    assert infer_project_type(tmp_path) == "node"


def test_infer_project_type_vue_from_deps(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"vue":"^3.4.0"}}\n',
        encoding="utf-8",
    )
    assert infer_project_type(tmp_path) == "vue"


def test_looks_like_existing_project(tmp_path: Path) -> None:
    assert looks_like_existing_project(tmp_path) is False
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    assert looks_like_existing_project(tmp_path) is True


def test_write_init_metadata_sets_speckit(tmp_path: Path) -> None:
    cfg = tmp_path / ".pm" / "config"
    cfg.mkdir(parents=True)
    yaml_path = cfg / "project.yaml"
    yaml_path.write_text("version: \"2.0\"\nproject:\n  name: demo\n", encoding="utf-8")
    constitution = tmp_path / ".specify" / "memory" / "constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_text("# C\n", encoding="utf-8")
    write_init_metadata(tmp_path, detect_speckit(tmp_path))
    text = yaml_path.read_text(encoding="utf-8")
    assert "speckit:" in text
    assert "present: true" in text
    assert ".specify/memory/constitution.md" in text
    assert "prd:" in text
