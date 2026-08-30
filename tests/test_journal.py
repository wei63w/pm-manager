from pathlib import Path

from pm_manager_cli.journal import classify_intent, extract_files
from pm_manager_cli.redact import redact


def test_classify_fix_extracts_real_path() -> None:
    parsed = classify_intent("修一下 src/app.py 的登录超时")
    assert parsed["kind"] == "fix"
    assert parsed["status"] == "parsed"
    assert "src/app.py" in parsed["files"]


def test_classify_unclear_does_not_invent_files() -> None:
    parsed = classify_intent("你好")
    assert parsed["status"] == "unresolved"
    assert parsed["files"] == []
    assert parsed["kind"] == "other"


def test_extract_files_ignores_plain_words() -> None:
    assert extract_files("修复登录超时") == []


def test_redact_strips_password_before_excerpt() -> None:
    text = redact("修一下 src/app.py password=supersecret")
    assert "supersecret" not in text
    assert "***" in text
