"""Find missing unit-test companions. Never write tests into the business tree."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.architecture import load_map
from pm_manager_cli.redact import redact

_SOURCE_SUFFIXES = {".py", ".java", ".kt", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".vue"}
_SKIP_PARTS = {
    "test",
    "tests",
    "__pycache__",
    "node_modules",
    ".pm",
    ".git",
    "dist",
    "build",
    "vendor",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _source_candidates(root: Path) -> list[str]:
    nav = load_map(root) or {}
    found: list[str] = []
    seen: set[str] = set()

    def add(rel: str) -> None:
        rel = rel.replace("\\", "/")
        if not rel or rel in seen or rel.startswith(".pm/"):
            return
        suf = Path(rel).suffix.lower()
        if suf not in _SOURCE_SUFFIXES:
            return
        parts = {p.lower() for p in rel.split("/")}
        if parts & _SKIP_PARTS:
            return
        name = Path(rel).name.lower()
        if name.startswith("test_") or name.endswith("_test.py") or ".spec." in name or ".test." in name:
            return
        if not (root / rel).is_file():
            return
        seen.add(rel)
        found.append(rel)

    for item in nav.get("key_files") or []:
        if isinstance(item, dict):
            add(str(item.get("path") or ""))
        else:
            add(str(item))
    for rel in nav.get("changed_paths") or []:
        add(str(rel))
    src = root / "src"
    if src.is_dir():
        for p in src.rglob("*"):
            if p.is_file():
                try:
                    add(p.relative_to(root).as_posix())
                except ValueError:
                    continue
            if len(found) >= 40:
                break
    return found[:40]


def _changed_set(root: Path) -> set[str]:
    nav = load_map(root) or {}
    out: set[str] = set()
    for rel in nav.get("changed_paths") or []:
        out.add(str(rel).replace("\\", "/"))
    try:
        from pm_manager_cli.journal import extract_changes

        for row in extract_changes(root):
            out.add(str(row.get("path") or "").replace("\\", "/"))
    except Exception:
        pass
    return out


def suggested_test_path(rel: str) -> str:
    p = Path(rel)
    suf = p.suffix.lower()
    stem = p.stem
    if suf == ".py":
        return f"tests/test_{stem}.py"
    if suf in {".ts", ".tsx", ".vue"}:
        return str(p.with_name(f"{stem}.spec.ts")).replace("\\", "/")
    if suf in {".js", ".jsx"}:
        return str(p.with_name(f"{stem}.spec.js")).replace("\\", "/")
    if suf == ".go":
        return str(p.with_name(f"{stem}_test.go")).replace("\\", "/")
    if suf == ".rs":
        return "tests/" + str(p.with_suffix("_test.rs").name)
    if suf in {".java", ".kt"}:
        return f"src/test/java/{stem}Test{suf}"
    return f"tests/{stem}_test{suf}"


def _has_companion(root: Path, rel: str) -> bool:
    p = Path(rel)
    stem = p.stem
    suf = p.suffix.lower()
    guesses = [
        root / suggested_test_path(rel),
        root / "tests" / f"test_{stem}.py",
        root / "tests" / f"{stem}_test.py",
        root / "tests" / f"{stem}.spec.ts",
        root / "tests" / f"{stem}.test.ts",
        root / "tests" / f"{stem}_test.go",
        p.parent / f"{stem}_test{suf}",
        p.parent / f"{stem}.spec{suf}",
        p.parent / f"{stem}.test{suf}",
        p.parent / f"{stem}.spec.ts",
        p.parent / f"{stem}.test.ts",
        p.parent / f"test_{stem}{suf}",
    ]
    if any(g.is_file() for g in guesses):
        return True
    tests = root / "tests"
    if tests.is_dir():
        for cand in tests.rglob(f"*{stem}*"):
            if cand.is_file() and cand.suffix.lower() in _SOURCE_SUFFIXES | {".py"}:
                name = cand.name.lower()
                if "test" in name or "spec" in name:
                    return True
    return False


def find_test_gaps(project_root: Path) -> list[dict[str, object]]:
    root = project_root.resolve()
    changed = _changed_set(root)
    gaps: list[dict[str, object]] = []
    for rel in _source_candidates(root):
        if _has_companion(root, rel):
            continue
        gaps.append(
            {
                "path": rel,
                "suggest": suggested_test_path(rel),
                "changed": rel in changed,
            }
        )
    return gaps


def write_test_gaps(project_root: Path) -> tuple[Path, list[dict[str, object]]]:
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    gaps = find_test_gaps(root)
    from pm_manager_cli.vue_detect import has_dep

    lines = [
        "# 单元测试缺口",
        "",
        f"> 更新: {_now()}",
        "> 只提示建议落点，不写业务树测试文件。",
    ]
    if has_dep(root, "vitest"):
        lines.append("> 检测到 Vitest，建议配套 `*.spec.ts` / `*.test.ts`。")
    lines += [
        "",
        "| 源文件 | 建议测试 | 本轮变更 |",
        "|--------|----------|----------|",
    ]
    if not gaps:
        lines.append("| — | 未发现核心源缺口 | — |")
    else:
        for g in gaps:
            ch = "是" if g.get("changed") else "否"
            lines.append(f"| `{g['path']}` | `{g['suggest']}` | {ch} |")
    lines.append("")
    dest = pm / "state" / "test-gaps.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(redact("\n".join(lines)), encoding="utf-8")
    return dest, gaps
