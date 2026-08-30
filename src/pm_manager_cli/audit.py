from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def audit_path(project_root: Path) -> Path:
    return project_root.resolve() / ".pm" / "state" / "audit.jsonl"


def append_audit(
    project_root: Path,
    *,
    command: str,
    input_summary: str = "",
    output_summary: str = "",
    reasoning: str | None = None,
    actor_or_session: str = "local",
) -> Path:
    """Append one JSONL audit event. Creates `.pm/state/` if missing."""
    path = audit_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    event: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_or_session": actor_or_session,
        "command": command,
        "input_summary": input_summary,
        "output_summary": output_summary,
    }
    if reasoning:
        event["reasoning"] = reasoning
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
        f.flush()
    return path


def read_audit(project_root: Path) -> list[dict[str, Any]]:
    path = audit_path(project_root)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
