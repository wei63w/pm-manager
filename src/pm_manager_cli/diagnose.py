"""Read-only .pm/ health diagnostics for `pm check` / `/pm-check`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pm_manager_cli.reviews import pending_review_count
from pm_manager_cli.speckit import read_prd_status


@dataclass
class CheckItem:
    name: str
    ok: bool
    detail: str = ""


def _audit_ok(root: Path) -> CheckItem:
    path = root / ".pm" / "state" / "audit.jsonl"
    if not path.is_file():
        return CheckItem(".pm/state/audit.jsonl", False, "缺失")
    bad = 0
    lines = 0
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            lines += 1
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                bad += 1
    except OSError as exc:
        return CheckItem(".pm/state/audit.jsonl", False, f"无法读取: {exc}")
    if bad:
        return CheckItem(".pm/state/audit.jsonl", False, f"{bad}/{lines} 行无法解析")
    return CheckItem(".pm/state/audit.jsonl", True, f"{lines} 行")


def _map_ok(root: Path) -> CheckItem:
    path = root / ".pm" / "architecture" / "map.json"
    if not path.is_file():
        return CheckItem(".pm/architecture/map.json", False, "缺失 — 运行 /pm-init 确认后轻扫或 `pm arch`")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CheckItem(".pm/architecture/map.json", False, f"损坏: {exc}")
    age_hours = (
        datetime.now(timezone.utc)
        - datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    ).total_seconds() / 3600
    detail = "可读"
    if age_hours > 24 * 14:
        detail = f"可读（已超过 {int(age_hours / 24)} 天，可用 `pm arch` 增量更新）"
    return CheckItem(".pm/architecture/map.json", True, detail)


def collect_checks(root: Path) -> list[CheckItem]:
    root = root.resolve()
    items: list[CheckItem] = []
    pm = root / ".pm"
    items.append(CheckItem(".pm/", pm.is_dir(), "" if pm.is_dir() else "请先运行 `pm init`"))
    if not pm.is_dir():
        return items

    items.append(
        CheckItem(
            ".pm/config/project.yaml",
            (pm / "config" / "project.yaml").is_file(),
            "" if (pm / "config" / "project.yaml").is_file() else "缺失配置",
        )
    )
    items.append(_map_ok(root))
    items.append(_audit_ok(root))
    items.append(
        CheckItem(
            ".pm/state/doc-index.md",
            (pm / "state" / "doc-index.md").is_file(),
            "" if (pm / "state" / "doc-index.md").is_file() else "运行 `pm docs`",
        )
    )
    dash = (pm / "dashboard" / "index.html").is_file()
    items.append(
        CheckItem(
            ".pm/dashboard/index.html",
            dash,
            "" if dash else "尚未生成 — `/pm-all` 或 `pm dashboard`",
        )
    )
    items.append(
        CheckItem(
            "Cursor 技能",
            (root / ".cursor" / "skills" / "pm-manager" / "SKILL.md").is_file(),
        )
    )
    claude = (
        any((root / ".claude" / "commands").glob("pm-*.md"))
        if (root / ".claude" / "commands").is_dir()
        else False
    )
    items.append(CheckItem("Claude 命令", claude))
    exclude = root / ".git" / "info" / "exclude"
    excluded = False
    if exclude.is_file():
        excluded = any(
            line.strip() == ".pm/"
            for line in exclude.read_text(encoding="utf-8").splitlines()
        )
    items.append(
        CheckItem(
            "git exclude .pm/",
            excluded,
            "" if excluded else "非 git 仓库或未写入 exclude",
        )
    )
    items.append(
        CheckItem(".pm/prd/prd.md", (pm / "prd" / "prd.md").is_file())
    )
    prd = read_prd_status(root) or "absent"
    items.append(
        CheckItem(
            "prd.status",
            prd in {"confirmed", "skipped", "absent"},
            prd if prd != "draft" else "draft — 回复 confirm / revise / skip，不阻塞技术扫描",
        )
    )
    pending = pending_review_count(root)
    items.append(
        CheckItem(
            "待处置评审",
            pending == 0,
            "无" if pending == 0 else f"{pending} 条 — 用 /pm-review 处置",
        )
    )
    return items


def repair_hints(items: list[CheckItem]) -> list[str]:
    names = {i.name: i for i in items}
    hints: list[str] = []
    if not names.get(".pm/", CheckItem("", True)).ok:
        hints.append("运行 `pm init` 或助手 `/pm-init`")
        return hints
    if names.get(".pm/architecture/map.json") and not names[".pm/architecture/map.json"].ok:
        hints.append("运行 `pm arch` 重建地图（不覆盖已确认 PRD）")
    if names.get(".pm/state/audit.jsonl") and not names[".pm/state/audit.jsonl"].ok:
        hints.append("损坏的 audit.jsonl：备份后保留可读行，或让 /pm-check repair 处理")
    if names.get(".pm/dashboard/index.html") and not names[".pm/dashboard/index.html"].ok:
        hints.append("运行 `pm dashboard` 或 `/pm-all` 生成看板")
    if names.get(".pm/state/doc-index.md") and not names[".pm/state/doc-index.md"].ok:
        hints.append("运行 `pm docs` 刷新文档索引")
    return hints
