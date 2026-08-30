"""Development journal: dialogue notes, intent, change points, timeline, suggestions."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pm_manager_cli.architecture import load_map
from pm_manager_cli.audit import read_audit
from pm_manager_cli.dashboard import hot_open_todos
from pm_manager_cli.docs_index import scan_core_docs
from pm_manager_cli.redact import redact
from pm_manager_cli.reviews import pending_review_count
from pm_manager_cli.speckit import read_prd_status

KINDS = ("consult", "code", "fix", "docs", "refactor", "other")
KIND_LABELS = {
    "consult": "需求咨询",
    "code": "代码生成",
    "fix": "bug修复",
    "docs": "文档编写",
    "refactor": "重构优化",
    "other": "其他",
}
_SOURCE_SUFFIXES = {".py", ".java", ".kt", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
_FILE_RE = re.compile(
    r"(?:`([^`\n]{3,160})`)"
    r"|((?:[\w.-]+[/\\])+[\w.-]+\.(?:py|ts|tsx|js|jsx|go|rs|java|kt|md|yml|yaml|json|toml|sql))"
    r"|((?:src|tests|docs|skills|adapters|scripts)[/\\][\w./\\-]{2,140})",
    re.IGNORECASE,
)
_FIX = (
    "修复",
    "修一下",
    "修好",
    "排查",
    "报错",
    "bug",
    "错误",
    "异常",
    "崩溃",
    "hotfix",
    "stack",
    "traceback",
    "fail",
    "panic",
    "分诊",
)
_DOCS = ("文档", "readme", "prd", "api.md", "design.md", "docs/", "补文档", "过期文档")
_REFACTOR = ("重构", "refactor", "清理代码", "rename")
_CODE = ("实现", "生成代码", "加上", "新增功能", "写一个", "implement", "feature", "写代码")
_CONSULT = ("怎么", "为什么", "什么是", "如何", "咨询", "how to", "what is", "why ")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _state(root: Path) -> Path:
    return root.resolve() / ".pm" / "state"


def dialogue_jsonl_path(root: Path) -> Path:
    return _state(root) / "dialogue.jsonl"


def dialogue_md_path(root: Path) -> Path:
    return _state(root) / "dialogue.md"


def _normalize_kind(kind: str | None) -> str:
    raw = (kind or "").strip().lower()
    aliases = {
        "咨询": "consult",
        "需求": "consult",
        "代码": "code",
        "生成": "code",
        "修复": "fix",
        "bug": "fix",
        "文档": "docs",
        "重构": "refactor",
        "其他": "other",
    }
    if raw in KINDS:
        return raw
    return aliases.get(raw, "")


def extract_files(text: str) -> list[str]:
    """Return path-like tokens only. Never invent files."""
    if not text:
        return []
    found: list[str] = []
    for match in _FILE_RE.finditer(text):
        raw = next((g for g in match.groups() if g), "")
        path = raw.strip().strip("`'\" ").replace("\\", "/")
        if not path or path in found:
            continue
        if "/" not in path and "\\" not in path:
            continue
        if any(ch in path for ch in (" ", "://", "*")):
            continue
        found.append(path)
        if len(found) >= 12:
            break
    return found


def classify_intent(
    text: str,
    *,
    kind: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Heuristic session intent. Unclear text → unresolved; never invent files."""
    excerpt = redact((text or "").strip())
    forced = _normalize_kind(kind)
    paths = list(files or []) or extract_files(excerpt)
    blob = excerpt.lower()

    detected = "other"
    if any(k in blob for k in _FIX):
        detected = "fix"
    elif any(k in blob for k in _DOCS):
        detected = "docs"
    elif any(k in blob for k in _REFACTOR):
        detected = "refactor"
    elif any(k in blob for k in _CODE):
        detected = "code"
    elif any(k in blob for k in _CONSULT):
        detected = "consult"

    final_kind = forced or detected
    first = excerpt.splitlines()[0] if excerpt else ""
    intent = redact(first[:80]) if first else ""
    if not intent:
        intent = "信息不足"

    status = "unresolved"
    if forced or detected != "other" or paths or (intent != "信息不足" and len(excerpt) >= 8):
        if forced or detected != "other" or paths:
            status = "parsed"
        elif len(excerpt) >= 12:
            status = "parsed"
            final_kind = final_kind if final_kind != "other" else "other"

    if not excerpt and not forced and not paths:
        status = "unresolved"
        final_kind = "other"
        intent = "信息不足"

    return {
        "kind": final_kind if final_kind in KINDS else "other",
        "intent": intent,
        "files": paths,
        "status": status,
        "excerpt": excerpt[:400],
    }


@dataclass
class DialogueNote:
    ts: str
    kind: str
    intent: str
    files: list[str] = field(default_factory=list)
    status: str = "unresolved"
    excerpt: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_notes(project_root: Path) -> list[DialogueNote]:
    path = dialogue_jsonl_path(project_root)
    if not path.is_file():
        return []
    notes: list[DialogueNote] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        files = raw.get("files") or []
        if not isinstance(files, list):
            files = []
        notes.append(
            DialogueNote(
                ts=str(raw.get("ts") or ""),
                kind=str(raw.get("kind") or "other"),
                intent=str(raw.get("intent") or "信息不足"),
                files=[str(f) for f in files if f],
                status=str(raw.get("status") or "unresolved"),
                excerpt=str(raw.get("excerpt") or ""),
            )
        )
    return notes


def _write_dialogue_md(root: Path, notes: list[DialogueNote]) -> Path:
    dest = dialogue_md_path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 开发对话记录",
        "",
        "> 脱敏后落盘。场景：需求咨询 / 代码生成 / bug修复 / 重构优化 / 文档编写。",
        "> 不可判断标 `unresolved`，禁止编造文件列表。",
        "",
    ]
    if not notes:
        lines.append("还没有对话摘要。运行 `pm log \"本轮在做什么\"` 或助手 `/pm-journal`。")
        lines.append("")
    else:
        for note in reversed(notes):
            label = KIND_LABELS.get(note.kind, note.kind)
            files = "、".join(f"`{p}`" for p in note.files) if note.files else "—"
            lines.extend(
                [
                    f"## {note.ts or '—'} · {label} · {note.status}",
                    "",
                    f"- 意图: {note.intent or '信息不足'}",
                    f"- 文件: {files}",
                    f"- 摘录: {note.excerpt or '—'}",
                    "",
                ]
            )
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def append_dialogue(
    project_root: Path,
    *,
    text: str = "",
    kind: str | None = None,
    intent: str | None = None,
    files: list[str] | None = None,
) -> DialogueNote:
    """Redact, classify, append one note. Does not invent file lists."""
    root = project_root.resolve()
    parsed = classify_intent(text, kind=kind, files=files)
    if intent and intent.strip():
        parsed["intent"] = redact(intent.strip())[:80]
        if parsed["status"] == "unresolved" and parsed["kind"] != "other":
            parsed["status"] = "parsed"
        if parsed["intent"] and parsed["intent"] != "信息不足":
            if parsed["kind"] != "other" or parsed["files"]:
                parsed["status"] = "parsed"
    note = DialogueNote(
        ts=_now(),
        kind=parsed["kind"],
        intent=parsed["intent"],
        files=parsed["files"],
        status=parsed["status"],
        excerpt=parsed["excerpt"],
    )
    dest = dialogue_jsonl_path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(note.as_dict(), ensure_ascii=False) + "\n")
        f.flush()
    notes = load_notes(root)
    _write_dialogue_md(root, notes)
    return note


def session_intent(notes: list[DialogueNote]) -> dict[str, Any]:
    recent = notes[-12:]
    if not recent:
        return {
            "generated_at": _now(),
            "kind": "other",
            "goal": "信息不足",
            "files": [],
            "status": "unresolved",
            "note_count": 0,
        }
    counts: dict[str, int] = {}
    files: list[str] = []
    goal = "信息不足"
    parsed_n = 0
    for note in reversed(recent):
        counts[note.kind] = counts.get(note.kind, 0) + 1
        for path in note.files:
            if path not in files:
                files.append(path)
        if goal == "信息不足" and note.intent and note.intent != "信息不足":
            goal = note.intent
        if note.status == "parsed":
            parsed_n += 1
    ranked = sorted(counts, key=lambda k: (-counts[k], k))
    kind = next((k for k in ranked if k != "other"), ranked[0] if ranked else "other")
    return {
        "generated_at": _now(),
        "kind": kind,
        "goal": goal,
        "files": files[:16],
        "status": "parsed" if parsed_n else "unresolved",
        "note_count": len(recent),
    }


def _git_changed_paths(root: Path) -> list[str]:
    commands = (
        ["git", "-C", str(root), "diff", "--name-only", "HEAD"],
        ["git", "-C", str(root), "diff", "--cached", "--name-only"],
        ["git", "-C", str(root), "status", "--porcelain"],
    )
    found: list[str] = []
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode != 0:
            continue
        for raw in proc.stdout.splitlines():
            line = raw.strip()
            if not line:
                continue
            if cmd[-1] == "--porcelain":
                line = line[3:].strip() if len(line) > 3 else line
                if " -> " in line:
                    line = line.split(" -> ", 1)[1]
            path = line.replace("\\", "/")
            if path.startswith(".pm/") or path in found:
                continue
            found.append(path)
            if len(found) >= 32:
                return found
    return found


def extract_changes(project_root: Path) -> list[dict[str, str]]:
    root = project_root.resolve()
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    nav = load_map(root) or {}
    for path in nav.get("changed_paths") or []:
        rel = str(path).replace("\\", "/")
        if not rel or rel in seen or rel.startswith(".pm/"):
            continue
        seen.add(rel)
        rows.append({"path": rel, "source": "map"})
    for path in _git_changed_paths(root):
        if path in seen:
            continue
        seen.add(path)
        rows.append({"path": path, "source": "git"})
    return rows[:32]


def build_suggestions(project_root: Path) -> list[dict[str, str]]:
    root = project_root.resolve()
    pm = root / ".pm"
    items: list[dict[str, str]] = []

    def add(priority: str, title: str, reason: str, action: str) -> None:
        items.append(
            {
                "id": f"SUG-{len(items) + 1:03d}",
                "priority": priority,
                "title": title,
                "reason": reason,
                "action": action,
            }
        )

    todos = hot_open_todos(pm) if pm.is_dir() else []
    if todos:
        add(
            "P0",
            f"{len(todos)} 条未关闭阻断/高优先级待办",
            "日常循环应先消化这些项",
            "/pm-next",
        )
    pending = pending_review_count(root)
    if pending:
        add(
            "P0",
            f"{pending} 条待处置评审",
            "确认 / 误报 / 延后，避免问题悬空",
            "/pm-review",
        )
    docs = scan_core_docs(root)
    missing = [e for e in docs if e.status == "missing"]
    stale = [e for e in docs if e.status == "possibly_stale"]
    if missing:
        add(
            "P1",
            f"缺失 {len(missing)} 份核心文档",
            "、".join(e.id for e in missing[:6]),
            "/pm-docs 或 `pm docs --draft`",
        )
    if stale:
        add(
            "P1",
            f"{len(stale)} 份文档可能过期",
            "代码变更晚于文档 mtime",
            "/pm-docs",
        )
    if not (root / ".pm" / "architecture" / "map.json").is_file():
        add("P1", "还没有导航地图", "先定位再改代码，避免全库递归", "`pm arch` / `/pm-arch`")
    else:
        nav = load_map(root) or {}
        risk_hint = nav.get("hotspots") or []
        if risk_hint:
            add(
                "P2",
                "本轮有热点文件",
                "、".join(str(h if not isinstance(h, dict) else h.get("path") or h) for h in risk_hint[:4]),
                "`pm map` 核对后再改",
            )

    prd = read_prd_status(root) or "absent"
    if prd == "draft":
        add("P2", "PRD 仍是草稿", "未确认不得当基线；跳过仍可做技术扫描", "/pm-init confirm / skip")

    changes = extract_changes(root)
    source_changes = [
        c["path"]
        for c in changes
        if Path(c["path"]).suffix.lower() in _SOURCE_SUFFIXES
    ]
    testish = any("test" in c["path"].replace("\\", "/").lower() for c in changes)
    if source_changes and not testish:
        add(
            "P2",
            "变更未见到配套测试",
            "、".join(source_changes[:4]),
            "确认后补测，或说明不需要",
        )

    notes = load_notes(root)
    unresolved = sum(1 for n in notes if n.status == "unresolved")
    if not notes:
        add("P2", "还没有对话落盘", "跨会话会丢掉本轮意图", '`pm log "本轮在做什么"` / `/pm-journal`')
    elif unresolved:
        add(
            "P2",
            f"{unresolved} 条对话意图未解析",
            "补一句目标和文件，避免编造路径",
            "`pm log --intent … --file …`",
        )
    return items


def build_timeline(project_root: Path) -> list[dict[str, str]]:
    root = project_root.resolve()
    events: list[dict[str, str]] = []
    for row in read_audit(root):
        events.append(
            {
                "ts": str(row.get("ts") or ""),
                "kind": "audit",
                "title": str(row.get("command") or "audit"),
                "detail": redact(str(row.get("output_summary") or row.get("input_summary") or "")),
            }
        )
    for note in load_notes(root):
        files = "、".join(note.files) if note.files else "—"
        events.append(
            {
                "ts": note.ts,
                "kind": note.kind,
                "title": note.intent or KIND_LABELS.get(note.kind, note.kind),
                "detail": files,
            }
        )
    nav = load_map(root) or {}
    gen = str(nav.get("generated_at") or "")
    for change in extract_changes(root)[:16]:
        events.append(
            {
                "ts": gen or _now(),
                "kind": "change",
                "title": change["path"],
                "detail": change["source"],
            }
        )
    events.sort(key=lambda e: e.get("ts") or "", reverse=True)
    return events[:80]


def _render_timeline(events: list[dict[str, str]]) -> str:
    kind_zh = {
        "audit": "审计",
        "change": "变更",
        **KIND_LABELS,
    }
    lines = [
        "# 开发迭代时间线",
        "",
        "> 合并审计、对话意图与变更点，供复盘 / 接手 / 追溯。",
        "",
        "| 时间 | 类型 | 摘要 | 证据 |",
        "|------|------|------|------|",
    ]
    if not events:
        lines.append("| — | — | 还没有记录 | 先 `pm log` 或跑一次治理命令 |")
    else:
        for ev in events:
            ts = (ev.get("ts") or "—").replace("|", " ")
            kind = kind_zh.get(ev.get("kind") or "", ev.get("kind") or "")
            title = (ev.get("title") or "—").replace("|", " ")
            detail = (ev.get("detail") or "—").replace("|", " ")
            lines.append(f"| {ts} | {kind} | {title} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def _render_suggestions(items: list[dict[str, str]]) -> str:
    lines = [
        "# 智能优化建议",
        "",
        "> 结合地图、文档索引、待办与评审。只提示，不自动改业务代码。",
        "",
    ]
    if not items:
        lines.append("暂无建议。治理台可用时日常走 `/pm-status`。")
        lines.append("")
        return "\n".join(lines)
    for band in ("P0", "P1", "P2"):
        group = [i for i in items if i["priority"] == band]
        if not group:
            continue
        lines.append(f"## {band}")
        lines.append("")
        for item in group:
            lines.append(f"- `{item['id']}` {item['title']}")
            lines.append(f"  - 原因: {item['reason']}")
            lines.append(f"  - 下一步: {item['action']}")
        lines.append("")
    return "\n".join(lines)


def _render_changes(rows: list[dict[str, str]]) -> str:
    lines = [
        "# 变更点",
        "",
        "> 来自导航地图 `changed_paths` 与 git（失败则忽略）。不含 `.pm/`。",
        "",
        "| 路径 | 来源 |",
        "|------|------|",
    ]
    if not rows:
        lines.append("| — | 本轮未检测到业务变更 |")
    else:
        for row in rows:
            lines.append(f"| `{row['path']}` | {row['source']} |")
    lines.append("")
    return "\n".join(lines)


@dataclass
class JournalReport:
    session: dict[str, Any]
    suggestions: list[dict[str, str]]
    changes: list[dict[str, str]]
    timeline: list[dict[str, str]]
    notes: list[DialogueNote]
    timeline_path: Path
    suggestions_path: Path
    session_path: Path
    changes_path: Path
    dialogue_path: Path


def write_journal(project_root: Path) -> JournalReport:
    """Refresh timeline / suggestions / session / changes / dialogue.md."""
    root = project_root.resolve()
    pm = root / ".pm"
    if not pm.is_dir():
        raise FileNotFoundError(f"缺少 .pm/（{root}）；请先运行 `pm init`")
    state = _state(root)
    state.mkdir(parents=True, exist_ok=True)
    notes = load_notes(root)
    session = session_intent(notes)
    suggestions = build_suggestions(root)
    changes = extract_changes(root)
    timeline = build_timeline(root)
    dialogue = _write_dialogue_md(root, notes)
    timeline_path = state / "timeline.md"
    suggestions_path = state / "suggestions.md"
    session_path = state / "session.json"
    changes_path = state / "changes.md"
    timeline_path.write_text(redact(_render_timeline(timeline)), encoding="utf-8")
    suggestions_path.write_text(redact(_render_suggestions(suggestions)), encoding="utf-8")
    session_path.write_text(
        json.dumps(session, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    changes_path.write_text(redact(_render_changes(changes)), encoding="utf-8")
    return JournalReport(
        session=session,
        suggestions=suggestions,
        changes=changes,
        timeline=timeline,
        notes=notes,
        timeline_path=timeline_path,
        suggestions_path=suggestions_path,
        session_path=session_path,
        changes_path=changes_path,
        dialogue_path=dialogue,
    )


def load_session(project_root: Path) -> dict[str, Any]:
    path = _state(project_root) / "session.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return session_intent(load_notes(project_root))
