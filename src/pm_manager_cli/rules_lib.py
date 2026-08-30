"""Team coding rules library in `.pm/engineering/rules.md`."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PLACEHOLDER = frozenset({"", "—", "-", "id"})


@dataclass
class Rule:
    id: str
    text: str
    source_finding: str
    enabled: bool
    severity: str = "P2"


def rules_path(project_root: Path) -> Path:
    return project_root.resolve() / ".pm" / "engineering" / "rules.md"


def parse_rules(text: str) -> list[Rule]:
    rows: list[Rule] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rid = cells[0]
        if rid.lower() in {"id"} or set(rid) <= {"-", ":"} or rid in PLACEHOLDER:
            continue
        enabled = cells[3].lower() not in {"false", "0", "no", "off", "禁用"}
        sev = cells[4] if len(cells) > 4 else "P2"
        rows.append(
            Rule(
                id=rid,
                text=cells[1],
                source_finding=cells[2],
                enabled=enabled,
                severity=sev or "P2",
            )
        )
    return rows


def load_rules(project_root: Path) -> list[Rule]:
    path = rules_path(project_root)
    if not path.is_file():
        return []
    try:
        return parse_rules(path.read_text(encoding="utf-8"))
    except OSError:
        return []


def enabled_rules(project_root: Path) -> list[Rule]:
    return [r for r in load_rules(project_root) if r.enabled]


def _esc(text: str) -> str:
    return (text or "").replace("|", " ").replace("\n", " ").strip()


def render_rules(rows: list[Rule]) -> str:
    lines = [
        "# 编码规范库",
        "",
        "只有评审里 **confirmed** 的条目可以写入。后续生成与评审必须加载 `enabled: true` 的规则。",
        "",
        "| id | text | source_finding | enabled | severity |",
        "|----|------|----------------|---------|----------|",
    ]
    if not rows:
        lines.append("| — | — | — | true | P2 |")
    else:
        for r in rows:
            lines.append(
                f"| {_esc(r.id)} | {_esc(r.text)} | {_esc(r.source_finding)} | "
                f"{'true' if r.enabled else 'false'} | {_esc(r.severity) or 'P2'} |"
            )
    lines.append("")
    return "\n".join(lines)


def write_rules(project_root: Path, rows: list[Rule]) -> Path:
    dest = rules_path(project_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_rules(rows), encoding="utf-8")
    return dest


def next_rule_id(rows: list[Rule]) -> str:
    n = 0
    for row in rows:
        m = re.fullmatch(r"RULE-(\d+)", row.id, flags=re.I)
        if m:
            n = max(n, int(m.group(1)))
    return f"RULE-{n + 1:03d}"


def add_rule(
    project_root: Path,
    text: str,
    *,
    source_finding: str = "",
    severity: str = "P2",
) -> Rule:
    rows = load_rules(project_root)
    for row in rows:
        if row.source_finding and source_finding and row.source_finding == source_finding:
            return row
    rule = Rule(
        id=next_rule_id(rows),
        text=text.strip(),
        source_finding=source_finding,
        enabled=True,
        severity=severity,
    )
    rows.append(rule)
    write_rules(project_root, rows)
    return rule


def set_rule_enabled(project_root: Path, rid: str, enabled: bool) -> Rule:
    rows = load_rules(project_root)
    want = (rid or "").strip().upper()
    found: Rule | None = None
    for row in rows:
        if row.id.upper() == want:
            row.enabled = enabled
            found = row
            break
    if found is None:
        raise FileNotFoundError(f"没有规则 {rid}")
    write_rules(project_root, rows)
    return found


def match_rules(project_root: Path, *, path: str = "", blob: str = "") -> list[Rule]:
    hay = f"{path} {blob}".lower()
    hits: list[Rule] = []
    for rule in enabled_rules(project_root):
        tokens = [t for t in re.split(r"[\s,，。；;]+", rule.text.lower()) if len(t) >= 3]
        if any(t in hay for t in tokens[:8]):
            hits.append(rule)
    return hits
